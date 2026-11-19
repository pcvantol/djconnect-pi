from __future__ import annotations

import base64
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("jsonschema", reason="Dedicated locked deployment-tool suite")

from Tools import pi_instance_remote_payload as remote
from Tools import pi_rc6_recovery as recovery

RUN = "50000000000"
BOOT = "01234567-89ab-cdef-0123-456789abcdef"


@pytest.fixture
def staged(monkeypatch, tmp_path):
    home = tmp_path / "home"
    (home / "djconnect-install").mkdir(parents=True)
    old = home / "djconnect-install" / ("djconnect-pi-rc6-" + recovery.ORIGINAL_RUN + "-" + recovery.PROFILE)
    old.mkdir()
    retained = old / "installer-private.log"
    retained.write_text("original failed evidence")
    boot = tmp_path / "boot_id"
    boot.write_text(BOOT)
    real_path = Path
    def path(value):
        return boot if str(value) == "/proc/sys/kernel/random/boot_id" else real_path(value)
    path.home = lambda: home
    monkeypatch.setattr(remote, "Path", path)
    monkeypatch.setattr(remote, "installer_permission", lambda: True)
    monkeypatch.setattr(remote, "services", lambda: {
        "djconnect-api.service": {"active": True, "pid": 200},
        "djconnect-client.service": {"active": True, "pid": 201}})
    raw = Path(recovery.__file__).with_name("pi_rc6_recovery_root.py").read_bytes()
    payload = {"source": recovery.SOURCE, "device_profile": recovery.PROFILE,
        "artifact_sha256": recovery.ARTIFACT_SHA256, "recovery_helper": base64.b64encode(raw).decode(),
        "recovery_boot_id": BOOT, "run_id": RUN}
    proof = {"result": "RECOVERED_PENDING_SMOKE", "original_deployment_workflow_run": recovery.ORIGINAL_RUN,
        "recovery_workflow_run": RUN, "source": recovery.SOURCE, "watchdog_restored": True,
        "configuration_preserved": True, "verified_packaged_files": 80}
    calls = []
    original_run = subprocess.run
    def execute(args, **kwargs):
        calls.append(args)
        assert args[:2] == ["sudo", "-n"] and args[-2:] == [RUN, BOOT]
        helper = Path(args[2])
        assert helper.read_bytes().startswith(b'#!/bin/sh\nexec /usr/bin/python3 -I - "$@" <<')
        assert raw in helper.read_bytes() and helper.stat().st_mode & 0o777 == 0o700
        # Parse the real wrapper, without executing either helper or sudo.
        original_run(["/bin/sh", "-n", str(helper)], check=True, capture_output=True)
        kwargs["stdout"].write(json.dumps(proof).encode())
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(remote.subprocess, "run", execute)
    yield payload, proof, calls, home, boot, retained
    assert retained.read_text() == "original failed evidence"


def test_real_recovery_wrapper_is_private_and_never_overwrites_or_repeats(staged):
    payload, _, calls, home, _, _ = staged
    assert remote.recover(payload)["result"] == "RECOVERED_PENDING_SMOKE"
    log = home / "djconnect-install" / ("djconnect-pi-rc6-recovery-" + RUN) / "recovery-root-private.log"
    assert log.stat().st_mode & 0o777 == 0o600
    with pytest.raises(remote.RemoteError, match="RECOVERY_STAGING_EXISTS"):
        remote.recover(payload)
    assert len(calls) == 1


@pytest.mark.parametrize("field,value", [("source", "a"*40), ("device_profile", "pi5-arm64"),
    ("artifact_sha256", "f"*64), ("recovery_helper", base64.b64encode(b"other source").decode()),
    ("recovery_boot_id", "11111111-1111-1111-1111-111111111111")])
def test_changed_scope_or_helper_or_boot_cannot_reach_sudo(staged, field, value):
    payload, _, calls, *_ = staged
    payload[field] = value
    with pytest.raises(remote.RemoteError):
        remote.recover(payload)
    assert not calls


@pytest.mark.parametrize("field,value", [("result", "DEPLOYED_PENDING_SMOKE"),
    ("original_deployment_workflow_run", "other"), ("recovery_workflow_run", "other"),
    ("source", "a"*40), ("watchdog_restored", 1), ("configuration_preserved", False),
    ("verified_packaged_files", True), ("verified_packaged_files", 79)])
def test_partial_root_proof_never_claims_recovery(staged, field, value):
    payload, proof, calls, *_ = staged
    proof[field] = value
    with pytest.raises(remote.RemoteError, match="RECOVERY_RESULT_INVALID"):
        remote.recover(payload)
    assert len(calls) == 1


def test_lost_root_ack_is_not_replayed(staged, monkeypatch):
    payload, _, calls, *_ = staged
    def lost(args, **kwargs):
        calls.append(args)
        raise subprocess.TimeoutExpired("private synthetic command", 1350)
    monkeypatch.setattr(remote.subprocess, "run", lost)
    with pytest.raises(subprocess.TimeoutExpired):
        remote.recover(payload)
    with pytest.raises(remote.RemoteError, match="RECOVERY_STAGING_EXISTS"):
        remote.recover(payload)
    assert len(calls) == 1


def test_missing_installer_authority_has_no_staging_effect(staged, monkeypatch):
    payload, _, calls, home, *_ = staged
    monkeypatch.setattr(remote, "installer_permission", lambda: False)
    with pytest.raises(remote.RemoteError, match="INSTALLER_NOT_AUTHORIZED"):
        remote.recover(payload)
    assert not calls and len(list((home / "djconnect-install").iterdir())) == 1


def test_boot_change_after_root_success_is_inconclusive(staged, monkeypatch):
    payload, _, calls, _, boot, _ = staged
    original = remote.subprocess.run
    def rebooted(args, **kwargs):
        result = original(args, **kwargs)
        boot.write_text("11111111-1111-1111-1111-111111111111")
        return result
    monkeypatch.setattr(remote.subprocess, "run", rebooted)
    with pytest.raises(remote.RemoteError, match="RECOVERY_BOOT_CHANGED"):
        remote.recover(payload)
    assert len(calls) == 1
