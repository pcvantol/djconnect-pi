"""Released Core public_session/session_retained rule; synthetic owner reads."""
from copy import deepcopy
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest
from test_session_controller import clock_fixture, enable_search
from test_session_history_view import timeline_fixture

from djconnect_pi.session_projection import history_page
from djconnect_pi.session_transport import SessionError

pytest_plugins = ["test_session_controller"]


def page(now, status="ENDED"):
    stamp = datetime.fromtimestamp(now - 86400 + 5, UTC).isoformat()
    return {"success": True, "schema_version": 2, "history_contract_version": 2,
        "retention_days": 1, "retention_revision": 1, "revision": "owner-r1", "next_cursor": "opaque-next",
        "sessions": [{"session_id": "saved", "revision": "session-r1", "lifecycle_status": status,
            "created_at": stamp, "started_at": stamp, "ended_at": stamp if status == "ENDED" else "",
            "interrupted_at": stamp if status == "INTERRUPTED" else ""}]}


@pytest.mark.parametrize("status", ["ENDED", "INTERRUPTED", "ACTIVE", "OPENING"])
def test_header_deadline_uses_explicit_policy_and_released_lifecycle_rule(status):
    now = 1792454400
    raw = page(now, status); original = deepcopy(raw)
    result = history_page(raw, now=now)
    assert raw == original
    deadline = result["sessions"][0]["_history_deadline"]
    assert deadline == (now + 5 if status in {"ENDED", "INTERRUPTED"} else None)
    if deadline:
        with pytest.raises(SessionError): history_page(raw, now=deadline)


@pytest.mark.parametrize("days", [None, True, 0, 91, "1"])
def test_nonempty_list_does_not_invent_a_retention_policy(days):
    raw = page(1792454400);raw["retention_days"] = days
    with pytest.raises(SessionError): history_page(raw, now=1792454400)


def test_header_rejects_unknown_lifecycle_and_unzoned_retention_stamp():
    for mutation in ["status", "stamp"]:
        raw = page(1792454400)
        if mutation == "status": raw["sessions"][0]["lifecycle_status"] = "unknown"
        else: raw["sessions"][0]["ended_at"] = "2026-10-19T00:00:00"
        with pytest.raises(SessionError): history_page(raw, now=1792454400)


def test_list_and_open_detail_with_longer_entry_expiry_withdraw_atomically(controller):
    owner, backend = controller
    host = clock_fixture(owner);enable_search(owner)
    owner.transport.history = Mock(return_value=page(host.wall))
    owner.loadHistory();backend.jobs.pop()()
    tail = timeline_fixture();tail["session"]["session_id"] = "saved"
    for row in tail["entries"]: row["session_id"] = "saved";row["retained_until"] = "9999-01-01T00:00:00Z"
    owner.transport.timeline = Mock(return_value=tail)
    owner.openSaved("saved");backend.jobs.pop()()
    assert owner.state["timeline"]["entries"]
    assert owner._timeline["_session_deadline"] == host.wall + 5
    owner._search = {"session_id": "saved", "matches": tail["entries"]}
    changed = Mock();owner.changed.connect(changed)
    host.tick = 5
    assert not owner.state["sessions"] and not owner.state["timeline"] and not owner.state["search"]
    assert not owner.state["has_more_sessions"] and owner._history_dirty
    host.wall -= 3600;owner._expire()
    changed.assert_called_once()
    assert not owner.state["sessions"] and not owner.state["timeline"]
    owner.loadHistory();backend.jobs.pop()()
    assert not owner.state["sessions"]  # unchanged old response cannot revive after rollback


def test_list_expiring_on_gui_queue_clears_previous_headers(controller):
    owner, backend = controller
    host = clock_fixture(owner);enable_search(owner)
    owner._sessions = [{"session_id": "old"}]
    owner.transport.history = Mock(return_value=page(host.wall))
    queued = []
    owner._ready.disconnect(owner._apply);owner._ready.connect(queued.append)
    owner.loadHistory();backend.jobs.pop()()
    assert queued[0]["history"]["sessions"]
    host.tick = 5;owner._apply(queued.pop())
    assert owner.state["sessions"] == [] and not owner.state["has_more_sessions"]
    assert owner.state["error"] == "unavailable"



def test_header_getter_withdrawal_does_not_swallow_selected_context_notification(controller):
    owner, backend = controller
    host = clock_fixture(owner);enable_search(owner)
    owner.transport.history = Mock(return_value=page(host.wall))
    owner.loadHistory();backend.jobs.pop()()
    owner._timeline = {"session": {"session_id": "saved"}, "_session_deadline": host.wall + 5,
        "entries": [{"entry_id": "selected", "retained_until": "9999-01-01T00:00:00Z"}]}
    owner._selection = {"kind": "selected_entry", "session_id": "saved", "entry_id": "selected"}
    notified = Mock();owner.selectionInvalidated.connect(notified)
    host.tick = 5
    assert not owner.state["timeline"] and not owner.state["selection"]
    notified.assert_not_called()
    owner._expire()
    notified.assert_called_once()
