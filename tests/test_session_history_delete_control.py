"""Actual controller/Qt tickets; synthetic owner reads and one mutation boundary."""
from copy import deepcopy
from threading import Event
from time import monotonic
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from PySide6.QtCore import QCoreApplication

from djconnect_pi.session_transport import SessionError

pytest_plugins = ["test_session_controller"]


def setup(controller):
    owner, backend = controller
    owner._session = {"session_id":"live", "runtime_state":"active", "broadcast":{"session":{"session_id":"live"}}}
    owner._loaded = True
    owner._caps = {"success":True,"capabilities":{"session_conversation_history":True,"session_history_delete":True},
                   "contract_versions":{"session_history_entries":2,"session_history_delete":1}}
    owner._timeline = {"success":True,"schema_version":2,"history_contract_version":2,"revision":"page-revision",
        "session":{"session_id":"saved","revision":"opaque-original","lifecycle_status":"ENDED"},"entries":[],"next_cursor":None,
        "_session_deadline":owner._clock.now()+86400}
    owner._sessions = [{"session_id":"saved","_history_deadline":owner._timeline["_session_deadline"]}]
    jobs=[]
    owner._archive_delete.executor=SimpleNamespace(submit=jobs.append,shutdown=lambda **kw:None)
    owner.transport.active=Mock(side_effect=lambda *a,**kw:{"success":True,"session":deepcopy(owner._session)})
    owner.transport.capabilities=Mock(side_effect=lambda *a,**kw:deepcopy(owner._caps))
    owner.transport.timeline=Mock(side_effect=lambda *a,**kw:deepcopy(owner._timeline))
    owner.transport.delete_history=Mock(return_value={"deleted":True})  # Typed transport itself is tested independently.
    owner.setArchiveDeleteVisible(True)
    return owner,backend,jobs


def prepare(owner,jobs):
    assert owner.beginHistoryDelete("saved")
    assert owner.busy and owner.state["archive_delete"]["status"]=="reading"
    jobs.pop(0)()
    assert owner.state["archive_delete"]["status"]=="confirm"
    owner.transport.delete_history.assert_not_called()
    return owner.state["archive_delete"]["lease"]


def test_explicit_read_confirmation_and_exact_receipt_invalidate_whole_archive_only(controller):
    owner,backend,jobs=setup(controller)
    owner._history_cursor="cursor";owner._history_trail=[{"start":"older"}];owner._timeline_trail=[{"cursor":"detail"}]
    owner._search={"query":"q","matches":[]};owner._history_loaded=True
    owner._conversation=[{"identity":"live-conversation"}];owner._retained_flow=[{"identity":"live-flow"}]
    original=deepcopy((owner._session,owner._conversation,owner._retained_flow,owner._current_reply,vars(backend.cfg)))
    epoch=owner._view_epoch
    lease=prepare(owner,jobs)
    assert owner.confirmHistoryDelete(lease)
    assert not owner.confirmHistoryDelete(lease)
    assert owner._sessions and owner._timeline and owner._search  # No optimistic erasure.
    jobs.pop(0)()
    owner.transport.delete_history.assert_called_once()
    assert owner.transport.delete_history.call_args.kwargs["expected_revision"]=="opaque-original"
    assert owner.transport.delete_history.call_args.kwargs["session_id"]=="saved"
    assert owner.transport.delete_history.call_args.kwargs["confirmed"] is True
    assert owner._view_epoch>epoch and not owner._sessions and not owner._timeline and not owner._search
    assert not owner._history_cursor and not owner._history_trail and not owner._timeline_trail and not owner._history_loaded
    assert (owner._session,owner._conversation,owner._retained_flow,owner._current_reply,vars(backend.cfg))==original
    assert owner.state["archive_delete"]["status"]=="deleted"
    assert len(backend.jobs)==1 and owner._running_action=="refresh"  # Independent owner read, never another mutation.


