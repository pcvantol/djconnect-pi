from __future__ import annotations

import json
from pathlib import Path
import subprocess

import djconnect_pi.client_api_daemon as client_api_daemon
from djconnect_pi.client_api_daemon import ClientAPIDaemon, _systemd_unit_status
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
    assert any(item["name"] == "Updater" and "djconnect-updater.timer" in item["detail"] for item in diagnostics)


def test_systemd_unit_status_normalizes_systemctl_output(monkeypatch) -> None:
    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="active\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert _systemd_unit_status("Touch UI", "djconnect-client.service") == {
        "name": "Touch UI",
        "status": "running",
        "detail": "djconnect-client.service: active",
    }
