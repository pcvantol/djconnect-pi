import QtQuick
import QtQuick.Layouts
import "MoodTheme.js" as MoodTheme

Item {
    id: avatar
    objectName: "sessionConfirmationAvatar"
    required property string mood
    implicitWidth: 52
    implicitHeight: implicitWidth
    Layout.alignment: Qt.AlignTop
    Accessible.ignored: true

    Rectangle {
        anchors.fill: parent
        radius: width / 2
        color: "#99000000"
    }
    DJSessionMenuSymbol {
        anchors.fill: parent
        gradientColors: [
            MoodTheme.moodColor(avatar.mood, "gradientStart"),
            MoodTheme.moodColor(avatar.mood, "gradientMid"),
            MoodTheme.moodColor(avatar.mood, "gradientEnd")
        ]
    }
}
