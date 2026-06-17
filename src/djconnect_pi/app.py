from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from importlib.resources import files
from pathlib import Path
import argparse
import hashlib
import json
import logging
import re
import subprocess
import sys
import time
from urllib.parse import urlparse

from PySide6.QtCore import QByteArray, QBuffer, QCoreApplication, QIODevice, QObject, Property, QTimer, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
import requests

from .config import CLIENT_TYPE, DEFAULT_CONFIG_PATH, DEFAULT_LOG_PATH, Config, load_config, save_config
from .ha import AuthenticationError, BackendUnavailable, DJConnectError, HAClient, Playback, ProtocolVersionMismatch
from .i18n import LANGUAGES, normalize_language, translate
from .logging_config import setup_logging
from .system_info import log_raspberry_pi_system_info

_LOGGER = logging.getLogger(__name__)
LOG_LINE_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}\s+(?P<time>\d{2}:\d{2}:\d{2})(?:[,.]\d+)?\s+(?P<level>[A-Z]+)\s+(?P<rest>.*)$"
)
LOG_LEVEL_SHORT = {"DEBUG": "DBG", "INFO": "INF", "WARNING": "WRN", "ERROR": "ERR", "CRITICAL": "ERR"}
LOG_DISPLAY_MAX_BYTES = 160_000
GAME_SOUND_SAMPLE_RATE = 16_000
MEDIA_ARTWORK_CACHE_LIMIT = 12


