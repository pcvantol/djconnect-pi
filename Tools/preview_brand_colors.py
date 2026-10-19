"""Render actual Pi pages with isolated fixtures; no HA, pairing or service changes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import Mock, patch

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QTimer, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtTest import QTest
from shiboken6 import delete

from djconnect_pi.app import DJConnectBackend
from djconnect_pi.brand_theme import apply_palette
from djconnect_pi.config import Config, save_config
from djconnect_pi.session_history_view import presented_history, search_page
from djconnect_pi.session_projection import history_page
from djconnect_pi.update_ui import UpdateUiBackend

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    warnings = []
    qInstallMessageHandler(lambda kind, context, message: warnings.append(message))
    QQuickStyle.setStyle("Basic")
    app = QGuiApplication([])
    apply_palette(app)
    checks = []
    for width, height, profile in [(720, 720, "pi-zero-2w-arm64"), (1200, 1920, "pi5-arm64")]:
        config = args.output / f"fixture-{width}.json"
        save_config(config, Config(language="nl", release_profile=profile, log_file=str(args.output / "fixture.log"), screen_timeout_seconds=0))
        with patch.object(QTimer, "singleShot"):
            backend = DJConnectBackend(config)
        for timer in backend.findChildren(QTimer):
            timer.stop()
        backend._executor.submit = Mock()
        engine = QQmlApplicationEngine()
        engine.rootContext().setContextProperty("djconnect", backend)
        engine.rootContext().setContextProperty("startWindowed", True)
        engine.load(str(ROOT / "src/djconnect_pi/qml/Main.qml"))
        assert engine.rootObjects(), warnings
        window = engine.rootObjects()[0]
        window.setWidth(width)
        window.setHeight(height)
        window.setProperty("splashVisible", False)

        def capture(name):
            QTest.qWait(200)
            image = window.grabWindow()
            assert not image.isNull(), name
            target = args.output / f"{name}-{width}x{height}.png"
            assert image.save(str(target))
            checks.append({"screen": name, "size": [image.width(), image.height()], "file": target.name})

        capture("pairing")
        backend.enterDemoMode()
        backend._toast_visible = False
        backend.toastChanged.emit()
        for screen in ["session", "history", "now", "control", "queue", "playlists", "askdj", "trackinsight", "discover", "musicdna", "more", "settings", "games"]:
            window.setProperty("activeScreen", screen)
            capture(screen)
        # Render retained source/receipt kinds and the real search popup; data remains a fixture.
        tail = json.loads((ROOT / "tests/fixtures/session_core/retention-v2-touch.json").read_text())["tail_window"]
        sid = tail["session"]["session_id"]
        owner = backend.djSession
        owner._timeline = presented_history(history_page(tail, session_id=sid))
        owner._caps = {"capabilities": {"session_conversation_history": True, "session_flow_text_search": True},
                       "contract_versions": {"session_history_entries": 2, "session_flow_text_search": 1}}
        owner.changed.emit()
        window.setProperty("activeScreen", "history")
        capture("history-detail")
        session_item = window.findChild(QObject, "djSessionScreen")
        assert session_item is not None
        assert QMetaObject.invokeMethod(session_item, "showSearch")
        keyboard = window.findChild(QObject, "sessionTouchKeyboard")
        search_input = window.findChild(QObject, "sessionSearchInput")
        assert keyboard is not None and search_input is not None
        assert QMetaObject.invokeMethod(keyboard, "insertKey", Q_ARG("QVariant", "é"))
        assert search_input.property("text") == "é"
        assert QMetaObject.invokeMethod(keyboard, "deleteKey")
        assert search_input.property("text") == ""
        assert QMetaObject.invokeMethod(keyboard, "insertKey", Q_ARG("QVariant", "synthetic"))
        assert search_input.property("text") == "synthetic"
        matches = [dict(tail["entries"][i], highlights=[{"start_utf16": 2, "length_utf16": 9}]) for i in (0, 3)]
        owner._search = search_page({"success": True, "schema_version": 2, "history_contract_version": 2,
            "session_id": sid, "query": "synthetic", "revision": tail["revision"], "matches": matches,
            "returned_count": 2, "total_count": 2, "complete": True, "next_cursor": None,
            "normalization": "NFKC-casefold", "highlight_units": "utf16"}, sid, "synthetic")
        owner.changed.emit()
        capture("history-search")
        owner.invalidate()
        assert search_input.property("text") == "", "Private query survives context invalidation"
        owner.closeSaved()
        window.setProperty("activeScreen", "now")
        window.setProperty("aboutOpen", True)
        capture("about")
        window.setProperty("aboutOpen", False)
        backend.showLogs()
        capture("logs")
        backend.hideLogs()
        window.setProperty("rebootConfirmOpen", True)
        capture("confirmation")
        backend.shutdown()
        delete(window)
        delete(engine)
        updater = UpdateUiBackend(args.output / "update-fixture.json", "http://127.0.0.1:18080", "nl", profile)
        updater._progress = 42
        updater._current_version = "fixture"
        updater._target_version = "fixture-next"
        updater._message = "DJConnect"
        engine = QQmlApplicationEngine()
        engine.rootContext().setContextProperty("updater", updater)
        engine.rootContext().setContextProperty("startWindowed", True)
        engine.load(str(ROOT / "src/djconnect_pi/qml/UpdateProgress.qml"))
        assert engine.rootObjects(), warnings
        window = engine.rootObjects()[0]
        window.setWidth(width)
        window.setHeight(height)
        QTest.qWait(600)
        capture("updater")
        delete(window)
        delete(engine)
    errors = [message for message in warnings if any(word in message for word in ("ReferenceError", "TypeError", "Error:", "Cannot assign", "is not a type", "failed to load"))]
    (args.output / "readback.json").write_text(json.dumps({"checks": checks, "qml_errors": errors, "proof": "offline fixture rendering, not installed or physical acceptance"}, indent=2))
    assert not errors, errors
    print(f"{len(checks)} actual QML page views; no QML errors")


if __name__ == "__main__":
    main()
