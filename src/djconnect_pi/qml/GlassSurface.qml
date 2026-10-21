import QtQuick
import "BrandTheme.js" as BrandTheme

// Portable translucent material. This does not claim native Apple Liquid Glass
// or backdrop blur; Qt shader effects require a separately qualified GPU path.
Rectangle {
    id: glass
    property color tint: BrandTheme.colors.actionAccent
    property bool selected: false
    property bool pressed: false
    property bool focused: false
    property bool interactive: false
    property bool elevated: false
    property bool primary: false
    property bool destructive: false
    property bool tertiary: false
    readonly property color surfaceFill: destructive ? Qt.rgba(1, 0.27, 0.23, 0.12) : selected ? Qt.rgba(tint.r, tint.g, tint.b, 0.22) : elevated ? "#F5171C30" : interactive ? "#1AFFFFFF" : "#80171C30"
    radius: 28
    color: tertiary ? "transparent" : surfaceFill
    border.width: focused ? 3 : (tertiary ? 0 : 1)
    border.color: focused ? "#F2FFFFFF" : selected ? Qt.rgba(tint.r, tint.g, tint.b, 0.55) : destructive ? "#1FFFFFFF" : interactive ? "#1FFFFFFF" : "#52FFFFFF"
    gradient: Gradient {
        orientation: Gradient.Horizontal
        GradientStop { position: 0; color: glass.tertiary ? "transparent" : glass.primary && !glass.destructive ? BrandTheme.colors.actionBlue : glass.surfaceFill }
        GradientStop { position: 1; color: glass.tertiary ? "transparent" : glass.primary && !glass.destructive ? BrandTheme.colors.actionPurple : glass.surfaceFill }
    }
    Rectangle {
        anchors.fill: parent; radius: glass.radius
        color: glass.pressed ? (glass.primary ? "#14000000" : "#1AFFFFFF") : "transparent"
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
