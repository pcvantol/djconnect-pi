from __future__ import annotations

from pathlib import Path
import json
import subprocess
from unittest.mock import Mock, patch

import pytest
from PySide6.QtCore import QCoreApplication

from djconnect_pi.config import Config, load_config, save_config
from djconnect_pi.app import (
    DJConnectBackend,
    SaveCurrentTrackError,
    _format_duration,
    _format_logs_for_display,
    _read_tail_text,
    cached_image_url,
    media_item_payload,
    parse_ask_dj_messages,
    parse_music_discovery_feed,
    parse_music_dna_profile,
    parse_playlist_items,
    parse_queue_items,
    prepare_media_artwork,
)
from djconnect_pi.ha import AuthenticationError, HAClient, Playback, ProtocolVersionMismatch, StaleBackendAction, UnsupportedBackendCapability


def ensure_app() -> QCoreApplication:
    return QCoreApplication.instance() or QCoreApplication([])


def test_backend_exposes_initial_config(tmp_path: Path) -> None:
    ensure_app()
    with patch("djconnect_pi.config.locale.getlocale", return_value=("nl_NL", "UTF-8")):
        backend = DJConnectBackend(tmp_path / "config.json")

    assert backend.deviceId.startswith("djconnect-raspberry-pi-")
    assert backend.paired is False
    assert backend.busy is False
    assert backend.title == "Niets speelt af"
    assert backend.connectionType == "Niet verbonden"


def test_backend_persists_touch_mood_selector(tmp_path: Path) -> None:
    ensure_app()
    config_path = tmp_path / "config.json"
    backend = DJConnectBackend(config_path)

    backend.setMoodValue(65)

    assert backend.moodValue == 65
    assert backend.cfg.mood == 65
    assert backend.client.cfg.mood == 65
    assert load_config(config_path).mood == 65


