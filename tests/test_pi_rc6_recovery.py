from __future__ import annotations

import base64
import hashlib
import io
import json
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

pytest.importorskip("jsonschema", reason="Dedicated locked deployment-tool suite")
from test_pi_instance_authority import CONSUMER, Client

from Tools import pi_instance_release as release
from Tools import pi_rc6_recovery as recovery
from Tools import pi_wall4_recovery_release as closed
from Tools.pi_instance_authority import resolve
from Tools.pi_instance_contract import (
    BindingError,
    recovered_deployment,
    validate_smoke_join,
)

RUN = "50000000000"
BOOT = "01234567-89ab-cdef-0123-456789abcdef"


def authority_fixture():
    client=Client();old=resolve(client,client.request,CONSUMER,client.configuration)
    from dataclasses import replace
    from types import MappingProxyType
    request={**dict(old.binding.request),"candidate_sha":recovery.SOURCE,"artifact_sha256":recovery.ARTIFACT_SHA256,"manifest_id":"reviewed-recovery-binding"}
    return replace(old,binding=replace(old.binding,request=MappingProxyType(request),smoke_contract="pi-rc6-wall4-recovery-readback-v1"))


class RecoveryClient:
    def __init__(self):
        self.calls=[]
        self.run={"id":int(recovery.ORIGINAL_RUN),"head_sha":recovery.SOURCE,"head_branch":"main",
            "event":"workflow_dispatch","path":release.WORKFLOWS["deploy"],"status":"completed",
            "conclusion":"failure","run_attempt":1,"actor":{"login":"pcvantol"}}
        self.artifacts={"total_count":1,"artifacts":[{"id":1,"name":"pi-deployment-evidence-wall-4inch","expired":False,"size_in_bytes":1000}]}
        self.receipt={"result":"DEPLOYMENT_INCONCLUSIVE","workflow_run_id":recovery.ORIGINAL_RUN,
            "candidate_sha":recovery.SOURCE,"consumer_sha":recovery.SOURCE,"deployment_instance":"wall-4inch",
            "device_profile":recovery.PROFILE,"artifact_sha256":recovery.ARTIFACT_SHA256,
            "manifest_id":recovery.ORIGINAL_MANIFEST,"operational_core_sha":recovery.ORIGINAL_CORE,
            "operational_manifest_sha256":recovery.ORIGINAL_MANIFEST_SHA256,"intent_dispatched":True,"remote_may_still_be_running":True}
        self.mutations={"deploy":[],"recover":[{"id":int(RUN),"head_sha":CONSUMER,"head_branch":"main",
            "event":"workflow_dispatch","path":recovery.WORKFLOW,"display_title":"Pi recovery / wall-4inch / reviewed-recovery-binding",
            "status":"in_progress","run_attempt":1,"actor":{"login":"pcvantol"},"updated_at":"2026-10-21T21:00:00Z"}]}
        self.zip_case=""

    def json(self,path):
        self.calls.append(path)
        if "/workflows/deploy-latest" in path:return {"workflow_runs":self.mutations["deploy"],"total_count":len(self.mutations["deploy"])}
        if "/workflows/recover-rc6" in path:return {"workflow_runs":self.mutations["recover"],"total_count":len(self.mutations["recover"])}
        if path.endswith("/artifacts?per_page=100"):return self.artifacts
        if path.endswith("/actions/runs/"+recovery.ORIGINAL_RUN):return self.run
        raise AssertionError(path)

    def archive(self,identifier):
        import zipfile
        assert identifier==1
        if self.zip_case=="malformed":return b"not a zip"
        out=io.BytesIO()
        with zipfile.ZipFile(out,"w") as archive:
            archive.writestr("other.json" if self.zip_case=="name" else "pi-deploy-evidence.json",json.dumps(self.receipt))
            if self.zip_case=="extra":archive.writestr("extra",b"no")
        return out.getvalue()


