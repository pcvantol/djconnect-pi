import json
from copy import deepcopy
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from djconnect_pi.session_history_view import (
    opened_entry,
    presented_history,
    search_page,
    sources,
)
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
    assert any(urlsplit(link).hostname == 'musicbrainz.org' for link in links)
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


def test_server_highlights_keep_literal_markup_emoji_and_linebreaks_without_duplicate_prose():
    from PySide6.QtGui import QTextDocument
    data = search_fixture()
    body = '<img src="https://untrusted.invalid/leak"> & 😀\nhello & goodbye'
    data['matches'][0]['text'] = body
    start = len(body[:body.index('😀')].encode('utf-16-le')) // 2
    data['matches'][0]['highlights'] = [
        {'start_utf16': start + 3, 'length_utf16': 5},
        {'start_utf16': start, 'length_utf16': 8},
        {'start_utf16': start, 'length_utf16': 2},
    ]
    parsed = search_page(data, data['session_id'], data['query'])
    row = parsed['matches'][0]
    assert row['text'] == body and 'highlighted_text' not in data['matches'][0]
    markup = row['highlighted_text']
    assert '<img' not in markup and '<a' not in markup and '<br>' in markup
    assert markup.count('<b><u>') == 1  # overlapping ranges are merged
    document = QTextDocument()
    document.setHtml(markup)
    assert document.toPlainText() == body


def test_search_rejects_highlight_that_splits_emoji_surrogate_pair():
    data = search_fixture()
    data['matches'][0]['text'] = 'A😀B'
    data['matches'][0]['highlights'] = [{'start_utf16': 2, 'length_utf16': 1}]
    with pytest.raises(SessionError):
        search_page(data, data['session_id'], data['query'])


def test_emphasis_follows_server_range_without_local_query_matching():
    data = search_fixture()
    data['matches'][0]['text'] = 'before 😀 after'
    data['matches'][0]['highlights'] = [{'start_utf16': 7, 'length_utf16': 2}]
    parsed = search_page(data, data['session_id'], data['query'])
    assert parsed['matches'][0]['highlighted_text'] == 'before <b><u>😀</u></b> after'


def test_historical_playback_fields_preserve_observation_without_promoting_it():
    row = {'kind': 'playback_observed', 'historical_view_only': True, 'current_display_allowed': False,
           'text': 'Original joined observation', 'requires_spotify_attribution': True,
           'playback': {'coverage': 'observed_playing_not_full_listen', 'title': '<img> 🎧',
                        'artist': 'Observed artist', 'album': 'Observed album',
                        'source_url': 'https://open.spotify.com/track/0000000000000000000001',
                        'artwork_url': 'https://unqualified.invalid/image', 'position_ms': 9000}}
    shown = presented_history({'entries': [row]})['entries'][0]
    assert shown['historical_playback'] == {'title': '<img> 🎧', 'artist': 'Observed artist', 'album': 'Observed album'}
    assert shown['text'] == row['text'] and shown['current_display_allowed'] is False
    assert shown['spotify_source_url'] == row['playback']['source_url']
    assert 'artwork_url' not in shown['historical_playback'] and 'position_ms' not in shown['historical_playback']
    assert 'historical_playback' not in row


@pytest.mark.parametrize('playback', [None, {}, {'coverage': 'full_listen'},
    {'coverage': 'observed_playing_not_full_listen', 'title': []},
    {'coverage': 'observed_playing_not_full_listen', 'title': 'x' * 513}])
def test_malformed_observed_playback_does_not_gain_typed_presentation(playback):
    with pytest.raises(SessionError):
        presented_history({'entries': [{'kind': 'playback_observed', 'playback': playback}]})


def test_empty_observation_keeps_original_text_fallback():
    row = {'kind': 'playback_observed', 'playback': {'coverage': 'observed_playing_not_full_listen'}, 'text': 'Original observation'}
    shown = presented_history({'entries': [row]})['entries'][0]
    assert shown['historical_playback'] == {} and shown['text'] == row['text']


@pytest.mark.parametrize('flag', [None, False])
def test_released_spotify_history_without_native_flag_requires_packaged_logo(flag):
    page = timeline_fixture()
    row = page['entries'][2]
    if flag is None: row.pop('requires_spotify_attribution', None)
    else: row['requires_spotify_attribution'] = flag
    original = deepcopy(page)
    rendered = presented_history(page)['entries'][2]
    assert rendered['requires_spotify_attribution'] is True
    assert urlsplit(rendered['spotify_source_url']).hostname == 'open.spotify.com'
    assert page == original


def test_spotify_history_link_alone_requires_attribution_and_invalid_provider_link_fails_closed():
    page = timeline_fixture()
    row = page['entries'][2]
    row['source_attribution']['provider'] = ''
    assert presented_history(page)['entries'][2]['requires_spotify_attribution']
    row['source_attribution'].update(provider='Spotify', url='https://example.org/no-spotify-source')
    with pytest.raises(SessionError): presented_history(page)


@pytest.mark.parametrize('flag', ['true', 1, None])
def test_malformed_historical_spotify_flag_does_not_become_a_display_grant(flag):
    page = timeline_fixture();page['entries'][2]['requires_spotify_attribution'] = flag
    with pytest.raises(SessionError): presented_history(page)
