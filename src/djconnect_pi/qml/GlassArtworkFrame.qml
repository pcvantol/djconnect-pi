import QtQuick

// Presentation only: the caller retains the image source, lifetime and loader.
// Never captures or fetches the image; the shared material samples decoration only.
Item {
    id: frame
    default property alias content: body.data
    property var backend: null
    property var imageItem: null
    property string leaseKey: ""
    property var admissionCheck: null
    property bool active: true
    readonly property string artworkTint: palette.tint
    function invalidatePalette() { palette.invalidate() }
    property real padding: 8
    property real radius: 28
    readonly property real contentInset: Math.max(0, Math.min(padding, width / 4, height / 4))
    GlassSurface {
        objectName: "artworkGlassSurface"
        anchors.fill: parent
        radius: frame.radius
        artworkTint: frame.artworkTint
    }
    ArtworkPalette {
        id: palette
        backend: frame.backend; imageItem: frame.imageItem
        leaseKey: frame.leaseKey; admissionCheck: frame.admissionCheck; active: frame.active
    }
    Item {
        id: body
        anchors.fill: parent
        anchors.margins: frame.contentInset
    }
}
