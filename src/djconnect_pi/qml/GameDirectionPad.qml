import QtQuick
import QtQuick.Controls
import "BrandTheme.js" as BrandTheme

Item {
    id: pad
    required property bool horizontal
    required property bool vertical
    required property bool canFire
    required property color accent
    required property var translate
    signal direction(string name)
    signal fire()

    Rectangle {
        anchors.fill: parent
        radius: width / 2
        color: "#38000000"
        border.color: "#22FFFFFF"
    }
    Item {
        id: cross
        anchors.centerIn: parent
        width: Math.floor(pad.width * 0.89)
        height: width
        readonly property real cell: width / 3

        Canvas {
            anchors.fill: parent
            onPaint: {
                var ctx = getContext("2d")
                var d = cross.cell
                ctx.reset()
                ctx.beginPath()
                ctx.moveTo(d, 1); ctx.lineTo(2*d, 1); ctx.lineTo(2*d, d); ctx.lineTo(3*d-1, d)
                ctx.lineTo(3*d-1, 2*d); ctx.lineTo(2*d, 2*d); ctx.lineTo(2*d, 3*d-1)
                ctx.lineTo(d, 3*d-1); ctx.lineTo(d, 2*d); ctx.lineTo(1, 2*d); ctx.lineTo(1, d)
                ctx.lineTo(d, d); ctx.closePath()
                var material = ctx.createLinearGradient(0, 0, width, height)
                material.addColorStop(0, "#525257")
                material.addColorStop(1, "#1D1D22")
                ctx.fillStyle = material
                ctx.fill()
                ctx.strokeStyle = "#70FFFFFF"
                ctx.stroke()
            }
        }
        Repeater {
            model: [
                {name: "up", col: 1, row: 0, icon: "▲"},
                {name: "left", col: 0, row: 1, icon: "◀"},
                {name: "fire", col: 1, row: 1, icon: "✦"},
                {name: "right", col: 2, row: 1, icon: "▶"},
                {name: "down", col: 1, row: 2, icon: "▼"}
            ]
            AbstractButton {
                id: key
                required property var modelData
                objectName: "gamePad-" + modelData.name
                readonly property bool center: modelData.name === "fire"
                enabled: center ? pad.canFire : modelData.col === 1 ? pad.vertical : pad.horizontal
                x: modelData.col * cross.cell
                y: modelData.row * cross.cell
                width: cross.cell; height: width
                text: pad.translate(modelData.name)
                Accessible.name: text
                background: Rectangle {
                    anchors.centerIn: parent
                    width: key.center ? key.width * 0.72 : key.width - 4
                    height: width
                    radius: key.center ? width / 2 : 7
                    color: key.center ? key.enabled ? pad.accent : "#18FFFFFF" : key.down ? "#38FFFFFF" : "transparent"
                    border.color: key.visualFocus ? BrandTheme.colors.text : "transparent"
                    border.width: key.visualFocus ? 2 : 0
                }
                contentItem: Text {
                    text: key.modelData.icon
                    color: key.center && key.enabled && pad.accent.g > 0.78 ? "#17171C" : "#FFFFFF"
                    opacity: key.enabled ? 0.88 : 0.25
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: Math.round(key.width * (key.center ? 0.46 : 0.32))
                }
                onClicked: {
                    if (center) pad.fire()
                    else pad.direction(modelData.name)
                }
            }
        }
    }
}
