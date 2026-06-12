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
        color: pill.active ? "#d9ef68" : "#1c272c"
        border.color: pill.down ? "#f5f8f8" : "#3b4e55"
        border.width: 1
        scale: pill.down ? 0.97 : 1.0

        Behavior on scale { NumberAnimation { duration: 80 } }
        Behavior on color { ColorAnimation { duration: 160 } }
    }

    contentItem: Text {
        text: pill.text
        color: pill.active ? "#131700" : "#d8e4e6"
        font: pill.font
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
}