class DJConnectBackend(QObject):
    statusTextChanged = Signal()
    backendAvailableChanged = Signal()
    titleChanged = Signal()
    artistChanged = Signal()
    imageUrlChanged = Signal()
    playingChanged = Signal()
    volumeChanged = Signal()
    shuffleChanged = Signal()
    repeatChanged = Signal()
    outputDeviceChanged = Signal()
    progressChanged = Signal()
    pairedChanged = Signal()
    busyChanged = Signal()
    settingsChanged = Signal()
    localApiUrlChanged = Signal()
    pairingCodeChanged = Signal()
    pairingSuccessChanged = Signal()
    djResponseChanged = Signal()
    toastChanged = Signal()
    versionMismatchChanged = Signal()
    logsChanged = Signal()
    mediaListsChanged = Signal()
    demoModeChanged = Signal()
    screenTimeoutChanged = Signal()
    screenBrightnessChanged = Signal()
    updateChannelChanged = Signal()
    logFileChanged = Signal()
    logLevelChanged = Signal()
    languageChanged = Signal()
    translationsChanged = Signal()
    wakeScreenRequested = Signal()
    temporaryWakeRequested = Signal(int, bool)
    screenshotRequested = Signal()
    debugScreenRequested = Signal(str)

    _playbackReady = Signal(object)
    _statusReady = Signal(str)
    _pairingReady = Signal(bool, str)
    _busyReady = Signal(bool)
    _versionMismatchReady = Signal(str, str)
    _mediaListReady = Signal(str, object)
    _outputDeviceRejected = Signal(str, str)
    _backendAvailableReady = Signal(bool)
    _toastReady = Signal(str, int)

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
        self._translation_version = 0
        self._version_mismatch_visible = False
        self._version_mismatch_text = ""
        self._pairing_success_visible = False
        self._update_service_triggered = False
        self._toast_timer = QTimer(self)
        self._toast_timer.setInterval(2000)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(self.hideToast)
        self._logs_text = ""
        self._logs_visible = False
        self._demo_mode = False
        self._queue_items: list[dict[str, object]] = []
        self._playlist_items: list[dict[str, object]] = []
        self._media_loads_in_flight: set[str] = set()
        self._media_artwork_cache_in_flight: set[str] = set()
        self._pending_output_device = ""
        self._pending_output_until = 0.0
        self._game_sound_objects: list[tuple[object, QBuffer]] = []
        self._status_text = self.tr_key("paired" if self.cfg.paired else "not_paired")
        self._backend_available = True
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
        self._mediaListReady.connect(self._apply_media_list)
        self._outputDeviceRejected.connect(self._apply_output_device_rejection)
        self._backendAvailableReady.connect(self._set_backend_available)
        self._toastReady.connect(self._show_toast)
        QTimer.singleShot(250, self.refresh)
        _LOGGER.info("DJConnect Pi client backend started for %s", self.cfg.device_id)

    @Property(str, notify=statusTextChanged)
    def statusText(self) -> str:
        return self._status_text

    @Property(bool, notify=backendAvailableChanged)
    def backendAvailable(self) -> bool:
        return self._backend_available

    @Property(str, notify=titleChanged)
    def title(self) -> str:
        return self.playback.title or self.tr_key("nothing_playing")

    @Property(str, notify=artistChanged)
    def artist(self) -> str:
        return self.playback.artist

    @Property(str, notify=imageUrlChanged)
    def imageUrl(self) -> str:
        return self.playback.image_url

    @Property("QVariantList", notify=mediaListsChanged)
    def queueItems(self) -> list[dict[str, object]]:
        return self._queue_items

    @Property("QVariantList", notify=mediaListsChanged)
    def playlistItems(self) -> list[dict[str, object]]:
        return self._playlist_items

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

    @Property(int, notify=progressChanged)
    def positionSeconds(self) -> int:
        return self.playback.position_seconds

    @Property(int, notify=progressChanged)
    def durationSeconds(self) -> int:
        return self.playback.duration_seconds

    @Property(float, notify=progressChanged)
    def trackProgress(self) -> float:
        if self.playback.duration_seconds <= 0:
            return 0.0
        return max(0.0, min(1.0, self.playback.position_seconds / self.playback.duration_seconds))

    @Property(str, notify=progressChanged)
    def progressLabel(self) -> str:
        return f"{_format_duration(self.playback.position_seconds)}/{_format_duration(self.playback.duration_seconds)}"

    @Property(str, notify=outputDeviceChanged)
    def outputDevice(self) -> str:
        return self.playback.output_device

    @Property("QVariantList", notify=outputDeviceChanged)
    def outputDevices(self) -> list[str]:
        return list(self.playback.output_devices)

    @Property(bool, notify=pairedChanged)
    def paired(self) -> bool:
        return bool(self.cfg.paired and self.cfg.device_token)

    @Property(bool, notify=pairingSuccessChanged)
    def pairingSuccessVisible(self) -> bool:
        return self._pairing_success_visible

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

    @Property(str, notify=localApiUrlChanged)
    def webPortalUrl(self) -> str:
        return self.cfg.local_url

    @Property(str, notify=settingsChanged)
    def deviceId(self) -> str:
        return self.cfg.device_id

    @Property(str, notify=pairingCodeChanged)
    def pairingCode(self) -> str:
        return self.cfg.pairing_code

    @Property(str, constant=True)
    def version(self) -> str:
        return self.cfg.version

    @Property(str, notify=settingsChanged)
    def screenshotFile(self) -> str:
        return self.cfg.screenshot_file

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

    @Property(str, notify=logLevelChanged)
    def logLevel(self) -> str:
        return self.cfg.log_level

    @Property(str, notify=languageChanged)
    def language(self) -> str:
        return self.cfg.language

    @Property(str, notify=translationsChanged)
    def languageName(self) -> str:
        return LANGUAGES.get(self.cfg.language, LANGUAGES["nl"])

    @Property(int, notify=translationsChanged)
    def translationVersion(self) -> int:
        return self._translation_version

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
        self._translation_version += 1
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
    def setLogLevel(self, value: str) -> None:
        level = value.strip().upper()
        if level not in {"DEBUG", "INFO", "WARNING", "ERROR"}:
            level = "INFO"
        if self.cfg.log_level == level:
            return
        self.cfg.log_level = level
        logging.getLogger().setLevel(getattr(logging, level, logging.INFO))
        save_config(self.config_path, self.cfg)
        self.logLevelChanged.emit()
        self.settingsChanged.emit()
        _LOGGER.info("User changed log level to %s", level)
        self.showToast(self.tr_key("log_level_saved", level=level))

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
            _LOGGER.debug("Refresh skipped because another task is active")
            return
        if not self.paired:
            latest = load_config(self.config_path)
            if latest.paired and latest.device_token:
                self.cfg = latest
                self.client.cfg = self.cfg
                self._pairing_success_visible = True
                self.pairedChanged.emit()
                self.settingsChanged.emit()
                self.pairingSuccessChanged.emit()
                self._set_status_text(self.tr_key("paired"))
                self._run(self.tr_key("refreshing"), self._refresh_worker)
                return
        if not self.paired and not self.cfg.ha_url:
            self._set_status_text(self.tr_key("ready_to_pair"))
            return
        self._run(self.tr_key("refreshing"), self._refresh_worker)

    def _sync_config_from_disk(self) -> None:
        latest = load_config(self.config_path)
        if (
            latest.device_token == self.cfg.device_token
            and latest.paired == self.cfg.paired
            and latest.ha_url == self.cfg.ha_url
            and latest.language == self.cfg.language
            and latest.log_level == self.cfg.log_level
            and latest.screen_brightness_percent == self.cfg.screen_brightness_percent
            and latest.screen_timeout_seconds == self.cfg.screen_timeout_seconds
            and latest.update_channel == self.cfg.update_channel
        ):
            return
        language_changed = latest.language != self.cfg.language
        self.cfg = latest
        self.client.cfg = self.cfg
        self.pairedChanged.emit()
        self.settingsChanged.emit()
        self.logLevelChanged.emit()
        self.screenBrightnessChanged.emit()
        self.screenTimeoutChanged.emit()
        self.updateChannelChanged.emit()
        if language_changed:
            self._translation_version += 1
            self.languageChanged.emit()
            self.translationsChanged.emit()

    @Slot()
    def startAfterPairing(self) -> None:
        self._pairing_success_visible = False
        self.pairingSuccessChanged.emit()
        self.refresh()

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
        self.wakeScreenRequested.emit()
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
        self.wakeScreenRequested.emit()
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
        value = max(0, min(60, int(value)))
        if value == self.playback.volume:
            return
        self.playback.volume = value
        self.volumeChanged.emit()
        _LOGGER.info("User set volume to %s", value)
        self.showToast(f"{self.tr_key('vol')} {value}")
        if self._demo_mode:
            return
        self.command("set_volume", value=value)

    @Slot(int)
    def adjustVolume(self, delta: int) -> None:
        self.setVolume(self.playback.volume + int(delta))

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

    @Slot(str)
    def setOutputDevice(self, value: str) -> None:
        value = value.strip()
        if not value:
            self.playback.output_device = ""
            self.outputDeviceChanged.emit()
            _LOGGER.info("User cleared output device selection from touch UI")
            self.showToast(self.tr_key("none"))
            return
        previous = self.playback.output_device
        self.playback.output_device = value
        self._pending_output_device = value
        self._pending_output_until = time.monotonic() + 20
        self.outputDeviceChanged.emit()
        _LOGGER.info("User selected output device: %s", value)
        self.showToast(value)
        if self._demo_mode:
            return
        self._run("set_output", lambda: self._set_output_worker(value, previous))

    @Slot()
    def enterDemoMode(self) -> None:
        if self.paired:
            return
        self._demo_mode = True
        self._queue_items = demo_queue_items()
        self._playlist_items = demo_playlist_items()
        self.demoModeChanged.emit()
        self.mediaListsChanged.emit()
        self._apply_demo_track("Midnight City", "M83")
        _LOGGER.info("User entered local demo mode")
        self.showToast(self.tr_key("demo_active"))
        self._set_status_text(self.tr_key("demo_active"))

    @Slot()
    def exitDemoMode(self) -> None:
        if not self._demo_mode:
            return
        self._demo_mode = False
        self._queue_items = []
        self._playlist_items = []
        self.demoModeChanged.emit()
        self.mediaListsChanged.emit()
        self.playback = Playback()
        self.titleChanged.emit()
        self.artistChanged.emit()
        self.imageUrlChanged.emit()
        self.playingChanged.emit()
        self.volumeChanged.emit()
        self.shuffleChanged.emit()
        self.repeatChanged.emit()
        self.outputDeviceChanged.emit()
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
    def manualRefresh(self) -> None:
        _LOGGER.info("User requested manual refresh")
        self._pending_output_device = ""
        self._pending_output_until = 0.0
        self.refresh()

    @Slot()
    def resetPairing(self) -> None:
        _LOGGER.info("User requested pairing reset from touch UI")
        self._forget_pairing()
        self.showToast(self.tr_key("ready_to_pair"))
        self._set_status_text(self.tr_key("ready_to_pair"))

    @Slot()
    def rebootDevice(self) -> None:
        _LOGGER.info("User requested device reboot from touch UI")
        self._run_power_command(
            action="reboot",
            status_key="rebooting",
            failure_key="reboot_failed",
            commands=(
                ["sudo", "-n", "/usr/bin/systemctl", "reboot"],
                ["sudo", "-n", "/bin/systemctl", "reboot"],
                ["sudo", "-n", "systemctl", "reboot"],
                ["/usr/bin/systemctl", "reboot"],
                ["/bin/systemctl", "reboot"],
            ),
        )

    @Slot()
    def shutdownDevice(self) -> None:
        _LOGGER.info("User requested device shutdown from touch UI")
        self._run_power_command(
            action="shutdown",
            status_key="shutting_down",
            failure_key="shutdown_failed",
            commands=(
                ["sudo", "-n", "/usr/bin/systemctl", "poweroff"],
                ["sudo", "-n", "/bin/systemctl", "poweroff"],
                ["sudo", "-n", "systemctl", "poweroff"],
                ["/usr/bin/systemctl", "poweroff"],
                ["/bin/systemctl", "poweroff"],
            ),
        )

    @Slot()
    def checkForUpdates(self) -> None:
        _LOGGER.info("User requested update check from touch UI")
        self._set_status_text(self.tr_key("checking_updates"))
        self.showToast(self.tr_key("checking_updates"))
        commands = (
            ["sudo", "-n", "/usr/bin/systemctl", "start", "djconnect-updater.service"],
            ["sudo", "-n", "/bin/systemctl", "start", "djconnect-updater.service"],
        )
        last_error = "unknown error"
        for command in commands:
            try:
                _LOGGER.info("Starting update check command: %s", " ".join(command))
                subprocess.run(command, check=True, timeout=8, capture_output=True, text=True)
                self._set_status_text(self.tr_key("update_check_started"))
                self.showToast(self.tr_key("update_check_started"))
                return
            except subprocess.CalledProcessError as exc:
                detail = (exc.stderr or exc.stdout or str(exc)).strip()
                last_error = detail or str(exc)
                _LOGGER.warning("Update check command failed: %s: %s", " ".join(command), last_error)
            except Exception as exc:
                last_error = str(exc)
                _LOGGER.warning("Update check command failed: %s: %s", " ".join(command), exc)
        message = self.tr_key("update_check_failed", error=last_error)
        self._set_status_text(message)
        self._show_toast(message, 5000)

    def _run_power_command(self, *, action: str, status_key: str, failure_key: str, commands: tuple[list[str], ...]) -> None:
        self._set_status_text(self.tr_key(status_key))
        self.showToast(self.tr_key(status_key))
        last_error: str = "unknown error"
        for command in commands:
            try:
                _LOGGER.info("Starting %s command: %s", action, " ".join(command))
                subprocess.run(command, check=True, timeout=5, capture_output=True, text=True)
                return
            except subprocess.CalledProcessError as exc:
                detail = (exc.stderr or exc.stdout or str(exc)).strip()
                last_error = detail or str(exc)
                _LOGGER.warning("%s command failed: %s: %s", action.capitalize(), " ".join(command), last_error)
            except Exception as exc:
                last_error = str(exc)
                _LOGGER.warning("%s command failed: %s: %s", action.capitalize(), " ".join(command), exc)
        message = self.tr_key(failure_key, error=last_error)
        self._set_status_text(message)
        self._show_toast(message, 5000)

    @Slot(str, str)
    def playMediaItem(self, command: str, item: str) -> None:
        command = command.strip()
        payload = media_item_payload(command, item)
        if not command or not payload:
            return
        if command not in {"start_queue_item", "start_playlist"}:
            _LOGGER.warning("Ignoring unsupported media item command from touch UI: %s", command)
            return
        _LOGGER.info("User requested %s from touch UI", command)
        self.showToast(self.tr_key("play"))
        self._run(command, lambda: self._play_media_item_worker(command, payload))

    @Slot()
    def showLogs(self) -> None:
        _LOGGER.info("User opened logs view")
        self.showToast(self.tr_key("logs"))
        path = Path(self.cfg.log_file)
        try:
            if path.exists():
                data = _read_tail_text(path, LOG_DISPLAY_MAX_BYTES)
                self._logs_text = _format_logs_for_display(data)
            else:
                self._logs_text = self.tr_key("logs_missing")
        except Exception as exc:
            self._logs_text = self.tr_key("logs_failed", error=exc)
        self._logs_visible = True
        self.logsChanged.emit()

    @Slot()
    def copyLogs(self) -> None:
        _LOGGER.info("User copied logs from touch UI")
        QGuiApplication.clipboard().setText(self._logs_text)
        self.showToast(self.tr_key("logs_copied"))

    @Slot()
    def clearLogs(self) -> None:
        _LOGGER.info("User cleared logs from touch UI")
        path = Path(self.cfg.log_file)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")
            self._logs_text = self.tr_key("logs_cleared")
            self.showToast(self.tr_key("logs_cleared"))
        except Exception as exc:
            self._logs_text = self.tr_key("logs_failed", error=exc)
        self.logsChanged.emit()

    @Slot()
    def hideLogs(self) -> None:
        self._logs_visible = False
        self.logsChanged.emit()

    @Slot(str)
    def showToast(self, text: str) -> None:
        self._show_toast(text, 2000)

    @Slot(str)
    def playGameSound(self, kind: str) -> None:
        try:
            from PySide6.QtMultimedia import QAudioFormat, QAudioSink, QMediaDevices
        except Exception as exc:
            _LOGGER.debug("Game sound unavailable: %s", exc)
            return
        tones = {
            "start": (220, 90),
            "move": (180, 45),
            "fire": (760, 65),
            "pellet": (520, 45),
            "power": (300, 110),
            "ghost": (880, 90),
            "death": (90, 140),
            "hit": (430, 55),
            "wall": (260, 45),
            "explode": (120, 120),
            "crash": (70, 140),
            "gameover": (100, 120),
        }
        frequency, duration_ms = tones.get(kind.strip(), (240, 55))
        try:
            device = QMediaDevices.defaultAudioOutput()
            if device.isNull():
                return
            audio_format = QAudioFormat()
            audio_format.setSampleRate(GAME_SOUND_SAMPLE_RATE)
            audio_format.setChannelCount(1)
            audio_format.setSampleFormat(QAudioFormat.Int16)
            if not device.isFormatSupported(audio_format):
                audio_format = device.preferredFormat()
            data = _square_wave_pcm(frequency, duration_ms, audio_format.sampleRate())
            if not data:
                return
            buffer = QBuffer(self)
            buffer.setData(QByteArray(data))
            buffer.open(QIODevice.ReadOnly)
            sink = QAudioSink(device, audio_format, self)
            sink.setVolume(0.04)
            sink.start(buffer)
            self._game_sound_objects.append((sink, buffer))
            QTimer.singleShot(duration_ms + 250, lambda: self._cleanup_game_sound(sink, buffer))
        except Exception as exc:
            _LOGGER.debug("Game sound skipped: %s", exc)

    def _cleanup_game_sound(self, sink: object, buffer: QBuffer) -> None:
        try:
            if hasattr(sink, "stop"):
                sink.stop()
            buffer.close()
        finally:
            self._game_sound_objects = [(s, b) for s, b in self._game_sound_objects if s is not sink and b is not buffer]

    def _show_toast(self, text: str, duration_ms: int = 2000) -> None:
        text = text.strip()
        if not text:
            return
        self._toast_text = text
        self._toast_visible = True
        self.toastChanged.emit()
        self._toast_timer.setInterval(duration_ms)
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

    @Slot(str)
    def playUri(self, uri: str) -> None:
        uri = uri.strip()
        if not uri:
            return
        _LOGGER.info("User requested play_uri from touch UI")
        self.showToast(self.tr_key("play"))
        self.command("play_uri", uri=uri)

    @Slot()
    def loadQueue(self) -> None:
        if self._demo_mode:
            self._queue_items = demo_queue_items()
            self.mediaListsChanged.emit()
            return
        self._sync_config_from_disk()
        if not self.paired:
            return
        if "queue" in self._media_loads_in_flight:
            _LOGGER.debug("Queue load skipped because a queue load is already active")
            return
        self._media_loads_in_flight.add("queue")
        _LOGGER.info("User requested queue from touch UI")
        self._run(self.tr_key("queue"), self._load_queue_worker, done=lambda: self._media_loads_in_flight.discard("queue"))

    @Slot()
    def loadPlaylists(self) -> None:
        if self._demo_mode:
            self._playlist_items = demo_playlist_items()
            self.mediaListsChanged.emit()
            return
        self._sync_config_from_disk()
        if not self.paired:
            return
        if "playlists" in self._media_loads_in_flight:
            _LOGGER.debug("Playlist load skipped because a playlist load is already active")
            return
        self._media_loads_in_flight.add("playlists")
        _LOGGER.info("User requested playlists from touch UI")
        self._run(self.tr_key("playlists"), self._load_playlists_worker, done=lambda: self._media_loads_in_flight.discard("playlists"))

    @Slot(str, result=str)
    def cachedImageUrl(self, url: str) -> str:
        return cached_image_url(url)

    def _pair_worker(self, code: str) -> None:
        _LOGGER.info("Pairing DJConnect Pi client")
        self.client.pair(code)
        save_config(self.config_path, self.cfg)
        self._pairingReady.emit(True, self.tr_key("paired"))

    def _refresh_worker(self) -> None:
        started = time.monotonic()
        _LOGGER.debug("Refreshing playback status")
        data = self.client.command("status") if self.paired else self.client.status()
        playback = self.client.playback_from_status(data)
        if self._pending_output_device and time.monotonic() < self._pending_output_until:
            if not playback.output_devices or self._pending_output_device in playback.output_devices:
                playback.output_device = self._pending_output_device
        elif self._pending_output_device:
            self._pending_output_device = ""
            self._pending_output_until = 0.0
        if self.playback.output_device and not playback.output_device:
            playback.output_device = self.playback.output_device
        if self.paired and not playback.output_devices:
            try:
                devices_data = self.client.command("devices")
                devices_playback = self.client.playback_from_status(devices_data)
                if devices_playback.output_devices:
                    playback.output_devices = devices_playback.output_devices
                    _LOGGER.debug("Loaded %s output devices from Home Assistant devices command", len(playback.output_devices))
            except DJConnectError as exc:
                _LOGGER.warning("Output devices refresh failed: %s", exc)
        if self.paired:
            self.client.status(playback)
        self._playbackReady.emit(playback)
        _LOGGER.info("Refresh completed in %.0fms", _elapsed_ms(started))

    def _command_worker(self, command: str, **payload: object) -> None:
        started = time.monotonic()
        _LOGGER.info("Sending playback command: %s", command)
        data = self.client.command(command, **payload)
        self._playbackReady.emit(self.client.playback_from_status(data))
        _LOGGER.info("Playback command %s completed in %.0fms", command, _elapsed_ms(started))

    def _play_media_item_worker(self, command: str, payload: dict[str, object]) -> None:
        started = time.monotonic()
        _LOGGER.info("Sending media item command: %s", command)
        data = self.client.command(command, **payload)
        self._playbackReady.emit(self.client.playback_from_status(data))
        if command == "start_playlist":
            self._load_queue_worker()
        else:
            self._refresh_worker()
        _LOGGER.info("Media item command %s completed in %.0fms", command, _elapsed_ms(started))

    def _set_output_worker(self, value: str, previous: str) -> None:
        started = time.monotonic()
        try:
            data = self.client.command("set_output", value=value)
            playback = self.client.playback_from_status(data)
            if playback.output_devices and value not in playback.output_devices:
                raise DJConnectError(f"Output device not available: {value}")
            if playback.output_devices and value in playback.output_devices:
                playback.output_device = value
            elif playback.output_device and playback.output_device != value:
                raise DJConnectError(f"Output device not accepted: {value}")
            if not playback.output_device:
                playback.output_device = value
            if not playback.output_devices:
                playback.output_devices = self.playback.output_devices or ((value,) if value else ())
            self._pending_output_device = value
            self._pending_output_until = time.monotonic() + 20
            self._playbackReady.emit(playback)
            _LOGGER.info("Output device %s validated in %.0fms", value, _elapsed_ms(started))
        except Exception:
            self._outputDeviceRejected.emit(previous, value)
            raise

    def _load_queue_worker(self) -> None:
        started = time.monotonic()
        _LOGGER.info("Loading queue from Home Assistant")
        data = self.client.command("queue", limit=100)
        items = parse_queue_items(data)
        _LOGGER.info("Loaded %s queue items from Home Assistant", len(items))
        self._mediaListReady.emit("queue", items)
        _LOGGER.info("Queue list displayed in %.0fms", _elapsed_ms(started))
        self._cache_media_artwork_async("queue", items)

    def _load_playlists_worker(self) -> None:
        started = time.monotonic()
        _LOGGER.info("Loading playlists from Home Assistant")
        data = self.client.command("playlists", limit=100)
        items = parse_playlist_items(data)
        _LOGGER.info("Loaded %s playlists from Home Assistant", len(items))
        self._mediaListReady.emit("playlists", items)
        _LOGGER.info("Playlist list displayed in %.0fms", _elapsed_ms(started))
        self._cache_media_artwork_async("playlists", items)

    def _cache_media_artwork_async(self, kind: str, items: list[dict[str, object]]) -> None:
        if not items:
            return
        if kind in self._media_artwork_cache_in_flight:
            _LOGGER.debug("%s artwork cache skipped because a cache worker is already active", kind)
            return
        self._media_artwork_cache_in_flight.add(kind)
        cache_items = [dict(item) for item in items[:MEDIA_ARTWORK_CACHE_LIMIT]]

        def worker() -> None:
            try:
                started = time.monotonic()
                cached = prepare_media_artwork(cache_items)
                _LOGGER.info("Cached %s artwork for %s items in %.0fms", kind, len(cached), _elapsed_ms(started))
                merged = [dict(item) for item in items]
                for index, cached_item in enumerate(cached):
                    if index < len(merged):
                        merged[index] = cached_item
                self._mediaListReady.emit(kind, merged)
            finally:
                self._media_artwork_cache_in_flight.discard(kind)

        self._executor.submit(worker)

    def _show_dj_response(self, payload: dict[str, object]) -> dict[str, object]:
        text = str(payload.get("dj_text") or payload.get("text") or payload.get("message") or "").strip()
        if not text:
            return {"success": False, "error": "missing_text"}
        self._dj_response_text = text
        self._dj_response_visible = True
        self.djResponseChanged.emit()
        self.temporaryWakeRequested.emit(20, False)
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
        self._queue_items = []
        self._playlist_items = []
        from .config import generate_pairing_code

        self.cfg.pairing_code = generate_pairing_code()
        save_config(self.config_path, self.cfg)
        self.pairedChanged.emit()
        self.pairingCodeChanged.emit()
        self.settingsChanged.emit()
        self.mediaListsChanged.emit()

    def _apply_demo_track(self, title: str, artist: str) -> None:
        self.playback.title = title
        self.playback.artist = artist
        self.playback.image_url = ""
        self.playback.is_playing = True
        self.titleChanged.emit()
        self.artistChanged.emit()
        self.imageUrlChanged.emit()
        self.playingChanged.emit()

    def _run(self, label: str, worker, done=None) -> None:
        self._set_busy(True)
        self._set_status_text(label)

        def execute() -> None:
            try:
                worker()
            except ProtocolVersionMismatch as exc:
                self._backendAvailableReady.emit(False)
                _LOGGER.warning("%s blocked by version mismatch: %s", label, exc)
                self._versionMismatchReady.emit(exc.client_version, exc.ha_version)
                self._statusReady.emit(str(exc))
            except AuthenticationError as exc:
                self._backendAvailableReady.emit(False)
                message = self.tr_key("ha_auth_failed")
                _LOGGER.warning("%s authentication failed: %s", label, exc)
                if not self.paired:
                    _LOGGER.info("Suppressing authentication toast while DJConnect is waiting for pairing")
                    self._statusReady.emit(self.tr_key("ready_to_pair"))
                    return
                self._statusReady.emit(message)
                self._toastReady.emit(message, 5000)
            except BackendUnavailable as exc:
                self._backendAvailableReady.emit(False)
                _LOGGER.warning("%s backend unavailable: %s", label, exc)
                message = self.tr_key("backend_unavailable")
                if not self.paired:
                    _LOGGER.info("Suppressing backend-unavailable toast while DJConnect is waiting for pairing")
                    self._statusReady.emit(self.tr_key("ready_to_pair"))
                    return
                self._statusReady.emit(message)
                self._toastReady.emit(message, 5000)
            except DJConnectError as exc:
                self._backendAvailableReady.emit(False)
                _LOGGER.warning("%s failed: %s", label, exc)
                self._statusReady.emit(str(exc))
            except Exception as exc:
                self._backendAvailableReady.emit(False)
                _LOGGER.exception("%s failed unexpectedly", label)
                self._statusReady.emit(self.tr_key("offline", error=exc))
            finally:
                if done is not None:
                    done()
                self._busyReady.emit(False)

        self._executor.submit(execute)

    @Slot(object)
    def _apply_playback(self, playback: Playback) -> None:
        self._set_backend_available(True)
        if self._version_mismatch_visible:
            self._version_mismatch_visible = False
            self._version_mismatch_text = ""
            self.versionMismatchChanged.emit()
        old = self.playback
        self.playback = playback
        track_changed = old.title != playback.title or old.artist != playback.artist or old.image_url != playback.image_url
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
        if old.output_device != playback.output_device or old.output_devices != playback.output_devices:
            self.outputDeviceChanged.emit()
        if old.position_seconds != playback.position_seconds or old.duration_seconds != playback.duration_seconds:
            self.progressChanged.emit()
        if track_changed and (playback.title or playback.artist or playback.image_url):
            self.temporaryWakeRequested.emit(10, True)
        self._set_status_text(self.tr_key("connected" if self.paired else "ready_to_pair"))

    @Slot(str, object)
    def _apply_media_list(self, kind: str, items: object) -> None:
        if not isinstance(items, list):
            return
        if kind == "queue":
            self._queue_items = items
        elif kind == "playlists":
            self._playlist_items = items
        else:
            return
        self.mediaListsChanged.emit()

    @Slot(str, str)
    def _apply_output_device_rejection(self, previous: str, attempted: str) -> None:
        self.playback.output_device = previous
        self.outputDeviceChanged.emit()
        _LOGGER.warning("Output device selection rejected: %s", attempted)

    @Slot(bool, str)
    def _apply_pairing(self, paired: bool, message: str) -> None:
        if paired:
            self._set_backend_available(True)
        if self._version_mismatch_visible:
            self._version_mismatch_visible = False
            self._version_mismatch_text = ""
            self.versionMismatchChanged.emit()
        if paired:
            self._pairing_success_visible = True
            self.pairedChanged.emit()
            self.settingsChanged.emit()
            self.pairingSuccessChanged.emit()
        self._set_status_text(message)

    @Slot(str)
    def _set_status_text(self, value: str) -> None:
        if self._status_text == value:
            return
        self._status_text = value
        self.statusTextChanged.emit()

    def _set_backend_available(self, value: bool) -> None:
        if self._backend_available == value:
            return
        self._backend_available = value
        self.backendAvailableChanged.emit()

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
        self._poll_dj_response_event()
        self._poll_command_event()
        self._poll_screenshot_event()

    def _poll_dj_response_event(self) -> None:
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

    def _poll_command_event(self) -> None:
        path = Path(self.cfg.command_event_file)
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            path.unlink(missing_ok=True)
        except (OSError, json.JSONDecodeError) as exc:
            _LOGGER.warning("Failed to read local command event file: %s", exc)
            return
        raw_events = data.get("events") if isinstance(data.get("events"), list) else [data]
        self._sync_config_from_disk()
        for event in raw_events:
            if not isinstance(event, dict):
                continue
            command = str(event.get("command") or "").strip()
            payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
            if not command:
                continue
            if command == "debug_show_screen":
                screen = str(payload.get("screen") or "").strip()
                if screen:
                    _LOGGER.info("Executing local debug screen request: %s", screen)
                    self.debugScreenRequested.emit(screen)
                continue
            if command == "settings":
                _LOGGER.info("Executing local web portal settings update")
                self._sync_config_from_disk()
                self.languageChanged.emit()
                self.logLevelChanged.emit()
                self.screenBrightnessChanged.emit()
                self.screenTimeoutChanged.emit()
                self.settingsChanged.emit()
                self.translationsChanged.emit()
                continue
            if command == "forget_pairing":
                _LOGGER.info("Executing local web portal pairing reset")
                self.resetPairing()
                continue
            if command == "reboot":
                _LOGGER.info("Executing local web portal reboot request")
                self.rebootDevice()
                continue
            if command == "shutdown":
                _LOGGER.info("Executing local web portal shutdown request")
                self.shutdownDevice()
                continue
            if command == "check_updates":
                _LOGGER.info("Executing local web portal update check request")
                self.checkForUpdates()
                continue
            if command in {"start_queue_item", "start_playlist"}:
                item_payload = media_item_payload(command, payload)
                if not item_payload:
                    _LOGGER.info("Ignoring local media item request without usable URI: %s", command)
                    continue
                _LOGGER.info("Executing local web portal media item request: %s", command)
                self.playMediaItem(command, item_payload)
                continue
            _LOGGER.info("Executing Client API command event from Home Assistant: %s", command)
            if command in {"previous", "next"}:
                self.wakeScreenRequested.emit()
            self.command(command, **{k: v for k, v in payload.items() if k not in {"command", "device_id", "client_type", "version", "firmware", "local_url", "capabilities"}})

    def _poll_screenshot_event(self) -> None:
        path = Path(self.cfg.screenshot_event_file)
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            path.unlink(missing_ok=True)
        except (OSError, json.JSONDecodeError) as exc:
            _LOGGER.warning("Failed to read local screenshot event file: %s", exc)
            return
        target = Path(str(data.get("target") or self.cfg.screenshot_file)) if isinstance(data, dict) else Path(self.cfg.screenshot_file)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            _LOGGER.warning("Failed to prepare screenshot directory: %s", exc)
            return
        _LOGGER.info("Capturing debug screenshot to %s", target)
        self.cfg.screenshot_file = str(target)
        self.wakeScreenRequested.emit()
        self.screenshotRequested.emit()


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


