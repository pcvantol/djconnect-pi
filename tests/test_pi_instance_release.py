from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

pytest.importorskip("jsonschema", reason="Dedicated locked deployment-tool suite")
from test_pi_instance_authority import CONSUMER, Client

from Tools import pi_instance_release as wire
from Tools.pi_instance_authority import resolve


@pytest.mark.parametrize("operation", ["readiness", "deploy", "smoke"])
def test_typed_phase_preserves_original_deployment_binding(operation):
    request = dict(Client().request)
    if operation == "smoke":request.update(action="deployment_smoke", deployment_workflow_run="321")
    selected, run = wire.selected_request(request, operation)
    assert selected["action"] == "deployment" and (run == "321") == (operation == "smoke")


@pytest.mark.parametrize("case", ["unknown", "missing", "free-host", "smoke-wrong-action", "bad-run"])
def test_phase_overrides_and_unknown_fields_cannot_open_a_route(case):
    request = dict(Client().request);operation = "deploy"
    if case == "unknown":operation = "other"
    if case == "missing":del request["device_profile"]
    if case == "free-host":request["host"] = "private-endpoint"
    if case == "smoke-wrong-action":operation = "smoke";request["deployment_workflow_run"] = "321"
    if case == "bad-run":operation = "smoke";request.update(action="deployment_smoke", deployment_workflow_run="321\n")
    with pytest.raises(wire.BindingError):wire.selected_request(request, operation)


@pytest.fixture
def context(monkeypatch):
    environment = {"GITHUB_ACTIONS": "true", "GITHUB_REPOSITORY": wire.PI, "GITHUB_SHA": CONSUMER,
        "GITHUB_RUN_ID": "456", "GITHUB_RUN_ATTEMPT": "1"}
    run = {"head_sha": CONSUMER, "head_branch": "main", "path": wire.WORKFLOWS["deploy"], "event": "workflow_dispatch",
        "status": "in_progress", "actor": {"login": "pcvantol"}, "repository": {"full_name": wire.PI}}
    client = SimpleNamespace(json=Mock(return_value=run))
    monkeypatch.setattr(wire.subprocess, "run", Mock(return_value=SimpleNamespace(stdout=CONSUMER+"\n")))
    return environment, run, client


def test_only_exact_running_qualified_workflow_can_enter(context):
    environment, _run, client = context
    assert wire.workflow_context(client, "deploy", environment) == (CONSUMER, "456")


@pytest.mark.parametrize("field,value", [("head_sha", "f"*40), ("head_branch", "feature"), ("path", "other.yml"),
    ("event", "push"), ("status", "completed"), ("actor", {"login": "other"})])
def test_wrong_workflow_context_cannot_dispatch(context, field, value):
    environment, run, client = context;run[field] = value
    with pytest.raises(wire.BindingError):wire.workflow_context(client, "deploy", environment)


def test_automatic_or_manual_rerun_requires_actual_state_review(context):
    environment, _run, client = context;environment["GITHUB_RUN_ATTEMPT"] = "2"
    with pytest.raises(wire.BindingError, match="RERUN_REQUIRES_ACTUAL_STATE_REVIEW"):wire.workflow_context(client, "deploy", environment)


def test_changed_operational_approval_stops_before_intent(monkeypatch):
    client = Client();authority = resolve(client, client.request, CONSUMER, client.configuration)
    session = SimpleNamespace(intent=Mock(side_effect=AssertionError("No dispatched intent")))
    class Channel:
        def __init__(self, binding):pass
        def __enter__(self):return session
        def __exit__(self, *args):pass
    monkeypatch.setattr(wire, "Channel", Channel)
    monkeypatch.setattr(wire, "current_authority", Mock(side_effect=wire.BindingError("SUPERSEDED")))
    with pytest.raises(wire.PhaseFailure) as failure:wire.execute(client, authority, "readiness", "456")
    assert failure.value.record["intent_dispatched"] is False
    session.intent.assert_not_called()


