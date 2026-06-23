from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from unittest.mock import patch

import pytest

from djconnect_pi.config import Config
from djconnect_pi.ha import (
    AuthenticationError,
    BackendUnavailable,
    DJConnectError,
    HAClient,
    Playback,
    ProtocolVersionMismatch,
    _compatible_ha_version,
)


@dataclass
class FakeResponse:
    status_code: int
    payload: dict[str, Any] | None = None
    text: str = ""
    json_error: Exception | None = None
    raw_content: bytes | None = None

    @property
    def content(self) -> bytes:
        if self.raw_content is not None:
            return self.raw_content
        return b"{}" if self.payload is not None else b""

    def json(self) -> dict[str, Any]:
        if self.json_error is not None:
            raise self.json_error
        return self.payload or {}


def test_pair_sends_raspberry_pi_identity_and_stores_token() -> None:
    cfg = Config(ha_url="http://ha", device_id="djconnect-raspberry-pi-ABCDEF123456")
    client = HAClient(cfg)
    captured: dict[str, Any] = {}

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        captured["url"] = url
        captured["json"] = kwargs["json"]
        return FakeResponse(200, {"device_token": "token-1"})

    with patch("djconnect_pi.ha.requests.post", side_effect=fake_post):
        client.pair("123456")

    assert captured["url"] == "http://ha/api/djconnect/pair"
    assert captured["json"]["client_type"] == "raspberry_pi"
    assert captured["json"]["device_id"] == "djconnect-raspberry-pi-ABCDEF123456"
    assert captured["json"]["app_version"] == cfg.version
    assert captured["json"]["language"] == cfg.language
    assert captured["json"]["pair_code"] == "123456"
    assert captured["json"]["capabilities"]["voice"] is False
    assert captured["json"]["capabilities"]["voice_supported"] is False
    assert captured["json"]["capabilities"]["tts_supported"] is False
    assert captured["json"]["capabilities"]["local_audio_supported"] is False
    assert captured["json"]["capabilities"]["ask_dj_supported"] is True
    assert captured["json"]["capabilities"]["ask_dj_mode"] == "readonly_actions"
    assert captured["json"]["capabilities"]["ask_dj_free_input_supported"] is False
    assert captured["json"]["capabilities"]["ask_dj_actions_supported"] is True
    assert captured["json"]["capabilities"]["local_dj_response_endpoint"] is False
    assert "device_type" not in captured["json"]
    assert "device_language" not in captured["json"]
    assert "voice_enabled" not in captured["json"]
    assert "wakeword_enabled" not in captured["json"]
    assert cfg.device_token == "token-1"
    assert cfg.paired is True


def test_status_uses_bearer_token_and_playback_fields() -> None:
    cfg = Config(
        ha_url="http://ha",
        device_id="djconnect-raspberry-pi-ABCDEF123456",
        device_token="token-1",
        paired=True,
    )
    client = HAClient(cfg)
    captured: dict[str, Any] = {}

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        captured.update(kwargs)
        return FakeResponse(200, {"success": True})

    with patch("djconnect_pi.ha.requests.post", side_effect=fake_post):
        client.status(Playback(title="Alive", artist="Pearl Jam", is_playing=True, volume=37, shuffle=True, repeat="context"))

    assert captured["headers"]["Authorization"] == "Bearer token-1"
    assert captured["headers"]["X-DJConnect-Device-ID"] == "djconnect-raspberry-pi-ABCDEF123456"
    assert captured["json"]["last_track"] == "Alive"
    assert captured["json"]["artist"] == "Pearl Jam"
    assert captured["json"]["client_type"] == "raspberry_pi"
    assert captured["json"]["app_version"] == cfg.version
    assert captured["json"]["language"] == cfg.language
    assert captured["json"]["ha_pairing_status"] == "paired"
    assert captured["json"]["spotify_status"] == "playing"
    assert captured["json"]["volume"] == 37
    assert captured["json"]["repeat_state"] == "context"
    for esp_only in ("battery", "wifi_rssi", "screen_state", "led_state", "screen_brightness", "screen_timeout", "speaker_volume"):
        assert esp_only not in captured["json"]


