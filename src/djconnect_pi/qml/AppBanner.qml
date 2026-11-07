import QtQuick
import QtQuick.Layouts
import "BrandTheme.js" as BrandTheme

GlassCard {
    id: banner
    objectName: "appBanner"
    required property string detailText
    property bool dense: false
    readonly property bool compact: width < 900
    readonly property int logoSize: dense ? 64 : compact ? 84 : 120

    Layout.fillWidth: true
    padding: dense ? 16 : compact ? 20 : 28
    background: GlassSurface {
        introduction: true
        radius: banner.compact ? 28 : 44
    }

    RowLayout {
        Layout.fillWidth: true
        Layout.maximumWidth: banner.dense ? 640 : 768
        Layout.alignment: Qt.AlignHCenter
        spacing: banner.compact || banner.dense ? 16 : 20

        Image {
            objectName: "appBannerMark"
            source: "brand-mark-128.png"
            Layout.preferredWidth: banner.logoSize
            Layout.preferredHeight: banner.logoSize
            fillMode: Image.PreserveAspectFit
            smooth: true
            mipmap: true
            Accessible.ignored: true
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: banner.compact ? 5 : 7
            BrandLockup {
                objectName: "appBannerName"
                wordmarkOnly: true
                Layout.preferredWidth: Math.min(parent.width, banner.dense ? 160 : banner.compact ? 186 : 232)
                Layout.preferredHeight: width * 162 / 1092
                Layout.alignment: Qt.AlignLeft
            }
            Text {
                objectName: "appBannerDetail"
                text: banner.detailText
                textFormat: Text.PlainText
                color: BrandTheme.colors.muted
                font.pixelSize: banner.compact || banner.dense ? 20 : 26
                font.weight: Font.DemiBold
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
        }
    }
}
