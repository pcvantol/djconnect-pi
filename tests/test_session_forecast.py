"""Pinned pure producer projection and closed text-only Pi consumption."""
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from djconnect_pi.session_forecast import ForecastReceiver, projection

ROOT = Path(__file__).parent / 'fixtures/session_core'
RAW = (ROOT / 'forecast-v1.json').read_bytes()
FRAMES = json.loads(RAW)
CAPS = {'capabilities': {'session_forecast': True}, 'contract_versions': {'session_forecast': 1}}


def session(frame):
    value = frame['projection']
    return {'session_id': value['session_id'], 'runtime_state': 'active',
        'selected_mood': 'groove', 'mood_revision': 0, 'selected_presence': 'balanced', 'presence_revision': 0,
        'dj_persona': frame['persona'], 'persona_revision': 0, 'locale': frame['locale'], 'broadcast': {
        'session': {'session_id': value['session_id']}, 'session_forecast': deepcopy(value),
        'playback': {'state': 'playing', 'item_id': value['current_anchor']['item_id'],
                     'title': 'Observed track', 'source_url': value['current_anchor']['source_url'],
                     'updated_at': value['issued_at']}}}


def test_producer_fixture_provenance():
    assert hashlib.sha256(RAW).hexdigest() == json.loads((ROOT / 'forecast-provenance.json').read_text())['sha256']
    assert len(FRAMES) == 20


@pytest.mark.parametrize('frame', FRAMES)
def test_exact_server_text_roles_and_links_survive_without_media(frame):
    value = projection(session(frame), CAPS, frame['now'])
    assert value['summary'] == frame['projection']['summary']
    assert [(row['title'], row['text'], row['claim_type']) for row in value['sections']] == [(row['title'], row['text'], row['claim_type']) for row in frame['projection']['sections']]
    assert value['source_url'] == frame['projection']['current_anchor']['source_url']
    assert 'imagery' not in value


def test_expired_same_revision_cannot_be_revived_or_renewed():
    frame = FRAMES[0]; current = session(frame); now = frame['now']; owner = ForecastReceiver()
    owner.receive(current, CAPS, now)
    assert owner.expire(now + 120)
    owner.receive(current, CAPS, now)  # deliberately rolled-back caller clock
    assert not owner.snapshot()['sections']
    fresh = deepcopy(current); fresh['broadcast']['session_forecast']['revision'] += 1
    owner.receive(fresh, CAPS, now)
    assert owner.snapshot()['sections']
    owner.receive(current, CAPS, now)
    assert not owner.snapshot()['sections']  # revision rollback is not a new grant


def test_same_revision_deadline_is_not_extended():
    frame = FRAMES[0]; current = session(frame); now = frame['now']; owner = ForecastReceiver()
    owner.receive(current, CAPS, now)
    extended = deepcopy(current); p = extended['broadcast']['session_forecast']
    p['issued_at'] = '2026-10-20T02:46:00+00:00'; p['valid_until'] = '2026-10-20T02:48:00+00:00'
    owner.receive(extended, CAPS, now + 60)
    assert owner.expire(now + 120)
    assert not owner.snapshot()['sections']


@pytest.mark.parametrize('withdrawal', ['capability', 'session', 'anchor', 'roles', 'withdrawn', 'deadline', 'subscription'])
def test_withdrawal_and_malformed_projection_never_keep_text(withdrawal):
    frame = FRAMES[0]; current = session(frame); caps = deepcopy(CAPS); owner = ForecastReceiver()
    owner.receive(current, caps, frame['now'])
    p = current['broadcast']['session_forecast']
    if withdrawal == 'capability': caps['capabilities']['session_forecast'] = False
    if withdrawal == 'session': p['session_id'] = 'other'
    if withdrawal == 'anchor': current['broadcast']['playback']['item_id'] = 'other'
    if withdrawal == 'roles': p['sections'][1]['claim_type'] = 'current'
    if withdrawal == 'withdrawn': p['state'] = 'withdrawn'
    if withdrawal == 'subscription': current['broadcast']['broadcast'] = {'subscription_state': 'revoked'}
    if withdrawal == 'deadline': p['valid_until'] = '2026-10-20T03:00:00+00:00'
    owner.receive(current, caps, frame['now'])
    assert not owner.snapshot()['sections']


@pytest.mark.parametrize('change', ['mood','presence','persona','playback','locale','direction'])
def test_equal_forecast_revision_cannot_rebind_to_another_runtime_scope(change):
    frame=FRAMES[0];current=session(frame);owner=ForecastReceiver();now=frame['now']
    owner.receive(current,CAPS,now)
    assert owner.snapshot()['sections']
    changed=deepcopy(current)
    if change=='mood': changed.update(selected_mood='party',mood_revision=1)
    if change=='presence': changed.update(selected_presence='talkative',presence_revision=1)
    if change=='persona': changed.update(dj_persona='club_dj',persona_revision=1)
    if change=='locale': changed['locale']='nl' if current['locale']!='nl' else 'en'
    if change=='direction': changed['session_direction']={'direction':'synthetic-changed-direction'}
    if change=='playback':
        changed['broadcast']['playback']['item_id']='other-qualified-item'
        changed['broadcast']['session_forecast']['current_anchor']['item_id']='other-qualified-item'
    owner.receive(changed,CAPS,now)
    assert not owner.snapshot()['sections']
    # Restoring the old scope cannot revive a withdrawn same-revision frame either.
    owner.receive(current,CAPS,now)
    assert not owner.snapshot()['sections']
    changed['broadcast']['session_forecast']['revision']+=1
    owner.receive(changed,CAPS,now)
    assert owner.snapshot()['sections']


