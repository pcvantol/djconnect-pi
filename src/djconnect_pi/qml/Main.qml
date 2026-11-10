import QtQuick
import "BrandTheme.js" as BrandTheme
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "MoodTheme.js" as MoodTheme

BrandWindow {
    id: root
    width: wallProfile ? Screen.width : 720
    height: wallProfile ? Screen.height : 720
    visible: true
    color: BrandTheme.colors.background
    title: "DJConnect"
    visibility: startWindowed ? Window.Windowed : Window.FullScreen

    readonly property string vibeScapeCurrentOwner: djconnect.djSession.state.owner_profile_id || djconnect.activeProfileId
    readonly property int vibeScapeCurrentEpoch: djconnect.djSession.state.owner_epoch || 0
    property int vibeScapeVisitEpoch: 0
    onVibeScapeCurrentOwnerChanged: syncVibeScape()
    onVibeScapeCurrentEpochChanged: syncVibeScape()
    property bool vibeScapeRequested: false
    property string vibeScapeOwner: ""
    property string vibeScapeSession: ""
    property real vibeScapePickerTop: 64
    readonly property bool vibeScapeAllowed: wallProfile && visible && active && activeScreen === "session" &&
        djconnect.paired && !djconnect.demoMode && vibeScapeCurrentOwner.length > 0 &&
        !djconnect.djSession.state.profile_confirmation_required && !djconnect.djSession.state.owner_read_only && djconnect.djSession.state.runtime_state === "active" &&
        djconnect.djSession.state.session_id.length > 0
    onVibeScapeAllowedChanged: if (!vibeScapeAllowed) closeVibeScape()
    function closeVibeScape() { vibeScapeLoader.active = false }
    function syncVibeScape() {
        if (vibeScapeLoader.active && (!vibeScapeAllowed || !djconnect.paired ||
                vibeScapeOwner !== vibeScapeCurrentOwner || vibeScapeVisitEpoch !== vibeScapeCurrentEpoch ||
                vibeScapeSession !== djconnect.djSession.state.session_id)) closeVibeScape()
    }
    Connections {
        target: djconnect.djSession
        function onChanged() { root.syncVibeScape() }
        function onNewCurrentContribution() {
            if (!root.screenBlanked || !root.active || root.splashVisible || !djconnect.paired)
                return
            djconnect.wakeDisplay()
            root.temporaryWake(20, false)
        }
    }
    Connections {
        target: djconnect
        function onProfileChanged() { root.trackArtworkOpen = false; root.syncVibeScape(); musicDnaOptIn.close() }
        function onPairedChanged() { root.trackArtworkOpen = false; root.syncVibeScape(); musicDnaOptIn.close() }
    }
    function openVibeScape(pickerTop) {
        if (!vibeScapeAllowed) return
        vibeScapeOwner = vibeScapeCurrentOwner
        vibeScapeVisitEpoch = vibeScapeCurrentEpoch
        vibeScapeSession = djconnect.djSession.state.session_id
        vibeScapePickerTop = Number.isFinite(pickerTop) ? vibeScapeLoader.mapFromItem(null, 0, pickerTop).y : 64
        vibeScapeRequested = true
        vibeScapeLoader.active = true
    }
    Loader {
        id: vibeScapeLoader
        objectName: "vibeScapeLoader"
        anchors.fill: parent; z: 35
        // Explicit visit latch: invalidation cannot re-arm a returned context.
        active: false
        focus: active
        onLoaded: item.forceActiveFocus()
        onActiveChanged: {
            if (!active) {
                root.vibeScapeRequested = false
                root.vibeScapeOwner = ""
                root.vibeScapeSession = ""
                root.vibeScapePickerTop = 64
                root.restartIdleTimer()
            }
        }
        sourceComponent: VibeScape {
            backend: djconnect; admitted: root.vibeScapeAllowed
            mood: root.appearanceMood
            pickerTop: root.vibeScapePickerTop
            forecastAvailable: djconnect.djSession.state.forecast_supported
            onCloseRequested: root.closeVibeScape()
            onFlowRequested: { root.closeVibeScape(); sharedSessionScreen.forecastMode = false }
            onForecastRequested: { root.closeVibeScape(); sharedSessionScreen.forecastMode = true }
        }
    }
    property bool wallProfile: djconnect.releaseProfile === "pi5-arm64"
    readonly property bool liquidGlassEnabled: djconnect.glassEnabled
    readonly property string appearanceMood: {
        if (root.activeScreen === "games") return gamesPanel.gameMood
        if (root.activeScreen === "trackinsight" && !trackInsightPanel.hasLiveSession)
            return trackInsightPanel.visualMood
        var session = djconnect.djSession.state
        if (session.session_id && ["chill", "groove", "energy", "party"].indexOf(session.mood) >= 0) return session.mood
        var settings = djconnect.sharedSettings
        var confirmed = settings && settings.available && !settings.selection_required ? (settings.values || {}).mood : ""
        return ["chill", "groove", "energy", "party"].indexOf(confirmed) >= 0 ? confirmed : ""
    }
    readonly property string visibleArtworkTint: activeScreen === "now" ? nowArtworkPalette.tint :
        activeScreen === "trackinsight" ? trackInsightArtworkFrame.artworkTint :
        activeScreen === "session" ? sharedSessionScreen.artworkTint : ""
    Binding { target: GlassStyle; property: "mood"; value: root.appearanceMood }
    Binding { target: GlassStyle; property: "contextArtworkTint"; value: root.visibleArtworkTint }
    Binding { target: GlassStyle; property: "moodAccent"; value: MoodTheme.moodColor(root.appearanceMood, "gradientStart") }
    Binding { target: GlassStyle; property: "surfaceTint"; value: MoodTheme.material(root.appearanceMood,root.visibleArtworkTint,GlassStyle.moodTintStrength,GlassStyle.artworkTintStrength) }
    Binding { target: GlassStyle; property: "heroStart"; value: MoodTheme.mix("#142652",MoodTheme.moodColor(root.appearanceMood,"gradientStart"),GlassStyle.heroMoodStrength) }
    Binding { target: GlassStyle; property: "heroMid"; value: MoodTheme.mix("#211745",MoodTheme.moodColor(root.appearanceMood,"gradientMid"),GlassStyle.heroMoodStrength) }
    Binding { target: GlassStyle; property: "heroEnd"; value: MoodTheme.mix("#2B1452",MoodTheme.moodColor(root.appearanceMood,"gradientEnd"),GlassStyle.heroMoodStrength) }
    Binding { target: GlassStyle; property: "enabled"; value: root.liquidGlassEnabled }
    Binding { target: GlassStyle; property: "hardware"; value: root.wallProfile && root.GraphicsInfo.api === GraphicsInfo.OpenGL }
    Binding { target: GlassStyle; property: "awake"; value: root.visible && !root.screenBlanked }
    Binding { target: GlassStyle; property: "backdrop"; value: glassUnderlay }
    Binding { target: GlassStyle; property: "texture"; value: sharedGlassCapture.item ? sharedGlassCapture.item.texture : null }
    // Never captures private content or the material itself; no recursive feedback.
    AppBackground {
        id: glassUnderlay
        visible: false
        sessionCanvas: root.activeScreen === "session" || root.activeScreen === "games" || root.activeScreen === "discover"
    }
    Loader {
        id: sharedGlassCapture
        objectName: "sharedGlassCapture"
        active: GlassStyle.enabled && GlassStyle.hardware && GlassStyle.awake
        anchors.fill: parent; visible: false
        sourceComponent: GlassBackdrop { sourceItem: glassUnderlay }
    }
    FrameAnimation {
        objectName: "glassGeometryAnimation"
        running: GlassStyle.active
        onTriggered: GlassStyle.geometryFrame = (GlassStyle.geometryFrame + 1) % 1000000
    }
    property real edge: wallProfile ? Math.max(56, width * 0.07) : 28
    property real wallTypeScale: wallProfile ? Math.min(width / 900, height / 1440) : 1
    property int motionFast: wallProfile ? 180 : 140
    property int motionStandard: wallProfile ? 360 : 240
    property int motionAmbient: wallProfile ? 4200 : 0
    property bool splashVisible: true
    property string activeScreen: "session"
    property bool settingsOpen: activeScreen === "settings"
    property bool gamesOpen: activeScreen === "games"
    property bool aboutOpen: false
    property bool resetPairingConfirmOpen: false
    property bool rebootConfirmOpen: false
    property bool shutdownConfirmOpen: false
    property bool clearLogsConfirmOpen: false
    property bool askDjClearConfirmOpen: false
    property bool musicDnaDisableConfirmOpen: false
    property bool musicDnaClearConfirmOpen: false
    property bool discoveryReasonOpen: false
    property string discoveryReasonTitle: ""
    property string discoveryReasonText: ""
    property bool forceScreenAwake: false
    property bool forceBrightnessFull: false
    property bool suppressNextNowPanelTap: false
    property bool trackArtworkOpen: false
    property bool trackArtworkControlsOpen: false
    readonly property bool trackArtworkCanControl: trackArtworkOpen && sessionTrackArtwork
        && trackArtworkViewOpen && !!sharedSessionScreen.state.playback_control.available
    onTrackArtworkCanControlChanged: if (!trackArtworkCanControl) trackArtworkControlsOpen = false
    onTrackArtworkControlsOpenChanged: {
        if (!trackArtworkControlsOpen && sharedSessionScreen.owner)
            sharedSessionScreen.owner.cancelPlaybackIntent()
    }
    property bool sessionTrackArtwork: false
    readonly property bool trackArtworkViewOpen: sharedSessionScreen.liveViewOpen
    onTrackArtworkViewOpenChanged: if (!trackArtworkViewOpen) trackArtworkOpen = false
    readonly property bool overlayTrackAvailable: sessionTrackArtwork ? sharedSessionScreen.trackArtworkAvailable : djconnect.hasTrackTitle
    onOverlayTrackAvailableChanged: if (!overlayTrackAvailable) trackArtworkOpen = false
    onTrackArtworkOpenChanged: if (!trackArtworkOpen) trackArtworkDismissTimer.stop()
    onScreenBlankedChanged: if (screenBlanked) trackArtworkOpen = false
    function showTrackArtwork(fromSession, automatic) {
        if (!trackArtworkViewOpen || (automatic && trackArtworkOpen && !trackArtworkDismissTimer.running))
            return
        sessionTrackArtwork = fromSession
        trackArtworkOpen = true
        trackArtworkControlsOpen = trackArtworkCanControl
        if (automatic && !trackArtworkControlsOpen) trackArtworkDismissTimer.restart()
        else trackArtworkDismissTimer.stop()
    }
    function toggleTrackArtworkControls() {
        if (!trackArtworkCanControl)
            return
        trackArtworkDismissTimer.stop()
        trackArtworkControlsOpen = !trackArtworkControlsOpen
    }
    function openTrackArtwork() {
        if (sharedSessionScreen.trackArtworkAvailable)
            showTrackArtwork(true)
    }
    property double lastWakeDisplayAt: 0
    property int wakeDisplayDebounceMs: 800
    property int standardButtonRadius: 24
    property bool screenBlanked: djconnect.screenTimeoutSeconds > 0 && !idleTimer.running && !root.forceScreenAwake && !vibeScapeLoader.active
    property real brightnessOverlayOpacity: root.screenBlanked || root.forceBrightnessFull ? 0 : 1 - (djconnect.screenBrightnessPercent / 100.0)
    property int trVersion: djconnect.translationVersion

    readonly property string edgeBackRoute: {
        if (!root.active || root.screenBlanked || root.splashVisible || (!djconnect.paired && !djconnect.demoMode)
                || root.trackArtworkOpen || vibeScapeLoader.active || musicDnaOptIn.visible || root.resetPairingConfirmOpen || root.rebootConfirmOpen
                || root.shutdownConfirmOpen || root.clearLogsConfirmOpen || root.askDjClearConfirmOpen
                || root.musicDnaDisableConfirmOpen || root.musicDnaClearConfirmOpen || root.discoveryReasonOpen)
            return ""
        if (djconnect.logsVisible) return "logs"
        if (root.aboutOpen) return "about"
        if (root.activeScreen === "history" || root.activeScreen === "session-history") {
            if (sharedSessionScreen.historyNavigationBlocked) return ""
            var state = djconnect.djSession.state
            return JSON.stringify([root.activeScreen, state.owner_profile_id || "", state.owner_epoch || 0,
                state.session_id || "", (state.timeline.session || {}).session_id || ""])
        }
        if (["askdj", "musicdna", "playlists", "settings", "legal", "privacy", "feedback", "games"].indexOf(root.activeScreen) >= 0)
            return root.activeScreen
        return ""
    }
    function navigateEdgeBack(route) {
        if (!route || route !== edgeBackRoute) return
        if (route === "logs") djconnect.hideLogs()
        else if (route === "about") root.aboutOpen = false
        else if (root.activeScreen === "history" || root.activeScreen === "session-history")
            sharedSessionScreen.navigateBackFromHistory()
        else root.activeScreen = "more"
    }

    function openMusicDnaPrompt(discoveryConsent) {
        if (musicDnaOptIn.visible || djconnect.musicDnaBusy || djconnect.musicDiscoveryBusy) return
        musicDnaOptIn.discoveryConsent = discoveryConsent
        musicDnaOptIn.profileId = djconnect.activeProfileId
        musicDnaOptIn.open()
    }

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

    function djAnnouncementOutputLabel(value) {
        if (value === "ha_speaker") return root.tr("dj_announcement_output_ha_speaker")
        return root.tr("dj_announcement_output_text_only")
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

    function moodColor(token) {
        return MoodTheme.color(root.appearanceMood, token)
    }

    function moodDisabledColor(position) {
        return MoodTheme.disabled(position)
    }

    function recordActivity() {
        var wasBlanked = root.screenBlanked
        root.restoreSessionFromSleep()
        root.forceBrightnessFull = false
        root.restartIdleTimer()
        if (root.forceScreenAwake && forcedWakeTimer.running) {
            forcedWakeTimer.restart()
        }
        if (wasBlanked) {
            root.hideTransientUi()
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
        var now = Date.now()
        if (now - root.lastWakeDisplayAt < root.wakeDisplayDebounceMs) {
            root.recordActivity()
            return
        }
        root.lastWakeDisplayAt = now
        djconnect.wakeDisplay()
        root.recordActivity()
    }

    onActiveScreenChanged: {
        root.trackArtworkOpen = false
        if (root.wallProfile && (root.activeScreen === "now" || root.activeScreen === "control")) {
            root.closeVibeScape()
            root.activeScreen = "session"
            return
        }
        root.restartIdleTimer()
        if (root.activeScreen === "askdj") {
            root.scrollAskDjToTop()
        } else if (root.activeScreen === "musicdna") {
            djconnect.loadMusicDna()
        } else if (root.activeScreen === "discover") {
            djconnect.loadMusicDiscovery()
        } else if (root.activeScreen === "settings") {
            djconnect.pollSharedSettings()
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
        root.resetPairingConfirmOpen = false
        root.rebootConfirmOpen = false
        root.shutdownConfirmOpen = false
        root.clearLogsConfirmOpen = false
        root.askDjClearConfirmOpen = false
        askDjPanel.closeSearch()
        root.musicDnaDisableConfirmOpen = false
        root.musicDnaClearConfirmOpen = false
        root.discoveryReasonOpen = false
        musicDnaOptIn.close()
    }

    function restoreSessionFromSleep() {
        if (root.screenBlanked && (djconnect.paired || djconnect.demoMode))
            root.activeScreen = "session"
    }

    function temporaryWake(seconds, fullBrightness = true) {
        root.restoreSessionFromSleep()
        root.forceScreenAwake = true
        root.forceBrightnessFull = fullBrightness
        forcedWakeTimer.interval = Math.max(1000, seconds * 1000)
        forcedWakeTimer.restart()
    }

    component PurpleButton: Button {
        id: control
        property bool primary: false
        font.pixelSize: 22
        font.bold: true
        contentItem: Text {
            text: control.text
            font: control.font
            color: control.enabled ? BrandTheme.colors.text : BrandTheme.colors.disabledText
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        background: GlassSurface {
            radius: control.primary ? height / 2 : root.standardButtonRadius
            interactive: true
            primary: control.primary
            pressed: control.down
            focused: control.activeFocus
            opacity: control.enabled ? 1 : 0.45
            scale: control.down ? 0.98 : 1
            Behavior on scale { NumberAnimation { duration: root.motionFast; easing.type: Easing.OutCubic } }
        }
    }

    component AskDjGradientButton: Button {
        id: askDjButton
        font.pixelSize: 18
        font.bold: true
        contentItem: Text {
            text: askDjButton.text
            font: askDjButton.font
            color: askDjButton.enabled ? BrandTheme.colors.text : BrandTheme.colors.muted
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            maximumLineCount: 1
        }
        background: GlassSurface {
            radius: height / 2
            interactive: true
            primary: true
            pressed: askDjButton.down
            focused: askDjButton.activeFocus
            opacity: askDjButton.enabled ? 1 : 0.45
        }
    }

    component MenuIcon: FeatureIcon {}

    component NavButton: PurpleButton {
        id: navControl
        property string iconName: ""

        font.pixelSize: 15
        contentItem: ColumnLayout {
            spacing: 3

            MenuIcon {
                objectName: "navIcon-" + navControl.iconName
                iconName: navControl.iconName
                iconColor: !navControl.enabled ? BrandTheme.colors.disabledText : navControl.iconName === "session" ?
                    BrandTheme.colors.white : (navControl.checked ? BrandTheme.colors.actionAccent : BrandTheme.colors.muted)
                strokeWidth: navControl.checked ? 2.8 : 2.4
                Layout.preferredWidth: navControl.checked ? 30 : 28
                Layout.preferredHeight: navControl.checked ? 30 : 28
                Layout.alignment: Qt.AlignHCenter
                Layout.fillWidth: true
            }

            Text {
                text: navControl.text
                color: navControl.enabled ? (navControl.checked ? BrandTheme.colors.actionAccent : BrandTheme.colors.muted) : BrandTheme.colors.disabledText
                font: navControl.font
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
                maximumLineCount: 1
                Layout.fillWidth: true
            }
        }
        background: Rectangle {
            radius: height / 2
            color: navControl.checked ? "#700e0b2a" : (navControl.down ? "#25ffffff" : "transparent")
            border.width: navControl.activeFocus ? 2 : 0
            border.color: BrandTheme.colors.focus
            Behavior on color { ColorAnimation { duration: 140 } }
        }
    }

    component RefreshIconButton: PurpleButton {
        id: refreshControl
        property bool loading: false

        text: root.tr("refresh")
        ToolTip.visible: hovered
        ToolTip.text: text
        Accessible.name: text
        Accessible.description: text
        Layout.preferredWidth: 48
        Layout.preferredHeight: 48
        background: GlassSurface { tertiary: true; interactive: true; pressed: refreshControl.down; focused: refreshControl.activeFocus }
        contentItem: Item {
            MenuIcon {
                iconName: "refresh"
                iconColor: refreshControl.enabled ? BrandTheme.colors.text : BrandTheme.colors.disabledText
                strokeWidth: 2.8
                anchors.centerIn: parent
                width: 28
                height: 28
                visible: !refreshControl.loading
            }
            BusyIndicator {
                anchors.centerIn: parent
                width: 28
                height: width
                visible: refreshControl.loading
                running: visible
            }
        }
    }

    component MoreMenuButton: Button {
        id: moreControl
        property string iconName: ""

        font.pixelSize: root.wallProfile ? 24 : 21
        font.weight: Font.DemiBold
        padding: root.wallProfile ? 20 : 15
        Layout.fillWidth: true
        Layout.preferredWidth: 1
        implicitHeight: Math.max(root.wallProfile ? 108 : 80, contentItem.implicitHeight + 2 * padding)
        Accessible.name: text
        contentItem: RowLayout {
            spacing: root.wallProfile ? 19 : 14

            Rectangle {
                Layout.preferredWidth: root.wallProfile ? 60 : 44
                Layout.preferredHeight: Layout.preferredWidth
                radius: root.wallProfile ? 19 : 14
                color: BrandTheme.alpha(BrandTheme.colors.actionAccent, "24")
                border.color: "#23FFFFFF"
                FeatureIcon {
                    anchors.centerIn: parent
                    width: parent.width * 0.63
                    height: width
                    iconName: moreControl.iconName
                    iconColor: BrandTheme.colors.actionAccent
                    Accessible.ignored: true
                }
            }
            Text {
                text: moreControl.text
                textFormat: Text.PlainText
                color: moreControl.enabled ? BrandTheme.colors.text : BrandTheme.colors.disabledText
                font: moreControl.font
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }
            FeatureIcon {
                iconName: "back"
                rotation: 180
                Layout.preferredWidth: 24
                Layout.preferredHeight: 24
                iconColor: BrandTheme.colors.muted
                Accessible.ignored: true
            }
        }
        background: GlassSurface {
            introduction: true
            radius: root.wallProfile ? 34 : 24
            pressed: moreControl.down
            focused: moreControl.activeFocus
        }
    }

    component LoadingSpinner: Item {
        id: spinner
        property bool running: true
        property color dotColor: BrandTheme.colors.muted
        property bool spokes: false

        implicitWidth: 42
        implicitHeight: 42

        Repeater {
            model: 12

            Rectangle {
                required property int index
                width: spinner.spokes ? Math.max(2, spinner.width * 0.08) : Math.max(4, spinner.width * 0.13)
                height: spinner.spokes ? spinner.height * 0.23 : width
                rotation: spinner.spokes ? index * 30 + 90 : 0
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
            duration: spinner.spokes ? 900 : root.wallProfile ? 1200 : 900
            easing.type: spinner.spokes ? Easing.Linear : Easing.InOutSine
        }

        SequentialAnimation on scale {
            running: spinner.running && spinner.visible && root.wallProfile && !spinner.spokes
            loops: Animation.Infinite
            NumberAnimation { to: 1.12; duration: 760; easing.type: Easing.InOutSine }
            NumberAnimation { to: 0.94; duration: 760; easing.type: Easing.InOutSine }
        }
    }

    component DangerButton: Button {
        id: control

        font.pixelSize: 24
        font.bold: true
        contentItem: Text {
            text: control.text
            font: control.font
            color: BrandTheme.colors.actionDanger
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        background: GlassSurface {
            radius: root.standardButtonRadius
            interactive: true; destructive: true; pressed: control.down; focused: control.activeFocus
            opacity: control.enabled ? 1 : 0.4
        }
    }

    component WarningButton: Button {
        id: control

        font.pixelSize: 24
        font.bold: true
        contentItem: Text {
            text: control.text
            font: control.font
            color: BrandTheme.colors.warning
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        background: Rectangle {
            radius: root.standardButtonRadius
            color: Qt.rgba(1, 0.82, 0.35, control.down ? 0.22 : 0.12)
            border.color: "#1FFFFFFF"
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
        id: appCanvas
        property bool sessionCanvas: false
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
            property real driftX: 0
            property real driftY: 0
            width: parent.width * 0.94
            height: width
            radius: width / 2
            x: -width * 0.30 + driftX
            y: parent.height * 0.08 + driftY
            color: root.moodColor("overlayStart")
            opacity: root.wallProfile ? 0.04 : 0
            scale: 0.94

            SequentialAnimation on scale {
                running: root.wallProfile && !root.screenBlanked && !appCanvas.sessionCanvas
                loops: Animation.Infinite
                NumberAnimation { to: 1.08; duration: 7200; easing.type: Easing.InOutSine }
                NumberAnimation { to: 0.94; duration: 7200; easing.type: Easing.InOutSine }
            }
            SequentialAnimation on driftX {
                running: root.wallProfile && !root.screenBlanked && !appCanvas.sessionCanvas
                loops: Animation.Infinite
                NumberAnimation { to: parent.width * 0.035; duration: 18000; easing.type: Easing.InOutSine }
                NumberAnimation { to: 0; duration: 18000; easing.type: Easing.InOutSine }
            }
            SequentialAnimation on driftY {
                running: root.wallProfile && !root.screenBlanked && !appCanvas.sessionCanvas
                loops: Animation.Infinite
                NumberAnimation { to: parent.height * 0.018; duration: 21000; easing.type: Easing.InOutSine }
                NumberAnimation { to: 0; duration: 21000; easing.type: Easing.InOutSine }
            }
        }

        Rectangle {
            property real driftX: 0
            property real driftY: 0
            width: parent.width * 0.82
            height: width
            radius: width / 2
            x: parent.width - width * 0.58 + driftX
            y: parent.height * 0.48 + driftY
            color: root.moodColor("overlayEnd")
            opacity: root.wallProfile ? 0.04 : 0
            scale: 1.05

            SequentialAnimation on scale {
                running: root.wallProfile && !root.screenBlanked && !appCanvas.sessionCanvas
                loops: Animation.Infinite
                NumberAnimation { to: 0.92; duration: 8200; easing.type: Easing.InOutSine }
                NumberAnimation { to: 1.05; duration: 8200; easing.type: Easing.InOutSine }
            }
            SequentialAnimation on driftX {
                running: root.wallProfile && !root.screenBlanked && !appCanvas.sessionCanvas
                loops: Animation.Infinite
                NumberAnimation { to: -parent.width * 0.028; duration: 20000; easing.type: Easing.InOutSine }
                NumberAnimation { to: 0; duration: 20000; easing.type: Easing.InOutSine }
            }
            SequentialAnimation on driftY {
                running: root.wallProfile && !root.screenBlanked && !appCanvas.sessionCanvas
                loops: Animation.Infinite
                NumberAnimation { to: -parent.height * 0.014; duration: 17000; easing.type: Easing.InOutSine }
                NumberAnimation { to: 0; duration: 17000; easing.type: Easing.InOutSine }
            }
        }

        Rectangle {
            anchors.fill: parent
            opacity: root.wallProfile ? 0.48 : 0.36
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: root.moodColor("overlayStart") }
                GradientStop { position: 0.48; color: "#00000000" }
                GradientStop { position: 1.0; color: root.moodColor("overlayEnd") }
            }
            SequentialAnimation on opacity {
                running: root.wallProfile && !root.screenBlanked && !appCanvas.sessionCanvas
                loops: Animation.Infinite
                NumberAnimation { to: 0.62; duration: 5200; easing.type: Easing.InOutSine }
                NumberAnimation { to: 0.42; duration: 5200; easing.type: Easing.InOutSine }
            }
        }
        Loader {
            anchors.fill: parent
            active: appCanvas.sessionCanvas
            sourceComponent: SessionMoodCanvas {
                mood: root.appearanceMood
                activeSession: root.activeScreen === "games" || (root.activeScreen === "session" && djconnect.djSession.state.runtime_state === "active")
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
                ctx.strokeStyle = BrandTheme.colors.text
                ctx.fillStyle = BrandTheme.colors.text
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
        background: GlassSurface {
            radius: control.primary ? height / 2 : root.standardButtonRadius
            interactive: true
            primary: control.primary
            selected: control.active
            pressed: control.down
            focused: control.activeFocus
            opacity: control.enabled ? 1 : 0.4
            scale: control.down ? 0.98 : 1
            Behavior on scale { NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }
        }
    }

    component MediaListPanel: Rectangle {
        id: panel
        property string heading: ""
        property string emptyText: ""
        property string searchLabel: ""
        property string iconName: "queue"
        property string playCommand: "play_context_at"
        property bool loading: false
        property var items: []
        property bool searching: false
        property bool keyboardOpen: false
        readonly property bool compact: width < 900
        readonly property var matches: filterItems(items, searchInput.text)
        signal refreshRequested()

        function filterItems(source, query) {
            var term = searchText(query.trim())
            if (!term) return source
            return source.filter(function(item) {
                return [item.title, item.subtitle, item.artist, item.album].some(function(value) {
                    return searchText(value || "").indexOf(term) >= 0
                })
            })
        }
        function searchText(value) {
            return String(value).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase()
        }
        function moveMatch(delta) {
            if (!matches.length || !searchInput.text.trim()) return
            mediaRows.currentIndex = (mediaRows.currentIndex + delta + matches.length) % matches.length
            mediaRows.positionViewAtIndex(mediaRows.currentIndex, ListView.Contain)
        }
        function closeSearch() {
            keyboardOpen = false
            searching = false
            searchInput.clear()
        }

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
        color: BrandTheme.colors.background
        z: 16
        onVisibleChanged: {
            if (visible) mediaRows.positionViewAtBeginning()
            else closeSearch()
        }
        onMatchesChanged: {
            mediaRows.currentIndex = 0
            mediaRows.positionViewAtBeginning()
        }
        Connections {
            target: djconnect
            function onProfileChanged() { panel.closeSearch() }
            function onPairedChanged() { panel.closeSearch() }
        }
        Connections {
            target: root
            function onActiveChanged() { if (!root.active) panel.closeSearch() }
            function onScreenBlankedChanged() { if (root.screenBlanked) panel.closeSearch() }
        }

        AppBackground { sessionCanvas: true }
        ModalBlocker {}

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: panel.compact ? 16 : 24
            anchors.bottomMargin: panel.keyboardOpen ? 8 : 132
            spacing: panel.compact ? 10 : 16

            PageToolbar {
                title: panel.heading
                showLeading: panel.playCommand === "start_playlist"
                leading: [ GlassButton {
                    iconName: "back"; tertiary: true; implicitWidth: 52
                    Accessible.name: root.tr("more")
                    onClicked: root.activeScreen = "more"
                } ]
                showConnection: true
                connectionLabel: root.tr("connection_type")
                connectionText: djconnect.connectionType

                GlassButton {
                    objectName: "mediaSearchOpen"
                    iconName: "search"
                    tertiary: true
                    implicitWidth: 52
                    foregroundColor: panel.searching ? BrandTheme.colors.actionAccent : BrandTheme.colors.text
                    Accessible.name: panel.searchLabel
                    enabled: panel.searching || panel.items.length > 0
                    onClicked: {
                        if (panel.searching) panel.closeSearch()
                        else {
                            panel.searching = true
                            panel.keyboardOpen = true
                            searchInput.forceActiveFocus()
                        }
                    }
                }
                RefreshIconButton {
                    objectName: "mediaRefresh"
                    loading: panel.loading
                    onClicked: if (!loading) panel.refreshRequested()
                }
            }
            Control {
                visible: panel.searching
                Layout.fillWidth: true
                padding: 5
                background: GlassSurface { radius: 24; interactive: true; focused: searchInput.activeFocus }
                contentItem: RowLayout {
                    spacing: 4
                    FeatureIcon { iconName: "search"; Layout.preferredWidth: 27; Layout.preferredHeight: 27 }
                    TextField {
                        id: searchInput
                        objectName: "mediaSearchInput"
                        Layout.fillWidth: true
                        Layout.minimumHeight: 48
                        background: Item {}
                        placeholderText: panel.searchLabel
                        Accessible.name: placeholderText
                        font.pixelSize: panel.compact ? 18 : 22
                        maximumLength: 120
                        selectByMouse: true
                        TapHandler { onTapped: panel.keyboardOpen = true }
                        onAccepted: {
                            if (panel.keyboardOpen) panel.keyboardOpen = false
                            else panel.moveMatch(1)
                        }
                        Keys.onEscapePressed: if (panel.keyboardOpen) panel.keyboardOpen = false; else panel.closeSearch()
                    }
                    GlassButton {
                        iconName: "arrow_up"; tertiary: true
                        Accessible.name: root.tr("logs_previous_match")
                        enabled: panel.matches.length > 0 && searchInput.text.trim().length > 0
                        onClicked: panel.moveMatch(-1)
                    }
                    GlassButton {
                        iconName: "arrow_down"; tertiary: true
                        Accessible.name: root.tr("logs_next_match")
                        enabled: panel.matches.length > 0 && searchInput.text.trim().length > 0
                        onClicked: panel.moveMatch(1)
                    }
                    GlassButton {
                        iconName: "end"; tertiary: true; Accessible.name: root.tr("close")
                        onClicked: panel.closeSearch()
                    }
                }
            }
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 0
                ListView {
                    id: mediaRows
                    objectName: "mediaRows"
                    anchors.fill: parent
                    visible: panel.matches.length > 0
                    model: panel.matches
                    clip: true
                    spacing: panel.compact ? 10 : 14
                    ScrollBar.vertical: ScrollBar {}
                    delegate: Button {
                        id: mediaRow
                        required property var modelData
                        required property int index
                        objectName: "mediaItemRow-" + index
                        width: mediaRows.width
                        implicitHeight: Math.max(panel.compact ? 86 : 100, contentItem.implicitHeight + 2 * verticalPadding)
                        topPadding: panel.compact ? 9 : 13
                        bottomPadding: topPadding
                        leftPadding: panel.compact ? 12 : 16
                        rightPadding: leftPadding
                        text: modelData.title || ""
                        Accessible.name: text
                        enabled: !!modelData.uri && !djconnect.mediaPlaybackBusy
                        opacity: enabled ? 1 : 0.58
                        onClicked: djconnect.playMediaItem(panel.playCommand, panel.itemPayload(modelData))
                        background: GlassSurface {
                            introduction: true
                            radius: panel.compact ? 24 : 34
                            pressed: mediaRow.down
                            focused: mediaRow.activeFocus || (searchInput.text.trim().length > 0
                                && mediaRows.currentIndex === mediaRow.index)
                        }
                        contentItem: RowLayout {
                            spacing: panel.compact ? 12 : 17
                            Rectangle {
                                id: mediaArt
                                Layout.preferredWidth: panel.compact ? 60 : 74
                                Layout.preferredHeight: Layout.preferredWidth
                                radius: panel.compact ? 14 : 19
                                color: "#22FFFFFF"
                                clip: true
                                FeatureIcon {
                                    anchors.centerIn: parent
                                    width: parent.width * 0.52; height: width
                                    visible: cover.status !== Image.Ready
                                    iconName: panel.iconName
                                    iconColor: BrandTheme.colors.muted
                                }
                                Image {
                                    id: cover
                                    anchors.fill: parent
                                    source: mediaRow.modelData.imageUrl || ""
                                    sourceSize.width: mediaArt.width
                                    sourceSize.height: mediaArt.height
                                    fillMode: Image.PreserveAspectCrop
                                    asynchronous: true
                                    cache: false
                                    visible: status === Image.Ready
                                }
                            }
                            ColumnLayout {
                                id: mediaText
                                Layout.fillWidth: true
                                spacing: 3
                                Text {
                                    text: mediaRow.text
                                    textFormat: Text.PlainText
                                    color: BrandTheme.colors.text
                                    font.pixelSize: panel.compact ? 20 : 24
                                    font.weight: Font.DemiBold
                                    wrapMode: Text.Wrap
                                    maximumLineCount: 2
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                                Text {
                                    text: mediaRow.modelData.subtitle || ""
                                    textFormat: Text.PlainText
                                    visible: text.length > 0
                                    color: BrandTheme.colors.muted
                                    font.pixelSize: panel.compact ? 16 : 19
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                                Text {
                                    text: mediaRow.modelData.album || ""
                                    textFormat: Text.PlainText
                                    visible: text.length > 0 && text !== (mediaRow.modelData.subtitle || "")
                                    color: BrandTheme.colors.muted
                                    font.pixelSize: panel.compact ? 14 : 16
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                            }
                            FeatureIcon {
                                objectName: "mediaPlayIndicator"
                                visible: mediaRow.enabled
                                iconName: "play"
                                Layout.preferredWidth: panel.compact ? 28 : 34
                                Layout.preferredHeight: Layout.preferredWidth
                                Accessible.ignored: true
                            }
                        }
                    }
                }
                ColumnLayout {
                    anchors.centerIn: parent
                    width: parent.width
                    visible: panel.matches.length === 0
                    spacing: 14
                    FeatureIcon {
                        iconName: panel.items.length > 0 ? "search" : panel.iconName
                        iconColor: BrandTheme.colors.muted
                        Layout.alignment: Qt.AlignHCenter
                        Layout.preferredWidth: panel.compact ? 40 : 62
                        Layout.preferredHeight: Layout.preferredWidth
                    }
                    Text {
                        text: panel.items.length > 0 ? root.tr("media_no_matches") : panel.emptyText
                        textFormat: Text.PlainText
                        color: BrandTheme.colors.muted
                        font.pixelSize: panel.compact ? 20 : 24
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }
                }
            }
            SearchKeyboardDock {
                visible: panel.searching && panel.keyboardOpen
                Layout.fillWidth: true
                backend: djconnect
                target: searchInput
                keyboardName: "mediaSearchKeyboard"
                onSubmitted: panel.keyboardOpen = false
                onDismissed: panel.keyboardOpen = false
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
            root.temporaryWake(10, false)
            root.restartIdleTimer()
        }
        function onTemporaryWakeRequested(seconds) {
            root.temporaryWake(seconds)
        }
        function onPlaybackTrackChanged() {
            if (root.splashVisible || (!djconnect.paired && !djconnect.demoMode) || !djconnect.hasTrackTitle)
                return
            djconnect.wakeDisplay()
            root.temporaryWake(10)
            root.showTrackArtwork(false, true)
        }
        function onDjResponseChanged() {
            if (djconnect.djResponseVisible) {
                djResponseTimer.restart()
            } else {
                djResponseTimer.stop()
            }
        }
        function onAskDjChanged() {
            if (djconnect.askDjMessages.length === 0 && askDjPanel.searchOpen)
                askDjPanel.closeSearch()
            if (root.activeScreen === "askdj" && !askDjPanel.searchOpen) {
                root.scrollAskDjToTop()
            }
            if (root.askDjClearConfirmOpen && djconnect.askDjMessages.length === 0) {
                root.askDjClearConfirmOpen = false
            }
        }
        function onScreenshotRequested() {
            root.temporaryWake(10, false)
            root.restartIdleTimer()
            root.wakeDisplay()
            Qt.callLater(function() {
                djconnect.saveWindowScreenshot(root)
            })
        }
        function onDebugScreenRequested(screen) {
            root.splashVisible = false
            root.aboutOpen = false
            root.resetPairingConfirmOpen = false
            root.rebootConfirmOpen = false
            root.shutdownConfirmOpen = false
            root.askDjClearConfirmOpen = false
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

            PageToolbar {
                title: root.tr("now_playing")
                showConnection: true
                connectionLabel: root.tr("connection_type")
                connectionText: djconnect.connectionType
                Layout.fillWidth: true

                BusyIndicator {
                    running: djconnect.busy
                    visible: djconnect.busy
                    implicitWidth: 28
                    implicitHeight: 28
                }

                GlassButton {
                    iconName: "control"
                    Accessible.name: root.tr("control")
                    onClicked: root.activeScreen = "control"
                }

                RefreshIconButton {
                    id: nowRefreshButton
                    Layout.rightMargin: 0
                    onClicked: djconnect.manualRefresh()
                }

            }

            Item {
                id: artShell
                objectName: "nowTrackArtwork"
                Layout.fillWidth: true
                Layout.fillHeight: true

                Rectangle {
                    id: artFrame
                    anchors.centerIn: parent
                    width: Math.min(parent.width, parent.height)
                    height: width
                    radius: 8
                    color: BrandTheme.colors.background
                    border.color: BrandTheme.colors.surfaceRaised
                    border.width: 1
                    scale: djconnect.playing ? 1.0 : 0.96
                    clip: true

                    Behavior on scale { NumberAnimation { duration: 280; easing.type: Easing.OutCubic } }

                    ArtworkPalette {
                        id: nowArtworkPalette
                        backend: djconnect; imageItem: albumArt
                        active: !root.screenBlanked
                        leaseKey: djconnect.activeProfileId + "|" + djconnect.title + "|" + djconnect.artist
                    }
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
                            color: BrandTheme.colors.text
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
                            color: BrandTheme.colors.muted
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
                        color: BrandTheme.colors.background
                        opacity: albumArt.status === Image.Ready ? 0 : 1

                        Text {
                            anchors.centerIn: parent
                            text: "DJConnect"
                            color: BrandTheme.colors.text
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

    }

    Rectangle {
        id: controlPanel
        onVisibleChanged: if (!visible) djconnect.cancelControlVolume()
        function adjustVolume(delta) {
            var lease = djconnect.beginControlVolume()
            if (lease > 0)
                djconnect.commitControlVolume(lease, Math.round(djconnect.volume + delta))
        }
        anchors.fill: parent
        color: BrandTheme.colors.background
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

            PageToolbar {
                title: root.tr("control")
                showConnection: true
                connectionLabel: root.tr("connection_type")
                connectionText: djconnect.connectionType
                Layout.fillWidth: true

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
                objectName: "controlTrackMetadata"
                Layout.preferredHeight: 72
                spacing: 2

                Text {
                    text: djconnect.title
                    color: BrandTheme.colors.text
                    font.pixelSize: 30
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideRight
                    maximumLineCount: 1
                    Layout.fillWidth: true
                }

                Text {
                    text: djconnect.artist
                    color: BrandTheme.colors.muted
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
                    color: BrandTheme.alpha(BrandTheme.colors.surface, "55")
                    border.color: BrandTheme.colors.surfaceRaised
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
                    color: BrandTheme.colors.text
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
                    color: BrandTheme.colors.muted
                    font.pixelSize: 24
                    Layout.preferredWidth: 46
                }

                PurpleButton {
                    text: "-"
                    font.pixelSize: 30
                    Layout.preferredWidth: 54
                    Layout.preferredHeight: 54
                    enabled: djconnect.controlVolumeAvailable
                    onClicked: controlPanel.adjustVolume(-10)
                }

                Slider {
                    id: controlVolumeSlider
                    objectName: "controlVolumeSlider"
                    from: 0
                    to: 60
                    enabled: djconnect.controlVolumeAvailable
                    stepSize: 1
                    Layout.fillWidth: true
                    Accessible.name: root.tr("vol")
                    onMoved: {
                        if (!controlVolumePointer.pressed) {
                            var lease = djconnect.beginControlVolume()
                            if (lease > 0) djconnect.commitControlVolume(lease, Math.round(value))
                        }
                    }
                    MouseArea {
                        id: controlVolumePointer
                        anchors.fill: parent
                        acceptedButtons: Qt.LeftButton
                        property int lease: 0
                        property int draft: 0

                        function valueAt(x) {
                            var slider = controlVolumeSlider
                            var halfHandle = slider.handle.width / 2
                            var travel = Math.max(1, slider.availableWidth - 2 * halfHandle)
                            var position = Math.max(0, Math.min(1, (x - slider.leftPadding - halfHandle) / travel))
                            return Math.round(slider.valueAt(slider.mirrored ? 1 - position : position))
                        }

                        onPressed: function(mouse) {
                            controlVolumeSlider.forceActiveFocus(Qt.MouseFocusReason)
                            lease = djconnect.beginControlVolume()
                            draft = valueAt(mouse.x)
                        }
                        onPositionChanged: function(mouse) {
                            if (pressed && lease > 0) draft = valueAt(mouse.x)
                        }
                        onReleased: function(mouse) {
                            var captured = lease
                            lease = 0
                            if (captured > 0) djconnect.commitControlVolume(captured, valueAt(mouse.x))
                        }
                        onCanceled: {
                            if (lease > 0) djconnect.cancelControlVolume()
                            lease = 0
                        }
                    }
                    Binding {
                        target: controlVolumeSlider; property: "value"
                        value: controlVolumePointer.lease > 0 ? controlVolumePointer.draft : Math.min(60, djconnect.volume)
                        restoreMode: Binding.RestoreNone
                    }
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
                        color: BrandTheme.colors.text
                        border.color: BrandTheme.colors.muted
                        border.width: 1
                    }
                }

                PurpleButton {
                    text: "+"
                    font.pixelSize: 30
                    Layout.preferredWidth: 54
                    Layout.preferredHeight: 54
                    enabled: djconnect.controlVolumeAvailable
                    onClicked: controlPanel.adjustVolume(10)
                }

                Text {
                    text: Math.round(Math.min(60, djconnect.volume) / 60 * 100) + "%"
                    color: BrandTheme.colors.text
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

                BrandComboBox {
                    id: controlOutputDeviceCombo
                    property string noOutputDeviceLabel: root.tr("none")
                    property var deviceChoices: [{ "name": noOutputDeviceLabel, "value": "" }].concat(djconnect.outputDeviceChoices.length > 0 ? djconnect.outputDeviceChoices : (djconnect.outputDevice.length > 0 ? [{ "name": djconnect.outputDevice, "value": djconnect.outputDevice }] : []))
                    function choiceName(choice) {
                        if (typeof choice === "string") return choice
                        return ((choice && choice.name) || (choice && choice.value) || "").toString()
                    }
                    function choiceValue(choice) {
                        if (typeof choice === "string") return choice
                        return ((choice && choice.value) || (choice && choice.name) || "").toString()
                    }
                    function selectedIndex() {
                        var selected = (djconnect.outputDevice || "").trim()
                        if (selected.length === 0) return 0
                        for (var i = 0; i < deviceChoices.length; i++) {
                            if (choiceName(deviceChoices[i]).trim() === selected || choiceValue(deviceChoices[i]).trim() === selected) return i
                        }
                        return 0
                    }
                    model: deviceChoices
                    textRole: "name"
                    visible: count > 1 || djconnect.outputDevice.length === 0
                    currentIndex: selectedIndex()
                    font.pixelSize: 26
                    delegate: ItemDelegate {
                        width: controlOutputDeviceCombo.width
                        text: controlOutputDeviceCombo.choiceName(modelData)
                        font.pixelSize: 28
                    }
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    onActivated: function(index) {
                        var value = controlOutputDeviceCombo.choiceName(controlOutputDeviceCombo.deviceChoices[index])
                        if (value === controlOutputDeviceCombo.noOutputDeviceLabel) value = ""
                        djconnect.setOutputDevice(value)
                    }
                }

                Text {
                    text: root.tr("output_device")
                    visible: controlOutputDeviceCombo.count <= 1 && djconnect.outputDevice.length > 0
                    color: BrandTheme.colors.muted
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
                    color: djconnect.paired ? (djconnect.backendAvailable ? BrandTheme.colors.success : BrandTheme.colors.danger) : BrandTheme.colors.warning
                    Layout.alignment: Qt.AlignVCenter
                }

                Text {
                    text: djconnect.statusText
                    color: BrandTheme.colors.muted
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
        color: BrandTheme.colors.background
        visible: settingsOpen && (djconnect.paired || djconnect.demoMode)
        z: 10
        onVisibleChanged: {
            if (visible && settingsScroll.contentItem) {
                settingsScroll.contentItem.contentY = 0
            }
        }

        AppBackground { sessionCanvas: true }

        PageToolbar {
            id: settingsToolbar
            anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
            anchors.margins: 22
            title: root.tr("setup_title")
            leading: [ GlassButton { iconName: "back"; tertiary: true; implicitWidth: 52; Accessible.name: root.tr("more"); onClicked: root.activeScreen = "more" } ]
        }

        ScrollView {
            id: settingsScroll
            anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
            anchors.top: settingsToolbar.bottom
            anchors.margins: 22
            anchors.bottomMargin: 130
            clip: true
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            contentWidth: availableWidth

            ColumnLayout {
                width: Math.max(0, settingsScroll.availableWidth)
                spacing: 20

                PurpleButton {
                    objectName: "settingsOpenLocalTerminal"
                    text: root.tr("local_terminal")
                    enabled: djconnect.localTerminalAvailable && !djconnect.busy
                    Layout.fillWidth: true
                    Layout.preferredHeight: 58
                    onClicked: djconnect.openLocalTerminal()
                }

                Text {
                    visible: !djconnect.localTerminalAvailable
                    text: root.tr("local_terminal_disabled")
                    color: BrandTheme.colors.muted
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                DangerButton {
                    objectName: "settingsShutdownDevice"
                    text: root.tr("shutdown_device")
                    font.pixelSize: 24
                    Layout.fillWidth: true
                    Layout.preferredHeight: 58
                    onClicked: root.shutdownConfirmOpen = true
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    BrandSwitch {
                        objectName: "glassAppearanceToggle"
                        text: root.tr("glass_title")
                        font.pixelSize: 24
                        checked: djconnect.glassEnabled
                        onToggled: djconnect.setGlassEnabled(checked)
                        Accessible.name: root.tr("glass_title")
                    }
                    Text {
                        text: root.tr("glass_description")
                        color: BrandTheme.colors.muted; font.pixelSize: 20
                        wrapMode: Text.WordWrap; textFormat: Text.PlainText
                        Layout.fillWidth: true
                    }
                    Text {
                        visible: root.liquidGlassEnabled && !GlassStyle.hardware
                        text: root.tr("glass_fallback")
                        color: BrandTheme.colors.muted; font.pixelSize: 18
                        wrapMode: Text.WordWrap; textFormat: Text.PlainText
                        Layout.fillWidth: true
                    }
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
                    color: BrandTheme.colors.muted
                    font.pixelSize: 22
                    Layout.preferredWidth: 176
                    wrapMode: Text.WordWrap
                }

                BrandSwitch {
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
                    text: root.tr("session_refresh_interval")
                    color: BrandTheme.colors.muted
                    font.pixelSize: 22
                    Layout.preferredWidth: 176
                    wrapMode: Text.WordWrap
                }

                BrandComboBox {
                    objectName: "sessionRefreshInterval"
                    readonly property var choices: [1, 5, 10, 15, 30, 60]
                    model: choices.map(function(seconds) {
                        return root.tr("session_refresh_seconds").replace("%1", seconds)
                    })
                    currentIndex: choices.indexOf(djconnect.sessionRefreshSeconds)
                    Accessible.name: root.tr("session_refresh_interval")
                    font.pixelSize: 28
                    Layout.fillWidth: true
                    onActivated: function(index) { djconnect.setSessionRefreshSeconds(choices[index]) }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 14

                Text {
                    text: root.tr("screen_off")
                    color: BrandTheme.colors.muted
                    font.pixelSize: 22
                    Layout.preferredWidth: 176
                }

                BrandComboBox {
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
                    color: BrandTheme.colors.muted
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
                        color: BrandTheme.colors.text
                        border.color: BrandTheme.colors.muted
                        border.width: 1
                    }
                }

                Text {
                    text: Math.round(brightnessSlider.value) + "%"
                    color: BrandTheme.colors.text
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
                    color: BrandTheme.colors.muted
                    font.pixelSize: 22
                    Layout.preferredWidth: 176
                }

                BrandComboBox {
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
                    color: BrandTheme.colors.muted
                    font.pixelSize: 22
                    Layout.preferredWidth: 176
                }

                BrandComboBox {
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
                    color: BrandTheme.colors.muted
                    font.pixelSize: 22
                    Layout.preferredWidth: 176
                }

                BrandComboBox {
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

            SharedSettingsPanel {
                backend: djconnect
                visible: djconnect.paired
                Layout.fillWidth: true
            }

            Text {
                visible: !djconnect.sharedSettingsManaged
                text: root.tr("dj_announcement_settings_title")
                color: BrandTheme.colors.text
                font.pixelSize: 26
                font.bold: true
                Layout.fillWidth: true
                Layout.topMargin: 8
            }

            RowLayout {
                visible: !djconnect.sharedSettingsManaged
                Layout.fillWidth: true
                spacing: 14

                Text {
                    text: root.tr("dj_announcement_output")
                    color: BrandTheme.colors.muted
                    font.pixelSize: 22
                    Layout.preferredWidth: 176
                    wrapMode: Text.WordWrap
                }

                BrandComboBox {
                    id: djAnnouncementOutputBox
                    visible: !djconnect.sharedSettingsManaged
                    property var outputChoices: djconnect.djAnnouncementSpeakerAvailable ? ["text_only", "ha_speaker"] : ["text_only"]
                    font.pixelSize: 24
                    model: outputChoices
                    currentIndex: Math.max(0, outputChoices.indexOf(djconnect.djAnnouncementOutput))
                    displayText: root.djAnnouncementOutputLabel(djconnect.djAnnouncementOutput)
                    delegate: ItemDelegate {
                        width: djAnnouncementOutputBox.width
                        text: root.djAnnouncementOutputLabel(modelData)
                        font.pixelSize: 26
                    }
                    Layout.fillWidth: true
                    onActivated: function(index) { djconnect.setDjAnnouncementOutput(outputChoices[index]) }
                }
            }

            Text {
                visible: !djconnect.sharedSettingsManaged && !djconnect.djAnnouncementSpeakerAvailable
                text: root.tr("dj_announcement_speaker_unavailable")
                color: BrandTheme.colors.muted
                font.pixelSize: 18
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            Text {
                visible: !djconnect.sharedSettingsManaged && djconnect.djAnnouncementSpeakerAvailable && djconnect.djAnnouncementSpeakerName.length > 0
                text: root.tr("dj_announcement_speaker_configured") + " " + djconnect.djAnnouncementSpeakerName
                color: BrandTheme.colors.muted
                font.pixelSize: 18
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            Text {
                text: root.tr("music_dna")
                color: BrandTheme.colors.text
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
                    color: BrandTheme.colors.muted
                    font.pixelSize: 22
                    font.bold: true
                    Layout.preferredWidth: 176
                }

                Text {
                    text: djconnect.musicDnaEnabled ? root.tr("music_dna_settings_enabled_description") : root.tr("music_dna_settings_disabled_description")
                    color: BrandTheme.colors.muted
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
                    color: BrandTheme.colors.text
                    font.pixelSize: 22
                    font.bold: true
                    Layout.preferredWidth: 176
                }

                Item { Layout.fillWidth: true }

                PurpleButton {
                    text: djconnect.musicDnaEnabled ? root.tr("music_dna_disable") : root.tr("music_dna_enable")
                    primary: !djconnect.musicDnaEnabled
                    enabled: !djconnect.musicDnaBusy
                    font.pixelSize: 22
                    Layout.preferredWidth: 190
                    Layout.preferredHeight: 52
                    onClicked: {
                        if (djconnect.musicDnaEnabled) {
                            root.musicDnaDisableConfirmOpen = true
                        } else {
                            root.openMusicDnaPrompt(false)
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 14

                Text {
                    text: root.tr("music_dna_settings_profile")
                    color: BrandTheme.colors.text
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

            Item { Layout.fillHeight: true }
        }
    }
    }

    MediaListPanel {
        id: queuePanel
        visible: root.activeScreen === "queue"
        heading: root.tr("queue")
        emptyText: root.tr("empty_queue")
        searchLabel: root.tr("media_search_queue")
        playCommand: "play_context_at"
        items: djconnect.queueItems
        loading: djconnect.queueLoading
        onRefreshRequested: djconnect.loadQueue()
    }

    MediaListPanel {
        id: playlistsPanel
        visible: root.activeScreen === "playlists"
        heading: root.tr("playlists")
        emptyText: root.tr("empty_playlists")
        searchLabel: root.tr("media_search_playlists")
        iconName: "playlists"
        playCommand: "start_playlist"
        items: djconnect.playlistItems
        loading: djconnect.playlistsLoading
        onRefreshRequested: djconnect.loadPlaylists()
    }

    Rectangle {
        id: morePanel
        anchors.fill: parent
        color: BrandTheme.colors.background
        visible: root.activeScreen === "more"
        z: 16

        AppBackground { sessionCanvas: true }
        ModalBlocker {}

        ColumnLayout {
            anchors.fill: parent
            anchors.leftMargin: 24
            anchors.topMargin: 24
            anchors.rightMargin: 24
            anchors.bottomMargin: root.edge + 126
            spacing: 16

            PageToolbar { title: root.tr("more") }

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentWidth: availableWidth
                clip: true
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                GridLayout {
                    width: parent.width
                    columns: root.width < 900 ? 1 : Math.max(2, Math.floor(width / 420))
                    columnSpacing: root.wallProfile ? 22 : 16
                    rowSpacing: columnSpacing
                    MoreMenuButton {
                        text: root.tr("ask_dj"); iconName: "chat"
                        onClicked: { root.activeScreen = "askdj"; djconnect.loadAskDjHistory() }
                    }
                    MoreMenuButton {
                        text: root.tr("session_history"); iconName: "session"
                        objectName: "openSessionArchive"
                        onClicked: sharedSessionScreen.openArchive()
                    }
                    MoreMenuButton {
                        text: root.tr("music_dna"); iconName: "heart"
                        onClicked: root.activeScreen = "musicdna"
                    }
                    MoreMenuButton {
                        text: root.tr("playlists"); iconName: "playlists"
                        onClicked: { root.activeScreen = "playlists"; djconnect.loadPlaylists() }
                    }
                    MoreMenuButton {
                        text: root.tr("games"); iconName: "gamepad"
                        onClicked: root.activeScreen = "games"
                    }
                    MoreMenuButton {
                        text: root.tr("setup"); iconName: "settings"
                        onClicked: root.activeScreen = "settings"
                    }
                    MoreMenuButton {
                        text: root.tr("logs"); iconName: "logs"
                        onClicked: djconnect.showLogs()
                    }
                    MoreMenuButton {
                        text: root.tr("about"); iconName: "info"
                        onClicked: root.aboutOpen = true
                    }
                    MoreMenuButton {
                        objectName: "openLegal"
                        text: root.tr("legal"); iconName: "document"
                        onClicked: root.activeScreen = "legal"
                    }
                    MoreMenuButton {
                        objectName: "openPrivacy"
                        text: root.tr("privacy"); iconName: "privacy"
                        onClicked: root.activeScreen = "privacy"
                    }
                    MoreMenuButton {
                        objectName: "openFeedback"
                        text: root.tr("feedback"); iconName: "chat"
                        onClicked: root.activeScreen = "feedback"
                    }
                }
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        visible: root.activeScreen === "legal" || root.activeScreen === "privacy" || root.activeScreen === "feedback"
        color: BrandTheme.colors.background
        z: 17
        AppBackground { sessionCanvas: true }
        ModalBlocker {}
        InformationPage {
            objectName: "informationPage"
            anchors.fill: parent
            anchors.bottomMargin: root.edge + 126
            privacy: root.activeScreen === "privacy"
            feedback: root.activeScreen === "feedback"
            backend: djconnect
            onBack: root.activeScreen = "more"
        }
    }

    Rectangle {
        id: trackInsightPanel
        objectName: "trackInsightPanel"
        property string visualMood: "groove"
        readonly property bool hasLiveSession: {
            const session = djconnect.djSession.state
            return !!session.session_id && ["opening", "active", "ending"].includes(session.runtime_state)
        }
        readonly property bool canChooseVisualMood: visible && root.active && !root.screenBlanked && !hasLiveSession
        onCanChooseVisualMoodChanged: if (!canChooseVisualMood) trackInsightMoodPopup.close()
        property bool autoInsightRequested: false
        anchors.fill: parent
        color: BrandTheme.colors.background
        visible: root.activeScreen === "trackinsight"
        z: 17
        onVisibleChanged: {
            if (visible && !autoInsightRequested && (djconnect.playing || djconnect.demoMode)) {
                autoInsightRequested = true
                djconnect.openTrackInsight()
            } else if (!visible) {
                autoInsightRequested = false
            }
        }

        AppBackground { sessionCanvas: true }
        ModalBlocker {}

        ColumnLayout {
            anchors.fill: parent
            anchors.leftMargin: 20
            anchors.topMargin: 20
            anchors.rightMargin: 20
            anchors.bottomMargin: root.edge + 126
            spacing: 12

            PageToolbar {
                title: root.tr("track_insight")
                showLeading: !trackInsightPanel.hasLiveSession
                leading: [
                    GlassButton {
                        id: trackInsightMoodButton
                        objectName: "trackInsightVisualMoodToggle"
                        iconName: "mood_" + trackInsightPanel.visualMood
                        tertiary: true
                        implicitWidth: 52
                        enabled: trackInsightPanel.canChooseVisualMood
                        Accessible.name: root.tr("shared_field_mood")
                        Accessible.description: root.tr("shared_mood_" + trackInsightPanel.visualMood)
                        onClicked: {
                            if (!trackInsightPanel.canChooseVisualMood)
                                return
                            const anchor = trackInsightMoodButton.mapToItem(trackInsightPanel, 0, trackInsightMoodButton.height)
                            trackInsightMoodPopup.x = Math.max(12, Math.min(anchor.x,
                                trackInsightPanel.width - trackInsightMoodPopup.width - 12))
                            trackInsightMoodPopup.y = anchor.y + 8
                            trackInsightMoodPopup.open()
                        }
                    }
                ]
                showConnection: true
                connectionLabel: root.tr("connection_type")
                connectionText: djconnect.connectionType
                Layout.fillWidth: true

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

            ScrollView {
                id: trackInsightScroll
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                contentWidth: availableWidth

                ColumnLayout {
                    width: Math.max(0, trackInsightScroll.availableWidth)
                    spacing: root.wallProfile ? 18 : 10

                    Text {
                        visible: djconnect.trackInsightError.length > 0
                        text: djconnect.trackInsightError
                        textFormat: Text.PlainText
                        color: BrandTheme.colors.muted
                        font.pixelSize: 20
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }

                    IntroductionCard {
                        objectName: "trackInsightEmptyHero"
                        compact: root.width < 900
                        iconName: "trackInsight"
                        title: root.tr("track_insight")
                        message: root.tr("track_insight_empty")
                        visible: djconnect.trackInsightError.length === 0 && djconnect.trackInsightText.length === 0
                                 && djconnect.trackInsightItems.length === 0 && djconnect.trackInsightSections.length === 0
                                 && !trackInsightSubject.visible && !trackInsightVisualizer.visible && !djconnect.askDjBusy
                    }

                    GlassCard {
                        id: trackInsightSubject
                        objectName: "trackInsightSubjectHero"
                        hero: true
                        artworkTint: trackInsightArtworkFrame.artworkTint
                        visible: djconnect.trackInsightTitle.length > 0 || djconnect.trackInsightArtist.length > 0 || djconnect.trackInsightImageUrl.length > 0
                        Layout.fillWidth: true
                        padding: root.wallProfile ? 32 : 12
                        background: GlassSurface {
                            hero: true
                            artworkTint: trackInsightArtworkFrame.artworkTint
                            border.color: root.moodColor("focus")
                            radius: root.wallProfile ? 44 : 28
                        }

                        GridLayout {
                            Layout.fillWidth: true
                            columns: root.wallProfile ? 1 : 2
                            rowSpacing: 18
                            columnSpacing: 12

                            GlassArtworkFrame {
                                id: trackInsightArtworkFrame
                                objectName: "trackInsightArtworkFrame"
                                backend: djconnect; imageItem: trackInsightArtworkImage
                                active: !root.screenBlanked
                                leaseKey: djconnect.activeProfileId + "|" + djconnect.trackInsightTitle + "|" + djconnect.trackInsightArtist
                                visible: djconnect.trackInsightImageUrl.length > 0
                                Layout.alignment: Qt.AlignHCenter
                                Layout.preferredWidth: root.wallProfile ? 228 : 76
                                Layout.preferredHeight: Layout.preferredWidth
                                radius: root.wallProfile ? 32 : 16
                                Image {
                                    id: trackInsightArtworkImage
                                    source: djconnect.trackInsightImageUrl
                                    visible: source.toString().length > 0
                                    anchors.fill: parent
                                    fillMode: Image.PreserveAspectCrop
                                    smooth: true
                                }

                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 4

                                Text {
                                    text: djconnect.trackInsightTitle
                                    textFormat: Text.PlainText
                                    color: BrandTheme.colors.text
                                    font.pixelSize: root.wallProfile ? 32 : 22
                                    font.bold: true
                                    horizontalAlignment: root.wallProfile ? Text.AlignHCenter : Text.AlignLeft
                                    wrapMode: Text.Wrap
                                    Layout.fillWidth: true
                                }

                                Text {
                                    text: [djconnect.trackInsightArtist, djconnect.trackInsightAlbum].filter(function(v) { return v && v.length > 0 }).join(" · ")
                                    color: BrandTheme.colors.muted
                                    font.pixelSize: root.wallProfile ? 21 : 17
                                    textFormat: Text.PlainText
                                    horizontalAlignment: root.wallProfile ? Text.AlignHCenter : Text.AlignLeft
                                    wrapMode: Text.Wrap
                                    Layout.fillWidth: true
                                }
                            }
                        }
                    }

                    GlassSurface {
                        border.color: root.moodColor("focus")
                        id: trackInsightVisualizer
                        visible: djconnect.trackInsightVisualizer.available === true
                        Layout.fillWidth: true
                        Layout.preferredHeight: 164
                        radius: root.standardButtonRadius
                        clip: true

                        property var visualizerData: djconnect.trackInsightVisualizer
                        property real phase: 0

                        onVisibleChanged: trackInsightVisualizerCanvas.requestPaint()
                        onVisualizerDataChanged: {
                            phase = 0
                            trackInsightVisualizerCanvas.requestPaint()
                        }

                        Timer {
                            interval: 180
                            repeat: true
                            running: root.wallProfile && trackInsightVisualizer.visible && root.activeScreen === "trackinsight"
                                     && djconnect.playing && root.active && !root.screenBlanked && !GlassStyle.reduceMotion
                            onTriggered: {
                                trackInsightVisualizer.phase = (trackInsightVisualizer.phase + 0.08) % 6.28
                                trackInsightVisualizerCanvas.requestPaint()
                            }
                        }

                        Canvas {
                            id: trackInsightVisualizerCanvas
                            anchors.fill: parent
                            antialiasing: true
                            onPaint: {
                                var ctx = getContext("2d")
                                ctx.clearRect(0, 0, width, height)
                                var data = trackInsightVisualizer.visualizerData || {}
                                var bars = data.bars || []
                                var colors = data.colors || []
                                var c0 = colors.length > 0 ? colors[0] : root.moodColor("gradientStart")
                                var c1 = colors.length > 1 ? colors[1] : root.moodColor("gradientMid")
                                var c2 = colors.length > 2 ? colors[2] : root.moodColor("gradientEnd")
                                var bg = ctx.createLinearGradient(0, 0, width, height)
                                bg.addColorStop(0.0, c0)
                                bg.addColorStop(0.58, c1)
                                bg.addColorStop(1.0, c2)
                                ctx.globalAlpha = 0.28
                                ctx.fillStyle = bg
                                ctx.fillRect(0, 0, width, height)
                                ctx.globalAlpha = 1

                                ctx.fillStyle = "rgba(5, 8, 18, 0.34)"
                                ctx.fillRect(0, 0, width, height)

                                var orbGradient = ctx.createRadialGradient(width * 0.55, height * 0.45, 4, width * 0.55, height * 0.45, Math.max(width, height) * 0.56)
                                orbGradient.addColorStop(0, c1)
                                orbGradient.addColorStop(0.42, "rgba(255,255,255,0.16)")
                                orbGradient.addColorStop(1, "rgba(0,0,0,0)")
                                ctx.globalAlpha = 0.42
                                ctx.fillStyle = orbGradient
                                ctx.fillRect(0, 0, width, height)
                                ctx.globalAlpha = 1

                                ctx.strokeStyle = "rgba(255,255,255,0.16)"
                                ctx.lineWidth = 1
                                for (var line = 0; line < 5; line++) {
                                    var y = height * (0.22 + line * 0.13)
                                    ctx.beginPath()
                                    ctx.moveTo(width * 0.08, y)
                                    ctx.bezierCurveTo(width * 0.28, y - 20, width * 0.52, y + 20, width * 0.92, y - 8)
                                    ctx.stroke()
                                }

                                if (bars.length === 0) {
                                    return
                                }
                                var baseY = height - 18
                                var topY = 28
                                var availableHeight = Math.max(28, baseY - topY)
                                var count = Math.min(48, bars.length)
                                var gap = Math.max(3, width * 0.008)
                                var barWidth = Math.max(4, (width - 34 - gap * (count - 1)) / count)
                                var startX = (width - (barWidth * count + gap * (count - 1))) / 2
                                var barGradient = ctx.createLinearGradient(0, topY, 0, baseY)
                                barGradient.addColorStop(0.0, c2)
                                barGradient.addColorStop(0.52, c1)
                                barGradient.addColorStop(1.0, c0)
                                ctx.fillStyle = barGradient
                                for (var i = 0; i < count; i++) {
                                    var value = Math.max(0.08, Math.min(1, Number(bars[i]) || 0.1))
                                    var pulse = 0.88 + Math.sin(trackInsightVisualizer.phase + i * 0.45) * 0.08
                                    var h = Math.max(10, availableHeight * value * pulse)
                                    var x = startX + i * (barWidth + gap)
                                    var yBar = baseY - h
                                    ctx.fillRect(x, yBar, barWidth, h)
                                }
                                ctx.fillStyle = c2
                                ctx.shadowColor = c2
                                ctx.shadowBlur = 16
                                ctx.beginPath()
                                ctx.arc(width * 0.5, baseY, 8, 0, Math.PI * 2)
                                ctx.fill()
                                ctx.shadowBlur = 0
                            }
                        }
                    }

                    GlassCard {
                        objectName: "trackInsightAnalysisCard"
                        visible: djconnect.trackInsightText.length > 0
                        Layout.fillWidth: true

                        Text {
                            text: djconnect.trackInsightText
                            textFormat: Text.PlainText
                            color: BrandTheme.colors.text
                            font.pixelSize: 21
                            wrapMode: Text.Wrap
                            Layout.fillWidth: true
                        }
                    }

                    Flow {
                        visible: djconnect.trackInsightItems.length > 0
                        spacing: 8
                        Layout.fillWidth: true

                        Repeater {
                            model: djconnect.trackInsightItems

                            GlassSurface {
                                border.color: root.moodColor("focus")
                                width: Math.max(132, trackMetricContent.implicitWidth + 24)
                                height: 64
                                radius: root.standardButtonRadius

                                ColumnLayout {
                                    id: trackMetricContent
                                    anchors.fill: parent
                                    anchors.margins: 8
                                    spacing: 1

                                    Text {
                                        text: root.trackInsightLabel(modelData.title || modelData.kind || "")
                                        color: BrandTheme.colors.text
                                        font.pixelSize: 15
                                        font.bold: true
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }

                                    Text {
                                        text: modelData.value || ""
                                        color: BrandTheme.colors.muted
                                        font.pixelSize: 19
                                        font.bold: true
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }
                                }
                            }
                        }
                    }

                    Repeater {
                        model: djconnect.trackInsightSections

                        GlassSurface {
                            border.color: root.moodColor("focus")
                            Layout.fillWidth: true
                            Layout.preferredHeight: trackSectionContent.implicitHeight + 18
                            radius: root.standardButtonRadius

                            ColumnLayout {
                                id: trackSectionContent
                                anchors.fill: parent
                                anchors.margins: 9
                                spacing: 5

                                Text {
                                    text: root.trackInsightLabel(modelData.title || modelData.kind || modelData.id || "")
                                    color: BrandTheme.colors.muted
                                    font.pixelSize: 18
                                    font.bold: true
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }

                                Text {
                                    visible: modelData.body && modelData.body.length > 0
                                    text: modelData.body || ""
                                    color: BrandTheme.colors.text
                                    font.pixelSize: 17
                                    wrapMode: Text.WordWrap
                                    Layout.fillWidth: true
                                }

                                Repeater {
                                    model: modelData.details || []
                                    Text {
                                        text: "- " + modelData
                                        color: BrandTheme.colors.muted
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
        }
        GlassPopup {
            id: trackInsightMoodPopup
            objectName: "trackInsightVisualMoodPopup"
            width: Math.min(trackInsightPanel.width - 24, 440)
            padding: 18
            modal: true
            dim: false
            closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
            background: GlassSurface { popover: true; elevated: true }

            contentItem: ColumnLayout {
                spacing: 12
                Text {
                    text: root.tr("shared_field_mood")
                    color: BrandTheme.colors.text
                    font.pixelSize: 24
                    font.bold: true
                }
                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 8
                    rowSpacing: 8
                    Repeater {
                        model: ["chill", "groove", "energy", "party"]
                        GlassButton {
                            required property string modelData
                            objectName: "trackInsightVisualMood-" + modelData
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            iconName: "mood_" + modelData
                            text: root.tr("shared_mood_" + modelData)
                            checked: trackInsightPanel.visualMood === modelData
                            enabled: trackInsightPanel.canChooseVisualMood
                            onClicked: {
                                if (!trackInsightPanel.canChooseVisualMood)
                                    return
                                trackInsightPanel.visualMood = modelData
                                trackInsightMoodPopup.close()
                            }
                        }
                    }
                }
            }
        }
    }

    Rectangle {
        id: musicDiscoveryPanel
        anchors.fill: parent
        color: BrandTheme.colors.background
        visible: root.activeScreen === "discover"
        z: 17

        AppBackground { sessionCanvas: true }
        ModalBlocker {}

        ColumnLayout {
            anchors.fill: parent
            anchors.leftMargin: 20
            anchors.topMargin: root.wallProfile ? 32 : 10
            anchors.rightMargin: 20
            anchors.bottomMargin: root.edge + 126
            spacing: root.wallProfile ? 22 : 10

            PageToolbar {
                title: root.tr("music_discovery")
                Layout.preferredHeight: compact ? implicitHeight : 140
                showConnection: true
                connectionLabel: root.tr("connection_type")
                connectionText: djconnect.connectionType
                Layout.fillWidth: true

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

            IntroductionCard {
                objectName: "discoveryIntroduction"
                compact: root.width < 900
                iconName: "discover"
                title: root.tr("music_discovery")
                message: root.tr("music_discovery_introduction")
            }

            GlassSurface {
                visible: djconnect.musicDiscoveryConsentRejected
                Layout.fillWidth: true
                Layout.preferredHeight: consentColumn.implicitHeight + 28
                radius: root.standardButtonRadius

                ColumnLayout {
                    id: consentColumn
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 10

                    Text {
                        text: root.tr("music_discovery_requires_music_dna")
                        color: BrandTheme.colors.text
                        font.pixelSize: 21
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        PurpleButton {
                            text: root.tr("music_discovery_enable")
                            primary: true
                            enabled: !djconnect.musicDiscoveryBusy
                            font.pixelSize: 17
                            Layout.fillWidth: true
                            Layout.preferredHeight: 48
                            onClicked: root.openMusicDnaPrompt(true)
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

            GlassSurface {
                hero: true
                visible: !djconnect.musicDnaEnabled && djconnect.musicDiscoveryItems.length === 0
                         && djconnect.musicDiscoveryError.length === 0 && !djconnect.musicDiscoveryBusy
                         && !djconnect.musicDiscoveryConsentRejected
                Layout.fillWidth: true
                Layout.preferredHeight: discoveryMusicDnaDisabledColumn.implicitHeight + 28
                radius: root.standardButtonRadius

                ColumnLayout {
                    id: discoveryMusicDnaDisabledColumn
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 10

                    Text {
                        text: djconnect.musicDiscoveryEmptyText.length > 0 ? djconnect.musicDiscoveryEmptyText : root.tr("music_discovery_requires_music_dna")
                        color: BrandTheme.colors.text
                        font.pixelSize: 21
                        font.bold: true
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }

                    Text {
                        text: root.tr("music_dna_opt_in")
                        color: BrandTheme.colors.muted
                        font.pixelSize: 19
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }

                    PurpleButton {
                        text: root.tr("music_discovery_enable")
                        primary: true
                        enabled: !djconnect.musicDnaBusy && !djconnect.musicDiscoveryBusy
                        font.pixelSize: 19
                        Layout.fillWidth: true
                        Layout.preferredHeight: 52
                        onClicked: root.openMusicDnaPrompt(false)
                    }
                }
            }

            Text {
                visible: (djconnect.musicDnaEnabled || djconnect.musicDiscoveryError.length > 0)
                         && djconnect.musicDiscoveryItems.length === 0 && !djconnect.musicDiscoveryBusy
                         && !djconnect.musicDiscoveryConsentRejected
                textFormat: Text.PlainText
                text: djconnect.musicDiscoveryError.length > 0 ? djconnect.musicDiscoveryError : (djconnect.musicDiscoveryEmptyText.length > 0 ? djconnect.musicDiscoveryEmptyText : root.tr("music_discovery_empty"))
                color: BrandTheme.colors.muted
                font.pixelSize: 20
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                Layout.topMargin: root.wallProfile ? 12 : 4
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

                        GlassSurface {
                            Layout.fillWidth: true
                            property int inset: root.wallProfile ? 24 : 14
                            Layout.preferredHeight: discoveryResult.implicitHeight + 2 * inset
                            radius: root.wallProfile ? 34 : 22
                            clip: true
                            introduction: true
                            focused: discoveryTap.activeFocus

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
                                id: discoveryResult
                                anchors.fill: parent
                                anchors.margins: parent.inset
                                spacing: 14

                                GlassArtworkFrame {
                                    objectName: "discoveryArtworkFrame"
                                    backend: djconnect; imageItem: discoveryArtworkImage
                                    active: !root.screenBlanked
                                    leaseKey: djconnect.activeProfileId + "|" + (modelData.id || modelData.title || "")
                                    visible: !!modelData.imageUrl && modelData.imageUrl.length > 0
                                    Layout.preferredWidth: 112; Layout.preferredHeight: 112
                                    radius: 20
                                    Image {
                                        id: discoveryArtworkImage
                                        source: modelData.imageUrl && modelData.imageUrl.length > 0 ? modelData.imageUrl : ""
                                        visible: source.toString().length > 0
                                        anchors.fill: parent
                                        fillMode: Image.PreserveAspectCrop
                                        smooth: true
                                    }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    spacing: 4

                                    Text {
                                        visible: modelData.sectionTitle && modelData.sectionTitle.length > 0
                                        text: modelData.sectionTitle || ""
                                        color: BrandTheme.colors.muted
                                        font.pixelSize: 17
                                        font.bold: true
                                        elide: Text.ElideRight
                                        maximumLineCount: 1
                                        Layout.fillWidth: true
                                    }

                                    Text {
                                        text: modelData.title || ""
                                        textFormat: Text.PlainText
                                        color: BrandTheme.colors.text
                                        font.pixelSize: 25
                                        font.bold: true
                                        elide: Text.ElideRight
                                        maximumLineCount: 1
                                        Layout.fillWidth: true
                                    }

                                    Text {
                                        text: [modelData.kindLabel || "", modelData.subtitle || ""].filter(function(v) { return v && v.length > 0 }).join(" · ")
                                        color: BrandTheme.colors.muted
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
                                        color: BrandTheme.colors.muted
                                        font.pixelSize: 17
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 8

                                        PurpleButton {
                                            text: root.tr("play_now")
                                            primary: true
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
        color: BrandTheme.alpha(BrandTheme.colors.background, "f2")
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
                    color: BrandTheme.colors.text
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
                color: BrandTheme.colors.text
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
                    color: BrandTheme.colors.muted
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
        color: BrandTheme.colors.background
        visible: root.activeScreen === "musicdna"
        z: 17

        AppBackground { sessionCanvas: true }
        ModalBlocker {}

        ColumnLayout {
            anchors.fill: parent
            anchors.leftMargin: 24
            anchors.topMargin: 22
            anchors.rightMargin: 24
            anchors.bottomMargin: root.edge + 126
            spacing: 14

            PageToolbar {
                title: root.tr("music_dna")
                leading: [ GlassButton { iconName: "back"; tertiary: true; implicitWidth: 52; Accessible.name: root.tr("more"); onClicked: root.activeScreen = "more" } ]
                showConnection: true
                connectionLabel: root.tr("connection_type")
                connectionText: djconnect.connectionType
                Layout.fillWidth: true

                LoadingSpinner {
                    visible: djconnect.musicDnaBusy
                    running: visible
                    Layout.preferredWidth: 38
                    Layout.preferredHeight: 38
                }

                RefreshIconButton {
                    id: musicDnaRefreshButton
                    objectName: "musicDnaRefreshButton"
                    enabled: !djconnect.musicDnaBusy
                    onClicked: djconnect.refreshMusicDna()
                }
            }

            GlassCard {
                objectName: "musicDnaErrorCard"
                visible: djconnect.musicDnaError.length > 0
                Layout.fillWidth: true
                Text {
                    text: djconnect.musicDnaError
                    textFormat: Text.PlainText
                    color: BrandTheme.colors.text
                    font.pixelSize: 22
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }

            IntroductionCard {
                objectName: "musicDnaOptInHero"
                compact: root.width < 900
                iconName: "heart"
                title: root.tr("music_dna")
                message: root.tr("music_dna_opt_in")
                visible: !djconnect.musicDnaEnabled && djconnect.musicDnaError.length === 0

                PurpleButton {
                    text: root.tr("music_dna_enable")
                    primary: true
                    enabled: !djconnect.musicDnaBusy
                    font.pixelSize: 22
                    Layout.fillWidth: true
                    Layout.preferredHeight: 56
                    onClicked: root.openMusicDnaPrompt(false)
                }
            }

            GlassCard {
                objectName: "musicDnaSummaryHero"
                hero: true; padding: root.wallProfile ? 32 : 18
                visible: djconnect.musicDnaError.length === 0 && djconnect.musicDnaEnabled && djconnect.musicDnaSummary.length > 0
                Layout.fillWidth: true
                Layout.maximumHeight: implicitHeight
                Text {
                    visible: djconnect.musicDnaError.length === 0 && djconnect.musicDnaEnabled && djconnect.musicDnaSummary.length > 0
                    text: djconnect.musicDnaSummary
                    textFormat: Text.PlainText
                    color: BrandTheme.colors.text
                    font.pixelSize: 22
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }

            ScrollView {
                id: musicDnaScroll
                visible: djconnect.musicDnaError.length === 0 && djconnect.musicDnaEnabled
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

                        GlassCard {
                            Layout.fillWidth: true
                            padding: root.wallProfile ? 30 : 18
                            spacing: 8

                            Text {
                                text: modelData.title || ""
                                textFormat: Text.PlainText
                                color: BrandTheme.colors.text
                                font.pixelSize: 19
                                font.weight: Font.DemiBold
                                wrapMode: Text.Wrap
                                Layout.fillWidth: true
                            }

                            Repeater {
                                model: modelData.lines || []
                                Text {
                                    text: modelData
                                    textFormat: Text.PlainText
                                    color: BrandTheme.colors.muted
                                    font.pixelSize: 17
                                    wrapMode: Text.Wrap
                                    Layout.fillWidth: true
                                }
                            }
                        }
                    }
                }
            }
            Item {
                visible: !djconnect.musicDnaEnabled || djconnect.musicDnaError.length > 0
                Layout.fillWidth: true; Layout.fillHeight: true
            }
        }
    }

    Rectangle {
        id: askDjPanel
        objectName: "askDjPanel"
        anchors.fill: parent
        color: BrandTheme.colors.background
        visible: root.activeScreen === "askdj"
        z: 17
        property bool searchOpen: false
        property bool searchKeyboardOpen: false
        property int selectedMatch: -1
        property string selectedMessageId: ""
        readonly property var matches: {
            const query = searchText(askDjSearchInput.text.trim())
            const messages = djconnect.askDjMessages
            const results = []
            if (query) {
                for (let i = 0; i < messages.length; i++) {
                    if (searchText(messages[i].text || "").includes(query))
                        results.push({row: i, messageId: messages[i].id || ""})
                }
            }
            return results
        }
        readonly property int selectedRow: matches[selectedMatch] ? matches[selectedMatch].row : -1

        onVisibleChanged: if (!visible) closeSearch()
        onMatchesChanged: {
            if (!searchOpen)
                return
            const previous = selectedMessageId
                ? matches.findIndex(match => match.messageId === selectedMessageId) : -1
            selectMatch(previous >= 0 ? previous : Math.max(0, Math.min(selectedMatch, matches.length - 1)))
        }

        function searchText(value) {
            return String(value).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase()
        }

        function openSearch() {
            searchOpen = true
            searchKeyboardOpen = true
            askDjSearchInput.forceActiveFocus()
        }

        function closeSearch() {
            searchOpen = false
            searchKeyboardOpen = false
            selectedMatch = -1
            selectedMessageId = ""
            askDjSearchInput.clear()
        }

        function selectMatch(position) {
            const match = matches[position]
            selectedMatch = match ? position : -1
            selectedMessageId = match ? match.messageId : ""
        }

        function centerSelectedMatch() {
            const bubble = askDjMessagesRepeater.itemAt(selectedRow)
            const flickable = askDjScroll.contentItem
            if (!searchOpen || !bubble || !flickable)
                return
            const top = flickable.originY
            const maxY = top + Math.max(0, flickable.contentHeight - flickable.height)
            const bubbleTop = bubble.mapToItem(flickable.contentItem, 0, 0).y
            const targetY = bubbleTop - Math.max(0, flickable.height - bubble.height) / 2
            flickable.contentY = Math.min(maxY, Math.max(top, targetY))
        }

        function startSearchAtFirstMatch() {
            selectMatch(0)
            Qt.callLater(centerSelectedMatch)
        }

        function dismissSearchKeyboard() {
            searchKeyboardOpen = false
            Qt.callLater(centerSelectedMatch)
        }

        function moveMatch(offset) {
            if (!matches.length)
                return
            selectMatch((selectedMatch + offset + matches.length) % matches.length)
            centerSelectedMatch()
        }

        AppBackground { sessionCanvas: true }
        ModalBlocker {}

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            anchors.bottomMargin: 130
            spacing: 10

            PageToolbar {
                title: root.tr("ask_dj")
                showConnection: true
                connectionLabel: root.tr("connection_type")
                connectionText: djconnect.connectionType
                Layout.fillWidth: true

                BusyIndicator {
                    running: djconnect.askDjBusy
                    visible: djconnect.askDjBusy
                    implicitWidth: 30
                    implicitHeight: 30
                }

                GlassButton {
                    objectName: "askDjSearchToggle"
                    iconName: "search"
                    tertiary: true
                    checkable: true
                    checked: askDjPanel.searchOpen
                    enabled: askDjPanel.searchOpen || djconnect.askDjMessages.length > 0
                    Accessible.name: root.tr("ask_dj_search_history")
                    onClicked: askDjPanel.searchOpen ? askDjPanel.closeSearch() : askDjPanel.openSearch()
                }

                RefreshIconButton {
                    id: askDjRefreshButton
                    enabled: !djconnect.askDjBusy
                    onClicked: djconnect.refreshAskDjHistory()
                }

                leading: [
                GlassButton { iconName: "back"; tertiary: true; implicitWidth: 52; Accessible.name: root.tr("more"); onClicked: root.activeScreen = "more" },
                Button {
                    id: askDjClearButton
                    enabled: !djconnect.askDjBusy && djconnect.askDjMessages.length > 0
                    ToolTip.visible: hovered
                    ToolTip.text: root.tr("ask_dj_clear_chat")
                    Accessible.name: root.tr("ask_dj_clear_chat")
                    Layout.preferredWidth: 48
                    Layout.preferredHeight: 48
                    onClicked: root.askDjClearConfirmOpen = true
                    contentItem: MenuIcon {
                        iconName: "trash"
                        iconColor: askDjClearButton.enabled ? BrandTheme.colors.text : BrandTheme.colors.disabledText
                        strokeWidth: 2.5
                        anchors.centerIn: parent
                        width: 28
                        height: 28
                    }
                    background: Rectangle {
                        radius: root.standardButtonRadius
                        color: askDjClearButton.down ? BrandTheme.colors.dangerPressed : (askDjClearButton.enabled ? BrandTheme.colors.dangerSurface : root.moodDisabledColor("start"))
                        border.color: askDjClearButton.hovered ? BrandTheme.colors.danger : (askDjClearButton.enabled ? BrandTheme.colors.danger : root.moodDisabledColor("mid"))
                        border.width: 1
                        opacity: askDjClearButton.enabled ? 1.0 : 0.62
                    }
                }
                ]

            }

            Control {
                visible: askDjPanel.searchOpen
                Layout.fillWidth: true
                padding: 5
                background: GlassSurface { radius: 24; interactive: true; focused: askDjSearchInput.activeFocus }
                contentItem: RowLayout {
                    spacing: 4
                    TextField {
                        id: askDjSearchInput
                        objectName: "askDjSearchInput"
                        Layout.fillWidth: true
                        Layout.minimumHeight: 48
                        background: Item {}
                        placeholderText: root.tr("ask_dj_search_history")
                        Accessible.name: placeholderText
                        font.pixelSize: root.width < 900 ? 18 : 22
                        maximumLength: 120
                        selectByMouse: true
                        TapHandler { onTapped: askDjPanel.searchKeyboardOpen = true }
                        onTextEdited: askDjPanel.startSearchAtFirstMatch()
                        onAccepted: {
                            if (askDjPanel.searchKeyboardOpen)
                                askDjPanel.dismissSearchKeyboard()
                            else
                                askDjPanel.moveMatch(1)
                        }
                        Keys.onEscapePressed: {
                            if (askDjPanel.searchKeyboardOpen)
                                askDjPanel.dismissSearchKeyboard()
                            else
                                askDjPanel.closeSearch()
                        }
                    }
                    Text {
                        objectName: "askDjSearchCount"
                        visible: askDjSearchInput.text.trim().length > 0
                        text: (askDjPanel.selectedMatch + 1) + "/" + askDjPanel.matches.length
                        color: BrandTheme.colors.muted
                        font.pixelSize: root.width < 900 ? 14 : 18
                    }
                    GlassButton {
                        objectName: "askDjPreviousMatch"
                        iconName: "arrow_up"; tertiary: true
                        Accessible.name: root.tr("logs_previous_match")
                        enabled: askDjPanel.matches.length > 0
                        onClicked: askDjPanel.moveMatch(-1)
                    }
                    GlassButton {
                        objectName: "askDjNextMatch"
                        iconName: "arrow_down"; tertiary: true
                        Accessible.name: root.tr("logs_next_match")
                        enabled: askDjPanel.matches.length > 0
                        onClicked: askDjPanel.moveMatch(1)
                    }
                    GlassButton {
                        objectName: "askDjSearchClose"
                        iconName: "end"; tertiary: true; Accessible.name: root.tr("close")
                        onClicked: askDjPanel.closeSearch()
                    }
                }
            }

            ScrollView {
                id: askDjScroll
                objectName: "askDjScroll"
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                contentWidth: availableWidth

                ColumnLayout {
                    width: Math.max(0, askDjScroll.availableWidth)
                    spacing: 10

                    IntroductionCard {
                        objectName: "askDjIntroduction"
                        compact: root.width < 900
                        iconName: "chat"
                        title: root.tr("ask_dj")
                        message: root.tr("ask_dj_introduction")
                    }

                    Text {
                        text: root.tr("ask_dj_empty")
                        visible: djconnect.askDjMessages.length === 0
                        color: BrandTheme.colors.muted
                        font.pixelSize: 24
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                        Layout.topMargin: 36
                    }

                    Repeater {
                        id: askDjMessagesRepeater
                        model: djconnect.askDjMessages

                        GlassSurface {
                            border.color: root.moodColor("focus")
                            focused: askDjPanel.searchOpen && askDjPanel.selectedRow === index
                            property bool userBubble: modelData.role === "user"
                            property bool systemBubble: modelData.role === "system" || modelData.role === "status" || modelData.messageKind === "system" || modelData.messageKind === "status"

                            Layout.preferredWidth: userBubble ? Math.min(askDjScroll.availableWidth * 0.78, 520) : askDjScroll.availableWidth
                            Layout.alignment: userBubble ? Qt.AlignRight : Qt.AlignLeft
                            property int bubblePadding: root.wallProfile ? 24 : 14
                            implicitHeight: askDjBubbleContent.implicitHeight + 2 * bubblePadding
                            radius: root.wallProfile ? 34 : 22
                            introduction: !userBubble

                            selected: userBubble

                            ColumnLayout {
                                id: askDjBubbleContent
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.margins: bubblePadding
                                spacing: 8

                                Text {
                                    text: modelData.displayTime || ""
                                    visible: modelData.displayTime && modelData.displayTime.length > 0
                                    color: systemBubble ? BrandTheme.colors.muted : (userBubble ? BrandTheme.colors.muted : BrandTheme.colors.purple)
                                    opacity: 0.82
                                    font.pixelSize: 14
                                    font.bold: false
                                    horizontalAlignment: userBubble ? Text.AlignRight : Text.AlignLeft
                                    Layout.fillWidth: true
                                }

                                Text {
                                    text: modelData.text
                                    textFormat: Text.PlainText
                                    color: BrandTheme.colors.text
                                    font.pixelSize: systemBubble ? 19 : 22
                                    font.weight: Font.Normal
                                    wrapMode: Text.Wrap
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
                                        color: BrandTheme.alpha(BrandTheme.colors.surface, "33")
                                        border.color: root.moodColor("focus")
                                        border.width: 1

                                        Text {
                                            id: trackInsightModeLabel
                                            anchors.centerIn: parent
                                            text: root.tr("music_dna_match") + " " + (modelData.musicDnaMatch || "")
                                            color: BrandTheme.colors.cyan
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
                                            color: BrandTheme.colors.surface
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

                                        GlassSurface {
                                            border.color: root.moodColor("focus")
                                            width: Math.min(askDjScroll.availableWidth, Math.max(132, trackInsightMetricContent.implicitWidth + 24))
                                            height: 58
                                            radius: 8
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
                                                        color: BrandTheme.colors.muted
                                                        font.pixelSize: 14
                                                        font.bold: true
                                                        elide: Text.ElideRight
                                                        maximumLineCount: 1
                                                        Layout.fillWidth: true
                                                    }

                                                    Text {
                                                        text: modelData.value || ""
                                                        color: BrandTheme.colors.text
                                                        font.pixelSize: 18
                                                        font.bold: true
                                                        elide: Text.ElideRight
                                                        maximumLineCount: 1
                                                    }
                                                }

                                                Text {
                                                    text: [modelData.source || "", modelData.confidence || ""].filter(function(value) { return value.length > 0 }).join(" · ")
                                                    color: BrandTheme.colors.muted
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

                                        GlassSurface {
                                            border.color: root.moodColor("focus")
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: trackInsightSectionContent.implicitHeight + 16
                                            radius: 8

                                            ColumnLayout {
                                                id: trackInsightSectionContent
                                                anchors.left: parent.left
                                                anchors.right: parent.right
                                                anchors.top: parent.top
                                                anchors.margins: 8
                                                spacing: 3

                                                Text {
                                                    text: root.trackInsightLabel(modelData.title || modelData.id || modelData.kind || "")
                                                    color: modelData.metadataContext ? BrandTheme.colors.cyan : BrandTheme.colors.text
                                                    font.pixelSize: 16
                                                    font.bold: true
                                                    elide: Text.ElideRight
                                                    maximumLineCount: 1
                                                    Layout.fillWidth: true
                                                }

                                                Text {
                                                    text: modelData.body || ""
                                                    color: BrandTheme.colors.muted
                                                    font.pixelSize: 14
                                                    wrapMode: Text.WordWrap
                                                    visible: text.length > 0
                                                    Layout.fillWidth: true
                                                }

                                                Repeater {
                                                    model: modelData.details || []

                                                    Text {
                                                        text: "• " + modelData
                                                        color: BrandTheme.colors.muted
                                                        font.pixelSize: 13
                                                        wrapMode: Text.WordWrap
                                                        Layout.fillWidth: true
                                                    }
                                                }

                                                Text {
                                                    text: [modelData.source || "", modelData.confidence || ""].filter(function(value) { return value.length > 0 }).join(" · ")
                                                    color: BrandTheme.colors.muted
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
                                                color: BrandTheme.colors.cyan
                                                font.pixelSize: 13
                                                font.bold: true
                                                Layout.preferredWidth: 86
                                                visible: text.length > 0
                                            }

                                            Text {
                                                text: modelData.label || modelData.kind || modelData.id || ""
                                                color: BrandTheme.colors.text
                                                font.pixelSize: 14
                                                elide: Text.ElideRight
                                                maximumLineCount: 1
                                                Layout.fillWidth: true
                                            }

                                            Text {
                                                text: [modelData.source || "", modelData.confidence || ""].filter(function(value) { return value.length > 0 }).join(" · ")
                                                color: BrandTheme.colors.muted
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
                                        color: BrandTheme.colors.cyan
                                        font.pixelSize: 13
                                        font.bold: true
                                        Layout.fillWidth: true
                                    }

                                    Repeater {
                                        model: modelData.analysis && modelData.analysis.metadata && modelData.analysis.metadata.details ? modelData.analysis.metadata.details : []

                                        Text {
                                            text: "• " + modelData
                                            color: BrandTheme.colors.muted
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
                                            color: BrandTheme.colors.muted
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

                                        GlassSurface {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 70
                                            radius: 8
                                            clip: true

                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.margins: 8
                                                spacing: 10

                                                Rectangle {
                                                    Layout.preferredWidth: 54
                                                    Layout.preferredHeight: 54
                                                    radius: 8
                                                    color: BrandTheme.colors.surface
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
                                                        color: BrandTheme.colors.muted
                                                        font.pixelSize: 24
                                                        font.bold: true
                                                    }
                                                }

                                                ColumnLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 2

                                                    Text {
                                                        text: modelData.title || ""
                                                        color: BrandTheme.colors.text
                                                        font.pixelSize: 17
                                                        font.bold: true
                                                        elide: Text.ElideRight
                                                        maximumLineCount: 1
                                                        Layout.fillWidth: true
                                                    }

                                                    Text {
                                                        text: modelData.subtitle || ""
                                                        color: BrandTheme.colors.muted
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
                                                    color: BrandTheme.colors.muted
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
                                        color: BrandTheme.colors.muted
                                        font.pixelSize: 13
                                        font.bold: true
                                        Layout.fillWidth: true
                                    }

                                    Repeater {
                                        model: modelData.analysis && modelData.analysis.limitations ? modelData.analysis.limitations : []

                                        Text {
                                            text: "• " + (modelData.text || modelData)
                                            color: BrandTheme.colors.muted
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
                                        color: BrandTheme.colors.muted
                                        font.pixelSize: 13
                                        font.bold: true
                                        Layout.fillWidth: true
                                    }

                                    Repeater {
                                        model: modelData.analysis && modelData.analysis.providers ? modelData.analysis.providers : []

                                        Text {
                                            text: "• " + [modelData.label || modelData.providerId || root.tr("unknown"), modelData.status || root.tr("unknown"), modelData.reason || ""].filter(function(value) { return value.length > 0 }).join(" · ")
                                            color: BrandTheme.colors.muted
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
                                        color: BrandTheme.colors.muted
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
                                                color: BrandTheme.colors.cyan
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

                                Text {
                                    visible: modelData.announcementDelivery && modelData.announcementDelivery.length > 0
                                    text: modelData.announcementDelivery === "ha_speaker"
                                        ? root.tr("dj_announcement_delivered_ha_speaker") + " " + (modelData.announcementTargetName || root.tr("home_assistant"))
                                        : root.tr("dj_announcement_text_only")
                                    color: BrandTheme.colors.cyan
                                    font.pixelSize: 14
                                    font.bold: true
                                    wrapMode: Text.WordWrap
                                    Layout.fillWidth: true
                                }

                                Repeater {
                                    model: modelData.announcementWarnings || []

                                    Text {
                                        text: modelData
                                        color: BrandTheme.colors.warning
                                        font.pixelSize: 13
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                }

                                ColumnLayout {
                                    visible: modelData.actions && modelData.actions.length > 0
                                    Layout.fillWidth: true
                                    spacing: 8

                                    Repeater {
                                        model: modelData.actions || []

                                        GlassSurface {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: (modelData.isMedia || modelData.isOutput) ? 88 : 50
                                            radius: 8
                                            clip: true

                                            tertiary: !modelData.isMedia && !modelData.isOutput

                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.margins: (modelData.isMedia || modelData.isOutput) ? 10 : 0
                                                spacing: 12

                                                Rectangle {
                                                    visible: modelData.isMedia || modelData.isOutput
                                                    Layout.preferredWidth: 68
                                                    Layout.preferredHeight: 68
                                                    radius: 8
                                                    color: BrandTheme.colors.surface
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
                                                        color: BrandTheme.colors.muted
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
                                                        color: BrandTheme.colors.text
                                                        font.pixelSize: 18
                                                        font.bold: true
                                                        elide: Text.ElideRight
                                                        maximumLineCount: 1
                                                        Layout.fillWidth: true
                                                    }

                                                    Text {
                                                        text: modelData.subtitle || ""
                                                        color: BrandTheme.colors.muted
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
                                                            color: BrandTheme.colors.text
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
                                                                ctx.fillStyle = BrandTheme.colors.text
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
                                                            color: BrandTheme.colors.text
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

            SearchKeyboardDock {
                visible: askDjPanel.searchOpen && askDjPanel.searchKeyboardOpen
                Layout.fillWidth: true
                backend: djconnect
                target: askDjSearchInput
                keyboardName: "askDjHistorySearchKeyboard"
                onEdited: askDjPanel.startSearchAtFirstMatch()
                onSubmitted: askDjPanel.dismissSearchKeyboard()
                onDismissed: askDjPanel.dismissSearchKeyboard()
            }
        }

    }

    Item {
        anchors.fill: parent
        visible: root.activeScreen === "session" || root.activeScreen === "history" || root.activeScreen === "session-history"
        z: 17
        AppBackground { sessionCanvas: root.activeScreen === "session" }
        SessionScreen {
            id: sharedSessionScreen
            anchors.fill: parent
            backend: djconnect
            pollingAllowed: root.active && !root.screenBlanked && !root.splashVisible && !vibeScapeLoader.active
                && !djconnect.logsVisible && !djconnect.versionMismatchVisible
            historical: root.activeScreen === "history" || root.activeScreen === "session-history"
            currentHistory: root.activeScreen === "session-history"
            onExpandTrackArtwork: root.openTrackArtwork()
            onOpenVibeScape: function(pickerTop) { root.openVibeScape(pickerTop) }
            onNavigate: function(destination) { root.activeScreen = destination }
        }
    }

    GamesPanel {
        id: gamesPanel
        anchors.fill: parent
        visible: gamesOpen
        z: 18
        onCloseRequested: root.activeScreen = "more"
    }

    GlassSurface {
        id: bottomNav
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 20
        width: Math.min(parent.width - 40, 760)
        height: 92
        radius: height / 2
        color: BrandTheme.alpha(BrandTheme.colors.surface, "dd")
        border.color: BrandTheme.colors.surfaceRaised
        border.width: 1
        visible: !root.splashVisible && (djconnect.paired || djconnect.demoMode) && !djconnect.logsVisible && !djconnect.versionMismatchVisible
            && !queuePanel.keyboardOpen && !playlistsPanel.keyboardOpen
        z: 25

        RowLayout {
            anchors.fill: parent
            anchors.margins: 6
            spacing: 2
            Repeater {
                model: [
                    {screen: "session", key: "session_title", icon: "session"},
                    {screen: "queue", key: "queue", icon: "queue"},
                    {screen: "trackinsight", key: "track_insight", icon: "trackInsight"},
                    {screen: "discover", key: "music_discovery", icon: "discover"},
                    {screen: "more", key: "more", icon: "more"}
                ]
                NavButton {
                    required property var modelData
                    text: root.tr(modelData.key)
                    objectName: "appTab-" + modelData.screen
                    iconName: modelData.icon
                    checkable: true
                    checked: root.aboutOpen ? modelData.screen === "more" : root.activeScreen === modelData.screen || (modelData.screen === "session" && root.activeScreen === "session-history") || (modelData.screen === "more" && ["askdj", "history", "playlists", "games", "settings", "musicdna", "legal", "privacy", "feedback"].indexOf(root.activeScreen) >= 0)
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    onClicked: {
                        root.aboutOpen = false
                        root.activeScreen = modelData.screen
                        if (modelData.screen === "queue") djconnect.loadQueue()
                    }
                }
            }
        }
    }

    Rectangle {
        id: pairingPanel
        anchors.fill: parent
        color: BrandTheme.colors.background
        visible: !root.splashVisible && !djconnect.paired && !djconnect.demoMode
        z: 30

        AppBackground {}
        ModalBlocker {}

        ColumnLayout {
            anchors.centerIn: parent
            width: Math.min(parent.width - 40, 640)
            spacing: 14

            AppBanner { detailText: root.tr("tagline") }

            Text {
                text: root.tr("pairing_screen_title")
                color: BrandTheme.colors.muted
                font.pixelSize: 38
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
            }

            Text {
                text: root.tr("pairing_hint")
                color: BrandTheme.colors.muted
                font.pixelSize: 20
                font.bold: true
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 76
                radius: root.liquidGlassEnabled ? 16 : 8
                color: root.liquidGlassEnabled ? BrandTheme.alpha(BrandTheme.colors.surface, "70") : BrandTheme.alpha(BrandTheme.colors.surface, "55")
                border.width: root.liquidGlassEnabled ? 1 : 0
                border.color: "#48ffffff"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 3

                    Text {
                        text: root.tr("home_assistant")
                        color: BrandTheme.colors.muted
                        font.pixelSize: 17
                        font.bold: true
                        Layout.fillWidth: true
                    }

                    Text {
                        text: djconnect.haUrl.length ? djconnect.haUrl : "http://homeassistant.local:8123"
                        color: BrandTheme.colors.text
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
                radius: root.liquidGlassEnabled ? 16 : 8
                color: root.liquidGlassEnabled ? BrandTheme.alpha(BrandTheme.colors.surface, "70") : BrandTheme.alpha(BrandTheme.colors.surface, "55")
                border.width: root.liquidGlassEnabled ? 1 : 0
                border.color: "#48ffffff"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 4

                    Text {
                        text: root.tr("pairing_code")
                        color: BrandTheme.colors.muted
                        font.pixelSize: 18
                        font.bold: true
                        Layout.fillWidth: true
                    }

                    Text {
                        text: djconnect.pairingCode
                        color: BrandTheme.colors.text
                        font.pixelSize: 36
                        font.bold: true
                        Layout.fillWidth: true
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 76
                radius: root.liquidGlassEnabled ? 16 : 8
                color: root.liquidGlassEnabled ? BrandTheme.alpha(BrandTheme.colors.surface, "70") : BrandTheme.alpha(BrandTheme.colors.surface, "55")
                border.width: root.liquidGlassEnabled ? 1 : 0
                border.color: "#48ffffff"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 3

                    Text {
                        text: root.tr("client_api_url")
                        color: BrandTheme.colors.muted
                        font.pixelSize: 17
                        font.bold: true
                        Layout.fillWidth: true
                    }

                    Text {
                        text: djconnect.localApiUrl
                        color: BrandTheme.colors.text
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
                radius: root.liquidGlassEnabled ? 16 : 8
                color: root.liquidGlassEnabled ? BrandTheme.alpha(BrandTheme.colors.surface, "70") : root.moodColor("chip")
                border.width: root.liquidGlassEnabled ? 1 : 0
                border.color: "#48ffffff"

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
                        color: BrandTheme.colors.text
                        font.pixelSize: 22
                        font.bold: true
                        Layout.fillWidth: true
                    }
                }
            }

            PurpleButton {
                id: startDemoButton
                primary: true
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
                                ctx.strokeStyle = BrandTheme.colors.text
                                ctx.fillStyle = BrandTheme.colors.text
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
                        color: startDemoButton.enabled ? BrandTheme.colors.text : BrandTheme.colors.disabledText
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
        color: BrandTheme.colors.background
        visible: !root.splashVisible && djconnect.pairingSuccessVisible
        z: 34

        AppBackground {}
        ModalBlocker {}

        ColumnLayout {
            anchors.centerIn: parent
            width: Math.min(parent.width - 40, 640)
            spacing: 28

            AppBanner { detailText: root.tr("tagline") }

            Rectangle {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: 132
                Layout.preferredHeight: 132
                radius: 66
                color: BrandTheme.colors.success

                Canvas {
                    anchors.fill: parent
                    antialiasing: true
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.clearRect(0, 0, width, height)
                        ctx.strokeStyle = BrandTheme.colors.surface
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
                    color: BrandTheme.colors.text
                    font.pixelSize: 38
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                }

                Text {
                    text: root.tr("pairing_success_message")
                    color: BrandTheme.colors.muted
                    font.pixelSize: 20
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                }
            }

            PurpleButton {
                text: root.tr("start")
                primary: true
                font.pixelSize: 24
                Layout.fillWidth: true
                Layout.preferredHeight: 58
                onClicked: {
                    root.activeScreen = "session"
                    djconnect.startAfterPairing()
                }
            }
        }
    }

    Item {
        id: splashPanel
        objectName: "launchSplash"
        anchors.fill: parent
        opacity: root.splashVisible ? 1 : 0
        visible: opacity > 0
        z: 40
        readonly property bool animate: root.splashVisible && root.active && GlassStyle.awake && !GlassStyle.reduceMotion

        Behavior on opacity {
            NumberAnimation { duration: GlassStyle.reduceMotion ? 0 : root.motionStandard; easing.type: Easing.OutCubic }
        }

        SessionMoodCanvas { anchors.fill: parent; mood: ""; activeSession: false }
        ModalBlocker {}

        GlassCard {
            id: launchCard
            objectName: "launchCard"
            anchors.centerIn: parent
            width: Math.min(parent.width - 48, root.wallProfile ? 560 : 430)
            height: implicitHeight
            padding: root.wallProfile ? 30 : 23
            spacing: root.wallProfile ? 24 : 17
            background: GlassSurface { introduction: true; radius: root.wallProfile ? 48 : 34 }

            AppBanner {
                detailText: root.tr("tagline")
                showCardBackground: false
                compact: !root.wallProfile
            }
            SessionWelcomeArtwork {
                objectName: "launchVinylArtwork"
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: Math.min(launchCard.availableWidth, root.wallProfile ? 360 : 240)
                Layout.preferredHeight: Layout.preferredWidth
                animate: splashPanel.animate
            }
            Text {
                objectName: "launchVersion"
                text: "v" + djconnect.version
                color: BrandTheme.colors.muted
                font.pixelSize: root.wallProfile ? 19 : 15
                font.weight: Font.DemiBold
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
            }
            LoadingSpinner {
                objectName: "launchSpinner"
                spokes: true
                running: splashPanel.animate
                implicitWidth: root.wallProfile ? 31 : 27
                implicitHeight: implicitWidth
                Layout.alignment: Qt.AlignHCenter
                Accessible.role: Accessible.Indicator
                Accessible.name: root.tr("startup_message")
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
        scale: djconnect.toastVisible ? 1 : 0.94
        transformOrigin: Item.Top
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: root.liquidGlassEnabled ? "#bd" + root.moodColor("toastStart").slice(1) : root.moodColor("toastStart") }
            GradientStop { position: 0.52; color: root.liquidGlassEnabled ? "#a8" + root.moodColor("toastMid").slice(1) : root.moodColor("toastMid") }
            GradientStop { position: 1.0; color: root.liquidGlassEnabled ? "#ba" + root.moodColor("toastEnd").slice(1) : root.moodColor("toastEnd") }
        }

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 2
            height: 2
            radius: 2
            color: "#bfffffff"
            opacity: root.liquidGlassEnabled ? 0.72 : 0
        }

        Behavior on opacity { NumberAnimation { duration: root.motionFast; easing.type: Easing.OutCubic } }
        Behavior on y { NumberAnimation { duration: root.motionStandard; easing.type: Easing.OutBack } }
        Behavior on scale { NumberAnimation { duration: root.motionStandard; easing.type: Easing.OutBack } }

        SequentialAnimation on border.color {
            running: djconnect.toastVisible && root.wallProfile
            loops: Animation.Infinite
            ColorAnimation { to: BrandTheme.colors.muted; duration: 1200; easing.type: Easing.InOutSine }
            ColorAnimation { to: "#b8ffffff"; duration: 1200; easing.type: Easing.InOutSine }
        }

        Row {
            anchors.centerIn: parent
            spacing: 16

            MenuIcon {
                width: 28
                height: 28
                iconName: djconnect.toastIcon
                iconColor: BrandTheme.colors.text
                strokeWidth: 2.8
                anchors.verticalCenter: parent.verticalCenter
            }

            Text {
                id: toastText
                width: Math.min(root.width - 188, implicitWidth)
                anchors.verticalCenter: parent.verticalCenter
                text: djconnect.toastText
                color: BrandTheme.colors.text
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
        color: BrandTheme.alpha(BrandTheme.colors.background, "f2")
        visible: !root.splashVisible && djconnect.versionMismatchVisible
        z: 60

        ModalBlocker {}

        ColumnLayout {
            anchors.centerIn: parent
            width: Math.min(parent.width - 72, 560)
            spacing: 18

            Text {
                text: root.tr("version_mismatch_title")
                color: BrandTheme.colors.text
                font.pixelSize: 40
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
            }

            Text {
                text: djconnect.versionMismatchText
                color: BrandTheme.colors.muted
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
                    color: BrandTheme.colors.disabledText
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
        color: BrandTheme.colors.background
        visible: djconnect.logsVisible
        z: 80

        AppBackground { sessionCanvas: true }
        ModalBlocker {}
        LogsView {
            anchors.fill: parent
            backend: djconnect
            confirmationOpen: root.clearLogsConfirmOpen
            onClearRequested: root.clearLogsConfirmOpen = true
        }
    }

    GlassSheet {
        id: musicDnaOptIn
        objectName: "musicDnaOptInSheet"
        property bool discoveryConsent: false
        property string profileId: ""
        z: 86
        onClosed: profileId = ""

        contentItem: ScrollView {
            id: optInScroll
            clip: true
            contentWidth: availableWidth
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ColumnLayout {
                width: optInScroll.availableWidth
                spacing: 22
                Item { Layout.preferredHeight: musicDnaOptIn.compact ? 0 : 22 }
                AppBanner {
                    Layout.fillWidth: true
                    Layout.maximumWidth: musicDnaOptIn.compact ? optInScroll.width - 40 : 900
                    Layout.alignment: Qt.AlignHCenter
                    detailText: root.tr("tagline")
                }
                IntroductionCard {
                    iconName: "heart"
                    title: root.tr("music_dna_opt_in_title")
                    message: root.tr("music_dna_opt_in_description")
                    compact: musicDnaOptIn.compact
                    centeredMessage: false
                    Layout.maximumWidth: musicDnaOptIn.compact ? optInScroll.width - 40 : 900
                    Layout.alignment: Qt.AlignHCenter

                    Repeater {
                        model: [
                            {icon: "trash", key: "music_dna_opt_in_erase"},
                            {icon: "settings", key: "music_dna_opt_in_turn_off"}
                        ]
                        RowLayout {
                            required property var modelData
                            Layout.fillWidth: true
                            spacing: 12
                            FeatureIcon {
                                iconName: modelData.icon
                                iconColor: modelData.icon === "trash" ? BrandTheme.colors.actionDanger : BrandTheme.colors.text
                                Layout.preferredWidth: 22; Layout.preferredHeight: 22
                            }
                            Text {
                                text: root.tr(modelData.key)
                                textFormat: Text.PlainText
                                color: BrandTheme.colors.text
                                font.pixelSize: musicDnaOptIn.compact ? 17 : 20
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                        }
                    }
                    GlassButton {
                        objectName: "musicDnaConfirmEnable"
                        primary: true
                        text: root.tr("music_dna_opt_in_accept")
                        iconName: "discover"
                        Layout.fillWidth: true
                        Layout.preferredHeight: musicDnaOptIn.compact ? 56 : 68
                        enabled: djconnect.paired && !djconnect.musicDnaBusy && !djconnect.musicDiscoveryBusy
                            && musicDnaOptIn.profileId === djconnect.activeProfileId
                        onClicked: {
                            if (!musicDnaOptIn.opened || !enabled) return
                            var discoveryConsent = musicDnaOptIn.discoveryConsent
                            musicDnaOptIn.close()
                            if (discoveryConsent) djconnect.acceptMusicDiscoveryConsent()
                            else djconnect.setMusicDnaEnabled(true)
                        }
                    }
                    GlassButton {
                        objectName: "musicDnaDeclineEnable"
                        foregroundColor: BrandTheme.colors.muted
                        font.pixelSize: musicDnaOptIn.compact ? 18 : 21
                        text: root.tr("music_dna_opt_in_not_now")
                        tertiary: true
                        Layout.fillWidth: true
                        onClicked: {
                            if (musicDnaOptIn.discoveryConsent) djconnect.rejectMusicDiscoveryConsent()
                            musicDnaOptIn.close()
                        }
                    }
                }
            }
        }
    }

    GlassSheet {
        id: clearLogsConfirmPanel
        objectName: "clearLogsConfirmSheet"
        visible: root.clearLogsConfirmOpen
        z: 86

        GlassSurface {
            anchors.centerIn: parent
            width: Math.min(parent.width - 48, 520)
            introduction: true
            radius: 32
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
                    color: BrandTheme.colors.text
                    font.pixelSize: 28
                    font.bold: true
                    Layout.fillWidth: true
                }

                Text {
                    text: root.tr("clear_logs_confirm_message")
                    color: BrandTheme.colors.text
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

    GlassSheet {
        id: askDjClearConfirmPanel
        visible: root.askDjClearConfirmOpen
        z: 86

        GlassSurface {
            anchors.centerIn: parent
            width: Math.min(parent.width - 48, 520)
            introduction: true
            radius: 32
            border.width: 1

            implicitHeight: askDjClearConfirmContent.implicitHeight + 44

            ColumnLayout {
                id: askDjClearConfirmContent
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 22
                spacing: 18

                Text {
                    text: root.tr("ask_dj_clear_confirm_title")
                    color: BrandTheme.colors.text
                    font.pixelSize: 28
                    font.bold: true
                    Layout.fillWidth: true
                }

                Text {
                    text: root.tr("ask_dj_clear_confirm_message")
                    color: BrandTheme.colors.text
                    font.pixelSize: 24
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                LoadingSpinner {
                    visible: djconnect.askDjBusy
                    running: visible
                    Layout.preferredWidth: 42
                    Layout.preferredHeight: 42
                    Layout.alignment: Qt.AlignHCenter
                }

                DangerButton {
                    text: root.tr("clear")
                    enabled: !djconnect.askDjBusy
                    Layout.fillWidth: true
                    Layout.preferredHeight: 56
                    onClicked: djconnect.clearAskDjHistory()
                }

                PurpleButton {
                    text: root.tr("cancel")
                    enabled: !djconnect.askDjBusy
                    font.pixelSize: 24
                    Layout.fillWidth: true
                    Layout.preferredHeight: 56
                    onClicked: root.askDjClearConfirmOpen = false
                }
            }
        }
    }

    GlassSheet {
        id: musicDnaClearConfirmPanel
        visible: root.musicDnaClearConfirmOpen
        z: 86

        GlassSurface {
            anchors.centerIn: parent
            width: Math.min(parent.width - 48, 520)
            introduction: true
            radius: 32
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
                    color: BrandTheme.colors.text
                    font.pixelSize: 28
                    font.bold: true
                    Layout.fillWidth: true
                }

                Text {
                    text: root.tr("music_dna_clear_confirm_message")
                    color: BrandTheme.colors.text
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

    GlassSheet {
        id: musicDnaDisableConfirmPanel
        visible: root.musicDnaDisableConfirmOpen
        z: 86

        GlassSurface {
            anchors.centerIn: parent
            width: Math.min(parent.width - 48, 520)
            introduction: true
            radius: 32
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
                    color: BrandTheme.colors.text
                    font.pixelSize: 28
                    font.bold: true
                    Layout.fillWidth: true
                }

                Text {
                    text: root.tr("music_dna_disable_confirm_message")
                    color: BrandTheme.colors.text
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

    GlassSheet {
        id: resetPairingConfirmPanel
        visible: root.resetPairingConfirmOpen
        z: 84


        GlassSurface {
            anchors.centerIn: parent
            width: Math.min(parent.width - 48, 520)
            introduction: true
            radius: 32
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
                    color: BrandTheme.colors.text
                    font.pixelSize: 28
                    font.bold: true
                    Layout.fillWidth: true
                }

                Text {
                    text: root.tr("reset_pairing_confirm_message")
                    color: BrandTheme.colors.text
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

    GlassSheet {
        id: rebootConfirmPanel
        visible: root.rebootConfirmOpen
        z: 84


        GlassSurface {
            anchors.centerIn: parent
            width: Math.min(parent.width - 48, 520)
            introduction: true
            radius: 32
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
                    color: BrandTheme.colors.text
                    font.pixelSize: 28
                    font.bold: true
                    Layout.fillWidth: true
                }

                Text {
                    text: root.tr("reboot_confirm_message")
                    color: BrandTheme.colors.text
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

    GlassSheet {
        id: shutdownConfirmPanel
        visible: root.shutdownConfirmOpen
        z: 84


        GlassSurface {
            anchors.centerIn: parent
            width: Math.min(parent.width - 48, 520)
            introduction: true
            radius: 32
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
                    color: BrandTheme.colors.text
                    font.pixelSize: 28
                    font.bold: true
                    Layout.fillWidth: true
                }

                Text {
                    text: root.tr("shutdown_confirm_message")
                    color: BrandTheme.colors.text
                    font.pixelSize: 24
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                DangerButton {
                    objectName: "confirmSettingsShutdown"
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
        color: BrandTheme.colors.background
        visible: root.aboutOpen
        z: 22
        onVisibleChanged: {
            if (visible && aboutScroll.contentItem) {
                aboutScroll.contentItem.contentY = 0
            }
        }

        AppBackground { sessionCanvas: true }
        ModalBlocker {}

        PageToolbar {
            id: aboutToolbar
            anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
            anchors.margins: 22
            title: root.tr("about")
            leading: [ GlassButton { iconName: "back"; tertiary: true; implicitWidth: 52; Accessible.name: root.tr("close"); onClicked: root.aboutOpen = false } ]
        }

        ScrollView {
            id: aboutScroll
            anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
            anchors.top: aboutToolbar.bottom
            anchors.margins: 24
            anchors.bottomMargin: root.edge + 126
            clip: true
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            contentWidth: availableWidth

            ColumnLayout {
                width: Math.max(0, aboutScroll.availableWidth)
                spacing: 18


                AppBanner {
                    detailText: root.tr("tagline")
                }

                GlassCard {
                    Layout.fillWidth: true
                Text {
                    text: root.tr("app_section")
                    color: BrandTheme.colors.muted
                    font.pixelSize: 20
                    font.bold: true
                    Layout.fillWidth: true
                }

                GridLayout {
                    columns: 2
                    columnSpacing: 18
                    rowSpacing: 10
                    Layout.fillWidth: true

                    Text { text: root.tr("version"); color: BrandTheme.colors.muted; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.version; color: BrandTheme.colors.text; font.pixelSize: 20; Layout.fillWidth: true }
                    Text { text: root.tr("device_name"); color: BrandTheme.colors.muted; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: "DJConnect"; color: BrandTheme.colors.text; font.pixelSize: 20; Layout.fillWidth: true }
                    Text { text: root.tr("client_type"); color: BrandTheme.colors.muted; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.clientType; color: BrandTheme.colors.text; font.pixelSize: 20; Layout.fillWidth: true }
                    Text { text: root.tr("website"); color: BrandTheme.colors.muted; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: "https://djconnect.dev"; color: BrandTheme.colors.text; font.pixelSize: 20; Layout.fillWidth: true; elide: Text.ElideRight }
                    Text { text: root.tr("web_address"); color: BrandTheme.colors.muted; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.webPortalUrl; color: BrandTheme.colors.text; font.pixelSize: 18; Layout.fillWidth: true; elide: Text.ElideMiddle }
                    Text { text: root.tr("device_id"); color: BrandTheme.colors.muted; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.deviceId; color: BrandTheme.colors.text; font.pixelSize: 18; Layout.fillWidth: true; elide: Text.ElideMiddle }
                }
                }

                GlassCard {
                    Layout.fillWidth: true
                Text {
                    text: root.tr("connection_section")
                    color: BrandTheme.colors.muted
                    font.pixelSize: 20
                    font.bold: true
                    Layout.fillWidth: true
                }

                GridLayout {
                    columns: 2
                    columnSpacing: 18
                    rowSpacing: 10
                    Layout.fillWidth: true

                    Text { text: root.tr("home_assistant"); color: BrandTheme.colors.muted; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.paired ? root.tr("paired") : root.tr("not_paired"); color: BrandTheme.colors.text; font.pixelSize: 20; Layout.fillWidth: true }
                    Text { text: root.tr("transport"); color: BrandTheme.colors.muted; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.transportMode; color: BrandTheme.colors.text; font.pixelSize: 20; Layout.fillWidth: true }
                    Text { text: root.tr("connection_type"); color: BrandTheme.colors.muted; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.connectionType; color: BrandTheme.colors.text; font.pixelSize: 20; Layout.fillWidth: true; elide: Text.ElideRight }
                    Text { text: root.tr("music_backend"); color: BrandTheme.colors.muted; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.paired ? root.tr("connected_value") : root.tr("not_connected_value"); color: djconnect.paired ? BrandTheme.colors.success : BrandTheme.colors.danger; font.pixelSize: 20; font.bold: true; Layout.fillWidth: true }
                    Text { text: root.tr("backend_name"); color: BrandTheme.colors.muted; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.musicBackendName.length ? djconnect.musicBackendName : "-"; color: BrandTheme.colors.text; font.pixelSize: 18; Layout.fillWidth: true; elide: Text.ElideMiddle }
                    Text { text: root.tr("backend_error"); color: BrandTheme.colors.muted; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190; visible: djconnect.musicBackendError.length > 0 }
                    Text { text: djconnect.musicBackendError; color: BrandTheme.colors.danger; font.pixelSize: 18; Layout.fillWidth: true; wrapMode: Text.Wrap; visible: djconnect.musicBackendError.length > 0 }
                    Text { text: root.tr("client_api_url_label"); color: BrandTheme.colors.muted; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.localApiUrl; color: BrandTheme.colors.text; font.pixelSize: 18; Layout.fillWidth: true; elide: Text.ElideMiddle }
                    Text { text: root.tr("ha_local_url"); color: BrandTheme.colors.muted; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: djconnect.haUrl; color: BrandTheme.colors.text; font.pixelSize: 18; Layout.fillWidth: true; elide: Text.ElideMiddle }
                }
                }

                GlassCard {
                    Layout.fillWidth: true
                Text {
                    text: root.tr("notices_section")
                    color: BrandTheme.colors.muted
                    font.pixelSize: 20
                    font.bold: true
                    Layout.fillWidth: true
                }

                GridLayout {
                    columns: 2
                    columnSpacing: 18
                    rowSpacing: 10
                    Layout.fillWidth: true

                    Text { text: root.tr("copyright"); color: BrandTheme.colors.muted; font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: 190 }
                    Text { text: "2026 Peter van Tol"; color: BrandTheme.colors.text; font.pixelSize: 20; Layout.fillWidth: true }
                }
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

    Timer {
        id: trackArtworkDismissTimer
        interval: 5000
        onTriggered: root.trackArtworkOpen = false
    }

    Loader {
        anchors.fill: parent
        z: 198
        active: root.trackArtworkOpen && root.trackArtworkViewOpen
        focus: active
        onLoaded: item.forceActiveFocus()
        sourceComponent: FocusScope {
            objectName: "trackArtworkOverlay"
            Keys.onEscapePressed: root.trackArtworkControlsOpen = false

            Rectangle {
                anchors.fill: parent
                color: BrandTheme.alpha(BrandTheme.colors.background, "ee")
            }
            ModalBlocker {
                onClicked: function(mouse) {
                    if (mouse.button === Qt.LeftButton && root.trackArtworkControlsOpen)
                        root.toggleTrackArtworkControls()
                }
            }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    SessionAttribution {
                        visible: requiresSpotify
                        requiresSpotify: root.sessionTrackArtwork && !!sharedSessionScreen.state.playback.requires_spotify_attribution
                        spotifyURL: requiresSpotify ? sharedSessionScreen.state.playback.source_url || "" : ""
                    }
                    Item { Layout.fillWidth: true }
                    GlassButton {
                        objectName: "closeTrackArtwork"
                        iconName: "end"
                        Accessible.name: root.tr("close")
                        onClicked: root.trackArtworkOpen = false
                    }
                }

                Item {
                    id: artworkArea
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    Column {
                        id: artworkColumn
                        anchors.centerIn: parent
                        width: parent.width
                        spacing: 12

                        GlassSurface {
                            anchors.horizontalCenter: parent.horizontalCenter
                            width: Math.max(0, Math.min(artworkArea.width,
                                artworkArea.height - expandedTitle.height - artworkColumn.spacing
                                - (expandedArtist.visible ? expandedArtist.height + artworkColumn.spacing : 0)))
                            height: width
                            radius: 28
                            elevated: true

                            VinylPlaceholder {
                                anchors.fill: parent
                                anchors.margins: 10
                                radius: 18
                                visible: expandedArt.status !== Image.Ready
                            }
                            Image {
                                id: expandedArt
                                objectName: "expandedTrackArtwork"
                                anchors.fill: parent
                                anchors.margins: 10
                                source: root.sessionTrackArtwork ? sharedSessionScreen.trackArtworkSource : djconnect.imageUrl
                                sourceSize.width: width
                                sourceSize.height: height
                                asynchronous: true
                                retainWhileLoading: false
                                fillMode: Image.PreserveAspectCrop
                                clip: true
                                visible: status === Image.Ready
                            }
                            Rectangle {
                                objectName: "trackArtworkControlsShade"
                                anchors.fill: parent
                                anchors.margins: 10
                                radius: 18
                                visible: root.trackArtworkCanControl && root.trackArtworkControlsOpen
                                color: "#80000000"
                            }
                            MouseArea {
                                anchors.fill: parent
                                enabled: root.trackArtworkCanControl
                                onClicked: root.toggleTrackArtworkControls()
                            }
                            Loader {
                                anchors.centerIn: parent
                                width: Math.min(parent.width - 16, 420)
                                active: root.trackArtworkCanControl && root.trackArtworkControlsOpen
                                sourceComponent: sharedSessionScreen.artworkTransportControls
                            }
                        }

                        Text {
                            id: expandedTitle
                            objectName: "expandedTrackTitle"
                            width: parent.width
                            text: root.sessionTrackArtwork ? sharedSessionScreen.state.playback.title || "" : djconnect.title
                            textFormat: Text.PlainText
                            color: BrandTheme.colors.text
                            font.pixelSize: root.wallProfile ? 42 : 32
                            font.bold: true
                            horizontalAlignment: Text.AlignHCenter
                            elide: Text.ElideRight
                        }

                        Text {
                            id: expandedArtist
                            objectName: "expandedTrackArtist"
                            width: parent.width
                            visible: text.length > 0
                            text: root.sessionTrackArtwork ? sharedSessionScreen.state.playback.artist || "" : djconnect.artist
                            textFormat: Text.PlainText
                            color: BrandTheme.colors.muted
                            font.pixelSize: root.wallProfile ? 30 : 24
                            horizontalAlignment: Text.AlignHCenter
                            elide: Text.ElideRight
                        }
                    }
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
        color: BrandTheme.alpha(BrandTheme.colors.surface, "cc")
        border.color: BrandTheme.alpha(BrandTheme.colors.muted, "80")
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
                detailText: root.tr("dj_response")
                dense: true
            }

            Text {
                id: djResponseText
                text: djconnect.djResponseText
                color: BrandTheme.colors.text
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

    Component.onCompleted: djconnect.edgeBackGesture.observe(root)
    onEdgeBackRouteChanged: djconnect.edgeBackGesture.cancel()
    Connections {
        target: djconnect.edgeBackGesture
        function onBackRequested(route) { root.navigateEdgeBack(route) }
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons
        propagateComposedEvents: true
        z: 199
        onPressed: function(mouse) {
            if (root.screenBlanked) {
                mouse.accepted = true
                return
            }
            root.recordActivity()
            mouse.accepted = false
        }
        onClicked: function(mouse) {
            if (root.screenBlanked) {
                root.wakeDisplay()
                if (mouse.button === Qt.LeftButton)
                    root.showTrackArtwork(sharedSessionScreen.trackArtworkAvailable, true)
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
    }
}
