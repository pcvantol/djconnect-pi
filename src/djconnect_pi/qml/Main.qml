import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "MoodTheme.js" as MoodTheme

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
    property bool musicDnaDisableConfirmOpen: false
    property bool musicDnaClearConfirmOpen: false
    property bool moodPopoverOpen: false
    property bool discoveryReasonOpen: false
    property string discoveryReasonTitle: ""
    property string discoveryReasonText: ""
    property bool forceScreenAwake: false
    property bool forceBrightnessFull: false
    property bool suppressNextNowPanelTap: false
    property int standardButtonRadius: 8
    property var returnToNowChoices: [30, 60, 120, 0]
    property bool screenBlanked: djconnect.screenTimeoutSeconds > 0 && !idleTimer.running && !root.forceScreenAwake
    property real brightnessOverlayOpacity: root.screenBlanked || root.forceBrightnessFull ? 0 : 1 - (djconnect.screenBrightnessPercent / 100.0)
    property int trVersion: djconnect.translationVersion

    function tr(key) {
        root.trVersion
        return djconnect.t(key)
    }

    function languageIndex() {
        for (var i = 0; i < languageBox.model.length; i++) {
            if (languageBox.model[i].code === djconnect.language) return i
        }
        return 0
    }

    function repeatLabel(value) {
        if (value === "track") return root.tr("repeat_one")
        if (value === "context") return root.tr("repeat")
        return root.tr("repeat_off")
    }

    function returnToNowLabel(value) {
        return value > 0 ? value : root.tr("return_to_now_off")
    }

    function returnToNowIndex() {
        for (var i = 0; i < root.returnToNowChoices.length; i++) {
            if (root.returnToNowChoices[i] === djconnect.returnToNowSeconds) return i
        }
        return 1
    }

    function trackInsightLabel(value) {
        var key = String(value || "").trim().toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "")
        var labels = {
            "summary": "track_insight_summary",
            "genre": "track_insight_genre",
            "vibe": "track_insight_vibe",
            "production": "track_insight_production",
            "production_notes": "track_insight_production",
            "instrumentation": "track_insight_instrumentation",
            "arrangement": "track_insight_arrangement",
            "arrangement_notes": "track_insight_arrangement",
            "listening_cues": "track_insight_listening_cues",
            "similar_tracks": "track_insight_similar_tracks",
            "why_it_fits_you": "track_insight_why_it_fits_you",
            "mood_context": "track_insight_mood_context",
            "this_expands_your_music_dna": "track_insight_music_dna_expands",
            "music_dna_match": "music_dna_match",
            "energy": "track_insight_energy",
            "danceability": "track_insight_danceability",
            "intensity": "track_insight_intensity",
            "confidence": "track_insight_confidence",
            "measured": "track_insight_measured",
            "inferred": "track_insight_inferred",
            "context": "analysis_context"
        }
        return labels[key] ? root.tr(labels[key]) : (value || "")
    }

    function lineNumbers(text) {
        if (!text || text.length === 0) return "1"
        var count = text.split("\n").length
        var lines = []
        for (var i = 1; i <= count; i++) lines.push(i.toString())
        return lines.join("\n")
    }

    function moodColor(token) {
        return MoodTheme.color(djconnect.moodValue, token)
    }

    function moodDisabledColor(position) {
        return MoodTheme.disabled(position)
    }

    function recordActivity() {
        var wasBlanked = root.screenBlanked
        root.forceBrightnessFull = false
        root.restartIdleTimer()
        root.restartReturnToNowTimer()
        if (root.forceScreenAwake && forcedWakeTimer.running) {
            forcedWakeTimer.restart()
        }
        if (wasBlanked) {
            root.hideTransientUi()
            if (djconnect.returnToNowSeconds > 0) {
                root.activeScreen = "now"
            }
            root.suppressNextNowPanelTap = true
            djconnect.refresh()
        }
    }

    function openTrackInsightScreen() {
        root.activeScreen = "trackinsight"
    }

    function restartIdleTimer() {
        if (djconnect.screenTimeoutSeconds > 0) {
            idleTimer.restart()
        }
    }

    function restartReturnToNowTimer() {
        if (djconnect.returnToNowSeconds > 0) {
            returnToNowTimer.restart()
        }
    }

    function wakeDisplay() {
        djconnect.wakeDisplay()
        root.recordActivity()
    }

    onActiveScreenChanged: {
        root.restartIdleTimer()
        root.restartReturnToNowTimer()
        if (root.activeScreen === "askdj") {
            root.scrollAskDjToTop()
        } else if (root.activeScreen === "musicdna") {
            djconnect.loadMusicDna()
        } else if (root.activeScreen === "discover") {
            djconnect.loadMusicDiscovery()
        }
        if (root.activeScreen !== "now") {
            root.moodPopoverOpen = false
        }
    }

    function scrollAskDjToTop() {
        Qt.callLater(function() {
            if (!askDjScroll || !askDjScroll.contentItem) {
                return
            }
            askDjScroll.contentItem.contentY = 0
        })
    }

    function hideTransientUi() {
        root.aboutOpen = false
        root.resetPairingConfirmOpen = false
        root.rebootConfirmOpen = false
        root.shutdownConfirmOpen = false
        root.clearLogsConfirmOpen = false
        root.musicDnaDisableConfirmOpen = false
        root.musicDnaClearConfirmOpen = false
        root.moodPopoverOpen = false
        root.discoveryReasonOpen = false
        djconnect.hideLogs()
    }

    function temporaryWake(seconds, navigateNow) {
        var wasBlanked = root.screenBlanked
        if (navigateNow && wasBlanked && djconnect.returnToNowSeconds > 0) {
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
                GradientStop { position: 0.0; color: control.enabled ? root.moodColor("gradientStart") : root.moodDisabledColor("start") }
                GradientStop { position: 0.58; color: control.enabled ? root.moodColor("gradientMid") : root.moodDisabledColor("mid") }
                GradientStop { position: 1.0; color: control.enabled ? root.moodColor("gradientEnd") : root.moodDisabledColor("end") }
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
                GradientStop { position: 0.0; color: askDjButton.enabled ? root.moodColor("gradientStart") : root.moodDisabledColor("start") }
                GradientStop { position: 0.58; color: askDjButton.enabled ? root.moodColor("gradientMid") : root.moodDisabledColor("mid") }
                GradientStop { position: 1.0; color: askDjButton.enabled ? root.moodColor("gradientEnd") : root.moodDisabledColor("end") }
            }
            opacity: askDjButton.down ? 0.78 : (askDjButton.enabled ? 1.0 : 0.62)
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
            function star(cx, cy, r) {
                ctx.beginPath()
                for (var i = 0; i < 8; i++) {
                    var a = -Math.PI / 2 + i * Math.PI / 4
                    var radius = i % 2 === 0 ? r : r * 0.42
                    var sx = px(cx) + Math.cos(a) * radius * s / 32
                    var sy = py(cy) + Math.sin(a) * radius * s / 32
                    if (i === 0) ctx.moveTo(sx, sy)
                    else ctx.lineTo(sx, sy)
                }
                ctx.closePath()
                ctx.fill()
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
            } else if (iconName === "musicdna") {
                ctx.beginPath()
                ctx.moveTo(px(8), py(8))
                ctx.bezierCurveTo(px(24), py(8), px(8), py(24), px(24), py(24))
                ctx.moveTo(px(24), py(8))
                ctx.bezierCurveTo(px(8), py(8), px(24), py(24), px(8), py(24))
                ctx.stroke()
                line(10, 13, 22, 13)
                line(10, 19, 22, 19)
            } else if (iconName === "trackInsight") {
                ctx.beginPath()
                ctx.moveTo(px(5), py(17))
                ctx.lineTo(px(8), py(17))
                ctx.bezierCurveTo(px(9), py(12), px(10.5), py(12), px(11.5), py(17))
                ctx.lineTo(px(13.2), py(22))
                ctx.lineTo(px(15.3), py(8))
                ctx.lineTo(px(18.1), py(24))
                ctx.lineTo(px(20.2), py(14))
                ctx.bezierCurveTo(px(21.4), py(17), px(22.4), py(17), px(24), py(17))
                ctx.lineTo(px(27), py(17))
                ctx.stroke()
                line(5, 25, 27, 25)
            } else if (iconName === "discover") {
                line(9, 23, 22, 10)
                line(19.5, 7.5, 24.5, 12.5)
                line(17.8, 9.2, 22.8, 14.2)
                star(9, 9, 3.2)
                star(24, 22, 2.5)
                star(14, 14, 1.8)
            } else if (iconName === "heart") {
                ctx.beginPath()
                ctx.moveTo(px(16), py(25))
                ctx.bezierCurveTo(px(7), py(19), px(5), py(13), px(8.5), py(9.5))
                ctx.bezierCurveTo(px(11.5), py(6.5), px(15), py(8.5), px(16), py(11))
                ctx.bezierCurveTo(px(17), py(8.5), px(20.5), py(6.5), px(23.5), py(9.5))
                ctx.bezierCurveTo(px(27), py(13), px(25), py(19), px(16), py(25))
                ctx.closePath()
                ctx.stroke()
            } else if (iconName === "mood") {
                circle(16, 16, 10, false)
                circle(12, 13, 1.4, true)
                circle(20, 13, 1.4, true)
                ctx.beginPath()
                ctx.arc(px(16), py(17), 5, Math.PI * 0.15, Math.PI * 0.85)
                ctx.stroke()
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
            } else if (iconName === "refresh") {
                ctx.beginPath()
                ctx.arc(px(16), py(16), 8, Math.PI * 0.25, Math.PI * 1.55)
                ctx.stroke()
                ctx.beginPath()
                ctx.moveTo(px(8.5), py(13))
                ctx.lineTo(px(8), py(21))
                ctx.lineTo(px(14.5), py(17))
                ctx.stroke()
                ctx.beginPath()
                ctx.arc(px(16), py(16), 8, Math.PI * 1.25, Math.PI * 2.55)
                ctx.stroke()
                ctx.beginPath()
                ctx.moveTo(px(23.5), py(19))
                ctx.lineTo(px(24), py(11))
                ctx.lineTo(px(17.5), py(15))
                ctx.stroke()
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
            border.color: root.moodColor("focus")
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: navControl.enabled ? root.moodColor("gradientStart") : root.moodDisabledColor("start") }
                GradientStop { position: 0.58; color: navControl.enabled ? root.moodColor("gradientMid") : root.moodDisabledColor("mid") }
                GradientStop { position: 1.0; color: navControl.enabled ? root.moodColor("gradientEnd") : root.moodDisabledColor("end") }
            }
            opacity: navControl.down ? 0.78 : (navControl.checked ? 1.0 : 0.72)
        }
    }

    component RefreshIconButton: PurpleButton {
        id: refreshControl

        text: root.tr("refresh")
        ToolTip.visible: hovered
        ToolTip.text: text
        Accessible.name: text
        Accessible.description: text
        Layout.preferredWidth: 48
        Layout.preferredHeight: 48
        contentItem: MenuIcon {
            iconName: "refresh"
            iconColor: refreshControl.enabled ? "#ffffff" : "#93a0b8"
            strokeWidth: 2.8
            anchors.centerIn: parent
            width: 28
            height: 28
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
            spacing: 16
            anchors.fill: parent
            anchors.leftMargin: 20
            anchors.rightMargin: 16
            anchors.topMargin: 7
            anchors.bottomMargin: 7

            MenuIcon {
                iconName: moreControl.iconName
                iconColor: moreControl.enabled ? "#ffffff" : "#93a0b8"
                strokeWidth: 2.5
                Layout.preferredWidth: 42
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
                horizontalAlignment: Text.AlignRight
                Layout.preferredWidth: 24
            }
        }
        background: Rectangle {
            radius: root.standardButtonRadius
            border.width: 0
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: moreControl.enabled ? root.moodColor("gradientStart") : root.moodDisabledColor("start") }
                GradientStop { position: 0.58; color: moreControl.enabled ? root.moodColor("gradientMid") : root.moodDisabledColor("mid") }
                GradientStop { position: 1.0; color: moreControl.enabled ? root.moodColor("gradientEnd") : root.moodDisabledColor("end") }
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
                GradientStop { position: 0.0; color: root.moodColor("gradientStart") }
                GradientStop { position: 0.58; color: root.moodColor("gradientMid") }
                GradientStop { position: 1.0; color: root.moodColor("gradientEnd") }
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
                GradientStop { position: 0.0; color: root.moodColor("gradientStart") }
                GradientStop { position: 0.58; color: root.moodColor("gradientMid") }
                GradientStop { position: 1.0; color: root.moodColor("gradientEnd") }
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
                GradientStop { position: 0.0; color: root.moodColor("backgroundStart") }
                GradientStop { position: 0.48; color: root.moodColor("backgroundMid") }
                GradientStop { position: 1.0; color: root.moodColor("backgroundEnd") }
            }
        }

        Rectangle {
            anchors.fill: parent
            opacity: 0.36
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: root.moodColor("overlayStart") }
                GradientStop { position: 0.48; color: "#00000000" }
                GradientStop { position: 1.0; color: root.moodColor("overlayEnd") }
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
            GradientStop { position: 0.0; color: root.moodColor("bannerStart") }
            GradientStop { position: 0.42; color: root.moodColor("bannerMid") }
            GradientStop { position: 0.72; color: root.moodColor("surface") }
            GradientStop { position: 1.0; color: root.moodColor("bannerEnd") }
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
                } else if (control.iconName === "heart" || control.iconName === "heartFilled") {
                    ctx.lineWidth = Math.max(4, s * 0.075)
                    ctx.beginPath()
                    ctx.moveTo(cx, cy + s * 0.28)
                    ctx.bezierCurveTo(cx - s * 0.40, cy + s * 0.02, cx - s * 0.34, cy - s * 0.33, cx - s * 0.10, cy - s * 0.28)
                    ctx.bezierCurveTo(cx - s * 0.01, cy - s * 0.26, cx, cy - s * 0.16, cx, cy - s * 0.16)
                    ctx.bezierCurveTo(cx, cy - s * 0.16, cx + s * 0.01, cy - s * 0.26, cx + s * 0.10, cy - s * 0.28)
                    ctx.bezierCurveTo(cx + s * 0.34, cy - s * 0.33, cx + s * 0.40, cy + s * 0.02, cx, cy + s * 0.28)
                    ctx.closePath()
                    if (control.iconName === "heartFilled") {
                        ctx.fill()
                    } else {
                        ctx.stroke()
                    }
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
            border.color: root.moodColor("focus")
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: control.enabled ? root.moodColor("gradientStart") : root.moodDisabledColor("start") }
                GradientStop { position: 0.58; color: control.enabled ? root.moodColor("gradientMid") : root.moodDisabledColor("mid") }
                GradientStop { position: 1.0; color: control.enabled ? root.moodColor("gradientEnd") : root.moodDisabledColor("end") }
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
                album: item.album || "",
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

                RefreshIconButton {
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
                            color: root.moodColor("accentSoft")
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

                                    Text {
                                        text: modelData.album || ""
                                        visible: modelData.album && modelData.album.length > 0 && modelData.album !== modelData.subtitle
                                        color: "#8fa0bf"
                                        font.pixelSize: 14
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
        onTriggered: root.hideTransientUi()
    }

    Timer {
        id: returnToNowTimer
        interval: Math.max(1000, djconnect.returnToNowSeconds * 1000)
        running: djconnect.returnToNowSeconds > 0
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
                root.scrollAskDjToTop()
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
            root.musicDnaDisableConfirmOpen = false
            root.musicDnaClearConfirmOpen = false
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
                    id: nowMoodButton
                    text: root.tr("mood")
                    ToolTip.visible: hovered
                    ToolTip.text: root.tr("mood_select")
                    Accessible.name: root.tr("mood")
                    Accessible.description: root.tr("mood_select")
                    Layout.preferredWidth: 48
                    Layout.preferredHeight: 48
                    contentItem: MenuIcon {
                        iconName: "mood"
                        iconColor: nowMoodButton.enabled ? "#ffffff" : "#93a0b8"
                        strokeWidth: 2.6
                        anchors.centerIn: parent
                        width: 28
                        height: 28
                    }
                    onClicked: root.moodPopoverOpen = !root.moodPopoverOpen
                }

                RefreshIconButton {
                    id: nowRefreshButton
                    Layout.rightMargin: 0
                    onClicked: djconnect.manualRefresh()
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
            id: moodPopover
            visible: root.activeScreen === "now" && root.moodPopoverOpen
            z: 40
            anchors.top: parent.top
            anchors.topMargin: 72
            anchors.right: parent.right
            anchors.rightMargin: 16
            width: Math.min(292, parent.width - 32)
            height: moodPopoverContent.implicitHeight + 24
            radius: root.standardButtonRadius
            color: "#141326"
            border.color: "#6a5bd8"
            border.width: 1

            ColumnLayout {
                id: moodPopoverContent
                anchors.fill: parent
                anchors.margins: 12
                spacing: 8

                Text {
                    text: root.tr("mood_select")
                    color: "#f7f3ff"
                    font.pixelSize: 18
                    font.bold: true
                    elide: Text.ElideRight
                    maximumLineCount: 1
                    Layout.fillWidth: true
                }

                GridLayout {
                    columns: 2
                    columnSpacing: 8
                    rowSpacing: 8
                    Layout.fillWidth: true

                    Button {
                        id: moodChillButton
                        text: root.tr("mood_chill")
                        checkable: true
                        checked: djconnect.moodValue >= 0 && djconnect.moodValue <= 24
                        Layout.fillWidth: true
                        Layout.preferredHeight: 44
                        onClicked: { djconnect.setMoodValue(0); root.moodPopoverOpen = false }
                        background: Rectangle {
                            radius: root.standardButtonRadius
                            color: moodChillButton.checked ? MoodTheme.color(0, "gradientStart") : "#24263f"
                            border.color: moodChillButton.checked ? MoodTheme.color(0, "focus") : "#3d4268"
                            border.width: 1
                        }
                        contentItem: Text { text: moodChillButton.text; color: "#ffffff"; font.pixelSize: 16; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
                    }

                    Button {
                        id: moodGrooveButton
                        text: root.tr("mood_groove")
                        checkable: true
                        checked: djconnect.moodValue >= 25 && djconnect.moodValue <= 59
                        Layout.fillWidth: true
                        Layout.preferredHeight: 44
                        onClicked: { djconnect.setMoodValue(35); root.moodPopoverOpen = false }
                        background: Rectangle {
                            radius: root.standardButtonRadius
                            color: moodGrooveButton.checked ? MoodTheme.color(35, "gradientStart") : "#24263f"
                            border.color: moodGrooveButton.checked ? MoodTheme.color(35, "focus") : "#3d4268"
                            border.width: 1
                        }
                        contentItem: Text { text: moodGrooveButton.text; color: "#ffffff"; font.pixelSize: 16; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
                    }

                    Button {
                        id: moodEnergyButton
                        text: root.tr("mood_energy")
                        checkable: true
                        checked: djconnect.moodValue >= 60 && djconnect.moodValue <= 84
                        Layout.fillWidth: true
                        Layout.preferredHeight: 44
                        onClicked: { djconnect.setMoodValue(70); root.moodPopoverOpen = false }
                        background: Rectangle {
                            radius: root.standardButtonRadius
                            color: moodEnergyButton.checked ? MoodTheme.color(70, "gradientStart") : "#24263f"
                            border.color: moodEnergyButton.checked ? MoodTheme.color(70, "focus") : "#3d4268"
                            border.width: 1
                        }
                        contentItem: Text { text: moodEnergyButton.text; color: "#ffffff"; font.pixelSize: 16; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
                    }

                    Button {
                        id: moodPartyButton
                        text: root.tr("mood_party")
                        checkable: true
                        checked: djconnect.moodValue >= 85
                        Layout.fillWidth: true
                        Layout.preferredHeight: 44
                        onClicked: { djconnect.setMoodValue(100); root.moodPopoverOpen = false }
                        background: Rectangle {
                            radius: root.standardButtonRadius
                            color: moodPartyButton.checked ? MoodTheme.color(100, "gradientStart") : "#24263f"
                            border.color: moodPartyButton.checked ? MoodTheme.color(100, "focus") : "#3d4268"
                            border.width: 1
                        }
                        contentItem: Text { text: moodPartyButton.text; color: "#ffffff"; font.pixelSize: 16; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
                    }
                }
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

                RefreshIconButton {
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
                            GradientStop { position: 0.0; color: root.moodColor("sliderStart") }
                            GradientStop { position: 1.0; color: root.moodColor("sliderEnd") }
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
                        color: root.moodColor("chip")

                        Rectangle {
                            width: controlVolumeSlider.visualPosition * parent.width
                            height: parent.height
                            radius: parent.radius
                            gradient: Gradient {
                                orientation: Gradient.Horizontal
                                GradientStop { position: 0.0; color: root.moodColor("sliderStart") }
                                GradientStop { position: 1.0; color: root.moodColor("sliderEnd") }
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
                    iconName: djconnect.currentTrackFavorite ? "heartFilled" : "heart"
                    active: djconnect.currentTrackFavorite
                    enabled: djconnect.favoriteAvailable && !djconnect.favoriteBusy
                    opacity: djconnect.favoriteAvailable ? (djconnect.favoriteBusy ? 0.55 : 1.0) : 0.0
                    onClicked: djconnect.saveCurrentTrack()
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
        onVisibleChanged: {
            if (visible && settingsScroll.contentItem) {
                settingsScroll.contentItem.contentY = 0
            }
        }

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
                    text: root.tr("websocket_fast_path")
                    color: "#d7e2e4"
                    font.pixelSize: 22
                    Layout.preferredWidth: 176
                    wrapMode: Text.WordWrap
                }

                Switch {
                    id: websocketFastPathSwitch
                    checked: djconnect.websocketFastPathEnabled
                    Layout.alignment: Qt.AlignVCenter
                    onToggled: djconnect.setWebSocketFastPathEnabled(checked)
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
                    text: root.tr("return_to_now")
                    color: "#d7e2e4"
                    font.pixelSize: 22
                    Layout.preferredWidth: 176
                    wrapMode: Text.WordWrap
                }

                ComboBox {
                    id: returnToNowBox
                    model: root.returnToNowChoices
                    currentIndex: root.returnToNowIndex()
                    font.pixelSize: 28
                    displayText: root.returnToNowLabel(djconnect.returnToNowSeconds)
                    delegate: ItemDelegate {
                        width: returnToNowBox.width
                        text: root.returnToNowLabel(modelData)
                        font.pixelSize: 30
                    }
                    Layout.fillWidth: true
                    onActivated: function(index) { djconnect.setReturnToNowSeconds(root.returnToNowChoices[index]) }
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
                        color: root.moodColor("chip")

                        Rectangle {
                            width: brightnessSlider.visualPosition * parent.width
                            height: parent.height
                            radius: parent.radius
                            gradient: Gradient {
                                orientation: Gradient.Horizontal
                                GradientStop { position: 0.0; color: root.moodColor("sliderStart") }
                                GradientStop { position: 1.0; color: root.moodColor("sliderEnd") }
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
                        { code: "en", label: "English" },
                        { code: "nl", label: "Nederlands" },
                        { code: "de", label: "Deutsch" },
                        { code: "fr", label: "Français" },
                        { code: "es", label: "Español" }
                    ]
                    textRole: "label"
                    valueRole: "code"
                    currentIndex: root.languageIndex()
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

            Text {
                text: root.tr("music_dna")
                color: "#f4f8f8"
                font.pixelSize: 26
                font.bold: true
                Layout.fillWidth: true
                Layout.topMargin: 8
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 14

                Text {
                    text: root.tr("music_dna_settings_status")
                    color: "#d7e2e4"
                    font.pixelSize: 22
                    font.bold: true
                    Layout.preferredWidth: 176
                }

                Text {
                    text: djconnect.musicDnaEnabled ? root.tr("music_dna_settings_enabled_description") : root.tr("music_dna_settings_disabled_description")
                    color: "#b9b5d4"
                    font.pixelSize: 22
                    font.bold: true
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignRight
                    Layout.fillWidth: true
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 14

                Text {
                    text: root.tr("music_dna")
                    color: "#f4f8f8"
                    font.pixelSize: 22
                    font.bold: true
                    Layout.preferredWidth: 176
                }

                Item { Layout.fillWidth: true }

                PurpleButton {
                    text: djconnect.musicDnaEnabled ? root.tr("music_dna_disable") : root.tr("music_dna_enable")
                    enabled: !djconnect.musicDnaBusy
                    font.pixelSize: 22
                    Layout.preferredWidth: 190
                    Layout.preferredHeight: 52
                    onClicked: {
                        if (djconnect.musicDnaEnabled) {
                            root.musicDnaDisableConfirmOpen = true
                        } else {
                            djconnect.setMusicDnaEnabled(true)
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 14

                Text {
                    text: root.tr("music_dna_settings_profile")
                    color: "#f4f8f8"
                    font.pixelSize: 22
                    font.bold: true
                    Layout.preferredWidth: 176
                }

                Item { Layout.fillWidth: true }

                DangerButton {
                    text: root.tr("music_dna_clear")
                    enabled: djconnect.musicDnaEnabled && !djconnect.musicDnaBusy
                    font.pixelSize: 22
                    Layout.preferredWidth: 150
                    Layout.preferredHeight: 52
                    onClicked: root.musicDnaClearConfirmOpen = true
                }
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
                        text: root.tr("control")
                        iconName: "control"
                        onClicked: root.activeScreen = "control"
                    }
                    Rectangle { Layout.fillWidth: true; Layout.leftMargin: 122; Layout.preferredHeight: 1; color: "#4d4a68" }

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
                        text: root.tr("music_dna")
                        iconName: "heart"
                        onClicked: root.activeScreen = "musicdna"
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
        id: trackInsightPanel
        property bool autoInsightRequested: false
        anchors.fill: parent
        color: "#070b16"
        visible: root.activeScreen === "trackinsight"
        z: 17
        onVisibleChanged: {
            if (visible && !autoInsightRequested && djconnect.playing) {
                autoInsightRequested = true
                djconnect.openTrackInsight()
            } else if (!visible) {
                autoInsightRequested = false
            }
        }

        AppBackground {}
        ModalBlocker {}

        ColumnLayout {
            anchors.fill: parent
            anchors.leftMargin: 20
            anchors.topMargin: 20
            anchors.rightMargin: 20
            anchors.bottomMargin: root.edge + 126
            spacing: 12

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Text {
                    text: root.tr("track_insight")
                    color: "#f4f8f8"
                    font.pixelSize: 40
                    font.bold: true
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }

                LoadingSpinner {
                    visible: djconnect.askDjBusy
                    running: visible
                    Layout.preferredWidth: 38
                    Layout.preferredHeight: 38
                }

                RefreshIconButton {
                    enabled: djconnect.paired && !djconnect.askDjBusy
                    onClicked: djconnect.refreshTrackInsight()
                }
            }

            Text {
                visible: djconnect.trackInsightError.length > 0
                text: djconnect.trackInsightError
                color: "#d8e3ee"
                font.pixelSize: 20
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            Text {
                visible: djconnect.trackInsightError.length === 0 && djconnect.trackInsightText.length === 0 && djconnect.trackInsightItems.length === 0 && !djconnect.askDjBusy
                text: root.tr("track_insight_empty")
                color: "#d8e3ee"
                font.pixelSize: 20
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            Rectangle {
                visible: djconnect.trackInsightTitle.length > 0 || djconnect.trackInsightArtist.length > 0 || djconnect.trackInsightImageUrl.length > 0
                Layout.fillWidth: true
                Layout.preferredHeight: 104
                radius: root.standardButtonRadius
                color: "#00000000"
                border.color: "#3b4a6e"
                border.width: 1
                clip: true

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10

                    Image {
                        source: djconnect.trackInsightImageUrl
                        visible: source.toString().length > 0
                        Layout.preferredWidth: 76
                        Layout.preferredHeight: 76
                        fillMode: Image.PreserveAspectCrop
                        smooth: true
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        Text {
                            text: djconnect.trackInsightTitle
                            color: "#ffffff"
                            font.pixelSize: 22
                            font.bold: true
                            elide: Text.ElideRight
                            maximumLineCount: 1
                            Layout.fillWidth: true
                        }

                        Text {
                            text: [djconnect.trackInsightArtist, djconnect.trackInsightAlbum].filter(function(v) { return v && v.length > 0 }).join(" · ")
                            color: "#cbd6ed"
                            font.pixelSize: 17
                            elide: Text.ElideRight
                            maximumLineCount: 1
                            Layout.fillWidth: true
                        }
                    }
                }
            }

            Text {
                visible: djconnect.trackInsightText.length > 0
                text: djconnect.trackInsightText
                color: "#ffffff"
                font.pixelSize: 21
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            Flow {
                visible: djconnect.trackInsightItems.length > 0
                spacing: 8
                Layout.fillWidth: true

                Repeater {
                    model: djconnect.trackInsightItems

                    Rectangle {
                        width: Math.max(132, trackMetricContent.implicitWidth + 24)
                        height: 64
                        radius: root.standardButtonRadius
                        color: "#00000000"
                        border.color: modelData.musicDna ? "#6aa0b9c8" : root.moodColor("accent")
                        border.width: 1

                        ColumnLayout {
                            id: trackMetricContent
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 1

                            Text {
                                text: root.trackInsightLabel(modelData.title || modelData.kind || "")
                                color: "#ffffff"
                                font.pixelSize: 15
                                font.bold: true
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }

                            Text {
                                text: modelData.value || ""
                                color: "#d8e3ee"
                                font.pixelSize: 19
                                font.bold: true
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }
                        }
                    }
                }
            }

            ScrollView {
                id: trackInsightScroll
                visible: djconnect.trackInsightSections.length > 0
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                contentWidth: availableWidth

                ColumnLayout {
                    width: Math.max(0, trackInsightScroll.availableWidth)
                    spacing: 10

                    Repeater {
                        model: djconnect.trackInsightSections

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: trackSectionContent.implicitHeight + 18
                            radius: root.standardButtonRadius
                            color: "#00000000"
                            border.color: modelData.metadataContext ? "#6aa0b9c8" : "#3b4a6e"
                            border.width: 1

                            ColumnLayout {
                                id: trackSectionContent
                                anchors.fill: parent
                                anchors.margins: 9
                                spacing: 5

                                Text {
                                    text: root.trackInsightLabel(modelData.title || modelData.kind || modelData.id || "")
                                    color: "#f2d8ff"
                                    font.pixelSize: 18
                                    font.bold: true
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }

                                Text {
                                    visible: modelData.body && modelData.body.length > 0
                                    text: modelData.body || ""
                                    color: "#ffffff"
                                    font.pixelSize: 17
                                    wrapMode: Text.WordWrap
                                    Layout.fillWidth: true
                                }

                                Repeater {
                                    model: modelData.details || []
                                    Text {
                                        text: "- " + modelData
                                        color: "#d8e3ee"
                                        font.pixelSize: 16
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                }
                            }
                        }
                    }
                }
            }

            Item {
                visible: !trackInsightScroll.visible
                Layout.fillWidth: true
                Layout.fillHeight: true
            }
        }
    }

    Rectangle {
        id: musicDiscoveryPanel
        anchors.fill: parent
        color: "#070b16"
        visible: root.activeScreen === "discover"
        z: 17

        AppBackground {}
        ModalBlocker {}

        ColumnLayout {
            anchors.fill: parent
            anchors.leftMargin: 20
            anchors.topMargin: 10
            anchors.rightMargin: 20
            anchors.bottomMargin: root.edge + 126
            spacing: 10

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 48
                spacing: 10

                Text {
                    text: root.tr("music_discovery")
                    color: "#f4f8f8"
                    font.pixelSize: 34
                    font.bold: true
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }

                LoadingSpinner {
                    visible: djconnect.musicDiscoveryBusy
                    running: visible
                    Layout.preferredWidth: 38
                    Layout.preferredHeight: 38
                }

                RefreshIconButton {
                    id: discoveryRefreshButton
                    enabled: !djconnect.musicDiscoveryBusy
                    onClicked: djconnect.refreshMusicDiscovery()
                }
            }

            Rectangle {
                visible: djconnect.musicDiscoveryConsentRejected
                Layout.fillWidth: true
                Layout.preferredHeight: consentColumn.implicitHeight + 28
                radius: root.standardButtonRadius
                color: "#182034"
                border.color: "#574b87"
                border.width: 1

                ColumnLayout {
                    id: consentColumn
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 10

                    Text {
                        text: root.tr("music_discovery_requires_music_dna")
                        color: "#ffffff"
                        font.pixelSize: 21
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        PurpleButton {
                            text: root.tr("music_discovery_enable")
                            enabled: !djconnect.musicDiscoveryBusy
                            font.pixelSize: 17
                            Layout.fillWidth: true
                            Layout.preferredHeight: 48
                            onClicked: djconnect.acceptMusicDiscoveryConsent()
                        }

                        DangerButton {
                            text: root.tr("cancel")
                            enabled: !djconnect.musicDiscoveryBusy
                            font.pixelSize: 17
                            Layout.preferredWidth: 130
                            Layout.preferredHeight: 48
                            onClicked: djconnect.rejectMusicDiscoveryConsent()
                        }
                    }
                }
            }

            Text {
                visible: djconnect.musicDiscoveryItems.length === 0 && !djconnect.musicDiscoveryBusy && !djconnect.musicDiscoveryConsentRejected
                text: djconnect.musicDiscoveryError.length > 0 ? djconnect.musicDiscoveryError : (djconnect.musicDiscoveryEmptyText.length > 0 ? djconnect.musicDiscoveryEmptyText : root.tr("music_discovery_empty"))
                color: "#d8e3ee"
                font.pixelSize: 20
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            ScrollView {
                id: discoveryScroll
                visible: djconnect.musicDiscoveryItems.length > 0
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                contentWidth: availableWidth

                GridLayout {
                    width: Math.max(0, discoveryScroll.availableWidth)
                    columns: 1
                    columnSpacing: 10
                    rowSpacing: 10

                    Repeater {
                        model: djconnect.musicDiscoveryItems

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: djconnect.musicDiscoveryFeedbackSupported ? 226 : 178
                            radius: root.standardButtonRadius
                            color: discoveryTap.activeFocus ? "#23385f" : "#172033"
                            border.color: discoveryTap.activeFocus ? root.moodColor("focus") : "#3b4a6e"
                            border.width: discoveryTap.activeFocus ? 2 : 1
                            clip: true

                            MouseArea {
                                id: discoveryTap
                                anchors.fill: parent
                                acceptedButtons: Qt.LeftButton
                                activeFocusOnTab: true
                                Keys.onReturnPressed: event.accepted = true
                                Keys.onEnterPressed: event.accepted = true
                                onClicked: function(mouse) { mouse.accepted = true }
                                onPressAndHold: {
                                    if (modelData.hasReason) {
                                        root.discoveryReasonTitle = modelData.title || root.tr("music_discovery_reason")
                                        root.discoveryReasonText = modelData.reason || ""
                                        root.discoveryReasonOpen = true
                                    }
                                }
                            }

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 14
                                spacing: 14

                                Image {
                                    source: modelData.imageUrl && modelData.imageUrl.length > 0 ? modelData.imageUrl : ""
                                    visible: source.toString().length > 0
                                    Layout.preferredWidth: 112
                                    Layout.preferredHeight: 112
                                    fillMode: Image.PreserveAspectCrop
                                    smooth: true
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    spacing: 4

                                    Text {
                                        visible: modelData.sectionTitle && modelData.sectionTitle.length > 0
                                        text: modelData.sectionTitle || ""
                                        color: "#f2d8ff"
                                        font.pixelSize: 17
                                        font.bold: true
                                        elide: Text.ElideRight
                                        maximumLineCount: 1
                                        Layout.fillWidth: true
                                    }

                                    Text {
                                        text: modelData.title || ""
                                        color: "#ffffff"
                                        font.pixelSize: 25
                                        font.bold: true
                                        elide: Text.ElideRight
                                        maximumLineCount: 1
                                        Layout.fillWidth: true
                                    }

                                    Text {
                                        text: [modelData.kindLabel || "", modelData.subtitle || ""].filter(function(v) { return v && v.length > 0 }).join(" · ")
                                        color: "#cbd6ed"
                                        font.pixelSize: 19
                                        elide: Text.ElideRight
                                        maximumLineCount: 1
                                        Layout.fillWidth: true
                                    }

                                    Text {
                                        visible: (modelData.qualityBand && modelData.qualityBand.length > 0)
                                                 || (modelData.qualityScore !== undefined && modelData.qualityScore !== null && String(modelData.qualityScore).length > 0)
                                        text: [modelData.qualityBand || "",
                                               (modelData.qualityScore !== undefined && modelData.qualityScore !== null) ? String(modelData.qualityScore) : ""]
                                              .filter(function(v) { return v && v.length > 0 }).join(" · ")
                                        color: "#b6c6ff"
                                        font.pixelSize: 17
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 8

                                        PurpleButton {
                                            text: root.tr("play_now")
                                            visible: modelData.playable
                                            enabled: modelData.playable && !djconnect.musicDiscoveryBusy
                                            font.pixelSize: 19
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 52
                                            onClicked: djconnect.playMusicDiscoveryItem(modelData.payload || "{}")
                                        }

                                        PurpleButton {
                                            visible: modelData.hasReason
                                            text: root.tr("music_discovery_reason")
                                            enabled: modelData.hasReason
                                            font.pixelSize: 18
                                            Layout.preferredWidth: 132
                                            Layout.preferredHeight: 52
                                            onClicked: {
                                                root.discoveryReasonTitle = modelData.title || root.tr("music_discovery_reason")
                                                root.discoveryReasonText = modelData.reason || ""
                                                root.discoveryReasonOpen = true
                                            }
                                        }
                                    }

                                    RowLayout {
                                        visible: djconnect.musicDiscoveryFeedbackSupported
                                        Layout.fillWidth: true
                                        spacing: 8

                                        PurpleButton {
                                            text: root.tr("music_discovery_not_for_me")
                                            enabled: !djconnect.musicDiscoveryBusy
                                            font.pixelSize: 14
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 40
                                            onClicked: djconnect.sendMusicDiscoveryFeedback(modelData.payload || "{}", "not_for_me")
                                        }

                                        PurpleButton {
                                            text: root.tr("music_discovery_less_like_this")
                                            enabled: !djconnect.musicDiscoveryBusy
                                            font.pixelSize: 14
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 40
                                            onClicked: djconnect.sendMusicDiscoveryFeedback(modelData.payload || "{}", "less_like_this")
                                        }

                                        PurpleButton {
                                            text: root.tr("music_discovery_hide_artist")
                                            enabled: !djconnect.musicDiscoveryBusy
                                            font.pixelSize: 14
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 40
                                            onClicked: djconnect.sendMusicDiscoveryFeedback(modelData.payload || "{}", "hide_artist")
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            Item {
                visible: !discoveryScroll.visible
                Layout.fillWidth: true
                Layout.fillHeight: true
            }
        }
    }

    Rectangle {
        id: discoveryReasonPanel
        anchors.fill: parent
        color: "#f2070b16"
        visible: root.discoveryReasonOpen
        z: 46

        ModalBlocker {}
        AppBackground {}

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 22
            anchors.bottomMargin: root.edge + 126
            spacing: 16

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 58
                spacing: 12

                Text {
                    text: root.tr("music_discovery_reason")
                    color: "#f4f8f8"
                    font.pixelSize: 36
                    font.bold: true
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }

                PurpleButton {
                    text: root.tr("close")
                    font.pixelSize: 18
                    Layout.preferredWidth: 132
                    Layout.preferredHeight: 52
                    onClicked: root.discoveryReasonOpen = false
                }
            }

            Text {
                text: root.discoveryReasonTitle
                color: "#ffffff"
                font.pixelSize: 28
                font.bold: true
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
                visible: text.length > 0
            }

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                contentWidth: availableWidth

                Text {
                    width: Math.max(0, parent.availableWidth)
                    text: root.discoveryReasonText
                    color: "#d8e3ee"
                    font.pixelSize: 24
                    lineHeight: 1.15
                    wrapMode: Text.WordWrap
                }
            }
        }
    }

    Rectangle {
        id: musicDnaPanel
        anchors.fill: parent
        color: "#070b16"
        visible: root.activeScreen === "musicdna"
        z: 17

        AppBackground {}
        ModalBlocker {}

        ColumnLayout {
            anchors.fill: parent
            anchors.leftMargin: 24
            anchors.topMargin: 22
            anchors.rightMargin: 24
            anchors.bottomMargin: root.edge + 126
            spacing: 14

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                Text {
                    text: root.tr("music_dna")
                    color: "#f4f8f8"
                    font.pixelSize: 42
                    font.bold: true
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }

                LoadingSpinner {
                    visible: djconnect.musicDnaBusy
                    running: visible
                    Layout.preferredWidth: 38
                    Layout.preferredHeight: 38
                }

                RefreshIconButton {
                    id: musicDnaRefreshButton
                    enabled: !djconnect.musicDnaBusy
                    onClicked: djconnect.refreshMusicDna()
                }
            }

            RowLayout {
                visible: !djconnect.musicDnaEnabled
                Layout.fillWidth: true
                spacing: 10

                Text {
                    text: root.tr("music_dna_disabled")
                    color: "#d9c4ff"
                    font.pixelSize: 21
                    font.bold: true
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }

            }

            Text {
                visible: !djconnect.musicDnaEnabled
                text: root.tr("music_dna_opt_in")
                color: "#cfd7ef"
                font.pixelSize: 20
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            Text {
                visible: djconnect.musicDnaEnabled && djconnect.musicDnaSummary.length > 0
                text: djconnect.musicDnaSummary
                color: "#ffffff"
                font.pixelSize: 22
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            ScrollView {
                id: musicDnaScroll
                visible: djconnect.musicDnaEnabled
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                contentWidth: availableWidth

                ColumnLayout {
                    width: Math.max(0, musicDnaScroll.availableWidth)
                    spacing: 10

                    Repeater {
                        model: djconnect.musicDnaSections

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: sectionColumn.implicitHeight + 22
                            radius: root.standardButtonRadius
                            color: "#182034"
                            border.color: "#3b4a6e"
                            border.width: 1

                            ColumnLayout {
                                id: sectionColumn
                                anchors.fill: parent
                                anchors.margins: 11
                                spacing: 5

                                Text {
                                    text: modelData.title || ""
                                    color: "#f2d8ff"
                                    font.pixelSize: 19
                                    font.bold: true
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }

                                Repeater {
                                    model: modelData.lines || []
                                    Text {
                                        text: modelData
                                        color: "#d8e3ee"
                                        font.pixelSize: 17
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
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
        id: askDjPanel
        anchors.fill: parent
        color: "#070b16"
        visible: root.activeScreen === "askdj"
        z: 17

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

                RefreshIconButton {
                    id: askDjRefreshButton
                    onClicked: djconnect.refreshAskDjHistory()
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
                            border.color: systemBubble ? "#6aa0b9c8" : (userBubble ? "#a5b4fc" : root.moodColor("accent"))
                            border.width: 1

                            ColumnLayout {
                                id: askDjBubbleContent
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.margins: 12
                                spacing: 8

                                Text {
                                    text: modelData.displayTime || ""
                                    visible: modelData.displayTime && modelData.displayTime.length > 0
                                    color: systemBubble ? "#c1d5df" : (userBubble ? "#d8defd" : "#c9c0ff")
                                    opacity: 0.82
                                    font.pixelSize: 14
                                    font.bold: false
                                    horizontalAlignment: userBubble ? Text.AlignRight : Text.AlignLeft
                                    Layout.fillWidth: true
                                }

                                Text {
                                    text: modelData.text
                                    color: "#ffffff"
                                    font.pixelSize: systemBubble ? 19 : 22
                                    font.bold: !systemBubble
                                    wrapMode: Text.WordWrap
                                    Layout.fillWidth: true
                                }

                                Flow {
                                    visible: modelData.trackInsight && modelData.musicDnaMatch && modelData.musicDnaMatch.length > 0
                                    spacing: 8
                                    Layout.fillWidth: true

                                    Rectangle {
                                        width: trackInsightModeLabel.implicitWidth + 24
                                        height: 30
                                        radius: 8
                                        color: "#33434a57"
                                        border.color: "#6aa0b9c8"
                                        border.width: 1

                                        Text {
                                            id: trackInsightModeLabel
                                            anchors.centerIn: parent
                                            text: root.tr("music_dna_match") + " " + (modelData.musicDnaMatch || "")
                                            color: "#d8f3ff"
                                            font.pixelSize: 15
                                            font.bold: true
                                            elide: Text.ElideRight
                                        }
                                    }
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

                                Flow {
                                    visible: modelData.trackInsight && modelData.items && modelData.items.length > 0
                                    spacing: 8
                                    Layout.fillWidth: true

                                    Repeater {
                                        model: modelData.items || []

                                        Rectangle {
                                            width: Math.min(askDjScroll.availableWidth, Math.max(132, trackInsightMetricContent.implicitWidth + 24))
                                            height: 58
                                            radius: 8
                                            color: "#00000000"
                                            border.color: modelData.musicDna ? "#6aa0b9c8" : root.moodColor("accent")
                                            border.width: 1
                                            clip: true

                                            ColumnLayout {
                                                id: trackInsightMetricContent
                                                anchors.fill: parent
                                                anchors.margins: 8
                                                spacing: 1

                                                RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 6

                                                    Text {
                                                        text: root.trackInsightLabel(modelData.title || modelData.kind || "")
                                                        color: "#d8c8ff"
                                                        font.pixelSize: 14
                                                        font.bold: true
                                                        elide: Text.ElideRight
                                                        maximumLineCount: 1
                                                        Layout.fillWidth: true
                                                    }

                                                    Text {
                                                        text: modelData.value || ""
                                                        color: "#ffffff"
                                                        font.pixelSize: 18
                                                        font.bold: true
                                                        elide: Text.ElideRight
                                                        maximumLineCount: 1
                                                    }
                                                }

                                                Text {
                                                    text: [modelData.source || "", modelData.confidence || ""].filter(function(value) { return value.length > 0 }).join(" · ")
                                                    color: "#9fb2d0"
                                                    font.pixelSize: 12
                                                    font.bold: true
                                                    elide: Text.ElideRight
                                                    maximumLineCount: 1
                                                    visible: text.length > 0
                                                    Layout.fillWidth: true
                                                }
                                            }
                                        }
                                    }
                                }

                                ColumnLayout {
                                    visible: modelData.trackInsight && modelData.analysis && modelData.analysis.sections && modelData.analysis.sections.length > 0
                                    Layout.fillWidth: true
                                    spacing: 6

                                    Repeater {
                                        model: modelData.analysis && modelData.analysis.sections ? modelData.analysis.sections : []

                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: trackInsightSectionContent.implicitHeight + 16
                                            radius: 8
                                            color: "#00000000"
                                            border.color: modelData.metadataContext ? "#6aa0b9c8" : ((modelData.source === "inferred" || modelData.source === "local_fallback" || modelData.source === "unavailable" || modelData.confidence === "low") ? "#b6a46a" : root.moodColor("accent"))
                                            border.width: 1

                                            ColumnLayout {
                                                id: trackInsightSectionContent
                                                anchors.left: parent.left
                                                anchors.right: parent.right
                                                anchors.top: parent.top
                                                anchors.margins: 8
                                                spacing: 3

                                                Text {
                                                    text: root.trackInsightLabel(modelData.title || modelData.id || modelData.kind || "")
                                                    color: modelData.metadataContext ? "#d8f3ff" : "#ffffff"
                                                    font.pixelSize: 16
                                                    font.bold: true
                                                    elide: Text.ElideRight
                                                    maximumLineCount: 1
                                                    Layout.fillWidth: true
                                                }

                                                Text {
                                                    text: modelData.body || ""
                                                    color: "#f0d7ea"
                                                    font.pixelSize: 14
                                                    wrapMode: Text.WordWrap
                                                    visible: text.length > 0
                                                    Layout.fillWidth: true
                                                }

                                                Repeater {
                                                    model: modelData.details || []

                                                    Text {
                                                        text: "• " + modelData
                                                        color: "#d8c8ff"
                                                        font.pixelSize: 13
                                                        wrapMode: Text.WordWrap
                                                        Layout.fillWidth: true
                                                    }
                                                }

                                                Text {
                                                    text: [modelData.source || "", modelData.confidence || ""].filter(function(value) { return value.length > 0 }).join(" · ")
                                                    color: "#9fb2d0"
                                                    font.pixelSize: 12
                                                    font.bold: true
                                                    visible: text.length > 0
                                                    Layout.fillWidth: true
                                                }
                                            }
                                        }
                                    }
                                }

                                ColumnLayout {
                                    visible: modelData.trackInsight && modelData.analysis && modelData.analysis.timeline && modelData.analysis.timeline.length > 0
                                    Layout.fillWidth: true
                                    spacing: 4

                                    Repeater {
                                        model: modelData.analysis && modelData.analysis.timeline ? modelData.analysis.timeline : []

                                        RowLayout {
                                            Layout.fillWidth: true
                                            spacing: 8

                                            Text {
                                                text: [modelData.start || "", modelData.end || ""].filter(function(value) { return value.length > 0 }).join("–")
                                                color: "#d8f3ff"
                                                font.pixelSize: 13
                                                font.bold: true
                                                Layout.preferredWidth: 86
                                                visible: text.length > 0
                                            }

                                            Text {
                                                text: modelData.label || modelData.kind || modelData.id || ""
                                                color: "#ffffff"
                                                font.pixelSize: 14
                                                elide: Text.ElideRight
                                                maximumLineCount: 1
                                                Layout.fillWidth: true
                                            }

                                            Text {
                                                text: [modelData.source || "", modelData.confidence || ""].filter(function(value) { return value.length > 0 }).join(" · ")
                                                color: "#9fb2d0"
                                                font.pixelSize: 11
                                                elide: Text.ElideRight
                                                maximumLineCount: 1
                                                visible: text.length > 0
                                                Layout.preferredWidth: 118
                                            }
                                        }
                                    }
                                }

                                ColumnLayout {
                                    visible: modelData.trackInsight && modelData.analysis && modelData.analysis.metadata && modelData.analysis.metadata.details && modelData.analysis.metadata.details.length > 0
                                    Layout.fillWidth: true
                                    spacing: 3

                                    Text {
                                        text: root.tr("analysis_context")
                                        color: "#d8f3ff"
                                        font.pixelSize: 13
                                        font.bold: true
                                        Layout.fillWidth: true
                                    }

                                    Repeater {
                                        model: modelData.analysis && modelData.analysis.metadata && modelData.analysis.metadata.details ? modelData.analysis.metadata.details : []

                                        Text {
                                            text: "• " + modelData
                                            color: "#9fb2d0"
                                            font.pixelSize: 13
                                            wrapMode: Text.WordWrap
                                            Layout.fillWidth: true
                                        }
                                    }
                                }

                                ColumnLayout {
                                    visible: modelData.trackInsight && modelData.analysis && modelData.analysis.djTips && modelData.analysis.djTips.length > 0
                                    Layout.fillWidth: true
                                    spacing: 4

                                    Repeater {
                                        model: modelData.analysis && modelData.analysis.djTips ? modelData.analysis.djTips : []

                                        Text {
                                            text: "• " + [modelData.title || modelData.kind || "", modelData.text || ""].filter(function(value) { return value.length > 0 }).join(": ")
                                            color: "#d8c8ff"
                                            font.pixelSize: 14
                                            wrapMode: Text.WordWrap
                                            Layout.fillWidth: true
                                        }
                                    }
                                }

                                ColumnLayout {
                                    visible: !modelData.trackInsight && modelData.items && modelData.items.length > 0
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
                                    visible: modelData.trackInsight && modelData.analysis && modelData.analysis.limitations && modelData.analysis.limitations.length > 0
                                    Layout.fillWidth: true
                                    spacing: 3

                                    Text {
                                        text: root.tr("analysis_limitations")
                                        color: "#9fb2d0"
                                        font.pixelSize: 13
                                        font.bold: true
                                        Layout.fillWidth: true
                                    }

                                    Repeater {
                                        model: modelData.analysis && modelData.analysis.limitations ? modelData.analysis.limitations : []

                                        Text {
                                            text: "• " + (modelData.text || modelData)
                                            color: "#9fb2d0"
                                            font.pixelSize: 13
                                            wrapMode: Text.WordWrap
                                            Layout.fillWidth: true
                                        }
                                    }
                                }

                                ColumnLayout {
                                    visible: modelData.trackInsight && modelData.analysis && modelData.analysis.providers && modelData.analysis.providers.length > 0
                                    Layout.fillWidth: true
                                    spacing: 3

                                    Text {
                                        text: root.tr("analysis_diagnostics")
                                        color: "#9fb2d0"
                                        font.pixelSize: 13
                                        font.bold: true
                                        Layout.fillWidth: true
                                    }

                                    Repeater {
                                        model: modelData.analysis && modelData.analysis.providers ? modelData.analysis.providers : []

                                        Text {
                                            text: "• " + [modelData.label || modelData.providerId || root.tr("unknown"), modelData.status || root.tr("unknown"), modelData.reason || ""].filter(function(value) { return value.length > 0 }).join(" · ")
                                            color: "#9fb2d0"
                                            font.pixelSize: 12
                                            wrapMode: Text.WordWrap
                                            Layout.fillWidth: true
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

                                AskDjGradientButton {
                                    visible: modelData.audioUrl && modelData.audioUrl.length > 0
                                    text: root.tr("replay_audio")
                                    font.pixelSize: 17
                                    Layout.preferredWidth: 220
                                    Layout.preferredHeight: 44
                                    onClicked: Qt.openUrlExternally(modelData.audioUrl)
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
                                                    text: modelData.isOutput ? root.tr("activate") : (modelData.isMedia ? root.tr("play_now") : (modelData.title || root.tr("start")))
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
                text: root.tr("track_insight")
                iconName: "trackInsight"
                checkable: true
                checked: root.activeScreen === "trackinsight"
                Layout.fillWidth: true
                Layout.fillHeight: true
                onClicked: root.openTrackInsightScreen()
            }

            NavButton {
                text: root.tr("music_discovery")
                iconName: "discover"
                checkable: true
                checked: root.activeScreen === "discover"
                Layout.fillWidth: true
                Layout.fillHeight: true
                onClicked: root.activeScreen = "discover"
            }

            NavButton {
                text: root.tr("more")
                iconName: "more"
                checkable: true
                checked: root.activeScreen === "more" || root.activeScreen === "playlists" || root.activeScreen === "games" || root.activeScreen === "settings" || root.activeScreen === "control"
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
                color: root.moodColor("chip")

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
            GradientStop { position: 0.0; color: root.moodColor("backgroundStart") }
            GradientStop { position: 0.5; color: root.moodColor("backgroundMid") }
            GradientStop { position: 1.0; color: root.moodColor("backgroundEnd") }
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
            GradientStop { position: 0.0; color: root.moodColor("toastStart") }
            GradientStop { position: 0.52; color: root.moodColor("toastMid") }
            GradientStop { position: 1.0; color: root.moodColor("toastEnd") }
        }

        Behavior on opacity { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
        Behavior on y { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }

        Row {
            anchors.centerIn: parent
            spacing: 16

            MenuIcon {
                width: 28
                height: 28
                iconName: djconnect.toastIcon
                iconColor: "#ffffff"
                strokeWidth: 2.8
                anchors.verticalCenter: parent.verticalCenter
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
                RefreshIconButton {
                    Layout.preferredHeight: 56
                    Layout.maximumHeight: 56
                    onClicked: {
                        djconnect.showLogs()
                        Qt.callLater(function() { logsArea.cursorPosition = 0 })
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
                clip: true

                RowLayout {
                    width: Math.max(logsScroll.availableWidth, logLineNumbers.implicitWidth + logsArea.implicitWidth + 36)
                    spacing: 0

                    Text {
                        id: logLineNumbers
                        text: root.lineNumbers(djconnect.logsText)
                        color: "#9aa6ad"
                        font.family: "monospace"
                        font.pixelSize: 24
                        horizontalAlignment: Text.AlignRight
                        Layout.preferredWidth: Math.max(54, implicitWidth + 18)
                        Layout.alignment: Qt.AlignTop
                        topPadding: 12
                        bottomPadding: 12
                        rightPadding: 10
                    }

                    TextArea {
                        id: logsArea
                        text: djconnect.logsText
                        readOnly: true
                        wrapMode: TextEdit.NoWrap
                        color: "#d7e2e4"
                        font.family: "monospace"
                        font.pixelSize: 24
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignTop
                        background: Rectangle {
                            color: "#10181c"
                            radius: 8
                            border.color: "#314449"
                        }
                        onTextChanged: Qt.callLater(function() { logsArea.cursorPosition = 0 })
                    }
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
        id: musicDnaClearConfirmPanel
        anchors.fill: parent
        color: "#cc070b16"
        visible: root.musicDnaClearConfirmOpen
        z: 86

        ModalBlocker {}

        Rectangle {
            anchors.centerIn: parent
            width: Math.min(parent.width - 48, 520)
            radius: 8
            color: "#f0151020"
            border.color: "#47345d"
            border.width: 1

            implicitHeight: musicDnaClearConfirmContent.implicitHeight + 44

            ColumnLayout {
                id: musicDnaClearConfirmContent
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 22
                spacing: 18

                Text {
                    text: root.tr("music_dna_clear_confirm_title")
                    color: "#ffffff"
                    font.pixelSize: 28
                    font.bold: true
                    Layout.fillWidth: true
                }

                Text {
                    text: root.tr("music_dna_clear_confirm_message")
                    color: "#f4f0ff"
                    font.pixelSize: 24
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                DangerButton {
                    text: root.tr("music_dna_clear")
                    Layout.fillWidth: true
                    Layout.preferredHeight: 56
                    onClicked: {
                        root.musicDnaClearConfirmOpen = false
                        djconnect.clearMusicDna()
                    }
                }

                PurpleButton {
                    text: root.tr("cancel")
                    font.pixelSize: 24
                    Layout.fillWidth: true
                    Layout.preferredHeight: 56
                    onClicked: root.musicDnaClearConfirmOpen = false
                }
            }
        }
    }

    Rectangle {
        id: musicDnaDisableConfirmPanel
        anchors.fill: parent
        color: "#cc070b16"
        visible: root.musicDnaDisableConfirmOpen
        z: 86

        ModalBlocker {}

        Rectangle {
            anchors.centerIn: parent
            width: Math.min(parent.width - 48, 520)
            radius: 8
            color: "#f0151020"
            border.color: "#47345d"
            border.width: 1

            implicitHeight: musicDnaDisableConfirmContent.implicitHeight + 44

            ColumnLayout {
                id: musicDnaDisableConfirmContent
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 22
                spacing: 18

                Text {
                    text: root.tr("music_dna_disable_confirm_title")
                    color: "#ffffff"
                    font.pixelSize: 28
                    font.bold: true
                    Layout.fillWidth: true
                }

                Text {
                    text: root.tr("music_dna_disable_confirm_message")
                    color: "#f4f0ff"
                    font.pixelSize: 24
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                DangerButton {
                    text: root.tr("music_dna_disable")
                    Layout.fillWidth: true
                    Layout.preferredHeight: 56
                    onClicked: {
                        root.musicDnaDisableConfirmOpen = false
                        djconnect.setMusicDnaEnabled(false)
                    }
                }

                PurpleButton {
                    text: root.tr("cancel")
                    font.pixelSize: 24
                    Layout.fillWidth: true
                    Layout.preferredHeight: 56
                    onClicked: root.musicDnaDisableConfirmOpen = false
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
                    Text { text: root.tr("client_type"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.clientType; color: "#ffffff"; font.pixelSize: 20; Layout.fillWidth: true }
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
                    Text { text: root.tr("transport"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.transportMode; color: "#ffffff"; font.pixelSize: 20; Layout.fillWidth: true }
                    Text { text: root.tr("connection_type"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.connectionType; color: "#ffffff"; font.pixelSize: 20; Layout.fillWidth: true; elide: Text.ElideRight }
                    Text { text: root.tr("music_backend"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.paired ? root.tr("connected_value") : root.tr("not_connected_value"); color: djconnect.paired ? "#32d35a" : "#ff3b30"; font.pixelSize: 20; font.bold: true; Layout.fillWidth: true }
                    Text { text: root.tr("backend_name"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.musicBackendName.length ? djconnect.musicBackendName : "-"; color: "#ffffff"; font.pixelSize: 18; Layout.fillWidth: true; elide: Text.ElideMiddle }
                    Text { text: root.tr("backend_error"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190; visible: djconnect.musicBackendError.length > 0 }
                    Text { text: djconnect.musicBackendError; color: "#ff8a8a"; font.pixelSize: 18; Layout.fillWidth: true; wrapMode: Text.Wrap; visible: djconnect.musicBackendError.length > 0 }
                    Text { text: root.tr("client_api_url_label"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.localApiUrl; color: "#ffffff"; font.pixelSize: 18; Layout.fillWidth: true; elide: Text.ElideMiddle }
                    Text { text: root.tr("ha_local_url"); color: "#b7a8c8"; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
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

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons
        propagateComposedEvents: true
        z: 199
        onPressed: function(mouse) {
            if (root.screenBlanked) {
                root.wakeDisplay()
                mouse.accepted = true
                return
            }
            root.recordActivity()
            mouse.accepted = false
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
