import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "BrandTheme.js" as BrandTheme
import "MoodTheme.js" as MoodTheme

GlassCard {
    id: card
    objectName: "sessionStartCard"
    // A fill-width card must not infer its width from wrapped child content.
    implicitWidth: 640
    property var backend
    property bool busy: false
    readonly property bool compact: width < 850
    readonly property real ipadScale: compact ? 1 : Math.min(1.45, width / 800)
    readonly property string mood: MoodTheme.key(selected("mood")) === "default" ? "chill" : selected("mood")
    readonly property var selection: MoodTheme.sessionSelection(mood)
    readonly property var colors: MoodTheme.sessionWelcome(mood)
    readonly property var settings: backend.sharedSettings
    readonly property bool ready: backend.demoMode || (!!settings.available && !settings.active && !settings.selection_required &&
        !settings.operation_pending && !settings.operation_unknown && !backend.sharedSettingsBusy &&
        typeof settings.edit_token === "string" && settings.edit_token.length > 0)
    signal startRequested(string mood)
    padding: compact ? 24 : 32 * ipadScale
    spacing: compact ? 18 : 29 * ipadScale
    background: Rectangle {
        radius: card.compact ? 28 : 34 * card.ipadScale
        border.color: "#52FFFFFF"
        gradient: Gradient {
            GradientStop { position: 0; color: card.colors.top }
            GradientStop { position: 0.52; color: card.colors.middle }
            GradientStop { position: 1; color: card.colors.bottom }
        }
    }
    function tr(key) { backend.translationVersion; return backend.t(key) }
    function choices(field) {
        return ((backend.demoMode ? backend.djSession.demoOptions : settings.options) || {})[field] || []
    }
    function selected(field) {
        return ((backend.demoMode ? backend.djSession.demoPreferences : settings.values) || {})[field] || ""
    }
    function canChoose(field) {
        return ready && !busy && (backend.demoMode || (settings.writable || []).indexOf(field) >= 0)
    }
    function choose(field, value) {
        if (!canChoose(field) || choices(field).indexOf(value) < 0 || selected(field) === value) return
        if (backend.demoMode) {
            backend.djSession.setDemoPreference(field, value)
            return
        }
        var patch = {_edit_token: settings.edit_token}
        patch[field] = value
        backend.saveSharedSettings(patch)
    }
    onVisibleChanged: { if (visible && !backend.demoMode) backend.pollSharedSettings() }
    Component.onCompleted: { if (visible && !backend.demoMode) backend.pollSharedSettings() }

    RowLayout {
        Layout.fillWidth: true
        spacing: 16
        Text {
            text: card.tr("session_welcome")
            textFormat: Text.PlainText
            color: BrandTheme.colors.text
            font.pixelSize: card.compact ? 20 : 20 * card.ipadScale
            font.weight: Font.DemiBold
            wrapMode: Text.Wrap
            Layout.fillWidth: true
        }
        SessionWelcomeArtwork {
            Layout.preferredWidth: card.compact ? 76 : 84 * card.ipadScale
            Layout.preferredHeight: width
        }
    }
    Text {
        objectName: "sessionWelcomeTitle"
        text: card.tr("session_welcome_title")
        textFormat: Text.PlainText
        color: BrandTheme.colors.text
        font.pixelSize: card.compact ? 37 : 42 * card.ipadScale
        font.bold: true
        wrapMode: Text.Wrap
        Layout.fillWidth: true
        Accessible.role: Accessible.Heading
    }
    Text {
        text: card.tr("session_welcome_lead")
        textFormat: Text.PlainText
        color: BrandTheme.colors.muted
        font.pixelSize: card.compact ? 19 : 17 * card.ipadScale
        wrapMode: Text.Wrap
        Layout.fillWidth: true
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: card.compact ? 8 : 18
        Repeater {
            model: [
                {icon: "music", key: "session_welcome_feature_music"},
                {icon: "book", key: "session_welcome_feature_stories"},
                {icon: "sparkles", key: "session_welcome_feature_discovery"}
            ]
            RowLayout {
                required property var modelData
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                spacing: card.compact ? 7 : 13
                Rectangle {
                    Layout.preferredWidth: card.compact ? 34 : 49 * card.ipadScale
                    Layout.preferredHeight: Layout.preferredWidth
                    radius: width * 0.32
                    color: "#26FFFFFF"
                    FeatureIcon {
                        anchors.centerIn: parent
                        width: parent.width * 0.70; height: width
                        iconName: modelData.icon
                        Accessible.ignored: true
                    }
                }
                Text {
                    text: card.tr(modelData.key)
                    textFormat: Text.PlainText
                    color: BrandTheme.colors.text
                    font.pixelSize: card.compact ? 15 : 15 * card.ipadScale
                    font.weight: Font.DemiBold
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }
            }
        }
    }
    GlassButton {
        objectName: "sessionStartAction"
        Layout.fillWidth: true
        implicitHeight: card.compact ? 62 : 56 * card.ipadScale
        text: card.tr("session_start")
        iconName: "session"
        primary: true
        enabled: card.ready && !card.busy && ["chill", "groove", "energy", "party"].indexOf(card.selected("mood")) >= 0
        background: Rectangle {
            radius: height / 2
            border.color: "#A6FFFFFF"
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0; color: card.colors.actionStart }
                GradientStop { position: 0.5; color: card.colors.actionMiddle }
                GradientStop { position: 1; color: card.colors.actionEnd }
            }
        }
        onClicked: card.startRequested(card.selected("mood"))
    }
    GlassCard {
        Layout.fillWidth: true
        padding: card.compact ? 13 : 15 * card.ipadScale
        background: Rectangle { radius: card.compact ? 22 : 30; color: "transparent"; border.color: "#52FFFFFF" }
        RowLayout {
            Layout.fillWidth: true
            spacing: 14
            FeatureIcon { iconName: "info"; Layout.preferredWidth: 30; Layout.preferredHeight: 30; Accessible.ignored: true }
            Text {
                text: card.tr("session_welcome_instruction")
                textFormat: Text.PlainText
                color: BrandTheme.colors.text
                font.pixelSize: card.compact ? 17 : 16 * card.ipadScale
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }
        }
    }
    Repeater {
        model: ["mood", "presence", "persona"]
        ColumnLayout {
            id: choiceRow
            required property string modelData
            Layout.fillWidth: true
            spacing: card.compact ? 8 : 12 * card.ipadScale
            Text {
                text: card.tr(choiceRow.modelData === "mood" ? "session_listen_how" : "session_start_" + choiceRow.modelData + "_title")
                textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: card.compact ? 20 : 17 * card.ipadScale; font.weight: Font.DemiBold
                wrapMode: Text.WordWrap; Layout.fillWidth: true
            }
            Text {
                text: card.tr("session_welcome_" + choiceRow.modelData + "_hint")
                textFormat: Text.PlainText
                color: BrandTheme.colors.muted
                font.pixelSize: card.compact ? 16 : 14 * card.ipadScale
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: card.compact ? 65 : 74 * card.ipadScale
                radius: height / 2
                color: "#24FFFFFF"
                border.color: "#62FFFFFF"
                RowLayout {
                    anchors.fill: parent; anchors.margins: 8; spacing: 6
                    Repeater {
                        model: card.choices(choiceRow.modelData)
                        GlassButton {
                            id: choiceButton
                            required property string modelData
                            objectName: "sessionStartChoice-" + choiceRow.modelData + "-" + modelData
                            Layout.fillWidth: true; Layout.preferredWidth: 1; Layout.fillHeight: true
                            iconName: choiceRow.modelData + "_" + modelData
                            Accessible.name: card.tr("shared_" + choiceRow.modelData + "_" + modelData)
                            checked: card.selected(choiceRow.modelData) === modelData
                            tint: card.selection.tint
                            selectionFill: card.selection.filled ? card.selection.tint : BrandTheme.colors.primaryActionFill
                            foregroundColor: checked ? card.selection.foreground : BrandTheme.colors.text
                            background: Rectangle {
                                radius: height / 2
                                color: choiceButton.checked ? choiceButton.selectionFill : "#28FFFFFF"
                                border.color: choiceButton.checked ? (card.selection.filled ? "#36FFFFFF" : BrandTheme.colors.primaryActionBorder) : "#32FFFFFF"
                                border.width: choiceButton.activeFocus ? 2 : 1
                            }
                            enabled: card.canChoose(choiceRow.modelData)
                            onClicked: card.choose(choiceRow.modelData, modelData)
                        }
                    }
                }
            }
            Text {
                text: card.selected(choiceRow.modelData) ? card.tr("shared_" + choiceRow.modelData + "_" + card.selected(choiceRow.modelData)) : card.tr("session_start_preferences_unavailable")
                textFormat: Text.PlainText; color: BrandTheme.colors.muted; font.pixelSize: card.compact ? 17 : 15 * card.ipadScale
                horizontalAlignment: Text.AlignHCenter; wrapMode: Text.WordWrap; Layout.fillWidth: true
            }
        }
    }
    Text {
        visible: !card.ready
        text: card.tr(card.settings.error === "uncertain" || card.settings.operation_pending || card.settings.operation_unknown ? "shared_error_uncertain" : card.settings.selection_required ? "shared_selection_required" : "session_start_preferences_unavailable")
        textFormat: Text.PlainText; color: BrandTheme.colors.muted; font.pixelSize: 20; wrapMode: Text.WordWrap; Layout.fillWidth: true
    }
}
