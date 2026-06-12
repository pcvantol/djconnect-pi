from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from importlib.resources import files
from pathlib import Path
import argparse
import json
import logging
import subprocess
import sys

from PySide6.QtCore import QCoreApplication, QObject, Property, QTimer, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from .config import CLIENT_TYPE, DEFAULT_CONFIG_PATH, Config, load_config, save_config
from .ha import DJConnectError, HAClient, Playback, ProtocolVersionMismatch
from .i18n import LANGUAGES, normalize_language, translate
from .logging_config import setup_logging
from .system_info import log_raspberry_pi_system_info

_LOGGER = logging.getLogger(__name__)


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
    localApiUrlChanged = Signal()
    djResponseChanged = Signal()
    toastChanged = Signal()
    versionMismatchChanged = Signal()
    logsChanged = Signal()
    demoModeChanged = Signal()
    screenTimeoutChanged = Signal()
    screenBrightnessChanged = Signal()
    updateChannelChanged = Signal()
    logFileChanged = Signal()
    languageChanged = Signal()
    translationsChanged = Signal()

    _playbackReady = Signal(object)
    _statusReady = Signal(str)
    _pairingReady = Signal(bool, str)
    _busyReady = Signal(bool)
    _versionMismatchReady = Signal(str, str)

    def __init__(self, config_path: Path) -> None:
        super().__init__()
        self.config_path = config_path
        self.cfg: Config = load_config(config_path)
        self.client = HAClient(self.cfg)
        self.playback = Playback()
        self._dj_response_text = ""
        self._dj_response_visible = False
        self._toast_text = ""
        self._toast_visible = False
        self._version_mismatch_visible = False
        self._version_mismatch_text = ""
        self._update_service_triggered = False
        self._toast_timer = QTimer(self)
        self._toast_timer.setInterval(2000)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(self.hideToast)
        self._logs_text = ""
        self._logs_visible = False
        self._demo_mode = False
        self._status_text = self.tr_key("paired" if self.cfg.paired else "not_paired")
        self._busy = False
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="djconnect")
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(5000)
        self._poll_timer.timeout.connect(self.refresh)
        self._poll_timer.start()
        self._event_timer = QTimer(self)
        self._event_timer.setInterval(1000)
        self._event_timer.timeout.connect(self._poll_local_events)
        self._event_timer.start()
        self._playbackReady.connect(self._apply_playback)
        self._statusReady.connect(self._set_status_text)
        self._pairingReady.connect(self._apply_pairing)
        self._busyReady.connect(self._set_busy)
        self._versionMismatchReady.connect(self._apply_version_mismatch)
        QTimer.singleShot(250, self.refresh)
        _LOGGER.info("DJConnect Pi client backend started for %s", self.cfg.device_id)

    @Property(str, notify=statusTextChanged)
    def statusText(self) -> str:
        return self._status_text

    @Property(str, notify=titleChanged)
    def title(self) -> str:
        return self.playback.title or self.tr_key("nothing_playing")

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

    @Property(bool, notify=demoModeChanged)
    def demoMode(self) -> bool:
        return self._demo_mode

    @Property(bool, notify=busyChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=settingsChanged)
    def haUrl(self) -> str:
        return self.cfg.ha_url

    @Property(str, notify=localApiUrlChanged)
    def localApiUrl(self) -> str:
        return self.cfg.local_url

    @Property(str, notify=settingsChanged)
    def deviceId(self) -> str:
        return self.cfg.device_id

    @Property(int, notify=screenTimeoutChanged)
    def screenTimeoutSeconds(self) -> int:
        return self.cfg.screen_timeout_seconds

    @Property(int, notify=screenBrightnessChanged)
    def screenBrightnessPercent(self) -> int:
        return self.cfg.screen_brightness_percent

    @Property(str, notify=updateChannelChanged)
    def updateChannel(self) -> str:
        return self.cfg.update_channel

    @Property(str, notify=logFileChanged)
    def logFile(self) -> str:
        return self.cfg.log_file

    @Property(str, notify=languageChanged)
    def language(self) -> str:
        return self.cfg.language

    @Property(str, notify=translationsChanged)
    def languageName(self) -> str:
        return LANGUAGES.get(self.cfg.language, LANGUAGES["nl"])

    @Property(str, notify=djResponseChanged)
    def djResponseText(self) -> str:
        return self._dj_response_text

    @Property(bool, notify=djResponseChanged)
    def djResponseVisible(self) -> bool:
        return self._dj_response_visible

    @Property(str, notify=toastChanged)
    def toastText(self) -> str:
        return self._toast_text

    @Property(bool, notify=toastChanged)
    def toastVisible(self) -> bool:
        return self._toast_visible

    @Property(bool, notify=versionMismatchChanged)
    def versionMismatchVisible(self) -> bool:
        return self._version_mismatch_visible

    @Property(str, notify=versionMismatchChanged)
    def versionMismatchText(self) -> str:
        return self._version_mismatch_text

    @Property(str, notify=logsChanged)
    def logsText(self) -> str:
        return self._logs_text

    @Property(bool, notify=logsChanged)
    def logsVisible(self) -> bool:
        return self._logs_visible

    @Slot(str, result=str)
    def t(self, key: str) -> str:
        return self.tr_key(key)

    def tr_key(self, key: str, **values: object) -> str:
        return translate(self.cfg.language, key, **values)

    @Slot(str)
    def setHaUrl(self, value: str) -> None:
        self.cfg.ha_url = value.strip()
        save_config(self.config_path, self.cfg)
        self.settingsChanged.emit()
        _LOGGER.info("User saved Home Assistant URL setting")
        self.showToast(self.tr_key("ha_url_saved"))
        self._set_status_text(self.tr_key("ha_url_saved"))

    @Slot(int)
    def setScreenTimeoutSeconds(self, value: int) -> None:
        value = max(0, int(value))
        if self.cfg.screen_timeout_seconds == value:
            return
        self.cfg.screen_timeout_seconds = value
        save_config(self.config_path, self.cfg)
        self.screenTimeoutChanged.emit()
        self.settingsChanged.emit()
        _LOGGER.info("User set screen timeout to %s seconds", value)
        self.showToast(self.tr_key("screen_timeout_saved"))
        self._set_status_text(self.tr_key("screen_timeout_saved"))

    @Slot(int)
    def setScreenBrightnessPercent(self, value: int) -> None:
        value = max(10, min(100, int(value)))
        if self.cfg.screen_brightness_percent == value:
            return
        self.cfg.screen_brightness_percent = value
        save_config(self.config_path, self.cfg)
        self.screenBrightnessChanged.emit()
        self.settingsChanged.emit()
        _LOGGER.info("User set app brightness to %s%%", value)
        self.showToast(self.tr_key("brightness_saved"))
        self._set_status_text(self.tr_key("brightness_saved"))

    @Slot(str)
    def setLanguage(self, value: str) -> None:
        language = normalize_language(value)
        if self.cfg.language == language:
            return
        self.cfg.language = language
        save_config(self.config_path, self.cfg)
        self.languageChanged.emit()
        self.translationsChanged.emit()
        self.settingsChanged.emit()
        self.titleChanged.emit()
        _LOGGER.info("User changed language to %s", language)
        self.showToast(self.tr_key("language_saved"))
        self._set_status_text(self.tr_key("language_saved"))

    @Slot(str)
    def setUpdateChannel(self, value: str) -> None:
        channel = value.strip().lower()
        if channel not in {"stable", "beta"}:
            channel = "stable"
        if self.cfg.update_channel == channel:
            return
        self.cfg.update_channel = channel
        save_config(self.config_path, self.cfg)
        self.updateChannelChanged.emit()
        self.settingsChanged.emit()
        _LOGGER.info("User changed update channel to %s", channel)
        self.showToast(self.tr_key("update_channel", channel=channel))
        self._set_status_text(self.tr_key("update_channel", channel=channel))

    @Slot(str)
    def pair(self, pair_code: str) -> None:
        if self._demo_mode:
            self.exitDemoMode()
        code = pair_code.strip()
        if not code:
            self._set_status_text(self.tr_key("enter_pairing_code"))
            self.showToast(self.tr_key("enter_pairing_code"))
            return
        _LOGGER.info("User started pairing from touch UI")
        self.showToast(self.tr_key("pairing"))
        self._run(self.tr_key("pairing"), lambda: self._pair_worker(code))

    @Slot()
    def refresh(self) -> None:
        if self._demo_mode:
            return
        if self._busy:
            return
        if not self.paired and not self.cfg.ha_url:
            self._set_status_text(self.tr_key("ready_to_pair"))
            return
        self._run(self.tr_key("refreshing"), self._refresh_worker)

    @Slot()
    def togglePlay(self) -> None:
        if self._demo_mode:
            self.playback.is_playing = not self.playback.is_playing
            self.playingChanged.emit()
            _LOGGER.info("User toggled demo playback to playing=%s", self.playback.is_playing)
            self.showToast(self.tr_key("pause") if self.playback.is_playing else self.tr_key("play"))
            return
        _LOGGER.info("User requested playback toggle")
        self.showToast(self.tr_key("pause") if self.playback.is_playing else self.tr_key("play"))
        self.command("pause" if self.playback.is_playing else "play")

    @Slot()
    def previous(self) -> None:
        if self._demo_mode:
            self._apply_demo_track("Blue Monday", "New Order")
            _LOGGER.info("User selected previous demo track")
            self.showToast(self.tr_key("previous"))
            return
        _LOGGER.info("User requested previous track")
        self.showToast(self.tr_key("previous"))
        self.command("previous")

    @Slot()
    def next(self) -> None:
        if self._demo_mode:
            self._apply_demo_track("Around the World", "Daft Punk")
            _LOGGER.info("User selected next demo track")
            self.showToast(self.tr_key("next"))
            return
        _LOGGER.info("User requested next track")
        self.showToast(self.tr_key("next"))
        self.command("next")

    @Slot(int)
    def setVolume(self, value: int) -> None:
        value = max(0, min(100, int(value)))
        if value == self.playback.volume:
            return
        self.playback.volume = value
        self.volumeChanged.emit()
        _LOGGER.info("User set volume to %s", value)
        self.showToast(f"{self.tr_key('vol')} {value}")
        if self._demo_mode:
            return
        self.command("set_volume", value=value)

    @Slot()
    def toggleShuffle(self) -> None:
        self.playback.shuffle = not self.playback.shuffle
        self.shuffleChanged.emit()
        _LOGGER.info("User toggled shuffle to %s", self.playback.shuffle)
        self.showToast(self.tr_key("shuffle"))
        if self._demo_mode:
            return
        self.command("set_shuffle", value=self.playback.shuffle)

    @Slot()
    def cycleRepeat(self) -> None:
        next_value = {"off": "context", "context": "track", "track": "off"}.get(self.playback.repeat, "off")
        self.playback.repeat = next_value
        self.repeatChanged.emit()
        _LOGGER.info("User changed repeat mode to %s", next_value)
        self.showToast(self.tr_key("repeat"))
        if self._demo_mode:
            return
        self.command("set_repeat", value=next_value)

    @Slot()
    def enterDemoMode(self) -> None:
        if self.paired:
            return
        self._demo_mode = True
        self.demoModeChanged.emit()
        self._apply_demo_track("Sweet Dreams", "Eurythmics")
        _LOGGER.info("User entered local demo mode")
        self.showToast(self.tr_key("demo_active"))
        self._set_status_text(self.tr_key("demo_active"))

    @Slot()
    def exitDemoMode(self) -> None:
        if not self._demo_mode:
            return
        self._demo_mode = False
        self.demoModeChanged.emit()
        self.playback = Playback()
        self.titleChanged.emit()
        self.artistChanged.emit()
        self.imageUrlChanged.emit()
        self.playingChanged.emit()
        self.volumeChanged.emit()
        self.shuffleChanged.emit()
        self.repeatChanged.emit()
        _LOGGER.info("User exited local demo mode")
        self.showToast(self.tr_key("exit_demo"))
        self._set_status_text(self.tr_key("ready_to_pair"))

    @Slot()
    def quitApp(self) -> None:
        _LOGGER.info("Quit requested from touch UI")
        app = QCoreApplication.instance()
        if app is not None:
            app.quit()

    @Slot()
    def clearDjResponse(self) -> None:
        if not self._dj_response_visible and not self._dj_response_text:
            return
        self._dj_response_text = ""
        self._dj_response_visible = False
        self.djResponseChanged.emit()

    @Slot()
    def resetPairing(self) -> None:
        _LOGGER.info("User requested pairing reset from touch UI")
        self._forget_pairing()
        self.showToast(self.tr_key("ready_to_pair"))
        self._set_status_text(self.tr_key("ready_to_pair"))

    @Slot()
    def rebootDevice(self) -> None:
        self._set_status_text(self.tr_key("rebooting"))
        try:
            subprocess.Popen(["systemctl", "reboot"])
        except Exception as exc:
            _LOGGER.warning("Reboot request failed: %s", exc)
            self._set_status_text(self.tr_key("reboot_failed", error=exc))

    @Slot()
    def showLogs(self) -> None:
        _LOGGER.info("User opened logs view")
        self.showToast(self.tr_key("logs"))
        path = Path(self.cfg.log_file)
        try:
            if path.exists():
                data = path.read_text(encoding="utf-8", errors="replace")
                self._logs_text = data[-12000:] if len(data) > 12000 else data
            else:
                self._logs_text = self.tr_key("logs_missing")
        except Exception as exc:
            self._logs_text = self.tr_key("logs_failed", error=exc)
        self._logs_visible = True
        self.logsChanged.emit()

    @Slot()
    def hideLogs(self) -> None:
        self._logs_visible = False
        self.logsChanged.emit()

    @Slot(str)
    def showToast(self, text: str) -> None:
        text = text.strip()
        if not text:
            return
        self._toast_text = text
        self._toast_visible = True
        self.toastChanged.emit()
        self._toast_timer.start()

    @Slot()
    def hideToast(self) -> None:
        if not self._toast_visible and not self._toast_text:
            return
        self._toast_visible = False
        self._toast_text = ""
        self.toastChanged.emit()

    def command(self, command: str, **payload: object) -> None:
        if self._demo_mode:
            return
        self._run(command, lambda: self._command_worker(command, **payload))

    def _pair_worker(self, code: str) -> None:
        _LOGGER.info("Pairing DJConnect Pi client")
        self.client.pair(code)
        save_config(self.config_path, self.cfg)
        self._pairingReady.emit(True, self.tr_key("paired"))

    def _refresh_worker(self) -> None:
        _LOGGER.debug("Refreshing playback status")
        data = self.client.command("status") if self.paired else self.client.status()
        playback = self.client.playback_from_status(data)
        if self.paired:
            self.client.status(playback)
        self._playbackReady.emit(playback)

    def _command_worker(self, command: str, **payload: object) -> None:
        _LOGGER.info("Sending playback command: %s", command)
        data = self.client.command(command, **payload)
        self._playbackReady.emit(self.client.playback_from_status(data))

    def _show_dj_response(self, payload: dict[str, object]) -> dict[str, object]:
        text = str(payload.get("dj_text") or payload.get("text") or payload.get("message") or "").strip()
        if not text:
            return {"success": False, "error": "missing_text"}
        self._dj_response_text = text
        self._dj_response_visible = True
        self.djResponseChanged.emit()
        return {
            "success": True,
            "displayed": True,
            "audio_played": False,
            "text": text,
        }

    def _forget_pairing(self) -> None:
        if self._demo_mode:
            self.exitDemoMode()
        self.cfg.device_token = ""
        self.cfg.paired = False
        save_config(self.config_path, self.cfg)
        self.pairedChanged.emit()
        self.settingsChanged.emit()

    def _apply_demo_track(self, title: str, artist: str) -> None:
        self.playback.title = title
        self.playback.artist = artist
        self.playback.image_url = ""
        self.playback.is_playing = True
        self.titleChanged.emit()
        self.artistChanged.emit()
        self.imageUrlChanged.emit()
        self.playingChanged.emit()

    def _run(self, label: str, worker) -> None:
        self._set_busy(True)
        self._set_status_text(label)

        def execute() -> None:
            try:
                worker()
            except ProtocolVersionMismatch as exc:
                _LOGGER.warning("%s blocked by version mismatch: %s", label, exc)
                self._versionMismatchReady.emit(exc.client_version, exc.ha_version)
                self._statusReady.emit(str(exc))
            except DJConnectError as exc:
                _LOGGER.warning("%s failed: %s", label, exc)
                self._statusReady.emit(str(exc))
            except Exception as exc:
                _LOGGER.exception("%s failed unexpectedly", label)
                self._statusReady.emit(self.tr_key("offline", error=exc))
            finally:
                self._busyReady.emit(False)

        self._executor.submit(execute)

    @Slot(object)
    def _apply_playback(self, playback: Playback) -> None:
        if self._version_mismatch_visible:
            self._version_mismatch_visible = False
            self._version_mismatch_text = ""
            self.versionMismatchChanged.emit()
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
        self._set_status_text(self.tr_key("connected" if self.paired else "ready_to_pair"))

    @Slot(bool, str)
    def _apply_pairing(self, paired: bool, message: str) -> None:
        if self._version_mismatch_visible:
            self._version_mismatch_visible = False
            self._version_mismatch_text = ""
            self.versionMismatchChanged.emit()
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

    @Slot(str, str)
    def _apply_version_mismatch(self, client_version: str, ha_version: str) -> None:
        self._version_mismatch_text = self.tr_key(
            "version_mismatch_message",
            client=client_version,
            ha=ha_version,
            required=f"{client_version.rsplit('.', 1)[0]}.x",
        )
        self._version_mismatch_visible = True
        self.versionMismatchChanged.emit()
        self.showToast(self.tr_key("version_mismatch_title"))
        self._trigger_update_service()

    def _trigger_update_service(self) -> None:
        if self._update_service_triggered:
            return
        self._update_service_triggered = True
        try:
            _LOGGER.info("Triggering djconnect-updater.service after version mismatch")
            subprocess.Popen(["systemctl", "start", "djconnect-updater.service"])
        except Exception as exc:
            _LOGGER.warning("Could not trigger updater service after version mismatch: %s", exc)

    @Slot()
    def shutdown(self) -> None:
        _LOGGER.info("Stopping DJConnect Pi client backend")
        self._poll_timer.stop()
        self._event_timer.stop()
        self._executor.shutdown(wait=False, cancel_futures=True)

    @Slot()
    def _poll_local_events(self) -> None:
        path = Path(self.cfg.dj_response_file)
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            path.unlink(missing_ok=True)
        except (OSError, json.JSONDecodeError) as exc:
            _LOGGER.warning("Failed to read local DJ response event file: %s", exc)
            return
        if isinstance(data, dict):
            _LOGGER.info("Displaying DJ response from local API daemon event")
            self._show_dj_response(data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--ha-url", default="")
    parser.add_argument("--windowed", action="store_true")
    parser.add_argument("--exit-after-ms", type=int, default=0)
    parser.add_argument("--log-file", default="")
    parser.add_argument("--log-level", default="")
    args = parser.parse_args()

    cfg = load_config(args.config)
    if args.ha_url:
        cfg.ha_url = args.ha_url
        save_config(args.config, cfg)
    if args.log_file:
        cfg.log_file = args.log_file
        save_config(args.config, cfg)
    if args.log_level:
        cfg.log_level = args.log_level.upper()
        save_config(args.config, cfg)

    setup_logging(cfg.log_file, cfg.log_level)
    _LOGGER.info("Starting DJConnect Pi client")
    log_raspberry_pi_system_info()

    QQuickStyle.setStyle("Basic")
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    backend = DJConnectBackend(args.config)
    app.aboutToQuit.connect(backend.shutdown)
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