def _format_logs_for_display(data: str, max_chars: int = 12000) -> str:
    lines = data.splitlines()[-220:]
    formatted: list[str] = []
    for line in lines:
        match = LOG_LINE_RE.match(line)
        if not match:
            formatted.append(line)
            continue
        level = LOG_LEVEL_SHORT.get(match.group("level"), match.group("level")[:3])
        formatted.append(f"{match.group('time')} {level} {match.group('rest')}")
    result = "\n".join(formatted)
    return result[-max_chars:] if len(result) > max_chars else result


def _read_tail_text(path: Path, max_bytes: int) -> str:
    size = path.stat().st_size
    with path.open("rb") as handle:
        if size > max_bytes:
            handle.seek(-max_bytes, 2)
        data = handle.read()
    return data.decode("utf-8", errors="replace")


def _elapsed_ms(started: float) -> float:
    return (time.monotonic() - started) * 1000


def _square_wave_pcm(frequency: int, duration_ms: int, sample_rate: int) -> bytes:
    if sample_rate <= 0:
        return b""
    sample_count = max(1, int(sample_rate * duration_ms / 1000))
    period = max(1, int(sample_rate / max(1, frequency)))
    amplitude = 1400
    data = bytearray()
    for index in range(sample_count):
        envelope = 1.0 - (index / sample_count)
        value = int((amplitude if (index % period) < period / 2 else -amplitude) * envelope)
        data.extend(value.to_bytes(2, "little", signed=True))
    return bytes(data)


