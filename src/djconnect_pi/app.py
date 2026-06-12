from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from importlib.resources import files
from pathlib import Path
import argparse
import sys

from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from .config import DEFAULT_CONFIG_PATH, Config, load_config, save_config
from .ha import DJConnectError, HAClient, Playback


class DJConnectBackend(QObject):
    statusTextChanged = Signal()
    titleChanged = Signal()
    artistChanged = Signal()
    imageUrlChanged = Signal()
    playingChanged = Signal()
    volumeChanged = Signal()
    shuffleChanged = Signal()
    repeatChanged = Signal()
    pairedChanged = Signal()
    busyChanged = Signal()
    settingsChanged = Signal()

    _playbackReady = Signal(object)
    _statusReady = Signal(str)
    _pairingReady = Signal(bool, str)
    _busyReady = Signal(bool)

    def __init__(self, config_path: Path) -> None:
        super().__init__()
        self.config_path = config_path
        self.cfg: Config = load_config(config_path)
        self.client = HAClient(self.cfg)
        self.playback = Playback()
        self._status_text = "Paired" if self.cfg.paired else "Not paired"
        self._busy = False
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="djconnect")
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(5000)
        self._poll_timer.timeout.connect(self.refresh)
        self._poll_timer.start()
        self._playbackReady.connect(self._apply_playback)
        self._statusReady.connect(self._set_status_text)
        self._pairingReady.connect(self._apply_pairing)
        self._busyReady.connect(self._set_busy)
        QTimer.singleShot(250, self.refresh)

    @Property(str, notify=statusTextChanged)
    def statusText(self) -> str:
        return self._status_text

    @Property(str, notify=titleChanged)
    def title(self) -> str:
        return self.playback.title

    @Property(str, notify=artistChanged)
    def artist(self) -> str:
        return self.playback.artist

    @Property(str, notify=imageUrlChanged)
    def imageUrl(self) -> str:
        return self.playback.image_url

    @Property(bool, notify=playingChanged)
    def playing(self) -> bool:
        return self.playback.is_playing

    @Property(int, notify=volumeChanged)
    def volume(self) -> int:
        return self.playback.volume

    @Property(bool, notify=shuffleChanged)
    def shuffle(self) -> bool:
        return self.playback.shuffle

    @Property(str, notify=repeatChanged)
    def repeat(self) -> str:
        return self.playback.repeat

    @Property(bool, notify=pairedChanged)
    def paired(self) -> bool:
        return bool(self.cfg.paired and self.cfg.device_token)

    @Property(bool, notify=busyChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=settingsChanged)
    def haUrl(self) -> str:
        return self.cfg.ha_url

    @Property(str, notify=settingsChanged)
    def deviceId(self) -> str:
        return self.cfg.device_id

    @Slot(str)
    def setHaUrl(self, value: str) -> None:
        self.cfg.ha_url = value.strip()
        save_config(self.config_path, self.cfg)
        self.settingsChanged.emit()
        self._set_status_text("Home Assistant URL saved")

    @Slot(str)
    def pair(self, pair_code: str) -> None:
        code = pair_code.strip()
        if not code:
            self._set_status_text("Enter pairing code")
            return
        self._run("Pairing", lambda: self._pair_worker(code))

    @Slot()
    def refresh(self) -> None:
        if self._busy:
            return
        self._run("Refreshing", self._refresh_worker)

    @Slot()
    def togglePlay(self) -> None:
        self.command("pause" if self.playback.is_playing else "play")

    @Slot()
    def previous(self) -> None:
        self.command("previous")

    @Slot()
    def next(self) -> None:
        self.command("next")

    @Slot(int)
    def setVolume(self, value: int) -> None:
        value = max(0, min(100, int(value)))
        if value == self.playback.volume:
            return
        self.playback.volume = value
        self.volumeChanged.emit()
        self.command("set_volume", value=value)

    @Slot()
    def toggleShuffle(self) -> None:
        self.playback.shuffle = not self.playback.shuffle
        self.shuffleChanged.emit()
        self.command("set_shuffle", value=self.playback.shuffle)

    @Slot()
    def cycleRepeat(self) -> None:
        next_value = {"off": "context", "context": "track", "track": "off"}.get(self.playback.repeat, "off")
        self.playback.repeat = next_value
        self.repeatChanged.emit()
        self.command("set_repeat", value=next_value)

    def command(self, command: str, **payload: object) -> None:
        self._run(command, lambda: self._command_worker(command, **payload))

    def _pair_worker(self, code: str) -> None:
        self.client.pair(code)
        save_config(self.config_path, self.cfg)
        self._pairingReady.emit(True, "Paired")

    def _refresh_worker(self) -> None:
        data = self.client.command("status") if self.paired else self.client.status()
        playback = self.client.playback_from_status(data)
        if self.paired:
            self.client.status(playback)
        self._playbackReady.emit(playback)

    def _command_worker(self, command: str, **payload: object) -> None:
        data = self.client.command(command, **payload)
        self._playbackReady.emit(self.client.playback_from_status(data))

    def _run(self, label: str, worker) -> None:
        self._set_busy(True)
        self._set_status_text(label)

        def execute() -> None:
            try:
                worker()
            except DJConnectError as exc:
                self._statusReady.emit(str(exc))
            except Exception as exc:
                self._statusReady.emit(f"Offline: {exc}")
            finally:
                self._busyReady.emit(False)

        self._executor.submit(execute)

    @Slot(object)
    def _apply_playback(self, playback: Playback) -> None:
        old = self.playback
        self.playback = playback
        if old.title != playback.title:
            self.titleChanged.emit()
        if old.artist != playback.artist:
            self.artistChanged.emit()
        if old.image_url != playback.image_url:
            self.imageUrlChanged.emit()
        if old.is_playing != playback.is_playing:
            self.playingChanged.emit()
        if old.volume != playback.volume:
            self.volumeChanged.emit()
        if old.shuffle != playback.shuffle:
            self.shuffleChanged.emit()
        if old.repeat != playback.repeat:
            self.repeatChanged.emit()
        self._set_status_text("Connected" if self.paired else "Ready to pair")

    @Slot(bool, str)
    def _apply_pairing(self, paired: bool, message: str) -> None:
        if paired:
            self.pairedChanged.emit()
            self.settingsChanged.emit()
        self._set_status_text(message)
        self.refresh()

    @Slot(str)
    def _set_status_text(self, value: str) -> None:
        if self._status_text == value:
            return
        self._status_text = value
        self.statusTextChanged.emit()

    def _set_busy(self, value: bool) -> None:
        if self._busy == value:
            return
        self._busy = value
        self.busyChanged.emit()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--ha-url", default="")
    parser.add_argument("--windowed", action="store_true")
    parser.add_argument("--exit-after-ms", type=int, default=0)
    args = parser.parse_args()

    cfg = load_config(args.config)
    if args.ha_url:
        cfg.ha_url = args.ha_url
        save_config(args.config, cfg)

    QQuickStyle.setStyle("Basic")
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    backend = DJConnectBackend(args.config)
    engine.rootContext().setContextProperty("djconnect", backend)
    engine.rootContext().setContextProperty("startWindowed", args.windowed)
    qml_path = files("djconnect_pi.qml").joinpath("Main.qml")
    engine.load(str(qml_path))
    if not engine.rootObjects():
        raise SystemExit(1)
    if args.exit_after_ms > 0:
        QTimer.singleShot(args.exit_after_ms, app.quit)
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
