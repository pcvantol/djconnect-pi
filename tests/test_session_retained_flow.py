"""Retained history in current Flow is read-only, never a native/current grant."""
from copy import deepcopy
from datetime import UTC, datetime

import pytest
from test_session_composer import anchor_transport, setup_composer
from test_session_controller import clock_fixture

pytest_plugins = ['test_session_controller']


def mixed_page(owner):
    page = setup_composer(owner)
    active = deepcopy(owner.transport.active.return_value)
    active["session"]["broadcast"]["native_delivery"] = {}
    owner.transport.active.return_value = active
    owner._session = deepcopy(active["session"])
    prototype = deepcopy(page['entries'][0])
    kinds = ['playback_observed', 'dj_moment', 'dj_publication', 'dj_silence']
    for offset, kind in enumerate(kinds, 3):
        row = deepcopy(prototype)
        row.update(entry_id=f'retained-{kind}', order=offset, kind=kind)
        if kind == 'playback_observed':
            row['playback'] = {'coverage': 'observed_playing_not_full_listen',
                'title': '<img> literal 🎵', 'artist': 'Observed artist', 'album': 'Observed album'}
        if kind in {'dj_publication', 'dj_silence'}:
            row.update(text=None, speech_available=False)
        page['entries'].append(row)
    owner.transport.capabilities.return_value = deepcopy(owner._caps)
    return page


def refresh(owner, backend):
    owner.refresh();backend.jobs.pop()()


def test_all_typed_retained_entries_keep_server_order_but_never_become_native_moments(controller):
    owner, backend = controller
    page = mixed_page(owner); original = deepcopy(page)
    refresh(owner, backend)
    state = owner.state
    assert [r['entry_id'] for r in state['retained_flow']] == [r['entry_id'] for r in page['entries']]
    assert len(state['conversation']) == 2
    assert not state['moments']
    assert all(r['historical_view_only'] and not r['current_display_allowed'] for r in state['retained_flow'])
    played = state['retained_flow'][2]['historical_playback']
    assert played['title'] == '<img> literal 🎵'
    assert page == original
    state['retained_flow'].clear()
    assert len(owner.state['retained_flow']) == 6


def test_retained_reading_does_not_require_free_input_authority(controller):
    owner, backend = controller
    mixed_page(owner)
    owner.transport.capabilities.return_value['capabilities']['ask_dj_contextual_dialogue'] = False
    refresh(owner, backend)
    assert len(owner.state['retained_flow']) == 6
    assert not owner.state['composer_available']
    owner.transport.question.assert_not_called()


@pytest.mark.parametrize('withdrawal', ['foreground', 'profile', 'capability', 'denied', 'expiry', 'empty'])
def test_retained_flow_withdrawal_has_no_hidden_body_cache(controller, withdrawal):
    owner, backend = controller
    page = mixed_page(owner)
    refresh(owner, backend)
    if withdrawal == 'foreground': owner.setForeground(False)
    elif withdrawal == 'profile':
        backend.cfg.active_profile_id = 'another-profile';owner.invalidate()
    elif withdrawal == 'capability':
        owner.transport.capabilities.return_value['capabilities']['session_conversation_history'] = False
        refresh(owner, backend)
    elif withdrawal == 'denied':
        from djconnect_pi.session_transport import SessionError
        owner.transport.timeline.side_effect = SessionError('denied');refresh(owner, backend)
    elif withdrawal == 'empty':
        page['entries'] = [];refresh(owner, backend)
    else:
        for row in owner._retained_flow: row['retained_until'] = '2000-01-01T00:00:00Z'
        owner._expire()
    assert not owner.state['retained_flow']


def test_anchor_receipt_reconciliation_keeps_other_typed_rows_and_exact_roles(controller):
    owner, backend = controller
    page = mixed_page(owner)
    # Keep a non-conversation tail; exact receipt is found only in fresh anchor.
    tail, calls = anchor_transport(owner, page)
    tail['entries'] = deepcopy(page['entries'][2:])
    owner.sendQuestion('Explicit question');backend.jobs.pop()()
    assert owner.state['question_status'] == 'accepted'
    assert len(owner.state['conversation']) == 2 and len(owner.state['retained_flow']) == 6
    assert len(calls) == 1 and not owner.state['moments']


def test_tail_larger_than_requested_twenty_rows_is_rejected(controller):
    owner, backend = controller
    page = mixed_page(owner)
    for index in range(7, 22):
        row = deepcopy(page['entries'][0]);row.update(entry_id=f'large-{index}', order=index)
        page['entries'].append(row)
    refresh(owner, backend)
    assert not owner.state['retained_flow']
    assert not owner.state['conversation']
    assert owner.state['question_status'] != 'accepted'


def test_retained_playback_cannot_replace_current_runtime_metadata(controller):
    owner, backend = controller
    mixed_page(owner)
    owner.transport.active.return_value['session']['broadcast']['playback'] = {
        'state': 'playing', 'item_id': 'current-runtime-track', 'title': 'CURRENT Runtime title',
        'artist': 'Current artist', 'updated_at': '2026-10-20T00:00:00Z'}
    refresh(owner, backend)
    assert owner.state['playback']['title'] == 'CURRENT Runtime title'
    assert owner.state['retained_flow'][2]['historical_playback']['title'] == '<img> literal 🎵'
    owner.transport.question.assert_not_called()


@pytest.mark.parametrize('operation', ['refresh', 'question'])
def test_retained_rows_expired_on_gui_queue_never_publish_in_flow(controller, operation):
    owner, backend = controller
    page = mixed_page(owner);host = clock_fixture(owner)
    for row in page['entries']:
        row['retained_until'] = datetime.fromtimestamp(host.wall + 4, UTC).isoformat()
    queued = []
    owner._ready.disconnect(owner._apply);owner._ready.connect(queued.append)
    if operation == 'question': owner.sendQuestion('One explicit question')
    else: owner.refresh()
    backend.jobs.pop()()
    assert queued[0]['retained_flow']
    observed = []
    owner.changed.connect(lambda: observed.append(len(owner.state['retained_flow'])))
    host.tick = 5;owner._apply(queued.pop())
    assert not owner.state['retained_flow'] and not owner.state['conversation']
    assert observed and not any(observed)