def _format_duration(seconds: int) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"


def cached_image_url(url: str, ttl_seconds: int = 24 * 60 * 60) -> str:
    url = str(url or "").strip()
    if not url:
        return ""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return url

    cache_dir = DEFAULT_LOG_PATH.parent.parent / "cache" / "album-art"
    cache_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(parsed.path).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        suffix = ".img"
    target = cache_dir / f"{hashlib.sha256(url.encode('utf-8')).hexdigest()}{suffix}"
    if target.exists() and time.time() - target.stat().st_mtime < ttl_seconds:
        return target.as_uri()

    try:
        response = requests.get(url, timeout=8)
        response.raise_for_status()
        target.write_bytes(response.content)
        return target.as_uri()
    except Exception as exc:
        _LOGGER.debug("Album art cache fallback for %s: %s", url, exc)
        return url


def prepare_media_artwork(items: list[dict[str, object]]) -> list[dict[str, object]]:
    for item in items:
        image_url = str(item.get("imageUrl") or "")
        if image_url:
            item["imageUrl"] = cached_image_url(image_url)
    return items


def demo_queue_items() -> list[dict[str, object]]:
    return [
        {
            "title": "Midnight City",
            "subtitle": "M83",
            "uri": "spotify:track:demo-0",
            "imageUrl": "",
            "tint": "#d946ef",
        },
        {
            "title": "Sweet Disposition",
            "subtitle": "The Temper Trap",
            "uri": "spotify:track:demo-1",
            "imageUrl": "",
            "tint": "#a78bfa",
        },
        {
            "title": "Electric Feel",
            "subtitle": "MGMT",
            "uri": "spotify:track:demo-2",
            "imageUrl": "",
            "tint": "#38bdf8",
        },
    ]


