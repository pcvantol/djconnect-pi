from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QCoreApplication

from djconnect_pi.app import DJConnectBackend


def ensure_app() -> QCoreApplication:
    return QCoreApplication.instance() or QCoreApplication([])


def test_backend_exposes_initial_config(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")

    assert backend.deviceId.startswith("djconnect-raspberry-pi-")
    assert backend.paired is False
    assert backend.busy is False
    assert backend.title == "Nothing playing"


def test_backend_set_ha_url_persists_value(tmp_path: Path) -> None:
    ensure_app()
    config_path = tmp_path / "config.json"
    backend = DJConnectBackend(config_path)

    backend.setHaUrl(" http://homeassistant.local:8123 ")
    reloaded = DJConnectBackend(config_path)

    assert backend.haUrl == "http://homeassistant.local:8123"
    assert reloaded.haUrl == "http://homeassistant.local:8123"


def test_backend_volume_clamps_and_dispatches_command(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    calls: list[tuple[str, dict[str, object]]] = []
    backend.command = lambda command, **payload: calls.append((command, payload))  # type: ignore[method-assign]

    backend.setVolume(125)

    assert backend.volume == 100
    assert calls == [("set_volume", {"value": 100})]


def test_backend_shuffle_and_repeat_dispatch_commands(tmp_path: Path) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    calls: list[tuple[str, dict[str, object]]] = []
    backend.command = lambda command, **payload: calls.append((command, payload))  # type: ignore[method-assign]

    backend.toggleShuffle()
    backend.cycleRepeat()
    backend.cycleRepeat()

    assert calls == [
        ("set_shuffle", {"value": True}),
        ("set_repeat", {"value": "context"}),
        ("set_repeat", {"value": "track"}),
    ]
