"""Dedicated wall4 recovery and separate readonly smoke; no two-instance aggregate."""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import re
import subprocess
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from Tools import pi_rc6_recovery as component
from Tools import pi_wall4_recovery_authority as authority_module
from Tools.pi_instance_artifact import inspect_artifact
from Tools.pi_instance_authority import PI, GitHubRead, verified_artifact
from Tools.pi_instance_contract import BindingError, require, strict_json, timestamp
from Tools.pi_instance_release import FIELDS, PhaseFailure
from Tools.pi_instance_ssh import Channel, validate_result
from Tools.pi_wall4_previous_failure import previous_failure
from Tools.pi_wall4_recovery_observer_pin import OBSERVER_SHA256

WORKFLOWS = {"recover": component.WORKFLOW, "smoke": ".github/workflows/smoke-rc6-wall4-recovery.yml"}


def observer_bytes():
    raw = Path(__file__).with_name("pi_wall4_recovery_observer.py").read_bytes()
    require(len(raw) <= 16384 and hashlib.sha256(raw).hexdigest() == OBSERVER_SHA256, "RECOVERY_OBSERVER_BYTES_CHANGED")
    return base64.b64encode(raw).decode("ascii")


def selected_request(inputs, operation):
    require(operation in WORKFLOWS and isinstance(inputs, dict), "RECOVERY_OPERATION_INVALID")
    extra = {"recovery_workflow_run"} if operation == "smoke" else set()
    require(set(inputs) == FIELDS | extra, "RECOVERY_INPUT_SET_INVALID")
    request = dict(inputs);run = request.pop("recovery_workflow_run", "")
    if operation == "smoke":require(isinstance(run, str) and re.fullmatch("[1-9][0-9]*", run), "RECOVERY_RUN_INVALID")
    return request, run


def workflow_context(client, operation, env):
    require(operation in WORKFLOWS and env.get("GITHUB_ACTIONS") == "true"
            and env.get("GITHUB_REPOSITORY") == PI and env.get("GITHUB_RUN_ATTEMPT") == "1", "RECOVERY_TRUSTED_WORKFLOW_REQUIRED")
    source = env.get("GITHUB_SHA", "");run_id = env.get("GITHUB_RUN_ID", "")
    require(re.fullmatch("[0-9a-f]{40}", source) and re.fullmatch("[1-9][0-9]*", run_id), "RECOVERY_WORKFLOW_IDENTITY_INVALID")
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    require(head == source, "CONSUMER_CHECKOUT_MISMATCH")
    row = client.json("repos/"+PI+"/actions/runs/"+run_id)
    require(str(row.get("id")) == run_id and row.get("head_sha") == source and row.get("head_branch") == "main"
            and row.get("path") in {WORKFLOWS[operation], WORKFLOWS[operation]+"@main"}
            and row.get("event") == "workflow_dispatch" and row.get("status") == "in_progress"
            and type(row.get("run_attempt")) is int and row["run_attempt"] == 1
            and row.get("actor", {}).get("login") == "pcvantol" and row.get("repository", {}).get("full_name") == PI,
            "RECOVERY_TRUSTED_WORKFLOW_REQUIRED")
    return source, run_id


