"""Synthetic authority fixtures never authorize a real recovery."""
from __future__ import annotations

import base64
import hashlib
import json
from copy import deepcopy

import pytest

pytest.importorskip("jsonschema", reason="Dedicated locked deployment-tool suite")
from test_pi_instance_contract import CONSUMER
from test_pi_instance_contract import fixtures as old_fixtures

from Tools import pi_wall4_recovery_authority as wire
from Tools.pi_instance_contract import BindingError, strict_json, validate_bindings
from Tools.pi_rc6_recovery import HELPER_SHA256, ORIGINAL_CORE, ORIGINAL_MANIFEST_SHA256


def fixtures():
    request, manifest, published = old_fixtures()
    manifest.update(schema_version=4, kind="platform_release_recovery_operational_manifest",
        manifest_id="release-4.0.0-rc.6-pi-wall4-recovery-SYNTHETIC", candidate_sha=wire.SOURCE)
    manifest["consumer"].update(smoke_contract_id=wire.SMOKE, recovery_contract_id=wire.CONTRACT)
    manifest["repositories"][0].update(source_sha=wire.SOURCE, artifact_run="39658681213")
    manifest["required_targets"] = manifest["required_targets"][:1]
    manifest["artifact_bindings"] = manifest["artifact_bindings"][:1]
    manifest["artifact_bindings"][0]["artifact_sha256"] = wire.ARTIFACT_SHA256
    manifest["recovery"] = {"operation":"recover", "contract_id":wire.CONTRACT,
        "workflow_path":".github/workflows/recover-rc6-wall4.yml",
        "smoke_workflow_path":".github/workflows/smoke-rc6-wall4-recovery.yml", "manifest_path":wire.PATH,
        "original_deployment_run":"39669504016", "original_candidate_sha":wire.SOURCE,
        "original_core_sha":ORIGINAL_CORE, "original_manifest_sha256":ORIGINAL_MANIFEST_SHA256,
        "root_helper_sha256":HELPER_SHA256, "aggregate_disposition":"SINGLE_INSTANCE_RECOVERY_ONLY"}
    request.update(candidate_sha=wire.SOURCE, manifest_id=manifest["manifest_id"], artifact_sha256=wire.ARTIFACT_SHA256)
    published.update(candidate_sha=wire.SOURCE)
    published["artifacts"][wire.PROFILE]["artifact_sha256"] = wire.ARTIFACT_SHA256
    return request, manifest, published


def authority():
    req, manifest, published = fixtures()
    return wire.RecoveryAuthority(wire.validate(req, manifest, CONSUMER, published), "d"*40, "e"*64, 1, 100)


def test_closed_binding_and_both_immutable_producer_pins():
    req, manifest, pub = fixtures();b = wire.validate(req, manifest, CONSUMER, pub)
    assert b.smoke_contract == wire.SMOKE and b.publication_run == "39658681213"
    assert b.inventory_row["hostname"] == "rbpi-djconnect"
    assert len(wire.contracts()) == 2
    with pytest.raises(TypeError):b.request["target"] = "other"
    assert authority().receipt()["contract_source"] == wire.CORE_SOURCE
    assert authority().receipt()["aggregate_disposition"] == "SINGLE_INSTANCE_RECOVERY_ONLY"


@pytest.mark.parametrize("field", sorted(fixtures()[0]))
def test_each_missing_transport_field_fails_closed(field):
    req, manifest, pub = fixtures();del req[field]
    with pytest.raises(BindingError):wire.validate(req, manifest, CONSUMER, pub)


@pytest.mark.parametrize("case", ["Pi10", "profile", "action", "mode", "host", "path", "oldmanifest", "hash", "source", "inventory", "manifestjoin"])
def test_request_has_no_target_host_action_or_old_manifest_fallback(case):
    req, manifest, pub = fixtures()
    key, value = {"Pi10":("deployment_instance","wall-10inch"), "profile":("device_profile","pi5-arm64"),
        "action":("action","recover"), "mode":("execution_mode","dry-run"), "host":("host","fixture.invalid"),
        "path":("manifest_path",wire.PATH), "oldmanifest":("manifest_id","release-4.0.0-rc.6-pi-two-instance-20261021"),
        "hash":("artifact_sha256","f"*64), "source":("candidate_sha","a"*40), "inventory":("inventory_sha256","f"*64),
        "manifestjoin":("manifest_id",req["manifest_id"]+"OTHER")}[case]
    req[key] = value
    with pytest.raises(BindingError):wire.validate(req, manifest, CONSUMER, pub)


