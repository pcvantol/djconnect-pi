import QtQuick
import "BrandTheme.js" as BrandTheme

// Shared local material; Pi5 uses one GPU-blurred decorative underlay.
// Other renderers use the bounded translucent fallback; off uses opaque surfaces.
Rectangle {
    id: glass
    property color tint: BrandTheme.colors.actionAccent
    property bool selected: false
    property bool pressed: false
    property bool focused: false
    property bool interactive: false
    property bool elevated: false
    property bool hero: false
    property bool primary: false
    property bool destructive: false
    property bool tertiary: false
    readonly property color surfaceFill: destructive ? Qt.rgba(1, 0.27, 0.23, 0.12) : selected ? Qt.rgba(tint.r, tint.g, tint.b, 0.22) : elevated ? "#F5171C30" : interactive ? "#1AFFFFFF" : "#80171C30"
    readonly property bool glassEnabled: GlassStyle.enabled
    property real interactionProgress: interactive && pressed && GlassStyle.motionEnabled ? 1 : 0
    Behavior on interactionProgress {
        NumberAnimation { duration: GlassStyle.motionEnabled ? GlassStyle.pressDuration : 0; easing.type: Easing.OutCubic }
    }
    readonly property point backdropPosition: {
        GlassStyle.geometryFrame
        return GlassStyle.backdrop ? glass.mapToItem(GlassStyle.backdrop,0,0) : Qt.point(0,0)
    }
    readonly property bool hardwareGlass: GlassStyle.active && visible && !tertiary && !hero &&
        width > 0 && height > 0 && width <= 2048 && height <= 2048 &&
        backdropPosition.x < GlassStyle.backdrop.width && backdropPosition.y < GlassStyle.backdrop.height &&
        backdropPosition.x + width > 0 && backdropPosition.y + height > 0
    radius: 28
    readonly property color effectiveFill: !glassEnabled ?
        (selected ? Qt.tint(BrandTheme.colors.opaqueGlass, Qt.rgba(tint.r,tint.g,tint.b,0.22)) : interactive ? BrandTheme.colors.surfaceRaised : BrandTheme.colors.opaqueGlass) :
        hardwareGlass && !interactive && !selected && !destructive ? "transparent" : surfaceFill
    color: tertiary ? "transparent" : effectiveFill
    border.width: focused ? 3 : (tertiary ? 0 : 1)
    border.color: focused ? "#F2FFFFFF" : selected ? Qt.rgba(tint.r, tint.g, tint.b, 0.55) : destructive ? "#1FFFFFFF" : interactive ? "#1FFFFFFF" : "#52FFFFFF"
    gradient: hero ? heroGradient : materialGradient
    Gradient {
        id: materialGradient
        orientation: Gradient.Horizontal
        GradientStop { position: 0; color: glass.tertiary ? "transparent" : glass.primary && !glass.destructive ? BrandTheme.colors.actionBlue : glass.effectiveFill }
        GradientStop { position: 1; color: glass.tertiary ? "transparent" : glass.primary && !glass.destructive ? BrandTheme.colors.actionPurple : glass.effectiveFill }
    }
    Gradient {
        id: heroGradient
        orientation: Gradient.Horizontal
        GradientStop { position: 0; color: GlassStyle.heroStart }
        GradientStop { position: 0.5; color: GlassStyle.heroMid }
        GradientStop { position: 1; color: GlassStyle.heroEnd }
    }
    Loader {
        id: gpuMaterial
        objectName: "glassGpuMaterial"
        anchors.fill: parent; z: -1
        active: glass.hardwareGlass
        sourceComponent: ShaderEffect {
            opacity: GlassStyle.surfaceOpacity
            property var source: GlassStyle.texture
            property vector2d dimensions: Qt.vector2d(width,height)
            property real radius: glass.radius
            property real strength: GlassStyle.refractionPixels * (1 + glass.interactionProgress * 0.2)
            property vector4d backdropRect: Qt.vector4d(
                glass.backdropPosition.x/GlassStyle.backdrop.width,
                glass.backdropPosition.y/GlassStyle.backdrop.height,
                width/GlassStyle.backdrop.width,height/GlassStyle.backdrop.height)
            property color materialTint: GlassStyle.surfaceTint
            property real tintAmount: GlassStyle.tintAmount
            property real edgeLight: GlassStyle.edgeLight + glass.interactionProgress * 0.18
            fragmentShader: "glass.frag.qsb"
        }
    }
    Rectangle {
        objectName: "glassPressHighlight"
        anchors.fill: parent; radius: glass.radius
        visible: glass.glassEnabled && glass.interactive && !glass.tertiary
        opacity: glass.interactionProgress * 0.14
        gradient: Gradient {
            GradientStop { position: 0; color: "white" }
            GradientStop { position: 1; color: "transparent" }
        }
    }
    Rectangle {
        anchors.fill: parent; radius: glass.radius
        color: glass.pressed ? (glass.primary ? "#14000000" : "#1AFFFFFF") : "transparent"
    }
    Rectangle {
        anchors.fill: parent
        visible: glass.glassEnabled
        anchors.margins: 2
        radius: Math.max(0, glass.radius - 2)
        color: "transparent"
        border.width: 1
        border.color: "#12ffffff"
    }
    Rectangle {
        visible: glass.glassEnabled
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
