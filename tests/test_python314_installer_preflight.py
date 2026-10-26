"""Execute the real installer Python preflight with synthetic interpreters/effects."""
from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts/install.sh").read_text()


def function(name):
    match = re.search(r"(?ms)^" + name + r"\(\) \{\n.*?^\}", SCRIPT)
    assert match
    return match.group()


def interpreter(tmp_path):
    body = tmp_path / "fake.py"
    body.write_text(
        "import json,os,sys,sysconfig\n"
        "sys.version_info=tuple(json.loads(os.environ['FIXTURE_VERSION']))\n"
        "sysconfig.get_config_var=lambda name: int(os.environ['FIXTURE_NO_GIL'])\n"
        "exec(compile(sys.stdin.read(),'<real-installer-version-check>','exec'))\n"
    )
    wrapper = tmp_path / "fixture-python"
    wrapper.write_text("#!/bin/sh\nexec " + shlex.quote(sys.executable) + " " + shlex.quote(str(body)) + ' "$@"\n')
    wrapper.chmod(0o755)
    return wrapper


@pytest.mark.parametrize("version,accepted", [
    ("[3,11,17]", False), ("[3,13,5]", False), ("[3,14,8]", False),
    ("[3,14,9]", True), ("[3,14,10]", True), ("[3,15,0]", False),
])
@pytest.mark.parametrize("approved", [False, True])
def test_real_preflight_precedes_both_service_effects(tmp_path, version, accepted, approved):
    python = interpreter(tmp_path)
    prefix = SCRIPT.split("main() {", 1)[1].split("  stop_running_updater_early", 1)[0]
    effect = tmp_path / "service-effects"
    shell = (
        "set -eu\nlog(){ :; }; print_resources(){ :; }\n"
        "parse_approved_input(){ :; }; verify_approved_release(){ :; }\n"
        "approved_config_digest(){ echo synthetic-digest; }\n"
        "check_cpu_architecture(){ :; }; provision_application_python(){ :; }\n"
        "check_runtime_dependencies(){ :; }; check_existing_python_environment(){ :; }; check_release_not_active(){ :; }\n"
        + function("check_python_version") + "\n"
        + "DJCONNECT_PYTHON=" + shlex.quote(str(python)) + "\n"
        + "APPROVED_ARTIFACT=" + ("synthetic" if approved else "''") + "\nDJCONNECT_VERSION=synthetic\n"
        + prefix + "\nprintf 'updater\\nclient\\n' > " + shlex.quote(str(effect))
    )
    result = subprocess.run(["bash", "-c", shell], capture_output=True, text=True, check=False,
                            env={**os.environ, "FIXTURE_VERSION": version, "FIXTURE_NO_GIL": "0"})
    assert (result.returncode == 0) is accepted, result.stderr
    assert effect.exists() is accepted
    if not accepted:
        assert "Python 3.14.9 or newer in 3.14 is required" in result.stderr


def test_free_threaded_python_is_rejected_before_effects(tmp_path):
    python = interpreter(tmp_path)
    result = subprocess.run(["bash", "-c", "set -e\nlog(){ :; }; print_resources(){ :; }\n"
                            + function("check_python_version") + "\nDJCONNECT_PYTHON="
                            + shlex.quote(str(python)) + "\ncheck_python_version\necho EFFECT"],
                            capture_output=True, text=True, check=False,
                            env={**os.environ, "FIXTURE_VERSION": "[3,14,9]", "FIXTURE_NO_GIL": "1"})
    assert result.returncode != 0 and "EFFECT" not in result.stdout


@pytest.mark.parametrize("marker", ["ready", "partial"])
@pytest.mark.parametrize("problem", ["old-version", "wrong-interpreter"])
def test_existing_old_python_venv_is_preserved_and_never_executed(tmp_path, marker, problem):
    python = interpreter(tmp_path)
    release = tmp_path / "releases/fixture"
    binary = release / ".venv/bin/python"
    binary.parent.mkdir(parents=True)
    executed = tmp_path / "OLD_INTERPRETER_EXECUTED"
    binary.write_text("#!/bin/sh\ntouch " + shlex.quote(str(executed)) + "\n")
    binary.chmod(0o755)
    cfg = binary.parents[1] / "pyvenv.cfg"
    cfg.write_text("version = " + ("3.13.5" if problem == "old-version" else "3.14.9")
                   + "\ninclude-system-site-packages = false\n")
    if marker == "partial":
        (release / ".install-state").mkdir()
        (release / ".install-state/venv_created").touch()
    before = binary.read_bytes()
    shell = ("set -eu\nlog(){ :; }; print_resources(){ :; }\nrelease_id(){ echo fixture; }\n"
             + "marker_done(){ " + ("return 0" if marker == "ready" else "return 1") + "; }\n"
             + function("check_existing_python_environment")
             + "\nDJCONNECT_PYTHON=" + shlex.quote(str(python))
             + "\nDJCONNECT_ROOT=" + shlex.quote(str(tmp_path))
             + "\ncheck_existing_python_environment\necho EFFECT")
    result = subprocess.run(["bash", "-c", shell], capture_output=True, text=True, check=False,
                            env={**os.environ, "FIXTURE_VERSION": "[3,14,9]", "FIXTURE_NO_GIL": "0"})
    assert result.returncode != 0 and "EFFECT" not in result.stdout
    assert not executed.exists() and binary.read_bytes() == before


