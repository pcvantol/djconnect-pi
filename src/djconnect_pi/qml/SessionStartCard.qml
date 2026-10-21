import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "BrandTheme.js" as BrandTheme

GlassCard {
    id: card
    hero: true
    objectName: "sessionStartCard"
    // A fill-width card must not infer its width from wrapped child content.
    implicitWidth: 640
    property var backend
    property bool busy: false
    readonly property bool compact: width < 850
    readonly property var settings: backend.sharedSettings
    readonly property bool ready: !!settings.available && !settings.active && !settings.selection_required &&
        !settings.operation_pending && !settings.operation_unknown && !backend.sharedSettingsBusy &&
        typeof settings.edit_token === "string" && settings.edit_token.length > 0
    signal startRequested(string mood)
    padding: compact ? 24 : 38
    spacing: compact ? 24 : 34
    function tr(key) { backend.translationVersion; return backend.t(key) }
    function choices(field) { return (settings.options || {})[field] || [] }
    function selected(field) { return (settings.values || {})[field] || "" }
    function choose(field, value) {
        if (!ready || busy || choices(field).indexOf(value) < 0 ||
            (settings.writable || []).indexOf(field) < 0 || selected(field) === value) return
        var patch = {_edit_token: settings.edit_token}
        patch[field] = value
        backend.saveSharedSettings(patch)
    }
    onVisibleChanged: { if (visible) backend.pollSharedSettings() }
    Component.onCompleted: { if (visible) backend.pollSharedSettings() }

    GridLayout {
        Layout.fillWidth: true
        columns: 2
        columnSpacing: card.compact ? 16 : 28
        ColumnLayout {
            Layout.fillWidth: true
            spacing: card.compact ? 18 : 26
            Text {
                text: card.tr("session_welcome")
                textFormat: Text.PlainText
                color: BrandTheme.colors.purple; font.pixelSize: card.compact ? 22 : 28; font.bold: true
                wrapMode: Text.WordWrap; Layout.fillWidth: true
            }
            Text {
                text: card.tr("session_welcome_title")
                textFormat: Text.PlainText
                color: BrandTheme.colors.text; font.pixelSize: card.compact ? 38 : 56; font.bold: true
                wrapMode: Text.WordWrap; Layout.fillWidth: true
            }
        }
        Item {
            Layout.preferredWidth: card.compact ? 150 : 280
            Layout.preferredHeight: width
            Accessible.ignored: true
            Rectangle {
                width: parent.width * 0.88; height: width; radius: width / 2; anchors.centerIn: parent
                color: "#100B25"; border.color: "#55B596F3"
                Repeater {
                    model: [0.95, 0.87, 0.79, 0.71, 0.63]
                    Rectangle {
                        required property real modelData
                        width: parent.width * modelData; height: width; radius: width / 2
                        anchors.centerIn: parent; color: "transparent"; border.color: "#18B5A5D3"
                    }
                }
                Rectangle {
                    width: parent.width * 0.42; height: width; radius: width / 2; anchors.centerIn: parent
                    gradient: Gradient {
                        GradientStop { position: 0; color: BrandTheme.colors.blue }
                        GradientStop { position: 1; color: BrandTheme.colors.purple }
                    }
                    Rectangle { width: parent.width * 0.24; height: width; radius: width / 2; color: "#100B25"; anchors.centerIn: parent }
                }
            }
            Repeater {
                model: ["presence_music_only", "presence_balanced", "waveform"]
                GlassSurface {
                    required property string modelData
                    required property int index
                    width: parent.width * (index === 2 ? 0.40 : 0.24); height: parent.width * 0.24; radius: height * 0.32
                    x: parent.width * (index === 0 ? 0.73 : index === 1 ? 0.00 : 0.53)
                    y: parent.height * (index === 0 ? 0.02 : index === 1 ? 0.53 : 0.75)
                    FeatureIcon { anchors.centerIn: parent; width: parent.height * 0.52; height: width; iconName: modelData; iconColor: index === 2 ? BrandTheme.colors.purple : BrandTheme.colors.text }
                }
            }
        }
    }
    Text { text: card.tr("session_welcome_lead"); textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: card.compact ? 21 : 25; wrapMode: Text.WordWrap; Layout.fillWidth: true }
    Text { text: card.tr("session_welcome_detail"); textFormat: Text.PlainText; color: BrandTheme.colors.muted; font.pixelSize: card.compact ? 19 : 22; wrapMode: Text.WordWrap; Layout.fillWidth: true }
    Repeater {
        model: ["mood", "presence", "persona"]
        ColumnLayout {
            id: choiceRow
            required property string modelData
            Layout.fillWidth: true
            spacing: 12
            Text {
                text: card.tr(choiceRow.modelData === "mood" ? "session_listen_how" : "session_start_" + choiceRow.modelData + "_title")
                textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: card.compact ? 22 : 26; font.bold: true
                wrapMode: Text.WordWrap; Layout.fillWidth: true
            }
            GlassSurface {
                Layout.fillWidth: true; implicitHeight: 84; radius: 42
                RowLayout {
                    anchors.fill: parent; anchors.margins: 8; spacing: 6
                    Repeater {
                        model: card.choices(choiceRow.modelData)
                        GlassButton {
                            required property string modelData
                            objectName: "sessionStartChoice-" + choiceRow.modelData + "-" + modelData
                            Layout.fillWidth: true; Layout.preferredWidth: 1; Layout.fillHeight: true
                            iconName: choiceRow.modelData + "_" + modelData
                            Accessible.name: card.tr("shared_" + choiceRow.modelData + "_" + modelData)
                            checked: card.selected(choiceRow.modelData) === modelData
                            enabled: card.ready && !card.busy && (card.settings.writable || []).indexOf(choiceRow.modelData) >= 0
                            onClicked: card.choose(choiceRow.modelData, modelData)
                        }
                    }
                }
            }
            Text {
                text: card.selected(choiceRow.modelData) ? card.tr("shared_" + choiceRow.modelData + "_" + card.selected(choiceRow.modelData)) : card.tr("session_start_preferences_unavailable")
                textFormat: Text.PlainText; color: BrandTheme.colors.muted; font.pixelSize: 20
                horizontalAlignment: Text.AlignHCenter; wrapMode: Text.WordWrap; Layout.fillWidth: true
            }
        }
    }
    Text {
        visible: !card.ready
        text: card.tr(card.settings.error === "uncertain" || card.settings.operation_pending || card.settings.operation_unknown ? "shared_error_uncertain" : card.settings.selection_required ? "shared_selection_required" : "session_start_preferences_unavailable")
        textFormat: Text.PlainText; color: BrandTheme.colors.muted; font.pixelSize: 20; wrapMode: Text.WordWrap; Layout.fillWidth: true
    }
    GlassButton {
        objectName: "sessionStartAction"
        Layout.fillWidth: true; implicitHeight: 72
        text: card.tr("session_start"); iconName: "play"; primary: true
        enabled: card.ready && !card.busy && ["chill", "groove", "energy", "party"].indexOf(card.selected("mood")) >= 0
        contentItem: Item {
            implicitHeight: 30
            Row {
                anchors.centerIn: parent; spacing: 16
                FeatureIcon { iconName: "play"; iconColor: BrandTheme.colors.text; width: 24; height: 30 }
                Text { text: card.tr("session_start"); textFormat: Text.PlainText; color: BrandTheme.colors.text; font.pixelSize: card.compact ? 21 : 24; font.bold: true }
            }
        }
        onClicked: card.startRequested(card.selected("mood"))
    }
}