def test_original_failed_run_is_evidence_not_a_success_or_retry():
    client=RecoveryClient();original=deepcopy(client.receipt)
    assert recovery.original_failure(client)==original
    assert client.receipt==original


@pytest.mark.parametrize("field,value",[("id",1),("head_sha","a"*40),("head_branch","feature"),("event","push"),
    ("path","other.yml"),("status","in_progress"),("conclusion","success"),("run_attempt",2),("run_attempt",True),("actor",{"login":"other"})])
def test_original_run_must_be_exact_completed_first_failed_mutation(field,value):
    client=RecoveryClient();client.run[field]=value
    with pytest.raises(BindingError):recovery.original_failure(client)
    assert not any("/artifacts" in p for p in client.calls)


@pytest.mark.parametrize("field,value",[("result","DEPLOYED_PENDING_SMOKE"),("workflow_run_id","other"),("candidate_sha","a"*40),
    ("consumer_sha","b"*40),("deployment_instance","wall-10inch"),("device_profile","pi5-arm64"),
    ("artifact_sha256","f"*64),("manifest_id","other"),("operational_core_sha","e"*40),
    ("operational_manifest_sha256","f"*64),("intent_dispatched",1),("intent_dispatched",False),("remote_may_still_be_running",False)])
def test_original_receipt_cannot_be_rebound_or_promoted(field,value):
    client=RecoveryClient();client.receipt[field]=value
    with pytest.raises(BindingError):recovery.original_failure(client)


@pytest.mark.parametrize("case",["missing","duplicate","expired","oversize","incomplete","name","extra","malformed"])
def test_missing_or_changed_original_artifact_never_invents_evidence(case):
    client=RecoveryClient()
    if case=="missing":client.artifacts={"artifacts":[],"total_count":0}
    elif case=="duplicate":client.artifacts["artifacts"]*=2;client.artifacts["total_count"]=2
    elif case=="expired":client.artifacts["artifacts"][0]["expired"]=True
    elif case=="oversize":client.artifacts["artifacts"][0]["size_in_bytes"]=262145
    elif case=="incomplete":client.artifacts["total_count"]=101
    else:client.zip_case=case
    with pytest.raises(BindingError):recovery.original_failure(client)


def test_recovery_requires_new_consumer_and_separate_operative_binding():
    authority=authority_fixture();recovery.selected(authority)
    for key,value in [("deployment_instance","wall-10inch"),("device_profile","pi5-arm64"),("candidate_sha","a"*40),("artifact_sha256","f"*64)]:
        request={**dict(authority.binding.request),key:value}
        wrong=SimpleNamespace(binding=SimpleNamespace(request=request,consumer_sha=CONSUMER),operational_core_sha=authority.operational_core_sha)
        with pytest.raises(BindingError):recovery.selected(wrong)
    wrong=SimpleNamespace(binding=SimpleNamespace(request=authority.binding.request,consumer_sha=recovery.SOURCE),operational_core_sha=authority.operational_core_sha)
    with pytest.raises(BindingError):recovery.selected(wrong)
    wrong=SimpleNamespace(binding=authority.binding,operational_core_sha=recovery.ORIGINAL_CORE)
    with pytest.raises(BindingError):recovery.selected(wrong)


def test_exact_helper_pin_matches_checked_source_and_remote_constant():
    from pathlib import Path
    raw=Path(recovery.__file__).with_name("pi_rc6_recovery_root.py").read_bytes()
    assert hashlib.sha256(raw).hexdigest()==recovery.HELPER_SHA256
    assert base64.b64decode(recovery.helper_bytes())==raw
    remote=Path(release.__file__).with_name("pi_instance_remote_payload.py").read_text()
    assert recovery.HELPER_SHA256 in remote
    contract=Path(release.__file__).with_name("pi_instance_contract.py").read_text()
    assert recovery.HELPER_SHA256 in contract


def test_own_current_intent_is_latest_and_not_a_hidden_retry():
    client=RecoveryClient();recovery.current_intent(client,RUN,authority_fixture())


