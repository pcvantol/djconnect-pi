from __future__ import annotations

import base64
import hashlib
import json

import pytest

pytest.importorskip("jsonschema", reason="Dedicated locked deployment-tool suite")
from Tools import pi_wall4_recovery_observer as observer
from Tools import pi_wall4_recovery_release as release
from Tools.pi_rc6_recovery_root import private_config_digest

BOOT = "01234567-89ab-cdef-0123-456789abcdef"
CONFIG = {"device_id":"djconnect-raspberry-pi-D83ADD41F167", "paired_token":"SYNTHETIC_NEVER_PUBLIC", "unknown_future":{"keep":True}}


def fake(monkeypatch, raw=None):
    monkeypatch.setattr(observer.os,"geteuid",lambda:0)
    monkeypatch.setattr(observer.socket,"gethostname",lambda:"rbpi-djconnect")
    calls = []
    def read(path, maximum):
        calls.append((path,maximum))
        if path == "/proc/sys/kernel/random/boot_id":return (BOOT+"\n").encode()
        if path == "/etc/djconnect-pi/device-profile":return b"pi-zero-2w-arm64\n"
        assert path == "/opt/djconnect/config/client.json" and maximum == 2097152
        return raw if raw is not None else json.dumps(CONFIG).encode()
    monkeypatch.setattr(observer,"read",read)
    return calls


def test_exact_observer_is_readonly_opaque_and_matches_original_digest(monkeypatch):
    calls = fake(monkeypatch);value = observer.observe(BOOT)
    assert value == {"boot_id":BOOT,"configuration_sha256":private_config_digest(json.dumps(CONFIG).encode())}
    assert len(calls) == 4 and all(not any(secret in json.dumps(value) for secret in ("paired_token","SYNTHETIC_NEVER_PUBLIC")) for _ in [0])
    code = base64.b64decode(release.observer_bytes())
    assert hashlib.sha256(code).hexdigest() == release.OBSERVER_SHA256
    assert b"subprocess" not in code and b"O_WRONLY" not in code and b"os.O_RDONLY" in code


@pytest.mark.parametrize("raw", [b'{"device_id":"x"}', b'{"device_id":1}', b'[]', b'{"x":NaN}', b'{"device_id":"djconnect-raspberry-pi-D83ADD41F167","x":1e999}', b'{"x":1,"x":2}', b'{'])
def test_bad_or_wrong_device_config_never_emits_observation(monkeypatch, raw):
    fake(monkeypatch,raw)
    with pytest.raises((ValueError,TypeError)):observer.observe(BOOT)


@pytest.mark.parametrize("case", ["notroot","wronghost","wrongboot","invalidboot"])
def test_privileged_scope_and_fresh_boot(monkeypatch, case):
    fake(monkeypatch)
    if case == "notroot":monkeypatch.setattr(observer.os,"geteuid",lambda:1000)
    if case == "wronghost":monkeypatch.setattr(observer.socket,"gethostname",lambda:"rbpi5-djconnect")
    with pytest.raises(ValueError):observer.observe("bad" if case == "invalidboot" else "f"+BOOT[1:] if case == "wrongboot" else BOOT)


@pytest.mark.parametrize("case", ["symlink","writable","overflow"])
def test_real_descriptor_refuses_unsafe_file(tmp_path, case):
    p = tmp_path/"config";p.write_bytes(b'{}');p.chmod(0o600)
    if case == "symlink":q=tmp_path/"link";q.symlink_to(p);p=q
    elif case == "writable":p.chmod(0o666)
    else:p.write_bytes(b'x'*11)
    with pytest.raises((ValueError,OSError)):observer.read(p,10)


def test_safe_real_descriptor_read(tmp_path):
    p=tmp_path/"config";p.write_bytes(b'{}');p.chmod(0o600)
    assert observer.read(p,10)==b'{}'
