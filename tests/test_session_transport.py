import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import requests

from djconnect_pi.session_transport import SessionError, SessionTransport


@pytest.fixture
def transport(monkeypatch):
    cfg = SimpleNamespace(paired=True, device_token="synthetic-token", ha_url="http://fixture.invalid",
        device_id="djconnect-raspberry-pi-fixture", explicit_profile_id="explicit-profile",
        active_profile_id="resolved-profile", active_profile_type="personal", active_profile_privacy_mode="private", private_session=False, language="nl")
    response = Mock(status_code=200, headers={})
    response.json.return_value = {"success": True, "session": None}
    def chunks(*, chunk_size):
        value = b"not JSON" if response.json.side_effect else json.dumps(response.json.return_value).encode()
        return iter(value[i:i + chunk_size] for i in range(0, len(value), chunk_size))
    response.iter_content.side_effect = chunks
    request = Mock(return_value=response)
    monkeypatch.setattr(requests, "request", request)
    class IsolatedSession:
        trust_env = True
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def request(self, *args, **kwargs):
            assert self.trust_env is False
            return request(*args, **kwargs)
    monkeypatch.setattr(requests, "Session", IsolatedSession)
    return SessionTransport(lambda: cfg), cfg, request, response


def test_read_is_pure_and_bound_to_device_and_explicit_profile(transport):
    client, cfg, request, _ = transport
    assert client.active(client.binding())["session"] is None
    args, kwargs = request.call_args
    assert args == ("GET", "http://fixture.invalid/api/djconnect/v1/session/active")
    assert kwargs["params"] == {"device_id": cfg.device_id, "client_type": "raspberry_pi", "profile_id": "explicit-profile"}
    assert kwargs["headers"]["Cache-Control"] == "no-store"
    assert "json" not in kwargs


def test_successor_profile_discards_delayed_response(transport):
    client, cfg, request, response = transport
    def delayed(*args, **kwargs):
        cfg.active_profile_id = "successor"
        return response
    request.side_effect = delayed
    with pytest.raises(SessionError, match="context_changed"):
        client.active(client.binding())


@pytest.mark.parametrize("method", ["start", "end"])
def test_write_timeout_is_uncertain_and_never_replayed(transport, method):
    client, _, request, _ = transport
    request.side_effect = requests.Timeout()
    with pytest.raises(SessionError, match="uncertain"):
        getattr(client, method)(client.binding(), "groove" if method == "start" else "exact-session")
    assert request.call_count == 1


def test_history_uses_negotiated_representation_and_safe_path_component(transport):
    client, _, request, _ = transport
    client.timeline(client.binding(), "session/foreign", window="anchor", anchor_entry_id="entry-1")
    assert request.call_args.args[1].endswith("session%2Fforeign")
    assert request.call_args.kwargs["params"]["history_contract_version"] == 2
    assert request.call_args.kwargs["params"]["anchor_entry_id"] == "entry-1"


def test_unauthorized_read_never_exposes_private_error_or_resets_pairing(transport):
    client, cfg, _, response = transport
    response.status_code = 403
    response.json.return_value = {"error": "private-server-body", "profile_id": "secret"}
    with pytest.raises(SessionError, match="^denied$"):
        client.active(client.binding())
    assert cfg.paired and cfg.device_token == "synthetic-token"


def test_no_request_with_old_binding_or_invalid_mood(transport):
    client, cfg, request, _ = transport
    binding = client.binding()
    cfg.device_token = "replacement"
    with pytest.raises(SessionError, match="context_changed"):
        client.active(binding)
    with pytest.raises(SessionError, match="invalid"):
        client.start(client.binding(), "continue")
    request.assert_not_called()


def test_question_is_single_profile_bound_text_only_request_with_exact_context(transport):
    client, cfg, request, _ = transport
    value = {'text': '  Tell me about this  ', 'client_message_id': 'pi-turn-fixture', 'session_id': 'active',
        'selected': {'kind': 'selected_entry', 'session_id': 'earlier', 'entry_id': 'entry-1'}}
    client.question(client.binding(), value)
    body = request.call_args.kwargs['json']
    assert body['client_type'] == 'raspberry_pi' and body['profile_id'] == cfg.explicit_profile_id
    assert body['text'] == 'Tell me about this' and body['audio_response'] == 'never'
    assert body['conversation_context'] == {'session_id': 'active', 'selected_entry': {'session_id': 'earlier', 'entry_id': 'entry-1'}}
    assert request.call_args.kwargs['timeout'] == (8, 120)
    request.assert_called_once()


def test_question_timeout_is_uncertain_with_no_write_replay(transport):
    client, _, request, _ = transport
    request.side_effect = requests.Timeout()
    with pytest.raises(SessionError, match='uncertain'):
        client.question(client.binding(), {'text': 'A question', 'client_message_id': 'new-turn', 'session_id': 'active'})
    request.assert_called_once()


def test_malformed_success_body_after_question_is_an_uncertain_mutation(transport):
    client, _, request, response = transport
    response.json.return_value = []
    with pytest.raises(SessionError, match='uncertain'):
        client.question(client.binding(), {'text':'Question','client_message_id':'turn','session_id':'active'})
    request.assert_called_once()


