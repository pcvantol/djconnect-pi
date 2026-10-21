"""One fresh authenticated SSH channel; no free endpoint or automatic intent replay."""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import selectors
import shlex
import stat
import subprocess
import time
from pathlib import Path

from Tools.pi_instance_contract import (
    CONFIGURATION_REFS,
    BindingError,
    require,
    strict_json,
    validate_identity,
)

# Fixed effective mapping candidate digests only; private endpoints/users/key paths stay outside source.
CONFIGURATION_DIGESTS = {'wall-4inch': 'aedaecc9cfb4474a23767c814c2d288d8e879c2e3008e4aedaa238e9414bcae6', 'wall-10inch': 'd4963bdd8137887928add2675b47e4456c61cffc4db746ba79449a65adddbf69'}
SSH_CLIENT = "/usr/bin/ssh"
CONFIGURATION_FIELDS = {"hostname", "user", "port", "identityfile", "proxycommand", "proxyjump", "userknownhostsfile", "globalknownhostsfile", "hostkeyalias", "identityagent", "setenv"}


def ssh_environment():
    # GitHub/HA/provider tokens and arbitrary SendEnv values never enter the SSH process.
    names = {"PATH", "USER", "LOGNAME", "LANG", "LC_CTYPE", "LC_ALL", "SSH_AUTH_SOCK"}
    return {**{name: value for name, value in os.environ.items() if name in names}, "HOME": str(Path.home())}