def test_matching_python314_venv_can_resume(tmp_path):
    release = tmp_path / "releases/fixture/.venv"
    (release / "bin").mkdir(parents=True)
    (release / "bin/python").symlink_to(sys._base_executable)
    (release / "pyvenv.cfg").write_text("version = 3.14.9\ninclude-system-site-packages = false\n")
    shell = ("set -eu\nrelease_id(){ echo fixture; }; marker_done(){ return 0; }\n"
             + function("check_existing_python_environment")
             + "\nDJCONNECT_PYTHON=" + shlex.quote(sys.executable)
             + "\nDJCONNECT_ROOT=" + shlex.quote(str(tmp_path))
             + "\ncheck_existing_python_environment\necho RESUME_ALLOWED")
    result = subprocess.run(["bash", "-c", shell], capture_output=True, text=True, check=False)
    assert result.returncode == 0 and "RESUME_ALLOWED" in result.stdout, result.stderr


@pytest.mark.parametrize("alias", [False, True])
def test_active_release_cannot_be_replaced_during_preparation(tmp_path, alias):
    release = tmp_path / "releases/fixture"
    release.mkdir(parents=True)
    target = release
    if alias:
        target = tmp_path / "alias"
        target.symlink_to(release, target_is_directory=True)
    (tmp_path / "current").symlink_to(target, target_is_directory=True)
    sentinel = release / "unchanged"
    sentinel.write_text("active")
    shell = ("set -eu\nrelease_id(){ echo fixture; }\n"
             + function("check_release_not_active") + "\nDJCONNECT_ROOT="
             + shlex.quote(str(tmp_path)) + "\ncheck_release_not_active\necho EFFECT")
    result = subprocess.run(["bash", "-c", shell], capture_output=True, text=True, check=False)
    assert result.returncode == 65 and "EFFECT" not in result.stdout
    assert "PYTHON_MIGRATION_REQUIRES_DISTINCT_RELEASE" in result.stderr
    assert sentinel.read_text() == "active"


@pytest.mark.parametrize("failed_stage", ["download_release", "install_python_dependencies", None])
def test_preparation_failure_keeps_old_client_running(tmp_path, failed_stage):
    main = SCRIPT.split("main() {", 1)[1].split('\nmain "$@"', 1)[0]
    events = tmp_path / "events"
    functions = re.findall(r"^ +([a-z_]+)(?: |$)", main, re.MULTILINE)
    stubs = ""
    for name in set(functions) - {"if", "else", "fi", "local", "echo"}:
        status = "return 17" if name == failed_stage else ":"
        stubs += name + "(){ echo " + name + " >> " + shlex.quote(str(events)) + "; " + status + "; };\n"
    shell = "set -eu\nAPPROVED_ARTIFACT=''\nDJCONNECT_VERSION=synthetic\n" + stubs + "main(){" + main + "\nmain"
    result = subprocess.run(["bash", "-c", shell], capture_output=True, text=True, check=False)
    calls = events.read_text().splitlines()
    if failed_stage:
        assert result.returncode == 17, result.stderr
        assert "stop_running_client_early" not in calls and "activate_release" not in calls
    else:
        assert result.returncode == 0, result.stderr
        assert calls.index("install_python_dependencies") < calls.index("stop_running_client_early") < calls.index("activate_release")


@pytest.mark.parametrize("variable", ["PYTHONPATH", "PYTHONHOME"])
def test_selected_interpreter_ignores_ambient_python_injection(tmp_path, variable):
    injected = tmp_path / "injection"
    injected.mkdir()
    marker = tmp_path / "UNTRUSTED_CODE_EXECUTED"
    (injected / "sitecustomize.py").write_text("from pathlib import Path;Path(" + repr(str(marker)) + ").touch()")
    shell = ("set -eu\nlog(){ :; }; print_resources(){ :; }\n"
             + function("check_python_version") + "\nDJCONNECT_PYTHON="
             + shlex.quote(sys.executable) + "\ncheck_python_version\necho VERIFIED")
    result = subprocess.run(["bash", "-c", shell], capture_output=True, text=True, check=False,
                            env={**os.environ, variable: str(injected)})
    assert result.returncode == 0 and "VERIFIED" in result.stdout, result.stderr
    assert not marker.exists()
