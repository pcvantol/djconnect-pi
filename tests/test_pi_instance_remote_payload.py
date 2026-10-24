from __future__ import annotations

import base64
import io
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from Tools import pi_instance_remote_payload as wire


@pytest.fixture
def sandbox(monkeypatch, tmp_path):
    real = Path
    def path(value):return real(str(value).replace("/opt/djconnect", str(tmp_path/"opt")))
    path.home = lambda: tmp_path/"home"
    monkeypatch.setattr(wire, "Path", path)
    monkeypatch.setattr(wire, "installer_permission", lambda: True)
    process = Mock(side_effect=AssertionError("No installer/service effect expected"));monkeypatch.setattr(wire.subprocess, "run", process)
    return tmp_path, process


@pytest.mark.parametrize("case", ["bad-hash", "existing-release"])
def test_rejected_intent_never_stages_or_calls_installer(sandbox, case):
    root, process = sandbox
    payload = {"artifact": base64.b64encode(b"bad archive").decode(), "artifact_sha256": "f"*64,
        "device_profile": "pi5-arm64", "run_id": "123", "source": "a"*40}
    if case == "existing-release":
        preserved = root/"opt/releases/4.0.0-rc.6-pi5-arm64";preserved.mkdir(parents=True)
        (preserved/"WIP").write_text("preserve")
    with pytest.raises(wire.RemoteError):wire.deploy(payload)
    process.assert_not_called();assert not (root/"home/djconnect-install").exists()
    if case == "existing-release":assert (preserved/"WIP").read_text() == "preserve"


@pytest.mark.parametrize("case", ["changed-identity", "unknown-override", "unknown-phase"])
def test_remote_identity_and_payload_fences_precede_dispatch(monkeypatch, case):
    first = {"challenge": "a"*64, "hostname": "synthetic", "architecture": "aarch64", "model": "synthetic", "device_profile": "pi5-arm64"}
    identity = Mock(side_effect=[first, {**first, "model": "changed"} if case == "changed-identity" else first])
    monkeypatch.setattr(wire, "identity", identity);monkeypatch.setattr(wire.sys, "argv", ["fixture", "a"*64])
    payload = {"phase": "deploy", "host": "forbidden"} if case != "unknown-phase" else {"phase": "other"}
    monkeypatch.setattr(wire.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(json.dumps(payload).encode()+b"\n")))
    dispatch = Mock(side_effect=AssertionError("No dispatch"));monkeypatch.setattr(wire, "deploy", dispatch)
    with pytest.raises(wire.RemoteError):wire.main()
    dispatch.assert_not_called()


def test_smoke_function_contains_no_write_or_repair_path():
    import ast
    source = Path(wire.__file__).read_text();tree = ast.parse(source)
    smoke = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "smoke")
    calls = [node for node in ast.walk(smoke) if isinstance(node, ast.Call)]
    assert not any(isinstance(node.func, ast.Name) and node.func.id == "deploy" for node in calls)
    assert not any(isinstance(node.func, ast.Attribute) and node.func.attr in {"mkdir", "write_bytes", "write_text", "unlink", "chmod", "run"} for node in calls)
    assert "/api/debug/screen" not in ast.get_source_segment(source, smoke)
