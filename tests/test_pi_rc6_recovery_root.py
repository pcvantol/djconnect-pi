from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import tarfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from Tools import pi_rc6_recovery_root as recovery

BOOT = "01234567-89ab-cdef-0123-456789abcdef"
RUN = "40000000000"


class FakeSystem:
    def __init__(self, tmp_path, fail=None):
        self.root = tmp_path
        self.calls = []
        self.fail = fail
        self.claimed = False
        self.held = False
        self.installed_calls = 0
        self.records = []
        self.boots = []
        self.config = b'{"token":"synthetic-only","profile":"original","unknown":{"value":true}}'
        self.units = {
            recovery.TIMER: self.unit_value("active", "enabled", "0"),
            recovery.WATCHDOG: self.unit_value("inactive", "static", "0"),
            recovery.API: self.unit_value("active", "enabled", "100"),
            recovery.CLIENT: self.unit_value("inactive", "disabled", "0"),
        }

    @staticmethod
    def unit_value(active, enabled, pid):
        return {"LoadState": "loaded", "ActiveState": active, "UnitFileState": enabled, "MainPID": pid}

    def check(self, name):
        self.calls.append(name)
        if self.fail == name:
            raise recovery.RecoveryError("SYNTHETIC_FAILURE")

    def boot(self):
        self.calls.append("boot")
        return self.boots.pop(0) if self.boots else BOOT

    def identity(self): self.check("identity")
    def no_competing_installer(self): self.check("no_competing_installer")
    def markers(self): self.check("markers")
    def maintenance_available(self): self.check("maintenance_available")
    def api(self): self.check("api")
    def configuration(self, holding=False): self.check("configuration")
    def unit(self, name): return self.units[name]
    def read(self, path, maximum):
        assert path == self.root/"config/client.json" and maximum == 2097152
        self.check("read_config")
        return self.config

    def installed(self):
        self.installed_calls += 1
        self.check("installed_before" if self.installed_calls == 1 else "installed_after")

    def artifact(self):
        self.check("artifact")
        return b"synthetic artifact", b"synthetic original installer"

    def claim(self, run):
        assert run == RUN
        self.check("claim")
        if self.claimed: raise FileExistsError("synthetic burned claim")
        self.claimed = True

    def hold(self):
        assert self.claimed
        self.held = True
        self.check("hold")

    def install(self, prepared):
        assert self.held and prepared.artifact == b"synthetic artifact"
        assert prepared.installer == b"synthetic original installer"
        self.check("install")
        self.units[recovery.CLIENT] = self.unit_value("active", "enabled", "101")
        self.units[recovery.API] = self.unit_value("active", "enabled", "102")
        if self.fail == "changed_config": self.config = b'{"token":"different-synthetic"}'

    def healthy(self, prepared):
        assert self.held and prepared.api_pid == 100
        self.check("healthy")

    def restore(self):
        self.check("restore")
        self.held = False

    def record(self, result): self.records.append(dict(result))


def test_confirmed_recovery_orders_hold_original_install_and_verified_restore(tmp_path):
    system = FakeSystem(tmp_path)
    result = recovery.execute(system, RUN, BOOT)
    assert result["result"] == "RECOVERED_PENDING_SMOKE"
    assert result["original_deployment_workflow_run"] == recovery.ORIGINAL_RUN
    assert result["watchdog_state"] == "RESTORED" and result["watchdog_restored"] is True
    assert result["configuration_preserved"] is True and result["verified_packaged_files"] == 80
    ordered = ["identity", "installed_before", "markers", "maintenance_available", "artifact", "claim", "hold", "install", "healthy", "installed_after", "restore"]
    positions = [system.calls.index(value) for value in ordered]
    assert positions == sorted(positions)
    assert system.calls.count("install") == system.calls.count("restore") == 1
    assert not system.held and system.claimed
    assert "synthetic" not in json.dumps(result)
    assert "SMOKE_PASS" not in json.dumps(result)


@pytest.mark.parametrize("phase", ["identity", "no_competing_installer", "installed_before", "markers", "maintenance_available", "configuration", "api", "artifact", "read_config"])
def test_preflight_failures_never_claim_hold_or_install(tmp_path, phase):
    system = FakeSystem(tmp_path, phase)
    with pytest.raises(recovery.RecoveryError): recovery.execute(system, RUN, BOOT)
    assert not system.claimed and not system.held and not system.records
    assert "claim" not in system.calls and "install" not in system.calls


