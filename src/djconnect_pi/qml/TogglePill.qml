import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Button {
    id: pill
    property string label: ""
    property bool active: false

    text: label
    Layout.fillWidth: true
    Layout.preferredHeight: 48
    font.pixelSize: 17
    font.bold: true

    background: Rectangle {
        radius: Math.min(width, height) / 2
        border.width: pill.active ? 2 : 0
        border.color: "#f5d0fe"
        scale: pill.down ? 0.97 : 1.0
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: pill.enabled ? "#247fff" : "#33415f" }
            GradientStop { position: 0.58; color: pill.enabled ? "#7757ff" : "#3c3f61" }
            GradientStop { position: 1.0; color: pill.enabled ? "#c33cff" : "#4b3d65" }
        }

        Behavior on scale { NumberAnimation { duration: 80 } }
        Behavior on color { ColorAnimation { duration: 160 } }
    }

    contentItem: Text {
        text: pill.text
        color: pill.enabled ? "#ffffff" : "#94a0b8"
        font: pill.font
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
}
