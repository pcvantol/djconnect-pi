"""Render actual Pi pages with isolated fixtures; no HA, pairing or service changes."""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject, QObject, QPointF, QTimer, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtTest import QTest
from shiboken6 import delete

from djconnect_pi.app import DJConnectBackend
from djconnect_pi.brand_theme import apply_palette
from djconnect_pi.config import Config, save_config
from djconnect_pi.expiry_clock import ExpiryClock
from djconnect_pi.session_history_view import presented_history, search_page
from djconnect_pi.session_projection import history_page, timestamp
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
        backend._session_executor.submit = backend._executor.submit
        backend._question_executor.submit = backend._executor.submit
        engine = QQmlApplicationEngine()
        engine.rootContext().setContextProperty("djconnect", backend)
        engine.rootContext().setContextProperty("startWindowed", True)
        engine.load(str(ROOT / "src/djconnect_pi/qml/Main.qml"))
        assert engine.rootObjects(), warnings
        window = engine.rootObjects()[0]
        window.setWidth(width)
        window.setHeight(height)
        window.setProperty("splashVisible", False)
        # Keep fixture reads explicit; wall-clock polling would race language/scope probes.
        for obj in window.findChildren(QObject):
            if 'Timer' in obj.metaObject().className() and obj.property('interval') in (3000,15000):
                QMetaObject.invokeMethod(obj,'stop')

        def visual_item(item, name):
            if item.objectName() == name:
                return item
            for child in item.childItems():
                found = visual_item(child, name)
                if found is not None:
                    return found
            return None

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
        window.setProperty("activeScreen", "session")
        for runtime_state in ("opening", "ending"):
            backend.djSession._session["runtime_state"] = runtime_state
            backend.djSession.changed.emit()
            capture("session-" + runtime_state)
        backend.djSession._session["runtime_state"] = "active"
        backend.djSession.changed.emit()
        # Explicit synthetic current-grant fixture: decode -> controller -> actual QML,
        # then move elapsed time beyond its original expiry while wall time rolls back.
        owner = backend.djSession
        original_clock = owner._clock
        now = datetime.now(UTC)
        clock_host = SimpleNamespace(wall=now.timestamp(), tick=0)
        owner._clock = ExpiryClock(lambda: clock_host.wall, lambda: clock_host.tick)
        deadline = (now + timedelta(seconds=3)).isoformat()
        owner._session = {"session_id": "preview-native-session", "runtime_state": "active", "broadcast": {
            "session_flow": {"items": [{"item_type": "dj_moment", "moment_id": "preview-moment"}]},
            "dj_moments": [{"moment_id": "preview-moment", "session_id": "preview-native-session",
                "title": "Offline fixture", "content": "Synthetic contribution for expiry rendering.",
                "presentation_intent": {"visibility": "owner_only"}}],
            "native_delivery": {"schema_version": 1, "session_id": "preview-native-session",
                "revision": "preview-native-revision", "revocation_scope": "session",
                "current_moment_id": "preview-moment", "active_flow_moment_ids": ["preview-moment"],
                "admissions": [{"moment_id": "preview-moment", "qualification": "qualified",
                    "executable_actions": [], "current_display_allowed": True, "active_flow_display_allowed": True,
                    "source_expires_at": deadline, "display_expires_at": deadline}]}}}
        owner._expire()
        QTest.qWait(100)
        live_rows = window.findChild(QObject, "sessionLiveMomentRows")
        assert owner.state["moments"] and live_rows is not None and live_rows.property("count") == 1
        scroll = window.findChild(QObject, "sessionHistoryScroll").property("contentItem")
        scroll.setProperty("contentY", max(0, scroll.property("contentHeight") - scroll.property("height")))
        capture("session-native-grant")
        clock_host.wall -= 3600
        clock_host.tick = 4
        owner._expire()
        capture("session-native-expired")
        assert live_rows.property("count") == 0, "Expired source remained rendered"
        owner._expire()  # same cached wire projection cannot resurrect after rollback
        assert not owner.state["moments"]
        owner.setForeground(False)
        capture("session-background-cleared")
        assert not owner.state["session_id"] and not owner.state["timeline"]
        owner.setForeground(True)
        owner._clock = original_clock
        # Unchanged published Core snapshots, frozen at their original render time.
        native_frames = json.loads((ROOT / "tests/fixtures/session_core/native-expressive-snapshots.json").read_text())
        for family, persona in [("birth", "home_dj"), ("formation", "home_dj"), ("description", "home_dj"),
                                ("edition", "home_dj"), ("genre", "home_dj"), ("genre", "club_dj")]:
            snapshot = native_frames[family]["nl"][persona][-1]
            authority = snapshot["native_delivery"]
            grant = next((row for row in authority["admissions"] if row["moment_id"] == authority["current_moment_id"]), None)
            fixture_time = timestamp(grant["display_expires_at"]) - 1 if grant else max(timestamp(row["created_at"]) for row in snapshot["dj_moments"]) + 1
            owner._clock = ExpiryClock(lambda stamp=fixture_time: stamp, lambda: 0)
            owner._session = {**snapshot["session"], "broadcast": snapshot}
            owner._loaded = True
            owner._expire()
            owner.changed.emit()
            QTest.qWait(100)
            scroll.setProperty("contentY", 0)
            capture("core-native-" + family + "-" + persona)
            assert live_rows.property("count") == len(owner.state["moments"])
            if owner.state["moments"]:
                current_card = visual_item(window.contentItem(), "sessionLiveMomentCard")
                assert current_card is not None
                top = current_card.mapToItem(scroll, QPointF(0, 0)).y()
                assert 0 <= top < scroll.property("height") / 2, (width, family, "contribution below fold", top)
            if family == "genre" and persona == "home_dj":
                assert not owner.state["moments"]
        owner._clock = original_clock
        owner._expire()
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
        # Synthetic extra retained rows ensure both viewports can position a non-first anchor.
        extended = deepcopy(owner._timeline)
        for i in range(10):
            extra = deepcopy(tail["entries"][-1])
            extra.update(entry_id=f"preview-extra-{i}", order=100 + i)
            extended["entries"].append(extra)
        owner._timeline = extended
        owner.changed.emit()
        QTest.qWait(100)
        # Recreate real layout replacement and confirm the visible reading identity survives.
        anchor = tail["entries"][1]["entry_id"]
        session_item.setProperty("readingOffset", 0)
        owner.timelineUpdated.emit(anchor)
        QTest.qWait(100)
        actual_anchor = QMetaObject.invokeMethod(session_item, "readingAnchor", Q_RETURN_ARG("QVariant"))
        assert actual_anchor == anchor, (width, actual_anchor, anchor)
        refreshed = deepcopy(owner._timeline)
        refreshed["entries"][0]["text"] = None
        owner._timeline = refreshed
        owner.changed.emit()
        owner.timelineUpdated.emit(anchor)
        QTest.qWait(100)
        actual_anchor = QMetaObject.invokeMethod(session_item, "readingAnchor", Q_RETURN_ARG("QVariant"))
        assert actual_anchor == anchor, (width, "reading position lost", actual_anchor, anchor)
        capture("history-reading-position")
        owner._timeline = presented_history(history_page(tail, session_id=sid))
        owner.changed.emit()
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
        panel = window.findChild(QObject, "sessionSearchPanel")
        panel.setProperty("keyboardVisible", False)
        capture("history-search")
        displayed = visual_item(window.contentItem(), "sessionSearchHighlightedBody")
        assert displayed is not None and "<b><u>synthetic</u></b>" in displayed.property("text")
        search_result = deepcopy(owner._search)
        for locale in ("en", "nl", "de", "fr", "es"):
            backend.setLanguage(locale)
            backend._toast_visible = False
            backend.toastChanged.emit()
            QMetaObject.invokeMethod(panel, "close")
            scroll.setProperty("contentY", 0)
            capture("history-dates-" + locale)
            date_label = visual_item(window.contentItem(), "sessionHistoryEntryDate")
            assert date_label is not None and "2026" in date_label.property("text")
            assert "2026-10-18T" not in date_label.property("text")
            QMetaObject.invokeMethod(session_item, "showSearch")
            panel.setProperty("keyboardVisible", False)
            capture("history-highlights-" + locale)
        backend.setLanguage("nl")
        literal = deepcopy(search_result)
        literal["matches"] = [deepcopy(matches[0])]
        literal["matches"][0].update(text='😀 <img src="https://untrusted.invalid/leak">\nA & B',
            highlights=[{"start_utf16": 0, "length_utf16": 2}])
        literal["returned_count"] = 1
        literal["total_count"] = 1
        owner._search = search_page(literal, sid, "synthetic")
        owner.changed.emit()
        backend._toast_visible = False
        backend.toastChanged.emit()
        capture("history-highlight-literal")
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