def test_smoke_requires_successful_matching_deployment_before_ssh(monkeypatch):
    client = Client();authority = resolve(client, client.request, CONSUMER, client.configuration)
    channel = Mock(side_effect=AssertionError("No SSH"));monkeypatch.setattr(wire, "Channel", channel)
    with pytest.raises(wire.BindingError):wire.execute(client, authority, "smoke", "456", deployment={}, deployment_run="321")
    channel.assert_not_called()


@pytest.mark.parametrize("operation", ["deploy", "smoke"])
def test_complete_executor_has_one_bound_intent_and_readonly_smoke(monkeypatch, operation):
    import hashlib

    from test_pi_instance_artifact import package
    client = Client();body = package();digest = hashlib.sha256(body).hexdigest();client.bodies[2] = body
    client.request["artifact_sha256"] = digest;client.manifest["artifact_bindings"][0]["artifact_sha256"] = digest
    client.published["artifacts"]["pi-zero-2w-arm64"]["artifact_sha256"] = digest
    authority = resolve(client, client.request, CONSUMER, client.configuration);calls = []
    original_json = client.json
    def json_read(path):
        if path.endswith("/actions/runs/321"):
            return {"head_sha": CONSUMER, "head_branch": "main", "path": wire.WORKFLOWS["deploy"], "event": "workflow_dispatch",
                "status": "completed", "conclusion": "success", "actor": {"login": "pcvantol"}}
        return original_json(path)
    client.json = json_read
    class Channel:
        def __init__(self, binding):pass
        def __enter__(self):return self
        def __exit__(self, *args):pass
        def intent(self, payload, **kwargs):
            calls.append(payload)
            services = {"djconnect-api.service": {"active": True, "pid": 12}, "djconnect-client.service": {"active": True, "pid": 13}}
            if operation == "deploy":
                assert "artifact" in payload
                return {"result": "DEPLOYED_PENDING_SMOKE", "configuration_preserved_by_installer": True, "services": services}
            assert "artifact" not in payload
            return {"result": "SMOKE_PASS", "installed_source": client.request["candidate_sha"], "installed_version": authority.binding.version,
                "installed_device_profile": client.request["device_profile"], "api_reachable": True, "client_active": True, "api_active": True,
                "paired": False, "services": services, "verified_packaged_files": 65}
    monkeypatch.setattr(wire, "Channel", Channel)
    deployment = {**authority.receipt(), "result": "DEPLOYED_PENDING_SMOKE", "deployment_workflow_run": "321"}
    result = wire.execute(client, authority, operation, "456", deployment=deployment, deployment_run="321")
    assert len(calls) == 1 and result["result"] == ("SMOKE_PASS" if operation == "smoke" else "DEPLOYED_PENDING_SMOKE")
    assert client.effects == 0


def test_lost_installer_ack_records_uncertainty_without_replay(monkeypatch):
    client = Client();authority = resolve(client, client.request, CONSUMER, client.configuration);calls = []
    monkeypatch.setattr(wire, "verified_artifact", lambda *args: b"synthetic")
    monkeypatch.setattr(wire, "inspect_artifact", lambda *args: SimpleNamespace(wheel_name="synthetic", wheel_sha256="f"*64))
    class Channel:
        sent = False
        def __init__(self, binding):pass
        def __enter__(self):return self
        def __exit__(self, *args):pass
        def intent(self, payload, **kwargs):
            self.sent = True;calls.append(payload)
            raise BrokenPipeError("synthetic-private-endpoint-must-not-escape")
    monkeypatch.setattr(wire, "Channel", Channel)
    with pytest.raises(wire.PhaseFailure) as failure:wire.execute(client, authority, "deploy", "456")
    assert len(calls) == 1 and failure.value.record["result"] == "DEPLOYMENT_INCONCLUSIVE"
    assert failure.value.record["remote_may_still_be_running"] is True
    assert "private-endpoint" not in str(failure.value.record)
