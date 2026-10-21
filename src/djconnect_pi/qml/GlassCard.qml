import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Control {
    id: card
    default property alias content: body.data
    property bool hero: false
    spacing: 16
    padding: 22
    implicitHeight: body.implicitHeight + topPadding + bottomPadding
    implicitWidth: body.implicitWidth + leftPadding + rightPadding
    background: GlassSurface { hero: card.hero }
    contentItem: ColumnLayout { id: body; spacing: card.spacing }
}