@pytest.mark.parametrize("phase", ["hold", "install", "healthy", "installed_after", "changed_config", "restore"])
def test_started_failure_keeps_claim_no_retry_and_no_automatic_watchdog_restore(tmp_path, phase):
    system = FakeSystem(tmp_path, phase)
    with pytest.raises(recovery.RecoveryError, match="RECOVERY_INCOMPLETE_REQUIRES_STATE_REVIEW"):
        recovery.execute(system, RUN, BOOT)
    assert system.claimed and system.held
    assert len(system.records) == 1 and system.records[0]["result"] == "RECOVERY_INCOMPLETE"
    assert system.records[0]["watchdog_state"] == "REQUIRES_ACTUAL_READBACK"
    assert "watchdog_restored" not in system.records[0]
    assert system.calls.count("install") <= 1
    assert system.calls.count("restore") == (1 if phase == "restore" else 0)
    # Even if the original admissible state reappears, the burned claim cannot rearm.
    second = FakeSystem(tmp_path)
    second.claimed = system.claimed
    with pytest.raises(FileExistsError): recovery.execute(second, RUN, BOOT)
    assert "hold" not in second.calls and "install" not in second.calls
    assert system.calls.count("install") <= 1


@pytest.mark.parametrize("run", ["", "0", "-1", "01", "123\n", "other", recovery.ORIGINAL_RUN, None])
def test_invalid_or_original_run_has_no_reads_or_effects(tmp_path, run):
    system = FakeSystem(tmp_path)
    with pytest.raises(recovery.RecoveryError): recovery.execute(system, run, BOOT)
    assert system.calls == []


@pytest.mark.parametrize("boot", ["", "unbound", BOOT.upper(), BOOT+"\n", None])
def test_invalid_boot_has_no_reads_or_effects(tmp_path, boot):
    system = FakeSystem(tmp_path)
    with pytest.raises(recovery.RecoveryError): recovery.execute(system, RUN, boot)
    assert system.calls == []


@pytest.mark.parametrize("boots,claimed", [(["changed"], False), ([BOOT, "changed"], False), ([BOOT, BOOT, "changed"], True)])
def test_boot_epoch_change_never_reaches_hold(tmp_path, boots, claimed):
    system = FakeSystem(tmp_path);system.boots = boots
    with pytest.raises(recovery.RecoveryError): recovery.execute(system, RUN, BOOT)
    assert system.claimed is claimed and not system.held and "install" not in system.calls


@pytest.mark.parametrize("unit,field,value", [
    (recovery.TIMER,"ActiveState","inactive"),(recovery.TIMER,"UnitFileState","disabled"),
    (recovery.WATCHDOG,"LoadState","masked"),(recovery.WATCHDOG,"ActiveState","active"),
    (recovery.API,"ActiveState","inactive"),(recovery.API,"MainPID","0"),
    (recovery.CLIENT,"ActiveState","active"),(recovery.CLIENT,"UnitFileState","enabled"),
    (recovery.CLIENT,"MainPID","123"),
])
def test_changed_service_state_is_not_repaired_or_admitted(tmp_path, unit, field, value):
    system = FakeSystem(tmp_path);system.units[unit][field] = value
    with pytest.raises(recovery.RecoveryError): recovery.execute(system, RUN, BOOT)
    assert not system.claimed and "hold" not in system.calls


@pytest.mark.parametrize("raw", [b'{"a":1,"a":2}', b'{"a":NaN}', b'[]', b'{', b'"private"', b'{"big":"'+b'x'*2097152+b'"}'])
def test_private_configuration_invalid_without_echo(raw):
    with pytest.raises(recovery.RecoveryError) as error: recovery.private_config_digest(raw)
    assert str(error.value).startswith("RECOVERY_JSON_")
    assert "private" not in str(error.value) and "xxxx" not in str(error.value)


