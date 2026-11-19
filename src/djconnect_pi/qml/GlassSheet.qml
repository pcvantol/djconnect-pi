import QtQuick
import QtQuick.Controls

GlassPopup {
    id: sheet
    parent: Overlay.overlay
    readonly property bool compact: width < 900
    readonly property real sheetTopOffset: compact ? 18 : 120
    x: 0
    y: sheetTopOffset
    width: parent ? parent.width : 0
    height: parent ? Math.max(0, parent.height - sheetTopOffset) : 0
    padding: 0
    modal: true
    dim: true
    focus: true
    closePolicy: Popup.NoAutoClose
    Overlay.modal: Rectangle { color: "#80080B20" }
    background: Rectangle {
        topLeftRadius: sheet.compact ? 30 : 52
        topRightRadius: topLeftRadius
        gradient: Gradient {
            GradientStop { position: 0; color: "#192859" }
            GradientStop { position: 0.48; color: "#181537" }
            GradientStop { position: 1; color: "#15102E" }
        }
    }
}
