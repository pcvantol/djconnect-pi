from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import json
import locale
import os
import re
import secrets
import uuid
from typing import Any

from .i18n import normalize_language

CLIENT_TYPE = "raspberry_pi"
PROTOCOL_VERSION = "3.2.20"
DEFAULT_CONFIG_PATH = Path.home() / ".config" / "djconnect-pi" / "config.json"
DEFAULT_LOG_PATH = Path.home() / ".local" / "state" / "djconnect-pi" / "client.log"


@dataclass
class Config:
    ha_url: str = ""
    device_id: str = ""
    device_name: str = "DJConnect"
    device_token: str = ""
    paired: bool = False
    pairing_code: str = field(default_factory=lambda: generate_pairing_code())
    version: str = PROTOCOL_VERSION
    update_repo: str = "pcvantol/djconnect-pi-releases"
    update_channel: str = "stable"
    local_url: str = ""
    # The Pi local API intentionally listens on the LAN by default.
    local_api_host: str = "0.0.0.0"  # nosec B104
    local_api_port: int = 18080
    screen_timeout_seconds: int = 120
    return_to_now_seconds: int = 60
    screen_brightness_percent: int = 100
    language: str = field(default_factory=lambda: default_language_from_system())
    log_file: str = str(DEFAULT_LOG_PATH)
    music_backend: str = ""
    music_backend_name: str = ""
    music_backend_available: bool = True
    music_backend_revision: int = 0
    music_backend_capabilities: dict[str, Any] = field(default_factory=dict)
    music_target_player: dict[str, str] = field(default_factory=dict)
    music_backend_error: str = ""
    music_dna_key: str = ""
    mood: int | None = None
    dj_announcement_output: str = "text_only"
    dj_announcement_output_user_set: bool = False
    websocket_fast_path_enabled: bool = True
    ha_websocket_token: str = ""
    dj_response_file: str = str(DEFAULT_LOG_PATH.parent / "dj-response.json")
    command_event_file: str = str(DEFAULT_LOG_PATH.parent / "command-event.json")
    screenshot_event_file: str = str(DEFAULT_LOG_PATH.parent / "screenshot-request.json")
    screenshot_file: str = str(DEFAULT_LOG_PATH.parent / "screenshot.png")
    updater_status_file: str = str(DEFAULT_LOG_PATH.parent / "updater-status.json")
    log_level: str = "INFO"


def stable_device_id() -> str:
    raw = uuid.getnode().to_bytes(6, "big").hex().upper()
    suffix = re.sub(r"[^A-Z0-9]", "", raw)[:12].ljust(12, "0")
    return f"djconnect-raspberry-pi-{suffix}"


def generate_pairing_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def default_language_from_system() -> str:
    candidates = [
        locale.getlocale()[0],
        os.environ.get("LC_ALL"),
        os.environ.get("LC_MESSAGES"),
        os.environ.get("LANG"),
    ]
    language = ""
    for candidate in candidates:
        if candidate:
            language = candidate.lower()
            break
    return normalize_language(language)


def load_config(path: Path) -> Config:
    if not path.exists():
        cfg = Config(device_id=stable_device_id())
        save_config(path, cfg)
        return cfg
    data = json.loads(path.read_text(encoding="utf-8"))
    cfg = Config(**{**asdict(Config()), **data})
    if "updater_status_file" not in data and path.name == "client.json":
        cfg.updater_status_file = str(path.parent / "updater-status.json")
    if not cfg.device_id:
        cfg.device_id = stable_device_id()
    if cfg.device_name in {"", "DJConnect Pi"}:
        cfg.device_name = "DJConnect"
    cfg.version = PROTOCOL_VERSION
    if not re.fullmatch(r"\d{6}", str(cfg.pairing_code)):
        cfg.pairing_code = generate_pairing_code()
    cfg.screen_timeout_seconds = max(0, int(cfg.screen_timeout_seconds))
    cfg.return_to_now_seconds = _normalize_return_to_now_seconds(cfg.return_to_now_seconds)
    cfg.screen_brightness_percent = max(10, min(100, int(cfg.screen_brightness_percent)))
    cfg.mood = _optional_mood(cfg.mood)
    cfg.dj_announcement_output = normalize_dj_announcement_output(
        cfg.dj_announcement_output,
        cfg.music_backend_capabilities,
    )
    cfg.local_api_port = max(1, min(65535, int(cfg.local_api_port)))
    cfg.language = normalize_language(cfg.language)
    if cfg.update_channel not in {"stable", "beta"}:
        cfg.update_channel = "stable"
    cfg.dj_announcement_output_user_set = bool(cfg.dj_announcement_output_user_set)
    return cfg


def _optional_mood(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return max(0, min(100, int(value)))
    except (TypeError, ValueError):
        return None


def _normalize_return_to_now_seconds(value: object) -> int:
    try:
        seconds = int(value)
    except (TypeError, ValueError):
        return 60
    return seconds if seconds in {0, 30, 60, 120} else 60


def dj_announcement_speaker_configured(capabilities: dict[str, Any] | None) -> bool:
    announcement = capabilities.get("dj_announcement") if isinstance(capabilities, dict) else None
    if isinstance(announcement, dict):
        if announcement.get("speaker_configured") is True:
            return True
        target = announcement.get("target") if isinstance(announcement.get("target"), dict) else {}
        return bool(
            announcement.get("speaker_entity_id")
            or announcement.get("speaker_name")
            or target.get("entity_id")
            or target.get("name")
        )
    return False


def normalize_dj_announcement_output(value: object, capabilities: dict[str, Any] | None = None) -> str:
    output = str(value or "").strip()
    announcement = capabilities.get("dj_announcement") if isinstance(capabilities, dict) else None
    supported = announcement.get("supported_outputs") if isinstance(announcement, dict) else None
    locked = announcement.get("locked_outputs") if isinstance(announcement, dict) else None
    supported_outputs = {str(item).strip() for item in supported if str(item).strip()} if isinstance(supported, list) else set()
    locked_outputs = {str(item).strip() for item in locked if str(item).strip()} if isinstance(locked, list) else set()
    ha_speaker_supported = not supported_outputs or "ha_speaker" in supported_outputs
    if output == "ha_speaker" and output not in locked_outputs and ha_speaker_supported and dj_announcement_speaker_configured(capabilities):
        return "ha_speaker"
    return "text_only"


def save_config(path: Path, cfg: Config) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(json.dumps(asdict(cfg), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.chmod(0o600)
    tmp_path.replace(path)
    path.chmod(0o600)
