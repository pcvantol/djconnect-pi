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
        color: control.primary ? "#1db954" : "#233036"
        border.color: control.down ? "#eaf4f5" : "#40545b"
        border.width: 1
        scale: control.down ? 0.96 : 1.0

        Behavior on scale { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }
        Behavior on color { ColorAnimation { duration: 140 } }
    }

    contentItem: Text {
        text: control.text
        color: control.primary ? "#06100a" : "#edf5f6"
        font: control.font
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
}
