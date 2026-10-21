import QtQuick
import QtQuick.Controls
import "BrandTheme.js" as BrandTheme

Switch {
    id: control
    indicator: GlassSurface {
        implicitWidth: 60
        implicitHeight: 34
        x: control.leftPadding
        y: (control.height - height) / 2
        radius: height / 2
        interactive: true
        selected: control.checked
        tint: BrandTheme.colors.buttonStart
        pressed: control.down && control.enabled
        focused: control.activeFocus
        Rectangle {
            objectName: "glassSwitchThumb"
            width: control.down && control.enabled && GlassStyle.motionEnabled ? 30 : 26
            height: 26; radius: 13
            x: 4 + control.visualPosition * (parent.width - width - 8)
            y: 4
            color: control.enabled ? BrandTheme.colors.text : BrandTheme.colors.disabledText
            Behavior on x {
                enabled: !control.down
                NumberAnimation { duration: GlassStyle.motionEnabled ? GlassStyle.settleDuration : 0; easing.type: Easing.OutCubic }
            }
            Behavior on width {
                NumberAnimation { duration: GlassStyle.motionEnabled ? GlassStyle.pressDuration : 0; easing.type: Easing.OutCubic }
            }
        }
    }
}
