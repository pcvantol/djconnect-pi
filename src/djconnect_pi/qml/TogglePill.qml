import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "MoodTheme.js" as MoodTheme

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
        border.color: MoodTheme.color(djconnect.moodValue, "focus")
        scale: pill.down ? 0.97 : 1.0
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: pill.enabled ? MoodTheme.color(djconnect.moodValue, "gradientStart") : MoodTheme.disabled("start") }
            GradientStop { position: 0.58; color: pill.enabled ? MoodTheme.color(djconnect.moodValue, "gradientMid") : MoodTheme.disabled("mid") }
            GradientStop { position: 1.0; color: pill.enabled ? MoodTheme.color(djconnect.moodValue, "gradientEnd") : MoodTheme.disabled("end") }
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
