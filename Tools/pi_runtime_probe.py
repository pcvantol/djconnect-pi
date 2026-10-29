"""Local native runtime check; no deployment authority or service/config changes.

Not wired into a released smoke schema. This verifies an installed venv, not
which interpreter an already-running app process uses.
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
