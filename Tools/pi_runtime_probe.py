"""Local native runtime check; no deployment authority or service/config changes.

Not wired into a released smoke schema. Installed-venv and caller-authenticated
running-PID executable checks remain separate from service/release authority.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

PYTHON_VERSION = "3.14.9"
QT_VERSION = "6.12.0"
PROBE_TIMEOUT = 15

# No output is collected: imports cannot fill a capture buffer or disclose local
# details in an exception. Every predicate is evaluated by the selected venv.
PROBE = """
import pathlib, sys, sysconfig
from PySide6 import __version__ as pyside_version
from PySide6.QtCore import qVersion
prefix, base = (pathlib.Path(value).resolve(strict=True) for value in sys.argv[1:])
valid = (
    sys.version_info[:3] == (3, 14, 9)
    and sysconfig.get_config_var('Py_GIL_DISABLED') != 1
    and sys._is_gil_enabled() is True
    and pathlib.Path(sys.prefix).resolve(strict=True) == prefix
    and pathlib.Path(sys.base_prefix).resolve(strict=True) == base
    and prefix != base
    and pathlib.Path(sys.executable).parent.parent.resolve(strict=True) == prefix
    and pyside_version == '6.12.0'
    and qVersion() == '6.12.0'
)
raise SystemExit(0 if valid else 78)
"""


class RuntimeProbeError(ValueError):
    """Static local failure only; never child output, config or credentials."""


@dataclass(frozen=True)
class RuntimeReadback:
    python_version: str
    qt_version: str
    gil_enabled: bool


def probe_installed_runtime(venv: Path, managed_base: Path) -> RuntimeReadback:
    """Verify the caller-selected installed venv against its trusted base.

    The caller must establish ownership, exact release and base provenance. This
    helper neither admits a target nor authenticates the supplied directories.
    """
    try:
        if not venv.is_absolute() or not managed_base.is_absolute():
            raise RuntimeProbeError("RUNTIME_PATH_INVALID")
        prefix = venv.resolve(strict=True)
        base = managed_base.resolve(strict=True)
        python = prefix / "bin/python"
        expected = base / "bin/python3.14"
        if (prefix == base or not python.is_file() or not expected.is_file()
                or python.resolve(strict=True) != expected.resolve(strict=True)):
            raise RuntimeProbeError("RUNTIME_BASE_MISMATCH")
        result = subprocess.run(
            [str(python), "-I", "-B", "-c", PROBE, str(prefix), str(base)],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"}, cwd=prefix,
            timeout=PROBE_TIMEOUT, check=False,
        )
        if result.returncode != 0:
            raise RuntimeProbeError("RUNTIME_NATIVE_CHECK_FAILED")
    except RuntimeProbeError:
        raise
    except (OSError, RuntimeError, subprocess.SubprocessError):
        raise RuntimeProbeError("RUNTIME_PROBE_UNAVAILABLE") from None
    return RuntimeReadback(PYTHON_VERSION, QT_VERSION, True)


PROC_ROOT = Path("/proc")


@dataclass(frozen=True)
class RunningInterpreterReadback:
    pid: int
    start_ticks: int


def _start_ticks(stat_path: Path, pid: int) -> int:
    with stat_path.open("rb") as stream:
        raw = stream.read(4097)
    if len(raw) > 4096 or not raw.startswith(f"{pid} (".encode()):
        raise RuntimeProbeError("PROCESS_IDENTITY_INVALID")
    # comm may itself contain spaces and parentheses; fields after its final ')'
    # begin at field3, so starttime(field22) is index19 in the remaining fields.
    marker = raw.rfind(b") ")
    fields = raw[marker+2:].split() if marker >= 0 else []
    if len(fields) < 20 or not fields[19].isdigit() or int(fields[19]) <= 0:
        raise RuntimeProbeError("PROCESS_IDENTITY_INVALID")
    return int(fields[19])


def probe_running_interpreter(pid: int, managed_base: Path) -> RunningInterpreterReadback:
    """Read a caller-authenticated service PID without arguments or credentials.

    Confirms executable path/inode and stable PID starttime across this bounded
    read. Does not prove module bytes, venv selection or future process lifetime.
    The parent must establish MainPID, trusted base and release provenance.
    """
    if type(pid) is not int or pid <= 0 or not managed_base.is_absolute():
        raise RuntimeProbeError("PROCESS_IDENTITY_INVALID")
    try:
        expected = (managed_base / "bin/python3.14").resolve(strict=True)
        expected_stat = expected.stat()
        if not expected.is_file():
            raise RuntimeProbeError("PROCESS_INTERPRETER_MISMATCH")
        process = PROC_ROOT / str(pid)
        start = _start_ticks(process / "stat", pid)
        executable = process / "exe"
        for _ in range(2):
            actual = executable.stat()
            if (executable.resolve(strict=True) != expected
                    or (actual.st_dev, actual.st_ino) != (expected_stat.st_dev, expected_stat.st_ino)):
                raise RuntimeProbeError("PROCESS_INTERPRETER_MISMATCH")
        if _start_ticks(process / "stat", pid) != start:
            raise RuntimeProbeError("PROCESS_IDENTITY_CHANGED")
    except RuntimeProbeError:
        raise
    except (OSError, RuntimeError):
        raise RuntimeProbeError("PROCESS_PROBE_UNAVAILABLE") from None
    return RunningInterpreterReadback(pid, start)
