import QtQuick

// Canonical pixels, including outlined typography. No local redrawing.
Item {
    id: lockup
    property bool lightBackground: false
    readonly property bool primary: width >= 512
    implicitHeight: width * (primary ? 512 / 2048 : 448 / 1728)
    Accessible.role: Accessible.Graphic
    Accessible.name: "DJConnect"
    Image {
        anchors.fill: parent
        source: "brand-wordmark-" + (lockup.primary ? "primary-" : "compact-") +
                (lockup.lightBackground ? "light.png" : "dark.png")
        fillMode: Image.PreserveAspectFit
        smooth: true
        mipmap: true
    }
}
