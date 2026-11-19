"""Fresh chronological history2 reading windows, not a native/current grant."""
from copy import deepcopy
from unittest.mock import Mock

import pytest
from test_session_controller import clock_fixture, enable_search
from test_session_history_view import timeline_fixture

from djconnect_pi.session_transport import SessionError

pytest_plugins = ['test_session_controller']


def prefix_pages(owner, count=7):
    enable_search(owner); clock_fixture(owner)
    seed = timeline_fixture(); pages = []
    for index in range(count):
        page = deepcopy(seed); page.pop('window', None);page.pop('anchor_entry_id', None)
        prototype = deepcopy(seed['entries'][0])
        page['entries'] = [{**deepcopy(prototype), 'entry_id':f'prefix-{index*20+i+1}',
            'order':index*20+i+1} for i in range(20)]
        page['next_cursor'] = f'prefix-page-{index+1}' if index+1<count else None
        pages.append(page)
    def read(binding, sid, **kwargs):
        cursor = kwargs.get('cursor', '')
        return deepcopy(pages[int(cursor.rsplit('-',1)[-1])] if cursor else pages[0])
    owner.transport.timeline = Mock(side_effect=read)
    owner._timeline = deepcopy(seed);owner.firstEntries()
    return pages


def run(backend): backend.jobs.pop()()


def test_extend_re_reads_first_pages_fresh_and_never_appends_cached_body(controller):
    owner, backend = controller
    pages = prefix_pages(owner);run(backend)
    owner.transport.timeline.reset_mock()
    pages[0]['entries'][0]['text'] = 'Fresh original first page'
    positioned = Mock();owner.timelinePositioned.connect(positioned)
    owner.extendEntries('prefix-1', -42.5);run(backend)
    assert [c.kwargs for c in owner.transport.timeline.call_args_list] == [
        {'window':None,'cursor':''},{'window':None,'cursor':'prefix-page-1'}]
    assert len(owner.state['timeline']['entries']) == 40
    assert owner.state['timeline']['entries'][0]['text'] == 'Fresh original first page'
    positioned.assert_called_once_with('prefix-1', -42.5)
    assert owner._timeline['_prefix_pages'] == 2


def test_five_page_bound_next_and_fresh_previous_prefix_restore(controller):
    owner, backend = controller
    pages = prefix_pages(owner);run(backend)
    for _ in range(4): owner.extendEntries();run(backend)
    assert len(owner._timeline['entries']) == 100 and owner._timeline['_prefix_pages'] == 5
    count = owner.transport.timeline.call_count
    owner.extendEntries();assert owner.transport.timeline.call_count == count and not backend.jobs
    owner.nextEntries('prefix-85', -65);run(backend)
    assert len(owner._timeline['entries']) == 20 and owner._timeline['entries'][0]['entry_id']=='prefix-101'
    assert owner._timeline_trail == [{'prefix_pages':5, 'reading':{'entry_id':'prefix-85','offset':-65.0}}]
    pages[0]['entries'][0]['text']='Fresh on previous'
    positioned=Mock();owner.timelinePositioned.connect(positioned)
    owner.transport.timeline.reset_mock();owner.previousEntries();run(backend)
    assert owner.transport.timeline.call_count == 5 and len(owner._timeline['entries']) == 100
    assert owner._timeline['entries'][0]['text']=='Fresh on previous'
    positioned.assert_called_once_with('prefix-85', -65.0)
    assert not owner._timeline_trail


def test_prefix_revalidation_reads_every_shown_page_with_fresh_cursors(controller):
    owner, backend = controller
    pages=prefix_pages(owner);run(backend)
    owner.extendEntries();run(backend)
    pages[0]['next_cursor']='new-1';pages[0]['entries'][0]['text']='Revalidated'
    owner.transport.timeline.side_effect=[deepcopy(pages[0]),deepcopy(pages[1])]
    owner.transport.timeline.reset_mock();owner.refreshSaved('prefix-1');run(backend)
    assert [c.kwargs for c in owner.transport.timeline.call_args_list] == [
        {'window':None,'cursor':''},{'window':None,'cursor':'new-1'}]
    assert owner._timeline['entries'][0]['text']=='Revalidated'
    assert len(owner._timeline['entries']) == 40


