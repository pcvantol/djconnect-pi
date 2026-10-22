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
from Tools import pi_wall4_latest_failure as previous
from Tools.pi_instance_contract import BindingError

FIXTURE = Path(__file__).parent / "fixtures/pi_wall4_recovery_v2"
RAW = (FIXTURE / "inconclusive_receipt.json").read_bytes()


class Client:
    def __init__(self):
        spec = previous.latest_spec()
        self.run = {
            "id": int(spec["workflow_run_id"]),
            "head_sha": spec["consumer_sha"],
            "head_branch": "main",
            "path": spec["workflow_path"],
            "event": "workflow_dispatch",
            "status": "completed",
            "conclusion": "failure",
            "run_attempt": 1,
            "actor": {"login": "pcvantol"},
            "repository": {"full_name": previous.PI},
            "display_title": "Pi recovery / wall-4inch / " + spec["manifest_id"],
        }
        self.artifact = {
            "id": int(spec["evidence_artifact_id"]),
            "name": spec["evidence_artifact_name"],
            "expired": False,
            "size_in_bytes": 1000,
        }
        self.files = {}
        for name in previous.PREVIOUS_CODE_PINS:
            raw = (FIXTURE / "code" / name).read_bytes()
            self.files[name] = {
                "type": "file",
                "path": name,
                "encoding": "base64",
                "content": base64.b64encode(raw).decode(),
                "sha": hashlib.sha1(
                    b"blob " + str(len(raw)).encode() + b"\0" + raw,
                    usedforsecurity=False,
                ).hexdigest(),
            }
        self.raw = RAW
        self.members = None
        self.calls = []

    def json(self, path):
        self.calls.append(path)
        prefix = "repos/" + previous.PI
        if path == prefix + "/actions/runs/39775941080":
            return deepcopy(self.run)
        if path == prefix + "/actions/runs/39775941080/artifacts?per_page=100":
            return {"total_count": 1, "artifacts": [deepcopy(self.artifact)]}
        for name, value in self.files.items():
            if (
                path
                == prefix
                + "/contents/"
                + name
                + "?ref=2e7479d0d15aa11ad3bff4c8103c18dbb1f2c32a"
            ):
                return deepcopy(value)
        raise AssertionError(path)

    def archive(self, identifier):
        assert identifier == self.artifact["id"]
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as z:
            for name, body in self.members or [("pi-recover-evidence.json", self.raw)]:
                z.writestr(name, body)
        return out.getvalue()


@pytest.fixture(autouse=True)
def qualified_without_network(monkeypatch):
    calls = []
    monkeypatch.setattr(
        previous, "qualified", lambda _client, repo, sha: calls.append((repo, sha))
    )
    return calls


def test_original_v2_receipt_retains_nested_prior_failure_and_uncertainty(
    qualified_without_network,
):
    assert hashlib.sha256(RAW).hexdigest() == previous.latest_spec()["evidence_sha256"]
    c = Client()
    record = previous.latest_failure(c)
    assert record == json.loads(RAW)
    assert (
        record["intent_dispatched"] is True
        and record["remote_may_still_be_running"] is True
    )
    assert (
        record["kind"] == "djconnect_pi_wall4_recovery_evidence"
        and type(record["schema_version"]) is int
        and record["schema_version"] == 1
    )
    assert not {
        "inputs",
        "action",
        "execution_mode",
        "root_static_diagnostic",
        "claim_absent",
    }.intersection(record)
    assert record["previous_recovery_attempt"]["workflow_run_id"] == "39695635601"
    assert qualified_without_network == [
        (previous.PI, "2e7479d0d15aa11ad3bff4c8103c18dbb1f2c32a")
    ]
    assert len(c.calls) == 7


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", True),
        ("id", 39775941081),
        ("head_sha", "f" * 40),
        ("head_branch", "feature"),
        ("path", ".github/workflows/deploy-latest-pi-release.yml"),
        ("event", "push"),
        ("status", "in_progress"),
        ("conclusion", "success"),
        ("run_attempt", True),
        ("run_attempt", 2),
        ("actor", {"login": "other"}),
        ("repository", {"full_name": "other/repo"}),
        ("display_title", "other manifest"),
    ],
)
def test_prior_run_metadata_is_not_an_old_or_new_execution_grant(field, value):
    c = Client()
    c.run[field] = value
    with pytest.raises(BindingError, match="PREVIOUS_FAILED_RUN_INVALID"):
        previous.latest_failure(c)


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", 12423814909),
        ("id", True),
        ("name", "other"),
        ("expired", True),
        ("expired", 0),
        ("size_in_bytes", True),
        ("size_in_bytes", 0),
        ("size_in_bytes", 262145),
    ],
)
def test_exact_previous_artifact_is_required(field, value):
    c = Client()
    c.artifact[field] = value
    with pytest.raises(BindingError):
        previous.latest_failure(c)


