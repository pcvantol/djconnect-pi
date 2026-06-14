from __future__ import annotations

import json
from pathlib import Path

import djconnect_pi.client_api_daemon as client_api_daemon
from djconnect_pi.client_api_daemon import ClientAPIDaemon
from djconnect_pi.config import Config, save_config


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