@pytest.mark.parametrize("reason",["hide","cancel","navigation","archive","epoch","profile","token","foreground","session","revision","retention","capability","end"])
@pytest.mark.parametrize("phase",["read","write"])
def test_queued_withdrawal_without_gui_tick_never_reaches_delete(controller,reason,phase):
    owner,backend,jobs=setup(controller)
    if phase=="write":
        lease=prepare(owner,jobs)
        assert owner.confirmHistoryDelete(lease)
    else: assert owner.beginHistoryDelete("saved")
    if reason=="hide": owner.setArchiveDeleteVisible(False)
    elif reason=="cancel": owner.cancelHistoryDelete()
    elif reason=="navigation": owner.closeSaved()
    elif reason=="archive": owner.clearArchive()
    elif reason=="epoch": owner._view_epoch+=1
    elif reason=="profile": backend.cfg.active_profile_id="other"
    elif reason=="token": backend.cfg.device_token="new"
    elif reason=="foreground": owner._foreground=False
    elif reason=="session": owner._session["session_id"]="successor"
    elif reason=="revision": owner._timeline["session"]["revision"]="new"
    elif reason=="retention": owner._timeline["_session_deadline"]=owner._clock.now()-1
    elif reason=="capability": owner._caps["capabilities"]["session_history_delete"]=False
    elif reason=="end": owner.end("live")
    jobs.pop(0)()
    owner.transport.delete_history.assert_not_called()


@pytest.mark.parametrize("reason",["caps","revision","target","state","owner_session","denial","malformed"])
@pytest.mark.parametrize("phase",["read","write"])
def test_fresh_server_preflights_cannot_authorize_changed_confirmation(controller,reason,phase):
    owner,_,jobs=setup(controller)
    if phase=="write":
        lease=prepare(owner,jobs)
        assert owner.confirmHistoryDelete(lease)
    else: assert owner.beginHistoryDelete("saved")
    page=deepcopy(owner._timeline)
    if reason=="caps": owner.transport.capabilities.side_effect=lambda *a,**kw:{"success":True}
    elif reason=="revision": page["session"]["revision"]="changed"
    elif reason=="target": page["session"]["session_id"]="other"
    elif reason=="state": page["session"]["lifecycle_status"]="ACTIVE"
    elif reason=="owner_session": owner.transport.active.side_effect=lambda *a,**kw:{"success":True,"session":None}
    elif reason=="denial": owner.transport.timeline.side_effect=SessionError("denied")
    elif reason=="malformed": page["entries"]=None
    if reason not in {"caps","owner_session","denial"}: owner.transport.timeline.side_effect=lambda *a,**kw:page
    jobs.pop(0)()
    owner.transport.delete_history.assert_not_called()
    assert not owner.state["archive_delete"]["lease"]


@pytest.mark.parametrize("error",["uncertain","unavailable","conflict","denied","context_changed"])
def test_post_failure_never_claims_erasure_or_retries(controller,error):
    owner,backend,jobs=setup(controller)
    lease=prepare(owner,jobs)
    owner.transport.delete_history.side_effect=SessionError(error)
    original=deepcopy(owner._sessions)
    assert owner.confirmHistoryDelete(lease)
    jobs.pop(0)()
    owner.transport.delete_history.assert_called_once()
    assert not jobs and not backend.jobs
    assert owner.state["archive_delete"]["status"]!="deleted"
    if error not in {"denied","context_changed"}: assert owner._sessions==original
    if error=="denied": assert not owner._session and backend.cfg.paired
    if error in {"uncertain","context_changed"}:
        assert owner.state["archive_delete"]["blocked"]
        assert not owner.beginHistoryDelete("saved")


def test_uncertain_explicit_recovery_withdraws_stale_archive_and_only_reads(controller):
    owner,backend,jobs=setup(controller)
    lease=prepare(owner,jobs);owner.transport.delete_history.side_effect=SessionError("uncertain")
    assert owner.confirmHistoryDelete(lease);jobs.pop(0)()
    assert owner.recoverHistoryDelete()
    for _ in range(4): QCoreApplication.processEvents()
    assert owner._running_action=="history" and len(backend.jobs)==1
    assert not owner._timeline and not owner._sessions and not owner._history_cursor
    owner.transport.delete_history.assert_called_once()
    assert not jobs


