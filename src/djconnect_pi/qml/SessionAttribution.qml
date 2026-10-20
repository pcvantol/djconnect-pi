import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "BrandTheme.js" as BrandTheme

ColumnLayout {
    id: attribution
    property var sources: []
    property bool requiresSpotify: false
    property string spotifyURL: ""
    readonly property bool ready: !requiresSpotify || (spotifyLogo.status === Image.Ready && spotifyURL.length > 0)
    spacing: 4
    Image {
        id: spotifyLogo
        source: "spotify-attribution.png"
        visible: attribution.requiresSpotify && attribution.spotifyURL.length > 0
        Layout.preferredWidth: 90; Layout.preferredHeight: 44
        fillMode: Image.PreserveAspectFit
        Accessible.name: "Spotify"
        activeFocusOnTab: visible && attribution.ready
        Keys.onReturnPressed: Qt.openUrlExternally(attribution.spotifyURL)
        TapHandler { enabled: attribution.ready; onTapped: Qt.openUrlExternally(attribution.spotifyURL) }
    }
    Repeater {
        model: attribution.ready ? attribution.sources : []
        ColumnLayout {
            id: sourceRow
            required property var modelData
            Layout.fillWidth: true
            spacing: 2
            Text {
                text: [sourceRow.modelData.provider, sourceRow.modelData.license].filter(function(value) { return value.length > 0 }).join(" · ")
                visible: text.length > 0
                textFormat: Text.PlainText; color: BrandTheme.colors.muted
                font.pixelSize: 16; wrapMode: Text.WordWrap; Layout.fillWidth: true
            }
            Repeater {
                model: sourceRow.modelData.links
                Text {
                    required property string modelData
                    text: modelData; textFormat: Text.PlainText
                    color: BrandTheme.colors.cyan; font.pixelSize: 16; font.underline: true
                    wrapMode: Text.WrapAnywhere; verticalAlignment: Text.AlignVCenter
                    Layout.fillWidth: true; Layout.minimumHeight: 44
                    activeFocusOnTab: true
                    Accessible.name: text
                    Keys.onReturnPressed: Qt.openUrlExternally(modelData)
                    Keys.onSpacePressed: Qt.openUrlExternally(modelData)
                    TapHandler { onTapped: Qt.openUrlExternally(parent.modelData) }
                }
            }
        }
    }
}
