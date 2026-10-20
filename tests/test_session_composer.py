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
    assert owner.state['composer_available']
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
