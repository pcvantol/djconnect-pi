from __future__ import annotations

import io
import json
import zipfile

import pytest

pytest.importorskip("jsonschema", reason="Dedicated locked deployment-tool suite")
from test_pi_instance_authority import CONSUMER, Client

from Tools import pi_instance_aggregate as wire
from Tools.pi_instance_authority import resolve


class AggregateClient(Client):
    def __init__(self):
        super().__init__();self.aggregate_case = "valid"
    def json(self, path):
        if "/workflows/deploy-latest" in path:
            runs = []
            for instance, run_id in (("wall-4inch", 90), ("wall-10inch", 91)):
                row = {"id": run_id, "head_sha": CONSUMER, "head_branch": "main", "display_title": "Pi deploy / "+instance+" / "+self.request["manifest_id"],
                    "path": ".github/workflows/deploy-latest-pi-release.yml", "event": "workflow_dispatch", "actor": {"login": "pcvantol"},
                    "status": "completed", "conclusion": "success", "run_attempt": 1, "updated_at": "2026-10-20T16:00:00Z"}
                runs.append(row)
                if getattr(self, "later_instance", None) == instance:
                    changed = {**row, "id": run_id+100, "updated_at": "2026-10-20T17:01:00Z"}
                    mode = self.later_mode
                    if mode == "queued-earlier-update":changed.update(status="queued", conclusion=None, updated_at="2026-10-20T15:59:00Z")
                    elif mode in {"same-id-rerun", "missing-attempt", "boolean-attempt", "string-attempt"}:
                        changed.update(id=run_id, run_attempt={"same-id-rerun": 2, "missing-attempt": None, "boolean-attempt": True, "string-attempt": "1"}[mode])
                        runs.remove(row)  # GitHub replaces this run row on a rerun.
                    if mode in {"queued", "in_progress"}:changed.update(status=mode, conclusion=None)
                    elif mode in {"failure", "cancelled", "timed_out"}:changed["conclusion"] = mode
                    elif mode == "manifest":changed["display_title"] += "-new"
                    elif mode == "consumer":changed["head_sha"] = "f"*40
                    runs.append(changed)
            return {"workflow_runs": runs, "total_count": len(runs)}
        if "/workflows/smoke-rbpi" in path:
            run = {"id": 100, "head_sha": CONSUMER, "head_branch": "main", "display_title": "Pi smoke / wall-10inch / "+self.request["manifest_id"],
                "path": ".github/workflows/smoke-rbpi-djconnect.yml", "event": "workflow_dispatch", "actor": {"login": "pcvantol"},
                "status": "completed", "conclusion": "success", "updated_at": "2026-10-20T17:00:00Z"}
            runs = [run]
            if self.aggregate_case == "missing":runs = []
            if self.aggregate_case == "newest-failed":runs.append({**run, "id": 99, "conclusion": "failure", "updated_at": "2026-10-20T17:01:00Z"})
            if self.aggregate_case == "newest-pending":runs.append({**run, "id": 101, "status": "in_progress", "conclusion": None, "updated_at": "2026-10-20T17:01:00Z"})
            if self.aggregate_case == "queued-smoke-earlier-update":runs.append({**run, "id": 101, "status": "queued", "conclusion": None, "updated_at": "2026-10-20T16:59:00Z"})
            if self.aggregate_case == "wrong-consumer":runs[0]["head_sha"] = "f"*40
            return {"workflow_runs": runs, "total_count": 21 if self.aggregate_case == "incomplete-list" else len(runs)}
        if "/actions/runs/100/artifacts" in path:
            artifact = {"id": 10, "name": "pi-deployment-smoke-evidence-wall-10inch", "expired": False, "size_in_bytes": 1000}
            if self.aggregate_case == "expired":artifact["expired"] = True
            return {"artifacts": [artifact]}
        return super().json(path)
    def archive(self, artifact_id):
        other = next(row for row in self.manifest["artifact_bindings"] if row["deployment_instance"] == "wall-10inch")
        request = {**self.request, **{key: other[key] for key in ("deployment_instance", "device_profile", "artifact_id", "artifact_sha256")}}
        authority = resolve(self, request, CONSUMER, self.configuration)
        record = {**authority.receipt(), "result": "SMOKE_PASS", "workflow_run_id": "100", "deployment_workflow_run": "91",
            "installed_source": request["candidate_sha"], "installed_version": authority.binding.version,
            "installed_device_profile": request["device_profile"], "api_reachable": True, "client_active": True, "api_active": True}
        if self.aggregate_case == "wrong-pair":record["operational_manifest_sha256"] = "f"*64
        if self.aggregate_case == "wrong-instance":record["deployment_instance"] = "wall-4inch"
        raw = io.BytesIO()
        with zipfile.ZipFile(raw, "w") as archive:archive.writestr("pi-smoke-evidence.json", json.dumps(record))
        return raw.getvalue()


def test_both_matching_required_instances_can_be_overall_operational():
    client = AggregateClient();authority = resolve(client, client.request, CONSUMER, client.configuration)
    result = wire.aggregate(client, authority, {"result": "SMOKE_PASS", "workflow_run_id": "101", "deployment_workflow_run": "90"})
    assert result["result"] == "DEPLOYMENT_OPERATIONAL" and client.effects == 0


@pytest.mark.parametrize("case", ["missing", "newest-failed", "newest-pending", "wrong-consumer", "incomplete-list", "expired", "wrong-pair", "wrong-instance", "queued-smoke-earlier-update"])
def test_no_old_or_partial_success_can_complete_the_release(case):
    client = AggregateClient();client.aggregate_case = case
    authority = resolve(client, client.request, CONSUMER, client.configuration)
    result = wire.aggregate(client, authority, {"result": "SMOKE_PASS", "workflow_run_id": "101", "deployment_workflow_run": "90"})
    assert result["result"] == "DEPLOYMENT_SMOKE_FAILED" and client.effects == 0


@pytest.mark.parametrize("instance", ["wall-4inch", "wall-10inch"])
@pytest.mark.parametrize("mode", ["queued", "in_progress", "failure", "cancelled", "timed_out", "manifest", "consumer", "success-unmatched", "queued-earlier-update", "same-id-rerun", "missing-attempt", "boolean-attempt", "string-attempt"])
def test_later_deployment_on_either_instance_invalidates_older_smoke(instance, mode):
    client = AggregateClient();client.later_instance = instance;client.later_mode = mode
    authority = resolve(client, client.request, CONSUMER, client.configuration)
    result = wire.aggregate(client, authority, {"result": "SMOKE_PASS", "workflow_run_id": "101", "deployment_workflow_run": "90"})
    assert result["result"] == "DEPLOYMENT_SMOKE_FAILED" and client.effects == 0


@pytest.mark.parametrize("instance", ["wall-4inch", "wall-10inch"])
def test_deployment_changes_while_aggregating_cannot_publish_operational(instance):
    client = AggregateClient();original = client.json;calls = 0
    def read(path):
        nonlocal calls
        if "/workflows/deploy-latest" in path:
            calls += 1
            if calls > 2:client.later_instance = instance;client.later_mode = "in_progress"
        return original(path)
    client.json = read
    authority = resolve(client, client.request, CONSUMER, client.configuration)
    result = wire.aggregate(client, authority, {"result": "SMOKE_PASS", "workflow_run_id": "101", "deployment_workflow_run": "90"})
    assert result["result"] == "DEPLOYMENT_SMOKE_FAILED" and client.effects == 0
