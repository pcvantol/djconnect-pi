"""Updater migration regression: real isolated probes; all update effects synthetic."""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from djconnect_pi import updater


def fake_interpreter(tmp_path, version, free_threaded=0):
    script = tmp_path / "probe.py"
    script.write_text("import sys,sysconfig\nsys.version_info=" + repr(version)
        + "\nsysconfig.get_config_var=lambda name:" + str(free_threaded)
        + "\nexec(sys.argv[-1])\n")
    executable = tmp_path / "python-selected"
    executable.write_text("#!/bin/sh\nexec " + shlex.quote(sys.executable)
        + " -I -B " + shlex.quote(str(script)) + ' "$@"\n')
    executable.chmod(0o755)
    return executable


@pytest.mark.parametrize("version,free_threaded,accepted", [
    ((3, 11, 17), 0, False), ((3, 13, 5), 0, False), ((3, 14, 8), 0, False),
    ((3, 14, 9), 0, True), ((3, 14, 10), 0, True), ((3, 15, 0), 0, False),
    ((3, 14, 9), 1, False),
])
def test_actual_selected_interpreter_probe(tmp_path, monkeypatch, version, free_threaded, accepted):
    executable = fake_interpreter(tmp_path, version, free_threaded)
    monkeypatch.setattr(updater, "APPLICATION_PYTHON", executable)
    if accepted:
        assert updater.application_python() == str(executable)
    else:
        with pytest.raises(RuntimeError, match="APPLICATION_PYTHON_UNAVAILABLE_OR_INCOMPATIBLE"):
            updater.application_python()


@pytest.mark.parametrize("failure", [FileNotFoundError(), subprocess.TimeoutExpired("probe", 30)])
def test_missing_or_hung_runtime_fails_closed(monkeypatch, failure):
    run = Mock(side_effect=failure)
    monkeypatch.setattr(updater.subprocess, "run", run)
    with pytest.raises(RuntimeError, match="APPLICATION_PYTHON_UNAVAILABLE_OR_INCOMPATIBLE"):
        updater.application_python()
    assert run.call_count == 1
    args, kwargs = run.call_args
    assert args[0][0] == "/opt/djconnect-python/cpython-3.14.9/bin/python3.14"
    assert args[0][1:4] == ["-I", "-B", "-c"]
    assert kwargs["env"] == {"PATH": "/usr/bin:/bin"} and kwargs["timeout"] == 30
    assert kwargs["stdout"] == kwargs["stderr"] == kwargs["stdin"] == subprocess.DEVNULL


def release_fixture(tmp_path):
    release = tmp_path / "release"
    (release / "wheels").mkdir(parents=True)
    (release / "wheels/djconnect_pi-4.0.0rc7-py3-none-any.whl").write_bytes(b"synthetic-wheel")
    (release / "requirements.lock").write_text("requests==2.34.2\n")
    return release