def current_intent(client, run_id, authority, operation):
    choices = (("deploy-latest-pi-release.yml", "Pi deploy / wall-4inch / "),
        ("smoke-rbpi-djconnect.yml", "Pi smoke / wall-4inch / "),
        ("recover-rc6-wall4.yml", "Pi recovery / wall-4inch / "),
        ("smoke-rc6-wall4-recovery.yml", "Pi recovery smoke / wall-4inch / "))
    matching = []
    for filename, prefix in choices:
        x = client.json("repos/"+PI+"/actions/workflows/"+filename+"/runs?event=workflow_dispatch&per_page=20")
        rows = x.get("workflow_runs")
        require(isinstance(rows, list) and type(x.get("total_count")) is int
                and 0 <= x["total_count"] <= 20 and len(rows) == x["total_count"], "RECOVERY_INTENT_LIST_INVALID")
        for row in rows:
            require(isinstance(row, dict), "RECOVERY_INTENT_LIST_INVALID")
            if row.get("head_branch") == "main" and row.get("event") == "workflow_dispatch" and isinstance(row.get("display_title"), str) and row["display_title"].startswith(prefix):
                require(type(row.get("id")) is int and row["id"] > 0
                        and row.get("path") in {".github/workflows/"+filename, ".github/workflows/"+filename+"@main"}, "RECOVERY_INTENT_LIST_INVALID")
                timestamp(row.get("updated_at"));matching.append(row)
    require(bool(matching), "RECOVERY_CURRENT_INTENT_MISSING")
    latest = max(matching, key=lambda row: row["id"])
    title = "Pi recovery / wall-4inch / " if operation == "recover" else "Pi recovery smoke / wall-4inch / "
    require(str(latest["id"]) == run_id and latest.get("status") == "in_progress"
            and latest.get("path") in {WORKFLOWS[operation], WORKFLOWS[operation]+"@main"}
            and latest.get("head_sha") == authority.binding.consumer_sha and latest.get("display_title") == title+authority.binding.request["manifest_id"]
            and type(latest.get("run_attempt")) is int and latest["run_attempt"] == 1
            and latest.get("actor", {}).get("login") == "pcvantol", "RECOVERY_INTENT_SUPERSEDED")
    require(all(datetime.fromisoformat(row["updated_at"]) <= datetime.fromisoformat(latest["updated_at"]) for row in matching), "RECOVERY_OLDER_INTENT_UPDATED")


def observation(value):
    require(isinstance(value, dict) and set(value) == {"boot_id", "configuration_sha256"}
        and isinstance(value["boot_id"], str) and re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", value["boot_id"])
        and isinstance(value["configuration_sha256"], str) and re.fullmatch("[0-9a-f]{64}", value["configuration_sha256"]), "RECOVERY_OBSERVATION_INVALID")
    return dict(value)


def recovery_record(client, authority, run_id, record):
    require(isinstance(run_id, str) and re.fullmatch("[1-9][0-9]*", run_id) and run_id != component.ORIGINAL_RUN, "RECOVERY_RUN_INVALID")
    run = client.json("repos/"+PI+"/actions/runs/"+run_id)
    require(str(run.get("id")) == run_id and run.get("head_sha") == authority.binding.consumer_sha
            and run.get("head_branch") == "main" and run.get("event") == "workflow_dispatch"
            and run.get("path") in {WORKFLOWS["recover"], WORKFLOWS["recover"]+"@main"}
            and run.get("status") == "completed" and run.get("conclusion") == "success"
            and type(run.get("run_attempt")) is int and run["run_attempt"] == 1
            and run.get("actor", {}).get("login") == "pcvantol" and run.get("repository", {}).get("full_name") == PI,
            "SUCCESSFUL_CLOSED_RECOVERY_REQUIRED")
    expected = authority.receipt()
    require(isinstance(record, dict) and all(authority_module.exact_json(record.get(k), v) for k, v in expected.items() if k != "classification")
            and type(record.get("schema_version")) is int and record["schema_version"] == 1
            and record.get("kind") == "djconnect_pi_wall4_recovery_evidence"
            and record.get("result") == "RECOVERED_PENDING_SMOKE" and record.get("workflow_run_id") == run_id
            and record.get("recovery_workflow_run") == run_id and record.get("original_deployment_workflow_run") == component.ORIGINAL_RUN
            and record.get("recovery_helper_sha256") == component.HELPER_SHA256 and record.get("observer_sha256") == OBSERVER_SHA256
            and record.get("watchdog_restored") is True and record.get("configuration_preserved_by_installer") is True
            and type(record.get("verified_packaged_files")) is int and record["verified_packaged_files"] == 80,
            "RECOVERY_EVIDENCE_INVALID")
    return observation(record.get("recovery_observation"))