@pytest.mark.parametrize("command", ["play", "pause", "previous", "next", "save_current_track"])
def test_playback_command_is_one_paired_profile_http_attempt_without_invented_wire_fences(transport, command):
    client, cfg, request, _ = transport
    client.playback_command(client.binding(), command)
    request.assert_called_once()
    args, kwargs = request.call_args
    assert args == ("POST", "http://fixture.invalid/api/djconnect/v1/command")
    assert kwargs["allow_redirects"] is False
    assert kwargs["headers"]["Authorization"] == "Bearer synthetic-token"
    assert kwargs["json"] == {"device_id": cfg.device_id, "client_type": "raspberry_pi", "profile_id": cfg.explicit_profile_id,
        "command": command, "request_source": "device_command", "app_version": "4.0.0-rc.5"}


def test_playback_timeout_is_uncertain_and_never_replayed(transport):
    client, _, request, _ = transport
    request.side_effect = requests.Timeout()
    with pytest.raises(SessionError, match="uncertain"):
        client.playback_command(client.binding(), "next")
    request.assert_called_once()



def test_playback_owner_preflight_can_isolate_ambient_auth_without_changing_identity(transport):
    client, cfg, request, _ = transport
    client.active(client.binding(), isolated=True)
    request.assert_called_once()
    assert request.call_args.kwargs["params"]["profile_id"] == cfg.explicit_profile_id
    assert request.call_args.kwargs["headers"]["Authorization"] == "Bearer synthetic-token"



@pytest.mark.parametrize("url", ["http://synthetic-user:synthetic-password@fixture.invalid", "ftp://fixture.invalid", "http://fixture.invalid?synthetic=1", "http://fixture.invalid#fragment", "http://fixture.invalid:70000", "http://fixture.invalid\n"])
@pytest.mark.parametrize("route", ["owner", "status", "write"])
def test_playback_rejects_credential_or_noncanonical_base_before_dispatch(transport, url, route):
    client, cfg, request, _ = transport
    cfg.ha_url = url
    binding = client.binding()
    with pytest.raises(SessionError, match="^invalid$"):
        if route == "owner": client.active(binding, isolated=True)
        elif route == "status": client.playback_status(binding)
        else: client.playback_command(binding, "next")
    request.assert_not_called()
    assert cfg.paired and cfg.device_token == "synthetic-token"


def test_playback_preserves_valid_configured_reverse_proxy_base_path(transport):
    client, cfg, request, _ = transport
    cfg.ha_url = "https://fixture.invalid/ha"
    client.playback_status(client.binding())
    request.assert_called_once()
    assert request.call_args.args == ("POST", "https://fixture.invalid/ha/api/djconnect/v1/command")


@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize("isolated", [False, True])
@pytest.mark.parametrize("status", [401, 403])
@pytest.mark.parametrize("body", ["empty", "malformed", "non_object"])
def test_http_denial_precedes_any_body_decode_and_keeps_pairing(transport, method, isolated, status, body):
    client, cfg, request, response = transport
    response.status_code = status
    if body == "non_object": response.json.return_value = []
    else: response.json.side_effect = ValueError(body)
    with pytest.raises(SessionError, match="^denied$"):
        client._request(client.binding(), method, "session/active", isolated=isolated)
    response.json.assert_not_called()
    request.assert_called_once()
    assert cfg.paired and cfg.device_token == "synthetic-token"


@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize("status", [401, 403])
def test_superseded_binding_precedes_denial_without_decoding_old_body(transport, method, status):
    client, cfg, request, response = transport
    response.status_code = status
    def delayed(*args, **kwargs):
        cfg.active_profile_id = "successor-profile"
        return response
    request.side_effect = delayed
    with pytest.raises(SessionError, match="^context_changed$"):
        client._request(client.binding(), method, "session/active", isolated=True)
    response.json.assert_not_called()
    request.assert_called_once()
    assert cfg.paired and cfg.device_token == "synthetic-token"


@pytest.mark.parametrize("method,expected", [("GET", "unavailable"), ("POST", "uncertain")])
def test_server_failure_remains_unavailable_or_uncertain_without_replay(transport, method, expected):
    client, cfg, request, response = transport
    response.status_code = 503
    response.json.side_effect = ValueError("malformed failure")
    with pytest.raises(SessionError, match="^" + expected + "$"):
        client._request(client.binding(), method, "session/active", isolated=True)
    response.json.assert_not_called()
    request.assert_called_once()
    assert cfg.paired and cfg.device_token == "synthetic-token"


@pytest.mark.parametrize("code", ["device_not_mapped", "profile_required", "invalid_profile", "profile_access_denied"])
def test_profile_rejection_is_distinct_from_transport_outage_and_never_replayed(transport, code):
    client, cfg, request, response = transport
    response.status_code = 409
    response.json.return_value = {"success": False, "error": code, "message": "private server context"}
    with pytest.raises(SessionError, match="profile_unavailable"):
        client.active(client.binding())
    assert request.call_count == 1
    assert cfg.paired is True
    assert cfg.explicit_profile_id == "explicit-profile"
