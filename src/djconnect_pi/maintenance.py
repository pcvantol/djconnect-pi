from __future__ import annotations

from pathlib import Path
import argparse
import subprocess
import time


def in_window(window: str) -> bool:
    if not window:
        return True
    start, end = window.split("-", 1)
    now = time.strftime("%H:%M")
    return start <= now <= end if start <= end else now >= start or now <= end


def run_apt(reboot: bool, window: str) -> str:
    if not in_window(window):
        return f"Outside maintenance window {window}"
    subprocess.run(["apt-get", "update"], check=True)
    subprocess.run(["apt-get", "-y", "upgrade"], check=True)
    if reboot and Path("/var/run/reboot-required").exists():
        subprocess.run(["systemctl", "reboot"], check=True)
        return "Upgrade complete; reboot requested"
    return "Upgrade complete"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--maintenance-window", default="03:00-04:00")
    parser.add_argument("--reboot", action="store_true")
    args = parser.parse_args()
    print(run_apt(args.reboot, args.maintenance_window))


if __name__ == "__main__":
    main()

