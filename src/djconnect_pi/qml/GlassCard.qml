import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Control {
    id: card
    default property alias content: body.data
    property bool hero: false
    property string artworkTint: ""
    property bool currentMoment: false
    property real trailingRevealWidth: 0
    clip: trailingRevealWidth > 0
    spacing: 16
    padding: 22
    implicitHeight: body.implicitHeight + topPadding + bottomPadding
    implicitWidth: body.implicitWidth + leftPadding + rightPadding
    background: GlassSurface {
        hero: card.hero; artworkTint: card.artworkTint; currentMoment: card.currentMoment
        transform: Translate { x: -card.trailingRevealWidth }
    }
    contentItem: ColumnLayout {
        id: body
        spacing: card.spacing
        transform: Translate { x: -card.trailingRevealWidth }
    }
}
