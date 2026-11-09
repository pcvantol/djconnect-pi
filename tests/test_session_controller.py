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
        self._session_executor = self._executor
        self._question_executor = self._executor


@pytest.fixture
def controller():
    _app = QCoreApplication.instance() or QCoreApplication([])
    backend = Backend()
    owner = SessionController(backend)
    owner._deadline_timer.stop()
    owner.transport.private_scope_owner = Mock(return_value=None)
    owner.transport.active = Mock(return_value={"success": True, "session": None})
    owner.transport.capabilities = Mock(return_value={"success": True,
        "capabilities": {"session_conversation_history": True}, "contract_versions": {"session_history_entries": 2}})
    yield owner, backend
    owner.shutdownImages()
    delete(owner)
    delete(backend)


def test_missing_metadata_permits_only_bounded_current_owner_read(controller):
    owner, backend = controller
    backend.cfg.explicit_profile_id = ""
    backend.cfg.active_profile_id = ""
    owner.refresh()
    assert owner.state["profile_confirmation_required"]
    assert len(backend.jobs) == 1
    backend.jobs.pop()()
    assert owner.state["error"] == "profile_required"
    owner.transport.active.assert_called_once()
    assert owner.transport.active.call_args.kwargs == {"isolated": True}
    owner.transport.capabilities.assert_not_called()
    assert backend.cfg.active_profile_id == backend.cfg.explicit_profile_id == ""


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
    assert owner.state["loaded"] and not owner.state["session_id"]
    owner.setDemoPreference("persona", "festival_dj")
    owner.setDemoPreference("presence", "occasional")
    owner.start("chill")
    assert owner.state["session_id"] == "demo-session"
    assert owner.state["persona"] == "festival_dj"
    assert owner.state["presence"] == "occasional"
    owner.setDemoPreference("mood", "energy")
    assert owner.state["mood"] == "energy"
    positioned = []
    owner.questionConfirmed.connect(positioned.append)
    assert owner.sendQuestion("What should I listen to next?")
    owner._expire()
    assert positioned == [owner.state["flow_rows"][0]["contribution"]["entry_id"]]
    assert [row["contribution"]["kind"] for row in owner.state["flow_rows"]] == [
        "conversation_dj", "conversation_user", "dj_moment",
    ]
    owner.end("demo-session")
    assert not owner.state["flow_rows"] and not owner.sendQuestion("No session")
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


def test_timeline_pages_replace_window_and_reject_changed_revision(controller):
    from copy import deepcopy

    from test_session_history_view import timeline_fixture
    owner, backend = controller
    enable_search(owner)
    tail = timeline_fixture()
    owner._timeline = deepcopy(tail)
    first = deepcopy(tail)
    first['entries'] = first['entries'][:2]
    first['next_cursor'] = 'opaque-page-two'
    owner.transport.timeline = Mock(return_value=first)
    owner.firstEntries()
    backend.jobs.pop()()
    assert owner.transport.timeline.call_args.kwargs == {'window': None, 'cursor': ''}
    assert len(owner.state['timeline']['entries']) == 2
    second = deepcopy(tail)
    second['entries'] = second['entries'][2:]
    owner.transport.timeline.return_value = second
    owner.nextEntries()
    backend.jobs.pop()()
    assert owner.transport.timeline.call_args.kwargs == {'window': None, 'cursor': 'opaque-page-two'}
    assert [row['entry_id'] for row in owner.state['timeline']['entries']] == [row['entry_id'] for row in second['entries']]  # no unvalidated prior-page cache
    owner._timeline['next_cursor'] = 'opaque-page-three'
    second['revision'] = 'changed-revision'
    owner.nextEntries()
    backend.jobs.pop()()
    assert owner.state['error'] == 'conflict'
    assert owner.state['timeline'] == {}


def test_refresh_revalidates_reading_anchor_and_withdraws_old_body_and_search(controller):
    from copy import deepcopy

    from test_session_history_view import timeline_fixture
    owner, backend = controller
    enable_search(owner)
    tail = timeline_fixture()
    row = next(row for row in tail['entries'] if row['kind'] == 'dj_moment')
    owner._timeline = deepcopy(tail)
    owner._search = {'matches': [deepcopy(row)]}
    refreshed = deepcopy(tail)
    withdrawn = next(entry for entry in refreshed['entries'] if entry['entry_id'] == row['entry_id'])
    withdrawn.update(kind='dj_publication', text=None, speech_available=False)
    refreshed['revision'] = 'withdrawal-revision'
    owner.transport.timeline = Mock(return_value=refreshed)
    signal = Mock()
    owner.timelineUpdated.connect(signal)
    owner.refreshSaved(row['entry_id'])
    backend.jobs.pop()()
    assert owner.transport.timeline.call_args.kwargs == {'window': 'anchor', 'anchor_entry_id': row['entry_id']}
    updated = next(entry for entry in owner.state['timeline']['entries'] if entry['entry_id'] == row['entry_id'])
    assert updated['kind'] == 'dj_publication' and updated['text'] is None
    assert owner.state['search'] == {}
    signal.assert_called_once_with(row['entry_id'])


def test_history_refresh_failure_clears_stale_prose_but_keeps_runtime(controller):
    from test_session_history_view import timeline_fixture
    owner, backend = controller
    enable_search(owner)
    owner._timeline = timeline_fixture()
    owner._session = {'session_id': 'active-runtime'}
    owner.transport.timeline = Mock(side_effect=SessionError('unavailable'))
    owner.refreshSaved(owner._timeline['entries'][0]['entry_id'])
    backend.jobs.pop()()
    assert owner.state['timeline'] == {}
    assert owner.state['session_id'] == 'active-runtime'


def test_context_closed_discards_inflight_revalidated_window(controller):
    from test_session_history_view import timeline_fixture
    owner, backend = controller
    enable_search(owner)
    tail = timeline_fixture()
    owner._timeline = tail
    owner.transport.timeline = Mock(return_value=tail)
    owner.refreshSaved(tail['entries'][0]['entry_id'])
    owner.closeSaved()
    backend.jobs.pop()()
    assert owner.state['timeline'] == {}


def test_paged_history_revalidation_keeps_forward_cursor_without_caching_previous_pages(controller):
    from test_session_history_view import timeline_fixture
    owner, backend = controller
    enable_search(owner)
    tail = timeline_fixture()
    tail['_page_cursor'] = 'current-page'
    tail['next_cursor'] = 'next-page'
    owner._timeline = tail
    owner.transport.timeline = Mock(return_value=tail)
    owner.refreshSaved(tail['entries'][0]['entry_id'])
    backend.jobs.pop()()
    assert owner.transport.timeline.call_args.kwargs == {'window': None, 'cursor': 'current-page'}
    assert owner.state['timeline']['next_cursor'] == 'next-page'
    assert owner.state['timeline']['_page_cursor'] == 'current-page'


def test_revoked_page_cursor_falls_back_to_fresh_anchor_without_replaying_actions(controller):
    from test_session_history_view import timeline_fixture
    owner, backend = controller
    enable_search(owner)
    tail = timeline_fixture()
    owner._timeline = {**tail, '_page_cursor': 'old-page'}
    owner.transport.timeline = Mock(side_effect=[SessionError('conflict'), tail])
    anchor = tail['entries'][0]['entry_id']
    owner.refreshSaved(anchor)
    backend.jobs.pop()()
    assert owner.transport.timeline.call_count == 2
    assert owner.transport.timeline.call_args.kwargs == {'window': 'anchor', 'anchor_entry_id': anchor}
    assert '_page_cursor' not in owner.state['timeline']
    assert owner.state['error'] == ''


def test_capability_withdrawal_clears_historical_prose_and_cursor(controller):
    from test_session_history_view import timeline_fixture
    owner, backend = controller
    enable_search(owner)
    owner._timeline = timeline_fixture()
    owner._search = {'matches': [{'text': 'private saved query result'}]}
    owner._sessions = [{'session_id': 'saved'}]
    owner._history_cursor = 'old-list-page'
    owner._history_loaded = True
    owner.transport.capabilities.return_value = {'capabilities': {}, 'contract_versions': {}}
    owner.refresh()
    backend.jobs.pop()()
    assert owner.state['timeline'] == {} and owner.state['search'] == {}
    assert owner.state['sessions'] == [] and not owner.state['has_more_sessions']
    assert not owner.state['history_loaded']


def clock_fixture(owner):
    from djconnect_pi.expiry_clock import ExpiryClock
    from djconnect_pi.session_projection import timestamp
    host = SimpleNamespace(wall=timestamp('2026-10-20T00:00:00Z'), tick=0)
    owner._clock = ExpiryClock(lambda: host.wall, lambda: host.tick)
    return host


