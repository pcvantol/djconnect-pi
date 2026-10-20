from __future__ import annotations

import gzip
import io
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import requests
from urllib3.response import HTTPResponse

from djconnect_pi import session_transport as wire
from djconnect_pi.session_transport import SessionError, SessionTransport


@pytest.fixture
def setup(monkeypatch):
    cfg = SimpleNamespace(paired=True, device_token="synthetic-token", ha_url="http://fixture.invalid",
        device_id="djconnect-raspberry-pi-fixture", explicit_profile_id="explicit-profile",
        active_profile_id="resolved-profile", active_profile_type="personal", active_profile_privacy_mode="private",
        private_session=False, language="nl")
    response = Mock(status_code=200, headers={})
    request = Mock(return_value=response)
    monkeypatch.setattr(requests, "request", request)
    class Isolated:
        trust_env = True
        def __enter__(self): return self
        def __exit__(self, *args): response.close.assert_called_once()
        def request(self, *args, **kwargs):
            assert self.trust_env is False
            return request(*args, **kwargs)
    monkeypatch.setattr(requests, "Session", Isolated)
    return SessionTransport(lambda: cfg), cfg, request, response


def encoded(size: int) -> bytes:
    base = b'{"success":true,"padding":""}'
    return base[:-2] + b"x" * (size - len(base)) + base[-2:]


def stream(response, raw: bytes):
    response.iter_content.side_effect = lambda *, chunk_size: (
        raw[i:i + chunk_size] for i in range(0, len(raw), chunk_size))


@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize("isolated", [False, True])
@pytest.mark.parametrize("declared", [False, True])
def test_exact_control_boundary_is_valid_and_fresh(setup, method, isolated, declared):
    client, _cfg, request, response = setup
    raw = encoded(wire.JSON_CONTROL_BYTES)
    stream(response, raw)
    if declared: response.headers = {"Content-Length": str(len(raw))}
    value = client._request(client.binding(), method, "command", isolated=isolated)
    assert value["success"] is True and len(value["padding"]) > 2_000_000
    assert request.call_args.kwargs["stream"] is True
    response.json.assert_not_called()
    response.close.assert_called_once()
    value["success"] = False
    assert client._request(client.binding(), method, "command", isolated=False)["success"] is True


@pytest.mark.parametrize("method,category", [("GET", "invalid"), ("POST", "uncertain")])
@pytest.mark.parametrize("isolated", [False, True])
@pytest.mark.parametrize("declared", [False, True])
def test_oversize_never_reaches_json_or_replays(setup, monkeypatch, method, category, isolated, declared):
    client, cfg, request, response = setup
    raw = encoded(wire.JSON_CONTROL_BYTES + 1)
    stream(response, raw)
    if declared: response.headers = {"Content-Length": str(len(raw))}
    decode = Mock(side_effect=AssertionError("JSON must not parse oversize"))
    monkeypatch.setattr(wire.json, "loads", decode)
    with pytest.raises(SessionError, match="^"+category+"$"):
        client._request(client.binding(), method, "command", isolated=isolated)
    request.assert_called_once();decode.assert_not_called();response.close.assert_called_once()
    if declared: response.iter_content.assert_not_called()
    assert cfg.paired and cfg.device_token == "synthetic-token"


@pytest.mark.parametrize("declared", ["-1", "unknown", "1, 2", "2.0", "１２", "9" * 21])
def test_bad_length_fails_closed_without_reading(setup, declared):
    client, _, request, response = setup
    response.headers = {"Content-Length": declared}
    with pytest.raises(SessionError, match="^invalid$"):client.active(client.binding())
    response.iter_content.assert_not_called();response.close.assert_called_once();request.assert_called_once()


@pytest.mark.parametrize("status,category", [(401, "denied"), (403, "denied"), (302, "unavailable"), (503, "unavailable")])
def test_terminal_headers_precede_any_body_or_length(setup, status, category):
    client, _, _, response = setup
    response.status_code = status;response.headers = {"Content-Length": "invalid"}
    with pytest.raises(SessionError, match="^"+category+"$"):client.active(client.binding())
    response.iter_content.assert_not_called();response.json.assert_not_called();response.close.assert_called_once()


