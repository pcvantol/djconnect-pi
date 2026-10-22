from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path

import pytest

from Tools import pi_rc6_recovery_root as recovery

RAW_PATH=Path(__file__).parent/"fixtures/pi_wall4_recovery_v1/systemctl_unit_shapes.json"
RAW=json.loads(RAW_PATH.read_text())["raw_unit_properties"]


@pytest.mark.parametrize("unit",[recovery.TIMER,recovery.API,recovery.CLIENT,recovery.WATCHDOG])
def test_exact_actual_unit_responses_use_type_specific_fields(unit):
    system=recovery.System();calls=[]
    def command(args):
        calls.append(args)
        expected="LoadState,ActiveState,UnitFileState"+("" if unit==recovery.TIMER else ",MainPID")
        assert args==["/usr/bin/systemctl","show",unit,"--property="+expected,"--no-pager"]
        return RAW[unit]
    system.command=command;result=system.unit(unit)
    assert ("MainPID" in result) is (unit!=recovery.TIMER)
    assert len(calls)==1


@pytest.mark.parametrize("unit",[recovery.API,recovery.CLIENT,recovery.WATCHDOG])
def test_service_mainpid_remains_mandatory(unit):
    s=recovery.System();s.command=lambda _:"\n".join(x for x in RAW[unit].splitlines() if not x.startswith("MainPID="))+"\n"
    with pytest.raises(recovery.RecoveryError,match="RECOVERY_UNIT_INVALID"):s.unit(unit)


@pytest.mark.parametrize("unit",[recovery.API,recovery.CLIENT,recovery.WATCHDOG])
@pytest.mark.parametrize("pid",["","-1","True","1.0","pid","1\nextra"])
def test_service_pid_shape_cannot_be_weakened(unit,pid):
    s=recovery.System();s.command=lambda _:"MainPID="+pid+"\n"+"\n".join(x for x in RAW[unit].splitlines() if not x.startswith("MainPID="))+"\n"
    with pytest.raises(recovery.RecoveryError):s.unit(unit)


@pytest.mark.parametrize("unit",list(RAW))
@pytest.mark.parametrize("field",["LoadState","ActiveState","UnitFileState"])
def test_common_required_fields_remain_exact(unit,field):
    s=recovery.System();s.command=lambda _:"\n".join(x for x in RAW[unit].splitlines() if not x.startswith(field+"="))+"\n"
    with pytest.raises(recovery.RecoveryError,match="RECOVERY_UNIT_INVALID"):s.unit(unit)


@pytest.mark.parametrize("unit",list(RAW))
def test_foreign_fields_fail_closed(unit):
    s=recovery.System();s.command=lambda _:RAW[unit]+"OtherField=unexpected\n"
    with pytest.raises(recovery.RecoveryError,match="RECOVERY_UNIT_INVALID"):s.unit(unit)


def test_timer_never_invents_or_accepts_a_service_pid():
    s=recovery.System();s.command=lambda _:RAW[recovery.TIMER]+"MainPID=0\n"
    with pytest.raises(recovery.RecoveryError,match="RECOVERY_UNIT_INVALID"):s.unit(recovery.TIMER)


@pytest.mark.parametrize("unit",["other.timer","other.service","djconnect-watchdog.timer\n","../service", ""])
def test_unknown_unit_cannot_reach_systemctl(unit):
    s=recovery.System();s.command=lambda _:pytest.fail("no command for an unknown unit")
    with pytest.raises(recovery.RecoveryError,match="RECOVERY_UNIT_NOT_ALLOWED"):s.unit(unit)


def test_complete_preclaim_and_recovery_with_pidless_timer(tmp_path):
    from test_pi_rc6_recovery_root import BOOT, RUN, FakeSystem
    s=FakeSystem(tmp_path);s.units[recovery.TIMER].pop("MainPID")
    result=recovery.execute(s,RUN,BOOT)
    assert result["result"]=="RECOVERED_PENDING_SMOKE" and s.installed_calls==2 and s.records[-1]["watchdog_restored"] is True
    assert s.calls.index("claim")<s.calls.index("hold")<s.calls.index("install")


@pytest.mark.parametrize("phase",["identity","no_competing_installer","installed_before","markers","maintenance_available","configuration","api","artifact","read_config"])
def test_preclaim_failure_still_cannot_hold_or_install(tmp_path,phase):
    from test_pi_rc6_recovery_root import BOOT, RUN, FakeSystem
    s=FakeSystem(tmp_path,phase);s.units[recovery.TIMER].pop("MainPID")
    with pytest.raises(recovery.RecoveryError):recovery.execute(s,RUN,BOOT)
    assert s.claimed is False and s.held is False and "hold" not in s.calls and "install" not in s.calls


@pytest.mark.parametrize("case",["known","unknown","oserror"])
def test_private_failure_diagnostic_uses_only_reviewed_static_codes(capsys,case):
    node=next(x for x in ast.parse(Path(recovery.__file__).read_text()).body if isinstance(x,ast.If) and isinstance(x.test,ast.Compare))
    def fail():
        if case=="known":raise recovery.RecoveryError("RECOVERY_UNIT_INVALID")
        if case=="unknown":raise recovery.RecoveryError("PRIVATE_CREDENTIAL_DO_NOT_EXPORT")
        raise OSError("/private/credential/DO_NOT_EXPORT")
    ns={"__name__":"__main__","main":fail,"RecoveryError":recovery.RecoveryError,"DIAGNOSTIC_CODES":recovery.DIAGNOSTIC_CODES,"json":json,"subprocess":subprocess}
    with pytest.raises(SystemExit) as e:exec(compile(ast.Module(body=[node],type_ignores=[]),"reviewed-private-diagnostic","exec"),ns)  # noqa: S102 -- only the reviewed local exception handler; main is a test double.
    assert e.value.code==1
    out=capsys.readouterr().out;data=json.loads(out)
    assert data=={"result":"RECOVERY_INCOMPLETE","code":"RECOVERY_UNIT_INVALID" if case=="known" else "REQUIRES_ACTUAL_STATE_REVIEW"}
    assert "PRIVATE" not in out and "credential" not in out and "DO_NOT_EXPORT" not in out


@pytest.mark.parametrize("tail",["unexpected\n","LoadState=loaded\n","MainPID=123\n","\n"])
def test_unparsed_or_duplicate_metadata_lines_cannot_be_hidden(tail):
    s=recovery.System();s.command=lambda _:RAW[recovery.API]+tail
    with pytest.raises(recovery.RecoveryError,match="RECOVERY_UNIT_INVALID"):s.unit(recovery.API)