def test_screen_wake_is_only_for_fresh_current_contributions_in_the_same_scope(controller):
    from test_session_projection import live_fixture

    owner, backend = controller
    host = clock_fixture(owner)
    data = live_fixture()
    wire = data["broadcast"]
    wire["session"] = {"session_id": data["session_id"]}
    row = wire["dj_moments"][0]
    grant = wire["native_delivery"]["admissions"][0]
    row["created_at"] = "2026-10-19T23:59:58Z"
    wakes = []
    owner.newCurrentContribution.connect(lambda: wakes.append(True))
    owner.transport.active.return_value = {"success": True, "session": data}

    def refresh():
        owner.refresh()
        backend.jobs.pop()()

    refresh()
    assert wakes == []
    host.tick = 8
    row.update(moment_id="m2", created_at="2026-10-20T00:00:07Z")
    grant["moment_id"] = "m2"
    wire["native_delivery"]["current_moment_id"] = "m2"
    refresh()
    refresh()
    assert wakes == [True]
    wire["native_delivery"]["current_moment_id"] = None
    refresh()
    wire["native_delivery"]["current_moment_id"] = "m2"
    refresh()
    assert wakes == [True]
    host.tick = 80
    row.update(moment_id="m3", created_at="2026-10-20T00:00:09Z")
    grant["moment_id"] = "m3"
    wire["native_delivery"]["current_moment_id"] = "m3"
    refresh()
    owner.invalidate()
    refresh()
    assert wakes == [True]


def test_clock_rollback_cannot_revive_current_or_source_expired_flow_on_refresh(controller):
    from test_session_projection import live_fixture
    owner, backend = controller
    host = clock_fixture(owner)
    data = live_fixture()
    grant = data['broadcast']['native_delivery']['admissions'][0]
    grant.update(display_expires_at='2026-10-20T00:00:03Z', source_expires_at='2026-10-20T00:00:05Z')
    data['broadcast']['session'] = {'session_id': data['session_id']}
    owner.transport.active.return_value = {'success': True, 'session': data}
    owner.refresh()
    backend.jobs.pop()()
    assert owner.state['moments'][0]['body'] == 'Confirmed body'
    host.tick = 4
    host.wall -= 3600
    owner._expire()
    assert owner.state['moments'] == []
    owner.refresh()  # same wire deadline, never a new lease
    backend.jobs.pop()()
    assert owner.state['moments'] == []
    data['broadcast']['native_delivery']['current_moment_id'] = None
    owner.refresh()
    backend.jobs.pop()()
    assert owner.state['moments'][0]['current'] is False  # original source still valid for Flow
    host.tick = 6
    owner._expire()
    assert owner.state['moments'] == []
    owner.refresh()
    backend.jobs.pop()()
    assert owner.state['moments'] == []


def test_rolled_back_clock_rejects_refetched_history_and_search_after_retention(controller):
    from test_session_history_view import search_fixture, timeline_fixture
    owner, backend = controller
    host = clock_fixture(owner)
    enable_search(owner)
    tail = timeline_fixture()
    for row in tail['entries']:
        row['retained_until'] = '2026-10-20T00:00:05Z'
    owner.transport.timeline = Mock(return_value=tail)
    sid = tail['session']['session_id']
    owner.openSaved(sid)
    backend.jobs.pop()()
    assert owner.state['timeline']['entries']
    query = search_fixture()
    query['matches'][0]['retained_until'] = '2026-10-20T00:00:05Z'
    owner.transport.search = Mock(return_value=query)
    owner.search(sid, query['query'])
    backend.jobs.pop()()
    assert owner.state['search']['matches']
    host.tick = 6
    host.wall -= 3600
    owner._expire()
    assert not owner.state['timeline']['entries'] and not owner.state['search']
    owner.openSaved(sid)
    backend.jobs.pop()()
    assert owner.state['timeline'] == {} and owner.state['error'] == 'unavailable'
    owner.search(sid, query['query'])
    backend.jobs.pop()()
    assert owner.state['search'] == {} and owner.state['error'] == 'unavailable'


def test_gui_queue_delay_cannot_present_expired_historical_response(controller):
    from test_session_history_view import timeline_fixture
    owner, backend = controller
    host = clock_fixture(owner)
    enable_search(owner)
    tail = timeline_fixture()
    for row in tail['entries']:
        row['retained_until'] = '2026-10-20T00:00:05Z'
    owner.transport.timeline = Mock(return_value=tail)
    pending = []
    owner._ready.disconnect(owner._apply)
    owner._ready.connect(pending.append)
    owner.openSaved(tail['session']['session_id'])
    backend.jobs.pop()()
    assert pending[0]['timeline']['entries']
    host.tick = 6
    host.wall -= 3600
    owner._apply(pending[0])
    assert not owner.state['timeline']['entries']


def test_background_clears_authority_and_late_results_resume_with_read_only(controller):
    owner, backend = controller
    owner._session = {'session_id': 'server-session'}
    owner._moments = [{'body': 'private live body'}]
    owner._timeline = {'entries': [{'text': 'private retained body'}]}
    owner.refresh()
    old_job = backend.jobs.pop()
    owner.setForeground(False)
    assert not owner.state['session_id'] and not owner.state['moments'] and not owner.state['timeline']
    old_job()
    assert not owner.state['loaded']
    owner.start('party')
    owner.refresh()
    assert not backend.jobs  # no refresh or writes while backgrounded
    owner.setForeground(True)
    assert len(backend.jobs) == 1
    backend.jobs.pop()()
    owner.transport.active.assert_called()  # only fresh current read, no replayed start/end
    assert owner.state['loaded']


@pytest.mark.parametrize('language', ['en', 'nl', 'de', 'fr', 'es'])
def test_history_dates_are_localized_and_equivalent_offsets_show_same_instant(controller, language):
    owner, backend = controller
    backend.cfg.language = language
    formatted = owner.formatTimestamp('2026-10-18T12:34:00Z')
    assert formatted == owner.formatTimestamp('2026-10-18T14:34:00+02:00')
    assert '2026' in formatted and '·' in formatted
    assert '2026-10-18' not in formatted and 'T12:34' not in formatted
    assert owner.formatTimestamp('2026-10-18T12:34:00') == ''  # no guessed timezone
    assert owner.formatTimestamp('not-a-date') == ''


def paged_timeline(owner):
    from copy import deepcopy

    from test_session_history_view import timeline_fixture
    enable_search(owner)
    clock_fixture(owner)
    original = timeline_fixture()
    pages = []
    for index in range(3):
        page = deepcopy(original)
        page.pop('window', None)
        page.pop('anchor_entry_id', None)
        page['entries'] = page['entries'][index*2:index*2+2]
        page['next_cursor'] = f'page-{index+1}' if index < 2 else None
        pages.append(page)
    def read(binding, sid, **kwargs):
        cursor = kwargs.get('cursor', '')
        return deepcopy(pages[int(cursor[-1])] if cursor else pages[0])
    owner.transport.timeline = Mock(side_effect=read)
    owner._timeline = deepcopy(original)
    owner.firstEntries()
    return pages


def test_previous_page_is_a_fresh_server_read_with_no_retained_body_cache(controller):
    owner, backend = controller
    pages = paged_timeline(owner)
    backend.jobs.pop()()
    owner.nextEntries(); backend.jobs.pop()()
    owner.nextEntries(); backend.jobs.pop()()
    assert owner.state['has_previous_entries']
    assert owner._timeline_trail == [{'window':None,'cursor':''},{'window':None,'cursor':'page-1'}]
    owner.previousEntries(); backend.jobs.pop()()
    assert owner.transport.timeline.call_args.kwargs == {'window':None,'cursor':'page-1'}
    assert owner.state['timeline']['entries'][0]['entry_id'] == pages[1]['entries'][0]['entry_id']
    owner.previousEntries(); backend.jobs.pop()()
    assert owner.transport.timeline.call_args.kwargs == {'window':None,'cursor':''}
    assert not owner.state['has_previous_entries']


@pytest.mark.parametrize('changed_revision', [False, True])
def test_stale_previous_page_uses_fresh_visible_anchor_and_forgets_old_trail(controller, changed_revision):
    from copy import deepcopy
    owner, backend = controller
    pages = paged_timeline(owner)
    backend.jobs.pop()()
    owner.nextEntries(); backend.jobs.pop()()
    owner.nextEntries(); backend.jobs.pop()()
    anchor = pages[2]['entries'][1]['entry_id']
    fresh = deepcopy(pages[2]); fresh['revision'] = 'new-server-revision'
    fresh.update(window='anchor', anchor_entry_id=anchor)
    old_page = deepcopy(pages[1]); old_page['revision'] = 'different-revision'
    owner.transport.timeline.side_effect = [old_page if changed_revision else SessionError('conflict'), fresh]
    owner.previousEntries(anchor); backend.jobs.pop()()
    assert owner.transport.timeline.call_args.kwargs == {'window':'anchor','anchor_entry_id':anchor}
    assert owner.state['timeline']['revision'] == 'new-server-revision'
    assert not owner.state['has_previous_entries']


