import QtQuick
import "BrandTheme.js" as BrandTheme
import QtQuick.Controls
import QtQuick.Layouts

Button {
    id: pill
    property string label: ""
    property bool active: false

    text: label
    Layout.fillWidth: true
    Layout.preferredHeight: 48
    font.pixelSize: 17
    font.bold: true

    background: GlassSurface {
        radius: Math.min(width, height) / 2
        interactive: true
        selected: pill.active
        pressed: pill.down
        focused: pill.activeFocus
        opacity: pill.enabled ? 1 : 0.45
        scale: pill.down ? 0.97 : 1
        Behavior on scale { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }
    }

    contentItem: Text {
        text: pill.text
        color: pill.enabled ? BrandTheme.colors.text : BrandTheme.colors.disabledText
        font: pill.font
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
}
