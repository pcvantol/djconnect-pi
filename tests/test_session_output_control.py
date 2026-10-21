"""Explicit server output inventory, original-output fence and one typed transfer."""
from copy import deepcopy
from unittest.mock import Mock

import pytest
import requests
from test_session_playback_control import ITEM_ID, setup

from djconnect_pi.session_playback_control import output_choices
from djconnect_pi.session_transport import SessionError

pytest_plugins = ["test_session_controller", "test_session_transport"]
SID = "synthetic-session"


def setup_outputs(controller):
    owner, backend = setup(controller)
    backend.cfg.music_backend_capabilities.update(supports_outputs=True, supports_transfer_or_output_selection=True)
    status = owner.transport.playback_status.return_value
    status["music_backend_capabilities"].update(supports_outputs=True, supports_transfer_or_output_selection=True)
    status["playback"]["device"] = {"id": "original-output", "active": True, "is_restricted": False}
    inventory = {**deepcopy(status), "devices": [
        {"id": "original-output", "name": "Living room", "active": True, "cached": False, "is_restricted": False},
        {"id": "selected-output", "name": "Kitchen <b>literal</b>", "active": False, "cached": False, "is_restricted": False},
        {"id": "old-output", "name": "Cached", "active": False, "cached": True, "is_restricted": False},
        {"id": "restricted-output", "name": "Restricted", "active": False, "cached": False, "is_restricted": True}]}
    owner.transport.playback_outputs = Mock(return_value=inventory)
    owner.transport.playback_output = Mock(return_value={"success": True, "playback": {"device": {"id": "selected-output"}}})
    return owner, backend, status, inventory


def read_ready(owner, backend):
    assert owner.readPlaybackOutputs(SID, ITEM_ID)
    backend.jobs.pop()()
    state = owner.state["playback_control"]["outputs"]
    assert state and not backend.jobs
    return state


def test_explicit_read_admits_only_server_non_cached_unrestricted_choices(controller):
    owner, backend, _, _ = setup_outputs(controller)
    original = deepcopy(owner._session)
    assert not owner.state["playback_control"]["outputs"]
    state = read_ready(owner, backend)
    assert state["origin"] == "original-output"
    assert [row["id"] for row in state["choices"]] == ["original-output", "selected-output"]
    assert owner._session == original
    owner.transport.playback_output.assert_not_called()
    owner.transport.active.assert_called_once()
    owner.transport.playback_status.assert_called_once()
    owner.transport.playback_outputs.assert_called_once()


@pytest.mark.parametrize("state", ["playing", "paused"])
def test_typed_selection_rechecks_original_and_choice_without_optimistic_import(controller, state):
    owner, backend, status, _ = setup_outputs(controller)
    owner._session["broadcast"]["playback"]["state"] = state
    status["playback"]["is_playing"] = state == "playing"
    lease = read_ready(owner, backend)["lease"]
    original = deepcopy(owner._session)
    assert owner.setPlaybackOutput(SID, ITEM_ID, lease, "selected-output")
    assert not owner.state["playback_control"]["outputs"]
    backend.jobs.pop()()
    owner.transport.playback_output.assert_called_once_with(owner.transport.binding(), "selected-output", state == "playing")
    assert owner._session == original and not owner.state["playback_control"]["outputs"]
    assert len(backend.jobs) == 1 and owner._running_action == "refresh"
    assert owner.transport.active.call_count == owner.transport.playback_status.call_count == owner.transport.playback_outputs.call_count == 2


@pytest.mark.parametrize("field,value", [("supports_outputs", False), ("supports_outputs", 1), ("supports_transfer_or_output_selection", False), ("supports_transfer_or_output_selection", "true")])
def test_local_missing_strict_transfer_capability_does_not_even_read(controller, field, value):
    owner, backend, _, _ = setup_outputs(controller)
    backend.cfg.music_backend_capabilities[field] = value
    assert not owner.readPlaybackOutputs(SID, ITEM_ID) and not backend.jobs
    owner.transport.playback_outputs.assert_not_called()


def test_ma_noop_set_output_is_not_advertised_as_transfer(controller):
    owner, backend, _, _ = setup_outputs(controller)
    backend.cfg.music_backend = "music_assistant"
    assert not owner.state["playback_control"]["outputs_supported"]
    assert not owner.readPlaybackOutputs(SID, ITEM_ID) and not backend.jobs