@pytest.mark.parametrize("field", sorted(fixtures()[1]))
def test_each_required_manifest_field(field):
    req, manifest, pub = fixtures();del manifest[field]
    with pytest.raises(BindingError):wire.validate(req, manifest, CONSUMER, pub)


@pytest.mark.parametrize("section", [None, "consumer", "approval", "recovery", "repositories", "required_targets", "artifact_bindings"])
def test_unknown_fields_at_every_object_level_fail_closed(section):
    req, manifest, pub = fixtures()
    obj = manifest if section is None else manifest[section]
    if isinstance(obj, list):obj = obj[0]
    obj["unknown"] = "not authority"
    with pytest.raises(BindingError):wire.validate(req, manifest, CONSUMER, pub)


@pytest.mark.parametrize("section", ["required_targets", "artifact_bindings", "repositories"])
@pytest.mark.parametrize("case", ["missing", "duplicate", "Pi10"])
def test_exactly_one_original_target_and_source(section, case):
    req, manifest, pub = fixtures()
    if case == "missing":manifest[section] = []
    elif case == "duplicate":manifest[section] *= 2
    else:manifest[section][0]["deployment_instance"] = "wall-10inch"
    with pytest.raises(BindingError):wire.validate(req, manifest, CONSUMER, pub)


@pytest.mark.parametrize("field", sorted(fixtures()[1]["recovery"]))
def test_every_recovery_provenance_discriminator_is_closed(field):
    req, manifest, pub = fixtures();manifest["recovery"][field] += "OTHER"
    with pytest.raises(BindingError):wire.validate(req, manifest, CONSUMER, pub)


@pytest.mark.parametrize("field", ["generated_at", "approved_at"])
@pytest.mark.parametrize("value", ["2026-10-21T22:00:00", "2026-02-30T22:00:00Z", "2026-10-21T22:00:00+99:99", "not a time", 1, None])
def test_actual_rfc3339_validation_not_schema_annotation_only(field, value):
    req, manifest, pub = fixtures()
    if field == "generated_at":manifest[field] = value
    else:manifest["approval"][field] = value
    with pytest.raises(BindingError):wire.validate(req, manifest, CONSUMER, pub)


def test_v3_and_v4_cannot_be_used_as_each_others_authority():
    req, old, pub = old_fixtures()
    with pytest.raises(BindingError):wire.validate(req, old, CONSUMER, pub)
    req, manifest, pub = fixtures()
    with pytest.raises(BindingError):validate_bindings(req, manifest, CONSUMER, pub)


@pytest.mark.parametrize("consumer", [wire.SOURCE, "2d7a0ee4e7ac581d04a7e01dac880621aac2e0a6", "7d8758f87d6d56f8f414a940fc4bb23d2e6637c6", "f"*40])
def test_component_or_wrong_consumer_cannot_be_promoted(consumer):
    req, manifest, pub = fixtures()
    with pytest.raises(BindingError):wire.validate(req, manifest, consumer, pub)


@pytest.mark.parametrize("raw", [b'{"schema_version":4,"schema_version":4}', b'{"x":NaN}', b'{"x":Infinity}', b'{"x":1e999}', b'[]', b'{"x":'+b' '*262144+b'1}'])
def test_strict_json_duplicate_nonfinite_and_bounds(raw):
    with pytest.raises(BindingError):strict_json(raw)


@pytest.mark.parametrize("pair", [{}, {wire.CONFIG[0]:"d"*40}, {wire.CONFIG[1]:"e"*64},
    {"PI_RC6_OPERATIONAL_CORE_SHA":"d"*40,"PI_RC6_OPERATIONAL_MANIFEST_SHA256":"e"*64},
    {wire.CONFIG[0]:ORIGINAL_CORE,wire.CONFIG[1]:ORIGINAL_MANIFEST_SHA256}])
