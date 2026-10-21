"""Explicit schema4 single-instance authority. No effects and no V3 fallback."""
from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from types import MappingProxyType

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

CORE_SOURCE = "265f151293735cddcf2e496e6c822f16c7cd2064"
CORE_FINALIZATION = "c8549876df54e22b71ed26fcded4ec822b3d166d"
CONTRACT = "pi-rc6-wall4-recovery-v1"
SMOKE = "pi-rc6-wall4-recovery-readback-v1"
PATH = "docs/release/PLATFORM_4_0_RC6_PI_WALL4_RECOVERY_MANIFEST.json"
CONFIG = ("PI_RC6_WALL4_RECOVERY_CORE_SHA", "PI_RC6_WALL4_RECOVERY_MANIFEST_SHA256")
PINS = {
    "PI_RC6_WALL4_RECOVERY_CONTRACT_V1.md": "45891da6108b271b2b5f1b2086e78d60ab5ec7d31e466390ed90aab519cfcd6e",
    "PI_RC6_WALL4_RECOVERY_REQUEST_V1.schema.json": "dd5a419bb1886dd4199ae917e4b4ee121af4cfe6b076b1f3dcd3b27200352999",
    "PI_RC6_WALL4_RECOVERY_MANIFEST_V1.schema.json": "590e10fb004eb0fdc0f111a6983e5741e9f89fe5fba8cbde45334fe827659185",
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
    validate_schema(request, schemas["PI_RC6_WALL4_RECOVERY_REQUEST_V1.schema.json"], "RECOVERY_REQUEST_INVALID")
    validate_schema(manifest, schemas["PI_RC6_WALL4_RECOVERY_MANIFEST_V1.schema.json"], "RECOVERY_MANIFEST_INVALID")
    require(exact_hex(consumer_sha, 40) and manifest["consumer"]["source_sha"] == consumer_sha
            and consumer_sha not in {SOURCE, "2d7a0ee4e7ac581d04a7e01dac880621aac2e0a6", "7d8758f87d6d56f8f414a940fc4bb23d2e6637c6"}, "RECOVERY_CONSUMER_MISMATCH")
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
    require(manifest["recovery"]["root_helper_sha256"] == HELPER_SHA256, "RECOVERY_HELPER_MISMATCH")
    return Binding(MappingProxyType(dict(request)), MappingProxyType(dict(row)), consumer_sha,
                   "39658681213", asset["artifact_url"], smoke_contract=SMOKE)


class RecoveryAuthority(Authority):
    def receipt(self):
        return {**super().receipt(), "contract_source": CORE_SOURCE,
            "contract_finalization": CORE_FINALIZATION, "recovery_contract_id": CONTRACT,
            "aggregate_disposition": "SINGLE_INSTANCE_RECOVERY_ONLY"}


def current(client, authority):
    raw, _ = fixed_file(client, "main")
    require(hashlib.sha256(raw).hexdigest() == authority.operational_manifest_sha256, "RECOVERY_AUTHORITY_SUPERSEDED")


def resolve(client, request, consumer_sha, configuration):
    pair = operational_pair(*(configuration.get(name, "") for name in CONFIG))
    require(pair[0] != ORIGINAL_CORE and pair[1] != ORIGINAL_MANIFEST_SHA256, "RECOVERY_ORIGINAL_PAIR_REJECTED")
    schemas = contracts()
    validate_schema(request, schemas["PI_RC6_WALL4_RECOVERY_REQUEST_V1.schema.json"], "RECOVERY_REQUEST_INVALID")
    # The protected documentary Final carries the exact normative producer bytes.
    qualified(client, CORE, CORE_SOURCE);qualified(client, CORE, CORE_FINALIZATION)
    qualified(client, CORE, pair[0])
    raw, blob = fixed_file(client, pair[0])
    require(hashlib.sha256(raw).hexdigest() == pair[1], "RECOVERY_OPERATIONAL_BYTES_MISMATCH")
    _raw, current_blob = fixed_file(client, "main")
    require(blob == current_blob, "RECOVERY_AUTHORITY_SUPERSEDED")
    qualified(client, PI, SOURCE);qualified(client, PI, consumer_sha)
    # The consumer must descend from the previously qualified component Final.
    comparison = client.json("repos/"+PI+"/compare/7d8758f87d6d56f8f414a940fc4bb23d2e6637c6..."+consumer_sha+"?per_page=1&page=2")
    require(comparison.get("status") == "ahead"
            and comparison.get("merge_base_commit", {}).get("sha") == "7d8758f87d6d56f8f414a940fc4bb23d2e6637c6", "RECOVERY_CONSUMER_ANCESTRY_INVALID")
    release = client.json("repos/"+PUBLICATION+"/releases/tags/v"+VERSION)
    metadata = release_asset(release, "djconnect-pi-"+VERSION+"-release-manifest.json", 262144)
    binding = validate(request, strict_json(raw), consumer_sha, strict_json(client.asset(metadata["id"], 262144)))
    run = client.json("repos/"+PI+"/actions/runs/39658681213")
    require(run.get("head_sha") == SOURCE and run.get("status") == "completed" and run.get("conclusion") == "success"
            and run.get("path") in {".github/workflows/publish-release.yml", ".github/workflows/publish-release.yml@main"}
            and run.get("repository", {}).get("full_name") == PI, "RECOVERY_PUBLICATION_RUN_MISMATCH")
    artifact = release_asset(release, request["artifact_id"].rsplit(":", 1)[-1], 33554432)
    return RecoveryAuthority(binding, pair[0], pair[1], artifact["id"], artifact["size"])
