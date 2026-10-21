import QtQuick
import "BrandTheme.js" as BrandTheme
import QtQuick.Controls
import QtQuick.Layouts

Button {
    id: control
    property string label: ""
    property bool primary: false

    scale: down && enabled && GlassStyle.motionEnabled ? GlassStyle.pressedScale : 1
    Behavior on scale {
        NumberAnimation { duration: GlassStyle.motionEnabled ? GlassStyle.pressDuration : 0; easing.type: Easing.OutCubic }
    }
    opacity: enabled ? 1 : 0.4
    text: label
    Layout.fillWidth: true
    Layout.preferredHeight: primary ? 88 : 76
    font.pixelSize: primary ? 25 : 18
    font.bold: true

    background: GlassSurface {
        radius: Math.min(width, height) / 2
        interactive: true
        primary: control.primary
        pressed: control.down
        focused: control.activeFocus
    }

    contentItem: Text {
        text: control.text
        color: BrandTheme.colors.text
        font: control.font
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
}
