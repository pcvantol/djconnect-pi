from __future__ import annotations

import base64
from copy import deepcopy
from types import SimpleNamespace

import pytest

pytest.importorskip("jsonschema", reason="Dedicated locked deployment-tool suite")
from test_pi_instance_authority import CONSUMER
from test_pi_wall4_recovery_contract import authority, fixtures

from Tools import pi_instance_aggregate as aggregate
from Tools import pi_instance_release as ordinary
from Tools import pi_wall4_recovery_release as release
from Tools.pi_instance_contract import BindingError

RUN = "50000000000"
PRIOR = "49999999999"
BOOT = "01234567-89ab-cdef-0123-456789abcdef"
OBS = {"boot_id":BOOT,"configuration_sha256":"d"*64}
SERVICES = {"djconnect-api.service":{"active":True,"pid":200},"djconnect-client.service":{"active":True,"pid":201}}


def row(operation="recover", run=RUN):
    return {"id":int(run),"head_sha":CONSUMER,"head_branch":"main","event":"workflow_dispatch",
        "status":"in_progress","path":release.WORKFLOWS[operation],"run_attempt":1,"actor":{"login":"pcvantol"},
        "repository":{"full_name":release.PI},"updated_at":"2026-10-21T23:00:00Z",
        "display_title":("Pi recovery / wall-4inch / " if operation=="recover" else "Pi recovery smoke / wall-4inch / ")+fixtures()[0]["manifest_id"]}


class Client:
    def __init__(self, operation="recover"):
        self.rows = {filename:[] for filename in ("deploy-latest-pi-release.yml", "smoke-rbpi-djconnect.yml", "recover-rc6-wall4.yml", "smoke-rc6-wall4-recovery.yml")}
        self.rows[release.WORKFLOWS[operation].split("/")[-1]]=[row(operation)]
        self.prior={**row("recover",PRIOR),"status":"completed","conclusion":"success"}
    def json(self, path):
        if "/workflows/" in path:
            rows=self.rows[path.split("/workflows/")[1].split("/")[0]]
            return {"workflow_runs":rows,"total_count":len(rows)}
        if path.endswith("/"+PRIOR):return self.prior
        if path.endswith("/"+RUN):return next(rows[0] for rows in self.rows.values() if rows)
        raise AssertionError(path)


def receipt():
    return {**authority().receipt(),"schema_version":1,"kind":"djconnect_pi_wall4_recovery_evidence",
        "result":"RECOVERED_PENDING_SMOKE","workflow_run_id":PRIOR,"recovery_workflow_run":PRIOR,
        "original_deployment_workflow_run":release.component.ORIGINAL_RUN,
        "recovery_helper_sha256":release.component.HELPER_SHA256,"observer_sha256":release.OBSERVER_SHA256,
        "watchdog_restored":True,"configuration_preserved_by_installer":True,"verified_packaged_files":80,
        "recovery_observation":dict(OBS)}


@pytest.mark.parametrize("operation",["recover","smoke"])
def test_all_four_current_intent_lists_and_exact_workflow(operation):
    client=Client(operation);release.current_intent(client,RUN,authority(),operation)


@pytest.mark.parametrize("workflow,prefix",[("deploy-latest-pi-release.yml","Pi deploy / wall-4inch / "),
    ("smoke-rbpi-djconnect.yml","Pi smoke / wall-4inch / "),("recover-rc6-wall4.yml","Pi recovery / wall-4inch / "),
    ("smoke-rc6-wall4-recovery.yml","Pi recovery smoke / wall-4inch / ")])
@pytest.mark.parametrize("operation",["recover","smoke"])
def test_newer_even_queued_deploy_recovery_or_smoke_withdraws_intent(workflow,prefix,operation):
    c=Client(operation);c.rows[workflow].append({**row(),"id":int(RUN)+1,"path":".github/workflows/"+workflow,"display_title":prefix+"OTHER","status":"queued"})
    with pytest.raises(BindingError,match="SUPERSEDED"):release.current_intent(c,RUN,authority(),operation)


@pytest.mark.parametrize("field,value",[("id",1),("head_sha","e"*40),("status","queued"),("run_attempt",2),
    ("run_attempt",True),("path","other.yml"),("actor",{"login":"other"}),("updated_at","2026-10-21T23:00:00")])
def test_mutated_or_rerun_intent_is_not_an_execution_grant(field,value):
    c=Client();c.rows["recover-rc6-wall4.yml"][0][field]=value
    with pytest.raises(BindingError):release.current_intent(c,RUN,authority(),"recover")


def test_recovery_smoke_matches_producer_consumer_helper_boot_and_config():
    assert release.recovery_record(Client(),authority(),PRIOR,receipt())==OBS


@pytest.mark.parametrize("field,value",[("result","SMOKE_PASS"),("consumer_sha","e"*40),("operational_core_sha","e"*40),
    ("operational_manifest_sha256","f"*64),("manifest_id","other"),("original_deployment_workflow_run","other"),
    ("recovery_workflow_run","other"),("workflow_run_id","other"),("recovery_helper_sha256","e"*64),
    ("observer_sha256","e"*64),("watchdog_restored",1),("configuration_preserved_by_installer",False),
    ("verified_packaged_files",True),("verified_packaged_files",79),("schema_version",True),
    ("recovery_observation",{"boot_id":BOOT,"configuration_sha256":"bad"})])
def test_old_partial_or_cross_consumer_receipt_never_qualifies(field,value):
    record=receipt();record[field]=value
    with pytest.raises(BindingError):release.recovery_record(Client(),authority(),PRIOR,record)


