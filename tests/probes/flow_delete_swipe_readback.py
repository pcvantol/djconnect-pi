"""Exercise the production swipe handler with synthetic touch points."""
import sys
from pathlib import Path

from PySide6.QtCore import QPoint, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtTest import QTest

QQuickStyle.setStyle("Basic")
app = QGuiApplication([])
engine = QQmlApplicationEngine()
folder = Path(__file__).resolve().parents[2] / "src/djconnect_pi/qml"
engine.loadData(
    f"""import QtQuick
Window {{
    visible: true
    width: {int(sys.argv[1])}; height: 360
    GlassCard {{
        id: contribution
        objectName: "contribution"
        x: 20; y: 20; width: parent.width - 40; height: 240
        trailingRevealWidth: action.revealWidth
        SessionFlowDelete {{
            id: action
            objectName: "deleteAction"
            card: contribution
            allowed: true
            actionLabel: "Delete contribution"
        }}
    }}
}}
""".encode(),
    QUrl.fromLocalFile(str(folder / "SwipeFixture.qml")),
)
assert engine.rootObjects()
window = engine.rootObjects()[0]
card = window.findChild(QQuickItem, "contribution")
action = window.findChild(QQuickItem, "deleteAction")
assert card is not None and action is not None
touch = QTest.createTouchDevice()
QTest.qWait(150)


def swipe(dx, dy, *, was_revealed, should_reveal):
    start = card.mapToScene(card.boundingRect().center()).toPoint()
    stroke = QTest.touchEvent(window, touch, False)
    stroke.press(0, start, window).commit()
    for step in range(1, 5):
        stroke.move(0, start + QPoint(dx * step // 4, dy * step // 4), window).commit()
        QTest.qWait(25)
    assert action.property("revealed") == was_revealed
    stroke.release(0, start + QPoint(dx, dy), window).commit()
    QTest.qWait(80)
    assert action.property("revealed") == should_reveal, (dx, dy)


swipe(-58, 0, was_revealed=False, should_reveal=False)
swipe(-96, 76, was_revealed=False, should_reveal=False)
swipe(0, 100, was_revealed=False, should_reveal=False)
swipe(-96, 32, was_revealed=False, should_reveal=True)
swipe(40, 0, was_revealed=True, should_reveal=False)