def test_withdrawn_previous_target_clears_prose_and_old_navigation(controller):
    owner, backend = controller
    paged_timeline(owner); backend.jobs.pop()()
    owner.nextEntries(); backend.jobs.pop()()
    owner.transport.timeline.side_effect = SessionError('unavailable')
    owner.previousEntries(); backend.jobs.pop()()
    assert owner.state['timeline'] == {} and not owner.state['has_previous_entries']


@pytest.mark.parametrize('withdrawal', ['close', 'background', 'profile'])
def test_late_previous_page_cannot_restore_a_closed_or_changed_context(controller, withdrawal):
    owner, backend = controller
    paged_timeline(owner); backend.jobs.pop()()
    owner.nextEntries(); backend.jobs.pop()()
    owner.previousEntries()
    work = backend.jobs.pop()
    if withdrawal == 'close':
        owner.closeSaved()
    elif withdrawal == 'background':
        owner.setForeground(False)
    else:
        backend.cfg.active_profile_id = 'another-owner'
        owner.invalidate()
    work()
    assert owner.state['timeline'] == {} and not owner.state['has_previous_entries']


def test_first_page_and_capability_withdrawal_forget_previous_navigation(controller):
    owner, backend = controller
    paged_timeline(owner); backend.jobs.pop()()
    owner.nextEntries(); backend.jobs.pop()()
    owner.firstEntries(); backend.jobs.pop()()
    assert not owner.state['has_previous_entries']
    owner.nextEntries(); backend.jobs.pop()()
    owner.transport.capabilities.return_value = {'capabilities':{},'contract_versions':{}}
    owner.refresh(); backend.jobs.pop()()
    assert not owner.state['has_previous_entries'] and owner.state['timeline'] == {}


def test_previous_cursor_fallback_refuses_a_missing_visible_anchor(controller):
    from copy import deepcopy
    owner, backend = controller
    pages = paged_timeline(owner); backend.jobs.pop()()
    owner.nextEntries(); backend.jobs.pop()()
    missing = deepcopy(pages[0])
    owner.transport.timeline.side_effect = [SessionError('conflict'), missing]
    owner.previousEntries(); backend.jobs.pop()()
    assert owner.state['timeline'] == {} and not owner.state['has_previous_entries']
    assert owner.state['error'] == 'unavailable'


def test_previous_page_restores_only_a_fresh_retained_reading_identity(controller):
    owner, backend = controller
    pages = paged_timeline(owner); backend.jobs.pop()()
    entry_id = pages[0]['entries'][0]['entry_id']
    positioned = Mock(); owner.timelinePositioned.connect(positioned)
    owner.nextEntries(entry_id, -73.5); backend.jobs.pop()()
    assert owner._timeline_trail[0]['reading'] == {'entry_id': entry_id, 'offset': -73.5}
    owner.previousEntries(); backend.jobs.pop()()
    assert owner.transport.timeline.call_args.kwargs == {'window': None, 'cursor': ''}
    positioned.assert_called_once_with(entry_id, -73.5)
    assert not owner._timeline_trail


@pytest.mark.parametrize('offset', [float('nan'), float('inf'), True, 1_000_001])
def test_invalid_reading_offsets_are_not_retained(controller, offset):
    owner, backend = controller
    pages = paged_timeline(owner); backend.jobs.pop()()
    owner.nextEntries(pages[0]['entries'][0]['entry_id'], offset); backend.jobs.pop()()
    assert 'reading' not in owner._timeline_trail[0]


def test_missing_previous_reading_entry_is_not_repositioned(controller):
    owner, backend = controller
    pages = paged_timeline(owner); backend.jobs.pop()()
    entry_id = pages[0]['entries'][0]['entry_id']
    owner.nextEntries(entry_id, -50); backend.jobs.pop()()
    pages[0]['entries'] = pages[0]['entries'][1:]
    positioned = Mock(); owner.timelinePositioned.connect(positioned)
    owner.previousEntries(); backend.jobs.pop()()
    positioned.assert_not_called()
    assert all(row['entry_id'] != entry_id for row in owner.state['timeline']['entries'])


def test_previous_revision_fallback_discards_old_pixel_position(controller):
    from copy import deepcopy
    owner, backend = controller
    pages = paged_timeline(owner); backend.jobs.pop()()
    owner.nextEntries(pages[0]['entries'][0]['entry_id'], -50); backend.jobs.pop()()
    anchor = pages[1]['entries'][0]['entry_id']
    fresh = deepcopy(pages[1]); fresh.update(revision='fresh-revision', window='anchor', anchor_entry_id=anchor)
    owner.transport.timeline.side_effect = [SessionError('conflict'), fresh]
    positioned = Mock(); owner.timelinePositioned.connect(positioned)
    owner.previousEntries(anchor); backend.jobs.pop()()
    positioned.assert_not_called()
    assert not owner._timeline_trail


def test_forecast_uses_captured_active_read_and_expires_before_gui_state(controller):
    from test_session_forecast import CAPS, FRAMES, session
    owner, backend = controller
    frame = FRAMES[0]; clock = [frame['now']]
    owner._clock = SimpleNamespace(now=lambda: clock[0])
    owner.transport.capabilities = Mock(return_value=CAPS)
    owner.transport.active = Mock(return_value={'success': True, 'session': session(frame)})
    owner.refresh(); backend.jobs.pop()()
    assert owner.state['forecast_supported'] and owner.state['forecast']['sections']
    notified = Mock(); owner.changed.connect(notified)
    clock[0] += 120
    assert not owner.state['forecast']['sections']
    assert owner.state['forecast']['state'] == 'expired'
    owner._expire()
    notified.assert_called_once()  # A GUI getter must not swallow the timer notification.
    owner.setForeground(False)
    assert not owner.state['forecast_supported'] and not owner.state['forecast']['sections']


def test_empty_view_clears_keep_ticket_fence_without_recursive_gui_notification(controller):
    owner, _backend = controller
    notified = Mock(); owner.changed.connect(notified)
    before = owner._view_epoch
    owner.clearSelection(); owner.clearSearch()
    assert owner._view_epoch == before + 1
    notified.assert_not_called()
    owner._search = {'matches': []}
    owner.clearSearch()
    assert owner._search == {} and owner._view_epoch == before + 2
    notified.assert_called_once()


def search_pages(count=2):
    from copy import deepcopy

    from test_session_history_view import search_fixture
    seed = search_fixture()
    pages = []
    for i in range(count):
        page = deepcopy(seed)
        page["matches"][0].update(entry_id=f"synthetic-search-{i}", order=i+1)
        page.update(complete=i==count-1, next_cursor=f"cursor-{i+1}" if i<count-1 else None,
            total_count=None)
        pages.append(page)
    return pages


def test_search_more_revalidates_previous_pages_and_refresh_withdraws_old_body(controller):
    from copy import deepcopy
    owner, backend = controller
    enable_search(owner)
    pages = search_pages()
    owner.transport.search = Mock(side_effect=lambda binding,sid,q,**kw: deepcopy(pages[0 if not kw['cursor'] else 1]))
    owner.search(pages[0]['session_id'], pages[0]['query']);backend.jobs.pop()()
    owner.moreSearch();backend.jobs.pop()()
    assert owner.transport.search.call_count == 3  # first page is re-read, never body-appended.
    assert len(owner.state['search']['matches']) == 2 and owner.state['search']['_pages'] == 2
    assert [call.kwargs['cursor'] for call in owner.transport.search.call_args_list] == ['', '', 'cursor-1']
    pages[0]['matches'][0]['text'] = 'Fresh server body retained on revalidation'
    pages[1]['matches'] = [];pages[1]['returned_count'] = 0
    owner.refreshSearch();backend.jobs.pop()()
    assert [row['text'] for row in owner.state['search']['matches']] == ['Fresh server body retained on revalidation']
    assert owner.state['search']['complete'] is True


