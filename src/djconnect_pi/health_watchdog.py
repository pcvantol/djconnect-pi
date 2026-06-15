from __future__ import annotations

from pathlib import Path
import argparse
import json
import logging
import subprocess
import sys

import requests

from .config import DEFAULT_CONFIG_PATH, load_config
from .logging_config import setup_logging

_LOGGER = logging.getLogger(__name__)
DEFAULT_STATE_FILE = Path("/opt/djconnect/config/watchdog-state.json")


def api_healthy(local_url: str, timeout: float) -> bool:
    if not local_url:
        return False
    response = requests.get(f"{local_url.rstrip('/')}/api/device/info", timeout=timeout)
    if response.status_code != 200:
        _LOGGER.warning("Watchdog API health returned HTTP %s", response.status_code)
        return False
    data = response.json()
    return bool(data.get("success") and data.get("client_type") == "raspberry_pi")


def systemd_active(service_name: str) -> bool:
    result = subprocess.run(
        ["systemctl", "is-active", "--quiet", service_name],
        check=False,
        timeout=5,
    )
    return result.returncode == 0


def load_failures(path: Path) -> int:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    return max(0, int(data.get("failures") or 0)) if isinstance(data, dict) else 0


def save_failures(path: Path, failures: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(json.dumps({"failures": max(0, failures)}, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def run_check(
    *,
    config_path: Path,
    state_file: Path,
    threshold: int,
    timeout: float,
    reboot: bool,
) -> str:
    cfg = load_config(config_path)
    checks = {
        "api": False,
        "api_service": systemd_active("djconnect-api.service"),
        "client_service": systemd_active("djconnect-client.service"),
    }
    try:
        checks["api"] = api_healthy(cfg.local_url, timeout)
    except Exception as exc:
        _LOGGER.warning("Watchdog API health failed: %s", exc)

    healthy = all(checks.values())
    if healthy:
        save_failures(state_file, 0)
        return "healthy"

    failures = load_failures(state_file) + 1
    save_failures(state_file, failures)
    _LOGGER.warning("DJConnect watchdog failure %s/%s: %s", failures, threshold, checks)
    if failures < threshold:
        return f"unhealthy {failures}/{threshold}"

    _LOGGER.error("DJConnect watchdog threshold reached; reboot=%s", reboot)
    if reboot:
        subprocess.run(["/usr/bin/systemctl", "reboot"], check=True, timeout=10)
    return "reboot requested"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--state-file", type=Path, default=DEFAULT_STATE_FILE)
    parser.add_argument("--threshold", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=4.0)
    parser.add_argument("--no-reboot", action="store_true")
    parser.add_argument("--log-file", default="")
    args = parser.parse_args()

    cfg = load_config(args.config)
    setup_logging(args.log_file or cfg.log_file, cfg.log_level)
    result = run_check(
        config_path=args.config,
        state_file=args.state_file,
        threshold=max(1, args.threshold),
        timeout=max(0.5, args.timeout),
        reboot=not args.no_reboot,
    )
    print(result)
    raise SystemExit(0)


if __name__ == "__main__":
    main()
