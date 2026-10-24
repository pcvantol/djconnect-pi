import json
import socket
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from PySide6.QtCore import QObject, QPoint, Qt, QTimer, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtTest import QTest
from shiboken6 import delete

from djconnect_pi.app import DJConnectBackend
from djconnect_pi.brand_theme import apply_palette
from djconnect_pi.config import Config, save_config

ROOT = Path(__file__).resolve().parents[2]
TEMP = tempfile.TemporaryDirectory()
OUT = Path(TEMP.name)
warnings = []
qInstallMessageHandler(lambda k, c, m: warnings.append(m))
QQuickStyle.setStyle("Basic")
app = QGuiApplication([])
apply_palette(app)
rows = []


def find(item, name):
    if item.objectName() == name:
        return item
    for c in item.childItems():
        r = find(c, name)
        if r is not None:
            return r
    return None


def click(w, item):
    assert item and item.property("visible")
    p = item.mapToScene(QPoint(int(item.width() / 2), int(item.height() / 2)))
    QTest.mouseClick(w, Qt.LeftButton, Qt.NoModifier, QPoint(int(p.x()), int(p.y())))
    QTest.qWait(100)


with (
    patch(
        "requests.sessions.Session.request",
        side_effect=AssertionError("network forbidden"),
    ),
    patch.object(
        socket.socket, "connect", side_effect=AssertionError("socket forbidden")
    ),
    patch("subprocess.run", side_effect=AssertionError("OS forbidden")),
):
    for width, height, profile in [
        (720, 720, "pi-zero-2w-arm64"),
        (1200, 1920, "pi5-arm64"),
    ]:
        if width != int(sys.argv[1]):
            continue
        cfg = OUT / f"fixture-{width}.json"
        save_config(
            cfg,
            Config(
                language="nl",
                release_profile=profile,
                screen_timeout_seconds=0,
                paired=True,
                device_token="synthetic",
                device_id="djconnect-raspberry-pi-fixture",
                ha_url="http://fixture.invalid",
                active_profile_id="owner",
                explicit_profile_id="owner",
                active_profile_type="personal",
                active_profile_privacy_mode="private",
                log_file=str(OUT / "fixture.log"),
            ),
        )
        b = DJConnectBackend(cfg)
        for timer in b.findChildren(QTimer):
            timer.stop()
        pools = [b._executor, b._session_executor, b._question_executor]
        for pool in pools:
            pool.submit = Mock()
        owner = b.djSession
        e = QQmlApplicationEngine()
        e.rootContext().setContextProperty("djconnect", b)
        e.rootContext().setContextProperty("startWindowed", True)
        e.load(str(ROOT / "src/djconnect_pi/qml/Main.qml"))
        assert e.rootObjects(), warnings
        w = e.rootObjects()[0]
        w.setWidth(width)
        w.setHeight(height)
        w.setProperty("splashVisible", False)
        w.setProperty("activeScreen", "session")
        w.requestActivate()
        QTest.qWait(500)

        def reset(b=b, owner=owner, w=w):
            b.cfg.paired = True
            b.cfg.active_profile_id = "owner"
            b.cfg.explicit_profile_id = "owner"
            b._demo_mode = False
            owner._session = {
                "session_id": "original-session",
                "runtime_state": "active",
                "selected_mood": "groove",
                "broadcast": {"session": {"session_id": "original-session"}},
            }
            owner._loaded = True
            owner._foreground = True
            owner._caps = {
                "capabilities": {"session_forecast": True},
                "contract_versions": {"session_forecast": 1},
            }
            b.settingsChanged.emit()
            b.pairedChanged.emit()
            b.profileChanged.emit()
            owner.changed.emit()
            w.setProperty("activeScreen", "session")
            QTest.qWait(100)

        for lang in ["nl"]:
            b.setLanguage(lang)
            b._toast_visible = False
            b.toastChanged.emit()
            reset()
            button = find(w.contentItem(), "sessionVibeScapeMode")
            assert button is not None
            if profile != "pi5-arm64":
                assert not button.property("visible")
                assert not w.property("vibeScapeAllowed")
                w.openVibeScape()
                assert not w.property("vibeScapeRequested")
                rows.append(
                    {"profile": profile, "locale": lang, "case": "no-entry-or-loader"}
                )
                continue
            assert w.property("vibeScapeAllowed"), (
                w.property("active"),
                b.paired,
                w.property("vibeScapeAllowed"),
            )
            w.grabWindow().save(str(OUT / f"{lang}-before.png"))
            click(w, button)
            visit = find(w.contentItem(), "vibeScapeVisit")
            w.grabWindow().save(str(OUT / f"{lang}-after.png"))
            assert visit is not None, (
                button.mapToScene(QPoint(0, 0)),
                button.width(),
                button.height(),
                w.property("vibeScapeAllowed"),
                w.property("vibeScapeRequested"),
                w.property("activeScreen"),
                w.property("active"),
                warnings,
            )
            assert not w.property("screenBlanked")
            assert owner._session["session_id"] == "original-session"
            timer = w.findChild(QObject, "returnToNowTimer")
            assert timer and not timer.property("running")
            timer.triggered.emit()  # A previously queued expiry cannot exit this visit.
            QTest.qWait(30)
            assert find(w.contentItem(), "vibeScapeVisit") is not None
            assert not visit.property(
                "renderable"
            )  # CI software scenegraph: honest unavailable, never fake GPU.
            im = w.grabWindow()
            assert not im.isNull()
            assert im.save(str(OUT / f"{lang}-native-main.png"))
            click(w, find(w.contentItem(), "vibeScapeFlow"))
            assert find(w.contentItem(), "vibeScapeVisit") is None
            assert timer.property("running")
            assert (
                w.property("vibeScapeOwner") == ""
                and w.property("vibeScapeSession") == ""
            )
            rows.append(
                {
                    "profile": profile,
                    "locale": lang,
                    "case": "click-entry-render-flow-return",
                }
            )
            for withdrawal in [
                "session",
                "profile",
                "background",
                "unpaired",
                "lifecycle",
                "navigation",
            ]:
                reset()
                click(w, find(w.contentItem(), "sessionVibeScapeMode"))
                assert find(w.contentItem(), "vibeScapeVisit")
                if withdrawal == "session":
                    owner._session["session_id"] = "successor"
                    owner.changed.emit()
                elif withdrawal == "profile":
                    b.cfg.active_profile_id = "successor"
                    b.profileChanged.emit()
                    owner.changed.emit()
                elif withdrawal == "background":
                    w.hide()
                elif withdrawal == "unpaired":
                    b.cfg.paired = False
                    b.pairedChanged.emit()
                elif withdrawal == "lifecycle":
                    owner._session["runtime_state"] = "ending"
                    owner.changed.emit()
                else:
                    w.setProperty("activeScreen", "now")
                assert not w.property("vibeScapeRequested"), withdrawal  # Immediate intent withdrawal.
                QTest.qWait(60)
                assert find(w.contentItem(), "vibeScapeVisit") is None, withdrawal
                if withdrawal == "background":
                    w.show()
                    w.requestActivate()
                    QTest.qWait(60)
                assert not w.property("vibeScapeRequested"), withdrawal
                rows.append({"profile": profile, "locale": lang, "case": withdrawal})
            reset()
            click(w, find(w.contentItem(), "sessionVibeScapeMode"))
            click(w, find(w.contentItem(), "vibeScapeForecast"))
            assert not w.property("vibeScapeRequested")
            # Rendering and all local gestures must not queue an app/HA action.
            # Foreground recovery may queue the existing independent owner refresh.
            jobs = [
                getattr(c.args[0], "__qualname__", "")
                for pool in pools
                for c in pool.submit.call_args_list
            ]
            assert all(
                name == "SessionController._launch.<locals>.worker" for name in jobs
            ), jobs
            assert (
                owner._running_action in ("", "refresh") and not owner._question_running
            ), owner._running_action
            for pool in pools:
                pool.submit.reset_mock()
        b.shutdown()
        QTest.qWait(20)
        delete(w)
        delete(e)
        for p in pools:
            p.shutdown(wait=True, cancel_futures=True)
        delete(b)
errors = [
    m
    for m in warnings
    if any(
        x in m
        for x in [
            "ReferenceError",
            "TypeError",
            "Error:",
            "Cannot assign",
            "Binding loop detected",
            "failed to load",
        ]
    )
]
(OUT / "verification.json").write_text(
    json.dumps(
        {
            "cases": rows,
            "warnings": warnings,
            "errors": errors,
            "scope": "SYNTHETIC_VM_NOT_INSTALLED_NOT_PI_GPU",
        },
        indent=2,
    )
)
assert not errors, errors
print("PASS:", len(rows), "synthetic VibeScape admission/exit cases; no GPU claim")