def demo_playlist_items() -> list[dict[str, object]]:
    return [
        {"title": "Friday Night", "subtitle": "", "uri": "spotify:playlist:djconnect-demo", "imageUrl": "", "tint": "#d946ef"},
        {"title": "Dinner Vibes", "subtitle": "", "uri": "spotify:playlist:djconnect-dinner", "imageUrl": "", "tint": "#64748b"},
        {"title": "DJConnect", "subtitle": "", "uri": "spotify:playlist:djconnect", "imageUrl": "", "tint": "#8b5cf6"},
    ]


def parse_queue_items(data: dict[str, object]) -> list[dict[str, object]]:
    raw_queue = _first_present(data, ("queue",))
    if isinstance(raw_queue, dict):
        raw_items = raw_queue.get("items")
    elif isinstance(raw_queue, list):
        raw_items = raw_queue
    else:
        raw_items = _first_present(data, ("items",))
    if not isinstance(raw_items, list):
        return []
    return [parsed for item in raw_items[:100] if isinstance(item, dict) and (parsed := _media_item(item))]


def parse_playlist_items(data: dict[str, object]) -> list[dict[str, object]]:
    raw_items = _first_present(data, ("playlists", "items"))
    if not isinstance(raw_items, list):
        return []
    return [parsed for item in raw_items[:100] if isinstance(item, dict) and (parsed := _media_item(item, playlist=True))]


