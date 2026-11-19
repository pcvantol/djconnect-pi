import QtQuick

// Canonical pixels, including outlined typography. No local redrawing.
Item {
    id: lockup
    property bool lightBackground: false
    property bool wordmarkOnly: false
    readonly property bool primary: width >= 512
    implicitHeight: width * (wordmarkOnly ? 162 / 1092 : primary ? 512 / 2048 : 448 / 1728)
    Accessible.role: Accessible.Graphic
    Accessible.name: "DJConnect"
    Image {
        anchors.fill: parent
        source: "brand-wordmark-" + (lockup.primary && !lockup.wordmarkOnly ? "primary-" : "compact-") +
                (lockup.lightBackground ? "light.png" : "dark.png")
        // Canonical compact asset alpha bounds for outlined name only.
        // The original pixels/files are preserved; layout places the mark separately.
        sourceClipRect: lockup.wordmarkOnly ? Qt.rect(525, 142, 1092, 162) : Qt.rect(0, 0, 0, 0)
        fillMode: Image.PreserveAspectFit
        smooth: true
        mipmap: true
    }
}
