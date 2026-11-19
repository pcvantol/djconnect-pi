"""Real Session controller and HTTP boundary, synthetic owner/output only."""
from copy import deepcopy
from unittest.mock import Mock

import pytest
import requests
from test_session_playback_control import ITEM_ID, setup

from djconnect_pi.session_playback_control import volume_observation
from djconnect_pi.session_transport import SessionError

pytest_plugins = ["test_session_controller", "test_session_transport"]
SID = "synthetic-session"


def setup_volume(controller, provider="spotify_direct", percent=30):
    owner, backend = setup(controller)
    backend.cfg.music_backend = provider
    backend.cfg.music_backend_capabilities["supports_volume"] = True
    status = owner.transport.playback_status.return_value
    status["music_backend"] = provider
    status["music_backend_capabilities"]["supports_volume"] = True
    status["playback"].update(volume_percent=percent, volume=percent,
        device={"id": "synthetic-output", "name": "<b>Literal output</b>",
                "active": True, "is_restricted": False, "supports_volume": True})
    if provider == "music_assistant":
        status["playback"]["device"] = {"id": "media_player.synthetic", "entity_id": "media_player.synthetic", "name": "Synthetic MA", "is_active": True}
    owner.transport.playback_volume = Mock(return_value={"success": True, "playback": {"volume_percent": 99}})
    return owner, backend, status


def read_ready(owner, backend):
    assert owner.readPlaybackVolume(SID, ITEM_ID)
    assert owner.busy
    backend.jobs.pop()()
    observation = owner.state["playback_control"]["volume"]
    assert observation and not owner.busy
    assert not backend.jobs  # No independent refresh is invented for an observation.
    return observation


@pytest.mark.parametrize("provider", ["spotify_direct", "music_assistant"])
@pytest.mark.parametrize("percent", [0, 1, 60, 85])
def test_explicit_read_preserves_actual_zero_or_above_limit_without_writing(controller, provider, percent):
    owner, backend, _ = setup_volume(controller, provider, percent)
    original = deepcopy(owner._session)
    owner._selection = {"synthetic": "unchanged"}
    observation = read_ready(owner, backend)
    assert observation["percent"] == percent
    assert observation["output_id"]
    assert owner._session == original and owner._selection == {"synthetic": "unchanged"}
    owner.transport.active.assert_called_once()
    owner.transport.playback_status.assert_called_once()
    owner.transport.playback_volume.assert_not_called()
    owner.transport.playback_command.assert_not_called()


@pytest.mark.parametrize("provider", ["spotify_direct", "music_assistant"])
@pytest.mark.parametrize("state", ["playing", "paused"])
@pytest.mark.parametrize("target", [0, 1, 60])
def test_one_explicit_intent_checks_fresh_target_and_never_imports_command_volume(controller, provider, state, target):
    owner, backend, status = setup_volume(controller, provider)
    owner._session["broadcast"]["playback"]["state"] = state
    status["playback"]["is_playing"] = state == "playing"
    if provider == "music_assistant":
        status["playback"]["device"]["is_active"] = state == "playing"
    observation = read_ready(owner, backend)
    original = deepcopy(owner._session)
    assert owner.setPlaybackVolume(SID, ITEM_ID, observation["lease"], target)
    assert not owner.state["playback_control"]["volume"]
    assert not owner.setPlaybackVolume(SID, ITEM_ID, observation["lease"], target)
    backend.jobs.pop()()
    owner.transport.playback_volume.assert_called_once_with(owner.transport.binding(), target, provider)
    assert owner._session == original and not owner.state["playback_control"]["volume"]
    assert owner.state["playback_control"]["status"] == "accepted"
    assert owner._running_action == "refresh" and len(backend.jobs) == 1