def _media_item(item: dict[str, object], playlist: bool = False) -> dict[str, object] | None:
    title = str(item.get("name") or item.get("title") or item.get("display_title") or item.get("track_name") or "")
    subtitle = str(item.get("artist") or item.get("artist_name") or item.get("artists") or item.get("subtitle") or item.get("album") or "")
    uri = str(item.get("uri") or item.get("id") or item.get("value") or item.get("playlist_uri") or item.get("track_uri") or "")
    context_uri = str(item.get("context_uri") or item.get("contextUri") or item.get("queue_context") or item.get("queueContext") or "")
    index = item.get("index")
    image_url = str(
        item.get("image_url")
        or item.get("imageUrl")
        or item.get("album_image_url")
        or item.get("albumImageUrl")
        or item.get("album_art_url")
        or item.get("media_image_url")
        or item.get("entity_picture")
        or item.get("thumbnail_url")
        or ""
    )
    if playlist:
        subtitle = str(item.get("owner") or item.get("owner_name") or item.get("description") or subtitle)
        if not title or not uri:
            return None
    result: dict[str, object] = {
        "title": title,
        "subtitle": subtitle,
        "uri": uri,
        "imageUrl": image_url,
        "tint": "#8b5cf6" if playlist else "#38bdf8",
    }
    if not playlist:
        result["contextUri"] = context_uri
        result["index"] = index if isinstance(index, int) else None
    return result


