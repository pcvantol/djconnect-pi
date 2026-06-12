import json
from pathlib import Path

from djconnect_pi.config import CLIENT_TYPE, Config, load_config, save_config


def test_default_config_uses_raspberry_pi_client_type(tmp_path: Path) -> None:
    cfg = load_config(tmp_path / "config.json")
    assert CLIENT_TYPE == "raspberry_pi"
    assert cfg.device_id.startswith("djconnect-raspberry-pi-")


def test_save_and_load_config_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    save_config(
        path,
        Config(
            ha_url="http://homeassistant.local:8123",
            device_id="djconnect-raspberry-pi-ABCDEF123456",
            device_token="secret",
            paired=True,
        ),
    )

    loaded = load_config(path)

    assert loaded.ha_url == "http://homeassistant.local:8123"
    assert loaded.device_id == "djconnect-raspberry-pi-ABCDEF123456"
    assert loaded.device_token == "secret"
    assert loaded.paired is True


def test_load_config_backfills_missing_device_id(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"ha_url": "http://ha"}), encoding="utf-8")

    loaded = load_config(path)

    assert loaded.device_id.startswith("djconnect-raspberry-pi-")
