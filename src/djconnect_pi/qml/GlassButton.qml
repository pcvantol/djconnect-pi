import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "BrandTheme.js" as BrandTheme

Button {
    id: control
    property string iconName: ""
    property bool primary: false
    property color tint: BrandTheme.colors.purple
    implicitHeight: 56
    implicitWidth: Math.max(56, contentItem.implicitWidth + 36)
    padding: 14
    font.pixelSize: 20
    font.bold: true
    Accessible.name: text
    background: GlassSurface {
        radius: height / 2
        interactive: true
        selected: control.primary || control.checked
        pressed: control.down
        focused: control.activeFocus
        tint: control.tint
        opacity: control.enabled ? 1 : 0.45
        scale: control.down ? 0.97 : 1
        Behavior on scale { NumberAnimation { duration: 100; easing.type: Easing.OutCubic } }
    }
    contentItem: RowLayout {
        spacing: control.text.length > 0 && control.iconName.length > 0 ? 10 : 0
        FeatureIcon {
            visible: control.iconName.length > 0
            iconName: control.iconName
            iconColor: control.enabled ? BrandTheme.colors.text : BrandTheme.colors.disabledText
            Layout.preferredWidth: 26
            Layout.preferredHeight: 26
            Layout.alignment: Qt.AlignHCenter
        }
        Text {
            visible: control.text.length > 0
            text: control.text
            font: control.font
            color: control.enabled ? BrandTheme.colors.text : BrandTheme.colors.disabledText
            textFormat: Text.PlainText
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            Layout.fillWidth: true
        }
    }
}
