"""Read-only provenance of the latest failed V2 recovery; not a new execution grant."""

from __future__ import annotations

import base64
import hashlib
import io
import zipfile

from Tools.pi_instance_authority import PI, qualified
from Tools.pi_instance_contract import BindingError, require, strict_json
from Tools.pi_wall4_recovery_authority import exact_json

PREVIOUS_CODE_PINS = {
    "Tools/pi_rc6_recovery_root.py": "c395af61f47c42633c65013d61853c66c442781832ed4225d035d9209e9f0be2",
    ".github/workflows/recover-rc6-wall4.yml": "31e6f69cc59fc6275fd45fa15b305cf56c4daa5ee54e4fe5ac4bdf0610e15343",
    "Tools/pi_wall4_recovery_authority.py": "7042263b36315dcbff58a8744ae69adb5d14b85e2a43358441dd0cba7bb43656",
    "Tools/pi_wall4_recovery_release.py": "091701a092a9692700c94c7259620bd17d98983b56171e5d450f719948c763da",
    "Tools/pi_contract/PI_RC6_WALL4_RECOVERY_REQUEST_V2.schema.json": "92e1e182d768d9f7fecad1a7433ac6a29ece0ff90084ae855fb6fb674e21ea6d",
}


def latest_spec():
    return {
        "workflow_run_id": "39775941080",
        "consumer_sha": "2e7479d0d15aa11ad3bff4c8103c18dbb1f2c32a",
        "workflow_path": ".github/workflows/recover-rc6-wall4.yml",
        "event": "workflow_dispatch",
        "actor": "pcvantol",
        "run_attempt": 1,
        "conclusion": "failure",
        "evidence_artifact_id": "12423814908",
        "evidence_artifact_name": "pi-wall4-recovery-evidence",
        "evidence_filename": "pi-recover-evidence.json",
        "evidence_sha256": "eb57af222e6be4f9d7e9e40be488f3f395ae2e6e94a583e6d4ea7e9d839c6b4d",
        "evidence_bytes": 3058,
        "operational_core_sha": "83744790decc6ef8940795dc2c9c0e3fb058173b",
        "operational_manifest_sha256": "c63ca35c9974b701e70d649a0cbc77a187a2ee83dc329602d6c887a680fcc51d",
        "manifest_id": "release-4.0.0-rc.6-pi-wall4-recovery-v2-20261022",
        "recovery_helper_sha256": "c395af61f47c42633c65013d61853c66c442781832ed4225d035d9209e9f0be2",
        "observer_sha256": "4ae5b8fa3297785a362dfb2e36354cffb4168ab2d0572ef169288d559239e36c",
        "recovery_contract_id": "pi-rc6-wall4-recovery-v2",
        "smoke_contract_id": "pi-rc6-wall4-recovery-readback-v2",
        "schema_version": 1,
        "kind": "djconnect_pi_wall4_recovery_evidence",
        "result": "RECOVERY_INCONCLUSIVE",
        "intent_dispatched": True,
        "remote_may_still_be_running": True,
        "claim_policy": "UNCHANGED_LEDGER_EXCLUSIVE_DURABLE_CREATE_BEFORE_EFFECTS",
        "previous_recovery_attempt": {
            "actor": "pcvantol",
            "conclusion": "failure",
            "consumer_sha": "77fc4047f797066876c5345e8e43b346ab96d782",
            "disposition": "FAILED_RECOVERY_REQUIRES_FRESH_STATE_AND_NEW_QUALIFIED_BINDING",
            "event": "workflow_dispatch",
            "evidence_artifact_id": "12391115673",
            "evidence_artifact_name": "pi-wall4-recovery-evidence",
            "evidence_filename": "pi-recover-evidence.json",
            "evidence_sha256": "ce97876b008d4417ec08100066aa38abf87dd57ae8398ae5e64de97d442744ec",
            "intent_dispatched": True,
            "manifest_id": "release-4.0.0-rc.6-pi-wall4-recovery-20261022",
            "operational_core_sha": "2945bd331f17f99138c1841cdf82c5da5cba4de8",
            "operational_manifest_sha256": "de22c4eb8644ef21fb2f690689ad716226aae1958f385fc83df8221207e6b0de",
            "remote_may_still_be_running": True,
            "result": "RECOVERY_INCONCLUSIVE",
            "root_helper_sha256": "11ce41115c7aa5ac34e568f3ea9008915f342bc3272850b56c61eed19a760ab9",
            "run_attempt": 1,
            "workflow_path": ".github/workflows/recover-rc6-wall4.yml",
            "workflow_run_id": "39695635601",
        },
        "root_helper_sha256": "c395af61f47c42633c65013d61853c66c442781832ed4225d035d9209e9f0be2",
        "disposition": "FAILED_RECOVERY_REQUIRES_FRESH_STATE_AND_NEW_QUALIFIED_BINDING",
    }


