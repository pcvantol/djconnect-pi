"""Profile-bound text adoption; no model/provider/HA calls in this suite."""
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from test_session_controller import clock_fixture, enable_search
from test_session_history_view import timeline_fixture
from test_session_projection import live_fixture

from djconnect_pi.session_history_view import accepted_question
from djconnect_pi.session_transport import SessionError

pytest_plugins = ["test_session_controller"]


def setup_composer(owner):
    clock_fixture(owner)
    enable_search(owner)
    owner._caps['capabilities']['ask_dj_contextual_dialogue'] = True
    owner._caps['contract_versions']['ask_dj_contextual_dialogue'] = 1
    active = live_fixture()
    active['broadcast']['session'] = {'session_id': active['session_id']}
    owner._session = active
    owner.transport.active.return_value = {'success': True, 'session': active}
    page = timeline_fixture()
    page['session']['session_id'] = active['session_id']
    page['entries'] = page['entries'][:2]
    for index, row in enumerate(page['entries']):
        row.update(session_id=active['session_id'], kind='conversation_user' if index == 0 else 'conversation_dj',
            turn_id='confirmed-turn', input_type='text', role='user' if index == 0 else 'assistant', text='From the server history')
    owner.transport.timeline = Mock(return_value=page)
    def answer(binding, request):
        for row in page["entries"]:
            if row["kind"] in {"conversation_user", "conversation_dj"}:
                row["client_message_id"] = request["client_message_id"]
        context = {'session_id': request['session_id']}
        selected = request.get('selected') or {}
        if selected:
            context[selected['kind']] = {k: v for k, v in selected.items() if k != 'kind'}
        return {'success': True, 'owner_profile_id': binding.resolved_profile_id,
            'client_message_id': request['client_message_id'], 'text': 'Never render this transient copy',
            'audio_url': 'https://fixture.invalid/audio', 'playback_actions': [{'action':'play'}],
            'conversation': {'schema_version':1,'turn_id':'confirmed-turn','context':context,
                'entry_ids':[row['entry_id'] for row in page['entries'] if row['kind'] in {'conversation_user', 'conversation_dj'}],'input_type':'text'}}
    owner.transport.question = Mock(side_effect=answer)
    return page


