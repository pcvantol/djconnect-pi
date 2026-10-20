"""Actual controller with held explicit command jobs; no HA/player effects."""
from copy import deepcopy
from hashlib import sha256
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from djconnect_pi.session_transport import SessionError

pytest_plugins = ["test_session_controller"]
URI = "spotify:track:0000000000000000000001"
ITEM_ID = sha256(URI.encode()).hexdigest()[:24]


def setup(controller):
    owner, backend = controller
    backend.cfg.music_backend = "spotify_direct"
    backend.cfg.music_backend_available = True
    backend.cfg.music_backend_revision = 4
    backend.cfg.music_backend_capabilities = {"supports_favorites": True}
    owner._session = {"session_id": "synthetic-session", "runtime_state": "active", "broadcast": {
        "session": {"session_id": "synthetic-session"}, "playback": {
            "state": "playing", "item_id": ITEM_ID, "title": "<b>Literal</b> 🎵", "source_url": "",
            "updated_at": "2026-10-20T12:00:00Z"}}}
    owner._playback_control.executor = SimpleNamespace(submit=backend.jobs.append, shutdown=lambda **kw: None)
    owner.transport.active = Mock(side_effect=lambda *args, **kw: {"success": True, "session": deepcopy(owner._session)})
    owner.transport.playback_status = Mock(return_value={"success": True, "music_backend": "spotify_direct", "music_backend_revision": 4, "music_backend_available": True,
        "backend_available": True, "music_backend_capabilities": {"supports_favorites": True},
        "playback": {"uri": URI, "has_playback": True, "is_playing": True}})
    owner.transport.playback_command = Mock(return_value={"success": True, "playback": {"title": "Never imported"}})
    owner.setPlaybackControlsVisible(True)
    return owner, backend


@pytest.mark.parametrize("command", ["pause", "next", "previous", "save_current_track", "play"])
def test_explicit_command_once_then_independent_owner_read_without_optimism(controller, command):
    owner, backend = setup(controller)
    if command == "play":
        owner._session["broadcast"]["playback"]["state"] = "paused"
        owner.transport.playback_status.return_value["playback"]["is_playing"] = False
    original = deepcopy(owner._session)
    assert owner.playbackCommand("synthetic-session", ITEM_ID, command)
    assert owner.busy and owner.state["playback_control"]["status"] == "sending"
    assert not owner.playbackCommand("synthetic-session", ITEM_ID, command)
    backend.jobs.pop()()
    owner.transport.playback_command.assert_called_once_with(owner.transport.binding(), command)
    assert owner._session == original  # No response/optimistic Runtime overwrite.
    assert owner.state["playback_control"]["status"] == "accepted"
    assert len(backend.jobs) == 1 and owner._running_action == "refresh"


@pytest.mark.parametrize("reason", ["foreground", "hide", "session", "item", "state", "profile", "backend", "backend_revision", "unavailable", "private", "favorite", "end"])
def test_withdrawal_before_queued_command_prevents_dispatch_without_tick(controller, reason):
    owner, backend = setup(controller)
    assert owner.playbackCommand("synthetic-session", ITEM_ID, "save_current_track")
    work = backend.jobs.pop()
    if reason == "foreground": owner.setForeground(False)
    elif reason == "hide": owner.setPlaybackControlsVisible(False)
    elif reason == "session": owner._session["session_id"] = "other"
    elif reason == "item": owner._session["broadcast"]["playback"]["item_id"] = "other"
    elif reason == "state": owner._session["broadcast"]["playback"]["state"] = "paused"
    elif reason == "profile": backend.cfg.active_profile_id = "other"
    elif reason == "backend": backend.cfg.music_backend = "later_manual"
    elif reason == "backend_revision": backend.cfg.music_backend_revision += 1
    elif reason == "unavailable": backend.cfg.music_backend_available = False
    elif reason == "private": backend.cfg.private_session = True
    elif reason == "favorite": backend.cfg.music_backend_capabilities["supports_favorites"] = False
    else: owner.end("synthetic-session")
    work()
    owner.transport.playback_command.assert_not_called()
    assert not owner._playback_control.running


