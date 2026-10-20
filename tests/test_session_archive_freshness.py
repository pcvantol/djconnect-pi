"""Fresh bounded owner-list traversal; synthetic transport, no server effects."""
from copy import deepcopy
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest
from test_session_controller import clock_fixture, enable_search
from test_session_header_retention import page

from djconnect_pi.session_transport import SessionError

pytest_plugins = ["test_session_controller"]


def archive_pages(owner, count=2, rows=1):
    host = clock_fixture(owner);enable_search(owner)
    pages = []
    for number in range(count):
        payload = page(host.wall)
        payload["sessions"] = []
        for index in range(rows):
            row = deepcopy(page(host.wall)["sessions"][0])
            row.update(session_id=f"saved-{number}-{index}", created_at=datetime.fromtimestamp(host.wall - (number * rows + index + 1) * 60, UTC).isoformat())
            row["summary"] = {"text": f"fresh-{number}-{index}"}
            payload["sessions"].append(row)
        payload["next_cursor"] = f"cursor-{number + 1}" if number + 1 < count else None
        pages.append(payload)
    def response(binding, *, cursor=""):
        return deepcopy(pages[int(cursor.split("-")[-1]) if cursor else 0])
    owner.transport.history = Mock(side_effect=response)
    return host, pages


def run(owner, backend, name):
    getattr(owner, name)();backend.jobs.pop()()


def test_more_and_refresh_read_every_page_again_using_only_fresh_cursors(controller):
    owner, backend = controller
    _, pages = archive_pages(owner)
    run(owner, backend, "loadHistory")
    pages[0]["sessions"][0]["summary"]["text"] = "updated first page"
    run(owner, backend, "moreHistory")
    assert [c.kwargs["cursor"] for c in owner.transport.history.call_args_list] == ["", "", "cursor-1"]
    assert owner.state["sessions"][0]["summary"]["text"] == "updated first page"
    pages[0]["sessions"] = []
    run(owner, backend, "refreshArchive")
    assert [r["session_id"] for r in owner.state["sessions"]] == ["saved-1-0"]
    assert owner._history_pages == 2


@pytest.mark.parametrize("conflict", ["revision", "policy", "duplicate", "order", "cycle", "denied"])
def test_conflicting_or_denied_page_withdraws_all_old_headers(controller, conflict):
    owner, backend = controller
    _, pages = archive_pages(owner, 3)
    run(owner, backend, "loadHistory")
    if conflict == "revision": pages[1]["revision"] = "changed"
    if conflict == "policy": pages[1]["retention_revision"] = 2
    if conflict == "duplicate": pages[1]["sessions"][0]["session_id"] = "saved-0-0"
    if conflict == "order": pages[1]["sessions"][0]["created_at"] = "9999-01-01T00:00:00Z"
    if conflict == "cycle": pages[1]["next_cursor"] = "cursor-1"
    if conflict == "denied": owner.transport.history.side_effect = SessionError("denied")
    run(owner, backend, "moreHistory")
    assert not owner.state["sessions"] and not owner.state["has_more_sessions"]
    assert owner.state["error"]


def test_sixth_page_is_not_loaded_or_misrepresented_as_complete(controller):
    owner, backend = controller
    archive_pages(owner, 6, 20)
    run(owner, backend, "loadHistory")
    for _ in range(4): run(owner, backend, "moreHistory")
    assert len(owner.state["sessions"]) == 100 and owner.state["history_limit_reached"]
    assert not owner.state["has_more_sessions"] and owner._history_cursor == "cursor-5"
    count = owner.transport.history.call_count
    owner.moreHistory()
    assert not backend.jobs and owner.transport.history.call_count == count
    run(owner, backend, "refreshArchive")
    assert owner.transport.history.call_count == count + 5


def test_cancellation_between_pages_stops_further_gets_and_cannot_publish(controller):
    owner, backend = controller
    archive_pages(owner)
    run(owner, backend, "loadHistory")
    original = owner.transport.history.side_effect
    def cancel(binding, *, cursor=""):
        result = original(binding, cursor=cursor)
        owner.clearSearch()  # existing view-epoch cancellation, no binding or source mutation
        return result
    owner.transport.history.side_effect = cancel
    before = owner.transport.history.call_count
    run(owner, backend, "moreHistory")
    assert owner.transport.history.call_count == before + 1
    assert owner._history_pages == 1


def test_known_header_deadline_is_not_extended_by_refetch(controller):
    owner, backend = controller
    host, pages = archive_pages(owner)
    run(owner, backend, "loadHistory")
    original = owner.state["sessions"][0]["_history_deadline"]
    for payload in pages: payload["retention_days"] = 2;payload["retention_revision"] = 2
    run(owner, backend, "refreshArchive")
    assert owner.state["sessions"][0]["_history_deadline"] == original
    host.tick = 5;owner._expire()
    assert not owner.state["sessions"]


def test_profile_binding_loss_between_pages_stops_old_owner_reads(controller):
    owner, backend = controller
    archive_pages(owner)
    run(owner, backend, "loadHistory")
    original = owner.transport.history.side_effect
    def change_profile(binding, *, cursor=""):
        result = original(binding, cursor=cursor)
        backend.cfg.active_profile_id = "foreign-profile"
        return result
    owner.transport.history.side_effect = change_profile
    before = owner.transport.history.call_count
    run(owner, backend, "moreHistory")
    assert owner.transport.history.call_count == before + 1
    assert not owner.state["sessions"]


def test_wire_page_cannot_exceed_the_twenty_requested_headers(controller):
    owner, backend = controller
    archive_pages(owner, 1, 21)
    run(owner, backend, "loadHistory")
    assert owner.state["error"] == "invalid" and not owner.state["sessions"]



def test_expiring_one_header_keeps_fresh_traversal_budget_for_remaining_pages(controller):
    owner, backend = controller
    host, pages = archive_pages(owner)
    pages[1]["sessions"][0]["ended_at"] = datetime.fromtimestamp(host.wall, UTC).isoformat()
    run(owner, backend, "loadHistory");run(owner, backend, "moreHistory")
    host.tick = 5;owner._expire()
    assert len(owner.state["sessions"]) == 1 and owner._history_pages == 2
    assert not owner.state["has_more_sessions"]
    pages[0]["sessions"] = []
    before = owner.transport.history.call_count
    run(owner, backend, "refreshArchive")
    assert owner.transport.history.call_count == before + 2
    assert len(owner.state["sessions"]) == 1 and owner._history_pages == 2