def test_command_posts_generic_command_payload() -> None:
    cfg = Config(ha_url="http://ha", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1")
    client = HAClient(cfg)
    captured: dict[str, Any] = {}

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        captured["url"] = url
        captured["json"] = kwargs["json"]
        return FakeResponse(200, {"playback": {"title": "Song"}})

    with patch("djconnect_pi.ha.requests.post", side_effect=fake_post):
        result = client.command("set_volume", value=42)

    assert captured["url"] == "http://ha/api/djconnect/command"
    assert captured["json"]["command"] == "set_volume"
    assert captured["json"]["value"] == 42
    assert captured["json"]["device_id"] == "djconnect-raspberry-pi-ABCDEF123456"
    assert captured["json"]["client_type"] == "raspberry_pi"
    assert result["playback"]["title"] == "Song"


def test_ask_dj_history_gets_since_revision() -> None:
    cfg = Config(ha_url="http://ha", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1")
    client = HAClient(cfg)
    captured: dict[str, Any] = {}

    def fake_get(url: str, **kwargs: Any) -> FakeResponse:
        captured["url"] = url
        captured["headers"] = kwargs["headers"]
        return FakeResponse(200, {"success": True, "messages": []})

    with patch("djconnect_pi.ha.requests.get", side_effect=fake_get):
        client.ask_dj_history(12)

    assert captured["url"] == "http://ha/api/djconnect/ask_dj/history?since_revision=12"
    assert captured["headers"]["Authorization"] == "Bearer token-1"
    assert captured["headers"]["X-DJConnect-Device-ID"] == "djconnect-raspberry-pi-ABCDEF123456"
    assert captured["headers"]["X-DJConnect-Client-Type"] == "raspberry_pi"


def test_ask_dj_action_uses_structured_command_payload() -> None:
    cfg = Config(ha_url="http://ha", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1")
    client = HAClient(cfg)
    captured: dict[str, Any] = {}

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        captured["url"] = url
        captured["json"] = kwargs["json"]
        captured["headers"] = kwargs["headers"]
        return FakeResponse(200, {"success": True, "messages": []})

    with patch("djconnect_pi.ha.requests.post", side_effect=fake_post):
        client.ask_dj_action({"kind": "confirmation", "response_value": "yes"})

    assert captured["url"] == "http://ha/api/djconnect/command"
    assert captured["json"]["command"] == "ask_dj_action"
    assert captured["json"]["action"] == {"kind": "confirmation", "response_value": "yes"}
    assert "prompt" not in captured["json"]
    assert "text" not in captured["json"]
    assert captured["headers"]["Authorization"] == "Bearer token-1"


def test_playback_from_status_accepts_aliases() -> None:
    playback = HAClient(Config()).playback_from_status(
        {
            "playback": {
                "track": "Even Flow",
                "artists": "Pearl Jam",
                "album_image_url": "http://image",
                "playing": True,
                "volume_percent": 66,
                "repeat": "track",
                "shuffle": True,
                "progress_ms": 138000,
                "duration_ms": 210000,
                "output_devices": [{"name": "Slaapkamer R + Slaapkamer L"}],
                "output_device": "Slaapkamer R + Slaapkamer L",
            }
        }
    )

    assert playback.title == "Even Flow"
    assert playback.artist == "Pearl Jam"
    assert playback.image_url == "http://image"
    assert playback.is_playing is True
    assert playback.volume == 66
    assert playback.repeat == "track"
    assert playback.shuffle is True
    assert playback.position_seconds == 138
    assert playback.duration_seconds == 210
    assert playback.output_device == "Slaapkamer R + Slaapkamer L"
    assert playback.output_devices == ("Slaapkamer R + Slaapkamer L",)


def test_playback_from_status_does_not_select_first_output_device_as_fallback() -> None:
    playback = HAClient(Config()).playback_from_status(
        {
            "playback": {
                "output_devices": [{"name": "Woonkamer"}, {"name": "Keuken"}],
            }
        }
    )

    assert playback.output_device == ""
    assert playback.output_devices == ("Woonkamer", "Keuken")


def test_playback_from_status_maps_output_device_id_to_name() -> None:
    playback = HAClient(Config()).playback_from_status(
        {
            "playback": {
                "output_devices": [
                    {"id": "speaker-1", "name": "Woonkamer"},
                    {"id": "speaker-2", "name": "Slaapkamer"},
                ],
                "output_device": "speaker-2",
            }
        }
    )

    assert playback.output_device == "Slaapkamer"
    assert playback.output_devices == ("Woonkamer", "Slaapkamer")


def test_playback_from_status_uses_active_output_device_flag() -> None:
    playback = HAClient(Config()).playback_from_status(
        {
            "playback": {
                "output_devices": [
                    {"id": "speaker-1", "name": "Woonkamer", "is_active": False},
                    {"id": "speaker-2", "name": "Slaapkamer", "is_active": True},
                ],
            }
        }
    )

    assert playback.output_device == "Slaapkamer"
    assert playback.output_devices == ("Woonkamer", "Slaapkamer")


def test_playback_from_status_uses_active_device_object() -> None:
    playback = HAClient(Config()).playback_from_status(
        {
            "playback": {
                "output_devices": [{"name": "Tuin"}, {"name": "Keuken"}],
                "device": {"id": "speaker-tuin", "name": "Tuin"},
            }
        }
    )

    assert playback.output_device == "Tuin"
    assert playback.output_devices == ("Tuin", "Keuken")


def test_playback_from_status_uses_current_device_object_without_output_list() -> None:
    playback = HAClient(Config()).playback_from_status(
        {
            "playback": {
                "current_device": {"id": "speaker-tuin", "name": "Tuin"},
            }
        }
    )

    assert playback.output_device == "Tuin"
    assert playback.output_devices == ("Tuin",)


def test_protocol_mismatch_raises_djconnect_error() -> None:
    client = HAClient(Config(ha_url="http://ha"))

    with pytest.raises(DJConnectError, match="Protocol version mismatch"):
        client._json(FakeResponse(426, {"error": "version_mismatch"}, "version_mismatch"))


def test_invalid_ha_json_is_logged(caplog) -> None:
    client = HAClient(Config(ha_url="http://ha"))
    caplog.set_level("WARNING")

    with pytest.raises(DJConnectError, match="invalid JSON"):
        client._json(FakeResponse(200, {}, json_error=ValueError("bad json")))

    assert "Home Assistant returned invalid JSON" in caplog.text
    assert "bad json" in caplog.text


def test_backend_unavailable_response_raises_specific_error(caplog) -> None:
    client = HAClient(Config(ha_url="http://ha"))
    caplog.set_level("WARNING")

    with pytest.raises(BackendUnavailable, match="Spotify unavailable"):
        client._json(FakeResponse(200, {"success": False, "backend_available": False, "error": "Spotify unavailable"}))

    assert "playback backend unavailable" in caplog.text


def test_status_has_playback_false_decodes_without_backend_unavailable() -> None:
    playback = HAClient(Config()).playback_from_status(
        {
            "success": True,
            "backend_available": True,
            "ha_version": "3.1.0",
            "playback": {"has_playback": False, "is_playing": False},
        }
    )

    assert playback.title == ""
    assert playback.artist == ""
    assert playback.is_playing is False


@pytest.mark.parametrize("command", ["status", "queue", "devices", "playlists"])
def test_successful_empty_playback_command_response_is_valid(command: str) -> None:
    cfg = Config(ha_url="http://ha", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1")
    client = HAClient(cfg)

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        return FakeResponse(200, {"success": True, "backend_available": True, "command": command, "playback": {}})

    with patch("djconnect_pi.ha.requests.post", side_effect=fake_post):
        data = client.command(command)

    playback = client.playback_from_status(data)
    assert data["success"] is True
    assert playback.title == ""
    assert playback.artist == ""
    assert playback.is_playing is False


def test_unauthorized_response_raises_authentication_error(caplog) -> None:
    client = HAClient(Config(ha_url="http://ha"))
    caplog.set_level("WARNING")

    with pytest.raises(AuthenticationError, match="unauthorized"):
        client._json(FakeResponse(401, {"success": False, "error": "unauthorized"}))

    assert "Home Assistant returned HTTP 401" in caplog.text


@pytest.mark.parametrize("status_code", [401, 403, 404])
def test_auth_stale_http_statuses_raise_authentication_error(status_code: int) -> None:
    client = HAClient(Config(ha_url="http://ha"))

    with pytest.raises(AuthenticationError):
        client._json(FakeResponse(status_code, {"success": False, "error": "unauthorized"}))


def test_empty_2xx_response_is_contract_error(caplog) -> None:
    client = HAClient(Config(ha_url="http://ha"))
    caplog.set_level("WARNING")

    with pytest.raises(DJConnectError, match="empty JSON response"):
        client._json(FakeResponse(200, None, raw_content=b""))

    assert "violates the DJConnect JSON contract" in caplog.text


def test_devices_accept_outputs_alias() -> None:
    playback = HAClient(Config()).playback_from_status({"outputs": [{"name": "Woonkamer"}, {"id": "kitchen"}]})

    assert playback.output_devices == ("Woonkamer", "kitchen")


def test_ha_version_compatibility_uses_major_minor_range() -> None:
    assert _compatible_ha_version("3.1.2", "3.1.0") is True
    assert _compatible_ha_version("3.1.2", "3.1.99") is True
    assert _compatible_ha_version("3.1.2", "3.2.0") is False
    assert _compatible_ha_version("3.1.2", "3.0.9") is False


def test_ha_version_mismatch_raises_protocol_error() -> None:
    client = HAClient(Config(version="3.1.2"))

    with pytest.raises(ProtocolVersionMismatch) as exc:
        client._validate_ha_version({"ha_version": "3.2.0"})

    assert exc.value.client_version == "3.1.2"
    assert exc.value.ha_version == "3.2.0"


def test_ha_major_minor_response_is_accepted() -> None:
    client = HAClient(Config(version="3.1.2"))

    client._validate_ha_version({"ha_major_minor": "3.1"})