def test_private_config_digest_keeps_all_fields_and_ignores_formatting_only():
    a=b'{"token":"synthetic","profile_id":"owner","unknown":[true,1],"release_profile":"pi-zero-2w-arm64"}'
    b=json.dumps(json.loads(a),indent=2).encode()
    assert recovery.private_config_digest(a) == recovery.private_config_digest(b)
    for key in json.loads(a):
        changed=json.loads(a);changed[key]="changed"
        assert recovery.private_config_digest(a) != recovery.private_config_digest(json.dumps(changed).encode())


def test_regular_descriptor_rejects_links_writable_and_oversize(tmp_path):
    system=recovery.System();p=tmp_path/"bytes";p.write_bytes(b"known");p.chmod(0o600)
    assert system.read(p,5)==b"known"
    link=tmp_path/"link";link.symlink_to(p)
    with pytest.raises(OSError): system.read(link,5)
    with pytest.raises(recovery.RecoveryError): system.read(p,4)
    p.chmod(0o666)
    with pytest.raises(recovery.RecoveryError): system.read(p,5)


def test_root_guard_rejects_unprivileged_or_extra_arguments_before_system(monkeypatch):
    monkeypatch.setattr(recovery.os,"geteuid",lambda:501)
    monkeypatch.setattr(recovery.sys,"argv",["helper",RUN,BOOT])
    effect=Mock(side_effect=AssertionError("No system construction"));monkeypatch.setattr(recovery,"System",effect)
    with pytest.raises(recovery.RecoveryError): recovery.main()
    effect.assert_not_called()
    monkeypatch.setattr(recovery.os,"geteuid",lambda:0)
    monkeypatch.setattr(recovery.sys,"argv",["helper",RUN,BOOT,"--override"])
    with pytest.raises(recovery.RecoveryError): recovery.main()
    effect.assert_not_called()


def test_guard_ownership_change_cannot_be_removed(tmp_path,monkeypatch):
    system=recovery.System();system.guard_dir=tmp_path/"guard";system.guard_dir.mkdir()
    guard=system.guard_dir/system.guard_name;guard.write_bytes(system.guard_content);guard.chmod(0o600)
    system._guard_inode=guard.lstat().st_ino+1
    effect=Mock();monkeypatch.setattr(system,"command",effect)
    with pytest.raises(recovery.RecoveryError): system.restore()
    effect.assert_not_called();assert guard.read_bytes()==system.guard_content


def test_api_client_refuses_redirect_and_ambient_proxy(monkeypatch):
    system=recovery.System();opener=Mock()
    opener.open.side_effect=OSError("synthetic endpoint failure")
    factory=Mock(return_value=opener);monkeypatch.setattr(recovery,"build_opener",factory)
    with pytest.raises(OSError):system.api()
    handlers=factory.call_args.args
    assert handlers[0].proxies == {} and isinstance(handlers[1],recovery.NoRedirect)
    assert handlers[1].redirect_request(None,None,302,None,None,"http://other.invalid") is None
    assert opener.open.call_args.args == ("http://127.0.0.1:18080/api/device/info",)


def test_installer_uses_private_sealed_original_bytes_closed_env_and_bounded_wait(tmp_path,monkeypatch):
    system=recovery.System();system.ledger=tmp_path/"ledger";system.ledger.mkdir()
    real_temp=recovery.tempfile.TemporaryDirectory
    monkeypatch.setattr(recovery.tempfile,"TemporaryDirectory",lambda **kwargs:real_temp(prefix="sealed-",dir=tmp_path))
    prepared=recovery.Prepared(b"verified-tar",b"verified-original-installer","digest",BOOT,100)
    def run(args,**kwargs):
        assert Path(args[1]).read_bytes()==prepared.installer
        assert Path(args[3]).read_bytes()==prepared.artifact
        assert os.stat(args[1]).st_mode & 0o777 == 0o700
        assert os.stat(args[3]).st_mode & 0o777 == 0o600
        assert args[2:] == ["--approved-artifact",args[3],"--artifact-sha256",recovery.ARTIFACT_SHA256,"--source-sha",recovery.SOURCE]
        assert kwargs["timeout"]==1200 and kwargs["check"] is False
        assert set(kwargs["env"])=={"PATH","HOME","LANG","SUDO_USER","DJCONNECT_RELEASE_PROFILE"}
        assert kwargs["env"]["SUDO_USER"]=="pi" and kwargs["env"]["DJCONNECT_RELEASE_PROFILE"]==recovery.PROFILE
        return SimpleNamespace(returncode=0)
    process=Mock(side_effect=run);monkeypatch.setattr(recovery.subprocess,"run",process)
    system.install(prepared);assert process.call_count==1
    assert list(tmp_path.iterdir())==[system.ledger]
    assert (system.ledger/"installer-private.log").stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize("reason",[1,subprocess.TimeoutExpired("synthetic",1200)])
