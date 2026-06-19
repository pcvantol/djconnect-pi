from __future__ import annotations

import json
from pathlib import Path
import subprocess

import djconnect_pi.client_api_daemon as client_api_daemon
from djconnect_pi.client_api_daemon import ClientAPIDaemon, _systemd_unit_status
from djconnect_pi.config import Config, save_config
from djconnect_pi.ha import HAClient


def test_client_api_daemon_queue_parser_hides_repeated_current_track() -> None:
    queue = client_api_daemon._parse_queue_items(
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


def test_client_api_daemon_writes_dj_response_event(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    event_file = tmp_path / "dj-response.json"
    save_config(config_path, Config(dj_response_file=str(event_file)))
    daemon = ClientAPIDaemon(config_path)

    result = daemon._dj_response({"text": "Hallo"})

    assert result["success"] is True
    assert result["displayed"] is True
    assert result["audio_played"] is False
    assert json.loads(event_file.read_text(encoding="utf-8")) == {"text": "Hallo"}


def test_client_api_daemon_queues_command_events(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    event_file = tmp_path / "command-event.json"
    save_config(config_path, Config(command_event_file=str(event_file)))
    daemon = ClientAPIDaemon(config_path)

    first = daemon._command("next", {"command": "next"})
    second = daemon._command("previous", {"command": "previous"})

    events = json.loads(event_file.read_text(encoding="utf-8"))["events"]
    assert first["success"] is True
    assert second["success"] is True
    assert [event["command"] for event in events] == ["next", "previous"]


def test_client_api_daemon_requests_debug_screenshot(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "config.json"
    event_file = tmp_path / "screenshot-request.json"
    screenshot_file = tmp_path / "screenshot.png"
    save_config(
        config_path,
        Config(screenshot_event_file=str(event_file), screenshot_file=str(screenshot_file)),
    )
    daemon = ClientAPIDaemon(config_path)
    monkeypatch.setattr(client_api_daemon, "SCREENSHOT_TIMEOUT_SECONDS", 0.01)

    result = daemon._screenshot()

    assert result["success"] is False
    assert result["error"] == "screenshot_timeout"
    assert result["path"] == str(screenshot_file)
    assert json.loads(event_file.read_text(encoding="utf-8"))["target"] == str(screenshot_file)


def test_client_api_daemon_portal_state_includes_diagnostics(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "config.json"
    save_config(config_path, Config(local_url="http://127.0.0.1:18080", ha_url="http://ha:8123", paired=False, device_token=""))
    daemon = ClientAPIDaemon(config_path)
    monkeypatch.setattr(
        client_api_daemon,
        "_systemd_unit_status",
        lambda label, unit: {"name": label, "status": "running", "detail": f"{unit}: active"},
    )

    state = daemon._portal_state(set())

    diagnostics = state["diagnostics"]
    assert {"name": "Local Client API", "status": "running", "detail": "http://127.0.0.1:18080"} in diagnostics
    assert any(item["name"] == "Touch UI" and item["status"] == "running" for item in diagnostics)
    assert any(item["name"] == "Update progress UI" and "djconnect-update-ui.service" in item["detail"] for item in diagnostics)
    assert any(item["name"] == "Updater" and "djconnect-updater.timer" in item["detail"] for item in diagnostics)
    assert any(item["name"] == "Nightly reboot" and "djconnect-nightly-reboot.timer" in item["detail"] for item in diagnostics)


def test_client_api_daemon_portal_state_loads_output_devices_when_status_omits_them(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "config.json"
    save_config(config_path, Config(ha_url="http://ha:8123", paired=True, device_token="token"))
    daemon = ClientAPIDaemon(config_path)
    parser = HAClient(Config())
    calls: list[str] = []

    class FakeHAClient:
        def __init__(self, cfg: Config) -> None:
            self.cfg = cfg

        def command(self, command: str, **payload: object) -> dict[str, object]:
            calls.append(command)
            if command == "status":
                return {"playback": {"title": "Song"}}
            if command == "devices":
                return {"devices": [{"name": "Woonkamer"}, {"name": "Keuken"}]}
            return {}

        def playback_from_status(self, data: dict[str, object]) -> object:
            return parser.playback_from_status(data)

    monkeypatch.setattr(client_api_daemon, "HAClient", FakeHAClient)
    monkeypatch.setattr(
        client_api_daemon,
        "_systemd_unit_status",
        lambda label, unit: {"name": label, "status": "running", "detail": f"{unit}: active"},
    )

    state = daemon._portal_state(set())

    assert calls == ["status", "devices"]
    assert state["backend_available"] is True
    assert state["playback"]["output_devices"] == ["Woonkamer", "Keuken"]
    assert state["playback"]["output_device"] == ""


def test_client_api_daemon_portal_state_requests_playlists_with_safe_limit(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "config.json"
    save_config(config_path, Config(ha_url="http://ha:8123", paired=True, device_token="token"))
    daemon = ClientAPIDaemon(config_path)
    parser = HAClient(Config())
    calls: list[tuple[str, dict[str, object]]] = []

    class FakeHAClient:
        def __init__(self, cfg: Config) -> None:
            self.cfg = cfg

        def command(self, command: str, **payload: object) -> dict[str, object]:
            calls.append((command, payload))
            if command == "status":
                return {"playback": {"title": "Song"}}
            if command == "playlists":
                return {"playlists": [{"name": "Friday", "uri": "spotify:playlist:1"}]}
            return {}

        def playback_from_status(self, data: dict[str, object]) -> object:
            return parser.playback_from_status(data)

    monkeypatch.setattr(client_api_daemon, "HAClient", FakeHAClient)
    monkeypatch.setattr(
        client_api_daemon,
        "_systemd_unit_status",
        lambda label, unit: {"name": label, "status": "running", "detail": f"{unit}: active"},
    )

    state = daemon._portal_state({"playlists"})

    assert calls == [("status", {}), ("devices", {}), ("playlists", {"limit": 100})]
    assert state["playlists"][0]["title"] == "Friday"


def test_systemd_unit_status_normalizes_systemctl_output(monkeypatch) -> None:
    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="active\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert _systemd_unit_status("Touch UI", "djconnect-client.service") == {
        "name": "Touch UI",
        "status": "running",
        "detail": "djconnect-client.service: active",
    }
