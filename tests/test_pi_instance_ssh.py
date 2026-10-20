from __future__ import annotations

import shlex
import subprocess
import sys

import pytest

pytest.importorskip("jsonschema", reason="Dedicated locked deployment-tool suite")
from test_pi_instance_contract import binding

from Tools import pi_instance_ssh as wire


@pytest.fixture
def protocol(monkeypatch, tmp_path):
    home = tmp_path/"home";(home/".ssh").mkdir(parents=True)
    config = home/".ssh/config";config.write_text("# synthetic fixed config\n");config.chmod(0o600)
    monkeypatch.setattr(wire.Path, "home", classmethod(lambda cls: home))
    original = subprocess.Popen
    record = {"case": "valid", "calls": [], "marker": tmp_path/"intent-count"}
    value = binding()
    monkeypatch.setattr(wire, "configuration_digest", lambda *args: wire.CONFIGURATION_DIGESTS[value.request["deployment_instance"]])
    def process(args, **kwargs):
        record["calls"].append(args)
        assert not {"GH_TOKEN", "GITHUB_TOKEN", "HA_TOKEN"} & set(kwargs["env"])
        assert args[0] == "/usr/bin/ssh" and args[-2] == value.inventory_row["endpoint_config_ref"]
        assert "StrictHostKeyChecking=yes" in args and "ControlPath=none" in args and "HostKeyAlgorithms=ssh-ed25519" in args
        remote = shlex.split(args[-1]);source = remote[3].split('if __name__ == "__main__":', 1)[0]
        challenge = remote[4]
        identity = {key: value.inventory_row[key] for key in ("hostname", "architecture", "model", "device_profile")}
        if record["case"] == "wrong-model":identity["model"] = "wrong board"
        if record["case"] == "private-extra":identity["private_endpoint"] = "synthetic-private-value"
        key = value.inventory_row["ssh_host_key_sha256"] if record["case"] != "wrong-key" else "SHA256:"+"A"*43
        source += "\nidentity = lambda c: {**"+repr(identity)+", 'challenge': c}\n"
        source += "text = lambda *args: '4.0.0-rc.3'\nservices = lambda: {'djconnect-api.service': {'active': True, 'pid': 12}, 'djconnect-client.service': {'active': True, 'pid': 13}}\n"
        source += "def installer_permission():\n    with open("+repr(str(record["marker"]))+", 'a') as marker: marker.write('intent\\n')\n    return True\n"
        source += "sys.stderr.write("+repr("debug1: Server host key: ssh-ed25519 "+key+"\r\n")+");sys.stderr.flush()\n"
        if record["case"] == "timeout":source += "time.sleep(2)\n"
        source += "main()\n"
        return original([sys.executable, "-u", "-c", source, challenge], **kwargs)
    monkeypatch.setattr(wire.subprocess, "Popen", process)
    return value, record


def test_real_pipe_protocol_admits_one_intent_and_never_replays(protocol):
    value, record = protocol
    with wire.Channel(value) as channel:
        result = channel.intent({"phase": "readiness"}, timeout=3)
        wire.validate_result(result, "readiness", value)
        with pytest.raises(wire.BindingError, match="INTENT_ALREADY_SENT"):channel.intent({"phase": "readiness"})
    assert record["marker"].read_text() == "intent\n" and len(record["calls"]) == 1


@pytest.mark.parametrize("case", ["wrong-key", "wrong-model", "private-extra", "timeout"])
def test_bad_fresh_peer_cannot_receive_intent(protocol, case):
    value, record = protocol;record["case"] = case
    with pytest.raises(wire.BindingError, match="TARGET_NOT_READY"):wire.Channel(value, timeout=0.2)
    assert not record["marker"].exists()


def test_partial_key_line_cannot_create_a_false_fingerprint():
    channel = wire.Channel.__new__(wire.Channel);channel.stderr = bytearray();channel.keys = set()
    key = "SHA256:"+"A"*43
    line = ("debug1: Server host key: ssh-ed25519 "+key+"\r\n").encode()
    channel._stderr(line[:-12]);assert channel.keys == set()
    channel._stderr(line[-12:]);assert channel.keys == {key}


@pytest.mark.parametrize("field", ["private_endpoint", "services", "current_version"])
def test_result_metadata_cannot_leak_unrecognized_or_private_data(field):
    value = binding();result = {"result": "TARGET_READY", "current_version": "4.0.0-rc.3",
        "services": {"djconnect-api.service": {"active": True, "pid": 12}, "djconnect-client.service": {"active": True, "pid": 13}}}
    result[field] = "synthetic-private-value"
    with pytest.raises(wire.BindingError):wire.validate_result(result, "readiness", value)