def test_installer_failure_or_timeout_never_retries(tmp_path,monkeypatch,reason):
    system=recovery.System();system.ledger=tmp_path/"ledger";system.ledger.mkdir()
    real_temp=recovery.tempfile.TemporaryDirectory
    monkeypatch.setattr(recovery.tempfile,"TemporaryDirectory",lambda **kwargs:real_temp(prefix="sealed-",dir=tmp_path))
    process=Mock(side_effect=reason) if isinstance(reason,Exception) else Mock(return_value=SimpleNamespace(returncode=reason))
    monkeypatch.setattr(recovery.subprocess,"run",process)
    with pytest.raises((recovery.RecoveryError,subprocess.TimeoutExpired)):
        system.install(recovery.Prepared(b"tar",b"installer","digest",BOOT,100))
    assert process.call_count==1


def package_system(tmp_path,monkeypatch):
    real_path=Path
    def path(value):
        value=str(value)
        for original in ("/etc/systemd/system","/run/systemd/system"):
            if value==original or value.startswith(original+"/"):
                return real_path(str(tmp_path)+value)
        return real_path(value)
    monkeypatch.setattr(recovery,"Path",path)
    system=recovery.System();system.root=tmp_path/"opt";system.stage=tmp_path/"original-stage"
    system.stage.mkdir();(system.stage/"scripts").mkdir()
    (tmp_path/"etc/systemd/system").mkdir(parents=True)
    (tmp_path/"run/systemd/system").mkdir(parents=True)
    wheel_buffer=io.BytesIO()
    import zipfile
    with zipfile.ZipFile(wheel_buffer,"w") as z:z.writestr("djconnect_pi/__init__.py",b"original fixture source")
    wheel=wheel_buffer.getvalue();installer=b"#!/bin/bash\n# synthetic never executed\nexit 0\n"
    prefix="djconnect-pi-"+recovery.PROFILE+"-"+recovery.VERSION
    artifact=system.stage/"approved-artifact.tar.gz"
    with tarfile.open(artifact,"w:gz") as a:
        for name,body in [("scripts/install.sh",installer),("systemd/"+recovery.WATCHDOG,b"watchdog-unit"),("systemd/"+recovery.TIMER,b"watchdog-timer")]:
            info=tarfile.TarInfo(prefix+"/"+name);info.size=len(body);a.addfile(info,io.BytesIO(body))
    (system.stage/"scripts/install.sh").write_bytes(installer)
    (tmp_path/"etc/systemd/system"/recovery.WATCHDOG).write_bytes(b"watchdog-unit")
    (tmp_path/"etc/systemd/system"/recovery.TIMER).write_bytes(b"watchdog-timer")
    monkeypatch.setattr(recovery,"ARTIFACT_SHA256",hashlib.sha256(artifact.read_bytes()).hexdigest())
    monkeypatch.setattr(recovery,"INSTALLER_SHA256",hashlib.sha256(installer).hexdigest())
    monkeypatch.setattr(recovery,"WHEEL_SHA256",hashlib.sha256(wheel).hexdigest())
    monkeypatch.setattr(recovery,"PACKAGED_FILES",1)
    release=system.root/"releases"/(recovery.VERSION+"-"+recovery.PROFILE)
    (release/"wheels").mkdir(parents=True);(release/"wheels"/recovery.WHEEL).write_bytes(wheel)
    site=release/".venv/lib/python3.13/site-packages/djconnect_pi";site.mkdir(parents=True)
    (site/"__init__.py").write_bytes(b"original fixture source")
    for n,v in [("VERSION",recovery.VERSION),("SOURCE_COMMIT",recovery.SOURCE),("RELEASE_PROFILE",recovery.PROFILE)]:
        (release/n).write_text(v+"\n")
    (system.root/"current").symlink_to(release,target_is_directory=True)
    state=system.root/"install-state"/(recovery.VERSION+"-"+recovery.PROFILE);state.mkdir(parents=True)
    (state/"approved-artifact.sha256").write_text(recovery.ARTIFACT_SHA256+"\n")
    for n in ("release_unpacked.done","venv_ready.done"):(state/n).touch()
    # The production reader intentionally rejects group-writable input; fixture
    # permissions must not depend on the test runner's inherited umask.
    for fixture in tmp_path.rglob("*"):
        if fixture.is_file() and not fixture.is_symlink():
            fixture.chmod(0o600)
    return system,release,state


