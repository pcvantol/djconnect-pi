"""Explicit schema5 single-instance authority. No effects and no V3 fallback."""
from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from types import MappingProxyType

from Tools import pi_json_equivalence
from Tools.pi_instance_authority import (
    CORE,
    PI,
    PUBLICATION,
    Authority,
    qualified,
    release_asset,
)
from Tools.pi_instance_contract import (
    INVENTORY_SHA256,
    VERSION,
    Binding,
    BindingError,
    exact_hex,
    operational_pair,
    pinned_contracts,
    require,
    strict_json,
    timestamp,
    validate_schema,
)
from Tools.pi_rc6_recovery import HELPER_SHA256, ORIGINAL_CORE, ORIGINAL_MANIFEST_SHA256
from Tools.pi_rc6_recovery_root import ARTIFACT_SHA256, PROFILE, SOURCE
from Tools.pi_wall4_latest_failure import constant_descriptor
from Tools.pi_wall4_recovery_observer_pin import OBSERVER_SHA256

exact_json = pi_json_equivalence.exact_json

CORE_SOURCE = "5cf78c1c83936cc9ed2feb750f83cf743b643b90"
CORE_FINALIZATION = "659bfe752dff0dcdcdbfc475be52bdf69090e085"
CONTRACT = "pi-rc6-wall4-recovery-v2"
SMOKE = "pi-rc6-wall4-recovery-readback-v2"
PATH = "docs/release/PLATFORM_4_0_RC6_PI_WALL4_RECOVERY_V2_MANIFEST.json"
CONFIG = ("PI_RC6_WALL4_RECOVERY_V2_CORE_SHA", "PI_RC6_WALL4_RECOVERY_V2_MANIFEST_SHA256")
PINS = {
    "PI_RC6_WALL4_RECOVERY_CONTRACT_V2.md": "4db98de3fa0dc6547b1399e20e487cd24ddbff81a6761b35aabbbb306eb9f048",
    "PI_RC6_WALL4_RECOVERY_REQUEST_V2.schema.json": "92e1e182d768d9f7fecad1a7433ac6a29ece0ff90084ae855fb6fb674e21ea6d",
    "PI_RC6_WALL4_RECOVERY_MANIFEST_V2.schema.json": "028dcd0fcde83edd8e568805f12861a80a60657363d4151f4de4e72d12aa8967",
}


def contracts():
    result = {}
    for name, digest in PINS.items():
        with (Path(__file__).with_name("pi_contract")/name).open("rb") as stream:
            raw = stream.read(262145)
        require(len(raw) <= 262144 and hashlib.sha256(raw).hexdigest() == digest, "RECOVERY_PRODUCER_PIN_MISMATCH")
        if name.endswith(".json"):result[name] = strict_json(raw)
    return result


def fixed_file(client, revision):
    require(revision == "main" or exact_hex(revision, 40), "RECOVERY_REFERENCE_INVALID")
    x = client.json("repos/"+CORE+"/contents/"+PATH+"?ref="+revision)
    require(x.get("type") == "file" and x.get("path") == PATH and x.get("encoding") == "base64"
            and isinstance(x.get("content"), str) and len(x["content"]) <= 360000, "RECOVERY_FILE_INVALID")
    try:raw = base64.b64decode("".join(x["content"].splitlines()), validate=True)
    except ValueError:raise BindingError("RECOVERY_FILE_INVALID") from None
    require(len(raw) <= 262144, "RECOVERY_FILE_INVALID")
    blob = hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw, usedforsecurity=False).hexdigest()
    require(x.get("sha") == blob, "RECOVERY_BLOB_MISMATCH")
    return raw, blob


def validate(request, manifest, consumer_sha, published):
    schemas = contracts()
    validate_schema(request, schemas["PI_RC6_WALL4_RECOVERY_REQUEST_V2.schema.json"], "RECOVERY_REQUEST_INVALID")
    validate_schema(manifest, schemas["PI_RC6_WALL4_RECOVERY_MANIFEST_V2.schema.json"], "RECOVERY_MANIFEST_INVALID")
    require(exact_hex(consumer_sha, 40) and manifest["consumer"]["source_sha"] == consumer_sha
            and consumer_sha not in {SOURCE, "2d7a0ee4e7ac581d04a7e01dac880621aac2e0a6", "7d8758f87d6d56f8f414a940fc4bb23d2e6637c6",
                                     "042cf36479e6c4d1c42cebd19acd3bdd00cfef79", "77fc4047f797066876c5345e8e43b346ab96d782"}, "RECOVERY_CONSUMER_MISMATCH")
    timestamp(manifest["generated_at"]);timestamp(manifest["approval"]["approved_at"])
    for name in ("manifest_id", "candidate_sha", "platform_version", "release_profile", "inventory_sha256"):
        require(request[name] == manifest[name], "RECOVERY_REQUEST_MANIFEST_MISMATCH")
    inventory = pinned_contracts()["PI_WALL_DEVICE_INVENTORY_V1.json"]
    require(manifest["inventory_id"] == inventory["inventory_id"] and request["inventory_sha256"] == INVENTORY_SHA256,
            "RECOVERY_INVENTORY_MISMATCH")
    matches = [row for row in inventory["instances"] if row["deployment_instance"] == "wall-4inch"]
    require(len(matches) == 1, "RECOVERY_INVENTORY_MISMATCH")
    row = matches[0];asset = manifest["artifact_bindings"][0]
    for name in ("target", "deployment_instance", "device_profile"):
        require(request[name] == row[name] == manifest["required_targets"][0][name] == asset[name], "RECOVERY_TARGET_MISMATCH")
    require(all(request[name] == asset[name] for name in ("artifact_id", "artifact_sha256")), "RECOVERY_ARTIFACT_MISMATCH")
    require(isinstance(published, dict) and published.get("candidate_sha") == SOURCE
            and published.get("version") == VERSION and published.get("release_tag") == "v"+VERSION
            and published.get("target") == "rbpi-djconnect" and published.get("platform_version") == "4.0"
            and published.get("kind") == "djconnect_pi_release_artifact"
            and type(published.get("schema_version")) is int and published["schema_version"] == 1,
            "RECOVERY_PUBLICATION_INVALID")
    assets = published.get("artifacts")
    require(isinstance(assets, dict) and set(assets) == {"pi-zero-2w-arm64", "pi5-arm64"}, "RECOVERY_PUBLICATION_INVALID")
    require(assets[PROFILE] == {"artifact_id": asset["artifact_id"].rsplit(":", 1)[-1], "artifact_sha256": ARTIFACT_SHA256},
            "RECOVERY_PUBLICATION_MISMATCH")
    require(manifest["recovery"]["root_helper_sha256"] == HELPER_SHA256
            and manifest["recovery"]["readonly_observer_sha256"] == OBSERVER_SHA256, "RECOVERY_HELPER_MISMATCH")
    return Binding(MappingProxyType(dict(request)), MappingProxyType(dict(row)), consumer_sha,
                   "39658681213", asset["artifact_url"], smoke_contract=SMOKE)


