import QtQuick

// Presentation only: the caller retains the image source, lifetime and loader.
// Never captures or fetches the image; the shared material samples decoration only.
Item {
    id: frame
    default property alias content: body.data
    property real padding: 8
    property real radius: 28
    readonly property real contentInset: Math.max(0, Math.min(padding, width / 4, height / 4))
    GlassSurface {
        objectName: "artworkGlassSurface"
        anchors.fill: parent
        radius: frame.radius
    }
    Item {
        id: body
        anchors.fill: parent
        anchors.margins: frame.contentInset
    }
}
