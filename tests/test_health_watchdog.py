from unittest.mock import Mock

from djconnect_pi import health_watchdog


def test_healthy_watchdog_keeps_state_file_until_health_changes(tmp_path, monkeypatch):
    state = tmp_path / "watchdog-state.json"
    api_healthy = Mock(side_effect=[True, True, False, True, True])
    systemd_active = Mock(return_value=True)
    monkeypatch.setattr(health_watchdog, "api_healthy", api_healthy)
    monkeypatch.setattr(health_watchdog, "systemd_active", systemd_active)
    args = {"local_url": "http://127.0.0.1:18080", "state_file": state, "threshold": 5, "timeout": 4, "reboot": False}

    assert health_watchdog.run_check(**args) == "healthy"
    original = state.stat()
    assert health_watchdog.run_check(**args) == "healthy"
    assert state.stat().st_ino == original.st_ino
    assert state.stat().st_mtime_ns == original.st_mtime_ns

    assert health_watchdog.run_check(**args) == "unhealthy 1/5"
    assert health_watchdog.load_failures(state) == 1
    assert health_watchdog.run_check(**args) == "healthy"
    assert health_watchdog.load_failures(state) == 0
    recovered = state.stat()
    assert health_watchdog.run_check(**args) == "healthy"
    assert state.stat().st_ino == recovered.st_ino
    assert state.stat().st_mtime_ns == recovered.st_mtime_ns
    assert api_healthy.call_count == 5
    assert systemd_active.call_count == 10


def test_watchdog_still_requests_reboot_at_threshold(tmp_path, monkeypatch):
    state = tmp_path / "watchdog-state.json"
    monkeypatch.setattr(health_watchdog, "api_healthy", Mock(return_value=True))
    monkeypatch.setattr(health_watchdog, "systemd_active", lambda unit: unit == "djconnect-api.service")
    reboot = Mock()
    monkeypatch.setattr(health_watchdog.subprocess, "run", reboot)
    args = {"local_url": "http://127.0.0.1:18080", "state_file": state, "threshold": 5, "timeout": 4, "reboot": True}
    health_watchdog.save_failures(state, 3)

    assert health_watchdog.run_check(**args) == "unhealthy 4/5"
    reboot.assert_not_called()
    assert health_watchdog.run_check(**args) == "reboot requested"
    reboot.assert_called_once_with(["/usr/bin/systemctl", "reboot"], check=True, timeout=10)
    assert health_watchdog.load_failures(state) == 5
