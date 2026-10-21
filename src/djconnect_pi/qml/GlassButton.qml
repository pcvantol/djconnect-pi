import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "BrandTheme.js" as BrandTheme

Button {
    id: control
    property string iconName: ""
    property bool primary: false
    property color tint: BrandTheme.colors.actionAccent
    property bool destructive: tint === BrandTheme.colors.danger || tint === BrandTheme.colors.actionDanger
    property bool tertiary: false
    opacity: enabled ? 1 : 0.4
    implicitHeight: 56
    implicitWidth: Math.max(56, contentItem.implicitWidth + 36)
    padding: 14
    font.pixelSize: 20
    font.bold: true
    Accessible.name: text
    background: GlassSurface {
        radius: height / 2
        interactive: true
        primary: control.primary
        selected: control.checked
        destructive: control.destructive
        tertiary: control.tertiary
        pressed: control.down
        focused: control.activeFocus
        tint: control.tint
        scale: control.down ? 0.98 : 1
        Behavior on scale { NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }
    }
    contentItem: RowLayout {
        spacing: control.text.length > 0 && control.iconName.length > 0 ? 10 : 0
        FeatureIcon {
            visible: control.iconName.length > 0
            iconName: control.iconName
            iconColor: control.destructive ? BrandTheme.colors.actionDanger : BrandTheme.colors.text
            Layout.preferredWidth: 26
            Layout.preferredHeight: 26
            Layout.alignment: Qt.AlignHCenter
        }
        Text {
            visible: control.text.length > 0
            text: control.text
            font: control.font
            color: control.destructive ? BrandTheme.colors.actionDanger : BrandTheme.colors.text
            textFormat: Text.PlainText
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            Layout.fillWidth: true
        }
    }
}
