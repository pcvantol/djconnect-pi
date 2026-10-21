pragma Singleton
import QtQuick

QtObject {
    // Window-local singleton; these are central tuning points for the material.
    property bool enabled: false
    property bool hardware: false
    property bool awake: true
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
