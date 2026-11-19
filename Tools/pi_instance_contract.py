"""Pure, fail-closed Pi two-instance bindings. This module never authorizes effects.

A protected workflow must independently establish current immutable producer,
consumer, publication and approval provenance before using these bindings.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

CORE_SOURCE = "802619ac1ab3ec11eace7a8609167018193bb98e"
CORE_FINALIZATION = "5c34c37bab2b73744f9dbe8832449ef4ab211a02"
INVENTORY_SHA256 = "530220ee38f6ccbcc824a78331b9dd89f236a5fa6ede12ebf7899dac83ff50c0"
SMOKE_CONTRACT = "pi-rc6-instance-readback-v1"
VERSION = "4.0.0-rc.6"
TARGET = "rbpi-djconnect"
OPERATIONAL_PATH = "docs/release/PLATFORM_4_0_RC6_PI_OPERATIONAL_MANIFEST.json"
PINNED_FILES = {'PI_TWO_HOST_DEPLOYMENT_CONTRACT_V2.md': '22a13aecd6f0bc5a19f368fe1b7d74d8419825df4f155b5c52c1f152106485b8', 'PI_TWO_HOST_DEPLOYMENT_REQUEST_V3.schema.json': '2f143afade9cb61c9b45e3ba58ebd90bdbfc3a2a3bbf7ca39d34353df97b9301', 'PI_TWO_HOST_OPERATIONAL_MANIFEST_V3.schema.json': '5739253ea065dae216edbb21023516309d2377f14e8bf803964b1dde41383412', 'PI_WALL_DEVICE_INVENTORY_V1.json': '530220ee38f6ccbcc824a78331b9dd89f236a5fa6ede12ebf7899dac83ff50c0'}
CONFIGURATION_REFS = {"wall-4inch": "djconnect-wall-4inch", "wall-10inch": "djconnect-pi10"}


class BindingError(ValueError):
    """Only static codes; never private JSON, URLs, credentials or endpoint values."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise BindingError(code)


def exact_hex(value: Any, length: int) -> bool:
    return isinstance(value, str) and re.fullmatch("[0-9a-f]{"+str(length)+"}", value) is not None


def strict_json(raw: bytes, maximum: int = 262144) -> dict:
    require(isinstance(raw, bytes) and len(raw) <= maximum, "JSON_SIZE_INVALID")
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "JSON_DUPLICATE_KEY")
            result[key] = value
        return result
    def nonfinite(_):
        raise BindingError("JSON_NONFINITE")
    def finite_float(text):
        value = float(text)
        require(math.isfinite(value), "JSON_NONFINITE")
        return value
    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite, parse_float=finite_float)
    except (ValueError, TypeError, RecursionError):
        raise BindingError("JSON_INVALID") from None
    require(isinstance(value, dict), "JSON_OBJECT_REQUIRED")
    return value


def pinned_contracts(directory: Path | None = None) -> dict:
    directory = directory or Path(__file__).with_name("pi_contract")
    loaded = {}
    for name, expected in PINNED_FILES.items():
        with (directory / name).open("rb") as stream:
            raw = stream.read(262145)
        require(len(raw) <= 262144 and hashlib.sha256(raw).hexdigest() == expected, "PRODUCER_PIN_MISMATCH")
        if name.endswith(".json"):
            loaded[name] = strict_json(raw)
    return loaded


def operational_pair(core_sha: str, manifest_sha256: str) -> tuple[str, str]:
    # Values come from one fixed protected run configuration snapshot, never inputs.
    require(exact_hex(core_sha, 40) and exact_hex(manifest_sha256, 64), "OPERATIONAL_PAIR_NOT_READY")
    return core_sha, manifest_sha256


def validate_schema(value: dict, schema: dict, code: str) -> None:
    try:
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(value)
    except (ValidationError, TypeError, ValueError, RecursionError):
        raise BindingError(code) from None


