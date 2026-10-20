"""No network or device mutation: protected-authority resolver counterexamples."""
from __future__ import annotations

import base64
import hashlib
import io
import json
from copy import deepcopy
from urllib.error import HTTPError

import pytest

pytest.importorskip("jsonschema", reason="Dedicated locked deployment-tool suite")
from test_pi_instance_contract import CONSUMER, SOURCE, fixtures

from Tools import pi_instance_authority as wire

OPERATIONAL = "e"*40


class Client:
    def __init__(self, instance="wall-4inch"):
        self.request, self.manifest, self.published = fixtures(instance)
        self.bodies = {2: b"SYNTHETIC FOUR INCH UNIT BYTES", 3: b"SYNTHETIC TEN INCH UNIT BYTES"}
        for index, asset in enumerate(self.manifest["artifact_bindings"], 2):
            digest = hashlib.sha256(self.bodies[index]).hexdigest()
            asset["artifact_sha256"] = digest
            self.published["artifacts"][asset["device_profile"]]["artifact_sha256"] = digest
            if asset["deployment_instance"] == instance:self.request["artifact_sha256"] = digest
        self.calls = [];self.case = "";self.effects = 0

    @property
    def raw(self):return json.dumps(self.manifest).encode()
    @property
    def configuration(self):
        return {"PI_RC5_OPERATIONAL_CORE_SHA": OPERATIONAL,
                "PI_RC5_OPERATIONAL_MANIFEST_SHA256": hashlib.sha256(self.raw).hexdigest()}

    def json(self, path):
        self.calls.append(path)
        if "/branches/main" in path:return {"protected": self.case != "unprotected"}
        if "/compare/" in path:
            sha = path.split("/compare/")[1].split("...")[0]
            return {"status": "ahead", "merge_base_commit": {"sha": "f"*40 if self.case == "not-main" else sha}}
        if "/commits/" in path:
            sha = path.split("/commits/")[1].split("/")[0]
            status = {"sha": sha, "statuses": [{"context": "Post-Merge Release Evidence / Reconcile release evidence", "state": "success", "description": "POST_MERGE_RELEASE_EVIDENCE_QUALIFIED"}]}
            if self.case == "missing-core-evidence" and sha == OPERATIONAL:status["statuses"] = []
            if self.case == "wrong-consumer-evidence" and sha == CONSUMER:status["sha"] = SOURCE
            return status
        if "/contents/" in path:
            raw = self.raw
            if self.case == "superseded" and path.endswith("ref=main"):raw += b" "
            if self.case == "bad-json":raw = b'{"duplicate":1,"duplicate":2}'
            result = {"path": wire.OPERATIONAL_PATH, "type": "file", "encoding": "base64",
                "content": base64.b64encode(raw).decode(), "sha": hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()}
            if self.case == "bad-blob":result["sha"] = "f"*40
            if self.case == "bad-encoding":result["encoding"] = "other"
            return result
        if "/releases/tags/" in path:
            result = {"tag_name": "v"+wire.VERSION, "draft": False, "prerelease": True,
                "assets": [{"name": "djconnect-pi-"+wire.VERSION+"-release-manifest.json", "id": 1, "state": "uploaded", "size": len(json.dumps(self.published).encode())}]}
            for index, asset in enumerate(self.manifest["artifact_bindings"], 2):
                result["assets"].append({"name": asset["artifact_id"].rsplit(":", 1)[-1], "id": index, "state": "uploaded", "size": len(self.bodies[index])})
            if self.case == "draft":result["draft"] = True
            if self.case == "duplicate-asset":result["assets"].append(deepcopy(result["assets"][0]))
            if self.case == "oversize-metadata":result["assets"][0]["size"] = 262145
            return result
        if "/actions/runs/" in path:
            result = {"head_sha": SOURCE, "status": "completed", "conclusion": "success", "path": ".github/workflows/publish-release.yml", "repository": {"full_name": wire.PI}}
            if self.case == "wrong-publication-source":result["head_sha"] = CONSUMER
            if self.case == "failed-publication":result["conclusion"] = "failure"
            if self.case == "wrong-publication-workflow":result["path"] = "other.yml"
            return result
        raise AssertionError(path)

    def asset(self, asset_id, maximum):
        self.calls.append((asset_id, maximum))
        if asset_id == 1:
            published = deepcopy(self.published)
            if self.case == "wrong-published-source":published["candidate_sha"] = CONSUMER
            return json.dumps(published).encode()
        return self.bodies[asset_id]


