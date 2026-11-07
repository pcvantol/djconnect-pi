import QtQuick
import "BrandTheme.js" as BrandTheme
import QtQuick.Controls
import QtQuick.Layouts
import "MoodTheme.js" as MoodTheme

Rectangle {
    id: root
    objectName: "gamesPanel"
    readonly property bool compact: width < 900
    color: BrandTheme.colors.background
    SessionMoodCanvas { anchors.fill: parent; mood: root.gameMood; activeSession: true }

    signal closeRequested()

    property int trVersion: djconnect.translationVersion

    function tr(key) {
        root.trVersion
        return djconnect.t(key)
    }

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

    property var games: [
        { id: "pong", titleKey: "game_pong", mood: "chill", icon: "game_racket" },
        { id: "asteroids", titleKey: "game_asteroids", mood: "groove", icon: "mood_chill" },
        { id: "fly", titleKey: "game_fly", mood: "energy", icon: "game_plane" },
        { id: "pacman", titleKey: "game_pacman", mood: "party", icon: "game_maze" }
    ]
    property int gameIndex: 0
    property string gameId: games[gameIndex].id
    property string gameTitle: root.tr(games[gameIndex].titleKey)
    readonly property string gameMood: games[gameIndex].mood
    readonly property color gameTint: MoodTheme.moodColor(gameMood, "gradientStart")
    readonly property bool horizontalControls: gameId === "asteroids" || gameId === "pacman"
    readonly property bool verticalControls: gameId !== "asteroids"
    readonly property bool fireControl: gameId === "asteroids" || gameId === "fly"
    function useDirection(direction) {
        if (direction === "left" || direction === "right") {
            if (horizontalControls) moveHorizontal(direction === "left" ? -1 : 1)
        } else if (verticalControls) move(direction === "up" ? -1 : 1)
    }
    onVisibleChanged: {
        if (visible) forceActiveFocus()
        else playing = false
    }
    Keys.onUpPressed: root.useDirection("up")
    Keys.onDownPressed: root.useDirection("down")
    Keys.onLeftPressed: root.useDirection("left")
    Keys.onRightPressed: root.useDirection("right")
    Keys.onSpacePressed: root.fire()
    Keys.onEscapePressed: root.closeRequested()
    property bool playing: false
    property int score: 0
    property var highScores: ({ pong: 0, asteroids: 0, fly: 0, pacman: 0 })
    property bool flash: false
    property int pauseTicks: 0
    property int hitPulseTicks: 0
    property int wallPulseTicks: 0
    property int deathTicks: 0
    property var explosions: []
    property var stars: []

    property real paddleY: 86
    property real ballX: 160
    property real ballY: 86
    property real ballVX: 3
    property real ballVY: 2
    property real shipX: 160
    property real asteroidX: 80
    property real asteroidY: 48
    property real asteroidVX: 2
    property real asteroidSpeed: 1.2
    property real asteroidSize: 9
    property int asteroidShape: 0
    property real asteroidBulletY: 120
    property bool asteroidBulletActive: false
    property real planeY: 86
    property real obstacleX: 300
    property real obstacleY: 90
    property int obstacleShape: 0
    property color obstacleColor: "#9a6b3f"
    property real flyShotX: 58
    property bool flyShotActive: false
    property real pacmanX: 46
    property real pacmanY: 86
    property real pacmanDX: 1
    property real pacmanDY: 0
    property real ghostX: 250
    property real ghostY: 86
    readonly property int pacmanPelletColumns: compact ? 10 : 11
    readonly property int pacmanPelletRows: compact ? 6 : 10
    readonly property real pacmanPelletOriginX: compact ? 20 : 40
    readonly property real pacmanPelletOriginY: compact ? 24 : 21
    readonly property real pacmanPelletSpacingX: (320 - 2 * pacmanPelletOriginX) / (pacmanPelletColumns - 1)
    readonly property real pacmanPelletSpacingY: (compact ? 140 : 128) / (pacmanPelletRows - 1)
    readonly property int pelletCount: pacmanPelletColumns * pacmanPelletRows
    readonly property var powerPellets: [0, pacmanPelletColumns - 1, pelletCount - pacmanPelletColumns, pelletCount - 1]
    onCompactChanged: if (gameCanvas && gameId === "pacman") resetGame()
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
        if (!playing) {
            playing = true
            playSfx("start")
        }
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
        pauseTicks = 0
        hitPulseTicks = 0
        wallPulseTicks = 0
        deathTicks = 0
        explosions = []
        resetStars()
        resetPacman()
        resetAsteroid()
        resetObstacle()
        gameCanvas.requestPaint()
    }

    function resetAsteroid() {
        asteroidX = 40 + Math.random() * 240
        asteroidY = 34
        asteroidVX = 0
        asteroidSpeed = 0.95 + Math.random() * 1.25 + Math.min(score / 30, 1.4)
        asteroidSize = 6 + Math.random() * 7
        asteroidShape = Math.floor(Math.random() * 3)
    }

    function resetObstacle() {
        obstacleX = 310
        obstacleY = 52 + Math.random() * 86
        obstacleShape = Math.floor(Math.random() * 4)
        var colors = ["#9a6b3f", "#e879f9", "#38bdf8", "#facc15"]
        obstacleColor = colors[obstacleShape]
    }

    function resetPacman() {
        pacmanX = 46
        pacmanY = 86
        pacmanDX = 1
        pacmanDY = 0
        ghostX = 250
        ghostY = 86
        ghostVulnerableTicks = 0
        deathTicks = 0
        pellets = []
        for (var i = 0; i < pacmanPelletColumns * pacmanPelletRows; i++) pellets.push(i)
    }

    function pacmanPelletX(pellet) {
        return pacmanPelletOriginX + (pellet % pacmanPelletColumns) * pacmanPelletSpacingX
    }

    function pacmanPelletY(pellet) {
        return pacmanPelletOriginY + Math.floor(pellet / pacmanPelletColumns) * pacmanPelletSpacingY
    }

    function pacmanMinX() {
        return pacmanPelletOriginX
    }

    function pacmanMaxX() {
        return pacmanPelletOriginX + (pacmanPelletColumns - 1) * pacmanPelletSpacingX
    }

    function pacmanMinY() {
        return pacmanPelletOriginY
    }

    function pacmanMaxY() {
        return pacmanPelletOriginY + (pacmanPelletRows - 1) * pacmanPelletSpacingY
    }

    function resetStars() {
        stars = []
        for (var i = 0; i < 32; i++) {
            stars.push({ x: Math.random() * 320, y: 30 + Math.random() * 130, speed: 0.35 + Math.random() * 1.8, phase: Math.random() * 6.28 })
        }
    }

    function showFlash() {
        flash = true
        flashTimer.restart()
    }

    function playSfx(kind) {
        djconnect.playGameSound(kind)
        haptic()
    }

    function haptic() {
        if (typeof navigator !== "undefined" && navigator.vibrate) navigator.vibrate(10)
    }

    function addExplosion(x, y, tint) {
        explosions.push({ x: x, y: y, age: 0, tint: tint })
    }

    function selectGame(index) {
        gameIndex = index
        playing = false
        resetGame()
    }

    function move(direction) {
        startGame()
        playSfx("move")
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
        playSfx("move")
        if (gameId === "pacman") {
            pacmanDX = direction
            pacmanDY = 0
        } else if (gameId === "asteroids") {
            shipX = Math.max(24, Math.min(296, shipX + direction * 14))
        }
        gameCanvas.requestPaint()
    }

    function fire() {
        if (!fireControl) return
        startGame()
        if (gameId === "asteroids" && !asteroidBulletActive) {
            asteroidBulletActive = true
            asteroidBulletY = 120
            playSfx("fire")
        } else if (gameId === "fly" && !flyShotActive) {
            flyShotActive = true
            flyShotX = 58
            playSfx("fire")
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
        for (var e = explosions.length - 1; e >= 0; e--) {
            explosions[e].age += 1
            if (explosions[e].age > 18) explosions.splice(e, 1)
        }
        if (pauseTicks > 0) {
            pauseTicks -= 1
            gameCanvas.requestPaint()
            return
        }
        if (hitPulseTicks > 0) hitPulseTicks -= 1
        if (wallPulseTicks > 0) wallPulseTicks -= 1
        for (var s = 0; s < stars.length; s++) {
            stars[s].x -= stars[s].speed * (gameId === "fly" ? 1.8 : 0.45)
            stars[s].phase += 0.08
            if (stars[s].x < 0) {
                stars[s].x = 320
                stars[s].y = 30 + Math.random() * 130
            }
        }
        if (gameId === "pong") {
            ballX += ballVX
            ballY += ballVY
            if (ballY <= 42 || ballY >= 156) {
                ballVY *= -1
                wallPulseTicks = 8
                playSfx("wall")
            }
            if (ballX >= 306) {
                ballVX = -Math.abs(ballVX)
                wallPulseTicks = 8
                playSfx("wall")
            }
            if (ballX <= 30) {
                if (ballY >= paddleY - 20 && ballY <= paddleY + 20) {
                    ballVX = Math.abs(ballVX)
                    hitPulseTicks = 10
                    playSfx("hit")
                    setScore(score + 1)
                } else {
                    showFlash()
                    playSfx("gameover")
                    setScore(0)
                    ballX = 160
                    ballY = 86
                    ballVX = 3
                    ballVY = Math.random() > 0.5 ? 2 : -2
                    pauseTicks = 26
                }
            }
        } else if (gameId === "asteroids") {
            asteroidY += asteroidSpeed
            if (asteroidBulletActive) {
                asteroidBulletY -= 8
                if (asteroidBulletY < 36) asteroidBulletActive = false
                else if (Math.abs(asteroidX - shipX) < asteroidSize + 8 && Math.abs(asteroidY - asteroidBulletY) < asteroidSize + 8) {
                    asteroidBulletActive = false
                    addExplosion(asteroidX, asteroidY, "#ff6fb3")
                    playSfx("explode")
                    setScore(score + 1)
                    resetAsteroid()
                }
            }
            if (asteroidY > 150) {
                showFlash()
                playSfx("gameover")
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
                    addExplosion(obstacleX, obstacleY, "#facc15")
                    playSfx("explode")
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
                addExplosion(48, planeY, "#ff5b5b")
                playSfx("crash")
                setScore(0)
                resetObstacle()
            }
        } else {
            if (deathTicks > 0) {
                deathTicks -= 1
                if (deathTicks === 0) {
                    setScore(0)
                    resetPacman()
                }
                gameCanvas.requestPaint()
                return
            }
            pacmanX = Math.max(pacmanMinX(), Math.min(pacmanMaxX(), pacmanX + pacmanDX * 4))
            pacmanY = Math.max(pacmanMinY(), Math.min(pacmanMaxY(), pacmanY + pacmanDY * 4))
            if (ghostVulnerableTicks > 0) ghostVulnerableTicks -= 1
            var step = ghostVulnerableTicks > 0 ? 1 : 1.35 + Math.min(Math.floor(score / 14) * 0.45, 1.8)
            if (Math.abs(ghostX - pacmanX) > 2) ghostX += ghostX < pacmanX ? step : -step
            if (Math.abs(ghostY - pacmanY) > 2) ghostY += ghostY < pacmanY ? step : -step
            for (var p = 0; p < pellets.length; p++) {
                var pellet = pellets[p]
                var px = pacmanPelletX(pellet)
                var py = pacmanPelletY(pellet)
                if (Math.abs(px - pacmanX) < 10 && Math.abs(py - pacmanY) < Math.min(10, pacmanPelletSpacingY / 2)) {
                    pellets.splice(p, 1)
                    if (powerPellets.indexOf(pellet) >= 0) {
                        ghostVulnerableTicks = 210
                        playSfx("power")
                        setScore(score + 3)
                    } else {
                        playSfx("pellet")
                        setScore(score + 1)
                    }
                    break
                }
            }
            if (pellets.length === 0) resetPacman()
            if (Math.abs(ghostX - pacmanX) < 14 && Math.abs(ghostY - pacmanY) < 14) {
                if (ghostVulnerableTicks > 0) {
                    setScore(score + 5)
                    playSfx("ghost")
                    ghostX = 250
                    ghostY = 86
                    ghostVulnerableTicks = 0
                } else {
                    showFlash()
                    playSfx("death")
                    deathTicks = 34
                    pauseTicks = 0
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
        anchors.margins: root.compact ? 14 : 26
        anchors.bottomMargin: root.compact ? 120 : 130
        spacing: root.compact ? 8 : 20

        RowLayout {
            Layout.fillWidth: true
            GlassButton {
                objectName: "gameBack"
                iconName: "back"; Accessible.name: root.tr("more")
                implicitWidth: 48; implicitHeight: 48; padding: 10
                onClicked: root.closeRequested()
            }
            Item { Layout.fillWidth: true }
            GlassSurface {
                id: gameSelector
                Layout.preferredWidth: selector.implicitWidth + 12
                Layout.preferredHeight: root.compact ? 50 : 66
                radius: height / 2
                RowLayout {
                    id: selector
                    anchors.centerIn: parent
                    spacing: root.compact ? 1 : 8
                    Repeater {
                        model: root.games
                        GlassButton {
                            required property var modelData
                            required property int index
                            objectName: "gameSelect-" + modelData.id
                            iconName: modelData.icon
                            Accessible.name: root.tr(modelData.titleKey)
                            ToolTip.text: Accessible.name
                            ToolTip.visible: hovered
                            checked: index === root.gameIndex
                            foregroundColor: checked ? BrandTheme.colors.actionAccent : BrandTheme.colors.text
                            implicitWidth: root.compact ? 48 : 64
                            implicitHeight: root.compact ? 46 : 58
                            padding: 9
                            background: Item {}
                            onClicked: root.selectGame(index)
                        }
                    }
                    GlassButton {
                        objectName: "gameReset"
                        iconName: "refresh"; Accessible.name: root.tr("reset")
                        implicitWidth: root.compact ? 48 : 64
                        implicitHeight: root.compact ? 46 : 58
                        padding: 9; background: Item {}
                        onClicked: { root.playing = false; root.resetGame() }
                    }
                }
            }
        }

        GlassCard {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 0
            padding: root.compact ? 12 : 20
            spacing: root.compact ? 8 : 18

            RowLayout {
                Layout.fillWidth: true
                spacing: 12
                FeatureIcon {
                    iconName: root.games[root.gameIndex].icon
                    iconColor: root.gameTint
                    Layout.preferredWidth: 30; Layout.preferredHeight: 30
                }
                Text {
                    text: root.gameTitle; color: root.gameTint
                    font.pixelSize: root.compact ? 22 : 29; font.bold: true
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                }
                Text {
                    text: root.tr("score") + " " + root.score
                    color: BrandTheme.colors.text; font.pixelSize: root.compact ? 16 : 20
                }
                Text {
                    text: root.tr("high") + " " + root.highScore()
                    color: BrandTheme.colors.muted; font.pixelSize: root.compact ? 16 : 20
                }
            }

            Rectangle {
                Layout.fillWidth: true; Layout.fillHeight: true; Layout.minimumHeight: 120
                radius: 12
                color: "#0E000000"
                border.color: "#27FFFFFF"
                clip: true
                Canvas {
                    id: gameCanvas
                    objectName: "gameCanvas"
                    anchors.fill: parent
                    anchors.margins: 4
                    antialiasing: true

                    onPaint: {
                        var ctx = getContext("2d")
                        var sx = width / 320
                        var sy = height / 170
                        function rx(v) { return v * sx }
                        function ry(v) { return v * sy }
                        function size(v) { return v * Math.min(sx, sy) }
                        ctx.reset()
                        ctx.clearRect(0, 0, width, height)
                        ctx.setLineDash([])
                        if (root.gameId === "asteroids" || root.gameId === "fly") {
                            for (var st = 0; st < root.stars.length; st++) {
                                var star = root.stars[st]
                                var alpha = root.gameId === "asteroids" ? 0.32 + Math.sin(star.phase) * 0.18 : 0.28
                                ctx.fillStyle = "rgba(255,255,255," + alpha + ")"
                                if (root.gameId === "fly") {
                                    ctx.fillRect(rx(star.x), ry(star.y), rx(8 + star.speed * 4), Math.max(1, ry(1)))
                                } else {
                                    ctx.fillRect(rx(star.x), ry(star.y), Math.max(1, rx(1.2)), Math.max(1, ry(1.2)))
                                }
                            }
                        }
                        if (root.gameId === "pong") {
                            ctx.strokeStyle = "rgba(255,255,255,0.22)"
                            ctx.setLineDash([rx(5), rx(7)])
                            ctx.beginPath()
                            ctx.moveTo(rx(160), ry(3))
                            ctx.lineTo(rx(160), ry(167))
                            ctx.stroke()
                            ctx.setLineDash([])
                            ctx.fillStyle = MoodTheme.moodColor(root.gameMood, "gradientEnd")
                            ctx.fillRect(rx(18 - (root.hitPulseTicks > 0 ? 2 : 0)), ry(root.paddleY - 17), rx(root.hitPulseTicks > 0 ? 12 : 8), ry(34))
                            if (root.wallPulseTicks > 0) {
                                ctx.strokeStyle = "rgba(255,255,255,0.28)"
                                ctx.lineWidth = 3
                                ctx.strokeRect(rx(4), ry(32), rx(312), ry(130))
                            }
                            if (root.playing) {
                                ctx.fillStyle = MoodTheme.moodColor(root.gameMood, "gradientMid")
                                ctx.beginPath()
                                ctx.arc(rx(root.ballX), ry(root.ballY), size(4), 0, Math.PI * 2)
                                ctx.fill()
                            }
                        } else if (root.gameId === "asteroids") {
                            ctx.fillStyle = root.gameTint
                            ctx.strokeStyle = MoodTheme.moodColor(root.gameMood, "gradientMid")
                            ctx.lineWidth = 2
                            ctx.beginPath()
                            ctx.moveTo(rx(root.shipX), ry(128))
                            ctx.lineTo(rx(root.shipX - 9), ry(141))
                            ctx.lineTo(rx(root.shipX - 7), ry(148))
                            ctx.lineTo(rx(root.shipX + 7), ry(148))
                            ctx.lineTo(rx(root.shipX + 9), ry(141))
                            ctx.closePath()
                            ctx.fill(); ctx.stroke()
                            ctx.strokeStyle = ["#ff6fb3", "#facc15", "#a78bfa"][root.asteroidShape]
                            ctx.beginPath()
                            if (root.asteroidShape === 0) {
                                ctx.arc(rx(root.asteroidX), ry(root.asteroidY), size(root.asteroidSize), 0, Math.PI * 2)
                            } else if (root.asteroidShape === 1) {
                                ctx.rect(rx(root.asteroidX - root.asteroidSize), ry(root.asteroidY - root.asteroidSize), rx(root.asteroidSize * 2), ry(root.asteroidSize * 2))
                            } else {
                                ctx.moveTo(rx(root.asteroidX), ry(root.asteroidY - root.asteroidSize))
                                ctx.lineTo(rx(root.asteroidX + root.asteroidSize), ry(root.asteroidY + root.asteroidSize))
                                ctx.lineTo(rx(root.asteroidX - root.asteroidSize), ry(root.asteroidY + root.asteroidSize * 0.8))
                                ctx.closePath()
                            }
                            ctx.stroke()
                            if (root.asteroidBulletActive) {
                                ctx.fillStyle = "#48d8ff"
                                ctx.fillRect(rx(root.shipX - 2), ry(root.asteroidBulletY), rx(4), ry(10))
                            }
                        } else if (root.gameId === "fly") {
                            var planeX = rx(46)
                            var planeY = ry(root.planeY)
                            ctx.fillStyle = MoodTheme.moodColor(root.gameMood, "gradientEnd")
                            ctx.beginPath()
                            ctx.moveTo(planeX - size(6), planeY - size(13))
                            ctx.lineTo(planeX + size(10), planeY)
                            ctx.lineTo(planeX - size(6), planeY + size(13))
                            ctx.lineTo(planeX - size(12), planeY)
                            ctx.closePath(); ctx.fill()
                            ctx.fillStyle = root.gameTint
                            ctx.beginPath()
                            ctx.moveTo(planeX + size(17), planeY)
                            ctx.lineTo(planeX + size(2), planeY + size(4))
                            ctx.lineTo(planeX - size(17), planeY + size(4))
                            ctx.lineTo(planeX - size(17), planeY - size(4))
                            ctx.lineTo(planeX + size(2), planeY - size(4))
                            ctx.closePath(); ctx.fill()
                            ctx.fillStyle = root.obstacleColor
                            ctx.beginPath()
                            if (root.obstacleShape === 0) {
                                ctx.fillRect(rx(root.obstacleX - 8), ry(root.obstacleY - 18), rx(16), ry(36))
                            } else if (root.obstacleShape === 1) {
                                ctx.arc(rx(root.obstacleX), ry(root.obstacleY), size(13), 0, Math.PI * 2)
                                ctx.fill()
                            } else if (root.obstacleShape === 2) {
                                ctx.moveTo(rx(root.obstacleX), ry(root.obstacleY - 18))
                                ctx.lineTo(rx(root.obstacleX + 16), ry(root.obstacleY))
                                ctx.lineTo(rx(root.obstacleX), ry(root.obstacleY + 18))
                                ctx.lineTo(rx(root.obstacleX - 16), ry(root.obstacleY))
                                ctx.closePath()
                                ctx.fill()
                            } else {
                                ctx.fillRect(rx(root.obstacleX - 14), ry(root.obstacleY - 8), rx(28), ry(16))
                            }
                            if (root.flyShotActive) {
                                ctx.fillStyle = "#d9fbff"
                                ctx.fillRect(rx(root.flyShotX), ry(root.planeY - 2), rx(14), ry(4))
                            }
                        } else {
                            ctx.fillStyle = "rgba(255,255,255,0.82)"
                            for (var i = 0; i < root.pellets.length; i++) {
                                var pellet = root.pellets[i]
                                var isPowerPellet = root.powerPellets.indexOf(pellet) >= 0
                                ctx.beginPath()
                                ctx.arc(
                                    rx(root.pacmanPelletX(pellet)),
                                    ry(root.pacmanPelletY(pellet)),
                                    isPowerPellet ? size(5) : size(2),
                                    0,
                                    Math.PI * 2
                                )
                                ctx.fill()
                            }
                            var pacRadius = size(10)
                            var mouthCenter = root.pacmanDX < 0 ? Math.PI
                                : root.pacmanDY < 0 ? Math.PI * 1.5
                                : root.pacmanDY > 0 ? Math.PI / 2
                                : 0
                            var mouthOpen = Math.PI / 5
                            ctx.fillStyle = root.gameTint
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
                            ctx.fillStyle = "#111827"
                            var eyeX = root.pacmanX + (root.pacmanDX !== 0 ? root.pacmanDX * 3 : 2)
                            var eyeY = root.pacmanY + (root.pacmanDY !== 0 ? root.pacmanDY * 3 : -4)
                            ctx.beginPath()
                            ctx.arc(rx(eyeX), ry(eyeY), size(1.8), 0, Math.PI * 2)
                            ctx.fill()
                            if (root.deathTicks > 0) {
                                ctx.strokeStyle = "#fff7ad"
                                ctx.lineWidth = 3
                                ctx.beginPath()
                                ctx.arc(rx(root.pacmanX), ry(root.pacmanY), Math.max(rx(16 + (34 - root.deathTicks) * 0.7), ry(16)), 0, Math.PI * 2)
                                ctx.stroke()
                            }
                            var ghostBlink = root.ghostVulnerableTicks > 0 && Math.floor(root.ghostVulnerableTicks / 12) % 2 === 0
                            ctx.fillStyle = root.ghostVulnerableTicks > 0 ? (ghostBlink ? "#e0f2fe" : "#3b82f6") : "#ff6fb3"
                            ctx.beginPath()
                            ctx.arc(rx(root.ghostX), ry(root.ghostY) - size(2), size(9), Math.PI, 0)
                            ctx.lineTo(rx(root.ghostX + 9), ry(root.ghostY) + size(9))
                            ctx.lineTo(rx(root.ghostX + 4), ry(root.ghostY) + size(5))
                            ctx.lineTo(rx(root.ghostX), ry(root.ghostY) + size(9))
                            ctx.lineTo(rx(root.ghostX - 4), ry(root.ghostY) + size(5))
                            ctx.lineTo(rx(root.ghostX - 9), ry(root.ghostY) + size(9))
                            ctx.closePath()
                            ctx.fill()
                            ctx.fillStyle = BrandTheme.colors.text
                            ctx.beginPath()
                            ctx.arc(rx(root.ghostX - 4), ry(root.ghostY) - size(2), size(2.6), 0, Math.PI * 2)
                            ctx.arc(rx(root.ghostX + 4), ry(root.ghostY) - size(2), size(2.6), 0, Math.PI * 2)
                            ctx.fill()
                            ctx.fillStyle = "#1d2bff"
                            ctx.beginPath()
                            ctx.arc(rx(root.ghostX - 3), ry(root.ghostY) - size(2), size(1.2), 0, Math.PI * 2)
                            ctx.arc(rx(root.ghostX + 5), ry(root.ghostY) - size(2), size(1.2), 0, Math.PI * 2)
                            ctx.fill()
                        }

                        if (root.flash) {
                            ctx.strokeStyle = "#ff5b5b"
                            ctx.lineWidth = 5
                            ctx.strokeRect(4, 4, width - 8, height - 8)
                        }
                        for (var ex = 0; ex < root.explosions.length; ex++) {
                            var boom = root.explosions[ex]
                            var radius = 4 + boom.age * 1.5
                            ctx.strokeStyle = boom.tint
                            ctx.globalAlpha = Math.max(0, 1 - boom.age / 18)
                            ctx.lineWidth = 3
                            ctx.beginPath()
                            ctx.arc(rx(boom.x), ry(boom.y), size(radius), 0, Math.PI * 2)
                            ctx.stroke()
                            ctx.globalAlpha = 1
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        onPressed: function(mouse) { root.handleTouch(mouse.x, mouse.y) }
                        onPositionChanged: function(mouse) { if (pressed) root.handleTouch(mouse.x, mouse.y) }
                        onReleased: root.fire()
                    }
                }

                GlassButton {
                    anchors.centerIn: parent
                    visible: !root.playing
                    text: root.tr("tap_to_play")
                    font.pixelSize: 22
                    onClicked: root.startGame()
                }
            }

            GameDirectionPad {
                objectName: "gameDirectionPad"
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: root.compact ? 138 : 238
                Layout.preferredHeight: Layout.preferredWidth
                horizontal: root.horizontalControls
                vertical: root.verticalControls
                canFire: root.fireControl
                accent: root.gameTint
                translate: root.tr
                onDirection: function(name) { root.useDirection(name) }
                onFire: root.fire()
            }

            Text {
                text: root.gameId === "pong" ? root.tr("game_help_pong")
                    : root.gameId === "asteroids" ? root.tr("game_help_asteroids")
                    : root.gameId === "fly" ? root.tr("game_help_fly")
                    : root.tr("game_help_pacman")
                color: BrandTheme.colors.muted
                font.pixelSize: root.compact ? 15 : 20
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
        }
    }

    Component.onCompleted: resetGame()
}