def previous_file(client, path, consumer):
    require(
        path in PREVIOUS_CODE_PINS
        and consumer == "2e7479d0d15aa11ad3bff4c8103c18dbb1f2c32a",
        "PREVIOUS_CODE_REFERENCE_INVALID",
    )
    x = client.json("repos/" + PI + "/contents/" + path + "?ref=" + consumer)
    require(
        x.get("type") == "file"
        and x.get("path") == path
        and x.get("encoding") == "base64"
        and isinstance(x.get("content"), str)
        and len(x["content"]) <= 100000,
        "PREVIOUS_CODE_INVALID",
    )
    try:
        raw = base64.b64decode("".join(x["content"].splitlines()), validate=True)
    except ValueError:
        raise BindingError("PREVIOUS_CODE_INVALID") from None
    require(
        len(raw) <= 65536
        and hashlib.sha256(raw).hexdigest() == PREVIOUS_CODE_PINS[path]
        and hashlib.sha1(
            b"blob " + str(len(raw)).encode() + b"\0" + raw, usedforsecurity=False
        ).hexdigest()
        == x.get("sha"),
        "PREVIOUS_CODE_BYTES_MISMATCH",
    )
    return raw


def latest_failure(client):
    expected = latest_spec()
    run_id = expected["workflow_run_id"]
    run = client.json("repos/" + PI + "/actions/runs/" + run_id)
    require(
        type(run.get("id")) is int
        and str(run["id"]) == run_id
        and run.get("head_sha") == expected["consumer_sha"]
        and run.get("head_branch") == "main"
        and run.get("path")
        in {expected["workflow_path"], expected["workflow_path"] + "@main"}
        and run.get("event") == expected["event"]
        and run.get("status") == "completed"
        and run.get("conclusion") == expected["conclusion"]
        and type(run.get("run_attempt")) is int
        and run["run_attempt"] == expected["run_attempt"]
        and run.get("actor", {}).get("login") == expected["actor"]
        and run.get("repository", {}).get("full_name") == PI
        and run.get("display_title")
        == "Pi recovery / wall-4inch / " + expected["manifest_id"],
        "PREVIOUS_FAILED_RUN_INVALID",
    )
    qualified(client, PI, expected["consumer_sha"])
    for path in PREVIOUS_CODE_PINS:
        raw = previous_file(client, path, expected["consumer_sha"])
        if path == "Tools/pi_rc6_recovery_root.py":
            require(
                hashlib.sha256(raw).hexdigest() == expected["root_helper_sha256"],
                "PREVIOUS_HELPER_MISMATCH",
            )
        if path.endswith("REQUEST_V2.schema.json"):
            schema = strict_json(raw)
            require(
                schema["properties"]["action"] == {"const": "deployment"}
                and schema["properties"]["execution_mode"] == {"const": "execute"}
                and schema["additionalProperties"] is False,
                "PREVIOUS_TRANSPORT_CHAIN_INVALID",
            )
    listing = client.json(
        "repos/" + PI + "/actions/runs/" + run_id + "/artifacts?per_page=100"
    )
    rows = listing.get("artifacts")
    require(
        isinstance(rows, list)
        and type(listing.get("total_count")) is int
        and len(rows) == listing["total_count"]
        and len(rows) <= 100,
        "PREVIOUS_ARTIFACT_LIST_INVALID",
    )
    choices = [
        x
        for x in rows
        if isinstance(x, dict) and x.get("name") == expected["evidence_artifact_name"]
    ]
    require(
        len(choices) == 1
        and type(choices[0].get("id")) is int
        and str(choices[0]["id"]) == expected["evidence_artifact_id"]
        and choices[0].get("expired") is False
        and type(choices[0].get("size_in_bytes")) is int
        and 0 < choices[0]["size_in_bytes"] <= 262144,
        "PREVIOUS_ARTIFACT_INVALID",
    )
    try:
        with zipfile.ZipFile(io.BytesIO(client.archive(choices[0]["id"]))) as z:
            members = z.infolist()
            require(
                len(members) == 1
                and members[0].filename == expected["evidence_filename"]
                and members[0].file_size <= 65536,
                "PREVIOUS_RECEIPT_LAYOUT_INVALID",
            )
            raw = z.read(members[0])
    except (zipfile.BadZipFile, EOFError, RuntimeError):
        raise BindingError("PREVIOUS_RECEIPT_LAYOUT_INVALID") from None
    require(
        hashlib.sha256(raw).hexdigest() == expected["evidence_sha256"],
        "PREVIOUS_RECEIPT_BYTES_MISMATCH",
    )
    record = strict_json(raw, 65536)
    joined = {
        "aggregate_disposition": "SINGLE_INSTANCE_RECOVERY_ONLY",
        "artifact_id": "release-asset:pcvantol/djconnect-pi-releases:v4.0.0-rc.6:djconnect-pi-pi-zero-2w-arm64-4.0.0-rc.6.tar.gz",
        "artifact_sha256": "d67869ffca53c4936059bdbbdbdf6be63b36eafac269fa2f3f9b090922cd0d64",
        "candidate_sha": "0dde0abe22a0859f170a7c1d3eab41f1ade44d37",
        "claim_policy": "UNCHANGED_LEDGER_EXCLUSIVE_DURABLE_CREATE_BEFORE_EFFECTS",
        "classification": "INCOMPLETE_REQUIRES_ACTUAL_STATE_REVIEW",
        "consumer_sha": "2e7479d0d15aa11ad3bff4c8103c18dbb1f2c32a",
        "contract_finalization": "659bfe752dff0dcdcdbfc475be52bdf69090e085",
        "contract_source": "5cf78c1c83936cc9ed2feb750f83cf743b643b90",
        "deployment_instance": "wall-4inch",
        "device_profile": "pi-zero-2w-arm64",
        "intent_dispatched": True,
        "inventory_sha256": "530220ee38f6ccbcc824a78331b9dd89f236a5fa6ede12ebf7899dac83ff50c0",
        "kind": "djconnect_pi_wall4_recovery_evidence",
        "manifest_id": "release-4.0.0-rc.6-pi-wall4-recovery-v2-20261022",
        "observer_sha256": "4ae5b8fa3297785a362dfb2e36354cffb4168ab2d0572ef169288d559239e36c",
        "operational_core_sha": "83744790decc6ef8940795dc2c9c0e3fb058173b",
        "operational_manifest_sha256": "c63ca35c9974b701e70d649a0cbc77a187a2ee83dc329602d6c887a680fcc51d",
        "original_deployment_workflow_run": "39669504016",
        "platform_version": "4.0",
        "previous_recovery_attempt": {
            "actor": "pcvantol",
            "conclusion": "failure",
            "consumer_sha": "77fc4047f797066876c5345e8e43b346ab96d782",
            "disposition": "FAILED_RECOVERY_REQUIRES_FRESH_STATE_AND_NEW_QUALIFIED_BINDING",
            "event": "workflow_dispatch",
            "evidence_artifact_id": "12391115673",
            "evidence_artifact_name": "pi-wall4-recovery-evidence",
            "evidence_filename": "pi-recover-evidence.json",
            "evidence_sha256": "ce97876b008d4417ec08100066aa38abf87dd57ae8398ae5e64de97d442744ec",
            "intent_dispatched": True,
            "manifest_id": "release-4.0.0-rc.6-pi-wall4-recovery-20261022",
            "operational_core_sha": "2945bd331f17f99138c1841cdf82c5da5cba4de8",
            "operational_manifest_sha256": "de22c4eb8644ef21fb2f690689ad716226aae1958f385fc83df8221207e6b0de",
            "remote_may_still_be_running": True,
            "result": "RECOVERY_INCONCLUSIVE",
            "root_helper_sha256": "11ce41115c7aa5ac34e568f3ea9008915f342bc3272850b56c61eed19a760ab9",
            "run_attempt": 1,
            "workflow_path": ".github/workflows/recover-rc6-wall4.yml",
            "workflow_run_id": "39695635601",
        },
        "publication_run": "39658681213",
        "readonly_observer_sha256": "4ae5b8fa3297785a362dfb2e36354cffb4168ab2d0572ef169288d559239e36c",
        "recovery_contract_id": "pi-rc6-wall4-recovery-v2",
        "recovery_helper_sha256": "c395af61f47c42633c65013d61853c66c442781832ed4225d035d9209e9f0be2",
        "recovery_workflow_run": "39775941080",
        "release_profile": "INTERNAL_RELEASE",
        "release_version": "4.0.0-rc.6",
        "remote_may_still_be_running": True,
        "result": "RECOVERY_INCONCLUSIVE",
        "schema_version": 1,
        "smoke_contract_id": "pi-rc6-wall4-recovery-readback-v2",
        "target": "rbpi-djconnect",
        "workflow_run_id": "39775941080",
    }
    require(exact_json(record, joined), "PREVIOUS_RECEIPT_JOIN_INVALID")
    # These are actual historical facts, never current cancellation or retry authority.
    return record


