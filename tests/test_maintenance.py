from pathlib import Path
from unittest.mock import patch

from djconnect_pi.maintenance import in_window, run_apt


def test_empty_window_is_allowed() -> None:
    assert in_window("")


def test_in_window_accepts_normal_window() -> None:
    with patch("djconnect_pi.maintenance.time.strftime", return_value="03:30"):
        assert in_window("03:00-04:00")


def test_in_window_rejects_normal_window() -> None:
    with patch("djconnect_pi.maintenance.time.strftime", return_value="05:00"):
        assert not in_window("03:00-04:00")


def test_in_window_accepts_overnight_window() -> None:
    with patch("djconnect_pi.maintenance.time.strftime", return_value="23:30"):
        assert in_window("23:00-04:00")
    with patch("djconnect_pi.maintenance.time.strftime", return_value="02:30"):
        assert in_window("23:00-04:00")


def test_run_apt_skips_outside_window() -> None:
    with patch("djconnect_pi.maintenance.in_window", return_value=False), patch("djconnect_pi.maintenance.subprocess.run") as run:
        assert run_apt(reboot=True, window="03:00-04:00") == "Outside maintenance window 03:00-04:00"
        run.assert_not_called()


def test_run_apt_updates_and_upgrades_without_reboot() -> None:
    calls: list[list[str]] = []

    with (
        patch("djconnect_pi.maintenance.in_window", return_value=True),
        patch("djconnect_pi.maintenance.Path.exists", return_value=False),
        patch("djconnect_pi.maintenance.subprocess.run", side_effect=lambda cmd, check: calls.append(cmd)),
    ):
        assert run_apt(reboot=True, window="") == "Upgrade complete"

    assert calls == [["apt-get", "update"], ["apt-get", "-y", "upgrade"]]


def test_run_apt_reboots_when_required() -> None:
    calls: list[list[str]] = []

    with (
        patch("djconnect_pi.maintenance.in_window", return_value=True),
        patch.object(Path, "exists", return_value=True),
        patch("djconnect_pi.maintenance.subprocess.run", side_effect=lambda cmd, check: calls.append(cmd)),
    ):
        assert run_apt(reboot=True, window="") == "Upgrade complete; reboot requested"

    assert calls[-1] == ["systemctl", "reboot"]
