from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import re
import time
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
    StaleBackendAction,
    UnsupportedBackendCapability,
    _compatible_ha_version,
    music_backend_summary_from,
)


ROOT = Path(__file__).resolve().parents[1]
ROUTE_SCAN_SUFFIXES = {"", ".json", ".md", ".py", ".qml", ".sh", ".service", ".timer", ".toml", ".txt"}


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


class FakeWebSocket:
    def __init__(self, frames: list[dict[str, Any]]) -> None:
        self.frames = [json.dumps(frame) for frame in frames]
        self.sent: list[dict[str, Any]] = []
        self.closed = False

    def recv(self) -> str:
        if not self.frames:
            raise TimeoutError("timeout")
        return self.frames.pop(0)

    def send(self, payload: str) -> None:
        self.sent.append(json.loads(payload))

    def close(self) -> None:
        self.closed = True


def test_home_assistant_djconnect_routes_use_v1_prefix() -> None:
    route_prefix = "/api/" + "djconnect/"
    old_route = re.compile(re.escape(route_prefix) + r"(?!v1(?:/|\b))")
    scanned_roots = [
        ROOT / "src",
        ROOT / "tests",
        ROOT / "docs",
        ROOT / "README.md",
        ROOT / "HANDOFF.md",
        ROOT / "CHAT_BOOTSTRAP.md",
        ROOT / "TESTS.md",
        ROOT / "CHANGELOG.md",
    ]
    violations: list[str] = []
    for root in scanned_roots:
        paths = root.rglob("*") if root.is_dir() else [root]
        for path in paths:
            if (
                path.is_dir()
                or path.name.startswith(".")
                or path.suffix not in ROUTE_SCAN_SUFFIXES
                or any(part.endswith(".egg-info") for part in path.parts)
            ):
                continue
            text = path.read_text(encoding="utf-8")
            for line_no, line in enumerate(text.splitlines(), start=1):
                if old_route.search(line):
                    violations.append(f"{path.relative_to(ROOT)}:{line_no}: {line.strip()}")

    assert violations == []


def test_client_contract_does_not_use_raw_ask_dj_or_old_search_aliases() -> None:
    scanned_roots = [
        ROOT / "src",
        ROOT / "docs",
        ROOT / "README.md",
        ROOT / "HANDOFF.md",
        ROOT / "CHAT_BOOTSTRAP.md",
        ROOT / "TESTS.md",
    ]
    forbidden_patterns = {
        "raw Ask DJ route": re.compile(r"/api/djconnect/v1/ask_dj(?:[\"'`\s]|$)"),
        "HA Ask DJ service": re.compile(r"\bdjconnect\.ask_dj\b"),
        "spotify search alias": re.compile(r"\bspotify_search_query\b"),
        "last spotify search alias": re.compile(r"\blast_spotify_search\b"),
    }
    violations: list[str] = []
    for root in scanned_roots:
        paths = root.rglob("*") if root.is_dir() else [root]
        for path in paths:
            if (
                path.is_dir()
                or path.name.startswith(".")
                or path.suffix not in ROUTE_SCAN_SUFFIXES
                or any(part.endswith(".egg-info") for part in path.parts)
            ):
                continue
            text = path.read_text(encoding="utf-8")
            for line_no, line in enumerate(text.splitlines(), start=1):
                for label, pattern in forbidden_patterns.items():
                    if label == "raw Ask DJ route" and "fixture-only legacy contract coverage" in line:
                        continue
                    if pattern.search(line):
                        violations.append(f"{path.relative_to(ROOT)}:{line_no}: {label}: {line.strip()}")

    assert violations == []


def test_pair_sends_raspberry_pi_identity_and_stores_token() -> None:
    cfg = Config(ha_url="http://ha", device_id="djconnect-raspberry-pi-ABCDEF123456", language="de")
    client = HAClient(cfg)
    captured: dict[str, Any] = {}

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        captured["url"] = url
        captured["json"] = kwargs["json"]
        return FakeResponse(200, {"device_token": "token-1"})

    with patch("djconnect_pi.ha.requests.post", side_effect=fake_post):
        client.pair("123456")

    assert captured["url"] == "http://ha/api/djconnect/v1/pair"
    assert captured["json"]["client_type"] == "raspberry_pi"
    assert captured["json"]["device_id"] == "djconnect-raspberry-pi-ABCDEF123456"
    assert captured["json"]["app_version"] == cfg.version
    assert captured["json"]["pair_code"] == "123456"
    assert captured["json"]["capabilities"]["voice"] is False
    assert captured["json"]["capabilities"]["voice_supported"] is False
    assert captured["json"]["capabilities"]["tts_supported"] is False
    assert captured["json"]["capabilities"]["local_audio_supported"] is False
    assert captured["json"]["capabilities"]["ask_dj_supported"] is True
    assert captured["json"]["capabilities"]["ask_dj_mode"] == "readonly_actions"
    assert captured["json"]["capabilities"]["ask_dj_free_input_supported"] is False
    assert captured["json"]["capabilities"]["ask_dj_actions_supported"] is True
    assert captured["json"]["capabilities"]["ask_dj_voice_supported"] is False
    assert captured["json"]["capabilities"]["ask_dj_audio_response_supported"] is False
    assert captured["json"]["capabilities"]["local_dj_response_endpoint"] is False
    assert "device_type" not in captured["json"]
    assert "device_language" not in captured["json"]
    assert "language" not in captured["json"]
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
        language="fr",
    )
    client = HAClient(cfg)
    captured: dict[str, Any] = {}

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        captured.update(kwargs)
        return FakeResponse(200, {"success": True})

    with patch("djconnect_pi.ha.requests.post", side_effect=fake_post):
        client.status(
            Playback(
                title="Alive",
                artist="Pearl Jam",
                is_playing=True,
                volume=37,
                shuffle=True,
                repeat="context",
                output_device="Woonkamer",
                output_devices=("Woonkamer", "Keuken"),
            ),
            queue_items=[{"title": "Next up"}],
        )

    assert captured["headers"]["Authorization"] == "Bearer token-1"
    assert captured["headers"]["X-DJConnect-Device-ID"] == "djconnect-raspberry-pi-ABCDEF123456"
    assert captured["json"]["last_track"] == "Alive"
    assert captured["json"]["artist"] == "Pearl Jam"
    assert captured["json"]["client_type"] == "raspberry_pi"
    assert captured["json"]["app_version"] == cfg.version
    assert captured["json"]["language"] == "fr-FR"
    assert captured["json"]["ha_pairing_status"] == "paired"
    assert captured["json"]["spotify_status"] == "playing"
    assert captured["json"]["volume"] == 37
    assert captured["json"]["repeat_state"] == "context"
    assert captured["json"]["sound_output"] == "Woonkamer"
    assert captured["json"]["output"] == "Woonkamer"
    assert captured["json"]["output_device"] == "Woonkamer"
    assert captured["json"]["output_devices"] == ["Woonkamer", "Keuken"]
    assert captured["json"]["available_outputs"] == [
        {"id": "Woonkamer", "name": "Woonkamer"},
        {"id": "Keuken", "name": "Keuken"},
    ]
    assert captured["json"]["playback"]["device"] == {"id": "Woonkamer", "name": "Woonkamer"}
    assert captured["json"]["playback"]["output_devices"] == ["Woonkamer", "Keuken"]
    assert captured["json"]["queue"] == {"items": [{"title": "Next up"}]}
    for esp_only in ("battery", "wifi_rssi", "screen_state", "led_state", "screen_brightness", "screen_timeout", "speaker_volume"):
        assert esp_only not in captured["json"]


