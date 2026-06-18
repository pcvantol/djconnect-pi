from __future__ import annotations

from importlib.resources import files
from pathlib import Path
import argparse
import json
import logging
import socket
import subprocess
import sys
from urllib.parse import urlparse

from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from .config import DEFAULT_CONFIG_PATH, load_config
from .logging_config import setup_logging

_LOGGER = logging.getLogger(__name__)


def _local_ip_from_config(local_url: str) -> str:
    host = urlparse(local_url).hostname if local_url else ""
    if host and host not in {"0.0.0.0", "127.0.0.1", "localhost"}:
        return host
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return str(sock.getsockname()[0])
    except OSError:
        return "rbpi-djconnect.local"


def wake_display() -> None:
    for command in (
        ["xset", "dpms", "force", "on"],
        ["xset", "s", "reset"],
    ):
        try:
            subprocess.run(command, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError as exc:
            _LOGGER.debug("Could not run display wake command %s: %s", command, exc)


class UpdateUiBackend(QObject):
    statusChanged = Signal()

    def __init__(self, status_file: Path, local_url: str) -> None:
        super().__init__()
        self.status_file = status_file
        self._device_address = _local_ip_from_config(local_url)
        self._ssh_command = f"ssh pi@{self._device_address}"
        self._mtime = 0.0
        self._title = "Update bezig"
        self._message = "DJConnect installeert een nieuwe versie. Laat de Pi aan staan."
        self._progress = 0
        self._current_version = ""
        self._target_version = ""
        self._logs = ""
        self._details_open = False
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self.refresh)
        self._timer.start()
        self.refresh()

    @Property(str, notify=statusChanged)
    def title(self) -> str:
        return self._title

    @Property(str, notify=statusChanged)
    def message(self) -> str:
        return self._message

    @Property(int, notify=statusChanged)
    def progress(self) -> int:
        return self._progress

    @Property(str, notify=statusChanged)
    def currentVersion(self) -> str:
        return self._current_version

    @Property(str, notify=statusChanged)
    def targetVersion(self) -> str:
        return self._target_version

    @Property(str, notify=statusChanged)
    def logs(self) -> str:
        return self._logs

    @Property(str, notify=statusChanged)
    def deviceAddress(self) -> str:
        return self._device_address

    @Property(str, notify=statusChanged)
    def sshCommand(self) -> str:
        return self._ssh_command

    @Property(bool, notify=statusChanged)
    def detailsOpen(self) -> bool:
        return self._details_open

    @Slot()
    def toggleDetails(self) -> None:
        self._details_open = not self._details_open
        self.statusChanged.emit()

    def refresh(self) -> None:
        if not self.status_file.exists():
            return
        try:
            stat = self.status_file.stat()
            if stat.st_mtime == self._mtime:
                return
            data = json.loads(self.status_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            _LOGGER.warning("Could not read updater status: %s", exc)
            return
        logs = data.get("logs")
        log_text = "\n".join(str(line) for line in logs[-100:]) if isinstance(logs, list) else str(logs or "")
        try:
            progress = int(data.get("progress", 0))
        except (TypeError, ValueError):
            progress = 0
        self._mtime = stat.st_mtime
        self._title = str(data.get("title") or "Update bezig")
        self._message = str(data.get("message") or "DJConnect installeert een nieuwe versie. Laat de Pi aan staan.")
        self._progress = max(0, min(100, progress))
        self._current_version = str(data.get("current_version") or "")
        self._target_version = str(data.get("target_version") or "")
        self._logs = log_text
        self.statusChanged.emit()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--windowed", action="store_true")
    parser.add_argument("--exit-after-ms", type=int, default=0)
    args = parser.parse_args()

    cfg = load_config(args.config)
    setup_logging(cfg.log_file, cfg.log_level)
    _LOGGER.info("Starting DJConnect updater UI")

    QQuickStyle.setStyle("Basic")
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    backend = UpdateUiBackend(Path(cfg.updater_status_file), cfg.local_url)
    engine.rootContext().setContextProperty("updater", backend)
    engine.rootContext().setContextProperty("startWindowed", args.windowed)
    engine.load(str(files("djconnect_pi.qml").joinpath("UpdateProgress.qml")))
    if not engine.rootObjects():
        raise SystemExit(1)
    QTimer.singleShot(0, wake_display)
    if args.exit_after_ms > 0:
        QTimer.singleShot(args.exit_after_ms, app.quit)
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
