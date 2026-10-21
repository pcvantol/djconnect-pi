pragma Singleton
import QtQuick

QtObject {
    // Window-local singleton; these are central tuning points for the material.
    property bool enabled: false
    property bool hardware: false
    property bool awake: true
    // One shared motion budget; effects never initiate input or server work.
    property bool reduceMotion: false
    readonly property bool motionEnabled: enabled && awake && !reduceMotion
    property int pressDuration: 120
    property int settleDuration: 180
    property int popupDuration: 160
    property real pressedScale: 0.98
    property var backdrop: null
    property var texture: null
    property int geometryFrame: 0
    property real blurStrength: 0.55
    property real surfaceOpacity: 0.96
    property color surfaceTint: "#171C30"
    property real tintAmount: 0.72
    property real refractionPixels: 14
    property real edgeLight: 0.55
    readonly property bool active: enabled && hardware && awake && backdrop !== null && texture !== null
}