def timestamp(value: str) -> None:
    require(isinstance(value, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})", value) is not None, "APPROVAL_TIME_INVALID")
    try:
        require(datetime.fromisoformat(value).tzinfo is not None, "APPROVAL_TIME_INVALID")
    except ValueError:
        raise BindingError("APPROVAL_TIME_INVALID") from None


@dataclass(frozen=True)
class Binding:
    request: Mapping
    inventory_row: Mapping
    consumer_sha: str
    publication_run: str
    artifact_url: str
    version: str = VERSION
    smoke_contract: str = SMOKE_CONTRACT

    def public_join(self) -> dict:
        return {**{key: value for key, value in self.request.items() if key not in {"action", "execution_mode"}}, "consumer_sha": self.consumer_sha,
                "release_version": self.version, "smoke_contract_id": self.smoke_contract}


def validate_bindings(request: dict, manifest: dict, consumer_sha: str, published: dict) -> Binding:
    """Schema+semantic validation only; APPROVED text is never proof of authority."""
    contracts = pinned_contracts()
    validate_schema(request, contracts["PI_TWO_HOST_DEPLOYMENT_REQUEST_V3.schema.json"], "REQUEST_SCHEMA_INVALID")
    validate_schema(manifest, contracts["PI_TWO_HOST_OPERATIONAL_MANIFEST_V3.schema.json"], "MANIFEST_SCHEMA_INVALID")
    require(exact_hex(consumer_sha, 40) and manifest["consumer"]["source_sha"] == consumer_sha, "CONSUMER_MISMATCH")
    for field in ("manifest_id", "candidate_sha", "platform_version", "release_profile", "inventory_sha256"):
        require(request[field] == manifest[field], "REQUEST_MANIFEST_MISMATCH")
    require(manifest["repositories"][0]["source_sha"] == request["candidate_sha"], "SOURCE_MISMATCH")
    timestamp(manifest["generated_at"]);timestamp(manifest["approval"]["approved_at"])
    inventory = contracts["PI_WALL_DEVICE_INVENTORY_V1.json"]
    require(manifest["inventory_id"] == inventory["inventory_id"], "INVENTORY_MISMATCH")
    rows = {row["deployment_instance"]: row for row in inventory["instances"]}
    require(set(rows) == set(CONFIGURATION_REFS), "INVENTORY_INSTANCES_INVALID")
    for instance, row in rows.items():
        require(row["endpoint_config_ref"] == CONFIGURATION_REFS[instance], "CONFIGURATION_REF_MISMATCH")
    targets = {row["deployment_instance"]: row for row in manifest["required_targets"]}
    assets = {row["deployment_instance"]: row for row in manifest["artifact_bindings"]}
    require(len(targets) == len(assets) == 2 and set(targets) == set(assets) == set(rows), "INSTANCE_SET_INVALID")
    require(isinstance(published, dict) and published.get("candidate_sha") == request["candidate_sha"]
            and published.get("version") == VERSION and published.get("release_tag") == "v"+VERSION
            and published.get("target") == TARGET and published.get("platform_version") == "4.0"
            and published.get("kind") == "djconnect_pi_release_artifact"
            and type(published.get("schema_version")) is int and published["schema_version"] == 1,
            "PUBLICATION_SOURCE_INVALID")
    require(isinstance(published.get("artifacts"), dict)
            and set(published["artifacts"]) == {row["device_profile"] for row in rows.values()}, "PUBLICATION_PROFILES_INVALID")
    for instance, asset in assets.items():
        row = rows[instance];target = targets[instance]
        require(target["target"] == asset["target"] == row["target"] == TARGET
                and target["device_profile"] == asset["device_profile"] == row["device_profile"], "PROFILE_JOIN_INVALID")
        profile_asset = published["artifacts"][row["device_profile"]]
        require(isinstance(profile_asset, dict) and set(profile_asset) == {"artifact_id", "artifact_sha256"}, "PUBLICATION_ASSET_INVALID")
        filename = asset["artifact_id"].rsplit(":", 1)[-1]
        require(profile_asset["artifact_id"] == filename
                and profile_asset["artifact_sha256"] == asset["artifact_sha256"], "PUBLICATION_ASSET_MISMATCH")
    instance = request["deployment_instance"];row = rows[instance];asset = assets[instance]
    require(request["device_profile"] == row["device_profile"]
            and request["artifact_id"] == asset["artifact_id"]
            and request["artifact_sha256"] == asset["artifact_sha256"], "SELECTED_BINDING_MISMATCH")
    return Binding(MappingProxyType(dict(request)), MappingProxyType(dict(row)), consumer_sha, manifest["repositories"][0]["artifact_run"], asset["artifact_url"])


