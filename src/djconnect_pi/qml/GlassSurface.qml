import QtQuick
import "BrandTheme.js" as BrandTheme

Rectangle {
    id: glass
    property color tint: BrandTheme.colors.purple
    property bool selected: false
    property bool pressed: false
    property bool focused: false
    property bool interactive: false
    property bool elevated: false
    radius: 28
    color: BrandTheme.alpha(BrandTheme.colors.surface, "c8")
    border.width: focused ? 2 : 1
    border.color: focused ? BrandTheme.colors.focus : (selected ? tint : "#65ffffff")
    gradient: Gradient {
        orientation: Gradient.Horizontal
        GradientStop { position: 0; color: glass.elevated ? "#fa242b49" : (glass.selected ? Qt.rgba(glass.tint.r, glass.tint.g, glass.tint.b, 0.42) : "#a836305b") }
        GradientStop { position: 0.55; color: glass.elevated ? "#f52b3156" : (glass.pressed ? "#d047416c" : "#b02b3156") }
        GradientStop { position: 1; color: glass.elevated ? "#fa273451" : (glass.selected ? Qt.rgba(glass.tint.r, glass.tint.g, glass.tint.b, 0.26) : "#b8273a60") }
    }
    Rectangle {
        anchors.fill: parent
        anchors.margins: 2
        radius: Math.max(0, glass.radius - 2)
        color: "transparent"
        border.width: 1
        border.color: "#12ffffff"
    }
    Rectangle {
        x: glass.radius; y: 1
        width: Math.max(0, parent.width - glass.radius * 2)
        height: 1
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0; color: "#00ffffff" }
            GradientStop { position: 0.5; color: "#85ffffff" }
            GradientStop { position: 1; color: "#00ffffff" }
        }
    }
    Behavior on border.color { ColorAnimation { duration: glass.interactive ? 140 : 0 } }
}