class RecoveryAuthority(Authority):
    def receipt(self):
        return {**super().receipt(), "contract_source": CORE_SOURCE,
            "contract_finalization": CORE_FINALIZATION, "recovery_contract_id": CONTRACT,
            "aggregate_disposition": "SINGLE_INSTANCE_RECOVERY_ONLY",
            "previous_recovery_attempt": previous_spec(), "readonly_observer_sha256": OBSERVER_SHA256,
            "claim_policy": "UNCHANGED_LEDGER_EXCLUSIVE_DURABLE_CREATE_BEFORE_EFFECTS"}


def current(client, authority):
    raw, _ = fixed_file(client, "main")
    require(hashlib.sha256(raw).hexdigest() == authority.operational_manifest_sha256, "RECOVERY_AUTHORITY_SUPERSEDED")


def resolve(client, request, consumer_sha, configuration):
    pair = operational_pair(*(configuration.get(name, "") for name in CONFIG))
    require(pair[0] not in {ORIGINAL_CORE, "2945bd331f17f99138c1841cdf82c5da5cba4de8"}
            and pair[1] not in {ORIGINAL_MANIFEST_SHA256, "de22c4eb8644ef21fb2f690689ad716226aae1958f385fc83df8221207e6b0de"},
            "RECOVERY_ORIGINAL_PAIR_REJECTED")
    schemas = contracts()
    validate_schema(request, schemas["PI_RC6_WALL4_RECOVERY_REQUEST_V2.schema.json"], "RECOVERY_REQUEST_INVALID")
    # The protected documentary Final carries the exact normative producer bytes.
    qualified(client, CORE, CORE_SOURCE);qualified(client, CORE, CORE_FINALIZATION)
    qualified(client, CORE, pair[0])
    raw, blob = fixed_file(client, pair[0])
    require(hashlib.sha256(raw).hexdigest() == pair[1], "RECOVERY_OPERATIONAL_BYTES_MISMATCH")
    _raw, current_blob = fixed_file(client, "main")
    require(blob == current_blob, "RECOVERY_AUTHORITY_SUPERSEDED")
    qualified(client, PI, SOURCE);qualified(client, PI, consumer_sha)
    # The consumer must descend from the actually qualified previous V1 consumer Final.
    comparison = client.json("repos/"+PI+"/compare/77fc4047f797066876c5345e8e43b346ab96d782..."+consumer_sha+"?per_page=1&page=2")
    require(comparison.get("status") == "ahead"
            and comparison.get("merge_base_commit", {}).get("sha") == "77fc4047f797066876c5345e8e43b346ab96d782", "RECOVERY_CONSUMER_ANCESTRY_INVALID")
    release = client.json("repos/"+PUBLICATION+"/releases/tags/v"+VERSION)
    metadata = release_asset(release, "djconnect-pi-"+VERSION+"-release-manifest.json", 262144)
    binding = validate(request, strict_json(raw), consumer_sha, strict_json(client.asset(metadata["id"], 262144)))
    run = client.json("repos/"+PI+"/actions/runs/39658681213")
    require(run.get("head_sha") == SOURCE and run.get("status") == "completed" and run.get("conclusion") == "success"
            and run.get("path") in {".github/workflows/publish-release.yml", ".github/workflows/publish-release.yml@main"}
            and run.get("repository", {}).get("full_name") == PI, "RECOVERY_PUBLICATION_RUN_MISMATCH")
    artifact = release_asset(release, request["artifact_id"].rsplit(":", 1)[-1], 33554432)
    return RecoveryAuthority(binding, pair[0], pair[1], artifact["id"], artifact["size"])


def previous_spec():
    """Fresh public constants from exact protected V2 bytes, never caller inputs."""
    schema = contracts()["PI_RC6_WALL4_RECOVERY_MANIFEST_V2.schema.json"]
    rule = schema["properties"]["recovery"]["properties"]["previous_recovery_attempt"]
    return constant_descriptor(rule)
