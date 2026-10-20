import QtQuick
import QtQuick.Controls
import "BrandTheme.js" as BrandTheme

Switch {
    id: control
    indicator: Rectangle {
        implicitWidth: 60
        implicitHeight: 34
        x: control.leftPadding
        y: (control.height - height) / 2
        radius: height / 2
        color: control.checked ? BrandTheme.colors.buttonStart : BrandTheme.colors.surface
        border.color: control.activeFocus ? BrandTheme.colors.focus : BrandTheme.colors.border
        border.width: control.activeFocus ? 2 : 1
        Rectangle {
            width: 26; height: 26; radius: 13
            x: control.checked ? parent.width - width - 4 : 4
            y: 4
            color: control.enabled ? BrandTheme.colors.text : BrandTheme.colors.disabledText
        }
    }
}