@pytest.mark.parametrize("case", ["old", "early314", "next315", "site", "binary", "unmarked", "missingcfg", "symlinkcfg", "fifo", "oversize", "symlinkvenv", "missingvenv"])
def test_incompatible_partial_environment_is_preserved_before_any_execution(tmp_path, monkeypatch, case):
    release = release_fixture(tmp_path)
    venv = release / ".venv"
    (venv / "bin").mkdir(parents=True)
    (venv / "bin/python").symlink_to(sys._base_executable)
    cfg = venv / "pyvenv.cfg"
    cfg.write_text("version = 3.14.9\ninclude-system-site-packages = false\n")
    state = release / ".install-state"
    state.mkdir()
    marker = state / "venv_created"
    marker.write_text("original-marker")
    if case in {"old", "early314", "next315"}:
        cfg.write_text("version = " + {"old": "3.13.5", "early314": "3.14.8", "next315": "3.15.0"}[case]
            + "\ninclude-system-site-packages = false\n")
    if case == "site": cfg.write_text("version = 3.14.9\ninclude-system-site-packages = true\n")
    if case == "binary":
        (venv / "bin/python").unlink()
        (venv / "bin/python").write_text("NEVER_EXECUTE_OLD_BINARY")
    if case == "unmarked": marker.unlink()
    if case in {"missingcfg", "symlinkcfg", "fifo"}:
        cfg.unlink()
        if case == "symlinkcfg":
            other = tmp_path / "other.cfg"
            other.write_text("version = 3.14.9\ninclude-system-site-packages = false\n")
            cfg.symlink_to(other)
        if case == "fifo": os.mkfifo(cfg)
    if case == "oversize": cfg.write_text("x" * 16385)
    if case in {"symlinkvenv", "missingvenv"}:
        venv.rename(release / "preserved-venv")
        if case == "symlinkvenv": venv.symlink_to("preserved-venv", target_is_directory=True)
    before = [(str(p.relative_to(release)), p.lstat().st_mode, p.lstat().st_size)
        for p in release.rglob("*")]
    monkeypatch.setattr(updater, "application_python", lambda: sys._base_executable)
    effect = Mock(side_effect=AssertionError("No process/cache/service effect allowed"))
    monkeypatch.setattr(updater.subprocess, "run", effect)
    monkeypatch.setattr(updater, "pip_environment", effect)
    with pytest.raises(RuntimeError, match="EXISTING_PYTHON_ENVIRONMENT_INCOMPATIBLE"):
        updater.install_python_dependencies(release, "4.0.0-rc.7")
    assert before == [(str(p.relative_to(release)), p.lstat().st_mode, p.lstat().st_size)
        for p in release.rglob("*")]
    effect.assert_not_called()


def test_fixed_runtime_creates_environment_and_isolated_pip_then_can_resume(tmp_path, monkeypatch):
    release = release_fixture(tmp_path)
    monkeypatch.setattr(updater, "application_python", lambda: sys._base_executable)
    monkeypatch.setattr(updater, "pip_environment", lambda: {"PIP_CACHE_DIR": "/synthetic-cache"})
    monkeypatch.setattr(updater, "validate_release_entrypoints", Mock())
    calls = []
    def command(args, **kwargs):
        calls.append((args, kwargs))
        if "venv" in args:
            venv = Path(args[-1])
            (venv / "bin").mkdir(parents=True)
            (venv / "bin/python").symlink_to(sys._base_executable)
            (venv / "pyvenv.cfg").write_text("version = 3.14.9\ninclude-system-site-packages = false\n")
    monkeypatch.setattr(updater.subprocess, "run", command)
    updater.install_python_dependencies(release, "4.0.0-rc.7")
    assert calls[0][0][:5] == [sys._base_executable, "-I", "-B", "-m", "venv"]
    assert all(args[1:5] == ["-I", "-B", "-m", "pip"] for args, _ in calls[1:])
    assert all(kwargs["env"] == {"PIP_CACHE_DIR": "/synthetic-cache"} for _, kwargs in calls[1:])
    count = len(calls)
    updater.install_python_dependencies(release, "4.0.0-rc.7")
    assert len(calls) == count