@pytest.mark.parametrize('field',['summary','body','title','order','state'])
def test_equal_revision_cannot_replace_immutable_forecast_content(field):
    frame=FRAMES[0];current=session(frame);owner=ForecastReceiver();now=frame['now']
    owner.receive(current,CAPS,now)
    p=current['broadcast']['session_forecast']
    if field=='summary': p['summary']='Different summary'
    if field=='body': p['sections'][0]['text']='Different body'
    if field=='title': p['sections'][0]['title']='Different title'
    if field=='order': p['sections'].reverse()
    if field=='state': p['state']='limited'
    owner.receive(current,CAPS,now)
    assert not owner.snapshot()['sections']


def test_old_forecast_with_new_scope_cannot_seed_equal_revision_recovery():
    frame=FRAMES[0];current=session(frame);now=frame['now'];owner=ForecastReceiver()
    current['broadcast']['session_forecast']['revision']=2
    owner.receive(current,CAPS,now)
    changed=deepcopy(current);changed.update(dj_persona='club_dj',persona_revision=1)
    changed['broadcast']['session_forecast']['revision']=1
    owner.receive(changed,CAPS,now)
    changed['broadcast']['session_forecast']['revision']=2
    owner.receive(changed,CAPS,now)
    assert not owner.snapshot()['sections']
    changed['broadcast']['session_forecast']['revision']=3
    owner.receive(changed,CAPS,now)
    assert owner.snapshot()['sections']


def test_persona_revision_floor_is_observed_even_when_another_style_value_is_unknown():
    frame=FRAMES[0];current=session(frame);now=frame['now'];owner=ForecastReceiver()
    owner.receive(current,CAPS,now)
    uncertain=deepcopy(current);uncertain.update(selected_mood=None,dj_persona=None,persona_revision=5)
    owner.receive(uncertain,CAPS,now)
    current['broadcast']['session_forecast']['revision']=8
    owner.receive(current,CAPS,now)  # Old Persona revision cannot bypass the independently observed floor.
    assert not owner.snapshot()['sections']
    current.update(dj_persona='club_dj',persona_revision=5)
    current['broadcast']['session_forecast']['revision']=9
    owner.receive(current,CAPS,now)
    assert owner.snapshot()['sections']


@pytest.mark.parametrize('field,counter,value',[('selected_mood','mood_revision','party'),('selected_presence','presence_revision','talkative'),('dj_persona','persona_revision','club_dj')])
def test_known_style_value_cannot_change_under_same_runtime_counter(field,counter,value):
    frame=FRAMES[0];current=session(frame);now=frame['now'];owner=ForecastReceiver()
    owner.receive(current,CAPS,now)
    current[field]=value;current['broadcast']['session_forecast']['revision']=10
    owner.receive(current,CAPS,now)
    assert not owner.snapshot()['sections']
    current[counter]=1;current['broadcast']['session_forecast']['revision']=11
    owner.receive(current,CAPS,now)
    assert owner.snapshot()['sections']


def test_playback_progress_and_observation_ticks_do_not_rebind_forecast():
    frame=FRAMES[0];current=session(frame);now=frame['now'];owner=ForecastReceiver()
    owner.receive(current,CAPS,now);before=owner.snapshot()
    current['broadcast']['playback'].update(position_ms=999,duration_ms=10000,
        updated_at='2026-10-20T02:45:01+00:00',state='paused')
    owner.receive(current,CAPS,now+1)
    assert owner.snapshot()==before


def test_unknown_scope_records_observed_forecast_floor_without_admitting_its_content():
    frame=FRAMES[0];current=session(frame);now=frame['now'];owner=ForecastReceiver()
    owner.receive(current,CAPS,now)
    unknown=deepcopy(current);unknown['dj_persona']=None
    unknown['broadcast']['session_forecast']['revision']=5
    owner.receive(unknown,CAPS,now)
    for revision in (4,5):
        current['broadcast']['session_forecast']['revision']=revision
        owner.receive(current,CAPS,now)
        assert not owner.snapshot()['sections']
    current['broadcast']['session_forecast']['revision']=6
    owner.receive(current,CAPS,now)
    assert owner.snapshot()['sections']


@pytest.mark.parametrize('withdrawal',['expiry','capability','revision'])
def test_withdrawn_forecast_does_not_leave_old_prose_in_an_immutable_comparison_cache(withdrawal):
    frame=FRAMES[0];current=session(frame);now=frame['now'];owner=ForecastReceiver()
    owner.receive(current,CAPS,now)
    body=frame['projection']['sections'][0]['text']
    assert body in json.dumps(vars(owner),ensure_ascii=False)
    if withdrawal=='expiry': owner.expire(now+120)
    elif withdrawal=='capability': owner.receive(current,{},now)
    else:
        current['broadcast']['session_forecast']['revision']=0
        owner.receive(current,CAPS,now)
    assert not owner.snapshot()['sections']
    assert body not in json.dumps(vars(owner),ensure_ascii=False)


@pytest.mark.parametrize('state',['expired','withdrawn','empty'])
def test_explicit_terminal_reads_keep_original_revision_and_state_without_renewing_text(state):
    frame=FRAMES[0];current=session(frame);now=frame['now'];owner=ForecastReceiver()
    owner.receive(current,CAPS,now)
    terminal=deepcopy(current);terminal['broadcast']['session_forecast']['state']=state
    for _ in range(2):
        owner.receive(terminal,CAPS,now)
        assert owner.snapshot()['state']==state
        assert not owner.snapshot()['sections']
        assert not owner.content_signature
    owner.receive(current,CAPS,now)
    assert not owner.snapshot()['sections']
    current['broadcast']['session_forecast']['revision']+=1
    owner.receive(current,CAPS,now)
    assert owner.snapshot()['sections']
