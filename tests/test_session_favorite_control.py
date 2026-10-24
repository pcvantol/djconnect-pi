"""Typed favorite observations and one explicit boolean intent; no provider effects."""
from copy import deepcopy
from unittest.mock import Mock

import pytest
import requests
from test_session_playback_control import ITEM_ID, setup

from djconnect_pi.session_transport import SessionError

pytest_plugins = ["test_session_controller", "test_session_transport"]
SID = "synthetic-session"


def setup_favorite(controller, liked=False):
    owner, backend = setup(controller)
    status = owner.transport.playback_status.return_value
    status["playback"].update(favorite_status=liked, is_liked=liked)
    owner.transport.playback_favorite = Mock(return_value={"success": True, "playback": {"favorite_status": not liked}})
    return owner, backend, status


def read_ready(owner, backend):
    assert owner.readPlaybackFavorite(SID, ITEM_ID)
    backend.jobs.pop()()
    state = owner.state["playback_control"]["favorite_observation"]
    assert state and not backend.jobs
    return state


@pytest.mark.parametrize("liked", [True, False])
def test_explicit_read_preserves_unknown_until_strict_boolean_without_writes(controller, liked):
    owner, backend, _ = setup_favorite(controller, liked)
    original = deepcopy(owner._session)
    assert not owner.state["playback_control"]["favorite_observation"]
    state = read_ready(owner, backend)
    assert state["liked"] is liked
    assert owner._session == original
    owner.transport.active.assert_called_once()
    owner.transport.playback_status.assert_called_once()
    owner.transport.playback_command.assert_not_called()
    owner.transport.playback_favorite.assert_not_called()


@pytest.mark.parametrize("liked", [True, False])
@pytest.mark.parametrize("state", ["playing", "paused"])
def test_one_explicit_opposite_boolean_has_fresh_preflight_and_no_optimism(controller, liked, state):
    owner, backend, status = setup_favorite(controller, liked)
    owner._session["broadcast"]["playback"]["state"] = state
    status["playback"]["is_playing"] = state == "playing"
    observation = read_ready(owner, backend)
    original = deepcopy(owner._session)
    assert owner.setPlaybackFavorite(SID, ITEM_ID, observation["lease"], not liked)
    assert not owner.state["playback_control"]["favorite_observation"]
    assert not owner.setPlaybackFavorite(SID, ITEM_ID, observation["lease"], not liked)
    backend.jobs.pop()()
    owner.transport.playback_favorite.assert_called_once_with(owner.transport.binding(), not liked)
    assert owner._session == original
    assert not owner.state["playback_control"]["favorite_observation"]
    assert owner._running_action == "refresh" and len(backend.jobs) == 1
    owner.transport.active.assert_called()
    assert owner.transport.active.call_count == 2 and owner.transport.playback_status.call_count == 2


@pytest.mark.parametrize("value", [None, 0, 1, "true", "false", [], {}])
def test_missing_or_untyped_status_is_not_unliked(controller, value):
    owner, backend, status = setup_favorite(controller)
    status["playback"]["favorite_status"] = value
    assert owner.readPlaybackFavorite(SID, ITEM_ID)
    backend.jobs.pop()()
    assert not owner.state["playback_control"]["favorite_observation"]
    assert owner.state["playback_control"]["favorite_status"] == "unavailable"
    assert owner.state["session_id"] and not backend.jobs
    owner.transport.playback_favorite.assert_not_called()


@pytest.mark.parametrize("reason", ["missing", "contradictory", "alias_type", "capability", "backend"])
def test_unsupported_or_inconsistent_observation_does_not_authorize_removal(controller, reason):
    owner, backend, status = setup_favorite(controller, True)
    if reason == "missing": status["playback"].pop("favorite_status")
    elif reason == "contradictory": status["playback"]["is_liked"] = False
    elif reason == "alias_type": status["playback"]["is_liked"] = 1
    elif reason == "capability": status["music_backend_capabilities"]["supports_favorites"] = "true"
    else: backend.cfg.music_backend = "music_assistant"
    queued = owner.readPlaybackFavorite(SID, ITEM_ID)
    if queued: backend.jobs.pop()()
    else: assert not backend.jobs
    assert not owner.state["playback_control"]["favorite_observation"]
    owner.transport.playback_favorite.assert_not_called()


