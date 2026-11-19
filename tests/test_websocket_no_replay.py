"""Exercise the actual socket send boundary, with no network or producer execution."""
import json
import time
from unittest.mock import Mock

import pytest

from djconnect_pi.config import Config
from djconnect_pi.ha import DJConnectError, HAClient
from djconnect_pi.ha_websocket import WebSocketFastPath, WebSocketWriteUnconfirmed
from djconnect_pi.i18n import translate


class Socket:
    def __init__(self, outcome):
        self.frames = [{"type": "auth_required"}, {"type": "auth_ok"}]
        self.outcome = outcome
        self.sent = []
        self.closed = False

    def send(self, raw):
        payload = json.loads(raw)
        self.sent.append(payload)
        if payload["type"] != "auth" and self.outcome == "partial_send":
            raise OSError("synthetic partial send")

    def recv(self):
        if self.frames:
            return json.dumps(self.frames.pop(0))
        if self.outcome == "timeout":
            raise TimeoutError("synthetic lost acknowledgement")
        if self.outcome == "decode":
            return "{"
        if self.outcome == "reject":
            return json.dumps({"type": "result", "success": False, "error": {"code": "forbidden"}})
        if self.outcome == "empty":
            return json.dumps({"type": "result", "success": True, "result": None})
        return json.dumps({"type": "result", "success": True, "result": {"success": True}})

    def close(self):
        self.closed = True


def configured(monkeypatch, outcome, route="djconnect/command"):
    cfg = Config(ha_url="http://fixture.invalid", device_id="djconnect-raspberry-pi-fixture",
                 device_token="synthetic-token", paired=True, explicit_profile_id="synthetic-profile")
    fast = WebSocketFastPath(cfg)
    fast.commands = (route,)
    fast.last_capability_refresh = time.monotonic()
    fast._access_token = "synthetic-session-token"
    fast._access_token_expires_at = time.time() + 600
    socket = Socket(outcome)
    monkeypatch.setattr("djconnect_pi.ha_websocket._websocket_create_connection", lambda *a, **k: socket)
    return fast, socket


@pytest.mark.parametrize("command", ["play", "pause", "next", "previous", "set_volume", "volume_delta", "save_current_track", "set_output", "set_shuffle", "set_repeat"])
@pytest.mark.parametrize("outcome", ["timeout", "partial_send", "decode", "reject", "empty"])
def test_dispatched_write_cannot_return_fallback_sentinel(monkeypatch, command, outcome):
    fast, socket = configured(monkeypatch, outcome)
    with pytest.raises(WebSocketWriteUnconfirmed):
        fast.try_request("djconnect/command", {"command": command, "value": 25}, command="djconnect/command", timeout=1)
    assert [p["command"] for p in socket.sent if "command" in p] == [command]
    assert socket.closed
    assert fast.last_error == "WebSocketWriteUnconfirmed"
    assert fast.cfg.paired and fast.cfg.device_token == "synthetic-token"


@pytest.mark.parametrize("route", ["djconnect/ask_dj/message", "djconnect/ask_dj/history/clear", "djconnect/music_dna/settings", "djconnect/music_discovery/play", "djconnect/music_discovery/feedback", "djconnect/unknown_future_write"])
def test_non_read_route_is_conservatively_non_replayable(monkeypatch, route):
    fast, socket = configured(monkeypatch, "timeout", route)
    with pytest.raises(WebSocketWriteUnconfirmed):
        fast.try_request(route, {}, command=route, timeout=1)
    assert [p["type"] for p in socket.sent] == ["auth", route]


@pytest.mark.parametrize("command", ["status", "devices", "queue", "playlists"])
def test_read_timeout_preserves_fallback(monkeypatch, command):
    fast, socket = configured(monkeypatch, "timeout")
    assert fast.try_request("djconnect/command", {"command": command}, command="djconnect/command", timeout=1) is None
    assert socket.closed


@pytest.mark.parametrize("language", ["en", "nl", "de", "fr", "es"])
def test_actual_client_does_not_http_replay_and_localizes_status(monkeypatch, language):
    fast, socket = configured(monkeypatch, "timeout")
    fast.cfg.language = language
    client = HAClient(fast.cfg)
    client.fast_path = fast
    post = Mock(side_effect=AssertionError("HTTP replay"))
    monkeypatch.setattr("djconnect_pi.ha.requests.post", post)
    with pytest.raises(DJConnectError) as error:
        client.command("next")
    assert str(error.value) == translate(language, "session_uncertain")
    post.assert_not_called()
    assert len(socket.sent) == 2


def test_before_dispatch_failure_allows_http_fallback(monkeypatch):
    fast, socket = configured(monkeypatch, "timeout")
    socket.frames = [{"type": "auth_required"}, {"type": "auth_invalid"}]
    assert fast.try_request("djconnect/command", {"command": "next"}, command="djconnect/command", timeout=1) is None
    assert [p["type"] for p in socket.sent] == ["auth"]


def test_confirmed_write_keeps_fast_path(monkeypatch):
    fast, socket = configured(monkeypatch, "success")
    assert fast.try_request("djconnect/command", {"command": "next"}, command="djconnect/command", timeout=1) == {"success": True}
    assert fast.transport == "websocket" and socket.closed


@pytest.mark.parametrize("command", [None, ["next"], {"command": "next"}])
def test_malformed_command_is_not_a_replay_safe_read(monkeypatch, command):
    fast, _ = configured(monkeypatch, "timeout")
    with pytest.raises(WebSocketWriteUnconfirmed):
        fast.try_request("djconnect/command", {"command": command}, command="djconnect/command", timeout=1)