def test_playback_from_status_reads_current_track_favorite_aliases() -> None:
    cfg = Config()
    client = HAClient(cfg)

    liked = client.playback_from_status(
        {
            "success": True,
            "playback": {
                "title": "Track",
                "artist": "Artist",
                "uri": "backend:track:1",
                "is_liked": True,
            },
        }
    )
    unliked = client.playback_from_status(
        {
            "success": True,
            "playback": {
                "title": "Track",
                "artist": "Artist",
                "uri": "backend:track:2",
                "favorite_status": False,
            },
        }
    )

    assert liked.is_favorite is True
    assert unliked.is_favorite is False


def test_command_posts_generic_command_payload() -> None:
    cfg = Config(ha_url="http://ha", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1", language="es")
    client = HAClient(cfg)
    captured: dict[str, Any] = {}

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        captured["url"] = url
        captured["json"] = kwargs["json"]
        return FakeResponse(200, {"playback": {"title": "Song"}})

    with patch("djconnect_pi.ha.requests.post", side_effect=fake_post):
        result = client.command("set_volume", value=42)

    assert captured["url"] == "http://ha/api/djconnect/v1/command"
    assert captured["json"]["command"] == "set_volume"
    assert captured["json"]["language"] == "es-ES"
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

    assert captured["url"] == "http://ha/api/djconnect/v1/ask_dj/history?since_revision=12"
    assert captured["headers"]["Authorization"] == "Bearer token-1"
    assert captured["headers"]["X-DJConnect-Device-ID"] == "djconnect-raspberry-pi-ABCDEF123456"
    assert captured["headers"]["X-DJConnect-Client-Type"] == "raspberry_pi"


def test_ask_dj_history_clear_posts_identity_and_music_dna_key() -> None:
    cfg = Config(ha_url="http://ha", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1", device_name="Kitchen Pi", music_dna_key="dna-1", language="nl", websocket_fast_path_enabled=False)
    client = HAClient(cfg)
    captured: dict[str, Any] = {}

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        captured["url"] = url
        captured["json"] = kwargs["json"]
        captured["headers"] = kwargs["headers"]
        return FakeResponse(200, {"success": True, "cleared": True, "history_revision": 7, "clear_revision": 3, "messages": []})

    with patch("djconnect_pi.ha.requests.post", side_effect=fake_post):
        data = client.ask_dj_history_clear()

    assert captured["url"] == "http://ha/api/djconnect/v1/ask_dj/history/clear"
    assert captured["headers"]["Authorization"] == "Bearer token-1"
    assert captured["json"]["client_type"] == "raspberry_pi"
    assert captured["json"]["device_id"] == "djconnect-raspberry-pi-ABCDEF123456"
    assert captured["json"]["device_name"] == "Kitchen Pi"
    assert captured["json"]["identity"] == {
        "client_type": "raspberry_pi",
        "device_id": "djconnect-raspberry-pi-ABCDEF123456",
        "device_name": "Kitchen Pi",
    }
    assert captured["json"]["music_dna_key"] == "dna-1"
    assert captured["json"]["language"] == "nl-NL"
    assert data["clear_revision"] == 3


def test_ask_dj_action_uses_structured_command_payload() -> None:
    cfg = Config(ha_url="http://ha", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1", language="en")
    client = HAClient(cfg)
    captured: dict[str, Any] = {}

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        captured["url"] = url
        captured["json"] = kwargs["json"]
        captured["headers"] = kwargs["headers"]
        return FakeResponse(200, {"success": True, "messages": []})

    with patch("djconnect_pi.ha.requests.post", side_effect=fake_post):
        client.ask_dj_action({"kind": "confirmation", "response_value": "yes", "music_dna_key": "followup-1"})

    assert captured["url"] == "http://ha/api/djconnect/v1/command"
    assert captured["json"]["command"] == "ask_dj_followup_response"
    assert captured["json"]["language"] == "en-GB"
    assert captured["json"]["value"] == {"kind": "confirmation", "response_value": "yes", "music_dna_key": "followup-1"}
    assert "play" not in captured["json"]
    assert "prompt" not in captured["json"]
    assert "text" not in captured["json"]


def test_status_and_command_forward_optional_mood() -> None:
    cfg = Config(ha_url="http://ha", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1", mood=12, websocket_fast_path_enabled=False)
    client = HAClient(cfg)
    captured: list[dict[str, Any]] = []

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        captured.append({"url": url, "json": kwargs["json"], "headers": kwargs["headers"]})
        return FakeResponse(200, {"success": True})

    with patch("djconnect_pi.ha.requests.post", side_effect=fake_post):
        client.status(Playback(title="Track", artist="Artist"))
        client.command("ask_dj_play_recommendation", value={"uri": "spotify:track:1"})

    assert captured[0]["url"] == "http://ha/api/djconnect/v1/status"
    assert captured[0]["json"]["mood"] == 12
    assert captured[0]["headers"]["X-DJConnect-Mood"] == "12"
    assert captured[1]["url"] == "http://ha/api/djconnect/v1/command"
    assert captured[1]["json"]["command"] == "ask_dj_play_recommendation"
    assert captured[1]["json"]["mood"] == 12
    assert captured[1]["headers"]["X-DJConnect-Mood"] == "12"


def test_track_insight_posts_current_track_metadata_and_music_dna_headers() -> None:
    cfg = Config(
        ha_url="http://ha",
        device_id="djconnect-raspberry-pi-ABCDEF123456",
        device_token="token-1",
        language="nl",
        music_dna_key="music-dna-1",
        mood=88,
    )
    cfg.music_backend = "music_assistant"
    cfg.music_target_player = {"id": "media_player.mass_woonkamer", "name": "Woonkamer"}
    client = HAClient(cfg)
    captured: dict[str, Any] = {}

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        captured["url"] = url
        captured["json"] = kwargs["json"]
        captured["headers"] = kwargs["headers"]
        captured["timeout"] = kwargs["timeout"]
        return FakeResponse(200, {"success": True, "track_insight": {"track": {"title": "Strobe"}}})

    with patch("djconnect_pi.ha.requests.post", side_effect=fake_post):
        client.track_insight(Playback(title="Strobe", artist="deadmau5", album="For Lack of a Better Name", image_url="https://example.test/art.jpg", uri="spotify:track:1", genres=("progressive house",)))

    assert captured["url"] == "http://ha/api/djconnect/v1/track_insight"
    assert captured["headers"]["Authorization"] == "Bearer token-1"
    assert captured["headers"]["Accept-Language"] == "nl-NL"
    assert captured["headers"]["X-DJConnect-Language"] == "nl-NL"
    assert captured["headers"]["X-DJConnect-Locale"] == "nl-NL"
    assert captured["headers"]["X-DJConnect-Device-ID"] == "djconnect-raspberry-pi-ABCDEF123456"
    assert captured["headers"]["X-DJConnect-Music-DNA-Key"] == "music-dna-1"
    assert captured["headers"]["X-DJConnect-Mood"] == "88"
    assert captured["json"]["title"] == "Strobe"
    assert captured["json"]["include_visual_profile"] is True
    assert captured["json"]["force_refresh"] is False
    assert captured["json"]["track"] == {
        "title": "Strobe",
        "artist": "deadmau5",
        "album": "For Lack of a Better Name",
        "artwork_url": "https://example.test/art.jpg",
        "uri": "spotify:track:1",
        "genres": ["progressive house"],
    }
    assert captured["json"]["player_id"] == "media_player.mass_woonkamer"
    assert captured["json"]["music_backend"] == "music_assistant"
    assert captured["json"]["mood"] == 88
    assert captured["timeout"] == 10.0
    assert captured["json"]["artist"] == "deadmau5"
    assert captured["json"]["album"] == "For Lack of a Better Name"
    assert captured["json"]["artwork_url"] == "https://example.test/art.jpg"
    assert captured["json"]["uri"] == "spotify:track:1"
    assert captured["json"]["genres"] == ["progressive house"]
    assert captured["json"]["track"] == {
        "title": "Strobe",
        "artist": "deadmau5",
        "album": "For Lack of a Better Name",
        "artwork_url": "https://example.test/art.jpg",
        "uri": "spotify:track:1",
        "genres": ["progressive house"],
    }
    assert captured["json"]["player_id"] == "media_player.mass_woonkamer"
    assert captured["json"]["music_backend"] == "music_assistant"
    assert captured["json"]["language"] == "nl-NL"
    assert captured["json"]["locale"] == "nl-NL"
    assert captured["json"]["mood"] == 88
    assert captured["json"]["include_visual_profile"] is True


def test_track_insight_no_track_and_rate_limit_are_retryable_states() -> None:
    cfg = Config(ha_url="http://ha", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1", websocket_fast_path_enabled=False)
    client = HAClient(cfg)

    with patch("djconnect_pi.ha.requests.post", return_value=FakeResponse(404, {"success": False, "error": "no_track_playing"})):
        no_track = client.track_insight(Playback())
    with patch("djconnect_pi.ha.requests.post", return_value=FakeResponse(429, {"success": False, "error": "rate_limited"})):
        limited = client.track_insight(Playback(title="Track"))

    assert no_track["error"] == "no_track_playing"
    assert limited["error"] == "rate_limited"


def test_track_insight_logging_omits_tokens_and_temporary_urls(caplog) -> None:
    cfg = Config(ha_url="http://ha", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="secret-token")
    client = HAClient(cfg)
    caplog.set_level("DEBUG")

    with patch(
        "djconnect_pi.ha.requests.post",
        return_value=FakeResponse(200, {"success": True, "track": {"title": "Track", "artwork_url": "https://temporary.example.test/art.jpg"}, "analysis": {"summary": "Private-ish text"}}),
    ):
        client.track_insight(Playback(title="Track", image_url="https://temporary.example.test/art.jpg"))

    assert "secret-token" not in caplog.text
    assert "temporary.example.test" not in caplog.text
    assert "Private-ish text" not in caplog.text


def test_music_dna_profile_posts_identity_language_mood_and_key() -> None:
    cfg = Config(
        ha_url="http://ha",
        device_id="djconnect-raspberry-pi-ABCDEF123456",
        device_token="token-1",
        language="es",
        music_dna_key="dna-1",
        mood=35,
    )
    client = HAClient(cfg)
    captured: dict[str, Any] = {}

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        captured["url"] = url
        captured["json"] = kwargs["json"]
        captured["headers"] = kwargs["headers"]
        return FakeResponse(200, {"success": True, "enabled": True, "summary": "Perfil"})

    with patch("djconnect_pi.ha.requests.post", side_effect=fake_post):
        client.music_dna_profile()

    assert captured["url"] == "http://ha/api/djconnect/v1/music_dna/profile"
    assert captured["headers"]["X-DJConnect-Music-DNA-Key"] == "dna-1"
    assert captured["headers"]["X-DJConnect-Mood"] == "35"
    assert captured["json"]["client_type"] == "raspberry_pi"
    assert captured["json"]["language"] == "es-ES"
    assert captured["json"]["locale"] == "es-ES"
    assert captured["json"]["mood"] == 35
    assert captured["json"]["music_dna_key"] == "dna-1"


def test_music_dna_settings_enable_disable_payloads() -> None:
    cfg = Config(ha_url="http://ha", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1", websocket_fast_path_enabled=False)
    client = HAClient(cfg)
    captured: list[dict[str, Any]] = []

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        captured.append(kwargs["json"])
        return FakeResponse(200, {"success": True, "enabled": kwargs["json"]["enabled"], "profile": {"summary": "ok"}})

    with patch("djconnect_pi.ha.requests.post", side_effect=fake_post):
        client.music_dna_settings(enabled=True)
        client.music_dna_settings(enabled=False)

    assert captured[0]["enabled"] is True
    assert captured[0]["client_type"] == "raspberry_pi"
    assert captured[0]["device_id"] == "djconnect-raspberry-pi-ABCDEF123456"
    assert captured[1]["enabled"] is False


def test_music_dna_clear_keeps_enabled_state_from_backend_response() -> None:
    cfg = Config(ha_url="http://ha", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1")
    client = HAClient(cfg)

    with patch("djconnect_pi.ha.requests.post", return_value=FakeResponse(200, {"success": True, "enabled": True, "profile": {"summary": "Fresh start"}})):
        data = client.music_dna_clear()

    assert data["enabled"] is True
    assert data["profile"]["summary"] == "Fresh start"


def test_music_dna_response_updates_resolved_key_for_next_calls() -> None:
    cfg = Config(ha_url="http://ha", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1", music_dna_key="old", websocket_fast_path_enabled=False)
    client = HAClient(cfg)
    captured: list[dict[str, Any]] = []

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        captured.append(kwargs["json"])
        return FakeResponse(200, {"success": True, "enabled": True, "music_dna_key": "resolved"})

    with patch("djconnect_pi.ha.requests.post", side_effect=fake_post):
        client.music_dna_profile()
        client.music_dna_profile()

    assert captured[0]["music_dna_key"] == "old"
    assert captured[1]["music_dna_key"] == "resolved"
    assert cfg.music_dna_key == "resolved"


def test_music_discovery_feed_get_sends_pi_identity() -> None:
    cfg = Config(ha_url="http://ha", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1", music_dna_key="dna-1", websocket_fast_path_enabled=False)
    client = HAClient(cfg)
    captured: dict[str, Any] = {}

    def fake_get(url: str, **kwargs: Any) -> FakeResponse:
        captured["url"] = url
        captured["params"] = kwargs["params"]
        captured["headers"] = kwargs["headers"]
        return FakeResponse(200, {"success": True, "items": []})

    with patch("djconnect_pi.ha.requests.get", side_effect=fake_get):
        client.music_discovery_feed()

    assert captured["url"] == "http://ha/api/djconnect/v1/music_discovery"
    assert captured["headers"]["Authorization"] == "Bearer token-1"
    assert captured["params"]["client_type"] == "raspberry_pi"
    assert captured["params"]["client_id"] == "djconnect-raspberry-pi-ABCDEF123456"
    assert captured["params"]["device_id"] == "djconnect-raspberry-pi-ABCDEF123456"
    assert captured["params"]["music_dna_key"] == "dna-1"


def test_music_discovery_refresh_and_play_use_contract_endpoints() -> None:
    cfg = Config(ha_url="http://ha", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1", websocket_fast_path_enabled=False)
    client = HAClient(cfg)
    captured: list[tuple[str, dict[str, Any]]] = []

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        captured.append((url, kwargs["json"]))
        return FakeResponse(200, {"success": True})

    with patch("djconnect_pi.ha.requests.post", side_effect=fake_post):
        client.music_discovery_refresh()
        client.music_discovery_play(
            {
                "section_id": "daily",
                "discovery_item_id": "rec-1",
                "id": "rec-1",
                "kind": "track",
                "uri": "spotify:track:1",
                "title": "Track",
            }
        )

    assert captured[0][0] == "http://ha/api/djconnect/v1/music_discovery/refresh"
    assert captured[0][1]["client_type"] == "raspberry_pi"
    assert captured[1][0] == "http://ha/api/djconnect/v1/music_discovery/play"
    assert captured[1][1]["section_id"] == "daily"
    assert captured[1][1]["discovery_item_id"] == "rec-1"
    assert "id" not in captured[1][1]
    assert "uri" not in captured[1][1]
    assert "kind" not in captured[1][1]
    assert "title" not in captured[1][1]
    assert "source" not in captured[1][1]
    assert captured[1][1]["client_type"] == "raspberry_pi"
    assert captured[1][1]["device_id"] == "djconnect-raspberry-pi-ABCDEF123456"


def test_music_discovery_feedback_uses_contract_endpoint() -> None:
    cfg = Config(ha_url="http://ha", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1")
    client = HAClient(cfg)
    captured: dict[str, Any] = {}

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        captured["url"] = url
        captured["json"] = kwargs["json"]
        return FakeResponse(200, {"success": True})

    with patch("djconnect_pi.ha.requests.post", side_effect=fake_post):
        client.music_discovery_feedback({"section_id": "daily", "discovery_item_id": "rec-1", "uri": "spotify:track:1"}, "not_for_me")

    assert captured["url"] == "http://ha/api/djconnect/v1/music_discovery/feedback"
    assert captured["json"]["feedback"] == "not_for_me"
    assert captured["json"]["section_id"] == "daily"
    assert captured["json"]["discovery_item_id"] == "rec-1"
    assert "uri" not in captured["json"]
    assert captured["json"]["client_type"] == "raspberry_pi"


def test_music_discovery_feedback_support_uses_capabilities_feature() -> None:
    cfg = Config(
        ha_url="http://ha.local:8123",
        device_id="djconnect-raspberry-pi-ABCDEF123456",
        device_token="token-1",
        websocket_fast_path_enabled=True,
        ha_websocket_token="ha-token",
    )
    client = HAClient(cfg)
    sockets = [FakeWebSocket(_ws_capabilities([], features={"music_discovery_feedback": True}))]

    with (
        patch("djconnect_pi.ha_websocket._websocket_create_connection", side_effect=sockets),
        patch("djconnect_pi.ha.requests.post", return_value=_ws_session_response()),
    ):
        assert client.music_discovery_feedback_supported() is True


def test_music_discovery_uses_advertised_http_fallback_path_when_websocket_command_missing() -> None:
    cfg = Config(
        ha_url="http://ha.local:8123",
        device_id="djconnect-raspberry-pi-ABCDEF123456",
        device_token="token-1",
        websocket_fast_path_enabled=True,
        ha_websocket_token="ha-token",
    )
    client = HAClient(cfg)
    sockets = [
        FakeWebSocket(_ws_capabilities([], fallbacks={"music_discovery_refresh": "/api/djconnect/v1/music_discovery/refresh"})),
    ]
    captured: dict[str, Any] = {}

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        captured["url"] = url
        captured["json"] = kwargs["json"]
        return FakeResponse(200, {"success": True})

    with (
        patch("djconnect_pi.ha_websocket._websocket_create_connection", side_effect=sockets),
        patch("djconnect_pi.ha.requests.post", side_effect=fake_post),
    ):
        client.music_discovery_refresh()

    assert captured["url"] == "http://ha.local:8123/api/djconnect/v1/music_discovery/refresh"
    assert captured["json"]["client_type"] == "raspberry_pi"


def test_music_discovery_logging_omits_tokens_and_temporary_urls(caplog) -> None:
    cfg = Config(ha_url="http://ha", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="secret-token", websocket_fast_path_enabled=False)
    client = HAClient(cfg)
    caplog.set_level("DEBUG")

    with patch(
        "djconnect_pi.ha.requests.get",
        return_value=FakeResponse(200, {"success": True, "sections": [{"items": [{"id": "rec-1", "kind": "track", "title": "Track", "image_url": "https://temporary.example.test/image.jpg"}]}]}),
    ):
        client.music_discovery_feed()

    assert "secret-token" not in caplog.text
    assert "temporary.example.test" not in caplog.text


def test_ask_dj_play_action_uses_action_command_or_play_recommendation() -> None:
    cfg = Config(ha_url="http://ha", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1", websocket_fast_path_enabled=False)
    client = HAClient(cfg)
    captured: list[dict[str, Any]] = []

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        captured.append(kwargs["json"])
        return FakeResponse(200, {"success": True, "messages": []})

    with patch("djconnect_pi.ha.requests.post", side_effect=fake_post):
        client.ask_dj_action({"kind": "playlist", "title": "Roadtrip", "uri": "spotify:playlist:1"})
        client.ask_dj_action({"command": "custom_action", "kind": "track", "uri": "spotify:track:1"})
        client.ask_dj_action({"kind": "control", "command": "pause", "title": "Pauze"})
        client.ask_dj_action({"kind": "output", "command": "set_output", "title": "Keuken", "value": "Keuken"})

    assert captured[0]["command"] == "ask_dj_play_recommendation"
    assert captured[0]["value"]["uri"] == "spotify:playlist:1"
    assert "play" not in captured[0]
    assert captured[1]["command"] == "custom_action"
    assert captured[1]["value"]["uri"] == "spotify:track:1"
    assert "play" not in captured[1]
    assert captured[2]["command"] == "pause"
    assert captured[2]["value"]["title"] == "Pauze"
    assert "play" not in captured[2]
    assert captured[3]["command"] == "set_output"
    assert captured[3]["value"] == "Keuken"
    assert "play" not in captured[3]


def test_ask_dj_speaker_replay_action_posts_full_backend_action() -> None:
    cfg = Config(ha_url="http://ha", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1")
    client = HAClient(cfg)
    captured: dict[str, Any] = {}
    action = {
        "kind": "output",
        "command": "ask_dj_play_recommendation_on_output",
        "title": "Keuken",
        "value": {"output": "Keuken", "original_request": {"kind": "track", "uri": "spotify:track:1"}},
    }

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        captured["json"] = kwargs["json"]
        return FakeResponse(200, {"success": True, "messages": []})

    with patch("djconnect_pi.ha.requests.post", side_effect=fake_post):
        client.ask_dj_action(action)

    assert captured["json"]["command"] == "ask_dj_play_recommendation_on_output"
    assert captured["json"]["value"] == action
    assert "play" not in captured["json"]


def test_ask_dj_save_current_track_action_posts_direct_command_payload() -> None:
    cfg = Config(ha_url="http://ha", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1")
    client = HAClient(cfg)
    captured: dict[str, Any] = {}

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        captured["url"] = url
        captured["json"] = kwargs["json"]
        captured["headers"] = kwargs["headers"]
        return FakeResponse(200, {"success": True})

    with patch("djconnect_pi.ha.requests.post", side_effect=fake_post):
        client.ask_dj_action({"kind": "control", "command": "save_current_track", "button_label": "Zet in favorieten"})

    assert captured["url"] == "http://ha/api/djconnect/v1/command"
    assert captured["headers"]["Authorization"] == "Bearer token-1"
    assert captured["headers"]["X-DJConnect-Device-ID"] == "djconnect-raspberry-pi-ABCDEF123456"
    assert captured["headers"]["Content-Type"] == "application/json"
    assert captured["json"]["device_id"] == "djconnect-raspberry-pi-ABCDEF123456"
    assert captured["json"]["client_type"] == "raspberry_pi"
    assert captured["json"]["command"] == "save_current_track"
    assert captured["json"]["value"] == {"kind": "control", "command": "save_current_track", "button_label": "Zet in favorieten"}
    assert "play" not in captured["json"]


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


def test_playback_from_status_accepts_nested_spotify_images() -> None:
    playback = HAClient(Config()).playback_from_status(
        {
            "playback": {
                "track": "Alive",
                "artists": "Pearl Jam",
                "album": {
                    "images": [
                        {"url": "http://image-small", "width": 64},
                        {"url": "http://image-large", "width": 640},
                    ]
                },
            }
        }
    )

    assert playback.image_url == "http://image-large"


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


def test_backend_summary_parses_ha_32_fields() -> None:
    summary = music_backend_summary_from(
        {
            "music_backend": "music_assistant",
            "music_backend_name": "Music Assistant",
            "music_backend_available": True,
            "music_backend_revision": 4,
            "music_backend_capabilities": {"supports_queue": True, "supports_top_items": False},
            "music_target_player": {"id": "media_player.mass_woonkamer", "name": "Woonkamer"},
            "music_backend_error": None,
        }
    )

    assert summary.backend == "music_assistant"
    assert summary.name == "Music Assistant"
    assert summary.available is True
    assert summary.revision == 4
    assert summary.capabilities == {"supports_queue": True, "supports_top_items": False}
    assert summary.target_player_id == "media_player.mass_woonkamer"
    assert summary.target_player_name == "Woonkamer"


def test_backend_summary_parses_safe_error_object() -> None:
    summary = music_backend_summary_from(
        {
            "music_backend": "music_assistant",
            "music_backend_error": {"code": "target_unavailable", "message": "Target player is offline"},
        }
    )

    assert summary.error == "target_unavailable: Target player is offline"


def test_command_response_updates_backend_summary() -> None:
    cfg = Config(ha_url="http://ha", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1")
    client = HAClient(cfg)

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        return FakeResponse(
            200,
            {
                "success": True,
                "music_backend": "music_assistant",
                "music_backend_name": "Music Assistant",
                "music_backend_revision": 4,
                "music_backend_capabilities": {"supports_queue": True},
                "music_target_player": {"id": "media_player.mass_woonkamer", "name": "Woonkamer"},
            },
        )

    with patch("djconnect_pi.ha.requests.post", side_effect=fake_post):
        client.command("status")

    assert cfg.music_backend == "music_assistant"
    assert cfg.music_backend_name == "Music Assistant"
    assert cfg.music_backend_revision == 4
    assert cfg.music_backend_capabilities == {"supports_queue": True}
    assert cfg.music_target_player == {"id": "media_player.mass_woonkamer", "name": "Woonkamer"}


def test_unsupported_backend_capability_response_is_specific_error() -> None:
    client = HAClient(Config(ha_url="http://ha"))

    with pytest.raises(UnsupportedBackendCapability, match="Top items are unavailable"):
        client._json(
            FakeResponse(
                200,
                {
                    "success": False,
                    "error": "unsupported_backend_capability",
                    "capability": "supports_top_items",
                    "backend": "music_assistant",
                    "message": "Top items are unavailable for Music Assistant.",
                },
            )
        )


def test_stale_backend_action_response_is_specific_error() -> None:
    client = HAClient(Config(ha_url="http://ha"))

    with pytest.raises(StaleBackendAction, match="Ask DJ opnieuw"):
        client._json(
            FakeResponse(
                200,
                {
                    "success": False,
                    "error": "music_backend_revision_mismatch",
                    "message": "Ask DJ opnieuw voordat je deze actie gebruikt.",
                },
            )
        )


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


@pytest.mark.parametrize("error", ["not_configured", "stale_pairing", "stale_token", "invalid_token"])
def test_auth_stale_success_false_errors_raise_authentication_error(error: str) -> None:
    client = HAClient(Config(ha_url="http://ha"))

    with pytest.raises(AuthenticationError):
        client._json(FakeResponse(200, {"success": False, "error": error}))


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
    assert _compatible_ha_version("3.2.2", "3.2.0") is True
    assert _compatible_ha_version("3.2.2", "3.2.99") is True
    assert _compatible_ha_version("3.2.2", "3.1.99") is False
    assert _compatible_ha_version("3.2.2", "3.3.0") is False


def test_ha_version_mismatch_raises_protocol_error() -> None:
    client = HAClient(Config(version="3.2.2"))

    with pytest.raises(ProtocolVersionMismatch) as exc:
        client._validate_ha_version({"ha_version": "3.1.112"})

    assert exc.value.client_version == "3.2.2"
    assert exc.value.ha_version == "3.1.112"


def test_ha_major_minor_response_is_accepted() -> None:
    client = HAClient(Config(version="3.2.2"))

    client._validate_ha_version({"ha_major_minor": "3.2"})


def _ws_capabilities(commands: list[str], *, features: dict[str, bool] | None = None, fallbacks: dict[str, str] | None = None) -> list[dict[str, Any]]:
    return [
        {"type": "auth_required"},
        {"type": "auth_ok"},
        {
            "id": 1,
            "type": "result",
            "success": True,
            "result": {
                "success": True,
                "websocket_supported": True,
                "transports": {"websocket": True},
                "commands": commands,
                "features": features or {},
                "fallbacks": fallbacks or {},
            },
        },
    ]


def _ws_result(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"type": "auth_required"},
        {"type": "auth_ok"},
        {"id": 2, "type": "result", "success": True, "result": result},
    ]


def _ws_session_response(*, token: str = "ha-session-token", websocket_url: str | None = None, expires_at: float | None = None) -> FakeResponse:
    payload: dict[str, Any] = {"access_token": token}
    if websocket_url:
        payload["websocket_url"] = websocket_url
    if expires_at is not None:
        payload["expires_at"] = expires_at
    return FakeResponse(200, payload)


def _session_or_http_response(http_payload: dict[str, Any]) -> Any:
    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        if url.endswith("/api/djconnect/v1/websocket/session"):
            return _ws_session_response()
        return FakeResponse(200, http_payload)

    return fake_post


def test_websocket_fast_path_setting_false_forces_http() -> None:
    cfg = Config(ha_url="http://ha.local:8123", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1", websocket_fast_path_enabled=False)
    client = HAClient(cfg)

    with (
        patch("djconnect_pi.ha_websocket._websocket_create_connection") as connect,
        patch("djconnect_pi.ha.requests.post", return_value=FakeResponse(200, {"success": True, "transport": "http"})) as post,
    ):
        data = client.command("play")

    assert data["transport"] == "http"
    assert connect.call_count == 0
    assert post.call_count == 1
    assert client.diagnostics()["websocketEnabled"] is False


def test_websocket_fast_path_uses_session_bootstrap_without_persisted_ha_token() -> None:
    cfg = Config(
        ha_url="http://ha.local:8123",
        device_id="djconnect-raspberry-pi-ABCDEF123456",
        device_token="token-1",
        websocket_fast_path_enabled=True,
    )
    client = HAClient(cfg)
    sockets = [FakeWebSocket(_ws_capabilities(["djconnect/command"])), FakeWebSocket(_ws_result({"success": True, "transport": "websocket"}))]
    posts: list[tuple[str, dict[str, Any], dict[str, str]]] = []

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        posts.append((url, kwargs["json"], kwargs["headers"]))
        return _ws_session_response(token="short-lived-ha-token")

    with (
        patch("djconnect_pi.ha_websocket._websocket_create_connection", side_effect=sockets) as connect,
        patch("djconnect_pi.ha.requests.post", side_effect=fake_post) as post,
    ):
        data = client.command("play")

    assert data["transport"] == "websocket"
    assert connect.call_count == 2
    assert post.call_count == 1
    assert posts[0][0] == "http://ha.local:8123/api/djconnect/v1/websocket/session"
    assert posts[0][1]["device_id"] == "djconnect-raspberry-pi-ABCDEF123456"
    assert posts[0][1]["client_type"] == "raspberry_pi"
    assert "requested_commands" in posts[0][1]
    assert "djconnect/command" in posts[0][1]["requested_commands"]
    assert "djconnect/vibecast" not in posts[0][1]["requested_commands"]
    assert "access_token" not in posts[0][1]
    assert posts[0][2]["Authorization"] == "Bearer token-1"
    assert sockets[0].sent[0] == {"type": "auth", "access_token": "short-lived-ha-token"}
    assert cfg.ha_websocket_token == ""


def test_websocket_capability_detection_success_sets_diagnostics() -> None:
    cfg = Config(ha_url="http://ha.local:8123", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1", websocket_fast_path_enabled=True)
    client = HAClient(cfg)
    sockets = [FakeWebSocket(_ws_capabilities(["djconnect/command"]))]

    with (
        patch("djconnect_pi.ha_websocket._websocket_create_connection", side_effect=sockets),
        patch("djconnect_pi.ha.requests.post", return_value=_ws_session_response()),
    ):
        assert client.fast_path.can_handle("djconnect/command") is True

    assert sockets[0].sent[0] == {"type": "auth", "access_token": "ha-session-token"}
    assert sockets[0].sent[1]["type"] == "djconnect/capabilities"
    assert client.diagnostics()["websocketConnected"] is True
    assert client.diagnostics()["websocketCommands"] == ["djconnect/command"]


def test_command_websocket_success_uses_fast_path_payload_identity() -> None:
    cfg = Config(
        ha_url="http://ha.local:8123",
        device_id="djconnect-raspberry-pi-ABCDEF123456",
        device_token="token-1",
        websocket_fast_path_enabled=True,
        ha_websocket_token="ha-token",
        language="de",
    )
    client = HAClient(cfg)
    sockets = [
        FakeWebSocket(_ws_capabilities(["djconnect/command"])),
        FakeWebSocket(_ws_result({"success": True, "playback": {"title": "Alive"}})),
    ]

    with (
        patch("djconnect_pi.ha_websocket._websocket_create_connection", side_effect=sockets),
        patch("djconnect_pi.ha.requests.post", return_value=_ws_session_response()) as post,
    ):
        data = client.command("play")

    assert data["playback"]["title"] == "Alive"
    assert post.call_count == 1
    payload = sockets[1].sent[1]
    assert payload["type"] == "djconnect/command"
    assert payload["command"] == "play"
    assert payload["language"] == "de-DE"
    assert payload["client_type"] == "raspberry_pi"
    assert payload["device_id"] == "djconnect-raspberry-pi-ABCDEF123456"
    assert payload["device_token"] == "token-1"
    assert client.diagnostics()["fastPathTransport"] == "websocket"


def test_websocket_session_token_is_cached_until_expiry_window() -> None:
    cfg = Config(ha_url="http://ha.local:8123", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1", websocket_fast_path_enabled=True)
    client = HAClient(cfg)
    sockets = [
        FakeWebSocket(_ws_capabilities(["djconnect/command"])),
        FakeWebSocket(_ws_result({"success": True, "first": True})),
        FakeWebSocket(_ws_result({"success": True, "second": True})),
    ]

    with (
        patch("djconnect_pi.ha_websocket._websocket_create_connection", side_effect=sockets),
        patch("djconnect_pi.ha.requests.post", return_value=_ws_session_response(expires_at=time.time() + 600)) as post,
    ):
        assert client.command("play")["first"] is True
        assert client.command("pause")["second"] is True

    assert post.call_count == 1
    assert sockets[1].sent[0] == {"type": "auth", "access_token": "ha-session-token"}
    assert sockets[2].sent[0] == {"type": "auth", "access_token": "ha-session-token"}


def test_missing_websocket_capability_falls_back_to_http_once() -> None:
    cfg = Config(ha_url="http://ha.local:8123", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1", websocket_fast_path_enabled=True, ha_websocket_token="ha-token")
    client = HAClient(cfg)
    sockets = [FakeWebSocket(_ws_capabilities(["djconnect/track_insight"]))]

    with (
        patch("djconnect_pi.ha_websocket._websocket_create_connection", side_effect=sockets),
        patch("djconnect_pi.ha.requests.post", side_effect=_session_or_http_response({"success": True, "playback": {"title": "HTTP"}})) as post,
    ):
        data = client.command("play")

    assert data["playback"]["title"] == "HTTP"
    assert [call.args[0] for call in post.call_args_list].count("http://ha.local:8123/api/djconnect/v1/command") == 1
    assert client.diagnostics()["fastPathTransport"] == "http"


def test_ask_dj_history_clear_uses_advertised_websocket_route() -> None:
    cfg = Config(
        ha_url="http://ha.local:8123",
        device_id="djconnect-raspberry-pi-ABCDEF123456",
        device_token="token-1",
        websocket_fast_path_enabled=True,
        ha_websocket_token="ha-token",
        music_dna_key="dna-1",
    )
    client = HAClient(cfg)
    sockets = [
        FakeWebSocket(_ws_capabilities(["djconnect/ask_dj/history/clear"])),
        FakeWebSocket(_ws_result({"success": True, "cleared": True, "history_revision": 4, "clear_revision": 2, "messages": []})),
    ]

    with (
        patch("djconnect_pi.ha_websocket._websocket_create_connection", side_effect=sockets),
        patch("djconnect_pi.ha.requests.post", return_value=_ws_session_response()) as post,
    ):
        data = client.ask_dj_history_clear()

    assert data["cleared"] is True
    assert post.call_count == 1
    payload = sockets[1].sent[1]
    assert payload["type"] == "djconnect/ask_dj/history/clear"
    assert payload["client_type"] == "raspberry_pi"
    assert payload["device_id"] == "djconnect-raspberry-pi-ABCDEF123456"
    assert payload["music_dna_key"] == "dna-1"


def test_ask_dj_history_clear_falls_back_to_http_when_websocket_fails() -> None:
    cfg = Config(
        ha_url="http://ha.local:8123",
        device_id="djconnect-raspberry-pi-ABCDEF123456",
        device_token="token-1",
        websocket_fast_path_enabled=True,
        ha_websocket_token="ha-token",
    )
    client = HAClient(cfg)
    sockets = [
        FakeWebSocket(_ws_capabilities(["djconnect/ask_dj/history/clear"])),
        FakeWebSocket([{"type": "auth_required"}, {"type": "auth_ok"}, {"id": 2, "type": "result", "success": False, "error": {"message": "boom"}}]),
    ]

    with (
        patch("djconnect_pi.ha_websocket._websocket_create_connection", side_effect=sockets),
        patch("djconnect_pi.ha.requests.post", side_effect=_session_or_http_response({"success": True, "cleared": True, "history_revision": 4, "clear_revision": 2, "messages": []})) as post,
    ):
        data = client.ask_dj_history_clear()

    assert data["cleared"] is True
    assert [call.args[0] for call in post.call_args_list].count("http://ha.local:8123/api/djconnect/v1/ask_dj/history/clear") == 1
    assert client.diagnostics()["fastPathTransport"] == "http"


def test_track_insight_websocket_success_returns_normalized_result() -> None:
    cfg = Config(ha_url="https://ha.local", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1", websocket_fast_path_enabled=True, ha_websocket_token="ha-token")
    client = HAClient(cfg)
    sockets = [
        FakeWebSocket(_ws_capabilities(["djconnect/track_insight"])),
        FakeWebSocket(_ws_result({"success": True, "track_insight": {"track": {"title": "Strobe"}}})),
    ]

    with (
        patch("djconnect_pi.ha_websocket._websocket_create_connection", side_effect=sockets) as connect,
        patch("djconnect_pi.ha.requests.post", return_value=_ws_session_response()) as post,
    ):
        data = client.track_insight(Playback(title="Strobe", artist="deadmau5"))

    assert connect.call_args_list[0].args[0] == "wss://ha.local/api/websocket"
    assert data["track_insight"]["track"]["title"] == "Strobe"
    assert post.call_count == 1
    payload = sockets[1].sent[1]
    assert payload["type"] == "djconnect/track_insight"
    assert payload["title"] == "Strobe"
    assert payload["artist"] == "deadmau5"
    assert payload["include_visual_profile"] is True


def test_music_dna_profile_websocket_uses_advertised_fast_path() -> None:
    cfg = Config(
        ha_url="http://ha.local:8123",
        device_id="djconnect-raspberry-pi-ABCDEF123456",
        device_token="token-1",
        websocket_fast_path_enabled=True,
        ha_websocket_token="ha-token",
        music_dna_key="dna-1",
    )
    client = HAClient(cfg)
    sockets = [
        FakeWebSocket(_ws_capabilities(["djconnect/music_dna/profile"])),
        FakeWebSocket(_ws_result({"success": True, "enabled": False, "profile": {}})),
    ]

    with (
        patch("djconnect_pi.ha_websocket._websocket_create_connection", side_effect=sockets),
        patch("djconnect_pi.ha.requests.post", return_value=_ws_session_response()) as post,
    ):
        data = client.music_dna_profile()

    assert data["enabled"] is False
    assert post.call_count == 1
    payload = sockets[1].sent[1]
    assert payload["type"] == "djconnect/music_dna/profile"
    assert payload["client_type"] == "raspberry_pi"
    assert payload["device_id"] == "djconnect-raspberry-pi-ABCDEF123456"
    assert payload["device_token"] == "token-1"
    assert payload["music_dna_key"] == "dna-1"


def test_music_dna_settings_and_clear_websocket_use_advertised_fast_path() -> None:
    cfg = Config(ha_url="http://ha.local:8123", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1", websocket_fast_path_enabled=True)
    client = HAClient(cfg)
    sockets = [
        FakeWebSocket(_ws_capabilities(["djconnect/music_dna/settings", "djconnect/music_dna/clear"])),
        FakeWebSocket(_ws_result({"success": True, "enabled": True})),
        FakeWebSocket(_ws_result({"success": True, "enabled": False})),
    ]

    with (
        patch("djconnect_pi.ha_websocket._websocket_create_connection", side_effect=sockets),
        patch("djconnect_pi.ha.requests.post", return_value=_ws_session_response()) as post,
    ):
        assert client.music_dna_settings(enabled=True)["enabled"] is True
        assert client.music_dna_clear()["enabled"] is False

    assert post.call_count == 1
    assert sockets[1].sent[1]["type"] == "djconnect/music_dna/settings"
    assert sockets[1].sent[1]["enabled"] is True
    assert sockets[2].sent[1]["type"] == "djconnect/music_dna/clear"


def test_music_dna_export_import_remain_http_only_when_websocket_routes_advertised() -> None:
    cfg = Config(ha_url="http://ha.local:8123", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1", websocket_fast_path_enabled=True, music_dna_key="dna-1")
    client = HAClient(cfg)
    captured: list[tuple[str, dict[str, Any]]] = []

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        captured.append((url, kwargs["json"]))
        return FakeResponse(200, {"success": True, "music_dna_key": "dna-1"})

    with (
        patch("djconnect_pi.ha_websocket._websocket_create_connection") as connect,
        patch("djconnect_pi.ha.requests.post", side_effect=fake_post),
    ):
        client.music_dna_export()
        client.music_dna_import({"summary": "Imported"})

    assert connect.call_count == 0
    assert [url for url, _ in captured] == [
        "http://ha.local:8123/api/djconnect/v1/music_dna/export",
        "http://ha.local:8123/api/djconnect/v1/music_dna/import",
    ]
    assert captured[0][1]["music_dna_key"] == "dna-1"
    assert captured[1][1]["profile"] == {"summary": "Imported"}


def test_music_dna_uses_advertised_http_fallback_path_when_websocket_command_missing() -> None:
    cfg = Config(
        ha_url="http://ha.local:8123",
        device_id="djconnect-raspberry-pi-ABCDEF123456",
        device_token="token-1",
        websocket_fast_path_enabled=True,
        ha_websocket_token="ha-token",
    )
    client = HAClient(cfg)
    sockets = [
        FakeWebSocket(_ws_capabilities([], features={"music_dna": True}, fallbacks={"music_dna": {"profile": "/api/djconnect/v1/music_dna/profile"}})),
    ]
    captured: dict[str, Any] = {}

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        captured["url"] = url
        captured["json"] = kwargs["json"]
        return FakeResponse(200, {"success": True, "enabled": False})

    with (
        patch("djconnect_pi.ha_websocket._websocket_create_connection", side_effect=sockets),
        patch("djconnect_pi.ha.requests.post", side_effect=lambda url, **kwargs: _ws_session_response() if url.endswith("/websocket/session") else fake_post(url, **kwargs)),
    ):
        client.music_dna_profile()

    assert captured["url"] == "http://ha.local:8123/api/djconnect/v1/music_dna/profile"
    assert captured["json"]["client_type"] == "raspberry_pi"


def test_music_discovery_refresh_websocket_uses_advertised_fast_path() -> None:
    cfg = Config(
        ha_url="http://ha.local:8123",
        device_id="djconnect-raspberry-pi-ABCDEF123456",
        device_token="token-1",
        websocket_fast_path_enabled=True,
        ha_websocket_token="ha-token",
    )
    client = HAClient(cfg)
    sockets = [
        FakeWebSocket(_ws_capabilities(["djconnect/music_discovery/refresh"])),
        FakeWebSocket(_ws_result({"success": True, "items": [{"id": "t1", "kind": "track", "title": "Track"}]})),
    ]

    with (
        patch("djconnect_pi.ha_websocket._websocket_create_connection", side_effect=sockets),
        patch("djconnect_pi.ha.requests.post", return_value=_ws_session_response()) as post,
    ):
        data = client.music_discovery_refresh()

    assert data["items"][0]["title"] == "Track"
    assert post.call_count == 1
    payload = sockets[1].sent[1]
    assert payload["type"] == "djconnect/music_discovery/refresh"
    assert payload["client_type"] == "raspberry_pi"
    assert payload["device_id"] == "djconnect-raspberry-pi-ABCDEF123456"


def test_music_discovery_play_and_feedback_websocket_payload_uses_backend_ids_only() -> None:
    cfg = Config(ha_url="http://ha.local:8123", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1", websocket_fast_path_enabled=True)
    client = HAClient(cfg)
    sockets = [
        FakeWebSocket(_ws_capabilities(["djconnect/music_discovery/play", "djconnect/music_discovery/feedback"])),
        FakeWebSocket(_ws_result({"success": True, "played": True})),
        FakeWebSocket(_ws_result({"success": True, "feedback": True})),
    ]

    with (
        patch("djconnect_pi.ha_websocket._websocket_create_connection", side_effect=sockets),
        patch("djconnect_pi.ha.requests.post", return_value=_ws_session_response()) as post,
    ):
        client.music_discovery_play({"section_id": "new_for_you", "discovery_item_id": "rec-1", "uri": "spotify:track:1", "title": "Track"})
        client.music_discovery_feedback({"section_id": "new_for_you", "discovery_item_id": "rec-1", "uri": "spotify:track:1"}, "not_for_me")

    assert post.call_count == 1
    play_payload = sockets[1].sent[1]
    feedback_payload = sockets[2].sent[1]
    assert play_payload["type"] == "djconnect/music_discovery/play"
    assert play_payload["section_id"] == "new_for_you"
    assert play_payload["discovery_item_id"] == "rec-1"
    assert "uri" not in play_payload
    assert "title" not in play_payload
    assert feedback_payload["type"] == "djconnect/music_discovery/feedback"
    assert feedback_payload["feedback"] == "not_for_me"
    assert feedback_payload["section_id"] == "new_for_you"
    assert feedback_payload["discovery_item_id"] == "rec-1"


def test_websocket_timeout_falls_back_to_http_exactly_once() -> None:
    cfg = Config(ha_url="http://ha.local:8123", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1", websocket_fast_path_enabled=True, ha_websocket_token="ha-token")
    client = HAClient(cfg)
    sockets = [FakeWebSocket(_ws_capabilities(["djconnect/command"])), FakeWebSocket([])]

    with (
        patch("djconnect_pi.ha_websocket._websocket_create_connection", side_effect=sockets),
        patch("djconnect_pi.ha.requests.post", side_effect=_session_or_http_response({"success": True, "fallback": True})) as post,
    ):
        data = client.command("play")

    assert data["fallback"] is True
    assert [call.args[0] for call in post.call_args_list].count("http://ha.local:8123/api/djconnect/v1/command") == 1
    assert client.diagnostics()["websocketConnected"] is False
    assert client.diagnostics()["lastWebSocketError"] == "TimeoutError"


def test_websocket_auth_error_falls_back_to_http_without_clearing_pairing() -> None:
    cfg = Config(
        ha_url="http://ha.local:8123",
        device_id="djconnect-raspberry-pi-ABCDEF123456",
        device_token="token-1",
        paired=True,
        websocket_fast_path_enabled=True,
        ha_websocket_token="ha-token",
    )
    client = HAClient(cfg)
    sockets = [FakeWebSocket([{"type": "auth_required"}, {"type": "auth_invalid", "message": "bad"}])]

    with (
        patch("djconnect_pi.ha_websocket._websocket_create_connection", side_effect=sockets),
        patch("djconnect_pi.ha.requests.post", side_effect=_session_or_http_response({"success": True})) as post,
    ):
        data = client.command("play")

    assert data["success"] is True
    assert [call.args[0] for call in post.call_args_list].count("http://ha.local:8123/api/djconnect/v1/command") == 1
    assert cfg.paired is True
    assert cfg.device_token == "token-1"


def test_websocket_missing_server_support_flags_falls_back_to_http() -> None:
    cfg = Config(
        ha_url="http://ha.local:8123",
        device_id="djconnect-raspberry-pi-ABCDEF123456",
        device_token="token-1",
        websocket_fast_path_enabled=True,
        ha_websocket_token="ha-token",
    )
    client = HAClient(cfg)
    sockets = [
        FakeWebSocket(
            [
                {"type": "auth_required"},
                {"type": "auth_ok"},
                {"id": 1, "type": "result", "success": True, "result": {"success": True, "commands": ["play"]}},
            ]
        )
    ]

    with (
        patch("djconnect_pi.ha_websocket._websocket_create_connection", side_effect=sockets),
        patch("djconnect_pi.ha.requests.post", side_effect=_session_or_http_response({"success": True, "fallback": True})) as post,
    ):
        data = client.command("play")

    assert data["fallback"] is True
    assert [call.args[0] for call in post.call_args_list].count("http://ha.local:8123/api/djconnect/v1/command") == 1
    assert client.diagnostics()["fastPathTransport"] == "http"


def test_websocket_error_result_falls_back_to_http() -> None:
    cfg = Config(ha_url="http://ha.local:8123", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1", websocket_fast_path_enabled=True, ha_websocket_token="ha-token")
    client = HAClient(cfg)
    sockets = [
        FakeWebSocket(_ws_capabilities(["djconnect/command"])),
        FakeWebSocket(
            [
                {"type": "auth_required"},
                {"type": "auth_ok"},
                {"id": 2, "type": "result", "success": False, "error": {"code": "not_supported", "message": "Nope"}},
            ]
        ),
    ]

    with (
        patch("djconnect_pi.ha_websocket._websocket_create_connection", side_effect=sockets),
        patch("djconnect_pi.ha.requests.post", side_effect=_session_or_http_response({"success": True, "fallback": True})) as post,
    ):
        data = client.command("play")

    assert data["fallback"] is True
    assert [call.args[0] for call in post.call_args_list].count("http://ha.local:8123/api/djconnect/v1/command") == 1


def test_remote_or_non_http_url_stays_http() -> None:
    cfg = Config(ha_url="nabu://example", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1")
    client = HAClient(cfg)

    with (
        patch("djconnect_pi.ha_websocket._websocket_create_connection") as connect,
        patch("djconnect_pi.ha.requests.post", side_effect=_session_or_http_response({"success": True})) as post,
    ):
        data = client.command("play")

    assert data["success"] is True
    assert connect.call_count == 0
    assert post.call_count == 1


def test_https_home_assistant_url_tries_websocket_then_falls_back_to_http() -> None:
    cfg = Config(
        ha_url="https://example.ui.nabu.casa",
        device_id="djconnect-raspberry-pi-ABCDEF123456",
        device_token="token-1",
        websocket_fast_path_enabled=True,
        ha_websocket_token="ha-token",
    )
    client = HAClient(cfg)

    with (
        patch("djconnect_pi.ha_websocket._websocket_create_connection") as connect,
        patch("djconnect_pi.ha.requests.post", side_effect=_session_or_http_response({"success": True})) as post,
    ):
        data = client.command("play")

    assert data["success"] is True
    assert connect.call_count == 1
    assert [call.args[0] for call in post.call_args_list].count("https://example.ui.nabu.casa/api/djconnect/v1/command") == 1


def test_websocket_failure_logging_omits_tokens_and_raw_prompt(caplog) -> None:
    cfg = Config(
        ha_url="http://ha.local:8123",
        device_id="djconnect-raspberry-pi-ABCDEF123456",
        device_token="secret-token",
        websocket_fast_path_enabled=True,
        ha_websocket_token="ha-secret-token",
    )
    client = HAClient(cfg)
    caplog.set_level("DEBUG")
    sockets = [FakeWebSocket(_ws_capabilities(["djconnect/command"])), FakeWebSocket([])]

    with (
        patch("djconnect_pi.ha_websocket._websocket_create_connection", side_effect=sockets),
        patch("djconnect_pi.ha.requests.post", return_value=FakeResponse(200, {"success": True})),
    ):
        client.command("ask_dj_followup_response", value={"text": "raw private prompt"})

    assert "secret-token" not in caplog.text
    assert "ha-secret-token" not in caplog.text
    assert "raw private prompt" not in caplog.text