def validate_identity(binding: Binding, observed: dict, challenge: str) -> None:
    fields = {"hostname", "architecture", "model", "device_profile", "ssh_host_key_type", "ssh_host_key_sha256"}
    require(isinstance(observed, dict) and set(observed) == fields | {"challenge"}
            and isinstance(challenge, str) and len(challenge) >= 32 and observed["challenge"] == challenge,
            "TARGET_NOT_READY")
    require(all(observed[field] == binding.inventory_row[field] for field in fields), "TARGET_NOT_READY")


def recovered_deployment(binding: Binding, record: dict, run_id: str) -> bool:
    # A new successful recovery is distinct from the retained failed deployment.
    return (binding.smoke_contract == "pi-rc6-wall4-recovery-readback-v1"
        and isinstance(record, dict) and binding.request["deployment_instance"] == "wall-4inch"
        and binding.request["candidate_sha"] == "0dde0abe22a0859f170a7c1d3eab41f1ade44d37"
        and binding.request["artifact_sha256"] == "d67869ffca53c4936059bdbbdbdf6be63b36eafac269fa2f3f9b090922cd0d64"
        and record.get("kind") == "djconnect_pi_recovery_evidence"
        and record.get("result") == "RECOVERED_PENDING_SMOKE"
        and record.get("original_deployment_workflow_run") == "39669504016"
        and record.get("deployment_workflow_run") == run_id and record.get("recovery_workflow_run") == run_id
        and run_id != "39669504016" and record.get("watchdog_restored") is True
        and record.get("configuration_preserved_by_installer") is True
        and type(record.get("verified_packaged_files")) is int and record["verified_packaged_files"] == 80
        and record.get("recovery_helper_sha256") == "11ce41115c7aa5ac34e568f3ea9008915f342bc3272850b56c61eed19a760ab9")


def validate_smoke_join(binding: Binding, deployment: dict, smoke: dict, run_id: str) -> None:
    require(isinstance(run_id, str) and re.fullmatch(r"[1-9][0-9]*", run_id) is not None, "DEPLOYMENT_RUN_INVALID")
    expected = binding.public_join()
    require(isinstance(deployment, dict) and deployment.get("result") == "DEPLOYED_PENDING_SMOKE" and deployment.get("deployment_workflow_run") == run_id, "DEPLOYMENT_EVIDENCE_INVALID")
    require(isinstance(smoke, dict) and smoke.get("result") == "SMOKE_PASS" and smoke.get("deployment_workflow_run") == run_id, "SMOKE_RUN_MISMATCH")
    require(all(deployment.get(key) == value and smoke.get(key) == value for key, value in expected.items()), "SMOKE_BINDING_MISMATCH")
    require(smoke.get("installed_source") == expected["candidate_sha"]
            and smoke.get("installed_version") == binding.version
            and smoke.get("installed_device_profile") == expected["device_profile"]
            and smoke.get("api_reachable") is True and smoke.get("client_active") is True
            and smoke.get("api_active") is True, "SMOKE_TARGET_NOT_READY")


def overall_smoke(results: dict) -> str:
    return "DEPLOYMENT_OPERATIONAL" if (set(results) == set(CONFIGURATION_REFS)
        and all(value == "SMOKE_PASS" for value in results.values())) else "DEPLOYMENT_SMOKE_FAILED"
