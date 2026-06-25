import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Button {
    id: control
    property string label: ""
    property bool primary: false

    text: label
    Layout.fillWidth: true
    Layout.preferredHeight: primary ? 88 : 76
    font.pixelSize: primary ? 25 : 18
    font.bold: true

    background: Rectangle {
        radius: Math.min(width, height) / 2
        border.width: 0
        scale: control.down ? 0.96 : 1.0
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: control.enabled ? "#247fff" : "#33415f" }
            GradientStop { position: 0.58; color: control.enabled ? "#7757ff" : "#3c3f61" }
            GradientStop { position: 1.0; color: control.enabled ? "#c33cff" : "#4b3d65" }
        }

        Behavior on scale { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }
        Behavior on color { ColorAnimation { duration: 140 } }
    }

    contentItem: Text {
        text: control.text
        color: control.enabled ? "#ffffff" : "#94a0b8"
        font: control.font
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
}
