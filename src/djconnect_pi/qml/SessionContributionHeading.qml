import QtQuick
import QtQuick.Layouts
import "BrandTheme.js" as BrandTheme

RowLayout {
    required property string label
    spacing: 8
    Layout.fillWidth: true
    FeatureIcon {
        iconName: "sparkles"
        Layout.preferredWidth: 20
        Layout.preferredHeight: 20
        Accessible.ignored: true
    }
    Text {
        objectName: "sessionContributionTitle"
        text: parent.label
        textFormat: Text.PlainText
        color: BrandTheme.colors.text
        font.pixelSize: 18
        font.bold: true
        wrapMode: Text.WordWrap
        Layout.fillWidth: true
        Accessible.role: Accessible.Heading
    }
}
