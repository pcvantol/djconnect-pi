from pathlib import Path

from djconnect_pi.config import CLIENT_TYPE, load_config


def test_default_config_uses_raspberry_pi_client_type(tmp_path: Path) -> None:
    cfg = load_config(tmp_path / "config.json")
    assert CLIENT_TYPE == "raspberry_pi"
    assert cfg.device_id.startswith("djconnect-raspberry-pi-")

