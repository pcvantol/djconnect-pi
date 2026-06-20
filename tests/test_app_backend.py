from __future__ import annotations

from pathlib import Path
import json
import subprocess
from unittest.mock import Mock, patch

import pytest
from PySide6.QtCore import QCoreApplication

from djconnect_pi.config import load_config, save_config
from djconnect_pi.app import (
    DJConnectBackend,
    _format_duration,
    _format_logs_for_display,
    _read_tail_text,
    cached_image_url,
    media_item_payload,
    parse_ask_dj_messages,
    parse_playlist_items,
    parse_queue_items,
    prepare_media_artwork,
)
from djconnect_pi.ha import AuthenticationError, HAClient, Playback


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
    assert "2026-06-13" not in text


def test_log_tail_reader_caps_large_files(tmp_path: Path) -> None:
    log_file = tmp_path / "client.log"
    log_file.write_text("A" * 200 + "TAIL", encoding="utf-8")

    assert _read_tail_text(log_file, 8) == "AAAATAIL"


def test_duration_format_for_now_playing_progress() -> None:
    assert _format_duration(0) == "0:00"
    assert _format_duration(138) == "2:18"
    assert _format_duration(210) == "3:30"


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


def test_ask_dj_parser_accepts_history_rich_messages() -> None:
    messages = parse_ask_dj_messages(
        {
            "messages": [
                {"id": "u1", "role": "user", "text": "Welke albums?"},
                {
                    "id": "a1",
                    "role": "assistant",
                    "dj_text": "Radiohead heeft meerdere albums.",
                    "images": [{"url": "http://ha/api/image/1", "thumbnail_url": "http://ha/api/thumb/1"}],
                    "links": [{"title": "Wikipedia", "url": "http://ha/link", "kind": "wikipedia"}],
                    "sources": [{"name": "MusicBrainz", "url": "http://ha/source", "source": "musicbrainz"}],
                    "playback_actions": [{"kind": "track", "title": "Play Now", "uri": "spotify:track:1", "subtitle": "Radiohead"}],
                    "confirmation_actions": [{"kind": "confirmation", "action_style": "confirmation", "response_value": "yes"}],
                },
            ]
        }
    )

    assert messages[0]["role"] == "user"
    assert messages[0]["text"] == "Welke albums?"
    assert messages[1]["text"] == "Radiohead heeft meerdere albums."
    assert messages[1]["images"] == [{"url": "http://ha/api/thumb/1", "title": ""}]
    assert len(messages[1]["links"]) == 2
    assert [action["kind"] for action in messages[1]["actions"]] == ["track", "confirmation"]
    assert "spotify:track:1" in messages[1]["actions"][0]["payload"]


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
    backend.setUpdateChannel("beta")
    reloaded = DJConnectBackend(config_path)

    assert backend.screenTimeoutSeconds == 120
    assert backend.updateChannel == "beta"
    assert reloaded.screenTimeoutSeconds == 120
    assert reloaded.updateChannel == "beta"


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


def test_backend_rejects_unknown_language(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")

    backend.setLanguage("de")

    assert backend.language == "nl"


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

    backend.hideToast()

    assert backend.toastVisible is False
    assert backend.toastText == ""


def test_backend_auth_error_marks_backend_unavailable_and_shows_toast(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    backend.cfg.paired = True
    backend.cfg.device_token = "token-1"

    class FakeExecutor:
        def submit(self, worker):
            worker()

    backend._executor = FakeExecutor()  # type: ignore[assignment]
    backend._run("refresh", lambda: (_ for _ in ()).throw(AuthenticationError("unauthorized")))

    assert backend.backendAvailable is False
    assert backend.statusText == backend.t("ha_auth_failed")
    assert backend.toastVisible is True
    assert backend.toastText == backend.t("ha_auth_failed")


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

        def status(self, playback: object) -> dict[str, object]:
            statuses.append(playback)
            return {"success": True}

    backend.client = FakeClient()  # type: ignore[assignment]
    backend._refresh_worker()

    assert [call[0] for call in calls] == ["status", "devices"]
    assert statuses
    assert statuses[0].output_devices == ("Slaapkamer R + Slaapkamer L",)


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

        def status(self, playback: object) -> dict[str, object]:
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

        def status(self, playback: object) -> dict[str, object]:
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

        def status(self, playback: object) -> dict[str, object]:
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