@pytest.mark.parametrize('failure', ['revision','duplicate_id','order','cycle','denied'])
def test_search_revalidation_refuses_mixed_or_revoked_pages(controller, failure):
    owner, backend = controller
    enable_search(owner)
    pages = search_pages()
    owner.transport.search = Mock(return_value=pages[0])
    owner.search(pages[0]['session_id'], pages[0]['query']);backend.jobs.pop()()
    assert owner.state['search']['matches']
    if failure == 'revision': pages[1]['revision'] = 'different-revision'
    if failure == 'duplicate_id': pages[1]['matches'][0]['entry_id'] = pages[0]['matches'][0]['entry_id']
    if failure == 'order': pages[1]['matches'][0]['order'] = pages[0]['matches'][0]['order']
    if failure == 'cycle': pages[1].update(complete=False,next_cursor='cursor-1')
    owner.transport.search = Mock(side_effect=[pages[0], SessionError('denied') if failure=='denied' else pages[1]])
    owner.moreSearch();backend.jobs.pop()()
    assert owner.state['search'] == {}
    assert owner.state['error'] == ('denied' if failure=='denied' else 'conflict' if failure=='revision' else 'invalid')


def test_search_scan_bound_is_partial_and_new_query_resets_budget(controller):
    owner, backend = controller
    enable_search(owner)
    pages = search_pages(6)
    owner.transport.search = Mock(side_effect=lambda binding,sid,q,**kw: pages[int(kw['cursor'].split('-')[-1]) if kw['cursor'] else 0])
    owner.search(pages[0]['session_id'], pages[0]['query']);backend.jobs.pop()()
    for _ in range(4): owner.moreSearch();backend.jobs.pop()()
    assert owner.state['search']['_pages'] == 5 and owner.state['search_limit_reached']
    assert not owner.state['search']['complete'] and len(owner.state['search']['matches']) == 5
    before = owner.transport.search.call_count
    owner.moreSearch()
    assert not backend.jobs and owner.transport.search.call_count == before
    owner.refreshSearch();backend.jobs.pop()()
    assert owner.transport.search.call_count == before+5
    owner.search(pages[0]['session_id'], pages[0]['query']);backend.jobs.pop()()
    assert owner.state['search']['_pages'] == 1 and not owner.state['search_limit_reached']


def test_search_refresh_cancelled_before_dispatch_does_not_send_private_query(controller):
    owner, backend = controller
    enable_search(owner)
    data = search_pages()[0]
    owner.transport.search = Mock(return_value=data)
    owner.search(data['session_id'],data['query']);backend.jobs.pop()()
    owner.refreshSearch();job=backend.jobs.pop()
    owner.clearSearch();before=owner.transport.search.call_count
    job()
    assert owner.transport.search.call_count==before and not owner.state['search']


def test_same_revision_history_poll_keeps_search_but_revision_change_withdraws_it(controller):
    from copy import deepcopy

    from test_session_history_view import search_fixture, timeline_fixture
    owner, backend = controller
    enable_search(owner)
    data, tail = search_fixture(), timeline_fixture()
    owner._timeline = deepcopy(tail)
    owner.transport.search = Mock(return_value=data)
    owner.search(data['session_id'],data['query']);backend.jobs.pop()()
    owner.transport.timeline = Mock(return_value=tail)
    owner.refreshSaved(tail['entries'][0]['entry_id']);backend.jobs.pop()()
    assert owner.state['search']['query']==data['query']
    tail['revision']='new-history-revision'
    owner.refreshSaved(tail['entries'][0]['entry_id']);backend.jobs.pop()()
    assert owner.state['search']=={}


def test_withdrawn_search_between_pages_stops_additional_private_reads(controller):
    owner, backend = controller
    enable_search(owner)
    pages = search_pages()
    owner.transport.search = Mock(return_value=pages[0])
    owner.search(pages[0]['session_id'],pages[0]['query']);backend.jobs.pop()()
    def withdraw_after_first(*args, **kwargs):
        owner.clearSearch()
        return pages[0]
    owner.transport.search = Mock(side_effect=withdraw_after_first)
    owner.moreSearch();backend.jobs.pop()()
    assert owner.transport.search.call_count==1 and not owner.state['search']


@pytest.mark.parametrize('scope',['mood','persona','playback'])
def test_current_reads_with_new_runtime_scope_require_a_new_forecast_revision(controller,scope):
    from copy import deepcopy

    from test_session_forecast import CAPS, FRAMES, session
    owner,backend=controller;frame=FRAMES[0]
    owner._clock=SimpleNamespace(now=lambda:frame['now'])
    current=session(frame)
    owner.transport.capabilities=Mock(return_value=CAPS)
    owner.transport.active=Mock(return_value={'success':True,'session':current})
    owner.refresh();backend.jobs.pop()()
    assert owner.state['forecast']['sections']
    changed=deepcopy(current)
    if scope=='mood': changed.update(selected_mood='party',mood_revision=1)
    if scope=='persona': changed.update(dj_persona='club_dj',persona_revision=1)
    if scope=='playback':
        changed['broadcast']['playback']['item_id']='new-current-item'
        changed['broadcast']['session_forecast']['current_anchor']['item_id']='new-current-item'
    owner.transport.active.return_value={'success':True,'session':changed}
    owner.refresh();backend.jobs.pop()()
    assert not owner.state['forecast']['sections']
    changed['broadcast']['session_forecast']['revision']+=1
    owner.refresh();backend.jobs.pop()()
    assert owner.state['forecast']['sections']


def test_server_mapped_profile_opens_session_without_second_confirmation(controller):
    owner, backend = controller
    backend.cfg.explicit_profile_id = ""
    owner.refresh()
    assert not owner.state["profile_confirmation_required"]
    assert len(backend.jobs) == 1
    backend.jobs.pop()()
    assert owner.state["loaded"] and not owner.state["session_id"]
    owner.transport.active.assert_called_once()
    assert owner.transport.active.call_args.args[0].profile_id == "profile-a"
    assert backend.cfg.explicit_profile_id == ""  # No local mapping/selection write.


def test_conflicting_local_selection_cannot_silently_choose_another_profile(controller):
    owner, backend = controller
    backend.cfg.explicit_profile_id = "different-profile"
    owner.refresh()
    assert owner.state["error"] == "profile_required"
    assert not backend.jobs
    owner.transport.active.assert_not_called()


@pytest.mark.parametrize("active", [None, True, 3, [], {}, " profile-a", "profile-a ", "profile\x00a", "profile\x7fa", "x" * 513])
def test_invalid_server_mapping_cannot_open_session(controller, active):
    owner, backend = controller
    backend.cfg.explicit_profile_id = ""
    backend.cfg.active_profile_id = active
    owner.refresh()
    assert owner.state["error"] == "profile_required"
    assert not backend.jobs
    owner.transport.active.assert_not_called()


def test_mapping_change_rejects_old_automatic_entry_read(controller):
    owner, backend = controller
    backend.cfg.explicit_profile_id = ""
    owner.refresh()
    job = backend.jobs.pop()
    backend.cfg.active_profile_id = "successor"
    job()
    assert not owner.state["loaded"] and not owner.state["session_id"]


def test_automatic_mapping_is_only_read_until_explicit_start(controller):
    owner, backend = controller
    backend.cfg.explicit_profile_id = ""
    owner.transport.start = Mock()
    owner.refresh()
    backend.jobs.pop()()
    owner.transport.start.assert_not_called()
    assert backend.cfg.explicit_profile_id == ""


def test_server_mapped_active_session_is_shown_without_onboarding(controller):
    owner, backend = controller
    backend.cfg.explicit_profile_id = ""
    owner.transport.active.return_value = {"success": True, "session": {"session_id": "already-active", "runtime_state": "active", "broadcast": {"session": {"session_id": "already-active"}}}}
    owner.transport.capabilities.return_value = {"success": True, "capabilities": {}, "contract_versions": {}}
    owner.refresh()
    backend.jobs.pop()()
    assert owner.state["loaded"] and owner.state["session_id"] == "already-active"
    assert not owner.state["profile_confirmation_required"]
    assert not backend.cfg.explicit_profile_id


# Fresh paired clients receive no legacy resolved_profile in current Core status.
# A current Session owner is a read/display witness, not a Profile/privacy grant.
def _missing_metadata(owner, backend, profile="profile-server", sid="active-server"):
    backend.cfg.active_profile_id = backend.cfg.explicit_profile_id = ""
    owner.transport.active.return_value = {"success": True, "session": {
        "session_id": sid, "owner_profile_id": profile, "runtime_state": "active",
        "broadcast": {"session": {"session_id": sid}}}}


def test_paired_current_owner_displays_without_guessing_profile_or_private_rights(controller):
    owner, backend = controller
    _missing_metadata(owner, backend)
    cfg_before = vars(backend.cfg).copy()
    owner.transport.timeline = Mock()
    owner.refresh(); backend.jobs.pop()()
    state = owner.state
    assert state["loaded"] and state["session_id"] == "active-server"
    assert state["owner_profile_id"] == "profile-server" and state["owner_read_only"]
    assert not state["profile_confirmation_required"] and not state["error"]
    assert not state["composer_available"] and not state["history_available"]
    assert not state["playback_control"]["available"]
    assert vars(backend.cfg) == cfg_before
    owner.transport.timeline.assert_not_called()