@pytest.mark.parametrize("reason", ["liked", "capability", "uri", "state", "backend", "revision"])
def test_fresh_status_change_prevents_effect(controller, reason):
    owner, backend, status = setup_favorite(controller, True)
    observation = read_ready(owner, backend)
    assert owner.setPlaybackFavorite(SID, ITEM_ID, observation["lease"], False)
    if reason == "liked": status["playback"].update(favorite_status=False, is_liked=False)
    elif reason == "capability": status["music_backend_capabilities"]["supports_favorites"] = False
    elif reason == "uri": status["playback"]["uri"] = "spotify:track:other"
    elif reason == "state": status["playback"]["is_playing"] = False
    elif reason == "backend": status["music_backend"] = "music_assistant"
    else: status["music_backend_revision"] += 1
    backend.jobs.pop()()
    owner.transport.playback_favorite.assert_not_called()
    assert not backend.jobs and owner.state["playback_control"]["status"] == "uncertain"


@pytest.mark.parametrize("reason", ["close", "foreground", "profile", "item", "backend", "revision", "capability", "end"])
def test_local_withdrawal_revokes_observation_and_queued_intent(controller, reason):
    owner, backend, _ = setup_favorite(controller, True)
    observation = read_ready(owner, backend)
    assert owner.setPlaybackFavorite(SID, ITEM_ID, observation["lease"], False)
    work = backend.jobs.pop()
    owner.transport.active.reset_mock()
    if reason == "close": owner.cancelPlaybackIntent()
    elif reason == "foreground": owner.setForeground(False)
    elif reason == "profile": backend.cfg.active_profile_id = "other"
    elif reason == "item": owner._session["broadcast"]["playback"]["item_id"] = "other"
    elif reason == "backend": backend.cfg.music_backend = "music_assistant"
    elif reason == "revision": backend.cfg.music_backend_revision += 1
    elif reason == "capability": backend.cfg.music_backend_capabilities["supports_favorites"] = False
    else: owner.end(SID)
    work()
    owner.transport.active.assert_not_called()
    owner.transport.playback_favorite.assert_not_called()
    assert not owner.state["playback_control"]["favorite_observation"]


@pytest.mark.parametrize("value", [None, 0, 1, "false", "toggle", [], {}])
def test_write_accepts_only_explicit_boolean_opposite_and_current_lease(controller, value):
    owner, backend, _ = setup_favorite(controller, True)
    observation = read_ready(owner, backend)
    assert not owner.setPlaybackFavorite(SID, ITEM_ID, observation["lease"], value)
    assert not owner.setPlaybackFavorite(SID, ITEM_ID, observation["lease"], True)
    assert not owner.setPlaybackFavorite(SID, ITEM_ID, observation["lease"]+1, False)
    assert not backend.jobs


def test_old_lease_cannot_survive_close_reopen_even_with_same_status(controller):
    owner, backend, _ = setup_favorite(controller, True)
    old = read_ready(owner, backend)
    owner.setPlaybackControlsVisible(False);owner.setPlaybackControlsVisible(True)
    new = read_ready(owner, backend)
    assert new["lease"] != old["lease"]
    assert not owner.setPlaybackFavorite(SID, ITEM_ID, old["lease"], False)
    assert not backend.jobs


@pytest.mark.parametrize("error", ["uncertain", "offline", "unavailable"])
def test_unconfirmed_write_is_not_replayed_or_imported(controller, error):
    owner, backend, _ = setup_favorite(controller)
    observation = read_ready(owner, backend)
    owner.transport.playback_favorite.side_effect = SessionError(error)
    assert owner.setPlaybackFavorite(SID, ITEM_ID, observation["lease"], True)
    backend.jobs.pop()()
    owner.changed.emit();owner._expire()
    assert owner.state["playback_control"]["status"] == "uncertain"
    assert not owner.state["playback_control"]["favorite_observation"]
    assert not owner.readPlaybackFavorite(SID, ITEM_ID) and not backend.jobs
    owner.transport.playback_favorite.assert_called_once()


@pytest.mark.parametrize("boundary", ["read", "write"])
def test_denial_withdraws_session_and_preserves_pairing(controller, boundary):
    owner, backend, _ = setup_favorite(controller)
    if boundary == "read":
        owner.transport.playback_status.side_effect = SessionError("denied")
        assert owner.readPlaybackFavorite(SID, ITEM_ID)
    else:
        observation = read_ready(owner, backend)
        owner.transport.playback_favorite.side_effect = SessionError("denied")
        assert owner.setPlaybackFavorite(SID, ITEM_ID, observation["lease"], True)
    backend.jobs.pop()()
    assert not owner.state["session_id"] and owner.state["error"] == "denied"
    assert backend.cfg.paired and not owner.state["playback_control"]["favorite_observation"]