def test_real_offline_descriptor_archive_marker_and_installed_byte_checks(tmp_path,monkeypatch):
    system,_,_=package_system(tmp_path,monkeypatch)
    raw,installer=system.artifact()
    assert hashlib.sha256(raw).hexdigest()==recovery.ARTIFACT_SHA256
    assert hashlib.sha256(installer).hexdigest()==recovery.INSTALLER_SHA256
    system.installed();system.markers()


@pytest.mark.parametrize("case",["artifact","staged-installer","watchdog-unit","watchdog-dropin","runtime-dropin","source","version","profile","wheel","installed-byte","count","marker","venv-marker","release-marker","current-target"])
def test_actual_filesystem_changes_reject_before_any_effect(tmp_path,monkeypatch,case):
    system,release,state=package_system(tmp_path,monkeypatch)
    if case=="artifact":(system.stage/"approved-artifact.tar.gz").write_bytes(b"other")
    if case=="staged-installer":(system.stage/"scripts/install.sh").write_text("edited")
    if case=="watchdog-unit":(tmp_path/"etc/systemd/system"/recovery.WATCHDOG).write_text("custom")
    if case in {"watchdog-dropin","runtime-dropin"}:
        base=tmp_path/("etc" if case=="watchdog-dropin" else "run")/"systemd/system"/(recovery.WATCHDOG+".d")
        base.mkdir();(base/"other.conf").write_text("preserve")
    if case in {"source","version","profile"}:
        name={"source":"SOURCE_COMMIT","version":"VERSION","profile":"RELEASE_PROFILE"}[case]
        (release/name).write_text("changed\n")
    if case=="wheel":(release/"wheels"/recovery.WHEEL).write_bytes(b"other")
    if case=="installed-byte":(release/".venv/lib/python3.13/site-packages/djconnect_pi/__init__.py").write_text("changed")
    if case=="count":monkeypatch.setattr(recovery,"PACKAGED_FILES",80)
    if case=="marker":(state/"approved-artifact.sha256").write_text("changed\n")
    if case=="venv-marker":(state/"venv_ready.done").unlink()
    if case=="release-marker":(state/"release_unpacked.done").write_text("unexpected")
    if case=="current-target":
        (system.root/"current").unlink();(system.root/"current").symlink_to(tmp_path)
    effects=Mock(side_effect=AssertionError("No root/systemd/network/installer effects"))
    monkeypatch.setattr(system,"command",effects)
    with pytest.raises((recovery.RecoveryError,OSError)):
        system.artifact();system.installed();system.markers()
    effects.assert_not_called()


def test_fifo_is_rejected_without_open_wait(tmp_path):
    fifo=tmp_path/"fifo";os.mkfifo(fifo,mode=0o600)
    with pytest.raises(recovery.RecoveryError):recovery.System().read(fifo,16)


@pytest.mark.parametrize("args,accepted",[
    ([b"/usr/bin/python3",b"unrelated"],True),
    ([b"sudo",b"/home/pi/djconnect-install/djconnect-pi-rc6-recovery-40000000000/scripts/install.sh"],True),
    ([b"sudo",b"/home/pi/djconnect-install/djconnect-pi-rc6-39669504016-pi-zero-2w-arm64/scripts/install.sh"],False),
    ([b"bash",b"/home/pi/djconnect-install/djconnect-pi-other/scripts/install.sh"],False),
    ([b"/bin/bash",b"/run/djconnect-rc6-recovery-other/install.sh"],False),
    ([b"/opt/djconnect/releases/4.0.0-rc.6-pi-zero-2w-arm64/.venv/bin/python",b"-m",b"pip"],False),
    ([b"/usr/bin/chown",b"-R",b"djconnect:djconnect",b"/opt/djconnect"],False),
])
def test_actual_process_inspection_rejects_other_installers_but_not_current_root_entry(tmp_path,monkeypatch,args,accepted):
    proc=tmp_path/"proc/123";proc.mkdir(parents=True);(proc/"cmdline").write_bytes(b"\0".join(args)+b"\0")
    real=Path
    monkeypatch.setattr(recovery,"Path",lambda value:tmp_path/"proc" if str(value)=="/proc" else real(value))
    system=recovery.System();system.recovery_run=RUN
    monkeypatch.setattr(system,"command",lambda _:"")
    if accepted:system.no_competing_installer()
    else:
        with pytest.raises(recovery.RecoveryError,match="RECOVERY_INSTALLER_STILL_RUNNING"):system.no_competing_installer()