def test_no_old_partial_or_caller_pair_before_network(pair):
    class Client:
        def json(self, path):raise AssertionError("must reject before network")
    with pytest.raises(BindingError):wire.resolve(Client(), fixtures()[0], CONSUMER, pair)


def test_fixed_path_is_separate_and_blob_verified():
    raw = json.dumps(fixtures()[1]).encode()
    blob = hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    class Client:
        def __init__(self):self.path = None
        def json(self, path):
            self.path = path
            return {"type":"file","path":wire.PATH,"encoding":"base64","content":base64.b64encode(raw).decode(),"sha":blob}
    c = Client();assert wire.fixed_file(c,"d"*40) == (raw,blob)
    assert wire.PATH in c.path and "?ref="+"d"*40 in c.path
    with pytest.raises(BindingError):wire.fixed_file(c,"../other")


@pytest.mark.parametrize("case", ["valid", "superseded", "mixedpair", "wrongconsumer", "notdescendant", "publicationfailed", "publicationwrongsource", "wrongpublishedbytes"])
def test_full_immutable_authority_resolution_and_currentness_without_effects(monkeypatch, case):
    req, manifest, published = fixtures()
    raw = json.dumps(manifest).encode();digest = hashlib.sha256(raw).hexdigest()
    qualifications=[]
    monkeypatch.setattr(wire,"qualified",lambda _client,repo,sha:qualifications.append((repo,sha)))
    if case == "wrongconsumer":manifest["consumer"]["source_sha"]="f"*40;raw=json.dumps(manifest).encode();digest=hashlib.sha256(raw).hexdigest()
    class Client:
        def json(self,path):
            if "/contents/" in path:
                assert wire.PATH in path and "PI_OPERATIONAL_MANIFEST.json" not in path
                body=raw+b" " if case=="superseded" and path.endswith("=main") else raw
                return {"path":wire.PATH,"type":"file","encoding":"base64","content":base64.b64encode(body).decode(),"sha":hashlib.sha1(b"blob "+str(len(body)).encode()+b"\0"+body).hexdigest()}
            if "/compare/" in path:
                assert "..."+CONSUMER+"?" in path
                return {"status":"diverged" if case=="notdescendant" else "ahead","merge_base_commit":{"sha":"7d8758f87d6d56f8f414a940fc4bb23d2e6637c6"}}
            if "/releases/tags/" in path:
                return {"tag_name":"v"+wire.VERSION,"draft":False,"prerelease":True,"assets":[
                    {"name":"djconnect-pi-"+wire.VERSION+"-release-manifest.json","id":1,"state":"uploaded","size":1000},
                    {"name":req["artifact_id"].rsplit(":",1)[-1],"id":2,"state":"uploaded","size":10000}]}
            if "/actions/runs/" in path:
                return {"head_sha":"f"*40 if case=="publicationwrongsource" else wire.SOURCE,"status":"completed","conclusion":"failure" if case=="publicationfailed" else "success","path":".github/workflows/publish-release.yml","repository":{"full_name":wire.PI}}
            raise AssertionError(path)
        def asset(self, identifier, maximum):
            assert identifier==1
            copy=deepcopy(published)
            if case=="wrongpublishedbytes":copy["artifacts"][wire.PROFILE]["artifact_sha256"]="f"*64
            return json.dumps(copy).encode()
    config={wire.CONFIG[0]:"d"*40,wire.CONFIG[1]:"e"*64 if case=="mixedpair" else digest}
    if case=="valid":
        result=wire.resolve(Client(),req,CONSUMER,config)
        assert result.asset_id==2 and result.binding.smoke_contract==wire.SMOKE
        assert qualifications==[(wire.CORE,wire.CORE_SOURCE),(wire.CORE,wire.CORE_FINALIZATION),(wire.CORE,"d"*40),(wire.PI,wire.SOURCE),(wire.PI,CONSUMER)]
        wire.current(Client(),result)
    else:
        with pytest.raises(BindingError):wire.resolve(Client(),req,CONSUMER,config)