@pytest.mark.parametrize("case",["later-deploy","later-recovery","old-updated-after","attempt2","queued","wrong-consumer","wrong-manifest","other-actor","wrong-path"])
def test_newer_or_changed_physical_intent_withdraws_recovery(case):
    client=RecoveryClient();current=client.mutations["recover"][0]
    if case.startswith("later-") or case=="old-updated-after":
        row={**current,"id":int(RUN)+1,"updated_at":"2026-10-21T22:00:00Z","status":"queued"}
        if case=="later-deploy":
            row.update(path=release.WORKFLOWS["deploy"],display_title="Pi deploy / wall-4inch / other")
            client.mutations["deploy"].append(row)
        else:
            if case=="old-updated-after":row.update(id=int(RUN)-1,status="completed")
            client.mutations["recover"].append(row)
    elif case=="attempt2":current["run_attempt"]=2
    elif case=="queued":current["status"]="queued"
    elif case=="wrong-consumer":current["head_sha"]="f"*40
    elif case=="wrong-manifest":current["display_title"]+="-other"
    elif case=="other-actor":current["actor"]={"login":"other"}
    elif case=="wrong-path":current["path"]="other.yml"
    with pytest.raises(BindingError):recovery.current_intent(client,RUN,authority_fixture())


def test_pi10_independent_intent_is_not_a_wall4_recovery_or_reinstall():
    client=RecoveryClient();row={**client.mutations["recover"][0],"id":int(RUN)+100,"path":release.WORKFLOWS["deploy"],"display_title":"Pi deploy / wall-10inch / other"}
    client.mutations["deploy"].append(row)
    recovery.current_intent(client,RUN,authority_fixture())


def recovery_receipt(authority):
    return {**authority.receipt(),"kind":"djconnect_pi_recovery_evidence","result":"RECOVERED_PENDING_SMOKE",
        "deployment_workflow_run":RUN,"recovery_workflow_run":RUN,"original_deployment_workflow_run":recovery.ORIGINAL_RUN,
        "watchdog_restored":True,"configuration_preserved_by_installer":True,"verified_packaged_files":80,
        "recovery_helper_sha256":recovery.HELPER_SHA256}


def test_generic_v3_smoke_cannot_accept_recovery_receipt():
    authority=authority_fixture();receipt=recovery_receipt(authority)
    run={"head_sha":CONSUMER,"head_branch":"main","path":recovery.WORKFLOW,"event":"workflow_dispatch",
        "status":"completed","conclusion":"success","run_attempt":1,"actor":{"login":"pcvantol"}}
    with pytest.raises(BindingError):
        release.deployment_record(SimpleNamespace(json=lambda _:run),authority.binding,authority,receipt,RUN)
    smoke={**authority.binding.public_join(),"result":"SMOKE_PASS","deployment_workflow_run":RUN,
        "installed_source":recovery.SOURCE,"installed_version":"4.0.0-rc.6","installed_device_profile":recovery.PROFILE,
        "api_reachable":True,"client_active":True,"api_active":True}
    with pytest.raises(BindingError):validate_smoke_join(authority.binding,receipt,smoke,RUN)
    assert receipt["result"]=="RECOVERED_PENDING_SMOKE"  # Never rewrite the original failed record.


@pytest.mark.parametrize("field,value",[("result","DEPLOYMENT_INCONCLUSIVE"),("kind","other"),("original_deployment_workflow_run","other"),
    ("watchdog_restored",1),("watchdog_restored",False),("configuration_preserved_by_installer",False),
    ("verified_packaged_files",True),("verified_packaged_files",79),("recovery_helper_sha256","f"*64),("recovery_workflow_run","other")])
def test_partial_or_forged_recovery_cannot_be_a_matching_success(field,value):
    authority=authority_fixture();receipt=recovery_receipt(authority);receipt[field]=value
    assert not recovered_deployment(authority.binding,receipt,RUN)


