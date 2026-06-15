from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from importlib.resources import files


def test_qml_files_are_packaged() -> None:
    qml_root = files("djconnect_pi.qml")

    assert qml_root.joinpath("Main.qml").is_file()
    assert qml_root.joinpath("ControlButton.qml").is_file()
    assert qml_root.joinpath("TogglePill.qml").is_file()
    assert qml_root.joinpath("GamesPanel.qml").is_file()
    assert qml_root.joinpath("app-icon.png").is_file()


def test_qml_has_blocking_pairing_and_splash_views() -> None:
    main_qml = files("djconnect_pi.qml").joinpath("Main.qml").read_text(encoding="utf-8")

    assert "id: pairingPanel" in main_qml
    assert "id: pairingSuccessPanel" in main_qml
    assert "id: splashPanel" in main_qml
    assert 'source: "app-icon.png"' in main_qml
    assert 'text: "v" + djconnect.version' in main_qml
    assert "!djconnect.paired && !djconnect.demoMode" in main_qml
    assert 'djconnect.t("client_api_url")' in main_qml
    assert "djconnect.pairingCode" in main_qml
    assert "blockingPairCodeField" not in main_qml
    assert "djconnect.pair(djconnect.pairingCode)" not in main_qml
    assert 'djconnect.t("waiting_for_ha")' in main_qml
    assert 'djconnect.t("start_demo_mode")' in main_qml
    assert "djconnect.pairingSuccessVisible" in main_qml
    assert 'djconnect.t("pairing_success_title")' in main_qml
    assert "djconnect.startAfterPairing()" in main_qml
    assert 'djconnect.t("startup_message")' in main_qml


def test_qml_has_touch_games_panel() -> None:
    qml_root = files("djconnect_pi.qml")
    main_qml = qml_root.joinpath("Main.qml").read_text(encoding="utf-8")
    games_qml = qml_root.joinpath("GamesPanel.qml").read_text(encoding="utf-8")

    assert "GamesPanel" in main_qml
    assert 'djconnect.t("games")' in main_qml
    assert 'id: "pong"' in games_qml
    assert 'id: "asteroids"' in games_qml
    assert 'id: "fly"' in games_qml
    assert 'id: "pacman"' in games_qml
    assert 'titleKey: "game_pong"' in games_qml
    assert "property string gameTitle: djconnect.t(games[gameIndex].titleKey)" in games_qml
    assert "djconnect.t(modelData.titleKey)" in games_qml
    assert "MouseArea" in games_qml
    assert "preventStealing: true" in games_qml
    assert "propagateComposedEvents: false" in games_qml
    assert "onClicked: function(mouse)" in games_qml
    assert "handleTouch" in games_qml
    assert "onPressed: function(mouse) { root.handleTouch(mouse.x, mouse.y) }" in games_qml
    assert "mouthOpen" in games_qml
    assert "ghostX - 4" in games_qml
    assert "property int powerPellet" in games_qml
    assert "property int ghostVulnerableTicks" in games_qml
    assert "ghostVulnerableTicks = 210" in games_qml
    assert "for (var i = 0; i < 32; i++) pellets.push(i)" in games_qml
    assert "powerPellet = 31" in games_qml
    assert "setScore(score + 5)" in games_qml
    assert 'root.ghostVulnerableTicks > 0 ? (ghostBlink ? "#e0f2fe" : "#3b82f6")' in games_qml