@pytest.mark.parametrize("field,value",[("head_sha","e"*40),("status","in_progress"),("conclusion","failure"),
    ("run_attempt",2),("path",ordinary.WORKFLOWS["deploy"]),("actor",{"login":"other"})])
def test_smoke_requires_actual_completed_successful_dedicated_first_attempt(field,value):
    c=Client();c.prior[field]=value
    with pytest.raises(BindingError):release.recovery_record(c,authority(),PRIOR,receipt())


@pytest.mark.parametrize("operation",["recover","smoke"])
@pytest.mark.parametrize("lost",[False,True])
def test_one_intent_explicit_smoke_and_uncertainty_no_replay(monkeypatch,operation,lost):
    c=Client(operation);a=authority();calls=[]
    monkeypatch.setattr(release.component,"original_failure",lambda *_:None)
    monkeypatch.setattr(release,"verified_artifact",lambda *_:b"synthetic")
    monkeypatch.setattr(release,"inspect_artifact",lambda *_:SimpleNamespace(wheel_name="djconnect_pi-4.0.0rc6-py3-none-any.whl",wheel_sha256="f"*64))
    monkeypatch.setattr(release.authority_module,"current",lambda *_:None)
    monkeypatch.setattr(release,"download_recovery",lambda *_:receipt())
    class Channel:
        sent=False;recovery_boot_id=BOOT
        def __init__(self,binding,**kwargs):assert kwargs=={"recovery":operation=="recover","recovery_smoke":operation=="smoke"}
        def __enter__(self):return self
        def __exit__(self,*_):pass
        def intent(self,payload,**kwargs):
            self.sent=True;calls.append(deepcopy(payload))
            assert "artifact" not in payload and payload["recovery_boot_id"]==BOOT
            assert base64.b64decode(payload["recovery_observer"])==release.Path(release.__file__).with_name("pi_wall4_recovery_observer.py").read_bytes()
            if operation=="recover":assert "recovery_helper" in payload
            else:assert payload["recovery_observation"]==OBS and "recovery_helper" not in payload
            if lost:raise BrokenPipeError("private synthetic message")
            if operation=="recover":return {"result":"RECOVERED_PENDING_SMOKE","configuration_preserved_by_installer":True,"watchdog_restored":True,"verified_packaged_files":80,"original_deployment_workflow_run":release.component.ORIGINAL_RUN,"services":SERVICES,"recovery_observation":OBS}
            return {"result":"SMOKE_PASS","installed_source":release.component.SOURCE,"installed_version":a.binding.version,"installed_device_profile":release.component.PROFILE,"api_reachable":True,"client_active":True,"api_active":True,"paired":True,"verified_packaged_files":80,"services":SERVICES,"recovery_observation":OBS}
    monkeypatch.setattr(release,"Channel",Channel)
    if lost:
        with pytest.raises(release.PhaseFailure) as failure:release.execute(c,a,operation,RUN,PRIOR if operation=="smoke" else "")
        assert failure.value.record["intent_dispatched"] is True
        assert failure.value.record["remote_may_still_be_running"] is (operation=="recover")
        assert "private synthetic" not in str(failure.value.record)
    else:
        result=release.execute(c,a,operation,RUN,PRIOR if operation=="smoke" else "")
        assert result["result"]==("RECOVERED_PENDING_SMOKE" if operation=="recover" else "SMOKE_PASS")
        assert result["aggregate_disposition"]=="SINGLE_INSTANCE_RECOVERY_ONLY"
        assert "DEPLOYMENT_OPERATIONAL" not in str(result)
    assert len(calls)==1


def test_ordinary_v3_cli_and_aggregate_reject_new_recovery_authority_before_effects(monkeypatch):
    c=SimpleNamespace(json=lambda _:pytest.fail("no network/effects"))
    with pytest.raises(BindingError):ordinary.selected_request(fixtures()[0],"recover")
    with pytest.raises(BindingError):aggregate.aggregate(c,authority(),{})
    with pytest.raises(ordinary.PhaseFailure) as failed:ordinary.execute(c,authority(),"readiness",RUN)
    assert failed.value.record["intent_dispatched"] is False


@pytest.mark.parametrize("case",["oldpath","attempt2","wrongconsumer","wrongrepo","wrongactor"])
def test_trusted_dedicated_context_is_mandatory_before_authority_resolution(monkeypatch,case):
    c=Client();env={"GITHUB_ACTIONS":"true","GITHUB_REPOSITORY":release.PI,"GITHUB_SHA":CONSUMER,"GITHUB_RUN_ID":RUN,"GITHUB_RUN_ATTEMPT":"1"}
    monkeypatch.setattr(release.subprocess,"run",lambda *_args,**_kw:SimpleNamespace(stdout=CONSUMER+"\n"))
    if case=="oldpath":c.rows["recover-rc6-wall4.yml"][0]["path"]=ordinary.WORKFLOWS["deploy"]
    elif case=="attempt2":env["GITHUB_RUN_ATTEMPT"]="2"
    elif case=="wrongconsumer":c.rows["recover-rc6-wall4.yml"][0]["head_sha"]="f"*40
    elif case=="wrongrepo":env["GITHUB_REPOSITORY"]="other/repo"
    else:c.rows["recover-rc6-wall4.yml"][0]["actor"]={"login":"other"}
    with pytest.raises(BindingError):release.workflow_context(c,"recover",env)
