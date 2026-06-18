from __future__ import annotations

from importlib.resources import files
from pathlib import Path
import argparse
import json
import logging
import sys

from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from .config import DEFAULT_CONFIG_PATH, load_config
from .logging_config import setup_logging

_LOGGER = logging.getLogger(__name__)


class UpdateUiBackend(QObject):
    statusChanged = Signal()

    def __init__(self, status_file: Path) -> None:
        super().__init__()
        self.status_file = status_file
        self._mtime = 0.0
        self._title = "Update bezig"
        self._message = "DJConnect installeert een nieuwe versie. Laat de Pi aan staan."
        self._progress = 0
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
    def logs(self) -> str:
        return self._logs

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
    backend = UpdateUiBackend(Path(cfg.updater_status_file))
    engine.rootContext().setContextProperty("updater", backend)
    engine.rootContext().setContextProperty("startWindowed", args.windowed)
    engine.load(str(files("djconnect_pi.qml").joinpath("UpdateProgress.qml")))
    if not engine.rootObjects():
        raise SystemExit(1)
    if args.exit_after_ms > 0:
        QTimer.singleShot(args.exit_after_ms, app.quit)
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
