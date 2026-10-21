import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "BrandTheme.js" as BrandTheme

// iPad-style separated action capsules and large title; compact keeps one row.
Control {
    id: bar
    objectName: "pageToolbar"
    property string title: ""
    property bool showConnection: false
    property string connectionLabel: ""
    property string connectionText: ""
    onVisibleChanged: if (!visible) connectionInfo.close()
    property bool compact: width < 900
    default property alias actions: trailingRow.data
    property alias leading: leadingRow.data
    implicitHeight: compact ? 58 : 118
    Layout.fillWidth: true
    Layout.preferredHeight: implicitHeight
    property GlassPopup connectionInfo: GlassPopup {
        x: Math.max(0, bar.width - width); y: 62
        width: Math.min(bar.width, 420); padding: 22
        modal: true; dim: false
        background: GlassSurface { elevated: true }
        contentItem: ColumnLayout {
            Text { text: bar.connectionLabel; textFormat: Text.PlainText; font.bold: true; font.pixelSize: 24; color: BrandTheme.colors.text; Layout.fillWidth: true; wrapMode: Text.WordWrap }
            Text { text: bar.connectionText; textFormat: Text.PlainText; font.pixelSize: 22; color: BrandTheme.colors.muted; Layout.fillWidth: true; wrapMode: Text.WordWrap }
        }
    }
    padding: 0
    contentItem: Item {
        RowLayout {
            id: chrome
            anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
            height: 58; spacing: 12
            GlassSurface {
                objectName: "pageToolbarLeading"
                visible: leadingRow.children.length > 0
                Layout.preferredWidth: leadingRow.implicitWidth + 12
                Layout.fillHeight: true; radius: height / 2
                RowLayout { id: leadingRow; anchors.centerIn: parent; spacing: 2 }
            }
            Text {
                visible: bar.compact
                text: bar.title; textFormat: Text.PlainText
                color: BrandTheme.colors.text; font.pixelSize: 34; font.bold: true
                elide: Text.ElideRight; Layout.fillWidth: true
            }
            Item { visible: !bar.compact; Layout.fillWidth: true }
            GlassSurface {
                objectName: "pageToolbarTrailing"
                visible: bar.showConnection || trailingRow.children.length > 0
                Layout.preferredWidth: trailingGroup.implicitWidth + 12
                Layout.fillHeight: true; radius: height / 2
                RowLayout {
                    id: trailingGroup; anchors.centerIn: parent; spacing: 2
                    GlassButton {
                        objectName: "pageToolbarConnection"
                        visible: bar.showConnection
                        iconName: "globe"; tertiary: true; implicitWidth: 52
                        Accessible.name: bar.connectionLabel
                        onClicked: connectionInfo.open()
                    }
                    RowLayout { id: trailingRow; spacing: 2 }
                }
            }
        }
        Text {
            objectName: "pageToolbarLargeTitle"
            visible: !bar.compact
            anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
            height: 48; text: bar.title; textFormat: Text.PlainText
            color: BrandTheme.colors.text; font.pixelSize: 40; font.bold: true
            elide: Text.ElideRight
        }
    }
}
