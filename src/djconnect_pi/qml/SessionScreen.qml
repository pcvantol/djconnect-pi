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
    onComposerContextChanged: { clearFlowReturn(); forecastMode = false; closeTransient(); if (historyReadPending && historyReadKind === "current") { historyRead.stop(); historyReadPending = false; navigate("session") } }
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
    // Only identity/position survives the history view, never a cached body.
    property var flowReturn: null
    function clearFlowReturn() { flowReturnRestore.stop(); flowReturn = null }
    function rememberFlow() {
        clearFlowReturn()
        if (historical || showForecast || !state.session_id) return
        followQuestionReply = false
        replyRestore.stop()
        currentReplyPosition.stop()
        pendingQuestionPosition.stop()
        var groups = [liveMomentRows, conversationRows]
        for (var g = 0; g < groups.length; g++) {
            for (var i = 0; i < groups[g].count; i++) {
                var card = groups[g].itemAt(i)
                if (!card) continue
                var y = card.mapToItem(historyScroll.contentItem, 0, 0).y
                if (y + card.height > 0 && y < historyScroll.contentItem.height && isFinite(y) && Math.abs(y) <= 1000000) {
                    flowReturn = {session: state.session_id, profile: backend.activeProfileId,
                        kind: g === 0 ? "moment" : "conversation",
                        id: g === 0 ? card.modelData.moment_id : card.modelData.entry_id, offset: y}
                    return
                }
            }
        }
        if (currentReplyCard.visible && state.current_reply.reply_id) {
            var replyY = currentReplyCard.mapToItem(historyScroll.contentItem, 0, 0).y
            if (replyY + currentReplyCard.height > 0 && replyY < historyScroll.contentItem.height && isFinite(replyY) && Math.abs(replyY) <= 1000000) {
                flowReturn = {session: state.session_id, profile: backend.activeProfileId,
                    kind: "current_reply", id: state.current_reply.reply_id, offset: replyY}
            }
        }
    }
    Timer {
        id: flowReturnRestore
        interval: 32
        onTriggered: {
            var saved = screen.flowReturn
            screen.flowReturn = null
            var flick = historyScroll.contentItem
            if (!screen.visible || screen.historical || flick.dragging) return
            if (!saved || saved.session !== screen.state.session_id || saved.profile !== screen.backend.activeProfileId) { flick.contentY = 0; return }
            if (saved.kind === "current_reply") {
                // The getter revalidates the live source; the descriptor grants nothing.
                if (screen.state.current_reply.reply_id === saved.id && currentReplyCard.visible) {
                    var replyDelta = currentReplyCard.mapToItem(flick, 0, 0).y - saved.offset
                    flick.contentY = Math.max(0, Math.min(flick.contentY + replyDelta, Math.max(0, flick.contentHeight - flick.height)))
                } else flick.contentY = 0
                return
            }
            var rows = saved.kind === "moment" ? liveMomentRows : conversationRows
            for (var i = 0; i < rows.count; i++) {
                var card = rows.itemAt(i)
                var id = card ? (saved.kind === "moment" ? card.modelData.moment_id : card.modelData.entry_id) : ""
                if (id === saved.id) {
                    var delta = card.mapToItem(flick, 0, 0).y - saved.offset
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
        if (!historical) rememberFlow()
        historyReadPending = true
        historyReadKind = "current"
        historyReadSession = state.session_id
        historyReadProfile = backend.activeProfileId
        navigate("session-history")
        owner.closeSaved()
        historyRead.restart()
    }
    function openArchive() {
        clearFlowReturn()
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
        else if (state.history_loaded) refreshArchiveList()
        else openArchive()
    }
    property var archiveIntent: null
    property bool archiveReadActive: false
    property var archiveReturn: null
    property var archiveDetailReturn: null
    property string archiveLayoutMark: ""
    property int archivePositionTries: 0
    property bool archivePositionApplied: false
    readonly property bool archivePositionPending: archivePosition.running
    function scheduleArchivePosition() {
        archiveLayoutMark = ""; archivePositionTries = 0; archivePositionApplied = false
        archivePosition.restart()
    }
    function cancelArchiveRead() { archiveRead.stop(); archivePosition.stop(); archiveIntent = null; archiveReadActive = false; archiveReturn = null }
    function rememberArchive() {
        archiveReturn = null
        var flick = historyScroll.contentItem
        if (flick.dragging) return
        historyContent.ensurePolished()
        for (var i = 0; i < archiveRows.count; i++) {
            var row = archiveRows.itemAt(i)
            if (!row) continue
            var y = row.mapToItem(flick, 0, 0).y
            if (y + row.height > 0 && y < flick.height && isFinite(y) && Math.abs(y) <= 1000000) {
                archiveReturn = {id: row.modelData.session_id, profile: backend.activeProfileId, offset: y}
                return
            }
        }
    }
    function openArchiveSession(sessionId) {
        if (!visible || !historical || currentHistory || state.timeline.session || owner.busy || archiveIntent) return
        if (!state.sessions.some(function(row) { return row.session_id === sessionId })) return
        rememberArchive(); archiveDetailReturn = archiveReturn; archiveReturn = null
        owner.openSaved(sessionId)
    }
    function returnArchiveDetail() {
        var saved = archiveDetailReturn
        owner.closeSaved()
        archiveDetailReturn = null; archiveReturn = saved
        archiveIntent = {profile: backend.activeProfileId}
        archiveRead.restart()
    }
    function changeArchiveWindow(direction) {
        if (!visible || !historical || currentHistory || state.timeline.session || owner.busy || archiveIntent || archiveReadActive) return
        if (direction === "older" && !state.has_older_sessions) return
        if (direction === "newer" && !state.has_newer_sessions) return
        if (direction === "newest" && !state.archive_older_window) return
        rememberArchive()
        var saved = archiveReturn
        archiveReturn = null; archivePosition.stop(); archiveReadActive = true
        if (direction === "older") owner.olderSessions(saved ? saved.id : "", saved ? saved.offset : 0)
        else if (direction === "newer") owner.newerSessions()
        else owner.loadHistory()
    }
    function refreshArchiveList() {
        if (!visible || !historical || currentHistory || state.timeline.session || archiveIntent || archiveReadActive) return
        rememberArchive()
        archiveIntent = {profile: backend.activeProfileId}
        archiveRead.restart()
    }
    Timer {
        id: archiveRead; interval: 0
        onTriggered: {
            var intent = screen.archiveIntent
            if (!intent || screen.owner.busy) return
            if (screen.visible && screen.historical && !screen.currentHistory && !screen.state.timeline.session && intent.profile === screen.backend.activeProfileId) { screen.archiveReadActive = true; screen.owner.refreshArchive() }
            screen.archiveIntent = null
        }
    }
    Timer {
        id: archivePosition; objectName: "sessionArchivePositionTimer"; interval: 32
        onTriggered: {
            var saved = screen.archiveReturn
            var flick = historyScroll.contentItem
            if (!screen.visible || !screen.historical || screen.currentHistory || screen.state.timeline.session || !saved || saved.profile !== screen.backend.activeProfileId || flick.dragging) { screen.archiveReturn = null; return }
            if (!saved.id) { flick.contentY = 0; screen.archiveReturn = null; return }
            historyContent.ensurePolished()
            var target = null
            for (var i = 0; i < archiveRows.count; i++) {
                var card = archiveRows.itemAt(i)
                if (card && card.modelData.session_id === saved.id) { target = card; break }
            }
            screen.archivePositionTries++
            var ready = target && archiveRows.count === screen.state.sessions.length && flick.contentHeight + 1 >= historyContent.implicitHeight
            var mark = ready ? [archiveRows.count, historyContent.implicitHeight, flick.contentHeight, flick.height, target.y, target.height].join("|") : ""
            if (!ready || mark !== screen.archiveLayoutMark) {
                screen.archiveLayoutMark = mark; screen.archivePositionApplied = false
                if (screen.archivePositionTries < 8) archivePosition.restart()
                else { flick.contentY = 0; screen.archiveReturn = null }
                return
            }
            var destination = Math.max(0, Math.min(flick.contentY + target.mapToItem(flick, 0, 0).y - saved.offset, Math.max(0, flick.contentHeight - flick.height)))
            if (screen.archivePositionApplied && Math.abs(flick.contentY - destination) < 1) { screen.archiveReturn = null; return }
            flick.contentY = destination; screen.archivePositionApplied = true
            if (screen.archivePositionTries < 8) archivePosition.restart()
            else screen.archiveReturn = null
        }
    }
    property var searchReturn: null
    property var searchRefreshIntent: null
    readonly property bool searchRefreshPending: !!searchRefreshIntent
    function cancelSearchRead() { searchRead.stop(); searchPosition.stop(); searchRefreshIntent = null; searchReturn = null }
    function rememberSearch() {
        searchReturn = null
        for (var i = 0; i < searchRows.count; i++) {
            var card = searchRows.itemAt(i)
            if (!card) continue
            var y = card.mapToItem(searchScroll.contentItem, 0, 0).y
            if (y + card.height > 0 && y < searchScroll.contentItem.height && isFinite(y) && Math.abs(y) <= 1000000) {
                searchReturn = {id: card.modelData.entry_id, offset: y}
                return
            }
        }
    }
    function refreshSearchResults() {
        if (!searchPanel.opened || !state.search.query || searchRefreshPending) return
        rememberSearch()
        searchRefreshIntent = {session: state.search.session_id, query: state.search.query, profile: backend.activeProfileId}
        searchRead.restart()
    }
    Timer {
        id: searchRead; interval: 0
        onTriggered: {
            var intent = screen.searchRefreshIntent
            if (!intent || screen.owner.busy) return
            if (searchPanel.opened && intent.profile === screen.backend.activeProfileId && intent.session === screen.state.search.session_id && intent.query === screen.state.search.query) screen.owner.refreshSearch()
            screen.searchRefreshIntent = null
        }
    }
    Timer { objectName: "sessionSearchRevalidationTimer"; interval: 15000; repeat: true; running: searchPanel.opened; onTriggered: screen.refreshSearchResults() }
    Timer {
        id: searchPosition; interval: 32
        onTriggered: {
            var saved = screen.searchReturn
            screen.searchReturn = null
            var flick = searchScroll.contentItem
            if (!searchPanel.opened || flick.dragging) return
            for (var i = 0; saved && i < searchRows.count; i++) {
                var card = searchRows.itemAt(i)
                if (card && card.modelData.entry_id === saved.id) {
                    flick.contentY = Math.max(0, Math.min(flick.contentY + card.mapToItem(flick, 0, 0).y - saved.offset, Math.max(0, flick.contentHeight - flick.height)))
                    return
                }
            }
            flick.contentY = 0
        }
    }
    Connections { target: searchScroll.contentItem; function onDraggingChanged() { if (searchScroll.contentItem.dragging) { searchPosition.stop(); screen.searchReturn = null } } }
    function searchNow() { cancelSearchRead(); owner.search(searchTarget, searchInput.text) }
    function showSearch() { searchPanel.open(); searchInput.forceActiveFocus() }
    function closeTransient() {
        archiveDetailReturn = null
        cancelSearchRead()
        clearComposer()
        if (searchPanel) searchPanel.close()
        if (searchInput) searchInput.clear()
        if (choices) choices.close()
        if (moreChoices) moreChoices.close()
        if (connectionInfo) connectionInfo.close()
        if (endConfirmation) endConfirmation.close()
        if (owner) owner.clearSearch()
    }
    onVisibleChanged: if (!visible) { cancelArchiveRead(); if (owner) owner.clearArchive(); clearFlowReturn(); historyRead.stop(); historyReadProfile = ""; historyReadSession = ""; historyReadPending = false; readingRestore.stop(); pendingReadingAnchor = ""; closeTransient() }
    onHistoricalChanged: { if (!historical) { archiveDetailReturn = null; cancelArchiveRead(); if (owner) owner.clearArchive() } readingRestore.stop(); pendingReadingAnchor = ""; readingOffset = 0; if (!historical && flowReturn) flowReturnRestore.restart() }
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
    Timer { objectName: "sessionRuntimePollTimer"; interval: 3000; running: screen.visible && screen.backend.paired && !screen.historyReadPending && !screen.searchRefreshPending; repeat: true; triggeredOnStart: true; onTriggered: { if (!screen.historical) screen.owner.refresh(); else if (!screen.currentHistory && !screen.state.history_loaded) screen.owner.loadHistory() } }
    Timer { objectName: "sessionHistoryRevalidationTimer"; interval: 15000; running: screen.visible && screen.historical && screen.backend.paired; repeat: true; onTriggered: screen.refreshHistory() }
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
    Timer {
        id: pendingQuestionPosition; interval: 32
        onTriggered: {
            if (!screen.visible || screen.historical || !screen.followQuestionReply || !screen.state.pending_question.text || historyScroll.contentItem.dragging) return
            var flick = historyScroll.contentItem
            flick.contentY = Math.max(0, Math.min(flick.contentY + pendingQuestionCard.mapToItem(flick, 0, 0).y - 12, Math.max(0, flick.contentHeight - flick.height)))
        }
    }
    Timer {
        id: currentReplyPosition; interval: 32
        onTriggered: {
            if (!screen.visible || screen.historical || !screen.followQuestionReply || !screen.state.current_reply.text || historyScroll.contentItem.dragging) return
            var flick = historyScroll.contentItem
            flick.contentY = Math.max(0, Math.min(flick.contentY + currentReplyCard.mapToItem(flick, 0, 0).y - 12, Math.max(0, flick.contentHeight - flick.height)))
            screen.followQuestionReply = false
        }
    }
    Connections {
        target: historyScroll.contentItem
        function onDraggingChanged() { if (historyScroll.contentItem.dragging) { archivePosition.stop(); screen.archiveReturn = null; screen.followQuestionReply = false; readingRestore.stop(); if (!screen.historical) screen.clearFlowReturn() } }
    }
    Connections {
        target: screen.owner
        function onPendingQuestionReady() { pendingQuestionPosition.restart() }
        function onCurrentReplyReady() { currentReplyPosition.restart() }
        function onQuestionConfirmed(entryId) { if (screen.followQuestionReply) { screen.pendingReplyId = entryId; replyRestore.restart() } }
        function onSelectionInvalidated() { screen.clearComposer() }
        function onTimelineUpdated(anchor) { screen.restoreReading(anchor) }
        function onTimelinePositioned(anchor, offset) { screen.readingOffset = offset; screen.restoreReading(anchor) }
        function onHistoryUpdated() { screen.scheduleArchivePosition() }
        function onArchivePositioned(sessionId, offset) {
            if (!screen.visible || !screen.historical || screen.currentHistory || screen.state.timeline.session || historyScroll.contentItem.dragging) return
            screen.archiveReturn = {id: sessionId, profile: screen.backend.activeProfileId, offset: offset}
            screen.scheduleArchivePosition()
        }
        function onChanged() { if (!screen.owner.busy) screen.archiveReadActive = false; if (!screen.historical || screen.currentHistory || screen.state.timeline.session) screen.cancelArchiveRead(); if (screen.archiveIntent && !screen.owner.busy) archiveRead.restart(); if (!screen.state.search.query) screen.cancelSearchRead(); if (screen.historyReadPending && !screen.owner.busy) historyRead.restart(); if (screen.searchRefreshPending && !screen.owner.busy) searchRead.restart() }
        function onSearchUpdated() { searchPosition.restart() }
        function onContextCleared() { screen.cancelArchiveRead(); screen.clearFlowReturn(); historyRead.stop(); screen.historyReadProfile = ""; screen.historyReadSession = ""; readingRestore.stop(); screen.pendingReadingAnchor = ""; screen.readingOffset = 0; screen.closeTransient(); if (screen.historical) screen.navigate(screen.currentHistory ? "session" : "more"); screen.historyReadPending = false }
        function onEntryOpened() {
            if (!screen.historical) screen.rememberFlow()
            searchPanel.close()
            screen.readingOffset = 0
            screen.navigate(screen.currentHistory || !screen.historical ? "session-history" : "history")
        }
    }

    Connections {
        target: screen.backend
        function onProfileChanged() { screen.cancelArchiveRead(); screen.clearFlowReturn(); if (screen.historyReadPending) screen.navigate(screen.historyReadKind === "current" ? "session" : "more"); historyRead.stop(); screen.historyReadProfile = ""; screen.historyReadSession = ""; screen.historyReadPending = false; screen.closeTransient(); screen.proposedMood = "groove" }
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
            id: historyContent
            width: parent.width; spacing: 22
            Text {
                text: screen.tr(screen.historical ? (screen.state.timeline.session ? "session_history_title" : "session_history") : "session_title") + (screen.backend.demoMode ? " · " + screen.tr("demo_mode") : "")
                color: BrandTheme.colors.text; font.pixelSize: screen.width > 800 ? 40 : 30; font.bold: true
                textFormat: Text.PlainText; Layout.fillWidth: true
            }
            VinylPlaceholder {
                visible: !screen.historical && screen.state.loaded && screen.state.moments.length === 0 && screen.state.retained_flow.length === 0 &&
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
                visible: !screen.historical && screen.state.session_id.length > 0 && screen.state.moments.length === 0 && screen.state.retained_flow.length === 0
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
                id: liveMomentRows
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
            Text {
                objectName: "sessionRetainedFlowLabel"
                visible: !screen.historical && screen.state.retained_flow.length > 0
                text: screen.tr("session_retained_flow"); textFormat: Text.PlainText
                color: BrandTheme.colors.muted; font.pixelSize: 18; wrapMode: Text.WordWrap; Layout.fillWidth: true
            }
            Repeater {
                id: conversationRows
                objectName: "sessionConversationRows"
                model: !screen.historical ? screen.state.retained_flow : []
                SessionRetainedEntry {
                    objectName: "sessionConversationCard"
                    required property var modelData
                    entry: modelData; translate: screen.tr; dateText: screen.displayDate(modelData.occurred_at)
                    selectionAvailable: screen.state.composer_available
                    selectionBusy: screen.owner.busy || screen.owner.questionBusy
                    onAskAbout: (sessionId, entryId) => { if (screen.owner.selectFlowEntry(sessionId, entryId)) composerPanel.open() }
                }
            }
            GlassCard {
                id: pendingQuestionCard
                objectName: "sessionPendingQuestion"
                visible: !screen.historical && !!screen.state.pending_question.text
                Layout.fillWidth: true
                Layout.maximumWidth: parent.width * 0.85
                Layout.alignment: Qt.AlignRight
                Text { text: screen.tr("session_you"); textFormat: Text.PlainText; color: BrandTheme.colors.muted; font.pixelSize: 18; Layout.fillWidth: true }
                Text { objectName: "sessionPendingQuestionText"; text: screen.state.pending_question.text || ""; textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 22; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                Text { text: screen.tr("session_question_sending"); textFormat: Text.PlainText; color: BrandTheme.colors.muted; font.pixelSize: 16; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            }
            ColumnLayout {
                id: currentReplyCard
                objectName: "sessionCurrentReply"
                visible: !screen.historical && !!screen.state.current_reply.text
                Layout.fillWidth: true
                spacing: 12
                GlassCard {
                    objectName: "sessionCurrentQuestion"
                    visible: !!screen.state.current_reply.question_text
                    Layout.fillWidth: true
                    Layout.maximumWidth: currentReplyCard.width * 0.85
                    Layout.alignment: Qt.AlignRight
                    Text { text: screen.tr("session_you"); textFormat: Text.PlainText; color: BrandTheme.colors.muted; font.pixelSize: 18; Layout.fillWidth: true }
                    Text { objectName: "sessionCurrentQuestionText"; text: screen.state.current_reply.question_text || ""; textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 22; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                }
                GlassCard {
                    Layout.fillWidth: true
                    Text { text: screen.tr("session_current_response"); textFormat: Text.PlainText; color: BrandTheme.colors.muted; font.pixelSize: 18; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Text { visible: currentReplySources.ready; text: screen.state.current_reply.text || ""; textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 22; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    SessionAttribution { id: currentReplySources; sources: screen.state.current_reply.display_sources || []; requiresSpotify: screen.state.current_reply.requires_spotify_attribution || false; spotifyURL: screen.state.current_reply.spotify_source_url || ""; Layout.fillWidth: true }
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
                onClicked: { if (screen.currentHistory) { screen.owner.closeSaved(); screen.navigate("session") } else if (screen.state.timeline.session) screen.returnArchiveDetail(); else { screen.owner.closeSaved(); screen.navigate("more") } }
            }
            Text {
                objectName: "sessionArchiveWindowReset"
                visible: screen.historical && !screen.state.timeline.session && screen.state.archive_window_reset
                text: screen.tr("session_archive_reset"); textFormat: Text.PlainText
                color: BrandTheme.colors.muted; font.pixelSize: 18; wrapMode: Text.WordWrap; Layout.fillWidth: true
            }
            Repeater {
                id: archiveRows
                objectName: "sessionArchiveRows"
                model: screen.historical && !screen.state.timeline.session ? screen.state.sessions : []
                GlassButton {
                    required property var modelData
                    Layout.fillWidth: true; implicitHeight: 78
                    objectName: "sessionArchiveRow"
                    enabled: !screen.owner.busy && !screen.archiveIntent
                    text: screen.tr("session_title") + " · " + screen.displayDate(modelData.started_at || modelData.created_at)
                    onClicked: screen.openArchiveSession(modelData.session_id)
                }
            }
            Text {
                visible: screen.historical && !screen.owner.busy && screen.state.history_loaded && screen.state.sessions.length === 0 && !screen.state.timeline.session
                text: screen.tr(screen.state.archive_older_window || screen.state.has_more_sessions || screen.state.has_older_sessions ? "session_archive_window_empty" : "session_history_empty"); color: BrandTheme.colors.muted; font.pixelSize: 22
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
                SessionRetainedEntry {
                    required property var modelData
                    entry: modelData; translate: screen.tr; dateText: screen.displayDate(modelData.occurred_at)
                    selectionAvailable: screen.state.composer_available; selectionBusy: screen.owner.busy
                    onAskAbout: (sessionId, entryId) => { if (screen.owner.selectEntry(sessionId, entryId)) { screen.navigate("session"); composerPanel.open() } }
                }
            }
            GlassButton {
                objectName: "sessionHistoryExtend"
                visible: screen.historical && !!screen.state.timeline.session && screen.state.timeline._page_cursor === "" && !!screen.state.timeline.next_cursor && (screen.state.timeline._prefix_pages || 1) < 5
                text: screen.tr("session_more"); enabled: !screen.owner.busy
                onClicked: screen.owner.extendEntries(screen.readingAnchor(), screen.readingOffset)
            }
            Text {
                objectName: "sessionHistoryWindowLimit"
                visible: screen.historical && !!screen.state.timeline.next_cursor && (screen.state.timeline._prefix_pages || 0) >= 5
                text: screen.tr("session_history_window_limit"); textFormat: Text.PlainText
                color: BrandTheme.colors.muted; font.pixelSize: 18; wrapMode: Text.WordWrap; Layout.fillWidth: true
            }
            Flow {
                visible: screen.historical && !!screen.state.timeline.session
                Layout.fillWidth: true; spacing: 10
                GlassButton { objectName: "sessionHistoryPrevious"; text: screen.tr("session_history_previous"); visible: screen.state.has_previous_entries; enabled: !screen.owner.busy; onClicked: screen.owner.previousEntries(screen.readingAnchor()) }
                GlassButton { objectName: "sessionHistoryNext"; text: screen.tr("session_history_next"); visible: !!screen.state.timeline.next_cursor; enabled: !screen.owner.busy; onClicked: screen.owner.nextEntries(screen.readingAnchor(), screen.readingOffset) }
            }
            GlassButton { visible: screen.historical && !screen.state.timeline.session && screen.state.has_more_sessions; objectName: "sessionArchiveMore"; text: screen.tr("session_more"); enabled: !screen.owner.busy && !screen.archiveIntent; onClicked: { if (screen.visible && screen.historical && !screen.currentHistory && !screen.state.timeline.session && screen.state.has_more_sessions && !screen.owner.busy && !screen.archiveIntent) { screen.rememberArchive(); screen.archiveReadActive = true; screen.owner.moreHistory() } } }
            Text { objectName: "sessionArchiveLimit"; visible: screen.historical && !screen.state.timeline.session && screen.state.history_limit_reached; text: screen.tr("session_archive_limit"); textFormat: Text.PlainText; color: BrandTheme.colors.muted; font.pixelSize: 18; wrapMode: Text.WordWrap; Layout.fillWidth: true }

            Flow {
                visible: screen.historical && !screen.currentHistory && !screen.state.timeline.session
                Layout.fillWidth: true; spacing: 10
                GlassButton { objectName: "sessionArchiveNewer"; text: screen.tr("session_archive_newer"); visible: screen.state.has_newer_sessions; enabled: !screen.owner.busy && !screen.archiveIntent; onClicked: screen.changeArchiveWindow("newer") }
                GlassButton { objectName: "sessionArchiveOlder"; text: screen.tr("session_archive_older"); visible: screen.state.has_older_sessions; enabled: !screen.owner.busy && !screen.archiveIntent; onClicked: screen.changeArchiveWindow("older") }
                GlassButton { objectName: "sessionArchiveNewest"; text: screen.tr("session_archive_newest"); visible: screen.state.archive_older_window; enabled: !screen.owner.busy && !screen.archiveIntent; onClicked: screen.changeArchiveWindow("newest") }
            }
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
                objectName: "sessionComposerStatus"
                visible: screen.state.question_status.length > 0 && (screen.state.question_status !== "sending" || !pendingQuestionCard.visible)
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
        onClosed: { screen.cancelSearchRead(); searchInput.clear(); screen.owner.clearSearch() }
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
                    onAccepted: if (!screen.owner.busy) screen.searchNow()
                }
                GlassButton {
                    iconName: "search"; Accessible.name: screen.tr("session_search")
                    enabled: !screen.owner.busy && searchInput.text.trim().length > 0
                    onClicked: screen.searchNow()
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
                text: screen.tr(screen.state.search_limit_reached ? "session_search_limit" : screen.state.search.complete ? "session_search_complete" : "session_search_partial")
                color: BrandTheme.colors.muted; font.pixelSize: 18
                wrapMode: Text.WordWrap; Layout.fillWidth: true
            }
            Text {
                visible: !!screen.state.search.query && (screen.state.search.matches || []).length === 0 && screen.state.search.complete
                text: screen.tr("session_search_empty"); color: BrandTheme.colors.muted; font.pixelSize: 20
            }
            ScrollView {
                id: searchScroll
                objectName: "sessionSearchScroll"
                Layout.fillWidth: true; Layout.fillHeight: true
                contentWidth: availableWidth; clip: true
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                ColumnLayout {
                    width: searchScroll.availableWidth; spacing: 14
                    Repeater {
                        id: searchRows
                        objectName: "sessionSearchRows"
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
                        visible: !!screen.state.search.next_cursor && !screen.state.search_limit_reached
                        text: screen.tr("session_more"); enabled: !screen.owner.busy
                        onClicked: { screen.rememberSearch(); screen.owner.moreSearch() }
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
                        screen.searchNow()
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
