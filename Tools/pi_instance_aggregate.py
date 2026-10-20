"""Read-only two-instance smoke aggregation; missing/newest-failed never falls back."""
from __future__ import annotations

import hashlib
import io
import zipfile
from datetime import datetime

from Tools.pi_instance_authority import CORE, OPERATIONAL_PATH, PI, github_file, resolve
from Tools.pi_instance_contract import (
    CONFIGURATION_REFS,
    BindingError,
    overall_smoke,
    require,
    strict_json,
)


def latest_deployment(client, authority, instance):
    # Any later attempt for this physical instance invalidates older smoke,
    # including a different manifest/consumer and an inconclusive mutation.
    listing = client.json("repos/"+PI+"/actions/workflows/deploy-latest-pi-release.yml/runs?event=workflow_dispatch&per_page=20")
    runs = listing.get("workflow_runs")
    require(isinstance(runs, list) and type(listing.get("total_count")) is int
            and 0 <= listing["total_count"] <= 20 and len(runs) <= 20, "DEPLOYMENT_RUN_LIST_INVALID")
    prefix = "Pi deploy / "+instance+" / "
    matching = [run for run in runs if run.get("head_branch") == "main"
        and isinstance(run.get("display_title"), str) and run["display_title"].startswith(prefix)
        and run.get("path") in {".github/workflows/deploy-latest-pi-release.yml", ".github/workflows/deploy-latest-pi-release.yml@main"}
        and run.get("event") == "workflow_dispatch"]
    require(bool(matching), "LATEST_DEPLOYMENT_MISSING")
    matching.sort(key=lambda run: int(run["id"]), reverse=True)
    run = matching[0]
    require(all(datetime.fromisoformat(old["updated_at"]) <= datetime.fromisoformat(run["updated_at"]) for old in matching), "OLDER_DEPLOYMENT_UPDATED_AFTER_NEWER_INTENT")
    require(type(run.get("run_attempt")) is int and run["run_attempt"] == 1 and run.get("status") == "completed" and run.get("conclusion") == "success"
            and run.get("head_sha") == authority.binding.consumer_sha
            and run.get("actor", {}).get("login") == "pcvantol"
            and run["display_title"] == prefix+authority.binding.request["manifest_id"], "LATEST_DEPLOYMENT_NOT_MATCHING_SUCCESS")
    return str(run["id"]), run.get("run_attempt"), run["updated_at"]