@pytest.mark.parametrize("path", sorted(previous.PREVIOUS_CODE_PINS))
@pytest.mark.parametrize(
    "field,value",
    [
        ("type", "dir"),
        ("path", "other"),
        ("encoding", "utf8"),
        ("content", "%%invalid"),
        ("sha", "f" * 40),
    ],
)
def test_all_five_previous_code_objects_are_exact_not_caller_selected(
    path, field, value
):
    c = Client()
    c.files[path][field] = value
    with pytest.raises(BindingError):
        previous.latest_failure(c)


@pytest.mark.parametrize("path", sorted(previous.PREVIOUS_CODE_PINS))
def test_git_blob_coherence_cannot_replace_protected_sha256_pin(path):
    c = Client()
    raw = b"foreign code"
    c.files[path].update(
        content=base64.b64encode(raw).decode(),
        sha=hashlib.sha1(
            b"blob " + str(len(raw)).encode() + b"\0" + raw, usedforsecurity=False
        ).hexdigest(),
    )
    with pytest.raises(BindingError, match="PREVIOUS_CODE_BYTES_MISMATCH"):
        previous.latest_failure(c)


@pytest.mark.parametrize(
    "members",
    [
        [("other.json", RAW)],
        [("../pi-recover-evidence.json", RAW)],
        [("pi-recover-evidence.json", RAW), ("extra", b"")],
        [("pi-recover-evidence.json", b" " * 65537)],
    ],
)
def test_archive_member_layout_never_imports_other_receipts(members):
    c = Client()
    c.members = members
    with pytest.raises(BindingError, match="PREVIOUS_RECEIPT_LAYOUT_INVALID"):
        previous.latest_failure(c)


@pytest.mark.parametrize(
    "field,value",
    [
        ("intent_dispatched", 1),
        ("intent_dispatched", False),
        ("remote_may_still_be_running", 1),
        ("remote_may_still_be_running", False),
        ("result", "RECOVERED_PENDING_SMOKE"),
        ("consumer_sha", "f" * 40),
        ("operational_core_sha", "d" * 40),
        ("operational_manifest_sha256", "e" * 64),
        ("classification", "success"),
        ("workflow_run_id", "50000000000"),
        ("manifest_id", "new manifest"),
    ],
)
def test_raw_receipt_cannot_be_rewritten_even_with_valid_json(field, value):
    c = Client()
    record = json.loads(RAW)
    record[field] = value
    c.raw = json.dumps(record).encode()
    with pytest.raises(BindingError, match="PREVIOUS_RECEIPT_BYTES_MISMATCH"):
        previous.latest_failure(c)


@pytest.mark.parametrize(
    "field",
    [
        "kind",
        "schema_version",
        "recovery_helper_sha256",
        "observer_sha256",
        "claim_policy",
        "previous_recovery_attempt",
    ],
)
def test_actual_v2_fields_are_historical_original_bytes_not_synthetic_current_authority(
    field,
):
    c = Client()
    record = json.loads(RAW)
    record[field] = None
    c.raw = json.dumps(record).encode()
    with pytest.raises(BindingError, match="PREVIOUS_RECEIPT_BYTES_MISMATCH"):
        previous.latest_failure(c)


def test_spec_returns_an_independent_nested_value():
    first = previous.latest_spec()
    first["previous_recovery_attempt"]["run_attempt"] = True
    assert (
        type(previous.latest_spec()["previous_recovery_attempt"]["run_attempt"]) is int
    )


def test_latest_spec_preserves_exact_original_v1_nested_provenance():
    from Tools.pi_wall4_previous_failure import previous_spec

    record = json.loads(RAW)
    spec = previous.latest_spec()
    assert (
        spec["previous_recovery_attempt"]
        == record["previous_recovery_attempt"]
        == previous_spec()
    )
    assert (
        spec["previous_recovery_attempt"]["consumer_sha"]
        == "77fc4047f797066876c5345e8e43b346ab96d782"
    )
    assert (
        spec["consumer_sha"]
        == record["consumer_sha"]
        == "2e7479d0d15aa11ad3bff4c8103c18dbb1f2c32a"
    )
