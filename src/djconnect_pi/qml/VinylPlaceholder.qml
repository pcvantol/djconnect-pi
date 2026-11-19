import QtQuick
import "BrandTheme.js" as BrandTheme

// Local, decorative fallback adapted from Apple's AlbumArtworkPlaceholder.
// No downloaded cover, provider request or inferred media permission.
GlassSurface {
    id: card
    implicitWidth: 320
    implicitHeight: width
    radius: 32
    Accessible.ignored: true
    Rectangle {
        id: record
        width: parent.width * 0.66; height: width
        anchors.centerIn: parent; radius: width / 2
        gradient: Gradient {
            GradientStop { position: 0; color: "#1F2133" }
            GradientStop { position: 1; color: "#060812" }
        }
        Repeater {
            model: [0.78, 0.90]
            Rectangle {
                required property real modelData
                anchors.centerIn: parent
                width: record.width * modelData; height: width; radius: width / 2
                color: "transparent"; border.color: "#0Cffffff"; border.width: 1
            }
        }
        Rectangle {
            anchors.centerIn: parent
            width: parent.width * 0.26; height: width; radius: width / 2
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0; color: BrandTheme.colors.blue }
                GradientStop { position: 1; color: BrandTheme.colors.purple }
            }
            Rectangle {
                anchors.centerIn: parent
                width: record.width * 0.045; height: width; radius: width / 2
                color: "#090A17"
            }
        }
    }
    Canvas {
        anchors.fill: parent
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset(); ctx.clearRect(0, 0, width, height)
            var d = Math.min(width, height) * 0.66
            ctx.save(); ctx.translate(width / 2, height / 2); ctx.scale(d, d)
            ctx.lineCap = "round"; ctx.lineJoin = "round"
            ctx.fillStyle = "#292929"; ctx.strokeStyle = "#66ffffff"; ctx.lineWidth = 0.004
            ctx.beginPath(); ctx.arc(0.44, -0.38, 0.055, 0, 2 * Math.PI); ctx.fill(); ctx.stroke()
            ctx.fillStyle = "#8C8C8C"; ctx.fillRect(0.412, -0.485, 0.065, 0.07)
            ctx.beginPath(); ctx.moveTo(0.45, -0.46); ctx.lineTo(0.44, -0.38)
            ctx.lineTo(0.38, 0.035); ctx.lineTo(0.18, 0.185)
            ctx.strokeStyle = "#2E2E2E"; ctx.lineWidth = 0.028; ctx.stroke()
            ctx.strokeStyle = "#DDDDDD"; ctx.lineWidth = 0.016; ctx.stroke()
            ctx.fillStyle = "#B2B2B2"
            ctx.beginPath(); ctx.arc(0.44, -0.38, 0.022, 0, 2 * Math.PI); ctx.fill()
            ctx.beginPath(); ctx.moveTo(0.215, 0.17); ctx.lineTo(0.177, 0.13)
            ctx.lineTo(0.112, 0.207); ctx.lineTo(0.15, 0.245); ctx.closePath()
            ctx.fillStyle = "#2E2940"; ctx.fill(); ctx.strokeStyle = "#8Cffffff"; ctx.lineWidth = 0.004; ctx.stroke()
            ctx.beginPath(); ctx.moveTo(0.13, 0.225); ctx.lineTo(0.113, 0.25)
            ctx.strokeStyle = "#E6ffffff"; ctx.lineWidth = 0.006; ctx.stroke()
            ctx.restore()
        }
    }
}