@pytest.mark.parametrize("provider", ["spotify_direct", "music_assistant"])
@pytest.mark.parametrize("reason", ["missing", "none", "bool", "string", "float", "conflict", "no_target", "capability"])
def test_unsupported_or_missing_observation_never_gets_a_default(controller, provider, reason):
    owner, backend, status = setup_volume(controller, provider)
    playback = status["playback"]
    if reason in {"missing", "none"}:
        playback.pop("volume_percent");playback.pop("volume")
        if reason == "none": playback["volume_percent"] = None
    elif reason in {"bool", "string", "float"}:
        playback["volume_percent"] = {"bool": True, "string": "30", "float": 30.0}[reason]
    elif reason == "conflict": playback["volume"] = 31
    elif reason == "no_target": playback["device"]["id"] = ""
    else: status["music_backend_capabilities"]["supports_volume"] = False
    assert owner.readPlaybackVolume(SID, ITEM_ID)
    backend.jobs.pop()()
    assert not owner.state["playback_control"]["volume"]
    assert owner.state["playback_control"]["volume_status"] == "unavailable"
    assert owner.state["playback_control"]["enabled"]  # A failed read is not a write-uncertainty latch.
    owner.transport.playback_volume.assert_not_called()


@pytest.mark.parametrize("field,value", [("active", False), ("supports_volume", False), ("supports_volume", "true"), ("is_restricted", True), ("is_restricted", None)])
def test_spotify_current_output_requires_strict_writable_device_fields(controller, field, value):
    owner, backend, status = setup_volume(controller)
    status["playback"]["device"][field] = value
    assert owner.readPlaybackVolume(SID, ITEM_ID)
    backend.jobs.pop()()
    assert not owner.state["playback_control"]["volume"]
    owner.transport.playback_volume.assert_not_called()


@pytest.mark.parametrize("reason", ["output", "observed_volume", "backend_revision", "backend", "capability", "restricted", "uri", "state"])
def test_fresh_status_change_rejects_queued_volume_without_any_effect(controller, reason):
    owner, backend, status = setup_volume(controller)
    observation = read_ready(owner, backend)
    assert owner.setPlaybackVolume(SID, ITEM_ID, observation["lease"], 40)
    if reason == "output": status["playback"]["device"]["id"] = "other-output"
    elif reason == "observed_volume": status["playback"].update(volume=31, volume_percent=31)
    elif reason == "backend_revision": status["music_backend_revision"] += 1
    elif reason == "backend": status["music_backend"] = "music_assistant"
    elif reason == "capability": status["music_backend_capabilities"]["supports_volume"] = False
    elif reason == "restricted": status["playback"]["device"]["is_restricted"] = True
    elif reason == "uri": status["playback"]["uri"] = "other-track"
    else: status["playback"]["is_playing"] = False
    backend.jobs.pop()()
    owner.transport.playback_volume.assert_not_called()
    assert owner.state["playback_control"]["status"] == "uncertain"
    assert not backend.jobs


@pytest.mark.parametrize("reason", ["hide", "close", "foreground", "profile", "item", "backend", "capability", "end"])
def test_local_withdrawal_cancels_queued_volume_before_owner_or_status_read(controller, reason):
    owner, backend, _ = setup_volume(controller)
    observation = read_ready(owner, backend)
    owner.transport.active.reset_mock();owner.transport.playback_status.reset_mock()
    assert owner.setPlaybackVolume(SID, ITEM_ID, observation["lease"], 40)
    work = backend.jobs.pop()
    if reason == "hide": owner.setPlaybackControlsVisible(False)
    elif reason == "close": owner.cancelPlaybackIntent()
    elif reason == "foreground": owner.setForeground(False)
    elif reason == "profile": backend.cfg.active_profile_id = "other"
    elif reason == "item": owner._session["broadcast"]["playback"]["item_id"] = "other"
    elif reason == "backend": backend.cfg.music_backend_revision += 1
    elif reason == "capability": backend.cfg.music_backend_capabilities["supports_volume"] = False
    else: owner.end(SID)
    work()
    owner.transport.active.assert_not_called()
    owner.transport.playback_status.assert_not_called()
    owner.transport.playback_volume.assert_not_called()
    assert not owner.state["playback_control"]["volume"]


@pytest.mark.parametrize("target", [True, -1, 61, 100, 1.0, None, "1"])
def test_untyped_or_out_of_range_release_does_not_queue(controller, target):
    owner, backend, _ = setup_volume(controller)
    observation = read_ready(owner, backend)
    assert not owner.setPlaybackVolume(SID, ITEM_ID, observation["lease"], target)
    assert not backend.jobs
    owner.transport.playback_volume.assert_not_called()


