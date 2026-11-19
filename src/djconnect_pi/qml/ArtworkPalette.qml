import QtQuick

// One tiny readback of the caller's already displayed Image; never loads a URL.
Item {
    id: sampler
    width: 0; height: 0
    property var backend: null
    property var imageItem: null
    property string leaseKey: ""
    property var admissionCheck: null
    property bool active: true
    readonly property bool admitted: typeof admissionCheck !== "function" || admissionCheck()
    property string sampledTint: ""
    readonly property string tint: sampledTint && eligible() ? sampledTint : ""
    property int generation: 0
    property int attemptedGeneration: -1
    property bool pending: false
    property bool disposed: false
    function eligible() {
        return !disposed && visible && active && GlassStyle.awake && backend && imageItem && imageItem.visible &&
            imageItem.status === Image.Ready && imageItem.opacity >= 0.99 && imageItem.width > 0 && imageItem.height > 0 &&
            admitted && (typeof admissionCheck !== "function" || admissionCheck())
    }
    function invalidate() { generation++; sampledTint = ""; sampleLater.restart() }
    function sample() {
        if (pending || !eligible() || attemptedGeneration === generation) return
        if (!GlassStyle.claimPalette(sampler)) return
        var version = generation
        var image = imageItem
        var target = sampler
        attemptedGeneration = version
        pending = true
        var accepted = image.grabToImage(function(result) {
            if (!target) return
            target.pending = false
            GlassStyle.releasePalette(target)
            if (version === target.generation && image === target.imageItem && target.eligible()) {
                var color = ""
                try { color = target.backend.sampleArtworkTint(result.image) } catch (error) { color = "" }
                if (version === target.generation && target.eligible()) target.sampledTint = color
            }
            if (version !== target.generation) sampleLater.restart()
        }, Qt.size(32, 32))
        if (!accepted) { pending = false; GlassStyle.releasePalette(sampler) }
    }
    onImageItemChanged: invalidate()
    onBackendChanged: invalidate()
    onLeaseKeyChanged: invalidate()
    onActiveChanged: invalidate()
    onAdmittedChanged: invalidate()
    onVisibleChanged: invalidate()
    Connections {
        target: sampler.imageItem
        function onSourceChanged() { sampler.invalidate() }
        function onStatusChanged() { sampler.invalidate() }
        function onVisibleChanged() { sampler.invalidate() }
        function onOpacityChanged() { sampleLater.restart() }
        function onWidthChanged() { sampleLater.restart() }
        function onHeightChanged() { sampleLater.restart() }
    }
    Timer { id: sampleLater; interval: 0; onTriggered: sampler.sample() }
    Connections {
        target: GlassStyle
        function onAwakeChanged() { sampler.invalidate() }
        function onPaletteOwnerChanged() { if (GlassStyle.awake && !sampler.disposed && !sampler.pending && sampler.visible && sampler.active && sampler.attemptedGeneration !== sampler.generation && !GlassStyle.paletteOwner) sampleLater.restart() }
    }
    Component.onCompleted: invalidate()
    Component.onDestruction: { disposed = true; sampleLater.stop(); sampledTint = ""; GlassStyle.releasePalette(sampler) }
}
