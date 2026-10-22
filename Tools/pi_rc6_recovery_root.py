"""Closed wall-4inch rc.6 recovery candidate; not an execution grant.

Only a separately qualified recovery workflow may stage this privileged helper.
No endpoints, paths, source versions or commands are supplied by the caller.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import platform
import re
import socket
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from urllib.request import HTTPRedirectHandler, ProxyHandler, build_opener

SOURCE = "0dde0abe22a0859f170a7c1d3eab41f1ade44d37"
VERSION = "4.0.0-rc.6"
PROFILE = "pi-zero-2w-arm64"
ORIGINAL_RUN = "39669504016"
ARTIFACT_SHA256 = "d67869ffca53c4936059bdbbdbdf6be63b36eafac269fa2f3f9b090922cd0d64"
INSTALLER_SHA256 = "712474d158524903542588ba513801b7953df625c0c8fc26710706a6655e37cc"
WHEEL_SHA256 = "0f238c4e978ad7b84684e5934761d5391fb1040016371b5b9204039f6ea7a18a"
WHEEL = "djconnect_pi-4.0.0rc6-py3-none-any.whl"
DEVICE = "djconnect-raspberry-pi-D83ADD41F167"
PACKAGED_FILES = 80
TIMER = "djconnect-watchdog.timer"
WATCHDOG = "djconnect-watchdog.service"
API = "djconnect-api.service"
CLIENT = "djconnect-client.service"


DIAGNOSTIC_CODES = frozenset(('RECOVERY_API_IDENTITY_CHANGED', 'RECOVERY_API_UNAVAILABLE', 'RECOVERY_ARCHIVE_BOUND', 'RECOVERY_ARCHIVE_DUPLICATE', 'RECOVERY_ARTIFACT_CHANGED', 'RECOVERY_BOOT_CHANGED', 'RECOVERY_BOOT_INVALID', 'RECOVERY_COMMAND_FAILED', 'RECOVERY_CONFIG_CHANGED', 'RECOVERY_EXISTING_MAINTENANCE', 'RECOVERY_FILE_BOUND', 'RECOVERY_FILE_INVALID', 'RECOVERY_GUARD_NOT_LOADED', 'RECOVERY_HOLD_FAILED', 'RECOVERY_HOLD_OWNERSHIP_CHANGED', 'RECOVERY_INCOMPLETE', 'RECOVERY_INCOMPLETE_REQUIRES_STATE_REVIEW', 'RECOVERY_INSTALLED_BYTES_CHANGED', 'RECOVERY_INSTALLER_CHANGED', 'RECOVERY_INSTALLER_INCOMPLETE', 'RECOVERY_INSTALLER_INVALID', 'RECOVERY_INSTALLER_STILL_RUNNING', 'RECOVERY_INSTALL_LAYOUT', 'RECOVERY_JSON_BOUND', 'RECOVERY_JSON_DUPLICATE', 'RECOVERY_JSON_INVALID', 'RECOVERY_JSON_NONFINITE', 'RECOVERY_JSON_OBJECT', 'RECOVERY_LEDGER_INVALID', 'RECOVERY_MARKER_CHANGED', 'RECOVERY_ORIGINAL_STATE_CHANGED', 'RECOVERY_PACKAGED_COUNT', 'RECOVERY_PATH_CHANGED', 'RECOVERY_PID_INVALID', 'RECOVERY_PROCESS_BOUND', 'RECOVERY_RELEASE_CHANGED', 'RECOVERY_ROOT_CONTEXT_REQUIRED', 'RECOVERY_RUN_INVALID', 'RECOVERY_SERVICES_NOT_STABLE', 'RECOVERY_SHUTDOWN_PENDING', 'RECOVERY_STAGING_CHANGED', 'RECOVERY_TARGET_CHANGED', 'RECOVERY_UNIT_INVALID', 'RECOVERY_UNIT_NOT_ALLOWED', 'RECOVERY_UNIT_POLICY_CHANGED', 'RECOVERY_WATCHDOG_CUSTOMIZED', 'RECOVERY_WATCHDOG_NOT_RESTORED', 'RECOVERY_WATCHDOG_STATE_CHANGED', 'RECOVERY_WHEEL_CHANGED', 'RECOVERY_WHEEL_LAYOUT'))

class RecoveryError(ValueError):
    """Static machine codes only; private process/configuration data never escape."""


def need(condition, code):
    if not condition:
        raise RecoveryError(code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def strict_object(raw, maximum=2097152):
    need(isinstance(raw, bytes) and len(raw) <= maximum, "RECOVERY_JSON_BOUND")
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, "RECOVERY_JSON_DUPLICATE")
            result[key] = value
        return result
    def invalid(_):
        raise RecoveryError("RECOVERY_JSON_NONFINITE")
    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    except (ValueError, TypeError, RecursionError):
        raise RecoveryError("RECOVERY_JSON_INVALID") from None
    need(isinstance(value, dict), "RECOVERY_JSON_OBJECT")
    return value


def private_config_digest(raw):
    value = strict_object(raw)
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode())


@dataclass(frozen=True)
class Prepared:
    artifact: bytes
    installer: bytes
    config_digest: str
    boot_id: str
    api_pid: int


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class System:
    """Production paths are fixed; only tests substitute an in-memory System."""
    root = Path("/opt/djconnect")
    stage = Path("/home/pi/djconnect-install/djconnect-pi-rc6-"+ORIGINAL_RUN+"-"+PROFILE)
    ledger = Path("/var/lib/djconnect-pi-recovery/rc6-wall4-from-"+ORIGINAL_RUN)
    guard_dir = Path("/run/systemd/system")/(WATCHDOG+".d")
    guard_name = "90-djconnect-rc6-wall4-recovery.conf"
    guard_content = b"[Service]\nExecCondition=/usr/bin/false\n"

    def read(self, path, maximum):
        # Read a stable descriptor; never reopen a mutable caller path after verification.
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as stream:
            meta = os.fstat(stream.fileno())
            need(stat.S_ISREG(meta.st_mode) and meta.st_size <= maximum
                 and not stat.S_IMODE(meta.st_mode) & 0o022, "RECOVERY_FILE_INVALID")
            raw = stream.read(maximum+1)
        need(len(raw) <= maximum, "RECOVERY_FILE_BOUND")
        return raw

    def identity(self):
        need(socket.gethostname() == "rbpi-djconnect" and platform.machine() == "aarch64"
             and self.read(Path("/proc/device-tree/model"), 128).rstrip(b"\0\n") == b"Raspberry Pi Zero 2 W Rev 1.0"
             and self.read(Path("/etc/djconnect-pi/device-profile"), 128) == (PROFILE+"\n").encode(),
             "RECOVERY_TARGET_CHANGED")
        for path in (self.stage, self.stage.parent, self.root, self.root/"config", self.root/"releases",
                     self.root/"releases"/(VERSION+"-"+PROFILE)):
            need(path.is_dir() and not path.is_symlink(), "RECOVERY_PATH_CHANGED")

    def boot(self):
        return self.read(Path("/proc/sys/kernel/random/boot_id"), 64).decode().strip()

    def command(self, args):
        result = subprocess.run(args, capture_output=True, timeout=30, check=False,
                                env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C.UTF-8"})
        need(result.returncode == 0 and len(result.stdout) <= 32768, "RECOVERY_COMMAND_FAILED")
        return result.stdout.decode("utf-8", errors="strict")

    def unit(self, name):
        need(name in {API, CLIENT, WATCHDOG, TIMER}, "RECOVERY_UNIT_NOT_ALLOWED")
        # MainPID belongs to service units. The fixed watchdog timer has no PID.
        properties = "LoadState,ActiveState,UnitFileState"
        expected = {"LoadState", "ActiveState", "UnitFileState"}
        if name != TIMER:
            properties += ",MainPID";expected.add("MainPID")
        raw = self.command(["/usr/bin/systemctl", "show", name, "--property="+properties, "--no-pager"])
        fields = {}
        for line in raw.splitlines():
            key, separator, value = line.partition("=")
            need(separator and key not in fields, "RECOVERY_UNIT_INVALID")
            fields[key] = value
        need(set(fields) == expected, "RECOVERY_UNIT_INVALID")
        if name != TIMER:
            need(re.fullmatch(r"[0-9]+", fields["MainPID"]) is not None, "RECOVERY_PID_INVALID")
        return fields

    def no_competing_installer(self):
        original = str(self.stage/"scripts/install.sh").encode()
        venv = str(self.root/"releases"/(VERSION+"-"+PROFILE)/".venv").encode()
        for path in Path("/proc").glob("[0-9]*/cmdline"):
            try:
                raw = path.read_bytes()
            except FileNotFoundError:
                continue
            need(len(raw) <= 1048576, "RECOVERY_PROCESS_BOUND")
            args = raw.split(b"\0")
            need(original not in args, "RECOVERY_INSTALLER_STILL_RUNNING")
            own_helper = ("/home/pi/djconnect-install/djconnect-pi-rc6-recovery-"
                          +self.recovery_run+"/scripts/install.sh").encode()
            for item in args:
                other_stage = item.startswith(b"/home/pi/djconnect-install/djconnect-pi-") and item.endswith(b"/scripts/install.sh")
                sealed_installer = item.startswith(b"/run/djconnect-rc6-recovery-") and item.endswith(b"/install.sh")
                need(not sealed_installer and (not other_stage or item == own_helper), "RECOVERY_INSTALLER_STILL_RUNNING")
            need(not (any(item.startswith(venv) for item in args) and b"pip" in args), "RECOVERY_INSTALLER_STILL_RUNNING")
            need(not (args and args[0].rsplit(b"/", 1)[-1] == b"chown" and str(self.root).encode() in args), "RECOVERY_INSTALLER_STILL_RUNNING")
        jobs = self.command(["/usr/bin/systemctl", "list-jobs", "--no-legend", "--plain"])
        need(re.search(r"(?:reboot|poweroff|halt|shutdown)\.(?:target|service)", jobs) is None, "RECOVERY_SHUTDOWN_PENDING")

    def api(self):
        opener = build_opener(ProxyHandler({}), NoRedirect())
        with opener.open("http://127.0.0.1:18080/api/device/info", timeout=8) as response:
            need(response.status == 200, "RECOVERY_API_UNAVAILABLE")
            raw = response.read(65537)
        info = strict_object(raw, 65536)
        need(info.get("success") is True and info.get("client_type") == "raspberry_pi"
             and info.get("device_id") == DEVICE and info.get("version") == VERSION
             and info.get("paired") is True, "RECOVERY_API_IDENTITY_CHANGED")

    def installed(self):
        current = self.root/"current"
        expected = self.root/"releases"/(VERSION+"-"+PROFILE)
        need(current.is_symlink() and current.resolve(strict=True) == expected, "RECOVERY_RELEASE_CHANGED")
        for name, value in (("VERSION", VERSION), ("SOURCE_COMMIT", SOURCE), ("RELEASE_PROFILE", PROFILE)):
            need(self.read(expected/name, 128) == (value+"\n").encode(), "RECOVERY_RELEASE_CHANGED")
        raw = self.read(expected/"wheels"/WHEEL, 8388608)
        need(digest(raw) == WHEEL_SHA256, "RECOVERY_WHEEL_CHANGED")
        sites = list((expected/".venv/lib").glob("python*/site-packages"))
        need(len(sites) == 1, "RECOVERY_INSTALL_LAYOUT")
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            names = [name for name in archive.namelist() if name.startswith("djconnect_pi/") and not name.endswith("/")]
            need(len(names) == PACKAGED_FILES and len(set(names)) == len(names), "RECOVERY_PACKAGED_COUNT")
            for name in names:
                need(".." not in Path(name).parts and not Path(name).is_absolute(), "RECOVERY_WHEEL_LAYOUT")
                need(archive.getinfo(name).file_size <= 8388608, "RECOVERY_WHEEL_LAYOUT")
                need(self.read(sites[0]/name, 8388608) == archive.read(name), "RECOVERY_INSTALLED_BYTES_CHANGED")

    def artifact(self):
        raw = self.read(self.stage/"approved-artifact.tar.gz", 33554432)
        need(digest(raw) == ARTIFACT_SHA256, "RECOVERY_ARTIFACT_CHANGED")
        prefix = "djconnect-pi-"+PROFILE+"-"+VERSION
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
            members = archive.getmembers()
            need(len(members) <= 4096 and sum(m.size for m in members) <= 67108864, "RECOVERY_ARCHIVE_BOUND")
            names = [m.name for m in members]
            need(len(set(names)) == len(names), "RECOVERY_ARCHIVE_DUPLICATE")
            member = archive.getmember(prefix+"/scripts/install.sh")
            need(member.isfile() and member.size <= 131072, "RECOVERY_INSTALLER_INVALID")
            installer = archive.extractfile(member).read(131073)
            need(digest(installer) == INSTALLER_SHA256, "RECOVERY_INSTALLER_CHANGED")
            # An unknown prior edited installer is not silently repaired from the tar.
            need(self.read(self.stage/"scripts/install.sh", 131072) == installer, "RECOVERY_STAGING_CHANGED")
            self._watchdog_units = {}
            for name in ("djconnect-watchdog.service", "djconnect-watchdog.timer"):
                original = archive.extractfile(prefix+"/systemd/"+name).read(32769)
                self._watchdog_units[name] = original
                need(self.read(Path("/etc/systemd/system")/name, 32768) == original, "RECOVERY_WATCHDOG_CUSTOMIZED")
                for parent in (Path("/etc/systemd/system"), Path("/run/systemd/system")):
                    drop = parent/(name+".d")
                    need(not drop.exists() or (drop.is_dir() and not any(drop.iterdir())), "RECOVERY_WATCHDOG_CUSTOMIZED")
        return raw, installer

    def markers(self):
        state = self.root/"install-state"/(VERSION+"-"+PROFILE)
        need(self.read(state/"approved-artifact.sha256", 128) == (ARTIFACT_SHA256+"\n").encode(), "RECOVERY_MARKER_CHANGED")
        for name in ("release_unpacked.done", "venv_ready.done"):
            need(self.read(state/name, 128) == b"", "RECOVERY_MARKER_CHANGED")

    def claim(self, run):
        parent = self.ledger.parent
        if not parent.exists():
            parent.mkdir(mode=0o700)
        need(not parent.is_symlink() and parent.stat().st_uid == 0
             and stat.S_IMODE(parent.stat().st_mode) == 0o700, "RECOVERY_LEDGER_INVALID")
        def sync_directory(path):
            fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        # A file fsync does not persist its directory entry. Persist the possibly
        # new private parent, claim data/metadata, claim entry, then ledger entry.
        # Every failure propagates before hold/install; no cleanup or rearm.
        sync_directory(parent.parent)
        self.ledger.mkdir(mode=0o700)
        fd = os.open(self.ledger/"claim.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write((json.dumps({"original_run": ORIGINAL_RUN, "recovery_run": run, "source": SOURCE})+"\n").encode())
            stream.flush()
            os.fchmod(stream.fileno(), 0o600)
            os.fsync(stream.fileno())
        sync_directory(self.ledger)
        sync_directory(parent)

    def maintenance_available(self):
        need(not self.guard_dir.exists() and not self.guard_dir.is_symlink(), "RECOVERY_EXISTING_MAINTENANCE")

    def configuration(self, holding=False):
        for name in (WATCHDOG, TIMER):
            if hasattr(self, "_watchdog_units"):
                need(self.read(Path("/etc/systemd/system")/name, 32768) == self._watchdog_units[name], "RECOVERY_WATCHDOG_CUSTOMIZED")
            raw = self.command(["/usr/bin/systemctl", "show", name,
                "--property=FragmentPath,DropInPaths,SuccessAction,FailureAction,JobTimeoutAction,OnSuccess,OnFailure", "--no-pager"])
            values = dict(line.split("=", 1) for line in raw.splitlines() if "=" in line)
            expected = {"FragmentPath": "/etc/systemd/system/"+name, "DropInPaths": "",
                "SuccessAction": "none", "FailureAction": "none", "JobTimeoutAction": "none", "OnSuccess": "", "OnFailure": ""}
            if holding and name == WATCHDOG:
                expected["DropInPaths"] = str(self.guard_dir/self.guard_name)
            need(values == expected, "RECOVERY_UNIT_POLICY_CHANGED")
        if holding:
            raw = self.command(["/usr/bin/systemctl", "show", WATCHDOG, "--property=ExecCondition", "--value"])
            need(re.fullmatch(r"\{ path=/usr/bin/false ; argv\[\]=/usr/bin/false ; ignore_errors=no ; [^\r\n]* \}\n?", raw) is not None,
                 "RECOVERY_GUARD_NOT_LOADED")

    def hold(self):
        self.maintenance_available();self.configuration()
        self.command(["/usr/bin/systemctl", "stop", TIMER, WATCHDOG])
        # A runtime mask would be shadowed by the existing /etc unit. A distinct
        # runtime drop-in is parsed after that unit and survives installer reloads.
        self.guard_dir.mkdir(mode=0o700)
        guard = self.guard_dir/self.guard_name
        fd = os.open(guard, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(self.guard_content);stream.flush();os.fsync(stream.fileno())
            self._guard_inode = os.fstat(stream.fileno()).st_ino
        self.command(["/usr/bin/systemctl", "daemon-reload"])
        self.configuration(holding=True)
        need(self.unit(TIMER)["ActiveState"] == "inactive"
             and self.unit(WATCHDOG)["ActiveState"] == "inactive", "RECOVERY_HOLD_FAILED")

    def install(self, prepared):
        # Only the sealed original published installer executes, with a closed environment.
        with tempfile.TemporaryDirectory(prefix="djconnect-rc6-recovery-", dir="/run") as temp:
            directory = Path(temp)
            installer = directory/"install.sh";installer.write_bytes(prepared.installer);installer.chmod(0o700)
            artifact = directory/"artifact.tar.gz";artifact.write_bytes(prepared.artifact);artifact.chmod(0o600)
            with (self.ledger/"installer-private.log").open("xb") as output:
                (self.ledger/"installer-private.log").chmod(0o600)
                result = subprocess.run(["/bin/bash", str(installer), "--approved-artifact", str(artifact),
                    "--artifact-sha256", ARTIFACT_SHA256, "--source-sha", SOURCE], stdout=output,
                    stderr=subprocess.STDOUT, check=False, timeout=1200,
                    env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "HOME": "/root", "LANG": "C.UTF-8",
                         "SUDO_USER": "pi", "DJCONNECT_RELEASE_PROFILE": PROFILE})
            need(result.returncode == 0, "RECOVERY_INSTALLER_INCOMPLETE")

    def healthy(self, prepared):
        deadline = time.monotonic()+90
        previous = None;stable_since = None
        while True:
            units = [self.unit(API), self.unit(CLIENT)]
            pids = tuple(int(u["MainPID"]) for u in units)
            if all(u["ActiveState"] == "active" for u in units) and all(pids) and pids[0] != prepared.api_pid:
                try:
                    self.api()
                except OSError:
                    # Startup health reads may settle; no mutation or request is replayed.
                    previous = None;stable_since = None
                    need(time.monotonic() < deadline, "RECOVERY_SERVICES_NOT_STABLE")
                    time.sleep(2)
                    continue
                if pids != previous:
                    previous = pids;stable_since = time.monotonic()
                if time.monotonic()-stable_since >= 6:
                    return
            else:
                previous = None;stable_since = None
            need(time.monotonic() < deadline, "RECOVERY_SERVICES_NOT_STABLE")
            time.sleep(2)

    def restore(self):
        guard = self.guard_dir/self.guard_name
        need(not self.guard_dir.is_symlink() and list(self.guard_dir.iterdir()) == [guard]
             and guard.lstat().st_ino == self._guard_inode
             and self.read(guard, 1024) == self.guard_content, "RECOVERY_HOLD_OWNERSHIP_CHANGED")
        self.configuration(holding=True)
        # Remove only our exact new runtime guard; do not touch any original unit.
        guard.unlink();self.guard_dir.rmdir()
        self.command(["/usr/bin/systemctl", "daemon-reload"])
        self.configuration()
        self.command(["/usr/bin/systemctl", "restart", TIMER])
        timer = self.unit(TIMER)
        need(timer["ActiveState"] == "active" and timer["UnitFileState"] == "enabled"
             and not self.guard_dir.exists(), "RECOVERY_WATCHDOG_NOT_RESTORED")

    def record(self, value):
        target = self.ledger/"result.json"
        target.write_text(json.dumps(value, sort_keys=True)+"\n");target.chmod(0o600)


def prepare(system, run, expected_boot):
    need(re.fullmatch(r"[1-9][0-9]*", run or "") is not None and run != ORIGINAL_RUN, "RECOVERY_RUN_INVALID")
    need(re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", expected_boot or "") is not None,
         "RECOVERY_BOOT_INVALID")
    need(system.boot() == expected_boot, "RECOVERY_BOOT_CHANGED")
    system.identity();system.no_competing_installer();system.installed();system.markers();system.maintenance_available();system.configuration()
    timer = system.unit(TIMER);watchdog = system.unit(WATCHDOG)
    api = system.unit(API);client = system.unit(CLIENT)
    need(timer["ActiveState"] == "active" and timer["UnitFileState"] == "enabled"
         and watchdog["LoadState"] == "loaded" and watchdog["ActiveState"] == "inactive", "RECOVERY_WATCHDOG_STATE_CHANGED")
    need(api["ActiveState"] == "active" and int(api["MainPID"]) > 0
         and client["ActiveState"] == "inactive" and client["UnitFileState"] == "disabled"
         and client["MainPID"] == "0", "RECOVERY_ORIGINAL_STATE_CHANGED")
    system.api();artifact, installer = system.artifact()
    config = private_config_digest(system.read(system.root/"config/client.json", 2097152))
    need(system.boot() == expected_boot, "RECOVERY_BOOT_CHANGED")
    return Prepared(artifact, installer, config, expected_boot, int(api["MainPID"]))


def execute(system, run, expected_boot):
    system.recovery_run = run
    prepared = prepare(system, run, expected_boot)
    system.claim(run)  # Burns once before any watchdog/installer command; never automatically rearmed.
    result = {"result": "RECOVERY_INCOMPLETE", "original_deployment_workflow_run": ORIGINAL_RUN,
              "recovery_workflow_run": run, "source": SOURCE, "watchdog_state": "REQUIRES_ACTUAL_READBACK"}
    try:
        need(system.boot() == prepared.boot_id, "RECOVERY_BOOT_CHANGED")
        system.hold();system.no_competing_installer()
        system.install(prepared);system.healthy(prepared);system.installed()
        need(private_config_digest(system.read(system.root/"config/client.json", 2097152)) == prepared.config_digest,
             "RECOVERY_CONFIG_CHANGED")
        need(system.boot() == prepared.boot_id, "RECOVERY_BOOT_CHANGED")
        system.restore();system.api()
        result.update(result="RECOVERED_PENDING_SMOKE", watchdog_restored=True, watchdog_state="RESTORED",
                      configuration_preserved=True, verified_packaged_files=PACKAGED_FILES)
        system.record(result)
        return result
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        # Never remove the runtime guard on an unproven installation; the original intent and claim remain.
        system.record(result)
        raise RecoveryError("RECOVERY_INCOMPLETE_REQUIRES_STATE_REVIEW") from None


def main():
    need(os.geteuid() == 0 and len(sys.argv) == 3, "RECOVERY_ROOT_CONTEXT_REQUIRED")
    print(json.dumps(execute(System(), sys.argv[1], sys.argv[2])), flush=True)


if __name__ == "__main__":
    try:
        main()
    except RecoveryError as error:
        code = str(error) if str(error) in DIAGNOSTIC_CODES else "REQUIRES_ACTUAL_STATE_REVIEW"
        print(json.dumps({"result": "RECOVERY_INCOMPLETE", "code": code}), flush=True)
        raise SystemExit(1) from None
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        print(json.dumps({"result": "RECOVERY_INCOMPLETE", "code": "REQUIRES_ACTUAL_STATE_REVIEW"}), flush=True)
        raise SystemExit(1) from None
