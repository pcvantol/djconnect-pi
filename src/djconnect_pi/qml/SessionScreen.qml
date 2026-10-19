import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "BrandTheme.js" as BrandTheme

Item {
    id: screen
    objectName: "djSessionScreen"
    property var backend
    property bool historical: false
    readonly property bool compact: width < 900
    property var owner: backend.djSession
    property var state: owner.state
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
    function refreshHistory() { if (historical && state.timeline.session) owner.refreshSaved(readingAnchor()) }
    function showSearch() { searchPanel.open(); searchInput.forceActiveFocus() }
    function closeTransient() {
        if (searchPanel) searchPanel.close()
        if (searchInput) searchInput.clear()
        if (choices) choices.close()
        if (moreChoices) moreChoices.close()
        if (connectionInfo) connectionInfo.close()
        if (endConfirmation) endConfirmation.close()
        if (owner) owner.clearSearch()
    }
    onVisibleChanged: if (!visible) closeTransient()
    onSearchTargetChanged: { if (searchPanel) searchPanel.close(); if (searchInput) searchInput.clear(); if (owner) owner.clearSearch() }
    signal navigate(string destination)
    function tr(key) { backend.translationVersion; return backend.t(key) }
    function openChoice(field, button) {
        choices.field = field
        choices.editToken = backend.sharedSettings.edit_token || ""
        choices.x = Math.max(12, Math.min(button.mapToItem(screen, 0, 0).x, width - choices.width - 12))
        choices.open()
    }
    Timer { interval: 3000; running: screen.visible && screen.backend.paired; repeat: true; triggeredOnStart: true; onTriggered: { if (!screen.historical) screen.owner.refresh(); else if (!screen.state.history_loaded) screen.owner.loadHistory() } }
    Timer { interval: 15000; running: screen.visible && screen.historical && screen.backend.paired; repeat: true; onTriggered: screen.refreshHistory() }
    Connections {
        target: screen.owner
        function onTimelineUpdated(anchor) { screen.restoreReading(anchor) }
        function onContextCleared() { screen.closeTransient() }
        function onEntryOpened() {
            searchPanel.close()
            screen.readingOffset = 0
            screen.navigate("history")
        }
    }

    Connections {
        target: screen.backend
        function onProfileChanged() { screen.closeTransient(); screen.proposedMood = "groove" }
    }
    RowLayout {
        id: toolbar
        anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
        anchors.margins: 20; height: 58; spacing: 10
        GlassSurface {
            Layout.preferredWidth: toolbarButtons.implicitWidth + 18
            Layout.fillHeight: true
            radius: height / 2
            RowLayout {
                id: toolbarButtons
                anchors.centerIn: parent; spacing: 2
                GlassButton {
                    id: moreButton
                    visible: screen.compact
                    iconName: "more"; Accessible.name: screen.tr("more")
                    implicitWidth: 52; background: Item {}
                    onClicked: moreChoices.open()
                }
                GlassButton {
                    visible: !screen.compact && screen.state.search_available && screen.searchTarget.length > 0
                    iconName: "search"; Accessible.name: screen.tr("session_search")
                    implicitWidth: 52; background: Item {}
                    onClicked: screen.showSearch()
                }
                GlassButton {
                    id: moodButton
                    iconName: "mood"; Accessible.name: screen.tr("mood_select")
                    implicitWidth: 52; background: Item {}
                    onClicked: screen.openChoice("mood", moodButton)
                }
                GlassButton {
                    id: presenceButton
                    visible: !screen.compact
                    iconName: "chat"; Accessible.name: screen.tr("shared_field_presence")
                    implicitWidth: 52; background: Item {}
                    onClicked: screen.openChoice("presence", presenceButton)
                }
                GlassButton {
                    id: personaButton
                    visible: !screen.compact
                    iconName: "persona"; Accessible.name: screen.tr("shared_field_persona")
                    implicitWidth: 52; background: Item {}
                    onClicked: screen.openChoice("persona", personaButton)
                }
                GlassButton {
                    id: voiceButton
                    iconName: "voice"; Accessible.name: screen.tr("shared_field_voice")
                    implicitWidth: 52; background: Item {}
                    onClicked: screen.openChoice("voice", voiceButton)
                }
                GlassButton {
                    visible: screen.state.session_id.length > 0 && !screen.historical
                    iconName: "end"; Accessible.name: screen.tr("session_end")
                    enabled: !screen.owner.busy && screen.state.runtime_state !== "ending"
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
                    iconName: "globe"; Accessible.name: screen.tr("connection_type")
                    implicitWidth: 52; background: Item {}
                    onClicked: connectionInfo.open()
                }
                GlassButton {
                    iconName: "refresh"; Accessible.name: screen.tr("refresh")
                    implicitWidth: 52; background: Item {}
                    enabled: !screen.owner.busy
                    onClicked: { if (screen.historical) screen.refreshHistory(); else screen.owner.refresh(); screen.backend.pollSharedSettings() }
                }
            }
        }
    }

    ScrollView {
        id: historyScroll
        objectName: "sessionHistoryScroll"
        anchors.top: toolbar.bottom; anchors.bottom: parent.bottom
        anchors.left: parent.left; anchors.right: parent.right
        anchors.margins: 20; anchors.bottomMargin: 132
        clip: true; contentWidth: availableWidth
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ColumnLayout {
            width: parent.width; spacing: 22
            Text {
                text: screen.tr(screen.historical ? "session_history" : "session_title") + (screen.backend.demoMode ? " · " + screen.tr("demo_mode") : "")
                color: BrandTheme.colors.text; font.pixelSize: screen.width > 800 ? 40 : 30; font.bold: true
                textFormat: Text.PlainText; Layout.fillWidth: true
            }
            VinylPlaceholder {
                visible: !screen.historical && screen.state.loaded &&
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
                visible: !screen.historical && screen.state.session_id.length > 0
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
                    GlassButton { text: screen.tr("session_history"); enabled: !screen.owner.busy; onClicked: { screen.owner.loadHistory(); screen.navigate("history") } }
                    Item { Layout.fillWidth: true }
                    GlassButton {
                        iconName: "trash"; Accessible.name: screen.tr("session_end")
                        enabled: !screen.owner.busy && screen.state.runtime_state !== "ending"
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
                    SessionAttribution { id: liveSources; sources: modelData.display_sources || []; requiresSpotify: modelData.requires_spotify_attribution || false; spotifyURL: modelData.spotify_source_url || ""; Layout.fillWidth: true }
                }
            }
            GlassButton {
                visible: screen.historical
                text: screen.tr(screen.state.timeline.session ? "session_history" : "session_back")
                onClicked: { var detail = !!screen.state.timeline.session; screen.owner.closeSaved(); if (!detail) screen.navigate("session") }
            }
            Repeater {
                model: screen.historical && !screen.state.timeline.session ? screen.state.sessions : []
                GlassButton {
                    required property var modelData
                    Layout.fillWidth: true; implicitHeight: 78
                    text: screen.tr("session_title") + " · " + (modelData.started_at || modelData.created_at || "")
                    onClicked: screen.owner.openSaved(modelData.session_id)
                }
            }
            Text {
                visible: screen.historical && !screen.owner.busy && screen.state.history_loaded && screen.state.sessions.length === 0 && !screen.state.timeline.session
                text: screen.tr("session_history_empty"); color: BrandTheme.colors.muted; font.pixelSize: 22
            }
            Text {
                visible: screen.historical && !!screen.state.timeline.session
                text: screen.tr("session_history_readonly"); color: BrandTheme.colors.muted; font.pixelSize: 20
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
                    required property var modelData
                    Layout.fillWidth: true
                    Text {
                        visible: historySources.ready
                        text: modelData.kind === "dj_silence" ? screen.tr("session_silence") : modelData.kind === "dj_publication" ? screen.tr("session_unavailable_contribution") : (modelData.summary || screen.tr("session_title"))
                        color: BrandTheme.colors.text; font.pixelSize: 24; font.bold: true; wrapMode: Text.WordWrap; textFormat: Text.PlainText; Layout.fillWidth: true
                    }
                    Text { text: modelData.text || ""; visible: historySources.ready && text.length > 0; color: BrandTheme.colors.text; font.pixelSize: 22; wrapMode: Text.WordWrap; textFormat: Text.PlainText; Layout.fillWidth: true }
                    SessionAttribution { id: historySources; sources: modelData.display_sources || []; requiresSpotify: modelData.requires_spotify_attribution || false; spotifyURL: modelData.spotify_source_url || ""; Layout.fillWidth: true }
                    Text { text: modelData.occurred_at || ""; color: BrandTheme.colors.muted; font.pixelSize: 16; textFormat: Text.PlainText }
                }
            }
            Flow {
                visible: screen.historical && !!screen.state.timeline.session
                Layout.fillWidth: true; spacing: 10
                GlassButton { text: screen.tr("session_history_next"); visible: !!screen.state.timeline.next_cursor; enabled: !screen.owner.busy; onClicked: screen.owner.nextEntries() }
            }
            GlassButton { visible: screen.historical && !screen.state.timeline.session && screen.state.has_more_sessions; text: screen.tr("session_more"); enabled: !screen.owner.busy; onClicked: screen.owner.moreHistory() }
            BusyIndicator { visible: screen.owner.busy; running: visible; Layout.alignment: Qt.AlignHCenter }
        }
    }
    Popup {
        id: searchPanel
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
                            Text { visible: searchSources.ready; text: modelData.text || ""; textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 20; wrapMode: Text.WordWrap; Layout.fillWidth: true }
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
                model: ["presence", "persona", "voice"]
                GlassButton {
                    required property string modelData
                    text: screen.tr("shared_field_" + modelData)
                    Layout.fillWidth: true
                    onClicked: { moreChoices.close(); screen.openChoice(modelData, moreButton) }
                }
            }
            GlassButton {
                text: screen.tr("session_history"); Layout.fillWidth: true
                onClicked: { moreChoices.close(); screen.owner.loadHistory(); screen.navigate("history") }
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
        property string field: "mood"
        property string editToken: ""
        y: 90; width: Math.min(screen.width - 24, 560); padding: 22
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
                        enabled: !!screen.backend.sharedSettings.available && !screen.backend.sharedSettingsBusy && !screen.backend.sharedSettings.selection_required
                        onClicked: {
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
