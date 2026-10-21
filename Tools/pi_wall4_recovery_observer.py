"""Fixed read-only privileged observer; opaque evidence stays in private artifacts."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import socket
import stat
import sys


def need(value):
    if not value:raise ValueError("RECOVERY_OBSERVATION_INVALID")


def read(path, maximum):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        meta = os.fstat(stream.fileno())
        need(stat.S_ISREG(meta.st_mode) and meta.st_size <= maximum and not stat.S_IMODE(meta.st_mode) & 0o022)
        raw = stream.read(maximum+1)
    need(len(raw) <= maximum)
    return raw


def pairs(items):
    result = {}
    for key, value in items:
        need(key not in result);result[key] = value
    return result


def nonfinite(_):
    raise ValueError("RECOVERY_OBSERVATION_INVALID")


def finite_float(text):
    value = float(text);need(math.isfinite(value))
    return value


def observe(expected_boot):
    need(os.geteuid() == 0 and socket.gethostname() == "rbpi-djconnect")
    need(isinstance(expected_boot, str) and re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", expected_boot))
    need(read("/proc/sys/kernel/random/boot_id", 64).decode("ascii").strip() == expected_boot)
    need(read("/etc/djconnect-pi/device-profile", 64) == b"pi-zero-2w-arm64\n")
    raw = read("/opt/djconnect/config/client.json", 2097152)
    config = json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite, parse_float=finite_float)
    need(isinstance(config, dict) and config.get("device_id") == "djconnect-raspberry-pi-D83ADD41F167")
    digest = hashlib.sha256(json.dumps(config, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
    need(read("/proc/sys/kernel/random/boot_id", 64).decode("ascii").strip() == expected_boot)
    return {"boot_id": expected_boot, "configuration_sha256": digest}


if __name__ == "__main__":
    try:
        need(len(sys.argv) == 2)
        print(json.dumps(observe(sys.argv[1])), flush=True)
    except (OSError, ValueError, TypeError, RecursionError):
        print("RECOVERY_OBSERVATION_INVALID", file=sys.stderr)
        raise SystemExit(1) from None
