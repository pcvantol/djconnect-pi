import QtQuick
import "MoodTheme.js" as MoodTheme

Canvas {
    id: canvas
    required property string mood
    required property bool activeSession

    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onMoodChanged: requestPaint()
    onActiveSessionChanged: requestPaint()

    onPaint: {
        var ctx = getContext("2d")
        var w = width
        var h = height
        var scale = w / 800
        var moodName = MoodTheme.key(mood) === "default" ? "chill" : mood
        var energy = activeSession && moodName === "energy"

        function fill(gradient) {
            ctx.fillStyle = gradient
            ctx.fillRect(0, 0, w, h)
        }
        function diagonal(colors) {
            var gradient = ctx.createLinearGradient(0, 0, w, h)
            for (var index = 0; index < colors.length; index++)
                gradient.addColorStop(index / (colors.length - 1), colors[index])
            fill(gradient)
        }
        function glow(x, y, radius, color) {
            var gradient = ctx.createRadialGradient(x, y, 0, x, y, radius * scale)
            gradient.addColorStop(0, color)
            gradient.addColorStop(1, Qt.rgba(color.r, color.g, color.b, 0))
            fill(gradient)
        }
        function tone(token, opacity) {
            var color = Qt.color(MoodTheme.moodColor(moodName, token))
            return Qt.rgba(color.r, color.g, color.b, opacity)
        }

        ctx.reset()
        if (w <= 0 || h <= 0) return
        if (energy) {
            diagonal(["#174a36", "#215938", "#122e26"])
        } else {
            diagonal(["#050817", "#120a26", "#08142e"])
            glow(w, 0, 880, Qt.rgba(0.22, 0.43, 0.98, 0.42))
            glow(0, h, 820, Qt.rgba(0.64, 0.12, 0.92, 0.34))
            glow(0, 0, 720, Qt.rgba(0.10, 0.18, 0.52, 0.26))
            var shade = ctx.createLinearGradient(0, 0, 0, h)
            shade.addColorStop(0, "#29000000")
            shade.addColorStop(0.5, "#00000000")
            shade.addColorStop(1, "#42000000")
            fill(shade)
        }
        if (activeSession) {
            var chill = moodName === "chill"
            var strength = chill ? 0.20 : energy ? 0.34 : 0.30
            diagonal([tone("gradientStart", strength),
                      tone("gradientMid", chill ? 0.10 : energy ? 0.08 : strength * 0.65),
                      tone("gradientEnd", chill ? 0.14 : strength * 0.85)])
            if (!chill) glow(w, h, 650, tone("gradientEnd", 0.10))
        }
    }
}
