from copy import deepcopy
import json
from pathlib import Path

import pytest

from djconnect_pi.session_history_view import opened_entry, presented_history, search_page, sources
from djconnect_pi.session_transport import SessionError


def timeline_fixture():
    return json.loads((Path(__file__).parent / 'fixtures/session_core/retention-v2-touch.json').read_text())['tail_window']


def search_fixture():
    # Synthetic search envelope using an unchanged, producer-pinned retained row.
    tail = timeline_fixture()
    row = deepcopy(tail['entries'][0])
    row['highlights'] = [{'start_utf16': 2, 'length_utf16': 9}]
    return {'success': True, 'schema_version': 2, 'history_contract_version': 2,
        'session_id': tail['session']['session_id'], 'query': 'synthetic',
        'revision': tail['revision'], 'matches': [row], 'returned_count': 1,
        'total_count': 1, 'complete': True, 'next_cursor': None,
        'normalization': 'NFKC-casefold', 'highlight_units': 'utf16'}


def test_attribution_keeps_primary_previous_and_revision_urls_without_changing_prose():
    raw = timeline_fixture()
    original = deepcopy(raw)
    rendered = presented_history(raw)
    assert raw == original
    for original_row, displayed in zip(raw['entries'], rendered['entries']):
        assert displayed['text'] == original_row['text']
    researched = next(row for row in rendered['entries'] if row.get('archive_basis') == 'public_artist_narration_v1')
    links = [link for source in researched['display_sources'] for link in source['links']]
    assert 'https://en.wikipedia.org/w/index.php?oldid=1' in links
    assert 'https://en.wikipedia.org/wiki/Example' in links
    assert any('musicbrainz.org' in link for link in links)
    assert sources({'source_attribution': {'provider':'MusicBrainz','license':'CC0-1.0',
        'url':'https://example.org/current','url_previous':'https://example.org/previous'}})[0]['links'] == ['https://example.org/current','https://example.org/previous']


def test_search_decodes_exact_session_query_and_retained_entry_not_live_permission():
    data = search_fixture()
    parsed = search_page(data, data['session_id'], data['query'])
    assert parsed['matches'][0]['current_display_allowed'] is False
    assert parsed['matches'][0]['historical_view_only'] is True
    assert parsed['matches'][0]['display_sources'][0]['provider'] == 'MusicBrainz'
    with pytest.raises(SessionError):
        search_page(data, 'other-session', data['query'])
    with pytest.raises(SessionError):
        search_page(data, data['session_id'], 'another query')


@pytest.mark.parametrize('mutation', [
    lambda s: s.update(returned_count=8),
    lambda s: s.update(complete=False),
    lambda s: s.update(next_cursor=[]),
    lambda s: s['matches'][0].update(entry_id=[]),
    lambda s: s['matches'][0].update(highlights=[{'start_utf16':0,'length_utf16':999999}]),
    lambda s: s['matches'][0].update(highlights=[{'start_utf16':True,'length_utf16':1}]),
    lambda s: s['matches'][0].update(historical_view_only=False),
])
def test_malformed_search_never_reaches_presentation(mutation):
    data = search_fixture()
    mutation(data)
    with pytest.raises(SessionError):
        search_page(data, data['session_id'], data['query'])


def test_navigation_revalidates_exact_entry_and_is_never_playback():
    tail = timeline_fixture()
    row = tail['entries'][0]
    data = {'success':True,'schema_version':2,'history_contract_version':2,
        'session':tail['session'],'entry':row,'read_only':True,'navigation_only':True}
    assert opened_entry(data, row['session_id'], row['entry_id']) == data
    with pytest.raises(SessionError):
        opened_entry(data, row['session_id'], 'foreign-entry')
    data['navigation_only'] = False
    with pytest.raises(SessionError):
        opened_entry(data, row['session_id'], row['entry_id'])


def test_spotify_row_needs_valid_source_url_and_no_foreign_credentials():
    tail = timeline_fixture()
    row = tail['entries'][0]
    row['requires_spotify_attribution'] = True
    with pytest.raises(SessionError):
        presented_history(tail)
    row['playback'] = {'source_url': 'https://open.spotify.com/track/exact-source'}
    assert presented_history(tail)['entries'][0]['spotify_source_url'].endswith('exact-source')
    row['playback']['source_url'] = 'https://user:password@open.spotify.com/track/x'
    with pytest.raises(SessionError):
        presented_history(tail)