def test_pinned_real_receipt_decodes_exact_owner_client_identity_and_selected_reference():
    root = Path(__file__).parent / 'fixtures/session_core'
    raw = (root / 'contextual-dialogue-v1.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == '9be892d55c8aaee4871e54ac68ed04945fb0676ce5472e2091a83ee66b2151a8'
    fixture = next(f for f in json.loads(raw)['fixtures'] if f['case'] == 'active-credit')
    body = fixture['body']; context = body['conversation']['context']
    request = {'session_id': context['session_id'], 'client_message_id':body['client_message_id'],
        'selected': {'kind': 'selected_moment', **context['selected_moment']}}
    binding = SimpleNamespace(resolved_profile_id=body['owner_profile_id'])
    assert accepted_question(body, binding, request)['turn_id'] == body['conversation']['turn_id']
    foreign = deepcopy(body); foreign['owner_profile_id'] = 'other-owner'
    with pytest.raises(SessionError, match='uncertain'):
        accepted_question(foreign, binding, request)


def test_composer_requires_current_explicit_personal_profile_and_known_contract(controller):
    owner, backend = controller
    assert not owner.sendQuestion('question') and not backend.jobs
    setup_composer(owner)
    assert owner.state['composer_available']
    owner._caps['contract_versions']['ask_dj_contextual_dialogue'] = 2
    assert not owner.sendQuestion('question')
    owner._caps['contract_versions']['ask_dj_contextual_dialogue'] = 1
    backend.cfg.private_session = True
    assert not owner.sendQuestion('question')
    backend.cfg.private_session = False
    backend.cfg.active_profile_id = 'different-mapping'
    assert not owner.sendQuestion('question') and not backend.jobs


def test_explicit_send_reads_confirmed_conversation_not_transient_response_and_never_replays(controller):
    owner, backend = controller
    page = setup_composer(owner)
    assert owner.sendQuestion('A deliberate question')
    assert not owner.sendQuestion('A duplicate tap')
    assert owner.state['conversation'] == [] and owner.state['question_status'] == 'sending'
    backend.jobs.pop()()
    owner.transport.question.assert_called_once()
    assert owner.state['question_status'] == 'accepted'
    assert [row['text'] for row in owner.state['conversation']] == [row['text'] for row in page['entries']]
    assert owner.state['session_id'] == 's1'


def test_timeout_keeps_runtime_but_never_optimistically_adds_a_bubble(controller):
    owner, backend = controller
    setup_composer(owner)
    owner.transport.question.side_effect = SessionError('uncertain')
    owner.sendQuestion('Deliberate question')
    backend.jobs.pop()()
    assert owner.state['question_status'] == 'uncertain' and owner.state['conversation'] == []
    assert owner.state['session_id'] == 's1'
    owner.transport.question.assert_called_once()


def test_post_accepted_history_failure_is_distinct_from_unconfirmed_delivery(controller):
    owner, backend = controller
    setup_composer(owner)
    owner.transport.timeline.side_effect = SessionError('offline')
    owner.sendQuestion('Question')
    backend.jobs.pop()()
    assert owner.state['question_status'] == 'accepted_unavailable'
    assert owner.state['conversation'] == []
    owner.transport.question.assert_called_once()


def test_profile_or_background_invalidation_discards_late_question_result(controller):
    owner, backend = controller
    setup_composer(owner)
    owner.sendQuestion('Question')
    work = backend.jobs.pop()
    owner.setForeground(False)
    work()
    assert owner.state['conversation'] == [] and owner.state['question_status'] == ''
    assert not owner.state['session_id']


def test_reference_is_frozen_in_the_question_and_not_inferred_from_visible_text(controller):
    owner, backend = controller
    page = setup_composer(owner)
    owner._timeline = page
    row = page['entries'][0]
    owner.selectEntry('s1', row['entry_id'])
    assert owner.sendQuestion('What about that?')
    backend.jobs.pop()()
    request = owner.transport.question.call_args.args[1]
    assert request['selected'] == {'kind': 'selected_entry', 'session_id': 's1', 'entry_id': row['entry_id']}
    assert owner.state['selection'] == {}


def test_context_change_after_acceptance_cannot_present_an_answer_in_another_session(controller):
    owner, backend = controller
    setup_composer(owner)
    new = deepcopy(owner._session)
    new['session_id'] = 'replacement-session'
    new['broadcast']['session']['session_id'] = new['session_id']
    owner.transport.active.return_value = {'success': True, 'session': new}
    owner.sendQuestion('A question')
    backend.jobs.pop()()
    assert owner.state['conversation'] == [] and owner.state['session_id'] == ''
    assert owner.state['question_status'] == 'accepted_unavailable'
    owner.transport.question.assert_called_once()


def test_selection_expiry_withdraws_the_reference_before_another_touch_can_submit_old_draft(controller):
    owner, _ = controller
    setup_composer(owner)
    host = clock_fixture(owner)
    grant = owner._session['broadcast']['native_delivery']['admissions'][0]
    grant['source_expires_at'] = '2026-10-20T00:00:05Z'
    owner.selectMoment('s1', 'm1')
    assert owner.state['selection']['moment_id'] == 'm1'
    invalidated = Mock()
    owner.selectionInvalidated.connect(invalidated)
    host.tick = 6
    owner._expire()
    assert owner.state['selection'] == {}
    invalidated.assert_called_once()


def test_history_moment_rows_never_become_current_conversation_bubbles(controller):
    owner, backend = controller
    page = setup_composer(owner)
    moment = deepcopy(timeline_fixture()['entries'][0])
    moment.update(session_id='s1', entry_id='unrelated-history-moment', order=3)
    page['entries'].append(moment)
    owner.sendQuestion('Question')
    backend.jobs.pop()()
    assert {row['kind'] for row in owner.state['conversation']} == {'conversation_user', 'conversation_dj'}
    assert owner.state['question_status'] == 'accepted'


def test_large_draft_and_shared_or_guest_mapping_never_send(controller):
    owner, backend = controller
    setup_composer(owner)
    assert not owner.sendQuestion('x' * 4001)
    backend.cfg.active_profile_privacy_mode = 'shared'
    assert not owner.sendQuestion('Question')
    backend.cfg.active_profile_privacy_mode = 'private'
    backend.cfg.active_profile_type = 'guest'
    assert not owner.sendQuestion('Question')
    backend.cfg.active_profile_type = 'household'
    assert not owner.state['composer_available']
    assert not owner.sendQuestion('Question')
    owner.transport.question.assert_not_called()


@pytest.mark.parametrize('changes', [{'role':'user'}, {'text':{'unsafe':'object'}}, {'input_type':'unknown'}, {'turn_id':None}])
def test_malformed_history_role_or_body_never_becomes_a_confirmed_answer(controller, changes):
    owner, backend = controller
    page = setup_composer(owner)
    page['entries'][1].update(changes)
    owner.sendQuestion('Question')
    backend.jobs.pop()()
    assert owner.state['question_status'] == 'accepted_unavailable'
    assert owner.state['conversation'] == []


def test_older_conversation_rows_are_not_mistaken_for_the_new_question_receipt(controller):
    owner, backend = controller
    page = setup_composer(owner)
    original = owner.transport.question.side_effect
    def accepted_without_new_archive(binding, request):
        response = original(binding, request)
        response['conversation']['entry_ids'] = []
        for row in page['entries']:
            row['client_message_id'] = 'a-different-older-question'
        return response
    owner.transport.question.side_effect = accepted_without_new_archive
    owner.sendQuestion('New question')
    backend.jobs.pop()()
    assert owner.state['conversation']  # valid older history remains visible as history
    assert owner.state['question_status'] == 'accepted_unavailable'
    owner.transport.question.assert_called_once()


def test_acceptance_status_from_an_earlier_session_does_not_follow_replacement(controller):
    owner, backend = controller
    setup_composer(owner)
    owner._question_status = 'accepted'
    replacement = deepcopy(owner._session)
    replacement['session_id'] = 'replacement'
    replacement['broadcast']['session']['session_id'] = replacement['session_id']
    owner.transport.active.return_value = {'success':True,'session':replacement}
    owner.refresh()
    backend.jobs.pop()()
    assert owner.state['session_id'] == 'replacement' and owner.state['question_status'] == ''
    assert owner.state['conversation'] == []


def test_refresh_and_end_remain_available_during_a_question_and_late_reply_cannot_revive_session(controller):
    owner, backend = controller
    setup_composer(owner)
    owner.transport.capabilities.return_value = deepcopy(owner._caps)
    owner.transport.end = Mock()
    assert owner.sendQuestion('A deliberate question')
    question = backend.jobs.pop()
    assert owner.questionBusy and not owner.busy
    owner.refresh()
    read = backend.jobs.pop()
    assert owner.busy and not owner.lifecycleBusy
    owner.end('s1')
    end = backend.jobs.pop()
    assert owner.lifecycleBusy
    owner.end('s1')
    assert not backend.jobs  # no repeated lifecycle write
    owner.transport.active.return_value = {'success': True, 'session': None}
    end()
    read()
    question()
    assert not owner.state['session_id'] and owner.state['conversation'] == []
    assert owner.state['question_status'] == '' and not owner.questionBusy
    owner.transport.end.assert_called_once()
    owner.transport.question.assert_not_called()  # revoked before dispatch


@pytest.mark.parametrize('question_first', [True, False])
def test_concurrent_refresh_is_reconciled_by_a_read_without_reposting(controller, question_first):
    owner, backend = controller
    setup_composer(owner)
    owner.transport.capabilities.return_value = deepcopy(owner._caps)
    assert owner.sendQuestion('One question')
    question = backend.jobs.pop()
    owner.refresh()
    read = backend.jobs.pop()
    for job in [question, read] if question_first else [read, question]:
        job()
    assert len(backend.jobs) == 1  # one new read after both snapshots, no write replay
    backend.jobs.pop()()
    assert not backend.jobs and owner.state['session_id'] == 's1'
    assert len(owner.state['conversation']) == 2
    owner.transport.question.assert_called_once()
    assert not owner.questionBusy and not owner.busy


@pytest.mark.parametrize('withdrawal', ['replacement', 'capability', 'expiry', 'end_failure'])
def test_late_question_cannot_restore_withdrawn_authority(controller, withdrawal):
    owner, backend = controller
    setup_composer(owner)
    owner.transport.capabilities.return_value = deepcopy(owner._caps)
    if withdrawal == 'expiry':
        host = clock_fixture(owner)
        grant = owner._session['broadcast']['native_delivery']['admissions'][0]
        grant['source_expires_at'] = '2026-10-20T00:00:05Z'
        owner.selectMoment('s1', 'm1')
    owner.sendQuestion('One question')
    question = backend.jobs.pop()
    if withdrawal == 'expiry':
        host.tick = 6
        owner._expire()
    elif withdrawal == 'end_failure':
        owner.transport.end = Mock(side_effect=SessionError('uncertain'))
        owner.end('s1')
        backend.jobs.pop()()
    else:
        if withdrawal == 'replacement':
            replacement = deepcopy(owner._session)
            replacement['session_id'] = 'replacement'
            replacement['broadcast']['session']['session_id'] = 'replacement'
            owner.transport.active.return_value = {'success': True, 'session': replacement}
        else:
            owner.transport.capabilities.return_value = {'capabilities': {}, 'contract_versions': {}}
        owner.refresh()
        backend.jobs.pop()()
    before = deepcopy(owner.state)
    question()
    assert owner.state == before
    assert not owner.questionBusy and not backend.jobs
    owner.transport.question.assert_not_called()


def test_real_worker_pools_allow_end_to_complete_before_blocked_question_returns(controller):
    # Run in a fresh Qt process: unrelated backend tests leave native timers alive.
    import os
    import subprocess
    import sys
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from PySide6.QtCore import QCoreApplication
    from PySide6.QtTest import QTest

    if not os.environ.get("PI_SESSION_WORKER_PROBE"):
        env = {**os.environ, "PI_SESSION_WORKER_PROBE": "1"}
        completed = subprocess.run([sys.executable, "-m", "pytest", __file__ + "::test_real_worker_pools_allow_end_to_complete_before_blocked_question_returns", "-q"], env=env, capture_output=True, text=True, timeout=20, check=False)
        assert completed.returncode == 0, completed.stdout + completed.stderr
        return
    owner, backend = controller
    setup_composer(owner)
    entered, release, ended = Event(), Event(), Event()
    original = owner.transport.question.side_effect
    def blocking_question(binding, value):
        entered.set()
        assert release.wait(3)
        return original(binding, value)
    def end(binding, value):
        ended.set()
    owner.transport.question.side_effect = blocking_question
    owner.transport.end = Mock(side_effect=end)
    owner.transport.active.return_value = {'success': True, 'session': None}
    with ThreadPoolExecutor(max_workers=1) as questions, ThreadPoolExecutor(max_workers=2) as controls:
        backend._question_executor = questions
        backend._session_executor = controls
        try:
            assert owner.sendQuestion('Question')
            assert entered.wait(1)
            owner.end('s1')
            assert ended.wait(1), 'End must run before releasing the question'
            for _ in range(100):
                QCoreApplication.processEvents()
                if not owner.busy:
                    break
                QTest.qWait(5)
            assert not owner.busy and not owner.state['session_id']
            assert owner.questionBusy
        finally:
            release.set()
    QCoreApplication.processEvents()
    assert not owner.questionBusy and owner.state['conversation'] == []
    owner.transport.question.assert_called_once()
    owner.transport.end.assert_called_once()


def test_question_denial_revokes_a_concurrent_read_instead_of_reconciling_private_content(controller):
    owner, backend = controller
    setup_composer(owner)
    owner.transport.capabilities.return_value = deepcopy(owner._caps)
    owner.transport.question.side_effect = SessionError('denied')
    owner.sendQuestion('One question')
    question = backend.jobs.pop()
    owner.refresh()
    read = backend.jobs.pop()
    question()
    read()
    assert not owner.state['session_id'] and not owner.state['conversation']
    assert owner.state['error'] == 'denied' and not backend.jobs
    owner.transport.question.assert_called_once()


@pytest.mark.parametrize('question_first', [True, False])
def test_exact_receipt_reconciles_after_concurrent_refresh_and_notifies_only_once(controller, question_first):
    owner, backend = controller
    setup_composer(owner)
    owner.transport.capabilities.return_value = deepcopy(owner._caps)
    confirmed = Mock()
    owner.questionConfirmed.connect(confirmed)
    owner.sendQuestion('One deliberate question')
    question = backend.jobs.pop()
    owner.refresh()
    read = backend.jobs.pop()
    for job in [question, read] if question_first else [read, question]:
        job()
    backend.jobs.pop()()
    assert owner.state['question_status'] == 'accepted'
    confirmed.assert_called_once_with(owner.state['conversation'][1]['entry_id'])
    owner.refresh()
    backend.jobs.pop()()
    assert confirmed.call_count == 1
    owner.transport.question.assert_called_once()


def test_accepted_receipt_survives_unavailable_history_until_exact_fresh_read(controller):
    owner, backend = controller
    setup_composer(owner)
    owner.transport.capabilities.return_value = deepcopy(owner._caps)
    owner.transport.timeline.side_effect = SessionError('offline')
    owner.sendQuestion('Question')
    backend.jobs.pop()()
    assert owner.state['question_status'] == 'accepted_unavailable'
    owner.transport.timeline.side_effect = None
    owner.refresh()
    backend.jobs.pop()()
    assert owner.state['question_status'] == 'accepted'
    owner.transport.question.assert_called_once()


@pytest.mark.parametrize('mutation', ['client', 'turn', 'session', 'partial', 'voice', 'empty'])
def test_fresh_history_cannot_confirm_a_receipt_with_wrong_identity_or_incomplete_text(controller, mutation):
    owner, backend = controller
    page = setup_composer(owner)
    owner.transport.capabilities.return_value = deepcopy(owner._caps)
    owner.transport.timeline.side_effect = SessionError('offline')
    owner.sendQuestion('Question')
    backend.jobs.pop()()
    owner.transport.timeline.side_effect = None
    if mutation == 'partial':
        page['entries'] = page['entries'][:1]
    else:
        key, value = {'client': ('client_message_id', 'another-client'), 'turn': ('turn_id', 'another-turn'),
            'session': ('session_id', 'another-session'), 'voice': ('input_type', 'voice'), 'empty': ('text', '  ')}[mutation]
        page['entries'][1][key] = value
    confirmed = Mock()
    owner.questionConfirmed.connect(confirmed)
    owner.refresh()
    backend.jobs.pop()()
    assert owner.state['question_status'] == 'accepted_unavailable'
    confirmed.assert_not_called()
    owner.transport.question.assert_called_once()


def test_confirmed_receipt_is_forgotten_at_original_retention_deadline(controller):
    owner, backend = controller
    page = setup_composer(owner)
    host = clock_fixture(owner)
    for row in page['entries']:
        row['retained_until'] = '2026-10-20T00:00:05Z'
    owner.sendQuestion('Question')
    backend.jobs.pop()()
    assert owner.state['question_status'] == 'accepted'
    host.tick = 6
    owner._expire()
    assert not owner._question_receipt and owner.state['question_status'] == ''
    assert owner.state['conversation'] == []


def test_refetch_cannot_extend_confirmed_receipt_deadline(controller):
    owner, backend = controller
    page = setup_composer(owner)
    host = clock_fixture(owner)
    owner.transport.capabilities.return_value = deepcopy(owner._caps)
    for row in page['entries']:
        row['retained_until'] = '2026-10-20T00:00:05Z'
    owner.sendQuestion('Question')
    backend.jobs.pop()()
    original_deadline = owner._question_receipt['retained_until']
    for row in page['entries']:
        row['retained_until'] = '2026-10-20T00:00:20Z'
    owner.refresh()
    backend.jobs.pop()()
    assert owner._question_receipt['retained_until'] == original_deadline
    host.tick = 6
    owner._expire()
    assert not owner._question_receipt and owner.state['question_status'] == ''


def test_unknown_delivery_cannot_be_confirmed_by_later_history_without_a_receipt(controller):
    owner, backend = controller
    setup_composer(owner)
    owner.transport.capabilities.return_value = deepcopy(owner._caps)
    owner.transport.question.side_effect = SessionError('uncertain')
    owner.sendQuestion('Question')
    backend.jobs.pop()()
    confirmed = Mock()
    owner.questionConfirmed.connect(confirmed)
    owner.refresh()
    backend.jobs.pop()()
    assert owner.state['question_status'] == 'uncertain'
    assert not owner._question_receipt
    confirmed.assert_not_called()
    owner.transport.question.assert_called_once()


def anchor_transport(owner, page, *, revision=None, reverse_receipt=False):
    tail = deepcopy(page)
    tail['entries'] = []
    anchor_calls = []
    def read(binding, sid, **kwargs):
        if kwargs.get('window') != 'anchor':
            return deepcopy(tail)
        anchor_calls.append(kwargs['anchor_entry_id'])
        response = deepcopy(page)
        if reverse_receipt and kwargs['anchor_entry_id'] == page['entries'][1]['entry_id']:
            response['entries'] = response['entries'][1:]
        response.update(window='anchor', anchor_entry_id=kwargs['anchor_entry_id'], window_limit=20,
            scanned_order_min=1, scanned_order_max=6, scan_complete=True,
            coverage='bounded_saved_entry_window', next_cursor=None)
        if revision:
            response['revision'] = revision
        return response
    owner.transport.timeline = Mock(side_effect=read)
    owner.transport.capabilities.return_value = deepcopy(owner._caps)
    return tail, anchor_calls


def test_receipt_outside_tail_is_found_by_exact_anchor_and_revalidated_without_reposting(controller):
    owner, backend = controller
    page = setup_composer(owner)
    _, calls = anchor_transport(owner, page)
    owner.sendQuestion('Question')
    backend.jobs.pop()()
    assert owner.state['question_status'] == 'accepted'
    assert len(owner.state['conversation']) == 2 and len(calls) == 1
    owner.refresh()
    backend.jobs.pop()()
    assert len(owner.state['conversation']) == 2 and len(calls) == 2
    owner.transport.question.assert_called_once()
    # Withdrawal is authoritative; old anchored prose cannot survive revalidation.
    owner.transport.timeline.side_effect = SessionError('denied')
    owner.refresh()
    backend.jobs.pop()()
    assert not owner.state['session_id'] and not owner.state['conversation']


def test_receipt_array_order_is_not_assumed_to_be_timeline_order(controller):
    owner, backend = controller
    page = setup_composer(owner)
    original = owner.transport.question.side_effect
    def answer(binding, request):
        result = original(binding, request)
        result['conversation']['entry_ids'].reverse()
        return result
    owner.transport.question.side_effect = answer
    _, calls = anchor_transport(owner, page, reverse_receipt=True)
    owner.sendQuestion('Question')
    backend.jobs.pop()()
    assert calls == [page['entries'][1]['entry_id'], page['entries'][0]['entry_id']]
    assert owner.state['question_status'] == 'accepted'


def test_anchor_and_tail_with_different_revision_are_never_combined_or_confirmed(controller):
    owner, backend = controller
    page = setup_composer(owner)
    _, calls = anchor_transport(owner, page, revision='a-new-revision')
    owner.sendQuestion('Question')
    backend.jobs.pop()()
    assert owner.state['conversation'] == [] and owner.state['question_status'] == 'accepted_unavailable'
    owner.refresh()
    backend.jobs.pop()()
    assert len(calls) == 1  # failed discovery is bounded; tail revalidation remains available


@pytest.mark.parametrize('fault', ['withdrawn', 'missing_limit', 'wrong_anchor', 'bad_scan'])
def test_bad_or_withdrawn_anchor_never_becomes_a_receipt_or_repeating_probe(controller, fault):
    owner, backend = controller
    page = setup_composer(owner)
    _, calls = anchor_transport(owner, page)
    read = owner.transport.timeline.side_effect
    def broken(binding, sid, **kwargs):
        response = read(binding, sid, **kwargs)
        if kwargs.get('window') == 'anchor':
            if fault == 'withdrawn':
                raise SessionError('unavailable')
            if fault == 'missing_limit':
                response.pop('window_limit')
            elif fault == 'wrong_anchor':
                response['anchor_entry_id'] = 'other-id'
            else:
                response['scanned_order_max'] = False
        return response
    owner.transport.timeline.side_effect = broken
    owner.sendQuestion('Question')
    backend.jobs.pop()()
    owner.refresh()
    backend.jobs.pop()()
    assert owner.state['conversation'] == [] and owner.state['question_status'] == 'accepted_unavailable'
    assert len(calls) == 1
    owner.transport.question.assert_called_once()


def test_active_session_can_open_full_history_from_beginning_without_a_write(controller):
    owner, backend = controller
    setup_composer(owner)
    owner.readCurrentHistory()
    backend.jobs.pop()()
    owner.transport.timeline.assert_called_once_with(owner.transport.binding(), 's1', window=None, cursor='')
    assert owner.state['timeline']['entries'] and owner.state['timeline']['session']['session_id'] == 's1'
    owner.transport.question.assert_not_called()


@pytest.mark.parametrize('collision', [False, True])
def test_only_same_revision_canonical_ordered_rows_are_merged_from_tail_and_anchor(controller, collision):
    owner, backend = controller
    page = setup_composer(owner)
    tail, _ = anchor_transport(owner, page)
    unrelated = deepcopy(page['entries'][0])
    unrelated.update(entry_id='unrelated-newer-entry', order=1 if collision else 10, turn_id='unrelated-turn')
    tail['entries'] = [unrelated]
    owner.sendQuestion('Question')
    backend.jobs.pop()()
    if collision:
        assert not owner.state['conversation'] and owner.state['question_status'] == 'accepted_unavailable'
    else:
        assert [row['order'] for row in owner.state['conversation']] == [1, 2, 10]
        assert owner.state['question_status'] == 'accepted'


@pytest.mark.parametrize('operation', ['question', 'refresh'])
@pytest.mark.parametrize('stage', ['active', 'tail', 'anchor'])
@pytest.mark.parametrize('withdrawal', ['foreground', 'profile', 'end'])
def test_conversation_read_stops_between_requests_when_its_authority_is_withdrawn(controller, stage, withdrawal, operation):
    owner, backend = controller
    page = setup_composer(owner)
    owner.transport.capabilities.return_value = deepcopy(owner._caps)
    if operation == 'refresh':
        owner.sendQuestion('Earlier explicit question')
        backend.jobs.pop()()
        assert owner.state['question_status'] == 'accepted'
    previous_conversation = deepcopy(owner.state["conversation"])
    active_response = deepcopy(owner.transport.active.return_value)
    reads = []

    def withdraw():
        if withdrawal == 'foreground':
            owner.setForeground(False)
        elif withdrawal == 'profile':
            backend.cfg.active_profile_id = 'different-profile'
        else:
            owner.end('s1')

    def active(binding):
        if stage == 'active':
            withdraw()
        return deepcopy(active_response)

    def timeline(binding, sid, **kwargs):
        reads.append(kwargs.get('window', 'tail'))
        result = deepcopy(page)
        if kwargs.get('window') != 'anchor':
            result['entries'] = []
            if stage == 'tail':
                withdraw()
        else:
            result['entries'] = result['entries'][:1]
            result.update(window='anchor', anchor_entry_id=kwargs['anchor_entry_id'],
                window_limit=20, scanned_order_min=1, scanned_order_max=6, scan_complete=True,
                coverage='bounded_saved_entry_window', next_cursor=None)
            if stage == 'anchor':
                withdraw()
        return result

    owner.transport.active.side_effect = active
    owner.transport.timeline.side_effect = timeline
    if operation == 'question':
        owner.sendQuestion('One explicit question')
    else:
        owner.refresh()
    backend.jobs.pop()()
    assert reads == {'active': [], 'tail': ['tail'], 'anchor': ['tail', 'anchor']}[stage]
    if withdrawal == 'end':
        # Existing retained rows remain until End completes; no late read replaces them.
        assert owner.state['conversation'] == previous_conversation
    else:
        assert not owner.state['conversation']
    assert not owner.state['current_reply']
    owner.transport.question.assert_called_once()
