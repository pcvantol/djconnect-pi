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
    title: "DJConnect"
    visibility: startWindowed ? Window.Windowed : Window.FullScreen

    property real edge: 28
    property bool splashVisible: true
    property string activeScreen: "now"
    property bool settingsOpen: activeScreen === "settings"
    property bool gamesOpen: activeScreen === "games"
    property bool aboutOpen: false
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

        font.pixelSize: primary ? 24 : 22
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

    component IconButton: Button {
        id: control
        property string iconName: "play"
        property bool primary: false
        property bool active: false

        Layout.fillWidth: true
        Layout.fillHeight: true
        contentItem: Canvas {
            id: iconCanvas
            anchors.fill: parent
            antialiasing: true
            onPaint: {
                var ctx = getContext("2d")
                ctx.clearRect(0, 0, width, height)
                var w = width
                var h = height
                var cx = w / 2
                var cy = h / 2
                var s = Math.min(w, h)
                ctx.strokeStyle = "#ffffff"
                ctx.fillStyle = "#ffffff"
                ctx.lineWidth = Math.max(4, s * 0.08)
                ctx.lineCap = "round"
                ctx.lineJoin = "round"

                function triangle(dir, x) {
                    ctx.beginPath()
                    if (dir > 0) {
                        ctx.moveTo(x - s * 0.12, cy - s * 0.20)
                        ctx.lineTo(x - s * 0.12, cy + s * 0.20)
                        ctx.lineTo(x + s * 0.18, cy)
                    } else {
                        ctx.moveTo(x + s * 0.12, cy - s * 0.20)
                        ctx.lineTo(x + s * 0.12, cy + s * 0.20)
                        ctx.lineTo(x - s * 0.18, cy)
                    }
                    ctx.closePath()
                    ctx.fill()
                }

                if (control.iconName === "pause") {
                    ctx.fillRect(cx - s * 0.18, cy - s * 0.22, s * 0.11, s * 0.44)
                    ctx.fillRect(cx + s * 0.07, cy - s * 0.22, s * 0.11, s * 0.44)
                } else if (control.iconName === "previous") {
                    triangle(-1, cx - s * 0.05)
                    triangle(-1, cx + s * 0.17)
                    ctx.fillRect(cx - s * 0.30, cy - s * 0.24, s * 0.07, s * 0.48)
                } else if (control.iconName === "next") {
                    triangle(1, cx + s * 0.05)
                    triangle(1, cx - s * 0.17)
                    ctx.fillRect(cx + s * 0.23, cy - s * 0.24, s * 0.07, s * 0.48)
                } else if (control.iconName === "shuffle") {
                    ctx.beginPath()
                    ctx.moveTo(cx - s * 0.32, cy - s * 0.16)
                    ctx.bezierCurveTo(cx - s * 0.08, cy - s * 0.16, cx + s * 0.02, cy + s * 0.16, cx + s * 0.26, cy + s * 0.16)
                    ctx.stroke()
                    ctx.beginPath()
                    ctx.moveTo(cx - s * 0.32, cy + s * 0.16)
                    ctx.bezierCurveTo(cx - s * 0.08, cy + s * 0.16, cx + s * 0.02, cy - s * 0.16, cx + s * 0.26, cy - s * 0.16)
                    ctx.stroke()
                    triangle(1, cx + s * 0.33)
                    triangle(1, cx + s * 0.33)
                    if (!control.active) {
                        ctx.strokeStyle = "#ff9bb8"
                        ctx.beginPath()
                        ctx.moveTo(cx - s * 0.34, cy + s * 0.30)
                        ctx.lineTo(cx + s * 0.34, cy - s * 0.30)
                        ctx.stroke()
                    }
                } else if (control.iconName === "repeat" || control.iconName === "repeatOne" || control.iconName === "repeatOff") {
                    ctx.beginPath()
                    ctx.moveTo(cx - s * 0.24, cy - s * 0.17)
                    ctx.lineTo(cx + s * 0.20, cy - s * 0.17)
                    ctx.lineTo(cx + s * 0.20, cy - s * 0.28)
                    ctx.stroke()
                    ctx.beginPath()
                    ctx.moveTo(cx + s * 0.30, cy - s * 0.17)
                    ctx.lineTo(cx + s * 0.18, cy - s * 0.29)
                    ctx.lineTo(cx + s * 0.18, cy - s * 0.05)
                    ctx.closePath()
                    ctx.fill()
                    ctx.beginPath()
                    ctx.moveTo(cx + s * 0.24, cy + s * 0.17)
                    ctx.lineTo(cx - s * 0.20, cy + s * 0.17)
                    ctx.lineTo(cx - s * 0.20, cy + s * 0.28)
                    ctx.stroke()
                    ctx.beginPath()
                    ctx.moveTo(cx - s * 0.30, cy + s * 0.17)
                    ctx.lineTo(cx - s * 0.18, cy + s * 0.29)
                    ctx.lineTo(cx - s * 0.18, cy + s * 0.05)
                    ctx.closePath()
                    ctx.fill()
                    if (control.iconName === "repeatOne") {
                        ctx.font = "bold " + Math.max(14, s * 0.24) + "px sans-serif"
                        ctx.textAlign = "center"
                        ctx.textBaseline = "middle"
                        ctx.fillText("1", cx, cy)
                    }
                    if (control.iconName === "repeatOff") {
                        ctx.strokeStyle = "#ff9bb8"
                        ctx.beginPath()
                        ctx.moveTo(cx - s * 0.34, cy + s * 0.30)
                        ctx.lineTo(cx + s * 0.34, cy - s * 0.30)
                        ctx.stroke()
                    }
                } else {
                    triangle(1, cx)
                }
            }
            Component.onCompleted: requestPaint()
            Connections {
                target: control
                function onIconNameChanged() { iconCanvas.requestPaint() }
                function onActiveChanged() { iconCanvas.requestPaint() }
                function onDownChanged() { iconCanvas.requestPaint() }
            }
        }
        background: Rectangle {
            radius: control.primary ? height / 2 : 8
            color: control.active ? "#8836f6" : "#3324145f"
            border.color: control.down || control.active || control.primary ? "#d9ccff" : "#7f67ff"
            border.width: 1
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: control.primary || control.active ? "#c026d3" : "#5524145f" }
                GradientStop { position: 0.55; color: control.primary || control.active ? "#bf36f6" : "#448b5cf6" }
                GradientStop { position: 1.0; color: control.primary || control.active ? "#7c3aed" : "#332563eb" }
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
                                    clip: true

                                    Image {
                                        anchors.fill: parent
                                        source: modelData.imageUrl && modelData.imageUrl.length > 0 ? djconnect.cachedImageUrl(modelData.imageUrl) : ""
                                        fillMode: Image.PreserveAspectCrop
                                        asynchronous: true
                                        opacity: status === Image.Ready ? 1 : 0
                                    }

                                    Text {
                                        anchors.centerIn: parent
                                        text: "DC"
                                        color: "#ffffff"
                                        font.pixelSize: 20
                                        font.bold: true
                                        visible: !modelData.imageUrl || modelData.imageUrl.length === 0
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

                                IconButton {
                                    iconName: "play"
                                    primary: true
                                    Layout.fillWidth: false
                                    Layout.fillHeight: false
                                    Layout.preferredWidth: 68
                                    Layout.minimumWidth: 68
                                    Layout.maximumWidth: 68
                                    Layout.preferredHeight: 58
                                    Layout.minimumHeight: 58
                                    Layout.maximumHeight: 58
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
            GradientStop { position: 0.0; color: "#2b0a5f" }
            GradientStop { position: 0.42; color: "#21105c" }
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
            anchors.bottomMargin: root.edge + 104
            spacing: 8

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

            }

            Item {
                id: artShell
                Layout.fillWidth: true
                Layout.preferredHeight: 250

                Rectangle {
                    id: artFrame
                    anchors.centerIn: parent
                    width: 250
                    height: 250
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
                Layout.preferredHeight: 72
                spacing: 22

                IconButton {
                    iconName: "previous"
                    onClicked: djconnect.previous()
                }

                IconButton {
                    Layout.preferredWidth: 180
                    iconName: djconnect.playing ? "pause" : "play"
                    primary: true
                    onClicked: djconnect.togglePlay()
                }

                IconButton {
                    iconName: "next"
                    onClicked: djconnect.next()
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 32
                spacing: 12

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 10
                    Layout.alignment: Qt.AlignVCenter
                    radius: 5
                    color: "#5524145f"
                    border.color: "#33406b"
                    border.width: 1

                    Rectangle {
                        width: parent.width * djconnect.trackProgress
                        height: parent.height
                        radius: parent.radius
                        gradient: Gradient {
                            orientation: Gradient.Horizontal
                            GradientStop { position: 0.0; color: "#c026d3" }
                            GradientStop { position: 1.0; color: "#8b5cf6" }
                        }
                    }
                }

                Text {
                    text: djconnect.progressLabel
                    color: "#f4f8f8"
                    font.pixelSize: 18
                    font.bold: true
                    horizontalAlignment: Text.AlignRight
                    Layout.preferredWidth: 102
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 44
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
                Layout.preferredHeight: 54
                spacing: 18

                IconButton {
                    iconName: "shuffle"
                    active: djconnect.shuffle
                    onClicked: djconnect.toggleShuffle()
                }

                IconButton {
                    iconName: djconnect.repeat === "track" ? "repeatOne" : djconnect.repeat === "context" ? "repeat" : "repeatOff"
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
            anchors.margins: 22
            anchors.bottomMargin: 126
            clip: true

            ColumnLayout {
                width: settingsPanel.width - 44
                spacing: 20

                Text {
                    text: djconnect.t("setup_title")
                    color: "#f4f8f8"
                    font.pixelSize: 38
                    font.bold: true
                    Layout.fillWidth: true
                }

                Text {
                    text: djconnect.deviceId
                    color: "#9fb4b8"
                    font.pixelSize: 18
                    elide: Text.ElideMiddle
                    Layout.fillWidth: true
                }

                PurpleButton {
                    visible: !djconnect.paired
                    text: djconnect.demoMode ? djconnect.t("exit_demo") : djconnect.t("demo_mode")
                    font.pixelSize: 24
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

            TextField {
                id: haUrlField
                text: djconnect.haUrl.length ? djconnect.haUrl : "http://homeassistant.local:8123"
                placeholderText: djconnect.t("ha_url")
                font.pixelSize: 24
                Layout.fillWidth: true
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 14

                Text {
                    text: djconnect.t("screen_off")
                    color: "#d7e2e4"
                    font.pixelSize: 22
                    Layout.preferredWidth: 176
                }

                SpinBox {
                    id: screenTimeoutBox
                    from: 0
                    to: 3600
                    stepSize: 30
                    value: djconnect.screenTimeoutSeconds
                    editable: true
                    font.pixelSize: 22
                    Layout.fillWidth: true
                    onValueModified: djconnect.setScreenTimeoutSeconds(value)
                }

                Text {
                    text: screenTimeoutBox.value === 0 ? djconnect.t("off") : djconnect.t("sec")
                    color: "#9fb4b8"
                    font.pixelSize: 20
                    Layout.preferredWidth: 38
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 14

                Text {
                    text: djconnect.t("brightness")
                    color: "#d7e2e4"
                    font.pixelSize: 22
                    Layout.preferredWidth: 176
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
                    font.pixelSize: 20
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
                    font.pixelSize: 22
                    Layout.preferredWidth: 176
                }

                ComboBox {
                    id: updateChannelBox
                    font.pixelSize: 22
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
                    font.pixelSize: 22
                    Layout.preferredWidth: 176
                }

                ComboBox {
                    id: languageBox
                    font.pixelSize: 22
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
                    font.pixelSize: 22
                    Layout.preferredWidth: 176
                }

                ComboBox {
                    id: logLevelBox
                    font.pixelSize: 22
                    model: ["DEBUG", "INFO", "WARNING", "ERROR"]
                    currentIndex: model.indexOf(djconnect.logLevel)
                    Layout.fillWidth: true
                    onActivated: djconnect.setLogLevel(currentText)
                }
            }

            Text {
                text: djconnect.t("log") + ": " + djconnect.logFile
                color: "#91a3a7"
                font.pixelSize: 17
                elide: Text.ElideMiddle
                Layout.fillWidth: true
            }

            PurpleButton {
                text: djconnect.t("save")
                font.pixelSize: 22
                Layout.fillWidth: true
                Layout.preferredHeight: 62
                onClicked: {
                    djconnect.setHaUrl(haUrlField.text)
                    if (djconnect.paired) root.activeScreen = "now"
                }
            }

            PurpleButton {
                text: djconnect.t("close")
                font.pixelSize: 24
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
        items: djconnect.queueItems
    }

    MediaListPanel {
        visible: root.activeScreen === "playlists"
        heading: djconnect.t("playlists")
        items: djconnect.playlistItems
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
                onClicked: {
                    root.activeScreen = "queue"
                    djconnect.loadQueue()
                }
            }

            PurpleButton {
                text: djconnect.t("playlists")
                font.pixelSize: 15
                checkable: true
                checked: root.activeScreen === "playlists"
                Layout.fillWidth: true
                Layout.fillHeight: true
                onClicked: {
                    root.activeScreen = "playlists"
                    djconnect.loadPlaylists()
                }
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
            width: Math.min(parent.width - 40, 640)
            spacing: 14

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

                    Image {
                        source: "app-icon.png"
                        Layout.preferredWidth: 84
                        Layout.preferredHeight: 84
                        fillMode: Image.PreserveAspectFit
                        smooth: true
                        mipmap: true
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6

                        Text {
                            text: "DJConnect"
                            color: "#ffffff"
                            font.pixelSize: 38
                            font.bold: true
                            Layout.fillWidth: true
                        }

                        Text {
                            text: djconnect.t("tagline")
                            color: "#c9c3d8"
                            font.pixelSize: 20
                            font.bold: true
                            Layout.fillWidth: true
                        }
                    }
                }
            }

            Text {
                text: djconnect.t("pairing_screen_title")
                color: "#d7e2e4"
                font.pixelSize: 38
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
            }

            Text {
                text: djconnect.t("pairing_hint")
                color: "#b7a8c8"
                font.pixelSize: 20
                font.bold: true
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 98
                radius: 8
                color: "#5524145f"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 4

                    Text {
                        text: djconnect.t("pairing_code")
                        color: "#b7a8c8"
                        font.pixelSize: 18
                        font.bold: true
                        Layout.fillWidth: true
                    }

                    Text {
                        text: djconnect.pairingCode
                        color: "#ffffff"
                        font.pixelSize: 36
                        font.bold: true
                        Layout.fillWidth: true
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 88
                radius: 8
                color: "#5524145f"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 4

                    Text {
                        text: djconnect.t("client_api_url")
                        color: "#b7a8c8"
                        font.pixelSize: 18
                        font.bold: true
                        Layout.fillWidth: true
                    }

                    Text {
                        text: djconnect.localApiUrl
                        color: "#ffffff"
                        font.pixelSize: 24
                        font.bold: true
                        font.family: "monospace"
                        elide: Text.ElideMiddle
                        Layout.fillWidth: true
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 72
                radius: 8
                color: "#3324145f"

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 18
                    spacing: 18

                    BusyIndicator {
                        running: pairingPanel.visible
                        implicitWidth: 38
                        implicitHeight: 38
                    }

                    Text {
                        text: djconnect.t("waiting_for_ha")
                        color: "#ffffff"
                        font.pixelSize: 22
                        font.bold: true
                        Layout.fillWidth: true
                    }
                }
            }

            PurpleButton {
                text: djconnect.t("start_demo_mode")
                font.pixelSize: 22
                Layout.fillWidth: true
                Layout.preferredHeight: 54
                onClicked: djconnect.enterDemoMode()
            }

        }
    }

    Rectangle {
        id: pairingSuccessPanel
        anchors.fill: parent
        color: "#e6070b16"
        visible: !root.splashVisible && djconnect.pairingSuccessVisible
        z: 34

        ColumnLayout {
            anchors.centerIn: parent
            width: Math.min(parent.width - 40, 640)
            spacing: 28

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

                    Image {
                        source: "app-icon.png"
                        Layout.preferredWidth: 84
                        Layout.preferredHeight: 84
                        fillMode: Image.PreserveAspectFit
                        smooth: true
                        mipmap: true
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6

                        Text {
                            text: "DJConnect"
                            color: "#ffffff"
                            font.pixelSize: 38
                            font.bold: true
                            Layout.fillWidth: true
                        }

                        Text {
                            text: djconnect.t("tagline")
                            color: "#c9c3d8"
                            font.pixelSize: 20
                            font.bold: true
                            Layout.fillWidth: true
                        }
                    }
                }
            }

            Rectangle {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: 132
                Layout.preferredHeight: 132
                radius: 66
                color: "#31d65a"

                Canvas {
                    anchors.fill: parent
                    antialiasing: true
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.clearRect(0, 0, width, height)
                        ctx.strokeStyle = "#2b1767"
                        ctx.lineWidth = 14
                        ctx.lineCap = "round"
                        ctx.lineJoin = "round"
                        ctx.beginPath()
                        ctx.moveTo(width * 0.28, height * 0.52)
                        ctx.lineTo(width * 0.44, height * 0.68)
                        ctx.lineTo(width * 0.72, height * 0.32)
                        ctx.stroke()
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 10

                Text {
                    text: djconnect.t("pairing_success_title")
                    color: "#f4f0ff"
                    font.pixelSize: 38
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                }

                Text {
                    text: djconnect.t("pairing_success_message")
                    color: "#c9c3d8"
                    font.pixelSize: 20
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                }
            }

            PurpleButton {
                text: djconnect.t("start")
                font.pixelSize: 24
                Layout.fillWidth: true
                Layout.preferredHeight: 58
                onClicked: {
                    root.activeScreen = "now"
                    djconnect.startAfterPairing()
                }
            }
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
            height: 300
            radius: 8
            color: "#cc0b1024"
            border.color: "#4050a8"
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 26
                spacing: 10

                Image {
                    source: "app-icon.png"
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: 92
                    Layout.preferredHeight: 92
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    mipmap: true
                }

                Text {
                    text: "DJConnect"
                    color: "#f4f8f8"
                    font.pixelSize: 46
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                }

                Text {
                    text: "v" + djconnect.version
                    color: "#d946ef"
                    font.pixelSize: 20
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
                    implicitWidth: 42
                    implicitHeight: 42
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
                PurpleButton {
                    text: djconnect.t("refresh")
                    font.pixelSize: 24
                    onClicked: {
                        djconnect.showLogs()
                        Qt.callLater(function() { logsArea.cursorPosition = logsArea.length })
                    }
                }
                PurpleButton { text: djconnect.t("close"); font.pixelSize: 24; onClicked: djconnect.hideLogs() }
            }

            ScrollView {
                id: logsScroll
                Layout.fillWidth: true
                Layout.fillHeight: true

                TextArea {
                    id: logsArea
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
                    onTextChanged: Qt.callLater(function() { logsArea.cursorPosition = logsArea.length })
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

                        Image {
                            Layout.preferredWidth: 82
                            Layout.preferredHeight: 82
                            source: "app-icon.png"
                            fillMode: Image.PreserveAspectFit
                            smooth: true
                            mipmap: true
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4

                            Text {
                                text: "DJConnect"
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
                    Text { text: "DJConnect"; color: "#ffffff"; font.pixelSize: 20; Layout.fillWidth: true }
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
