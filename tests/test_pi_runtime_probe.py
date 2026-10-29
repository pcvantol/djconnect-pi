import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from Tools import pi_runtime_probe as probe


@pytest.fixture
def paths(tmp_path: Path):
    base = tmp_path / "base"
    venv = tmp_path / "venv"
    (base / "bin").mkdir(parents=True)
    (venv / "bin").mkdir(parents=True)
    (base / "bin/python3.14").write_text("not executed by unit fixtures")
    (venv / "bin/python").symlink_to(base / "bin/python3.14")
    return venv, base


def test_native_probe_is_one_bounded_isolated_process(paths, monkeypatch):
    run = Mock(return_value=SimpleNamespace(returncode=0))
    monkeypatch.setattr(probe.subprocess, "run", run)
    venv, base = paths
    assert probe.probe_installed_runtime(venv, base) == probe.RuntimeReadback("3.14.9", "6.12.0", True)
    args, options = run.call_args
    assert run.call_count == 1
    assert args[0] == [str(venv / "bin/python"), "-I", "-B", "-c", probe.PROBE, str(venv), str(base)]
    assert options == {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL,
                       "stderr": subprocess.DEVNULL, "env": {"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
                       "cwd": venv, "timeout": 15, "check": False}


@pytest.mark.parametrize("status", [1, 78, -11, 127])
def test_native_failure_never_reports_success_or_retries(paths, monkeypatch, status):
    run = Mock(return_value=SimpleNamespace(returncode=status))
    monkeypatch.setattr(probe.subprocess, "run", run)
    with pytest.raises(probe.RuntimeProbeError, match="^RUNTIME_NATIVE_CHECK_FAILED$"):
        probe.probe_installed_runtime(*paths)
    assert run.call_count == 1


@pytest.mark.parametrize("failure", [OSError("private detail"), subprocess.TimeoutExpired("secret", 15)])
def test_unavailable_probe_keeps_private_details_out_of_message(paths, monkeypatch, failure):
    run = Mock(side_effect=failure)
    monkeypatch.setattr(probe.subprocess, "run", run)
    with pytest.raises(probe.RuntimeProbeError, match="^RUNTIME_PROBE_UNAVAILABLE$"):
        probe.probe_installed_runtime(*paths)
    assert run.call_count == 1


@pytest.mark.parametrize("kind", ["relative", "missing", "wrong-base", "same-prefix"])
def test_bad_paths_are_rejected_before_execution(paths, monkeypatch, kind):
    venv, base = paths
    run = Mock()
    monkeypatch.setattr(probe.subprocess, "run", run)
    if kind == "relative":
        venv = Path("relative")
    elif kind == "missing":
        venv = venv / "absent"
    elif kind == "wrong-base":
        (venv / "bin/python").unlink()
        (venv / "bin/python").write_text("wrong base")
    else:
        venv = base
    with pytest.raises(probe.RuntimeProbeError):
        probe.probe_installed_runtime(venv, base)
    run.assert_not_called()


@pytest.mark.parametrize("case", ["valid", "old-python", "future-python", "disabled-gil-build",
                                  "disabled-gil-runtime", "wrong-qt", "wrong-pyside",
                                  "wrong-prefix", "wrong-base", "wrong-executable", "system-prefix"])
def test_exact_native_predicates(paths, case):
    import builtins
    venv, base = paths
    native = SimpleNamespace(version_info=(3, 14, 9), argv=["-c", str(venv), str(base)],
                             prefix=str(venv), base_prefix=str(base), executable=str(venv / "bin/python"),
                             _is_gil_enabled=lambda: True)
    disabled = 0
    qt = "6.12.0"
    pyside = SimpleNamespace(__version__="6.12.0")
    if case == "old-python": native.version_info = (3, 13, 5)
    elif case == "future-python": native.version_info = (3, 15, 0)
    elif case == "disabled-gil-build": disabled = 1
    elif case == "disabled-gil-runtime": native._is_gil_enabled = lambda: False
    elif case == "wrong-qt": qt = "6.11.2"
    elif case == "wrong-pyside": pyside.__version__ = "6.11.2"
    elif case == "wrong-prefix": native.prefix = str(base)
    elif case == "wrong-base": native.base_prefix = str(venv)
    elif case == "wrong-executable": native.executable = str(base / "bin/python3.14")
    elif case == "system-prefix": native.argv = ["-c", str(base), str(base)]; native.prefix = str(base)
    replacements = {"sys": native, "sysconfig": SimpleNamespace(get_config_var=lambda _: disabled),
                    "PySide6": pyside, "PySide6.QtCore": SimpleNamespace(qVersion=lambda: qt)}
    def controlled_import(name, *args, **kwargs):
        return replacements[name] if name in replacements else builtins.__import__(name, *args, **kwargs)
    environment = {"__builtins__": {**vars(builtins), "__import__": controlled_import}}
    with pytest.raises(SystemExit) as result:
        exec(probe.PROBE, environment)  # noqa: S102 - exact internal constant, controlled imports only
    assert result.value.code == (0 if case == "valid" else 78)


@pytest.fixture
def running(paths, tmp_path, monkeypatch):
    _, base = paths
    proc = tmp_path / "proc"
    process = proc / "123"
    process.mkdir(parents=True)
    (process / "exe").symlink_to(base / "bin/python3.14")
    (process / "stat").write_bytes(b"123 (python ) worker) S " + b"0 " * 18 + b"456 0\n")
    monkeypatch.setattr(probe, "PROC_ROOT", proc)
    return process, base


def test_running_executable_join_and_comm_parentheses(running):
    _, base = running
    assert probe.probe_running_interpreter(123, base) == probe.RunningInterpreterReadback(123, 456)


@pytest.mark.parametrize("pid", [True, False, 0, -1, "123", None, 1.5])
def test_running_pid_requires_positive_strict_integer(running, pid):
    _, base = running
    with pytest.raises(probe.RuntimeProbeError, match="^PROCESS_IDENTITY_INVALID$"):
        probe.probe_running_interpreter(pid, base)


@pytest.mark.parametrize("kind", ["wrong-pid", "truncated", "zero-start", "non-numeric", "oversize"])
def test_running_stat_is_bounded_and_strict(running, kind):
    process, base = running
    values = {"wrong-pid": b"12 (python) S " + b"0 " * 18 + b"456",
              "truncated": b"123 (python) S 0", "zero-start": b"123 (python) S " + b"0 " * 19,
              "non-numeric": b"123 (python) S " + b"0 " * 18 + b"false",
              "oversize": b"123 (" + b"x" * 4096}
    (process / "stat").write_bytes(values[kind])
    with pytest.raises(probe.RuntimeProbeError, match="^PROCESS_IDENTITY_INVALID$"):
        probe.probe_running_interpreter(123, base)


@pytest.mark.parametrize("kind", ["gone", "wrong-exe", "deleted-exe", "same-inode-wrong-path"])
def test_running_missing_or_wrong_executable_fails(running, kind):
    process, base = running
    (process / "exe").unlink()
    if kind == "wrong-exe":
        (process / "exe").write_text("other image")
    elif kind == "deleted-exe":
        (process / "exe").symlink_to(str(base / "bin/python3.14") + " (deleted)")
    elif kind == "same-inode-wrong-path":
        alternate = base / "bin/other"
        alternate.hardlink_to(base / "bin/python3.14")
        (process / "exe").symlink_to(alternate)
    with pytest.raises(probe.RuntimeProbeError):
        probe.probe_running_interpreter(123, base)


def test_running_pid_reuse_between_reads_fails(running, monkeypatch):
    _, base = running
    read = Mock(side_effect=[456, 789])
    monkeypatch.setattr(probe, "_start_ticks", read)
    with pytest.raises(probe.RuntimeProbeError, match="^PROCESS_IDENTITY_CHANGED$"):
        probe.probe_running_interpreter(123, base)
    assert read.call_count == 2


def test_running_exec_change_between_reads_fails(running, monkeypatch):
    process, base = running
    real = Path.resolve
    calls = 0
    def changing(path, *args, **kwargs):
        nonlocal calls
        if path == process / "exe":
            calls += 1
            if calls == 2:
                return base / "other"
        return real(path, *args, **kwargs)
    monkeypatch.setattr(Path, "resolve", changing)
    with pytest.raises(probe.RuntimeProbeError, match="^PROCESS_INTERPRETER_MISMATCH$"):
        probe.probe_running_interpreter(123, base)


def test_running_probe_never_reads_arguments_or_environment(running, monkeypatch):
    process, base = running
    original = Path.open
    opened = []
    def tracking(path, *args, **kwargs):
        opened.append(path)
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", tracking)
    probe.probe_running_interpreter(123, base)
    assert opened == [process / "stat", process / "stat"]


def test_running_same_path_with_different_inode_is_rejected(running, monkeypatch):
    process, base = running
    original = Path.stat
    def changed(path, *args, **kwargs):
        result = original(path, *args, **kwargs)
        return SimpleNamespace(st_dev=result.st_dev, st_ino=result.st_ino + 1) if path == process / "exe" else result
    monkeypatch.setattr(Path, "stat", changed)
    with pytest.raises(probe.RuntimeProbeError, match="^PROCESS_INTERPRETER_MISMATCH$"):
        probe.probe_running_interpreter(123, base)