def aggregate(client, authority, current: dict) -> dict:
    selected = authority.binding.request["deployment_instance"]
    other = next(instance for instance in CONFIGURATION_REFS if instance != selected)
    results = {selected: current["result"], other: "SMOKE_INCONCLUSIVE"}
    report = {"result": "DEPLOYMENT_SMOKE_FAILED", "instances": results, "smoke_workflow_runs": {selected: current["workflow_run_id"]}}
    try:
        selected_deploy = latest_deployment(client, authority, selected)
        require(current.get("deployment_workflow_run") == selected_deploy[0], "CURRENT_SMOKE_DEPLOYMENT_SUPERSEDED")
        other_deploy = latest_deployment(client, authority, other)
        raw, _blob = github_file(client, CORE, OPERATIONAL_PATH, authority.operational_core_sha)
        require(hashlib.sha256(raw).hexdigest() == authority.operational_manifest_sha256, "OPERATIONAL_BYTES_MISMATCH")
        manifest = strict_json(raw)
        matches = [row for row in manifest["artifact_bindings"] if row["deployment_instance"] == other]
        require(len(matches) == 1, "OTHER_INSTANCE_BINDING_MISSING")
        request = dict(authority.binding.request)
        request.update({key: matches[0][key] for key in ("deployment_instance", "device_profile", "artifact_id", "artifact_sha256")})
        configuration = {"PI_RC5_OPERATIONAL_CORE_SHA": authority.operational_core_sha, "PI_RC5_OPERATIONAL_MANIFEST_SHA256": authority.operational_manifest_sha256}
        other_authority = resolve(client, request, authority.binding.consumer_sha, configuration)
        listing = client.json("repos/"+PI+"/actions/workflows/smoke-rbpi-djconnect.yml/runs?event=workflow_dispatch&head_sha="+authority.binding.consumer_sha+"&per_page=20")
        runs = listing.get("workflow_runs");require(isinstance(runs, list) and len(runs) <= 20
                and type(listing.get("total_count")) is int and 0 <= listing["total_count"] <= 20, "SMOKE_RUN_LIST_INVALID")
        title = "Pi smoke / "+other+" / "+request["manifest_id"]
        matching = [run for run in runs if run.get("head_sha") == authority.binding.consumer_sha
            and run.get("head_branch") == "main" and run.get("display_title") == title
            and run.get("path") in {".github/workflows/smoke-rbpi-djconnect.yml", ".github/workflows/smoke-rbpi-djconnect.yml@main"}
            and run.get("event") == "workflow_dispatch" and run.get("actor", {}).get("login") == "pcvantol"]
        require(bool(matching), "OTHER_INSTANCE_SMOKE_PENDING")
        # Never let an older successful run erase a newer failed/inconclusive observation.
        matching.sort(key=lambda run: int(run["id"]), reverse=True);run = matching[0]
        require(all(datetime.fromisoformat(old["updated_at"]) <= datetime.fromisoformat(run["updated_at"]) for old in matching), "OLDER_SMOKE_UPDATED_AFTER_NEWER_INTENT")
        require(run.get("status") == "completed" and run.get("conclusion") == "success", "LATEST_OTHER_SMOKE_NOT_PASS")
        artifacts = client.json("repos/"+PI+"/actions/runs/"+str(run["id"])+"/artifacts?per_page=100").get("artifacts")
        require(isinstance(artifacts, list) and len(artifacts) <= 100, "EVIDENCE_LIST_INVALID")
        matches = [artifact for artifact in artifacts if artifact.get("name") == "pi-deployment-smoke-evidence-"+other]
        require(len(matches) == 1 and matches[0].get("expired") is False
                and type(matches[0].get("size_in_bytes")) is int and 0 < matches[0]["size_in_bytes"] <= 262144, "EVIDENCE_ARTIFACT_INVALID")
        raw = client.archive(matches[0]["id"])
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            members = archive.infolist()
            require(len(members) == 1 and members[0].filename == "pi-smoke-evidence.json"
                    and members[0].file_size <= 65536, "EVIDENCE_LAYOUT_INVALID")
            evidence = strict_json(archive.read(members[0]), 65536)
        expected = other_authority.receipt()
        require(evidence.get("result") == "SMOKE_PASS" and str(evidence.get("workflow_run_id")) == str(run["id"])
                and all(evidence.get(key) == value for key, value in expected.items() if key != "classification")
                and evidence.get("installed_source") == request["candidate_sha"]
                and evidence.get("installed_version") == other_authority.binding.version
                and evidence.get("installed_device_profile") == request["device_profile"]
                and all(evidence.get(key) is True for key in ("api_reachable", "client_active", "api_active")), "OTHER_SMOKE_BINDING_INVALID")
        require(evidence.get("deployment_workflow_run") == other_deploy[0], "OTHER_SMOKE_DEPLOYMENT_SUPERSEDED")
        require(latest_deployment(client, authority, selected) == selected_deploy
                and latest_deployment(client, authority, other) == other_deploy, "DEPLOYMENT_CHANGED_DURING_AGGREGATION")
        latest, _blob = github_file(client, CORE, OPERATIONAL_PATH, "main")
        require(hashlib.sha256(latest).hexdigest() == authority.operational_manifest_sha256, "OPERATIONAL_MANIFEST_SUPERSEDED")
        results[other] = "SMOKE_PASS";report["smoke_workflow_runs"][other] = str(run["id"])
        report["result"] = overall_smoke(results)
    except (BindingError, OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile):
        pass  # Current instance remains independently observed; overall fails closed.
    return report
