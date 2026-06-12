from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from unittest.mock import patch

import pytest

from djconnect_pi.config import Config
from djconnect_pi.ha import DJConnectError, HAClient, Playback, ProtocolVersionMismatch, _compatible_ha_version


@dataclass
class FakeResponse:
    status_code: int
    payload: dict[str, Any] | None = None
    text: str = ""
    json_error: Exception | None = None

    @property
    def content(self) -> bytes:
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
    assert captured["json"]["pair_code"] == "123456"
    assert captured["json"]["capabilities"]["voice"] is False
    assert captured["json"]["capabilities"]["local_dj_response_endpoint"] is True
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
    assert captured["json"]["spotify_status"] == "playing"
    assert captured["json"]["volume"] == 37
    assert captured["json"]["repeat_state"] == "context"


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
    assert captured["json"] == {"command": "set_volume", "value": 42}
    assert result["playback"]["title"] == "Song"


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
