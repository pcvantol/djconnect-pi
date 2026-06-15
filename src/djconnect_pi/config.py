from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import json
import locale
import os
import re
import secrets
import uuid

from .i18n import normalize_language

CLIENT_TYPE = "raspberry_pi"
PROTOCOL_VERSION = "3.1.57"
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
    local_api_host: str = "0.0.0.0"
    local_api_port: int = 18080
    screen_timeout_seconds: int = 120
    screen_brightness_percent: int = 100
    language: str = field(default_factory=lambda: default_language_from_system())
    log_file: str = str(DEFAULT_LOG_PATH)
    dj_response_file: str = str(DEFAULT_LOG_PATH.parent / "dj-response.json")
    command_event_file: str = str(DEFAULT_LOG_PATH.parent / "command-event.json")
    screenshot_event_file: str = str(DEFAULT_LOG_PATH.parent / "screenshot-request.json")
    screenshot_file: str = str(DEFAULT_LOG_PATH.parent / "screenshot.png")
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
    if language.startswith("nl"):
        return "nl"
    if language.startswith("en"):
        return "en"
    return "en"


def load_config(path: Path) -> Config:
    if not path.exists():
        cfg = Config(device_id=stable_device_id())
        save_config(path, cfg)
        return cfg
    data = json.loads(path.read_text(encoding="utf-8"))
    cfg = Config(**{**asdict(Config()), **data})
    if not cfg.device_id:
        cfg.device_id = stable_device_id()
    if cfg.device_name in {"", "DJConnect Pi"}:
        cfg.device_name = "DJConnect"
    cfg.version = PROTOCOL_VERSION
    if not re.fullmatch(r"\d{6}", str(cfg.pairing_code)):
        cfg.pairing_code = generate_pairing_code()
    cfg.screen_timeout_seconds = max(0, int(cfg.screen_timeout_seconds))
    cfg.screen_brightness_percent = max(10, min(100, int(cfg.screen_brightness_percent)))
    cfg.local_api_port = max(1, min(65535, int(cfg.local_api_port)))
    cfg.language = normalize_language(cfg.language)
    if cfg.update_channel not in {"stable", "beta"}:
        cfg.update_channel = "stable"
    return cfg


def save_config(path: Path, cfg: Config) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(json.dumps(asdict(cfg), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.chmod(0o600)
    tmp_path.replace(path)
    path.chmod(0o600)
