"""Actual Qt geometry, click and close checks; synthetic local properties only."""
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QPointF, Qt, QUrl, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlExpression
from PySide6.QtQuick import QQuickItem
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtTest import QTest

from djconnect_pi.brand_theme import apply_palette

QQuickStyle.setStyle("Basic")
app = QGuiApplication([])
apply_palette(app)
messages = []
qInstallMessageHandler(lambda kind, context, message: messages.append(message))
engine = QQmlApplicationEngine()
folder = Path.cwd() / 'src/djconnect_pi/qml'
engine.loadData(('''import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "''' + folder.as_uri() + '''"
Window {
    id: root; visible: true; width: ''' + sys.argv[1] + '''; height: 400
    property int calls: 0
    PageToolbar {
        id: toolbar; objectName: "toolbar"; width: parent.width - 40; x: 20; y: 20
        title: "Session / Musique / Einstellungen"
        showConnection: true; connectionLabel: "Connection"; connectionText: "<b>synthetic</b>"
        leading: [ GlassButton { objectName: "delete"; iconName: "trash"; tertiary: true; onClicked: root.calls++ } ]
        GlassButton { objectName: "refresh"; iconName: "refresh"; tertiary: true; onClicked: root.calls++ }
    }
}
''').encode(), QUrl.fromLocalFile(str(folder / 'ToolbarFixture.qml')))
assert engine.rootObjects(), messages
window = engine.rootObjects()[0]
QTest.qWait(120)
bar = window.findChild(QObject, 'toolbar')
refresh = window.findChild(QQuickItem, 'refresh')
remove = window.findChild(QQuickItem, 'delete')
connection = window.findChild(QQuickItem, 'pageToolbarConnection')
assert bar and refresh and remove and connection
for item in (refresh, remove, connection):
    point = item.mapToScene(QPointF(0, 0))
    assert 0 <= point.x() < window.width() and point.x() + item.width() <= window.width()
    assert item.height() >= 44 and item.width() >= 44
assert remove.mapToScene(QPointF()).x() < connection.mapToScene(QPointF()).x() < refresh.mapToScene(QPointF()).x()
assert window.property('calls') == 0
for item, count in [(refresh, 1), (remove, 2)]:
    QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, item.mapToScene(QPointF(item.width()/2, item.height()/2)).toPoint())
    assert window.property('calls') == count
def popup_visible():
    expression = QQmlExpression(engine.rootContext(), bar, 'connectionInfo.visible')
    value = expression.evaluate()
    assert not expression.hasError(), expression.error().toString()
    return value[0] if isinstance(value, tuple) else value
QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, connection.mapToScene(QPointF(connection.width()/2, connection.height()/2)).toPoint())
assert popup_visible() and window.property('calls') == 2
bar.setVisible(False)
assert not popup_visible()
bar.setVisible(True)
QTest.qWait(50)
assert not popup_visible() and window.property('calls') == 2
large = window.findChild(QObject, 'pageToolbarLargeTitle')
assert large.property('visible') == (int(sys.argv[1]) >= 940)
if large.property('visible'):
    assert large.property('y') > refresh.mapToItem(bar, QPointF()).y() + refresh.height()
assert not messages, messages
window.close()
engine.deleteLater()
QTest.qWait(30)
print('PASS: bounded geometry, separate groups, one explicit click, local connection, immediate hidden close, no implicit action')
