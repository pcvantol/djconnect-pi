import QtQuick

// Same repository-owned DJPersonaMark geometry as the iOS menu symbol.
// Source: djconnect-app e106a467, DJPersonaAvatarView.swift, 100-unit canvas.
Canvas {
    id: symbol
    property color iconColor: "white"
    implicitWidth: 32
    implicitHeight: 32
    onIconColorChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onPaint: {
        var ctx = getContext("2d")
        ctx.reset()
        ctx.clearRect(0, 0, width, height)
        var side = Math.min(width, height)
        ctx.save()
        ctx.translate((width - side) / 2, (height - side) / 2)
        ctx.scale(side / 100, side / 100)
        ctx.strokeStyle = iconColor
        ctx.fillStyle = iconColor
        ctx.lineCap = "round"
        ctx.lineJoin = "round"
        ctx.lineWidth = 4.5
        ctx.beginPath()
        ctx.arc(50, 53, 28, 0, Math.PI * 2)
        ctx.stroke()
        ctx.lineWidth = 5
        ctx.beginPath()
        ctx.moveTo(13, 57)
        ctx.bezierCurveTo(8, -4, 92, -4, 87, 57)
        ctx.stroke()
        function roundedFill(x, y, w, h, r) {
            ctx.beginPath()
            ctx.moveTo(x + r, y)
            ctx.lineTo(x + w - r, y)
            ctx.quadraticCurveTo(x + w, y, x + w, y + r)
            ctx.lineTo(x + w, y + h - r)
            ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h)
            ctx.lineTo(x + r, y + h)
            ctx.quadraticCurveTo(x, y + h, x, y + h - r)
            ctx.lineTo(x, y + r)
            ctx.quadraticCurveTo(x, y, x + r, y)
            ctx.closePath()
            ctx.fill()
        }
        roundedFill(7, 43, 11, 27, 5)
        roundedFill(82, 43, 11, 27, 5)
        var heights = [12, 24, 34, 24, 12]
        for (var i = 0; i < heights.length; ++i)
            roundedFill(33 + i * 7.5, 53 - heights[i] / 2, 4, heights[i], 2)
        ctx.restore()
    }
}
