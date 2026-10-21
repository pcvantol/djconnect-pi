"""Synthetic paired wire/consent boundaries, never personal-data erasure."""
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID

import pytest
import requests

from djconnect_pi import session_history_delete as consent
from djconnect_pi.session_transport import (
    JSON_CONTROL_BYTES,
    SessionError,
    SessionTransport,
)

NOW = 1_792_576_800.0
OP = str(UUID(int=(int(NOW * 1000) << 80) | (7 << 76) | (2 << 62) | 1))
CAPS = {"capabilities": {"session_history_delete": True}, "contract_versions": {"session_history_delete": 1}}
DETAIL = {"success": True, "schema_version": 2, "history_contract_version": 2,
          "session": {"session_id": "old-session", "lifecycle_status": "ENDED", "revision": "opaque:exact:revision"}}


@pytest.fixture
def wire(monkeypatch):
    cfg = SimpleNamespace(paired=True, device_token="synthetic-token", ha_url="https://fixture.invalid/ha",
        device_id="djconnect-raspberry-pi-fixture", explicit_profile_id="owner", active_profile_id="owner",
        active_profile_type="personal", active_profile_privacy_mode="private", private_session=False, language="nl")
    response = Mock(status_code=200, headers={})
    response.body = {"success": True, "schema_version": 1, "operation_id": OP,
                     "owner_profile_id": "owner", "deleted_session_id": "old-session", "deleted": True}
    response.iter_content.side_effect = lambda **_: iter([json.dumps(response.body).encode()])
    response.json.side_effect = AssertionError("Never call unbounded Response.json")
    request = Mock(return_value=response)
    monkeypatch.setattr(requests, "request", Mock(side_effect=AssertionError("No ambient HTTP")))
    class Isolated:
        trust_env = True
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def request(self, *args, **kw):
            assert self.trust_env is False
            return request(*args, **kw)
    monkeypatch.setattr(requests, "Session", Isolated)
    monkeypatch.setattr(consent, "operation_id", lambda: OP)
    return SessionTransport(lambda: cfg), cfg, request, response


def delete(client, **kw):
    return client.delete_history(client.binding(), "old-session", "opaque:exact:revision", OP, confirmed=True, **kw)


def test_exact_closed_payload_original_profile_header_and_bounded_receipt(wire):
    client, cfg, request, response = wire
    cfg.private_session = True  # Must not leak this generic body hint into the closed allowlist.
    receipt = delete(client)
    assert request.call_count == 1
    args, kw = request.call_args
    assert args == ("POST", "https://fixture.invalid/ha/api/djconnect/v1/session/history/delete")
    assert kw["json"] == {"device_id": cfg.device_id, "client_type": "raspberry_pi", "session_id": "old-session",
                          "expected_revision": "opaque:exact:revision", "operation_id": OP,
                          "confirmed": True, "history_contract_version": 2}
    assert kw["headers"]["X-DJConnect-Profile-ID"] == "owner"
    assert kw["headers"]["Authorization"] == "Bearer synthetic-token"
    assert kw["headers"]["Cache-Control"] == "no-store"
    assert kw["allow_redirects"] is False and kw["stream"] is True
    assert receipt == {"operation_id": OP, "owner_profile_id": "owner", "deleted_session_id": "old-session", "deleted": True}
    response.close.assert_called_once()
    response.json.assert_not_called()


@pytest.mark.parametrize("status,code,category", [(400,"invalid_history_delete_request","unavailable"),
    (404,"history_unavailable","unavailable"),(409,"session_not_archived","conflict"),
    (409,"history_revision_conflict","conflict"),(409,"history_delete_operation_conflict","conflict"),
    (503,"history_unavailable","unavailable"),(503,"history_delete_outcome_unknown","uncertain"),
    (503,"history_delete_capacity","unavailable"),(500,"private-body-token","uncertain"),
    (503,"private-body-token","uncertain"),(200,"history_delete_outcome_unknown","uncertain")])