def test_lease_close_reopen_and_new_observation_cannot_authorize_old_drag(controller):
    owner, backend, _ = setup_volume(controller)
    old = read_ready(owner, backend)
    owner.cancelPlaybackIntent()
    assert not owner.setPlaybackVolume(SID, ITEM_ID, old["lease"], 40)
    current = read_ready(owner, backend)
    assert current["lease"] != old["lease"]
    assert not owner.setPlaybackVolume(SID, ITEM_ID, old["lease"], 40)
    assert not backend.jobs


@pytest.mark.parametrize("error", ["uncertain", "offline", "unavailable"])
def test_unconfirmed_volume_is_never_replayed_or_displayed_optimistically(controller, error):
    owner, backend, _ = setup_volume(controller)
    observation = read_ready(owner, backend)
    owner.transport.playback_volume.side_effect = SessionError(error)
    assert owner.setPlaybackVolume(SID, ITEM_ID, observation["lease"], 40)
    backend.jobs.pop()()
    assert not owner.state["playback_control"]["volume"]
    owner.changed.emit();owner._expire()
    assert not owner.readPlaybackVolume(SID, ITEM_ID)
    assert not owner.setPlaybackVolume(SID, ITEM_ID, observation["lease"], 40)
    owner.transport.playback_volume.assert_called_once()
    assert not backend.jobs


@pytest.mark.parametrize("boundary", ["read", "write"])
def test_denial_withdraws_session_volume_but_preserves_pairing(controller, boundary):
    owner, backend, _ = setup_volume(controller)
    if boundary == "read":
        owner.transport.playback_status.side_effect = SessionError("denied")
        assert owner.readPlaybackVolume(SID, ITEM_ID)
    else:
        observation = read_ready(owner, backend)
        owner.transport.playback_volume.side_effect = SessionError("denied")
        assert owner.setPlaybackVolume(SID, ITEM_ID, observation["lease"], 40)
    backend.jobs.pop()()
    assert not owner.state["session_id"] and owner.state["error"] == "denied"
    assert backend.cfg.paired and not owner.state["playback_control"]["volume"]


@pytest.mark.parametrize("provider", ["spotify_direct", "music_assistant"])
@pytest.mark.parametrize("target", [0, 1, 2, 59, 60])
def test_actual_http_volume_payload_uses_pinned_backend_units_once(transport, provider, target):
    client, _, request, _ = transport
    client.playback_volume(client.binding(), target, provider)
    assert request.call_count == 1
    args, kwargs = request.call_args
    assert args[0] == "POST" and args[1].endswith("/api/djconnect/v1/command")
    assert kwargs["json"]["command"] == "set_volume"
    assert kwargs["json"]["client_type"] == "raspberry_pi"
    wire = kwargs["json"]["value"]
    assert wire == (target / 100 if provider == "music_assistant" else target)
    assert type(wire) is (float if provider == "music_assistant" else int)
    assert not ({"expected_session", "session_id", "item_id", "output_id", "backend"} & set(kwargs["json"]))
    assert kwargs["allow_redirects"] is False and kwargs["stream"] is True


@pytest.mark.parametrize("value", [True, -1, 61, 1.0, None, "1"])
def test_transport_rejects_untyped_volume_without_http(transport, value):
    client, _, request, _ = transport
    with pytest.raises(SessionError, match="invalid"):
        client.playback_volume(client.binding(), value, "music_assistant")
    request.assert_not_called()


@pytest.mark.parametrize("provider", [None, True, [], "", "later_manual"])
def test_transport_rejects_unknown_backend_without_http(transport, provider):
    client, _, request, _ = transport
    with pytest.raises(SessionError, match="invalid"):
        client.playback_volume(client.binding(), 1, provider)
    request.assert_not_called()


def test_actual_volume_http_timeout_has_no_fallback_or_retry(transport):
    client, _, request, _ = transport
    request.side_effect = requests.Timeout()
    with pytest.raises(SessionError, match="uncertain"):
        client.playback_volume(client.binding(), 1, "music_assistant")
    assert request.call_count == 1


