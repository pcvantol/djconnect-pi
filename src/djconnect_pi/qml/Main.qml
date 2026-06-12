import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

Window {
    id: root
    width: 720
    height: 720
    visible: true
    color: "#0b1012"
    title: "DJConnect Pi"
    visibility: startWindowed ? Window.Windowed : Window.FullScreen

    property real edge: 28
    property bool settingsOpen: !djconnect.paired || djconnect.haUrl.length === 0
    property int dimLevel: idleTimer.running ? 0 : 1

    function repeatLabel(value) {
        if (value === "track") return "Repeat 1"
        if (value === "context") return "Repeat"
        return "Repeat off"
    }

    Timer {
        id: idleTimer
        interval: 90000
        running: true
        repeat: false
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons
        propagateComposedEvents: true
        onPressed: idleTimer.restart()
    }

    Rectangle {
        anchors.fill: parent
        color: "#0b1012"

        Rectangle {
            id: ambient
            anchors.centerIn: parent
            width: 680
            height: 680
            radius: 340
            color: djconnect.playing ? "#183927" : "#18252b"
            opacity: 0.34
            scale: djconnect.playing ? 1.03 : 0.94

            Behavior on scale { NumberAnimation { duration: 600; easing.type: Easing.OutCubic } }
            Behavior on color { ColorAnimation { duration: 450 } }
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: root.edge
            spacing: 12

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 34
                spacing: 10

                Rectangle {
                    width: 10
                    height: 10
                    radius: 5
                    color: djconnect.paired ? "#1db954" : "#e0a83a"
                    Layout.alignment: Qt.AlignVCenter
                }

                Text {
                    text: djconnect.statusText
                    color: "#c2d3d6"
                    font.pixelSize: 16
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }

                BusyIndicator {
                    running: djconnect.busy
                    visible: djconnect.busy
                    implicitWidth: 28
                    implicitHeight: 28
                }

                Button {
                    text: "Setup"
                    onClicked: settingsOpen = true
                }
            }

            Item {
                id: artShell
                Layout.fillWidth: true
                Layout.preferredHeight: 388

                Rectangle {
                    id: artFrame
                    anchors.centerIn: parent
                    width: 366
                    height: 366
                    radius: 8
                    color: "#172024"
                    border.color: "#314449"
                    border.width: 1
                    scale: djconnect.playing ? 1.0 : 0.96
                    clip: true

                    Behavior on scale { NumberAnimation { duration: 280; easing.type: Easing.OutCubic } }

                    Image {
                        id: albumArt
                        anchors.fill: parent
                        source: djconnect.imageUrl
                        fillMode: Image.PreserveAspectCrop
                        asynchronous: true
                        opacity: status === Image.Ready ? 1 : 0

                        Behavior on opacity { NumberAnimation { duration: 240 } }
                    }

                    Rectangle {
                        anchors.fill: parent
                        color: "#1e2a2f"
                        opacity: albumArt.status === Image.Ready ? 0 : 1

                        Text {
                            anchors.centerIn: parent
                            text: "DJConnect"
                            color: "#edf5f6"
                            font.pixelSize: 42
                            font.bold: true
                        }
                    }

                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        height: 92
                        color: "#990b1012"
                    }
                }

                DragHandler {
                    id: swipeHandler
                    target: null
                    xAxis.enabled: true
                    yAxis.enabled: false
                    onActiveChanged: {
                        if (!active) {
                            if (centroid.position.x - centroid.pressPosition.x > 96) djconnect.previous()
                            if (centroid.position.x - centroid.pressPosition.x < -96) djconnect.next()
                        }
                    }
                }

                TapHandler {
                    onTapped: djconnect.togglePlay()
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 3

                Text {
                    text: djconnect.title
                    color: "#f4f8f8"
                    font.pixelSize: 30
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideRight
                    maximumLineCount: 1
                    Layout.fillWidth: true
                }

                Text {
                    text: djconnect.artist
                    color: "#aebfc3"
                    font.pixelSize: 18
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideRight
                    maximumLineCount: 1
                    Layout.fillWidth: true
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 104
                spacing: 18

                ControlButton {
                    label: "Prev"
                    onClicked: djconnect.previous()
                }

                ControlButton {
                    Layout.preferredWidth: 172
                    label: djconnect.playing ? "Pause" : "Play"
                    primary: true
                    onClicked: djconnect.togglePlay()
                }

                ControlButton {
                    label: "Next"
                    onClicked: djconnect.next()
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 54
                spacing: 14

                Text {
                    text: "Vol"
                    color: "#c6d3d6"
                    font.pixelSize: 16
                    Layout.preferredWidth: 38
                }

                Slider {
                    id: volumeSlider
                    from: 0
                    to: 100
                    value: djconnect.volume
                    stepSize: 1
                    Layout.fillWidth: true
                    onMoved: djconnect.setVolume(Math.round(value))
                }

                Text {
                    text: djconnect.volume
                    color: "#f4f8f8"
                    font.pixelSize: 18
                    horizontalAlignment: Text.AlignRight
                    Layout.preferredWidth: 42
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 56
                spacing: 16

                TogglePill {
                    label: "Shuffle"
                    active: djconnect.shuffle
                    onClicked: djconnect.toggleShuffle()
                }

                TogglePill {
                    label: repeatLabel(djconnect.repeat)
                    active: djconnect.repeat !== "off"
                    onClicked: djconnect.cycleRepeat()
                }
            }
        }

        Rectangle {
            anchors.fill: parent
            color: "#000000"
            opacity: root.dimLevel ? 0.55 : 0
            visible: opacity > 0

            Behavior on opacity { NumberAnimation { duration: 700 } }

            TapHandler {
                onTapped: idleTimer.restart()
            }
        }
    }

    Rectangle {
        id: settingsPanel
        anchors.fill: parent
        color: "#ee0b1012"
        visible: settingsOpen
        z: 10

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 42
            spacing: 18

            Text {
                text: "DJConnect Setup"
                color: "#f4f8f8"
                font.pixelSize: 34
                font.bold: true
                Layout.fillWidth: true
            }

            Text {
                text: djconnect.deviceId
                color: "#9fb4b8"
                font.pixelSize: 14
                elide: Text.ElideMiddle
                Layout.fillWidth: true
            }

            TextField {
                id: haUrlField
                text: djconnect.haUrl.length ? djconnect.haUrl : "http://homeassistant.local:8123"
                placeholderText: "Home Assistant URL"
                font.pixelSize: 20
                Layout.fillWidth: true
            }

            TextField {
                id: pairCodeField
                placeholderText: "Pairing code"
                font.pixelSize: 26
                horizontalAlignment: TextInput.AlignHCenter
                Layout.fillWidth: true
            }

            Button {
                text: djconnect.paired ? "Save" : "Pair"
                font.pixelSize: 22
                Layout.fillWidth: true
                Layout.preferredHeight: 62
                onClicked: {
                    djconnect.setHaUrl(haUrlField.text)
                    if (!djconnect.paired) djconnect.pair(pairCodeField.text)
                    if (djconnect.paired) settingsOpen = false
                }
            }

            Button {
                text: "Close"
                enabled: djconnect.paired
                font.pixelSize: 20
                Layout.fillWidth: true
                Layout.preferredHeight: 56
                onClicked: settingsOpen = false
            }

            Item { Layout.fillHeight: true }

            Text {
                text: "No voice, microphone, or local DJ response playback on this client."
                color: "#91a3a7"
                font.pixelSize: 15
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
        }
    }
}
