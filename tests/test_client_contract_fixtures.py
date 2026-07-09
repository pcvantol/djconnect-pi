from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

from djconnect_pi.app import parse_ask_dj_messages, parse_music_discovery_feed, parse_music_dna_profile
from djconnect_pi.config import Config
from djconnect_pi.ha import HAClient
from djconnect_pi.ha_websocket import WebSocketFastPath

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "djconnect_contracts"


def _manifest() -> dict[str, Any]:
    return json.loads((FIXTURE_DIR / "manifest.json").read_text(encoding="utf-8"))


def _fixture(fixture_id: str) -> dict[str, Any]:
    manifest = _manifest()
    entry = next(item for item in manifest["fixtures"] if item["id"] == fixture_id)
    return json.loads((FIXTURE_DIR / entry["file"]).read_text(encoding="utf-8"))


def test_exported_client_contract_manifest_and_json_are_valid() -> None:
    manifest = _manifest()

    assert manifest["format"] == "djconnect.client_contract_fixtures"
    fixture_ids = {entry["id"] for entry in manifest["fixtures"]}
    assert {
        "capabilities.websocket",
        "music_dna.profile.disabled",
        "music_dna.profile.empty",
        "music_dna.profile.rich",
        "music_discovery.feed",
        "ask_dj.recently_played_history",
    }.issubset(fixture_ids)
    for entry in manifest["fixtures"]:
        payload = _fixture(entry["id"])
        assert isinstance(payload, dict)
        assert payload, entry["id"]


def test_capabilities_fixture_configures_websocket_routes_and_fallbacks() -> None:
    payload = _fixture("capabilities.websocket")
    cfg = Config(
        ha_url="http://ha.local:8123",
        device_id="djconnect-raspberry-pi-ABCDEF123456",
        device_token="token-1",
        websocket_fast_path_enabled=True,
    )
    fast_path = WebSocketFastPath(cfg)

    with patch.object(fast_path, "_ensure_session"), patch.object(fast_path, "_exchange", return_value=payload):
        fast_path.refresh_capabilities(timeout=1)

    assert fast_path.connected is True
    assert fast_path.commands == tuple(payload["commands"])
    assert {"djconnect/music_dna/profile", "djconnect/music_dna/settings", "djconnect/music_dna/clear", "djconnect/music_dna/import", "djconnect/music_dna/export"}.issubset(fast_path.commands)
    assert {"djconnect/music_discovery/feed", "djconnect/music_discovery/refresh", "djconnect/music_discovery/play", "djconnect/music_discovery/feedback"}.issubset(fast_path.commands)
    assert fast_path.features["music_dna"] is True
    assert fast_path.features["music_discovery"] is True
    assert fast_path.fallbacks["music_dna_http_paths_profile"] == "/api/djconnect/v1/music_dna/profile"
    assert fast_path.fallbacks["music_dna_http_paths_export"] == "/api/djconnect/v1/music_dna/export"
    assert fast_path.fallbacks["music_discovery_http_paths_feed"] == "/api/djconnect/v1/music_discovery"
    assert fast_path.fallbacks["music_discovery_feedback_http_path"] == "/api/djconnect/v1/music_discovery/feedback"
    assert "djconnect/vibecast" not in fast_path.commands