@pytest.mark.parametrize("bad", [None, True, 3, [], {}, "", " profile-a", "profile-a ", "a\x00b", "a\x7fb", "x" * 513])
def test_bootstrap_rejects_missing_or_malformed_owner(controller, bad):
    owner, backend = controller
    _missing_metadata(owner, backend, bad)
    owner.refresh(); backend.jobs.pop()()
    assert not owner.state["session_id"] and owner.state["profile_confirmation_required"]
    assert owner.state["error"] == "invalid"
    owner.transport.capabilities.assert_not_called()


@pytest.mark.parametrize("action,value", [("start", "groove"), ("end", "active-server"), ("history", ""), ("timeline", "active-server"), ("search", {})])
def test_owner_witness_never_enables_writes_or_archive_intents(controller, action, value):
    owner, backend = controller
    _missing_metadata(owner, backend)
    owner.refresh(); backend.jobs.pop()()
    owner.transport.start = Mock(); owner.transport.end = Mock()
    owner._launch(action, value)
    assert not backend.jobs
    owner.transport.start.assert_not_called(); owner.transport.end.assert_not_called()
    assert owner.state["error"] == "profile_required"


@pytest.mark.parametrize("field,value", [("device_token", "replacement"), ("ha_url", "http://other.invalid"), ("device_id", "other-device"), ("active_profile_id", "other-profile"), ("explicit_profile_id", "other-profile"), ("paired", False)])
def test_bootstrap_queue_and_display_are_fenced_to_original_binding(controller, field, value):
    owner, backend = controller
    _missing_metadata(owner, backend)
    owner.refresh(); job = backend.jobs.pop()
    setattr(backend.cfg, field, value)
    job()
    assert not owner.state["session_id"] and not owner.state["moments"]
    owner.transport.active.assert_not_called()


@pytest.mark.parametrize("field,value", [("device_token", "replacement"), ("ha_url", "http://other.invalid"), ("device_id", "other-device"), ("active_profile_id", "other-profile"), ("explicit_profile_id", "other-profile"), ("paired", False)])
def test_bootstrap_visible_data_withdraws_even_before_next_gui_notification(controller, field, value):
    owner, backend = controller
    _missing_metadata(owner, backend)
    owner.refresh(); backend.jobs.pop()()
    assert owner.state["session_id"]
    setattr(backend.cfg, field, value)
    assert not owner.state["session_id"] and not owner.state["moments"]
    assert not owner.state["playback"] and not owner.state["forecast_supported"]


@pytest.mark.parametrize("category", ["denied", "unpaired", "context_changed"])
def test_bootstrap_capability_denial_withdraws_prior_active_read(controller, category):
    owner, backend = controller
    _missing_metadata(owner, backend)
    owner.transport.capabilities.side_effect = SessionError(category)
    owner.refresh(); backend.jobs.pop()()
    assert not owner.state["session_id"] and not owner.state["owner_read_only"]


def test_bootstrap_close_revokes_queued_read_without_network(controller):
    owner, backend = controller
    _missing_metadata(owner, backend)
    owner.refresh(); job = backend.jobs.pop()
    owner.setForeground(False); job()
    owner.transport.active.assert_not_called()
    assert not owner.state["session_id"]


def test_bootstrap_refresh_revalidates_owner_and_empty_session_withdraws(controller):
    owner, backend = controller
    _missing_metadata(owner, backend)
    owner.refresh(); backend.jobs.pop()()
    cleared = Mock(); owner.contextCleared.connect(cleared)
    _missing_metadata(owner, backend, "successor-profile", "successor-session")
    owner.refresh(); backend.jobs.pop()()
    assert owner.state["owner_profile_id"] == "successor-profile"
    assert owner.state["session_id"] == "successor-session" and cleared.call_count == 1
    owner.transport.active.return_value = {"success": True, "session": None}
    owner.refresh(); backend.jobs.pop()()
    assert not owner.state["session_id"] and not owner.state["owner_read_only"]
    assert backend.cfg.active_profile_id == backend.cfg.explicit_profile_id == ""


# The protected Apple/Core Profile-conversation read supplies actual personal
# admission even when legacy status supplies no Profile type/privacy metadata.
def _personal_owner(owner, backend):
    _missing_metadata(owner, backend)
    backend.cfg.active_profile_type = "household"  # Unknown Config default, not a server claim.
    backend.cfg.active_profile_privacy_mode = "shared"
    owner.transport.private_scope_owner.return_value = "profile-server"
    owner.transport.capabilities.return_value = {"success": True,
        "capabilities": {"session_conversation_history": True, "ask_dj_contextual_dialogue": True},
        "contract_versions": {"session_history_entries": 2, "ask_dj_contextual_dialogue": 1}}


def test_personal_scope_enables_existing_private_functions_without_fake_config(controller):
    from djconnect_pi.session_transport import (
        private_binding_allowed,
        private_scope_allowed,
    )
    owner, backend = controller
    _personal_owner(owner, backend)
    before = vars(backend.cfg).copy()
    owner.refresh(); backend.jobs.pop()()
    state = owner.state
    assert not state["owner_read_only"] and not state["profile_confirmation_required"]
    assert state["owner_profile_id"] == "profile-server" and state["history_available"]
    assert state["composer_available"] and private_scope_allowed(owner)
    binding = owner.transport.binding()
    assert binding.profile_id == binding.resolved_profile_id == "profile-server"
    assert binding.private_authorized and private_binding_allowed(binding)
    assert binding.profile_type == binding.privacy_mode == ""  # No fabricated metadata.
    assert vars(backend.cfg) == before
    owner.transport.private_scope_owner.assert_called_once()


def test_personal_scope_without_runtime_shows_creation_and_binds_explicit_start(controller):
    owner, backend = controller
    _personal_owner(owner, backend)
    owner.transport.active.return_value = {"success": True, "session": None}
    owner.transport.start = Mock()
    owner.refresh(); backend.jobs.pop()()
    assert owner.state["loaded"] and not owner.state["session_id"]
    assert not owner.state["profile_confirmation_required"] and owner.state["history_available"]
    owner.transport.start.assert_not_called()
    owner.start("groove"); backend.jobs.pop()()
    owner.transport.start.assert_called_once()
    assert owner.transport.start.call_args.args[0].profile_id == "profile-server"


def test_personal_scope_second_read_imports_only_existing_typed_flow(controller):
    owner, backend = controller
    _personal_owner(owner, backend)
    owner._read_conversation = Mock(return_value={"conversation": [], "retained_flow": []})
    owner.refresh(); backend.jobs.pop()()
    owner._read_conversation.assert_not_called()
    owner.refresh(); backend.jobs.pop()()
    owner._read_conversation.assert_called_once()
    assert owner._read_conversation.call_args.args[0].private_authorized
    assert owner.transport.private_scope_owner.call_count == 2
    assert owner.state["composer_available"]


def test_personal_scope_revocation_removes_private_views_and_late_binding(controller):
    from djconnect_pi.session_transport import private_scope_allowed
    owner, backend = controller
    _personal_owner(owner, backend)
    owner.refresh(); backend.jobs.pop()()
    old = owner.transport.binding()
    owner._sessions = [{"session_id": "old-private"}]
    owner.transport.private_scope_owner.return_value = None
    owner.refresh(); backend.jobs.pop()()
    assert not private_scope_allowed(owner) and not owner.state["composer_available"]
    assert not owner.state["history_available"] and not owner.state["sessions"]
    assert owner.state["owner_read_only"] and owner.state["session_id"] == "active-server"
    assert old != owner.transport.binding()


def test_current_and_personal_owner_must_join_exactly(controller):
    owner, backend = controller
    _personal_owner(owner, backend)
    owner.transport.private_scope_owner.return_value = "another-owner"
    owner.refresh(); backend.jobs.pop()()
    assert not owner.state["session_id"] and not owner.state["history_available"]
    assert owner.state["error"] == "context_changed"


@pytest.mark.parametrize("category", ["denied", "unpaired", "context_changed", "invalid", "offline"])
def test_failed_scope_read_never_becomes_private_admission(controller, category):
    from djconnect_pi.session_transport import private_scope_allowed
    owner, backend = controller
    _personal_owner(owner, backend)
    owner.transport.private_scope_owner.side_effect = SessionError(category)
    owner.refresh(); backend.jobs.pop()()
    assert not private_scope_allowed(owner) and not owner.state["history_available"]
    assert not owner.state["session_id"]


