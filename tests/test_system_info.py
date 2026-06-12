from __future__ import annotations

from djconnect_pi.system_info import log_raspberry_pi_system_info, raspberry_pi_system_info


def test_raspberry_pi_system_info_contains_expected_keys() -> None:
    info = raspberry_pi_system_info()

    assert {
        "hostname",
        "platform",
        "python",
        "machine",
        "model",
        "cpu",
        "memory_mb",
        "os_pretty_name",
    } == set(info)
    assert info["hostname"]
    assert info["platform"]
    assert info["python"]


def test_system_info_logging_includes_runtime_marker(caplog) -> None:
    caplog.set_level("INFO")

    log_raspberry_pi_system_info()

    assert "DJConnect Pi runtime system info" in caplog.text
    assert "hostname=" in caplog.text
