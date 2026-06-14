import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    gradient: Gradient {
        orientation: Gradient.Vertical
        GradientStop { position: 0.0; color: "#1b0f45" }
        GradientStop { position: 0.42; color: "#0b1d4f" }
        GradientStop { position: 1.0; color: "#070b16" }
    }

    Rectangle {
        anchors.fill: parent
        opacity: 0.28
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "#2f8cff" }
            GradientStop { position: 0.5; color: "#00000000" }
            GradientStop { position: 1.0; color: "#8b5cf6" }
        }
    }

    signal closeRequested()

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons
        hoverEnabled: true
        preventStealing: true
        propagateComposedEvents: false
        onClicked: function(mouse) { mouse.accepted = true }
        onPressed: function(mouse) { mouse.accepted = true }
        onReleased: function(mouse) { mouse.accepted = true }
        onWheel: function(wheel) { wheel.accepted = true }
    }

    component GlassButton: Button {
        id: control
        font.pixelSize: 22
        font.bold: true
        contentItem: Text {
            text: control.text
            font: control.font
            color: control.enabled ? "#ffffff" : "#94a0b8"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        background: Rectangle {
            radius: 8
            color: control.checked ? "#668b5cf6" : "#3324145f"
            border.color: control.down || control.checked ? "#d9ccff" : "#7f67ff"
            border.width: 1
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: control.enabled ? "#556d28d9" : "#25293d" }
                GradientStop { position: 0.55; color: control.enabled ? "#448b5cf6" : "#2c3048" }
                GradientStop { position: 1.0; color: control.enabled ? "#332563eb" : "#25293d" }
            }
        }
    }

    property var games: [
        { id: "pong", titleKey: "game_pong", tint: "#ff9f43" },
        { id: "asteroids", titleKey: "game_asteroids", tint: "#4aa3ff" },
        { id: "fly", titleKey: "game_fly", tint: "#48d8ff" },
        { id: "pacman", titleKey: "game_pacman", tint: "#ffe35a" }
    ]
    property int gameIndex: 0
    property string gameId: games[gameIndex].id
    property string gameTitle: djconnect.t(games[gameIndex].titleKey)
    property color gameTint: games[gameIndex].tint
    property bool playing: false
    property int score: 0
    property var highScores: ({ pong: 0, asteroids: 0, fly: 0, pacman: 0 })
    property bool flash: false

    property real paddleY: 86
    property real ballX: 160
    property real ballY: 86
    property real ballVX: 3
    property real ballVY: 2
    property real shipX: 160
    property real asteroidX: 80
    property real asteroidY: 48
    property real asteroidVX: 2
    property real asteroidBulletY: 120
    property bool asteroidBulletActive: false
    property real planeY: 86
    property real obstacleX: 300
    property real obstacleY: 90
    property real flyShotX: 58
    property bool flyShotActive: false
    property real pacmanX: 46
    property real pacmanY: 86
    property real pacmanDX: 1
    property real pacmanDY: 0
    property real ghostX: 250
    property real ghostY: 86
    property int powerPellet: 23
    property int ghostVulnerableTicks: 0
    property var pellets: []

    function highScore() {
        return highScores[gameId] || 0
    }

    function setScore(value) {
        score = value
        if (value > highScore()) {
            highScores[gameId] = value
            highScoresChanged()
        }
    }

    function startGame() {
        if (!playing) playing = true
    }

    function resetGame() {
        score = 0
        paddleY = 86
        ballX = 160
        ballY = 86
        ballVX = 3
        ballVY = 2
        shipX = 160
        asteroidBulletActive = false
        planeY = 86
        flyShotActive = false
        resetPacman()
        resetAsteroid()
        resetObstacle()
        gameCanvas.requestPaint()
    }

    function resetAsteroid() {
        asteroidX = 40 + Math.random() * 240
        asteroidY = 46
        asteroidVX = Math.random() > 0.5 ? 2 : -2
    }

    function resetObstacle() {
        obstacleX = 310
        obstacleY = 52 + Math.random() * 86
    }

    function resetPacman() {
        pacmanX = 46
        pacmanY = 86
        pacmanDX = 1
        pacmanDY = 0
        ghostX = 250
        ghostY = 86
        powerPellet = 23
        ghostVulnerableTicks = 0
        pellets = []
        for (var i = 0; i < 24; i++) pellets.push(i)
    }

    function showFlash() {
        flash = true
        flashTimer.restart()
    }

    function selectGame(index) {
        gameIndex = index
        playing = false
        resetGame()
    }

    function move(direction) {
        startGame()
        if (gameId === "pong") {
            paddleY = Math.max(42, Math.min(126, paddleY + direction * 12))
        } else if (gameId === "asteroids") {
            shipX = Math.max(24, Math.min(296, shipX + direction * 14))
        } else if (gameId === "fly") {
            planeY = Math.max(52, Math.min(138, planeY + direction * 12))
        } else {
            pacmanDY = direction
            pacmanDX = 0
        }
        gameCanvas.requestPaint()
    }

    function moveHorizontal(direction) {
        startGame()
        if (gameId === "pacman") {
            pacmanDX = direction
            pacmanDY = 0
        } else if (gameId === "asteroids") {
            shipX = Math.max(24, Math.min(296, shipX + direction * 14))
        }
        gameCanvas.requestPaint()
    }

    function fire() {
        startGame()
        if (gameId === "asteroids" && !asteroidBulletActive) {
            asteroidBulletActive = true
            asteroidBulletY = 120
        } else if (gameId === "fly" && !flyShotActive) {
            flyShotActive = true
            flyShotX = 58
        }
    }

    function handleTouch(x, y) {
        startGame()
        var gx = x / gameCanvas.width * 320
        var gy = y / gameCanvas.height * 170
        if (gameId === "pong") {
            paddleY = Math.max(42, Math.min(126, gy))
        } else if (gameId === "asteroids") {
            shipX = Math.max(24, Math.min(296, gx))
        } else if (gameId === "fly") {
            planeY = Math.max(52, Math.min(138, gy))
        } else {
            var dx = gx - pacmanX
            var dy = gy - pacmanY
            if (Math.abs(dx) > Math.abs(dy)) {
                pacmanDX = dx < 0 ? -1 : 1
                pacmanDY = 0
            } else {
                pacmanDX = 0
                pacmanDY = dy < 0 ? -1 : 1
            }
        }
        gameCanvas.requestPaint()
    }

    function tickGame() {
        if (!playing) return
        if (gameId === "pong") {
            ballX += ballVX
            ballY += ballVY
            if (ballY <= 42 || ballY >= 156) ballVY *= -1
            if (ballX >= 306) ballVX = -Math.abs(ballVX)
            if (ballX <= 30) {
                if (ballY >= paddleY - 20 && ballY <= paddleY + 20) {
                    ballVX = Math.abs(ballVX)
                    setScore(score + 1)
                } else {
                    showFlash()
                    setScore(0)
                    ballX = 160
                    ballY = 86
                    ballVX = 3
                    ballVY = Math.random() > 0.5 ? 2 : -2
                }
            }
        } else if (gameId === "asteroids") {
            asteroidX += asteroidVX
            asteroidY += 2 + Math.min(Math.floor(score / 5), 3)
            if (asteroidX < 24 || asteroidX > 296) asteroidVX *= -1
            if (asteroidBulletActive) {
                asteroidBulletY -= 8
                if (asteroidBulletY < 36) asteroidBulletActive = false
                else if (Math.abs(asteroidX - shipX) < 16 && Math.abs(asteroidY - asteroidBulletY) < 16) {
                    asteroidBulletActive = false
                    setScore(score + 1)
                    resetAsteroid()
                }
            }
            if (asteroidY > 150) {
                showFlash()
                setScore(0)
                resetAsteroid()
            }
        } else if (gameId === "fly") {
            obstacleX -= 4 + Math.min(Math.floor(score / 6), 4)
            if (flyShotActive) {
                flyShotX += 9
                if (flyShotX > 310) flyShotActive = false
                else if (Math.abs(flyShotX - obstacleX) < 16 && Math.abs(planeY - obstacleY) < 24) {
                    flyShotActive = false
                    setScore(score + 1)
                    resetObstacle()
                }
            }
            if (obstacleX < 24) {
                setScore(score + 1)
                resetObstacle()
            }
            if (obstacleX < 66 && obstacleX > 28 && Math.abs(planeY - obstacleY) < 28) {
                showFlash()
                setScore(0)
                resetObstacle()
            }
        } else {
            pacmanX = Math.max(28, Math.min(292, pacmanX + pacmanDX * 4))
            pacmanY = Math.max(44, Math.min(140, pacmanY + pacmanDY * 4))
            if (ghostVulnerableTicks > 0) ghostVulnerableTicks -= 1
            var step = ghostVulnerableTicks > 0 ? 1 : 1.35 + Math.min(Math.floor(score / 14) * 0.45, 1.8)
            if (Math.abs(ghostX - pacmanX) > 2) ghostX += ghostX < pacmanX ? step : -step
            if (Math.abs(ghostY - pacmanY) > 2) ghostY += ghostY < pacmanY ? step : -step
            for (var p = 0; p < pellets.length; p++) {
                var pellet = pellets[p]
                var px = 48 + (pellet % 8) * 28
                var py = 52 + Math.floor(pellet / 8) * 28
                if (Math.abs(px - pacmanX) < 10 && Math.abs(py - pacmanY) < 10) {
                    pellets.splice(p, 1)
                    if (pellet === powerPellet) {
                        ghostVulnerableTicks = 210
                        setScore(score + 3)
                    } else {
                        setScore(score + 1)
                    }
                    break
                }
            }
            if (pellets.length === 0) resetPacman()
            if (Math.abs(ghostX - pacmanX) < 14 && Math.abs(ghostY - pacmanY) < 14) {
                if (ghostVulnerableTicks > 0) {
                    setScore(score + 5)
                    ghostX = 250
                    ghostY = 86
                    ghostVulnerableTicks = 0
                } else {
                    showFlash()
                    setScore(0)
                    resetPacman()
                }
            }
        }
        gameCanvas.requestPaint()
    }

    Timer {
        interval: 33
        running: root.visible && playing
        repeat: true
        onTriggered: tickGame()
    }

    Timer {
        id: flashTimer
        interval: 350
        repeat: false
        onTriggered: {
            flash = false
            gameCanvas.requestPaint()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        anchors.bottomMargin: 130
        spacing: 12

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Text {
                text: djconnect.t("games")
                color: "#f4f8f8"
                font.pixelSize: 30
                font.bold: true
                Layout.fillWidth: true
            }

        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Repeater {
                model: root.games
                GlassButton {
                    text: djconnect.t(modelData.titleKey)
                    checkable: true
                    checked: index === root.gameIndex
                    Layout.fillWidth: true
                    onClicked: root.selectGame(index)
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 14

            Text {
                text: root.gameTitle
                color: root.gameTint
                font.pixelSize: 24
                font.bold: true
                Layout.fillWidth: true
            }

            Text {
                text: djconnect.t("score") + " " + root.score
                color: "#f4f8f8"
                font.pixelSize: 18
                font.bold: true
            }

            Text {
                text: djconnect.t("high") + " " + root.highScore()
                color: "#9fb4b8"
                font.pixelSize: 18
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 318

            Canvas {
                id: gameCanvas
                anchors.fill: parent
                antialiasing: true

                onPaint: {
                    var ctx = getContext("2d")
                    var sx = width / 320
                    var sy = height / 170
                    function rx(v) { return v * sx }
                    function ry(v) { return v * sy }
                    ctx.setLineDash([])
                    ctx.fillStyle = "#05080a"
                    ctx.fillRect(0, 0, width, height)
                    ctx.strokeStyle = "#26383d"
                    ctx.lineWidth = 2
                    ctx.strokeRect(1, 1, width - 2, height - 2)
                    ctx.fillStyle = root.gameTint
                    ctx.font = Math.max(16, 14 * sx) + "px sans-serif"
                    ctx.fillText(root.gameTitle, rx(12), ry(20))

                    if (root.gameId === "pong") {
                        ctx.strokeStyle = "rgba(255,255,255,0.22)"
                        ctx.setLineDash([rx(5), rx(7)])
                        ctx.beginPath()
                        ctx.moveTo(rx(160), ry(28))
                        ctx.lineTo(rx(160), ry(150))
                        ctx.stroke()
                        ctx.setLineDash([])
                        ctx.fillStyle = "#ff9f43"
                        ctx.fillRect(rx(18), ry(root.paddleY - 17), rx(8), ry(34))
                        if (root.playing) {
                            ctx.fillStyle = "#1db954"
                            ctx.beginPath()
                            ctx.arc(rx(root.ballX), ry(root.ballY), Math.max(rx(4), ry(4)), 0, Math.PI * 2)
                            ctx.fill()
                        }
                    } else if (root.gameId === "asteroids") {
                        ctx.strokeStyle = "#4aa3ff"
                        ctx.lineWidth = 2
                        ctx.beginPath()
                        ctx.moveTo(rx(root.shipX), ry(128))
                        ctx.lineTo(rx(root.shipX - 9), ry(146))
                        ctx.lineTo(rx(root.shipX + 9), ry(146))
                        ctx.closePath()
                        ctx.stroke()
                        ctx.strokeStyle = "#ff6fb3"
                        ctx.beginPath()
                        ctx.arc(rx(root.asteroidX), ry(root.asteroidY), Math.max(rx(10), ry(10)), 0, Math.PI * 2)
                        ctx.stroke()
                        if (root.asteroidBulletActive) {
                            ctx.fillStyle = "#48d8ff"
                            ctx.fillRect(rx(root.shipX - 2), ry(root.asteroidBulletY), rx(4), ry(10))
                        }
                    } else if (root.gameId === "fly") {
                        ctx.fillStyle = "#48d8ff"
                        ctx.beginPath()
                        ctx.moveTo(rx(62), ry(root.planeY))
                        ctx.lineTo(rx(30), ry(root.planeY - 12))
                        ctx.lineTo(rx(30), ry(root.planeY + 12))
                        ctx.closePath()
                        ctx.fill()
                        ctx.fillStyle = "#9a6b3f"
                        ctx.fillRect(rx(root.obstacleX - 8), ry(root.obstacleY - 18), rx(16), ry(36))
                        if (root.flyShotActive) {
                            ctx.fillStyle = "#d9fbff"
                            ctx.fillRect(rx(root.flyShotX), ry(root.planeY - 2), rx(14), ry(4))
                        }
                    } else {
                        ctx.fillStyle = "rgba(255,255,255,0.82)"
                        for (var i = 0; i < root.pellets.length; i++) {
                            var pellet = root.pellets[i]
                            var col = pellet % 8
                            var row = Math.floor(pellet / 8)
                            var isPowerPellet = pellet === root.powerPellet
                            ctx.beginPath()
                            ctx.arc(
                                rx(48 + col * 28),
                                ry(52 + row * 28),
                                isPowerPellet ? Math.max(rx(5), ry(5)) : Math.max(rx(2), ry(2)),
                                0,
                                Math.PI * 2
                            )
                            ctx.fill()
                        }
                        var pacRadius = Math.max(rx(10), ry(10))
                        var mouthCenter = root.pacmanDX < 0 ? Math.PI
                            : root.pacmanDY < 0 ? Math.PI * 1.5
                            : root.pacmanDY > 0 ? Math.PI / 2
                            : 0
                        var mouthOpen = Math.PI / 5
                        ctx.fillStyle = "#ffe35a"
                        ctx.beginPath()
                        ctx.moveTo(rx(root.pacmanX), ry(root.pacmanY))
                        ctx.arc(
                            rx(root.pacmanX),
                            ry(root.pacmanY),
                            pacRadius,
                            mouthCenter + mouthOpen,
                            mouthCenter + Math.PI * 2 - mouthOpen,
                            false
                        )
                        ctx.closePath()
                        ctx.fill()
                        var ghostBlink = root.ghostVulnerableTicks > 0 && Math.floor(root.ghostVulnerableTicks / 12) % 2 === 0
                        ctx.fillStyle = root.ghostVulnerableTicks > 0 ? (ghostBlink ? "#e0f2fe" : "#3b82f6") : "#ff6fb3"
                        ctx.beginPath()
                        ctx.arc(rx(root.ghostX), ry(root.ghostY - 2), Math.max(rx(9), ry(9)), Math.PI, 0)
                        ctx.lineTo(rx(root.ghostX + 9), ry(root.ghostY + 9))
                        ctx.lineTo(rx(root.ghostX + 4), ry(root.ghostY + 5))
                        ctx.lineTo(rx(root.ghostX), ry(root.ghostY + 9))
                        ctx.lineTo(rx(root.ghostX - 4), ry(root.ghostY + 5))
                        ctx.lineTo(rx(root.ghostX - 9), ry(root.ghostY + 9))
                        ctx.closePath()
                        ctx.fill()
                        ctx.fillStyle = "#ffffff"
                        ctx.beginPath()
                        ctx.arc(rx(root.ghostX - 4), ry(root.ghostY - 2), Math.max(rx(2.6), ry(2.6)), 0, Math.PI * 2)
                        ctx.arc(rx(root.ghostX + 4), ry(root.ghostY - 2), Math.max(rx(2.6), ry(2.6)), 0, Math.PI * 2)
                        ctx.fill()
                        ctx.fillStyle = "#1d2bff"
                        ctx.beginPath()
                        ctx.arc(rx(root.ghostX - 3), ry(root.ghostY - 2), Math.max(rx(1.2), ry(1.2)), 0, Math.PI * 2)
                        ctx.arc(rx(root.ghostX + 5), ry(root.ghostY - 2), Math.max(rx(1.2), ry(1.2)), 0, Math.PI * 2)
                        ctx.fill()
                    }

                    if (root.flash) {
                        ctx.strokeStyle = "#ff5b5b"
                        ctx.lineWidth = 5
                        ctx.strokeRect(4, 4, width - 8, height - 8)
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    onPressed: function(mouse) { root.handleTouch(mouse.x, mouse.y) }
                    onPositionChanged: function(mouse) { root.handleTouch(mouse.x, mouse.y) }
                    onReleased: root.fire()
                }
            }

            GlassButton {
                anchors.centerIn: parent
                visible: !root.playing
                text: djconnect.t("tap_to_play")
                font.pixelSize: 22
                onClicked: root.startGame()
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 66
            spacing: 10

            GlassButton {
                text: root.gameId === "asteroids" ? djconnect.t("left") : djconnect.t("up")
                Layout.fillWidth: true
                Layout.fillHeight: true
                onClicked: root.gameId === "asteroids" ? root.moveHorizontal(-1) : root.move(-1)
            }

            GlassButton {
                text: root.gameId === "asteroids" ? djconnect.t("right") : djconnect.t("down")
                Layout.fillWidth: true
                Layout.fillHeight: true
                onClicked: root.gameId === "asteroids" ? root.moveHorizontal(1) : root.move(1)
            }

            GlassButton {
                visible: root.gameId === "asteroids" || root.gameId === "fly"
                text: djconnect.t("fire")
                Layout.fillWidth: true
                Layout.fillHeight: true
                onClicked: root.fire()
            }

            GlassButton {
                text: djconnect.t("reset")
                Layout.fillWidth: true
                Layout.fillHeight: true
                onClicked: {
                    root.playing = false
                    root.resetGame()
                }
            }
        }

        Text {
            text: root.gameId === "pong" ? djconnect.t("game_help_pong")
                : root.gameId === "asteroids" ? djconnect.t("game_help_asteroids")
                : root.gameId === "fly" ? djconnect.t("game_help_fly")
                : djconnect.t("game_help_pacman")
            color: "#9fb4b8"
            font.pixelSize: 15
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
    }

    Component.onCompleted: resetGame()
}