@pytest.mark.parametrize("value", [True, False])
def test_actual_http_boundary_sends_explicit_boolean_not_toggle_once(transport, value):
    client, _, request, response = transport
    client.playback_favorite(client.binding(), value)
    assert request.call_count == 1
    args, kwargs = request.call_args
    assert args[0] == "POST" and args[1].endswith("/command")
    assert kwargs["json"]["command"] == "set_current_track_favorite"
    assert kwargs["json"]["value"] is value
    assert "uri" not in kwargs["json"] and "expected_revision" not in kwargs["json"]
    assert kwargs["stream"] and kwargs["allow_redirects"] is False
    response.json.assert_not_called()


@pytest.mark.parametrize("value", [0, 1, None, "true", "false", [], {}])
def test_transport_rejects_untyped_boolean_without_http(transport, value):
    client, _, request, _ = transport
    with pytest.raises(SessionError): client.playback_favorite(client.binding(), value)
    request.assert_not_called()


def test_actual_http_timeout_does_not_retry_or_fallback(transport):
    client, _, request, _ = transport
    request.side_effect = requests.Timeout()
    with pytest.raises(SessionError, match="uncertain"):
        client.playback_favorite(client.binding(), False)
    request.assert_called_once()


@pytest.mark.parametrize("boundary", ["read", "write"])
@pytest.mark.parametrize("reason", ["hide", "foreground", "profile", "item", "end"])
def test_started_favorite_result_after_withdrawal_cannot_publish_or_refresh(controller, boundary, reason):
    owner, backend, _ = setup_favorite(controller)
    if boundary == "write":
        lease = read_ready(owner, backend)["lease"]
        assert owner.setPlaybackFavorite("synthetic-session", ITEM_ID, lease, True)
    else:
        assert owner.readPlaybackFavorite("synthetic-session", ITEM_ID)
    work = backend.jobs.pop()
    def late(*args):
        if reason == "hide": owner.setPlaybackControlsVisible(False)
        elif reason == "foreground": owner.setForeground(False)
        elif reason == "profile": backend.cfg.active_profile_id = "other"
        elif reason == "item": owner._session["broadcast"]["playback"]["item_id"] = "other"
        else: owner.end("synthetic-session")
        return {"success": True} if boundary == "write" else owner.transport.playback_status.return_value
    target = owner.transport.playback_favorite if boundary == "write" else owner.transport.playback_status
    target.side_effect = late
    owner.transport.active.reset_mock()
    work()
    assert not owner.state["playback_control"]["favorite_observation"]
    assert owner.state["playback_control"]["status"] == ""
    owner.transport.active.assert_called_once()
    if reason != "end": assert not backend.jobs


@pytest.mark.parametrize("boundary", ["read", "write"])
def test_real_held_favorite_worker_keeps_end_available(boundary):
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
from test_session_favorite_control import setup_favorite, read_ready, ITEM_ID
app=QCoreApplication([]);backend=Backend();owner=SessionController(backend);owner._deadline_timer.stop()
setup_favorite((owner,backend))
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
if boundary=='write': owner.transport.playback_favorite.side_effect=held
else: owner.transport.playback_status.side_effect=held
assert (owner.setPlaybackFavorite('synthetic-session',ITEM_ID,lease,True) if boundary=='write' else owner.readPlaybackFavorite('synthetic-session',ITEM_ID))
assert entered.wait(2)
owner.end('synthetic-session');assert len(backend.jobs)==1
backend.jobs.pop()();owner.transport.end.assert_called_once()
assert not owner.state['session_id'] and not release.is_set()
release.set();owner._playback_control.executor.shutdown(wait=True);app.processEvents()
assert not owner.state['playback_control']['favorite_observation'] and not owner.state['session_id']
assert owner.transport.active.call_count==2
owner.shutdownImages()
""".replace("BOUNDARY", repr(boundary))
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, "PYTHONPATH": str(root/"src")+os.pathsep+str(root/"tests")}
    result = subprocess.run([sys.executable, "-c", script], cwd=root, env=env,
                            capture_output=True, text=True, timeout=12, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
