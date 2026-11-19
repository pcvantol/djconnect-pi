"""Synthetic whole-set consent and actual worker fences; never personal erasure."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime
from threading import Event
from time import monotonic
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from PySide6.QtCore import QCoreApplication
from test_session_history_delete import NOW, OP
from test_session_history_delete_control import setup as single_setup

from djconnect_pi.session_history_delete import (
    ArchiveDeleteSnapshot,
    BulkDeleteIntent,
    bulk_delete_supported,
)
from djconnect_pi.session_transport import JSON_CONTROL_BYTES, SessionError

pytest_plugins = ["test_session_controller", "test_session_history_delete"]
CAPS = {"capabilities": {"session_history_bulk_delete": True}, "contract_versions": {"session_history_bulk_delete": 1}}


def snapshot(now=NOW, count=12):
    return {"success": True, "schema_version": 1, "owner_profile_id": "owner", "snapshot_id": "opaque-snapshot",
            "target_count": count, "created_at": datetime.fromtimestamp(now, UTC).isoformat(),
            "expires_at": datetime.fromtimestamp(now+300, UTC).isoformat()}


def bulk(client, count=12):
    return client.delete_all_history(client.binding(), "opaque-snapshot", OP, count, confirmed=True)


def test_closed_get_and_post_bind_header_never_private_hints_or_page_set(wire):
    client, cfg, request, response = wire
    cfg.private_session = True
    response.body = snapshot()
    assert client.history_delete_snapshot(client.binding()) == snapshot()
    args, kw = request.call_args
    assert args == ("GET", cfg.ha_url + "/api/djconnect/v1/session/history/delete_snapshot")
    assert kw["params"] == {"device_id": cfg.device_id, "client_type": "raspberry_pi", "history_contract_version": 2}
    assert kw["headers"]["X-DJConnect-Profile-ID"] == "owner" and not kw["allow_redirects"]
    response.body = {"success": True, "schema_version": 1, "owner_profile_id": "owner", "snapshot_id": "opaque-snapshot",
                     "operation_id": OP, "deleted": True, "deleted_session_count": 12}
    assert bulk(client)["deleted_session_count"] == 12
    args, kw = request.call_args
    assert args == ("POST", cfg.ha_url + "/api/djconnect/v1/session/history/delete_all")
    assert kw["json"] == {"device_id": cfg.device_id, "client_type": "raspberry_pi", "history_contract_version": 2,
                          "snapshot_id": "opaque-snapshot", "operation_id": OP, "confirmed": True}
    assert kw["stream"] and kw["headers"]["Authorization"] == "Bearer synthetic-token"
    assert request.call_count == 2 and response.close.call_count == 2
    response.json.assert_not_called()


@pytest.mark.parametrize("field,value", [("owner_profile_id","other"),("schema_version",True),("schema_version",2),
    ("operation_id","other"),("snapshot_id","other"),("deleted",1),("deleted_session_count",True),
    ("deleted_session_count",11),("deleted_session_count",13),("deleted_session_count",None)])
def test_exact_receipt_or_uncertain_no_retry(wire, field, value):
    client, _, request, response = wire
    response.body = {"success":True,"schema_version":1,"owner_profile_id":"owner","snapshot_id":"opaque-snapshot",
                     "operation_id":OP,"deleted":True,"deleted_session_count":12}
    response.body[field] = value
    with pytest.raises(SessionError, match="uncertain"): bulk(client)
    request.assert_called_once()


@pytest.mark.parametrize("method",["snapshot","write"])
@pytest.mark.parametrize("status,code,category",[(401,"anything","denied"),(403,"anything","denied"),
    (409,"history_delete_snapshot_conflict","conflict"),(409,"history_delete_operation_conflict","conflict"),
    (503,"history_delete_outcome_unknown","uncertain"),(503,"history_unavailable","unavailable"),
    (503,"private-personal-error","uncertain"),(404,"history_unavailable","unavailable")])
def test_typed_bulk_errors_and_denial_before_body(wire, method, status, code, category):
    client, _, request, response = wire
    response.status_code, response.body = status, {"success":False,"error":code}
    if status in (401,403): response.iter_content.side_effect = AssertionError("denial must not decode")
    with pytest.raises(SessionError) as got:
        client.history_delete_snapshot(client.binding()) if method=="snapshot" else bulk(client)
    assert got.value.category == category
    assert got.value.code == (code if status not in (401,403) and code!="private-personal-error" else "")
    request.assert_called_once(); response.close.assert_called_once()


@pytest.mark.parametrize("method",["snapshot","write"])
@pytest.mark.parametrize("kind",["declared","stream","depth","redirect","binding"])
def test_stream_resource_and_original_authority_fences(wire, method, kind):
    client, cfg, request, response = wire
    if kind=="declared": response.headers={"Content-Length":str(JSON_CONTROL_BYTES+1)}
    elif kind=="stream": response.iter_content.side_effect=lambda **kw: iter([b" "*(JSON_CONTROL_BYTES+1)])
    elif kind=="depth": response.iter_content.side_effect=lambda **kw: iter([b"["*65+b"]"*65])
    elif kind=="redirect": response.status_code=307
    else:
        def changed(**kw):
            cfg.active_profile_id="successor"
            yield b"{}"
        response.iter_content.side_effect=changed
    with pytest.raises(SessionError):
        client.history_delete_snapshot(client.binding()) if method=="snapshot" else bulk(client)
    request.assert_called_once();response.close.assert_called_once()


@pytest.mark.parametrize("field,value",[("success",False),("schema_version",True),("schema_version",2),
    ("owner_profile_id","foreign"),("snapshot_id",""),("snapshot_id","x"*201),
    ("target_count",True),("target_count",-1),("target_count",1.0),("target_count","12"),
    ("target_count",2**53),("created_at",None),("created_at","2026-10-21T10:00:00"),
    ("expires_at",None),("expires_at","garbage")])
def test_snapshot_strict_metadata_never_defaulted(wire, field, value):
    client,_,_,_=wire
    data=snapshot();data[field]=value
    with pytest.raises(SessionError): ArchiveDeleteSnapshot.parse(data,client.binding(),now=NOW)


@pytest.mark.parametrize("created,expires,now",[(NOW+31,NOW+331,NOW),(NOW,NOW+301,NOW),
    (NOW,NOW,NOW),(NOW,NOW+300,NOW+300),(NOW,NOW+300,float("nan")),(NOW,NOW+300,True)])
def test_snapshot_original_clock_bounds(wire, created, expires, now):
    client,_,_,_=wire
    data=snapshot(created);data["expires_at"]=datetime.fromtimestamp(expires,UTC).isoformat()
    with pytest.raises(SessionError): ArchiveDeleteSnapshot.parse(data,client.binding(),now=now)


@pytest.mark.parametrize("value",[False,None,1,"true"])
def test_no_bulk_capability_or_explicit_confirmation_inferred(wire, value):
    client,_,_,_=wire
    cap=deepcopy(CAPS);cap["capabilities"]["session_history_bulk_delete"]=value
    assert not bulk_delete_supported(cap)
    snap=ArchiveDeleteSnapshot.parse(snapshot(),client.binding(),now=NOW)
    with pytest.raises(SessionError): BulkDeleteIntent.confirmed(client.binding(),0,snap,CAPS,now=NOW,confirmed=value)


def test_one_atomic_bulk_ticket_keeps_original_snapshot_expiry_and_count(wire):
    client,_,_,_=wire
    snap=ArchiveDeleteSnapshot.parse(snapshot(NOW-250),client.binding(),now=NOW)
    intent=BulkDeleteIntent.confirmed(client.binding(),3,snap,CAPS,now=NOW,confirmed=True)
    assert intent.expires_at == NOW+50
    def claim(_):
        try: return intent.claim(client.binding(),3,CAPS,now=NOW)
        except SessionError: return None
    with ThreadPoolExecutor(max_workers=8) as pool: results=list(pool.map(claim,range(16)))
    assert len([r for r in results if r])==1
    assert next(r for r in results if r)=={"snapshot_id":"opaque-snapshot","operation_id":OP,"target_count":12,"confirmed":True}


@pytest.mark.parametrize("reason",["expired","rollback","epoch","binding","caps","zero"])
def test_consent_cannot_renew_or_cross_original_context(wire, reason):
    client,_,_,_=wire
    snap=ArchiveDeleteSnapshot.parse(snapshot(count=0 if reason=="zero" else 12),client.binding(),now=NOW)
    if reason=="zero":
        with pytest.raises(SessionError): BulkDeleteIntent.confirmed(client.binding(),0,snap,CAPS,now=NOW,confirmed=True)
        return
    intent=BulkDeleteIntent.confirmed(client.binding(),0,snap,CAPS,now=NOW,confirmed=True)
    with pytest.raises(SessionError): intent.claim(replace(client.binding(),token="other") if reason=="binding" else client.binding(),
        1 if reason=="epoch" else 0, {} if reason=="caps" else CAPS,
        now=NOW+300 if reason=="expired" else NOW-31 if reason=="rollback" else NOW)


def setup(controller, count=12):
    owner,backend,jobs=single_setup(controller)
    owner._timeline={};owner._caps["capabilities"]["session_history_bulk_delete"]=True
    owner._caps["contract_versions"]["session_history_bulk_delete"]=1
    data=snapshot(owner._clock.now(),count);data["owner_profile_id"]=backend.cfg.active_profile_id
    owner.transport.history_delete_snapshot=Mock(return_value=data)
    owner.transport.delete_all_history=Mock(return_value={"deleted":True})
    return owner,backend,jobs


def prepare(owner,jobs):
    assert owner.beginBulkHistoryDelete();jobs.pop(0)()
    return owner.state["archive_delete"]["lease"]


def test_whole_server_set_not_client_page_or_filter_and_one_receipt_invalidates_all(controller):
    owner,backend,jobs=setup(controller)
    owner._search={"query":"only-one-match"};owner._history_cursor="older";owner._timeline_trail=[{}]
    original=deepcopy((owner._session,vars(backend.cfg)))
    epoch=owner._view_epoch
    lease=prepare(owner,jobs)
    assert owner.state["archive_delete"]["count"]==12 and len(owner._sessions)==1
    assert owner.confirmHistoryDelete(lease) and not owner.confirmHistoryDelete(lease)
    assert owner._sessions and owner._search
    jobs.pop(0)()
    assert owner.transport.delete_all_history.call_args.kwargs["target_count"]==12
    assert owner.transport.delete_all_history.call_args.kwargs["snapshot_id"]=="opaque-snapshot"
    owner.transport.history_delete_snapshot.assert_called_once()  # No replacement token/set at confirmation.
    owner.transport.timeline.assert_not_called();owner.transport.delete_history.assert_not_called()
    assert not owner._sessions and not owner._search and not owner._history_cursor and not owner._timeline_trail
    assert owner._view_epoch>epoch and (owner._session,vars(backend.cfg))==original
    assert len(backend.jobs)==1 and owner._running_action=="refresh"


def test_zero_is_informational_without_uuid_confirmation_or_mutation(controller):
    owner,_,jobs=setup(controller,0);lease=prepare(owner,jobs)
    assert owner.state["archive_delete"]["status"]=="empty"
    assert not owner.confirmHistoryDelete(lease) and not jobs
    owner.transport.delete_all_history.assert_not_called()


@pytest.mark.parametrize("reason",["hide","cancel","epoch","profile","token","foreground","runtime","detail","caps","end"])
@pytest.mark.parametrize("phase",["read","write"])
def test_withdrawal_before_worker_without_gui_tick(controller,reason,phase):
    owner,backend,jobs=setup(controller)
    if phase=="write": assert owner.confirmHistoryDelete(prepare(owner,jobs))
    else: assert owner.beginBulkHistoryDelete()
    if reason=="hide": owner.setArchiveDeleteVisible(False)
    elif reason=="cancel": owner.cancelHistoryDelete()
    elif reason=="epoch": owner._view_epoch+=1
    elif reason=="profile": backend.cfg.active_profile_id="other"
    elif reason=="token": backend.cfg.device_token="other"
    elif reason=="foreground": owner._foreground=False
    elif reason=="runtime": owner._session["session_id"]="other"
    elif reason=="detail": owner._timeline={"session":{"session_id":"other"}}
    elif reason=="caps": owner._caps["capabilities"]["session_history_bulk_delete"]=False
    else: owner.end("live")
    jobs.pop(0)();owner.transport.delete_all_history.assert_not_called()


@pytest.mark.parametrize("when",["active","caps","post"])
@pytest.mark.parametrize("reason",["hide","epoch","profile"])
def test_transport_stage_withdrawal_and_late_receipts(controller,when,reason):
    owner,backend,jobs=setup(controller);assert owner.confirmHistoryDelete(prepare(owner,jobs))
    method={"active":owner.transport.active,"caps":owner.transport.capabilities,"post":owner.transport.delete_all_history}[when]
    original=method.side_effect
    def changed(*args,**kw):
        result=original(*args,**kw) if callable(original) else method.return_value
        if reason=="hide": owner.setArchiveDeleteVisible(False)
        elif reason=="epoch": owner._view_epoch+=1
        else: backend.cfg.active_profile_id="other";owner.invalidate()
        return result
    method.side_effect=changed;jobs.pop(0)()
    assert owner._sessions or reason=="profile"
    assert owner.state["archive_delete"]["status"]!="deleted"
    assert owner.transport.delete_all_history.call_count==(1 if when=="post" else 0)


@pytest.mark.parametrize("category,code,status,blocked",[("uncertain","history_delete_outcome_unknown","uncertain",True),
    ("conflict","history_delete_snapshot_conflict","snapshot_conflict",False),
    ("unavailable","history_unavailable","failed",False)])
def test_no_optimistic_erasure_no_replay_and_explicit_readonly_recovery(controller,category,code,status,blocked):
    owner,backend,jobs=setup(controller);assert owner.confirmHistoryDelete(prepare(owner,jobs))
    owner.transport.delete_all_history.side_effect=SessionError(category,code)
    jobs.pop(0)();assert owner._sessions and owner.state["archive_delete"]["status"]==status
    assert owner.state["archive_delete"]["blocked"]==blocked
    assert owner.recoverHistoryDelete()
    for _ in range(4): QCoreApplication.processEvents()
    assert len(backend.jobs)==1 and owner._running_action=="history"
    owner.transport.delete_all_history.assert_called_once();owner.transport.history_delete_snapshot.assert_called_once()
    assert not jobs


def test_snapshot_original_expiry_before_queued_send_does_not_renew(controller):
    owner,_,jobs=setup(controller);assert owner.confirmHistoryDelete(prepare(owner,jobs))
    now=owner._clock.now();owner._clock=SimpleNamespace(now=lambda:now+301)
    jobs.pop(0)();owner.transport.delete_all_history.assert_not_called()
    owner.transport.history_delete_snapshot.assert_called_once()


def test_bulk_without_active_runtime_and_no_private_mode_type_ban(controller):
    owner,backend,jobs=setup(controller)
    owner._session={};backend.cfg.active_profile_privacy_mode="recording";backend.cfg.private_session=True
    owner.transport.active=Mock(return_value={"success":True,"session":None})
    assert owner.confirmHistoryDelete(prepare(owner,jobs));jobs.pop(0)()
    owner.transport.delete_all_history.assert_called_once();assert not owner._session


@pytest.mark.parametrize("phase",["read","write"])
def test_actual_one_worker_keeps_end_independent(controller,phase):
    owner,backend,jobs=setup(controller)
    if phase=="write": lease=prepare(owner,jobs)
    owner._archive_delete.executor=None
    entered,released,finished=Event(),Event(),Event()
    original=owner.transport.active.side_effect
    def held(*args,**kw):
        entered.set();assert released.wait(3)
        try:return original(*args,**kw)
        finally:finished.set()
    owner.transport.active.side_effect=held
    try:
        assert owner.confirmHistoryDelete(lease) if phase=="write" else owner.beginBulkHistoryDelete()
        assert entered.wait(1)
        started=monotonic();owner.end("live")
        assert monotonic()-started<0.2 and owner._running_action=="end" and len(backend.jobs)==1
        released.set();assert finished.wait(1)
        for _ in range(20):QCoreApplication.processEvents()
        owner.transport.delete_all_history.assert_not_called()
    finally:released.set();owner._archive_delete.shutdown()


@pytest.mark.parametrize("language",["en","nl","de","fr","es"])
def test_dynamic_bulk_count_can_be_translated_before_qml_substitution(language):
    from djconnect_pi.i18n import translate
    text=translate(language,"session_delete_all_confirm")
    assert text.count("%1")==1 and "12" in text.replace("%1","12")


@pytest.mark.parametrize("count",[0,-1,True,"12",12.0])
def test_typed_zero_or_wrong_count_never_reaches_http(wire,count):
    client,_,request,_=wire
    with pytest.raises(SessionError): bulk(client,count)
    request.assert_not_called()


@pytest.mark.parametrize("method,route,payload",[("GET","session/history/delete_snapshot",{"profile_id":"owner"}),
    ("POST","session/history/delete_all",{"snapshot_id":"token","operation_id":OP,"confirmed":True,"history_contract_version":2,"private_session":True}),
    ("POST","session/history/unknown",{}),("GET","session/history/delete_all",{})])
def test_typed_exception_cannot_expand_to_arbitrary_payload_or_route(wire,method,route,payload):
    client,_,request,_=wire
    with pytest.raises(SessionError): client._request(client.binding(),method,route,payload,archive_delete=True)
    request.assert_not_called()


@pytest.mark.parametrize("change",["caps","runtime","denial","malformed"])
@pytest.mark.parametrize("phase",["read","write"])
def test_fresh_server_cannot_authorize_changed_owner_or_capability(controller,change,phase):
    owner,_,jobs=setup(controller)
    if phase=="write": assert owner.confirmHistoryDelete(prepare(owner,jobs))
    else: assert owner.beginBulkHistoryDelete()
    if change=="caps": owner.transport.capabilities=Mock(return_value={})
    elif change=="runtime": owner.transport.active=Mock(return_value={"success":True,"session":{"session_id":"successor","runtime_state":"active"}})
    elif change=="denial": owner.transport.active.side_effect=SessionError("denied")
    else: owner.transport.active=Mock(return_value={"malformed":True})
    jobs.pop(0)();owner.transport.delete_all_history.assert_not_called()


@pytest.mark.parametrize("reason",["cancel","hide","profile","epoch"])
def test_completed_bulk_worker_waiting_for_gui_cannot_replace_successor(controller,reason):
    owner,backend,jobs=setup(controller);assert owner.confirmHistoryDelete(prepare(owner,jobs))
    control=owner._archive_delete;control.ready.disconnect(control.finish);results=[];control.ready.connect(results.append)
    jobs.pop(0)();assert len(results)==1
    if reason=="cancel": owner.cancelHistoryDelete()
    elif reason=="hide": owner.setArchiveDeleteVisible(False)
    elif reason=="profile": backend.cfg.active_profile_id="other";owner.invalidate()
    else: owner._view_epoch+=1
    before=deepcopy(owner._sessions);control.finish(results[0])
    assert owner._sessions==before and control.status!="deleted" and not jobs


@pytest.mark.parametrize("close",["destroy","shutdown"])
def test_deferred_playback_notification_is_owned_and_cannot_outlive_controller(close):
    import os
    import subprocess
    import sys
    code = """