def test_recovery_context_is_one_new_main_attempt_not_old_deployment(monkeypatch):
    environment={"GITHUB_ACTIONS":"true","GITHUB_REPOSITORY":release.PI,"GITHUB_SHA":CONSUMER,"GITHUB_RUN_ID":RUN,"GITHUB_RUN_ATTEMPT":"1"}
    run={"id":int(RUN),"run_attempt":1,"head_sha":CONSUMER,"head_branch":"main","path":recovery.WORKFLOW,"event":"workflow_dispatch","status":"in_progress","actor":{"login":"pcvantol"},"repository":{"full_name":release.PI}}
    monkeypatch.setattr(release.subprocess,"run",Mock(return_value=SimpleNamespace(stdout=CONSUMER+"\n")))
    client=SimpleNamespace(json=lambda _:run)
    assert closed.workflow_context(client,"recover",environment)==(CONSUMER,RUN)
    environment["GITHUB_RUN_ATTEMPT"]="2"
    with pytest.raises(BindingError):closed.workflow_context(client,"recover",environment)
    environment["GITHUB_RUN_ATTEMPT"]="1";run["path"]=release.WORKFLOWS["deploy"]
    with pytest.raises(BindingError):closed.workflow_context(client,"recover",environment)


@pytest.mark.parametrize("lost",[False,True])
def test_executor_sends_one_bound_recovery_intent_and_never_replays(monkeypatch,lost):
    from test_pi_wall4_recovery_contract import authority as fixture
    authority=fixture();client=RecoveryClient();calls=[]
    monkeypatch.setattr(closed,"current_intent",lambda *_:None)
    monkeypatch.setattr(closed,"verified_artifact",lambda *_:b"synthetic previously hash-qualified artifact")
    monkeypatch.setattr(closed,"inspect_artifact",lambda *_:SimpleNamespace(wheel_name="djconnect_pi-4.0.0rc6-py3-none-any.whl",wheel_sha256="f"*64))
    monkeypatch.setattr(closed.authority_module,"current",lambda *_:None)
    class Channel:
        sent=False
        recovery_boot_id=BOOT
        def __init__(self,binding,*,recovery,recovery_smoke):assert recovery is True and recovery_smoke is False
        def __enter__(self):return self
        def __exit__(self,*_):pass
        def intent(self,payload,**kwargs):
            self.sent=True;calls.append(payload)
            assert payload["phase"]=="recover" and payload["recovery_boot_id"]==BOOT and "artifact" not in payload
            assert hashlib.sha256(base64.b64decode(payload["recovery_helper"])).hexdigest()==recovery.HELPER_SHA256
            if lost:raise BrokenPipeError("synthetic private error")
            return {"result":"RECOVERED_PENDING_SMOKE","configuration_preserved_by_installer":True,"watchdog_restored":True,
                "verified_packaged_files":80,"original_deployment_workflow_run":recovery.ORIGINAL_RUN,
                "recovery_observation":{"boot_id":BOOT,"configuration_sha256":"d"*64},
                "services":{"djconnect-api.service":{"active":True,"pid":200},"djconnect-client.service":{"active":True,"pid":201}}}
    monkeypatch.setattr(closed,"Channel",Channel)
    if lost:
        with pytest.raises(release.PhaseFailure) as failed:closed.execute(client,authority,"recover",RUN)
        assert failed.value.record["result"]=="RECOVERY_INCONCLUSIVE" and failed.value.record["intent_dispatched"] is True
        assert failed.value.record["remote_may_still_be_running"] is True
        assert "private error" not in str(failed.value.record)
    else:
        receipt=closed.execute(client,authority,"recover",RUN)
        assert receipt["result"]=="RECOVERED_PENDING_SMOKE" and receipt["recovery_workflow_run"]==RUN
        assert receipt["original_deployment_workflow_run"]==recovery.ORIGINAL_RUN
    assert len(calls)==1