@pytest.mark.parametrize('fault', ['revision','duplicate','order','cycle','wire_bound','denied','expired','foreign'])
def test_prefix_rejects_conflicting_or_withdrawn_pages_atomically(controller, fault):
    owner, backend = controller
    pages=prefix_pages(owner);run(backend)
    if fault=='revision': pages[1]['revision']='different'
    elif fault=='duplicate': pages[1]['entries'][0]['entry_id']=pages[0]['entries'][0]['entry_id']
    elif fault=='order': pages[1]['entries'][0]['order']=1
    elif fault=='cycle': pages[1]['next_cursor']=pages[0]['next_cursor']
    elif fault=='wire_bound': pages[1]['entries'].append({**pages[1]['entries'][-1],'entry_id':'extra','order':41})
    elif fault=='expired': pages[1]['entries'][0]['retained_until']='2000-01-01T00:00:00Z'
    elif fault=='foreign': pages[1]['session']['session_id']='other-session'
    else: owner.transport.timeline.side_effect=[deepcopy(pages[0]),SessionError('denied')]
    owner.extendEntries();run(backend)
    assert owner.state['timeline'] == {} and not owner._timeline_trail


@pytest.mark.parametrize('boundary', ['before','between'])
def test_prefix_view_withdrawal_prevents_further_gets_and_late_publication(controller, boundary):
    owner, backend = controller
    pages=prefix_pages(owner);run(backend)
    owner.transport.timeline.reset_mock()
    if boundary=='between':
        def first(*args,**kwargs): owner.closeSaved();return deepcopy(pages[0])
        owner.transport.timeline.side_effect=first
    owner.extendEntries();work=backend.jobs.pop()
    if boundary=='before': owner.closeSaved()
    work()
    assert owner.transport.timeline.call_count == (0 if boundary=='before' else 1)
    assert owner.state['timeline']=={}


def test_previous_prefix_revision_drift_uses_only_fresh_visible_anchor(controller):
    owner, backend = controller
    pages=prefix_pages(owner);run(backend)
    owner.extendEntries();run(backend);owner.nextEntries();run(backend)
    pages[0]['revision']=pages[1]['revision']='new-revision'
    anchor=deepcopy(pages[2]);anchor.update(window='anchor',anchor_entry_id='prefix-41')
    owner.transport.timeline.side_effect=[deepcopy(pages[0]),deepcopy(pages[1]),anchor]
    owner.previousEntries('prefix-41');run(backend)
    assert len(owner._timeline['entries'])==20 and owner._timeline['window']=='anchor'
    assert not owner._timeline_trail


@pytest.mark.parametrize('offset', [float('nan'),float('inf'),True,1_000_001])
def test_prefix_unsafe_reading_metadata_never_enters_transport_or_descriptor(controller, offset):
    owner, backend = controller
    prefix_pages(owner);run(backend)
    positioned=Mock();owner.timelinePositioned.connect(positioned)
    owner.extendEntries('prefix-1',offset);run(backend)
    positioned.assert_not_called()
    assert all(set(c.kwargs)=={'window','cursor'} for c in owner.transport.timeline.call_args_list)


def test_prefix_gui_queue_expiry_removes_all_new_bodies(controller):
    owner, backend = controller
    pages=prefix_pages(owner);run(backend)
    from datetime import UTC, datetime
    host=clock_fixture(owner)
    for page in pages:
        for row in page['entries']: row['retained_until']=datetime.fromtimestamp(host.wall+4,UTC).isoformat()
    queued=[];owner._ready.disconnect(owner._apply);owner._ready.connect(queued.append)
    owner.extendEntries();run(backend)
    host.tick=5
    owner._apply(queued[0]);assert not owner.state['timeline']['entries']


def test_unknown_wire_prefix_marker_cannot_change_local_traversal_budget(controller):
    owner, backend = controller
    pages=prefix_pages(owner);pages[0]['_prefix_pages']=4;run(backend)
    assert '_prefix_pages' not in owner._timeline
    owner.transport.timeline.reset_mock();owner.extendEntries();run(backend)
    assert owner._timeline['_prefix_pages']==2 and owner.transport.timeline.call_count==2
