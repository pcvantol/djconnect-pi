import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "BrandTheme.js" as BrandTheme

GlassCard {
    id: historyCard
    required property var entry
    required property var translate
    property string dateText: ""
    property string confirmationMood: ""
    property bool selectionAvailable: false
    property bool selectionBusy: false
    property bool deletionAvailable: false
    property string flowDeletionScope: ""
    property Item flowSurface: null
    trailingRevealWidth: deleteAction.revealWidth
    signal deleteEntry(string sessionId, string entryId)
    readonly property bool attributionReady: historySources.ready
    property alias bodyItem: retainedBody
    signal askAbout(string sessionId, string entryId)
    readonly property bool sourceWithdrawn: entry.state === "source_withdrawn"
    readonly property bool canAsk: !sourceWithdrawn && selectionAvailable && historySources.ready
    function askAboutEntry() {
        if (canAsk && !selectionBusy) askAbout(entry.session_id, entry.entry_id)
    }
    readonly property bool settingsConfirmation: !sourceWithdrawn && entry.kind === "dj_moment"
        && entry.archive_basis === "runtime_accepted_settings_v1"
    readonly property var played: entry.historical_playback || {}
    Layout.fillWidth: true
    RowLayout {
        visible: historySources.ready
        Layout.fillWidth: true
        spacing: 8
        SessionContributionHeading {
            visible: historyCard.settingsConfirmation
            label: historyCard.translate("session_dj_contribution")
        }
        Text {
            visible: !historyCard.settingsConfirmation
            text: historyCard.sourceWithdrawn ? historyCard.translate("session_unavailable_contribution") : entry.kind === "playback_observed" ? historyCard.translate("session_history_playback") : entry.kind === "conversation_user" ? historyCard.translate("session_you") : entry.kind === "conversation_dj" ? historyCard.translate("session_dj") : entry.kind === "dj_silence" ? historyCard.translate("session_silence") : entry.kind === "dj_publication" ? historyCard.translate("session_unavailable_contribution") : (entry.summary || historyCard.translate("session_title"))
            color: BrandTheme.colors.text; font.pixelSize: 24; font.bold: true; wrapMode: Text.WordWrap; textFormat: Text.PlainText; Layout.fillWidth: true
        }
        GlassButton {
            objectName: "sessionRetainedAskAbout"
            visible: historyCard.canAsk
            enabled: !historyCard.selectionBusy
            iconName: "chat"
            tertiary: true
            padding: 0
            Layout.preferredWidth: 44; Layout.preferredHeight: 44
            Layout.alignment: Qt.AlignTop
            Accessible.name: historyCard.translate("session_ask_about")
            ToolTip.text: Accessible.name
            ToolTip.visible: hovered
            onClicked: historyCard.askAboutEntry()
        }
    }
    RowLayout {
        visible: retainedBody.hasBody
        Layout.fillWidth: true
        spacing: 12
        SessionConfirmationAvatar {
            visible: historyCard.settingsConfirmation
            mood: historyCard.confirmationMood || entry.mood || ""
        }
        Text {
            id: retainedBody
            objectName: "sessionRetainedBody"
            text: entry.text || ""
            readonly property bool hasBody: historySources.ready && text.length > 0 && !historyCard.played.title
                && !historyCard.played.artist && !historyCard.played.album
            visible: hasBody
            Layout.alignment: Qt.AlignTop
            color: BrandTheme.colors.text; font.pixelSize: 22
            wrapMode: Text.WordWrap; textFormat: Text.PlainText; Layout.fillWidth: true
            TapHandler {
                enabled: historyCard.canAsk && !historyCard.selectionBusy
                    && ["dj_moment", "playback_observed", "conversation_dj"].includes(historyCard.entry.kind)
                onTapped: historyCard.askAboutEntry()
            }
        }
    }
    Text { visible: historySources.ready && text.length > 0; text: historyCard.played.title || ""; textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 26; font.bold: true; wrapMode: Text.WordWrap; Layout.fillWidth: true }
    Text { visible: historySources.ready && text.length > 0; text: historyCard.played.artist || ""; textFormat: Text.PlainText; color: BrandTheme.colors.muted; font.pixelSize: 23; wrapMode: Text.WordWrap; Layout.fillWidth: true }
    Text { visible: historySources.ready && text.length > 0; text: historyCard.played.album || ""; textFormat: Text.PlainText; color: BrandTheme.colors.muted; font.pixelSize: 19; wrapMode: Text.WordWrap; Layout.fillWidth: true }
    SessionAttribution { id: historySources; sources: entry.display_sources || []; requiresSpotify: entry.requires_spotify_attribution || false; spotifyURL: entry.spotify_source_url || ""; Layout.fillWidth: true }
    SessionFlowDelete {
        id: deleteAction
        objectName: "sessionDeleteRetainedEntry"
        card: historyCard
        scope: historyCard.flowDeletionScope
        dismissalSurface: historyCard.flowSurface
        gesturesOnly: scope.length > 0
        allowed: historyCard.deletionAvailable && !historyCard.sourceWithdrawn
            && ["dj_moment", "conversation_user", "conversation_dj"].includes(entry.kind)
        enabled: !historyCard.selectionBusy
        actionLabel: historyCard.translate("session_content_delete_action")
        onDeleteRequested: historyCard.deleteEntry(entry.session_id, entry.entry_id)
    }
    Text { objectName: "sessionHistoryEntryDate"; text: historyCard.dateText; color: BrandTheme.colors.muted; font.pixelSize: 16; textFormat: Text.PlainText }
}
