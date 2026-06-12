from __future__ import annotations

from pathlib import Path
from typing import Any

import requests
import pytest

from djconnect_pi.client_api import ClientAPI, ClientAPIState, MAX_REQUEST_BYTES, _mdns_properties
from djconnect_pi.config import Config


def start_api(tmp_path: Path) -> tuple[ClientAPI, Config, list[str]]:
    cfg = Config(
        device_id="djconnect-raspberry-pi-ABCDEF123456",
        local_api_host="127.0.0.1",
        local_api_port=0,
    )
    events: list[str] = []
    api = ClientAPI(
        ClientAPIState(
            cfg=cfg,
            config_path=tmp_path / "config.json",
            playback_provider=lambda: {"title": "Alive"},
            command_handler=lambda command, payload: {"success": True, "command": command},
            dj_response_handler=lambda payload: events.append(str(payload.get("text"))) or {"success": True},
            pair_handler=lambda: events.append("paired"),
            forget_handler=lambda: events.append("forgotten"),
        )
    )
    try:
        api.start()
    except PermissionError as exc:
        pytest.skip(f"socket bind not permitted in this environment: {exc}")
    return api, cfg, events


def test_client_api_info_and_pairing_info(tmp_path: Path) -> None:
    api, cfg, _events = start_api(tmp_path)
    try:
        info = requests.get(f"{cfg.local_url}/api/device/info", timeout=3).json()
        pairing = requests.get(f"{cfg.local_url}/api/device/pairing-info", timeout=3).json()
    finally:
        api.stop()

    assert info["client_type"] == "raspberry_pi"
    assert info["local_url"] == cfg.local_url
    assert info["capabilities"]["local_dj_response_endpoint"] is True
    assert pairing["pair_code"] == "ABCDEF123456"


def test_mdns_properties_include_ha_discovery_fields() -> None:
    cfg = Config(device_id="djconnect-raspberry-pi-ABCDEF123456", device_name="Kitchen Pi")

    properties = _mdns_properties(cfg, "http://192.0.2.10:18080")

    assert properties == {
        "device_id": "djconnect-raspberry-pi-ABCDEF123456",
        "client_type": "raspberry_pi",
        "version": cfg.version,
        "device_name": "Kitchen Pi",
        "local_url": "http://192.0.2.10:18080",
    }


def test_client_api_pair_stores_token_and_ha_url(tmp_path: Path) -> None:
    api, cfg, events = start_api(tmp_path)
    try:
        response = requests.post(
            f"{cfg.local_url}/api/device/pair",
            json={"device_token": "token-1", "ha_local_url": "http://ha:8123"},
            timeout=3,
        )
    finally:
        api.stop()

    assert response.status_code == 200
    assert cfg.device_token == "token-1"
    assert cfg.ha_url == "http://ha:8123"
    assert cfg.paired is True
    assert "paired" in events


def test_client_api_requires_auth_for_dj_response(tmp_path: Path) -> None:
    api, cfg, events = start_api(tmp_path)
    cfg.device_token = "token-1"
    try:
        unauth = requests.post(f"{cfg.local_url}/api/device/dj_response", json={"text": "Hoi"}, timeout=3)
        ok = requests.post(
            f"{cfg.local_url}/api/device/dj_response",
            json={"text": "Hoi"},
            headers={"Authorization": "Bearer token-1"},
            timeout=3,
        )
    finally:
        api.stop()

    assert unauth.status_code == 401
    assert ok.status_code == 200
    assert "Hoi" in events


def test_client_api_rejects_oversized_request_body(tmp_path: Path) -> None:
    api, cfg, _events = start_api(tmp_path)
    cfg.device_token = "token-1"
    try:
        response = requests.post(
            f"{cfg.local_url}/api/device/command",
            data=b"{" + b'"x":"' + (b"a" * MAX_REQUEST_BYTES) + b'"}',
            headers={"Authorization": "Bearer token-1", "Content-Type": "application/json"},
            timeout=3,
        )
    finally:
        api.stop()

    assert response.status_code == 413
    assert response.json()["error"] == "request_too_large"
