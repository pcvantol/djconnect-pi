import QtQuick
import QtQuick.Effects

// A single shared texture, not one blur pass per card. Only the decorative
// underlay is sampled: no Session text, private media or recursive scene cache.
Item {
    id: capture
    property Item sourceItem
    property real blurStrength: GlassStyle.blurStrength
    property alias texture: blurredTexture
    visible: false
    ShaderEffectSource {
        id: sourceTexture
        sourceItem: capture.sourceItem
        textureSize: Qt.size(Math.max(1,Math.min(960,Math.ceil(capture.width/2))), Math.max(1,Math.min(960,Math.ceil(capture.height/2))))
        live: true; visible: false
    }
    MultiEffect {
        id: blur
        anchors.fill: parent; source: sourceTexture
        blurEnabled: true; blur: capture.blurStrength; blurMax: 32
        autoPaddingEnabled: false; visible: false
    }
    ShaderEffectSource { id: blurredTexture; sourceItem: blur; textureSize: sourceTexture.textureSize; live: true; visible: false }
}