def test_context_change_inside_scope_read_cannot_grant_successor(controller):
    owner, backend = controller
    _personal_owner(owner, backend)
    def changed(binding):
        backend.cfg.device_token = "successor"
        return "profile-server"
    owner.transport.private_scope_owner.side_effect = changed
    owner.refresh(); backend.jobs.pop()()
    assert not owner.state["session_id"] and not owner.state["history_available"]
    assert backend.cfg.active_profile_id == backend.cfg.explicit_profile_id == ""


@pytest.mark.parametrize("kind", ["household", "room", "guest", "kids", "party"])
def test_nonpersonal_legacy_metadata_does_not_grant_private_functions(controller, kind):
    from djconnect_pi.session_transport import private_scope_allowed
    owner, backend = controller
    backend.cfg.active_profile_type = kind
    assert not private_scope_allowed(owner)
    owner._session = {"session_id": "existing", "runtime_state": "active"}
    owner._caps = {"capabilities": {"session_conversation_history": True, "ask_dj_contextual_dialogue": True},
        "contract_versions": {"session_history_entries": 2, "ask_dj_contextual_dialogue": 1}}
    assert not owner.state["composer_available"]



def test_personal_scope_regrant_never_revives_an_older_binding(controller):
    owner, backend = controller
    _personal_owner(owner, backend)
    owner.refresh(); backend.jobs.pop()()
    original = owner.transport.binding()
    owner.transport.private_scope_owner.return_value = None
    owner.refresh(); backend.jobs.pop()()
    withdrawn = owner.transport.binding()
    owner.transport.private_scope_owner.return_value = "profile-server"
    owner.refresh(); backend.jobs.pop()()
    successor = owner.transport.binding()
    assert original.profile_id == successor.profile_id and original.private_authorized and successor.private_authorized
    assert original.owner_epoch < withdrawn.owner_epoch < successor.owner_epoch
    assert original != successor


def test_raw_context_revocation_hides_all_private_models_without_gui_tick(controller):
    owner, backend = controller
    _personal_owner(owner, backend)
    owner.refresh(); backend.jobs.pop()()
    owner._sessions = [{"session_id": "secret"}]
    owner._timeline = {"session": {"session_id": "secret"}, "entries": [{"text": "private"}]}
    owner._search = {"query": "private"}
    owner._retained_flow = [{"entry_id": "private"}]
    backend.cfg.device_token = "new-context"
    state = owner.state
    assert not state["sessions"] and not state["timeline"] and not state["search"]
    assert not state["retained_flow"] and not state["current_reply"] and not state["pending_question"]
    assert not state["session_id"] and not state["loaded"]



def test_flow_native_join_falls_back_only_to_independently_retained_original_body(controller):
    from copy import deepcopy

    from test_session_projection import live_fixture
    owner, _ = controller
    host = clock_fixture(owner)
    session = live_fixture()
    grant = session["broadcast"]["native_delivery"]["admissions"][0]
    grant["display_expires_at"] = "2026-10-20T00:00:03Z"
    grant["source_expires_at"] = "2026-10-20T00:00:03Z"
    owner._session = session
    from djconnect_pi.session_history_view import live_presentations
    owner._moments = live_presentations(session, now=host.wall)
    row = {"entry_id": "retained", "session_id": "s1", "kind": "dj_moment", "moment_id": "m1", "text": "independent retained prose", "retained_until": "2026-10-20T00:00:05Z"}
    owner._retained_flow = [row]
    original = deepcopy(row)
    assert owner.state["moments"] and not owner.state["flow_rows"]
    assert owner.state["retained_flow"] == [original]
    host.tick = 4; owner._expire()
    assert not owner.state["moments"]
    assert owner.state["flow_rows"] == [{"bulletin": False, "contribution": original}]
    assert row == original
    host.tick = 6; owner._expire()
    assert not owner.state["moments"] and not owner.state["retained_flow"] and not owner.state["flow_rows"]


def test_raw_scope_withdrawal_masks_joined_presentation_as_well(controller):
    owner, backend = controller
    _personal_owner(owner, backend)
    owner.refresh(); backend.jobs.pop()()
    owner._retained_flow = [{"entry_id": "secret", "kind": "conversation_dj"}]
    assert owner.state["flow_rows"]
    backend.cfg.device_token = "changed"
    assert owner.state["flow_rows"] == []


@pytest.mark.parametrize("source", ["flow", "timeline"])
def test_withdrawn_entry_is_not_a_selected_question_target(controller, source):
    owner, _backend = controller
    owner._session = {"session_id": "s1"}
    row = {"session_id": "s1", "entry_id": "row-a", "retained_until": "9999-01-01T00:00:00Z"}
    owner._retained_flow = [row]
    owner._timeline = {"session": {"session_id": "s1"}, "entries": [row]}
    selected = {"kind": "selected_entry", "session_id": "s1", "entry_id": "row-a"}
    assert owner._entry_selection_valid(selected, source)
    row["state"] = "source_withdrawn"
    assert not owner._entry_selection_valid(selected, source)


def _content_delete_fixture(owner, monkeypatch):
    from test_session_content_delete import CAPS, preview
    from test_session_history_delete import OP

    from djconnect_pi import session_content_delete
    from djconnect_pi.session_projection import timestamp

    stamp = timestamp(preview(owner.transport.binding())["created_at"])
    monkeypatch.setattr(owner._clock, "now", lambda: stamp)
    monkeypatch.setattr(session_content_delete, "operation_id", lambda: OP)
    owner.setContentDeleteVisible(True)
    owner._caps = CAPS
    owner.transport.capabilities.return_value = CAPS
    owner._session = {"session_id": "saved"}
    owner._retained_flow = [{
        "session_id": "saved", "entry_id": "entry-original", "kind": "conversation_dj",
        "retained_until": "9999-01-01T00:00:00Z", "text": "private fixture",
    }]
    owner.transport.prepare_content_delete = Mock(return_value=preview(
        owner.transport.binding(), affected_moments=[{"session_id": "saved", "moment_id": "live"}]))
    owner.transport.delete_content = Mock(side_effect=SessionError("uncertain"))
    owner.transport.content_delete_status = Mock(return_value="completed")


def test_content_erasure_requires_confirmation_and_withdraws_only_after_original_receipt(controller, monkeypatch):
    owner, backend = controller
    _content_delete_fixture(owner, monkeypatch)
    assert owner.beginContentDelete("entry", "saved", "entry-original")
    assert not owner.confirmContentDelete(1)
    backend.jobs.pop()()
    scope = owner.state["content_delete"]
    assert scope["status"] == "confirm"
    assert (scope["remove_entries"], scope["unavailable_entries"], scope["moments"]) == (1, 1, 1)
    original = owner._retained_flow.copy()
    assert owner.confirmContentDelete(scope["lease"])
    assert not owner.confirmContentDelete(scope["lease"])
    backend.jobs.pop()()
    assert owner.state["content_delete"]["status"] == "uncertain"
    assert owner._retained_flow == original
    owner.cancelContentDelete()
    assert not owner.beginContentDelete("entry", "saved", "entry-original")
    assert owner.checkContentDeleteStatus()
    backend.jobs.pop()()
    owner.transport.delete_content.assert_called_once()
    owner.transport.content_delete_status.assert_called_once()
    assert owner.transport.delete_content.call_args.args[1] is owner.transport.content_delete_status.call_args.args[1]
    assert owner.state["content_delete"]["status"] == "deleted"
    assert owner._retained_flow == []
    assert owner._without_withdrawn_entries(original) == []
    session = {"session_id": "saved", "broadcast": {"dj_moments": [{"moment_id": "live"}, {"moment_id": "other"}]}}
    assert owner._without_withdrawn_moments(session)["broadcast"]["dj_moments"] == [{"moment_id": "other"}]


def test_content_erasure_discards_prepared_scope_after_profile_switch(controller, monkeypatch):
    owner, backend = controller
    _content_delete_fixture(owner, monkeypatch)
    assert owner.beginContentDelete("entry", "saved", "entry-original")
    backend.jobs.pop()()
    lease = owner.state["content_delete"]["lease"]
    backend.cfg.active_profile_id = "profile-b"
    backend.cfg.explicit_profile_id = "profile-b"
    owner.invalidate()
    assert not owner.confirmContentDelete(lease)
    owner.transport.delete_content.assert_not_called()


