import QtQuick
import QtQuick.Controls
import "BrandTheme.js" as BrandTheme

ComboBox {
    id: control
    implicitHeight: 54
    leftPadding: 14
    rightPadding: 44
    palette.dark: BrandTheme.colors.muted
    background: Rectangle {
        radius: 8
        color: control.enabled ? BrandTheme.colors.surfaceRaised : BrandTheme.colors.disabledStart
        border.color: control.activeFocus ? BrandTheme.colors.focus : BrandTheme.colors.border
        border.width: control.activeFocus ? 2 : 1
    }
    contentItem: Text {
        text: control.displayText
        font: control.font
        color: control.enabled ? BrandTheme.colors.text : BrandTheme.colors.disabledText
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    indicator: Text {
        anchors.right: parent.right
        anchors.rightMargin: 14
        anchors.verticalCenter: parent.verticalCenter
        text: "⌄"
        font.pixelSize: 26
        color: control.enabled ? BrandTheme.colors.cyan : BrandTheme.colors.disabledText
    }
}