@pytest.mark.parametrize("job",["1 reboot.target start running", "2 shutdown.target start waiting", "3 poweroff.service start running"])
def test_shutdown_jobs_reject_before_claim(tmp_path,monkeypatch,job):
    real=Path;(tmp_path/"proc").mkdir()
    monkeypatch.setattr(recovery,"Path",lambda value:tmp_path/"proc" if str(value)=="/proc" else real(value))
    system=recovery.System();system.recovery_run=RUN
    monkeypatch.setattr(system,"command",lambda _:job)
    with pytest.raises(recovery.RecoveryError,match="RECOVERY_SHUTDOWN_PENDING"):system.no_competing_installer()


def guard_system(tmp_path,monkeypatch):
    system=recovery.System();system.guard_dir=tmp_path/"guard"
    calls=[]
    states={recovery.TIMER:FakeSystem.unit_value("active","enabled","0"),recovery.WATCHDOG:FakeSystem.unit_value("inactive","static","0")}
    def command(args):
        calls.append(list(args))
        if args[1]=="stop":states[recovery.TIMER]["ActiveState"]="inactive"
        if args[1]=="restart":states[recovery.TIMER]["ActiveState"]="active"
        if args[1]=="show":
            name=args[2]
            if "--property=ExecCondition" in args:
                return "{ path=/usr/bin/false ; argv[]=/usr/bin/false ; ignore_errors=no ; start_time=[n/a] ; status=0 }\n"
            drop=str(system.guard_dir/system.guard_name) if name==recovery.WATCHDOG and system.guard_dir.exists() else ""
            return "\n".join(["FragmentPath=/etc/systemd/system/"+name,"DropInPaths="+drop,"SuccessAction=none","FailureAction=none","JobTimeoutAction=none","OnSuccess=","OnFailure="])+"\n"
        return ""
    monkeypatch.setattr(system,"command",command);monkeypatch.setattr(system,"unit",lambda name:states[name])
    return system,calls,states


def test_real_runtime_guard_survives_installer_timer_enable_and_restores_only_owned_file(tmp_path,monkeypatch):
    system,calls,states=guard_system(tmp_path,monkeypatch)
    system.hold();guard=system.guard_dir/system.guard_name
    assert guard.read_bytes()==b"[Service]\nExecCondition=/usr/bin/false\n"
    assert guard.stat().st_mode & 0o777 == 0o600
    assert calls.index(["/usr/bin/systemctl","stop",recovery.TIMER,recovery.WATCHDOG]) < calls.index(["/usr/bin/systemctl","daemon-reload"])
    states[recovery.TIMER]["ActiveState"]="active"  # Original published installer enables its timer again.
    assert guard.exists()  # Reloads/timer starts keep the independently owned service condition.
    system.restore()
    assert not system.guard_dir.exists() and states[recovery.TIMER]["ActiveState"]=="active"
    assert not any("mask" in arg or "unmask" in arg for args in calls for arg in args)
    assert calls[-1]==["/usr/bin/systemctl","restart",recovery.TIMER]


