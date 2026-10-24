import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "BrandTheme.js" as BrandTheme

// Renderer-local visit. No microphone, media, analysis, server command or storage.
Rectangle {
    id: scene
    objectName: "vibeScapeVisit"
    required property var backend
    required property bool admitted
    property bool forecastAvailable: false
    required property string mood
    property bool reduceMotion: GlassStyle.reduceMotion
    property bool shaderFailed: false
    readonly property bool renderable: GraphicsInfo.api === GraphicsInfo.OpenGL && !shaderFailed
    property real phase: 0
    property real dynamics: 0.5
    property real touchClock: 0
    property var touches: []
    property bool controlsVisible: true
    readonly property var scenePalette: mood === "chill" ? ["#4DA3FF", "#7B61FF", "#D184FF"] : mood === "groove" ? ["#06C7AD", "#169BC8", "#10B981"] : mood === "energy" ? ["#DDFF00", "#00B8FF", "#39FF78"] : mood === "party" ? ["#FF287F", "#AA38F5", "#F43DCE"] : ["#3285FF", "#843DF5", "#CB27F5"]
    property vector4d composition: Qt.vector4d(Math.random(), Math.random(), Math.random(), Math.random())
    signal closeRequested()
    signal forecastRequested()
    color: "black"
    focus: true
    Keys.onEscapePressed: closeRequested()
    function tr(key) { return backend.t(key) }
    function colorVector(value, w) { var c = Qt.color(value); return Qt.vector4d(c.r,c.g,c.b,w) }
    function touchVector(i) {
        var t = touches[i]
        return t ? Qt.vector4d(t.x,t.y,touchClock-t.at,1) : Qt.vector4d(0,0,0,0)
    }
    function showControls() { controlsVisible = true; controlsTimeout.restart() }
    function impulse(x,y) {
        if (!admitted || reduceMotion) return
        var fresh = touches.filter(function(t) { return touchClock-t.at < 2.6 })
        if (fresh.length && touchClock-fresh[fresh.length-1].at < 0.08) return
        fresh.push({x:(x/width*2-1)*width/height, y:1-y/height*2, at:touchClock})
        touches = fresh.slice(-4)
    }
    onAdmittedChanged: if (!admitted) { touches = []; closeRequested() }
    onMoodChanged: touches = []
    onReduceMotionChanged: if (reduceMotion) touches = []
    Component.onCompleted: controlsTimeout.start()
    Timer {
        interval: 33; repeat: true
        running: scene.visible && scene.admitted && scene.renderable && !scene.reduceMotion
        onTriggered: {
            // Bounded local animation clock, independent of track progress/beat.
            scene.touchClock += 0.033
            scene.phase += 0.033 * (scene.mood === "chill" ? 0.18 : 0.30) * (0.04 + 3.84*scene.dynamics*scene.dynamics)
            if (scene.touches.length && scene.touchClock-scene.touches[scene.touches.length-1].at > 2.6) scene.touches = []
        }
    }
    Timer {
        id: controlsTimeout; interval: 3000
        onTriggered: { if (!dynamicsSlider.pressed) scene.controlsVisible = false; else restart() }
    }
    Item {
        anchors.fill: parent
        // Fixed pixel budget; GPU renders the field at <=480x768 then scales.
        layer.smooth: true
        layer.enabled: scene.renderable && scene.admitted
        layer.textureSize: Qt.size(Math.min(480,width), Math.min(768,height))
        Loader {
            anchors.fill: parent
            active: scene.renderable && scene.admitted
            sourceComponent: ShaderEffect {
                objectName: "vibeScapeShader"
                property vector4d resolutionTime: Qt.vector4d(width,height,scene.phase,0)
                property vector4d composition: scene.composition
                property vector4d paletteMotion: scene.colorVector(scene.scenePalette[0],scene.dynamics)
                property vector4d secondary: scene.colorVector(scene.scenePalette[1],0)
                property vector4d accent: scene.colorVector(scene.scenePalette[2],0)
                property vector4d shape: Qt.vector4d(0.6,0.08,(0.25+0.45*scene.composition.z)*(0.15+1.7*scene.dynamics),scene.composition.w)
                property vector4d touch0: scene.touchVector(0)
                property vector4d touch1: scene.touchVector(1)
                property vector4d touch2: scene.touchVector(2)
                property vector4d touch3: scene.touchVector(3)
                onStatusChanged: if (status === ShaderEffect.Error) scene.shaderFailed = true
                fragmentShader: "vibescape.frag.qsb"
            }
        }
    }
    MouseArea {
        anchors.fill: parent
        onClicked: scene.showControls()
        onPressed: mouse => scene.impulse(mouse.x,mouse.y)
        onPositionChanged: mouse => { if (pressed) scene.impulse(mouse.x,mouse.y) }
    }
    Text {
        objectName: "vibeScapeUnavailable"
        visible: !scene.renderable
        anchors.centerIn: parent; width: parent.width-64
        text: scene.tr("vibescape_unavailable"); textFormat: Text.PlainText
        horizontalAlignment: Text.AlignHCenter; wrapMode: Text.WordWrap
        color: "white"; font.pixelSize: 26
    }
    RowLayout {
        anchors.top: parent.top; anchors.horizontalCenter: parent.horizontalCenter
        anchors.topMargin: 32; visible: scene.controlsVisible
        GlassButton { objectName: "vibeScapeFlow"; text: scene.tr("session_flow"); onClicked: scene.closeRequested() }
        GlassButton { objectName: "vibeScapeForecast"; visible: scene.forecastAvailable; text: scene.tr("session_forecast"); onClicked: scene.forecastRequested() }
        GlassButton { text: scene.tr("vibescape_title"); checked: true; onClicked: scene.showControls() }
    }
    GlassSurface {
        anchors.bottom: parent.bottom; anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 32; width: Math.min(parent.width-64,560); height: 128
        visible: scene.controlsVisible && scene.renderable; elevated: true
        ColumnLayout {
            anchors.fill: parent; anchors.margins: 20
            Text { text: scene.tr("vibescape_dynamics"); color: "white"; font.pixelSize: 22; textFormat: Text.PlainText }
            Slider {
                id: dynamicsSlider; objectName: "vibeScapeDynamics"
                Layout.fillWidth: true; from: 0; to: 1; value: scene.dynamics
                Accessible.name: scene.tr("vibescape_dynamics")
                onMoved: { scene.dynamics = value; scene.showControls() }
                onPressedChanged: scene.showControls()
            }
        }
    }
}