from PySide6.QtCore import QCoreApplication
from shiboken6 import delete
from test_session_controller import Backend
from djconnect_pi.session_controller import SessionController
app=QCoreApplication([])
for _ in range(30):
    backend=Backend();owner=SessionController(backend);owner._deadline_timer.stop()
    owner.setPlaybackControlsVisible(True);owner.cancelPlaybackIntent()
    if CLOSE=='shutdown':owner.shutdownImages()
    delete(owner);delete(backend)
app.processEvents()
print('OWNED_NOTIFICATION_PASS')
""".replace("CLOSE",repr(close))
    result=subprocess.run([sys.executable,"-c",code],capture_output=True,text=True,timeout=15,check=False,
        env={**os.environ,"PYTHONPATH":"src:tests","QT_QPA_PLATFORM":"offscreen","QT_QUICK_BACKEND":"software"})
    assert result.returncode==0,(result.returncode,result.stderr)
    assert result.stdout.strip()=="OWNED_NOTIFICATION_PASS" and not result.stderr


def test_visibility_notifications_remain_deferred_coalesced_and_revocation_immediate(controller):
    owner,_,_=setup(controller)
    QCoreApplication.processEvents()  # Finish the fixture's separate archive-visibility notification.
    signals=[];owner.changed.connect(lambda:signals.append(True))
    owner.setPlaybackControlsVisible(True);owner.setPlaybackControlsVisible(False);owner.cancelPlaybackIntent()
    assert not signals and not owner._playback_control.visible
    QCoreApplication.processEvents()
    assert len(signals)==1