@pytest.fixture
def vibecast_sender(controller):
    owner, backend = controller
    owner._session = {"session_id": "vibe-session", "runtime_state": "active"}
    owner._caps = {"session_broadcast": {"paired_display_admission": {
        "supported": True, "version": 1, "owner_authentication": "paired_device_bearer",
        "owner_context_path": "/api/djconnect/v1/display/owner/context",
        "entry_path": "/djconnect/vibecast/display", "owner_client_types": ["ios", "macos", "raspberry_pi"],
    }}}
    responses = {
        "context": {"session_id": "vibe-session", "issuer_epoch": "e" * 43,
                    "route_trust": "paired_owner_response",
                    "display_entry_url": "https://display.djconnect.dev/djconnect/vibecast/display"},
        "resolve": {"issuer_epoch": "e" * 43, "claim_id": "c" * 43,
                    "browser_generation": "b" * 43, "expires_in": 120},
        "approve": {"session_id": "vibe-session", "state": "approved", "display_id": "d" * 43,
                    "share_id": "s" * 43, "share_generation": 1, "share_expires_in": 7199},
        "revoke": {},
    }

    def dispatch(_binding, action, _payload):
        return {"success": True, "contract_version": 1, **responses[action]}

    owner.transport.display_owner = Mock(side_effect=dispatch)
    owner.transport.end = Mock()
    return owner, backend, responses


def test_vibecast_lookup_approve_and_stop_are_distinct_from_session_end(vibecast_sender):
    owner, backend, responses = vibecast_sender
    assert owner.openVibeCast()
    backend.jobs.pop()()
    assert not owner.resolveVibeCastCode("12345")
    assert owner.resolveVibeCastCode("012345")
    backend.jobs.pop()()
    assert [call.args[1] for call in owner.transport.display_owner.call_args_list] == ["context", "context", "resolve"]
    assert owner.state["vibecast"]["status"] == "confirm"
    assert "012345" not in str(owner.state["vibecast"])
    assert owner.approveVibeCast()
    assert not owner.approveVibeCast()
    backend.jobs.pop()()
    approved = owner.transport.display_owner.call_args.args
    assert approved[1] == "approve"
    assert approved[2] == {
        "session_id": "vibe-session", "issuer_epoch": "e" * 43, "claim_id": "c" * 43,
        "browser_generation": "b" * 43, "code": "012345",
        "share": {"mode": "create", "consent": True, "lifetime_seconds": 7200},
    }
    responses["context"].update(share_id="s" * 43, share_generation=1, expires_in=7199)
    assert owner.stopVibeCast()
    backend.jobs.pop()()
    assert owner.transport.display_owner.call_args.args[1:] == (
        "revoke", {"session_id": "vibe-session", "share_id": "s" * 43},
    )
    assert owner.state["vibecast"]["status"] == "stopped"
    assert owner.state["session_id"] == "vibe-session"
    owner.transport.end.assert_not_called()


@pytest.mark.parametrize("transition", ["profile", "foreground", "session", "closed", "expired", "capability"])
def test_vibecast_never_dispatches_approval_after_losing_original_scope(vibecast_sender, transition):
    owner, backend, _ = vibecast_sender
    assert owner.openVibeCast()
    backend.jobs.pop()()
    assert owner.resolveVibeCastCode("012345")
    backend.jobs.pop()()
    if transition == "expired":
        owner._vibecast.expire_claim()
        assert not owner.approveVibeCast()
    else:
        assert owner.approveVibeCast()
        approve = backend.jobs.pop()
        if transition == "profile":
            backend.cfg.active_profile_id = "other"
        elif transition == "foreground":
            owner.setForeground(False)
        elif transition == "session":
            owner._session["session_id"] = "different"
        elif transition == "closed":
            owner.closeVibeCast()
        elif transition == "capability":
            owner._caps = {}
        approve()
    assert [call.args[1] for call in owner.transport.display_owner.call_args_list] == ["context", "context", "resolve"]


@pytest.mark.parametrize("pending_confirmation", [False, True])
def test_vibecast_can_stop_all_from_sender_without_local_display_receipt(vibecast_sender, pending_confirmation):
    owner, backend, responses = vibecast_sender
    responses["context"].update(share_id="s" * 43, share_generation=2, expires_in=240)
    assert owner.openVibeCast()
    backend.jobs.pop()()
    assert owner.state["vibecast"]["has_share"]
    assert not owner.state["vibecast"]["has_display"]

    if pending_confirmation:
        assert owner.resolveVibeCastCode("012345")
        backend.jobs.pop()()
        assert owner.state["vibecast"]["status"] == "confirm"

    assert owner.stopVibeCast()
    assert not owner.approveVibeCast()
    backend.jobs.pop()()
    assert owner.transport.display_owner.call_args.args[1:] == (
        "revoke", {"session_id": "vibe-session", "share_id": "s" * 43},
    )
    assert owner.state["vibecast"]["status"] == "stopped"
    assert not owner.state["vibecast"]["has_share"]
    assert not owner.approveVibeCast()
    owner.transport.end.assert_not_called()


@pytest.mark.parametrize("replacement", [False, True])
def test_vibecast_stop_reads_new_share_without_replaying(vibecast_sender, replacement):
    owner, backend, responses = vibecast_sender
    context = responses["context"]
    context.update(share_id="s" * 43, share_generation=1, expires_in=240)
    assert owner.openVibeCast()
    backend.jobs.pop()()
    if replacement:
        context.update(share_id="r" * 43, share_generation=2)
    else:
        for field in ("share_id", "share_generation", "expires_in"):
            context.pop(field)

    assert owner.stopVibeCast()
    backend.jobs.pop()()
    assert [call.args[1] for call in owner.transport.display_owner.call_args_list] == ["context", "context"]
    assert owner.state["vibecast"]["status"] == "share_changed"
    assert owner.state["vibecast"]["has_share"] is replacement
    assert owner.stopVibeCast() is replacement
    if replacement:
        backend.jobs.pop()()
        assert owner.transport.display_owner.call_args.args[1:] == (
            "revoke", {"session_id": "vibe-session", "share_id": "r" * 43},
        )
    owner.transport.end.assert_not_called()


@pytest.mark.parametrize("code_found", [False, True])
def test_vibecast_lookup_notices_share_started_by_another_sender(vibecast_sender, code_found):
    owner, backend, responses = vibecast_sender
    assert owner.openVibeCast()
    backend.jobs.pop()()
    assert not owner.state["vibecast"]["has_share"]
    responses["context"].update(share_id="s" * 43, share_generation=2, expires_in=240)
    responses["resolve"]["success"] = code_found

    assert owner.resolveVibeCastCode("012345")
    backend.jobs.pop()()
    assert owner.state["vibecast"]["has_share"]
    assert owner.state["vibecast"]["status"] == ("confirm" if code_found else "lookup_failed")
    assert [call.args[1] for call in owner.transport.display_owner.call_args_list] == ["context", "context", "resolve"]
    if code_found:
        responses["approve"].update(share_generation=2, share_expires_in=239)
        assert owner.approveVibeCast()
        backend.jobs.pop()()
        assert owner.transport.display_owner.call_args.args[2]["share"] == {
            "mode": "existing", "share_id": "s" * 43, "share_generation": 2,
        }


@pytest.mark.parametrize("change", [None, "expired", "generation"])
def test_vibecast_disconnect_targets_only_last_approved_display(vibecast_sender, monkeypatch, change):
    owner, backend, responses = vibecast_sender
    assert owner.openVibeCast()
    backend.jobs.pop()()
    assert not owner.disconnectVibeCastDisplay()
    assert owner.resolveVibeCastCode("012345")
    backend.jobs.pop()()
    assert owner.approveVibeCast()
    backend.jobs.pop()()
    assert owner.state["vibecast"]["has_display"]

    responses["context"].update(share_id="s" * 43, share_generation=1, expires_in=7199)
    assert owner.disconnectVibeCastDisplay()
    if change == "generation":
        responses["context"]["share_generation"] = 2
    elif change == "expired":
        deadline = owner._vibecast.context.display_receipt[1]
        monkeypatch.setattr("djconnect_pi.session_vibecast.time.monotonic", lambda: deadline)
    backend.jobs.pop()()
    writes = [call.args[2] for call in owner.transport.display_owner.call_args_list if call.args[1] == "revoke"]
    if change is None:
        assert writes == [{"session_id": "vibe-session", "share_id": "s" * 43, "display_id": "d" * 43}]
        assert owner.state["vibecast"]["status"] == "display_stopped"
        assert owner.state["vibecast"]["has_share"]
    else:
        assert writes == []
    assert not owner.state["vibecast"]["has_display"]
    assert not owner.disconnectVibeCastDisplay()
    owner.transport.end.assert_not_called()


@pytest.mark.parametrize("entry_url", [
    None,
    "http://display.djconnect.dev/djconnect/vibecast/display",
    "https://display.djconnect.dev:443/djconnect/vibecast/display",
    "https://display.djconnect.dev/djconnect/vibecast/display?redirect=other",
    "https://display.djconnect.dev/djconnect/vibecast",
    "https://display.local/djconnect/vibecast/display",
    "https://127.0.0.1/djconnect/vibecast/display",
])
def test_vibecast_requires_canonical_external_display_route(vibecast_sender, entry_url):
    owner, backend, responses = vibecast_sender
    responses["context"]["display_entry_url"] = entry_url
    assert owner.openVibeCast()
    backend.jobs.pop()()
    assert owner.state["vibecast"]["status"] == "failed"
    assert not owner.resolveVibeCastCode("012345")
    assert [call.args[1] for call in owner.transport.display_owner.call_args_list] == ["context"]


