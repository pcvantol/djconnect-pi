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
                GlassCard {
                    visible: page.privacy && !page.feedback
                    Layout.fillWidth: true
                    Text { text: page.tr("privacy"); textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 26; font.bold: true; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Repeater {
                        model: ["privacy_data_body", "privacy_tokens_body", "privacy_ai_body"]
                        Text { required property string modelData; text: page.tr(modelData); textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 22; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    }
                }
                GlassCard {
                    visible: !page.privacy && !page.feedback
                    Layout.fillWidth: true
                    Text { text: page.tr("legal"); textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 26; font.bold: true; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Text { text: page.tr("legal_independence"); textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 22; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Text { text: page.tr("legal_trademarks"); textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 22; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                }
                GlassCard {
                    visible: !page.privacy && !page.feedback
                    Layout.fillWidth: true
                    Text { text: page.tr("legal_oss"); textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 26; font.bold: true; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Text { text: page.tr("legal_oss_body"); textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: 22; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    GlassButton { text: page.tr("legal_license"); onClicked: Qt.openUrlExternally("https://github.com/pcvantol/djconnect-pi/blob/main/LICENSE") }
                }
            }
        }
    }
    onVisibleChanged: { feedbackOpenFailed = false; if (visible) scroll.contentItem.contentY = 0 }
    onFeedbackChanged: { feedbackOpenFailed = false; scroll.contentItem.contentY = 0 }
}