def media_item_payload(command: str, item: object) -> dict[str, object]:
    if isinstance(item, str):
        text = item.strip()
        if text.startswith("{"):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                return {}
            if not isinstance(parsed, dict):
                return {}
            item_data = parsed
            uri = str(item_data.get("uri") or item_data.get("value") or "").strip()
        else:
            uri = text
            item_data = {"uri": uri}
    elif isinstance(item, dict):
        item_data = item
        uri = str(item_data.get("uri") or item_data.get("value") or "").strip()
    else:
        return {}
    if not uri:
        return {}
    if command == "start_playlist":
        return {"value": uri, "uri": uri, "context_uri": uri}

    payload: dict[str, object] = {"value": uri, "uri": uri}
    title = str(item_data.get("title") or "").strip()
    artist = str(item_data.get("artist") or item_data.get("subtitle") or "").strip()
    context_uri = str(
        item_data.get("context_uri")
        or item_data.get("contextUri")
        or item_data.get("queue_context")
        or item_data.get("queueContext")
        or ""
    ).strip()
    index = item_data.get("index")
    if title:
        payload["title"] = title
    if artist:
        payload["artist"] = artist
    if isinstance(index, int):
        payload["index"] = index
    if context_uri:
        payload["context_uri"] = context_uri
        if _context_supports_offset(context_uri):
            payload["offset_uri"] = uri
    return payload


def _context_supports_offset(context_uri: str) -> bool:
    return context_uri.startswith(("spotify:playlist:", "spotify:album:", "spotify:show:"))


def _first_present(data: dict[str, object], keys: tuple[str, ...]) -> object:
    for key in keys:
        value = data.get(key)
        if value is not None:
            return value
    for container_key in ("data", "result"):
        container = data.get(container_key)
        if isinstance(container, dict):
            value = _first_present(container, keys)
            if value is not None:
                return value
    return None


if __name__ == "__main__":
    main()