def download_recovery(client, run_id):
    require(isinstance(run_id, str) and re.fullmatch("[1-9][0-9]*", run_id), "RECOVERY_RUN_INVALID")
    listing = client.json("repos/"+PI+"/actions/runs/"+run_id+"/artifacts?per_page=100")
    rows = listing.get("artifacts")
    require(isinstance(rows, list) and type(listing.get("total_count")) is int
            and len(rows) == listing["total_count"] and len(rows) <= 100, "RECOVERY_EVIDENCE_LIST_INVALID")
    choices = [x for x in rows if isinstance(x, dict) and x.get("name") == "pi-wall4-recovery-evidence"]
    require(len(choices) == 1 and choices[0].get("expired") is False and type(choices[0].get("id")) is int and choices[0]["id"] > 0
            and type(choices[0].get("size_in_bytes")) is int and 0 < choices[0]["size_in_bytes"] <= 262144, "RECOVERY_EVIDENCE_ARTIFACT_INVALID")
    try:
        with zipfile.ZipFile(io.BytesIO(client.archive(choices[0]["id"]))) as z:
            members = z.infolist()
            require(len(members) == 1 and members[0].filename == "pi-recover-evidence.json" and members[0].file_size <= 65536, "RECOVERY_EVIDENCE_LAYOUT_INVALID")
            return strict_json(z.read(members[0]), 65536)
    except (zipfile.BadZipFile, EOFError, RuntimeError):raise BindingError("RECOVERY_EVIDENCE_LAYOUT_INVALID") from None