def test_typed_failure_no_response_import_or_retry(wire, status, code, category):
    client, cfg, request, response = wire
    response.status_code, response.body = status, {"success": False, "error": code}
    with pytest.raises(SessionError) as got: delete(client)
    assert got.value.category == category
    assert got.value.code == (code if status in {400,404,409,503} and code != "private-body-token" else "")
    assert str(got.value) == category and cfg.paired
    request.assert_called_once()
    response.close.assert_called_once()


@pytest.mark.parametrize("status", [401,403,301,302,307,308])
def test_denial_redirect_never_reads_body(wire, status):
    client, _, request, response = wire
    response.status_code = status
    response.iter_content.side_effect = AssertionError("No body allocation")
    with pytest.raises(SessionError, match="denied" if status in {401,403} else "uncertain"): delete(client)
    request.assert_called_once()
    response.close.assert_called_once()


@pytest.mark.parametrize("field,value", [("schema_version",True),("schema_version",2),("operation_id","foreign"),
    ("owner_profile_id","foreign"),("deleted_session_id","active"),("deleted",1),("deleted",False)])
def test_false_or_mismatched_receipt_is_never_erasure(wire, field, value):
    client, _, request, response = wire
    response.body[field] = value
    with pytest.raises(SessionError, match="uncertain"): delete(client)
    request.assert_called_once()


@pytest.mark.parametrize("field,value", [("session_id",None),("session_id"," x"),("session_id","x"*201),
    ("expected_revision",0),("expected_revision",True),("expected_revision",None),("expected_revision",""),
    ("expected_revision","x"*4097),("operation_id",None),("operation_id","replay-id"),
    ("operation_id",OP.upper()),("confirmed",False),("confirmed",1),("confirmed",None)])
def test_malformed_or_unconfirmed_request_has_zero_http(wire, field, value):
    client, _, request, _ = wire
    args = {"session_id":"old-session","expected_revision":"opaque:exact:revision","operation_id":OP,"confirmed":True}
    args[field] = value
    with pytest.raises(SessionError, match="invalid"): client.delete_history(client.binding(),**args)
    request.assert_not_called()


@pytest.mark.parametrize("url", ["https://user:password@fixture.invalid", "ftp://fixture.invalid", "https://fixture.invalid?x=1",
    "https://fixture.invalid#x", "https://fixture.invalid:70000", "https://fixture.invalid\n"])
def test_bad_origin_never_prepares_or_sends(wire, url):
    client, cfg, request, _ = wire
    cfg.ha_url = url
    with pytest.raises(SessionError, match="invalid"): delete(client)
    request.assert_not_called()


@pytest.mark.parametrize("status", [200,503])
@pytest.mark.parametrize("body_kind", ["oversize_header","oversize_chunk","deep","malformed","nonobject"])
def test_delete_success_and_pending_errors_have_control_budget(wire, status, body_kind):
    client, _, request, response = wire
    response.status_code = status
    if body_kind == "oversize_header": response.headers = {"Content-Length": str(JSON_CONTROL_BYTES+1)}
    else:
        raw = {"oversize_chunk":b" "*(JSON_CONTROL_BYTES+1), "deep":b"["*65+b"]"*65,
               "malformed":b"not JSON", "nonobject":b"[]"}[body_kind]
        response.iter_content.side_effect = lambda **_: iter([raw])
    with pytest.raises(SessionError, match="uncertain"): delete(client)
    request.assert_called_once()
    response.close.assert_called_once()


