import json
from copy import deepcopy
from pathlib import Path

import pytest

from djconnect_pi.session_projection import (
    active_session,
    history_page,
    live_moments,
    session_current_idle,
)
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


def test_bulletin_links_preserve_producer_credit_only_during_live_admission():
    from djconnect_pi.session_history_view import live_presentations

    data = live_fixture()
    wire = data["broadcast"]
    admission = wire["native_delivery"]["admissions"][0]
    expiry = "2026-10-19T01:00:00+00:00"
    admission["source_expires_at"] = expiry
    first = {"provider": "CBS", "title": "First release", "license": "CC BY 4.0",
             "url": "https://example.org/first", "published_at": "2026-10-18T10:00:00Z"}
    second = {**first, "title": "Second release", "url": "https://example.org/second"}
    moment = wire["dj_moments"][0]
    moment.update({
        "type": "dj_bulletin", "visibility": "owner_only", "delivery_channels": ["owner"],
        "presentation_intent": {"visibility": "owner_only", "delivery_channels": ["owner"]},
        "generation_metadata": {"bulletin_schema": "1", "context_source": "fixed_rss_metadata_v1"},
        "knowledge_intent": {"type": "dj_bulletin"}, "source_references": ["fixed_rss_metadata_v1"],
        "created_at": "2026-10-18T11:00:00Z", "actions": [], "sources": [first, first, second],
    })
    card, = live_presentations(data, now=0)
    assert card["bulletin_sources"] == [
        {"url": source["url"], "label": "CBS · CC BY 4.0",
         "accessible_label": f"CBS · {source['title']} · CC BY 4.0", "published_at": source["published_at"]}
        for source in (first, second)
    ]
    assert live_presentations(data, now=9999999999) == []
    second["url"] = "https://user:password@example.org/second"
    assert live_presentations(data, now=0) == []


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


def test_session_playback_uses_only_current_renderer_observation():
    from copy import deepcopy

    from djconnect_pi.session_projection import session_playback
    observation = {"state": "paused", "item_id": "observed-id", "title": "<img> 🎧", "artist": "Artist", "album": "Album", "target_name": "Room", "updated_at": "2026-10-20T02:00:00Z", "duration_ms": 180000, "position_ms": 210000, "source_url": "https://open.spotify.com/track/0000000000000000000001"}
    current = {"session_id": "s", "runtime_state": "active", "broadcast": {"session": {"session_id": "s"}, "playback": observation}}
    shown = session_playback(current)
    assert shown["title"] == "<img> 🎧"
    assert shown["time_label"] == "3:00 / 3:00" and shown["progress"] == 1
    assert shown["requires_spotify_attribution"] is True
    assert "artwork_url" not in shown and "up_next" not in shown
    for field, invalid in [("state", []), ("state", "idle"), ("updated_at", "2026-10-20"), ("item_id", ""), ("source_url", "https://open.spotify.com.evil.invalid/track/0000000000000000000001"), ("source_url", "https://open.spotify.com/track/0000000000000000000001?x=1"), ("source_url", 9)]:
        changed = deepcopy(current); changed["broadcast"]["playback"][field] = invalid
        assert session_playback(changed) == {}
    for changed in [{}, {**current, "runtime_state": "ending"}, {**current, "broadcast": {"session": None}}, {**current, "broadcast": {"session": {"session_id": "other"}, "playback": observation}}]:
        assert session_playback(changed) == {}
    for field in ["duration_ms", "position_ms"]:
        changed = deepcopy(current); changed["broadcast"]["playback"][field] = True
        assert "time_label" not in session_playback(changed)


@pytest.mark.parametrize(("field", "value"), [
    ("current_moment_id", "active-moment"),
    ("current_silence_moment_id", "silent-moment"),
    ("session_id", "different-session"),
    ("revision", " "),
    ("revocation_scope", "unknown"),
    ("schema_version", True),
])
def test_current_idle_requires_confirmed_native_scope(field, value):
    native_delivery = {
        "schema_version": 1, "session_id": "current-session", "revocation_scope": "session",
        "revision": "observed", "current_moment_id": None, "current_silence_moment_id": None,
    }
    session = {
        "session_id": "current-session", "runtime_state": "active",
        "broadcast": {
            "session": {"session_id": "current-session", "runtime_state": "active"},
            "native_delivery": native_delivery,
        },
    }
    assert session_current_idle(session)
    native_delivery[field] = value
    assert not session_current_idle(session)
    native_delivery.pop(field)
    assert not session_current_idle(session)


def test_timestamp_reuses_valid_deadlines_without_caching_invalid_input():
    from djconnect_pi.session_projection import _cached_timestamp, timestamp

    _cached_timestamp.cache_clear()
    try:
        value = "2026-11-10T01:00:00+01:00"
        deadline = timestamp(value)
        assert deadline == timestamp("2026-11-10T00:00:00Z")
        assert timestamp(value) == deadline
        assert _cached_timestamp.cache_info().hits == 1
        assert timestamp("2026-11-10T01:00:00") is None
        assert timestamp("not a timestamp") is None
        assert timestamp([]) is None
        assert _cached_timestamp.cache_info().currsize == 2
        for seconds in range(1000):
            timestamp(f"2026-11-10T00:{seconds // 60:02d}:{seconds % 60:02d}Z")
        assert _cached_timestamp.cache_info().currsize == 256
    finally:
        _cached_timestamp.cache_clear()
