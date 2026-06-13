from __future__ import annotations

import json
from pathlib import Path

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