def test_qml_has_touch_readable_glass_controls_and_scrollable_settings() -> None:
    qml_root = files("djconnect_pi.qml")
    main_qml = qml_root.joinpath("Main.qml").read_text(encoding="utf-8")
    games_qml = qml_root.joinpath("GamesPanel.qml").read_text(encoding="utf-8")

    assert "component PurpleButton" in main_qml
    assert "component DangerButton" in main_qml
    assert "component ModalBlocker" in main_qml
    assert "component PlaybackButton" in main_qml
    assert "component IconButton" in main_qml
    assert "component MediaPlayButton" in main_qml
    assert "component MediaListPanel" in main_qml
    assert "component GlassButton" in games_qml
    assert "#3324145f" in main_qml
    assert "#3324145f" in games_qml
    assert 'color: "#ffffff"' in main_qml
    assert "id: settingsPanel" in main_qml
    assert "id: settingsScroll" in main_qml
    assert "ScrollView" in main_qml
    assert "ScrollBar.horizontal.policy: ScrollBar.AlwaysOff" in main_qml
    assert "contentWidth: availableWidth" in main_qml
    assert 'color: "#070b16"' in main_qml
    assert "font.pixelSize: 24" in main_qml
    assert "root.brightnessOverlayOpacity" in main_qml
    assert "z: 200" in main_qml
    assert 'djconnect.t("about")' in main_qml
    assert "aboutScroll.availableWidth" in main_qml
    assert 'text: "https://djconnect.dev"' in main_qml
    assert 'djconnect.t("reset_pairing_confirm_title")' in main_qml
    assert 'djconnect.t("reset_pairing_confirm_message")' in main_qml
    assert 'djconnect.t("cancel")' in main_qml
    assert "root.resetPairingConfirmOpen = true" in main_qml
    assert "root.rebootConfirmOpen = true" in main_qml
    assert 'djconnect.t("reboot_confirm_title")' in main_qml
    assert 'djconnect.t("reboot_confirm_message")' in main_qml
    assert 'text: djconnect.t("no_voice")' not in main_qml
    assert "placeholderText: djconnect.t(\"ha_url\")" not in main_qml
    assert "ModalBlocker {}" in main_qml
    assert "onClicked: function(mouse)" in main_qml
    assert "onWheel: function(wheel)" in main_qml
    assert 'djconnect.t("queue")' in main_qml
    assert 'djconnect.t("playlists")' in main_qml
    assert "djconnect.queueItems" in main_qml
    assert "djconnect.playlistItems" in main_qml
    assert 'emptyText: djconnect.t("empty_queue")' in main_qml
    assert 'emptyText: djconnect.t("empty_playlists")' in main_qml
    assert "visible: panel.items.length === 0" in main_qml
    assert "djconnect.loadQueue()" in main_qml
    assert "djconnect.loadPlaylists()" in main_qml
    assert "onRefreshRequested: djconnect.loadQueue()" in main_qml
    assert "onRefreshRequested: djconnect.loadPlaylists()" in main_qml
    assert "djconnect.manualRefresh()" in main_qml
    assert main_qml.count("Layout.preferredWidth: 142") >= 2
    assert main_qml.count("Layout.preferredHeight: 48") >= 2
    assert "djconnect.outputDevices" in main_qml
    assert "property var deviceChoices" in main_qml
    assert "djconnect.setOutputDevice" in main_qml
    assert 'text: "🔊"' not in main_qml
    assert "djconnect.cachedImageUrl(modelData.imageUrl)" not in main_qml
    assert "source: modelData.imageUrl && modelData.imageUrl.length > 0 ? modelData.imageUrl : \"\"" in main_qml
    assert "height: 92" not in main_qml
    assert "color: \"#990b1012\"" not in main_qml
    assert "Layout.preferredHeight: 86" in main_qml
    assert "id: mediaArt" in main_qml
    assert "id: mediaPlay" in main_qml
    assert "anchors.left: mediaArt.right" in main_qml
    assert "anchors.right: mediaPlay.left" in main_qml
    assert "anchors.right: parent.right" in main_qml
    assert "MediaPlayButton {" in main_qml
    assert "djconnect.trackProgress" in main_qml
    assert "djconnect.progressLabel" in main_qml
    assert 'iconName: djconnect.playing ? "pause" : "play"' in main_qml
    assert 'iconName: "previous"' in main_qml
    assert 'iconName: "next"' in main_qml
    assert 'iconName: "shuffle"' in main_qml
    assert "repeatOne" in main_qml
    assert "repeatOff" in main_qml
    assert "logsArea.cursorPosition = logsArea.length" in main_qml
    assert "djconnect.copyLogs()" in main_qml
    assert "djconnect.clearLogs()" in main_qml
    assert "pairCodeField" not in main_qml
    assert "djconnect.pair(pairCodeField.text)" not in main_qml
    assert 'djconnect.t("pairing_blocked")' not in main_qml
    assert 'djconnect.t("dismiss")' not in main_qml
    assert 'text: "DJConnect Pi"' not in main_qml
    assert 'text: "DJ"' not in main_qml
    assert "djconnect.quitApp()" not in main_qml