@pytest.mark.parametrize("method", ["GET", "POST"])
def test_binding_change_midstream_cancels_before_decode(setup, monkeypatch, method):
    client, cfg, request, response = setup
    def chunks(**_):
        yield b'{"success":'
        cfg.active_profile_id = "successor"
        yield b'true}'
    response.iter_content.side_effect = chunks
    decode = Mock(side_effect=AssertionError("No old-context decode"));monkeypatch.setattr(wire.json, "loads", decode)
    with pytest.raises(SessionError, match="^context_changed$"):
        client._request(client.binding(), method, "session/active", isolated=True)
    decode.assert_not_called();response.close.assert_called_once();request.assert_called_once()


@pytest.mark.parametrize("method,category", [("GET", "offline"), ("POST", "uncertain")])
def test_midstream_timeout_is_not_replayed(setup, method, category):
    client, _, request, response = setup
    def chunks(**_):
        yield b'{"success":'
        raise requests.Timeout()
    response.iter_content.side_effect = chunks
    with pytest.raises(SessionError, match="^"+category+"$"):
        client._request(client.binding(), method, "command", isolated=True)
    request.assert_called_once();response.close.assert_called_once()


def test_compressed_length_does_not_authorize_expanded_bytes(setup, monkeypatch):
    client, _, request, _ = setup
    compressed = gzip.compress(encoded(wire.JSON_CONTROL_BYTES+1))
    response = requests.Response();response.status_code = 200
    response.headers = {"Content-Length": str(len(compressed)), "Content-Encoding": "gzip"}
    response.raw = HTTPResponse(body=io.BytesIO(compressed), headers=response.headers, preload_content=False)
    request.return_value = response
    with pytest.raises(SessionError, match="^uncertain$"):
        client._request(client.binding(), "POST", "command")
    request.assert_called_once()
    assert response.raw.closed


def test_maximum_history_body_shape_with_escaped_unicode_is_not_clipped(setup):
    client, _, _, response = setup
    text = "\U0001f3b5" * 32768
    body = {"success": True, "entries": [{"text": text} for _ in range(50)]}
    raw = json.dumps(body, ensure_ascii=True).encode()
    assert 50 * 32768 * 12 <= len(raw) < wire.JSON_HISTORY_BYTES
    stream(response, raw)
    value = client._request(client.binding(), "GET", "session/history/synthetic")
    assert len(value["entries"]) == 50 and all(row["text"] == text for row in value["entries"])
    response.close.assert_called_once()


@pytest.mark.parametrize("route,expected", [("capabilities", wire.JSON_CONTROL_BYTES), ("command", wire.JSON_CONTROL_BYTES),
    ("session/active", wire.JSON_SESSION_BYTES), ("ask_dj/message", wire.JSON_SESSION_BYTES),
    ("session/history", wire.JSON_HISTORY_BYTES), ("session/history/sid/search", wire.JSON_HISTORY_BYTES),
    ("session/history/open", wire.JSON_CONTROL_BYTES)])
def test_closed_consumer_route_budget(route, expected):
    assert wire.response_budget(route) == expected


@pytest.mark.parametrize("raw", [b'{"success":true,"nested":'+b'['*65+b'0'+b']'*65+b'}',
    b'{"success":true,"items":['+b'0,'*100_001+b'0]}'])
def test_structural_bombs_are_rejected_before_decode(setup, monkeypatch, raw):
    client, _, request, response = setup
    stream(response, raw)
    decode = Mock(side_effect=AssertionError("Structural limit must precede decode"));monkeypatch.setattr(wire.json, "loads", decode)
    with pytest.raises(SessionError, match="^uncertain$"):
        client._request(client.binding(), "POST", "command")
    request.assert_called_once();decode.assert_not_called();response.close.assert_called_once()


def test_quoted_and_escaped_punctuation_does_not_consume_structure_budget(setup):
    client, _, _, response = setup
    value = '\"{}[],:\\'*20_000
    stream(response, json.dumps({"success": True, "text": value}).encode())
    assert client.active(client.binding())["text"] == value