def configuration_digest(configuration: Path, alias: str) -> str:
    result = subprocess.run([SSH_CLIENT, "-G", "-F", str(configuration), "-o", "ForwardAgent=no", "-o", "ForwardX11=no", "-o", "RemoteCommand=none", alias], capture_output=True, text=True, timeout=10, check=False, env=ssh_environment())
    require(result.returncode == 0 and len(result.stdout) <= 65536, "SSH_CONFIGURATION_NOT_READY")
    selected = {}
    for line in result.stdout.splitlines():
        key, _separator, value = line.partition(" ")
        if key in CONFIGURATION_FIELDS:selected.setdefault(key, []).append(value)
    require({"hostname", "user", "port", "identityfile"} <= set(selected), "SSH_CONFIGURATION_NOT_READY")
    require(selected.get("setenv") in (None, [], [""]), "SSH_SETENV_NOT_QUALIFIED")
    return hashlib.sha256(json.dumps(selected, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class Channel:
    def __init__(self, binding, timeout=15, *, recovery=False):
        require(type(recovery) is bool, "SSH_CONTEXT_INVALID")
        self.recovery_boot_id = None
        instance = binding.request["deployment_instance"]
        require(instance in CONFIGURATION_REFS and binding.inventory_row["endpoint_config_ref"] == CONFIGURATION_REFS[instance], "CLOSED_CONFIGURATION_REQUIRED")
        self.binding = binding;self.sent = False;self.challenge = secrets.token_hex(32)
        self.instance = instance
        configuration = Path.home()/".ssh/config"
        require(configuration.is_file() and not configuration.is_symlink(), "SSH_CONFIGURATION_NOT_READY")
        metadata = configuration.stat()
        require(metadata.st_uid == os.getuid() and not stat.S_IMODE(metadata.st_mode) & 0o022, "SSH_CONFIGURATION_NOT_READY")
        require(configuration_digest(configuration, CONFIGURATION_REFS[instance]) == CONFIGURATION_DIGESTS[instance], "SSH_CONFIGURATION_MAPPING_CHANGED")
        self.configuration = configuration
        source = Path(__file__).with_name("pi_instance_remote_payload.py").read_text(encoding="utf-8")
        command = "python3 -u -c "+shlex.quote(source)+" "+self.challenge+(" recovery" if recovery else "")
        args = [SSH_CLIENT, "-F", str(configuration), "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
            "-o", "UpdateHostKeys=no", "-o", "ControlMaster=no", "-o", "ControlPath=none",
            "-o", "ConnectionAttempts=1", "-o", "ConnectTimeout=8", "-o", "ServerAliveInterval=10",
            "-o", "ServerAliveCountMax=2", "-o", "HostKeyAlgorithms=ssh-ed25519", "-o", "ClearAllForwardings=yes",
            "-o", "PermitLocalCommand=no", "-o", "ForwardAgent=no", "-o", "ForwardX11=no", "-o", "RemoteCommand=none", "-o", "RequestTTY=no", "-o", "LogLevel=DEBUG1", CONFIGURATION_REFS[instance], command]
        self.process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ssh_environment())
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ, "stdout")
        self.selector.register(self.process.stderr, selectors.EVENT_READ, "stderr")
        self.stdout = bytearray();self.stderr = bytearray();self.keys = set()
        try:
            observed = self.read_line(timeout)
            require(self.keys == {binding.inventory_row["ssh_host_key_sha256"]}, "SSH_NEGOTIATED_KEY_MISMATCH")
            if recovery:
                require(isinstance(observed, dict) and set(observed) == {"challenge", "hostname", "architecture", "model", "device_profile", "boot_id"}, "TARGET_NOT_READY")
                self.recovery_boot_id = observed.pop("boot_id")
                require(isinstance(self.recovery_boot_id, str) and re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", self.recovery_boot_id) is not None, "TARGET_NOT_READY")
            require(set(observed) == {"challenge", "hostname", "architecture", "model", "device_profile"}, "TARGET_NOT_READY")
            observed.update(ssh_host_key_type="ssh-ed25519", ssh_host_key_sha256=next(iter(self.keys)))
            validate_identity(binding, observed, self.challenge)
        except (BindingError, OSError, ValueError):
            self.close()
            raise BindingError("TARGET_NOT_READY") from None

    def _stderr(self, chunk):
        self.stderr.extend(chunk)
        require(len(self.stderr) <= 262144, "SSH_DIAGNOSTIC_BOUND_EXCEEDED")
        for line in self.stderr.splitlines(keepends=True):
            if not line.endswith(b"\n"):continue
            match = re.search(rb"Server host key: ssh-ed25519 (SHA256:[A-Za-z0-9+/]{43})\r?\n$", line)
            if match:self.keys.add(match[1].decode("ascii"))

    def read_line(self, timeout):
        deadline = time.monotonic()+timeout
        while True:
            # Drain pending handshake diagnostics before admitting a stdout identity.
            events = self.selector.select(min(0.1, max(0, deadline-time.monotonic())))
            for selected, _mask in sorted(events, key=lambda item: item[0].data != "stderr"):
                chunk = os.read(selected.fd, 8192)
                if not chunk:
                    self.selector.unregister(selected.fileobj)
                    continue
                if selected.data == "stderr":self._stderr(chunk)
                else:
                    self.stdout.extend(chunk);require(len(self.stdout) <= 65536, "REMOTE_METADATA_BOUND_EXCEEDED")
            if b"\n" in self.stdout:
                raw, _separator, rest = self.stdout.partition(b"\n")
                self.stdout = bytearray(rest)
                return strict_json(bytes(raw), 65536)
            require(time.monotonic() < deadline and (self.process.poll() is None or self.selector.get_map()), "REMOTE_RESPONSE_INCONCLUSIVE")

    def intent(self, payload, *, timeout=900):
        require(not self.sent, "INTENT_ALREADY_SENT")
        require(configuration_digest(self.configuration, CONFIGURATION_REFS[self.instance]) == CONFIGURATION_DIGESTS[self.instance], "SSH_CONFIGURATION_MAPPING_CHANGED")
        raw = json.dumps(payload, separators=(",", ":")).encode()+b"\n"
        require(len(raw) <= 44755608, "INTENT_TOO_LARGE")
        self.sent = True  # Any subsequent transport failure is uncertain, never retried.
        deadline = time.monotonic()+30
        descriptor = self.process.stdin.fileno();os.set_blocking(descriptor, False)
        written = 0
        while written < len(raw):
            try:written += os.write(descriptor, raw[written:written+16384])
            except BlockingIOError:time.sleep(0.01)
            require(time.monotonic() < deadline and (written == len(raw) or self.process.poll() is None), "REMOTE_DISPATCH_INCONCLUSIVE_CHECK_ACTUAL_STATE")
        self.process.stdin.close()
        result = self.read_line(timeout)
        require(self.keys == {self.binding.inventory_row["ssh_host_key_sha256"]}, "SSH_KEY_CHANGED_CHECK_ACTUAL_STATE")
        require(result.get("result") in {"TARGET_READY", "DEPLOYED_PENDING_SMOKE", "SMOKE_PASS", "RECOVERED_PENDING_SMOKE"}, "REMOTE_PHASE_INCONCLUSIVE_CHECK_ACTUAL_STATE")
        return result

    def close(self):
        # Closing a controller does not prove a dispatched remote installer stopped.
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            if stream and not stream.closed:stream.close()
        self.selector.close()
        if self.process.poll() is None:
            self.process.terminate()
            try:self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:self.process.kill();self.process.wait(timeout=3)

    def __enter__(self):return self
    def __exit__(self, *args):self.close()


def validate_result(result: dict, phase: str, binding) -> None:
    service_fields = {"djconnect-api.service", "djconnect-client.service"}
    require(isinstance(result.get("services"), dict) and set(result["services"]) == service_fields, "REMOTE_RESULT_INVALID")
    for value in result["services"].values():
        require(isinstance(value, dict) and set(value) == {"active", "pid"}
                and type(value["active"]) is bool and type(value["pid"]) is int and value["pid"] >= 0, "REMOTE_RESULT_INVALID")
    if phase == "readiness":
        require(set(result) == {"result", "current_version", "services"}
                and result["result"] == "TARGET_READY" and isinstance(result["current_version"], str)
                and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-rc\.[0-9]+)?", result["current_version"]) is not None, "REMOTE_RESULT_INVALID")
    elif phase == "deploy":
        require(set(result) == {"result", "configuration_preserved_by_installer", "services"}
                and result["result"] == "DEPLOYED_PENDING_SMOKE" and result["configuration_preserved_by_installer"] is True, "REMOTE_RESULT_INVALID")
    elif phase == "recover":
        require(binding.request["deployment_instance"] == "wall-4inch"
                and set(result) == {"result", "configuration_preserved_by_installer", "watchdog_restored", "verified_packaged_files", "original_deployment_workflow_run", "services"}
                and result["result"] == "RECOVERED_PENDING_SMOKE" and result["configuration_preserved_by_installer"] is True
                and result["watchdog_restored"] is True and type(result["verified_packaged_files"]) is int
                and result["verified_packaged_files"] == 80 and result["original_deployment_workflow_run"] == "39669504016"
                and all(row["active"] and row["pid"] > 0 for row in result["services"].values()), "RECOVERY_RESULT_INVALID")
    elif phase == "smoke":
        fields = {"result", "installed_source", "installed_version", "installed_device_profile", "api_reachable", "client_active", "api_active", "paired", "services", "verified_packaged_files"}
        require(set(result) == fields and result["result"] == "SMOKE_PASS"
                and result["installed_source"] == binding.request["candidate_sha"]
                and result["installed_version"] == binding.version
                and result["installed_device_profile"] == binding.request["device_profile"]
                and all(result[key] is True for key in ("api_reachable", "client_active", "api_active"))
                and type(result["paired"]) is bool and type(result["verified_packaged_files"]) is int
                and 0 < result["verified_packaged_files"] <= 256, "REMOTE_RESULT_INVALID")
    else:raise BindingError("REMOTE_PHASE_INVALID")