def test_backend_clamps_touch_mood_selector(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")

    backend.setMoodValue(400)

    assert backend.moodValue == 100


def test_backend_connection_type_reports_websocket_fast_path(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.cfg.paired = True
    backend.cfg.device_token = "token"
    backend.client.diagnostics = Mock(return_value={"fastPathTransport": "websocket", "websocketConnected": True})  # type: ignore[method-assign]

    assert backend.connectionType == "Local WebSocket fast path"


def test_music_discovery_disabled_backend_reason_shows_empty_state(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.cfg.paired = True
    backend.cfg.device_token = "token"
    backend.client.music_discovery_feed = Mock(return_value={"success": True, "enabled": False, "reason": "music_dna_disabled"})  # type: ignore[method-assign]

    backend._music_discovery_feed_worker()

    backend.client.music_discovery_feed.assert_called_once()
    assert backend.musicDiscoveryItems == []
    assert backend.musicDiscoveryEmptyText == "music_dna_disabled"


def test_music_discovery_accept_enables_music_dna_and_loads_feed(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.cfg.paired = True
    backend.cfg.device_token = "token"
    backend.client.music_dna_settings = Mock(return_value={"success": True, "enabled": True, "profile": {"summary": "Ready"}})  # type: ignore[method-assign]
    backend.client.music_discovery_feed = Mock(return_value={"success": True, "sections": [{"id": "new_for_you", "items": [{"id": "t1", "kind": "track", "title": "Track"}]}]})  # type: ignore[method-assign]

    backend._music_discovery_accept_worker()

    backend.client.music_dna_settings.assert_called_once_with(enabled=True)
    backend.client.music_discovery_feed.assert_called_once()
    assert backend.musicDnaEnabled is True
    assert backend.musicDiscoveryItems[0]["title"] == "Track"


def test_music_discovery_reject_shows_gating_state(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")

    backend.rejectMusicDiscoveryConsent()

    assert backend.musicDiscoveryConsentRejected is True
    assert backend.musicDiscoveryEmptyText


def test_music_discovery_play_ignores_items_without_backend_id(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.cfg.paired = True
    backend.cfg.device_token = "token-1"
    backend.client.music_discovery_play = Mock()  # type: ignore[method-assign]

    backend.playMusicDiscoveryItem(json.dumps({"section_id": "daily"}))

    backend.client.music_discovery_play.assert_not_called()


def test_log_display_uses_compact_touch_prefix() -> None:
    text = _format_logs_for_display(
        "2026-06-13 17:53:49,528 INFO djconnect_pi.app: Started\n"
        "2026-06-13 17:53:50,100 WARNING djconnect_pi.ha: Slow\n"
        "2026-06-13 17:53:51,200 DEBUG djconnect_pi.ha: Payload\n"
        "2026-06-13 17:53:52,300 ERROR djconnect_pi.ha: Failed\n"
    )

    assert "17:53:49 INF djconnect_pi.app: Started" in text
    assert "17:53:50 WRN djconnect_pi.ha: Slow" in text
    assert "17:53:51 DBG djconnect_pi.ha: Payload" in text
    assert "17:53:52 ERR djconnect_pi.ha: Failed" in text
    assert text.splitlines()[0] == "17:53:52 ERR djconnect_pi.ha: Failed"
    assert text.splitlines()[-1] == "17:53:49 INF djconnect_pi.app: Started"
    assert "2026-06-13" not in text


def test_log_tail_reader_caps_large_files(tmp_path: Path) -> None:
    log_file = tmp_path / "client.log"
    log_file.write_text("A" * 200 + "TAIL", encoding="utf-8")

    assert _read_tail_text(log_file, 8) == "AAAATAIL"


def test_duration_format_for_now_playing_progress() -> None:
    assert _format_duration(0) == "0:00"
    assert _format_duration(138) == "2:18"
    assert _format_duration(210) == "3:30"


def test_music_dna_parser_accepts_disabled_profile() -> None:
    parsed = parse_music_dna_profile({"success": True, "enabled": False, "profile": {}})

    assert parsed == {"enabled": False, "summary": "", "sections": []}


def test_music_dna_parser_accepts_enabled_summary_only_profile() -> None:
    parsed = parse_music_dna_profile({"success": True, "enabled": True, "profile": {"summary": "You lean toward warm synths."}})

    assert parsed["enabled"] is True
    assert parsed["summary"] == "You lean toward warm synths."
    assert parsed["sections"] == []


def test_music_dna_parser_renders_optional_blocks_and_hides_empty_cards() -> None:
    parsed = parse_music_dna_profile(
        {
            "success": True,
            "enabled": True,
            "profile": {
                "summary": "Eclectic.",
                "favorite_genres": ["house", "indie"],
                "recent_favorite_tracks": [{"title": "Strobe", "artist": "deadmau5"}],
                "playtime": {"total_seconds": 3661, "formatted_total": "1h 1m", "top_artists": [{"name": "Robyn"}], "top_albums": ["Body Talk"]},
                "listening_rhythm": {"sample_count": 3, "top_daypart": "evening", "top_weekday": "Friday", "distribution": {"evening": 3}},
                "mood_mix": {"sample_count": 1, "chill": 1, "groove": 2, "energy": 3, "party": 4},
                "repeat_magnets": {"eligible": True, "items": [{"title": "Ever Again"}]},
                "explicit_positives": {"eligible": True, "items": ["Saved favorites"]},
                "taste_anchors": {"eligible": True, "items": ["Nordic pop"]},
                "top_tracks_by_range": {"short_term": [{"title": "A", "artist": "B"}]},
                "snapshot_history": [{"title": "July", "favorite_genres": ["house"]}],
                "discovery_feedback": {"accepted": [{"title": "Accepted"}], "negative": [{"title": "Skipped"}]},
                "privacy_dashboard": {"stores_raw_audio": False, "stores_oauth_tokens": False, "raw_counts": {"tracks": 12}, "bearer_token": "secret"},
                "recommendation_signals": [],
            },
        }
    )

    titles = [section["title"] for section in parsed["sections"]]
    assert "Favorite genres" in titles
    assert "Recent favorites" in titles
    assert "Playtime" in titles
    assert "Listening rhythm" in titles
    assert "Mood mix" in titles
    assert "Repeat magnets" in titles
    assert "Accepted signals" in titles
    assert "Taste anchors" in titles
    assert "Top tracks" in titles
    assert "Snapshot history" in titles
    assert "Discovery feedback" in titles
    assert "Privacy dashboard" in titles
    assert "Recommendation signals" not in titles
    assert all(section["lines"] for section in parsed["sections"])
    privacy = next(section for section in parsed["sections"] if section["title"] == "Privacy dashboard")
    assert any("Stores Raw Audio: False" in line for line in privacy["lines"])
    assert not any("secret" in line for line in privacy["lines"])


def test_music_dna_parser_hides_ineligible_blocks() -> None:
    parsed = parse_music_dna_profile(
        {
            "success": True,
            "enabled": True,
            "profile": {
                "summary": "Minimal.",
                "repeat_magnets": {"eligible": False, "reason": "not_enough_data", "items": ["Hidden"]},
                "explicit_positives": {"eligible": False, "items": ["Hidden"]},
                "taste_anchors": {"eligible": False, "items": ["Hidden"]},
            },
        }
    )

    assert parsed["sections"] == []


def test_music_discovery_feed_renders_backend_sections_in_order_without_assumed_ids() -> None:
    parsed = parse_music_discovery_feed(
        {
            "revision": 42,
            "cache": {"hit": True},
            "recent_tracks": [
                {"id": "raw-recent", "kind": "track", "title": "Raw recent", "uri": "spotify:track:raw"}
            ],
            "sections": [
                {
                    "id": "new_for_you",
                    "title": "Nieuw voor jou",
                    "items": [
                        {
                            "id": "t1",
                            "kind": "track",
                            "title": "Track",
                            "artist": "Artist",
                            "uri": "spotify:track:1",
                            "image_url": "https://example.test/t.jpg",
                            "reason": "Because HA said so",
                            "reason_sources": ["seed:artist", "music_dna"],
                            "quality_score": 0.91,
                            "quality_band": "high",
                            "quality_factors": {"seed_fit": 0.9},
                        },
                        {"id": "a1", "kind": "album", "title": "Album", "subtitle": "Artist", "uri": "spotify:album:1", "image_url": "https://example.test/a.jpg"},
                        {"id": "dup", "kind": "track", "title": "Duplicate", "uri": "spotify:track:1"},
                    ],
                },
                {
                    "id": "opaque-backend-section",
                    "title": "Backend order",
                    "items": [
                        {"id": "ar1", "kind": "artist", "title": "Artist", "image_url": "https://example.test/ar.jpg", "based_on_count": 3},
                        {"id": "p1", "kind": "playlist", "title": "Playlist", "context": "For tonight", "uri": "spotify:playlist:1", "image_url": "https://example.test/p.jpg"},
                        {"id": "x1", "kind": "podcast", "title": "Hidden"},
                    ],
                },
            ]
        }
    )

    assert [item["title"] for item in parsed["items"]] == ["Track", "Album", "Duplicate", "Artist", "Playlist", "Hidden"]
    assert [item["kind"] for item in parsed["items"]] == ["track", "album", "track", "artist", "playlist", "podcast"]
    assert parsed["items"][0]["imageUrl"] == "https://example.test/t.jpg"
    assert parsed["items"][0]["reason"] == "Because HA said so"
    assert parsed["items"][0]["reasonSources"] == ["seed:artist", "music_dna"]
    assert parsed["items"][0]["qualityScore"] == 0.91
    assert parsed["items"][0]["qualityBand"] == "high"
    assert parsed["items"][0]["qualityFactors"] == {"seed_fit": 0.9}
    assert parsed["items"][0]["hasReason"] is True
    assert parsed["items"][0]["sectionId"] == "new_for_you"
    assert parsed["items"][0]["sectionTitle"] == "Nieuw voor jou"
    assert parsed["items"][0]["playable"] is True
    payload = json.loads(str(parsed["items"][0]["payload"]))
    assert payload["section_id"] == "new_for_you"
    assert payload["discovery_item_id"] == "t1"
    assert set(payload) == {"section_id", "discovery_item_id"}
    assert parsed["items"][1]["hasReason"] is False
    assert parsed["items"][3]["sectionId"] == "opaque-backend-section"
    assert parsed["items"][3]["playable"] is False


def test_music_discovery_feed_ignores_top_level_items_and_recent_history() -> None:
    parsed = parse_music_discovery_feed(
        {
            "items": [{"id": "legacy", "kind": "track", "title": "Legacy", "uri": "spotify:track:legacy"}],
            "recommendations": [{"id": "rec", "kind": "track", "title": "Rec", "uri": "spotify:track:rec"}],
            "recent_tracks": [{"id": "recent", "kind": "track", "title": "Recent", "uri": "spotify:track:recent"}],
        }
    )

    assert parsed["items"] == []


def test_music_discovery_disabled_reason_does_not_fabricate_recommendations(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")

    backend._apply_music_discovery_data({"enabled": False, "reason": "music_dna_disabled", "sections": [{"items": [{"id": "fake", "kind": "track", "title": "Fake", "uri": "spotify:track:fake"}]}]})

    assert backend.musicDiscoveryItems == []
    assert backend.musicDiscoveryEmptyText == "music_dna_disabled"


def test_cached_image_url_reuses_24_hour_cache(tmp_path: Path, monkeypatch) -> None:
    cache_root = tmp_path / "state" / "client.log"
    monkeypatch.setattr("djconnect_pi.app.DEFAULT_LOG_PATH", cache_root)
    response = Mock()
    response.content = b"image"
    response.raise_for_status.return_value = None

    with patch("djconnect_pi.app.requests.get", return_value=response) as get:
        first = cached_image_url("https://example.test/art.jpg")
        second = cached_image_url("https://example.test/art.jpg")

    assert first == second
    assert first.startswith("file://")
    get.assert_called_once()


def test_media_list_parsers_accept_ha_artwork_aliases() -> None:
    queue = parse_queue_items(
        {
            "queue": {
                "items": [
                    {
                        "track_name": "Track One",
                        "artist_name": "Artist One",
                        "track_uri": "spotify:track:1",
                        "entity_picture": "https://example.test/track.jpg",
                    }
                ]
            }
        }
    )
    playlists = parse_playlist_items(
        {
            "playlists": [
                {
                    "name": "Friday Night",
                    "uri": "spotify:playlist:1",
                    "entity_picture": "https://example.test/playlist.jpg",
                }
            ]
        }
    )

    assert queue[0]["title"] == "Track One"
    assert queue[0]["subtitle"] == "Artist One"
    assert queue[0]["imageUrl"] == "https://example.test/track.jpg"
    assert playlists[0]["title"] == "Friday Night"
    assert playlists[0]["imageUrl"] == "https://example.test/playlist.jpg"


def test_media_list_parsers_accept_nested_spotify_images() -> None:
    queue = parse_queue_items(
        {
            "queue": {
                "items": [
                    {
                        "track_name": "Track One",
                        "artist_name": "Artist One",
                        "track_uri": "spotify:track:1",
                        "album": {
                            "images": [
                                {"url": "https://example.test/small.jpg", "width": 64},
                                {"url": "https://example.test/large.jpg", "width": 640},
                            ]
                        },
                    }
                ]
            }
        }
    )
    playlists = parse_playlist_items(
        {
            "playlists": [
                {
                    "name": "Friday Night",
                    "uri": "spotify:playlist:1",
                    "images": [{"url": "https://example.test/playlist-large.jpg", "width": 300}],
                }
            ]
        }
    )

    assert queue[0]["imageUrl"] == "https://example.test/large.jpg"
    assert playlists[0]["imageUrl"] == "https://example.test/playlist-large.jpg"


def test_ask_dj_parser_accepts_history_rich_messages(monkeypatch) -> None:
    monkeypatch.setattr("djconnect_pi.app.cached_image_url", lambda url: f"file:///cache/{url.rsplit('/', 1)[-1]}")
    messages = parse_ask_dj_messages(
        {
            "messages": [
                {"id": "u1", "role": "user", "text": "Welke albums?"},
                {
                    "id": "a1",
                    "role": "assistant",
                    "dj_text": "Radiohead heeft meerdere albums.",
                    "images": [
                        {"url": "http://ha/api/image/1", "thumbnail_url": "http://ha/api/thumb/1"},
                        {"image_url": "http://ha/api/album/ten.jpg"},
                    ],
                    "links": [{"title": "Wikipedia", "url": "http://ha/link", "kind": "wikipedia"}],
                    "sources": [{"name": "MusicBrainz", "url": "http://ha/source", "source": "musicbrainz"}],
                    "playback_actions": [
                        {
                            "kind": "track",
                            "title": "Play Now",
                            "uri": "spotify:track:1",
                            "subtitle": "Radiohead",
                            "item": {"album": {"images": [{"url": "http://ha/api/track/art.jpg", "width": 640}]}},
                        }
                    ],
                    "confirmation_actions": [{"kind": "confirmation", "action_style": "confirmation", "response_value": "yes"}],
                    "audio_url": "https://ha.local/tts.mp3",
                },
                {"id": "s1", "kind": "status", "text": "Ask DJ denkt na"},
            ]
        }
    )

    assert messages[0]["role"] == "user"
    assert messages[0]["text"] == "Welke albums?"
    assert messages[1]["text"] == "Radiohead heeft meerdere albums."
    assert messages[1]["images"] == [
        {"url": "file:///cache/1", "title": ""},
        {"url": "file:///cache/ten.jpg", "title": ""},
    ]
    assert len(messages[1]["links"]) == 2
    assert [action["kind"] for action in messages[1]["actions"]] == ["track", "confirmation"]
    assert messages[1]["actions"][0]["isMedia"] is True
    assert messages[1]["actions"][0]["imageUrl"] == "file:///cache/art.jpg"
    assert messages[1]["actions"][1]["isMedia"] is False
    assert "spotify:track:1" in messages[1]["actions"][0]["payload"]
    assert messages[1]["audioUrl"] == "https://ha.local/tts.mp3"
    assert messages[2]["role"] == "status"
    assert messages[2]["text"] == "Ask DJ denkt na"


def test_ask_dj_output_actions_render_as_rows_without_duplicate_bullets() -> None:
    messages = parse_ask_dj_messages(
        {
            "messages": [
                {
                    "id": "speaker-list",
                    "role": "assistant",
                    "text": "Dit zijn de momenteel beschikbare speakers:\n- Tuin\n- Speelhoek + Keuken\n- iPhone",
                    "playback_actions": [
                        {"command": "set_output", "kind": "output", "title": "Tuin", "value": "Tuin"},
                        {"command": "set_output", "kind": "output", "title": "Speelhoek + Keuken", "value": "Speelhoek + Keuken"},
                        {"command": "set_output", "kind": "output", "title": "iPhone", "value": "iPhone"},
                    ],
                }
            ]
        }
    )

    assert messages[0]["text"] == "Dit zijn de momenteel beschikbare speakers:"
    assert [action["title"] for action in messages[0]["actions"]] == ["Tuin", "Speelhoek + Keuken", "iPhone"]
    assert all(action["isOutput"] is True for action in messages[0]["actions"])
    assert all(action["isMedia"] is False for action in messages[0]["actions"])


def test_ask_dj_control_status_has_no_art_or_audio_button() -> None:
    messages = parse_ask_dj_messages(
        {
            "messages": [
                {
                    "id": "shuffle",
                    "role": "assistant",
                    "text": "Shuffle staat aan.",
                    "images": [],
                    "playback_actions": [
                        {"kind": "control", "command": "set_shuffle", "title": "Shuffle uitzetten", "value": False, "image_url": "https://example.test/old.jpg"}
                    ],
                    "audio_url": None,
                }
            ]
        }
    )

    assert messages[0]["text"] == "Shuffle staat aan."
    assert messages[0]["images"] == []
    assert messages[0]["audioUrl"] == ""
    assert messages[0]["actions"][0]["title"] == "Shuffle uitzetten"
    assert messages[0]["actions"][0]["isMedia"] is False
    assert messages[0]["actions"][0]["imageUrl"] == ""


def test_ask_dj_save_current_track_control_uses_button_label_without_art() -> None:
    messages = parse_ask_dj_messages(
        {
            "messages": [
                {
                    "id": "favorite",
                    "role": "assistant",
                    "text": "Ik kan het huidige nummer opslaan.",
                    "playback_actions": [
                        {
                            "kind": "control",
                            "command": "save_current_track",
                            "button_label": "Zet in favorieten",
                            "image_url": "https://example.test/track.jpg",
                        }
                    ],
                }
            ]
        }
    )

    assert messages[0]["actions"][0]["title"] == "Zet in favorieten"
    assert messages[0]["actions"][0]["isMedia"] is False
    assert messages[0]["actions"][0]["imageUrl"] == ""
    assert "save_current_track" in messages[0]["actions"][0]["payload"]


def test_ask_dj_music_dna_summary_is_text_only_with_music_dna_source() -> None:
    messages = parse_ask_dj_messages(
        {
            "text": "Je houdt van Kebu en rustige ochtendmuziek.",
            "intent": "personal_music_dna_summary",
            "action": "music_dna_summary",
            "sources": [{"source": "djconnect_music_dna"}],
            "images": [],
            "playback_actions": [],
            "audio_url": None,
        }
    )

    assert messages[0]["text"] == "Je houdt van Kebu en rustige ochtendmuziek."
    assert messages[0]["images"] == []
    assert messages[0]["actions"] == []
    assert messages[0]["audioUrl"] == ""
    assert messages[0]["links"] == [{"title": "djconnect_music_dna", "url": "", "kind": "djconnect_music_dna", "source": "djconnect_music_dna"}]


def test_ask_dj_recently_played_items_render_as_compact_rows_without_actions(monkeypatch) -> None:
    cache_mock = Mock(side_effect=lambda url: f"file:///cache/{url.rsplit('/', 1)[-1]}")
    monkeypatch.setattr("djconnect_pi.app.cached_image_url", cache_mock)
    messages = parse_ask_dj_messages(
        {
            "text": "Deze nummers heb je afgelopen uur afgespeeld.",
            "intent": "recently_played_history",
            "items": [
                {
                    "title": "Nightdrive",
                    "artist": "Kebu",
                    "played_at": "08:42",
                    "image_url": "https://example.test/nightdrive.jpg",
                }
            ],
            "playback_actions": [],
        }
    )

    assert messages[0]["actions"] == []
    assert messages[0]["images"] == []
    assert messages[0]["items"] == [
        {
            "title": "Nightdrive",
            "subtitle": "Kebu",
            "value": "",
            "time": "08:42",
            "kind": "",
            "source": "",
            "confidence": "",
            "imageUrl": "https://example.test/nightdrive.jpg",
            "trackInsightMetric": False,
            "musicDna": False,
        }
    ]
    cache_mock.assert_not_called()


def test_ask_dj_track_insight_renders_music_dna_without_playback_actions() -> None:
    messages = parse_ask_dj_messages(
        {
            "success": True,
            "text": "This expands your Music DNA.",
            "intent": {"intent": "track_insight", "action": "track_insight"},
            "action": "track_insight",
            "type": "track_insight",
            "open_screen": "track_insight",
            "track_insight": {
                "track": {"title": "Strobe", "artist": "deadmau5", "album": "For Lack of a Better Name"},
                "analysis": {
                    "summary": "A progressive electronic slow burn.",
                    "genre": "Progressive house",
                    "subgenre": "Melodic progressive",
                    "vibe": "Long progressive build with a patient emotional payoff.",
                    "why_it_fits": ["Melodic tension", "Late-night electronic focus"],
                    "energy": 81,
                    "danceability": 68,
                    "bpm": 128,
                    "key": "C minor",
                },
                "music_dna": {
                    "match_percent": 92,
                    "summary": "Matches your progressive electronic Music DNA.",
                    "traits": ["progressive", "melodic", "patient build"],
                },
                "visual_profile": {"palette": ["blue", "violet"]},
                "cache": {"hit": False},
            },
            "images": [],
            "playback_actions": [],
        }
    )

    assert messages[0]["trackInsight"] is True
    assert messages[0]["text"] == "This expands your Music DNA."
    assert messages[0]["images"] == []
    assert messages[0]["actions"] == []
    assert messages[0]["musicDnaMatch"] == "92%"
    assert messages[0]["trackInsightData"]["track"]["title"] == "Strobe"
    assert messages[0]["trackInsightData"]["visual_profile"] == {"palette": ["blue", "violet"]}
    assert messages[0]["items"][0]["title"] == "Music DNA Match"
    assert messages[0]["items"][0]["value"] == "92%"
    item_titles = [item["title"] for item in messages[0]["items"]]
    assert "BPM" not in item_titles
    assert "Key" not in item_titles
    assert "Energy" in item_titles
    assert "Danceability" in item_titles
    assert messages[0]["items"][1]["value"] == "81%"
    assert messages[0]["items"][2]["value"] == "68%"
    section_titles = [section["title"] for section in messages[0]["analysis"]["sections"]]
    assert section_titles[:4] == ["Summary", "Genre", "Vibe", "Why it fits you"]
    assert "This expands your Music DNA." in section_titles
    serialized = json.dumps(messages[0], sort_keys=True)
    assert "128" not in serialized
    assert "C minor" not in serialized


def test_track_insight_direct_and_wrapped_response_decode_same_contract() -> None:
    direct = parse_ask_dj_messages(
        {
            "success": True,
            "track": {"title": "Strobe", "artist": "deadmau5", "genres": ["progressive house"]},
            "analysis": {"summary": "A long build.", "genre": "Progressive house", "subgenre": "Melodic", "confidence": 0.77},
            "visual_profile": {"motion_style": "slow_pulse", "seed": "ignored"},
            "mood_context": {"zone": "energy"},
        }
    )[0]
    wrapped = parse_ask_dj_messages(
        {
            "success": True,
            "track_insight": {
                "track": {"title": "Strobe", "artist": "deadmau5", "genres": ["progressive house"]},
                "analysis": {"summary": "A long build.", "genre": "Progressive house", "subgenre": "Melodic", "confidence": 0.77},
                "visual_profile": {"motion_style": "slow_pulse", "seed": "ignored"},
                "mood_context": {"zone": "energy"},
            },
        }
    )[0]

    for message in (direct, wrapped):
        assert message["trackInsight"] is True
        assert message["trackInsightData"]["track"]["title"] == "Strobe"
        assert message["trackInsightData"]["visual_profile"]["motion_style"] == "slow_pulse"
        assert message["items"][0]["title"] == "Confidence"
        assert message["items"][0]["value"] == "77%"
        titles = [section["title"] for section in message["analysis"]["sections"]]
        assert "Summary" in titles
        assert "Genre" in titles
        assert "Visual profile" not in titles
        assert "Mood context" in titles


def test_ask_dj_track_insight_no_track_playing_is_empty_state() -> None:
    messages = parse_ask_dj_messages({"intent": "track_insight", "track_insight": {"error": "no_track_playing"}})

    assert messages[0]["trackInsight"] is True
    assert messages[0]["text"] == "Er speelt nu geen track."
    assert messages[0]["actions"] == []
    assert messages[0]["items"] == []


def test_track_insight_no_track_and_rate_limit_clear_previous_view(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend._apply_track_insight_data({"track": {"title": "Strobe", "artist": "deadmau5"}, "analysis": {"summary": "A long build."}})

    assert backend.trackInsightTitle == "Strobe"

    backend._apply_track_insight_data({"success": False, "error": "no_track_playing"})
    assert backend.trackInsightTitle == ""
    assert backend.trackInsightItems == []
    assert backend.trackInsightError == backend.tr_key("track_insight_no_track")

    backend._apply_track_insight_data({"track": {"title": "Track"}, "analysis": {"summary": "Fresh"}})
    backend._apply_track_insight_data({"success": False, "error": "rate_limited"})
    assert backend.trackInsightText == ""
    assert backend.trackInsightError == backend.tr_key("track_insight_rate_limited")


def test_track_insight_clears_when_current_track_changes(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend._apply_playback(Playback(title="Old Track", artist="Artist", image_url="https://example.test/old.jpg"))
    backend._apply_track_insight_data({"track": {"title": "Old Track", "artist": "Artist"}, "analysis": {"summary": "Old analysis"}})

    assert backend.trackInsightText

    backend._apply_playback(Playback(title="New Track", artist="Artist", image_url="https://example.test/new.jpg"))

    assert backend.trackInsightText == ""
    assert backend.trackInsightSections == []


def test_ask_dj_track_insight_explicit_playback_actions_are_preserved() -> None:
    messages = parse_ask_dj_messages(
        {
            "text": "Track Insight.",
            "intent": "track_insight",
            "track_insight": {"track": {"title": "Strobe"}},
            "playback_actions": [{"kind": "track", "title": "Play Now", "uri": "spotify:track:1"}],
            "confirmation_actions": [{"kind": "confirmation", "response_value": "yes"}],
        }
    )

    assert [action["title"] for action in messages[0]["actions"]] == ["Play Now"]


def test_ask_dj_track_insight_metadata_mode_does_not_reuse_old_artwork(monkeypatch) -> None:
    monkeypatch.setattr("djconnect_pi.app.cached_image_url", lambda url: f"file:///cache/{url.rsplit('/', 1)[-1]}")
    messages = parse_ask_dj_messages(
        {
            "messages": [
                {
                    "id": "old-media",
                    "role": "assistant",
                    "text": "Speel deze track.",
                    "images": [{"url": "https://example.test/old.jpg"}],
                    "playback_actions": [{"kind": "track", "title": "Play Now", "uri": "spotify:track:old", "image_url": "https://example.test/old.jpg"}],
                },
                {
                    "id": "insight",
                    "role": "assistant",
                    "text": "Metadata-only Track Insight.",
                    "intent": "track_insight",
                    "track_insight": {
                        "track": {"title": "Strobe"},
                        "analysis": {"vibe": "Rustige opbouw."},
                        "music_dna": {"match_percent": 81},
                    },
                    "images": [],
                    "items": [],
                    "playback_actions": [],
                },
            ]
        }
    )

    assert messages[0]["images"] == [{"url": "file:///cache/old.jpg", "title": ""}]
    assert messages[0]["actions"][0]["isMedia"] is True
    assert messages[1]["trackInsight"] is True
    assert messages[1]["images"] == []
    assert messages[1]["actions"] == []

def test_ask_dj_parser_prefers_canonical_response_messages() -> None:
    messages = parse_ask_dj_messages(
        {
            "user_message": "heb je playlists van snowpatrol",
            "assistant_message": "Legacy antwoord dat niet los moet renderen",
            "messages": [
                {
                    "id": "u-server",
                    "client_message_id": "client-1",
                    "exchange_id": "exchange-1",
                    "exchange_order": 0,
                    "role": "user",
                    "text": "heb je playlists van snowpatrol",
                },
                {
                    "id": "a-server",
                    "client_message_id": "client-1",
                    "exchange_id": "exchange-1",
                    "exchange_order": 1,
                    "role": "assistant",
                    "text": "Ik heb een paar Snow Patrol playlists gevonden.",
                },
            ],
        }
    )

    assert [message["id"] for message in messages] == ["u-server", "a-server"]
    assert [message["role"] for message in messages] == ["user", "assistant"]
    assert [message["exchange_order"] for message in messages] == [0, 1]


def test_ask_dj_parser_accepts_assistant_message_object_items() -> None:
    messages = parse_ask_dj_messages(
        {
            "assistant_message": {
                "text": "Dit zijn je recent afgespeelde tracks.",
                "items": [
                    {
                        "title": "Song A",
                        "artist": "Artist A",
                        "type": "tracks",
                        "played_at": "2026-07-05T08:00:00Z",
                        "source": "spotify_recently_played",
                    }
                ],
            },
            "intent": {"intent": "recently_played_history", "item_type": "tracks"},
            "images": [],
            "playback_actions": [],
        }
    )

    assert len(messages) == 1
    assert messages[0]["text"] == "Dit zijn je recent afgespeelde tracks."
    assert messages[0]["items"] == [
        {
            "title": "Song A",
            "subtitle": "Artist A",
            "value": "",
            "time": "2026-07-05T08:00:00Z",
            "kind": "tracks",
            "source": "spotify_recently_played",
            "confidence": "",
            "imageUrl": "",
            "trackInsightMetric": False,
            "musicDna": False,
        }
    ]
    assert messages[0]["actions"] == []


def test_ask_dj_parser_keeps_legacy_user_before_assistant() -> None:
    messages = parse_ask_dj_messages(
        {
            "client_message_id": "client-legacy",
            "user_message": "heb je playlists van snowpatrol",
            "assistant_message": "Ik heb een paar Snow Patrol playlists gevonden.",
            "created_at": "2026-06-24T12:00:00Z",
        }
    )

    assert [message["role"] for message in messages] == ["user", "assistant"]
    assert [message["text"] for message in messages] == [
        "heb je playlists van snowpatrol",
        "Ik heb een paar Snow Patrol playlists gevonden.",
    ]


def test_ask_dj_merge_orders_exchange_and_deduplicates_refreshes(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend._merge_ask_dj_messages(
        [
            {
                "id": "",
                "client_message_id": "client-1",
                "role": "user",
                "text": "heb je playlists van snowpatrol",
                "created_at": "2026-06-24T12:00:00Z",
                "pending": True,
            }
        ]
    )
    backend._apply_ask_dj_data(
        {
            "history_revision": 5,
            "messages": [
                {
                    "id": "a-server",
                    "client_message_id": "client-1",
                    "exchange_id": "exchange-1",
                    "exchange_order": 1,
                    "role": "assistant",
                    "text": "Ik heb een paar Snow Patrol playlists gevonden.",
                    "created_at": "2026-06-24T12:00:01Z",
                },
                {
                    "id": "u-server",
                    "client_message_id": "client-1",
                    "exchange_id": "exchange-1",
                    "exchange_order": 0,
                    "role": "user",
                    "text": "heb je playlists van snowpatrol",
                    "created_at": "2026-06-24T12:00:02Z",
                },
            ],
        }
    )
    backend._apply_ask_dj_data(
        {
            "history_revision": 6,
            "messages": [
                {
                    "id": "u-server",
                    "client_message_id": "client-1",
                    "exchange_id": "exchange-1",
                    "exchange_order": 0,
                    "role": "user",
                    "text": "heb je playlists van snowpatrol",
                },
                {
                    "id": "a-server",
                    "client_message_id": "client-1",
                    "exchange_id": "exchange-1",
                    "exchange_order": 1,
                    "role": "assistant",
                    "text": "Ik heb een paar Snow Patrol playlists gevonden.",
                },
            ],
        }
    )

    rendered = [(message["role"], message["text"], message["displayTime"]) for message in backend.askDjMessages]
    assert rendered == [
        ("assistant", "Ik heb een paar Snow Patrol playlists gevonden.", "12:00"),
        ("user", "heb je playlists van snowpatrol", "12:00"),
    ]


def test_ask_dj_history_limit_is_applied_from_server(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")

    backend._apply_ask_dj_data(
        {
            "history_revision": 1,
            "history_limit": 2,
            "messages": [
                {"id": "m1", "role": "assistant", "text": "Een", "created_at": "2026-06-24T12:00:01Z"},
                {"id": "m2", "role": "assistant", "text": "Twee", "created_at": "2026-06-24T12:00:02Z"},
                {"id": "m3", "role": "assistant", "text": "Drie", "created_at": "2026-06-24T12:00:03Z"},
            ],
        }
    )

    assert [message["id"] for message in backend.askDjMessages] == ["m3", "m2"]
    assert [message["displayTime"] for message in backend.askDjMessages] == ["12:00", "12:00"]


def test_ask_dj_clear_and_trim_revisions_are_server_authoritative(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend._apply_ask_dj_data(
        {
            "history_revision": 10,
            "messages": [
                {"id": "m1", "role": "assistant", "text": "Een", "created_at": "2026-07-05T08:00:01Z"},
                {"id": "m2", "role": "assistant", "text": "Twee", "created_at": "2026-07-05T08:00:02Z"},
                {"id": "m3", "role": "assistant", "text": "Drie", "created_at": "2026-07-05T08:00:03Z"},
            ],
        }
    )

    backend._apply_ask_dj_data({"history_revision": 11, "history_trimmed_count": 1, "messages": []})
    assert [message["id"] for message in backend.askDjMessages] == ["m3", "m2"]
    assert backend._ask_dj_history_revision == 11

    backend._apply_ask_dj_data({"clear_revision": 2, "history_revision": 12, "messages": []})
    assert backend.askDjMessages == []
    assert backend._ask_dj_clear_revision == 2
    assert backend._ask_dj_history_revision == 12


def test_ask_dj_poll_requires_pairing_and_token(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.client.ask_dj_history = Mock()

    backend.pollAskDjHistory()

    backend.client.ask_dj_history.assert_not_called()


def test_ask_dj_poll_worker_uses_revision_and_applies_backoff(tmp_path: Path) -> None:
    ensure_app()
    config_path = tmp_path / "config.json"
    backend = DJConnectBackend(config_path)
    backend.cfg.paired = True
    backend.cfg.device_token = "token-1"
    backend.client.cfg = backend.cfg
    backend._ask_dj_history_revision = 7
    backend.client.ask_dj_history = Mock(return_value={"history_revision": 8, "messages": [{"id": "a1", "role": "assistant", "text": "Hoi"}]})

    backend._poll_ask_dj_history_worker()

    backend.client.ask_dj_history.assert_called_once_with(7)
    assert backend.askDjMessages[0]["text"] == "Hoi"
    assert backend._ask_dj_history_revision == 8
    assert backend._ask_dj_poll_error_count == 0

    backend.client.ask_dj_history = Mock(side_effect=AuthenticationError("stale token"))
    backend._poll_ask_dj_history_worker()

    assert backend._ask_dj_poll_error_count == 1
    assert backend._ask_dj_unavailable_until > 0


def test_ask_dj_action_tap_sends_structured_payload_only(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.cfg.paired = True
    backend.cfg.device_token = "token-1"
    backend.client.cfg = backend.cfg
    backend.client.ask_dj_action = Mock(return_value={"success": True, "messages": []})

    backend._send_ask_dj_action_worker({"kind": "confirmation", "response_value": "yes"})

    backend.client.ask_dj_action.assert_called_once_with({"kind": "confirmation", "response_value": "yes"})


def test_ask_dj_action_accepts_music_assistant_payload_without_spotify_uri(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.cfg.paired = True
    backend.cfg.device_token = "token-1"
    backend.client.cfg = backend.cfg
    action = {
        "kind": "track",
        "command": "ask_dj_play_recommendation",
        "music_backend": "music_assistant",
        "backend_revision": 4,
        "value": {"item_id": "mass-track-1", "provider": "library", "player_id": "media_player.mass_woonkamer"},
    }
    backend.client.ask_dj_action = Mock(return_value={"success": True, "messages": []})

    backend._send_ask_dj_action_worker(action)

    backend.client.ask_dj_action.assert_called_once_with(action)


def test_ask_dj_action_surfaces_unsupported_capability(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.client.ask_dj_action = Mock(side_effect=UnsupportedBackendCapability("Top items unavailable"))

    with pytest.raises(UnsupportedBackendCapability, match="Top items unavailable"):
        backend._send_ask_dj_action_worker({"kind": "track", "command": "top_items"})


def test_ask_dj_action_surfaces_stale_backend_action(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.client.ask_dj_action = Mock(side_effect=StaleBackendAction("Ask DJ opnieuw"))

    with pytest.raises(StaleBackendAction, match="Ask DJ opnieuw"):
        backend._send_ask_dj_action_worker({"kind": "track", "backend_revision": 3})


def test_version_mismatch_does_not_clear_pairing_or_token(tmp_path: Path) -> None:
    ensure_app()
    config_path = tmp_path / "config.json"
    cfg = Config(
        device_id="djconnect-raspberry-pi-ABCDEF123456",
        device_token="token-1",
        paired=True,
        ha_url="http://ha.local:8123",
    )
    save_config(config_path, cfg)
    backend = DJConnectBackend(config_path)
    backend.client.command = Mock(side_effect=ProtocolVersionMismatch("3.2.0", "3.1.112"))

    with pytest.raises(ProtocolVersionMismatch), patch.object(backend, "_trigger_update_service"):
        backend._refresh_worker()

    saved = load_config(config_path)
    assert saved.device_token == "token-1"
    assert saved.paired is True


def test_authentication_error_clears_pairing_and_ask_dj_cache(tmp_path: Path) -> None:
    ensure_app()
    config_path = tmp_path / "config.json"
    cfg = Config(
        device_id="djconnect-raspberry-pi-ABCDEF123456",
        device_token="token-1",
        paired=True,
        ha_url="http://ha.local:8123",
    )
    save_config(config_path, cfg)
    backend = DJConnectBackend(config_path)
    backend._ask_dj_messages = [{"id": "m1", "role": "assistant", "text": "Cached"}]
    backend._ask_dj_history_revision = 9
    backend._ask_dj_clear_revision = 4

    backend.client.command = Mock(side_effect=AuthenticationError("stale pairing"))
    backend._run("status", lambda: backend.client.command("status"))
    backend._executor.shutdown(wait=True)

    saved = load_config(config_path)
    assert saved.device_token == ""
    assert saved.paired is False
    assert backend.askDjMessages == []
    assert backend._ask_dj_history_revision == 0
    assert backend._ask_dj_clear_revision == 0


def test_save_current_track_worker_raises_specific_error_on_success_false(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.client.command = Mock(return_value={"success": False, "error": "spotify_save_failed"})

    with pytest.raises(SaveCurrentTrackError):
        backend._save_current_track_worker()

    backend.client.command.assert_called_once_with("save_current_track")


def test_demo_mode_uses_example_output_devices(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")

    backend.enterDemoMode()

    assert backend.outputDevice == ""
    assert backend.outputDevices == ["Keuken", "Woonkamer"]
    assert "True" not in backend.outputDevices


def test_queue_parser_preserves_optional_context_and_episode_uri() -> None:
    queue = parse_queue_items(
        {
            "queue": {
                "items": [
                    {
                        "title": "Podcast Episode",
                        "artist": "Podcast",
                        "uri": "spotify:episode:episode-1",
                    },
                    {
                        "title": "Playlist Track",
                        "uri": "spotify:track:track-1",
                        "queue_context": "spotify:playlist:playlist-1",
                        "index": 4,
                    },
                ]
            }
        }
    )

    assert queue[0]["uri"] == "spotify:episode:episode-1"
    assert queue[0]["contextUri"] == ""
    assert queue[1]["contextUri"] == "spotify:playlist:playlist-1"
    assert queue[1]["index"] == 4


def test_queue_parser_renders_artist_album_identity_and_artwork_aliases() -> None:
    queue = parse_queue_items(
        {
            "queue": [
                {
                    "title": "Nothing Else Matters",
                    "artist": "Scala & Kolacny Brothers",
                    "artist_name": "Fallback Artist",
                    "subtitle": "Fallback Subtitle",
                    "album": "Scala On The Rocks",
                    "album_name": "Fallback Album",
                    "id": "spotify:track:nothing-else",
                    "duration_ms": 388000,
                    "album_image_url": "https://example.test/album.jpg",
                    "image_url": "https://example.test/image.jpg",
                    "thumbnail_url": "https://example.test/thumb.jpg",
                }
            ]
        }
    )

    assert queue == [
        {
            "title": "Nothing Else Matters",
            "subtitle": "Scala & Kolacny Brothers",
            "artist": "Scala & Kolacny Brothers",
            "album": "Scala On The Rocks",
            "uri": "spotify:track:nothing-else",
            "imageUrl": "https://example.test/album.jpg",
            "tint": "#38bdf8",
            "contextUri": "",
            "index": None,
        }
    ]


def test_queue_parser_accepts_nested_items_and_preserves_container_context() -> None:
    queue = parse_queue_items(
        {
            "queue": {
                "context": "ignored display context",
                "contextUri": "spotify:playlist:context-1",
                "items": [
                    {
                        "title": "Track One",
                        "artist_name": "Artist One",
                        "album_name": "Album One",
                        "uri": "spotify:track:1",
                        "image_url": "https://example.test/image.jpg",
                    },
                    {
                        "title": "Track Two",
                        "subtitle": "Artist Two",
                        "uri": "spotify:track:2",
                        "thumbnail_url": "https://example.test/thumb.jpg",
                        "context_uri": "spotify:album:item-context",
                    },
                ],
            }
        }
    )

    assert [item["title"] for item in queue] == ["Track One", "Track Two"]
    assert queue[0]["subtitle"] == "Artist One"
    assert queue[0]["album"] == "Album One"
    assert queue[0]["imageUrl"] == "https://example.test/image.jpg"
    assert queue[0]["contextUri"] == "spotify:playlist:context-1"
    assert queue[1]["subtitle"] == "Artist Two"
    assert queue[1]["imageUrl"] == "https://example.test/thumb.jpg"
    assert queue[1]["contextUri"] == "spotify:album:item-context"


def test_queue_parser_ignores_top_level_items_without_queue_container() -> None:
    assert parse_queue_items({"items": [{"title": "Recommendation", "artist": "Artist", "uri": "spotify:track:1"}]}) == []


def test_media_item_payload_allows_queue_item_without_context() -> None:
    payload = media_item_payload(
        "play_context_at",
        {"title": "Episode", "subtitle": "Podcast", "uri": "spotify:episode:episode-1"},
    )

    assert payload == {
        "value": {
            "uri": "spotify:episode:episode-1",
            "title": "Episode",
            "artist": "Podcast",
        },
        "play": True,
    }


def test_media_item_payload_accepts_qml_json_payload() -> None:
    payload = media_item_payload(
        "play_context_at",
        json.dumps({"title": "Episode", "subtitle": "Podcast", "uri": "spotify:episode:episode-1"}),
    )

    assert payload["value"]["uri"] == "spotify:episode:episode-1"
    assert "context_uri" not in payload["value"]


def test_media_item_payload_preserves_context_offset_when_supported() -> None:
    payload = media_item_payload(
        "play_context_at",
        {
            "title": "Track",
            "uri": "spotify:track:track-1",
            "contextUri": "spotify:show:show-1",
            "index": 2,
        },
    )

    assert payload["value"]["uri"] == "spotify:track:track-1"
    assert payload["value"]["context_uri"] == "spotify:show:show-1"
    assert payload["value"]["offset_uri"] == "spotify:track:track-1"
    assert payload["value"]["index"] == 2


def test_media_item_payload_skips_queue_item_without_uri() -> None:
    assert media_item_payload("play_context_at", {"title": "Missing URI"}) == {}


@pytest.mark.parametrize(
    ("payload", "expected_title"),
    [
        ({"playlists": [{"name": "Top Level", "uri": "spotify:playlist:1"}]}, "Top Level"),
        ({"items": [{"title": "Items", "id": "spotify:playlist:2"}]}, "Items"),
        ({"data": {"playlists": [{"display_title": "Data Playlists", "value": "spotify:playlist:3"}]}}, "Data Playlists"),
        ({"data": {"items": [{"name": "Data Items", "playlist_uri": "spotify:playlist:4"}]}}, "Data Items"),
        ({"result": {"playlists": [{"title": "Result Playlists", "uri": "spotify:playlist:5"}]}}, "Result Playlists"),
        ({"result": {"items": [{"name": "Result Items", "id": "spotify:playlist:6"}]}}, "Result Items"),
    ],
)
def test_playlist_parser_accepts_contract_container_shapes(payload: dict[str, object], expected_title: str) -> None:
    playlists = parse_playlist_items(payload)

    assert len(playlists) == 1
    assert playlists[0]["title"] == expected_title


def test_playlist_parser_accepts_aliases_and_ignores_unplayable_items() -> None:
    playlists = parse_playlist_items(
        {
            "playlists": [
                {
                    "display_title": "Alias Playlist",
                    "playlist_uri": "spotify:playlist:alias",
                    "owner_name": "Peter",
                    "imageUrl": "https://example.test/image-url.jpg",
                },
                {"name": "Missing URI"},
                {"uri": "spotify:playlist:missing-title"},
            ]
        }
    )

    assert playlists == [
        {
            "title": "Alias Playlist",
            "subtitle": "Peter",
            "uri": "spotify:playlist:alias",
            "imageUrl": "https://example.test/image-url.jpg",
            "tint": "#8b5cf6",
        }
    ]


def test_empty_playlists_response_decodes_empty_state() -> None:
    assert parse_playlist_items({"playlists": []}) == []


def test_playlist_parser_limits_to_100_items() -> None:
    playlists = parse_playlist_items(
        {
            "data": {
                "items": [
                    {
                        "name": f"Playlist {index}",
                        "id": f"spotify:playlist:{index}",
                        "owner": "Peter",
                        "entity_picture": f"https://example.test/{index}.jpg",
                    }
                    for index in range(120)
                ]
            }
        }
    )

    assert len(playlists) == 100
    assert playlists[0] == {
        "title": "Playlist 0",
        "subtitle": "Peter",
        "uri": "spotify:playlist:0",
        "imageUrl": "https://example.test/0.jpg",
        "tint": "#8b5cf6",
    }
    assert playlists[-1]["title"] == "Playlist 99"


def test_queue_parser_limits_to_100_items_and_accepts_nullable_fields() -> None:
    queue = parse_queue_items({"queue": [{"title": f"Track {index}"} for index in range(120)]})

    assert len(queue) == 100
    assert queue[0]["title"] == "Track 0"
    assert queue[-1]["title"] == "Track 99"


def test_queue_parser_treats_repeated_current_track_as_empty_queue() -> None:
    queue = parse_queue_items(
        {
            "queue": [
                {
                    "title": "Mind Games",
                    "artist": "HAEVN",
                    "uri": "spotify:track:mind-games",
                    "image_url": "https://example.test/mind-games.jpg",
                }
                for _ in range(5)
            ]
        }
    )

    assert queue == []


def test_queue_parser_dedupes_repeated_items_but_keeps_real_queue() -> None:
    queue = parse_queue_items(
        {
            "queue": [
                {"title": "Track One", "artist": "Artist", "uri": "spotify:track:1"},
                {"title": "Track Two", "artist": "Artist", "uri": "spotify:track:2"},
                {"title": "Track One", "artist": "Artist", "uri": "spotify:track:1"},
            ]
        }
    )

    assert [item["title"] for item in queue] == ["Track One", "Track Two"]


def test_prepare_media_artwork_caches_urls_before_qml_render(monkeypatch) -> None:
    items = [{"title": "Track", "imageUrl": "https://example.test/art.jpg"}]

    monkeypatch.setattr("djconnect_pi.app.cached_image_url", lambda url: f"file:///cache/{url.rsplit('/', 1)[-1]}")

    assert prepare_media_artwork(items) is items
    assert items[0]["imageUrl"] == "file:///cache/art.jpg"


def test_backend_set_ha_url_persists_value(tmp_path: Path) -> None:
    ensure_app()
    config_path = tmp_path / "config.json"
    backend = DJConnectBackend(config_path)

    backend.setHaUrl(" http://homeassistant.local:8123 ")
    reloaded = DJConnectBackend(config_path)

    assert backend.haUrl == "http://homeassistant.local:8123"
    assert reloaded.haUrl == "http://homeassistant.local:8123"


def test_backend_persists_screen_timeout_and_update_channel(tmp_path: Path) -> None:
    ensure_app()
    config_path = tmp_path / "config.json"
    backend = DJConnectBackend(config_path)

    backend.setScreenTimeoutSeconds(120)
    backend.setReturnToNowSeconds(0)
    backend.setUpdateChannel("beta")
    reloaded = DJConnectBackend(config_path)

    assert backend.screenTimeoutSeconds == 120
    assert backend.returnToNowSeconds == 0
    assert backend.updateChannel == "beta"
    assert reloaded.screenTimeoutSeconds == 120
    assert reloaded.returnToNowSeconds == 0
    assert reloaded.updateChannel == "beta"


def test_backend_clamps_return_to_now_timeout(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")

    backend.setReturnToNowSeconds(999)

    assert backend.returnToNowSeconds == 60


def test_backend_persists_screen_brightness(tmp_path: Path) -> None:
    ensure_app()
    config_path = tmp_path / "config.json"
    backend = DJConnectBackend(config_path)

    backend.setScreenBrightnessPercent(42)
    reloaded = DJConnectBackend(config_path)

    assert backend.screenBrightnessPercent == 42
    assert reloaded.screenBrightnessPercent == 42


def test_backend_clamps_screen_brightness(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")

    backend.setScreenBrightnessPercent(0)
    assert backend.screenBrightnessPercent == 10

    backend.setScreenBrightnessPercent(150)
    assert backend.screenBrightnessPercent == 100


def test_backend_persists_language_and_translates(tmp_path: Path) -> None:
    ensure_app()
    config_path = tmp_path / "config.json"
    with patch("djconnect_pi.config.locale.getlocale", return_value=("nl_NL", "UTF-8")):
        backend = DJConnectBackend(config_path)

    assert backend.t("setup") == "Instellingen"
    assert backend.translationVersion == 0
    backend.setLanguage("en")
    reloaded = DJConnectBackend(config_path)

    assert backend.language == "en"
    assert backend.translationVersion == 1
    assert backend.t("setup") == "Setup"
    assert reloaded.language == "en"


def test_backend_accepts_supported_language_and_rejects_unknown_language(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")

    backend.setLanguage("de")
    assert backend.language == "de"

    backend.setLanguage("it")
    assert backend.language == "en"


def test_backend_quit_app_requests_qcoreapplication_quit(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    app = Mock()

    with patch("djconnect_pi.app.QCoreApplication.instance", return_value=app):
        backend.quitApp()

    app.quit.assert_called_once_with()


def test_backend_rejects_unknown_update_channel(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")

    backend.setUpdateChannel("nightly")

    assert backend.updateChannel == "stable"


def test_backend_demo_mode_is_local_only(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    calls: list[tuple[str, dict[str, object]]] = []
    backend.command = lambda command, **payload: calls.append((command, payload))  # type: ignore[method-assign]

    assert backend.queueItems == []
    assert backend.playlistItems == []

    backend.enterDemoMode()
    backend.togglePlay()
    backend.next()
    backend.setVolume(33)
    backend.toggleShuffle()
    backend.cycleRepeat()

    assert backend.demoMode is True
    assert backend.title == "Around the World"
    assert backend.volume == 33
    assert [item["title"] for item in backend.queueItems] == ["Midnight City", "Sweet Disposition", "Electric Feel"]
    assert [item["title"] for item in backend.playlistItems] == ["Friday Night", "Dinner Vibes", "DJConnect"]
    assert calls == []

    backend.exitDemoMode()
    assert backend.demoMode is False


def test_backend_wakes_screen_for_previous_next(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    wakes: list[bool] = []
    calls: list[tuple[str, dict[str, object]]] = []
    backend.wakeScreenRequested.connect(lambda: wakes.append(True))
    backend.command = lambda command, **payload: calls.append((command, payload))  # type: ignore[method-assign]

    backend.previous()
    backend.next()

    assert len(wakes) == 2
    assert calls == [("previous", {}), ("next", {})]


def test_backend_wake_display_resets_x11_dpms(tmp_path: Path, monkeypatch) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    commands: list[list[str]] = []

    def fake_run(command, **kwargs):
        commands.append(command)

    monkeypatch.setattr(subprocess, "run", fake_run)

    backend.wakeDisplay()

    assert ["xset", "dpms", "force", "on"] in commands
    assert ["xset", "s", "reset"] in commands


def test_backend_favorite_state_requires_capability_and_track_uri(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.cfg.paired = True
    backend.cfg.device_token = "token-1"
    backend.cfg.music_backend_capabilities = {"supports_favorites": True}

    assert backend.favoriteAvailable is False

    backend._apply_playback(Playback(title="Track", artist="Artist", uri="backend:track:1", is_favorite=True))

    assert backend.favoriteAvailable is True
    assert backend.currentTrackFavorite is True

    backend._apply_playback(Playback(title="Other", artist="Artist", uri="backend:track:2"))

    assert backend.favoriteAvailable is True
    assert backend.currentTrackFavorite is False


def test_backend_save_current_track_uses_existing_command_route_and_busy_state(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.cfg.paired = True
    backend.cfg.device_token = "token-1"
    backend.cfg.music_backend_capabilities = {"supports_favorites": True}
    backend.playback = Playback(title="Track", artist="Artist", uri="backend:track:1")
    calls: list[tuple[str, dict[str, object]]] = []
    backend._sync_config_from_disk = lambda: None  # type: ignore[method-assign]
    backend._run = lambda label, worker, done=None: (worker(), done and done())  # type: ignore[method-assign]

    def fake_command(command: str, **payload: object) -> dict[str, object]:
        calls.append((command, payload))
        assert backend.favoriteBusy is True
        return {
            "success": True,
            "playback": {"title": "Track", "artist": "Artist", "uri": "backend:track:1", "is_liked": True},
        }

    backend.client.command = fake_command  # type: ignore[method-assign]

    backend.saveCurrentTrack()

    assert calls == [("save_current_track", {})]
    assert backend.favoriteBusy is False
    assert backend.currentTrackFavorite is True


def test_backend_requests_temporary_wake_for_backend_track_change(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    wakes: list[tuple[int, bool]] = []
    backend.temporaryWakeRequested.connect(lambda seconds, navigate: wakes.append((seconds, navigate)))

    backend._apply_playback(Playback(title="New Track", artist="Artist", image_url="https://example.test/art.jpg"))

    assert wakes == [(10, True)]


def test_backend_requests_temporary_wake_when_playback_resumes(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.playback = Playback(title="Same Track", artist="Artist", is_playing=False)
    wakes: list[tuple[int, bool]] = []
    backend.temporaryWakeRequested.connect(lambda seconds, navigate: wakes.append((seconds, navigate)))

    backend._apply_playback(Playback(title="Same Track", artist="Artist", is_playing=True))
    backend._apply_playback(Playback(title="Same Track", artist="Artist", is_playing=False))

    assert wakes == [(10, True)]


def test_backend_demo_mode_is_blocked_after_pairing(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.cfg.paired = True
    backend.cfg.device_token = "token"

    backend.enterDemoMode()

    assert backend.demoMode is False
    assert backend.title == backend.t("nothing_playing")


def test_backend_pairing_exits_demo_mode(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    calls: list[tuple[str, object]] = []
    backend._run = lambda label, worker: calls.append((label, worker))  # type: ignore[method-assign]

    backend.enterDemoMode()
    backend.pair("ABCDEF")

    assert backend.demoMode is False
    assert calls and calls[0][0] == backend.t("pairing")


def test_backend_reset_pairing_exits_demo_and_clears_token(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.cfg.paired = True
    backend.cfg.device_token = "token"

    backend.resetPairing()
    backend.enterDemoMode()
    backend.resetPairing()

    assert backend.demoMode is False
    assert backend.paired is False
    assert backend.cfg.device_token == ""
    assert backend.statusText == backend.t("ready_to_pair")


def test_backend_displays_local_dj_response_event_file(tmp_path: Path) -> None:
    ensure_app()
    config_path = tmp_path / "config.json"
    backend = DJConnectBackend(config_path)
    event_file = tmp_path / "dj-response.json"
    backend.cfg.dj_response_file = str(event_file)
    event_file.write_text(json.dumps({"text": "Hallo vanaf HA"}), encoding="utf-8")
    wakes: list[tuple[int, bool]] = []
    backend.temporaryWakeRequested.connect(lambda seconds, navigate: wakes.append((seconds, navigate)))

    backend._poll_local_events()

    assert backend.djResponseVisible is True
    assert backend.djResponseText == "Hallo vanaf HA"
    assert backend.toastVisible is False
    assert wakes == [(20, False)]
    assert not event_file.exists()


def test_backend_executes_local_command_event_file(tmp_path: Path) -> None:
    ensure_app()
    config_path = tmp_path / "config.json"
    backend = DJConnectBackend(config_path)
    event_file = tmp_path / "command-event.json"
    backend.cfg.command_event_file = str(event_file)
    backend.cfg.paired = True
    backend.cfg.device_token = "token"
    calls: list[tuple[str, dict[str, object]]] = []
    backend.command = lambda command, **payload: calls.append((command, payload))  # type: ignore[method-assign]
    event_file.write_text(
        json.dumps({"events": [{"command": "next", "payload": {"command": "next", "client_type": "raspberry_pi"}}]}),
        encoding="utf-8",
    )

    backend._poll_local_events()

    assert calls == [("next", {})]
    assert not event_file.exists()


def test_backend_debug_screen_event_emits_qml_signal(tmp_path: Path) -> None:
    ensure_app()
    config_path = tmp_path / "config.json"
    backend = DJConnectBackend(config_path)
    event_file = tmp_path / "command-event.json"
    backend.cfg.command_event_file = str(event_file)
    screens: list[str] = []
    calls: list[tuple[str, dict[str, object]]] = []
    backend.debugScreenRequested.connect(lambda screen: screens.append(screen))
    backend.command = lambda command, **payload: calls.append((command, payload))  # type: ignore[method-assign]
    event_file.write_text(
        json.dumps({"events": [{"command": "debug_show_screen", "payload": {"screen": "settings"}}]}),
        encoding="utf-8",
    )

    backend._poll_local_events()

    assert screens == ["settings"]
    assert calls == []
    assert not event_file.exists()


def test_backend_wakes_screen_for_previous_next_command_events(tmp_path: Path) -> None:
    ensure_app()
    config_path = tmp_path / "config.json"
    backend = DJConnectBackend(config_path)
    event_file = tmp_path / "command-event.json"
    backend.cfg.command_event_file = str(event_file)
    backend.cfg.paired = True
    backend.cfg.device_token = "token"
    wakes: list[bool] = []
    backend.wakeScreenRequested.connect(lambda: wakes.append(True))
    backend.command = lambda command, **payload: None  # type: ignore[method-assign]
    event_file.write_text(
        json.dumps({"events": [{"command": "previous", "payload": {}}, {"command": "next", "payload": {}}]}),
        encoding="utf-8",
    )

    backend._poll_local_events()

    assert len(wakes) == 2


def test_backend_toast_can_be_shown_and_hidden(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")

    backend.showToast("Opgeslagen")

    assert backend.toastVisible is True
    assert backend.toastText == "Opgeslagen"
    assert backend.toastIcon == "music"

    backend.showToastForContext("Wachtrij", "queue")

    assert backend.toastVisible is True
    assert backend.toastText == "Wachtrij"
    assert backend.toastIcon == "queue"

    backend.hideToast()

    assert backend.toastVisible is False
    assert backend.toastText == ""
    assert backend.toastIcon == "music"


def test_backend_auth_error_clears_pairing_and_shows_ready_to_pair(tmp_path: Path) -> None:
    ensure_app()
    config_path = tmp_path / "config.json"
    cfg = Config(
        device_id="djconnect-raspberry-pi-ABCDEF123456",
        device_token="token-1",
        paired=True,
        ha_url="http://ha.local:8123",
    )
    save_config(config_path, cfg)
    backend = DJConnectBackend(config_path)

    class FakeExecutor:
        def submit(self, worker):
            worker()

    backend._executor = FakeExecutor()  # type: ignore[assignment]
    backend._run("refresh", lambda: (_ for _ in ()).throw(AuthenticationError("unauthorized")))

    saved = load_config(config_path)
    assert backend.backendAvailable is False
    assert backend.paired is False
    assert saved.paired is False
    assert saved.device_token == ""
    assert backend.statusText == backend.t("ready_to_pair")
    assert backend.toastVisible is True
    assert backend.toastText == backend.t("ready_to_pair")


def test_backend_auth_error_does_not_toast_while_waiting_for_pairing(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")

    class FakeExecutor:
        def submit(self, worker):
            worker()

    backend._executor = FakeExecutor()  # type: ignore[assignment]
    backend._run("refresh", lambda: (_ for _ in ()).throw(AuthenticationError("unauthorized")))

    assert backend.paired is False
    assert backend.backendAvailable is False
    assert backend.statusText == backend.t("ready_to_pair")
    assert backend.toastVisible is False
    assert backend.toastText == ""


def test_backend_reboot_uses_passwordless_absolute_systemctl(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    calls: list[list[str]] = []

    def fake_run(command: list[str], **_kwargs: object) -> None:
        calls.append(command)
        if command == ["sudo", "-n", "/usr/bin/systemctl", "reboot"]:
            raise subprocess.CalledProcessError(1, command)

    with patch("djconnect_pi.app.subprocess.run", side_effect=fake_run):
        backend.rebootDevice()

    assert calls == [
        ["sudo", "-n", "/usr/bin/systemctl", "reboot"],
        ["sudo", "-n", "/bin/systemctl", "reboot"],
    ]


def test_backend_shutdown_uses_passwordless_absolute_systemctl(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    calls: list[list[str]] = []

    def fake_run(command: list[str], **_kwargs: object) -> None:
        calls.append(command)
        if command == ["sudo", "-n", "/usr/bin/systemctl", "poweroff"]:
            raise subprocess.CalledProcessError(1, command, stderr="denied")

    with patch("djconnect_pi.app.subprocess.run", side_effect=fake_run):
        backend.shutdownDevice()

    assert calls == [
        ["sudo", "-n", "/usr/bin/systemctl", "poweroff"],
        ["sudo", "-n", "/bin/systemctl", "poweroff"],
    ]


def test_backend_check_for_updates_triggers_updater_service(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")

    with patch("djconnect_pi.app.subprocess.run") as run:
        backend.checkForUpdates()

    run.assert_called_once_with(
        ["sudo", "-n", "/usr/bin/systemctl", "start", "djconnect-updater.service"],
        check=True,
        timeout=8,
        capture_output=True,
        text=True,
    )
    assert backend.statusText == backend.t("update_check_started")


def test_backend_version_mismatch_blocks_ui_and_triggers_update(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")

    with patch("djconnect_pi.app.subprocess.Popen") as popen:
        backend._apply_version_mismatch("3.1.2", "3.2.0")
        backend._apply_version_mismatch("3.1.2", "3.2.0")

    assert backend.versionMismatchVisible is True
    assert "3.1.2" in backend.versionMismatchText
    assert "3.2.0" in backend.versionMismatchText
    popen.assert_called_once_with(["systemctl", "start", "djconnect-updater.service"])


def test_backend_volume_clamps_and_dispatches_command(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    calls: list[tuple[str, dict[str, object]]] = []
    backend.command = lambda command, **payload: calls.append((command, payload))  # type: ignore[method-assign]

    backend.setVolume(125)

    assert backend.volume == 60
    assert calls == [("set_volume", {"value": 60})]


def test_backend_output_device_dispatches_command(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    calls: list[str] = []
    backend._run = lambda label, worker: calls.append(label)  # type: ignore[method-assign]

    backend.setOutputDevice(" Slaapkamer ")

    assert backend.outputDevice == "Slaapkamer"
    assert calls == ["set_output"]


def test_backend_manual_refresh_clears_pending_output_device(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")

    backend._pending_output_device = "Slaapkamer"
    backend._pending_output_until = 999999
    backend.manualRefresh()

    assert backend._pending_output_device == ""
    assert backend._pending_output_until == 0
    assert backend.toastText == backend.t("refreshing")


def test_backend_ask_dj_refresh_shows_toast(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.cfg.paired = True
    backend.cfg.device_token = "token"
    calls: list[tuple[str, object, object]] = []

    def fake_run(label: str, worker, done=None) -> None:
        calls.append((label, worker, done))

    backend._run = fake_run  # type: ignore[method-assign]
    backend._sync_config_from_disk = lambda: None  # type: ignore[method-assign]

    backend.refreshAskDjHistory()

    assert backend.toastText == backend.t("refreshing")
    assert calls
    assert calls[0][0] == backend.t("ask_dj")


def test_backend_music_dna_refresh_shows_toast(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.cfg.paired = True
    backend.cfg.device_token = "token"
    calls: list[tuple[str, object, object]] = []

    def fake_run(label: str, worker, done=None) -> None:
        calls.append((label, worker, done))

    backend._run = fake_run  # type: ignore[method-assign]
    backend._sync_config_from_disk = lambda: None  # type: ignore[method-assign]

    backend.refreshMusicDna()

    assert backend.toastText == backend.t("refreshing")
    assert backend.toastIcon == "musicdna"
    assert calls
    assert calls[0][0] == backend.t("music_dna")


def test_backend_track_insight_refresh_shows_toast(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.cfg.paired = True
    backend.cfg.device_token = "token"
    calls: list[tuple[str, object, object]] = []

    def fake_run(label: str, worker, done=None) -> None:
        calls.append((label, worker, done))

    backend._run = fake_run  # type: ignore[method-assign]
    backend._sync_config_from_disk = lambda: None  # type: ignore[method-assign]

    backend.refreshTrackInsight()

    assert backend.toastText == backend.t("refreshing")
    assert backend.toastIcon == "info"
    assert calls
    assert calls[0][0] == backend.t("track_insight")


def test_backend_track_insight_auto_open_requires_playing_track(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.cfg.paired = True
    backend.cfg.device_token = "token"
    calls: list[tuple[str, object, object]] = []

    def fake_run(label: str, worker, done=None) -> None:
        calls.append((label, worker, done))

    backend._run = fake_run  # type: ignore[method-assign]
    backend._sync_config_from_disk = lambda: None  # type: ignore[method-assign]

    backend.playback.is_playing = False
    backend.openTrackInsight()
    assert calls == []

    backend.playback.is_playing = True
    backend.openTrackInsight()
    assert calls
    assert calls[0][0] == backend.t("track_insight")


def test_backend_music_discovery_refresh_shows_toast(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.cfg.paired = True
    backend.cfg.device_token = "token"
    calls: list[tuple[str, object, object]] = []

    def fake_run(label: str, worker, done=None) -> None:
        calls.append((label, worker, done))

    backend._run = fake_run  # type: ignore[method-assign]
    backend._sync_config_from_disk = lambda: None  # type: ignore[method-assign]

    backend.refreshMusicDiscovery()

    assert backend.toastText == backend.t("refreshing")
    assert backend.toastIcon == "musicdna"
    assert calls
    assert calls[0][0] == backend.t("music_discovery")


def test_backend_sync_config_updates_live_settings(tmp_path: Path) -> None:
    ensure_app()
    config_path = tmp_path / "config.json"
    backend = DJConnectBackend(config_path)
    updated = load_config(config_path)
    updated.language = "nl" if backend.language == "en" else "en"
    updated.log_level = "DEBUG"
    updated.screen_brightness_percent = 42
    updated.screen_timeout_seconds = 300
    updated.update_channel = "beta"
    save_config(config_path, updated)

    backend._sync_config_from_disk()

    assert backend.language == updated.language
    assert backend.translationVersion == 1
    assert backend.logLevel == "DEBUG"
    assert backend.screenBrightnessPercent == 42
    assert backend.screenTimeoutSeconds == 300
    assert backend.updateChannel == "beta"


def test_backend_output_device_can_be_cleared_locally(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.playback.output_device = "Slaapkamer"
    calls: list[str] = []
    backend._run = lambda label, worker: calls.append(label)  # type: ignore[method-assign]

    backend.setOutputDevice("")

    assert backend.outputDevice == ""
    assert calls == []


def test_backend_output_device_worker_rolls_back_rejected_device(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.playback.output_device = "Woonkamer"
    backend.playback.output_devices = ("Woonkamer", "Keuken")

    class FakeClient:
        def command(self, command: str, **payload: object) -> dict[str, object]:
            return {"playback": {"output_device": "Badkamer", "output_devices": ["Woonkamer", "Keuken"]}}

        def playback_from_status(self, data: dict[str, object]) -> object:
            return HAClient(backend.cfg).playback_from_status(data)

    backend.client = FakeClient()  # type: ignore[assignment]

    with pytest.raises(Exception, match="Output device not available"):
        backend._set_output_worker("Badkamer", "Woonkamer")

    assert backend.outputDevice == "Woonkamer"


def test_backend_refresh_loads_output_devices_when_status_omits_them(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.cfg.paired = True
    backend.cfg.device_token = "token"
    parser = HAClient(backend.cfg)
    calls: list[tuple[str, dict[str, object]]] = []
    statuses: list[object] = []

    class FakeClient:
        def command(self, command: str, **payload: object) -> dict[str, object]:
            calls.append((command, payload))
            if command == "status":
                return {"playback": {"title": "Song", "artist": "Artist"}}
            if command == "devices":
                return {"devices": [{"name": "Slaapkamer R + Slaapkamer L"}]}
            return {}

        def playback_from_status(self, data: dict[str, object]) -> object:
            return parser.playback_from_status(data)

        def status(self, playback: object, queue_items: list[dict[str, object]] | None = None) -> dict[str, object]:
            statuses.append((playback, queue_items))
            return {"success": True}

    backend.client = FakeClient()  # type: ignore[assignment]
    backend._refresh_worker()

    assert [call[0] for call in calls] == ["status", "devices"]
    assert statuses
    assert statuses[0][0].output_devices == ("Slaapkamer R + Slaapkamer L",)
    assert statuses[0][1] == []


def test_backend_refresh_caches_now_playing_artwork_before_render(tmp_path: Path, monkeypatch) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.cfg.paired = True
    backend.cfg.device_token = "token"
    parser = HAClient(backend.cfg)
    playback_updates: list[Playback] = []

    class FakeClient:
        def command(self, command: str, **payload: object) -> dict[str, object]:
            if command == "status":
                return {"playback": {"title": "Song", "artist": "Artist", "image_url": "https://example.test/art.jpg"}}
            return {}

        def playback_from_status(self, data: dict[str, object]) -> Playback:
            return parser.playback_from_status(data)

        def status(self, playback: object, queue_items: list[dict[str, object]] | None = None) -> dict[str, object]:
            return {"success": True}

    monkeypatch.setattr("djconnect_pi.app.cached_image_url", lambda url, **kwargs: "file:///cache/art.jpg")
    backend._playbackReady.connect(lambda playback: playback_updates.append(playback))
    backend.client = FakeClient()  # type: ignore[assignment]

    backend._refresh_worker()

    assert playback_updates[-1].image_url == "file:///cache/art.jpg"


def test_backend_refresh_loads_active_output_device_when_status_omits_it(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.cfg.paired = True
    backend.cfg.device_token = "token"
    parser = HAClient(backend.cfg)
    statuses: list[object] = []

    class FakeClient:
        def command(self, command: str, **payload: object) -> dict[str, object]:
            if command == "status":
                return {
                    "playback": {
                        "title": "Song",
                        "artist": "Artist",
                        "output_devices": [{"name": "Slaapkamer"}, {"name": "Tuin"}],
                    }
                }
            if command == "devices":
                return {"devices": [{"name": "Slaapkamer", "is_active": False}, {"name": "Tuin", "is_active": True}]}
            return {}

        def playback_from_status(self, data: dict[str, object]) -> object:
            return parser.playback_from_status(data)

        def status(self, playback: object, queue_items: list[dict[str, object]] | None = None) -> dict[str, object]:
            statuses.append(playback)
            return {"success": True}

    backend.client = FakeClient()  # type: ignore[assignment]
    backend._refresh_worker()

    assert statuses
    assert statuses[0].output_device == "Tuin"
    assert statuses[0].output_devices == ("Slaapkamer", "Tuin")


def test_backend_refresh_preserves_selected_output_device_when_status_omits_it(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.cfg.paired = True
    backend.cfg.device_token = "token"
    backend.playback.output_device = "Keuken"
    parser = HAClient(backend.cfg)
    statuses: list[object] = []

    class FakeClient:
        def command(self, command: str, **payload: object) -> dict[str, object]:
            if command == "status":
                return {"playback": {"title": "Song", "artist": "Artist"}}
            if command == "devices":
                return {"devices": [{"name": "Woonkamer"}, {"name": "Keuken"}]}
            return {}

        def playback_from_status(self, data: dict[str, object]) -> object:
            return parser.playback_from_status(data)

        def status(self, playback: object, queue_items: list[dict[str, object]] | None = None) -> dict[str, object]:
            statuses.append(playback)
            return {"success": True}

    backend.client = FakeClient()  # type: ignore[assignment]
    backend._refresh_worker()

    assert statuses
    assert statuses[0].output_device == "Keuken"
    assert statuses[0].output_devices == ("Woonkamer", "Keuken")


def test_backend_queue_request_is_limited_to_100_items(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    calls: list[tuple[str, dict[str, object]]] = []

    class FakeClient:
        def command(self, command: str, **payload: object) -> dict[str, object]:
            calls.append((command, payload))
            return {"queue": {"items": []}}

    backend.client = FakeClient()  # type: ignore[assignment]
    backend._load_queue_worker()

    assert calls == [("queue", {"limit": 100})]


def test_backend_queue_item_worker_sends_direct_uri_without_required_context(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    parser = HAClient(backend.cfg)
    calls: list[tuple[str, dict[str, object]]] = []
    backend._refresh_worker = lambda: None  # type: ignore[method-assign]

    class FakeClient:
        def command(self, command: str, **payload: object) -> dict[str, object]:
            calls.append((command, payload))
            return {"playback": {"title": "Episode"}}

        def playback_from_status(self, data: dict[str, object]) -> Playback:
            return parser.playback_from_status(data)

    backend.client = FakeClient()  # type: ignore[assignment]

    backend._play_media_item_worker(
        "play_context_at",
        media_item_payload("play_context_at", {"title": "Episode", "uri": "spotify:episode:episode-1"}),
    )

    assert calls == [
        (
            "play_context_at",
            {
                "value": {
                    "uri": "spotify:episode:episode-1",
                    "title": "Episode",
                },
                "play": True,
            },
        )
    ]


def test_backend_queue_item_play_uses_play_context_at_command(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    parser = HAClient(backend.cfg)
    calls: list[tuple[str, dict[str, object]]] = []
    runs: list[str] = []
    backend._refresh_worker = lambda: None  # type: ignore[method-assign]

    def run_now(status: str, worker, **_: object) -> None:
        runs.append(status)
        worker()

    class FakeClient:
        def command(self, command: str, **payload: object) -> dict[str, object]:
            calls.append((command, payload))
            return {"playback": {"title": "Queued Track"}}

        def playback_from_status(self, data: dict[str, object]) -> Playback:
            return parser.playback_from_status(data)

    backend._run = run_now  # type: ignore[method-assign]
    backend.client = FakeClient()  # type: ignore[assignment]

    backend.playMediaItem(
        "play_context_at",
        json.dumps({"title": "Queued Track", "uri": "spotify:track:track-1", "index": 2}),
    )

    assert runs == ["play_context_at"]
    assert calls == [
        (
            "play_context_at",
            {
                "value": {
                    "uri": "spotify:track:track-1",
                    "title": "Queued Track",
                    "index": 2,
                },
                "play": True,
            },
        )
    ]


def test_backend_media_item_play_does_not_navigate_to_now_playing(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    parser = HAClient(backend.cfg)
    wakes: list[tuple[int, bool]] = []
    backend.temporaryWakeRequested.connect(lambda seconds, navigate: wakes.append((seconds, navigate)))
    backend._refresh_worker = lambda: None  # type: ignore[method-assign]

    def run_now(status: str, worker, **_: object) -> None:
        worker()

    class FakeClient:
        def command(self, command: str, **payload: object) -> dict[str, object]:
            return {"playback": {"title": "Queued Track", "artist": "Artist", "playing": True}}

        def playback_from_status(self, data: dict[str, object]) -> Playback:
            return parser.playback_from_status(data)

    backend._run = run_now  # type: ignore[method-assign]
    backend.client = FakeClient()  # type: ignore[assignment]

    backend.playMediaItem(
        "play_context_at",
        json.dumps({"title": "Queued Track", "uri": "spotify:track:track-1", "index": 2}),
    )
    QCoreApplication.processEvents()

    assert wakes == [(10, False)]


def test_backend_playlists_are_emitted_before_artwork_cache(tmp_path: Path, monkeypatch) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    calls: list[tuple[str, dict[str, object]]] = []
    emitted: list[tuple[str, list[dict[str, object]]]] = []
    submitted: list[object] = []
    backend._mediaListReady.connect(lambda kind, items: emitted.append((kind, items)))
    monkeypatch.setattr("djconnect_pi.app.prepare_media_artwork", lambda items: items)

    class FakeExecutor:
        def submit(self, worker):
            submitted.append(worker)

    class FakeClient:
        def command(self, command: str, **payload: object) -> dict[str, object]:
            calls.append((command, payload))
            return {"playlists": [{"name": "Friday Night", "uri": "spotify:playlist:1", "image_url": "https://example.test/a.jpg"}]}

    backend._executor = FakeExecutor()  # type: ignore[assignment]
    backend.client = FakeClient()  # type: ignore[assignment]

    backend._load_playlists_worker()

    assert calls == [("playlists", {"limit": 100})]
    assert emitted[0][0] == "playlists"
    assert emitted[0][1][0]["title"] == "Friday Night"
    assert emitted[0][1][0]["imageUrl"] == "https://example.test/a.jpg"
    assert submitted


def test_backend_artwork_cache_is_limited_and_deduplicated(tmp_path: Path, monkeypatch) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    submitted: list[object] = []
    processed_lengths: list[int] = []

    def fake_prepare(items: list[dict[str, object]]) -> list[dict[str, object]]:
        processed_lengths.append(len(items))
        return items

    class FakeExecutor:
        def submit(self, worker):
            submitted.append(worker)

    backend._executor = FakeExecutor()  # type: ignore[assignment]
    monkeypatch.setattr("djconnect_pi.app.prepare_media_artwork", fake_prepare)
    items = [{"title": f"Item {index}", "imageUrl": f"https://example.test/{index}.jpg"} for index in range(40)]

    backend._cache_media_artwork_async("playlists", items)
    backend._cache_media_artwork_async("playlists", items)

    assert len(submitted) == 1
    submitted[0]()
    assert processed_lengths == [6]


def test_backend_skips_duplicate_media_loads_while_in_flight(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.cfg.paired = True
    backend.cfg.device_token = "token"
    calls: list[tuple[str, object, object]] = []

    def fake_run(label: str, worker, done=None) -> None:
        calls.append((label, worker, done))

    backend._run = fake_run  # type: ignore[method-assign]
    backend._sync_config_from_disk = lambda: None  # type: ignore[method-assign]

    backend.loadQueue()
    backend.loadQueue()
    backend.loadPlaylists()
    backend.loadPlaylists()

    assert len(calls) == 2
    assert backend.toastText == backend.t("refreshing")
    assert calls[0][0] == backend.t("queue")
    assert calls[1][0] == backend.t("playlists")

    assert calls[0][2] is not None
    calls[0][2]()  # type: ignore[operator]
    backend.loadQueue()

    assert len(calls) == 3


def test_backend_shuffle_and_repeat_dispatch_commands(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    calls: list[tuple[str, dict[str, object]]] = []
    backend.command = lambda command, **payload: calls.append((command, payload))  # type: ignore[method-assign]

    backend.toggleShuffle()
    backend.cycleRepeat()
    backend.cycleRepeat()

    assert calls == [
        ("set_shuffle", {"value": True}),
        ("set_repeat", {"value": "context"}),
        ("set_repeat", {"value": "track"}),
    ]
