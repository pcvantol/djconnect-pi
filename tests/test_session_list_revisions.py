"""SQL list metadata never becomes an opaque detail/delete revision."""
from copy import deepcopy

import pytest
from test_session_archive_freshness import archive_pages, run
from test_session_history_view import timeline_fixture

from djconnect_pi.session_projection import history_page
from djconnect_pi.session_transport import SessionError

pytest_plugins = ["test_session_controller"]


def response(revision):
    # Core public_session copies the SQL revision unchanged into this header.
    return {"success": True, "schema_version": 2, "history_contract_version": 2,
            "revision": "synthetic-owner-list-revision", "retention_days": 7,
            "retention_revision": 0, "next_cursor": None, "sessions": [{
                "session_id": "synthetic-saved", "lifecycle_status": "ENDED",
                "created_at": "2026-10-20T12:00:00Z", "started_at": None,
                "ended_at": "2026-10-20T12:05:00Z", "interrupted_at": None,
                "revision": revision, "read_only": True,
                "history_coverage": "saved_entries_only_no_retrospective_observations"}]}


@pytest.mark.parametrize("revision", [0, 1, 2**31, 2**63 - 1])
def test_numeric_sql_list_metadata_is_preserved_without_conversion(revision):
    payload = response(revision)
    original = deepcopy(payload)
    decoded = history_page(payload, now=1792497600)
    assert decoded["sessions"][0]["revision"] == revision
    assert type(decoded["sessions"][0]["revision"]) is int
    assert decoded["revision"] == "synthetic-owner-list-revision"
    assert payload == original


@pytest.mark.parametrize("revision", [True, False, -1, 1.0, None, "", [], {}])
def test_malformed_list_revisions_are_not_admitted(revision):
    with pytest.raises(SessionError, match="invalid"):
        history_page(response(revision), now=1792497600)


def test_existing_nonempty_string_list_metadata_remains_compatible():
    decoded = history_page(response("legacy-list-revision"), now=1792497600)
    assert decoded["sessions"][0]["revision"] == "legacy-list-revision"


@pytest.mark.parametrize("revision", [0, 1, True, None, ""])
def test_numeric_list_metadata_does_not_relax_opaque_detail_revision(revision):
    payload = timeline_fixture()
    payload["revision"] = revision
    with pytest.raises(SessionError, match="invalid"):
        history_page(payload, session_id=payload["session"]["session_id"], now=1792324800)


def test_numeric_list_headers_keep_retention_deadlines():
    with pytest.raises(SessionError, match="unavailable"):
        history_page(response(3), now=999999999999)


def test_numeric_list_load_more_and_refresh_use_fresh_owner_pages(controller):
    owner, backend = controller
    _, pages = archive_pages(owner)
    pages[0]["sessions"][0]["revision"] = 0
    pages[1]["sessions"][0]["revision"] = 3
    run(owner, backend, "loadHistory")
    assert [r["revision"] for r in owner.state["sessions"]] == [0]
    run(owner, backend, "moreHistory")
    assert [r["revision"] for r in owner.state["sessions"]] == [0, 3]
    pages[0]["sessions"][0]["revision"] = 4
    run(owner, backend, "refreshArchive")
    assert [r["revision"] for r in owner.state["sessions"]] == [4, 3]
    assert all(set(call.kwargs) == {"cursor"} for call in owner.transport.history.call_args_list)
    owner.transport.active.assert_not_called()


def test_numeric_list_header_does_not_authorize_a_late_profile_result(controller):
    owner, backend = controller
    _, pages = archive_pages(owner)
    pages[0]["sessions"][0]["revision"] = 3
    owner.loadHistory()
    work = backend.jobs.pop()
    backend.cfg.active_profile_id = "other-profile"
    work()
    assert not owner.state["sessions"] and not owner.state["history_loaded"]


def test_malformed_numeric_page_withdraws_previous_archive_projection(controller):
    owner, backend = controller
    _, pages = archive_pages(owner)
    pages[0]["sessions"][0]["revision"] = 3
    run(owner, backend, "loadHistory")
    assert owner.state["sessions"]
    pages[0]["sessions"][0]["revision"] = True
    run(owner, backend, "refreshArchive")
    assert not owner.state["sessions"] and owner.state["error"] == "invalid"