def execute(client, authority, operation, run_id, recovery_run=""):
    sent = False
    try:
        require(operation in WORKFLOWS and isinstance(authority, authority_module.RecoveryAuthority)
                and authority.binding.smoke_contract == authority_module.SMOKE, "CLOSED_RECOVERY_AUTHORITY_REQUIRED")
        component.selected(authority);component.original_failure(client);previous_failure(client)
        current_intent(client, run_id, authority, operation)
        previous = download_recovery(client, recovery_run) if operation == "smoke" else None
        prior = recovery_record(client, authority, recovery_run, previous) if previous is not None else None
        package = inspect_artifact(verified_artifact(client, authority), component.PROFILE, component.SOURCE)
        payload = {"phase": "recover" if operation == "recover" else "recovery-smoke", "source": component.SOURCE,
            "version": authority.binding.version, "device_profile": component.PROFILE, "wheel_name": package.wheel_name,
            "wheel_sha256": package.wheel_sha256, "run_id": run_id, "artifact_sha256": component.ARTIFACT_SHA256,
            "recovery_observer": observer_bytes()}
        if operation == "recover":payload["recovery_helper"] = component.helper_bytes()
        else:payload["recovery_observation"] = prior
        with Channel(authority.binding, recovery=operation == "recover", recovery_smoke=operation == "smoke") as channel:
            authority_module.current(client, authority);current_intent(client, run_id, authority, operation)
            payload["recovery_boot_id"] = channel.recovery_boot_id
            if prior is not None:require(prior["boot_id"] == channel.recovery_boot_id, "RECOVERY_BOOT_CHANGED")
            try:result = channel.intent(payload, timeout=1400 if operation == "recover" else 60)
            finally:sent = bool(channel.sent)
            seen = observation(result.get("recovery_observation"))
            require(seen["boot_id"] == channel.recovery_boot_id and (prior is None or seen == prior), "RECOVERY_OBSERVATION_CHANGED")
            validate_result({k: v for k, v in result.items() if k != "recovery_observation"}, "recover" if operation == "recover" else "smoke", authority.binding)
            if operation == "smoke":require(result.get("paired") is True and result.get("verified_packaged_files") == 80, "RECOVERY_SMOKE_INVALID")
            authority_module.current(client, authority);current_intent(client, run_id, authority, operation)
        return {**authority.receipt(), **result, "schema_version": 1,
            "kind": "djconnect_pi_wall4_recovery_evidence" if operation == "recover" else "djconnect_pi_wall4_recovery_smoke_evidence",
            "workflow_run_id": run_id, "recovery_workflow_run": run_id if operation == "recover" else recovery_run,
            "original_deployment_workflow_run": component.ORIGINAL_RUN, "recovery_helper_sha256": component.HELPER_SHA256,
            "observer_sha256": OBSERVER_SHA256, "timestamp": datetime.now(UTC).isoformat(),
            "classification": "SINGLE_INSTANCE_ONLY_NO_LIVE_PROFILE_TOUCH_OR_AUDIO_ACCEPTANCE"}
    except (BindingError, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        raise PhaseFailure({**authority.receipt(), "schema_version": 1,
            "kind": "djconnect_pi_wall4_recovery_evidence" if operation == "recover" else "djconnect_pi_wall4_recovery_smoke_evidence",
            "workflow_run_id": run_id, "recovery_workflow_run": run_id if operation == "recover" else recovery_run,
            "original_deployment_workflow_run": component.ORIGINAL_RUN,
            "recovery_helper_sha256": component.HELPER_SHA256, "observer_sha256": OBSERVER_SHA256,
            "result": "RECOVERY_INCONCLUSIVE" if operation == "recover" else "SMOKE_INCONCLUSIVE",
            "intent_dispatched": sent, "remote_may_still_be_running": sent and operation == "recover",
            "classification": "INCOMPLETE_REQUIRES_ACTUAL_STATE_REVIEW"}) from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation", choices=sorted(WORKFLOWS), required=True)
    parser.add_argument("--prepare", action="store_true");args = parser.parse_args()
    env = dict(os.environ);client = GitHubRead(env.get("GH_TOKEN", ""))
    inputs = strict_json(env.get("PI_INPUTS_JSON", "").encode(), 65535)
    request, recovery_run = selected_request(inputs, args.operation)
    consumer, run_id = workflow_context(client, args.operation, env)
    authority = authority_module.resolve(client, request, consumer, {k: env.get(k, "") for k in authority_module.CONFIG})
    component.original_failure(client);previous_failure(client);current_intent(client, run_id, authority, args.operation)
    component.helper_bytes();observer_bytes()
    folder = Path(env["RUNNER_TEMP"])/("pi-qualified-wall4-recovery-"+run_id+"-1")
    folder.mkdir(mode=0o700, exist_ok=True)
    if args.prepare:
        (folder/"prepared.json").write_text(json.dumps(authority.receipt(), sort_keys=True)+"\n")
        config = Path.home()/".ssh/config";require(config.is_file(), "SSH_CONFIGURATION_NOT_READY")
        with Path(env["GITHUB_ENV"]).open("a") as output:
            output.write("PI_INSTANCE_ENDPOINT_REF="+authority.binding.inventory_row["endpoint_config_ref"]+"\nPI_INSTANCE_SSH_CONFIG="+str(config)+"\n")
        return
    require(env.get("PI_CANONICAL_PREFLIGHT_PASSED") == "true", "CANONICAL_PREFLIGHT_REQUIRED")
    require(strict_json((folder/"prepared.json").read_bytes()) == authority.receipt(), "RUN_BOUND_AUTHORITY_CHANGED")
    try:record = execute(client, authority, args.operation, run_id, recovery_run)
    except PhaseFailure as failure:
        (folder/("pi-"+args.operation+"-evidence.json")).write_text(json.dumps(failure.record, sort_keys=True, indent=2)+"\n")
        raise
    (folder/("pi-"+args.operation+"-evidence.json")).write_text(json.dumps(record, sort_keys=True, indent=2)+"\n")


if __name__ == "__main__":
    try:main()
    except (BindingError, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        print("WALL4_RECOVERY_NOT_COMPLETED_REQUIRES_STATE_REVIEW", file=__import__("sys").stderr)
        raise SystemExit(1) from None
