"""Actual pinned Core Runtime frames; these are not live provider/HA qualification."""
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from djconnect_pi.session_history_view import live_presentations
from djconnect_pi.session_projection import timestamp

ROOT = Path(__file__).parent / 'fixtures/session_core'
RAW = (ROOT / 'native-expressive-snapshots.json').read_bytes()
FRAMES = json.loads(RAW)
CASES = [(family, lang, persona, index)
         for family, languages in FRAMES.items()
         for lang, personas in languages.items()
         for persona, frames in personas.items()
         for index in range(len(frames))]


def producer_frame(family, lang, persona, index):
    snapshot = deepcopy(FRAMES[family][lang][persona][index])
    authority = snapshot['native_delivery']
    current = next((grant for grant in authority['admissions']
                    if grant['moment_id'] == authority['current_moment_id']), None)
    # Freeze at the original presentation time. Never rewrite a wire deadline.
    now = timestamp(current['display_expires_at']) - 1 if current else max(timestamp(row['created_at']) for row in snapshot['dj_moments']) + 1
    return {**snapshot['session'], 'broadcast': snapshot}, now


def test_native_producer_fixture_provenance_matches_immutable_bytes():
    provenance = json.loads((ROOT / 'native-expressive-provenance.json').read_text())
    assert hashlib.sha256(RAW).hexdigest() == provenance['sha256']
    assert provenance['protected_source'] == '8b221d07fe2215d9516d18fe92c832332c7a16ab'
    assert len(CASES) == 200


@pytest.mark.parametrize('family,lang,persona,index', CASES)
def test_published_source_frames_preserve_allowed_prose_and_original_links(family, lang, persona, index):
    session, now = producer_frame(family, lang, persona, index)
    snapshot = session['broadcast']
    authority = snapshot['native_delivery']
    rendered = live_presentations(session, now=now)
    expected = set(authority['active_flow_moment_ids'])
    if authority['current_moment_id']:
        expected.add(authority['current_moment_id'])
    assert {card['moment_id'] for card in rendered} == expected
    for card in rendered:
        original = next(row for row in snapshot['dj_moments'] if row['moment_id'] == card['moment_id'])
        assert card['body'] == original['content']
        assert card['title'] == original['title']
        attribution = original.get('source_attribution', {})
        original_links = [attribution[key] for key in ('url', 'url_previous') if attribution.get(key)]
        assert card['source_links'] == original_links
        displayed_links = {link for source in card['display_sources'] for link in source['links']}
        assert set(original_links) <= displayed_links
        assert card['current'] == (card['moment_id'] == authority['current_moment_id'])
    # Per-Moment authority wins: genre frames can also contain admitted internal Direction.
    rejected = {grant['moment_id'] for grant in authority['admissions'] if grant['qualification'] != 'qualified'}
    assert rejected.isdisjoint({card['moment_id'] for card in rendered})


@pytest.mark.parametrize('family', ['birth', 'formation', 'description', 'edition'])
def test_source_expiry_and_subscription_withdrawal_cannot_restore_producer_copy(family):
    session, now = producer_frame(family, 'nl', 'home_dj', 1)
    assert live_presentations(session, now=now)
    deadline = max(timestamp(g['source_expires_at']) for g in session['broadcast']['native_delivery']['admissions'])
    assert live_presentations(session, now=deadline) == []
    session['broadcast']['native_delivery']['revocation_scope'] = 'subscription'
    assert live_presentations(session, now=now) == []
