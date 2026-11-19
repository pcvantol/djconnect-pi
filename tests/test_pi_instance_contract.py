"""Synthetic semantic joins only: no operational approval or external effects."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

pytest.importorskip("jsonschema", reason="Dedicated locked deployment-tool suite runs these tests")
from Tools import pi_instance_contract as wire

SOURCE = "a" * 40
CONSUMER = "c" * 40


def fixtures(instance="wall-4inch"):
    inventory = wire.pinned_contracts()["PI_WALL_DEVICE_INVENTORY_V1.json"]
    assets = []
    targets = []
    published = {"schema_version": 1, "kind": "djconnect_pi_release_artifact", "candidate_sha": SOURCE,
        "version": wire.VERSION, "release_tag": "v"+wire.VERSION, "platform_version": "4.0", "target": wire.TARGET, "artifacts": {}}
    for index, row in enumerate(inventory["instances"]):
        profile = row["device_profile"];filename = "djconnect-pi-"+profile+"-"+wire.VERSION+".tar.gz"
        target = {key: row[key] for key in ("target", "deployment_instance", "device_profile")};targets.append(target)
        asset = {**target, "owner": "pcvantol/djconnect-pi-releases",
            "artifact_id": "release-asset:pcvantol/djconnect-pi-releases:v"+wire.VERSION+":"+filename,
            "artifact_sha256": str(index+1)*64,
            "artifact_url": "https://github.com/pcvantol/djconnect-pi-releases/releases/download/v"+wire.VERSION+"/"+filename}
        assets.append(asset);published["artifacts"][profile] = {"artifact_id": filename, "artifact_sha256": asset["artifact_sha256"]}
    manifest = {"schema_version": 3, "kind": "platform_release_operational_manifest", "status": "APPROVED_DEPLOYMENT_DISPATCH_PENDING",
        "manifest_id": "release-SYNTHETIC-NOT-AUTHORITY", "candidate_sha": SOURCE, "platform_version": "4.0", "release_version": wire.VERSION,
        "release_profile": "INTERNAL_RELEASE", "generated_at": "2026-10-20T16:00:00Z", "inventory_id": inventory["inventory_id"],
        "inventory_sha256": wire.INVENTORY_SHA256, "consumer": {"repository": "pcvantol/djconnect-pi", "source_sha": CONSUMER, "smoke_contract_id": wire.SMOKE_CONTRACT},
        "approval": {"state": "APPROVED", "approved_at": "2026-10-20T16:00:01Z", "approved_statement": "SYNTHETIC TEST ONLY", "authority_record": "SYNTHETIC NO AUTHORITY"},
        "repositories": [{"repository": "pcvantol/djconnect-pi", "source_sha": SOURCE, "version": wire.VERSION, "artifact_run": "123"}],
        "required_targets": targets, "artifact_bindings": assets, "constraints": ["Synthetic test never permits effects"]}
    asset = next(row for row in assets if row["deployment_instance"] == instance)
    request = {"action": "deployment", "execution_mode": "execute", "manifest_id": manifest["manifest_id"], "candidate_sha": SOURCE,
        "artifact_id": asset["artifact_id"], "artifact_sha256": asset["artifact_sha256"], "target": wire.TARGET,
        "platform_version": "4.0", "release_profile": "INTERNAL_RELEASE", "deployment_instance": instance,
        "device_profile": asset["device_profile"], "inventory_sha256": wire.INVENTORY_SHA256}
    return request, manifest, published


def binding(instance="wall-4inch"):
    request, manifest, published = fixtures(instance)
    return wire.validate_bindings(request, manifest, CONSUMER, published)


@pytest.mark.parametrize("instance", ["wall-4inch", "wall-10inch"])
def test_both_independent_semantic_bindings(instance):
    value = binding(instance)
    assert value.inventory_row["endpoint_config_ref"] == wire.CONFIGURATION_REFS[instance]
    assert value.version == wire.VERSION and value.smoke_contract == wire.SMOKE_CONTRACT
    assert not hasattr(value, "authorized")  # Bindings alone are never authority.


@pytest.mark.parametrize("field", ["action", "execution_mode", "candidate_sha", "manifest_id", "artifact_id", "artifact_sha256", "target", "platform_version", "release_profile", "deployment_instance", "device_profile", "inventory_sha256"])
def test_every_required_request_field(field):
    request, manifest, published = fixtures();del request[field]
    with pytest.raises(wire.BindingError):wire.validate_bindings(request, manifest, CONSUMER, published)


@pytest.mark.parametrize("field,value", [("target", "rbpi5-djconnect"), ("deployment_instance", "unknown"), ("device_profile", "pi5-arm64"),
    ("artifact_sha256", "f"*64), ("candidate_sha", "b"*40), ("manifest_id", "release-OTHER"),
    ("candidate_sha", SOURCE+"\n"), ("artifact_sha256", "F"*64), ("host", "forbidden.invalid"), ("port", 22), ("inventory_sha256", "b"*64)])
def test_wrong_or_free_request_input(field, value):
    request, manifest, published = fixtures();request[field] = value
    with pytest.raises(wire.BindingError):wire.validate_bindings(request, manifest, CONSUMER, published)


@pytest.mark.parametrize("case", ["v1", "duplicate-target", "duplicate-asset", "profile-swap", "source-swap", "consumer-swap", "wrong-inventory", "unapproved", "bad-time", "bad-asset-url", "missing-target"])
def test_manifest_cross_joins(case):
    request, manifest, published = fixtures()
    if case == "v1": manifest["schema_version"] = 1
    elif case == "duplicate-target": manifest["required_targets"][1] = deepcopy(manifest["required_targets"][0])
    elif case == "duplicate-asset": manifest["artifact_bindings"][1] = deepcopy(manifest["artifact_bindings"][0])
    elif case == "profile-swap": manifest["required_targets"][0]["device_profile"] = "pi5-arm64"
    elif case == "source-swap": manifest["repositories"][0]["source_sha"] = "b"*40
    elif case == "consumer-swap": manifest["consumer"]["source_sha"] = "b"*40
    elif case == "wrong-inventory": manifest["inventory_sha256"] = "b"*64
    elif case == "unapproved": manifest["approval"]["state"] = "PENDING"
    elif case == "bad-time": manifest["approval"]["approved_at"] = "not-a-timestamp"
    elif case == "bad-asset-url": manifest["artifact_bindings"][0]["artifact_url"] = "https://fixture.invalid/evil"
    else: manifest["required_targets"].pop()
    with pytest.raises(wire.BindingError):wire.validate_bindings(request, manifest, CONSUMER, published)


@pytest.mark.parametrize("case", ["source", "version", "tag", "target", "profile-missing", "extra-profile", "hash-swap", "filename", "extra-asset-field"])
def test_published_manifest_must_bind_both_profile_assets(case):
    request, manifest, published = fixtures();first = published["artifacts"]["pi-zero-2w-arm64"]
    if case == "source": published["candidate_sha"] = "b"*40
    elif case == "version": published["version"] = "4.0.0-rc.4"
    elif case == "tag": published["release_tag"] = "latest"
    elif case == "target": published["target"] = "other"
    elif case == "profile-missing": del published["artifacts"]["pi5-arm64"]
    elif case == "extra-profile": published["artifacts"]["generic"] = first
    elif case == "hash-swap": first["artifact_sha256"] = "2"*64
    elif case == "filename": first["artifact_id"] = "generic.tar.gz"
    else: first["url_override"] = "forbidden"
    with pytest.raises(wire.BindingError):wire.validate_bindings(request, manifest, CONSUMER, published)


@pytest.mark.parametrize("sha,digest", [("", ""), (SOURCE, ""), ("", "b"*64), (SOURCE+"\n", "b"*64), (SOURCE, "B"*64)])
def test_closed_operational_pair(sha, digest):
    with pytest.raises(wire.BindingError):wire.operational_pair(sha, digest)


def test_valid_operational_pair_does_not_claim_approval():
    assert wire.operational_pair(SOURCE, "b"*64) == (SOURCE, "b"*64)


@pytest.mark.parametrize("raw", [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}', b'[]', b'null', b'{', b' '*262145])
def test_strict_json_rejects_ambiguous_nonfinite_and_oversize(raw):
    with pytest.raises(wire.BindingError):wire.strict_json(raw)


@pytest.mark.parametrize("field", ["hostname", "architecture", "model", "device_profile", "ssh_host_key_type", "ssh_host_key_sha256", "challenge", "private_endpoint"])
def test_fresh_identity_mismatch_or_extra_private_data_fails(field):
    value = binding();challenge = "x"*32
    observed = {key: value.inventory_row[key] for key in ("hostname", "architecture", "model", "device_profile", "ssh_host_key_type", "ssh_host_key_sha256")}
    observed["challenge"] = challenge;observed[field] = "wrong"
    with pytest.raises(wire.BindingError, match="TARGET_NOT_READY"):wire.validate_identity(value, observed, challenge)


@pytest.mark.parametrize("instance", ["wall-4inch", "wall-10inch"])
def test_matching_identity_and_installed_smoke_joins(instance):
    value = binding(instance);challenge = "x"*32
    observed = {key: value.inventory_row[key] for key in ("hostname", "architecture", "model", "device_profile", "ssh_host_key_type", "ssh_host_key_sha256")}
    wire.validate_identity(value, {**observed, "challenge": challenge}, challenge)
    deployment = {**value.public_join(), "deployment_workflow_run": "321", "result": "DEPLOYED_PENDING_SMOKE"}
    smoke = {**value.public_join(), "deployment_workflow_run": "321", "result": "SMOKE_PASS", "installed_source": SOURCE,
        "installed_version": wire.VERSION, "installed_device_profile": value.request["device_profile"],
        "api_reachable": True, "client_active": True, "api_active": True}
    wire.validate_smoke_join(value, deployment, smoke, "321")


@pytest.mark.parametrize("field", ["candidate_sha", "artifact_id", "artifact_sha256", "manifest_id", "target", "deployment_instance", "device_profile", "inventory_sha256", "consumer_sha", "smoke_contract_id", "deployment_workflow_run", "installed_source", "installed_version", "installed_device_profile", "api_reachable", "client_active", "api_active"])
def test_wrong_instance_source_asset_run_or_health_is_not_smoke_pass(field):
    value = binding();deployment = {**value.public_join(), "deployment_workflow_run": "321", "result": "DEPLOYED_PENDING_SMOKE"}
    smoke = {**value.public_join(), "deployment_workflow_run": "321", "result": "SMOKE_PASS", "installed_source": SOURCE,
        "installed_version": wire.VERSION, "installed_device_profile": value.request["device_profile"], "api_reachable": True, "client_active": True, "api_active": True}
    smoke[field] = "wrong"
    with pytest.raises(wire.BindingError):wire.validate_smoke_join(value, deployment, smoke, "321")


def test_pinned_producer_bytes_cannot_be_rewritten(tmp_path: Path):
    for name in wire.PINNED_FILES:
        (tmp_path/name).write_bytes((Path(wire.__file__).with_name("pi_contract")/name).read_bytes())
    (tmp_path/"PI_WALL_DEVICE_INVENTORY_V1.json").write_bytes(b'{}')
    with pytest.raises(wire.BindingError, match="PRODUCER_PIN_MISMATCH"):wire.pinned_contracts(tmp_path)


def test_successful_pure_binding_is_immutable():
    value = binding()
    with pytest.raises(TypeError): value.request["deployment_instance"] = "other"
    with pytest.raises(TypeError): value.inventory_row["hostname"] = "other"


@pytest.mark.parametrize("results", [{}, {"wall-4inch": "SMOKE_PASS"}, {"wall-10inch": "SMOKE_PASS"},
    {"wall-4inch": "SMOKE_PASS", "wall-10inch": "SMOKE_INCONCLUSIVE"},
    {"wall-4inch": "SMOKE_FAIL", "wall-10inch": "SMOKE_PASS"}])
def test_partial_or_failed_instances_are_not_overall_operational(results):
    assert wire.overall_smoke(results) == "DEPLOYMENT_SMOKE_FAILED"


def test_both_smokes_are_required_for_operational_result():
    assert wire.overall_smoke({"wall-4inch": "SMOKE_PASS", "wall-10inch": "SMOKE_PASS"}) == "DEPLOYMENT_OPERATIONAL"


@pytest.mark.parametrize("version", [1, 2, True, "3", 4])
def test_rc6_rejects_every_old_or_noninteger_manifest_schema(version):
    request, manifest, published = fixtures()
    manifest["schema_version"] = version
    with pytest.raises(wire.BindingError, match="MANIFEST_SCHEMA_INVALID"):
        wire.validate_bindings(request, manifest, CONSUMER, published)


@pytest.mark.parametrize("value", ["4.0.0-rc.1", "4.0.0-rc.2", "4.0.0-rc.5", "4.0.0-rc.7"])
def test_rc6_does_not_autodetect_another_release(value):
    request, manifest, published = fixtures()
    manifest["release_version"] = value
    with pytest.raises(wire.BindingError): wire.validate_bindings(request, manifest, CONSUMER, published)


@pytest.mark.parametrize("field", ["generated_at", "approved_at"])
@pytest.mark.parametrize("value", ["2026-02-30T01:00:00Z", "2026-10-21T25:00:00Z", "2026-10-21T00:00:00+25:00", "2026-10-21T00:00:00", "not-a-date", True])
def test_rfc3339_is_really_parsed_without_optional_format_checker(field, value):
    request, manifest, published = fixtures()
    if field == "approved_at":manifest["approval"][field] = value
    else:manifest[field] = value
    with pytest.raises(wire.BindingError): wire.validate_bindings(request, manifest, CONSUMER, published)


def test_preserved_rc5_schema_cannot_admit_rc6_manifest():
    import json
    _request, manifest, _published = fixtures()
    old = json.loads((Path(wire.__file__).with_name("pi_contract")/"PI_TWO_HOST_OPERATIONAL_MANIFEST_V2.schema.json").read_bytes())
    with pytest.raises(wire.BindingError): wire.validate_schema(manifest, old, "OLD_SCHEMA_REJECTS_RC6")
