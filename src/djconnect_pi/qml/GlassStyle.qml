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
    // At most one live 32x32 palette readback per QML engine; no URL/body queue.
    property var paletteOwner: null
    function claimPalette(owner) {
        if (paletteOwner) return false
        paletteOwner = owner
        return true
    }
    function releasePalette(owner) { if (paletteOwner === owner) paletteOwner = null }
    property int geometryFrame: 0
    property real blurStrength: 0.55
    property real surfaceOpacity: 0.96
    property color heroStart: "#142652"
    property color heroMid: "#211745"
    property color heroEnd: "#2B1452"
    property string mood: ""
    property string contextArtworkTint: ""
    property color moodAccent: "#3285FF"
    property color surfaceTint: "#171C30"
    property real tintAmount: 0.72
    property real moodTintStrength: 0.12
    property real artworkTintStrength: 0.16
    property real heroMoodStrength: 0.18
    property real materialChannelCeiling: 0.24
    property real refractionPixels: 14
    property real edgeLight: 0.55
    readonly property bool active: enabled && hardware && awake && backdrop !== null && texture !== null
}