@pytest.mark.parametrize("stage", ["before","headers","chunks"])
def test_original_binding_precedes_body_and_denial(wire, stage):
    client, cfg, request, response = wire
    original = client.binding()
    if stage == "before": cfg.active_profile_id = "foreign"
    elif stage == "headers":
        def changed(*args,**kw):
            cfg.active_profile_id = "foreign"
            response.status_code = 403
            return response
        request.side_effect = changed
    else:
        def chunks(**kw):
            cfg.active_profile_id = "foreign"
            yield b"{}"
        response.iter_content.side_effect = chunks
    with pytest.raises(SessionError,match="context_changed"):
        client.delete_history(original,"old-session","opaque",OP,confirmed=True)
    assert request.call_count == (0 if stage == "before" else 1)


def test_timeout_never_replayed_and_errors_content_free(wire):
    client, _, request, _ = wire
    request.side_effect = requests.Timeout("private credentials")
    with pytest.raises(SessionError,match="^uncertain$"): delete(client)
    request.assert_called_once()


def intent(client, **kw):
    args = {"session_id":"old-session","admitted_until":NOW+600,"now":NOW,"confirmed":True}
    args.update(kw)
    return consent.SingleDeleteIntent.confirmed(client.binding(),7,DETAIL,CAPS,**args)


def test_intent_contains_no_body_and_claim_is_one_shot_under_concurrency(wire):
    client, _, _, _ = wire
    prepared = intent(client)
    assert prepared.expires_at == NOW+300
    def claim():
        try: return prepared.claim(client.binding(),7,CAPS,now=NOW)
        except SessionError: return None
    with ThreadPoolExecutor(max_workers=8) as executor: results = list(executor.map(lambda _:claim(),range(16)))
    assert sum(result is not None for result in results) == 1
    body = next(result for result in results if result is not None)
    assert body == {"session_id":"old-session","expected_revision":"opaque:exact:revision","operation_id":OP,"confirmed":True}
    assert "opaque" not in repr(prepared) and "synthetic-token" not in repr(prepared)


@pytest.mark.parametrize("value", [False,1,None,"true"])
def test_confirmation_must_be_explicit_bool(wire,value):
    client, _, request, _ = wire
    with pytest.raises(SessionError,match="invalid"): intent(client,confirmed=value)
    request.assert_not_called()


@pytest.mark.parametrize("caps", [{},None,{"capabilities":True},
    {"capabilities":{"session_history_delete":1},"contract_versions":{"session_history_delete":1}},
    {"capabilities":{"session_history_delete":True},"contract_versions":{"session_history_delete":True}},
    {"capabilities":{"session_history_delete":True},"contract_versions":{"session_history_delete":2}}])
def test_capability_missing_or_unreleased_hides_consumer(wire,caps):
    client, _, _, _ = wire
    assert not consent.single_delete_supported(caps)
    with pytest.raises(SessionError): consent.SingleDeleteIntent.confirmed(client.binding(),7,DETAIL,caps,session_id="old-session",admitted_until=NOW+600,now=NOW,confirmed=True)


@pytest.mark.parametrize("revision", [0,True,None,"",[],{}])
def test_list_revisions_never_become_detail_cas(wire,revision):
    client, _, _, _ = wire
    detail={**DETAIL,"session":{**DETAIL["session"],"revision":revision}}
    with pytest.raises(SessionError): consent.SingleDeleteIntent.confirmed(client.binding(),7,detail,CAPS,session_id="old-session",admitted_until=NOW+600,now=NOW,confirmed=True)


@pytest.mark.parametrize("status", ["OPENING","ACTIVE",None,[],{}])
def test_nonterminal_detail_never_mints_operation(wire,status,monkeypatch):
    client, _, _, _ = wire
    maker=Mock(side_effect=AssertionError("No UUID before admissible confirmation"))
    monkeypatch.setattr(consent,"operation_id",maker)
    with pytest.raises(SessionError): consent.SingleDeleteIntent.confirmed(client.binding(),7,{**DETAIL,"session":{**DETAIL["session"],"lifecycle_status":status}},CAPS,session_id="old-session",admitted_until=NOW+600,now=NOW,confirmed=True)
    maker.assert_not_called()


