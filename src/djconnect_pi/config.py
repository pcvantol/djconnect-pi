from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
import re
import uuid

CLIENT_TYPE = "raspberry_pi"
PROTOCOL_VERSION = "3.1.17"
DEFAULT_CONFIG_PATH = Path.home() / ".config" / "djconnect-pi" / "config.json"
DEFAULT_LOG_PATH = Path.home() / ".local" / "state" / "djconnect-pi" / "client.log"


@dataclass
class Config:
    ha_url: str = ""
    device_id: str = ""
    device_name: str = "DJConnect Pi"
    device_token: str = ""
    paired: bool = False
    version: str = PROTOCOL_VERSION
    update_repo: str = "pcvantol/djconnect-pi"
    update_channel: str = "stable"
    screen_timeout_seconds: int = 300
    log_file: str = str(DEFAULT_LOG_PATH)
    log_level: str = "INFO"


def stable_device_id() -> str:
    raw = uuid.getnode().to_bytes(6, "big").hex().upper()
    suffix = re.sub(r"[^A-Z0-9]", "", raw)[:12].ljust(12, "0")
    return f"djconnect-raspberry-pi-{suffix}"


def load_config(path: Path) -> Config:
    if not path.exists():
        cfg = Config(device_id=stable_device_id())
        save_config(path, cfg)
        return cfg
    data = json.loads(path.read_text(encoding="utf-8"))
    cfg = Config(**{**asdict(Config()), **data})
    if not cfg.device_id:
        cfg.device_id = stable_device_id()
    cfg.screen_timeout_seconds = max(0, int(cfg.screen_timeout_seconds))
    if cfg.update_channel not in {"stable", "beta"}:
        cfg.update_channel = "stable"
    return cfg


def save_config(path: Path, cfg: Config) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(cfg), indent=2, sort_keys=True) + "\n", encoding="utf-8")