@pytest.mark.parametrize("case",["foreign-file","changed-content","replaced-inode","directory-symlink"])
def test_runtime_guard_does_not_remove_changed_or_foreign_maintenance(tmp_path,monkeypatch,case):
    system,calls,_=guard_system(tmp_path,monkeypatch);system.hold()
    guard=system.guard_dir/system.guard_name
    if case=="foreign-file":(system.guard_dir/"other.conf").write_text("preserve")
    if case=="changed-content":guard.write_text("changed")
    if case=="replaced-inode":system._guard_inode+=1
    if case=="directory-symlink":
        old=tmp_path/"kept";system.guard_dir.rename(old);system.guard_dir.symlink_to(old,target_is_directory=True)
    before=len(calls)
    with pytest.raises(recovery.RecoveryError):system.restore()
    assert len(calls)==before and guard.exists()
    if case=="foreign-file":assert (system.guard_dir/"other.conf").read_text()=="preserve"


@pytest.mark.parametrize("property_name,value",[("SuccessAction","reboot"),("FailureAction","reboot"),("JobTimeoutAction","reboot"),("OnSuccess","other.service"),("OnFailure","other.service"),("DropInPaths","/run/other.conf"),("FragmentPath","/other/unit")])
def test_foreign_unit_policy_prevents_any_stop_or_hold(tmp_path,monkeypatch,property_name,value):
    system,calls,_=guard_system(tmp_path,monkeypatch);original=system.command
    def command(args):
        raw=original(args)
        return "\n".join(property_name+"="+value if line.startswith(property_name+"=") else line for line in raw.splitlines())+"\n"
    monkeypatch.setattr(system,"command",command)
    with pytest.raises(recovery.RecoveryError):system.hold()
    assert not system.guard_dir.exists()
    assert not any(args[1] in {"stop","daemon-reload","restart"} for args in calls)


@pytest.mark.parametrize("condition",["", "{ path=/usr/bin/true ; argv[]=/usr/bin/true ; ignore_errors=no ; status=0 }\n", "{ path=/usr/bin/false ; argv[]=/usr/bin/false ; ignore_errors=yes ; status=0 }\n"])
def test_guard_must_be_loaded_as_nonignored_false_condition(tmp_path,monkeypatch,condition):
    system,calls,_=guard_system(tmp_path,monkeypatch);original=system.command
    def command(args):return condition if "--property=ExecCondition" in args else original(args)
    monkeypatch.setattr(system,"command",command)
    with pytest.raises(recovery.RecoveryError,match="RECOVERY_GUARD_NOT_LOADED"):system.hold()
    assert (system.guard_dir/system.guard_name).exists()
    assert not any(args[1]=="restart" for args in calls)


def test_health_reads_settle_after_transient_connection_failure_and_stable_new_pids(tmp_path,monkeypatch):
    system=recovery.System();clock=SimpleNamespace(now=0)
    monkeypatch.setattr(recovery.time,"monotonic",lambda:clock.now)
    monkeypatch.setattr(recovery.time,"sleep",lambda delay:setattr(clock,"now",clock.now+delay))
    monkeypatch.setattr(system,"unit",lambda name:FakeSystem.unit_value("active","enabled","101" if name==recovery.API else "102"))
    api=Mock(side_effect=[OSError("transient"),None,None,None,None]);monkeypatch.setattr(system,"api",api)
    system.healthy(recovery.Prepared(b"",b"","",BOOT,100))
    assert clock.now==8 and api.call_count==5


def test_health_wait_never_accepts_old_api_pid_or_restarts_services(tmp_path,monkeypatch):
    system=recovery.System();clock=SimpleNamespace(now=0)
    monkeypatch.setattr(recovery.time,"monotonic",lambda:clock.now)
    monkeypatch.setattr(recovery.time,"sleep",lambda delay:setattr(clock,"now",clock.now+delay))
    monkeypatch.setattr(system,"unit",lambda name:FakeSystem.unit_value("active","enabled","100" if name==recovery.API else "102"))
    command=Mock(side_effect=AssertionError("No restart"));api=Mock();monkeypatch.setattr(system,"command",command);monkeypatch.setattr(system,"api",api)
    with pytest.raises(recovery.RecoveryError,match="RECOVERY_SERVICES_NOT_STABLE"):
        system.healthy(recovery.Prepared(b"",b"","",BOOT,100))
    assert clock.now==90;command.assert_not_called();api.assert_not_called()


