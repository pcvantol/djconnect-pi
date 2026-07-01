from __future__ import annotations

from pathlib import Path
import argparse
import base64
import json
import logging
import signal
import subprocess
import sys
import threading
import time

from .client_api import ClientAPI, ClientAPIState
from .config import DEFAULT_CONFIG_PATH, Config, generate_pairing_code, load_config, save_config
from .ha import AuthenticationError, BackendUnavailable, DJConnectError, HAClient, Playback
from .i18n import translate
from .logging_config import setup_logging
from .system_info import log_raspberry_pi_system_info

_LOGGER = logging.getLogger(__name__)
SCREENSHOT_TIMEOUT_SECONDS = 8.0
DIAGNOSTIC_UNITS = (
    ("Client API", "djconnect-api.service"),
    ("Touch UI", "djconnect-client.service"),
    ("Update progress UI", "djconnect-update-ui.service"),
    ("Updater", "djconnect-updater.timer"),
    ("OS maintenance", "djconnect-maintenance.timer"),
    ("Watchdog", "djconnect-watchdog.timer"),
    ("Screen off", "djconnect-screen-off.timer"),
    ("Screen on", "djconnect-screen-on.timer"),
    ("Nightly reboot", "djconnect-nightly-reboot.timer"),
)


class ClientAPIDaemon:
    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path
        self.cfg: Config = load_config(config_path)
        self._stopped = threading.Event()
        self._api = ClientAPI(
            ClientAPIState(
                cfg=self.cfg,
                config_path=self.config_path,
                playback_provider=self._playback,
                command_handler=self._command,
                screenshot_handler=self._screenshot,
                pair_handler=self._paired,
                forget_handler=self._forgotten,
                portal_state_provider=self._portal_state,
            )
        )

    def start(self) -> None:
        self._api.start()
        _LOGGER.info("DJConnect Pi Client API daemon listening on %s", self.cfg.local_url)

    def stop(self) -> None:
        _LOGGER.info("Stopping DJConnect Pi Client API daemon")
        self._api.stop()
        self._stopped.set()

    def wait(self) -> None:
        self._stopped.wait()

    def _playback(self) -> dict[str, object]:
        return _playback_payload(
            Playback(
                title="",
                artist="",
                image_url="",
                is_playing=False,
                volume=50,
                shuffle=False,
                repeat="off",
            )
        )

    def _portal_state(self, include: set[str]) -> dict[str, object]:
        self.cfg = load_config(self.config_path)
        playback = Playback()
        queue: list[dict[str, object]] = []
        playlists: list[dict[str, object]] = []
        logs = ""
        backend_available = bool(self.cfg.paired and self.cfg.device_token)
        status_text = translate(self.cfg.language, "connected" if backend_available else "not_paired")
        fast_path_diagnostics: dict[str, object] = {}
        if self.cfg.paired and self.cfg.device_token and self.cfg.ha_url:
            client = HAClient(self.cfg)
            try:
                playback = client.playback_from_status(client.command("status"))
                if not playback.output_devices:
                    try:
                        devices_playback = client.playback_from_status(client.command("devices"))
                        if devices_playback.output_devices:
                            playback.output_devices = devices_playback.output_devices
                    except DJConnectError as exc:
                        _LOGGER.warning("Portal output devices refresh failed: %s", exc)
                if "queue" in include:
                    queue = _parse_queue_items(client.command("queue", limit=100))
                if "playlists" in include:
                    playlists = _parse_playlist_items(client.command("playlists", limit=100))
                backend_available = True
                status_text = "Verbonden"
            except AuthenticationError as exc:
                backend_available = False
                status_text = f"Home Assistant autorisatie mislukt: {exc}"
            except BackendUnavailable as exc:
                backend_available = False
                status_text = f"Backend niet beschikbaar: {exc}"
            except DJConnectError as exc:
                backend_available = False
                status_text = str(exc)
            except Exception as exc:
                backend_available = False
                status_text = f"Portal status mislukt: {exc}"
                _LOGGER.warning("Portal state refresh failed: %s", exc)
            finally:
                fast_path_diagnostics = client.diagnostics()
        if "logs" in include:
            logs = _read_tail_text(Path(self.cfg.log_file), 48_000)
        return {
            "success": True,
            "paired": self.cfg.paired,
            "backend_available": backend_available,
            "status_text": status_text,
            "playback": _playback_payload(playback),
            "queue": queue,
            "playlists": playlists,
            "logs": logs,
            "settings": {
                "language": self.cfg.language,
                "log_level": self.cfg.log_level,
                "screen_brightness_percent": self.cfg.screen_brightness_percent,
                "screen_timeout_seconds": self.cfg.screen_timeout_seconds,
                "update_channel": self.cfg.update_channel,
            },
            "about": {
                translate(self.cfg.language, "version"): self.cfg.version,
                translate(self.cfg.language, "device_name"): self.cfg.device_name,
                translate(self.cfg.language, "device_id"): self.cfg.device_id,
                translate(self.cfg.language, "client_api_url_label"): self.cfg.local_url,
                translate(self.cfg.language, "home_assistant"): translate(self.cfg.language, "paired" if self.cfg.paired else "not_paired"),
                translate(self.cfg.language, "ha_local_url"): self.cfg.ha_url,
            },
            "diagnostics": self._diagnostics(backend_available=backend_available, fast_path=fast_path_diagnostics),
        }

    def _fallback_playback(self) -> dict[str, object]:
        return {
            "title": "",
            "artist": "",
            "image_url": "",
            "is_playing": False,
            "volume": 50,
            "shuffle": False,
            "repeat_state": "off",
        }

    def _command(self, command: str, payload: dict[str, object]) -> dict[str, object]:
        if command == "status":
            return {"success": True, "playback": self._playback()}
        if command == "dj_response":
            return self._dj_response(payload)
        if not command:
            return {"success": False, "error": "missing_command"}
        if command in {"reboot", "shutdown", "check_updates"}:
            self._write_command_event({"command": command, "payload": payload})
            return {"success": True, "queued": True, "command": command}
        self._write_command_event({"command": command, "payload": payload})
        _LOGGER.info("Queued Client API command for touch UI: %s", command)
        return {"success": True, "queued": True, "command": command}

    def _dj_response(self, payload: dict[str, object]) -> dict[str, object]:
        text = str(payload.get("dj_text") or payload.get("text") or payload.get("message") or "").strip()
        if not text:
            return {"success": False, "error": "missing_text"}
        self._write_dj_response_event({"text": text})
        _LOGGER.info("Received DJ response text through Client API daemon")
        return {"success": True, "displayed": True, "audio_played": False, "text": text}

    def _screenshot(self) -> dict[str, object]:
        self.cfg = load_config(self.config_path)
        target = Path(self.cfg.screenshot_file)
        request_time = time.time()
        if target.exists():
            target.unlink(missing_ok=True)
        self._write_event_file(
            Path(self.cfg.screenshot_event_file),
            {"requested_at": request_time, "target": str(target)},
        )
        _LOGGER.info("Requested touch UI debug screenshot at %s", target)
        deadline = request_time + SCREENSHOT_TIMEOUT_SECONDS
        while time.time() < deadline:
            if target.exists() and target.stat().st_size > 0 and target.stat().st_mtime >= request_time:
                content = target.read_bytes()
                return {
                    "success": True,
                    "path": str(target),
                    "content_type": "image/png",
                    "size": len(content),
                    "content_base64": base64.b64encode(content).decode("ascii"),
                }
            time.sleep(0.2)
        return {"success": False, "error": "screenshot_timeout", "path": str(target)}

    def _diagnostics(self, *, backend_available: bool, fast_path: dict[str, object] | None = None) -> list[dict[str, object]]:
        diagnostics = [
            {
                "name": "Home Assistant API",
                "status": "running" if backend_available else "failed",
                "detail": self.cfg.ha_url or "not configured",
            },
            {
                "name": "Local Client API",
                "status": "running",
                "detail": self.cfg.local_url,
            },
            {
                "name": "Pairing",
                "status": "running" if self.cfg.paired else "stopped",
                "detail": "paired" if self.cfg.paired else "waiting for pairing",
            },
        ]
        if fast_path:
            transport = str(fast_path.get("fastPathTransport") or "http")
            enabled = bool(fast_path.get("websocketEnabled"))
            connected = bool(fast_path.get("websocketConnected"))
            commands = fast_path.get("websocketCommands")
            command_count = len(commands) if isinstance(commands, list) else 0
            error = str(fast_path.get("lastWebSocketError") or "")
            detail_parts = [f"enabled={str(enabled).lower()}", f"transport={transport}", f"commands={command_count}"]
            if error:
                detail_parts.append(f"last_error={error}")
            diagnostics.append(
                {
                    "name": "HA WebSocket fast path",
                    "status": "running" if connected else "stopped",
                    "detail": ", ".join(detail_parts),
                }
            )
        diagnostics.extend(_systemd_unit_status(label, unit) for label, unit in DIAGNOSTIC_UNITS)
        return diagnostics

    def _paired(self) -> None:
        self.cfg = load_config(self.config_path)
        _LOGGER.info("Client API pairing stored for %s", self.cfg.device_id)

    def _forgotten(self) -> None:
        self.cfg = load_config(self.config_path)
        self.cfg.device_token = ""
        self.cfg.paired = False
        self.cfg.pairing_code = generate_pairing_code()
        save_config(self.config_path, self.cfg)
        _LOGGER.info("Client API pairing reset for %s", self.cfg.device_id)

    def _write_dj_response_event(self, payload: dict[str, object]) -> None:
        path = Path(self.cfg.dj_response_file)
        self._write_event_file(path, payload)

    def _write_command_event(self, payload: dict[str, object]) -> None:
        path = Path(self.cfg.command_event_file)
        events: list[object] = []
        if path.exists():
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(existing, dict) and isinstance(existing.get("events"), list):
                    events = existing["events"]
                else:
                    events = existing if isinstance(existing, list) else [existing]
            except (OSError, json.JSONDecodeError):
                events = []
        events.append(payload)
        self._write_event_file(path, {"events": events[-20:]})

    @staticmethod
    def _write_event_file(path: Path, payload: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_name(f".{path.name}.tmp")
        tmp_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
        tmp_path.chmod(0o600)
        tmp_path.replace(path)
        path.chmod(0o600)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--log-file", default="")
    parser.add_argument("--log-level", default="")
    args = parser.parse_args()

    cfg = load_config(args.config)
    if args.log_file:
        cfg.log_file = args.log_file
        save_config(args.config, cfg)
    if args.log_level:
        cfg.log_level = args.log_level.upper()
        save_config(args.config, cfg)

    setup_logging(cfg.log_file, cfg.log_level)
    _LOGGER.info("Starting DJConnect Pi Client API daemon")
    log_raspberry_pi_system_info()
    daemon = ClientAPIDaemon(args.config)

    def handle_stop(signum: int, _frame: object) -> None:
        _LOGGER.info("Received signal %s", signum)
        daemon.stop()

    signal.signal(signal.SIGINT, handle_stop)
    signal.signal(signal.SIGTERM, handle_stop)
    daemon.start()
    daemon.wait()
    raise SystemExit(0)


def _playback_payload(playback: Playback) -> dict[str, object]:
    return {
        "title": playback.title,
        "artist": playback.artist,
        "image_url": playback.image_url,
        "is_playing": playback.is_playing,
        "volume": playback.volume,
        "shuffle": playback.shuffle,
        "repeat_state": playback.repeat,
        "position_seconds": playback.position_seconds,
        "duration_seconds": playback.duration_seconds,
        "output_device": playback.output_device,
        "output_devices": list(playback.output_devices),
    }


def _parse_queue_items(data: dict[str, object]) -> list[dict[str, object]]:
    raw_queue = _first_present(data, ("queue",))
    if isinstance(raw_queue, dict):
        raw_items = raw_queue.get("items")
    elif isinstance(raw_queue, list):
        raw_items = raw_queue
    else:
        raw_items = _first_present(data, ("items",))
    if not isinstance(raw_items, list):
        return []
    return _dedupe_queue_items([parsed for item in raw_items[:100] if isinstance(item, dict) and (parsed := _media_item(item))])


def _parse_playlist_items(data: dict[str, object]) -> list[dict[str, object]]:
    raw_items = _first_present(data, ("playlists", "items"))
    if not isinstance(raw_items, list):
        return []
    return [parsed for item in raw_items[:100] if isinstance(item, dict) and (parsed := _media_item(item, playlist=True))]


def _dedupe_queue_items(items: list[dict[str, object]]) -> list[dict[str, object]]:
    seen: set[tuple[str, str, str, str]] = set()
    deduped: list[dict[str, object]] = []
    for item in items:
        key = (
            str(item.get("uri") or "").strip().casefold(),
            str(item.get("title") or "").strip().casefold(),
            str(item.get("subtitle") or "").strip().casefold(),
            str(item.get("imageUrl") or "").strip(),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    if len(items) > 1 and len(deduped) == 1:
        return []
    return deduped


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


def _read_tail_text(path: Path, max_bytes: int) -> str:
    if not path.exists():
        return ""
    size = path.stat().st_size
    with path.open("rb") as handle:
        if size > max_bytes:
            handle.seek(-max_bytes, 2)
        data = handle.read()
    return data.decode("utf-8", errors="replace")


def _systemd_unit_status(label: str, unit: str) -> dict[str, object]:
    try:
        result = subprocess.run(
            ["systemctl", "is-active", unit],
            check=False,
            capture_output=True,
            text=True,
            timeout=1.5,
        )
    except FileNotFoundError:
        return {"name": label, "status": "unknown", "detail": f"{unit}: systemctl unavailable"}
    except subprocess.TimeoutExpired:
        return {"name": label, "status": "unknown", "detail": f"{unit}: status timeout"}
    status = (result.stdout or result.stderr or "unknown").strip().splitlines()[0]
    normalized = {
        "active": "running",
        "inactive": "stopped",
        "failed": "failed",
        "activating": "starting",
        "deactivating": "stopping",
    }.get(status, "unknown")
    return {"name": label, "status": normalized, "detail": f"{unit}: {status}"}


if __name__ == "__main__":
    main()
