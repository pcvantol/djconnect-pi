from __future__ import annotations

from pathlib import Path
import random
from unittest.mock import Mock, patch

from PySide6.QtCore import QCoreApplication

from djconnect_pi.app import DJConnectBackend


def ensure_app() -> QCoreApplication:
    return QCoreApplication.instance() or QCoreApplication([])


def test_backend_monkey_touch_actions_do_not_break_state(tmp_path: Path, monkeypatch) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")
    dispatched: list[tuple[str, dict[str, object]]] = []
    rng = random.Random(3101)

    backend.command = lambda command, **payload: dispatched.append((command, payload))  # type: ignore[method-assign]

    actions = [
        lambda: backend.setVolume(rng.randint(-50, 150)),
        lambda: backend.toggleShuffle(),
        lambda: backend.cycleRepeat(),
        lambda: backend.setScreenTimeoutSeconds(rng.randint(-120, 4200)),
        lambda: backend.setScreenBrightnessPercent(rng.randint(-25, 140)),
        lambda: backend.setUpdateChannel(rng.choice(["stable", "beta", "nightly", ""])),
        lambda: backend.setLanguage(rng.choice(["nl", "en", "de", ""])),
        lambda: backend.setHaUrl(rng.choice(["http://homeassistant.local:8123", " http://ha.local:8123 "])),
        lambda: backend._show_dj_response({"text": f"bericht {rng.randint(1, 999)}"}),
        lambda: backend.clearDjResponse(),
        lambda: backend.showLogs(),
        lambda: backend.hideLogs(),
        lambda: backend.resetPairing(),
        lambda: backend.enterDemoMode(),
        lambda: backend.exitDemoMode(),
    ]

    for _ in range(250):
        rng.choice(actions)()
        assert 0 <= backend.volume <= 100
        assert 0 <= backend.screenTimeoutSeconds
        assert 10 <= backend.screenBrightnessPercent <= 100
        assert backend.updateChannel in {"stable", "beta"}
        assert backend.language in {"en", "nl", "de", "fr", "es"}
        assert backend.repeat in {"off", "context", "track"}
        assert isinstance(backend.statusText, str)
        assert isinstance(backend.title, str)
        assert isinstance(backend.demoMode, bool)

    assert dispatched


def test_backend_monkey_reboot_and_quit_are_safe(tmp_path: Path, monkeypatch) -> None:
    ensure_app()
    backend = DJConnectBackend(tmp_path / "config.json")

    with patch("djconnect_pi.app.subprocess.run") as run:
        backend.rebootDevice()
    run.assert_called_once_with(
        ["sudo", "-n", "/usr/bin/systemctl", "reboot"],
        check=True,
        timeout=5,
        capture_output=True,
        text=True,
    )

    app = Mock()
    with patch("djconnect_pi.app.QCoreApplication.instance", return_value=app):
        backend.quitApp()
    app.quit.assert_called_once_with()
