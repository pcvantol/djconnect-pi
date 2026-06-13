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
        radius: 8
        color: control.primary ? "#668b5cf6" : "#3324145f"
        border.color: control.down || control.primary ? "#d9ccff" : "#7f67ff"
        border.width: 1
        scale: control.down ? 0.96 : 1.0
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: control.enabled ? "#556d28d9" : "#25293d" }
            GradientStop { position: 0.55; color: control.enabled ? "#448b5cf6" : "#2c3048" }
            GradientStop { position: 1.0; color: control.enabled ? "#332563eb" : "#25293d" }
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