@pytest.mark.parametrize("when",["active","caps","detail","post"])
@pytest.mark.parametrize("reason",["cancel","hide","profile","epoch"])
def test_late_withdrawal_cannot_publish_confirmation_or_receipt(controller,when,reason):
    owner,backend,jobs=setup(controller)
    lease=prepare(owner,jobs)
    assert owner.confirmHistoryDelete(lease)
    def withdraw():
        if reason=="cancel": owner.cancelHistoryDelete()
        elif reason=="hide": owner.setArchiveDeleteVisible(False)
        elif reason=="profile": backend.cfg.active_profile_id="successor";owner.invalidate()
        else: owner._view_epoch+=1
    target={"active":owner.transport.active,"caps":owner.transport.capabilities,"detail":owner.transport.timeline,"post":owner.transport.delete_history}[when]
    previous=target.side_effect
    value=target.return_value
    def changed(*args,**kwargs):
        response=previous(*args,**kwargs) if callable(previous) else value
        withdraw()
        return response
    target.side_effect=changed
    original=deepcopy(owner._sessions)
    jobs.pop(0)()
    assert owner.state["archive_delete"]["status"]!="deleted"
    assert owner.transport.delete_history.call_count==(1 if when=="post" else 0)
    if reason!="profile": assert owner._sessions==original
    else: assert not owner.state["archive_delete"]["blocked"]


def test_removed_and_restored_capability_cannot_revive_queued_ticket(controller):
    owner,_,jobs=setup(controller)
    lease=prepare(owner,jobs);assert owner.confirmHistoryDelete(lease)
    owner._caps["capabilities"]["session_history_delete"]=False;owner.changed.emit()
    owner._caps["capabilities"]["session_history_delete"]=True;owner.changed.emit()
    jobs.pop(0)();owner.transport.delete_history.assert_not_called()


@pytest.mark.parametrize("field,value",[("revision",3),("revision",True),("lifecycle_status","ACTIVE"),("lifecycle_status",None)])
def test_nonterminal_or_numeric_list_metadata_has_no_action(controller,field,value):
    owner,_,jobs=setup(controller)
    owner._timeline["session"][field]=value
    assert not owner.state["archive_delete"]["available"]
    assert not owner.beginHistoryDelete("saved") and not jobs


@pytest.mark.parametrize("phase",["read","write"])
def test_read_and_mutation_use_actual_dedicated_worker_and_end_stays_available(controller,phase):
    owner,backend,jobs=setup(controller)
    if phase=="write": lease=prepare(owner,jobs)
    owner._archive_delete.executor=None
    entered,released,finished=Event(),Event(),Event()
    original=owner.transport.active.side_effect
    def held(*args,**kwargs):
        entered.set()
        assert released.wait(3)
        try: return original(*args,**kwargs)
        finally: finished.set()
    owner.transport.active.side_effect=held
    try:
        assert owner.confirmHistoryDelete(lease) if phase=="write" else owner.beginHistoryDelete("saved")
        assert entered.wait(1)
        started=monotonic();owner.end("live")
        assert monotonic()-started<0.2 and owner._running_action=="end" and len(backend.jobs)==1
        assert not owner.prepareArtwork("live","any")
        released.set();assert finished.wait(1)
        for _ in range(20): QCoreApplication.processEvents()
        owner.transport.delete_history.assert_not_called()
    finally:
        released.set();owner._archive_delete.shutdown()


def test_archive_epoch_rejects_read_completed_before_erasure(controller):
    owner,_,jobs=setup(controller)
    old_epoch=owner._view_epoch
    old_page=deepcopy(owner._timeline)
    lease=prepare(owner,jobs);assert owner.confirmHistoryDelete(lease);jobs.pop(0)()
    owner._running=99
    owner._apply({"serial":99,"binding":owner.transport.binding(),"action":"timeline","view_epoch":old_epoch,"timeline":old_page})
    assert not owner._timeline and owner._session["session_id"]=="live"


