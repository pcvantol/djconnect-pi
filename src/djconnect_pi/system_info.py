from __future__ import annotations

from pathlib import Path
import logging
import os
import platform
import socket

_LOGGER = logging.getLogger(__name__)


def raspberry_pi_system_info() -> dict[str, str]:
    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "machine": platform.machine(),
        "model": _read_first_line(Path("/proc/device-tree/model")) or _read_first_line(Path("/sys/firmware/devicetree/base/model")),
        "cpu": _cpu_model(),
        "memory_mb": _memory_mb(),
        "os_pretty_name": _os_pretty_name(),
    }


def log_raspberry_pi_system_info() -> None:
    info = raspberry_pi_system_info()
    details = ", ".join(f"{key}={value or 'unknown'}" for key, value in info.items())
    _LOGGER.info("DJConnect Pi runtime system info: %s", details)


def _read_first_line(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore").replace("\x00", "").splitlines()[0].strip()
    except (FileNotFoundError, IndexError, OSError):
        return ""


def _cpu_model() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.lower().startswith(("model name", "hardware", "processor")):
                return line.split(":", 1)[-1].strip()
    except OSError:
        return ""
    return ""


def _memory_mb() -> str:
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith("MemTotal:"):
                kb = int(line.split()[1])
                return str(kb // 1024)
    except (OSError, ValueError, IndexError):
        return ""
    return ""


def _os_pretty_name() -> str:
    try:
        for line in Path("/etc/os-release").read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith("PRETTY_NAME="):
                return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return os.name
