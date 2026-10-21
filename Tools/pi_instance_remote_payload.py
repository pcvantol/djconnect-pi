"""Authenticated SSH stdlib payload; no effects before the checked parent intent."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import platform
import re
import socket
import subprocess
import sys
import tarfile
import time
import zipfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from urllib.request import ProxyHandler, build_opener

VERSION = "4.0.0-rc.6"


class RemoteError(ValueError):
    pass


def need(value, code="TARGET_NOT_READY"):
    if not value:raise RemoteError(code)


def identity(challenge):
    return {"challenge": challenge, "hostname": socket.gethostname(), "architecture": platform.machine(),
        "model": Path("/proc/device-tree/model").read_bytes().rstrip(b"\0").decode("utf-8"),
        "device_profile": Path("/etc/djconnect-pi/device-profile").read_text().rstrip("\n")}


def text(path, maximum=128):
    with Path(path).open("rb") as stream:raw = stream.read(maximum+1)
    need(len(raw) <= maximum)
    return raw.decode("ascii").rstrip("\n")


def services():
    result = {}
    for name in ("djconnect-api.service", "djconnect-client.service"):
        proc = subprocess.run(["systemctl", "show", name, "--property=MainPID,ActiveState", "--no-pager"], capture_output=True, text=True, timeout=8, check=False)
        fields = dict(line.split("=", 1) for line in proc.stdout.splitlines() if "=" in line)
        result[name] = {"active": fields.get("ActiveState") == "active", "pid": int(fields.get("MainPID", "0"))}
    return result


def installer_permission():
    proc = subprocess.run(["sudo", "-n", "-l"], capture_output=True, text=True, timeout=8, check=False)
    pattern = str(Path.home()/"djconnect-install/djconnect-pi-*/scripts/install.sh")
    return proc.returncode == 0 and any("NOPASSWD:" in line and pattern in line for line in proc.stdout.splitlines())


@contextmanager
def package_members(raw, payload):
    need(len(raw) <= 33554432 and hashlib.sha256(raw).hexdigest() == payload["artifact_sha256"], "ARTIFACT_BYTES_MISMATCH")
    prefix = "djconnect-pi-"+payload["device_profile"]+"-"+VERSION
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        seen = set();total = 0
        for member in archive:
            path = PurePosixPath(member.name)
            need(bool(path.parts) and path.parts[0] == prefix and not path.is_absolute() and ".." not in path.parts
                and "\\" not in member.name and len(member.name.encode()) <= 4096
                and all(ord(c) >= 32 for c in member.name)
                and (member.name == path.as_posix() or (member.isdir() and member.name == path.as_posix()+"/"))
                and path.as_posix() not in seen and (member.isfile() or member.isdir()), "ARTIFACT_LAYOUT_INVALID")
            seen.add(path.as_posix());total += member.size
            need(total <= 67108864 and len(seen) <= 4096, "ARTIFACT_LAYOUT_INVALID")
        for name, expected in (("VERSION", VERSION), ("SOURCE_COMMIT", payload["source"]), ("RELEASE_PROFILE", payload["device_profile"])):
            member = archive.getmember(prefix+"/"+name);need(member.isfile() and member.size <= 128, "ARTIFACT_LAYOUT_INVALID")
            need(archive.extractfile(member).read(129) == (expected+"\n").encode(), "ARTIFACT_IDENTITY_INVALID")
        wheel = archive.getmember(prefix+"/wheels/"+payload["wheel_name"])
        need(wheel.isfile() and wheel.size <= 8388608, "ARTIFACT_LAYOUT_INVALID")
        need(hashlib.sha256(archive.extractfile(wheel).read(8388609)).hexdigest() == payload["wheel_sha256"], "WHEEL_MISMATCH")
        yield archive, prefix

def deploy(payload):
    need(installer_permission(), "INSTALLER_NOT_AUTHORIZED")
    release = Path("/opt/djconnect/releases")/(VERSION+"-"+payload["device_profile"])
    need(not release.exists() and not release.is_symlink(), "RELEASE_ALREADY_PRESENT_REQUIRES_REVIEW")
    raw = base64.b64decode(payload["artifact"], validate=True)
    with package_members(raw, payload) as (archive, prefix):
        stage = Path.home()/"djconnect-install"/("djconnect-pi-rc6-"+payload["run_id"]+"-"+payload["device_profile"])
        # A repeated/rerun controller cannot overwrite earlier staging or replay its installer.
        need(not stage.exists() and not stage.is_symlink(), "STAGING_ALREADY_PRESENT_REQUIRES_REVIEW")
        need(not stage.parent.is_symlink() and (not stage.parent.exists() or stage.parent.is_dir()), "STAGING_PARENT_INVALID")
        stage.parent.mkdir(mode=0o700, exist_ok=True)
        stage.mkdir(mode=0o700)
        bundle = stage/"approved-artifact.tar.gz";bundle.write_bytes(raw);bundle.chmod(0o600)
        for member in archive.getmembers():
            relative = PurePosixPath(member.name).relative_to(prefix)
            if not relative.parts:continue
            target = stage.joinpath(*relative.parts)
            if member.isdir():target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as source, target.open("xb") as output:
                    while chunk := source.read(16384):output.write(chunk)
                target.chmod(member.mode & 0o777 & ~0o022)
    before = services()
    command = ["sudo", "-n", str(stage/"scripts/install.sh"), "--approved-artifact", str(bundle),
        "--artifact-sha256", payload["artifact_sha256"], "--source-sha", payload["source"]]
    log = stage/"installer-private.log"
    with log.open("xb") as output:
        log.chmod(0o600)
        # No guessed cancellation or automatic recovery: controller loss may leave this running.
        result = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, check=False)
    need(result.returncode == 0, "INSTALLER_FAILED_REQUIRES_STATE_REVIEW")
    deadline = time.monotonic()+90
    while True:
        current = services()
        healthy = all(row["active"] and row["pid"] > 0 and row["pid"] != before[name]["pid"] for name, row in current.items())
        if healthy and text("/opt/djconnect/current/VERSION") == VERSION and text("/opt/djconnect/current/SOURCE_COMMIT") == payload["source"]:
            return {"result": "DEPLOYED_PENDING_SMOKE", "configuration_preserved_by_installer": True, "services": current}
        need(time.monotonic() < deadline, "ACTIVATION_INCONCLUSIVE_REQUIRES_STATE_REVIEW")
        time.sleep(2)


def recover(payload):
    need(payload["source"] == "0dde0abe22a0859f170a7c1d3eab41f1ade44d37"
         and payload["device_profile"] == "pi-zero-2w-arm64"
         and payload["artifact_sha256"] == "d67869ffca53c4936059bdbbdbdf6be63b36eafac269fa2f3f9b090922cd0d64", "RECOVERY_SCOPE_INVALID")
    need(installer_permission(), "INSTALLER_NOT_AUTHORIZED")
    code = base64.b64decode(payload["recovery_helper"], validate=True)
    need(len(code) <= 65536 and hashlib.sha256(code).hexdigest() == "11ce41115c7aa5ac34e568f3ea9008915f342bc3272850b56c61eed19a760ab9", "RECOVERY_HELPER_BYTES_CHANGED")
    boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    need(boot == payload["recovery_boot_id"] and re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", boot), "RECOVERY_BOOT_CHANGED")
    stage = Path.home()/"djconnect-install"/("djconnect-pi-rc6-recovery-"+payload["run_id"])
    need(not stage.exists() and not stage.is_symlink() and not stage.parent.is_symlink(), "RECOVERY_STAGING_EXISTS")
    stage.mkdir(mode=0o700);(stage/"scripts").mkdir(mode=0o700)
    helper = stage/"scripts/install.sh"
    delimiter = "DJCONNECT_QUALIFIED_RC6_ROOT_HELPER"
    need(delimiter.encode() not in code, "RECOVERY_HELPER_INVALID")
    helper.write_bytes(b"#!/bin/sh\nexec /usr/bin/python3 -I - \"$@\" <<'"+delimiter.encode()+b"'\n"+code+b"\n"+delimiter.encode()+b"\n")
    helper.chmod(0o700)
    log = stage/"recovery-root-private.log"
    with log.open("xb") as output:
        log.chmod(0o600)
        result = subprocess.run(["sudo", "-n", str(helper), payload["run_id"], boot],
            stdout=output, stderr=subprocess.STDOUT, check=False, timeout=1350)
    need(result.returncode == 0 and log.stat().st_size <= 65536, "RECOVERY_PHASE_INCONCLUSIVE")
    proof = json.loads(log.read_bytes())
    need(isinstance(proof, dict) and proof.get("result") == "RECOVERED_PENDING_SMOKE"
         and proof.get("original_deployment_workflow_run") == "39669504016"
         and proof.get("recovery_workflow_run") == payload["run_id"] and proof.get("source") == payload["source"]
         and proof.get("watchdog_restored") is True and proof.get("configuration_preserved") is True
         and type(proof.get("verified_packaged_files")) is int and proof["verified_packaged_files"] == 80,
         "RECOVERY_RESULT_INVALID")
    need(Path("/proc/sys/kernel/random/boot_id").read_text().strip() == boot, "RECOVERY_BOOT_CHANGED")
    return {"result": "RECOVERED_PENDING_SMOKE", "configuration_preserved_by_installer": True,
        "watchdog_restored": True, "verified_packaged_files": 80,
        "original_deployment_workflow_run": "39669504016", "services": services()}


def smoke(payload):
    root = Path("/opt/djconnect/current")
    need(text(root/"VERSION") == VERSION and text(root/"SOURCE_COMMIT") == payload["source"]
        and text(root/"RELEASE_PROFILE") == payload["device_profile"], "INSTALLED_IDENTITY_MISMATCH")
    wheel = root/"wheels"/payload["wheel_name"]
    need(wheel.stat().st_size <= 8388608, "INSTALLED_WHEEL_MISMATCH")
    with wheel.open("rb") as stream:need(hashlib.file_digest(stream, "sha256").hexdigest() == payload["wheel_sha256"], "INSTALLED_WHEEL_MISMATCH")
    sites = list((root/".venv/lib").glob("python*/site-packages"));need(len(sites) == 1)
    with zipfile.ZipFile(wheel) as archive:
        members = [name for name in archive.namelist() if name.startswith("djconnect_pi/") and not name.endswith("/")]
        need(bool(members) and len(members) <= 256)
        for name in members:
            path = PurePosixPath(name);need(not path.is_absolute() and ".." not in path.parts)
            need(archive.getinfo(name).file_size <= 8388608)
            expected = archive.read(name)
            with sites[0].joinpath(*path.parts).open("rb") as stream:actual = stream.read(len(expected)+1)
            need(actual == expected, "INSTALLED_SOURCE_BYTES_MISMATCH")
    current = services();need(all(row["active"] and row["pid"] > 0 for row in current.values()), "SERVICES_NOT_READY")
    opener = build_opener(ProxyHandler({}))
    with opener.open("http://127.0.0.1:18080/api/device/info", timeout=8) as response:
        raw = response.read(65537);need(len(raw) <= 65536)
    info = json.loads(raw)
    need(info.get("success") is True and info.get("client_type") == "raspberry_pi"
        and info.get("transport") == "local_only" and info.get("version") == VERSION, "LOCAL_API_NOT_READY")
    return {"result": "SMOKE_PASS", "installed_source": payload["source"], "installed_version": VERSION,
        "installed_device_profile": payload["device_profile"], "api_reachable": True,
        "client_active": current["djconnect-client.service"]["active"], "api_active": current["djconnect-api.service"]["active"],
        "paired": info.get("paired") is True, "services": current, "verified_packaged_files": len(members)}


# Fixed observer bytes/entrypoint only. The existing sudo policy is checked for
# this exact staged command; no rule, credential, installer or service changes.
OBSERVER_SHA256 = "4ae5b8fa3297785a362dfb2e36354cffb4168ab2d0572ef169288d559239e36c"


def stage_observer(payload):
    code = base64.b64decode(payload["recovery_observer"], validate=True)
    need(len(code) <= 16384 and hashlib.sha256(code).hexdigest() == OBSERVER_SHA256, "RECOVERY_OBSERVER_BYTES_CHANGED")
    stage = Path.home()/"djconnect-install"/("djconnect-pi-rc6-observe-"+payload["run_id"])
    need(not stage.exists() and not stage.is_symlink() and not stage.parent.is_symlink(), "RECOVERY_OBSERVER_STAGING_EXISTS")
    stage.mkdir(mode=0o700);(stage/"scripts").mkdir(mode=0o700)
    helper = stage/"scripts/install.sh"
    delimiter = "DJCONNECT_QUALIFIED_RC6_READONLY_OBSERVER"
    need(delimiter.encode() not in code, "RECOVERY_OBSERVER_INVALID")
    helper.write_bytes(b"#!/bin/sh\nexec /usr/bin/python3 -I -B - \"$@\" <<'"+delimiter.encode()+b"'\n"+code+b"\n"+delimiter.encode()+b"\n")
    helper.chmod(0o700)
    return helper


def observe_recovery(helper, boot):
    command = [str(helper), boot]
    allowed = subprocess.run(["sudo", "-n", "-l", "--", *command], capture_output=True, timeout=8, check=False)
    need(allowed.returncode == 0 and len(allowed.stdout) <= 65536 and len(allowed.stderr) <= 65536, "RECOVERY_OBSERVER_NOT_AUTHORIZED")
    proc = subprocess.run(["sudo", "-n", "--", *command], capture_output=True, timeout=10, check=False)
    need(proc.returncode == 0 and not proc.stderr and len(proc.stdout) <= 1024, "RECOVERY_OBSERVER_FAILED")
    proof = json.loads(proc.stdout)
    need(isinstance(proof, dict) and set(proof) == {"boot_id", "configuration_sha256"}
         and proof["boot_id"] == boot and isinstance(proof["configuration_sha256"], str)
         and re.fullmatch("[0-9a-f]{64}", proof["configuration_sha256"]), "RECOVERY_OBSERVER_FAILED")
    return proof


def closed_recovery(payload):
    boot = payload["recovery_boot_id"]
    need(Path("/proc/sys/kernel/random/boot_id").read_text().strip() == boot, "RECOVERY_BOOT_CHANGED")
    helper = stage_observer(payload)
    before = observe_recovery(helper, boot)
    if payload["phase"] == "recover":
        result = recover(payload)
    else:
        need(payload["phase"] == "recovery-smoke", "RECOVERY_CONTEXT_INVALID")
        need(before == payload["recovery_observation"], "RECOVERY_OBSERVATION_CHANGED")
        result = smoke(payload)
        timer = subprocess.run(["systemctl", "show", "djconnect-watchdog.timer", "--property=ActiveState,UnitFileState", "--no-pager"], capture_output=True, text=True, timeout=8, check=False)
        condition = subprocess.run(["systemctl", "show", "djconnect-watchdog.service", "--property=ExecCondition", "--no-pager"], capture_output=True, text=True, timeout=8, check=False)
        fields = dict(line.split("=", 1) for line in timer.stdout.splitlines() if "=" in line)
        need(timer.returncode == condition.returncode == 0 and fields == {"ActiveState":"active", "UnitFileState":"enabled"}
             and condition.stdout.strip() == "ExecCondition=", "RECOVERY_WATCHDOG_NOT_RESTORED")
        need(result["paired"] is True and result["verified_packaged_files"] == 80, "RECOVERY_SMOKE_INVALID")
    after = observe_recovery(helper, boot)
    need(before == after, "RECOVERY_OBSERVATION_CHANGED")
    return {**result, "recovery_observation": after}


def main():
    challenge = sys.argv[1];need(re.fullmatch("[0-9a-f]{64}", challenge) is not None)
    recovery_context = sys.argv[2:] in (["recovery"], ["recovery-smoke"])
    context_phase = "recover" if sys.argv[2:] == ["recovery"] else "recovery-smoke"
    need(sys.argv[2:] in ([], ["recovery"], ["recovery-smoke"]), "REMOTE_CONTEXT_INVALID")
    initial = identity(challenge)
    if recovery_context:initial["boot_id"] = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    print(json.dumps(initial), flush=True)
    raw = sys.stdin.buffer.readline(44755609)
    need(len(raw) < 44755609, "INTENT_TOO_LARGE")
    payload = json.loads(raw)
    observed = identity(challenge)
    if recovery_context:observed["boot_id"] = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    need(isinstance(payload, dict) and observed == initial, "TARGET_CHANGED")
    need((recovery_context and payload.get("phase") == context_phase)
         or (not recovery_context and payload.get("phase") not in {"recover", "recovery-smoke"}), "REMOTE_RECOVERY_CONTEXT_MISMATCH")
    if payload == {"phase": "readiness"}:
        result = {"result": "TARGET_READY" if installer_permission() else "TARGET_NOT_READY", "current_version": text("/opt/djconnect/current/VERSION"), "services": services()}
    else:
        common = {"phase", "source", "version", "device_profile", "wheel_name", "wheel_sha256", "run_id", "artifact_sha256"}
        extra = {"artifact"} if payload.get("phase") == "deploy" else set()
        if recovery_context:
            extra = {"recovery_observer", "recovery_boot_id"}
            extra |= {"recovery_helper"} if context_phase == "recover" else {"recovery_observation"}
        need(set(payload) == common | extra)
        need(payload.get("phase") in {"deploy", "smoke", "recover", "recovery-smoke"} and payload.get("version") == VERSION
            and payload.get("device_profile") == initial["device_profile"]
            and re.fullmatch("[0-9a-f]{40}", payload.get("source", "")) is not None
            and re.fullmatch("[0-9a-f]{64}", payload.get("artifact_sha256", "")) is not None
            and re.fullmatch("[0-9a-f]{64}", payload.get("wheel_sha256", "")) is not None
            and payload.get("wheel_name") == "djconnect_pi-4.0.0rc6-py3-none-any.whl"
            and re.fullmatch("[1-9][0-9]*", payload.get("run_id", "")) is not None)
        result = deploy(payload) if payload["phase"] == "deploy" else closed_recovery(payload) if recovery_context else smoke(payload)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    try:main()
    except (OSError, ValueError, KeyError, TypeError, EOFError, tarfile.TarError, zipfile.BadZipFile, subprocess.SubprocessError):
        # Private process output/config/URLs never escape this channel on failure.
        print(json.dumps({"result": "REMOTE_PHASE_INCONCLUSIVE", "code": "REQUIRES_ACTUAL_STATE_REVIEW"}), flush=True)
        raise SystemExit(1) from None
