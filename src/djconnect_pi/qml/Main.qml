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
    property bool resetPairingConfirmOpen: false
    property bool rebootConfirmOpen: false
    property bool shutdownConfirmOpen: false
    property bool clearLogsConfirmOpen: false
    property bool forceScreenAwake: false
    property bool forceBrightnessFull: false
    property bool suppressNextNowPanelTap: false
    property bool askDjKeyboardShift: false
    property bool askDjKeyboardOpen: false
    property int standardButtonRadius: 8
    property bool screenBlanked: djconnect.screenTimeoutSeconds > 0 && !idleTimer.running && !root.forceScreenAwake
    property real brightnessOverlayOpacity: root.screenBlanked || root.forceBrightnessFull ? 0 : 1 - (djconnect.screenBrightnessPercent / 100.0)
    property int trVersion: djconnect.translationVersion

    function tr(key) {
        root.trVersion
        return djconnect.t(key)
    }

    function repeatLabel(value) {
        if (value === "track") return root.tr("repeat_one")
        if (value === "context") return root.tr("repeat")
        return root.tr("repeat_off")
    }

    function recordActivity() {
        var wasBlanked = root.screenBlanked
        root.forceBrightnessFull = false
        root.restartIdleTimer()
        if (wasBlanked) {
            root.hideTransientUi()
            root.activeScreen = "now"
            root.suppressNextNowPanelTap = true
            djconnect.refresh()
        }
    }

    function restartIdleTimer() {
        if (djconnect.screenTimeoutSeconds > 0) {
            idleTimer.restart()
        }
    }

    function wakeDisplay() {
        root.recordActivity()
    }

    onActiveScreenChanged: {
        root.restartIdleTimer()
        root.askDjKeyboardOpen = false
        root.askDjKeyboardShift = false
        if (root.activeScreen === "askdj") {
            root.scrollAskDjToBottom()
        }
    }

    function scrollAskDjToBottom() {
        Qt.callLater(function() {
            if (!askDjScroll || !askDjScroll.contentItem) {
                return
            }
            askDjScroll.contentItem.contentY = Math.max(
                0,
                askDjScroll.contentItem.contentHeight - askDjScroll.contentItem.height
            )
        })
    }

    function hideTransientUi() {
        root.aboutOpen = false
        root.resetPairingConfirmOpen = false
        root.rebootConfirmOpen = false
        root.shutdownConfirmOpen = false
        root.clearLogsConfirmOpen = false
        djconnect.hideLogs()
    }

    function temporaryWake(seconds, navigateNow) {
        if (navigateNow) {
            root.hideTransientUi()
            root.activeScreen = "now"
        }
        root.forceScreenAwake = true
        root.forceBrightnessFull = true
        forcedWakeTimer.interval = Math.max(1000, seconds * 1000)
        forcedWakeTimer.restart()
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
            radius: root.standardButtonRadius
            border.width: 0
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: control.enabled ? "#247fff" : "#33415f" }
                GradientStop { position: 0.58; color: control.enabled ? "#7757ff" : "#3c3f61" }
                GradientStop { position: 1.0; color: control.enabled ? "#c33cff" : "#4b3d65" }
            }
            opacity: control.down ? 0.78 : (control.enabled ? 1.0 : 0.62)
        }
    }

    component AskDjGradientButton: Button {
        id: askDjButton
        font.pixelSize: 18
        font.bold: true
        contentItem: Text {
            text: askDjButton.text
            font: askDjButton.font
            color: askDjButton.enabled ? "#ffffff" : "#d4d8e8"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            maximumLineCount: 1
        }
        background: Rectangle {
            radius: root.standardButtonRadius
            border.width: 0
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: askDjButton.enabled ? "#247fff" : "#33415f" }
                GradientStop { position: 0.58; color: askDjButton.enabled ? "#7757ff" : "#3c3f61" }
                GradientStop { position: 1.0; color: askDjButton.enabled ? "#c33cff" : "#4b3d65" }
            }
            opacity: askDjButton.down ? 0.78 : (askDjButton.enabled ? 1.0 : 0.62)
        }
    }

    component AskDjKeyButton: Button {
        id: keyButton
        property string keyText: ""
        property string displayText: keyText
        property bool active: false

        text: displayText
        font.pixelSize: 19
        font.bold: true
        Layout.fillWidth: true
        Layout.fillHeight: true
        contentItem: Text {
            text: keyButton.text
            font: keyButton.font
            color: keyButton.enabled ? "#ffffff" : "#93a0b8"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            maximumLineCount: 1
        }
        background: Rectangle {
            radius: root.standardButtonRadius
            color: keyButton.active ? "#3f66d8" : (keyButton.down ? "#4a326e" : "#231a3c")
            border.color: keyButton.active ? "#d8e0ff" : "#4b557d"
            border.width: 1
            opacity: keyButton.enabled ? 1.0 : 0.56
        }
    }

    component MenuIcon: Canvas {
        id: menuIcon
        property string iconName: "more"
        property color iconColor: "#f7f3ff"
        property real strokeWidth: 2.4

        implicitWidth: 32
        implicitHeight: 32
        onIconNameChanged: requestPaint()
        onIconColorChanged: requestPaint()
        onStrokeWidthChanged: requestPaint()
        onPaint: {
            var ctx = getContext("2d")
            var w = width
            var h = height
            var s = Math.min(w, h)
            var x = (w - s) / 2
            var y = (h - s) / 2
            function px(v) { return x + v * s / 32 }
            function py(v) { return y + v * s / 32 }
            function line(x1, y1, x2, y2) {
                ctx.beginPath()
                ctx.moveTo(px(x1), py(y1))
                ctx.lineTo(px(x2), py(y2))
                ctx.stroke()
            }
            function circle(cx, cy, r, fill) {
                ctx.beginPath()
                ctx.arc(px(cx), py(cy), r * s / 32, 0, Math.PI * 2)
                if (fill) ctx.fill()
                else ctx.stroke()
            }
            function roundRect(x0, y0, ww, hh, rr) {
                ctx.beginPath()
                ctx.moveTo(px(x0 + rr), py(y0))
                ctx.lineTo(px(x0 + ww - rr), py(y0))
                ctx.quadraticCurveTo(px(x0 + ww), py(y0), px(x0 + ww), py(y0 + rr))
                ctx.lineTo(px(x0 + ww), py(y0 + hh - rr))
                ctx.quadraticCurveTo(px(x0 + ww), py(y0 + hh), px(x0 + ww - rr), py(y0 + hh))
                ctx.lineTo(px(x0 + rr), py(y0 + hh))
                ctx.quadraticCurveTo(px(x0), py(y0 + hh), px(x0), py(y0 + hh - rr))
                ctx.lineTo(px(x0), py(y0 + rr))
                ctx.quadraticCurveTo(px(x0), py(y0), px(x0 + rr), py(y0))
                ctx.closePath()
                ctx.stroke()
            }

            ctx.clearRect(0, 0, w, h)
            ctx.strokeStyle = menuIcon.iconColor
            ctx.fillStyle = menuIcon.iconColor
            ctx.lineWidth = menuIcon.strokeWidth
            ctx.lineCap = "round"
            ctx.lineJoin = "round"

            if (iconName === "music") {
                line(13, 10, 13, 23)
                line(13, 10, 22, 7)
                line(22, 7, 22, 19)
                circle(10, 23, 3.2, true)
                circle(19, 19, 3.2, true)
            } else if (iconName === "control") {
                line(8, 10, 24, 10); circle(13, 10, 3, false)
                line(8, 16, 24, 16); circle(20, 16, 3, false)
                line(8, 22, 24, 22); circle(11, 22, 3, false)
            } else if (iconName === "chat") {
                roundRect(6, 8, 14, 11, 3)
                line(11, 19, 9, 23)
                roundRect(13, 13, 13, 10, 3)
                line(21, 23, 24, 26)
            } else if (iconName === "queue") {
                ctx.beginPath()
                ctx.moveTo(px(6), py(7)); ctx.lineTo(px(10), py(9.5)); ctx.lineTo(px(6), py(12)); ctx.closePath(); ctx.fill()
                line(13, 9.5, 26, 9.5)
                line(7, 16, 26, 16)
                line(7, 22.5, 26, 22.5)
            } else if (iconName === "more") {
                circle(9, 16, 2.2, true); circle(16, 16, 2.2, true); circle(23, 16, 2.2, true)
            } else if (iconName === "playlists") {
                line(10, 7, 22, 7); line(8, 10, 24, 10)
                roundRect(7, 12, 18, 13, 2)
            } else if (iconName === "gamepad") {
                ctx.beginPath()
                ctx.moveTo(px(8), py(20))
                ctx.quadraticCurveTo(px(10), py(12), px(14), py(14))
                ctx.lineTo(px(18), py(14))
                ctx.quadraticCurveTo(px(22), py(12), px(24), py(20))
                ctx.quadraticCurveTo(px(25), py(25), px(21), py(23))
                ctx.lineTo(px(18), py(20))
                ctx.lineTo(px(14), py(20))
                ctx.lineTo(px(11), py(23))
                ctx.quadraticCurveTo(px(7), py(25), px(8), py(20))
                ctx.stroke()
                line(11, 18, 15, 18); line(13, 16, 13, 20)
                circle(20, 17, 1.2, true); circle(23, 20, 1.2, true)
            } else if (iconName === "settings") {
                circle(16, 16, 5, false)
                for (var i = 0; i < 8; i++) {
                    var a = i * Math.PI / 4
                    line(16 + Math.cos(a) * 8, 16 + Math.sin(a) * 8, 16 + Math.cos(a) * 11, 16 + Math.sin(a) * 11)
                }
            } else if (iconName === "logs") {
                roundRect(9, 6, 13, 18, 2)
                line(13, 11, 18, 11); line(13, 16, 17, 16)
                circle(21, 22, 3.5, false); line(23.5, 24.5, 26, 27)
            } else if (iconName === "info") {
                circle(16, 16, 10, false)
                line(16, 15, 16, 22); circle(16, 10.5, 1.2, true)
            }
        }
    }

    component NavButton: PurpleButton {
        id: navControl
        property string iconName: ""

        font.pixelSize: 15
        contentItem: ColumnLayout {
            spacing: 3

            MenuIcon {
                iconName: navControl.iconName
                iconColor: navControl.enabled ? (navControl.checked ? "#ffffff" : "#d8defa") : "#93a0b8"
                strokeWidth: navControl.checked ? 2.8 : 2.4
                Layout.preferredWidth: navControl.checked ? 30 : 28
                Layout.preferredHeight: navControl.checked ? 30 : 28
                Layout.alignment: Qt.AlignHCenter
                Layout.fillWidth: true
            }

            Text {
                text: navControl.text
                color: navControl.enabled ? (navControl.checked ? "#ffffff" : "#d8defa") : "#93a0b8"
                font: navControl.font
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
                maximumLineCount: 1
                Layout.fillWidth: true
            }
        }
        background: Rectangle {
            radius: root.standardButtonRadius
            border.width: navControl.checked ? 2 : 0
            border.color: "#f5d0fe"
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: navControl.enabled ? "#247fff" : "#33415f" }
                GradientStop { position: 0.58; color: navControl.enabled ? "#7757ff" : "#3c3f61" }
                GradientStop { position: 1.0; color: navControl.enabled ? "#c33cff" : "#4b3d65" }
            }
            opacity: navControl.down ? 0.78 : (navControl.checked ? 1.0 : 0.72)
        }
    }

    component MoreMenuButton: Button {
        id: moreControl
        property string iconName: ""

        font.pixelSize: 25
        font.bold: false
        Layout.fillWidth: true
        Layout.preferredHeight: 66
        contentItem: RowLayout {
            spacing: 18

            MenuIcon {
                iconName: moreControl.iconName
                iconColor: "#f02dff"
                strokeWidth: 2.5
                Layout.preferredWidth: 48
                Layout.preferredHeight: 36
            }

            Text {
                text: moreControl.text
                color: moreControl.enabled ? "#f7f3ff" : "#93a0b8"
                font: moreControl.font
                elide: Text.ElideRight
                verticalAlignment: Text.AlignVCenter
                Layout.fillWidth: true
            }

            Text {
                text: "›"
                color: "#a9abc3"
                font.pixelSize: 42
                verticalAlignment: Text.AlignVCenter
                Layout.preferredWidth: 28
            }
        }
        background: Rectangle {
            radius: root.standardButtonRadius
            border.width: 0
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: moreControl.enabled ? "#247fff" : "#33415f" }
                GradientStop { position: 0.58; color: moreControl.enabled ? "#7757ff" : "#3c3f61" }
                GradientStop { position: 1.0; color: moreControl.enabled ? "#c33cff" : "#4b3d65" }
            }
            opacity: moreControl.down ? 0.78 : (moreControl.enabled ? 1.0 : 0.62)
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
            border.width: 0
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: "#247fff" }
                GradientStop { position: 0.58; color: "#7757ff" }
                GradientStop { position: 1.0; color: "#c33cff" }
            }
            opacity: control.down ? 0.78 : 1.0
            scale: control.down ? 0.96 : 1.0
            Behavior on scale { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }
        }
    }

    component MediaPlayButton: Button {
        id: control

        width: 68
        height: 58
        Layout.fillWidth: false
        Layout.fillHeight: false
        Layout.preferredWidth: 68
        Layout.minimumWidth: 68
        Layout.maximumWidth: 68
        Layout.preferredHeight: 58
        Layout.minimumHeight: 58
        Layout.maximumHeight: 58
        contentItem: Text {
            text: "▶"
            color: "#ffffff"
            font.pixelSize: 28
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            radius: 29
            border.width: 0
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: "#247fff" }
                GradientStop { position: 0.58; color: "#7757ff" }
                GradientStop { position: 1.0; color: "#c33cff" }
            }
            opacity: control.down ? 0.78 : 1.0
        }
    }

    component LoadingSpinner: Item {
        id: spinner
        property bool running: true
        property color dotColor: "#d9ccff"

        implicitWidth: 42
        implicitHeight: 42

        Repeater {
            model: 12

            Rectangle {
                width: Math.max(4, spinner.width * 0.13)
                height: width
                radius: width / 2
                color: spinner.dotColor
                opacity: 0.18 + (index / 11) * 0.72
                x: spinner.width / 2 - width / 2 + Math.cos((index / 12) * Math.PI * 2) * spinner.width * 0.32
                y: spinner.height / 2 - height / 2 + Math.sin((index / 12) * Math.PI * 2) * spinner.height * 0.32
            }
        }

        RotationAnimation on rotation {
            running: spinner.running && spinner.visible
            loops: Animation.Infinite
            from: 0
            to: 360
            duration: 900
        }
    }

    component DangerButton: Button {
        id: control

        font.pixelSize: 24
        font.bold: true
        contentItem: Text {
            text: control.text
            font: control.font
            color: "#ff3128"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        background: Rectangle {
            radius: root.standardButtonRadius
            color: control.down ? "#8d2a35" : "#682632"
            border.color: control.down ? "#ff8a80" : "#a43b49"
            border.width: 1
            opacity: control.down ? 0.82 : 1.0
        }
    }

    component WarningButton: Button {
        id: control

        font.pixelSize: 24
        font.bold: true
        contentItem: Text {
            text: control.text
            font: control.font
            color: "#fff3c4"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        background: Rectangle {
            radius: root.standardButtonRadius
            color: control.down ? "#9a6a17" : "#7a4e10"
            border.color: control.down ? "#ffd166" : "#c58b23"
            border.width: 1
            opacity: control.down ? 0.82 : 1.0
        }
    }

    component ModalBlocker: MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons
        hoverEnabled: true
        preventStealing: true
        propagateComposedEvents: false
        onClicked: function(mouse) { root.recordActivity(); mouse.accepted = true }
        onPressed: function(mouse) { root.recordActivity(); mouse.accepted = true }
        onReleased: function(mouse) { mouse.accepted = true }
        onWheel: function(wheel) { wheel.accepted = true }
    }

    component AppBackground: Item {
        anchors.fill: parent

        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                orientation: Gradient.Vertical
                GradientStop { position: 0.0; color: "#2b0a5f" }
                GradientStop { position: 0.48; color: "#191053" }
                GradientStop { position: 1.0; color: "#070b16" }
            }
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
    }

    component AppBanner: Rectangle {
        id: appBanner
        property string detailText: root.tr("tagline")
        property int logoSize: 84
        property int titleSize: 38
        property int detailSize: 20
        property int horizontalPadding: 28
        property int verticalPadding: 18
        property int contentSpacing: 22

        Layout.fillWidth: true
        Layout.preferredHeight: 132
        radius: 24
        color: "#171029"
        border.color: "#3b2a63"
        border.width: 1
        clip: true
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "#12091d" }
            GradientStop { position: 0.42; color: "#26103f" }
            GradientStop { position: 0.72; color: "#37145a" }
            GradientStop { position: 1.0; color: "#141125" }
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: appBanner.horizontalPadding
            anchors.rightMargin: appBanner.horizontalPadding
            anchors.topMargin: appBanner.verticalPadding
            anchors.bottomMargin: appBanner.verticalPadding
            spacing: appBanner.contentSpacing

            Image {
                source: "app-icon.png"
                Layout.preferredWidth: appBanner.logoSize
                Layout.preferredHeight: appBanner.logoSize
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
                    font.pixelSize: appBanner.titleSize
                    font.bold: true
                    elide: Text.ElideRight
                    maximumLineCount: 1
                    Layout.fillWidth: true
                }

                Text {
                    text: appBanner.detailText
                    color: "#c9c3d8"
                    font.pixelSize: appBanner.detailSize
                    font.bold: true
                    elide: Text.ElideRight
                    maximumLineCount: 1
                    Layout.fillWidth: true
                }
            }
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

                function arrowHead(x, y, dir) {
                    var l = s * 0.11
                    var o = s * 0.08
                    ctx.beginPath()
                    ctx.moveTo(x, y)
                    ctx.lineTo(x - dir * l, y - o)
                    ctx.moveTo(x, y)
                    ctx.lineTo(x - dir * l, y + o)
                    ctx.stroke()
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
                    ctx.lineWidth = Math.max(5, s * 0.09)
                    ctx.beginPath()
                    ctx.moveTo(cx - s * 0.34, cy - s * 0.19)
                    ctx.bezierCurveTo(cx - s * 0.10, cy - s * 0.19, cx + s * 0.02, cy + s * 0.19, cx + s * 0.32, cy + s * 0.19)
                    ctx.stroke()
                    arrowHead(cx + s * 0.34, cy + s * 0.19, 1)
                    ctx.beginPath()
                    ctx.moveTo(cx - s * 0.34, cy + s * 0.19)
                    ctx.bezierCurveTo(cx - s * 0.10, cy + s * 0.19, cx + s * 0.02, cy - s * 0.19, cx + s * 0.32, cy - s * 0.19)
                    ctx.stroke()
                    arrowHead(cx + s * 0.34, cy - s * 0.19, 1)
                } else if (control.iconName === "repeat" || control.iconName === "repeatOne" || control.iconName === "repeatOff") {
                    ctx.lineWidth = Math.max(5, s * 0.09)
                    ctx.beginPath()
                    ctx.moveTo(cx - s * 0.26, cy - s * 0.18)
                    ctx.lineTo(cx + s * 0.25, cy - s * 0.18)
                    ctx.stroke()
                    arrowHead(cx + s * 0.31, cy - s * 0.18, 1)
                    ctx.beginPath()
                    ctx.moveTo(cx + s * 0.26, cy + s * 0.18)
                    ctx.lineTo(cx - s * 0.25, cy + s * 0.18)
                    ctx.stroke()
                    arrowHead(cx - s * 0.31, cy + s * 0.18, -1)
                    if (control.iconName === "repeatOne") {
                        ctx.font = "bold " + Math.max(14, s * 0.24) + "px sans-serif"
                        ctx.textAlign = "center"
                        ctx.textBaseline = "middle"
                        ctx.fillText("1", cx, cy)
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
            radius: root.standardButtonRadius
            border.width: control.active ? 2 : 0
            border.color: "#f5d0fe"
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: control.enabled ? "#247fff" : "#33415f" }
                GradientStop { position: 0.58; color: control.enabled ? "#7757ff" : "#3c3f61" }
                GradientStop { position: 1.0; color: control.enabled ? "#c33cff" : "#4b3d65" }
            }
            opacity: control.down ? 0.78 : (control.enabled ? 1.0 : 0.62)
            scale: control.down ? 0.96 : 1.0
            Behavior on scale { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }
        }
    }

    component MediaListPanel: Rectangle {
        id: panel
        property string heading: ""
        property string emptyText: ""
        property string playCommand: "play_context_at"
        property var items: []
        signal refreshRequested()

        function itemPayload(item) {
            return JSON.stringify({
                title: item.title || "",
                subtitle: item.subtitle || "",
                artist: item.artist || "",
                uri: item.uri || "",
                value: item.value || "",
                contextUri: item.contextUri || "",
                context_uri: item.context_uri || "",
                queueContext: item.queueContext || "",
                queue_context: item.queue_context || "",
                index: typeof item.index === "number" ? item.index : null
            })
        }

        anchors.fill: parent
        color: "#070b16"
        z: 16

        AppBackground {}
        ModalBlocker {}

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            anchors.bottomMargin: 130
            spacing: 12

            RowLayout {
                Layout.fillWidth: true

                Text {
                    text: panel.heading
                    color: "#ffffff"
                    font.pixelSize: 34
                    font.bold: true
                    Layout.fillWidth: true
                }

                PurpleButton {
                    text: root.tr("refresh")
                    font.pixelSize: 18
                    Layout.preferredWidth: 142
                    Layout.preferredHeight: 48
                    onClicked: panel.refreshRequested()
                }
            }

            ScrollView {
                id: mediaScroll
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                contentWidth: availableWidth

                ColumnLayout {
                    width: Math.max(0, mediaScroll.availableWidth)
                    spacing: 12

                    Text {
                        text: panel.emptyText
                        visible: panel.items.length === 0
                        color: "#b7c2d8"
                        font.pixelSize: 26
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                        Layout.topMargin: 36
                    }

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

                            Item {
                                anchors.fill: parent
                                anchors.margins: 12

                                MouseArea {
                                    anchors.fill: parent
                                    enabled: modelData.uri && modelData.uri.length > 0
                                    onClicked: djconnect.playMediaItem(panel.playCommand, panel.itemPayload(modelData))
                                }

                                Rectangle {
                                    id: mediaArt
                                    anchors.left: parent.left
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: 68
                                    height: 68
                                    radius: 8
                                    color: modelData.tint
                                    clip: true

                                    Image {
                                        anchors.fill: parent
                                        source: modelData.imageUrl && modelData.imageUrl.length > 0 ? modelData.imageUrl : ""
                                        sourceSize.width: 68
                                        sourceSize.height: 68
                                        fillMode: Image.PreserveAspectCrop
                                        asynchronous: true
                                        cache: false
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

                                Column {
                                    id: mediaText
                                    anchors.left: mediaArt.right
                                    anchors.leftMargin: 14
                                    anchors.right: mediaPlay.left
                                    anchors.rightMargin: 14
                                    anchors.verticalCenter: parent.verticalCenter
                                    spacing: 2
                                    clip: true

                                    Text {
                                        text: modelData.title
                                        color: "#ffffff"
                                        font.pixelSize: 24
                                        font.bold: true
                                        elide: Text.ElideRight
                                        width: parent.width
                                    }

                                    Text {
                                        text: modelData.subtitle
                                        visible: modelData.subtitle.length > 0
                                        color: "#b7c2d8"
                                        font.pixelSize: 17
                                        elide: Text.ElideRight
                                        width: parent.width
                                    }
                                }

                                MediaPlayButton {
                                    id: mediaPlay
                                    anchors.right: parent.right
                                    anchors.verticalCenter: parent.verticalCenter
                                    enabled: modelData.uri && modelData.uri.length > 0
                                    onClicked: djconnect.playMediaItem(panel.playCommand, panel.itemPayload(modelData))
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
        onTriggered: {
            root.hideTransientUi()
            root.activeScreen = "now"
        }
    }

    Timer {
        id: forcedWakeTimer
        interval: 10000
        repeat: false
        onTriggered: {
            root.forceScreenAwake = false
            root.forceBrightnessFull = false
        }
    }

    Timer {
        id: djResponseTimer
        interval: 20000
        repeat: false
        onTriggered: djconnect.clearDjResponse()
    }

    Timer {
        id: askDjPollTimer
        interval: 7000
        running: root.activeScreen === "askdj" && djconnect.paired && !djconnect.demoMode
        repeat: true
        triggeredOnStart: true
        onTriggered: djconnect.pollAskDjHistory()
    }

    Connections {
        target: djconnect
        function onWakeScreenRequested() {
            root.forceScreenAwake = true
            root.forceBrightnessFull = false
            root.restartIdleTimer()
            forcedWakeTimer.interval = 10000
            forcedWakeTimer.restart()
        }
        function onTemporaryWakeRequested(seconds, navigateNow) {
            root.temporaryWake(seconds, navigateNow)
        }
        function onDjResponseChanged() {
            if (djconnect.djResponseVisible) {
                djResponseTimer.restart()
            } else {
                djResponseTimer.stop()
            }
        }
        function onAskDjChanged() {
            if (root.activeScreen === "askdj") {
                root.scrollAskDjToBottom()
            }
        }
        function onScreenshotRequested() {
            root.forceScreenAwake = true
            root.forceBrightnessFull = false
            root.restartIdleTimer()
            forcedWakeTimer.interval = 10000
            forcedWakeTimer.restart()
            Qt.callLater(function() {
                root.contentItem.grabToImage(function(result) {
                    result.saveToFile(djconnect.screenshotFile)
                }, Qt.size(root.width, root.height))
            })
        }
        function onDebugScreenRequested(screen) {
            root.splashVisible = false
            root.aboutOpen = false
            root.resetPairingConfirmOpen = false
            root.rebootConfirmOpen = false
            root.shutdownConfirmOpen = false
            if (screen === "logs") {
                djconnect.showLogs()
                return
            }
            djconnect.hideLogs()
            if (screen === "about") {
                root.activeScreen = "settings"
                root.aboutOpen = true
                return
            }
            if (screen === "queue") {
                root.activeScreen = "queue"
                djconnect.loadQueue()
                return
            }
            if (screen === "playlists") {
                root.activeScreen = "playlists"
                djconnect.loadPlaylists()
                return
            }
            if (screen === "games" || screen === "settings" || screen === "now" || screen === "control" || screen === "askdj") {
                root.activeScreen = screen
            }
        }
    }

    Timer {
        id: splashTimer
        interval: 1400
        running: true
        repeat: false
        onTriggered: root.splashVisible = false
    }

    Rectangle {
        anchors.fill: parent
        color: root.color
        z: -1000
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons
        propagateComposedEvents: true
        onPressed: function(mouse) { root.recordActivity(); mouse.accepted = false }
    }

    Item {
        id: nowPanel
        anchors.fill: parent
        visible: root.activeScreen === "now"
        z: 5

        AppBackground {}

        ColumnLayout {
            anchors.fill: parent
            anchors.leftMargin: 16
            anchors.topMargin: 16
            anchors.rightMargin: 16
            anchors.bottomMargin: root.edge + 96
            spacing: 10

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 48
                spacing: 10

                Text {
                    text: root.tr("now_playing")
                    color: "#f4f8f8"
                    font.pixelSize: 34
                    font.bold: true
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
                    text: root.tr("refresh")
                    font.pixelSize: 18
                    Layout.preferredWidth: 118
                    Layout.preferredHeight: 48
                    Layout.rightMargin: 0
                    onClicked: djconnect.manualRefresh()
                }

                PurpleButton {
                    text: root.tr("add_to_favorites")
                    font.pixelSize: 17
                    Layout.preferredWidth: 126
                    Layout.preferredHeight: 48
                    enabled: djconnect.paired && (djconnect.title.length > 0 || djconnect.artist.length > 0)
                    onClicked: djconnect.saveCurrentTrack()
                }

            }

            Item {
                id: artShell
                Layout.fillWidth: true
                Layout.fillHeight: true

                Rectangle {
                    id: artFrame
                    anchors.centerIn: parent
                    width: Math.min(parent.width, parent.height)
                    height: width
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
                        sourceSize.width: width
                        sourceSize.height: height
                        fillMode: Image.PreserveAspectCrop
                        asynchronous: true
                        cache: true
                        opacity: status === Image.Ready ? 1 : 0

                        Behavior on opacity { NumberAnimation { duration: 240 } }
                    }

                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        z: 2
                        height: Math.max(112, parent.height * 0.34)
                        gradient: Gradient {
                            orientation: Gradient.Vertical
                            GradientStop { position: 0.0; color: "#00000000" }
                            GradientStop { position: 0.44; color: "#b0000000" }
                            GradientStop { position: 1.0; color: "#e8000000" }
                        }
                    }

                    ColumnLayout {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        anchors.margins: 18
                        z: 3
                        spacing: 4

                        Text {
                            text: djconnect.title
                            color: "#ffffff"
                            font.pixelSize: 34
                            font.bold: true
                            horizontalAlignment: Text.AlignHCenter
                            elide: Text.ElideRight
                            maximumLineCount: 1
                            style: Text.Raised
                            styleColor: "#aa000000"
                            Layout.fillWidth: true
                        }

                        Text {
                            text: djconnect.artist
                            color: "#d8e3f2"
                            font.pixelSize: 24
                            horizontalAlignment: Text.AlignHCenter
                            elide: Text.ElideRight
                            maximumLineCount: 1
                            style: Text.Raised
                            styleColor: "#aa000000"
                            Layout.fillWidth: true
                        }
                    }

                    Rectangle {
                        anchors.fill: parent
                        z: 1
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

                }

                TapHandler {
                    onTapped: {
                        if (root.suppressNextNowPanelTap) {
                            root.suppressNextNowPanelTap = false
                            return
                        }
                        root.activeScreen = "control"
                    }
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
                onTapped: root.wakeDisplay()
            }
        }

    }

    Rectangle {
        id: controlPanel
        anchors.fill: parent
        color: "#070b16"
        visible: root.activeScreen === "control"
        z: 10

        AppBackground {}
        ModalBlocker {}

        ColumnLayout {
            anchors.fill: parent
            anchors.leftMargin: 16
            anchors.topMargin: 16
            anchors.rightMargin: 16
            anchors.bottomMargin: root.edge + 112
            spacing: 10

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 48
                spacing: 10

                Text {
                    text: root.tr("control")
                    color: "#f4f8f8"
                    font.pixelSize: 34
                    font.bold: true
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }

                BusyIndicator {
                    running: djconnect.busy
                    visible: djconnect.busy
                    implicitWidth: 30
                    implicitHeight: 30
                }

                PurpleButton {
                    text: root.tr("refresh")
                    font.pixelSize: 18
                    Layout.preferredWidth: 142
                    Layout.preferredHeight: 48
                    onClicked: djconnect.manualRefresh()
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 72
                spacing: 2

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
                    color: "#b8c5e8"
                    font.pixelSize: 28
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideRight
                    maximumLineCount: 1
                    Layout.fillWidth: true
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 178
                spacing: 18

                IconButton {
                    iconName: "previous"
                    onClicked: djconnect.previous()
                }

                IconButton {
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
                Layout.preferredHeight: 54
                spacing: 12

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 18
                    Layout.alignment: Qt.AlignVCenter
                    radius: 8
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
                    font.pixelSize: 24
                    font.bold: true
                    horizontalAlignment: Text.AlignRight
                    Layout.preferredWidth: 128
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 74
                spacing: 14

                Text {
                    text: root.tr("vol")
                    color: "#d7e2e4"
                    font.pixelSize: 24
                    Layout.preferredWidth: 46
                }

                PurpleButton {
                    text: "-"
                    font.pixelSize: 30
                    Layout.preferredWidth: 54
                    Layout.preferredHeight: 54
                    onClicked: djconnect.adjustVolume(-10)
                }

                Slider {
                    id: controlVolumeSlider
                    from: 0
                    to: 60
                    value: Math.min(60, djconnect.volume)
                    stepSize: 1
                    Layout.fillWidth: true
                    onMoved: djconnect.setVolume(Math.round(value))
                    background: Rectangle {
                        x: controlVolumeSlider.leftPadding
                        y: controlVolumeSlider.topPadding + controlVolumeSlider.availableHeight / 2 - height / 2
                        width: controlVolumeSlider.availableWidth
                        height: 10
                        radius: 5
                        color: "#3324145f"

                        Rectangle {
                            width: controlVolumeSlider.visualPosition * parent.width
                            height: parent.height
                            radius: parent.radius
                            gradient: Gradient {
                                orientation: Gradient.Horizontal
                                GradientStop { position: 0.0; color: "#ec4899" }
                                GradientStop { position: 1.0; color: "#8b5cf6" }
                            }
                        }
                    }
                    handle: Rectangle {
                        x: controlVolumeSlider.leftPadding + controlVolumeSlider.visualPosition * (controlVolumeSlider.availableWidth - width)
                        y: controlVolumeSlider.topPadding + controlVolumeSlider.availableHeight / 2 - height / 2
                        width: 34
                        height: 34
                        radius: 17
                        color: "#f8f4ff"
                        border.color: "#d9ccff"
                        border.width: 1
                    }
                }

                PurpleButton {
                    text: "+"
                    font.pixelSize: 30
                    Layout.preferredWidth: 54
                    Layout.preferredHeight: 54
                    onClicked: djconnect.adjustVolume(10)
                }

                Text {
                    text: Math.round(Math.min(60, djconnect.volume) / 60 * 100) + "%"
                    color: "#f4f8f8"
                    font.pixelSize: 26
                    font.bold: true
                    horizontalAlignment: Text.AlignRight
                    Layout.preferredWidth: 54
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 76
                spacing: 12

                ComboBox {
                    id: controlOutputDeviceCombo
                    property string noOutputDeviceLabel: root.tr("none")
                    property var deviceChoices: [noOutputDeviceLabel].concat(djconnect.outputDevices.length > 0 ? djconnect.outputDevices : (djconnect.outputDevice.length > 0 ? [djconnect.outputDevice] : []))
                    function selectedIndex() {
                        var selected = (djconnect.outputDevice || "").trim()
                        if (selected.length === 0) return 0
                        for (var i = 0; i < deviceChoices.length; i++) {
                            if ((deviceChoices[i] || "").trim() === selected) return i
                        }
                        return 0
                    }
                    model: deviceChoices
                    visible: count > 1 || djconnect.outputDevice.length === 0
                    currentIndex: selectedIndex()
                    font.pixelSize: 26
                    delegate: ItemDelegate {
                        width: controlOutputDeviceCombo.width
                        text: modelData
                        font.pixelSize: 28
                    }
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    onActivated: function(index) {
                        var value = controlOutputDeviceCombo.textAt(index)
                        djconnect.setOutputDevice(value === controlOutputDeviceCombo.noOutputDeviceLabel ? "" : value)
                    }
                }

                Text {
                    text: root.tr("output_device")
                    visible: controlOutputDeviceCombo.count <= 1 && djconnect.outputDevice.length > 0
                    color: "#b8c5e8"
                    font.pixelSize: 24
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 126
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

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 24
                spacing: 9

                Rectangle {
                    width: 14
                    height: 14
                    radius: 7
                    color: djconnect.paired ? (djconnect.backendAvailable ? "#32d35a" : "#ff3b30") : "#e0a83a"
                    Layout.alignment: Qt.AlignVCenter
                }

                Text {
                    text: djconnect.statusText
                    color: "#c2d3d6"
                    font.pixelSize: 16
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
            }
        }
    }

    Rectangle {
        id: settingsPanel
        anchors.fill: parent
        color: "#070b16"
        visible: settingsOpen && (djconnect.paired || djconnect.demoMode)
        z: 10

        AppBackground {}

        ScrollView {
            id: settingsScroll
            anchors.fill: parent
            anchors.margins: 22
            anchors.bottomMargin: 130
            clip: true
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            contentWidth: availableWidth

            ColumnLayout {
                width: Math.max(0, settingsScroll.availableWidth)
                spacing: 20

                Text {
                    text: root.tr("setup_title")
                    color: "#f4f8f8"
                    font.pixelSize: 38
                    font.bold: true
                    Layout.fillWidth: true
                }

                PurpleButton {
                    visible: !djconnect.paired
                    text: djconnect.demoMode ? root.tr("exit_demo") : root.tr("demo_mode")
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

            RowLayout {
                Layout.fillWidth: true
                spacing: 14

                Text {
                    text: root.tr("screen_off")
                    color: "#d7e2e4"
                    font.pixelSize: 22
                    Layout.preferredWidth: 176
                }

                ComboBox {
                    id: screenTimeoutBox
                    property var timeoutChoices: [30, 60, 90, 120, 180, 240, 300, 600]
                    model: timeoutChoices
                    currentIndex: Math.max(0, timeoutChoices.indexOf(djconnect.screenTimeoutSeconds))
                    font.pixelSize: 28
                    delegate: ItemDelegate {
                        width: screenTimeoutBox.width
                        text: modelData
                        font.pixelSize: 30
                    }
                    Layout.fillWidth: true
                    onActivated: function(index) { djconnect.setScreenTimeoutSeconds(timeoutChoices[index]) }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 14

                Text {
                    text: root.tr("brightness")
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
                    background: Rectangle {
                        x: brightnessSlider.leftPadding
                        y: brightnessSlider.topPadding + brightnessSlider.availableHeight / 2 - height / 2
                        width: brightnessSlider.availableWidth
                        height: 10
                        radius: 5
                        color: "#3324145f"

                        Rectangle {
                            width: brightnessSlider.visualPosition * parent.width
                            height: parent.height
                            radius: parent.radius
                            gradient: Gradient {
                                orientation: Gradient.Horizontal
                                GradientStop { position: 0.0; color: "#ec4899" }
                                GradientStop { position: 1.0; color: "#8b5cf6" }
                            }
                        }
                    }
                    handle: Rectangle {
                        x: brightnessSlider.leftPadding + brightnessSlider.visualPosition * (brightnessSlider.availableWidth - width)
                        y: brightnessSlider.topPadding + brightnessSlider.availableHeight / 2 - height / 2
                        width: 30
                        height: 30
                        radius: 15
                        color: "#f8f4ff"
                        border.color: "#d9ccff"
                        border.width: 1
                    }
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
                    text: root.tr("updates")
                    color: "#d7e2e4"
                    font.pixelSize: 22
                    Layout.preferredWidth: 176
                }

                ComboBox {
                    id: updateChannelBox
                    font.pixelSize: 28
                    model: ["stable", "beta"]
                    currentIndex: djconnect.updateChannel === "beta" ? 1 : 0
                    delegate: ItemDelegate {
                        width: updateChannelBox.width
                        text: modelData
                        font.pixelSize: 30
                    }
                    Layout.fillWidth: true
                    onActivated: djconnect.setUpdateChannel(currentText)
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 14

                Text {
                    text: root.tr("language")
                    color: "#d7e2e4"
                    font.pixelSize: 22
                    Layout.preferredWidth: 176
                }

                ComboBox {
                    id: languageBox
                    font.pixelSize: 28
                    model: [
                        { code: "nl", label: "Nederlands" },
                        { code: "en", label: "English" }
                    ]
                    textRole: "label"
                    valueRole: "code"
                    currentIndex: djconnect.language === "en" ? 1 : 0
                    delegate: ItemDelegate {
                        width: languageBox.width
                        text: modelData.label
                        font.pixelSize: 30
                    }
                    Layout.fillWidth: true
                    onActivated: djconnect.setLanguage(currentValue)
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 14

                Text {
                    text: root.tr("log_level")
                    color: "#d7e2e4"
                    font.pixelSize: 22
                    Layout.preferredWidth: 176
                }

                ComboBox {
                    id: logLevelBox
                    font.pixelSize: 28
                    model: ["DEBUG", "INFO", "WARNING", "ERROR"]
                    currentIndex: model.indexOf(djconnect.logLevel)
                    delegate: ItemDelegate {
                        width: logLevelBox.width
                        text: modelData
                        font.pixelSize: 30
                    }
                    Layout.fillWidth: true
                    onActivated: djconnect.setLogLevel(currentText)
                }
            }

            PurpleButton {
                text: root.tr("view_logs")
                font.pixelSize: 24
                Layout.fillWidth: true
                Layout.preferredHeight: 58
                onClicked: djconnect.showLogs()
            }

            PurpleButton {
                text: root.tr("check_updates")
                font.pixelSize: 24
                Layout.fillWidth: true
                Layout.preferredHeight: 58
                onClicked: djconnect.checkForUpdates()
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                DangerButton {
                    text: root.tr("reset_pairing")
                    Layout.fillWidth: true
                    Layout.preferredHeight: 58
                    onClicked: root.resetPairingConfirmOpen = true
                }

                PurpleButton {
                    text: root.tr("about")
                    Layout.fillWidth: true
                    Layout.preferredHeight: 58
                    onClicked: root.aboutOpen = true
                }
            }

            WarningButton {
                text: root.tr("reboot_device")
                font.pixelSize: 24
                Layout.fillWidth: true
                Layout.preferredHeight: 58
                onClicked: root.rebootConfirmOpen = true
            }

            DangerButton {
                text: root.tr("shutdown_device")
                font.pixelSize: 24
                Layout.fillWidth: true
                Layout.preferredHeight: 58
                onClicked: root.shutdownConfirmOpen = true
            }

            Item { Layout.fillHeight: true }
        }
    }
    }

    MediaListPanel {
        visible: root.activeScreen === "queue"
        heading: root.tr("queue")
        emptyText: root.tr("empty_queue")
        playCommand: "play_context_at"
        items: djconnect.queueItems
        onRefreshRequested: djconnect.loadQueue()
    }

    MediaListPanel {
        visible: root.activeScreen === "playlists"
        heading: root.tr("playlists")
        emptyText: root.tr("empty_playlists")
        playCommand: "start_playlist"
        items: djconnect.playlistItems
        onRefreshRequested: djconnect.loadPlaylists()
    }

    Rectangle {
        id: morePanel
        anchors.fill: parent
        color: "#070b16"
        visible: root.activeScreen === "more"
        z: 16

        AppBackground {}
        ModalBlocker {}

        ColumnLayout {
            anchors.fill: parent
            anchors.leftMargin: 28
            anchors.topMargin: 26
            anchors.rightMargin: 28
            anchors.bottomMargin: root.edge + 126
            spacing: 16

            Text {
                text: root.tr("more")
                color: "#f4f8f8"
                font.pixelSize: 48
                font.bold: true
                elide: Text.ElideRight
                Layout.fillWidth: true
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: moreMenuColumn.implicitHeight
                radius: 24
                color: "#dd20113d"
                border.color: "#3b3d68"
                border.width: 1
                clip: true
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: "#3a0f43" }
                    GradientStop { position: 0.58; color: "#251a54" }
                    GradientStop { position: 1.0; color: "#1b2456" }
                }

                ColumnLayout {
                    id: moreMenuColumn
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    spacing: 0

                    MoreMenuButton {
                        text: root.tr("playlists")
                        iconName: "playlists"
                        onClicked: {
                            root.activeScreen = "playlists"
                            djconnect.loadPlaylists()
                        }
                    }
                    Rectangle { Layout.fillWidth: true; Layout.leftMargin: 122; Layout.preferredHeight: 1; color: "#4d4a68" }

                    MoreMenuButton {
                        text: root.tr("games")
                        iconName: "gamepad"
                        onClicked: root.activeScreen = "games"
                    }
                    Rectangle { Layout.fillWidth: true; Layout.leftMargin: 122; Layout.preferredHeight: 1; color: "#4d4a68" }

                    MoreMenuButton {
                        text: root.tr("setup")
                        iconName: "settings"
                        onClicked: root.activeScreen = "settings"
                    }
                    Rectangle { Layout.fillWidth: true; Layout.leftMargin: 122; Layout.preferredHeight: 1; color: "#4d4a68" }

                    MoreMenuButton {
                        text: root.tr("logs")
                        iconName: "logs"
                        onClicked: djconnect.showLogs()
                    }
                    Rectangle { Layout.fillWidth: true; Layout.leftMargin: 122; Layout.preferredHeight: 1; color: "#4d4a68" }

                    MoreMenuButton {
                        text: root.tr("about")
                        iconName: "info"
                        onClicked: root.aboutOpen = true
                    }
                }
            }

            Item { Layout.fillHeight: true }
        }
    }

    Rectangle {
        id: askDjPanel
        anchors.fill: parent
        color: "#070b16"
        visible: root.activeScreen === "askdj"
        z: 17

        function sendAskDjInput() {
            var message = askDjInput.text.trim()
            if (message.length > 0 && !djconnect.askDjBusy) {
                askDjInput.text = ""
                root.askDjKeyboardShift = false
                root.askDjKeyboardOpen = false
                djconnect.sendAskDjMessage(message)
            }
        }

        function insertAskDjText(value) {
            if (djconnect.askDjBusy || value.length === 0) {
                return
            }
            var pos = Math.max(0, askDjInput.cursorPosition)
            askDjInput.text = askDjInput.text.slice(0, pos) + value + askDjInput.text.slice(pos)
            askDjInput.cursorPosition = pos + value.length
            root.askDjKeyboardOpen = true
            askDjInput.forceActiveFocus()
        }

        function insertAskDjKey(value) {
            askDjPanel.insertAskDjText(root.askDjKeyboardShift ? value.toUpperCase() : value)
            if (root.askDjKeyboardShift) {
                root.askDjKeyboardShift = false
            }
        }

        function deleteAskDjText() {
            if (djconnect.askDjBusy) {
                return
            }
            var start = askDjInput.selectionStart
            var end = askDjInput.selectionEnd
            if (start !== end) {
                askDjInput.text = askDjInput.text.slice(0, start) + askDjInput.text.slice(end)
                askDjInput.cursorPosition = start
            } else if (askDjInput.cursorPosition > 0) {
                var pos = askDjInput.cursorPosition
                askDjInput.text = askDjInput.text.slice(0, pos - 1) + askDjInput.text.slice(pos)
                askDjInput.cursorPosition = pos - 1
            }
            root.askDjKeyboardOpen = true
            askDjInput.forceActiveFocus()
        }

        AppBackground {}
        ModalBlocker {}

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            anchors.bottomMargin: 130
            spacing: 10

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 48
                spacing: 10

                Text {
                    text: root.tr("ask_dj")
                    color: "#ffffff"
                    font.pixelSize: 34
                    font.bold: true
                    Layout.fillWidth: true
                }

                BusyIndicator {
                    running: djconnect.askDjBusy
                    visible: djconnect.askDjBusy
                    implicitWidth: 30
                    implicitHeight: 30
                }

                AskDjGradientButton {
                    id: askDjRefreshButton
                    text: root.tr("refresh")
                    font.pixelSize: 18
                    Layout.preferredWidth: 132
                    Layout.preferredHeight: 48
                    onClicked: djconnect.refreshAskDjHistory()
                }

                AskDjGradientButton {
                    text: root.tr("clear")
                    font.pixelSize: 18
                    Layout.preferredWidth: 112
                    Layout.preferredHeight: 48
                    onClicked: djconnect.clearAskDjHistory()
                }
            }

            Text {
                text: root.tr("ask_dj_readonly_hint")
                color: "#b7c2d8"
                font.pixelSize: 17
                font.bold: true
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 58
                radius: 8
                color: "#3324145f"
                border.color: "#5c4d95"
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 8

                    TextField {
                        id: askDjInput
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        placeholderText: root.tr("ask_dj_input_placeholder")
                        enabled: !djconnect.askDjBusy
                        color: "#ffffff"
                        placeholderTextColor: "#91a0bd"
                        font.pixelSize: 20
                        selectByMouse: false
                        maximumLength: 500
                        background: Rectangle {
                            radius: 8
                            color: "#22070b16"
                            border.color: askDjInput.activeFocus ? "#a5b4fc" : "#39415f"
                            border.width: 1
                        }
                        onActiveFocusChanged: {
                            if (activeFocus) {
                                root.askDjKeyboardOpen = true
                            }
                        }
                        onAccepted: askDjPanel.sendAskDjInput()

                        TapHandler {
                            onTapped: {
                                root.askDjKeyboardOpen = true
                                askDjInput.forceActiveFocus()
                            }
                        }
                    }

                    AskDjGradientButton {
                        text: root.tr("send")
                        enabled: !djconnect.askDjBusy && askDjInput.text.trim().length > 0
                        font.pixelSize: 18
                        Layout.preferredWidth: 112
                        Layout.fillHeight: true
                        onClicked: askDjPanel.sendAskDjInput()
                    }
                }
            }

            ScrollView {
                id: askDjScroll
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                contentWidth: availableWidth

                ColumnLayout {
                    width: Math.max(0, askDjScroll.availableWidth)
                    spacing: 10

                    Text {
                        text: root.tr("ask_dj_empty")
                        visible: djconnect.askDjMessages.length === 0
                        color: "#b7c2d8"
                        font.pixelSize: 24
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                        Layout.topMargin: 36
                    }

                    Repeater {
                        model: djconnect.askDjMessages

                        Rectangle {
                            property bool userBubble: modelData.role === "user"
                            property bool systemBubble: modelData.role === "system" || modelData.role === "status" || modelData.messageKind === "system" || modelData.messageKind === "status"

                            Layout.preferredWidth: userBubble ? Math.min(askDjScroll.availableWidth * 0.78, 520) : askDjScroll.availableWidth
                            Layout.alignment: userBubble ? Qt.AlignRight : Qt.AlignLeft
                            implicitHeight: askDjBubbleContent.implicitHeight + 24
                            radius: 8
                            color: systemBubble ? "#33434a57" : (userBubble ? "#664f46e5" : "#4434145f")
                            border.color: systemBubble ? "#6aa0b9c8" : (userBubble ? "#a5b4fc" : "#7f67ff")
                            border.width: 1

                            ColumnLayout {
                                id: askDjBubbleContent
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.margins: 12
                                spacing: 8

                                Text {
                                    text: modelData.text
                                    color: "#ffffff"
                                    font.pixelSize: systemBubble ? 19 : 22
                                    font.bold: !systemBubble
                                    wrapMode: Text.WordWrap
                                    Layout.fillWidth: true
                                }

                                Flow {
                                    visible: modelData.images && modelData.images.length > 0
                                    spacing: 8
                                    Layout.fillWidth: true

                                    Repeater {
                                        model: modelData.images || []
                                        Rectangle {
                                            width: 112
                                            height: 112
                                            radius: 8
                                            color: "#22182e"
                                            clip: true
                                            Image {
                                                anchors.fill: parent
                                                source: modelData.url || ""
                                                fillMode: Image.PreserveAspectCrop
                                                sourceSize.width: 112
                                                sourceSize.height: 112
                                                asynchronous: true
                                                cache: false
                                            }
                                        }
                                    }
                                }

                                ColumnLayout {
                                    visible: modelData.items && modelData.items.length > 0
                                    Layout.fillWidth: true
                                    spacing: 8

                                    Repeater {
                                        model: modelData.items || []

                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 70
                                            radius: 8
                                            color: "#44291f4b"
                                            border.color: "#44ffffff"
                                            border.width: 1
                                            clip: true

                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.margins: 8
                                                spacing: 10

                                                Rectangle {
                                                    Layout.preferredWidth: 54
                                                    Layout.preferredHeight: 54
                                                    radius: 8
                                                    color: "#22182e"
                                                    clip: true

                                                    Image {
                                                        visible: modelData.imageUrl && modelData.imageUrl.length > 0
                                                        anchors.fill: parent
                                                        source: modelData.imageUrl || ""
                                                        fillMode: Image.PreserveAspectCrop
                                                        sourceSize.width: 54
                                                        sourceSize.height: 54
                                                        asynchronous: true
                                                        cache: false
                                                    }

                                                    Text {
                                                        anchors.centerIn: parent
                                                        visible: !modelData.imageUrl || modelData.imageUrl.length === 0
                                                        text: "♪"
                                                        color: "#d8c8ff"
                                                        font.pixelSize: 24
                                                        font.bold: true
                                                    }
                                                }

                                                ColumnLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 2

                                                    Text {
                                                        text: modelData.title || ""
                                                        color: "#ffffff"
                                                        font.pixelSize: 17
                                                        font.bold: true
                                                        elide: Text.ElideRight
                                                        maximumLineCount: 1
                                                        Layout.fillWidth: true
                                                    }

                                                    Text {
                                                        text: modelData.subtitle || ""
                                                        color: "#f0d7ea"
                                                        font.pixelSize: 15
                                                        font.bold: true
                                                        elide: Text.ElideRight
                                                        maximumLineCount: 1
                                                        visible: text.length > 0
                                                        Layout.fillWidth: true
                                                    }
                                                }

                                                Text {
                                                    text: modelData.time || ""
                                                    color: "#b7c2d8"
                                                    font.pixelSize: 14
                                                    font.bold: true
                                                    horizontalAlignment: Text.AlignRight
                                                    elide: Text.ElideRight
                                                    maximumLineCount: 1
                                                    Layout.preferredWidth: 112
                                                    visible: text.length > 0
                                                }
                                            }
                                        }
                                    }
                                }

                                ColumnLayout {
                                    visible: modelData.links && modelData.links.length > 0
                                    Layout.fillWidth: true
                                    spacing: 4

                                    Text {
                                        text: root.tr("sources")
                                        color: "#d8c8ff"
                                        font.pixelSize: 16
                                        font.bold: true
                                        Layout.fillWidth: true
                                    }

                                    Repeater {
                                        model: modelData.links || []
                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 28
                                            color: "#00000000"

                                            Text {
                                                anchors.fill: parent
                                                text: modelData.title || modelData.url || ""
                                                color: "#a7f3ff"
                                                font.pixelSize: 17
                                                elide: Text.ElideRight
                                                verticalAlignment: Text.AlignVCenter
                                            }

                                            MouseArea {
                                                anchors.fill: parent
                                                enabled: modelData.url && modelData.url.length > 0
                                                onClicked: Qt.openUrlExternally(modelData.url)
                                            }
                                        }
                                    }
                                }

                                ColumnLayout {
                                    visible: modelData.actions && modelData.actions.length > 0
                                    Layout.fillWidth: true
                                    spacing: 8

                                    Repeater {
                                        model: modelData.actions || []

                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: (modelData.isMedia || modelData.isOutput) ? 88 : 50
                                            radius: 8
                                            color: (modelData.isMedia || modelData.isOutput) ? "#55291f4b" : "#00000000"
                                            border.color: (modelData.isMedia || modelData.isOutput) ? "#55ffffff" : "#00000000"
                                            border.width: (modelData.isMedia || modelData.isOutput) ? 1 : 0
                                            clip: true

                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.margins: (modelData.isMedia || modelData.isOutput) ? 10 : 0
                                                spacing: 12

                                                Rectangle {
                                                    visible: modelData.isMedia || modelData.isOutput
                                                    Layout.preferredWidth: 68
                                                    Layout.preferredHeight: 68
                                                    radius: 8
                                                    color: "#22182e"
                                                    clip: true

                                                    Image {
                                                        visible: modelData.isMedia
                                                        anchors.fill: parent
                                                        source: modelData.imageUrl && modelData.imageUrl.length > 0 ? modelData.imageUrl : ""
                                                        fillMode: Image.PreserveAspectCrop
                                                        sourceSize.width: 68
                                                        sourceSize.height: 68
                                                        asynchronous: true
                                                        cache: false
                                                    }

                                                    Text {
                                                        anchors.centerIn: parent
                                                        visible: modelData.isOutput || !modelData.imageUrl || modelData.imageUrl.length === 0
                                                        text: modelData.isOutput ? "OUT" : "♪"
                                                        color: "#d8c8ff"
                                                        font.pixelSize: modelData.isOutput ? 18 : 28
                                                        font.bold: true
                                                    }
                                                }

                                                ColumnLayout {
                                                    visible: modelData.isMedia || modelData.isOutput
                                                    Layout.fillWidth: true
                                                    spacing: 3

                                                    Text {
                                                        text: modelData.title || root.tr("start")
                                                        color: "#ffffff"
                                                        font.pixelSize: 18
                                                        font.bold: true
                                                        elide: Text.ElideRight
                                                        maximumLineCount: 1
                                                        Layout.fillWidth: true
                                                    }

                                                    Text {
                                                        text: modelData.subtitle || ""
                                                        color: "#f0d7ea"
                                                        font.pixelSize: 16
                                                        font.bold: true
                                                        elide: Text.ElideRight
                                                        maximumLineCount: 1
                                                        visible: text.length > 0
                                                        Layout.fillWidth: true
                                                    }

                                                    Rectangle {
                                                        Layout.preferredHeight: 24
                                                        Layout.preferredWidth: Math.max(78, actionKindLabel.implicitWidth + 24)
                                                        radius: 12
                                                        color: "#33ffffff"

                                                        Text {
                                                            id: actionKindLabel
                                                            anchors.centerIn: parent
                                                            text: modelData.kind || "media"
                                                            color: "#ffffff"
                                                            font.pixelSize: 14
                                                            font.bold: true
                                                            elide: Text.ElideRight
                                                        }
                                                    }
                                                }

                                                AskDjGradientButton {
                                                    id: askDjActionButton
                                                    text: modelData.isOutput ? root.tr("activate") : (modelData.isMedia ? "Play Now" : (modelData.title || root.tr("start")))
                                                    font.pixelSize: (modelData.isMedia || modelData.isOutput) ? 16 : 18
                                                    Layout.fillWidth: !(modelData.isMedia || modelData.isOutput)
                                                    Layout.preferredWidth: (modelData.isMedia || modelData.isOutput) ? 118 : 0
                                                    Layout.preferredHeight: (modelData.isMedia || modelData.isOutput) ? 44 : 50
                                                    contentItem: RowLayout {
                                                        spacing: 8

                                                        Canvas {
                                                            visible: modelData.isMedia
                                                            Layout.preferredWidth: 18
                                                            Layout.preferredHeight: 18
                                                            antialiasing: true
                                                            onPaint: {
                                                                var ctx = getContext("2d")
                                                                ctx.clearRect(0, 0, width, height)
                                                                ctx.fillStyle = "#ffffff"
                                                                ctx.beginPath()
                                                                ctx.moveTo(width * 0.33, height * 0.22)
                                                                ctx.lineTo(width * 0.33, height * 0.78)
                                                                ctx.lineTo(width * 0.78, height * 0.5)
                                                                ctx.closePath()
                                                                ctx.fill()
                                                            }
                                                        }

                                                        Text {
                                                            id: actionLabel
                                                            text: askDjActionButton.text
                                                            font: askDjActionButton.font
                                                            color: "#ffffff"
                                                            horizontalAlignment: Text.AlignHCenter
                                                            verticalAlignment: Text.AlignVCenter
                                                            elide: Text.ElideRight
                                                            maximumLineCount: 1
                                                            Layout.fillWidth: true
                                                        }
                                                    }
                                                    onClicked: djconnect.sendAskDjAction(modelData.payload || "{}")
                                                }
                                            }
                                        }
                                    }
                                }

                            }
                        }
                    }
                }
            }
        }

        Rectangle {
            id: askDjKeyboard
            visible: root.askDjKeyboardOpen
            x: Math.max(16, askDjInput.mapToItem(askDjPanel, 0, 0).x)
            y: askDjInput.mapToItem(askDjPanel, 0, askDjInput.height).y + 8
            width: Math.min(askDjPanel.width - x - 16, Math.max(420, askDjInput.width))
            height: 216
            radius: 8
            color: "#f20b1024"
            border.color: "#6573aa"
            border.width: 1
            clip: true
            z: 40

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 7

                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 6

                    Repeater {
                        model: ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"]

                        AskDjKeyButton {
                            keyText: modelData
                            displayText: root.askDjKeyboardShift ? keyText.toUpperCase() : keyText
                            onClicked: askDjPanel.insertAskDjKey(keyText)
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.leftMargin: 18
                    Layout.rightMargin: 18
                    spacing: 6

                    Repeater {
                        model: ["a", "s", "d", "f", "g", "h", "j", "k", "l"]

                        AskDjKeyButton {
                            keyText: modelData
                            displayText: root.askDjKeyboardShift ? keyText.toUpperCase() : keyText
                            onClicked: askDjPanel.insertAskDjKey(keyText)
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 6

                    AskDjKeyButton {
                        displayText: "⇧"
                        active: root.askDjKeyboardShift
                        Layout.preferredWidth: 72
                        Layout.fillWidth: false
                        onClicked: {
                            root.askDjKeyboardShift = !root.askDjKeyboardShift
                            root.askDjKeyboardOpen = true
                            askDjInput.forceActiveFocus()
                        }
                    }

                    Repeater {
                        model: ["z", "x", "c", "v", "b", "n", "m"]

                        AskDjKeyButton {
                            keyText: modelData
                            displayText: root.askDjKeyboardShift ? keyText.toUpperCase() : keyText
                            onClicked: askDjPanel.insertAskDjKey(keyText)
                        }
                    }

                    AskDjKeyButton {
                        displayText: "⌫"
                        Layout.preferredWidth: 72
                        Layout.fillWidth: false
                        onClicked: askDjPanel.deleteAskDjText()
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 6

                    AskDjKeyButton {
                        displayText: "?"
                        Layout.preferredWidth: 70
                        Layout.fillWidth: false
                        onClicked: askDjPanel.insertAskDjText("?")
                    }

                    AskDjKeyButton {
                        displayText: root.tr("keyboard_space")
                        Layout.fillWidth: true
                        onClicked: askDjPanel.insertAskDjText(" ")
                    }

                    AskDjKeyButton {
                        displayText: "."
                        Layout.preferredWidth: 58
                        Layout.fillWidth: false
                        onClicked: askDjPanel.insertAskDjText(".")
                    }

                    AskDjKeyButton {
                        displayText: ","
                        Layout.preferredWidth: 58
                        Layout.fillWidth: false
                        onClicked: askDjPanel.insertAskDjText(",")
                    }

                    AskDjGradientButton {
                        text: root.tr("send")
                        enabled: !djconnect.askDjBusy && askDjInput.text.trim().length > 0
                        font.pixelSize: 17
                        Layout.preferredWidth: 116
                        Layout.fillHeight: true
                        onClicked: askDjPanel.sendAskDjInput()
                    }
                }
            }
        }
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
        height: 104
        color: "#dd0b1024"
        border.color: "#33406b"
        border.width: 1
        visible: !root.splashVisible && (djconnect.paired || djconnect.demoMode) && !djconnect.logsVisible && !djconnect.versionMismatchVisible
        z: 25

        RowLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 8

            NavButton {
                text: root.tr("now_playing")
                iconName: "music"
                checkable: true
                checked: root.activeScreen === "now"
                Layout.fillWidth: true
                Layout.fillHeight: true
                onClicked: root.activeScreen = "now"
            }

            NavButton {
                text: root.tr("control")
                iconName: "control"
                checkable: true
                checked: root.activeScreen === "control"
                Layout.fillWidth: true
                Layout.fillHeight: true
                onClicked: root.activeScreen = "control"
            }

            NavButton {
                text: root.tr("ask_dj")
                iconName: "chat"
                checkable: true
                checked: root.activeScreen === "askdj"
                Layout.fillWidth: true
                Layout.fillHeight: true
                onClicked: {
                    root.activeScreen = "askdj"
                    djconnect.loadAskDjHistory()
                }
            }

            NavButton {
                text: root.tr("queue")
                iconName: "queue"
                checkable: true
                checked: root.activeScreen === "queue"
                Layout.fillWidth: true
                Layout.fillHeight: true
                onClicked: {
                    root.activeScreen = "queue"
                    djconnect.loadQueue()
                }
            }

            NavButton {
                text: root.tr("more")
                iconName: "more"
                checkable: true
                checked: root.activeScreen === "more" || root.activeScreen === "playlists" || root.activeScreen === "games" || root.activeScreen === "settings"
                Layout.fillWidth: true
                Layout.fillHeight: true
                onClicked: root.activeScreen = "more"
            }
        }
    }

    Rectangle {
        id: pairingPanel
        anchors.fill: parent
        color: "#070b16"
        visible: !root.splashVisible && !djconnect.paired && !djconnect.demoMode
        z: 30

        ModalBlocker {}

        ColumnLayout {
            anchors.centerIn: parent
            width: Math.min(parent.width - 40, 640)
            spacing: 14

            AppBanner {}

            Text {
                text: root.tr("pairing_screen_title")
                color: "#d7e2e4"
                font.pixelSize: 38
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
            }

            Text {
                text: root.tr("pairing_hint")
                color: "#b7a8c8"
                font.pixelSize: 20
                font.bold: true
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 76
                radius: 8
                color: "#5524145f"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 3

                    Text {
                        text: root.tr("home_assistant")
                        color: "#b7a8c8"
                        font.pixelSize: 17
                        font.bold: true
                        Layout.fillWidth: true
                    }

                    Text {
                        text: djconnect.haUrl.length ? djconnect.haUrl : "http://homeassistant.local:8123"
                        color: "#ffffff"
                        font.pixelSize: 22
                        font.bold: true
                        font.family: "monospace"
                        elide: Text.ElideMiddle
                        Layout.fillWidth: true
                    }
                }
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
                        text: root.tr("pairing_code")
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
                Layout.preferredHeight: 76
                radius: 8
                color: "#5524145f"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 3

                    Text {
                        text: root.tr("client_api_url")
                        color: "#b7a8c8"
                        font.pixelSize: 17
                        font.bold: true
                        Layout.fillWidth: true
                    }

                    Text {
                        text: djconnect.localApiUrl
                        color: "#ffffff"
                        font.pixelSize: 22
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

                    LoadingSpinner {
                        running: pairingPanel.visible
                        implicitWidth: 38
                        implicitHeight: 38
                    }

                    Text {
                        text: root.tr("waiting_for_ha")
                        color: "#ffffff"
                        font.pixelSize: 22
                        font.bold: true
                        Layout.fillWidth: true
                    }
                }
            }

            PurpleButton {
                id: startDemoButton
                text: root.tr("start_demo_mode")
                font.pixelSize: 22
                Layout.fillWidth: true
                Layout.preferredHeight: 54
                contentItem: RowLayout {
                    spacing: 10

                    Item {
                        Layout.preferredWidth: 28
                        Layout.preferredHeight: 28

                        Canvas {
                            anchors.fill: parent
                            antialiasing: true
                            onPaint: {
                                var ctx = getContext("2d")
                                var s = Math.min(width, height)
                                ctx.clearRect(0, 0, width, height)
                                ctx.strokeStyle = "#ffffff"
                                ctx.fillStyle = "#ffffff"
                                ctx.lineWidth = 3
                                ctx.beginPath()
                                ctx.arc(width / 2, height / 2, s * 0.38, 0, Math.PI * 2)
                                ctx.stroke()
                                ctx.beginPath()
                                ctx.moveTo(width * 0.43, height * 0.33)
                                ctx.lineTo(width * 0.43, height * 0.67)
                                ctx.lineTo(width * 0.68, height * 0.5)
                                ctx.closePath()
                                ctx.fill()
                            }
                        }
                    }

                    Text {
                        text: startDemoButton.text
                        font: startDemoButton.font
                        color: startDemoButton.enabled ? "#ffffff" : "#93a0b8"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                        Layout.fillWidth: false
                    }
                }
                onClicked: djconnect.enterDemoMode()
            }

        }
    }

    Rectangle {
        id: pairingSuccessPanel
        anchors.fill: parent
        color: "#070b16"
        visible: !root.splashVisible && djconnect.pairingSuccessVisible
        z: 34

        ModalBlocker {}

        ColumnLayout {
            anchors.centerIn: parent
            width: Math.min(parent.width - 40, 640)
            spacing: 28

            AppBanner {}

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
                    text: root.tr("pairing_success_title")
                    color: "#f4f0ff"
                    font.pixelSize: 38
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                }

                Text {
                    text: root.tr("pairing_success_message")
                    color: "#c9c3d8"
                    font.pixelSize: 20
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                }
            }

            PurpleButton {
                text: root.tr("start")
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

        ModalBlocker {}

        Rectangle {
            anchors.centerIn: parent
            width: Math.min(parent.width - 64, 560)
            height: 300
            color: "#00000000"

            ColumnLayout {
                anchors.fill: parent
                spacing: 18

                AppBanner {
                    detailText: "v" + djconnect.version
                    titleSize: 42
                    detailSize: 20
                    logoSize: 92
                }

                Text {
                    text: root.tr("startup_message")
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
        anchors.topMargin: 32
        width: Math.min(parent.width - 58, Math.max(300, toastText.implicitWidth + 112))
        height: Math.max(64, toastText.implicitHeight + 26)
        radius: height / 2
        border.color: "#b8ffffff"
        border.width: 2
        opacity: djconnect.toastVisible ? 1 : 0
        visible: opacity > 0
        z: 70
        y: djconnect.toastVisible ? 0 : -16
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "#ff5a2e" }
            GradientStop { position: 0.52; color: "#f13ccc" }
            GradientStop { position: 1.0; color: "#b731ff" }
        }

        Behavior on opacity { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
        Behavior on y { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }

        Row {
            anchors.centerIn: parent
            spacing: 16

            Canvas {
                width: 28
                height: 28
                anchors.verticalCenter: parent.verticalCenter
                onPaint: {
                    var ctx = getContext("2d")
                    ctx.reset()
                    ctx.fillStyle = "#ffffff"
                    ctx.beginPath()
                    ctx.moveTo(6, 4)
                    ctx.lineTo(6, 24)
                    ctx.lineTo(24, 14)
                    ctx.closePath()
                    ctx.fill()
                }
            }

            Text {
                id: toastText
                width: Math.min(root.width - 188, implicitWidth)
                anchors.verticalCenter: parent.verticalCenter
                text: djconnect.toastText
                color: "#ffffff"
                font.pixelSize: 24
                font.bold: true
                wrapMode: Text.NoWrap
                horizontalAlignment: Text.AlignLeft
                elide: Text.ElideRight
                maximumLineCount: 1
            }
        }
    }

    Rectangle {
        id: versionMismatchPanel
        anchors.fill: parent
        color: "#f2070b16"
        visible: !root.splashVisible && djconnect.versionMismatchVisible
        z: 60

        ModalBlocker {}

        ColumnLayout {
            anchors.centerIn: parent
            width: Math.min(parent.width - 72, 560)
            spacing: 18

            Text {
                text: root.tr("version_mismatch_title")
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
                    text: root.tr("update_trying")
                    color: "#9fb4b8"
                    font.pixelSize: 17
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                PurpleButton {
                    text: root.tr("view_logs")
                    font.pixelSize: 18
                    Layout.fillWidth: true
                    onClicked: djconnect.showLogs()
                }
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "#070b16"
        visible: djconnect.logsVisible
        z: 80

        AppBackground {}
        ModalBlocker {}

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 28
            spacing: 12

            Text {
                text: root.tr("logs")
                color: "#f4f8f8"
                font.pixelSize: 34
                font.bold: true
                Layout.fillWidth: true
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.minimumHeight: 56
                Layout.preferredHeight: 56
                Layout.maximumHeight: 56
                Layout.fillHeight: false
                spacing: 10

                PurpleButton {
                    text: root.tr("clear_logs")
                    font.pixelSize: 22
                    Layout.fillWidth: true
                    Layout.preferredHeight: 56
                    Layout.maximumHeight: 56
                    onClicked: root.clearLogsConfirmOpen = true
                }
                PurpleButton {
                    text: root.tr("refresh")
                    font.pixelSize: 22
                    Layout.fillWidth: true
                    Layout.preferredHeight: 56
                    Layout.maximumHeight: 56
                    onClicked: {
                        djconnect.showLogs()
                        Qt.callLater(function() { logsArea.cursorPosition = logsArea.length })
                    }
                }
                PurpleButton {
                    text: root.tr("close")
                    font.pixelSize: 22
                    Layout.fillWidth: true
                    Layout.preferredHeight: 56
                    Layout.maximumHeight: 56
                    onClicked: djconnect.hideLogs()
                }
            }

            ScrollView {
                id: logsScroll
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 360

                TextArea {
                    id: logsArea
                    height: logsScroll.availableHeight
                    text: djconnect.logsText
                    readOnly: true
                    wrapMode: TextEdit.Wrap
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

            Text {
                text: root.tr("log") + ": " + djconnect.logFile
                color: "#91a3a7"
                font.pixelSize: 17
                elide: Text.ElideMiddle
                Layout.fillWidth: true
            }
        }
    }

    Rectangle {
        id: clearLogsConfirmPanel
        anchors.fill: parent
        color: "#cc070b16"
        visible: root.clearLogsConfirmOpen
        z: 86

        ModalBlocker {}

        Rectangle {
            anchors.centerIn: parent
            width: Math.min(parent.width - 48, 520)
            radius: 8
            color: "#f0151020"
            border.color: "#47345d"
            border.width: 1

            implicitHeight: clearLogsConfirmContent.implicitHeight + 44

            ColumnLayout {
                id: clearLogsConfirmContent
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 22
                spacing: 18

                Text {
                    text: root.tr("clear_logs_confirm_title")
                    color: "#ffffff"
                    font.pixelSize: 28
                    font.bold: true
                    Layout.fillWidth: true
                }

                Text {
                    text: root.tr("clear_logs_confirm_message")
                    color: "#f4f0ff"
                    font.pixelSize: 24
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                DangerButton {
                    text: root.tr("clear_logs")
                    Layout.fillWidth: true
                    Layout.preferredHeight: 56
                    onClicked: {
                        root.clearLogsConfirmOpen = false
                        djconnect.clearLogs()
                    }
                }

                PurpleButton {
                    text: root.tr("cancel")
                    font.pixelSize: 24
                    Layout.fillWidth: true
                    Layout.preferredHeight: 56
                    onClicked: root.clearLogsConfirmOpen = false
                }
            }
        }
    }

    Rectangle {
        id: resetPairingConfirmPanel
        anchors.fill: parent
        color: "#cc070b16"
        visible: root.resetPairingConfirmOpen
        z: 84

        ModalBlocker {}

        Rectangle {
            anchors.centerIn: parent
            width: Math.min(parent.width - 48, 520)
            radius: 8
            color: "#f0151020"
            border.color: "#47345d"
            border.width: 1

            implicitHeight: confirmContent.implicitHeight + 44

            ColumnLayout {
                id: confirmContent
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 22
                spacing: 18

                Text {
                    text: root.tr("reset_pairing_confirm_title")
                    color: "#ffffff"
                    font.pixelSize: 28
                    font.bold: true
                    Layout.fillWidth: true
                }

                Text {
                    text: root.tr("reset_pairing_confirm_message")
                    color: "#f4f0ff"
                    font.pixelSize: 24
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                DangerButton {
                    text: root.tr("reset_pairing")
                    Layout.fillWidth: true
                    Layout.preferredHeight: 56
                    onClicked: {
                        root.resetPairingConfirmOpen = false
                        djconnect.resetPairing()
                        root.activeScreen = "now"
                    }
                }

                PurpleButton {
                    text: root.tr("cancel")
                    font.pixelSize: 24
                    Layout.fillWidth: true
                    Layout.preferredHeight: 56
                    onClicked: root.resetPairingConfirmOpen = false
                }
            }
        }
    }

    Rectangle {
        id: rebootConfirmPanel
        anchors.fill: parent
        color: "#cc070b16"
        visible: root.rebootConfirmOpen
        z: 84

        ModalBlocker {}

        Rectangle {
            anchors.centerIn: parent
            width: Math.min(parent.width - 48, 520)
            radius: 8
            color: "#f0151020"
            border.color: "#47345d"
            border.width: 1

            implicitHeight: rebootConfirmContent.implicitHeight + 44

            ColumnLayout {
                id: rebootConfirmContent
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 22
                spacing: 18

                Text {
                    text: root.tr("reboot_confirm_title")
                    color: "#ffffff"
                    font.pixelSize: 28
                    font.bold: true
                    Layout.fillWidth: true
                }

                Text {
                    text: root.tr("reboot_confirm_message")
                    color: "#f4f0ff"
                    font.pixelSize: 24
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                WarningButton {
                    text: root.tr("reboot_device")
                    Layout.fillWidth: true
                    Layout.preferredHeight: 56
                    onClicked: {
                        root.rebootConfirmOpen = false
                        djconnect.rebootDevice()
                    }
                }

                PurpleButton {
                    text: root.tr("cancel")
                    font.pixelSize: 24
                    Layout.fillWidth: true
                    Layout.preferredHeight: 56
                    onClicked: root.rebootConfirmOpen = false
                }
            }
        }
    }

    Rectangle {
        id: shutdownConfirmPanel
        anchors.fill: parent
        color: "#cc070b16"
        visible: root.shutdownConfirmOpen
        z: 84

        ModalBlocker {}

        Rectangle {
            anchors.centerIn: parent
            width: Math.min(parent.width - 48, 520)
            radius: 8
            color: "#f0151020"
            border.color: "#47345d"
            border.width: 1

            implicitHeight: shutdownConfirmContent.implicitHeight + 44

            ColumnLayout {
                id: shutdownConfirmContent
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 22
                spacing: 18

                Text {
                    text: root.tr("shutdown_confirm_title")
                    color: "#ffffff"
                    font.pixelSize: 28
                    font.bold: true
                    Layout.fillWidth: true
                }

                Text {
                    text: root.tr("shutdown_confirm_message")
                    color: "#f4f0ff"
                    font.pixelSize: 24
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                DangerButton {
                    text: root.tr("shutdown_device")
                    Layout.fillWidth: true
                    Layout.preferredHeight: 56
                    onClicked: {
                        root.shutdownConfirmOpen = false
                        djconnect.shutdownDevice()
                    }
                }

                PurpleButton {
                    text: root.tr("cancel")
                    font.pixelSize: 24
                    Layout.fillWidth: true
                    Layout.preferredHeight: 56
                    onClicked: root.shutdownConfirmOpen = false
                }
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "#070b16"
        visible: root.aboutOpen
        z: 82

        AppBackground {}
        ModalBlocker {}

        ScrollView {
            id: aboutScroll
            anchors.fill: parent
            anchors.margins: 22
            clip: true
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            contentWidth: availableWidth

            ColumnLayout {
                width: Math.max(0, aboutScroll.availableWidth)
                spacing: 18

                AppBanner {
                    logoSize: 82
                }

                Text {
                    text: root.tr("app_section")
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

                    Text { text: root.tr("version"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.version; color: "#ffffff"; font.pixelSize: 20; Layout.fillWidth: true }
                    Text { text: root.tr("device_name"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: "DJConnect"; color: "#ffffff"; font.pixelSize: 20; Layout.fillWidth: true }
                    Text { text: root.tr("website"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: "https://djconnect.dev"; color: "#ffffff"; font.pixelSize: 20; Layout.fillWidth: true; elide: Text.ElideRight }
                    Text { text: root.tr("web_address"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.webPortalUrl; color: "#ffffff"; font.pixelSize: 18; Layout.fillWidth: true; elide: Text.ElideMiddle }
                    Text { text: root.tr("device_id"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.deviceId; color: "#ffffff"; font.pixelSize: 18; Layout.fillWidth: true; elide: Text.ElideMiddle }
                }

                Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: "#443262" }

                Text {
                    text: root.tr("connection_section")
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

                    Text { text: root.tr("home_assistant"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.paired ? root.tr("paired") : root.tr("not_paired"); color: "#ffffff"; font.pixelSize: 20; Layout.fillWidth: true }
                    Text { text: root.tr("music"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.paired ? root.tr("connected_value") : root.tr("not_connected_value"); color: djconnect.paired ? "#32d35a" : "#ff3b30"; font.pixelSize: 20; font.bold: true; Layout.fillWidth: true }
                    Text { text: root.tr("client_api_url_label"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.localApiUrl; color: "#ffffff"; font.pixelSize: 18; Layout.fillWidth: true; elide: Text.ElideMiddle }
                    Text { text: root.tr("home_assistant"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.haUrl; color: "#ffffff"; font.pixelSize: 18; Layout.fillWidth: true; elide: Text.ElideMiddle }
                }

                Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: "#443262" }

                Text {
                    text: root.tr("notices_section")
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

                    Text { text: root.tr("copyright"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: "2026 Peter van Tol"; color: "#ffffff"; font.pixelSize: 20; Layout.fillWidth: true }
                    Text { text: root.tr("spotify_notice"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: root.tr("spotify_trademark"); color: "#ffffff"; font.pixelSize: 20; Layout.fillWidth: true }
                }

                PurpleButton {
                    text: root.tr("close")
                    font.pixelSize: 26
                    Layout.fillWidth: true
                    Layout.preferredHeight: 64
                    onClicked: root.aboutOpen = false
                }
            }
        }
    }

    Rectangle {
        id: djResponseOverlay
        anchors.centerIn: parent
        width: Math.min(parent.width - 52, 620)
        height: Math.min(parent.height - 120, Math.max(260, djResponseText.implicitHeight + 112))
        radius: 8
        color: "#cc160f2a"
        border.color: "#80d9ccff"
        border.width: 1
        visible: opacity > 0
        opacity: djconnect.djResponseVisible && !root.splashVisible ? 1 : 0
        z: 190

        Behavior on opacity { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }

        ModalBlocker {}

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 24
            spacing: 16

            AppBanner {
                Layout.fillWidth: true
                Layout.preferredHeight: 98
                detailText: root.tr("dj_response")
                logoSize: 64
                titleSize: 30
                detailSize: 20
                horizontalPadding: 20
                verticalPadding: 14
                contentSpacing: 16
            }

            Text {
                id: djResponseText
                text: djconnect.djResponseText
                color: "#ffffff"
                font.pixelSize: 34
                font.bold: true
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                style: Text.Raised
                styleColor: "#aa000000"
                Layout.fillWidth: true
                Layout.fillHeight: true
            }
        }

        TapHandler {
            onTapped: djconnect.clearDjResponse()
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
            onTapped: root.wakeDisplay()
        }
    }
}
