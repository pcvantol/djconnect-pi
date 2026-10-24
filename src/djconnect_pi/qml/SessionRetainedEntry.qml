import QtQuick
import QtQuick.Layouts
import "BrandTheme.js" as BrandTheme

GlassCard {
    id: historyCard
    required property var entry
    required property var translate
    property string dateText: ""
    property bool selectionAvailable: false
    property bool selectionBusy: false
    readonly property bool attributionReady: historySources.ready
    property alias bodyItem: retainedBody
    signal askAbout(string sessionId, string entryId)
    readonly property var played: entry.historical_playback || {}
    Layout.fillWidth: true
    Text {
        visible: historySources.ready
        text: entry.kind === "playback_observed" ? historyCard.translate("session_history_playback") : entry.kind === "conversation_user" ? historyCard.translate("session_you") : entry.kind === "conversation_dj" ? historyCard.translate("session_dj") : entry.kind === "dj_silence" ? historyCard.translate("session_silence") : entry.kind === "dj_publication" ? historyCard.translate("session_unavailable_contribution") : (entry.summary || historyCard.translate("session_title"))
        color: BrandTheme.colors.text; font.pixelSize: 24; font.bold: true; wrapMode: Text.WordWrap; textFormat: Text.PlainText; Layout.fillWidth: true
    }
    Text { id: retainedBody; text: entry.text || ""; visible: historySources.ready && text.length > 0 && !historyCard.played.title && !historyCard.played.artist && !historyCard.played.album; color: BrandTheme.colors.text; font.pixelSize: 22; wrapMode: Text.WordWrap; textFormat: Text.PlainText; Layout.fillWidth: true }
    Text { visible: historySources.ready && text.length > 0; text: historyCard.played.title || ""; textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 26; font.bold: true; wrapMode: Text.WordWrap; Layout.fillWidth: true }
    Text { visible: historySources.ready && text.length > 0; text: historyCard.played.artist || ""; textFormat: Text.PlainText; color: BrandTheme.colors.muted; font.pixelSize: 23; wrapMode: Text.WordWrap; Layout.fillWidth: true }
    Text { visible: historySources.ready && text.length > 0; text: historyCard.played.album || ""; textFormat: Text.PlainText; color: BrandTheme.colors.muted; font.pixelSize: 19; wrapMode: Text.WordWrap; Layout.fillWidth: true }
    SessionAttribution { id: historySources; sources: entry.display_sources || []; requiresSpotify: entry.requires_spotify_attribution || false; spotifyURL: entry.spotify_source_url || ""; Layout.fillWidth: true }
    GlassButton {
        objectName: "sessionRetainedAskAbout"
        visible: historyCard.selectionAvailable && historySources.ready
        text: historyCard.translate("session_ask_about"); enabled: !historyCard.selectionBusy
        onClicked: { historyCard.askAbout(entry.session_id, entry.entry_id) }
    }
    Text { objectName: "sessionHistoryEntryDate"; text: historyCard.dateText; color: BrandTheme.colors.muted; font.pixelSize: 16; textFormat: Text.PlainText }
}