@pytest.mark.parametrize("reason", ["foreground", "profile", "item", "hide", "end"])
def test_started_command_can_finish_but_late_success_cannot_publish_or_read(controller, reason):
    owner, backend = setup(controller)
    def late(*args):
        if reason == "foreground": owner.setForeground(False)
        elif reason == "profile": backend.cfg.active_profile_id = "other"
        elif reason == "item": owner._session["broadcast"]["playback"]["item_id"] = "other"
        elif reason == "hide": owner.setPlaybackControlsVisible(False)
        else: owner.end("synthetic-session")
        return {"success": True}
    owner.transport.playback_command.side_effect = late
    assert owner.playbackCommand("synthetic-session", ITEM_ID, "next")
    backend.jobs.pop()()
    owner.transport.playback_command.assert_called_once()
    owner.transport.active.assert_called_once()  # The preflight; no follow-up after withdrawal.
    assert owner.state["playback_control"]["status"] == ""


@pytest.mark.parametrize("error", ["uncertain", "offline", "unavailable", "invalid"])
def test_uncertain_command_never_replays_and_blocks_until_explicit_refresh(controller, error):
    owner, backend = setup(controller)
    owner.transport.playback_command.side_effect = SessionError(error)
    original = deepcopy(owner._session)
    assert owner.playbackCommand("synthetic-session", ITEM_ID, "next")
    backend.jobs.pop()()
    assert not backend.jobs and owner._session == original
    assert owner.state["playback_control"]["status"] == "uncertain"
    owner.changed.emit();owner._expire()
    assert not owner.playbackCommand("synthetic-session", ITEM_ID, "next")
    owner.refreshPlayback()
    assert owner._running_action == "refresh" and len(backend.jobs) == 1
    owner.transport.playback_command.assert_called_once()


def test_observed_change_and_back_cannot_revive_queued_intent(controller):
    owner, backend = setup(controller)
    assert owner.playbackCommand("synthetic-session", ITEM_ID, "next")
    owner._session["broadcast"]["playback"]["item_id"] = "other";owner.changed.emit()
    owner._session["broadcast"]["playback"]["item_id"] = ITEM_ID;owner.changed.emit()
    backend.jobs.pop()()
    owner.transport.playback_command.assert_not_called()


def test_denial_withdraws_only_current_private_client_context(controller):
    owner, backend = setup(controller)
    owner.transport.playback_command.side_effect = SessionError("denied")
    assert owner.playbackCommand("synthetic-session", ITEM_ID, "next")
    backend.jobs.pop()()
    assert not owner.state["session_id"] and owner.state["error"] == "denied"
    assert backend.cfg.paired


@pytest.mark.parametrize("command", ["set_volume", "seek", "toggle", "", None, ["next"]])
def test_only_closed_supported_command_inputs_are_accepted(controller, command):
    owner, backend = setup(controller)
    assert not owner.playbackCommand("synthetic-session", ITEM_ID, command)
    assert not backend.jobs


def test_favorite_requires_strict_advertised_capability(controller):
    owner, backend = setup(controller)
    backend.cfg.music_backend_capabilities = {"supports_favorites": "true"}
    assert not owner.state["playback_control"]["favorite"]
    assert not owner.playbackCommand("synthetic-session", ITEM_ID, "save_current_track")


def test_hide_round_trip_cancels_queued_intent_and_preserves_draft_context(controller):
    owner, backend = setup(controller)
    owner._selection = {"unchanged": "selection"}
    assert owner.playbackCommand("synthetic-session", ITEM_ID, "pause")
    owner.setPlaybackControlsVisible(False);owner.setPlaybackControlsVisible(True)
    backend.jobs.pop()()
    owner.transport.playback_command.assert_not_called()
    assert owner._selection == {"unchanged": "selection"}


