"""Read-only exact provenance of the actual failed V1 recovery; never replay it."""
from __future__ import annotations

import base64
import hashlib
import io
import zipfile

from Tools.pi_instance_authority import PI, qualified
from Tools.pi_instance_contract import BindingError, require, strict_json
from Tools.pi_json_equivalence import exact_json
from Tools.pi_wall4_latest_failure import latest_spec

PREVIOUS_CODE_PINS = {'Tools/pi_rc6_recovery_root.py': '11ce41115c7aa5ac34e568f3ea9008915f342bc3272850b56c61eed19a760ab9', '.github/workflows/recover-rc6-wall4.yml': '582e49ff37eb6241442e05eb727874a56ba060d9e82a7570dfa70411cb70b6fa', 'Tools/pi_wall4_recovery_authority.py': '0dcb0fe488e3542b15065bba2289907427a94dba8278c167c5200f252d39925f', 'Tools/pi_wall4_recovery_release.py': '2b34eb04a0fca3e199825d637f3d18cda4801669c601203a84062cc9ff279091', 'Tools/pi_contract/PI_RC6_WALL4_RECOVERY_REQUEST_V1.schema.json': 'dd5a419bb1886dd4199ae917e4b4ee121af4cfe6b076b1f3dcd3b27200352999'}


def previous_file(client, path, consumer):
    require(path in PREVIOUS_CODE_PINS and consumer == "77fc4047f797066876c5345e8e43b346ab96d782", "PREVIOUS_CODE_REFERENCE_INVALID")
    x = client.json("repos/"+PI+"/contents/"+path+"?ref="+consumer)
    require(x.get("type") == "file" and x.get("path") == path and x.get("encoding") == "base64"
            and isinstance(x.get("content"), str) and len(x["content"]) <= 100000, "PREVIOUS_CODE_INVALID")
    try:raw = base64.b64decode("".join(x["content"].splitlines()), validate=True)
    except ValueError:raise BindingError("PREVIOUS_CODE_INVALID") from None
    require(len(raw) <= 65536 and hashlib.sha256(raw).hexdigest() == PREVIOUS_CODE_PINS[path]
            and hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw, usedforsecurity=False).hexdigest() == x.get("sha"),
            "PREVIOUS_CODE_BYTES_MISMATCH")
    return raw


def previous_spec():
    """Original V1 facts remain independent of the live successor version."""
    return latest_spec()["previous_recovery_attempt"]


def previous_failure(client):
    expected = previous_spec();run_id = expected["workflow_run_id"]
    run = client.json("repos/"+PI+"/actions/runs/"+run_id)
    require(type(run.get("id")) is int and str(run["id"]) == run_id
            and run.get("head_sha") == expected["consumer_sha"] and run.get("head_branch") == "main"
            and run.get("path") in {expected["workflow_path"], expected["workflow_path"]+"@main"}
            and run.get("event") == expected["event"] and run.get("status") == "completed"
            and run.get("conclusion") == expected["conclusion"] and type(run.get("run_attempt")) is int
            and run["run_attempt"] == expected["run_attempt"] and run.get("actor", {}).get("login") == expected["actor"]
            and run.get("repository", {}).get("full_name") == PI
            and run.get("display_title") == "Pi recovery / wall-4inch / "+expected["manifest_id"], "PREVIOUS_FAILED_RUN_INVALID")
    qualified(client, PI, expected["consumer_sha"])
    for path in PREVIOUS_CODE_PINS:
        raw = previous_file(client, path, expected["consumer_sha"])
        if path == "Tools/pi_rc6_recovery_root.py":
            require(hashlib.sha256(raw).hexdigest() == expected["root_helper_sha256"], "PREVIOUS_HELPER_MISMATCH")
        if path.endswith("REQUEST_V1.schema.json"):
            schema = strict_json(raw)
            require(schema["properties"]["action"] == {"const": "deployment"}
                    and schema["properties"]["execution_mode"] == {"const": "execute"}
                    and schema["additionalProperties"] is False, "PREVIOUS_TRANSPORT_CHAIN_INVALID")
    listing = client.json("repos/"+PI+"/actions/runs/"+run_id+"/artifacts?per_page=100")
    rows = listing.get("artifacts")
    require(isinstance(rows, list) and type(listing.get("total_count")) is int
            and len(rows) == listing["total_count"] and len(rows) <= 100, "PREVIOUS_ARTIFACT_LIST_INVALID")
    choices = [x for x in rows if isinstance(x, dict) and x.get("name") == expected["evidence_artifact_name"]]
    require(len(choices) == 1 and type(choices[0].get("id")) is int
            and str(choices[0]["id"]) == expected["evidence_artifact_id"] and choices[0].get("expired") is False
            and type(choices[0].get("size_in_bytes")) is int and 0 < choices[0]["size_in_bytes"] <= 262144,
            "PREVIOUS_ARTIFACT_INVALID")
    try:
        with zipfile.ZipFile(io.BytesIO(client.archive(choices[0]["id"]))) as z:
            members = z.infolist()
            require(len(members) == 1 and members[0].filename == expected["evidence_filename"] and members[0].file_size <= 65536,
                    "PREVIOUS_RECEIPT_LAYOUT_INVALID")
            raw = z.read(members[0])
    except (zipfile.BadZipFile, EOFError, RuntimeError):raise BindingError("PREVIOUS_RECEIPT_LAYOUT_INVALID") from None
    require(hashlib.sha256(raw).hexdigest() == expected["evidence_sha256"], "PREVIOUS_RECEIPT_BYTES_MISMATCH")
    record = strict_json(raw, 65536)
    joined = {k: expected[k] for k in ("workflow_run_id", "consumer_sha", "operational_core_sha", "operational_manifest_sha256",
                                       "manifest_id", "result", "intent_dispatched", "remote_may_still_be_running")}
    joined.update(candidate_sha="0dde0abe22a0859f170a7c1d3eab41f1ade44d37", deployment_instance="wall-4inch",
        device_profile="pi-zero-2w-arm64", target="rbpi-djconnect", platform_version="4.0", release_profile="INTERNAL_RELEASE",
        release_version="4.0.0-rc.6", artifact_sha256="d67869ffca53c4936059bdbbdbdf6be63b36eafac269fa2f3f9b090922cd0d64",
        artifact_id="release-asset:pcvantol/djconnect-pi-releases:v4.0.0-rc.6:djconnect-pi-pi-zero-2w-arm64-4.0.0-rc.6.tar.gz",
        inventory_sha256="530220ee38f6ccbcc824a78331b9dd89f236a5fa6ede12ebf7899dac83ff50c0", publication_run="39658681213",
        contract_source="265f151293735cddcf2e496e6c822f16c7cd2064", contract_finalization="c8549876df54e22b71ed26fcded4ec822b3d166d",
        recovery_contract_id="pi-rc6-wall4-recovery-v1", smoke_contract_id="pi-rc6-wall4-recovery-readback-v1",
        aggregate_disposition="SINGLE_INSTANCE_RECOVERY_ONLY", classification="INCOMPLETE_REQUIRES_ACTUAL_STATE_REVIEW")
    require(all(exact_json(record.get(k), v) for k, v in joined.items()), "PREVIOUS_RECEIPT_JOIN_INVALID")
    # Preserve the original raw's absence of kind/schema/helper/input fields.
    return record