def test_valid_current_reply_and_native_flow_are_preserved_after_receipt(controller, monkeypatch):
    from test_session_current_reply import send, setup_reply
    owner,backend,jobs=setup(controller)
    page=deepcopy(owner._timeline)
    setup_reply(owner)
    send(owner,backend)
    assert owner.state["current_reply"]
    from uuid import UUID

    from djconnect_pi import session_history_delete
    # The unchanged source fixture uses its original historical clock. Mint only
    # this synthetic operation at that same clock, never rebase a display grant.
    op = str(UUID(int=(int(owner._clock.now()*1000)<<80)|(7<<76)|(2<<62)|1))
    monkeypatch.setattr(session_history_delete, "operation_id", lambda: op)
    owner._caps["capabilities"]["session_history_delete"]=True
    owner._caps["contract_versions"]["session_history_delete"]=1
    owner._timeline=page
    owner.transport.timeline=Mock(side_effect=lambda *a,**kw:deepcopy(page))
    owner.transport.active=Mock(side_effect=lambda *a,**kw:{"success":True,"session":deepcopy(owner._session)})
    owner.transport.capabilities=Mock(side_effect=lambda *a,**kw:deepcopy(owner._caps))
    before=deepcopy((owner._session,owner._current_reply,owner._moments,owner._retained_flow))
    lease=prepare(owner,jobs);assert owner.confirmHistoryDelete(lease);jobs.pop(0)()
    assert owner.state["archive_delete"]["status"]=="deleted"
    assert (owner._session,owner._current_reply,owner._moments,owner._retained_flow)==before


@pytest.mark.parametrize("change",["hide","profile","session","foreground","detail","shutdown"])
def test_deferred_recovery_cannot_start_in_a_successor_context(controller,change):
    owner,backend,_=setup(controller)
    assert owner.recoverHistoryDelete()
    assert not owner.recoverHistoryDelete()  # One bounded pending read, not a retry loop.
    if change=="hide": owner.setArchiveDeleteVisible(False)
    elif change=="profile": backend.cfg.active_profile_id="other"
    elif change=="session": owner._session["session_id"]="other"
    elif change=="foreground": owner._foreground=False
    elif change=="detail": owner._timeline={"session":{"session_id":"other"}}
    else: owner._archive_delete.shutdown()
    for _ in range(4): QCoreApplication.processEvents()
    assert not backend.jobs


def test_operation_expiry_before_queued_send_never_renews_or_posts(controller):
    owner,_,jobs=setup(controller)
    lease=prepare(owner,jobs)
    assert owner.confirmHistoryDelete(lease)
    operation=owner._archive_delete.request["intent"].operation
    now=owner._clock.now()
    owner._clock=SimpleNamespace(now=lambda:now+301)
    jobs.pop(0)()
    owner.transport.delete_history.assert_not_called()
    assert not owner.confirmHistoryDelete(lease)
    assert operation  # The original ID was created once; no automatic replacement job.
    assert not jobs


@pytest.mark.parametrize("reason",["cancel","hide","profile","epoch"])
def test_completed_worker_receipt_waiting_for_gui_cannot_replace_successor_view(controller,reason):
    owner,backend,jobs=setup(controller)
    lease=prepare(owner,jobs);assert owner.confirmHistoryDelete(lease)
    control=owner._archive_delete
    control.ready.disconnect(control.finish)
    results=[];control.ready.connect(results.append)
    jobs.pop(0)();assert len(results)==1
    owner.transport.delete_history.assert_called_once()
    if reason=="cancel": owner.cancelHistoryDelete()
    elif reason=="hide": owner.setArchiveDeleteVisible(False)
    elif reason=="profile": backend.cfg.active_profile_id="other";owner.invalidate()
    else: owner._view_epoch+=1
    before=deepcopy(owner._timeline)
    control.finish(results[0])
    assert owner._timeline==before and control.status!="deleted"
    assert not jobs


def test_saved_session_can_be_deleted_without_any_active_runtime(controller):
    owner,backend,jobs=setup(controller)
    owner._session={}
    owner.transport.active=Mock(return_value={"success":True,"session":None})
    lease=prepare(owner,jobs);assert owner.confirmHistoryDelete(lease);jobs.pop(0)()
    owner.transport.delete_history.assert_called_once()
    assert owner.state["archive_delete"]["status"]=="deleted" and not owner._session
    assert len(backend.jobs)==1 and owner._running_action=="refresh"  # No start/end/playback command.