def test_qml_has_bottom_navigation_bar() -> None:
    main_qml = files("djconnect_pi.qml").joinpath("Main.qml").read_text(encoding="utf-8")

    assert "id: bottomNav" in main_qml
    assert "component NavButton" in main_qml
    assert "height: 104" in main_qml
    assert "border.width: navControl.checked ? 3 : 1" in main_qml
    assert "visible: navControl.checked" in main_qml
    assert 'iconSymbol: "▶"' in main_qml
    assert 'iconSymbol: "≡"' in main_qml
    assert 'iconSymbol: "▦"' in main_qml
    assert 'iconSymbol: "◆"' in main_qml
    assert 'iconSymbol: "⚙"' in main_qml
    assert 'djconnect.t("now_playing")' in main_qml
    assert 'djconnect.t("games")' in main_qml
    assert 'djconnect.t("setup")' in main_qml
    assert main_qml.index('text: djconnect.t("playlists")') < main_qml.index('text: djconnect.t("games")')
    assert 'root.activeScreen = "now"' in main_qml
    assert 'root.activeScreen = "games"' in main_qml
    assert 'root.activeScreen = "settings"' in main_qml


def test_qml_stop_demo_button_returns_to_pairing_flow() -> None:
    main_qml = files("djconnect_pi.qml").joinpath("Main.qml").read_text(encoding="utf-8")

    assert 'text: djconnect.demoMode ? djconnect.t("exit_demo") : djconnect.t("demo_mode")' in main_qml
    assert "djconnect.exitDemoMode()" in main_qml
    assert 'root.activeScreen = "now"' in main_qml


def test_qml_screen_blanking_wakes_on_tap() -> None:
    main_qml = files("djconnect_pi.qml").joinpath("Main.qml").read_text(encoding="utf-8")

    assert "property bool forceScreenAwake: false" in main_qml
    assert "property bool screenBlanked: djconnect.screenTimeoutSeconds > 0 && !idleTimer.running && !root.forceScreenAwake" in main_qml
    assert "onTapped: root.wakeDisplay()" in main_qml
    assert "id: forcedWakeTimer" in main_qml
    assert "interval: 10000" in main_qml
    assert "function onScreenshotRequested()" in main_qml
    assert "function wakeDisplay()" in main_qml
    assert "root.splashVisible = true" in main_qml
    assert "splashTimer.restart()" in main_qml
    assert "root.grabToImage" in main_qml
    assert "result.saveToFile(djconnect.screenshotFile)" in main_qml
    assert "function onWakeScreenRequested()" in main_qml
    assert "forcedWakeTimer.restart()" in main_qml
    assert "opacity: root.screenBlanked ? 1 : root.brightnessOverlayOpacity" in main_qml


def test_qml_has_backend_toast_overlay() -> None:
    main_qml = files("djconnect_pi.qml").joinpath("Main.qml").read_text(encoding="utf-8")

    assert "id: toast" in main_qml
    assert "djconnect.toastVisible" in main_qml
    assert "djconnect.toastText" in main_qml
    assert "Behavior on opacity" in main_qml


def test_qml_has_blocking_version_mismatch_view() -> None:
    main_qml = files("djconnect_pi.qml").joinpath("Main.qml").read_text(encoding="utf-8")

    assert "id: versionMismatchPanel" in main_qml
    assert "djconnect.versionMismatchVisible" in main_qml
    assert "djconnect.versionMismatchText" in main_qml
    assert 'djconnect.t("update_trying")' in main_qml


def test_qml_uses_dark_djconnect_gradient_theme() -> None:
    qml_root = files("djconnect_pi.qml")
    main_qml = qml_root.joinpath("Main.qml").read_text(encoding="utf-8")
    games_qml = qml_root.joinpath("GamesPanel.qml").read_text(encoding="utf-8")

    for text in (main_qml, games_qml):
        assert "Gradient" in text
        assert "#2f8cff" in text
        assert "#8b5cf6" in text
        assert "#070b16" in text
    assert "id: splashPanel" in main_qml
    assert "#24105c" in main_qml


def test_qml_offscreen_smoke_loads() -> None:
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    tmpdir = tempfile.gettempdir()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "djconnect_pi.app",
            "--windowed",
            "--exit-after-ms",
            "250",
            "--config",
            os.path.join(tmpdir, "djconnect-pi-qml-test.json"),
            "--log-file",
            os.path.join(tmpdir, "djconnect-pi-qml-test.log"),
        ],
        env=env,
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )

    assert result.returncode == 0
    assert "Error:" not in result.stderr