def test_music_dna_profile_fixtures_render_backend_privacy_dashboard_only() -> None:
    disabled = parse_music_dna_profile(_fixture("music_dna.profile.disabled"))
    empty = parse_music_dna_profile(_fixture("music_dna.profile.empty"))
    rich = parse_music_dna_profile(_fixture("music_dna.profile.rich"))

    assert disabled == {"enabled": False, "summary": "", "sections": []}
    assert empty["enabled"] is True
    assert empty["summary"] == "Music DNA staat aan, maar er is nog niet genoeg luistercontext."
    empty_privacy = next(section for section in empty["sections"] if section["title"] == "Privacy dashboard")
    assert any("Recent tracks" in line for line in empty_privacy["lines"])
    assert any("Stores Raw Audio: False" in line for line in empty_privacy["lines"])
    assert any("Stores Oauth Tokens: False" in line for line in empty_privacy["lines"])
    assert any("Stores Full Prompts: False" in line for line in empty_privacy["lines"])

    assert rich["enabled"] is True
    assert rich["summary"] == "Je Music DNA leunt naar indie, ambient en artiesten als The xx."
    privacy = next(section for section in rich["sections"] if section["title"] == "Privacy dashboard")
    lines = "\n".join(privacy["lines"])
    assert "Spotify recent/top profile snapshots" in lines
    assert "Recommendation feedback" in lines
    assert "Negative feedback" in lines
    assert "Clear Supported: True" in lines
    assert "Stores Raw Audio: False" in lines
    assert "Stores Oauth Tokens: False" in lines
    assert "Stores Full Prompts: False" in lines
    assert "secret" not in lines.lower()


def test_music_discovery_fixture_renders_backend_sections_items_and_actions() -> None:
    payload = _fixture("music_discovery.feed")
    parsed = parse_music_discovery_feed(payload)

    assert len(parsed["items"]) == sum(len(section["items"]) for section in payload["sections"])
    item = parsed["items"][0]
    raw = payload["sections"][0]["items"][0]
    assert item["id"] == raw["id"]
    assert item["kind"] == raw["kind"]
    assert item["title"] == raw["title"]
    assert item["subtitle"] == raw["subtitle"]
    assert item["imageUrl"] == raw["image_url"]
    assert item["reason"] == raw["reason"]
    assert item["reasonSources"] == raw["reason_sources"]
    assert item["qualityScore"] == raw["quality_score"]
    assert item["qualityBand"] == raw["quality_band"]
    assert item["qualityFactors"] == raw["quality_factors"]
    assert item["playable"] is True
    action_payload = json.loads(str(item["payload"]))
    assert action_payload == {"section_id": "new_for_you", "discovery_item_id": raw["id"]}
    assert "uri" not in action_payload
    assert "title" not in action_payload


def test_music_discovery_play_and_feedback_use_fixture_backend_ids_only() -> None:
    cfg = Config(ha_url="http://ha.local:8123", device_id="djconnect-raspberry-pi-ABCDEF123456", device_token="token-1", websocket_fast_path_enabled=False)
    client = HAClient(cfg)
    item = parse_music_discovery_feed(_fixture("music_discovery.feed"))["items"][0]
    payload = json.loads(str(item["payload"]))
    captured: list[dict[str, Any]] = []

    def fake_post(_url: str, **kwargs: Any) -> Any:
        captured.append(kwargs["json"])

        class Response:
            status_code = 200
            content = b"{}"

            @staticmethod
            def json() -> dict[str, Any]:
                return {"success": True}

        return Response()

    with patch("djconnect_pi.ha.requests.post", side_effect=fake_post):
        client.music_discovery_play(payload)
        client.music_discovery_feedback(payload, "not_for_me")

    assert captured[0]["section_id"] == "new_for_you"
    assert captured[0]["discovery_item_id"] == payload["discovery_item_id"]
    assert "uri" not in captured[0]
    assert "title" not in captured[0]
    assert captured[1]["feedback"] == "not_for_me"
    assert captured[1]["section_id"] == "new_for_you"
    assert captured[1]["discovery_item_id"] == payload["discovery_item_id"]


def test_ask_dj_recently_played_fixture_renders_informative_items_without_actions() -> None:
    payload = _fixture("ask_dj.recently_played_history")
    messages = parse_ask_dj_messages(payload)

    assert len(messages) == 1
    message = messages[0]
    assert message["text"] == payload["text"]
    assert message["actions"] == []
    assert message["images"] == []
    assert len(message["items"]) == len(payload["items"])
    item = message["items"][0]
    raw = payload["items"][0]
    assert item["title"] == raw["title"]
    assert item["subtitle"] == raw["subtitle"]
    assert item["kind"] == raw["kind"]
    assert item["imageUrl"] == raw["image_url"]
    assert item["time"] == raw["played_at"]
