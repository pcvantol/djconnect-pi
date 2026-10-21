"""Qualified workflow entrypoint; phase, identity and immutable authority are separate."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from Tools.pi_instance_aggregate import aggregate
from Tools.pi_instance_artifact import inspect_artifact
from Tools.pi_instance_authority import (
    CORE,
    OPERATIONAL_PATH,
    PI,
    GitHubRead,
    github_file,
    resolve,
    verified_artifact,
)
from Tools.pi_instance_contract import (
    BindingError,
    require,
    strict_json,
    validate_smoke_join,
)
from Tools.pi_instance_ssh import Channel, validate_result

WORKFLOWS = {"readiness": ".github/workflows/pi-deployment-readiness.yml", "deploy": ".github/workflows/deploy-latest-pi-release.yml", "smoke": ".github/workflows/smoke-rbpi-djconnect.yml"}
FIELDS = {"action", "execution_mode", "candidate_sha", "manifest_id", "artifact_id", "artifact_sha256", "target", "platform_version", "release_profile", "deployment_instance", "device_profile", "inventory_sha256"}


def selected_request(inputs: dict, operation: str) -> tuple[dict, str]:
    require(operation in WORKFLOWS and isinstance(inputs, dict), "OPERATION_INVALID")
    additional = {"deployment_workflow_run"} if operation == "smoke" else set()
    require(set(inputs) == FIELDS | additional, "INPUT_SET_INVALID")
    request = dict(inputs);deployment_run = request.pop("deployment_workflow_run", "")
    if operation == "smoke":
        require(request["action"] == "deployment_smoke" and isinstance(deployment_run, str)
                and re.fullmatch("[1-9][0-9]*", deployment_run) is not None, "SMOKE_INPUT_INVALID")
        request["action"] = "deployment"  # Revalidate the originating authorized deployment binding.
    return request, deployment_run


def workflow_context(client, operation: str, environment: dict) -> tuple[str, str]:
    require(environment.get("GITHUB_ACTIONS") == "true" and environment.get("GITHUB_REPOSITORY") == PI, "QUALIFIED_WORKFLOW_REQUIRED")
    source = environment.get("GITHUB_SHA", "");run_id = environment.get("GITHUB_RUN_ID", "")
    require(re.fullmatch("[0-9a-f]{40}", source) is not None and re.fullmatch("[1-9][0-9]*", run_id) is not None, "WORKFLOW_IDENTITY_INVALID")
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    require(head == source, "CONSUMER_CHECKOUT_MISMATCH")
    run = client.json("repos/"+PI+"/actions/runs/"+run_id)
    require(run.get("head_sha") == source and run.get("head_branch") == "main"
            and run.get("path") in {WORKFLOWS[operation], WORKFLOWS[operation]+"@main"} and run.get("event") == "workflow_dispatch"
            and run.get("status") == "in_progress" and run.get("actor", {}).get("login") == "pcvantol"
            and run.get("repository", {}).get("full_name") == PI, "QUALIFIED_WORKFLOW_REQUIRED")
    if operation == "deploy":require(environment.get("GITHUB_RUN_ATTEMPT") == "1", "RERUN_REQUIRES_ACTUAL_STATE_REVIEW")
    return source, run_id


def current_authority(client, authority):
    raw, _blob = github_file(client, CORE, OPERATIONAL_PATH, "main")
    require(hashlib.sha256(raw).hexdigest() == authority.operational_manifest_sha256, "OPERATIONAL_MANIFEST_SUPERSEDED")


def deployment_record(client, binding, authority, receipt: dict, run_id: str):
    run = client.json("repos/"+PI+"/actions/runs/"+run_id)
    require(run.get("head_sha") == binding.consumer_sha and run.get("head_branch") == "main"
            and run.get("path") in {WORKFLOWS["deploy"], WORKFLOWS["deploy"]+"@main"} and run.get("event") == "workflow_dispatch"
            and run.get("status") == "completed" and run.get("conclusion") == "success"
            and run.get("actor", {}).get("login") == "pcvantol", "SUCCESSFUL_DEPLOYMENT_REQUIRED")
    expected = authority.receipt()
    require(receipt.get("result") == "DEPLOYED_PENDING_SMOKE" and receipt.get("deployment_workflow_run") == run_id
            and all(receipt.get(key) == value for key, value in expected.items() if key != "classification"), "DEPLOYMENT_EVIDENCE_MISMATCH")


def _execute(client, authority, operation: str, run_id: str, *, deployment=None, deployment_run="", progress=None) -> dict:
    binding = authority.binding
    if operation == "smoke":deployment_record(client, binding, authority, deployment, deployment_run)
    payload = {"phase": "readiness"}
    if operation != "readiness":
        raw = verified_artifact(client, authority)
        package = inspect_artifact(raw, binding.request["device_profile"], binding.request["candidate_sha"])
        payload = {"phase": operation, "source": binding.request["candidate_sha"], "version": binding.version,
            "device_profile": binding.request["device_profile"], "wheel_name": package.wheel_name,
            "wheel_sha256": package.wheel_sha256, "run_id": run_id, "artifact_sha256": binding.request["artifact_sha256"]}
        if operation == "deploy":payload["artifact"] = base64.b64encode(raw).decode("ascii")
    with Channel(binding) as channel:
        current_authority(client, authority)  # Last immutable-approval currentness check on this fresh identity channel.
        try:
            result = channel.intent(payload, timeout=1200 if operation == "deploy" else 45)
        finally:
            if progress is not None:progress["intent_dispatched"] = bool(getattr(channel, "sent", True))
        validate_result(result, operation, binding)
    record = {**authority.receipt(), **result, "schema_version": 2,
        "kind": {"deploy": "djconnect_pi_deployment_evidence", "smoke": "djconnect_pi_deployment_smoke_evidence", "readiness": "djconnect_pi_readiness_evidence"}[operation], "workflow_run_id": run_id,
        "timestamp": datetime.now(UTC).isoformat(), "classification": "PHYSICAL_READBACK_NO_LIVE_PROFILE_OR_TOUCH_ACCEPTANCE"}
    if operation == "deploy":record["deployment_workflow_run"] = run_id
    if operation == "smoke":
        record["deployment_workflow_run"] = deployment_run
        validate_smoke_join(binding, deployment, record, deployment_run)
    return record


class PhaseFailure(BindingError):
    def __init__(self, record):
        self.record = record
        super().__init__("PI_INSTANCE_NOT_COMPLETED_REQUIRES_STATE_REVIEW")


def execute(client, authority, operation: str, run_id: str, *, deployment=None, deployment_run="") -> dict:
    progress = {"intent_dispatched": False}
    try:
        return _execute(client, authority, operation, run_id, deployment=deployment, deployment_run=deployment_run, progress=progress)
    except (BindingError, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        record = {**authority.receipt(), "schema_version": 2, "workflow_run_id": run_id,
            "result": "SMOKE_INCONCLUSIVE" if operation == "smoke" else "DEPLOYMENT_INCONCLUSIVE" if operation == "deploy" else "TARGET_NOT_READY",
            "intent_dispatched": progress["intent_dispatched"],
            "remote_may_still_be_running": operation == "deploy" and progress["intent_dispatched"],
            "classification": "INCOMPLETE_REQUIRES_ACTUAL_STATE_REVIEW", "error": "NEEDS_ACTUAL_STATE_REVIEW", "timestamp": datetime.now(UTC).isoformat()}
        if operation == "smoke":record["deployment_workflow_run"] = deployment_run
        raise PhaseFailure(record) from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation", choices=sorted(WORKFLOWS), required=True)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--deployment-evidence", type=Path)
    args = parser.parse_args()
    environment = dict(os.environ)
    inputs = strict_json(environment.get("PI_INPUTS_JSON", "").encode(), 65535)
    request, deployment_run = selected_request(inputs, args.operation)
    client = GitHubRead(environment.get("GH_TOKEN", ""))
    consumer_sha, run_id = workflow_context(client, args.operation, environment)
    configuration = {key: environment.get(key, "") for key in ("PI_RC6_OPERATIONAL_CORE_SHA", "PI_RC6_OPERATIONAL_MANIFEST_SHA256")}
    authority = resolve(client, request, consumer_sha, configuration)
    root = Path(environment["RUNNER_TEMP"])/("pi-qualified-instance-"+run_id+"-"+environment.get("GITHUB_RUN_ATTEMPT", "1"));root.mkdir(mode=0o700, exist_ok=True)
    if args.prepare:
        (root/"prepared.json").write_text(json.dumps(authority.receipt(), sort_keys=True)+"\n")
        configuration_file = Path.home()/".ssh/config"
        require(configuration_file.is_file(), "SSH_CONFIGURATION_NOT_READY")
        with Path(environment["GITHUB_ENV"]).open("a") as output:
            output.write("PI_INSTANCE_ENDPOINT_REF="+authority.binding.inventory_row["endpoint_config_ref"]+"\n")
            output.write("PI_INSTANCE_SSH_CONFIG="+str(configuration_file)+"\n")
        return
    require(environment.get("PI_CANONICAL_PREFLIGHT_PASSED") == "true", "CANONICAL_PREFLIGHT_REQUIRED")
    prepared = strict_json((root/"prepared.json").read_bytes())
    require(prepared == authority.receipt(), "RUN_BOUND_AUTHORITY_CHANGED")
    deployment = None
    if args.operation == "smoke":
        require(args.deployment_evidence is not None, "DEPLOYMENT_EVIDENCE_REQUIRED")
        with args.deployment_evidence.open("rb") as stream:deployment = strict_json(stream.read(262145))
    try:
        record = execute(client, authority, args.operation, run_id, deployment=deployment, deployment_run=deployment_run)
    except PhaseFailure as failure:
        (root/("pi-"+args.operation+"-evidence.json")).write_text(json.dumps(failure.record, sort_keys=True, indent=2)+"\n")
        raise
    (root/("pi-"+args.operation+"-evidence.json")).write_text(json.dumps(record, sort_keys=True, indent=2)+"\n")
    if args.operation == "smoke":
        overall = aggregate(client, authority, record)
        (root/"overall-smoke.json").write_text(json.dumps(overall, sort_keys=True, indent=2)+"\n")
        with Path(environment["GITHUB_OUTPUT"]).open("a") as output:
            output.write("overall_operational="+("true" if overall["result"] == "DEPLOYMENT_OPERATIONAL" else "false")+"\n")


if __name__ == "__main__":
    try:main()
    except (BindingError, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        # Do not publish private exceptions/URLs or pretend a dispatched installer stopped.
        print("PI_INSTANCE_NOT_COMPLETED_REQUIRES_STATE_REVIEW", file=__import__("sys").stderr)
        raise SystemExit(1) from None