@pytest.mark.parametrize("reason", ["origin_id", "inactive", "restricted", "caps", "backend", "revision", "available", "devices_type", "duplicate", "duplicate_cached", "bad_id", "name", "active_type", "no_active", "other_active"])
def test_bad_status_or_inventory_preserves_session_without_default_choice(controller, reason):
    owner, backend, status, inventory = setup_outputs(controller)
    if reason == "origin_id": status["playback"]["device"]["id"] = ""
    elif reason == "inactive": status["playback"]["device"]["active"] = False
    elif reason == "restricted": status["playback"]["device"]["is_restricted"] = True
    elif reason == "caps": inventory["music_backend_capabilities"]["supports_outputs"] = False
    elif reason == "backend": inventory["music_backend"] = "music_assistant"
    elif reason == "revision": inventory["music_backend_revision"] = True
    elif reason == "available": inventory["backend_available"] = False
    elif reason == "devices_type": inventory["devices"] = {}
    elif reason in {"duplicate", "duplicate_cached"}:
        row = deepcopy(inventory["devices"][1]);row["cached"] = reason == "duplicate_cached";inventory["devices"].append(row)
    elif reason == "bad_id": inventory["devices"][1]["id"] = "bad\nID"
    elif reason == "name": inventory["devices"][1]["name"] = ""
    elif reason == "active_type": inventory["devices"][1]["active"] = 0
    elif reason == "no_active": inventory["devices"][0]["active"] = False
    else: inventory["devices"][1]["active"] = True
    assert owner.readPlaybackOutputs(SID, ITEM_ID)
    backend.jobs.pop()()
    assert not owner.state["playback_control"]["outputs"] and owner.state["session_id"]
    assert owner.state["playback_control"]["outputs_status"] == "unavailable" and not backend.jobs
    owner.transport.playback_output.assert_not_called()


@pytest.mark.parametrize("count,valid", [(1, True), (32, True), (33, False), (100, False), (101, False)])
def test_inventory_and_ram_choice_bounds_do_not_truncate(controller, count, valid):
    _, _, _, inventory = setup_outputs(controller)
    inventory["devices"] = [{"id": "original-output" if i == 0 else str(i), "name": str(i), "active": i == 0, "cached": False, "is_restricted": False} for i in range(count)]
    if valid: assert len(output_choices(inventory, "spotify_direct", 4, "original-output")) == count
    else:
        with pytest.raises(SessionError): output_choices(inventory, "spotify_direct", 4, "original-output")


@pytest.mark.parametrize("reason", ["origin", "missing_choice", "cached_choice", "restricted_choice", "caps", "backend_revision", "profile", "item", "state"])
def test_fresh_preflight_must_still_match_original_and_selectable_choice(controller, reason):
    owner, backend, status, inventory = setup_outputs(controller)
    lease = read_ready(owner, backend)["lease"]
    assert owner.setPlaybackOutput(SID, ITEM_ID, lease, "selected-output")
    if reason == "origin": status["playback"]["device"]["id"] = "other-output"
    elif reason == "missing_choice": inventory["devices"].pop(1)
    elif reason == "cached_choice": inventory["devices"][1]["cached"] = True
    elif reason == "restricted_choice": inventory["devices"][1]["is_restricted"] = True
    elif reason == "caps": inventory["music_backend_capabilities"]["supports_transfer_or_output_selection"] = False
    elif reason == "backend_revision": inventory["music_backend_revision"] += 1
    elif reason == "profile": backend.cfg.active_profile_id = "other"
    elif reason == "item": owner._session["broadcast"]["playback"]["item_id"] = "other"
    else: status["playback"]["is_playing"] = False
    backend.jobs.pop()()
    owner.transport.playback_output.assert_not_called()
    assert not owner.state["playback_control"]["outputs"]


@pytest.mark.parametrize("target", ["original-output", "old-output", "restricted-output", "arbitrary", "", None, [], True])
def test_only_explicit_leased_selectable_other_id_can_queue(controller, target):
    owner, backend, _, _ = setup_outputs(controller)
    lease = read_ready(owner, backend)["lease"]
    assert not owner.setPlaybackOutput(SID, ITEM_ID, lease, target)
    assert not owner.setPlaybackOutput(SID, ITEM_ID, lease+1, "selected-output")
    assert not backend.jobs


