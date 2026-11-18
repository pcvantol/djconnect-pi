import QtQuick
import "BrandTheme.js" as BrandTheme

Item {
    id: artwork
    property bool animate: false
    readonly property real size: Math.min(width, height)
    Accessible.ignored: true

    Canvas {
        anchors.fill: parent
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            var x = width / 2
            var y = height / 2
            var glow = ctx.createRadialGradient(x, y, 0, x, y, Math.max(1, artwork.size * 0.49))
            glow.addColorStop(0, "#A67959FF")
            glow.addColorStop(0.65, "#63734DE0")
            glow.addColorStop(1, "#00734DE0")
            ctx.fillStyle = glow
            ctx.fillRect(0, 0, width, height)
        }
    }
    Rectangle {
        id: record
        objectName: "welcomeVinylRecord"
        width: artwork.size * 0.79
        height: width
        radius: width / 2
        anchors.centerIn: parent
        border.color: "#39FFFFFF"
        gradient: Gradient {
            GradientStop { position: 0; color: "#0A0916" }
            GradientStop { position: 1; color: "#302454" }
        }
        Repeater {
            model: [0.53, 0.61, 0.70, 0.78, 0.86]
            Rectangle {
                required property real modelData
                width: record.width * modelData
                height: width
                radius: width / 2
                anchors.centerIn: parent
                color: "transparent"
                border.color: "#13FFFFFF"
            }
        }
        Canvas {
            anchors.fill: parent
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()
            onPaint: {
                var ctx = getContext("2d")
                ctx.reset()
                var x = width / 2
                var y = height / 2
                var shine = ctx.createLinearGradient(x, y - width * 0.26, x, y + width * 0.31)
                shine.addColorStop(0, "#00FFFFFF")
                shine.addColorStop(0.50, "#35FFFFFF")
                shine.addColorStop(1, "#00FFFFFF")
                ctx.fillStyle = shine
                ctx.beginPath()
                ctx.arc(x, y, width * 0.46, -0.6, 0.72)
                ctx.arc(x, y, width * 0.30, 0.72, -0.6, true)
                ctx.closePath()
                ctx.fill()
            }
        }
        Rectangle {
            width: artwork.size * 0.32
            height: width
            radius: width / 2
            anchors.centerIn: parent
            gradient: Gradient {
                GradientStop { position: 0; color: "#5377FF" }
                GradientStop { position: 1; color: "#CA46ED" }
            }
            Rectangle {
                width: artwork.size * 0.07
                height: width
                radius: width / 2
                anchors.centerIn: parent
                color: "#0A0819"
            }
        }
        RotationAnimation on rotation {
            running: artwork.animate && artwork.visible && GlassStyle.awake && !GlassStyle.reduceMotion
                && Qt.application.state === Qt.ApplicationActive
            from: 0; to: 360
            duration: 8000
            loops: Animation.Infinite
        }
    }
    Repeater {
        model: [{icon: "music", x: 0.35, y: -0.25}, {icon: "presence_balanced", x: -0.35, y: 0.13}]
        GlassSurface {
            required property var modelData
            width: artwork.size * 0.18
            height: width
            radius: width / 3
            x: artwork.width / 2 + artwork.size * modelData.x - width / 2
            y: artwork.height / 2 + artwork.size * modelData.y - height / 2
            introduction: true
            FeatureIcon {
                anchors.centerIn: parent
                width: parent.width * 0.63
                height: width
                iconName: modelData.icon
                heroGradient: true
            }
        }
    }
    GlassSurface {
        objectName: "welcomeVinylWaveBadge"
        width: artwork.size * 0.32
        height: artwork.size * 0.18
        radius: height / 2
        x: artwork.width / 2 + artwork.size * 0.16 - width / 2
        y: artwork.height / 2 + artwork.size * 0.32 - height / 2
        introduction: true
        Row {
            anchors.centerIn: parent
            spacing: artwork.size * 0.012
            Repeater {
                model: [10, 18, 28, 15, 34, 23, 12, 27, 17]
                Item {
                    required property int modelData
                    width: artwork.size * 0.015
                    height: artwork.size * 0.10
                    Rectangle {
                        width: parent.width
                        height: parent.height * modelData / 34
                        anchors.centerIn: parent
                        radius: width / 2
                        gradient: Gradient {
                            GradientStop { position: 0; color: BrandTheme.colors.blue }
                            GradientStop { position: 1; color: "#CA46ED" }
                        }
                    }
                }
            }
        }
    }
}
