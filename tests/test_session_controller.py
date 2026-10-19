from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from PySide6.QtCore import QCoreApplication, QObject, Signal
from shiboken6 import delete

from djconnect_pi.session_controller import SessionController
from djconnect_pi.session_transport import SessionError


class Backend(QObject):
    demoModeChanged = Signal()
    settingsChanged = Signal()

    def __init__(self):
        super().__init__()
        self.demoMode = False
        self.cfg = SimpleNamespace(paired=True, device_token="fixture-token", ha_url="http://fixture.invalid",
            device_id="fixture-device", explicit_profile_id="profile-a", active_profile_id="profile-a",
            active_profile_type="personal", active_profile_privacy_mode="private", private_session=False, language="nl")
        self.jobs = []
        self._executor = SimpleNamespace(submit=self.jobs.append)


@pytest.fixture
def controller():
    app = QCoreApplication.instance() or QCoreApplication([])
    backend = Backend()
    owner = SessionController(backend)
    owner._deadline_timer.stop()
    owner.transport.active = Mock(return_value={"success": True, "session": None})
    owner.transport.capabilities = Mock(return_value={"success": True,
        "capabilities": {"session_conversation_history": True}, "contract_versions": {"session_history_entries": 2}})
    yield owner, backend
    delete(owner)
    delete(backend)


def test_no_server_call_until_explicit_profile_confirmation(controller):
    owner, backend = controller
    backend.cfg.explicit_profile_id = ""
    owner.refresh()
    assert owner.state["profile_confirmation_required"]
    assert owner.state["error"] == "profile_required"
    assert not backend.jobs
    owner.transport.active.assert_not_called()


def test_invalidating_profile_discards_already_queued_results(controller):
    owner, backend = controller
    owner.refresh()
    old_job = backend.jobs.pop()
    backend.cfg.active_profile_id = "profile-b"
    owner.invalidate()
    old_job()
    assert not owner.state["loaded"] and not owner.state["session_id"]
    assert not owner.busy


def test_same_context_refresh_marks_empty_only_after_success(controller):
    owner, backend = controller
    owner.refresh()
    assert not owner.state["loaded"] and owner.busy
    backend.jobs.pop()()
    assert owner.state["loaded"] and not owner.busy
    assert owner.state["history_available"] and not owner.state["session_id"]


def test_uncertain_write_never_replays_or_retains_old_current_cards(controller):
    owner, backend = controller
    owner._session = {"session_id": "s1"}
    owner._moments = [{"body": "old current text"}]
    owner.transport.end = Mock(side_effect=SessionError("uncertain"))
    owner.end("s1")
    owner.end("s1")
    assert len(backend.jobs) == 1
    backend.jobs.pop()()
    assert owner.state["error"] == "uncertain"
    assert owner.state["moments"] == [] and not owner.state["session_id"]
    owner.transport.end.assert_called_once()
    owner.transport.active.assert_not_called()


def test_expired_history_is_removed_without_waiting_for_a_network_read(controller):
    owner, _ = controller
    owner._timeline = {"entries": [{"entry_id": "expired", "retained_until": "2000-01-01T00:00:00Z"},
        {"entry_id": "retained", "retained_until": "9999-01-01T00:00:00Z"}]}
    owner._expire()
    assert [row["entry_id"] for row in owner.state["timeline"]["entries"]] == ["retained"]


def test_demo_session_never_uses_server_or_survives_demo_exit(controller):
    owner, backend = controller
    backend.demoMode = True
    backend.demoModeChanged.emit()
    assert owner.state["session_id"] == "demo-session"
    owner.end("demo-session")
    assert owner.state["loaded"] and not owner.state["session_id"]
    owner.start("party")
    assert owner.state["mood"] == "party"
    assert not backend.jobs
    owner.transport.active.assert_not_called()
    backend.demoMode = False
    backend.demoModeChanged.emit()
    assert not owner.state["session_id"] and not owner.state["loaded"]


def enable_search(owner):
    owner._caps = {'capabilities': {'session_conversation_history': True, 'session_flow_text_search': True},
        'contract_versions': {'session_history_entries': 2, 'session_flow_text_search': 1}}


def test_search_requires_advertised_capability(controller):
    owner, backend = controller
    owner.search('saved', 'synthetic')
    assert not backend.jobs
    assert owner.state['error'] == 'unsupported'


def test_leaving_history_discards_delayed_search_without_erasing_active_session(controller):
    from test_session_history_view import search_fixture
    owner, backend = controller
    enable_search(owner)
    data = search_fixture()
    owner._session = {'session_id': 'current-session'}
    owner.transport.search = Mock(return_value=data)
    owner.search(data['session_id'], data['query'])
    work = backend.jobs.pop()
    owner.closeSaved()
    work()
    assert owner.state['search'] == {}
    assert owner.state['session_id'] == 'current-session'
    assert not owner.busy


def test_open_result_uses_navigation_then_anchor_without_mutating_runtime(controller):
    from test_session_history_view import timeline_fixture
    owner, backend = controller
    enable_search(owner)
    tail = timeline_fixture()
    row = tail['entries'][0]
    owner._session = {'session_id':'current-session'}
    owner.transport.open_entry = Mock(return_value={
        'success':True,'schema_version':2,'history_contract_version':2,
        'session':tail['session'],'entry':row,'read_only':True,'navigation_only':True})
    owner.transport.timeline = Mock(return_value=tail)
    owner.transport.start = Mock()
    owner.transport.end = Mock()
    signal = Mock()
    owner.entryOpened.connect(signal)
    owner.openEntry(row['session_id'], row['entry_id'])
    backend.jobs.pop()()
    assert owner.state['session_id'] == 'current-session'
    assert owner.state['timeline']['selected_entry_id'] == row['entry_id']
    assert owner.transport.timeline.call_args.kwargs == {'window':'anchor','anchor_entry_id':row['entry_id']}
    owner.transport.start.assert_not_called()
    owner.transport.end.assert_not_called()
    signal.assert_called_once()


def test_unavailable_history_cannot_end_or_replace_current_session(controller):
    owner, backend = controller
    enable_search(owner)
    owner._session = {'session_id':'current-session'}
    owner.transport.search = Mock(side_effect=SessionError('unavailable'))
    owner.search('saved-session', 'some question')
    backend.jobs.pop()()
    assert owner.state['error'] == 'unavailable'
    assert owner.state['session_id'] == 'current-session'
