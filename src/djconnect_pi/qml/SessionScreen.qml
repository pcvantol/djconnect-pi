import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "BrandTheme.js" as BrandTheme

Item {
    id: screen
    objectName: "djSessionScreen"
    property var backend
    property bool historical: false
    property bool currentHistory: false
    readonly property bool compact: width < 900
    readonly property bool sessionControlsVisible: !historical && state.session_id.length > 0
    property var owner: backend.djSession
    property var state: owner.state
    property string draft: ""
    property bool followQuestionReply: false
    property string pendingReplyId: ""
    readonly property string composerContext: state.session_id + "|" + backend.activeProfileId
    property bool forecastMode: false
    readonly property bool showForecast: !historical && state.forecast_supported && forecastMode
    onComposerContextChanged: { forecastMode = false; closeTransient(); if (historyReadPending && historyReadKind === "current") { historyRead.stop(); historyReadPending = false; navigate("session") } }
    function clearComposer() { followQuestionReply = false; pendingReplyId = ""; draft = ""; if (composeInput) composeInput.clear(); if (composerPanel) composerPanel.close(); if (owner) owner.clearSelection() }
    function submitQuestion() { if (owner.sendQuestion(composeInput.text)) { forecastMode = false; followQuestionReply = true; draft = ""; composeInput.clear(); composerPanel.close() } }
    property string proposedMood: "groove"
    readonly property string searchTarget: historical ? ((state.timeline.session || {}).session_id || "") : state.session_id
    property real readingOffset: 0
    function readingAnchor() {
        if (!historical || !historyRows) return ""
        for (var i = 0; i < historyRows.count; i++) {
            var card = historyRows.itemAt(i)
            if (!card) continue
            var y = card.mapToItem(historyScroll.contentItem, 0, 0).y
            if (y + card.height > 0) { readingOffset = y; return card.modelData.entry_id }
        }
        readingOffset = 0
        return ""
    }
    property string pendingReadingAnchor: ""
    function restoreReading(anchor) { pendingReadingAnchor = anchor; readingRestore.restart() }
    Timer {
        id: readingRestore
        interval: 32
        onTriggered: {
            var anchor = screen.pendingReadingAnchor
            if (!screen.historical) return
            var flick = historyScroll.contentItem
            if (flick.dragging) return
            if (!anchor) { flick.contentY = 0; return }
            for (var i = 0; i < historyRows.count; i++) {
                var card = historyRows.itemAt(i)
                if (card && card.modelData.entry_id === anchor) {
                    var delta = card.mapToItem(flick, 0, 0).y - screen.readingOffset
                    flick.contentY = Math.max(0, Math.min(flick.contentY + delta, Math.max(0, flick.contentHeight - flick.height)))
                    return
                }
            }
            flick.contentY = 0
        }
    }
    property string historyReadProfile: ""
    property bool historyReadPending: false
    property string historyReadKind: "archive"
    property string historyReadSession: ""
    function openCurrentHistory() {
        if (!state.session_id) return
        historyReadPending = true
        historyReadKind = "current"
        historyReadSession = state.session_id
        historyReadProfile = backend.activeProfileId
        navigate("session-history")
        owner.closeSaved()
        historyRead.restart()
    }
    function openArchive() {
        historyReadPending = true
        historyReadKind = "archive"
        historyReadProfile = backend.activeProfileId
        navigate("history")
        owner.closeSaved()
        historyRead.restart()
    }
    Timer {
        id: historyRead
        interval: 0
        onTriggered: {
            if (screen.historyReadPending && screen.visible && screen.historical && screen.historyReadProfile === screen.backend.activeProfileId && !screen.owner.busy) {
                if (screen.historyReadKind === "archive" && !screen.currentHistory) screen.owner.loadHistory()
                else if (screen.historyReadKind === "current" && screen.currentHistory && screen.historyReadSession === screen.state.session_id) screen.owner.readCurrentHistory()
                screen.historyReadPending = false
                screen.historyReadSession = ""
                screen.historyReadProfile = ""
            }
        }
    }
    function refreshHistory() {
        if (!historical) return
        if (state.timeline.session) owner.refreshSaved(readingAnchor())
        else if (currentHistory) openCurrentHistory()
        else openArchive()
    }
    function showSearch() { searchPanel.open(); searchInput.forceActiveFocus() }
    function closeTransient() {
        clearComposer()
        if (searchPanel) searchPanel.close()
        if (searchInput) searchInput.clear()
        if (choices) choices.close()
        if (moreChoices) moreChoices.close()
        if (connectionInfo) connectionInfo.close()
        if (endConfirmation) endConfirmation.close()
        if (owner) owner.clearSearch()
    }
    onVisibleChanged: if (!visible) { historyRead.stop(); historyReadProfile = ""; historyReadSession = ""; historyReadPending = false; readingRestore.stop(); pendingReadingAnchor = ""; closeTransient() }
    onHistoricalChanged: { readingRestore.stop(); pendingReadingAnchor = ""; readingOffset = 0 }
    onSearchTargetChanged: { if (searchPanel) searchPanel.close(); if (searchInput) searchInput.clear(); if (owner) owner.clearSearch() }
    signal navigate(string destination)
    function tr(key) { backend.translationVersion; return backend.t(key) }
    function displayDate(value) { backend.translationVersion; return owner.formatTimestamp(value || "") }
    function toolbarValue(field) {
        var shared = backend.sharedSettings
        var value = (shared.values || {})[field]
        if (shared.available && !shared.selection_required && typeof value === "string") return value
        if (field === "mood") return typeof state.mood === "string" ? state.mood : ""
        if (field === "presence") return typeof state.presence === "string" ? state.presence : ""
        return ""
    }
    function toolbarIcon(field) {
        var value = toolbarValue(field)
        if (field === "mood") return ["chill", "groove", "energy", "party"].indexOf(value) >= 0 ? "mood_" + value : "waveform"
        if (field === "presence") return ["music_only", "occasional", "balanced", "talkative", "presenter"].indexOf(value) >= 0 ? "presence_" + value : "chat"
        return ["home_dj", "radio_dj", "club_dj", "festival_dj"].indexOf(value) >= 0 ? "persona_" + value : "session_persona"
    }
    function openChoice(field, button) {
        if (!sessionControlsVisible) return
        choices.sessionId = state.session_id
        choices.profileId = backend.activeProfileId
        choices.field = field
        choices.editToken = backend.sharedSettings.edit_token || ""
        choices.x = Math.max(12, Math.min(button.mapToItem(screen, 0, 0).x, width - choices.width - 12))
        choices.open()
    }
    Timer { interval: 3000; running: screen.visible && screen.backend.paired && !screen.historyReadPending; repeat: true; triggeredOnStart: true; onTriggered: { if (!screen.historical) screen.owner.refresh(); else if (!screen.currentHistory && !screen.state.history_loaded) screen.owner.loadHistory() } }
    Timer { interval: 15000; running: screen.visible && screen.historical && screen.backend.paired; repeat: true; onTriggered: screen.refreshHistory() }
    Timer {
        id: replyRestore
        interval: 32
        onTriggered: {
            if (!screen.visible || screen.historical || !screen.followQuestionReply) return
            for (var i = 0; i < conversationRows.count; i++) {
                var card = conversationRows.itemAt(i)
                if (card && card.modelData.entry_id === screen.pendingReplyId) {
                    var flick = historyScroll.contentItem
                    flick.contentY = Math.max(0, Math.min(flick.contentY + card.mapToItem(flick, 0, 0).y - 12, Math.max(0, flick.contentHeight - flick.height)))
                    screen.followQuestionReply = false
                    screen.pendingReplyId = ""
                    return
                }
            }
        }
    }
    Connections {
        target: historyScroll.contentItem
        function onDraggingChanged() { if (historyScroll.contentItem.dragging) { screen.followQuestionReply = false; readingRestore.stop() } }
    }
    Connections {
        target: screen.owner
        function onQuestionConfirmed(entryId) { if (screen.followQuestionReply) { screen.pendingReplyId = entryId; replyRestore.restart() } }
        function onSelectionInvalidated() { screen.clearComposer() }
        function onTimelineUpdated(anchor) { screen.restoreReading(anchor) }
        function onTimelinePositioned(anchor, offset) { screen.readingOffset = offset; screen.restoreReading(anchor) }
        function onChanged() { if (screen.historyReadPending && !screen.owner.busy) historyRead.restart() }
        function onContextCleared() { historyRead.stop(); screen.historyReadProfile = ""; screen.historyReadSession = ""; readingRestore.stop(); screen.pendingReadingAnchor = ""; screen.readingOffset = 0; screen.closeTransient(); if (screen.historical) screen.navigate(screen.currentHistory ? "session" : "more"); screen.historyReadPending = false }
        function onEntryOpened() {
            searchPanel.close()
            screen.readingOffset = 0
            screen.navigate(screen.currentHistory || !screen.historical ? "session-history" : "history")
        }
    }

    Connections {
        target: screen.backend
        function onProfileChanged() { if (screen.historyReadPending) screen.navigate(screen.historyReadKind === "current" ? "session" : "more"); historyRead.stop(); screen.historyReadProfile = ""; screen.historyReadSession = ""; screen.historyReadPending = false; screen.closeTransient(); screen.proposedMood = "groove" }
        function onSharedSettingsChanged() {
            if (choices.opened && choices.editToken !== (screen.backend.sharedSettings.edit_token || "")) choices.close()
        }
    }
    RowLayout {
        id: toolbar
        anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
        anchors.margins: 20; height: 58; spacing: 10
        GlassSurface {
            visible: screen.sessionControlsVisible || (screen.state.search_available && screen.searchTarget.length > 0)
            Layout.preferredWidth: toolbarButtons.implicitWidth + 18
            Layout.fillHeight: true
            radius: height / 2
            RowLayout {
                id: toolbarButtons
                anchors.centerIn: parent; spacing: 2
                GlassButton {
                    id: moreButton
                    objectName: "sessionToolbarMore"
                    visible: screen.compact && screen.sessionControlsVisible
                    iconName: "more"; Accessible.name: screen.tr("more")
                    implicitWidth: 52; background: Item {}
                    onClicked: moreChoices.open()
                }
                GlassButton {
                    visible: (!screen.compact || !screen.sessionControlsVisible) && screen.state.search_available && screen.searchTarget.length > 0
                    iconName: "search"; Accessible.name: screen.tr("session_search")
                    implicitWidth: 52; background: Item {}
                    onClicked: screen.showSearch()
                }
                GlassButton {
                    id: moodButton
                    objectName: "sessionToolbarMood"
                    visible: screen.sessionControlsVisible
                    iconName: screen.toolbarIcon("mood"); Accessible.name: screen.tr("mood_select")
                    implicitWidth: 52; background: Item {}
                    onClicked: screen.openChoice("mood", moodButton)
                }
                GlassButton {
                    id: presenceButton
                    objectName: "sessionToolbarPresence"
                    visible: screen.sessionControlsVisible
                    iconName: screen.toolbarIcon("presence"); Accessible.name: screen.tr("shared_field_presence")
                    implicitWidth: 52; background: Item {}
                    onClicked: screen.openChoice("presence", presenceButton)
                }
                GlassButton {
                    id: personaButton
                    objectName: "sessionToolbarPersona"
                    visible: screen.sessionControlsVisible
                    iconName: screen.toolbarIcon("persona"); Accessible.name: screen.tr("shared_field_persona")
                    implicitWidth: 52; background: Item {}
                    onClicked: screen.openChoice("persona", personaButton)
                }
                GlassButton {
                    id: voiceButton
                    objectName: "sessionToolbarVoice"
                    visible: !screen.compact && screen.sessionControlsVisible
                    iconName: "voice"; Accessible.name: screen.tr("shared_field_voice")
                    implicitWidth: 52; background: Item {}
                    onClicked: screen.openChoice("voice", voiceButton)
                }
                GlassButton {
                    visible: screen.sessionControlsVisible
                    objectName: "sessionCompactEnd"
                    iconName: "end"; Accessible.name: screen.tr("session_end")
                    enabled: !screen.owner.lifecycleBusy && screen.state.runtime_state !== "ending"
                    implicitWidth: 52; background: Item {}
                    onClicked: { endConfirmation.expectedSessionId = screen.state.session_id; endConfirmation.open() }
                }
            }
        }
        Item { Layout.fillWidth: true }
        GlassSurface {
            Layout.preferredWidth: connectionButtons.implicitWidth + 18
            Layout.fillHeight: true; radius: height / 2
            RowLayout {
                id: connectionButtons
                anchors.centerIn: parent; spacing: 2
                GlassButton {
                    objectName: "sessionToolbarConnection"
                    visible: screen.sessionControlsVisible
                    iconName: "globe"; Accessible.name: screen.tr("connection_type")
                    implicitWidth: 52; background: Item {}
                    onClicked: connectionInfo.open()
                }
                GlassButton {
                    objectName: "sessionRefresh"
                    iconName: "refresh"; Accessible.name: screen.tr("refresh")
                    implicitWidth: 52; background: Item {}
                    enabled: !screen.owner.busy
                    onClicked: { if (screen.historical) screen.refreshHistory(); else screen.owner.refresh(); screen.backend.pollSharedSettings() }
                }
            }
        }
    }

    RowLayout {
        id: modeSwitch
        visible: !screen.historical && screen.state.forecast_supported
        anchors.left: parent.left; anchors.top: toolbar.bottom
        anchors.leftMargin: 20; anchors.topMargin: 10; height: 48
        GlassButton { objectName: "sessionFlowMode"; text: screen.tr("session_flow"); primary: !screen.forecastMode; onClicked: screen.forecastMode = false }
        GlassButton { objectName: "sessionForecastMode"; text: screen.tr("session_forecast"); primary: screen.forecastMode; onClicked: screen.forecastMode = true }
    }
    ScrollView {
        id: forecastScroll
        objectName: "sessionForecastScroll"
        visible: screen.showForecast
        anchors.top: modeSwitch.bottom; anchors.bottom: parent.bottom
        anchors.left: parent.left; anchors.right: parent.right
        anchors.margins: 20; anchors.bottomMargin: composerDock.visible ? composerDock.height + 144 : 132
        clip: true; contentWidth: availableWidth
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ColumnLayout {
            width: parent.width; spacing: 20
            Text { text: screen.tr("session_forecast"); textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: screen.compact ? 30 : 40; font.bold: true; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            Text { visible: !!screen.state.forecast.source_url; text: screen.tr("session_forecast_source"); textFormat: Text.PlainText; color: BrandTheme.colors.muted; font.pixelSize: 18 }
            SessionAttribution { id: forecastSource; requiresSpotify: !!screen.state.forecast.source_url; spotifyURL: screen.state.forecast.source_url || ""; Layout.fillWidth: true }
            Repeater {
                model: forecastSource.ready ? screen.state.forecast.sections : []
                GlassCard {
                    required property var modelData
                    Layout.fillWidth: true
                    Text { text: screen.tr("session_forecast_" + modelData.claim_type); textFormat: Text.PlainText; color: BrandTheme.colors.cyan; font.pixelSize: 18; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Text { text: modelData.title; textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 25; font.bold: true; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Text { text: modelData.text; textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 23; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                }
            }
            Text { visible: screen.state.forecast.sections.length === 0; text: screen.tr("session_forecast_empty"); textFormat: Text.PlainText; color: BrandTheme.colors.muted; font.pixelSize: 23; wrapMode: Text.WordWrap; Layout.fillWidth: true }
        }
    }
    ScrollView {
        id: historyScroll
        visible: !screen.showForecast
        objectName: "sessionHistoryScroll"
        anchors.top: modeSwitch.visible ? modeSwitch.bottom : toolbar.bottom; anchors.bottom: parent.bottom
        anchors.left: parent.left; anchors.right: parent.right
        anchors.margins: 20; anchors.bottomMargin: composerDock.visible ? composerDock.height + 144 : 132
        clip: true; contentWidth: availableWidth
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ColumnLayout {
            width: parent.width; spacing: 22
            Text {
                text: screen.tr(screen.historical ? (screen.state.timeline.session ? "session_history_title" : "session_history") : "session_title") + (screen.backend.demoMode ? " · " + screen.tr("demo_mode") : "")
                color: BrandTheme.colors.text; font.pixelSize: screen.width > 800 ? 40 : 30; font.bold: true
                textFormat: Text.PlainText; Layout.fillWidth: true
            }
            VinylPlaceholder {
                visible: !screen.historical && screen.state.loaded && screen.state.moments.length === 0 && screen.state.conversation.length === 0 &&
                    (!screen.state.profile_confirmation_required || screen.backend.demoMode)
                Layout.preferredWidth: Math.min(parent.width, screen.compact ? screen.height * 0.38 : 520)
                Layout.preferredHeight: width
                Layout.alignment: Qt.AlignHCenter
            }
            GlassCard {
                visible: screen.state.profile_confirmation_required && !screen.backend.demoMode
                Layout.fillWidth: true
                Text { text: screen.tr("session_profile_choose"); color: BrandTheme.colors.text; font.pixelSize: 26; font.bold: true }
                Text {
                    text: screen.backend.activeProfileId.length > 0 ? screen.backend.activeProfileName : screen.tr("session_profile_missing")
                    color: BrandTheme.colors.muted; font.pixelSize: 22; wrapMode: Text.WordWrap
                    textFormat: Text.PlainText; Layout.fillWidth: true
                }
                GlassButton {
                    text: screen.tr("session_profile_use"); primary: true
                    enabled: screen.backend.paired && screen.backend.activeProfileId.length > 0
                    onClicked: screen.owner.confirmProfile(screen.backend.activeProfileId)
                }
            }
            GlassCard {
                visible: screen.state.error.length > 0 && screen.state.error !== "profile_required"
                Layout.fillWidth: true
                Text {
                    text: screen.tr(screen.state.error === "uncertain" ? "session_uncertain" : "session_error")
                    color: BrandTheme.colors.warning; font.pixelSize: 21; wrapMode: Text.WordWrap
                    Layout.fillWidth: true; textFormat: Text.PlainText
                }
            }
            GlassCard {
                visible: !screen.historical && screen.state.loaded && !screen.state.session_id
                Layout.fillWidth: true
                Text { text: screen.tr("session_empty"); color: BrandTheme.colors.text; font.pixelSize: 25; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                Flow {
                    Layout.fillWidth: true; spacing: 10
                    Repeater {
                        model: ["chill", "groove", "energy", "party"]
                        GlassButton {
                            required property string modelData
                            text: screen.tr("shared_mood_" + modelData)
                            checkable: true; checked: screen.proposedMood === modelData
                            onClicked: screen.proposedMood = modelData
                        }
                    }
                }
                GlassButton { text: screen.tr("session_start"); primary: true; enabled: !screen.owner.busy; onClicked: screen.owner.start(screen.proposedMood) }
            }
            GlassCard {
                visible: !screen.historical && screen.state.session_id.length > 0 && screen.state.moments.length === 0 && screen.state.conversation.length === 0
                Layout.fillWidth: true
                RowLayout {
                    Layout.fillWidth: true; spacing: 18
                    DJSessionMenuSymbol { iconColor: BrandTheme.colors.purple; Layout.preferredWidth: 64; Layout.preferredHeight: 64 }
                    Text { text: screen.tr(screen.state.runtime_state === "opening" ? "session_starting" : screen.state.runtime_state === "ending" ? "session_ending" : "session_listening"); color: BrandTheme.colors.text; font.pixelSize: screen.width > 800 ? 30 : 24; font.bold: true; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                }
                Text {
                    visible: screen.backend.demoMode
                    text: screen.tr("session_demo_body"); textFormat: Text.PlainText
                    color: BrandTheme.colors.muted; font.pixelSize: 22
                    wrapMode: Text.WordWrap; Layout.fillWidth: true
                }
                RowLayout {
                    Layout.fillWidth: true
                    GlassButton { text: screen.tr("session_history"); enabled: !screen.owner.busy; onClicked: screen.openArchive() }
                    Item { Layout.fillWidth: true }
                    GlassButton {
                        objectName: "sessionExpandedEnd"
                        iconName: "trash"; Accessible.name: screen.tr("session_end")
                        enabled: !screen.owner.lifecycleBusy && screen.state.runtime_state !== "ending"
                        onClicked: { endConfirmation.expectedSessionId = screen.state.session_id; endConfirmation.open() }
                    }
                }
            }
            Repeater {
                objectName: "sessionLiveMomentRows"
                model: !screen.historical ? screen.state.moments : []
                GlassCard {
                    objectName: "sessionLiveMomentCard"
                    required property var modelData
                    Layout.fillWidth: true
                    Text { visible: liveSources.ready; text: modelData.title; textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 26; font.bold: true; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Text { visible: liveSources.ready; text: modelData.body; textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 23; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    GlassButton {
                        visible: screen.state.composer_available && liveSources.ready
                        text: screen.tr("session_ask_about"); enabled: !screen.owner.busy
                        onClicked: { if (screen.owner.selectMoment(screen.state.session_id, modelData.moment_id)) composerPanel.open() }
                    }
                    SessionAttribution { id: liveSources; sources: modelData.display_sources || []; requiresSpotify: modelData.requires_spotify_attribution || false; spotifyURL: modelData.spotify_source_url || ""; Layout.fillWidth: true }
                }
            }
            GlassCard {
                objectName: "sessionPlaybackMetadata"
                visible: !screen.historical && !!screen.state.playback.item_id
                Layout.fillWidth: true
                Text { visible: playbackSources.ready && text.length > 0; text: screen.state.playback.title || ""; textFormat: Text.PlainText; font.pixelSize: screen.compact ? 26 : 30; font.bold: true; color: BrandTheme.colors.text; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                Text { visible: playbackSources.ready && text.length > 0; text: screen.state.playback.artist || ""; textFormat: Text.PlainText; font.pixelSize: 23; color: BrandTheme.colors.muted; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                Text { visible: playbackSources.ready && text.length > 0; text: screen.state.playback.album || ""; textFormat: Text.PlainText; font.pixelSize: 19; color: BrandTheme.colors.muted; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                ProgressBar {
                    id: playbackProgress
                    visible: playbackSources.ready && screen.state.playback.time_label !== undefined
                    value: screen.state.playback.progress || 0; Layout.fillWidth: true
                    Accessible.name: screen.tr("now_playing")
                    background: Rectangle { implicitHeight: 6; radius: 3; color: BrandTheme.colors.text; opacity: 0.18 }
                    contentItem: Item {
                        implicitHeight: 6
                        Rectangle { width: playbackProgress.visualPosition * parent.width; height: parent.height; radius: 3; color: BrandTheme.colors.text }
                    }
                }
                Text { visible: playbackSources.ready && text.length > 0; text: screen.state.playback.time_label || ""; textFormat: Text.PlainText; font.pixelSize: 18; color: BrandTheme.colors.muted; Layout.alignment: Qt.AlignRight }
                RowLayout {
                    visible: playbackSources.ready && !!screen.state.playback.target_name
                    Layout.fillWidth: true
                    FeatureIcon { iconName: "music"; Layout.preferredWidth: 22; Layout.preferredHeight: 22 }
                    Text { text: screen.state.playback.target_name || ""; textFormat: Text.PlainText; font.pixelSize: 19; color: BrandTheme.colors.muted; wrapMode: Text.WordWrap; Layout.fillWidth: true; Accessible.name: screen.tr("output_device") + ": " + text }
                }
                SessionAttribution { id: playbackSources; requiresSpotify: !!screen.state.playback.requires_spotify_attribution; spotifyURL: screen.state.playback.source_url || ""; Layout.fillWidth: true }
            }
            Repeater {
                id: conversationRows
                objectName: "sessionConversationRows"
                model: !screen.historical ? screen.state.conversation : []
                GlassCard {
                    objectName: "sessionConversationCard"
                    required property var modelData
                    Layout.fillWidth: true
                    Text { text: screen.tr(modelData.kind === "conversation_user" ? "session_you" : "session_dj"); color: BrandTheme.colors.muted; font.pixelSize: 18; textFormat: Text.PlainText }
                    Text { visible: conversationSources.ready; text: modelData.text || ""; color: BrandTheme.colors.text; font.pixelSize: 22; textFormat: Text.PlainText; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Text { text: screen.displayDate(modelData.occurred_at); color: BrandTheme.colors.muted; font.pixelSize: 16; textFormat: Text.PlainText }
                    SessionAttribution { id: conversationSources; sources: modelData.display_sources || []; requiresSpotify: modelData.requires_spotify_attribution || false; spotifyURL: modelData.spotify_source_url || ""; Layout.fillWidth: true }
                }
            }
            GlassButton {
                objectName: "sessionReadCurrentHistory"
                visible: !screen.historical && screen.state.history_available && screen.state.session_id.length > 0
                text: screen.tr("session_history_first"); enabled: !screen.owner.busy
                onClicked: screen.openCurrentHistory()
            }
            GlassButton {
                visible: screen.historical
                objectName: "sessionHistoryBack"
                text: screen.tr(screen.currentHistory ? "session_back" : screen.state.timeline.session ? "session_history" : "more")
                onClicked: { var detail = !!screen.state.timeline.session; var current = screen.currentHistory; screen.owner.closeSaved(); if (current) screen.navigate("session"); else if (!detail) screen.navigate("more") }
            }
            Repeater {
                model: screen.historical && !screen.state.timeline.session ? screen.state.sessions : []
                GlassButton {
                    required property var modelData
                    Layout.fillWidth: true; implicitHeight: 78
                    objectName: "sessionArchiveRow"
                    text: screen.tr("session_title") + " · " + screen.displayDate(modelData.started_at || modelData.created_at)
                    onClicked: screen.owner.openSaved(modelData.session_id)
                }
            }
            Text {
                visible: screen.historical && !screen.owner.busy && screen.state.history_loaded && screen.state.sessions.length === 0 && !screen.state.timeline.session
                text: screen.tr("session_history_empty"); color: BrandTheme.colors.muted; font.pixelSize: 22
            }
            Text {
                visible: screen.historical && !!screen.state.timeline.session
                text: screen.tr("session_history_view_readonly"); color: BrandTheme.colors.muted; font.pixelSize: 20
            }
            GlassButton {
                visible: screen.historical && !!screen.state.timeline.session
                text: screen.tr("session_history_first"); enabled: !screen.owner.busy
                onClicked: screen.owner.firstEntries()
            }
            Repeater {
                id: historyRows
                objectName: "sessionHistoryRows"
                model: screen.historical ? (screen.state.timeline.entries || []) : []
                GlassCard {
                    id: historyCard
                    required property var modelData
                    readonly property var played: modelData.historical_playback || {}
                    Layout.fillWidth: true
                    Text {
                        visible: historySources.ready
                        text: modelData.kind === "playback_observed" ? screen.tr("session_history_playback") : modelData.kind === "conversation_user" ? screen.tr("session_you") : modelData.kind === "conversation_dj" ? screen.tr("session_dj") : modelData.kind === "dj_silence" ? screen.tr("session_silence") : modelData.kind === "dj_publication" ? screen.tr("session_unavailable_contribution") : (modelData.summary || screen.tr("session_title"))
                        color: BrandTheme.colors.text; font.pixelSize: 24; font.bold: true; wrapMode: Text.WordWrap; textFormat: Text.PlainText; Layout.fillWidth: true
                    }
                    Text { text: modelData.text || ""; visible: historySources.ready && text.length > 0 && !historyCard.played.title && !historyCard.played.artist && !historyCard.played.album; color: BrandTheme.colors.text; font.pixelSize: 22; wrapMode: Text.WordWrap; textFormat: Text.PlainText; Layout.fillWidth: true }
                    Text { visible: historySources.ready && text.length > 0; text: historyCard.played.title || ""; textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 26; font.bold: true; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Text { visible: historySources.ready && text.length > 0; text: historyCard.played.artist || ""; textFormat: Text.PlainText; color: BrandTheme.colors.muted; font.pixelSize: 23; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Text { visible: historySources.ready && text.length > 0; text: historyCard.played.album || ""; textFormat: Text.PlainText; color: BrandTheme.colors.muted; font.pixelSize: 19; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    SessionAttribution { id: historySources; sources: modelData.display_sources || []; requiresSpotify: modelData.requires_spotify_attribution || false; spotifyURL: modelData.spotify_source_url || ""; Layout.fillWidth: true }
                    GlassButton {
                        visible: screen.state.composer_available && historySources.ready
                        text: screen.tr("session_ask_about"); enabled: !screen.owner.busy
                        onClicked: { if (screen.owner.selectEntry(modelData.session_id, modelData.entry_id)) { screen.navigate("session"); composerPanel.open() } }
                    }
                    Text { objectName: "sessionHistoryEntryDate"; text: screen.displayDate(modelData.occurred_at); color: BrandTheme.colors.muted; font.pixelSize: 16; textFormat: Text.PlainText }
                }
            }
            Flow {
                visible: screen.historical && !!screen.state.timeline.session
                Layout.fillWidth: true; spacing: 10
                GlassButton { objectName: "sessionHistoryPrevious"; text: screen.tr("session_history_previous"); visible: screen.state.has_previous_entries; enabled: !screen.owner.busy; onClicked: screen.owner.previousEntries(screen.readingAnchor()) }
                GlassButton { objectName: "sessionHistoryNext"; text: screen.tr("session_history_next"); visible: !!screen.state.timeline.next_cursor; enabled: !screen.owner.busy; onClicked: screen.owner.nextEntries(screen.readingAnchor(), screen.readingOffset) }
            }
            GlassButton { visible: screen.historical && !screen.state.timeline.session && screen.state.has_more_sessions; text: screen.tr("session_more"); enabled: !screen.owner.busy; onClicked: screen.owner.moreHistory() }
            BusyIndicator { visible: screen.owner.busy; running: visible; Layout.alignment: Qt.AlignHCenter }
        }
    }
    GlassSurface {
        id: composerDock
        objectName: "sessionComposerDock"
        visible: screen.state.composer_available
        anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
        anchors.leftMargin: 20; anchors.rightMargin: 20; anchors.bottomMargin: 120
        height: composerColumn.implicitHeight + 16; radius: 30; elevated: true
        ColumnLayout {
            id: composerColumn
            anchors.fill: parent; anchors.margins: 8; spacing: 4
            Text {
                visible: screen.state.question_status.length > 0
                text: screen.tr("session_question_" + (screen.state.question_status || "sending"))
                Layout.fillWidth: true; Layout.leftMargin: 16
                color: BrandTheme.colors.muted; font.pixelSize: 16; wrapMode: Text.WordWrap; textFormat: Text.PlainText
            }
            RowLayout {
                Layout.fillWidth: true; spacing: 8
                GlassButton {
                    Layout.fillWidth: true; enabled: !screen.owner.busy
                    onClicked: composerPanel.open()
                    contentItem: Text { text: screen.draft || screen.tr("session_question_placeholder"); textFormat: Text.PlainText; elide: Text.ElideRight; color: BrandTheme.colors.muted; font.pixelSize: 21; verticalAlignment: Text.AlignVCenter }
                }
                GlassButton {
                    iconName: "send"; Accessible.name: screen.tr("session_send"); primary: true
                    enabled: !screen.owner.busy && !screen.owner.questionBusy && screen.draft.trim().length > 0
                    onClicked: { composeInput.text = screen.draft; screen.submitQuestion() }
                }
            }
        }
    }
    Popup {
        id: composerPanel
        objectName: "sessionComposerPanel"
        x: 16; y: toolbar.y + toolbar.height + 8
        width: screen.width - 32; height: Math.min(screen.height - y - 126, 580)
        padding: 20; modal: true; dim: false
        onOpened: { composeInput.text = screen.draft; composeInput.forceActiveFocus() }
        background: GlassSurface { elevated: true }
        contentItem: ColumnLayout {
            spacing: 12
            Text { text: screen.tr("session_question_title"); color: BrandTheme.colors.text; font.bold: true; font.pixelSize: 25; textFormat: Text.PlainText; Layout.fillWidth: true }
            RowLayout {
                visible: !!screen.state.selection.kind
                Layout.fillWidth: true
                Text { text: screen.tr("session_question_selected"); color: BrandTheme.colors.muted; font.pixelSize: 18; wrapMode: Text.WordWrap; textFormat: Text.PlainText; Layout.fillWidth: true }
                GlassButton { iconName: "end"; Accessible.name: screen.tr("session_clear_reference"); onClicked: screen.owner.clearSelection() }
            }
            TextField {
                id: composeInput
                objectName: "sessionComposerInput"
                Layout.fillWidth: true; Layout.minimumHeight: 58
                placeholderText: screen.tr("session_question_placeholder")
                Accessible.name: screen.tr("session_question_placeholder")
                maximumLength: 4000; selectByMouse: true; font.pixelSize: 22
                onTextChanged: screen.draft = text
                onAccepted: screen.submitQuestion()
            }
            TouchKeyboard {
                objectName: "sessionComposerKeyboard"
                Layout.fillWidth: true; target: composeInput; backend: screen.backend
                submitIcon: "send"; submitLabel: screen.tr("session_send")
                onSubmitted: screen.submitQuestion()
                onDismissed: composerPanel.close()
            }
            RowLayout {
                Layout.fillWidth: true
                GlassButton { text: screen.tr("close"); onClicked: composerPanel.close() }
                Item { Layout.fillWidth: true }
                GlassButton { text: screen.tr("session_send"); iconName: "send"; primary: true; enabled: !screen.owner.busy && !screen.owner.questionBusy && composeInput.text.trim().length > 0; onClicked: screen.submitQuestion() }
            }
        }
    }
    Popup {
        id: searchPanel
        objectName: "sessionSearchPanel"
        property bool keyboardVisible: true
        onOpened: keyboardVisible = true
        x: 16; y: toolbar.y + toolbar.height + 8
        width: screen.width - 32; height: Math.min(screen.height - y - 126, 760)
        padding: 20; modal: true; dim: false
        background: GlassSurface { elevated: true }
        contentItem: ColumnLayout {
            spacing: 12
            RowLayout {
                Layout.fillWidth: true
                TextField {
                    id: searchInput
                    objectName: "sessionSearchInput"
                    onActiveFocusChanged: if (activeFocus) searchPanel.keyboardVisible = true
                    placeholderText: screen.tr("session_search")
                    maximumLength: 200; font.pixelSize: 21
                    Layout.fillWidth: true; Layout.minimumHeight: 52
                    Accessible.name: screen.tr("session_search")
                    selectByMouse: true
                    onTextEdited: screen.owner.clearSearch()
                    onAccepted: if (!screen.owner.busy) screen.owner.search(screen.searchTarget, text)
                }
                GlassButton {
                    iconName: "search"; Accessible.name: screen.tr("session_search")
                    enabled: !screen.owner.busy && searchInput.text.trim().length > 0
                    onClicked: screen.owner.search(screen.searchTarget, searchInput.text)
                }
                GlassButton { text: screen.tr("close"); onClicked: searchPanel.close() }
            }
            Text {
                visible: screen.state.error.length > 0
                text: screen.tr(screen.state.error === "uncertain" ? "session_uncertain" : "session_error")
                color: BrandTheme.colors.warning; font.pixelSize: 18
                wrapMode: Text.WordWrap; Layout.fillWidth: true
            }
            Text {
                visible: !!screen.state.search.query
                text: screen.tr(screen.state.search.complete ? "session_search_complete" : "session_search_partial")
                color: BrandTheme.colors.muted; font.pixelSize: 18
                wrapMode: Text.WordWrap; Layout.fillWidth: true
            }
            Text {
                visible: !!screen.state.search.query && (screen.state.search.matches || []).length === 0 && screen.state.search.complete
                text: screen.tr("session_search_empty"); color: BrandTheme.colors.muted; font.pixelSize: 20
            }
            ScrollView {
                id: searchScroll
                Layout.fillWidth: true; Layout.fillHeight: true
                contentWidth: availableWidth; clip: true
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                ColumnLayout {
                    width: searchScroll.availableWidth; spacing: 14
                    Repeater {
                        model: screen.state.search.matches || []
                        GlassCard {
                            required property var modelData
                            Layout.fillWidth: true
                            Text { visible: searchSources.ready; text: modelData.summary || screen.tr("session_title"); textFormat: Text.PlainText; color: BrandTheme.colors.text; font.bold: true; font.pixelSize: 22; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                            Text { objectName: "sessionSearchHighlightedBody"; visible: searchSources.ready; text: modelData.highlighted_text || ""; textFormat: Text.StyledText; color: BrandTheme.colors.text; font.pixelSize: 20; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                            SessionAttribution { id: searchSources; sources: modelData.display_sources || []; requiresSpotify: modelData.requires_spotify_attribution || false; spotifyURL: modelData.spotify_source_url || ""; Layout.fillWidth: true }
                            GlassButton {
                                text: screen.tr("session_open_entry"); enabled: !screen.owner.busy
                                onClicked: screen.owner.openEntry(modelData.session_id, modelData.entry_id)
                            }
                        }
                    }
                    GlassButton {
                        visible: !!screen.state.search.next_cursor
                        text: screen.tr("session_more"); enabled: !screen.owner.busy
                        onClicked: screen.owner.moreSearch()
                    }
                    BusyIndicator { visible: screen.owner.busy; running: visible; Layout.alignment: Qt.AlignHCenter }
                }
            }
            TouchKeyboard {
                visible: searchPanel.keyboardVisible
                Layout.fillWidth: true
                target: searchInput; backend: screen.backend
                onEdited: screen.owner.clearSearch()
                onSubmitted: {
                    if (!screen.owner.busy && searchInput.text.trim().length > 0) {
                        searchPanel.keyboardVisible = false
                        screen.owner.search(screen.searchTarget, searchInput.text)
                    }
                }
                onDismissed: searchPanel.keyboardVisible = false
            }
        }
    }
    Popup {
        id: moreChoices
        x: 20; y: toolbar.y + toolbar.height + 8
        width: Math.min(screen.width - 40, 420); padding: 16
        modal: true; dim: false
        background: GlassSurface { elevated: true }
        contentItem: ColumnLayout {
            spacing: 10
            GlassButton {
                visible: screen.state.search_available && screen.searchTarget.length > 0
                text: screen.tr("session_search"); iconName: "search"
                Layout.fillWidth: true
                onClicked: { moreChoices.close(); screen.showSearch() }
            }
            Repeater {
                model: ["voice"]
                GlassButton {
                    required property string modelData
                    text: screen.tr("shared_field_" + modelData)
                    Layout.fillWidth: true
                    onClicked: { moreChoices.close(); screen.openChoice(modelData, moreButton) }
                }
            }
            GlassButton {
                text: screen.tr("session_history"); Layout.fillWidth: true
                onClicked: { moreChoices.close(); screen.openArchive() }
            }
        }
    }
    Popup {
        id: connectionInfo
        x: screen.width - width - 20; y: toolbar.y + toolbar.height + 8
        width: Math.min(screen.width - 40, 420); padding: 22
        modal: true; dim: false
        background: GlassSurface { elevated: true }
        contentItem: ColumnLayout {
            Text { text: screen.tr("connection_type"); font.bold: true; font.pixelSize: 24; color: BrandTheme.colors.text }
            Text { text: screen.backend.connectionType; textFormat: Text.PlainText; font.pixelSize: 22; color: BrandTheme.colors.muted; wrapMode: Text.WordWrap; Layout.fillWidth: true }
        }
    }
    Popup {
        id: choices
        objectName: "sessionToolbarChoice"
        property string sessionId: ""
        property string profileId: ""
        property string field: "mood"
        property string editToken: ""
        readonly property bool canSubmit: choices.visible && screen.state.runtime_state === "active" && screen.sessionControlsVisible && choices.sessionId === screen.state.session_id && choices.profileId === screen.backend.activeProfileId && choices.editToken === (screen.backend.sharedSettings.edit_token || "") && !!screen.backend.sharedSettings.available && !screen.backend.sharedSettingsBusy && !screen.backend.sharedSettings.selection_required && choices.editToken.length > 0 && !screen.backend.sharedSettings.operation_pending
        y: toolbar.y + toolbar.height + 8; width: Math.min(screen.width - 24, 560); padding: 22
        modal: true; dim: false
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: GlassSurface { radius: 28; elevated: true }
        contentItem: ColumnLayout {
            spacing: 18
            Text { text: screen.tr("shared_field_" + choices.field); color: BrandTheme.colors.text; font.pixelSize: 26; font.bold: true }
            Flow {
                Layout.fillWidth: true; spacing: 10
                Repeater {
                    model: (screen.backend.sharedSettings.options || {})[choices.field] || []
                    GlassButton {
                        required property var modelData
                        text: choices.field === "voice" ? (modelData.label || "") : screen.tr("shared_" + choices.field + "_" + modelData)
                        primary: screen.toolbarValue(choices.field) === (choices.field === "voice" ? modelData.value : modelData)
                        enabled: choices.canSubmit
                        objectName: "sessionToolbarOption"
                        onClicked: {
                            if (!choices.canSubmit) return
                            var patch = {_edit_token: choices.editToken}
                            patch[choices.field] = choices.field === "voice" ? modelData.value : modelData
                            screen.backend.saveSharedSettings(patch)
                            choices.close()
                        }
                    }
                }
            }
            GlassButton { text: screen.tr("shared_title"); onClicked: { choices.close(); screen.navigate("settings") } }
        }
    }
    Popup {
        id: endConfirmation
        property string expectedSessionId: ""
        anchors.centerIn: parent
        width: Math.min(screen.width - 40, 520); padding: 24; modal: true
        background: GlassSurface { elevated: true }
        contentItem: ColumnLayout {
            spacing: 20
            Text { text: screen.tr("session_end_confirm"); color: BrandTheme.colors.text; font.pixelSize: 26; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            GlassButton { text: screen.tr("session_end"); onClicked: { screen.owner.end(endConfirmation.expectedSessionId); endConfirmation.close() } }
            GlassButton { text: screen.tr("cancel"); onClicked: endConfirmation.close() }
        }
    }
}