def latest_descriptor():
    """Exact historical public descriptor; never current execution authority."""
    value = latest_spec()
    value.pop("evidence_bytes")  # Local evidence metadata is not a contract field.
    value["classification"] = "INCOMPLETE_REQUIRES_ACTUAL_STATE_REVIEW"
    return value


def constant_descriptor(rule):
    """Decode only a bounded, recursively closed constant-object schema."""
    budget = [256]

    def decode(value, depth):
        budget[0] -= 1
        require(
            budget[0] >= 0 and depth <= 8 and isinstance(value, dict),
            "LATEST_FAILURE_SCHEMA_NOT_CLOSED",
        )
        if set(value) == {"const"}:
            literal = value["const"]
            require(
                type(literal) in (str, int, bool), "LATEST_FAILURE_SCHEMA_NOT_CLOSED"
            )
            require(
                not isinstance(literal, str) or len(literal) <= 4096,
                "LATEST_FAILURE_SCHEMA_NOT_CLOSED",
            )
            return literal
        require(
            set(value) == {"type", "additionalProperties", "properties", "required"}
            and value["type"] == "object"
            and value["additionalProperties"] is False,
            "LATEST_FAILURE_SCHEMA_NOT_CLOSED",
        )
        properties = value["properties"]
        required = value["required"]
        require(
            isinstance(properties, dict)
            and 0 < len(properties) <= 64
            and isinstance(required, list)
            and all(isinstance(k, str) and 0 < len(k) <= 128 for k in required)
            and len(required) == len(set(required))
            and set(required) == set(properties),
            "LATEST_FAILURE_SCHEMA_NOT_CLOSED",
        )
        return {key: decode(properties[key], depth + 1) for key in required}

    result = decode(rule, 0)
    require(isinstance(result, dict), "LATEST_FAILURE_SCHEMA_NOT_CLOSED")
    return result


def matches_latest_descriptor(rule):
    """Compatibility equality only; caller still needs released authority and fresh reads."""
    return exact_json(constant_descriptor(rule), latest_descriptor())
