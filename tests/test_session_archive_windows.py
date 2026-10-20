"""Bounded older/newer owner-list windows; no old header-body cache."""
import pytest
from test_session_archive_freshness import archive_pages, run

from djconnect_pi.session_transport import SessionError

pytest_plugins = ['test_session_controller']


def first_window(owner, backend, count=12):
    host, pages = archive_pages(owner, count, 20)
    run(owner, backend, 'loadHistory')
    for _ in range(4): run(owner, backend, 'moreHistory')
    return host, pages


def test_older_window_reaches_past_hundred_and_newer_is_a_fresh_bounded_read(controller):
    owner, backend = controller
    _, pages = first_window(owner, backend)
    owner.olderSessions('saved-2-0', -17.5);backend.jobs.pop()()
    assert owner._history_start == 'cursor-5' and len(owner.state['sessions']) == 20
    assert owner.state['sessions'][0]['session_id'] == 'saved-5-0'
    assert owner.state['has_newer_sessions'] and owner.state['archive_older_window']
    assert not owner.state['has_older_sessions'] and owner.state['has_more_sessions']
    assert all(set(row) <= {'pages','start','scope','before','reading'} for row in owner._history_trail)
    for _ in range(4): run(owner, backend, 'moreHistory')
    assert len(owner.state['sessions']) == 100 and owner.state['has_older_sessions']
    assert owner.state['sessions'][0]['session_id'] == 'saved-5-0'
    pages[0]['sessions'][0]['summary']['text'] = 'Freshly changed earlier summary'
    positioned = [];owner.archivePositioned.connect(lambda sid,offset:positioned.append((sid,offset)))
    count = owner.transport.history.call_count
    run(owner, backend, 'newerSessions')
    assert owner.transport.history.call_count == count + 5
    assert owner.state['sessions'][0]['summary']['text'] == 'Freshly changed earlier summary'
    assert positioned == [('saved-2-0', -17.5)]
    assert not owner._history_start and not owner._history_trail
    assert all(set(c.kwargs) == {'cursor'} for c in owner.transport.history.call_args_list)


@pytest.mark.parametrize('change', ['cursor', 'revision', 'policy'])
def test_withdrawn_older_window_returns_once_to_fresh_newest_and_clears_trail(controller, change):
    owner, backend = controller
    first_window(owner, backend)
    owner.olderSessions('',0);backend.jobs.pop()()
    original = owner.transport.history.side_effect
    def read(binding, *, cursor=''):
        if cursor == 'cursor-5':
            if change == 'cursor': raise SessionError('conflict')
            row=original(binding,cursor=cursor)
            row['revision' if change=='revision' else 'retention_revision'] = 'changed' if change=='revision' else 9
            return row
        return original(binding,cursor=cursor)
    owner.transport.history.side_effect = read
    count=owner.transport.history.call_count
    run(owner, backend, 'refreshArchive')
    assert owner.transport.history.call_count==count+2
    assert not owner._history_start and not owner._history_trail
    assert owner.state['archive_window_reset']
    assert owner.state['sessions'][0]['session_id']=='saved-0-0'
    run(owner,backend,'refreshArchive')
    assert not owner.state['archive_window_reset']


def test_denial_never_falls_back_or_preserves_window_navigation(controller):
    owner, backend = controller
    first_window(owner, backend);owner.olderSessions('',0);backend.jobs.pop()()
    owner.transport.history.side_effect=SessionError('denied')
    count=owner.transport.history.call_count
    run(owner,backend,'refreshArchive')
    assert owner.transport.history.call_count==count+1
    assert not owner.state['sessions'] and not owner._history_start and not owner._history_trail
    assert not owner.state['has_newer_sessions']


def test_older_keyset_boundary_is_checked_on_every_refresh(controller):
    owner,backend=controller
    _,pages=first_window(owner,backend)
    owner.olderSessions('',0);backend.jobs.pop()()
    pages[5]['sessions'][0]['created_at']=pages[0]['sessions'][0]['created_at']
    run(owner,backend,'refreshArchive')
    assert not owner.state['sessions'] and owner.state['error']=='invalid'
    assert not owner._history_trail


@pytest.mark.parametrize('offset',[float('nan'),float('inf'),True,1_000_001])
def test_invalid_reading_metadata_is_not_saved_or_sent(controller,offset):
    owner,backend=controller
    first_window(owner,backend)
    owner.olderSessions('saved-2-0',offset);backend.jobs.pop()()
    assert 'reading' not in owner._history_trail[-1]
    assert all(set(c.kwargs)=={'cursor'} for c in owner.transport.history.call_args_list)


def test_missing_fresh_reading_id_returns_to_top(controller):
    owner,backend=controller
    _,pages=first_window(owner,backend)
    owner.olderSessions('saved-2-0',12);backend.jobs.pop()()
    pages[2]['sessions']=[row for row in pages[2]['sessions'] if row['session_id']!='saved-2-0']
    events=[];owner.archivePositioned.connect(lambda sid,offset:events.append((sid,offset)))
    run(owner,backend,'newerSessions')
    assert events==[('',0)]


def test_clear_archive_cancels_late_read_without_ending_current_session(controller):
    owner,backend=controller
    first_window(owner,backend)
    owner._session={'session_id':'still-current'}
    owner.olderSessions('',0);job=backend.jobs.pop()
    owner.clearArchive();job()
    assert owner._session['session_id']=='still-current'
    assert not owner.state['sessions'] and not owner._history_trail and not owner._history_start
    assert not owner.state['history_loaded']


def test_return_trail_is_bounded_and_newest_remains_reachable(controller):
    owner,backend=controller
    first_window(owner,backend,count=176)
    for _ in range(34):
        owner.olderSessions('',0);backend.jobs.pop()()
        for _ in range(4): run(owner,backend,'moreHistory')
        assert len(owner.state['sessions'])<=100 and len(owner._history_trail)<=32
    assert len(owner._history_trail)==32 and owner.state['archive_older_window']
    for _ in range(32): run(owner,backend,'newerSessions')
    assert not owner.state['has_newer_sessions'] and owner.state['archive_older_window']
    run(owner,backend,'loadHistory')
    assert not owner._history_start and not owner._history_trail
    assert owner.state['sessions'][0]['session_id']=='saved-0-0'