def run_fixture(tmp_path, monkeypatch, failure=None):
    events = []
    root = tmp_path / "root"
    old = root / "releases/old"
    old.mkdir(parents=True)
    (old / "VERSION").write_text("4.0.0-rc.6")
    (root / "current").symlink_to(old)
    target = root / "releases/new"
    target.mkdir()
    cfg = updater.UpdaterConfig(repo="fixture/release", release_profile="pi5-arm64", install_root=root)
    monkeypatch.setattr(updater, "public_latest_release", lambda _: {"tag_name": "v4.0.0-rc.7"})
    monkeypatch.setattr(updater, "profile_asset_url", lambda *a: "synthetic-url")
    def event(name):
        events.append(name)
        if name == failure: raise RuntimeError("synthetic-" + name)
    monkeypatch.setattr(updater, "application_python", lambda: event("runtime"), raising=False)
    monkeypatch.setattr(updater, "download", lambda *a: event("download"))
    monkeypatch.setattr(updater, "verify_sha256", lambda *a: event("verify"))
    def prepare(*args, **kwargs):
        assert kwargs["activate"] is False
        assert "stop" not in events and (root / "current").resolve() == old
        event("prepare")
        return target
    monkeypatch.setattr(updater, "install_release", prepare)
    monkeypatch.setattr(updater, "stop_services", lambda *a: event("stop"))
    monkeypatch.setattr(updater, "start_service", lambda *a: event("start-ui"))
    def activate(*args):
        event("activate")
        (root / "current").unlink()
        (root / "current").symlink_to(target)
    monkeypatch.setattr(updater, "activate_release", activate)
    monkeypatch.setattr(updater, "refresh_systemd_units", lambda *a: event("units"))
    monkeypatch.setattr(updater, "cleanup_old_releases", lambda *a: event("cleanup"))
    monkeypatch.setattr(updater, "stop_service", lambda *a: event("stop-ui"))
    monkeypatch.setattr(updater, "restart_services", lambda *a: event("restart"))
    return cfg, events, old, target


@pytest.mark.parametrize("failure", ["runtime", "download", "verify", "prepare"])
def test_preparation_failure_never_stops_or_restarts_current_app(tmp_path, monkeypatch, failure):
    cfg, events, old, _ = run_fixture(tmp_path, monkeypatch, failure)
    with pytest.raises(RuntimeError, match="synthetic-" + failure): updater.run(cfg)
    assert not {"stop", "start-ui", "stop-ui", "restart", "activate"}.intersection(events)
    assert (cfg.install_root / "current").resolve() == old
    assert json.loads((cfg.install_root / "config/updater-status.json").read_text())["state"] == "failed"


@pytest.mark.parametrize("failure", ["stop", "start-ui", "activate", "units", "cleanup", "stop-ui", "restart"])
def test_started_switch_always_attempts_one_service_restart_and_reports_failure(tmp_path, monkeypatch, failure):
    cfg, events, old, target = run_fixture(tmp_path, monkeypatch, failure)
    with pytest.raises(RuntimeError, match="synthetic-" + failure): updater.run(cfg)
    assert events.count("stop-ui") == events.count("restart") == 1
    assert events.index("prepare") < events.index("stop")
    expected = old if failure in {"stop", "start-ui", "activate"} else target
    assert (cfg.install_root / "current").resolve() == expected
    assert json.loads((cfg.install_root / "config/updater-status.json").read_text())["state"] == "failed"


def test_normal_switch_is_one_activation_then_restart(tmp_path, monkeypatch):
    cfg, events, _, target = run_fixture(tmp_path, monkeypatch)
    assert updater.run(cfg) == "Installed 4.0.0-rc.7"
    assert events.index("prepare") < events.index("stop") < events.index("activate") < events.index("restart")
    assert events.count("activate") == events.count("restart") == 1
    assert (cfg.install_root / "current").resolve() == target


@pytest.mark.parametrize("alias", [False, True])
def test_current_release_refused_before_unpack_or_dependency_effects(tmp_path, monkeypatch, alias):
    target = tmp_path / "releases/4.0.0-rc.7-pi5-arm64"
    target.mkdir(parents=True)
    current = tmp_path / "current"
    current.symlink_to(target)
    if alias:
        current.unlink()
        other = tmp_path / "alias"
        other.symlink_to(target)
        current.symlink_to(other)
    effect = Mock(side_effect=AssertionError("Active release must not be modified"))
    monkeypatch.setattr(updater, "unpack_release", effect)
    with pytest.raises(RuntimeError, match="UPDATE_REQUIRES_DISTINCT_RELEASE"):
        updater.install_release(tmp_path / "unused.tar", "4.0.0-rc.7", tmp_path, release_profile="pi5-arm64", activate=False)
    effect.assert_not_called()