@pytest.mark.parametrize("reason", ["denied", "backend", "available", "capability", "profile", "item", "foreground"])
def test_fresh_owner_preflight_cannot_authorize_stale_or_unsupported_write(controller, reason):
    owner, backend = setup(controller)
    status = deepcopy(owner.transport.playback_status.return_value)
    def check(*args):
        if reason == "denied": raise SessionError("denied")
        if reason == "backend": status["music_backend"] = "music_assistant"
        elif reason == "available": status["backend_available"] = False
        elif reason == "capability": status["music_backend_capabilities"]["supports_favorites"] = False
        elif reason == "profile": backend.cfg.active_profile_id = "other"
        elif reason == "item": owner._session["broadcast"]["playback"]["item_id"] = "other"
        else: owner.setForeground(False)
        return status
    owner.transport.playback_status.side_effect = check
    assert owner.playbackCommand("synthetic-session", ITEM_ID, "save_current_track")
    backend.jobs.pop()()
    owner.transport.playback_command.assert_not_called()



def test_real_held_command_does_not_block_end_in_isolated_qt_process():
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
from test_session_playback_control import setup, ITEM_ID
app=QCoreApplication([]);backend=Backend();owner=SessionController(backend);owner._deadline_timer.stop()
setup((owner,backend));owner._playback_control.executor=None
entered=Event();release=Event()
owner.transport.end=Mock(return_value={'success':True})
owner.transport.active=Mock(side_effect=lambda *args, **kw:{'success':True,'session':None if owner._running_action=='end' else deepcopy(owner._session)})
owner.transport.capabilities=Mock(return_value={})
def held(*args):
    entered.set()
    assert release.wait(3)
    return {'success':True}
owner.transport.playback_command.side_effect=held
assert owner.playbackCommand('synthetic-session',ITEM_ID,'next') and entered.wait(2)
owner.end('synthetic-session');assert len(backend.jobs)==1
backend.jobs.pop()()
owner.transport.end.assert_called_once()
assert not owner.state['session_id'] and not release.is_set()
release.set();owner._playback_control.executor.shutdown(wait=True);app.processEvents()
assert owner.transport.active.call_count==2 and not owner.state['session_id']
owner.shutdownImages()
"""
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, "PYTHONPATH": str(root/"src")+os.pathsep+str(root/"tests")}
    result = subprocess.run([sys.executable, "-c", script], cwd=root, env=env, capture_output=True, text=True, timeout=12, check=False)
    assert result.returncode == 0, result.stdout + result.stderr



def test_closing_popout_before_dispatch_revokes_queued_command(controller):
    owner, backend = setup(controller)
    assert owner.playbackCommand("synthetic-session", ITEM_ID, "next")
    owner.cancelPlaybackIntent()
    assert owner._playback_control.request is None
    backend.jobs.pop()()
    owner.transport.playback_status.assert_not_called()
    owner.transport.playback_command.assert_not_called()


@pytest.mark.parametrize("reason", ["item", "state", "missing", "revision"])
def test_fresh_backend_observation_must_match_original_rendered_item(controller, reason):
    owner, backend = setup(controller)
    status = owner.transport.playback_status.return_value
    if reason == "item": status["playback"]["uri"] = "spotify:track:0000000000000000000002"
    elif reason == "state": status["playback"]["is_playing"] = False
    elif reason == "missing": status.pop("playback")
    else: status["music_backend_revision"] += 1
    assert owner.playbackCommand("synthetic-session", ITEM_ID, "next")
    backend.jobs.pop()()
    owner.transport.playback_command.assert_not_called()


def test_owner_session_withdrawn_at_preflight_cannot_dispatch_or_keep_old_context(controller):
    owner, backend = setup(controller)
    owner.transport.active.side_effect = None
    owner.transport.active.return_value = {"success": True, "session": None}
    assert owner.playbackCommand("synthetic-session", ITEM_ID, "next")
    backend.jobs.pop()()
    owner.transport.playback_command.assert_not_called()
    assert not owner.state["session_id"]