@pytest.mark.parametrize("action", ["approve", "revoke"])
def test_vibecast_refuses_mutation_when_display_origin_changes(vibecast_sender, action):
    owner, backend, responses = vibecast_sender
    if action == "revoke":
        responses["context"].update(share_id="s" * 43, share_generation=1, expires_in=7199)
    assert owner.openVibeCast()
    backend.jobs.pop()()
    if action == "approve":
        assert owner.resolveVibeCastCode("012345")
        backend.jobs.pop()()
        assert owner.approveVibeCast()
    else:
        assert owner.stopVibeCast()

    responses["context"]["display_entry_url"] = "https://other.djconnect.dev/djconnect/vibecast/display"
    backend.jobs.pop()()
    calls = [call.args[1] for call in owner.transport.display_owner.call_args_list]
    assert calls == (["context", "context", "resolve", "context"] if action == "approve" else ["context", "context"])
    assert owner.state["vibecast"]["status"] == "failed"


def test_vibecast_lookup_can_retry_after_rejection_or_expiry(vibecast_sender):
    owner, backend, responses = vibecast_sender
    assert owner.openVibeCast()
    backend.jobs.pop()()
    responses["resolve"]["success"] = False
    assert owner.resolveVibeCastCode("012345")
    backend.jobs.pop()()
    assert owner.state["vibecast"]["status"] == "lookup_failed"
    assert not owner.approveVibeCast()

    responses["resolve"]["success"] = True
    assert owner.resolveVibeCastCode("123456")
    backend.jobs.pop()()
    owner._vibecast.expire_claim()
    assert owner.state["vibecast"]["status"] == "expired"
    assert not owner.approveVibeCast()
    assert owner.resolveVibeCastCode("234567")
    backend.jobs.pop()()
    assert owner.state["vibecast"]["status"] == "confirm"
    assert [call.args[1] for call in owner.transport.display_owner.call_args_list] == [
        "context", "context", "resolve", "context", "resolve", "context", "resolve",
    ]


def test_vibecast_uncertain_revoke_uses_status_read_instead_of_replay(vibecast_sender):
    owner, backend, responses = vibecast_sender
    responses["context"].update(share_id="s" * 43, share_generation=1, expires_in=7199)
    assert owner.openVibeCast()
    backend.jobs.pop()()
    dispatch = owner.transport.display_owner.side_effect

    def lost_reply(binding, action, payload):
        if action == "revoke":
            for field in ("share_id", "share_generation", "expires_in"):
                responses["context"].pop(field)
            raise SessionError("uncertain")
        return dispatch(binding, action, payload)

    owner.transport.display_owner.side_effect = lost_reply
    assert owner.stopVibeCast()
    backend.jobs.pop()()
    assert owner.state["vibecast"]["status"] == "uncertain"
    assert not owner.stopVibeCast()
    owner.refreshVibeCast()
    backend.jobs.pop()()
    assert owner.state["vibecast"]["status"] == "ready"
    assert [call.args[1] for call in owner.transport.display_owner.call_args_list] == [
        "context", "context", "revoke", "context",
    ]
    owner.transport.end.assert_not_called()


@pytest.mark.parametrize("phase", ["context", "approve"])
def test_vibecast_approval_respects_original_code_deadline(vibecast_sender, monkeypatch, phase):
    owner, backend, _ = vibecast_sender
    clock = [100.0]
    monkeypatch.setattr("djconnect_pi.session_vibecast.time.monotonic", lambda: clock[0])
    assert owner.openVibeCast()
    backend.jobs.pop()()
    assert owner.resolveVibeCastCode("012345")
    backend.jobs.pop()()
    dispatch = owner.transport.display_owner.side_effect

    def delayed_reply(binding, action, payload):
        if action == phase:
            clock[0] = 220.0
        return dispatch(binding, action, payload)

    owner.transport.display_owner.side_effect = delayed_reply
    assert owner.approveVibeCast()
    backend.jobs.pop()()
    assert owner.state["vibecast"]["status"] == ("expired" if phase == "context" else "uncertain")
    assert not owner.state["vibecast"]["has_display"]
    assert not owner.approveVibeCast()
    calls = [call.args[1] for call in owner.transport.display_owner.call_args_list]
    assert calls.count("approve") == (0 if phase == "context" else 1)


def test_vibecast_approval_does_not_extend_original_share_deadline(vibecast_sender, monkeypatch):
    owner, backend, responses = vibecast_sender
    responses["context"].update(share_id="s" * 43, share_generation=1, expires_in=1)
    clock = [100.0]
    monkeypatch.setattr("djconnect_pi.session_vibecast.time.monotonic", lambda: clock[0])
    assert owner.openVibeCast()
    backend.jobs.pop()()
    assert owner.resolveVibeCastCode("012345")
    backend.jobs.pop()()
    clock[0] = 101.0
    responses["context"]["expires_in"] = 5
    assert owner.approveVibeCast()
    backend.jobs.pop()()
    assert [call.args[1] for call in owner.transport.display_owner.call_args_list] == [
        "context", "context", "resolve", "context",
    ]
    assert owner.state["vibecast"]["status"] == "failed"


def test_vibecast_uncertain_approval_uses_status_read_instead_of_replay(vibecast_sender):
    owner, backend, responses = vibecast_sender
    assert owner.openVibeCast()
    backend.jobs.pop()()
    assert owner.resolveVibeCastCode("012345")
    backend.jobs.pop()()
    dispatch = owner.transport.display_owner.side_effect

    def lost_reply(binding, action, payload):
        if action == "approve":
            responses["context"].update(share_id="s" * 43, share_generation=1, expires_in=7199)
            raise SessionError("uncertain")
        return dispatch(binding, action, payload)

    owner.transport.display_owner.side_effect = lost_reply
    assert owner.approveVibeCast()
    backend.jobs.pop()()
    assert owner.state["vibecast"]["status"] == "uncertain"
    assert not owner.approveVibeCast()
    owner.refreshVibeCast()
    backend.jobs.pop()()
    assert owner.state["vibecast"]["status"] == "active"
    assert [call.args[1] for call in owner.transport.display_owner.call_args_list] == [
        "context", "context", "resolve", "context", "approve", "context",
    ]


def test_flow_loads_a_larger_authorized_tail_without_opening_saved_history(controller):
    owner, backend = controller
    session = {"session_id": "s", "runtime_state": "active", "broadcast": {"session": {"session_id": "s"}}}
    owner.transport.active.return_value = {"success": True, "session": session}

    def tail(binding, sid, *, limit=20):
        assert sid == "s"
        return {"success": True, "schema_version": 2, "history_contract_version": 2,
                "session": {"session_id": sid}, "revision": "r", "next_cursor": None,
                "window": "tail", "coverage": "bounded_saved_entry_window", "window_limit": limit,
                "scan_complete": limit >= 30, "entries": [
                    {"entry_id": f"entry-{i}", "session_id": sid, "order": i, "kind": "dj_silence",
                     "text": None, "speech_available": False, "historical_view_only": True,
                     "current_display_allowed": False, "occurred_at": "2026-11-09T00:00:00Z",
                     "retained_until": "2099-01-01T00:00:00Z"}
                    for i in range(max(1, 31 - limit), 31)]}

    owner.transport.timeline = Mock(side_effect=tail)
    owner.refresh()
    backend.jobs.pop()()
    assert owner.state["flow_more"] and len(owner.state["flow_rows"]) == 20
    owner.expandFlow("wrong-session")
    assert not backend.jobs
    owner.expandFlow("s")
    backend.jobs.pop()()
    assert len(owner.state["flow_rows"]) == 30
    assert not owner.state["flow_more"] and not owner.state["timeline"]
    owner.refresh()
    backend.jobs.pop()()
    assert owner.transport.timeline.call_args.kwargs == {"limit": 50}
    assert len(owner.state["flow_rows"]) == 30

    new_session = {"session_id": "new", "runtime_state": "active",
                   "broadcast": {"session": {"session_id": "new"}}}
    owner.transport.active.return_value = {"success": True, "session": new_session}
    owner.transport.timeline.side_effect = None
    owner.transport.timeline.return_value = {**tail(None, "s"), "session": {"session_id": "new"}, "entries": []}
    owner.refresh()
    backend.jobs.pop()()
    assert owner.transport.timeline.call_args.kwargs == {}
    assert owner.state["session_id"] == "new" and not owner.state["flow_rows"]
