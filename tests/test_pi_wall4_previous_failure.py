"""Actual historical public bytes plus synthetic HTTP envelopes; zero effects."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import zipfile
from copy import deepcopy
from pathlib import Path

import pytest

pytest.importorskip("jsonschema", reason="Dedicated locked deployment-tool suite")
from Tools import pi_wall4_previous_failure as previous
from Tools import pi_wall4_recovery_authority as authority
from Tools.pi_instance_contract import BindingError

FIXTURE = Path(__file__).parent/"fixtures/pi_wall4_recovery_v1"
RAW = (FIXTURE/"inconclusive_receipt.json").read_bytes()


class Client:
    def __init__(self):
        spec = authority.previous_spec()
        self.run = {"id":int(spec["workflow_run_id"]), "head_sha":spec["consumer_sha"], "head_branch":"main",
            "path":spec["workflow_path"], "event":"workflow_dispatch", "status":"completed", "conclusion":"failure",
            "run_attempt":1, "actor":{"login":"pcvantol"}, "repository":{"full_name":previous.PI},
            "display_title":"Pi recovery / wall-4inch / "+spec["manifest_id"]}
        self.artifact = {"id":int(spec["evidence_artifact_id"]), "name":spec["evidence_artifact_name"],
            "expired":False, "size_in_bytes":1000}
        self.files = {}
        for name in previous.PREVIOUS_CODE_PINS:
            raw = (FIXTURE/"code"/name).read_bytes()
            self.files[name] = {"type":"file", "path":name, "encoding":"base64",
                "content":base64.b64encode(raw).decode(),
                "sha":hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw, usedforsecurity=False).hexdigest()}
        self.raw = RAW
        self.members = None
        self.calls = []
    def json(self, path):
        self.calls.append(path)
        prefix = "repos/"+previous.PI
        if path == prefix+"/actions/runs/39695635601":return deepcopy(self.run)
        if path == prefix+"/actions/runs/39695635601/artifacts?per_page=100":return {"total_count":1,"artifacts":[deepcopy(self.artifact)]}
        for name, value in self.files.items():
            if path == prefix+"/contents/"+name+"?ref=77fc4047f797066876c5345e8e43b346ab96d782":return deepcopy(value)
        raise AssertionError(path)
    def archive(self, identifier):
        assert identifier == self.artifact["id"]
        out = io.BytesIO()
        with zipfile.ZipFile(out,"w") as z:
            for name, body in self.members or [("pi-recover-evidence.json",self.raw)]:z.writestr(name,body)
        return out.getvalue()


@pytest.fixture(autouse=True)
def qualified_without_network(monkeypatch):
    calls = []
    monkeypatch.setattr(previous,"qualified",lambda _client, repo, sha:calls.append((repo,sha)))
    return calls


def test_actual_prior_receipt_accepts_missing_nonexistent_fields_and_keeps_uncertainty(qualified_without_network):
    assert hashlib.sha256(RAW).hexdigest() == authority.previous_spec()["evidence_sha256"]
    c = Client();record = previous.previous_failure(c)
    assert record == json.loads(RAW)
    assert record["intent_dispatched"] is True and record["remote_may_still_be_running"] is True
    assert not {"kind","schema_version","helper","observer","inputs","action","execution_mode"}.intersection(record)
    assert qualified_without_network == [(previous.PI,"77fc4047f797066876c5345e8e43b346ab96d782")]
    assert len(c.calls) == 7


@pytest.mark.parametrize("field,value",[("id",True),("id",39695635602),("head_sha","f"*40),("head_branch","feature"),
    ("path",".github/workflows/deploy-latest-pi-release.yml"),("event","push"),("status","in_progress"),
    ("conclusion","success"),("run_attempt",True),("run_attempt",2),("actor",{"login":"other"}),
    ("repository",{"full_name":"other/repo"}),("display_title","other manifest")])
def test_prior_run_metadata_is_not_an_old_or_new_execution_grant(field,value):
    c = Client();c.run[field] = value
    with pytest.raises(BindingError,match="PREVIOUS_FAILED_RUN_INVALID"):previous.previous_failure(c)


@pytest.mark.parametrize("field,value",[("id",12391115674),("id",True),("name","other"),("expired",True),
    ("expired",0),("size_in_bytes",True),("size_in_bytes",0),("size_in_bytes",262145)])
def test_exact_previous_artifact_is_required(field,value):
    c = Client();c.artifact[field] = value
    with pytest.raises(BindingError):previous.previous_failure(c)


@pytest.mark.parametrize("path",sorted(previous.PREVIOUS_CODE_PINS))
@pytest.mark.parametrize("field,value",[("type","dir"),("path","other"),("encoding","utf8"),("content","%%invalid"),("sha","f"*40)])
def test_all_five_previous_code_objects_are_exact_not_caller_selected(path,field,value):
    c = Client();c.files[path][field] = value
    with pytest.raises(BindingError):previous.previous_failure(c)


@pytest.mark.parametrize("path",sorted(previous.PREVIOUS_CODE_PINS))
def test_git_blob_coherence_cannot_replace_protected_sha256_pin(path):
    c = Client();raw = b"foreign code"
    c.files[path].update(content=base64.b64encode(raw).decode(),sha=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw,usedforsecurity=False).hexdigest())
    with pytest.raises(BindingError,match="PREVIOUS_CODE_BYTES_MISMATCH"):previous.previous_failure(c)


@pytest.mark.parametrize("members",[[('other.json',RAW)],[('../pi-recover-evidence.json',RAW)],
    [('pi-recover-evidence.json',RAW),('extra',b'')],[('pi-recover-evidence.json',b' '*65537)]])
def test_archive_member_layout_never_imports_other_receipts(members):
    c = Client();c.members = members
    with pytest.raises(BindingError,match="PREVIOUS_RECEIPT_LAYOUT_INVALID"):previous.previous_failure(c)


@pytest.mark.parametrize("field,value",[("intent_dispatched",1),("intent_dispatched",False),
    ("remote_may_still_be_running",1),("remote_may_still_be_running",False),("result","RECOVERED_PENDING_SMOKE"),
    ("consumer_sha","f"*40),("operational_core_sha","d"*40),("operational_manifest_sha256","e"*64),
    ("classification","success"),("workflow_run_id","50000000000"),("manifest_id","new manifest")])
def test_raw_receipt_cannot_be_rewritten_even_with_valid_json(field,value):
    c = Client();record = json.loads(RAW);record[field] = value;c.raw = json.dumps(record).encode()
    with pytest.raises(BindingError,match="PREVIOUS_RECEIPT_BYTES_MISMATCH"):previous.previous_failure(c)


@pytest.mark.parametrize("field",sorted(authority.previous_spec()))
def test_every_nested_previous_discriminator_is_validated_against_protected_schema(field):
    from test_pi_wall4_recovery_contract import CONSUMER, fixtures
    req, manifest, pub = fixtures()
    manifest["recovery"]["previous_recovery_attempt"][field] = None
    with pytest.raises(BindingError):authority.validate(req,manifest,CONSUMER,pub)


@pytest.mark.parametrize("field",["intent_dispatched","remote_may_still_be_running","run_attempt"])
def test_recursive_receipt_equality_does_not_equate_boolean_with_number(field):
    expected = authority.previous_spec();changed = deepcopy(expected)
    changed[field] = 1 if type(changed[field]) is bool else True
    assert not authority.exact_json(changed,expected)


@pytest.mark.parametrize("sha",["042cf36479e6c4d1c42cebd19acd3bdd00cfef79","77fc4047f797066876c5345e8e43b346ab96d782"])
def test_qualified_v1_consumer_does_not_implement_v2(sha):
    from test_pi_wall4_recovery_contract import fixtures
    req, manifest, pub = fixtures();manifest["consumer"]["source_sha"] = sha
    with pytest.raises(BindingError,match="RECOVERY_CONSUMER_MISMATCH"):authority.validate(req,manifest,sha,pub)


@pytest.mark.parametrize("field",["intent_dispatched","remote_may_still_be_running","run_attempt"])
def test_smoke_rejects_nested_previous_receipt_boolean_numeric_substitution(field):
    from test_pi_wall4_recovery_contract import authority as fixture
    from test_pi_wall4_recovery_release import PRIOR, receipt
    from test_pi_wall4_recovery_release import Client as ReleaseClient

    from Tools import pi_wall4_recovery_release as release
    record = receipt();nested = record["previous_recovery_attempt"]
    nested[field] = 1 if type(nested[field]) is bool else True
    with pytest.raises(BindingError):release.recovery_record(ReleaseClient(),fixture(),PRIOR,record)


@pytest.mark.parametrize("suffix",["", "&extra=1", "/../contents/file", "\n"])
def test_real_http_edge_allows_only_exact_fixed_v2_ancestor_route(suffix):
    from test_pi_instance_authority import Response

    from Tools.pi_instance_authority import GitHubRead
    calls = []
    class Opener:
        def open(self, request, timeout):
            calls.append(request.full_url);return Response(b"{}")
    reader = GitHubRead("synthetic-not-a-credential");reader.opener = Opener()
    path = "repos/pcvantol/djconnect-pi/compare/77fc4047f797066876c5345e8e43b346ab96d782..."+"a"*40+"?per_page=1&page=2"+suffix
    if suffix:
        with pytest.raises(BindingError,match="GITHUB_PATH_INVALID"):reader.get(path)
        assert not calls
    else:
        assert reader.get(path) == b"{}"
        assert calls == ["https://api.github.com/"+path]
