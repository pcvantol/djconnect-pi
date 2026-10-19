import QtQuick
import "BrandTheme.js" as BrandTheme
import QtQuick.Controls
import QtQuick.Layouts

Button {
    id: control
    property string label: ""
    property bool primary: false

    text: label
    Layout.fillWidth: true
    Layout.preferredHeight: primary ? 88 : 76
    font.pixelSize: primary ? 25 : 18
    font.bold: true

    background: GlassSurface {
        radius: Math.min(width, height) / 2
        interactive: true
        selected: control.primary
        pressed: control.down
        focused: control.activeFocus
        opacity: control.enabled ? 1 : 0.45
        scale: control.down ? 0.97 : 1
        Behavior on scale { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }
    }

    contentItem: Text {
        text: control.text
        color: control.enabled ? BrandTheme.colors.text : BrandTheme.colors.disabledText
        font: control.font
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
}
