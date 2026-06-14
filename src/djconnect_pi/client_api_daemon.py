from __future__ import annotations

from pathlib import Path
import argparse
import json
import logging
import signal
import sys
import threading
import time

from .client_api import ClientAPI, ClientAPIState
from .config import DEFAULT_CONFIG_PATH, Config, load_config, save_config
from .logging_config import setup_logging
from .system_info import log_raspberry_pi_system_info

_LOGGER = logging.getLogger(__name__)
SCREENSHOT_TIMEOUT_SECONDS = 8.0


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
                dj_response_handler=self._dj_response,
                screenshot_handler=self._screenshot,
                pair_handler=self._paired,
                forget_handler=self._forgotten,
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
                return {
                    "success": True,
                    "path": str(target),
                    "content_type": "image/png",
                    "size": target.stat().st_size,
                }
            time.sleep(0.2)
        return {"success": False, "error": "screenshot_timeout", "path": str(target)}

    def _paired(self) -> None:
        self.cfg = load_config(self.config_path)
        _LOGGER.info("Client API pairing stored for %s", self.cfg.device_id)

    def _forgotten(self) -> None:
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


if __name__ == "__main__":
    main()
