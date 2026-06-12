import json
import stat
from pathlib import Path
from unittest.mock import patch

from djconnect_pi.config import CLIENT_TYPE, Config, default_language_from_system, load_config, save_config


def test_default_config_uses_raspberry_pi_client_type(tmp_path: Path) -> None:
    cfg = load_config(tmp_path / "config.json")
    assert CLIENT_TYPE == "raspberry_pi"
    assert cfg.device_id.startswith("djconnect-raspberry-pi-")
    assert cfg.screen_timeout_seconds == 120
    assert cfg.update_repo == "pcvantol/djconnect-pi-releases"


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


def test_save_config_writes_private_file_permissions(tmp_path: Path) -> None:
    path = tmp_path / "config.json"

    save_config(path, Config(device_token="secret"))

    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_load_config_backfills_missing_device_id(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"ha_url": "http://ha"}), encoding="utf-8")

    loaded = load_config(path)

    assert loaded.device_id.startswith("djconnect-raspberry-pi-")


def test_load_config_normalizes_runtime_settings(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
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
