import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "BrandTheme.js" as BrandTheme
import "ForecastGuidance.js" as ForecastGuidance
import "MoodTheme.js" as MoodTheme

Item {
    id: screen
    objectName: "djSessionScreen"
    property bool pollingAllowed: true
    readonly property bool liveViewOpen: visible && !historical && pollingAllowed
    readonly property bool historyViewOpen: visible && historical && pollingAllowed
    onLiveViewOpenChanged: syncSessionVisibility()
    property Item revealedFlowAction: null
    readonly property bool trackArtworkAvailable: playbackMetadata.visible && playbackSources.ready
    readonly property url trackArtworkSource: trackCover.source
    signal expandTrackArtwork()
    Item {
        anchors.fill: parent
        z: 10
        visible: !!screen.revealedFlowAction
        TapHandler {
            gesturePolicy: TapHandler.DragThreshold
            onTapped: eventPoint => {
                const action = screen.revealedFlowAction
                if (action && !action.contains(action.mapFromItem(screen, eventPoint.position)))
                    action.dismiss()
            }
        }
    }
    property var backend
    property bool historical: false
    property bool currentHistory: false
    readonly property bool compact: width < 900
    readonly property bool lowMemoryProfile: backend.releaseProfile === "pi-zero-2w-arm64"
    readonly property real ipadScale: compact ? 1 : Math.min(1.45, width / 835)
    readonly property bool idleWelcome: !historical && state.loaded && !state.session_id && !state.error
    readonly property bool sessionControlsVisible: !historical && state.session_id.length > 0 && !state.owner_read_only
    property var owner: backend.djSession
    property var state: owner.screenState
    readonly property var archiveSessions: visible && historical && !currentHistory && !state.timeline.session
        ? owner.archiveRows : []
    readonly property bool sessionVoiceAvailable: backend.sessionVoiceAvailable
    onSessionVoiceAvailableChanged: if (!sessionVoiceAvailable && choices && choices.field === "voice") choices.close()
    readonly property var projectedFlow: visible && !historical ? owner.flowRows : []
    property var displayedFlow: []
    property string displayedFlowKey: "[]"
    onProjectedFlowChanged: syncDisplayedFlow()
    function syncDisplayedFlow() {
        const rows = projectedFlow || []
        const key = JSON.stringify(rows)
        if (key !== displayedFlowKey) {
            displayedFlowKey = key
            displayedFlow = rows
        }
    }
    readonly property var contentDeletion: state.content_delete || ({})
    function deleteContent(kind, sessionId, identifier) {
        if (owner.beginContentDelete(kind, sessionId, identifier)) contentDeletePanel.open()
    }
    component SessionTimingCard: GlassCard {
        id: timingCard
        required property string startedAt
        property string endedAt: ""
        readonly property string started: screen.displayDate(startedAt)
        readonly property string ended: screen.displayDate(endedAt)
        visible: started.length > 0 || ended.length > 0
        Layout.fillWidth: true
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            FeatureIcon { iconName: "history"; Layout.preferredWidth: 24; Layout.preferredHeight: 24 }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4
                SessionTimingLine { date: timingCard.started; translationKey: "session_start_metadata" }
                SessionTimingLine { date: timingCard.ended; translationKey: "session_end_metadata" }
            }
        }
    }
    component SessionTimingLine: Text {
        required property string date
        required property string translationKey
        visible: date.length > 0
        text: screen.tr(translationKey).replace("%1", date)
        textFormat: Text.PlainText
        color: BrandTheme.colors.muted
        font.pixelSize: screen.compact ? 17 : 20
        wrapMode: Text.WordWrap
        Layout.fillWidth: true
    }
    component LiveMomentCard: GlassCard {
        id: liveCard
        objectName: "sessionLiveMomentCard"
        artworkTint: currentMomentArtworkFrame.artworkTint
        currentMoment: modelData.current
        trailingRevealWidth: deleteAction.revealWidth
        required property var modelData
        Layout.fillWidth: true
        property alias bodyItem: momentBody
        readonly property bool canAsk: screen.state.composer_available && liveSources.ready
            && !screen.owner.busy && !screen.owner.questionBusy
        function askAbout() {
            if (canAsk && screen.owner.selectMoment(screen.state.session_id, modelData.moment_id))
                composerPanel.open()
        }
        SessionFlowDelete {
            id: deleteAction
            objectName: "sessionDeleteLiveMoment"
            card: liveCard
            dismissalSurface: screen
            allowed: !!screen.contentDeletion.available && liveSources.ready
                && !screen.owner.busy && !screen.owner.questionBusy && !screen.showForecast
            scope: screen.composerContext + "|" + modelData.moment_id
            actionLabel: screen.tr("session_content_delete_action")
            onDeleteRequested: screen.deleteContent("moment", screen.state.session_id, modelData.moment_id)
        }
        ColumnLayout {
            objectName: "sessionMomentArtworkCard"
            visible: liveSources.ready && !!screen.owner.momentArtwork.source && modelData.current && screen.owner.momentArtwork.moment_id === modelData.moment_id && artworkSource.ready
            Layout.fillWidth: true
            GlassArtworkFrame {
                Connections {
                    target: screen.owner
                    function onArtworkAboutToChange() { currentMomentArtworkFrame.invalidatePalette() }
                }
                id: currentMomentArtworkFrame
                objectName: "sessionMomentArtworkFrame"
                backend: screen.backend; imageItem: currentMomentArtworkImage
                leaseKey: screen.scopeProfileId + "|" + screen.state.session_id + "|" + modelData.moment_id
                admissionCheck: function() {
                    var art = screen.owner.momentArtwork
                    return modelData.current && liveSources.ready && artworkSource.ready && !!art.source && art.moment_id === modelData.moment_id
                }
                Layout.preferredWidth: 100 * (screen.owner.momentArtwork.width || 100) / Math.max(screen.owner.momentArtwork.width || 100, screen.owner.momentArtwork.height || 100)
                Layout.preferredHeight: 100 * (screen.owner.momentArtwork.height || 100) / Math.max(screen.owner.momentArtwork.width || 100, screen.owner.momentArtwork.height || 100)
                Layout.alignment: Qt.AlignLeft
                Image {
                    id: currentMomentArtworkImage
                    objectName: "sessionMomentArtworkImage"
                    sourceSize: screen.lowMemoryProfile ? Qt.size(192, 192) : Qt.size(0, 0)
                    source: parent.visible ? (screen.owner.momentArtwork.source || "") : ""
                    cache: false; asynchronous: true; retainWhileLoading: false
                    fillMode: Image.PreserveAspectFit
                    anchors.fill: parent
                    Accessible.name: screen.owner.momentArtwork.artist || ""
                }
            }
            SessionAttribution { id: artworkSource; requiresSpotify: true; spotifyURL: screen.owner.momentArtwork.source_url || ""; Layout.fillWidth: true }
        }
        RowLayout {
            visible: liveSources.ready
            Layout.fillWidth: true
            spacing: screen.compact ? 12 : 16
            DJSessionMenuSymbol {
                objectName: "sessionCurrentMomentIdentity"
                visible: modelData.current
                iconColor: BrandTheme.colors.purple
                Layout.preferredWidth: screen.compact ? 52 : 76
                Layout.preferredHeight: Layout.preferredWidth
                Layout.alignment: Qt.AlignTop
                Accessible.ignored: true
            }
            ColumnLayout {
                Layout.fillWidth: true
                Text { text: modelData.title; textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 26; font.bold: true; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                Text {
                    id: momentBody
                    objectName: "sessionLiveMomentBody"
                    text: modelData.body; textFormat: Text.PlainText
                    color: BrandTheme.colors.text; font.pixelSize: 23
                    wrapMode: Text.WordWrap; Layout.fillWidth: true
                    TapHandler { enabled: liveCard.canAsk; onTapped: liveCard.askAbout() }
                }
            }
        }
        GlassButton {
            objectName: "sessionPrepareArtwork"
            visible: liveSources.ready && modelData.current && screen.state.artwork_prepare.available && screen.state.artwork_prepare.moment_id === modelData.moment_id
            text: screen.tr(screen.state.artwork_prepare.status === "loading" ? "session_artwork_loading" : "session_artwork_load")
            enabled: !screen.owner.busy && !screen.owner.questionBusy
            onClicked: screen.owner.prepareArtwork(screen.state.session_id, modelData.moment_id)
        }
        Text {
            objectName: "sessionPrepareArtworkStatus"
            visible: modelData.current && liveSources.ready && (screen.state.artwork_prepare.status === "unavailable" || screen.state.artwork_prepare.status === "uncertain")
            text: screen.tr(screen.state.artwork_prepare.status === "uncertain" ? "session_artwork_uncertain" : "session_artwork_unavailable")
            textFormat: Text.PlainText; color: BrandTheme.colors.muted; font.pixelSize: 20; wrapMode: Text.WordWrap; Layout.fillWidth: true
        }
        GlassButton {
            visible: screen.state.composer_available && liveSources.ready
            text: screen.tr("session_ask_about"); enabled: liveCard.canAsk
            onClicked: liveCard.askAbout()
        }
        SessionAttribution {
            id: liveSources
            bulletinSources: modelData.bulletin_sources || []
            sources: bulletinSources.length ? [] : modelData.display_sources || []
            requiresSpotify: modelData.requires_spotify_attribution || false
            spotifyURL: modelData.spotify_source_url || ""
            Layout.fillWidth: true
        }

    }
    readonly property string scopeProfileId: state.owner_profile_id || backend.activeProfileId
    readonly property string artworkTint: {
        if (!visible || historical) return ""
        if (showForecast) return forecastArtworkFrame.artworkTint
        if (trackArtworkFrame.artworkTint) return trackArtworkFrame.artworkTint
        if (!liveMomentRows) return ""
        for (var i = 0; i < liveMomentRows.count; i++) {
            var card = liveMomentRows.itemAt(i)
            if (card && card.visible && card.modelData.current) return card.artworkTint
        }
        return ""
    }
    property string draft: ""
    property bool followQuestionReply: false
    property string pendingReplyId: ""
    readonly property string composerContext: state.session_id + "|" + scopeProfileId + "|" + (state.owner_epoch || 0)
    readonly property string playbackMenuScope: JSON.stringify([
        state.playback.item_id || "", state.playback.source_url || "", state.playback.target_name || ""
    ])
    onPlaybackMenuScopeChanged: {
        if (playbackPanel && playbackPanel.visible) playbackPanel.close()
        if (outputsPanel && outputsPanel.visible) outputsPanel.close()
    }
    property bool forecastMode: false
    readonly property bool showForecast: !historical && state.forecast_supported && forecastMode
    function syncMediaVisibility() {
        if (!owner) return
        owner.setContentDeleteVisible(visible && !showForecast)
        owner.setArchiveDeleteVisible(visible && historical && !currentHistory)
        owner.setPlaybackControlsVisible(visible && !historical && !showForecast)
        owner.setForecastImagesVisible(showForecast && visible)
        owner.setMomentArtworkVisible(visible && !historical && !showForecast)
        owner.setPlaybackArtworkVisible(visible && !historical && !showForecast)
    }
    function syncSessionVisibility() {
        if (owner) owner.setViewActive(liveViewOpen)
    }
    Component.onCompleted: {
        syncDisplayedFlow()
        syncSessionVisibility()
        syncMediaVisibility()
    }
    onShowForecastChanged: { if (showForecast) { outputsPanel.close(); playbackPanel.close() } if (!showForecast) clearForecastReading(); syncMediaVisibility() }
    onStateChanged: {
        if (contentDeletePanel && contentDeletePanel.opened && state.content_delete
                && (!state.content_delete.status
                    || (!state.content_delete.available && !state.content_delete.status_available)))
            contentDeletePanel.close()
        if (archiveDeletePanel && archiveDeletePanel.opened && state.archive_delete
                && !state.archive_delete.status && !state.archive_delete.running) archiveDeletePanel.close()
        var control = state.playback_control
        if (!control) return
        if (playbackPanel && (!control.available
                || (playbackPanel.controlView === "volume" && !control.volume_supported)
                || (playbackPanel.controlView === "favorite" && !control.favorite))) playbackPanel.close()
        if (outputsPanel && (!control.available || !control.outputs_supported)) outputsPanel.close()
    }
    onComposerContextChanged: { clearForecastReading(); clearFlowReturn(); forecastMode = false; closeTransient(); if (historyReadPending && historyReadKind === "current") { historyRead.stop(); historyReadPending = false; navigate("session") } }
    function clearComposer() { followQuestionReply = false; pendingReplyId = ""; draft = ""; if (composeInput) composeInput.clear(); if (composerPanel) composerPanel.close(); if (owner) owner.clearSelection() }
    function submitQuestion() {
        // A local demo answer can arrive before sendQuestion returns.
        if (backend.demoMode) followQuestionReply = true
        if (!owner.sendQuestion(composeInput.text)) {
            if (backend.demoMode) followQuestionReply = false
            return
        }
        forecastMode = false
        followQuestionReply = true
        draft = ""
        composeInput.clear()
        composerPanel.close()
    }
    // A position descriptor grants no image or text retention.
    property var forecastReading: null
    property int forecastReadingTries: 0
    property bool forecastReadingApplied: false
    property string forecastLayoutMark: ""
    function clearForecastReading() { forecastReadingRestore.stop(); forecastReading = null }
    function rememberForecastReading() {
        clearForecastReading()
        var flick = forecastScroll.contentItem
        if (!visible || !showForecast || flick.dragging || flick.moving || state.forecast.revision === undefined) return
        for (var i = 0; i < forecastRows.count; i++) {
            var card = forecastRows.itemAt(i)
            if (!card) continue
            var y = card.mapToItem(flick, 0, 0).y
            if (y <= 0 && y + card.height > 0 && isFinite(y) && Math.abs(y) <= 1000000) {
                forecastReading = {session: state.session_id, profile: scopeProfileId,
                    revision: state.forecast.revision, id: card.modelData.id, offset: y}
                forecastReadingTries = 0; forecastReadingApplied = false; forecastLayoutMark = ""
                return
            }
        }
    }
    Timer {
        id: forecastReadingRestore
        objectName: "sessionForecastReadingRestore"
        interval: 32
        onTriggered: {
            var saved = screen.forecastReading
            var flick = forecastScroll.contentItem
            if (!saved || !screen.visible || !screen.showForecast || flick.dragging || flick.moving ||
                saved.session !== screen.state.session_id || saved.profile !== screen.scopeProfileId ||
                saved.revision !== screen.state.forecast.revision) { screen.clearForecastReading(); return }
            forecastContent.ensurePolished()
            var target = null
            for (var i = 0; i < forecastRows.count; i++) {
                var card = forecastRows.itemAt(i)
                if (card && card.modelData.id === saved.id) { target = card; break }
            }
            screen.forecastReadingTries++
            if (!target) { screen.clearForecastReading(); return }
            var mark = [forecastContent.implicitHeight, flick.contentHeight, flick.height, target.y, target.height].join("|")
            if (mark !== screen.forecastLayoutMark) {
                screen.forecastLayoutMark = mark; screen.forecastReadingApplied = false
                if (screen.forecastReadingTries < 8) forecastReadingRestore.restart()
                else screen.clearForecastReading()
                return
            }
            var destination = Math.max(0, Math.min(flick.contentY + target.mapToItem(flick, 0, 0).y - saved.offset, Math.max(0, flick.contentHeight - flick.height)))
            if (screen.forecastReadingApplied && Math.abs(flick.contentY - destination) < 1) { screen.clearForecastReading(); return }
            flick.contentY = destination; screen.forecastReadingApplied = true
            if (screen.forecastReadingTries < 8) forecastReadingRestore.restart()
            else screen.clearForecastReading()
        }
    }
    Connections {
        target: forecastScroll.contentItem
        function onMovementStarted() { screen.clearForecastReading() }
        function onDraggingChanged() { if (forecastScroll.contentItem.dragging) screen.clearForecastReading() }
    }
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
    function clearFlowReturn() { flowReturnRestore.stop(); flowReturnRestore.artworkTries = 0; flowReturnRestore.artworkLayout = ""; flowReturnRestore.resetIfMissing = true; flowReturn = null }
    function rememberFlow() {
        clearFlowReturn()
        if (historical || showForecast || !state.session_id) return
        followQuestionReply = false
        replyRestore.stop()
        currentReplyPosition.stop()
        pendingQuestionPosition.stop()
        // Use actual visible order, including current-only replies above saved rows.
        var best = null
        var groups = [liveMomentRows, conversationRows]
        for (var g = 0; g < groups.length; g++) {
            for (var i = 0; i < groups[g].count; i++) {
                var card = flowCardAt(groups[g], i)
                if (!card || !card.visible) continue
                var y = card.mapToItem(historyScroll.contentItem, 0, 0).y
                if (y + card.height > 0 && y < historyScroll.contentItem.height && isFinite(y) && Math.abs(y) <= 1000000 && (!best || y < best.offset)) {
                    best = {session: state.session_id, profile: scopeProfileId,
                        kind: card.modelData.entry_id ? "conversation" : "moment",
                        id: card.modelData.entry_id || card.modelData.moment_id, offset: y}
                }
            }
        }
        if (currentReplyCard.visible && state.current_reply.reply_id) {
            var replyY = currentReplyCard.mapToItem(historyScroll.contentItem, 0, 0).y
            if (replyY + currentReplyCard.height > 0 && replyY < historyScroll.contentItem.height && isFinite(replyY) && Math.abs(replyY) <= 1000000 && (!best || replyY < best.offset)) {
                best = {session: state.session_id, profile: scopeProfileId,
                    kind: "current_reply", id: state.current_reply.reply_id, offset: replyY}
            }
        }
        // Playback is a navigation fallback only; existing admitted prose keeps priority.
        if (!best && playbackMetadata.visible && playbackSources.ready && state.playback.item_id) {
            var playbackY = playbackMetadata.mapToItem(historyScroll.contentItem, 0, 0).y
            if (playbackY + playbackMetadata.height > 0 && playbackY < historyScroll.contentItem.height && isFinite(playbackY) && Math.abs(playbackY) <= 1000000) {
                best = {session: state.session_id, profile: scopeProfileId,
                    kind: "playback", id: state.playback.item_id, offset: playbackY}
            }
        }
        flowReturn = best
    }
    function rememberArtworkReading() {
        for (var i = 0; i < liveMomentRows.count; i++) {
            var card = liveMomentRows.itemAt(i)
            var body = card ? card.bodyItem : null
            if (!body || !body.visible) continue
            var y = body.mapToItem(historyScroll.contentItem, 0, 0).y
            if (y <= 0 && y + body.height > 0 && isFinite(y) && Math.abs(y) <= 1000000) {
                clearFlowReturn()
                flowReturn = {session: state.session_id, profile: scopeProfileId,
                    kind: "moment_text", id: card.modelData.moment_id, offset: y}
                return
            }
        }
        rememberFlow()
    }
    function flowIdentityPresent(saved) {
        if (!saved || typeof saved.id !== "string" || saved.id.length === 0 ||
                typeof saved.offset !== "number" || !isFinite(saved.offset) || Math.abs(saved.offset) > 1000000) return false
        if (saved.kind === "playback") return state.playback.item_id === saved.id && playbackSources.ready
        if (saved.kind === "current_reply") return state.current_reply.reply_id === saved.id
        if (saved.kind === "moment" || saved.kind === "moment_text") return state.moments.some(function(row) { return row.moment_id === saved.id }) ||
            displayedFlow.some(function(item) {
                var row = item.contribution
                return !item.bulletin && row.kind === "dj_moment" && row.session_id === state.session_id && row.moment_id === saved.id
            })
        if (saved.kind === "conversation") return state.retained_flow.some(function(row) { return row.entry_id === saved.id })
        return false
    }
    function flowCardAt(rows, index) {
        var delegate = rows.itemAt(index)
        return rows === conversationRows && delegate ? delegate.item : delegate
    }
    function findFlowCard(field, identity, match) {
        var groups = [liveMomentRows, conversationRows]
        for (var g = 0; g < groups.length; g++) {
            for (var i = 0; i < groups[g].count; i++) {
                var card = flowCardAt(groups[g], i)
                if (card && card.visible && card.modelData[field] === identity && match(card.modelData)) return card
            }
        }
        return null
    }
    function flowTarget(saved) {
        if (saved.kind === "playback") return playbackMetadata.visible ? playbackMetadata : null
        if (saved.kind === "current_reply") return currentReplyCard.visible ? currentReplyCard : null
        var nativeRow = saved.kind === "moment" || saved.kind === "moment_text"
        var card = findFlowCard(nativeRow ? "moment_id" : "entry_id", saved.id,
                                function(row) { return !nativeRow || !row.entry_id })
        if (!card && nativeRow) {
            card = findFlowCard("moment_id", saved.id, function(row) {
                return row.kind === "dj_moment" && row.session_id === state.session_id
            })
        } else if (!card) {
            // The canonical entry must still authorize matching the exact Moment.
            var entries = state.retained_flow.filter(function(row) {
                return row.entry_id === saved.id && row.kind === "dj_moment" && row.session_id === state.session_id
            })
            if (entries.length === 1 && typeof entries[0].moment_id === "string")
                card = findFlowCard("moment_id", entries[0].moment_id, function(row) { return !row.entry_id })
        }
        return card && saved.kind === "moment_text" ? card.bodyItem : card
    }
    Timer {
        id: flowReturnRestore
        objectName: "sessionArtworkReadingRestore"
        interval: 32
        property int artworkTries: 0
        property bool resetIfMissing: true
        property string artworkLayout: ""
        onTriggered: {
            var saved = screen.flowReturn
            if (!saved) return
            var flick = historyScroll.contentItem
            if (!screen.visible || screen.historical || screen.showForecast || screen.followQuestionReply || flick.dragging || flick.moving) { screen.clearFlowReturn(); return }
            // Re-resolve admission and the visual item on every bounded attempt.
            if (saved.session !== screen.state.session_id || saved.profile !== screen.scopeProfileId || !screen.flowIdentityPresent(saved)) {
                if (resetIfMissing) flick.contentY = 0
                screen.clearFlowReturn(); return
            }
            historyContent.ensurePolished()
            var target = screen.flowTarget(saved)
            artworkTries++
            if (!target || !target.visible || target.height <= 0 || flick.contentHeight + 1 < historyContent.implicitHeight) {
                if (artworkTries < 8) restart()
                else { if (resetIfMissing) flick.contentY = 0; screen.clearFlowReturn() }
                return
            }
            target.ensurePolished(); flick.ensurePolished()
            var delta = target.mapToItem(flick, 0, 0).y - saved.offset
            flick.contentY = Math.max(0, Math.min(flick.contentY + delta, Math.max(0, flick.contentHeight - flick.height)))
            var mark = [historyContent.implicitHeight, flick.contentHeight, flick.height, target.width, target.height, target.mapToItem(historyContent, 0, 0).y].join("|")
            var settled = artworkLayout === mark && Math.abs(target.mapToItem(flick, 0, 0).y - saved.offset) <= 1
            artworkLayout = mark
            if (!settled && artworkTries < 8) restart()
            else screen.clearFlowReturn()
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
        historyReadProfile = scopeProfileId
        navigate("session-history")
        owner.closeSaved()
        historyRead.restart()
    }
    function openArchive() {
        clearFlowReturn()
        historyReadPending = true
        historyReadKind = "archive"
        historyReadProfile = scopeProfileId
        navigate("history")
        owner.closeSaved()
        historyRead.restart()
    }
    Timer {
        id: historyRead
        interval: 0
        onTriggered: {
            if (screen.historyReadPending && screen.visible && screen.historical && screen.historyReadProfile === screen.scopeProfileId && !screen.owner.busy) {
                if (screen.historyReadKind === "archive" && !screen.currentHistory) screen.owner.loadHistory()
                else if (screen.historyReadKind === "current" && screen.currentHistory && screen.historyReadSession === screen.state.session_id) screen.owner.readCurrentHistory()
                screen.historyReadPending = false
                screen.historyReadSession = ""
                screen.historyReadProfile = ""
            }
        }
    }
    readonly property bool historyNavigationBlocked: searchPanel.visible || archiveDeletePanel.visible || contentDeletePanel.visible
        || moreChoices.visible || connectionInfo.visible || choices.visible
    function navigateBackFromHistory() {
        if (!historical) return
        if (currentHistory) { owner.closeSaved(); navigate("session") }
        else if (state.timeline.session) returnArchiveDetail()
        else { owner.closeSaved(); navigate("more") }
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
                archiveReturn = {id: row.modelData.session_id, profile: scopeProfileId, offset: y}
                return
            }
        }
    }
    function openArchiveSession(sessionId) {
        if (!visible || !historical || currentHistory || state.timeline.session || owner.busy || archiveIntent) return
        if (!archiveSessions.some(function(row) { return row.session_id === sessionId })) return
        rememberArchive(); archiveDetailReturn = archiveReturn; archiveReturn = null
        owner.openSaved(sessionId)
    }
    function returnArchiveDetail() {
        var saved = archiveDetailReturn
        owner.closeSaved()
        archiveDetailReturn = null; archiveReturn = saved
        archiveIntent = {profile: scopeProfileId}
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
        archiveIntent = {profile: scopeProfileId}
        archiveRead.restart()
    }
    Timer {
        id: archiveRead; interval: 0
        onTriggered: {
            var intent = screen.archiveIntent
            if (!intent || screen.owner.busy) return
            if (screen.visible && screen.historical && !screen.currentHistory && !screen.state.timeline.session && intent.profile === screen.scopeProfileId) { screen.archiveReadActive = true; screen.owner.refreshArchive() }
            screen.archiveIntent = null
        }
    }
    Timer {
        id: archivePosition; objectName: "sessionArchivePositionTimer"; interval: 32
        onTriggered: {
            var saved = screen.archiveReturn
            var flick = historyScroll.contentItem
            if (!screen.visible || !screen.historical || screen.currentHistory || screen.state.timeline.session || !saved || saved.profile !== screen.scopeProfileId || flick.dragging) { screen.archiveReturn = null; return }
            if (!saved.id) { flick.contentY = 0; screen.archiveReturn = null; return }
            historyContent.ensurePolished()
            var target = null
            for (var i = 0; i < archiveRows.count; i++) {
                var card = archiveRows.itemAt(i)
                if (card && card.modelData.session_id === saved.id) { target = card; break }
            }
            screen.archivePositionTries++
            var ready = target && archiveRows.count === screen.archiveSessions.length && flick.contentHeight + 1 >= historyContent.implicitHeight
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
        searchRefreshIntent = {session: state.search.session_id, query: state.search.query, profile: scopeProfileId}
        searchRead.restart()
    }
    Timer {
        id: searchRead; interval: 0
        onTriggered: {
            var intent = screen.searchRefreshIntent
            if (!intent || screen.owner.busy) return
            if (searchPanel.opened && intent.profile === screen.scopeProfileId && intent.session === screen.state.search.session_id && intent.query === screen.state.search.query) screen.owner.refreshSearch()
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
        if (outputsPanel) outputsPanel.close()
        if (playbackPanel) playbackPanel.close()
        if (searchPanel) searchPanel.close()
        if (searchInput) searchInput.clear()
        if (choices) choices.close()
        if (moreChoices) moreChoices.close()
        if (connectionInfo) connectionInfo.close()
        if (endConfirmation) endConfirmation.close()
        if (archiveDeletePanel) archiveDeletePanel.close()
        if (contentDeletePanel) contentDeletePanel.close()
        if (owner) owner.clearSearch()
    }
    onVisibleChanged: { syncMediaVisibility(); if (!visible) { clearForecastReading(); cancelArchiveRead(); if (owner) owner.clearArchive(); clearFlowReturn(); historyRead.stop(); historyReadProfile = ""; historyReadSession = ""; historyReadPending = false; readingRestore.stop(); pendingReadingAnchor = ""; closeTransient() } }
    onHistoricalChanged: { if (historical) { outputsPanel.close(); playbackPanel.close() } syncMediaVisibility(); if (!historical) { archiveDetailReturn = null; cancelArchiveRead(); if (owner) owner.clearArchive() } readingRestore.stop(); pendingReadingAnchor = ""; readingOffset = 0; if (!historical && flowReturn) { historyScroll.contentItem.cancelFlick(); flowReturnRestore.restart() } }
    onSearchTargetChanged: { if (searchPanel) searchPanel.close(); if (searchInput) searchInput.clear(); if (owner) owner.clearSearch() }
    signal openVibeScape(real pickerTop)
    signal navigate(string destination)
    function tr(key) { backend.translationVersion; return backend.t(key) }
    function displayDate(value) { backend.translationVersion; return owner.formatTimestamp(value || "") }
    function savedDurationSuffix(header) {
        backend.translationVersion
        var duration = owner.formatSavedDuration(header || ({}))
        return duration ? " · " + duration : ""
    }
    function toolbarValue(field) {
        if (backend.demoMode) return owner.demoPreferences[field] || ""
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
        if (!sessionControlsVisible || (field === "voice" && !sessionVoiceAvailable)) return
        choices.sessionId = state.session_id
        choices.profileId = scopeProfileId
        choices.field = field
        choices.editToken = backend.sharedSettings.edit_token || ""
        choices.x = Math.max(12, Math.min(button.mapToItem(screen, 0, 0).x, width - choices.width - 12))
        choices.open()
    }
    Timer {
        objectName: "sessionRuntimePollTimer"
        interval: screen.backend.sessionRefreshSeconds * 1000
        running: screen.liveViewOpen && screen.backend.paired && !screen.searchRefreshPending
        repeat: true
        triggeredOnStart: true
        onTriggered: if (screen.liveViewOpen) screen.owner.poll()
    }
    Timer {
        interval: 3000
        running: screen.historyViewOpen && screen.backend.paired && !screen.historyReadPending && !screen.searchRefreshPending
        repeat: true
        triggeredOnStart: true
        onTriggered: if (screen.historyViewOpen && !screen.currentHistory && !screen.state.history_loaded) screen.owner.loadHistory()
    }
    Timer { objectName: "sessionHistoryRevalidationTimer"; interval: 15000; running: screen.historyViewOpen && screen.backend.paired; repeat: true; onTriggered: { if (!screen.state.saved_open_retry) screen.refreshHistory() } }
    Timer {
        id: replyRestore
        interval: 32
        onTriggered: {
            if (!screen.visible || screen.historical || !screen.followQuestionReply) return
            for (var i = 0; i < conversationRows.count; i++) {
                var card = flowCardAt(conversationRows, i)
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
        id: pendingQuestionPosition; objectName: "sessionPendingQuestionPosition"; interval: 32
        property string messageId: ""
        property int tries: 0
        property string layoutMark: ""
        onTriggered: {
            var flick = historyScroll.contentItem
            if (!screen.visible || screen.historical || !screen.followQuestionReply || !screen.state.pending_question.text ||
                    messageId !== screen.state.pending_question.client_message_id || flick.dragging || flick.moving) { messageId = ""; return }
            historyContent.ensurePolished(); pendingQuestionCard.ensurePolished()
            flick.contentY = Math.max(0, Math.min(flick.contentY + pendingQuestionCard.mapToItem(flick, 0, 0).y - 12, Math.max(0, flick.contentHeight - flick.height)))
            var mark = [historyContent.implicitHeight, flick.contentHeight, flick.height, pendingQuestionCard.height, pendingQuestionCard.y].join("|")
            var settled = layoutMark === mark && Math.abs(pendingQuestionCard.mapToItem(flick, 0, 0).y - 12) <= 1
            layoutMark = mark; tries++
            if (!settled && tries < 8) restart()
            else messageId = ""
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
        property string flowDragContext: ""
        property string automaticLoadContext: ""
        property real flowDragStart: 0
        function onDraggingChanged() {
            var flick = historyScroll.contentItem
            if (!flick.dragging) return
            flowDragContext = flowLoadOlder.visible && screen.visible ? screen.composerContext : ""
            flowDragStart = flick.contentY
            archivePosition.stop()
            screen.archiveReturn = null
            screen.followQuestionReply = false
            readingRestore.stop()
            if (!screen.historical) screen.clearFlowReturn()
        }
        function onMovementEnded() {
            var dragContext = flowDragContext
            flowDragContext = ""
            var flick = historyScroll.contentItem
            if (!dragContext || dragContext !== screen.composerContext || dragContext === automaticLoadContext
                    || !screen.visible || !flowLoadOlder.visible || !flowLoadOlder.enabled
                    || !flick.atYEnd || flick.contentY <= flowDragStart) return
            automaticLoadContext = dragContext
            screen.owner.expandFlow(screen.state.session_id)
        }
    }
    Connections {
        target: screen.owner
        function onFlowExpansionAboutToChange() {
            if (!screen.visible || screen.historical || screen.showForecast || screen.followQuestionReply
                    || historyScroll.contentItem.moving || screen.flowReturn) return
            screen.rememberFlow()
            if (screen.flowReturn) {
                flowReturnRestore.resetIfMissing = false
                flowReturnRestore.restart()
            }
        }
        function onFlowIdleHeaderAboutToChange() {
            if (screen.historical || !jumpCurrent.visible || screen.followQuestionReply || historyScroll.contentItem.moving || screen.flowReturn) return
            screen.rememberArtworkReading()
            if (screen.flowReturn) {
                flowReturnRestore.resetIfMissing = false
                flowReturnRestore.restart()
            }
        }
        function onArtworkAboutToChange() { if (screen.visible && !screen.historical && !screen.showForecast && !screen.followQuestionReply && !historyScroll.contentItem.moving && !screen.flowReturn) screen.rememberArtworkReading() }
        function onArtworkChanged() { if (screen.visible && !screen.historical && !screen.showForecast && !screen.followQuestionReply && !historyScroll.contentItem.moving && screen.flowReturn) { flowReturnRestore.artworkTries = 0; flowReturnRestore.artworkLayout = ""; flowReturnRestore.restart() } }
        function onForecastImageAboutToChange() { screen.rememberForecastReading() }
        function onForecastImageChanged() { if (screen.forecastReading) forecastReadingRestore.restart() }
        function onPendingQuestionReady() { pendingQuestionPosition.messageId = screen.state.pending_question.client_message_id || ""; pendingQuestionPosition.tries = 0; pendingQuestionPosition.layoutMark = ""; pendingQuestionPosition.restart() }
        function onCurrentReplyReady() { currentReplyPosition.restart() }
        function onQuestionConfirmed(entryId) { if (screen.followQuestionReply) { screen.pendingReplyId = entryId; replyRestore.restart() } }
        function onSelectionInvalidated() { screen.clearComposer() }
        function onTimelineUpdated(anchor) { screen.restoreReading(anchor) }
        function onTimelinePositioned(anchor, offset) { screen.readingOffset = offset; screen.restoreReading(anchor) }
        function onHistoryUpdated() { screen.scheduleArchivePosition() }
        function onArchiveInvalidated() {
            screen.cancelArchiveRead(); screen.archiveReturn = null; screen.archiveDetailReturn = null
            screen.searchReturn = null; screen.cancelSearchRead(); searchPanel.close()
            readingRestore.stop(); screen.pendingReadingAnchor = ""; screen.readingOffset = 0
            if (screen.historyReadKind === "archive") { historyRead.stop(); screen.historyReadPending = false }
        }
        function onArchivePositioned(sessionId, offset) {
            if (!screen.visible || !screen.historical || screen.currentHistory || screen.state.timeline.session || historyScroll.contentItem.dragging) return
            screen.archiveReturn = {id: sessionId, profile: screen.scopeProfileId, offset: offset}
            screen.scheduleArchivePosition()
        }
        function onChanged() { if (!screen.owner.busy) screen.archiveReadActive = false; if (!screen.historical || screen.currentHistory || screen.state.timeline.session) screen.cancelArchiveRead(); if (screen.archiveIntent && !screen.owner.busy) archiveRead.restart(); if (!screen.state.search.query) screen.cancelSearchRead(); if (screen.historyReadPending && !screen.owner.busy) historyRead.restart(); if (screen.searchRefreshPending && !screen.owner.busy) searchRead.restart() }
        function onSearchUpdated() { searchPosition.restart() }
        function onContextCleared() { screen.clearForecastReading(); screen.cancelArchiveRead(); screen.clearFlowReturn(); historyRead.stop(); screen.historyReadProfile = ""; screen.historyReadSession = ""; readingRestore.stop(); screen.pendingReadingAnchor = ""; screen.readingOffset = 0; screen.closeTransient(); if (screen.historical) screen.navigate(screen.currentHistory ? "session" : "more"); screen.historyReadPending = false }
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
        z: screen.idleWelcome && !screen.compact ? 2 : 0
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
                    visible: !screen.compact && screen.sessionControlsVisible && screen.sessionVoiceAvailable
                    iconName: "voice"; Accessible.name: screen.tr("shared_field_voice")
                    implicitWidth: 52; background: Item {}
                    onClicked: screen.openChoice("voice", voiceButton)
                }
                SessionPlaybackShortcut {
                    id: toolbarVolume
                    objectName: "sessionToolbarVolume"
                    visible: !screen.compact && screen.sessionControlsVisible && !screen.showForecast
                        && !!screen.state.playback_control.available && !!screen.state.playback_control.volume_supported
                    enabled: !!screen.state.playback_control.enabled
                    iconName: "voice"; Accessible.name: screen.tr("volume")
                    implicitWidth: 52; background: Item {}
                    onCurrentTrackClicked: {
                        if (screen.owner.readPlaybackVolume(screen.state.session_id, screen.state.playback.item_id))
                            playbackPanel.openFrom(toolbarVolume, "volume")
                    }
                }
                SessionPlaybackShortcut {
                    id: toolbarOutput
                    objectName: "sessionToolbarOutput"
                    visible: !screen.compact && screen.sessionControlsVisible && !screen.showForecast
                        && !!screen.state.playback_control.available && !!screen.state.playback_control.outputs_supported
                    enabled: !!screen.state.playback_control.enabled
                    iconName: "output"; Accessible.name: screen.tr("session_output_title")
                    implicitWidth: 52; background: Item {}
                    onCurrentTrackClicked: outputsPanel.openForCurrentItem(toolbarOutput)
                }
                GlassButton {
                    objectName: "sessionToolbarVibeCast"
                    visible: screen.sessionControlsVisible && !screen.showForecast && screen.state.vibecast.available
                    enabled: !screen.state.vibecast.busy
                    iconName: "vibecast"; Accessible.name: "VibeCast"
                    implicitWidth: 52; background: Item {}
                    onClicked: { if (screen.owner.openVibeCast()) vibeCastPanel.open() }
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
                    visible: screen.sessionControlsVisible || screen.idleWelcome
                    iconName: "globe"; foregroundColor: screen.idleWelcome ? BrandTheme.colors.cyan : BrandTheme.colors.text
                    Accessible.name: screen.tr("connection_type")
                    implicitWidth: 52; background: Item {}
                    onClicked: connectionInfo.open()
                }
                GlassButton {
                    objectName: "sessionRefresh"
                    iconName: screen.owner.refreshing ? "" : "refresh"
                    Accessible.name: screen.tr("refresh")
                    implicitWidth: 52; background: Item {}
                    enabled: !screen.owner.busy || screen.owner.refreshing
                    onClicked: {
                        if (screen.owner.refreshing) return
                        if (screen.historical) screen.refreshHistory(); else screen.owner.refresh()
                        screen.backend.pollSharedSettings()
                    }
                    BusyIndicator {
                        objectName: "sessionRefreshSpinner"
                        anchors.centerIn: parent
                        width: 28
                        height: width
                        visible: screen.owner.refreshing
                        running: visible
                    }
                }
            }
        }
    }

    SessionModeStrip {
        id: modeSwitch
        translate: screen.tr
        mood: screen.state.mood
        forecastAvailable: screen.state.forecast_supported
        vibeScapeAvailable: screen.backend.releaseProfile === "pi5-arm64" && screen.state.runtime_state === "active"
            && !screen.state.profile_confirmation_required && !screen.state.owner_read_only
        showingForecast: screen.showForecast
        visible: !screen.historical && (forecastAvailable || vibeScapeAvailable)
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: toolbar.bottom
        anchors.topMargin: 10
        onFlowRequested: screen.forecastMode = false
        onForecastRequested: screen.forecastMode = true
        onVibeScapeRequested: screen.openVibeScape(modeSwitch.mapToItem(null, 0, 0).y)
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
            id: forecastContent
            width: parent.width; spacing: 20
            Text { text: screen.tr("session_forecast"); textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: screen.compact ? 30 : 40; font.bold: true; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            Text { visible: !!screen.state.forecast.source_url; text: screen.tr("session_forecast_source"); textFormat: Text.PlainText; color: BrandTheme.colors.muted; font.pixelSize: 18 }
            SessionAttribution { id: forecastSource; requiresSpotify: !!screen.state.forecast.source_url; spotifyURL: screen.state.forecast.source_url || ""; Layout.fillWidth: true }
            GlassCard {
                objectName: "sessionForecastArtistCard"
                artworkTint: forecastArtworkFrame.artworkTint
                visible: !!screen.owner.forecastImage.source && imageAttribution.ready
                Layout.fillWidth: true
                GlassArtworkFrame {
                    Connections {
                        target: screen.owner
                        function onForecastImageAboutToChange() { forecastArtworkFrame.invalidatePalette() }
                    }
                    id: forecastArtworkFrame
                    objectName: "sessionForecastArtworkFrame"
                    backend: screen.backend; imageItem: forecastArtworkImage
                    leaseKey: screen.scopeProfileId + "|" + screen.state.session_id + "|" + (screen.owner.forecastImage.source_url || "")
                    admissionCheck: function() { return screen.showForecast && imageAttribution.ready && !!screen.owner.forecastImage.source }
                    Layout.fillWidth: true; Layout.preferredHeight: screen.compact ? 300 : 440
                    Image {
                        id: forecastArtworkImage
                        objectName: "sessionForecastArtistImage"
                        sourceSize: screen.lowMemoryProfile ? Qt.size(720, 360) : Qt.size(0, 0)
                        anchors.fill: parent
                        source: imageAttribution.ready ? (screen.owner.forecastImage.source || "") : ""
                        cache: false; asynchronous: true; retainWhileLoading: false
                        fillMode: Image.PreserveAspectFit
                        Accessible.name: screen.tr("session_forecast_artist_image") + ": " + (screen.owner.forecastImage.artist || "")
                    }
                }
                Text { text: screen.owner.forecastImage.artist || ""; textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 23; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                SessionAttribution { id: imageAttribution; requiresSpotify: true; spotifyURL: screen.owner.forecastImage.source_url || ""; Layout.fillWidth: true }
            }
            Repeater {
                id: forecastRows
                objectName: "sessionForecastRows"
                model: forecastSource.ready ? screen.state.forecast.sections : []
                GlassCard {
                    required property var modelData
                    objectName: "sessionForecastSection-" + modelData.id
                    Layout.fillWidth: true
                    RowLayout {
                        spacing: 10; Layout.fillWidth: true
                        FeatureIcon {
                            objectName: "sessionForecastSectionIcon"
                            iconName: modelData.id === "current" ? "play" : modelData.id === "guidance" ? "forecast_clock" : "forecast_target"
                            Layout.preferredWidth: 26; Layout.preferredHeight: 26; Layout.alignment: Qt.AlignTop
                            Accessible.ignored: true
                        }
                        Text {
                            text: modelData.title; textFormat: Text.PlainText; color: BrandTheme.colors.text
                            font.pixelSize: 25; font.bold: true; wrapMode: Text.Wrap; Layout.fillWidth: true
                            Accessible.role: Accessible.Heading
                        }
                    }
                    Text { text: screen.tr("session_forecast_" + modelData.claim_type); textFormat: Text.PlainText; color: BrandTheme.colors.muted; font.pixelSize: 18; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    readonly property var guidance: ForecastGuidance.split(modelData.id, modelData.text)
                    Text {
                        objectName: "sessionForecastSectionBody"
                        text: guidance ? guidance.intro : modelData.text
                        textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 23
                        wrapMode: Text.Wrap; Layout.fillWidth: true
                    }
                    ColumnLayout {
                        visible: !!guidance
                        spacing: 7; Layout.fillWidth: true
                        Repeater {
                            model: guidance ? guidance.tracks : []
                            RowLayout {
                                required property string modelData
                                spacing: 8; Layout.fillWidth: true
                                Text {
                                    text: "•"; color: BrandTheme.colors.text; font.pixelSize: 23
                                    Layout.alignment: Qt.AlignTop; Accessible.ignored: true
                                }
                                Text {
                                    objectName: "sessionForecastQueueTrack"; text: modelData
                                    textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 23
                                    wrapMode: Text.Wrap; Layout.fillWidth: true
                                }
                            }
                        }
                    }
                    Text {
                        objectName: "sessionForecastQueueNote"; visible: !!guidance
                        text: guidance ? guidance.note : ""
                        textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 23
                        wrapMode: Text.Wrap; Layout.fillWidth: true
                    }
                }
            }
            Text { visible: screen.state.forecast.sections.length === 0; text: screen.tr("session_forecast_empty"); textFormat: Text.PlainText; color: BrandTheme.colors.muted; font.pixelSize: 23; wrapMode: Text.WordWrap; Layout.fillWidth: true }
        }
    }
    ScrollView {
        id: historyScroll
        visible: !screen.showForecast
        objectName: "sessionHistoryScroll"
        readonly property bool spaciousFlow: !screen.compact && !screen.historical
            && screen.state.loaded && screen.state.runtime_state === "active" && !screen.state.error
        readonly property int flowSpacing: spaciousFlow ? 26 : 22
        anchors.top: screen.idleWelcome && !screen.compact ? parent.top : modeSwitch.visible ? modeSwitch.bottom : toolbar.bottom; anchors.bottom: parent.bottom
        anchors.left: parent.left; anchors.right: parent.right
        anchors.margins: 20
        anchors.topMargin: screen.idleWelcome && !screen.compact ? 44 : spaciousFlow ? flowSpacing : 20
        anchors.bottomMargin: composerDock.visible ? composerDock.height + 144 : 132
        clip: true; contentWidth: availableWidth
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ColumnLayout {
            id: historyContent
            width: parent.width; spacing: historyScroll.flowSpacing
            Text {
                id: historyHeading
                objectName: "sessionFlowHeading"
                visible: !screen.idleWelcome && (screen.historical || screen.backend.demoMode || !screen.state.loaded
                    || !screen.state.session_id || screen.state.runtime_state !== "active" || !!screen.state.error)
                text: screen.tr(screen.historical ? (screen.state.timeline.session ? "session_history_title" : "session_history") : "session_title") + (screen.backend.demoMode ? " · " + screen.tr("demo_mode") : "")
                color: BrandTheme.colors.text; font.pixelSize: screen.width > 800 ? 40 : 30; font.bold: true
                textFormat: Text.PlainText; Layout.fillWidth: true
            }
            VinylPlaceholder {
                objectName: "sessionWaitingVinyl"
                visible: !screen.historical && screen.state.session_id.length > 0 && screen.state.loaded && !screen.state.playback.item_id &&
                    screen.state.moments.length === 0 && screen.state.retained_flow.length === 0 &&
                    (!screen.state.profile_confirmation_required || screen.backend.demoMode)
                Layout.preferredWidth: Math.min(parent.width, screen.compact ? screen.height * 0.38 : 520)
                Layout.preferredHeight: width
                Layout.alignment: Qt.AlignHCenter
            }
            GlassCard {
                visible: screen.state.error.length > 0
                Layout.fillWidth: true
                Text {
                    text: screen.tr(screen.state.error === "uncertain" ? "session_uncertain" : (screen.state.error === "profile_unavailable" || screen.state.error === "profile_required") ? "session_profile_missing" : "session_error")
                    color: BrandTheme.colors.warning; font.pixelSize: 21; wrapMode: Text.WordWrap
                    Layout.fillWidth: true; textFormat: Text.PlainText
                }
                GlassButton {
                    objectName: "sessionArchiveRetry"
                    visible: screen.historical && !screen.currentHistory && !screen.state.timeline.session
                        && screen.state.history_available
                        && ["offline", "unavailable", "conflict"].indexOf(screen.state.error) >= 0
                    enabled: !screen.owner.busy && !screen.historyReadPending
                        && !screen.archiveReadActive && !screen.archiveIntent
                    iconName: "refresh"
                    text: screen.tr(screen.state.saved_open_retry ? "session_saved_reopen" : "session_archive_retry")
                    onClicked: {
                        if (screen.state.saved_open_retry) screen.owner.retrySavedOpen()
                        else screen.refreshHistory()
                    }
                }
            }
            Text {
                visible: !screen.historical && !!screen.state.owner_read_only
                text: screen.tr("session_owner_read_only"); textFormat: Text.PlainText
                color: BrandTheme.colors.muted; font.pixelSize: 21
                wrapMode: Text.WordWrap; Layout.fillWidth: true
            }
            SessionStartCard {
                visible: screen.idleWelcome
                Layout.fillWidth: true
                backend: screen.backend
                busy: screen.owner.busy
                onStartRequested: function(mood) { screen.owner.start(mood) }
            }
            // Current music context precedes admitted native Moments, as in the Apple header.
            GlassCard {
                id: playbackMetadata
                objectName: "sessionPlaybackMetadata"
                artworkTint: screen.artworkTint
                visible: !screen.historical && !!screen.state.playback.item_id
                Layout.fillWidth: true
                padding: screen.compact ? 16 : 0
                background: GlassSurface { visible: screen.compact; artworkTint: playbackMetadata.artworkTint }
                GridLayout {
                    columns: 2
                    columnSpacing: screen.compact ? 12 : 24 * screen.ipadScale
                    rowSpacing: screen.compact ? 8 : 10
                    Layout.fillWidth: true
                    Item {
                        id: coverTile
                        visible: screen.trackArtworkAvailable
                        Layout.row: 0
                        Layout.column: 0
                        Layout.rowSpan: screen.compact ? 1 : 4
                        Layout.preferredWidth: screen.compact ? 60 : Math.round(270 * screen.ipadScale)
                        Layout.preferredHeight: Layout.preferredWidth
                        Layout.alignment: Qt.AlignTop

                        AbstractButton {
                            objectName: "sessionExpandTrackArtwork"
                            anchors.fill: parent
                            Accessible.name: screen.tr("track_artwork")
                            onClicked: screen.expandTrackArtwork()
                            background: Item {
                                VinylPlaceholder {
                                    anchors.fill: parent
                                    visible: trackCover.status !== Image.Ready
                                    radius: screen.compact ? 14 : 24
                                }
                                GlassArtworkFrame {
                                    id: trackArtworkFrame
                                    anchors.fill: parent
                                    visible: trackCover.status === Image.Ready
                                    radius: screen.compact ? 14 : 24
                                    padding: screen.compact ? 3 : 6
                                    backend: screen.backend
                                    imageItem: trackCover
                                    leaseKey: screen.state.playback.item_id || ""
                                    active: screen.visible && !screen.historical && !screen.showForecast
                                    admissionCheck: function() {
                                        return screen.owner.playbackArtwork.session_id === screen.state.session_id
                                            && screen.owner.playbackArtwork.item_id === screen.state.playback.item_id
                                            && !!screen.owner.playbackArtwork.source
                                    }
                                    Image {
                                        id: trackCover
                                        objectName: "sessionTrackArtwork"
                                        sourceSize: screen.lowMemoryProfile ? Qt.size(128, 128) : Qt.size(0, 0)
                                        anchors.fill: parent
                                        source: coverTile.visible && trackArtworkFrame.admittedCover
                                            ? (screen.owner.playbackArtwork.source || "") : ""
                                        cache: false
                                        asynchronous: true
                                        retainWhileLoading: false
                                        fillMode: Image.PreserveAspectFit
                                    }
                                    readonly property bool admittedCover: admissionCheck()
                                }
                            }
                        }

                        SessionTransportButton {
                            id: vinylButton
                            objectName: "sessionPlaybackVinyl"
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            width: screen.compact ? 44 : 60
                            height: width
                            visible: !!screen.state.playback_control.available
                            transportSurfaceReady: visible && !playbackPanel.visible && !outputsPanel.visible
                            commandName: screen.state.playback.state === "playing" ? "pause" : "play"
                            iconName: commandName
                            Accessible.name: screen.tr(commandName)
                            padding: 0
                        }
                    }
                    RowLayout {
                        id: trackTitleRow
                        Layout.row: 0
                        Layout.column: 1
                        Layout.alignment: Qt.AlignTop
                        Layout.fillWidth: true
                        spacing: 12
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: screen.compact ? 4 : 12
                            objectName: "sessionExpandTrackMetadata"
                            TapHandler {
                                enabled: screen.trackArtworkAvailable
                                onTapped: screen.expandTrackArtwork()
                            }
                            Text { visible: playbackSources.ready && text.length > 0; text: screen.state.playback.title || ""; textFormat: Text.PlainText; font.pixelSize: screen.compact ? 24 : 30; font.bold: true; color: BrandTheme.colors.text; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                            Text {
                                visible: screen.compact && playbackSources.ready && text.length > 0
                                text: [screen.state.playback.artist || "", screen.state.playback.album || ""].filter(function(value) { return value.length > 0 }).join(" · ")
                                textFormat: Text.PlainText; font.pixelSize: 18; color: BrandTheme.colors.muted; wrapMode: Text.WordWrap; Layout.fillWidth: true
                            }
                            Text { visible: !screen.compact && playbackSources.ready && text.length > 0; text: screen.state.playback.artist || ""; textFormat: Text.PlainText; font.pixelSize: 23; color: BrandTheme.colors.muted; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                            Text { visible: !screen.compact && playbackSources.ready && text.length > 0; text: screen.state.playback.album || ""; textFormat: Text.PlainText; font.pixelSize: 19; color: BrandTheme.colors.muted; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                        }
                        SessionPlaybackShortcut {
                            id: currentOutputButton
                            Layout.column: screen.compact ? -1 : 0
                            parent: screen.compact ? trackTitleRow : trackOutputRow
                            objectName: "sessionCurrentOutput"
                            readonly property bool offered: playbackSources.ready && !!screen.state.playback_control.available
                                && !!screen.state.playback_control.outputs_supported
                            visible: offered
                            enabled: !!screen.state.playback_control.enabled
                            iconName: "voice"
                            text: screen.compact ? "" : (screen.state.playback.target_name || "")
                            Accessible.name: screen.tr("session_output_title")
                            Accessible.description: screen.state.playback.target_name || ""
                            Layout.preferredWidth: text.length ? Math.min(220 * screen.ipadScale, implicitWidth) : 48 * screen.ipadScale
                            Layout.preferredHeight: 48 * screen.ipadScale
                            Layout.alignment: Qt.AlignTop
                            onCurrentTrackClicked: outputsPanel.openForCurrentItem(currentOutputButton)
                        }
                        SessionPlaybackShortcut {
                            id: currentVolumeButton
                            Layout.column: screen.compact ? -1 : 2
                            parent: screen.compact ? trackTitleRow : trackOutputRow
                            objectName: "sessionCurrentVolume"
                            visible: playbackSources.ready && !!screen.state.playback_control.available
                                && !!screen.state.playback_control.volume_supported
                            enabled: !!screen.state.playback_control.enabled
                            iconName: "voice"
                            Accessible.name: screen.tr("volume")
                            Layout.preferredWidth: 48 * screen.ipadScale; Layout.preferredHeight: 48 * screen.ipadScale; Layout.alignment: Qt.AlignTop
                            onCurrentTrackClicked: {
                                if (screen.owner.readPlaybackVolume(screen.state.session_id, screen.state.playback.item_id)) {
                                    playbackPanel.openFrom(currentVolumeButton, "volume")
                                }
                            }
                        }
                        SessionPlaybackShortcut {
                            id: currentFavoriteButton
                            Layout.column: screen.compact ? -1 : 0
                            parent: screen.compact ? trackTitleRow : trackFavoriteRow
                            objectName: "sessionCurrentFavorite"
                            visible: playbackSources.ready && !!screen.state.playback_control.available
                                && !!screen.state.playback_control.favorite
                            enabled: !!screen.state.playback_control.enabled
                            iconName: "heart"
                            Accessible.name: screen.tr("session_favorite_read")
                            Layout.preferredWidth: 48 * screen.ipadScale; Layout.preferredHeight: 48 * screen.ipadScale; Layout.alignment: Qt.AlignTop
                            onCurrentTrackClicked: {
                                if (screen.owner.readPlaybackFavorite(screen.state.session_id, screen.state.playback.item_id)) {
                                    playbackPanel.openFrom(currentFavoriteButton, "favorite")
                                }
                            }
                        }
                        GlassButton {
                            id: playbackMoreButton
                            Layout.column: screen.compact ? -1 : 1
                            parent: screen.compact ? trackTitleRow : trackFavoriteRow
                            objectName: "sessionPlaybackOpen"
                            visible: playbackSources.ready && !!screen.state.playback_control.available
                                && (screen.compact || !progressControl.visible)
                            iconName: "more"; Accessible.name: screen.tr("session_playback_controls")
                            Layout.preferredWidth: 48 * screen.ipadScale; Layout.preferredHeight: 48 * screen.ipadScale; Layout.alignment: Qt.AlignTop
                            onClicked: playbackPanel.openFrom(playbackMoreButton, "all")
                        }
                        SessionAttribution {
                            id: playbackSources
                            requiresSpotify: !!screen.state.playback.requires_spotify_attribution
                            spotifyURL: screen.state.playback.source_url || ""
                            visible: requiresSpotify
                            Layout.preferredWidth: 90; Layout.alignment: Qt.AlignTop
                        }
                    }
                    AbstractButton {
                        id: progressControl
                        objectName: "sessionPlaybackProgress"
                        visible: playbackSources.ready && screen.state.playback.time_label !== undefined
                        enabled: !!screen.state.playback_control.available
                        implicitHeight: enabled ? Math.max(44, contentItem.implicitHeight) : contentItem.implicitHeight
                        Layout.row: 1
                        Layout.column: screen.compact ? 0 : 1
                        Layout.columnSpan: screen.compact ? 2 : 1
                        Layout.fillWidth: true
                        Accessible.name: screen.tr("session_playback_controls")
                        Accessible.description: screen.state.playback.time_label || ""
                        Accessible.ignored: !enabled
                        onClicked: playbackPanel.openFrom(progressControl, "all")
                        background: GlassSurface {
                            visible: progressControl.down || (progressControl.visualFocus && !playbackPanel.visible)
                            radius: height / 2
                            interactive: true
                            pressed: progressControl.down
                            focused: progressControl.visualFocus
                        }
                        contentItem: RowLayout {
                            Row {
                                id: playbackMeter
                                objectName: "sessionPlaybackMeter"
                                readonly property bool playing: screen.state.playback.state === "playing"
                                readonly property bool animating: visible && playing && GlassStyle.motionEnabled
                                    && screen.backend.releaseProfile !== "pi-zero-2w-arm64"
                                    && Qt.application.state === Qt.ApplicationActive
                                property real phase: 0
                                spacing: 2
                                Layout.preferredWidth: 18
                                Layout.preferredHeight: 20
                                Accessible.ignored: true
                                Timer {
                                    interval: 80
                                    repeat: true
                                    running: playbackMeter.animating
                                    onTriggered: playbackMeter.phase = (playbackMeter.phase + 0.32) % (2 * Math.PI)
                                }
                                Repeater {
                                    model: [0.85, 0.35, 0.62, 0.25]
                                    Rectangle {
                                        required property int index
                                        required property real modelData
                                        readonly property real level: playbackMeter.animating
                                            ? 0.18 + 0.82 * (0.5 + 0.5 * Math.sin(playbackMeter.phase + index * 1.7))
                                            : playbackMeter.playing ? modelData : 0.16
                                        anchors.verticalCenter: parent.verticalCenter
                                        width: 3
                                        height: Math.max(3, playbackMeter.height * level)
                                        radius: 1
                                        color: BrandTheme.colors.text
                                    }
                                }
                            }
                            ProgressBar {
                                id: playbackProgress
                                value: screen.state.playback.progress || 0; Layout.fillWidth: true
                                Accessible.name: screen.tr("now_playing")
                                Accessible.ignored: progressControl.enabled
                                background: Rectangle { implicitHeight: 6; radius: 3; color: BrandTheme.colors.text; opacity: 0.18 }
                                contentItem: Item {
                                    implicitHeight: 6
                                    Rectangle { width: playbackProgress.visualPosition * parent.width; height: parent.height; radius: 3; color: BrandTheme.colors.text }
                                }
                            }
                            Text { visible: screen.compact || !trackFavoriteRow.visible; text: screen.state.playback.time_label || ""; textFormat: Text.PlainText; font.pixelSize: screen.compact ? 16 : 18; color: BrandTheme.colors.muted }
                        }
                    }
                    GridLayout {
                        id: trackFavoriteRow
                        columns: 4
                        visible: !screen.compact && playbackSources.ready && (screen.state.playback.time_label !== undefined
                            || !!screen.state.playback_control.available)
                        Layout.row: 2
                        Layout.column: 1
                        Layout.fillWidth: true
                        Item { Layout.column: 2; Layout.fillWidth: true; Layout.preferredHeight: 1 }
                        Text {
                            Layout.column: 3
                            text: screen.state.playback.time_label || ""
                            textFormat: Text.PlainText
                            color: BrandTheme.colors.muted
                            font.pixelSize: 18
                        }
                    }
                    GridLayout {
                        id: trackOutputRow
                        columns: 3
                        visible: !screen.compact && playbackSources.ready && (!!screen.state.playback.target_name
                            || (!!screen.state.playback_control.available
                                && (!!screen.state.playback_control.outputs_supported || !!screen.state.playback_control.volume_supported)))
                        Layout.row: 3
                        Layout.column: 1
                        Layout.fillWidth: true
                        Text {
                            Layout.column: 0
                            visible: !currentOutputButton.offered && text.length > 0
                            text: screen.state.playback.target_name || ""
                            textFormat: Text.PlainText
                            color: BrandTheme.colors.muted
                            font.pixelSize: 18
                        }
                        Item { Layout.column: 1; Layout.fillWidth: true; Layout.preferredHeight: 1 }
                    }
                    RowLayout {
                        visible: screen.compact && playbackSources.ready && !!screen.state.playback.target_name
                        Layout.row: 2
                        Layout.column: 0
                        Layout.columnSpan: 2
                        Layout.fillWidth: true
                        FeatureIcon { iconName: "music"; Layout.preferredWidth: 22; Layout.preferredHeight: 22 }
                        Text { text: screen.state.playback.target_name || ""; textFormat: Text.PlainText; font.pixelSize: 19; color: BrandTheme.colors.muted; wrapMode: Text.WordWrap; Layout.fillWidth: true; Accessible.name: screen.tr("output_device") + ": " + text }
                    }
                }
            }
            GlassCard {
                id: waitingCard
                objectName: "sessionWaitingCard"
                readonly property bool confirmedIdle: screen.state.loaded && !screen.state.error
                    && !screen.backend.demoMode && !!screen.state.current_moment_idle
                    && !screen.state.moments.some(function(moment) { return moment.current })
                    && playbackSources.ready
                readonly property bool compactIdle: confirmedIdle && screen.state.playback.state === "playing"
                readonly property bool playbackPaused: !screen.state.error && playbackSources.ready
                    && screen.state.playback.state === "paused"
                readonly property bool emptyFlow: screen.state.moments.length === 0 && screen.state.retained_flow.length === 0
                visible: !screen.historical && screen.state.session_id.length > 0
                    && (emptyFlow || compactIdle || (confirmedIdle && playbackPaused))
                Layout.fillWidth: !compactIdle
                Layout.alignment: Qt.AlignLeft
                padding: compactIdle ? 14 : 22
                RowLayout {
                    Layout.fillWidth: true; spacing: 18
                    DJSessionMenuSymbol {
                        iconColor: BrandTheme.colors.purple
                        Layout.preferredWidth: 64
                        Layout.preferredHeight: 64
                        Accessible.role: Accessible.StaticText
                        Accessible.name: screen.tr("session_listening")
                        Accessible.ignored: !waitingCard.compactIdle
                    }
                    ColumnLayout {
                        visible: !waitingCard.compactIdle
                        Layout.fillWidth: true
                        Text {
                            objectName: "sessionWaitingTitle"
                            text: screen.tr(waitingCard.playbackPaused ? "session_playback_paused"
                                : screen.state.runtime_state === "opening" ? "session_starting"
                                : screen.state.runtime_state === "ending" ? "session_ending" : "session_listening")
                            textFormat: Text.PlainText
                            color: BrandTheme.colors.text; font.pixelSize: screen.compact ? 24 : 30
                            font.bold: true; wrapMode: Text.WordWrap; Layout.fillWidth: true
                        }
                        Text {
                            objectName: "sessionWaitingPausedDetail"
                            visible: waitingCard.playbackPaused
                            text: screen.tr("session_playback_paused_detail")
                            textFormat: Text.PlainText
                            color: BrandTheme.colors.muted; font.pixelSize: 22
                            wrapMode: Text.WordWrap; Layout.fillWidth: true
                        }
                    }
                }
                Text {
                    visible: screen.backend.demoMode
                    text: screen.tr("session_demo_body"); textFormat: Text.PlainText
                    color: BrandTheme.colors.muted; font.pixelSize: 22
                    wrapMode: Text.WordWrap; Layout.fillWidth: true
                }
                RowLayout {
                    Layout.fillWidth: true
                    visible: waitingCard.emptyFlow && !waitingCard.compactIdle && !screen.state.owner_read_only
                    Item { Layout.fillWidth: true }
                    GlassButton {
                        objectName: "sessionExpandedEnd"
                        iconName: "end"; Accessible.name: screen.tr("session_end")
                        enabled: !screen.owner.lifecycleBusy && screen.state.runtime_state !== "ending"
                        onClicked: { endConfirmation.expectedSessionId = screen.state.session_id; endConfirmation.open() }
                    }
                }
            }
            GlassButton {
                objectName: "sessionContentDeleteStatus"
                visible: !!screen.contentDeletion.status_available
                text: screen.tr("session_delete_status_action")
                enabled: !screen.owner.busy && !screen.owner.questionBusy
                onClicked: { if (screen.owner.checkContentDeleteStatus()) contentDeletePanel.open() }
            }
            Repeater {
                id: liveMomentRows
                objectName: "sessionLiveMomentRows"
                model: screen.visible && !screen.historical ? screen.state.moments.filter(function(moment) {
                    return moment.current || !moment.flow_bulletin
                }) : []
                LiveMomentCard {}
            }
            RowLayout {
                visible: !screen.historical && screen.backend.demoMode && !!screen.state.playback.item_id
                Layout.alignment: Qt.AlignHCenter
                GlassButton {
                    iconName: "previous"; Accessible.name: screen.tr("previous")
                    onClicked: screen.backend.previous()
                }
                GlassButton {
                    iconName: screen.backend.playing ? "pause" : "play"
                    Accessible.name: screen.tr(screen.backend.playing ? "pause" : "play")
                    onClicked: screen.backend.togglePlay()
                }
                GlassButton {
                    iconName: "next"; Accessible.name: screen.tr("next")
                    onClicked: screen.backend.next()
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
            Text {
                objectName: "sessionRetainedFlowLabel"
                visible: !screen.historical && screen.displayedFlow.length > 0
                    && !screen.displayedFlow.some(function(row) { return row.bulletin })
                text: screen.tr(screen.contentDeletion.available || screen.contentDeletion.status_available
                    ? "session_saved_contributions" : "session_retained_flow"); textFormat: Text.PlainText
                color: BrandTheme.colors.muted; font.pixelSize: 18; wrapMode: Text.WordWrap; Layout.fillWidth: true
            }
            Repeater {
                id: conversationRows
                objectName: "sessionConversationRows"
                // Presentation only: canonical owner/model order remains ascending.
                model: !screen.historical ? screen.displayedFlow : []
                Loader {
                    id: flowRow
                    required property var modelData
                    Layout.fillWidth: true
                    sourceComponent: modelData.bulletin ? bulletin : retained
                    Component {
                        id: bulletin
                        LiveMomentCard { modelData: flowRow.modelData.contribution }
                    }
                    Component {
                        id: retained
                        SessionRetainedEntry {
                            objectName: "sessionConversationCard"
                            readonly property var modelData: flowRow.modelData.contribution
                            entry: modelData; translate: screen.tr; dateText: screen.displayDate(modelData.occurred_at)
                            selectionAvailable: screen.state.composer_available
                            selectionBusy: screen.owner.busy || screen.owner.questionBusy
                            deletionAvailable: !!screen.contentDeletion.available && !screen.showForecast
                            flowDeletionScope: screen.composerContext + "|" + modelData.entry_id
                            flowSurface: screen
                            onDeleteEntry: (sessionId, entryId) => screen.deleteContent("entry", sessionId, entryId)
                            onAskAbout: (sessionId, entryId) => { if (screen.owner.selectFlowEntry(sessionId, entryId)) composerPanel.open() }
                        }
                    }
                }
            }
            SessionTimingCard {
                objectName: "sessionFlowStartMetadata"
                startedAt: !screen.historical && screen.state.runtime_state === "active"
                    ? (screen.state.started_at || "") : ""
            }
            GlassButton {
                id: flowLoadOlder
                objectName: "sessionFlowLoadOlder"
                visible: !screen.historical && !!screen.state.flow_more
                text: screen.tr("session_more"); enabled: !screen.owner.busy && !screen.owner.questionBusy
                onClicked: screen.owner.expandFlow(screen.state.session_id)
            }
            Text {
                objectName: "sessionFlowHistoryHint"
                visible: !screen.historical && !!screen.state.flow_history_hint
                text: screen.tr("session_flow_history_hint")
                textFormat: Text.PlainText
                color: BrandTheme.colors.muted
                font.pixelSize: 18
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
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
                onClicked: screen.navigateBackFromHistory()
            }
            GlassButton {
                objectName: "sessionDeleteAllSaved"
                visible: screen.historical && !screen.currentHistory && !!screen.state.archive_delete && screen.state.archive_delete.bulk_available
                text: screen.tr("session_delete_all_action"); iconName: "trash"; tint: BrandTheme.colors.danger; Layout.fillWidth: true
                enabled: !screen.owner.busy && !screen.state.archive_delete.blocked
                onClicked: { if (screen.owner.beginBulkHistoryDelete()) archiveDeletePanel.open() }
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
                model: screen.archiveSessions
                GlassButton {
                    required property var modelData
                    id: archiveRow
                    Layout.fillWidth: true
                    implicitHeight: Math.max(78, contentItem.implicitHeight + topPadding + bottomPadding)
                    objectName: "sessionArchiveRow"
                    contentItem: RowLayout {
                        spacing: 12
                        SavedMoodMark {
                            objectName: "sessionArchiveMoodMark"
                            metrics: archiveRow.modelData.summary_metrics || []
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Text {
                                text: archiveRow.text
                                font: archiveRow.font
                                color: archiveRow.foregroundColor
                                textFormat: Text.PlainText
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                            Repeater {
                                objectName: "sessionArchiveSummary"
                                model: archiveRow.modelData.summary_metrics || []
                                SessionSummaryMetric { compactMetric: true }
                            }
                        }
                    }
                    enabled: !screen.owner.busy && !screen.archiveIntent
                    text: screen.tr("session_title") + " · " + screen.displayDate(modelData.started_at || modelData.created_at)
                        + screen.savedDurationSuffix(modelData)
                        + (modelData.lifecycle_status === "INTERRUPTED" ? "\n" + screen.tr("session_history_interrupted") : "")
                    onClicked: screen.openArchiveSession(modelData.session_id)
                }
            }
            Text {
                objectName: "sessionArchiveEmpty"
                visible: screen.historical && !screen.currentHistory && !screen.owner.busy && !screen.state.error
                    && screen.state.history_loaded && screen.archiveSessions.length === 0 && !screen.state.timeline.session
                text: screen.tr(screen.state.archive_older_window || screen.state.has_more_sessions || screen.state.has_older_sessions ? "session_archive_window_empty" : "session_history_empty"); color: BrandTheme.colors.muted; font.pixelSize: 22
            }
            Text {
                visible: screen.historical && !!screen.state.timeline.session
                text: screen.tr(screen.state.archive_delete.available ? "session_saved_title" : "session_history_view_readonly") + screen.savedDurationSuffix(screen.state.timeline.session); color: BrandTheme.colors.muted; font.pixelSize: 20
            }
            Text {
                objectName: "sessionSavedInterruptedStatus"
                visible: screen.historical && !!screen.state.timeline.session
                    && screen.state.timeline.session.lifecycle_status === "INTERRUPTED"
                text: screen.tr("session_history_interrupted")
                textFormat: Text.PlainText
                color: BrandTheme.colors.muted
                font.pixelSize: 17
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
            }
            GlassButton {
                visible: screen.historical && !!screen.state.timeline.session
                text: screen.tr("session_history_first"); enabled: !screen.owner.busy
                onClicked: screen.owner.firstEntries()
            }
            RowLayout {
                visible: screen.historical && !screen.currentHistory && !!screen.state.timeline.session
                Layout.fillWidth: true
                spacing: 12
                SavedMoodMark {
                    objectName: "sessionSavedMoodMark"
                    metrics: screen.state.saved_summary || []
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    Repeater {
                        objectName: "sessionSavedSummary"
                        model: screen.state.saved_summary || []
                        SessionSummaryMetric { objectName: "sessionSavedSummaryMetric" }
                    }
                }
            }
            GlassButton {
                objectName: "sessionDeleteSaved"
                visible: screen.historical && !screen.currentHistory && !!screen.state.archive_delete && screen.state.archive_delete.available
                text: screen.tr("session_delete_action"); iconName: "trash"; primary: true; tint: BrandTheme.colors.danger
                enabled: !screen.owner.busy && !screen.state.archive_delete.blocked
                onClicked: { if (screen.owner.beginHistoryDelete((screen.state.timeline.session || {}).session_id || "")) archiveDeletePanel.open() }
            }
            Text {
                objectName: "sessionDeleteUncertain"
                visible: screen.historical && !!screen.state.archive_delete && screen.state.archive_delete.blocked
                text: screen.tr("session_delete_uncertain"); textFormat: Text.PlainText
                color: BrandTheme.colors.muted; font.pixelSize: 20; wrapMode: Text.WordWrap; Layout.fillWidth: true
            }
            GlassButton {
                objectName: "sessionDeleteStatus"
                visible: screen.historical && !!screen.state.archive_delete && screen.state.archive_delete.status_available
                text: screen.tr("session_delete_status_action"); enabled: !screen.owner.busy; Layout.fillWidth: true
                onClicked: { if (screen.owner.checkHistoryDeleteStatus()) archiveDeletePanel.open() }
            }
            GlassButton {
                objectName: "sessionDeleteRecovery"
                visible: screen.historical && !!screen.state.archive_delete && (screen.state.archive_delete.blocked || screen.state.archive_delete.status === "deleted")
                text: screen.tr("refresh"); enabled: !screen.owner.busy
                onClicked: screen.owner.recoverHistoryDelete()
            }
            Text {
                objectName: "sessionTimelineEmpty"
                visible: screen.historical && !!screen.state.timeline.session && !!screen.state.timeline.revision
                    && !screen.owner.busy && !screen.historyReadPending && !screen.state.error
                    && (screen.state.timeline.entries || []).length === 0
                text: screen.tr("session_timeline_empty")
                textFormat: Text.PlainText
                color: BrandTheme.colors.muted
                font.pixelSize: screen.compact ? 18 : 21
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Repeater {
                id: historyRows
                objectName: "sessionHistoryRows"
                model: screen.historical ? (screen.state.timeline.entries || []) : []
                SessionRetainedEntry {
                    required property var modelData
                    entry: modelData; translate: screen.tr; dateText: screen.displayDate(modelData.occurred_at)
                    selectionAvailable: screen.state.composer_available; selectionBusy: screen.owner.busy || screen.owner.questionBusy
                    deletionAvailable: !!screen.contentDeletion.available
                    onDeleteEntry: (sessionId, entryId) => screen.deleteContent("entry", sessionId, entryId)
                    onAskAbout: (sessionId, entryId) => { if (screen.owner.selectEntry(sessionId, entryId)) { screen.navigate("session"); composerPanel.open() } }
                }
            }
            SessionTimingCard {
                objectName: "sessionSavedStartMetadata"
                readonly property var header: screen.state.timeline.session || ({})
                startedAt: screen.historical && header.session_id && typeof header.started_at === "string"
                    ? header.started_at : ""
                readonly property var endStamp: header.lifecycle_status === "INTERRUPTED" ? header.interrupted_at
                    : header.lifecycle_status === "ENDED" ? header.ended_at : ""
                endedAt: screen.historical && header.session_id && typeof endStamp === "string" ? endStamp : ""
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
            BusyIndicator { visible: screen.owner.busy && !screen.owner.refreshing; running: visible; Layout.alignment: Qt.AlignHCenter }
        }
    }
    GlassButton {
        id: jumpCurrent
        objectName: "sessionJumpCurrent"
        readonly property real currentHeaderBottom: {
            if (screen.historical)
                return screen.state.timeline.session && historyHeading.visible ? historyHeading.y + historyHeading.height : 0
            for (var i = 0; i < liveMomentRows.count; i++) {
                var card = liveMomentRows.itemAt(i)
                if (card && card.modelData.current && card.visible)
                    return card.y + card.height
            }
            if (waitingCard.visible) return waitingCard.y + waitingCard.height
            if (playbackMetadata.visible && playbackSources.ready)
                return playbackMetadata.y + playbackMetadata.height
            return 0
        }
        visible: screen.visible && !screen.showForecast
            && (screen.historical ? !!screen.state.timeline.session : !!screen.state.session_id)
            && currentHeaderBottom > 0 && historyScroll.contentItem.contentY >= currentHeaderBottom
        enabled: !screen.historical || !screen.owner.busy
        anchors.right: historyScroll.right
        anchors.bottom: historyScroll.bottom
        anchors.margins: 8
        width: 52
        height: 52
        iconName: "arrow_up"
        Accessible.name: screen.tr(screen.historical ? "session_back_top" : "session_back_current")
        onClicked: {
            if (screen.historical) {
                readingRestore.stop()
                screen.pendingReadingAnchor = ""
                screen.readingOffset = 0
            }
            screen.followQuestionReply = false
            screen.pendingReplyId = ""
            replyRestore.stop()
            currentReplyPosition.stop()
            pendingQuestionPosition.stop()
            screen.clearFlowReturn()
            var flick = historyScroll.contentItem
            flick.cancelFlick()
            flick.contentY = flick.originY
        }
    }
    GlassSurface {
        id: composerDock
        objectName: "sessionComposerDock"
        visible: !screen.historical && !screen.showForecast && !searchPanel.visible
            && screen.state.composer_available
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom; anchors.bottomMargin: 120
        width: screen.compact ? parent.width - 40 : Math.min(1000, parent.width - 24) * 0.75
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
                    objectName: "openSessionComposer"
                    Accessible.name: screen.tr("session_question_placeholder")
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
    component SavedMoodMark: Rectangle {
        id: moodMark
        required property var metrics
        readonly property string moodKey: {
            const mood = metrics.find(metric => metric.label === "session_summary_mood"
                                      && metric.coverage === "complete")
            return MoodTheme.key(mood ? mood.value : "")
        }
        implicitWidth: screen.compact ? 42 : 52
        implicitHeight: implicitWidth
        Layout.alignment: Qt.AlignVCenter
        radius: width / 2
        border.width: 1
        border.color: moodKey === "default" ? BrandTheme.colors.border : MoodTheme.moodColor(moodKey, "focus")
        Accessible.ignored: true

        gradient: Gradient {
            GradientStop {
                position: 0
                color: moodMark.moodKey === "default" ? BrandTheme.colors.surfaceRaised
                    : MoodTheme.mix(BrandTheme.colors.surface, MoodTheme.moodColor(moodMark.moodKey, "gradientStart"), 0.35)
            }
            GradientStop { position: 1; color: BrandTheme.colors.surface }
        }
        FeatureIcon {
            objectName: "savedMoodIcon"
            anchors.centerIn: parent
            width: parent.width * 0.62
            height: width
            iconName: moodMark.moodKey === "default" ? "session" : "mood_" + moodMark.moodKey
        }
    }
    component SessionSummaryMetric: Text {
        required property var modelData
        property bool compactMetric: false
        readonly property string valueText: {
            if (modelData.coverage === "withdrawn") return screen.tr("session_summary_withdrawn")
            if (modelData.value === null) return screen.tr("session_summary_unknown")
            if (typeof modelData.value === "string")
                return screen.tr(modelData.value === "mixed" ? "session_summary_mixed" : "mood_" + modelData.value)
            const count = Number(modelData.value).toLocaleString(Qt.locale(screen.backend.language), "f", 0)
            return modelData.coverage === "partial" ? count + " · " + screen.tr("session_summary_partial") : count
        }
        text: screen.tr(modelData.label) + ": " + valueText
        textFormat: Text.PlainText
        color: BrandTheme.colors.muted
        font.pixelSize: compactMetric || screen.compact ? 17 : 20
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
    }
    component SessionPlaybackShortcut: GlassButton {
        signal currentTrackClicked()
        readonly property int transportEpoch: screen.state.playback_control.transport_epoch || 0
        readonly property string reportedOutput: screen.state.playback.target_name || ""
        property int pressedEpoch: 0

        onPressed: pressedEpoch = transportEpoch
        onCanceled: pressedEpoch = 0
        onReportedOutputChanged: pressedEpoch = 0
        onVisibleChanged: if (!visible) pressedEpoch = 0
        onEnabledChanged: if (!enabled) pressedEpoch = 0
        onClicked: {
            var epoch = pressedEpoch
            pressedEpoch = 0
            if (epoch && epoch === transportEpoch) currentTrackClicked()
        }
    }
    component SessionTransportButton: GlassButton {
        required property string commandName
        property int pressedEpoch: 0
        property bool transportSurfaceReady: playbackPanel.opened
        property bool round: false
        Layout.fillWidth: !round
        implicitWidth: round ? 46 * screen.ipadScale : Math.max(56, contentItem.implicitWidth + 36)
        implicitHeight: round ? 46 * screen.ipadScale : 56
        padding: round ? 10 : 14
        enabled: transportSurfaceReady && !!screen.state.playback_control.enabled
        onPressed: pressedEpoch = screen.state.playback_control.transport_epoch || 0
        onCanceled: pressedEpoch = 0
        onTransportSurfaceReadyChanged: if (!transportSurfaceReady) pressedEpoch = 0
        onClicked: {
            var epoch = pressedEpoch
            pressedEpoch = 0
            if (epoch && transportSurfaceReady)
                screen.owner.playbackCommand(screen.state.session_id, screen.state.playback.item_id, commandName, epoch)
        }
    }
    component AnchoredPlaybackPopup: GlassPopup {
        property rect sourceRect: Qt.rect(0, 0, 0, 0)
        readonly property bool anchored: sourceRect.width > 0
        readonly property real edgeMargin: 16
        function captureSource(source) {
            var top = source.mapToItem(screen, 0, 0)
            var bottom = source.mapToItem(screen, source.width, source.height)
            sourceRect = Qt.rect(top.x, top.y, bottom.x - top.x, bottom.y - top.y)
        }
        x: anchored
            ? Math.max(edgeMargin, Math.min(sourceRect.x + (sourceRect.width - width) / 2, screen.width - width - edgeMargin))
            : (screen.width - width) / 2
        y: {
            if (!anchored) return toolbar.y + toolbar.height + 8
            var below = sourceRect.y + sourceRect.height + 8
            var above = sourceRect.y - height - 8
            var lastTop = screen.height - height - edgeMargin
            if (below <= lastTop) return below
            if (above >= edgeMargin) return above
            return Math.max(edgeMargin, lastTop)
        }
        property int wideWidth: 380
        width: Math.min(screen.width - 32, screen.compact ? 520 : Math.round(wideWidth * screen.ipadScale))
        padding: 20; modal: true; dim: false
    }
    AnchoredPlaybackPopup {
        id: playbackPanel
        objectName: "sessionPlaybackPanel"
        property string controlView: "all"
        function openFrom(source, view) {
            captureSource(source)
            controlView = view
            open()
        }
        wideWidth: volumeOnly ? 320 : favoriteOnly ? 360 : 380
        readonly property bool volumeOnly: controlView === "volume"
        readonly property bool favoriteOnly: controlView === "favorite"
        onAboutToHide: { outputsPanel.close(); if (screen.owner) screen.owner.cancelPlaybackIntent() }
        height: Math.min(implicitHeight, Math.max(0, screen.height - 2 * edgeMargin),
                         !screen.compact && controlView === "all" ? 460 * screen.ipadScale : screen.height)
        onOpened: playbackScroll.contentItem.contentY = 0
        background: GlassSurface { elevated: true; popover: !screen.compact }
        contentItem: ColumnLayout {
            spacing: 12
            ScrollView {
                id: playbackScroll
                objectName: "sessionPlaybackScroll"
                clip: true
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 0
                implicitHeight: playbackOptions.implicitHeight
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                contentItem: Flickable {
                    contentWidth: width
                    contentHeight: playbackOptions.implicitHeight
                    flickableDirection: Flickable.VerticalFlick
                    boundsBehavior: Flickable.StopAtBounds
                    interactive: contentHeight > height
                    ColumnLayout {
                        id: playbackOptions
                        width: playbackScroll.availableWidth
                        spacing: 16
                        Text {
                            text: !screen.compact && playbackPanel.controlView === "all" ? screen.state.playback.title || screen.tr("session_playback_controls")
                                : screen.tr(playbackPanel.volumeOnly ? "volume" : playbackPanel.favoriteOnly ? "add_to_favorites" : "session_playback_controls")
                            textFormat: Text.PlainText; font.pixelSize: 25; font.bold: true
                            color: BrandTheme.colors.text; Layout.fillWidth: true; wrapMode: Text.WordWrap
                        }
                        Text {
                            text: playbackPanel.volumeOnly ? screen.state.playback.target_name || ""
                                : !screen.compact && playbackPanel.controlView === "all" ? screen.state.playback.artist || "" : screen.state.playback.title || ""
                            visible: text.length > 0
                            textFormat: Text.PlainText; font.pixelSize: 20; color: BrandTheme.colors.muted
                            Layout.fillWidth: true; wrapMode: Text.WordWrap
                        }
                        RowLayout {
                            visible: playbackPanel.controlView === "all"
                            Layout.fillWidth: screen.compact
                            Layout.alignment: Qt.AlignHCenter
                            spacing: 14
                            SessionTransportButton {
                                objectName: "sessionPlaybackPrevious"
                                round: !screen.compact
                                commandName: "previous"; iconName: "previous"
                                Accessible.name: screen.tr("previous")
                            }
                            SessionTransportButton {
                                objectName: "sessionPlaybackToggle"
                                round: !screen.compact
                                checked: round
                                commandName: screen.state.playback.state === "playing" ? "pause" : "play"
                                iconName: commandName
                                Accessible.name: screen.tr(commandName)
                            }
                            SessionTransportButton {
                                objectName: "sessionPlaybackNext"
                                round: !screen.compact
                                commandName: "next"; iconName: "next"
                                Accessible.name: screen.tr("next")
                            }
                        }
                        GlassButton {
                            objectName: "sessionPlaybackFavorite"
                            readonly property var observation: screen.state.playback_control.favorite_observation || ({})
                            readonly property bool known: typeof observation.liked === "boolean"
                            readonly property int currentLease: known ? observation.lease : 0
                            property int pressedEpoch: 0
                            property int pressedLease: 0
                            visible: !playbackPanel.volumeOnly && !!screen.state.playback_control.favorite
                            text: screen.tr(!known ? "session_favorite_read" : observation.liked ? "session_favorite_remove" : "session_favorite_add")
                            iconName: "heart"; checked: known && observation.liked
                            Layout.fillWidth: true; enabled: !!screen.state.playback_control.enabled
                            onPressed: {
                                pressedEpoch = screen.state.playback_control.transport_epoch || 0
                                pressedLease = currentLease
                            }
                            onCanceled: pressedEpoch = 0
                            onClicked: {
                                var epoch = pressedEpoch
                                pressedEpoch = 0
                                if (!playbackPanel.opened || !epoch || epoch !== screen.state.playback_control.transport_epoch
                                        || pressedLease !== currentLease) return
                                if (known) screen.owner.setPlaybackFavorite(screen.state.session_id, screen.state.playback.item_id, pressedLease, !observation.liked)
                                else screen.owner.readPlaybackFavorite(screen.state.session_id, screen.state.playback.item_id)
                            }
                        }
                        Text {
                            visible: !playbackPanel.volumeOnly && screen.state.playback_control.favorite_status === "unavailable"
                            text: screen.tr("session_favorite_unavailable"); textFormat: Text.PlainText
                            font.pixelSize: 18; color: BrandTheme.colors.muted; wrapMode: Text.WordWrap; Layout.fillWidth: true
                        }
                        ColumnLayout {
                            objectName: "sessionVolumeControls"
                            visible: !playbackPanel.favoriteOnly && !!screen.state.playback_control.volume_supported
                            Layout.fillWidth: true; spacing: 8
                            readonly property var observation: screen.state.playback_control.volume || ({})
                            readonly property bool known: typeof observation.percent === "number"
                            Text {
                                objectName: "sessionVolumeObserved"
                                text: parent.known ? screen.tr("volume") + ": " + parent.observation.percent + "%" : screen.tr(screen.state.playback_control.volume_status === "unavailable" ? "session_volume_unavailable" : "session_volume_unknown")
                                textFormat: Text.PlainText; color: BrandTheme.colors.text
                                font.pixelSize: 19; Layout.fillWidth: true; wrapMode: Text.WordWrap
                            }
                            Text {
                                text: parent.observation.output_name || ""
                                visible: text.length > 0; textFormat: Text.PlainText
                                color: BrandTheme.colors.muted; font.pixelSize: 16; Layout.fillWidth: true; wrapMode: Text.WordWrap
                            }
                            Text {
                                text: screen.tr("session_volume_limit"); textFormat: Text.PlainText
                                color: BrandTheme.colors.muted; font.pixelSize: 16; Layout.fillWidth: true; wrapMode: Text.WordWrap
                            }
                            Slider {
                                id: sessionVolumeSlider
                                objectName: "sessionVolumeSlider"
                                from: 0; to: 60; stepSize: 1; Layout.fillWidth: true
                                implicitHeight: 44
                                visible: parent.known && parent.observation.percent <= 60
                                enabled: !!screen.state.playback_control.enabled && parent.known
                                Accessible.name: screen.tr("volume")
                                readonly property int observationLease: parent.known ? parent.observation.lease : -1
                                onObservationLeaseChanged: volumePointer.intentLease = -1
                                onMoved: {
                                    if (!volumePointer.pressed && observationLease >= 0)
                                        screen.owner.setPlaybackVolume(screen.state.session_id, screen.state.playback.item_id, observationLease, Math.round(value))
                                }
                                MouseArea {
                                    id: volumePointer
                                    objectName: "sessionVolumePointer"
                                    anchors.fill: parent
                                    acceptedButtons: Qt.LeftButton
                                    property int intentLease: -1
                                    property int draft: 0

                                    function valueAt(x) {
                                        var slider = sessionVolumeSlider
                                        var halfHandle = slider.handle ? slider.handle.width / 2 : 0
                                        var travel = Math.max(1, slider.availableWidth - 2 * halfHandle)
                                        var position = Math.max(0, Math.min(1, (x - slider.leftPadding - halfHandle) / travel))
                                        return Math.round(slider.valueAt(slider.mirrored ? 1 - position : position))
                                    }

                                    onPressed: function(mouse) {
                                        sessionVolumeSlider.forceActiveFocus(Qt.MouseFocusReason)
                                        intentLease = sessionVolumeSlider.observationLease
                                        draft = valueAt(mouse.x)
                                    }
                                    onPositionChanged: function(mouse) {
                                        if (pressed && intentLease >= 0) draft = valueAt(mouse.x)
                                    }
                                    onReleased: function(mouse) {
                                        var lease = intentLease
                                        intentLease = -1
                                        if (lease >= 0 && lease === sessionVolumeSlider.observationLease
                                                && sessionVolumeSlider.enabled && sessionVolumeSlider.visible && playbackPanel.opened)
                                            screen.owner.setPlaybackVolume(screen.state.session_id, screen.state.playback.item_id, lease, valueAt(mouse.x))
                                    }
                                    // Losing the grab is not a user release.
                                    onCanceled: intentLease = -1
                                }
                                Binding {
                                    target: sessionVolumeSlider; property: "value"
                                    value: volumePointer.intentLease >= 0 ? volumePointer.draft
                                        : (sessionVolumeSlider.parent.known ? sessionVolumeSlider.parent.observation.percent : 0)
                                    restoreMode: Binding.RestoreNone
                                }
                            }
                            GlassButton {
                                objectName: "sessionVolumeReduce"
                                visible: parent.known && parent.observation.percent > 60
                                text: screen.tr("session_volume_reduce"); Layout.fillWidth: true
                                enabled: !!screen.state.playback_control.enabled
                                onClicked: screen.owner.setPlaybackVolume(screen.state.session_id, screen.state.playback.item_id, screen.state.playback_control.volume.lease, 60)
                            }
                            GlassButton {
                                objectName: "sessionVolumeRead"
                                text: screen.tr("session_volume_read"); Layout.fillWidth: true
                                enabled: !!screen.state.playback_control.enabled
                                onClicked: screen.owner.readPlaybackVolume(screen.state.session_id, screen.state.playback.item_id)
                            }
                        }
                        GlassButton {
                            id: menuOutputButton
                            objectName: "sessionOutputOpen"
                            visible: playbackPanel.controlView === "all" && !!screen.state.playback_control.outputs_supported
                            text: screen.tr("session_output_title"); Layout.fillWidth: true
                            enabled: !!screen.state.playback_control.enabled
                            onClicked: outputsPanel.openForCurrentItem(menuOutputButton)
                        }
                        Text {
                            objectName: "sessionPlaybackStatus"
                            visible: !!screen.state.playback_control.status
                            text: screen.tr((screen.state.playback_control.reading_volume || screen.state.playback_control.reading_favorite || screen.state.playback_control.reading_outputs) ? "loading" : screen.state.playback_control.status === "sending" ? "session_question_sending" : screen.state.playback_control.status === "accepted" ? "session_playback_sent" : "session_uncertain")
                            textFormat: Text.PlainText; font.pixelSize: 18; color: BrandTheme.colors.muted; wrapMode: Text.WordWrap; Layout.fillWidth: true
                        }

                    }
                }
            }
            RowLayout {
                Layout.fillWidth: true
                GlassButton { objectName: "sessionPlaybackRefresh"; text: screen.tr("refresh"); enabled: !screen.owner.busy; onClicked: screen.owner.refreshPlayback() }
                Item { Layout.fillWidth: true }
                GlassButton { objectName: "sessionPlaybackClose"; text: screen.tr("close"); onClicked: playbackPanel.close() }
            }
        }
    }
    AnchoredPlaybackPopup {
        id: outputsPanel
        objectName: "sessionOutputPanel"
        wideWidth: 360
        padding: screen.compact ? 20 : 16
        readonly property var observation: screen.state.playback_control.outputs || ({})
        readonly property var choices: observation.choices || []
        function openForCurrentItem(source) {
            captureSource(source)
            if (screen.owner.readPlaybackOutputs(screen.state.session_id, screen.state.playback.item_id)) open()
        }
        onAboutToHide: if (screen.owner) screen.owner.cancelPlaybackIntent()
        background: GlassSurface { elevated: true; popover: !screen.compact }
        contentItem: ColumnLayout {
            spacing: 16
            RowLayout {
                id: outputHeader
                Layout.fillWidth: true
                Text { text: screen.tr("session_output_title"); textFormat: Text.PlainText; font.pixelSize: 25; font.bold: true; color: BrandTheme.colors.text; Layout.fillWidth: true; wrapMode: Text.WordWrap }
            }
            ListView {
                id: outputChoices
                objectName: "sessionOutputChoices"
                Layout.fillWidth: true
                Layout.preferredHeight: Math.min(300 * screen.ipadScale, contentHeight)
                clip: true; spacing: 8; model: outputsPanel.choices
                ScrollBar.vertical: ScrollBar { }
                delegate: GlassButton {
                    id: outputChoice
                    required property var modelData
                    objectName: "sessionOutputChoice-" + modelData.id
                    readonly property bool volumeKnown: typeof modelData.volume_percent === "number"
                    readonly property string volumeLabel: volumeKnown ? modelData.volume_percent + "%" : "–"
                    width: outputChoices.width
                    text: modelData.name + (screen.compact && modelData.active ? " · " + screen.tr("session_output_current") : "")
                    Accessible.name: modelData.name + (modelData.active ? " · " + screen.tr("session_output_current") : "")
                    Accessible.description: volumeKnown ? screen.tr("volume") + " " + volumeLabel : ""
                    checked: modelData.active && !screen.compact
                    opacity: modelData.active ? 1 : (enabled ? 1 : 0.4)
                    enabled: !!screen.state.playback_control.enabled && !modelData.active
                    implicitHeight: Math.max(56, outputChoiceLabels.implicitHeight + 28)
                    contentItem: RowLayout {
                        spacing: 12
                        FeatureIcon {
                            visible: !screen.compact
                            iconName: "voice"
                            Layout.preferredWidth: 24; Layout.preferredHeight: 24
                        }
                        ColumnLayout {
                            id: outputChoiceLabels
                            Layout.fillWidth: true
                            spacing: 2
                            Text {
                                text: outputChoice.text; textFormat: Text.PlainText; wrapMode: Text.WordWrap
                                font: outputChoice.font; color: BrandTheme.colors.text
                                Layout.fillWidth: true
                                horizontalAlignment: screen.compact ? Text.AlignHCenter : Text.AlignLeft
                            }
                            Text {
                                objectName: "sessionOutputChoiceVolume"
                                text: outputChoice.volumeLabel; textFormat: Text.PlainText
                                color: BrandTheme.colors.muted; font.pixelSize: 15
                                Layout.fillWidth: true
                                horizontalAlignment: screen.compact ? Text.AlignHCenter : Text.AlignLeft
                                Accessible.ignored: true
                            }
                        }
                        Text {
                            visible: !screen.compact && outputChoice.modelData.active
                            text: "✓"; color: BrandTheme.colors.text; font.pixelSize: 20
                            Accessible.ignored: true
                        }
                    }
                    onClicked: screen.owner.setPlaybackOutput(screen.state.session_id, screen.state.playback.item_id, outputsPanel.observation.lease, modelData.id)
                }
            }
            Text {
                objectName: "sessionOutputStatus"
                Layout.fillWidth: true; wrapMode: Text.WordWrap; textFormat: Text.PlainText
                color: BrandTheme.colors.muted; font.pixelSize: 18
                visible: text.length > 0
                text: screen.state.playback_control.reading_outputs ? screen.tr("loading")
                    : screen.state.playback_control.status === "sending" ? screen.tr("session_question_sending")
                    : screen.state.playback_control.status === "uncertain" ? screen.tr("session_uncertain")
                    : screen.state.playback_control.outputs_status === "unavailable" ? screen.tr("session_output_unavailable")
                    : screen.state.playback_control.status === "accepted" ? screen.tr("session_playback_sent")
                    : outputsPanel.observation.lease !== undefined && outputsPanel.choices.length <= 1 ? screen.tr("session_output_empty") : ""
            }
            RowLayout {
                id: outputFooter
                Layout.fillWidth: true
                GlassButton {
                    parent: screen.compact ? outputFooter : outputHeader
                    objectName: "sessionOutputRead"
                    text: screen.compact ? screen.tr("refresh") : ""
                    iconName: screen.compact ? "" : "refresh"
                    Accessible.name: screen.tr("refresh")
                    enabled: !screen.owner.busy && !!screen.state.playback_control.available && !!screen.state.playback_control.outputs_supported
                    onClicked: {
                        if (screen.state.playback_control.status === "uncertain") screen.owner.refreshPlayback()
                        else screen.owner.readPlaybackOutputs(screen.state.session_id, screen.state.playback.item_id)
                    }
                }
                Item { Layout.fillWidth: true }
                GlassButton { objectName: "sessionOutputClose"; text: screen.tr("close"); onClicked: outputsPanel.close() }
            }
        }
    }
    GlassPopup {
        id: composerPanel
        objectName: "sessionComposerPanel"
        property bool keyboardVisible: true
        x: screen.compact ? 8 : 16
        y: screen.height - height - 8
        width: screen.width - 2 * x
        height: Math.min(screen.height - 16, contentItem.implicitHeight + 2 * padding)
        padding: screen.compact ? 12 : 20
        modal: true; dim: false
        onOpened: {
            keyboardVisible = true
            composeInput.text = screen.draft
            composeInput.forceActiveFocus()
        }
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
                Layout.fillWidth: true; Layout.minimumHeight: screen.compact ? 58 : 96
                placeholderText: screen.tr("session_question_placeholder")
                Accessible.name: screen.tr("session_question_placeholder")
                maximumLength: 4000; selectByMouse: true; font.pixelSize: screen.compact ? 22 : 30
                onTextChanged: screen.draft = text
                onAccepted: screen.submitQuestion()
                TapHandler { onTapped: composerPanel.keyboardVisible = true }
            }
            TouchKeyboard {
                objectName: "sessionComposerKeyboard"
                visible: composerPanel.keyboardVisible
                docked: true
                keyHeight: screen.compact ? 44 : Math.max(44, Math.min(88, Math.floor(screen.height / 10)))
                keyFontSize: screen.compact ? 19 : 30
                keyGap: screen.compact ? 4 : 8
                Layout.fillWidth: true; target: composeInput; backend: screen.backend
                submitIcon: "send"; submitLabel: screen.tr("session_send")
                onSubmitted: screen.submitQuestion()
                onDismissed: composerPanel.keyboardVisible = false
            }
            RowLayout {
                visible: !composerPanel.keyboardVisible
                Layout.fillWidth: true
                GlassButton { text: screen.tr("close"); onClicked: composerPanel.close() }
                Item { Layout.fillWidth: true }
                GlassButton { text: screen.tr("session_send"); iconName: "send"; primary: true; enabled: !screen.owner.busy && !screen.owner.questionBusy && composeInput.text.trim().length > 0; onClicked: screen.submitQuestion() }
            }
        }
    }
    GlassPopup {
        id: searchPanel
        objectName: "sessionSearchPanel"
        property bool keyboardVisible: false
        property string selectedMatchId: ""
        readonly property var matches: screen.state.search.matches || []
        readonly property int selectedMatchIndex: matches.findIndex(function(row) { return row.entry_id === selectedMatchId })
        onMatchesChanged: {
            if (selectedMatchId && !matches.some(function(row) { return row.entry_id === selectedMatchId }))
                selectedMatchId = ""
        }
        function resetSearch() {
            selectedMatchId = ""
            screen.owner.clearSearch()
        }
        function moveMatch(delta) {
            var count = matches.length
            if (!count) return
            var index = selectedMatchIndex < 0 ? (delta < 0 ? count - 1 : 0)
                : (selectedMatchIndex + delta + count) % count
            var card = searchRows.itemAt(index)
            if (!card) return
            selectedMatchId = card.modelData.entry_id
            var flick = searchScroll.contentItem
            flick.cancelFlick()
            searchPosition.stop()
            var top = flick.contentY + card.mapToItem(flick, 0, 0).y
            flick.contentY = Math.max(0, Math.min(top, flick.contentHeight - flick.height))
            screen.rememberSearch()
        }
        readonly property int bodyMargin: keyboardVisible ? 20 : 0
        function submitSearch() {
            if (screen.owner.busy || !searchInput.text.trim().length) return
            keyboardVisible = false
            screen.searchNow()
        }
        onOpened: keyboardVisible = true
        onClosed: { keyboardVisible = false; screen.cancelSearchRead(); searchInput.clear(); resetSearch() }
        x: keyboardVisible ? 0 : 16
        y: toolbar.y + toolbar.height + 8
        width: screen.width - 2 * x
        height: keyboardVisible ? screen.height - y : Math.min(screen.height - y - 126, 760)
        padding: keyboardVisible ? 0 : 20
        topPadding: 20
        modal: true; dim: false
        background: GlassSurface { elevated: true }
        contentItem: ColumnLayout {
            spacing: 12
            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: searchPanel.bodyMargin; Layout.rightMargin: searchPanel.bodyMargin
                TextField {
                    id: searchInput
                    objectName: "sessionSearchInput"
                    onActiveFocusChanged: if (activeFocus) searchPanel.keyboardVisible = true
                    placeholderText: screen.tr("session_search")
                    maximumLength: 200; font.pixelSize: 21
                    Layout.fillWidth: true; Layout.minimumHeight: 52
                    background: GlassSurface { radius: 20; interactive: true; focused: searchInput.activeFocus }
                    Accessible.name: screen.tr("session_search")
                    selectByMouse: true
                    onTextEdited: searchPanel.resetSearch()
                    TapHandler { onTapped: searchPanel.keyboardVisible = true }
                    onAccepted: searchPanel.submitSearch()
                }
                GlassButton {
                    iconName: "search"; Accessible.name: screen.tr("session_search")
                    enabled: !screen.owner.busy && searchInput.text.trim().length > 0
                    onClicked: searchPanel.submitSearch()
                }
                Text {
                    objectName: "sessionSearchMatchCount"
                    visible: searchPanel.matches.length > 0
                    text: searchPanel.selectedMatchIndex < 0 ? String(searchPanel.matches.length)
                        : (searchPanel.selectedMatchIndex + 1) + " / " + searchPanel.matches.length
                    color: BrandTheme.colors.muted; font.pixelSize: 17
                }
                GlassButton {
                    objectName: "sessionSearchPreviousMatch"
                    iconName: "arrow_up"; Accessible.name: screen.tr("session_search_previous_match")
                    enabled: searchPanel.matches.length > 0
                    onClicked: searchPanel.moveMatch(-1)
                }
                GlassButton {
                    objectName: "sessionSearchNextMatch"
                    iconName: "arrow_down"; Accessible.name: screen.tr("session_search_next_match")
                    enabled: searchPanel.matches.length > 0
                    onClicked: searchPanel.moveMatch(1)
                }
                GlassButton { text: screen.tr("close"); onClicked: searchPanel.close() }
            }
            Text {
                Layout.leftMargin: searchPanel.bodyMargin; Layout.rightMargin: searchPanel.bodyMargin
                visible: screen.state.error.length > 0
                text: screen.tr(screen.state.error === "uncertain" ? "session_uncertain" : (screen.state.error === "profile_unavailable" || screen.state.error === "profile_required") ? "session_profile_missing" : "session_error")
                color: BrandTheme.colors.warning; font.pixelSize: 18
                wrapMode: Text.WordWrap; Layout.fillWidth: true
            }
            Text {
                Layout.leftMargin: searchPanel.bodyMargin; Layout.rightMargin: searchPanel.bodyMargin
                visible: !!screen.state.search.query
                text: screen.tr(screen.state.search_limit_reached ? "session_search_limit" : screen.state.search.complete ? "session_search_complete" : "session_search_partial")
                color: BrandTheme.colors.muted; font.pixelSize: 18
                wrapMode: Text.WordWrap; Layout.fillWidth: true
            }
            Text {
                Layout.leftMargin: searchPanel.bodyMargin; Layout.rightMargin: searchPanel.bodyMargin
                visible: !!screen.state.search.query && (screen.state.search.matches || []).length === 0 && screen.state.search.complete
                text: screen.tr("session_search_empty"); color: BrandTheme.colors.muted; font.pixelSize: 20
            }
            ScrollView {
                id: searchScroll
                objectName: "sessionSearchScroll"
                Layout.fillWidth: true; Layout.fillHeight: true; Layout.minimumHeight: 0
                Layout.leftMargin: searchPanel.bodyMargin; Layout.rightMargin: searchPanel.bodyMargin
                contentWidth: availableWidth; clip: true
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                ColumnLayout {
                    width: searchScroll.availableWidth; spacing: 14
                    Repeater {
                        id: searchRows
                        objectName: "sessionSearchRows"
                        model: searchPanel.matches
                        GlassCard {
                            id: searchMatch
                            required property var modelData
                            readonly property bool selectedMatch: modelData.entry_id === searchPanel.selectedMatchId
                            Layout.fillWidth: true
                            Accessible.selected: selectedMatch
                            background: GlassSurface { selected: searchMatch.selectedMatch }
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
            SearchKeyboardDock {
                visible: searchPanel.keyboardVisible
                Layout.fillWidth: true
                target: searchInput; backend: screen.backend
                onEdited: searchPanel.resetSearch()
                onSubmitted: searchPanel.submitSearch()
                onDismissed: searchPanel.keyboardVisible = false
            }
        }
    }
    GlassPopup {
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
            GlassButton {
                visible: screen.sessionVoiceAvailable
                text: screen.tr("shared_field_voice")
                Layout.fillWidth: true
                onClicked: { moreChoices.close(); screen.openChoice("voice", moreButton) }
            }
            GlassButton {
                text: screen.tr("session_history"); Layout.fillWidth: true
                onClicked: { moreChoices.close(); screen.openArchive() }
            }
        }
    }
    GlassPopup {
        id: connectionInfo
        x: screen.width - width - 20; y: toolbar.y + toolbar.height + 8
        width: Math.min(screen.width - 40, 420); padding: 22
        modal: true; dim: false
        background: GlassSurface { elevated: true }
        contentItem: ColumnLayout {
            Text { text: screen.tr("connection_type"); font.bold: true; font.pixelSize: 24; color: BrandTheme.colors.text }
            Text { text: screen.backend.connectionType; textFormat: Text.PlainText; font.pixelSize: 22; color: BrandTheme.colors.muted; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            GlassButton {
                visible: screen.idleWelcome && !screen.compact
                enabled: !screen.owner.busy
                iconName: "refresh"
                text: screen.tr("refresh")
                Layout.fillWidth: true
                onClicked: {
                    connectionInfo.close()
                    screen.owner.refresh()
                    screen.backend.pollSharedSettings()
                }
            }
        }
    }
    GlassPopup {
        id: choices
        objectName: "sessionToolbarChoice"
        property string sessionId: ""
        property string profileId: ""
        property string field: "mood"
        property string editToken: ""
        readonly property bool canSubmit: choices.visible && screen.state.runtime_state === "active"
            && screen.sessionControlsVisible && choices.sessionId === screen.state.session_id
            && choices.profileId === screen.scopeProfileId
            && (screen.backend.demoMode ? (screen.owner.demoOptions[choices.field] || []).length > 0
                : ((choices.field !== "voice" || screen.sessionVoiceAvailable)
                    && choices.editToken === (screen.backend.sharedSettings.edit_token || "")
                    && !!screen.backend.sharedSettings.available && !screen.backend.sharedSettingsBusy
                    && !screen.backend.sharedSettings.selection_required && choices.editToken.length > 0
                    && !screen.backend.sharedSettings.operation_pending))
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
                    model: (screen.backend.demoMode ? screen.owner.demoOptions : screen.backend.sharedSettings.options || {})[choices.field] || []
                    GlassButton {
                        required property var modelData
                        text: choices.field === "voice" ? (modelData.label_key ? screen.tr(modelData.label_key) : modelData.label || "") : screen.tr("shared_" + choices.field + "_" + modelData)
                        checked: screen.toolbarValue(choices.field) === (choices.field === "voice" ? modelData.value : modelData)
                        enabled: choices.canSubmit
                        objectName: "sessionToolbarOption"
                        onClicked: {
                            if (!choices.canSubmit) return
                            if (screen.backend.demoMode) {
                                screen.owner.setDemoPreference(choices.field, modelData)
                            } else {
                                var patch = {_edit_token: choices.editToken}
                                patch[choices.field] = choices.field === "voice" ? modelData.value : modelData
                                screen.backend.saveSharedSettings(patch)
                            }
                            choices.close()
                        }
                    }
                }
            }
            GlassButton { text: screen.tr("shared_title"); onClicked: { choices.close(); screen.navigate("settings") } }
        }
    }
    GlassPopup {
        id: vibeCastPanel
        objectName: "sessionVibeCastPanel"
        anchors.centerIn: parent
        width: Math.min(screen.width - 32, 520)
        padding: 18
        modal: true
        background: GlassSurface { elevated: true }
        readonly property var sender: screen.state.vibecast
        onAboutToHide: {
            codeInput.clear()
            screen.owner.closeVibeCast()
        }
        Connections {
            target: screen
            function onStateChanged() {
                if (vibeCastPanel.opened && !vibeCastPanel.sender.open) vibeCastPanel.close()
            }
            function onShowForecastChanged() { if (screen.showForecast) vibeCastPanel.close() }
            function onVisibleChanged() { if (!screen.visible) vibeCastPanel.close() }
            function onHistoricalChanged() { if (screen.historical) vibeCastPanel.close() }
        }
        contentItem: ColumnLayout {
            spacing: 8
            FeatureIcon {
                objectName: "sessionVibeCastGlyph"
                iconName: "vibecast"
                heroGradient: true
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: screen.compact ? 48 : 64
                Layout.preferredHeight: Layout.preferredWidth
            }
            Text {
                text: "VibeCast"; color: BrandTheme.colors.text
                font.pixelSize: 23; font.bold: true
                Layout.alignment: Qt.AlignHCenter
            }
            Text {
                objectName: "sessionVibeCastStatus"
                Layout.fillWidth: true
                color: BrandTheme.colors.text
                wrapMode: Text.WordWrap; textFormat: Text.PlainText
                text: {
                    const status = vibeCastPanel.sender.status
                    if (status === "loading") return screen.tr("loading")
                    if (status === "confirm" && vibeCastPanel.sender.has_share)
                        return screen.tr("vibecast_confirm_existing")
                    return screen.tr("vibecast_" + (status || "ready"))
                }
            }
            TextField {
                id: codeInput
                objectName: "sessionVibeCastCode"
                visible: ["ready", "active", "sharing", "stopped", "lookup_failed", "expired",
                          "display_stopped", "share_changed"]
                    .includes(vibeCastPanel.sender.status)
                Layout.fillWidth: true
                Layout.preferredHeight: screen.compact ? 48 : 60
                readonly property int cellGap: 6
                readonly property real cellWidth: Math.max(0, (width - 5 * cellGap) / 6)
                color: "transparent"
                selectionColor: "transparent"
                selectedTextColor: "transparent"
                cursorDelegate: Item { width: 1 }
                font.pixelSize: screen.compact ? 24 : 28
                Accessible.name: screen.tr("vibecast_code")
                maximumLength: 6
                validator: RegularExpressionValidator { regularExpression: /^[0-9]{0,6}$/ }
                inputMethodHints: Qt.ImhDigitsOnly | Qt.ImhNoPredictiveText
                onAccepted: lookupCode.clicked()
                MouseArea {
                    anchors.fill: parent
                    onClicked: (mouse) => {
                        codeInput.forceActiveFocus(Qt.MouseFocusReason)
                        const cell = Math.floor(mouse.x / (codeInput.cellWidth + codeInput.cellGap))
                        codeInput.cursorPosition = Math.min(codeInput.length, cell)
                    }
                }
                background: Row {
                    spacing: codeInput.cellGap
                    Repeater {
                        model: 6
                        GlassSurface {
                            required property int index
                            objectName: "sessionVibeCastCodeCell-" + index
                            width: codeInput.cellWidth
                            height: codeInput.height
                            radius: 12
                            interactive: true
                            selected: index >= codeInput.selectionStart && index < codeInput.selectionEnd
                            focused: codeInput.activeFocus && index === Math.min(codeInput.cursorPosition, 5)
                            Text {
                                anchors.centerIn: parent
                                text: codeInput.text.charAt(parent.index)
                                color: BrandTheme.colors.text
                                font.pixelSize: codeInput.font.pixelSize
                                font.bold: true
                                Accessible.ignored: true
                            }
                        }
                    }
                }
            }
            GridLayout {
                visible: codeInput.visible
                Layout.fillWidth: true
                columns: 6
                Repeater {
                    model: ["1", "2", "3", "4", "5", "⌫", "6", "7", "8", "9", "0"]
                    GlassButton {
                        required property string modelData
                        objectName: "sessionVibeCastDigit-" + modelData
                        text: modelData
                        Layout.fillWidth: true
                        Layout.preferredWidth: 1
                        Layout.preferredHeight: 42
                        focusPolicy: Qt.NoFocus
                        Accessible.name: modelData === "⌫" ? screen.tr("keyboard_delete") : modelData
                        onClicked: {
                            const selected = codeInput.selectionStart !== codeInput.selectionEnd
                            const start = selected ? codeInput.selectionStart : codeInput.cursorPosition
                            const end = selected ? codeInput.selectionEnd : start
                            if (modelData === "⌫") {
                                const removeFrom = selected ? start : Math.max(0, start - 1)
                                codeInput.remove(removeFrom, end)
                                codeInput.cursorPosition = removeFrom
                            } else if (selected || codeInput.length < 6) {
                                codeInput.remove(start, end)
                                codeInput.insert(start, modelData)
                                codeInput.cursorPosition = start + 1
                            }
                        }
                    }
                }
            }
            GlassButton {
                id: lookupCode
                objectName: "sessionVibeCastResolve"
                visible: codeInput.visible
                enabled: visible && codeInput.acceptableInput && codeInput.length === 6
                text: screen.tr("vibecast_lookup")
                primary: true
                Layout.fillWidth: true
                onClicked: {
                    if (enabled && screen.owner.resolveVibeCastCode(codeInput.text)) codeInput.clear()
                }
            }
            GlassButton {
                objectName: "sessionVibeCastApprove"
                visible: vibeCastPanel.sender.status === "confirm"
                text: screen.tr("vibecast_approve"); primary: true
                Layout.fillWidth: true
                onClicked: screen.owner.approveVibeCast()
            }
            GlassButton {
                objectName: "sessionVibeCastDisconnect"
                visible: vibeCastPanel.sender.has_display && !vibeCastPanel.sender.busy
                    && vibeCastPanel.sender.status !== "confirm"
                text: screen.tr("vibecast_disconnect_display")
                Layout.fillWidth: true
                onClicked: screen.owner.disconnectVibeCastDisplay()
            }
            GlassButton {
                objectName: "sessionVibeCastStop"
                visible: vibeCastPanel.sender.has_share
                enabled: !vibeCastPanel.sender.busy
                text: screen.tr("vibecast_stop_all")
                tint: BrandTheme.colors.danger
                Layout.fillWidth: true
                onClicked: screen.owner.stopVibeCast()
            }
            RowLayout {
                Layout.fillWidth: true
                GlassButton {
                    text: screen.tr("refresh")
                    enabled: !vibeCastPanel.sender.busy
                    Layout.fillWidth: true
                    onClicked: { codeInput.clear(); screen.owner.refreshVibeCast() }
                }
                GlassButton {
                    text: screen.tr("close")
                    Layout.fillWidth: true
                    onClicked: vibeCastPanel.close()
                }
            }
        }
    }

    GlassPopup {
        id: contentDeletePanel
        objectName: "sessionContentDeletePanel"
        anchors.centerIn: parent
        width: Math.min(screen.width - 40, 560); padding: 24; modal: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        onAboutToHide: screen.owner.cancelContentDelete()
        background: GlassSurface { elevated: true }
        contentItem: ColumnLayout {
            spacing: 14
            Text {
                Layout.fillWidth: true; wrapMode: Text.WordWrap; textFormat: Text.PlainText
                color: BrandTheme.colors.text; font.pixelSize: screen.compact ? 20 : 24
                text: {
                    var status = screen.contentDeletion.status
                    if (status === "confirm") return screen.tr("session_content_delete_confirm")
                    if (status === "deleted") return screen.tr("session_content_delete_complete")
                    if (status === "pending") return screen.tr("session_delete_status_pending")
                    if (status === "expired_unknown") return screen.tr("session_delete_status_expired")
                    if (status === "unknown" || status === "uncertain") return screen.tr("session_content_delete_uncertain")
                    return screen.tr(status === "loading" ? "loading" : "session_error")
                }
            }
            Text {
                visible: screen.contentDeletion.status === "confirm"
                Layout.fillWidth: true; wrapMode: Text.WordWrap; textFormat: Text.PlainText
                color: BrandTheme.colors.muted; font.pixelSize: 17
                text: !visible ? "" : screen.tr("session_content_delete_" + screen.contentDeletion.unit)
                    + " · " + screen.tr("session_content_delete_expires").replace("%1",
                        new Date(screen.contentDeletion.expires).toLocaleTimeString(Qt.locale(), Locale.ShortFormat))
                    + "\n" + screen.tr("session_content_delete_scope")
                    .replace("%1", screen.contentDeletion.remove_entries)
                    .replace("%2", screen.contentDeletion.unavailable_entries)
                    .replace("%3", screen.contentDeletion.remove_messages)
                    .replace("%4", screen.contentDeletion.unavailable_messages)
                    .replace("%5", screen.contentDeletion.moments)
                    .replace("%6", screen.contentDeletion.fenced)
            }
            GlassButton {
                objectName: "sessionContentDeleteConfirm"
                Layout.fillWidth: true; visible: screen.contentDeletion.status === "confirm"
                text: screen.tr("session_content_delete_action"); iconName: "trash"; primary: true; tint: BrandTheme.colors.danger
                enabled: !screen.owner.busy && !screen.owner.questionBusy && screen.contentDeletion.lease > 0
                onClicked: screen.owner.confirmContentDelete(screen.contentDeletion.lease)
            }
            GlassButton {
                Layout.fillWidth: true; visible: !!screen.contentDeletion.status_available
                text: screen.tr("session_delete_status_action"); enabled: !screen.owner.busy && !screen.owner.questionBusy
                onClicked: screen.owner.checkContentDeleteStatus()
            }
            GlassButton {
                Layout.fillWidth: true
                text: screen.tr(screen.contentDeletion.status === "confirm" ? "cancel" : "close")
                onClicked: contentDeletePanel.close()
            }
        }
    }
    GlassPopup {
        id: archiveDeletePanel
        objectName: "sessionDeletePanel"
        readonly property bool bulk: screen.state.archive_delete.kind === "bulk"
        anchors.centerIn: parent
        width: Math.min(screen.width - 40, 560); padding: 24; modal: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        onAboutToHide: screen.owner.cancelHistoryDelete()
        background: GlassSurface { elevated: true }
        contentItem: ColumnLayout {
            spacing: screen.compact ? 14 : 18
            Text {
                objectName: "sessionDeleteMessage"
                text: screen.tr(screen.state.archive_delete.status === "confirm" ? (archiveDeletePanel.bulk ? "session_delete_all_confirm" : "session_delete_confirm") : screen.state.archive_delete.status === "deleted" ? (archiveDeletePanel.bulk ? "session_delete_all_complete" : "session_delete_complete") : screen.state.archive_delete.status === "uncertain" ? "session_delete_uncertain" : screen.state.archive_delete.status === "pending" ? "session_delete_status_pending" : screen.state.archive_delete.status === "unknown" ? "session_delete_status_unknown" : screen.state.archive_delete.status === "expired_unknown" ? "session_delete_status_expired" : screen.state.archive_delete.status === "empty" ? "session_delete_all_empty" : screen.state.archive_delete.status === "snapshot_conflict" ? "session_delete_all_conflict" : screen.state.archive_delete.status === "failed" ? "session_error" : "loading").replace("%1", String(screen.state.archive_delete.count))
                textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: screen.compact ? 22 : 28
                wrapMode: Text.WordWrap; Layout.fillWidth: true
            }
            Text {
                objectName: "sessionDeleteTarget"
                visible: screen.state.archive_delete.status === "confirm" && !archiveDeletePanel.bulk
                text: screen.tr("session_title") + " · " + screen.displayDate((screen.state.timeline.session || {}).started_at || (screen.state.timeline.session || {}).created_at)
                textFormat: Text.PlainText; color: BrandTheme.colors.muted; font.pixelSize: 20
                wrapMode: Text.WordWrap; Layout.fillWidth: true
            }
            GlassButton {
                objectName: "sessionDeleteConfirm"
                visible: screen.state.archive_delete.status === "confirm"
                text: screen.tr(archiveDeletePanel.bulk ? "session_delete_all_action" : "session_delete_action"); iconName: "trash"; primary: true; tint: BrandTheme.colors.danger; Layout.fillWidth: true
                enabled: !screen.owner.busy && screen.state.archive_delete.lease > 0
                onClicked: screen.owner.confirmHistoryDelete(screen.state.archive_delete.lease)
            }
            GlassButton {
                objectName: "sessionDeletePanelStatus"
                visible: screen.state.archive_delete.status_available
                text: screen.tr("session_delete_status_action"); Layout.fillWidth: true; enabled: !screen.owner.busy
                onClicked: screen.owner.checkHistoryDeleteStatus()
            }
            GlassButton {
                objectName: "sessionDeletePanelRefresh"
                visible: screen.state.archive_delete.status === "pending" || screen.state.archive_delete.status === "unknown" || screen.state.archive_delete.status === "expired_unknown" || screen.state.archive_delete.status === "snapshot_conflict" || screen.state.archive_delete.status === "empty" || screen.state.archive_delete.status === "failed" || screen.state.archive_delete.status === "uncertain" || screen.state.archive_delete.status === "deleted"
                text: screen.tr("refresh"); Layout.fillWidth: true; enabled: !screen.owner.busy
                onClicked: { if (screen.owner.recoverHistoryDelete()) archiveDeletePanel.close() }
            }
            GlassButton { objectName: "sessionDeleteCancel"; text: screen.tr((screen.state.archive_delete.status === "reading" && !screen.state.archive_delete.attempted) || screen.state.archive_delete.status === "confirm" ? "cancel" : "close"); Layout.fillWidth: true; onClicked: archiveDeletePanel.close() }
        }
    }
    GlassPopup {
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