def test_raw_aliases_and_ma_identity_must_not_contradict(controller):
    _, _, status = setup_volume(controller, "music_assistant", 0)
    assert volume_observation(status, "music_assistant")["percent"] == 0
    status["playback"]["device"]["entity_id"] = "media_player.other"
    with pytest.raises(SessionError): volume_observation(status, "music_assistant")


@pytest.mark.parametrize("boundary", ["read", "write"])
@pytest.mark.parametrize("reason", ["hide", "foreground", "profile", "item", "end"])
def test_started_volume_result_after_withdrawal_cannot_publish_or_refresh(controller, boundary, reason):
    owner, backend, _ = setup_volume(controller)
    if boundary == "write":
        lease = read_ready(owner, backend)["lease"]
        assert owner.setPlaybackVolume("synthetic-session", ITEM_ID, lease, 1)
    else:
        assert owner.readPlaybackVolume("synthetic-session", ITEM_ID)
    work = backend.jobs.pop()
    def late(*args):
        if reason == "hide": owner.setPlaybackControlsVisible(False)
        elif reason == "foreground": owner.setForeground(False)
        elif reason == "profile": backend.cfg.active_profile_id = "other"
        elif reason == "item": owner._session["broadcast"]["playback"]["item_id"] = "other"
        else: owner.end("synthetic-session")
        return {"success": True} if boundary == "write" else owner.transport.playback_status.return_value
    target = owner.transport.playback_volume if boundary == "write" else owner.transport.playback_status
    target.side_effect = late
    owner.transport.active.reset_mock()
    work()
    assert not owner.state["playback_control"]["volume"]
    assert owner.state["playback_control"]["status"] == ""
    owner.transport.active.assert_called_once()
    if reason != "end": assert not backend.jobs


@pytest.mark.parametrize("boundary", ["read", "write"])
def test_real_held_volume_worker_keeps_end_available(boundary):
    import os
    import subprocess
    import sys
    from pathlib import Path

    script = """
from threading import Event
from copy import deepcopy
from unittest.mock import Mock
from PySide6.QtCore import QCoreApplication
from djconnect_pi.session_controller import SessionController
from test_session_controller import Backend
from test_session_volume_control import setup_volume, read_ready, ITEM_ID
app=QCoreApplication([]);backend=Backend();owner=SessionController(backend);owner._deadline_timer.stop()
setup_volume((owner,backend))
boundary=BOUNDARY
if boundary=='write': lease=read_ready(owner,backend)['lease']
owner._playback_control.executor=None
entered=Event();release=Event()
owner.transport.end=Mock(return_value={'success':True})
owner.transport.active=Mock(side_effect=lambda *a,**k:{'success':True,'session':None if owner._running_action=='end' else deepcopy(owner._session)})
owner.transport.capabilities=Mock(return_value={})
def held(*args):
    entered.set();assert release.wait(3)
    return {'success':True} if boundary=='write' else owner.transport.playback_status.return_value
if boundary=='write': owner.transport.playback_volume.side_effect=held
else: owner.transport.playback_status.side_effect=held
assert (owner.setPlaybackVolume('synthetic-session',ITEM_ID,lease,1) if boundary=='write' else owner.readPlaybackVolume('synthetic-session',ITEM_ID))
assert entered.wait(2)
owner.end('synthetic-session');assert len(backend.jobs)==1
backend.jobs.pop()();owner.transport.end.assert_called_once()
assert not owner.state['session_id'] and not release.is_set()
release.set();owner._playback_control.executor.shutdown(wait=True);app.processEvents()
assert not owner.state['playback_control']['volume'] and not owner.state['session_id']
assert owner.transport.active.call_count==2
owner.shutdownImages()
""".replace("BOUNDARY", repr(boundary))
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, "PYTHONPATH": str(root/"src")+os.pathsep+str(root/"tests")}
    result = subprocess.run([sys.executable, "-c", script], cwd=root, env=env,
                            capture_output=True, text=True, timeout=12, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
