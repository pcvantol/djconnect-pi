import QtQuick
import QtQuick.Layouts
import "BrandTheme.js" as BrandTheme

GlassCard {
    id: intro
    required property string iconName
    required property string title
    required property string message
    property bool compact: true
    property bool centeredMessage: true
    Layout.fillWidth: true
    Layout.minimumHeight: compact ? 212 : 340
    padding: compact ? 16 : 30
    spacing: compact ? 10 : 20

    background: GlassSurface {
        introduction: true
        radius: intro.compact ? 26 : 44
    }

    Item { Layout.fillHeight: true }
    FeatureIcon {
        id: glyph
        objectName: "introductionGlyph"
        readonly property bool glowing: visible && GlassStyle.awake && !GlassStyle.reduceMotion
            && Qt.application.state === Qt.ApplicationActive
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: intro.compact ? 64 : 102
        Layout.preferredHeight: Layout.preferredWidth
        iconName: intro.iconName
        heroGradient: true
        whiteSweep: glowing ? phase : -1
        strokeWidth: intro.compact ? 3.4 : 5
        Accessible.ignored: true
        property real phase: 0
        Timer {
            interval: 33
            repeat: true
            running: glyph.glowing
            onTriggered: glyph.phase = (glyph.phase + interval / 12000) % 1
        }
    }
    Text {
        text: intro.title
        textFormat: Text.PlainText
        font.bold: true
        font.pixelSize: intro.compact ? 24 : 30
        color: BrandTheme.colors.text
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.Wrap
        Layout.fillWidth: true
        Accessible.role: Accessible.Heading
    }
    Text {
        text: intro.message
        textFormat: Text.PlainText
        font.pixelSize: intro.compact ? 18 : 21
        color: BrandTheme.colors.muted
        horizontalAlignment: intro.centeredMessage ? Text.AlignHCenter : Text.AlignLeft
        wrapMode: Text.Wrap
        Layout.fillWidth: true
        Layout.maximumWidth: 1080
        Layout.alignment: Qt.AlignHCenter
    }
    Item { Layout.fillHeight: true }
}
