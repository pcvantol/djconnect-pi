from __future__ import annotations

from pathlib import Path
import json
import subprocess
from unittest.mock import Mock, patch

from PySide6.QtCore import QCoreApplication

from djconnect_pi.app import DJConnectBackend, _format_duration, _format_logs_for_display, cached_image_url, parse_playlist_items, parse_queue_items


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
                        "title": "Track One",
                        "artist": "Artist One",
                        "uri": "spotify:track:1",
                        "album_image_url": "https://example.test/track.jpg",
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
    backend.setLanguage("en")
    reloaded = DJConnectBackend(config_path)

    assert backend.language == "en"
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

    backend._poll_local_events()

    assert backend.djResponseVisible is False
    assert backend.djResponseText == "Hallo vanaf HA"
    assert backend.toastVisible is True
    assert backend.toastText == "Hallo vanaf HA"
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


def test_backend_toast_can_be_shown_and_hidden(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")

    backend.showToast("Opgeslagen")

    assert backend.toastVisible is True
    assert backend.toastText == "Opgeslagen"

    backend.hideToast()

    assert backend.toastVisible is False
    assert backend.toastText == ""


def test_backend_reboot_falls_back_to_passwordless_sudo(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    calls: list[list[str]] = []

    def fake_run(command: list[str], **_kwargs: object) -> None:
        calls.append(command)
        if command == ["systemctl", "reboot"]:
            raise subprocess.CalledProcessError(1, command)

    with patch("djconnect_pi.app.subprocess.run", side_effect=fake_run):
        backend.rebootDevice()

    assert calls == [["systemctl", "reboot"], ["sudo", "-n", "systemctl", "reboot"]]


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

    assert backend.volume == 100
    assert calls == [("set_volume", {"value": 100})]


def test_backend_output_device_dispatches_command(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    calls: list[tuple[str, dict[str, object]]] = []
    backend.command = lambda command, **payload: calls.append((command, payload))  # type: ignore[method-assign]

    backend.setOutputDevice(" Slaapkamer ")

    assert backend.outputDevice == "Slaapkamer"
    assert calls == [("set_output", {"value": "Slaapkamer"})]


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
