import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "BrandTheme.js" as BrandTheme

ColumnLayout {
    id: attribution
    property var sources: []
    property var bulletinSources: []
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
        model: attribution.bulletinSources
        Text {
            id: bulletinLink
            required property var modelData
            objectName: "sessionBulletinSourceLink"
            text: modelData.label; textFormat: Text.PlainText
            color: BrandTheme.colors.text; font.pixelSize: 16
            font.underline: activeFocus || hover.hovered
            wrapMode: Text.WrapAnywhere; verticalAlignment: Text.AlignVCenter
            Layout.fillWidth: true; Layout.minimumHeight: 44
            activeFocusOnTab: true
            Accessible.role: Accessible.Link
            Accessible.name: modelData.accessible_label
            Accessible.description: modelData.url
            Accessible.onPressAction: activate()
            Keys.onReturnPressed: activate()
            Keys.onSpacePressed: activate()
            HoverHandler { id: hover }
            TapHandler { onTapped: bulletinLink.activate() }
            function activate() { Qt.openUrlExternally(modelData.url) }
        }
    }
    Repeater {
        model: attribution.ready ? attribution.sources : []
        Flow {
            id: sourceRow
            required property var modelData
            readonly property string providerName: modelData.provider || ""
            readonly property var sourceUrls: modelData.links || []
            readonly property string linkLabel: {
                if (providerName) return providerName
                djconnect.translationVersion
                return djconnect.t("session_attribution_source")
            }
            Layout.fillWidth: true
            spacing: 8

            SourceLink {
                visible: sourceRow.sourceUrls.length > 0
                text: sourceRow.linkLabel
                targetUrl: sourceRow.sourceUrls[0] || ""
                width: Math.min(implicitWidth, sourceRow.width)
            }
            Text {
                visible: !sourceRow.sourceUrls.length && text.length > 0
                text: sourceRow.providerName
                width: Math.min(implicitWidth, sourceRow.width)
                textFormat: Text.PlainText
                color: BrandTheme.colors.muted
                font.pixelSize: 16
                wrapMode: Text.Wrap
            }
            Text {
                visible: !!sourceRow.modelData.license
                text: (sourceRow.providerName || sourceRow.sourceUrls.length ? "· " : "") + (sourceRow.modelData.license || "")
                width: Math.min(implicitWidth, sourceRow.width)
                height: Math.max(implicitHeight, sourceRow.sourceUrls.length ? 44 : 0)
                verticalAlignment: Text.AlignVCenter
                textFormat: Text.PlainText
                color: BrandTheme.colors.muted
                font.pixelSize: 16
                wrapMode: Text.Wrap
            }
            Repeater {
                model: sourceRow.sourceUrls.slice(1)
                SourceLink {
                    required property string modelData
                    required property int index
                    text: sourceRow.linkLabel + " (" + (index + 2) + ")"
                    targetUrl: modelData
                    width: Math.min(implicitWidth, sourceRow.width)
                }
            }
        }
    }

    component SourceLink: Text {
        id: sourceLink
        required property string targetUrl
        objectName: "sessionAttributionSourceLink"
        textFormat: Text.PlainText
        color: BrandTheme.colors.cyan
        font.pixelSize: 16
        font.underline: true
        wrapMode: Text.Wrap
        verticalAlignment: Text.AlignVCenter
        height: Math.max(implicitHeight, 44)
        activeFocusOnTab: visible && targetUrl.length > 0
        Accessible.role: Accessible.Link
        Accessible.name: text
        Accessible.onPressAction: activate()
        Keys.onReturnPressed: activate()
        Keys.onSpacePressed: activate()
        TapHandler { onTapped: sourceLink.activate() }

        function activate() {
            if (visible && targetUrl.length) Qt.openUrlExternally(targetUrl)
        }
    }
}
