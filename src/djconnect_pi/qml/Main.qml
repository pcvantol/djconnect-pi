import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

Window {
    id: root
    width: 720
    height: 720
    visible: true
    color: "#080b18"
    title: "DJConnect Pi"
    visibility: startWindowed ? Window.Windowed : Window.FullScreen

    property real edge: 28
    property bool splashVisible: true
    property string activeScreen: "now"
    property bool settingsOpen: activeScreen === "settings"
    property bool gamesOpen: activeScreen === "games"
    property bool aboutOpen: false
    property var queueItems: [
        { title: "Murder On The Dancefloor", subtitle: "Sophie Ellis-Bextor", uri: "spotify:track:murder", tint: "#d946ef" },
        { title: "SOS", subtitle: "ABBA", uri: "spotify:track:sos", tint: "#a78bfa" },
        { title: "All I Want Is You", subtitle: "", uri: "spotify:track:all-i-want", tint: "#38bdf8" },
        { title: "Around the World (La La La La La)", subtitle: "ATC", uri: "spotify:track:around-the-world", tint: "#8b5cf6" },
        { title: "Smells Like Teen Spirit - Live", subtitle: "", uri: "spotify:track:teen-spirit", tint: "#64748b" },
        { title: "Summer Of 69", subtitle: "Bryan Adams", uri: "spotify:track:summer-69", tint: "#f97316" }
    ]
    property var playlistItems: [
        { title: "DJConnect", subtitle: "", uri: "spotify:playlist:djconnect", tint: "#d946ef" },
        { title: "HAEVN - Songs of Solitude", subtitle: "", uri: "spotify:playlist:haevn", tint: "#64748b" },
        { title: "Acid Trip", subtitle: "", uri: "spotify:playlist:acid-trip", tint: "#fb7185" },
        { title: "LSD TRIP 26", subtitle: "", uri: "spotify:playlist:lsd-trip", tint: "#facc15" },
        { title: "Lucy", subtitle: "", uri: "spotify:playlist:lucy", tint: "#38bdf8" },
        { title: "HAEVN Wide Awake Tour Setlist", subtitle: "", uri: "spotify:playlist:haevn-wide-awake", tint: "#8b5cf6" }
    ]
    property bool screenBlanked: djconnect.screenTimeoutSeconds > 0 && !idleTimer.running
    property real brightnessOverlayOpacity: root.screenBlanked ? 0 : 1 - (djconnect.screenBrightnessPercent / 100.0)

    function repeatLabel(value) {
        if (value === "track") return djconnect.t("repeat_one")
        if (value === "context") return djconnect.t("repeat")
        return djconnect.t("repeat_off")
    }

    component PurpleButton: Button {
        id: control
        font.pixelSize: 22
        font.bold: true
        contentItem: Text {
            text: control.text
            font: control.font
            color: control.enabled ? "#ffffff" : "#93a0b8"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        background: Rectangle {
            radius: 8
            border.color: control.down || control.checked ? "#d9ccff" : "#7f67ff"
            border.width: 1
            color: control.checked ? "#668b5cf6" : "#3324145f"
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: control.enabled ? "#556d28d9" : "#25293d" }
                GradientStop { position: 0.52; color: control.enabled ? "#448b5cf6" : "#2c3048" }
                GradientStop { position: 1.0; color: control.enabled ? "#332563eb" : "#25293d" }
            }
            opacity: control.down ? 0.78 : 1.0
        }
    }

    component PlaybackButton: Button {
        id: control
        property bool primary: false

        font.pixelSize: primary ? 42 : 34
        font.bold: true
        Layout.fillWidth: true
        Layout.fillHeight: true
        contentItem: Text {
            text: control.text
            font: control.font
            color: "#ffffff"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            radius: primary ? 42 : 8
            color: primary ? "#ccbf36f6" : "#3324145f"
            border.color: control.down || primary ? "#d9ccff" : "#7f67ff"
            border.width: 1
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: primary ? "#c026d3" : "#5524145f" }
                GradientStop { position: 0.55; color: primary ? "#bf36f6" : "#448b5cf6" }
                GradientStop { position: 1.0; color: primary ? "#a855f7" : "#332563eb" }
            }
            opacity: control.down ? 0.78 : 1.0
            scale: control.down ? 0.96 : 1.0
            Behavior on scale { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }
        }
    }

    component MediaListPanel: Rectangle {
        id: panel
        property string heading: ""
        property var items: []

        anchors.fill: parent
        color: "#e6070b16"
        z: 16

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            anchors.bottomMargin: 104
            spacing: 12

            Text {
                text: panel.heading
                color: "#ffffff"
                font.pixelSize: 34
                font.bold: true
                Layout.fillWidth: true
            }

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true

                ColumnLayout {
                    width: parent.width
                    spacing: 12

                    Repeater {
                        model: panel.items

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 94
                            radius: 8
                            color: "#3324145f"
                            border.color: "#4d2470a8"
                            border.width: 1
                            gradient: Gradient {
                                orientation: Gradient.Horizontal
                                GradientStop { position: 0.0; color: "#33100b24" }
                                GradientStop { position: 1.0; color: "#5524145f" }
                            }

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 14

                                Rectangle {
                                    Layout.preferredWidth: 68
                                    Layout.preferredHeight: 68
                                    radius: 8
                                    color: modelData.tint

                                    Text {
                                        anchors.centerIn: parent
                                        text: "♪"
                                        color: "#ffffff"
                                        font.pixelSize: 28
                                        font.bold: true
                                    }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 2

                                    Text {
                                        text: modelData.title
                                        color: "#ffffff"
                                        font.pixelSize: 24
                                        font.bold: true
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }

                                    Text {
                                        text: modelData.subtitle
                                        visible: modelData.subtitle.length > 0
                                        color: "#b7c2d8"
                                        font.pixelSize: 17
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }
                                }

                                PlaybackButton {
                                    text: "▶"
                                    primary: true
                                    Layout.preferredWidth: 68
                                    Layout.preferredHeight: 68
                                    onClicked: djconnect.playUri(modelData.uri)
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Timer {
        id: idleTimer
        interval: Math.max(1000, djconnect.screenTimeoutSeconds * 1000)
        running: djconnect.screenTimeoutSeconds > 0
        repeat: false
    }

    Timer {
        interval: 1400
        running: true
        repeat: false
        onTriggered: root.splashVisible = false
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons
        propagateComposedEvents: true
        onPressed: idleTimer.restart()
    }

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            orientation: Gradient.Vertical
            GradientStop { position: 0.0; color: "#1b0f45" }
            GradientStop { position: 0.42; color: "#0b1d4f" }
            GradientStop { position: 1.0; color: "#070b16" }
        }

        Rectangle {
            anchors.fill: parent
            opacity: 0.36
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: "#2f8cff" }
                GradientStop { position: 0.48; color: "#00000000" }
                GradientStop { position: 1.0; color: "#8b5cf6" }
            }
        }

        Rectangle {
            id: ambient
            anchors.centerIn: parent
            width: 680
            height: 680
            radius: 340
            color: djconnect.playing ? "#2f8cff" : "#8b5cf6"
            opacity: djconnect.playing ? 0.22 : 0.16
            scale: djconnect.playing ? 1.03 : 0.94

            Behavior on scale { NumberAnimation { duration: 600; easing.type: Easing.OutCubic } }
            Behavior on color { ColorAnimation { duration: 450 } }
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: root.edge
            anchors.bottomMargin: root.edge + 84
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

                PurpleButton {
                    text: "x"
                    implicitWidth: 34
                    implicitHeight: 34
                    font.pixelSize: 18
                    font.bold: true
                    onClicked: djconnect.quitApp()
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
                Layout.preferredHeight: 112
                spacing: 22

                PlaybackButton {
                    text: "⏮"
                    onClicked: djconnect.previous()
                }

                PlaybackButton {
                    Layout.preferredWidth: 180
                    text: djconnect.playing ? "⏸" : "▶"
                    primary: true
                    onClicked: djconnect.togglePlay()
                }

                PlaybackButton {
                    text: "⏭"
                    onClicked: djconnect.next()
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 54
                spacing: 14

                Text {
                    text: djconnect.t("vol")
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
                Layout.preferredHeight: 74
                spacing: 18

                TogglePill {
                    label: djconnect.t("shuffle")
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
            opacity: root.screenBlanked ? 1 : 0
            visible: opacity > 0

            Behavior on opacity { NumberAnimation { duration: 450 } }

            TapHandler {
                onTapped: idleTimer.restart()
            }
        }

        Rectangle {
            anchors.fill: parent
            color: "#dd0b1012"
            visible: djconnect.djResponseVisible
            z: 8

            ColumnLayout {
                anchors.centerIn: parent
                width: 600
                spacing: 18

                Text {
                    text: djconnect.t("dj_response")
                    color: "#f4f8f8"
                    font.pixelSize: 24
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                }

                Text {
                    text: djconnect.djResponseText
                    color: "#d7e2e4"
                    font.pixelSize: 22
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                }

                PurpleButton {
                    text: djconnect.t("dismiss")
                    font.pixelSize: 18
                    Layout.alignment: Qt.AlignHCenter
                    onClicked: djconnect.clearDjResponse()
                }
            }
        }
    }

    Rectangle {
        id: settingsPanel
        anchors.fill: parent
        color: "#d9070b16"
        visible: settingsOpen && (djconnect.paired || djconnect.demoMode)
        z: 10

        ScrollView {
            anchors.fill: parent
            anchors.margins: 42
            anchors.bottomMargin: 126
            clip: true

            ColumnLayout {
                width: parent.width
                spacing: 18

                Text {
                    text: djconnect.t("setup_title")
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

                PurpleButton {
                    visible: !djconnect.paired
                    text: djconnect.demoMode ? djconnect.t("exit_demo") : djconnect.t("demo_mode")
                    font.pixelSize: 18
                    Layout.fillWidth: true
                    onClicked: {
                        if (djconnect.demoMode) {
                            djconnect.exitDemoMode()
                            root.activeScreen = "now"
                        } else {
                            djconnect.enterDemoMode()
                            root.activeScreen = "now"
                        }
                    }
                }

            Text {
                text: djconnect.t("client_api_url") + ": " + djconnect.localApiUrl
                color: "#9fb4b8"
                font.pixelSize: 14
                elide: Text.ElideMiddle
                Layout.fillWidth: true
            }

            Text {
                text: djconnect.t("pairing_code") + ": " + djconnect.pairingCode
                color: "#f4f8f8"
                font.pixelSize: 24
                font.bold: true
                Layout.fillWidth: true
            }

            TextField {
                id: haUrlField
                text: djconnect.haUrl.length ? djconnect.haUrl : "http://homeassistant.local:8123"
                placeholderText: djconnect.t("ha_url")
                font.pixelSize: 20
                Layout.fillWidth: true
            }

            TextField {
                id: pairCodeField
                placeholderText: djconnect.t("pairing_code")
                font.pixelSize: 26
                horizontalAlignment: TextInput.AlignHCenter
                Layout.fillWidth: true
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 14

                Text {
                    text: djconnect.t("screen_off")
                    color: "#d7e2e4"
                    font.pixelSize: 18
                    Layout.preferredWidth: 130
                }

                SpinBox {
                    id: screenTimeoutBox
                    from: 0
                    to: 3600
                    stepSize: 30
                    value: djconnect.screenTimeoutSeconds
                    editable: true
                    Layout.fillWidth: true
                    onValueModified: djconnect.setScreenTimeoutSeconds(value)
                }

                Text {
                    text: screenTimeoutBox.value === 0 ? djconnect.t("off") : djconnect.t("sec")
                    color: "#9fb4b8"
                    font.pixelSize: 16
                    Layout.preferredWidth: 38
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 14

                Text {
                    text: djconnect.t("brightness")
                    color: "#d7e2e4"
                    font.pixelSize: 18
                    Layout.preferredWidth: 130
                }

                Slider {
                    id: brightnessSlider
                    from: 10
                    to: 100
                    stepSize: 1
                    value: djconnect.screenBrightnessPercent
                    Layout.fillWidth: true
                    onMoved: djconnect.setScreenBrightnessPercent(Math.round(value))
                }

                Text {
                    text: Math.round(brightnessSlider.value) + "%"
                    color: "#f4f8f8"
                    font.pixelSize: 16
                    horizontalAlignment: Text.AlignRight
                    Layout.preferredWidth: 48
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 14

                Text {
                    text: djconnect.t("updates")
                    color: "#d7e2e4"
                    font.pixelSize: 18
                    Layout.preferredWidth: 130
                }

                ComboBox {
                    id: updateChannelBox
                    model: ["stable", "beta"]
                    currentIndex: djconnect.updateChannel === "beta" ? 1 : 0
                    Layout.fillWidth: true
                    onActivated: djconnect.setUpdateChannel(currentText)
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 14

                Text {
                    text: djconnect.t("language")
                    color: "#d7e2e4"
                    font.pixelSize: 18
                    Layout.preferredWidth: 130
                }

                ComboBox {
                    id: languageBox
                    model: [
                        { code: "nl", label: "Nederlands" },
                        { code: "en", label: "English" }
                    ]
                    textRole: "label"
                    valueRole: "code"
                    currentIndex: djconnect.language === "en" ? 1 : 0
                    Layout.fillWidth: true
                    onActivated: djconnect.setLanguage(currentValue)
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 14

                Text {
                    text: djconnect.t("log_level")
                    color: "#d7e2e4"
                    font.pixelSize: 18
                    Layout.preferredWidth: 130
                }

                ComboBox {
                    id: logLevelBox
                    model: ["DEBUG", "INFO", "WARNING", "ERROR"]
                    currentIndex: model.indexOf(djconnect.logLevel)
                    Layout.fillWidth: true
                    onActivated: djconnect.setLogLevel(currentText)
                }
            }

            Text {
                text: djconnect.t("log") + ": " + djconnect.logFile
                color: "#91a3a7"
                font.pixelSize: 13
                elide: Text.ElideMiddle
                Layout.fillWidth: true
            }

            PurpleButton {
                text: djconnect.paired ? djconnect.t("save") : djconnect.t("pair")
                font.pixelSize: 22
                Layout.fillWidth: true
                Layout.preferredHeight: 62
                onClicked: {
                    djconnect.setHaUrl(haUrlField.text)
                    if (!djconnect.paired) djconnect.pair(pairCodeField.text)
                    if (djconnect.paired) root.activeScreen = "now"
                }
            }

            PurpleButton {
                text: djconnect.t("close")
                enabled: djconnect.paired
                font.pixelSize: 20
                Layout.fillWidth: true
                Layout.preferredHeight: 56
                onClicked: root.activeScreen = "now"
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                PurpleButton {
                    text: djconnect.t("view_logs")
                    Layout.fillWidth: true
                    onClicked: djconnect.showLogs()
                }

                PurpleButton {
                    text: djconnect.t("about")
                    Layout.fillWidth: true
                    onClicked: root.aboutOpen = true
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                PurpleButton {
                    text: djconnect.t("reset_pairing")
                    Layout.fillWidth: true
                    onClicked: djconnect.resetPairing()
                }
            }

            PurpleButton {
                text: djconnect.t("reboot_device")
                Layout.fillWidth: true
                onClicked: djconnect.rebootDevice()
            }

            Item { Layout.fillHeight: true }

            Text {
                text: djconnect.t("no_voice")
                color: "#91a3a7"
                font.pixelSize: 15
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
        }
    }
    }

    MediaListPanel {
        visible: root.activeScreen === "queue"
        heading: djconnect.t("queue")
        items: root.queueItems
    }

    MediaListPanel {
        visible: root.activeScreen === "playlists"
        heading: djconnect.t("playlists")
        items: root.playlistItems
    }

    GamesPanel {
        anchors.fill: parent
        visible: gamesOpen
        z: 18
        onCloseRequested: root.activeScreen = "now"
    }

    Rectangle {
        id: bottomNav
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 78
        color: "#dd0b1024"
        border.color: "#33406b"
        border.width: 1
        visible: !root.splashVisible && (djconnect.paired || djconnect.demoMode) && !djconnect.logsVisible && !djconnect.versionMismatchVisible
        z: 25

        RowLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 8

            PurpleButton {
                text: djconnect.t("now_playing")
                font.pixelSize: 15
                checkable: true
                checked: root.activeScreen === "now"
                Layout.fillWidth: true
                Layout.fillHeight: true
                onClicked: root.activeScreen = "now"
            }

            PurpleButton {
                text: djconnect.t("games")
                font.pixelSize: 15
                checkable: true
                checked: root.activeScreen === "games"
                Layout.fillWidth: true
                Layout.fillHeight: true
                onClicked: root.activeScreen = "games"
            }

            PurpleButton {
                text: djconnect.t("queue")
                font.pixelSize: 15
                checkable: true
                checked: root.activeScreen === "queue"
                Layout.fillWidth: true
                Layout.fillHeight: true
                onClicked: root.activeScreen = "queue"
            }

            PurpleButton {
                text: djconnect.t("playlists")
                font.pixelSize: 15
                checkable: true
                checked: root.activeScreen === "playlists"
                Layout.fillWidth: true
                Layout.fillHeight: true
                onClicked: root.activeScreen = "playlists"
            }

            PurpleButton {
                text: djconnect.t("setup")
                font.pixelSize: 15
                checkable: true
                checked: root.activeScreen === "settings"
                Layout.fillWidth: true
                Layout.fillHeight: true
                onClicked: root.activeScreen = "settings"
            }
        }
    }

    Rectangle {
        id: pairingPanel
        anchors.fill: parent
        color: "#e6070b16"
        visible: !root.splashVisible && !djconnect.paired && !djconnect.demoMode
        z: 30

        ColumnLayout {
            anchors.centerIn: parent
            width: Math.min(parent.width - 72, 560)
            spacing: 18

            Text {
                text: "DJConnect Pi"
                color: "#f4f8f8"
                font.pixelSize: 46
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
            }

            Text {
                text: djconnect.t("pairing_title")
                color: "#d7e2e4"
                font.pixelSize: 28
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
            }

            Text {
                text: djconnect.t("pairing_hint")
                color: "#9fb4b8"
                font.pixelSize: 17
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 82
                radius: 8
                color: "#10181c"
                border.color: "#314449"
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 4

                    Text {
                        text: djconnect.t("client_api_url")
                        color: "#9fb4b8"
                        font.pixelSize: 14
                        Layout.fillWidth: true
                    }

                    Text {
                        text: djconnect.localApiUrl
                        color: "#f4f8f8"
                        font.pixelSize: 20
                        font.bold: true
                        elide: Text.ElideMiddle
                        Layout.fillWidth: true
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 104
                radius: 8
                color: "#151020"
                border.color: "#8b5cf6"
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 2

                    Text {
                        text: djconnect.t("pairing_code")
                        color: "#d9ccff"
                        font.pixelSize: 18
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                        Layout.fillWidth: true
                    }

                    Text {
                        text: djconnect.pairingCode
                        color: "#ffffff"
                        font.pixelSize: 46
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                        Layout.fillWidth: true
                    }
                }
            }

            TextField {
                id: blockingPairCodeField
                placeholderText: djconnect.t("pairing_code")
                font.pixelSize: 28
                horizontalAlignment: TextInput.AlignHCenter
                Layout.fillWidth: true
                Layout.preferredHeight: 66
                onAccepted: {
                    djconnect.pair(text)
                    text = ""
                }
            }

            PurpleButton {
                text: djconnect.t("pair")
                font.pixelSize: 22
                Layout.fillWidth: true
                Layout.preferredHeight: 62
                onClicked: {
                    djconnect.pair(blockingPairCodeField.text.length ? blockingPairCodeField.text : djconnect.pairingCode)
                    blockingPairCodeField.text = ""
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                PurpleButton {
                    text: djconnect.t("demo_mode")
                    font.pixelSize: 18
                    Layout.fillWidth: true
                    onClicked: djconnect.enterDemoMode()
                }

                PurpleButton {
                    text: djconnect.t("view_logs")
                    font.pixelSize: 18
                    Layout.fillWidth: true
                    onClicked: djconnect.showLogs()
                }
            }

            Text {
                text: djconnect.t("pairing_blocked")
                color: "#91a3a7"
                font.pixelSize: 15
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
            }
        }

        PurpleButton {
            text: "x"
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.margins: 18
            implicitWidth: 34
            implicitHeight: 34
            font.pixelSize: 18
            font.bold: true
            onClicked: djconnect.quitApp()
        }
    }

    Rectangle {
        id: splashPanel
        anchors.fill: parent
        gradient: Gradient {
            orientation: Gradient.Vertical
            GradientStop { position: 0.0; color: "#24105c" }
            GradientStop { position: 0.5; color: "#0f2b68" }
            GradientStop { position: 1.0; color: "#070b16" }
        }
        visible: root.splashVisible
        z: 40

        Rectangle {
            anchors.centerIn: parent
            width: Math.min(parent.width - 64, 560)
            height: 190
            radius: 8
            color: "#cc0b1024"
            border.color: "#4050a8"
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 14

                Text {
                    text: "DJConnect"
                    color: "#f4f8f8"
                    font.pixelSize: 48
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                }

                Text {
                    text: djconnect.t("startup_message")
                    color: "#9fb4b8"
                    font.pixelSize: 18
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                }

                BusyIndicator {
                    running: splashPanel.visible
                    implicitWidth: 46
                    implicitHeight: 46
                    Layout.alignment: Qt.AlignHCenter
                }
            }
        }
    }

    Rectangle {
        id: toast
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.topMargin: 22
        width: Math.min(parent.width - 64, Math.max(220, toastText.implicitWidth + 58))
        height: 48
        radius: 24
        color: "#d92f8cff"
        border.color: "#80ffffff"
        border.width: 1
        opacity: djconnect.toastVisible ? 1 : 0
        visible: opacity > 0
        z: 70
        y: djconnect.toastVisible ? 0 : -16

        Behavior on opacity { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
        Behavior on y { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }

        Text {
            id: toastText
            anchors.centerIn: parent
            width: parent.width - 34
            text: djconnect.toastText
            color: "#ffffff"
            font.pixelSize: 17
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
            maximumLineCount: 1
        }
    }

    Rectangle {
        id: versionMismatchPanel
        anchors.fill: parent
        color: "#f2070b16"
        visible: !root.splashVisible && djconnect.versionMismatchVisible
        z: 60

        ColumnLayout {
            anchors.centerIn: parent
            width: Math.min(parent.width - 72, 560)
            spacing: 18

            Text {
                text: djconnect.t("version_mismatch_title")
                color: "#f4f8f8"
                font.pixelSize: 40
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
            }

            Text {
                text: djconnect.versionMismatchText
                color: "#d7e2e4"
                font.pixelSize: 20
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
            }

            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 12

                BusyIndicator {
                    running: versionMismatchPanel.visible
                    implicitWidth: 34
                    implicitHeight: 34
                }

                Text {
                    text: djconnect.t("update_trying")
                    color: "#9fb4b8"
                    font.pixelSize: 17
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                PurpleButton {
                    text: djconnect.t("view_logs")
                    font.pixelSize: 18
                    Layout.fillWidth: true
                    onClicked: djconnect.showLogs()
                }

                PurpleButton {
                    text: "x"
                    font.pixelSize: 18
                    font.bold: true
                    Layout.preferredWidth: 58
                    onClicked: djconnect.quitApp()
                }
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "#f2070b16"
        visible: djconnect.logsVisible
        z: 80

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 28
            spacing: 12

            RowLayout {
                Layout.fillWidth: true
                PurpleButton {
                    text: djconnect.t("copy_logs")
                    font.pixelSize: 24
                    Layout.fillWidth: true
                    onClicked: djconnect.copyLogs()
                }
                PurpleButton {
                    text: djconnect.t("clear_logs")
                    font.pixelSize: 24
                    Layout.fillWidth: true
                    onClicked: djconnect.clearLogs()
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                Text {
                    text: djconnect.t("logs")
                    color: "#f4f8f8"
                    font.pixelSize: 30
                    font.bold: true
                    Layout.fillWidth: true
                }
                PurpleButton { text: djconnect.t("refresh"); font.pixelSize: 24; onClicked: djconnect.showLogs() }
                PurpleButton { text: djconnect.t("close"); font.pixelSize: 24; onClicked: djconnect.hideLogs() }
            }

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true

                TextArea {
                    text: djconnect.logsText
                    readOnly: true
                    wrapMode: TextEdit.NoWrap
                    color: "#d7e2e4"
                    font.family: "monospace"
                    font.pixelSize: 24
                    background: Rectangle {
                        color: "#10181c"
                        radius: 8
                        border.color: "#314449"
                    }
                }
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "#f2070b16"
        visible: root.aboutOpen
        z: 82

        ScrollView {
            anchors.fill: parent
            anchors.margins: 22
            clip: true

            ColumnLayout {
                width: parent.width
                spacing: 18

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 132
                    radius: 8
                    color: "#dd151020"
                    border.color: "#3f2f70"
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 18

                        Rectangle {
                            Layout.preferredWidth: 82
                            Layout.preferredHeight: 82
                            radius: 8
                            gradient: Gradient {
                                orientation: Gradient.Vertical
                                GradientStop { position: 0.0; color: "#8b5cf6" }
                                GradientStop { position: 1.0; color: "#0b1d4f" }
                            }

                            Text {
                                anchors.centerIn: parent
                                text: "DJ"
                                color: "#ffffff"
                                font.pixelSize: 32
                                font.bold: true
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4

                            Text {
                                text: "DJConnect Pi"
                                color: "#ffffff"
                                font.pixelSize: 38
                                font.bold: true
                                Layout.fillWidth: true
                            }

                            Text {
                                text: djconnect.t("tagline")
                                color: "#c8bfd4"
                                font.pixelSize: 20
                                font.bold: true
                                Layout.fillWidth: true
                            }
                        }
                    }
                }

                Text {
                    text: djconnect.t("app_section")
                    color: "#b7a8c8"
                    font.pixelSize: 20
                    font.bold: true
                    Layout.fillWidth: true
                }

                GridLayout {
                    columns: 2
                    columnSpacing: 18
                    rowSpacing: 10
                    Layout.fillWidth: true

                    Text { text: djconnect.t("version"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.version; color: "#ffffff"; font.pixelSize: 20; Layout.fillWidth: true }
                    Text { text: djconnect.t("device_name"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: "DJConnect Pi"; color: "#ffffff"; font.pixelSize: 20; Layout.fillWidth: true }
                    Text { text: djconnect.t("website"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: "https://djconnect.pages.dev"; color: "#f044ff"; font.pixelSize: 20; Layout.fillWidth: true; elide: Text.ElideRight }
                    Text { text: djconnect.t("device_id"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.deviceId; color: "#ffffff"; font.pixelSize: 18; Layout.fillWidth: true; elide: Text.ElideMiddle }
                }

                Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: "#443262" }

                Text {
                    text: djconnect.t("connection_section")
                    color: "#b7a8c8"
                    font.pixelSize: 20
                    font.bold: true
                    Layout.fillWidth: true
                }

                GridLayout {
                    columns: 2
                    columnSpacing: 18
                    rowSpacing: 10
                    Layout.fillWidth: true

                    Text { text: djconnect.t("pairing_status"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.paired ? djconnect.t("paired") : djconnect.t("not_paired"); color: "#ffffff"; font.pixelSize: 20; Layout.fillWidth: true }
                    Text { text: djconnect.t("music"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.paired ? djconnect.t("connected_value") : djconnect.t("not_connected_value"); color: "#ffffff"; font.pixelSize: 20; Layout.fillWidth: true }
                    Text { text: djconnect.t("client_api_url_label"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.localApiUrl; color: "#ffffff"; font.pixelSize: 18; Layout.fillWidth: true; elide: Text.ElideMiddle }
                    Text { text: djconnect.t("home_assistant"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.haUrl; color: "#ffffff"; font.pixelSize: 18; Layout.fillWidth: true; elide: Text.ElideMiddle }
                }

                Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: "#443262" }

                Text {
                    text: djconnect.t("notices_section")
                    color: "#b7a8c8"
                    font.pixelSize: 20
                    font.bold: true
                    Layout.fillWidth: true
                }

                GridLayout {
                    columns: 2
                    columnSpacing: 18
                    rowSpacing: 10
                    Layout.fillWidth: true

                    Text { text: djconnect.t("copyright"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: "2026 Peter van Tol"; color: "#ffffff"; font.pixelSize: 20; Layout.fillWidth: true }
                    Text { text: djconnect.t("spotify_notice"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.t("spotify_trademark"); color: "#ffffff"; font.pixelSize: 20; Layout.fillWidth: true }
                }

                PurpleButton {
                    text: djconnect.t("close")
                    font.pixelSize: 26
                    Layout.fillWidth: true
                    Layout.preferredHeight: 64
                    onClicked: root.aboutOpen = false
                }
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "#000000"
        opacity: root.screenBlanked ? 1 : root.brightnessOverlayOpacity
        visible: opacity > 0
        z: 200

        Behavior on opacity { NumberAnimation { duration: 450 } }

        TapHandler {
            onTapped: idleTimer.restart()
        }
    }
}
