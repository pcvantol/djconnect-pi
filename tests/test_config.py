import json
import stat
from pathlib import Path
from unittest.mock import patch

from djconnect_pi.config import CLIENT_TYPE, PROTOCOL_VERSION, Config, default_language_from_system, generate_pairing_code, load_config, save_config


def test_default_config_uses_raspberry_pi_client_type(tmp_path: Path) -> None:
    cfg = load_config(tmp_path / "config.json")
    assert CLIENT_TYPE == "raspberry_pi"
    assert cfg.device_id.startswith("djconnect-raspberry-pi-")
    assert len(cfg.pairing_code) == 6
    assert cfg.pairing_code.isdigit()
    assert cfg.screen_timeout_seconds == 120
    assert cfg.update_repo == "pcvantol/djconnect-pi-releases"
    assert cfg.device_name == "DJConnect"
    assert cfg.websocket_fast_path_enabled is False
    assert cfg.ha_websocket_token == ""


def test_save_and_load_config_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    save_config(
        path,
        Config(
            ha_url="http://homeassistant.local:8123",
            device_id="djconnect-raspberry-pi-ABCDEF123456",
            device_token="secret",
            paired=True,
            websocket_fast_path_enabled=True,
            ha_websocket_token="ha-secret",
        ),
    )

    loaded = load_config(path)

    assert loaded.ha_url == "http://homeassistant.local:8123"
    assert loaded.device_id == "djconnect-raspberry-pi-ABCDEF123456"
    assert loaded.device_token == "secret"
    assert loaded.paired is True
    assert loaded.websocket_fast_path_enabled is True
    assert loaded.ha_websocket_token == "ha-secret"
    assert len(loaded.pairing_code) == 6
    assert loaded.pairing_code.isdigit()


def test_generate_pairing_code_returns_six_digits() -> None:
    code = generate_pairing_code()

    assert len(code) == 6
    assert code.isdigit()


def test_save_config_writes_private_file_permissions(tmp_path: Path) -> None:
    path = tmp_path / "config.json"

    save_config(path, Config(device_token="secret"))

    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_load_config_backfills_missing_device_id(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"ha_url": "http://ha"}), encoding="utf-8")

    loaded = load_config(path)

    assert loaded.device_id.startswith("djconnect-raspberry-pi-")
    assert len(loaded.pairing_code) == 6
    assert loaded.pairing_code.isdigit()


def test_load_config_normalizes_runtime_settings(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "device_name": "DJConnect Pi",
                "version": "3.1.25",
                "screen_timeout_seconds": -5,
                "screen_brightness_percent": 900,
                "update_channel": "nightly",
                "language": "de",
            }
        ),
        encoding="utf-8",
    )

    loaded = load_config(path)

    assert loaded.screen_timeout_seconds == 0
    assert loaded.screen_brightness_percent == 100
    assert loaded.update_channel == "stable"
    assert loaded.language == "nl"
    assert loaded.device_name == "DJConnect"
    assert loaded.version == PROTOCOL_VERSION


def test_default_language_uses_raspberry_pi_locale() -> None:
    with patch("djconnect_pi.config.locale.getlocale", return_value=("nl_NL", "UTF-8")):
        assert default_language_from_system() == "nl"

    with patch("djconnect_pi.config.locale.getlocale", return_value=("en_GB", "UTF-8")):
        assert default_language_from_system() == "en"


def test_default_language_falls_back_to_english_for_unknown_locale() -> None:
    with (
        patch("djconnect_pi.config.locale.getlocale", return_value=("de_DE", "UTF-8")),
        patch.dict("djconnect_pi.config.os.environ", {}, clear=True),
    ):
        assert default_language_from_system() == "en"