@pytest.mark.parametrize("reason", ["close", "foreground", "profile", "item", "backend", "revision", "capability", "end"])
def test_local_withdrawal_prevents_queued_reads_and_write(controller, reason):
    owner, backend, _, _ = setup_outputs(controller)
    lease = read_ready(owner, backend)["lease"]
    assert owner.setPlaybackOutput(SID, ITEM_ID, lease, "selected-output")
    work = backend.jobs.pop();owner.transport.active.reset_mock();owner.transport.playback_outputs.reset_mock()
    if reason == "close": owner.cancelPlaybackIntent()
    elif reason == "foreground": owner.setForeground(False)
    elif reason == "profile": backend.cfg.active_profile_id = "other"
    elif reason == "item": owner._session["broadcast"]["playback"]["item_id"] = "other"
    elif reason == "backend": backend.cfg.music_backend = "music_assistant"
    elif reason == "revision": backend.cfg.music_backend_revision += 1
    elif reason == "capability": backend.cfg.music_backend_capabilities["supports_outputs"] = False
    else: owner.end(SID)
    work();owner.transport.active.assert_not_called();owner.transport.playback_outputs.assert_not_called()
    owner.transport.playback_output.assert_not_called()
    assert not owner.state["playback_control"]["outputs"]


def test_close_roundtrip_never_revives_old_choice_lease(controller):
    owner, backend, _, _ = setup_outputs(controller)
    old = read_ready(owner, backend)["lease"]
    owner.setPlaybackControlsVisible(False);owner.setPlaybackControlsVisible(True)
    assert read_ready(owner, backend)["lease"] != old
    assert not owner.setPlaybackOutput(SID, ITEM_ID, old, "selected-output")


@pytest.mark.parametrize("error", ["uncertain", "offline", "unavailable"])
def test_uncertain_transfer_is_not_replayed_or_imported(controller, error):
    owner, backend, _, _ = setup_outputs(controller)
    lease = read_ready(owner, backend)["lease"]
    owner.transport.playback_output.side_effect = SessionError(error)
    assert owner.setPlaybackOutput(SID, ITEM_ID, lease, "selected-output")
    backend.jobs.pop()();owner.changed.emit();owner._expire()
    assert owner.state["playback_control"]["status"] == "uncertain" and not backend.jobs
    assert not owner.readPlaybackOutputs(SID, ITEM_ID)
    owner.transport.playback_output.assert_called_once()


@pytest.mark.parametrize("boundary", ["inventory", "write"])
def test_denial_withdraws_context_preserving_pairing(controller, boundary):
    owner, backend, _, _ = setup_outputs(controller)
    if boundary == "inventory":
        owner.transport.playback_outputs.side_effect = SessionError("denied")
        assert owner.readPlaybackOutputs(SID, ITEM_ID)
    else:
        lease = read_ready(owner, backend)["lease"]
        owner.transport.playback_output.side_effect = SessionError("denied")
        assert owner.setPlaybackOutput(SID, ITEM_ID, lease, "selected-output")
    backend.jobs.pop()()
    assert owner.state["error"] == "denied" and not owner.state["session_id"] and backend.cfg.paired


@pytest.mark.parametrize("play", [True, False])
def test_actual_http_output_payload_is_explicit_and_preserves_requested_play_flag(transport, play):
    client, _, request, response = transport
    client.playback_output(client.binding(), "selected-output", play)
    assert request.call_count == 1
    args, kwargs = request.call_args
    assert args[0] == "POST" and args[1].endswith("/command")
    assert kwargs["json"]["command"] == "set_output" and kwargs["json"]["value"] == "selected-output"
    assert kwargs["json"]["play"] is play and kwargs["json"]["client_type"] == "raspberry_pi"
    assert not ({"uri", "expected_session", "item_id", "backend"} & set(kwargs["json"]))
    assert kwargs["stream"] is True and kwargs["allow_redirects"] is False
    response.json.assert_not_called()


@pytest.mark.parametrize("target,play", [(None, False), ([], False), ("", False), ("a\nb", False), ("user ", False), ("x"*513, False), ("a", None), ("a", 1)])
def test_transport_rejects_untyped_or_invalid_output_without_request(transport, target, play):
    client, _, request, _ = transport
    with pytest.raises(SessionError): client.playback_output(client.binding(), target, play)
    request.assert_not_called()


