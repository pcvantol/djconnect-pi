from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("jsonschema", reason="Dedicated locked deployment-tool suite")
from Tools import pi_instance_remote_payload as remote
from Tools import pi_wall4_recovery_release as release

BOOT="01234567-89ab-cdef-0123-456789abcdef"
OBS={"boot_id":BOOT,"configuration_sha256":"d"*64}


def test_actual_observer_wrapper_and_exact_existing_sudo_route(monkeypatch,tmp_path):
    (tmp_path/"djconnect-install").mkdir();monkeypatch.setattr(remote.Path,"home",lambda:tmp_path)
    helper=remote.stage_observer({"recovery_observer":release.observer_bytes(),"run_id":"500"})
    subprocess.run(["/bin/sh","-n",str(helper)],check=True,capture_output=True)
    assert helper.stat().st_mode & 0o777==0o700
    calls=[]
    def run(args,**kwargs):
        calls.append(args)
        assert args in (["sudo","-n","-l","--",str(helper),BOOT],["sudo","-n","--",str(helper),BOOT])
        return SimpleNamespace(returncode=0,stdout=b"allowed" if "-l" in args else json.dumps(OBS).encode(),stderr=b"")
    monkeypatch.setattr(remote.subprocess,"run",run)
    assert remote.observe_recovery(helper,BOOT)==OBS
    assert len(calls)==2 and calls[0][2]=="-l"
    with pytest.raises(remote.RemoteError):remote.stage_observer({"recovery_observer":release.observer_bytes(),"run_id":"500"})


@pytest.mark.parametrize("case",["denied","rooterror","rootstderr","overflow","wrongboot","extra","badjson"])
def test_no_rule_change_or_root_fallback_if_observer_route_or_proof_invalid(monkeypatch,case):
    calls=[]
    def run(args,**kwargs):
        calls.append(args)
        if "-l" in args:return SimpleNamespace(returncode=1 if case=="denied" else 0,stdout=b"allowed",stderr=b"")
        proof=dict(OBS)
        if case=="wrongboot":proof["boot_id"]="f"+BOOT[1:]
        if case=="extra":proof["token"]="SYNTHETIC"
        return SimpleNamespace(returncode=1 if case=="rooterror" else 0,stdout=b'x'*1025 if case=="overflow" else b'{' if case=="badjson" else json.dumps(proof).encode(),stderr=b'error' if case=="rootstderr" else b'')
    monkeypatch.setattr(remote.subprocess,"run",run)
    with pytest.raises(ValueError):remote.observe_recovery(Path('/SYNTHETIC/scripts/install.sh'),BOOT)
    assert len(calls)==(1 if case=="denied" else 2)
    assert all(args[:2]==["sudo","-n"] for args in calls)


@pytest.mark.parametrize("case",["good","changedconfig","changedboot","watchdogdisabled","heldwatchdog","unpaired"])
def test_separate_readonly_smoke_joins_current_observation_and_restored_watchdog(monkeypatch,case):
    boot=SimpleNamespace(read_text=lambda:BOOT)
    monkeypatch.setattr(remote,"Path",lambda _:boot)
    monkeypatch.setattr(remote,"stage_observer",lambda _:"fixed-observer")
    readings=[dict(OBS),dict(OBS)]
    if case=="changedconfig":readings[1]["configuration_sha256"]="e"*64
    if case=="changedboot":readings[0]["boot_id"]="f"+BOOT[1:]
    monkeypatch.setattr(remote,"observe_recovery",lambda *_:readings.pop(0))
    monkeypatch.setattr(remote,"smoke",lambda _: {"paired":case!="unpaired","verified_packaged_files":80,"result":"SMOKE_PASS"})
    monkeypatch.setattr(remote,"recover",lambda _:pytest.fail("readonly smoke cannot invoke recovery"))
    def run(args,**kwargs):
        assert args[:2]==["systemctl","show"]
        out="ActiveState=active\nUnitFileState="+("disabled" if case=="watchdogdisabled" else "enabled")+"\n" if args[2].endswith(".timer") else "ExecCondition="+("held" if case=="heldwatchdog" else "")+"\n"
        return SimpleNamespace(returncode=0,stdout=out)
    monkeypatch.setattr(remote.subprocess,"run",run)
    payload={"phase":"recovery-smoke","recovery_boot_id":BOOT,"recovery_observation":dict(OBS)}
    if case=="good":assert remote.closed_recovery(payload)["recovery_observation"]==OBS
    else:
        with pytest.raises(remote.RemoteError):remote.closed_recovery(payload)
