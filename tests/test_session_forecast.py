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
    return {'session_id': value['session_id'], 'runtime_state': 'active', 'broadcast': {
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
