import json
from copy import deepcopy
from pathlib import Path

import pytest

from djconnect_pi.session_projection import active_session, history_page, live_moments
from djconnect_pi.session_transport import SessionError


def test_actual_producer_retention_kinds_decode_without_relabelling():
    payload = json.loads((Path(__file__).parent / 'fixtures/session_core/retention-v2-touch.json').read_text())
    tail = payload['tail_window']
    parsed = history_page(tail, session_id=tail['session']['session_id'], now=1792324800)
    assert parsed == tail
    assert {row.get('archive_basis') for row in parsed['entries'] if row['kind'] == 'dj_moment'}
    assert live_moments({'session_id':tail['session']['session_id'], 'runtime_state':'active', 'broadcast':tail}) == []


def test_expired_or_wrong_owner_history_is_not_rendered():
    payload = json.loads((Path(__file__).parent / 'fixtures/session_core/retention-v2-touch.json').read_text())['tail_window']
    with pytest.raises(SessionError):
        history_page(payload, session_id='other-owner', now=1792324800)
    with pytest.raises(SessionError, match='unavailable'):
        history_page(payload, session_id=payload['session']['session_id'], now=999999999999)


def live_fixture():
    return {'session_id':'s1','runtime_state':'active','broadcast':{
        'session_flow':{'items':[{'item_type':'dj_moment','moment_id':'m1'}]},
        'dj_moments':[{'moment_id':'m1','session_id':'s1','title':'Direction','content':'Confirmed body',
                       'presentation_intent':{'visibility':'owner_only'}}],
        'native_delivery':{'schema_version':1,'session_id':'s1','revision':'r1','revocation_scope':'session',
            'current_moment_id':'m1','active_flow_moment_ids':['m1'],'admissions':[{
                'moment_id':'m1','qualification':'qualified','executable_actions':[],
                'current_display_allowed':True,'active_flow_display_allowed':True,
                'source_expires_at':None,'display_expires_at':'2026-10-20T01:00:00+00:00'}]}}}


def test_current_grant_expires_independently_of_historical_permission():
    data=live_fixture()
    assert live_moments(data,now=0)[0]['body']=='Confirmed body'
    assert live_moments(data,now=9999999999)==[]
    data['broadcast']['native_delivery']['revocation_scope']='subscription'
    assert live_moments(data,now=0)==[]


@pytest.mark.parametrize('mutation',[
    lambda s:s['broadcast']['native_delivery'].update(current_moment_id=[]),
    lambda s:s['broadcast'].update(session_flow=None),
    lambda s:s['broadcast'].update(dj_moments={}),
    lambda s:s['broadcast']['native_delivery'].update(admissions=None),
    lambda s:s['broadcast']['native_delivery'].update(active_flow_moment_ids=[{}]),
    lambda s:s['broadcast']['native_delivery'].update(active_flow_moment_ids=None),
])
def test_malformed_native_authority_is_closed_without_crashing(mutation):
    data=deepcopy(live_fixture());mutation(data)
    assert live_moments(data,now=0)==[]


@pytest.mark.parametrize("state", ["opening", "ending", "ended", "interrupted"])
def test_lifecycle_transitions_never_render_live_content(state):
    data = live_fixture()
    data["runtime_state"] = state
    data["broadcast"]["session"] = {"session_id": data["session_id"]}
    decoded = active_session({"success": True, "session": data})
    assert live_moments(decoded, now=0) == []
    if state in {"ended", "interrupted"}:
        assert decoded == {}
    else:
        assert decoded["runtime_state"] == state


@pytest.mark.parametrize('field,value', [('revision', None), ('revision', ''), ('next_cursor', []), ('next_cursor', 'x' * 8193)])
def test_timeline_rejects_missing_revision_or_malformed_cursor(field, value):
    from test_session_history_view import timeline_fixture
    payload = timeline_fixture()
    payload[field] = value
    with pytest.raises(SessionError):
        history_page(payload, session_id=payload['session']['session_id'])