@pytest.mark.parametrize("instance", ["wall-4inch", "wall-10inch"])
def test_protected_run_bound_pair_and_artifact(instance):
    client = Client(instance)
    authority = wire.resolve(client, client.request, CONSUMER, client.configuration)
    assert authority.receipt()["operational_core_sha"] == OPERATIONAL
    assert authority.receipt()["operational_manifest_sha256"] == client.configuration["PI_RC5_OPERATIONAL_MANIFEST_SHA256"]
    assert "endpoint" not in json.dumps(authority.receipt())
    assert wire.verified_artifact(client, authority) == client.bodies[authority.asset_id]
    assert client.effects == 0


@pytest.mark.parametrize("case", ["unprotected", "not-main", "missing-core-evidence", "wrong-consumer-evidence", "superseded", "bad-blob", "bad-encoding", "draft", "duplicate-asset", "oversize-metadata", "wrong-publication-source", "failed-publication", "wrong-publication-workflow", "wrong-published-source"])
def test_incomplete_stale_or_untrusted_provenance_fails_before_effects(case):
    client = Client();client.case = case
    with pytest.raises(wire.BindingError):wire.resolve(client, client.request, CONSUMER, client.configuration)
    assert client.effects == 0


@pytest.mark.parametrize("configuration", [{}, {"PI_RC5_OPERATIONAL_CORE_SHA": OPERATIONAL},
    {"PI_RC5_OPERATIONAL_MANIFEST_SHA256": "a"*64},
    {"PI_RC5_OPERATIONAL_CORE_SHA": OPERATIONAL, "PI_RC5_OPERATIONAL_MANIFEST_SHA256": "A"*64}])
def test_missing_partial_or_malformed_pair_makes_no_api_call(configuration):
    client = Client()
    with pytest.raises(wire.BindingError):wire.resolve(client, client.request, CONSUMER, configuration)
    assert client.calls == [] and client.effects == 0


def test_mixed_configuration_pair_does_not_select_another_manifest():
    client = Client();configuration = client.configuration;configuration["PI_RC5_OPERATIONAL_MANIFEST_SHA256"] = "a"*64
    with pytest.raises(wire.BindingError, match="OPERATIONAL_BYTES_MISMATCH"):
        wire.resolve(client, client.request, CONSUMER, configuration)
    assert client.effects == 0


def test_unknown_request_override_rejected_before_api_calls():
    client = Client();client.request["host"] = "private-endpoint-value"
    with pytest.raises(wire.BindingError, match="REQUEST_SCHEMA_INVALID"):
        wire.resolve(client, client.request, CONSUMER, client.configuration)
    assert not client.calls


def test_actual_downloaded_bytes_must_match_approved_digest():
    client = Client();authority = wire.resolve(client, client.request, CONSUMER, client.configuration)
    client.bodies[authority.asset_id] = b"MUTATED SAME ASSET ID"
    with pytest.raises(wire.BindingError, match="ARTIFACT_BYTES_MISMATCH"):wire.verified_artifact(client, authority)
    assert client.effects == 0


class Response(io.BytesIO):
    def __init__(self, value):
        super().__init__(value)
        self.headers = {}
    def __enter__(self):return self
    def __exit__(self, *args):self.close()


@pytest.mark.parametrize("location", ["http://objects.githubusercontent.com/fixture", "https://untrusted.invalid/fixture", "https://user:secret@objects.githubusercontent.com/fixture", "https://production-results.blob.core.windows.net/fixture"])
def test_signed_asset_redirect_cannot_export_identity(location):
    client = wire.GitHubRead("synthetic-not-a-credential")
    calls = []
    class Opener:
        def open(self, request, timeout):
            calls.append(request)
            raise HTTPError(request.full_url, 302, "synthetic", {"Location": location}, io.BytesIO())
    client.opener = Opener()
    with pytest.raises(wire.BindingError):client.asset(1, 100)
    assert len(calls) == 1


def test_github_token_is_not_forwarded_to_signed_artifact_host():
    client = wire.GitHubRead("synthetic-not-a-credential");calls = []
    class Opener:
        def open(self, request, timeout):
            calls.append(request)
            if len(calls) == 1:raise HTTPError(request.full_url, 302, "synthetic", {"Location": "https://release-assets.githubusercontent.com/fixture"}, io.BytesIO())
            return Response(b"asset")
    client.opener = Opener()
    assert client.asset(1, 100) == b"asset"
    assert calls[0].get_header("Authorization") == "Bearer synthetic-not-a-credential"
    assert calls[1].get_header("Authorization") is None


def test_declared_and_actual_github_metadata_are_bounded():
    response = Response(b"too large");response.headers = {"Content-Length": "101"}
    with pytest.raises(wire.BindingError):wire.GitHubRead.bounded(response, 100)
    assert response.tell() == 0
    response = Response(b"x"*101)
    with pytest.raises(wire.BindingError):wire.GitHubRead.bounded(response, 100)
