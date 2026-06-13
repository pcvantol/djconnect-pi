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
        radius: 8
        color: pill.active ? "#668b5cf6" : "#3324145f"
        border.color: pill.down || pill.active ? "#d9ccff" : "#7f67ff"
        border.width: 1
        scale: pill.down ? 0.97 : 1.0
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: pill.enabled ? "#556d28d9" : "#25293d" }
            GradientStop { position: 0.55; color: pill.enabled ? "#448b5cf6" : "#2c3048" }
            GradientStop { position: 1.0; color: pill.enabled ? "#332563eb" : "#25293d" }
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
