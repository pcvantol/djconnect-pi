from __future__ import annotations

import json
from unittest.mock import Mock, patch

import pytest
from PySide6.QtCore import QCoreApplication, QTimer
from shiboken6 import delete

from djconnect_pi.app import DJConnectBackend, configure_graphics
from djconnect_pi.config import (
    Config,
    effective_glass_enabled,
    load_config,
    save_config,
)

_APP = None


@pytest.mark.parametrize("profile,expected", [("pi5-arm64", True), ("pi-zero-2w-arm64", False), ("", False), ("unknown", False)])
def test_profile_default_is_read_only_until_user_choice(tmp_path, profile, expected):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"device_id": "djconnect-raspberry-pi-test", "release_profile": profile}))
    before = path.read_bytes()
    cfg = load_config(path)
    assert cfg.glass_enabled is None
    assert effective_glass_enabled(cfg) is expected
    assert path.read_bytes() == before


@pytest.mark.parametrize("choice", [False, True])
@pytest.mark.parametrize("profile", ["pi5-arm64", "pi-zero-2w-arm64"])
def test_explicit_choice_survives_roundtrip_and_profile_change(tmp_path, choice, profile):
    path = tmp_path / "config.json"
    cfg = Config(device_id="djconnect-raspberry-pi-test", release_profile=profile, glass_enabled=choice)
    save_config(path, cfg)
    loaded = load_config(path)
    assert loaded.glass_enabled is choice
    loaded.release_profile = "pi5-arm64" if profile != "pi5-arm64" else "pi-zero-2w-arm64"
    assert effective_glass_enabled(loaded) is choice


@pytest.mark.parametrize("bad", [0, 1, "false", "true", [], {}, None])
def test_malformed_preference_cannot_be_truthy(tmp_path, bad):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"device_id": "djconnect-raspberry-pi-test", "release_profile": "pi-zero-2w-arm64", "glass_enabled": bad}))
    cfg = load_config(path)
    assert cfg.glass_enabled is None
    assert effective_glass_enabled(cfg) is False


@pytest.mark.parametrize("profile", ["pi5-arm64", "pi-zero-2w-arm64"])
def test_local_toggle_preserves_pairing_profile_and_does_not_call_server(tmp_path, profile):
    global _APP
    _APP = QCoreApplication.instance() or QCoreApplication([])
    path = tmp_path / "config.json"
    save_config(path, Config(device_id="djconnect-raspberry-pi-test", release_profile=profile, paired=True,
                            device_token="synthetic", active_profile_id="profile-test", explicit_profile_id="profile-test"))
    backend = DJConnectBackend(path)
    for timer in backend.findChildren(QTimer):
        timer.stop()
    client = backend.client
    backend.client = Mock()
    changed = Mock()
    backend.glassChanged.connect(changed)
    try:
        assert backend.setGlassEnabled(False)
        assert backend.glassEnabled is False
        assert backend.setGlassEnabled(True)
        assert backend.glassEnabled is True
        count = changed.call_count
        assert backend.setGlassEnabled(True)
        assert changed.call_count == count
        assert not backend.setGlassEnabled("false")
        assert backend.client.mock_calls == []
        cfg = load_config(path)
        assert cfg.paired and cfg.device_token == "synthetic"
        assert cfg.active_profile_id == cfg.explicit_profile_id == "profile-test"
        saved = path.read_bytes()
        with patch("djconnect_pi.app.save_config", side_effect=OSError("synthetic disk full")), patch.object(backend, "showToastForContext") as toast:
            assert not backend.setGlassEnabled(False)
            assert backend.glassEnabled is True
            assert path.read_bytes() == saved
            toast.assert_called_once()
        cfg.glass_enabled = False
        save_config(path, cfg)
        changed.reset_mock()
        with patch.object(backend, "_invalidate_shared_settings_if_context_changed"):
            backend._sync_config_from_disk()
        assert backend.glassEnabled is False
        changed.assert_called_once()
        assert backend.cfg.explicit_profile_id == "profile-test"
    finally:
        backend.client = client
        backend.shutdown()
        for pool in (backend._executor, backend._session_executor, backend._question_executor):
            pool.shutdown(wait=True, cancel_futures=True)
        delete(backend)


@pytest.mark.parametrize("profile", ["pi5-arm64", "pi-zero-2w-arm64", ""])
def test_graphics_request_is_pi5_only_and_respects_operator_overrides(profile):
    env = {}
    configure_graphics(Config(release_profile=profile), env)
    assert env == ({"QT_QUICK_BACKEND": "rhi", "QSG_RHI_BACKEND": "opengl"} if profile == "pi5-arm64" else {})
    override = {"QT_QUICK_BACKEND": "software", "QSG_RHI_BACKEND": "vulkan"}
    configure_graphics(Config(release_profile=profile), override)
    assert override == {"QT_QUICK_BACKEND": "software", "QSG_RHI_BACKEND": "vulkan"}
