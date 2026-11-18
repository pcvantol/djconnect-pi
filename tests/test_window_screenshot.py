from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from PySide6.QtGui import QColor, QImage

from djconnect_pi import app as app_module


def capture(tmp_path, monkeypatch, image=None, *, visible=True):
    class Window:
        isVisible = Mock(return_value=visible)
        grabWindow = Mock(return_value=image)

    monkeypatch.setattr(app_module, "QQuickWindow", Window)
    backend = SimpleNamespace(cfg=SimpleNamespace(screenshot_file=str(tmp_path / "screenshot.png")))
    return backend, Window()


def test_window_screenshot_writes_complete_png_at_configured_path(tmp_path, monkeypatch):
    image = QImage(32, 48, QImage.Format.Format_RGB32)
    image.fill(QColor("#3a7bd5"))
    backend, window = capture(tmp_path, monkeypatch, image)
    target = Path(backend.cfg.screenshot_file)
    target.write_bytes(b"previous image")

    assert app_module.DJConnectBackend.saveWindowScreenshot(backend, window)

    saved = QImage(str(target))
    assert (saved.width(), saved.height()) == (32, 48)
    assert saved.pixelColor(16, 24) == QColor("#3a7bd5")
    assert target.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert list(tmp_path.iterdir()) == [target]


@pytest.mark.parametrize("case", ["wrong_type", "hidden", "null_image", "encode_failure", "grab_failure", "deleted_window"])
def test_window_screenshot_failure_keeps_previous_complete_file(tmp_path, monkeypatch, case):
    image = Mock()
    image.isNull.return_value = False
    image.save.return_value = False
    backend, window = capture(tmp_path, monkeypatch, image, visible=case != "hidden")
    target = Path(backend.cfg.screenshot_file)
    target.write_bytes(b"previous complete image")
    if case == "wrong_type":
        window = object()
    elif case == "null_image":
        image.isNull.return_value = True
    elif case == "grab_failure":
        window.grabWindow.side_effect = RuntimeError("Window is no longer available")
    elif case == "deleted_window":
        window.isVisible.side_effect = RuntimeError("Deleted Qt wrapper")

    assert not app_module.DJConnectBackend.saveWindowScreenshot(backend, window)
    assert target.read_bytes() == b"previous complete image"
    assert list(tmp_path.iterdir()) == [target]
    if case == "hidden":
        window.grabWindow.assert_not_called()


def test_window_screenshot_does_not_create_missing_parent_directory(tmp_path, monkeypatch):
    image = Mock()
    image.isNull.return_value = False
    backend, window = capture(tmp_path, monkeypatch, image)
    backend.cfg.screenshot_file = str(tmp_path / "missing" / "screenshot.png")

    assert not app_module.DJConnectBackend.saveWindowScreenshot(backend, window)
    image.save.assert_not_called()
    assert list(tmp_path.iterdir()) == []
