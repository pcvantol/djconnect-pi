from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import logging

import requests
import pytest

from djconnect_pi.client_api import ClientAPI, ClientAPIState, MAX_REQUEST_BYTES, _mdns_properties
from djconnect_pi.client_api import ClientAPIHandler
from djconnect_pi.config import Config, load_config, save_config
from djconnect_pi.web_portal import index_html


def start_api(tmp_path: Path, *, device_token: str = "") -> tuple[ClientAPI, Config, list[str]]:
    cfg = Config(
        device_id="djconnect-raspberry-pi-ABCDEF123456",
        pairing_code="123456",
        local_api_host="127.0.0.1",
        local_api_port=0,
        device_token=device_token,
    )
    events: list[str] = []
    api = ClientAPI(
        ClientAPIState(
            cfg=cfg,
            config_path=tmp_path / "config.json",
            playback_provider=lambda: {"title": "Alive"},
            command_handler=lambda command, payload: {"success": True, "command": command},
            screenshot_handler=lambda: {"success": True, "path": "/tmp/screenshot.png"},
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
    assert info["app_version"] == cfg.version
    assert info["local_url"] == cfg.local_url
    assert info["paired"] is False
    assert info["ha_pairing_status"] == "pending"
    assert info["capabilities"]["local_dj_response_endpoint"] is False
    assert info["capabilities"]["ask_dj_supported"] is True
    assert info["capabilities"]["ask_dj_mode"] == "text_actions"
    assert info["capabilities"]["ask_dj_free_input_supported"] is True
    assert info["capabilities"]["ask_dj_actions_supported"] is True
    assert info["capabilities"]["voice_supported"] is False
    assert info["capabilities"]["tts_supported"] is False
    assert info["capabilities"]["local_audio_supported"] is False
    assert pairing["pair_code"] == "123456"
    assert pairing["pairing_code"] == "123456"
    assert pairing["pairing_token"] == "123456"
    assert pairing["device_id"] == cfg.device_id
    assert pairing["client_type"] == "raspberry_pi"


def test_client_api_log_message_formats_http_server_args(caplog) -> None:
    caplog.set_level(logging.INFO)

    ClientAPIHandler.log_message(object(), '"%s" %s %s', "GET /api/device/pairing-info HTTP/1.1", "200", "-")

    assert "GET /api/device/pairing-info" in caplog.text


def test_postman_collection_documents_local_api_endpoints() -> None:
    path = Path("docs/postman/DJConnect Pi Local Client API.postman_collection.json")
    collection = json.loads(path.read_text(encoding="utf-8"))
    urls = {item["request"]["url"]["raw"] for item in collection["item"]}
    scripts = "\n".join(
        line
        for event in collection.get("event", [])
        for line in event.get("script", {}).get("exec", [])
    )

    assert "{{client_api_url}}/api/device/info" in urls
    assert "{{client_api_url}}/api/device/pairing-info" in urls
    assert "{{client_api_url}}/api/device/pair" in urls
    assert "{{client_api_url}}/api/device/command" in urls
    assert "{{client_api_url}}/api/device/dj_response" not in urls
    assert "{{client_api_url}}/api/debug/screenshot" in urls
    assert "{{client_api_url}}/api/device/forget" in urls
    assert "{{client_api_url}}/api/device/restart" in urls
    assert "{{client_api_url}}/api/device/shutdown" in urls
    assert "status is 2xx" in scripts
    assert "response is successful JSON" in scripts


def test_web_portal_renders_diagnostics_block() -> None:
    html = index_html("3.1.55").decode("utf-8")

    assert "<h2>Diagnostics</h2>" in html
    assert 'id="diagnostics"' in html
    assert "diagnosticsHtml" in html
    assert "data.diagnostics" in html
    assert ".chip.running" in html
    assert "Controleer op updates" in html


def test_web_portal_media_buttons_and_refresh_are_clickable() -> None:
    html = index_html("3.1.64").decode("utf-8")

    assert "encodeURIComponent(JSON.stringify(item))" in html
    assert "decodeURIComponent" in html
    assert "playMedia(command,encodedItem)" in html
    assert "function mediaPayload(command,item)" in html
    assert "value.context_uri=context" in html
    assert "value.offset_uri=uri" in html
    assert "itemHtml(i,'start_queue_item')" in html
    assert "itemHtml(i,'play_context_at')" not in html
    assert "selectOutput(this.value)" in html
    assert "pendingOutputDevice" not in html
    assert "const selectedOutput=playback.output_device" in html
    assert "none.textContent=t('none')" in html
    assert "setBusy('refreshButton',true,t('refreshing'))" in html
    assert "refreshAll(true)" in html
    assert "scrollLogsToBottom()" in html
    assert "setBusy('logsRefreshButton',true,t('refreshing'))" in html


def test_web_portal_has_local_games_with_sound_hooks() -> None:
    html = index_html("3.1.64").decode("utf-8")

    assert "id=\"gameCanvas\"" in html
    assert "const gameDefs" in html
    assert "function sfx(kind)" in html
    assert "AudioContext" in html
    assert "navigator.vibrate" in html
    assert "game_help_asteroids:'Beweeg links en rechts. Schiet om meteorieten te raken.'" in html
    assert "game_help_asteroids:'Move left and right. Fire to hit meteors.'" in html
    assert "power:[0,7,24,31]" in html
    assert "setInterval(gameTick,33)" in html
    assert "Gekopieerd naar klembord" in html
    assert "const I18N" in html
    assert 'data-i18n="settings"' in html
    assert "translateStatic()" in html
    assert "adjustVolume(-10)" in html
    assert "adjustVolume(10)" in html
    assert "range.selectNodeContents(logs)" in html
    assert "document.execCommand('copy')" in html
    assert "Instellingen opslaan" not in html
    assert "saveSettingsDebounced(t('brightness_saved'))" in html
    assert "button.warning" in html
    assert 'class="warning" onclick="confirm(' in html
    toast_css = html[html.index(".toast") : html.index(".toast::before")]
    assert "box-shadow" not in toast_css


def test_mdns_properties_include_ha_discovery_fields() -> None:
    cfg = Config(device_id="djconnect-raspberry-pi-ABCDEF123456", device_name="Kitchen Pi")

    properties = _mdns_properties(cfg, "http://192.0.2.10:18080")

    assert properties == {
        "device_id": "djconnect-raspberry-pi-ABCDEF123456",
        "client_type": "raspberry_pi",
        "version": cfg.version,
        "app_version": cfg.version,
        "device_name": "Kitchen Pi",
        "local_url": "http://192.0.2.10:18080",
        "pair_code": cfg.pairing_code,
        "paired": "false",
    }


def test_mdns_is_not_advertised_when_already_paired(tmp_path: Path, monkeypatch) -> None:
    registered: list[object] = []

    class FakeZeroconf:
        def register_service(self, info: object) -> None:
            registered.append(info)

        def unregister_service(self, info: object) -> None:
            pass

        def close(self) -> None:
            pass

    class FakeServiceInfo:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.args = args
            self.kwargs = kwargs

    monkeypatch.setattr("djconnect_pi.client_api.Zeroconf", FakeZeroconf)
    monkeypatch.setattr("djconnect_pi.client_api.ServiceInfo", FakeServiceInfo)
    monkeypatch.setattr("djconnect_pi.client_api._local_ip", lambda: "127.0.0.1")
    config_path = tmp_path / "config.json"
    cfg = Config(
        device_id="djconnect-raspberry-pi-ABCDEF123456",
        local_api_host="127.0.0.1",
        local_api_port=18080,
        local_url="http://127.0.0.1:18080",
        paired=True,
        device_token="token-1",
    )
    save_config(config_path, cfg)
    api = ClientAPI(
        ClientAPIState(
            cfg=cfg,
            config_path=config_path,
            playback_provider=lambda: {},
            command_handler=lambda command, payload: {"success": True},
            screenshot_handler=lambda: {"success": True},
            pair_handler=lambda: None,
            forget_handler=lambda: None,
        )
    )
    api.refresh_mdns()

    assert registered == []


def test_mdns_stops_after_pair_and_returns_after_forget(tmp_path: Path, monkeypatch) -> None:
    registered: list[object] = []
    unregistered: list[object] = []

    class FakeZeroconf:
        def register_service(self, info: object) -> None:
            registered.append(info)

        def unregister_service(self, info: object) -> None:
            unregistered.append(info)

        def close(self) -> None:
            pass

    class FakeServiceInfo:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.args = args
            self.kwargs = kwargs

    monkeypatch.setattr("djconnect_pi.client_api.Zeroconf", FakeZeroconf)
    monkeypatch.setattr("djconnect_pi.client_api.ServiceInfo", FakeServiceInfo)
    monkeypatch.setattr("djconnect_pi.client_api._local_ip", lambda: "127.0.0.1")
    config_path = tmp_path / "config.json"
    cfg = Config(
        device_id="djconnect-raspberry-pi-ABCDEF123456",
        local_api_host="127.0.0.1",
        local_api_port=18080,
        local_url="http://127.0.0.1:18080",
    )
    save_config(config_path, cfg)
    api = ClientAPI(
        ClientAPIState(
            cfg=cfg,
            config_path=config_path,
            playback_provider=lambda: {},
            command_handler=lambda command, payload: {"success": True},
            screenshot_handler=lambda: {"success": True},
            pair_handler=lambda: None,
            forget_handler=lambda: None,
        )
    )

    api.refresh_mdns()
    assert len(registered) == 1
    saved = load_config(config_path)
    saved.device_token = "token-1"
    saved.paired = True
    save_config(config_path, saved)
    api.refresh_mdns()
    assert len(unregistered) == 1
    saved.device_token = ""
    saved.paired = False
    save_config(config_path, saved)
    api.refresh_mdns()

    assert len(registered) == 2


def test_client_api_pair_stores_token_and_ha_url(tmp_path: Path) -> None:
    api, cfg, events = start_api(tmp_path)
    config_path = tmp_path / "config.json"
    try:
        response = requests.post(
            f"{cfg.local_url}/api/device/pair",
            json={
                "device_id": cfg.device_id,
                "client_type": "raspberry_pi",
                "device_token": "token-1",
                "ha_local_url": "http://ha:8123",
            },
            timeout=3,
        )
    finally:
        api.stop()

    saved = load_config(config_path)
    assert response.status_code == 200
    assert saved.device_token == "token-1"
    assert saved.ha_url == "http://ha:8123"
    assert saved.paired is True
    assert "paired" in events


@pytest.mark.parametrize(
    ("payload", "error"),
    [
        ({"client_type": "esp32", "device_token": "token-1", "ha_local_url": "http://ha:8123"}, "invalid_client_type"),
        (
            {
                "client_type": "raspberry_pi",
                "device_id": "djconnect-raspberry-pi-WRONG000000",
                "device_token": "token-1",
                "ha_local_url": "http://ha:8123",
            },
            "invalid_device_id",
        ),
    ],
)
def test_client_api_pair_rejects_wrong_identity(tmp_path: Path, payload: dict[str, str], error: str) -> None:
    api, cfg, events = start_api(tmp_path)
    try:
        response = requests.post(f"{cfg.local_url}/api/device/pair", json=payload, timeout=3)
    finally:
        api.stop()

    saved = load_config(tmp_path / "config.json")
    assert response.status_code == 400
    assert response.json()["error"] == error
    assert saved.device_token == ""
    assert saved.paired is False
    assert events == []


def test_client_api_pairing_info_reloads_rotated_pairing_code(tmp_path: Path) -> None:
    api, cfg, _events = start_api(tmp_path)
    config_path = tmp_path / "config.json"
    updated = load_config(config_path)
    updated.pairing_code = "654321"
    save_config(config_path, updated)
    try:
        pairing = requests.get(f"{cfg.local_url}/api/device/pairing-info", timeout=3).json()
    finally:
        api.stop()

    assert pairing["pair_code"] == "654321"
    assert pairing["pairing_code"] == "654321"
    assert pairing["pairing_token"] == "654321"


def test_client_api_does_not_expose_local_dj_response_endpoint(tmp_path: Path) -> None:
    api, cfg, events = start_api(tmp_path, device_token="token-1")
    try:
        response = requests.post(
            f"{cfg.local_url}/api/device/dj_response",
            json={"text": "Hoi"},
            headers={"Authorization": "Bearer token-1"},
            timeout=3,
        )
    finally:
        api.stop()

    assert response.status_code == 404
    assert events == []


def test_client_api_restart_and_shutdown_require_device_auth(tmp_path: Path) -> None:
    cfg = Config(
        device_id="djconnect-raspberry-pi-ABCDEF123456",
        pairing_code="123456",
        local_api_host="127.0.0.1",
        local_api_port=0,
        device_token="token-1",
    )
    commands: list[str] = []
    api = ClientAPI(
        ClientAPIState(
            cfg=cfg,
            config_path=tmp_path / "config.json",
            playback_provider=lambda: {"title": "Alive"},
            command_handler=lambda command, payload: commands.append(command) or {"success": True, "command": command},
            screenshot_handler=lambda: {"success": True, "path": "/tmp/screenshot.png"},
            pair_handler=lambda: None,
            forget_handler=lambda: None,
        )
    )
    try:
        try:
            api.start()
        except PermissionError as exc:
            pytest.skip(f"socket bind not permitted in this environment: {exc}")
        unauth = requests.post(f"{cfg.local_url}/api/device/restart", timeout=3)
        wrong_device = requests.post(
            f"{cfg.local_url}/api/device/restart",
            headers={"Authorization": "Bearer token-1", "X-DJConnect-Device-ID": "other-device"},
            timeout=3,
        )
        restart = requests.post(
            f"{cfg.local_url}/api/device/restart",
            headers={"Authorization": "Bearer token-1", "X-DJConnect-Device-ID": cfg.device_id},
            timeout=3,
        )
        shutdown = requests.post(
            f"{cfg.local_url}/api/device/shutdown",
            headers={"Authorization": "Bearer token-1", "X-DJConnect-Device-ID": cfg.device_id},
            timeout=3,
        )
    finally:
        api.stop()

    assert unauth.status_code == 401
    assert unauth.json()["success"] is False
    assert wrong_device.status_code == 403
    assert wrong_device.json()["error"] == "unauthorized"
    assert restart.status_code == 200
    assert restart.json() == {"success": True, "message": "Restart scheduled"}
    assert shutdown.status_code == 200
    assert shutdown.json() == {"success": True, "message": "Shutdown scheduled"}
    assert commands == ["reboot", "shutdown"]


def test_client_api_debug_screenshot_allows_loopback_when_paired(tmp_path: Path) -> None:
    api, cfg, _events = start_api(tmp_path, device_token="token-1")
    try:
        unauth_loopback = requests.get(f"{cfg.local_url}/api/debug/screenshot", timeout=3)
        ok = requests.get(
            f"{cfg.local_url}/api/debug/screenshot",
            headers={"Authorization": "Bearer token-1"},
            timeout=3,
        )
    finally:
        api.stop()

    assert unauth_loopback.status_code == 200
    assert ok.status_code == 200
    assert ok.json()["path"] == "/tmp/screenshot.png"


def test_client_api_debug_screen_is_loopback_only(tmp_path: Path) -> None:
    api, cfg, events = start_api(tmp_path)
    try:
        response = requests.get(f"{cfg.local_url}/api/debug/screen?screen=settings", timeout=3)
    finally:
        api.stop()

    assert response.status_code == 200
    assert response.json()["command"] == "debug_show_screen"
    assert response.json()["success"] is True
    assert events == []


def test_client_api_rejects_oversized_request_body(tmp_path: Path) -> None:
    api, cfg, _events = start_api(tmp_path, device_token="token-1")
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