def test_root_claim_is_exclusive_across_distinct_new_runs_and_never_rearmed(tmp_path,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    system=recovery.System();system.ledger=tmp_path/"private"/"claim";system.ledger.parent.mkdir(mode=0o700)
    real=Path.stat
    def metadata(path,*args,**kwargs):
        result=real(path,*args,**kwargs)
        if path==system.ledger.parent:return SimpleNamespace(st_uid=0,st_mode=0o40700)
        return result
    monkeypatch.setattr(Path,"stat",metadata)
    def claim(value):
        try:system.claim(value);return True
        except FileExistsError:return False
    with ThreadPoolExecutor(max_workers=12) as pool:results=list(pool.map(claim,[str(50000000000+i) for i in range(12)]))
    assert sum(results)==1
    original=(system.ledger/"claim.json").read_bytes()
    with pytest.raises(FileExistsError):system.claim("60000000000")
    assert (system.ledger/"claim.json").read_bytes()==original
    assert (system.ledger/"claim.json").stat().st_mode & 0o777 == 0o600


def test_late_api_loss_after_restore_is_uncertain_not_false_watchdog_hold_claim(tmp_path):
    system=FakeSystem(tmp_path);normal=system.api
    def api():
        if "restore" in system.calls:raise OSError("late local read failure")
        return normal()
    system.api=api
    with pytest.raises(recovery.RecoveryError):recovery.execute(system,RUN,BOOT)
    assert system.claimed and not system.held
    assert system.calls.count("restore")==1 and system.calls.count("install")==1
    assert system.records[-1]["watchdog_state"]=="REQUIRES_ACTUAL_READBACK"
    assert "watchdog_restored" not in system.records[-1]


def test_boot_change_after_install_keeps_guard_and_claim(tmp_path):
    system=FakeSystem(tmp_path);system.boots=[BOOT,BOOT,BOOT,"changed"]
    with pytest.raises(recovery.RecoveryError):recovery.execute(system,RUN,BOOT)
    assert system.held and system.claimed and "restore" not in system.calls


@pytest.mark.parametrize("parent_exists", [False, True])
@pytest.mark.parametrize("fail_at", [None, 1, 2, 3, 4])
def test_real_claim_syncs_all_data_and_directory_entries_before_effects(tmp_path, monkeypatch, parent_exists, fail_at):
    system = FakeSystem(tmp_path)
    system.ledger = tmp_path / "private" / "ledger"
    parent = system.ledger.parent
    if parent_exists:
        parent.mkdir(mode=0o700)
    real_stat = Path.stat
    def metadata(path, *args, **kwargs):
        actual = real_stat(path, *args, **kwargs)
        if path == parent:
            return SimpleNamespace(st_uid=0, st_mode=actual.st_mode)
        return actual
    monkeypatch.setattr(Path, "stat", metadata)
    original_open = os.open
    opened = {}
    syncs = []
    def open_file(path, flags, *args, **kwargs):
        fd = original_open(path, flags, *args, **kwargs)
        opened[fd] = Path(path)
        return fd
    monkeypatch.setattr(recovery.os, "open", open_file)
    def sync(fd):
        path = opened[fd]
        syncs.append(path)
        assert "hold" not in system.calls and "install" not in system.calls
        if path.name == "claim.json":
            assert json.loads(path.read_bytes()) == {"original_run": recovery.ORIGINAL_RUN, "recovery_run": RUN, "source": recovery.SOURCE}
            assert os.fstat(fd).st_mode & 0o777 == 0o600
        if len(syncs) == fail_at:
            raise OSError("synthetic fsync failure")
    monkeypatch.setattr(recovery.os, "fsync", sync)
    def durable_claim(run):
        recovery.System.claim(system, run)
        system.claimed = True
    system.claim = durable_claim
    expected = [parent.parent, system.ledger / "claim.json", system.ledger, parent]
    if fail_at:
        with pytest.raises(OSError, match="fsync failure"):
            recovery.execute(system, RUN, BOOT)
        assert syncs == expected[:fail_at]
        assert not system.claimed and not system.held and "hold" not in system.calls and "install" not in system.calls
        # A partly written claim is retained, never removed or automatically rearmed.
        assert system.ledger.exists() is (fail_at > 1)
    else:
        assert recovery.execute(system, RUN, BOOT)["result"] == "RECOVERED_PENDING_SMOKE"
        assert syncs == expected and system.claimed and "install" in system.calls
        assert (system.ledger / "claim.json").exists()
