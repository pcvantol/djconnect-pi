"""Explicit one-instance recovery consumer; never a replay of the failed deploy."""
from __future__ import annotations

import base64
import hashlib
import io
import zipfile
from datetime import datetime
from pathlib import Path

from Tools.pi_instance_authority import PI
from Tools.pi_instance_contract import BindingError, require, strict_json
from Tools.pi_rc6_recovery_root import ARTIFACT_SHA256, ORIGINAL_RUN, PROFILE, SOURCE

WORKFLOW = ".github/workflows/recover-rc6-wall4.yml"
ORIGINAL_MANIFEST = "release-4.0.0-rc.6-pi-two-instance-20261021"
ORIGINAL_CORE = "0b9b4b9845ac7764c9380e0ca88cafd05e10b1fe"
ORIGINAL_MANIFEST_SHA256 = "8740b4c3d751354061b9aeaf45689a4dbe525240f7047a2b923008d7e6495393"
# Set from the exact reviewed helper bytes; a local edited helper is never staged.
HELPER_SHA256 = "c395af61f47c42633c65013d61853c66c442781832ed4225d035d9209e9f0be2"


def selected(authority):
    request = authority.binding.request
    require(request["deployment_instance"] == "wall-4inch" and request["device_profile"] == PROFILE
            and request["candidate_sha"] == SOURCE and request["artifact_sha256"] == ARTIFACT_SHA256
            and authority.binding.consumer_sha != SOURCE and authority.operational_core_sha != ORIGINAL_CORE,
            "RECOVERY_SEPARATE_AUTHORITY_REQUIRED")


def helper_bytes():
    raw = Path(__file__).with_name("pi_rc6_recovery_root.py").read_bytes()
    require(len(raw) <= 65536 and hashlib.sha256(raw).hexdigest() == HELPER_SHA256,
            "RECOVERY_HELPER_BYTES_CHANGED")
    return base64.b64encode(raw).decode("ascii")


def original_failure(client):
    run = client.json("repos/"+PI+"/actions/runs/"+ORIGINAL_RUN)
    require(str(run.get("id")) == ORIGINAL_RUN and run.get("head_sha") == SOURCE
            and run.get("head_branch") == "main" and run.get("event") == "workflow_dispatch"
            and run.get("path") in {".github/workflows/deploy-latest-pi-release.yml", ".github/workflows/deploy-latest-pi-release.yml@main"}
            and run.get("status") == "completed" and run.get("conclusion") == "failure"
            and type(run.get("run_attempt")) is int and run["run_attempt"] == 1
            and run.get("actor", {}).get("login") == "pcvantol", "RECOVERY_ORIGINAL_RUN_INVALID")
    listing = client.json("repos/"+PI+"/actions/runs/"+ORIGINAL_RUN+"/artifacts?per_page=100")
    rows = listing.get("artifacts")
    require(isinstance(rows, list) and type(listing.get("total_count")) is int
            and len(rows) == listing["total_count"] and len(rows) <= 100, "RECOVERY_ORIGINAL_ARTIFACTS_INVALID")
    matches = [a for a in rows if a.get("name") == "pi-deployment-evidence-wall-4inch"]
    require(len(matches) == 1 and matches[0].get("expired") is False
            and type(matches[0].get("id")) is int and matches[0]["id"] > 0
            and type(matches[0].get("size_in_bytes")) is int and 0 < matches[0]["size_in_bytes"] <= 262144,
            "RECOVERY_ORIGINAL_ARTIFACT_INVALID")
    raw = client.archive(matches[0]["id"])
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            rows = archive.infolist()
            require(len(rows) == 1 and rows[0].filename == "pi-deploy-evidence.json"
                    and rows[0].file_size <= 65536, "RECOVERY_ORIGINAL_LAYOUT_INVALID")
            receipt = strict_json(archive.read(rows[0]), 65536)
    except (zipfile.BadZipFile, EOFError, RuntimeError):
        raise BindingError("RECOVERY_ORIGINAL_LAYOUT_INVALID") from None
    expected = {"result": "DEPLOYMENT_INCONCLUSIVE", "workflow_run_id": ORIGINAL_RUN,
        "candidate_sha": SOURCE, "consumer_sha": SOURCE, "deployment_instance": "wall-4inch",
        "device_profile": PROFILE, "artifact_sha256": ARTIFACT_SHA256,
        "manifest_id": ORIGINAL_MANIFEST, "operational_core_sha": ORIGINAL_CORE,
        "operational_manifest_sha256": ORIGINAL_MANIFEST_SHA256, "intent_dispatched": True,
        "remote_may_still_be_running": True}
    require(all(type(receipt.get(k)) is type(v) and receipt[k] == v for k, v in expected.items()),
            "RECOVERY_ORIGINAL_RECEIPT_INVALID")
    return receipt


def current_intent(client, run_id, authority):
    """A newer queued physical intent also withdraws this proposed recovery."""
    matching = []
    for filename, prefix in (("deploy-latest-pi-release.yml", "Pi deploy / wall-4inch / "),
                              ("recover-rc6-wall4.yml", "Pi recovery / wall-4inch / ")):
        listing = client.json("repos/"+PI+"/actions/workflows/"+filename+"/runs?event=workflow_dispatch&per_page=20")
        rows = listing.get("workflow_runs")
        require(isinstance(rows, list) and type(listing.get("total_count")) is int
                and 0 <= listing["total_count"] <= 20 and len(rows) <= 20, "RECOVERY_MUTATION_LIST_INVALID")
        for row in rows:
            if (row.get("head_branch") == "main" and row.get("event") == "workflow_dispatch"
                and row.get("path") in {".github/workflows/"+filename, ".github/workflows/"+filename+"@main"}
                and isinstance(row.get("display_title"), str) and row["display_title"].startswith(prefix)):
                require(type(row.get("id")) is int and row["id"] > 0, "RECOVERY_MUTATION_LIST_INVALID")
                matching.append(row)
    require(bool(matching), "RECOVERY_CURRENT_INTENT_MISSING")
    matching.sort(key=lambda row: row["id"], reverse=True);latest = matching[0]
    require(str(latest["id"]) == run_id and latest.get("status") == "in_progress"
            and latest.get("path") in {WORKFLOW, WORKFLOW+"@main"}
            and latest.get("head_sha") == authority.binding.consumer_sha
            and latest.get("display_title") == "Pi recovery / wall-4inch / "+authority.binding.request["manifest_id"]
            and type(latest.get("run_attempt")) is int and latest["run_attempt"] == 1
            and latest.get("actor", {}).get("login") == "pcvantol", "RECOVERY_INTENT_SUPERSEDED")
    require(all(datetime.fromisoformat(old["updated_at"]) <= datetime.fromisoformat(latest["updated_at"])
                for old in matching), "RECOVERY_OLDER_INTENT_UPDATED")