def test_actual_http_devices_uses_existing_isolated_command_once(transport):
    client, _, request, _ = transport
    client.playback_outputs(client.binding())
    request.assert_called_once()
    assert request.call_args.kwargs["json"]["command"] == "devices"


def test_actual_transfer_timeout_has_no_replay_or_fallback(transport):
    client, _, request, _ = transport
    request.side_effect = requests.Timeout()
    with pytest.raises(SessionError, match="uncertain"): client.playback_output(client.binding(), "selected-output", True)
    request.assert_called_once()


@pytest.mark.parametrize("boundary", ["read", "write"])
@pytest.mark.parametrize("reason", ["hide", "foreground", "profile", "item", "end"])
def test_started_output_result_after_withdrawal_cannot_publish_or_refresh(controller, boundary, reason):
    owner, backend, _, _ = setup_outputs(controller)
    if boundary == "write":
        lease = read_ready(owner, backend)["lease"]
        assert owner.setPlaybackOutput("synthetic-session", ITEM_ID, lease, "selected-output")
    else:
        assert owner.readPlaybackOutputs("synthetic-session", ITEM_ID)
    work = backend.jobs.pop()
    def late(*args):
        if reason == "hide": owner.setPlaybackControlsVisible(False)
        elif reason == "foreground": owner.setForeground(False)
        elif reason == "profile": backend.cfg.active_profile_id = "other"
        elif reason == "item": owner._session["broadcast"]["playback"]["item_id"] = "other"
        else: owner.end("synthetic-session")
        return {"success": True} if boundary == "write" else owner.transport.playback_outputs.return_value
    target = owner.transport.playback_output if boundary == "write" else owner.transport.playback_outputs
    target.side_effect = late
    owner.transport.active.reset_mock()
    work()
    assert not owner.state["playback_control"]["outputs"]
    assert owner.state["playback_control"]["status"] == ""
    owner.transport.active.assert_called_once()
    if reason != "end": assert not backend.jobs


@pytest.mark.parametrize("boundary", ["read", "write"])
def test_real_held_output_worker_keeps_end_available(boundary):
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
from test_session_output_control import setup_outputs, read_ready, ITEM_ID
app=QCoreApplication([]);backend=Backend();owner=SessionController(backend);owner._deadline_timer.stop()
setup_outputs((owner,backend))
boundary=BOUNDARY
if boundary=='write': lease=read_ready(owner,backend)['lease']
owner._playback_control.executor=None
entered=Event();release=Event()
owner.transport.end=Mock(return_value={'success':True})
owner.transport.active=Mock(side_effect=lambda *a,**k:{'success':True,'session':None if owner._running_action=='end' else deepcopy(owner._session)})
owner.transport.capabilities=Mock(return_value={})
def held(*args):
    entered.set();assert release.wait(3)
    return {'success':True} if boundary=='write' else owner.transport.playback_outputs.return_value
if boundary=='write': owner.transport.playback_output.side_effect=held
else: owner.transport.playback_outputs.side_effect=held
assert (owner.setPlaybackOutput('synthetic-session',ITEM_ID,lease,'selected-output') if boundary=='write' else owner.readPlaybackOutputs('synthetic-session',ITEM_ID))
assert entered.wait(2)
owner.end('synthetic-session');assert len(backend.jobs)==1
backend.jobs.pop()();owner.transport.end.assert_called_once()
assert not owner.state['session_id'] and not release.is_set()
release.set();owner._playback_control.executor.shutdown(wait=True);app.processEvents()
assert not owner.state['playback_control']['outputs'] and not owner.state['session_id']
assert owner.transport.active.call_count==2
owner.shutdownImages()
""".replace("BOUNDARY", repr(boundary))
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, "PYTHONPATH": str(root/"src")+os.pathsep+str(root/"tests")}
    result = subprocess.run([sys.executable, "-c", script], cwd=root, env=env,
                            capture_output=True, text=True, timeout=12, check=False)
    assert result.returncode == 0, result.stdout + result.stderr



@pytest.mark.parametrize("field", ["music_backend_capabilities", "music_backend"])
def test_absent_backend_metadata_stays_unavailable_without_breaking_other_session_state(controller, field):
    owner, backend, _, _ = setup_outputs(controller)
    delattr(backend.cfg, field)
    assert not owner.state["playback_control"]["outputs_supported"]
    assert not owner.readPlaybackOutputs(SID, ITEM_ID)
    assert owner.state["session_id"] == SID and not backend.jobs