@pytest.mark.parametrize("deadline", [None,True,0,NOW,float("inf"),float("nan")])
def test_no_known_original_retention_means_no_consent(wire,deadline):
    client, _, _, _ = wire
    with pytest.raises(SessionError): intent(client,admitted_until=deadline)


@pytest.mark.parametrize("change", ["profile","token","epoch","caps","expired","retention","rollback"])
def test_original_authority_deadline_and_epoch_before_claim(wire,change):
    client, _, _, _ = wire
    prepared=intent(client,admitted_until=NOW+10 if change=="retention" else NOW+600)
    binding,epoch,caps,now=client.binding(),7,CAPS,NOW
    if change=="profile": binding=replace(binding,resolved_profile_id="foreign")
    if change=="token": binding=replace(binding,token="new-token")
    if change=="epoch": epoch=8
    if change=="caps": caps={}
    if change=="expired": now=NOW+300
    if change=="retention": now=NOW+10
    if change=="rollback": now=NOW-31
    with pytest.raises(SessionError): prepared.claim(binding,epoch,caps,now=now)
    assert not prepared._claimed


def test_claimed_timeout_cannot_be_rearmed_by_refresh_or_new_confirmation_flag(wire):
    client, _, request, _ = wire
    prepared=intent(client)
    args=prepared.claim(client.binding(),7,CAPS,now=NOW)
    request.side_effect=requests.Timeout()
    with pytest.raises(SessionError): client.delete_history(client.binding(),**args)
    with pytest.raises(SessionError,match="uncertain"): prepared.claim(client.binding(),7,CAPS,now=NOW+1)
    request.assert_called_once()


@pytest.mark.parametrize("method,route,payload", [("GET","session/history/delete",{}),
    ("POST","session/start",{}),("POST","command",{}),("POST","session/history/delete",{"profile_id":"foreign"}),
    ("POST","session/history/delete",None)])
def test_special_decoder_cannot_be_selected_for_another_route_or_payload(wire,method,route,payload):
    client,_,request,_=wire
    with pytest.raises(SessionError,match="invalid"):
        client._request(client.binding(),method,route,payload,archive_delete=True)
    request.assert_not_called()


@pytest.mark.parametrize("status",["ENDED","INTERRUPTED"])
def test_terminal_consent_binds_exact_header_revision_not_page_revision(wire,status):
    client,_,_,_=wire
    detail={**DETAIL,"revision":"different-page-revision", "session":{**DETAIL["session"],"lifecycle_status":status}}
    prepared=consent.SingleDeleteIntent.confirmed(client.binding(),7,detail,CAPS,session_id="old-session",admitted_until=NOW+600,now=NOW,confirmed=True)
    assert prepared.revision=="opaque:exact:revision"


@pytest.mark.parametrize("mode",["public","private","private_ephemeral"])
def test_erasure_not_blocked_by_recording_or_display_privacy_mode(wire,mode):
    client,cfg,_,_=wire
    cfg.active_profile_privacy_mode=mode
    assert intent(client).session_id=="old-session"


def test_conservative_clock_does_not_extend_original_operation_or_retention(wire):
    from djconnect_pi.expiry_clock import ExpiryClock
    client,_,_,_=wire
    wall,tick=[NOW],[0.0]
    clock=ExpiryClock(wall=lambda:wall[0],elapsed=lambda:tick[0])
    prepared=intent(client)
    tick[0],wall[0]=301,NOW-1000
    with pytest.raises(SessionError,match="unavailable"):
        prepared.claim(client.binding(),7,CAPS,now=clock.now())
    assert prepared.expires_at==NOW+300


@pytest.mark.parametrize("selected", ["another-session", "active-session", "new-selection"])
def test_fresh_detail_cannot_retarget_original_confirmation(wire, selected):
    client, _, request, _ = wire
    with pytest.raises(SessionError, match="context_changed"):
        intent(client, session_id=selected)
    request.assert_not_called()
