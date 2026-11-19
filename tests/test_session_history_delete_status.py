"""Original archive outcome reads, never personal deletion or mutation replay."""
import json
from copy import deepcopy
from hashlib import sha256
from threading import Event
from time import monotonic
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from PySide6.QtCore import QCoreApplication
from test_session_history_bulk_delete import prepare as bulk_prepare
from test_session_history_bulk_delete import setup as bulk_setup
from test_session_history_delete import OP
from test_session_history_delete_control import prepare as single_prepare
from test_session_history_delete_control import setup as single_setup

from djconnect_pi.session_history_delete import (
    archive_status_supported,
    original_archive_status,
)
from djconnect_pi.session_transport import JSON_CONTROL_BYTES, SessionError

pytest_plugins=["test_session_controller","test_session_history_delete"]


def body(mode):
    return {"session_id":"old-session","expected_revision":"opaque:exact:revision"} if mode=="single" else {"snapshot_id":"opaque-snapshot"}


def response(mode,state="completed"):
    fields=body(mode)
    result={"success":True,"schema_version":1,"owner_profile_id":"owner","operation_id":OP,"operation":mode,
        "request_digest":sha256(json.dumps(fields,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
        **fields,"state":state,"definitive":state=="completed"}
    if state=="completed":
        result["receipt"]={"success":True,"schema_version":1,"owner_profile_id":"owner","operation_id":OP,"deleted":True,
            **({"deleted_session_id":"old-session"} if mode=="single" else {"snapshot_id":"opaque-snapshot","deleted_session_count":12})}
    return result


def read(client,mode):
    return client.history_delete_status(client.binding(),mode,OP,body(mode),**({"target_count":12} if mode=="all" else {}))


@pytest.mark.parametrize("mode",["single","all"])
@pytest.mark.parametrize("state",["completed","unknown","pending","expired_unknown"])
def test_exact_original_closed_get_digest_and_minimal_state(wire,mode,state):
    client,cfg,request,reply=wire;cfg.private_session=True;reply.body=response(mode,state)
    assert read(client,mode)=={"state":state,"definitive":state=="completed"}
    args,kw=request.call_args
    assert args==("GET",cfg.ha_url+"/api/djconnect/v1/session/history/delete/status")
    assert kw["params"]=={"device_id":cfg.device_id,"client_type":"raspberry_pi","contract_version":1,
                          "operation_id":OP,"operation":mode,**body(mode)}
    assert "confirmed" not in kw["params"] and "confirmation_id" not in kw["params"]
    assert kw["headers"]["X-DJConnect-Profile-ID"]=="owner" and kw["stream"] and not kw["allow_redirects"]
    request.assert_called_once();reply.json.assert_not_called();reply.close.assert_called_once()


@pytest.mark.parametrize("mode",["single","all"])
@pytest.mark.parametrize("field,value",[("owner_profile_id","other"),("operation_id","other"),("operation","content"),
    ("request_digest","0"*64),("schema_version",True),("schema_version",2),("state","rejected"),
    ("state",{}),("definitive",1),("definitive",False)])
def test_unbound_or_fictitious_completion_is_never_admitted(wire,mode,field,value):
    client,_,request,reply=wire;reply.body=response(mode);reply.body[field]=value
    with pytest.raises(SessionError,match="uncertain"):read(client,mode)
    request.assert_called_once()


@pytest.mark.parametrize("mode",["single","all"])
@pytest.mark.parametrize("field,value",[("success",False),("schema_version",True),("operation_id","other"),
    ("owner_profile_id","other"),("deleted",1)])
def test_nested_original_receipt_must_be_exact(wire,mode,field,value):
    client,_,_,reply=wire;reply.body=response(mode);reply.body["receipt"][field]=value
    with pytest.raises(SessionError,match="uncertain"):read(client,mode)


@pytest.mark.parametrize("mode",["single","all"])
def test_wrong_echoed_target_and_nested_target_are_both_rejected(wire,mode):
    client,_,request,reply=wire
    key="session_id" if mode=="single" else "snapshot_id"
    reply.body=response(mode);reply.body[key]="other"
    with pytest.raises(SessionError):read(client,mode)
    reply.body=response(mode);reply.body["receipt"]["deleted_session_id" if mode=="single" else "snapshot_id"]="other"
    with pytest.raises(SessionError):read(client,mode)
    assert request.call_count==2


@pytest.mark.parametrize("value",[True,11,13,None,"12"])
def test_bulk_status_requires_original_captured_count(wire,value):
    client,_,_,reply=wire;reply.body=response("all");reply.body["receipt"]["deleted_session_count"]=value
    with pytest.raises(SessionError):read(client,"all")


@pytest.mark.parametrize("mode",["single","all"])
@pytest.mark.parametrize("state",["unknown","pending","expired_unknown"])
def test_unsettled_state_cannot_smuggle_a_receipt_or_definitive_rejection(wire,mode,state):
    client,_,_,reply=wire;reply.body=response(mode,state);reply.body["receipt"]=response(mode)["receipt"]
    with pytest.raises(SessionError):read(client,mode)
    reply.body=response(mode,state);reply.body["definitive"]=True
    with pytest.raises(SessionError):read(client,mode)


@pytest.mark.parametrize("mode",["single","all"])
@pytest.mark.parametrize("kind",["denied401","denied403","declared","stream","depth","redirect","binding","pending503"])
def test_status_transport_boundaries_never_replay(wire,mode,kind):
    client,cfg,request,reply=wire;reply.body=response(mode)
    if kind.startswith("denied"):
        reply.status_code=int(kind[-3:]);reply.iter_content.side_effect=AssertionError("No denial body")
    elif kind=="declared":reply.headers={"Content-Length":str(JSON_CONTROL_BYTES+1)}
    elif kind=="stream":reply.iter_content.side_effect=lambda **kw:iter([b" "*(JSON_CONTROL_BYTES+1)])
    elif kind=="depth":reply.iter_content.side_effect=lambda **kw:iter([b"["*65+b"]"*65])
    elif kind=="redirect":reply.status_code=307
    elif kind=="binding":
        def changed(**kw):
            cfg.device_token="successor"
            yield b"{}"
        reply.iter_content.side_effect=changed
    else:reply.status_code=503;reply.body={"success":False,"error":"history_delete_outcome_unknown"}
    with pytest.raises(SessionError):read(client,mode)
    request.assert_called_once();assert request.call_args.args[0]=="GET";reply.close.assert_called_once()


@pytest.mark.parametrize("operation,fields",[("content",{}),("single",{"session_id":"x"}),("all",{"snapshot_id":"x","confirmed":True}),
    ("single",{"session_id":"x","expected_revision":3}),(None,{})])
def test_malformed_original_request_cannot_use_status_exception(wire,operation,fields):
    client,_,request,_=wire
    with pytest.raises(SessionError):client.history_delete_status(client.binding(),operation,OP,fields)
    request.assert_not_called()


def setup(controller,mode):
    owner,backend,jobs=(single_setup if mode=="single" else bulk_setup)(controller)
    owner._caps["capabilities"]["session_history_delete_status"]=True
    owner._caps["contract_versions"]["session_history_delete_status"]=1
    owner.transport.history_delete_status=Mock(return_value={"state":"completed","definitive":True})
    prepare=single_prepare if mode=="single" else bulk_prepare
    lease=prepare(owner,jobs);assert owner.confirmHistoryDelete(lease)
    post=owner.transport.delete_history if mode=="single" else owner.transport.delete_all_history
    post.side_effect=SessionError("uncertain")
    jobs.pop(0)();assert owner.state["archive_delete"]["blocked"] and owner.state["archive_delete"]["status_available"]
    return owner,backend,jobs,post


@pytest.mark.parametrize("mode",["single","all"])
def test_manual_status_reconciles_exact_original_attempt_no_second_post(controller,mode):
    owner,backend,jobs,post=setup(controller,mode)
    original=owner._archive_delete.pending["intent"];epoch=owner._view_epoch;active=deepcopy(owner._session)
    assert owner.checkHistoryDeleteStatus();assert not owner.checkHistoryDeleteStatus()
    assert owner._sessions and not backend.jobs
    jobs.pop(0)()
    post.assert_called_once();owner.transport.history_delete_status.assert_called_once_with(original.binding,**original_archive_status(original))
    assert owner.state["archive_delete"]["status"]=="deleted" and not owner.state["archive_delete"]["blocked"]
    assert not owner._sessions and not owner._timeline and owner._view_epoch>epoch
    assert owner._session==active and len(backend.jobs)==1 and owner._running_action=="refresh"


@pytest.mark.parametrize("mode",["single","all"])
@pytest.mark.parametrize("state",["unknown","pending","expired_unknown"])
def test_unknown_and_expiry_never_authorize_replacement_id_or_optimistic_erasure(controller,mode,state):
    owner,backend,jobs,post=setup(controller,mode)
    original=owner._archive_delete.pending["intent"];before=deepcopy(owner._sessions)
    owner.transport.history_delete_status.return_value={"state":state,"definitive":False}
    assert owner.checkHistoryDeleteStatus();jobs.pop(0)()
    assert owner._sessions==before and owner.state["archive_delete"]["status"]==state
    assert owner.state["archive_delete"]["blocked"] and owner._archive_delete.pending["intent"] is original
    assert not owner.beginHistoryDelete("saved") and not owner.beginBulkHistoryDelete()
    assert owner.recoverHistoryDelete()
    for _ in range(4):QCoreApplication.processEvents()
    assert owner.state["archive_delete"]["blocked"] and owner._archive_delete.pending["intent"] is original
    assert len(backend.jobs)==1 and owner._running_action=="history"
    post.assert_called_once();owner.transport.history_delete_status.assert_called_once();assert not jobs


@pytest.mark.parametrize("mode",["single","all"])
@pytest.mark.parametrize("category",["invalid","conflict","unavailable","uncertain"])
def test_definitive_error_for_status_request_cannot_settle_ambiguous_post(controller,mode,category):
    owner,_,jobs,post=setup(controller,mode)
    owner.transport.history_delete_status.side_effect=SessionError(category)
    assert owner.checkHistoryDeleteStatus();jobs.pop(0)()
    assert owner.state["archive_delete"]["blocked"] and owner.state["archive_delete"]["status"]=="uncertain"
    assert owner._archive_delete.pending and owner._sessions
    post.assert_called_once()


@pytest.mark.parametrize("mode",["single","all"])
@pytest.mark.parametrize("change",["hide","cancel","profile","token","epoch","foreground","runtime","caps","end"])
def test_queued_status_withdrawal_is_immediate_and_never_mutates(controller,mode,change):
    owner,backend,jobs,post=setup(controller,mode)
    assert owner.checkHistoryDeleteStatus()
    if change=="hide":owner.setArchiveDeleteVisible(False)
    elif change=="cancel":owner.cancelHistoryDelete()
    elif change=="profile":backend.cfg.active_profile_id="other"
    elif change=="token":backend.cfg.device_token="other"
    elif change=="epoch":owner._view_epoch+=1
    elif change=="foreground":owner._foreground=False
    elif change=="runtime":owner._session["session_id"]="other"
    elif change=="caps":owner._caps["capabilities"]["session_history_delete_status"]=False
    else:owner.end("live")
    jobs.pop(0)();owner.transport.history_delete_status.assert_not_called();post.assert_called_once()


@pytest.mark.parametrize("mode",["single","all"])
@pytest.mark.parametrize("stage",["active","caps","status","gui"])
def test_late_bound_completed_status_cannot_overwrite_successor_view(controller,mode,stage):
    owner,_,jobs,post=setup(controller,mode);assert owner.checkHistoryDeleteStatus()
    if stage=="gui":
        control=owner._archive_delete;control.ready.disconnect(control.finish);results=[];control.ready.connect(results.append)
        jobs.pop(0)();owner._view_epoch+=1;control.finish(results[0])
    else:
        method={"active":owner.transport.active,"caps":owner.transport.capabilities,"status":owner.transport.history_delete_status}[stage]
        original=method.side_effect
        def changed(*args,**kw):
            value=original(*args,**kw) if callable(original) else method.return_value
            owner._view_epoch+=1
            return value
        method.side_effect=changed;jobs.pop(0)()
    assert owner._sessions and owner.state["archive_delete"]["status"]!="deleted"
    post.assert_called_once()


@pytest.mark.parametrize("mode",["single","all"])
def test_status_after_original_operation_expiry_can_only_report_uncertainty(controller,mode):
    owner,_,jobs,post=setup(controller,mode)
    now=owner._clock.now();owner._clock=SimpleNamespace(now=lambda:now+301)
    assert owner.checkHistoryDeleteStatus();jobs.pop(0)()
    assert owner.state["archive_delete"]["blocked"] and owner._sessions
    post.assert_called_once()  # Even a synthetic late completed receipt cannot extend the journal.


@pytest.mark.parametrize("version",[None,True,0,2,"1"])
def test_status_unknown_capability_versions_stay_hidden(controller,version):
    owner,_,jobs,_=setup(controller,"single")
    owner._caps["contract_versions"]["session_history_delete_status"]=version
    assert not archive_status_supported(owner._caps)
    assert not owner.state["archive_delete"]["status_available"] and not owner.checkHistoryDeleteStatus() and not jobs


@pytest.mark.parametrize("mode",["single","all"])
def test_original_status_survives_dialog_close_and_archive_refresh_but_not_new_owner(controller,mode):
    owner,backend,jobs,post=setup(controller,mode);original=owner._archive_delete.pending["intent"]
    owner.cancelHistoryDelete();assert owner.state["archive_delete"]["status_available"]
    assert owner.recoverHistoryDelete()
    for _ in range(4):QCoreApplication.processEvents()
    backend.jobs.pop(0)();owner._running=0;owner._running_action=""
    assert owner.checkHistoryDeleteStatus();jobs.pop(0)()
    assert owner.transport.history_delete_status.call_args.kwargs["operation_id"]==original.operation
    post.assert_called_once()
    owner._archive_delete.pending={"intent":original,"posted":True,"kind":"single"};owner._archive_delete.blocked=True
    backend.cfg.active_profile_id="other";owner.changed.emit()
    assert owner._archive_delete.pending is None and not owner._archive_delete.blocked


@pytest.mark.parametrize("mode",["single","all"])
def test_actual_status_worker_keeps_end_free_and_never_replays(controller,mode):
    owner,backend,_jobs,post=setup(controller,mode)
    owner._archive_delete.executor=None;entered,released,finished=Event(),Event(),Event()
    def held(*args,**kw):
        entered.set();assert released.wait(3)
        try:return {"state":"completed","definitive":True}
        finally:finished.set()
    owner.transport.history_delete_status.side_effect=held
    try:
        assert owner.checkHistoryDeleteStatus() and entered.wait(1)
        start=monotonic();owner.end("live")
        assert monotonic()-start<.2 and len(backend.jobs)==1 and owner._running_action=="end"
        released.set();assert finished.wait(1)
        owner._archive_delete.executor.shutdown(wait=True)
        for _ in range(4):QCoreApplication.processEvents()
        assert owner.state["archive_delete"]["status"]!="deleted"
        post.assert_called_once()
    finally:released.set();owner._archive_delete.shutdown()


def test_whole_archive_withdrawal_announces_no_intermediate_stale_detail(controller):
    owner,_,_=single_setup(controller)
    owner._search={"query":"old"};owner._history_cursor="cursor";owner._timeline_trail=[{}]
    observed=[]
    owner.changed.connect(lambda:observed.append((bool(owner._sessions),bool(owner._timeline),bool(owner._search),bool(owner._history_cursor),bool(owner._timeline_trail))))
    owner.invalidateArchive()
    assert observed and all(row==(False,False,False,False,False) for row in observed)
