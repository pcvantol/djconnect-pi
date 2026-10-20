import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "BrandTheme.js" as BrandTheme

Item {
    id: page
    property var backend
    property bool privacy: false
    property bool feedback: false
    property bool feedbackOpenFailed: false
    signal back()
    function tr(key) { backend.translationVersion; return backend.t(key) }
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 20
        RowLayout {
            Layout.fillWidth: true
            GlassButton { objectName: "informationBack"; text: page.tr("more"); iconName: "back"; onClicked: page.back() }
            Text { text: page.tr(page.feedback ? "feedback" : page.privacy ? "privacy" : "legal"); color: BrandTheme.colors.text; font.pixelSize: 32; font.bold: true; wrapMode: Text.WordWrap; Layout.fillWidth: true }
        }
        ScrollView {
            id: scroll
            objectName: "informationScroll"
            Layout.fillWidth: true; Layout.fillHeight: true
            contentWidth: availableWidth; clip: true
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ColumnLayout {
                width: scroll.availableWidth
                spacing: 20
                BrandLockup { Layout.fillWidth: true; Layout.preferredHeight: 100 }
                GlassCard {
                    visible: page.feedback
                    Layout.fillWidth: true
                    Text { text: page.tr("feedback_share"); textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 26; font.bold: true; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Text { text: page.tr("feedback_help"); textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 22; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    GlassButton { objectName: "feedbackOpenIssue"; text: page.tr("feedback_open"); iconName: "chat"; Layout.fillWidth: true; onClicked: page.feedbackOpenFailed = !page.backend.openFeedbackIssue() }
                    Text { objectName: "feedbackOpenError"; visible: page.feedbackOpenFailed; text: page.tr("feedback_unavailable"); textFormat: Text.PlainText; color: BrandTheme.colors.muted; font.pixelSize: 22; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                }
                Repeater {
                    model: page.feedback ? [] : page.privacy ? [
                        {heading: "privacy_profile_heading", body: "privacy_profile_body"},
                        {heading: "privacy_storage_heading", body: "privacy_storage_body"},
                        {heading: "privacy_audio_heading", body: "privacy_audio_body"}
                    ] : [
                        {heading: "legal", body: "legal_independence"},
                        {heading: "spotify_notice", body: "legal_trademarks"},
                        {heading: "legal_oss", body: "legal_oss_body"}
                    ]
                    GlassCard {
                        required property var modelData
                        Layout.fillWidth: true
                        Text { text: page.tr(modelData.heading); textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 26; font.bold: true; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                        Text { text: page.tr(modelData.body); textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 22; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    }
                }
                GlassCard {
                    visible: !page.feedback
                    Layout.fillWidth: true
                    Text { text: page.tr(page.privacy ? "pi_no_spotify_credentials" : "spotify_trademark"); color: BrandTheme.colors.muted; font.pixelSize: 22; textFormat: Text.PlainText; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Text { visible: page.privacy; text: page.tr("privacy_ai_body"); color: BrandTheme.colors.muted; font.pixelSize: 22; textFormat: Text.PlainText; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    GlassButton { visible: !page.privacy; text: page.tr("legal_license"); onClicked: Qt.openUrlExternally("https://github.com/pcvantol/djconnect-pi/blob/main/LICENSE") }
                }
            }
        }
    }
    onVisibleChanged: { feedbackOpenFailed = false; if (visible) scroll.contentItem.contentY = 0 }
    onFeedbackChanged: { feedbackOpenFailed = false; scroll.contentItem.contentY = 0 }
}
