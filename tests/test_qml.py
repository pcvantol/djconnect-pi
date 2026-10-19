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
    assert qml_root.joinpath("MoodTheme.js").is_file()
    assert qml_root.joinpath("app-icon.png").is_file()


def test_qml_has_blocking_pairing_and_splash_views() -> None:
    main_qml = files("djconnect_pi.qml").joinpath("Main.qml").read_text(encoding="utf-8")

    assert "id: pairingPanel" in main_qml
    assert "id: pairingSuccessPanel" in main_qml
    assert 'id: pairingPanel\n        anchors.fill: parent\n        color: BrandTheme.colors.background' in main_qml
    assert 'id: pairingSuccessPanel\n        anchors.fill: parent\n        color: BrandTheme.colors.background' in main_qml
    assert "id: splashPanel" in main_qml
    assert "BrandLockup {" in main_qml
    assert "component AppBanner" in main_qml
    assert 'radius: root.wallProfile ? 32 : 24\n        color: root.liquidGlassEnabled ? BrandTheme.alpha(BrandTheme.colors.surface, "8a") : BrandTheme.colors.background' in main_qml
    assert 'GradientStop { position: 0.72; color: root.liquidGlassEnabled ? "#70" + root.moodColor("surface").slice(1) : root.moodColor("surface") }' in main_qml
    assert 'detailText: "v" + djconnect.version' in main_qml
    assert "!djconnect.paired && !djconnect.demoMode" in main_qml
    assert "property int trVersion: djconnect.translationVersion" in main_qml
    assert "function tr(key)" in main_qml
    assert 'root.tr("client_api_url")' in main_qml
    assert "Client API URL" not in main_qml
    assert "component LoadingSpinner" in main_qml
    assert "RotationAnimation on rotation" in main_qml
    assert "LoadingSpinner {\n                        running: pairingPanel.visible" in main_qml
    pairing_panel = main_qml[main_qml.index("id: pairingPanel") : main_qml.index("id: pairingSuccessPanel")]
    assert pairing_panel.index('root.tr("home_assistant")') < pairing_panel.index('root.tr("pairing_code")')
    assert pairing_panel.index('root.tr("pairing_code")') < pairing_panel.index('root.tr("client_api_url")')
    assert "djconnect.pairingCode" in main_qml
    assert "blockingPairCodeField" not in main_qml
    assert "djconnect.pair(djconnect.pairingCode)" not in main_qml
    assert 'root.tr("waiting_for_ha")' in main_qml
    assert 'root.tr("start_demo_mode")' in main_qml
    assert "id: startDemoButton" in main_qml
    assert "ctx.arc(width / 2, height / 2, s * 0.38, 0, Math.PI * 2)" in main_qml
    assert "ctx.lineTo(width * 0.68, height * 0.5)" in main_qml
    assert "djconnect.pairingSuccessVisible" in main_qml
    assert 'root.tr("pairing_success_title")' in main_qml
    assert "djconnect.startAfterPairing()" in main_qml
    assert 'root.tr("startup_message")' in main_qml


def test_qml_has_touch_games_panel() -> None:
    qml_root = files("djconnect_pi.qml")
    main_qml = qml_root.joinpath("Main.qml").read_text(encoding="utf-8")
    games_qml = qml_root.joinpath("GamesPanel.qml").read_text(encoding="utf-8")

    assert "GamesPanel" in main_qml
    assert 'root.tr("games")' in main_qml
    assert 'id: "pong"' in games_qml
    assert 'id: "asteroids"' in games_qml
    assert 'id: "fly"' in games_qml
    assert 'id: "pacman"' in games_qml
    assert 'titleKey: "game_pong"' in games_qml
    assert "property int trVersion: djconnect.translationVersion" in games_qml
    assert "function tr(key)" in games_qml
    assert "property string gameTitle: root.tr(games[gameIndex].titleKey)" in games_qml
    assert "id: gameSelector" in games_qml
    assert "id: gameSegment" in games_qml
    assert 'color: BrandTheme.alpha(BrandTheme.colors.surface, "cc")' in games_qml
    assert 'GradientStop { position: 0.0; color: gameSegment.checked ? MoodTheme.color(djconnect.moodValue, "gradientStart") : "#00000000" }' in games_qml
    assert 'GradientStop { position: 1.0; color: gameSegment.checked ? MoodTheme.color(djconnect.moodValue, "gradientEnd") : "#00000000" }' in games_qml
    assert "root.tr(modelData.titleKey)" in games_qml
    assert "MouseArea" in games_qml
    assert "preventStealing: true" in games_qml
    assert "propagateComposedEvents: false" in games_qml
    assert "onClicked: function(mouse)" in games_qml
    assert "handleTouch" in games_qml
    assert "onPressed: function(mouse) { root.handleTouch(mouse.x, mouse.y) }" in games_qml
    assert "mouthOpen" in games_qml
    assert "ghostX - 4" in games_qml
    assert "property int pacmanPelletColumns: 10" in games_qml
    assert "property int pacmanPelletRows: 6" in games_qml
    assert "property real pacmanPelletSpacingX: 280 / (pacmanPelletColumns - 1)" in games_qml
    assert "property real pacmanPelletSpacingY: 28" in games_qml
    assert "property var powerPellets: [0, 9, 50, 59]" in games_qml
    assert "function pacmanPelletX(pellet)" in games_qml
    assert "function pacmanPelletY(pellet)" in games_qml
    assert "function pacmanMaxX()" in games_qml
    assert "Math.min(pacmanMaxX(), pacmanX + pacmanDX * 4)" in games_qml
    assert "property int ghostVulnerableTicks" in games_qml
    assert "ghostVulnerableTicks = 210" in games_qml
    assert "for (var i = 0; i < pacmanPelletColumns * pacmanPelletRows; i++) pellets.push(i)" in games_qml
    assert "powerPellets = [0, 9, 50, 59]" in games_qml
    assert "anchors.leftMargin: 12" in games_qml
    assert "anchors.topMargin: 34" in games_qml
    assert "anchors.rightMargin: 12" in games_qml
    assert "Layout.topMargin: 10" in games_qml
    assert "width: Math.min(parent.width, parent.height * 320 / 170)" in games_qml
    assert "height: width * 170 / 320" in games_qml
    assert "setScore(score + 5)" in games_qml
    assert 'root.ghostVulnerableTicks > 0 ? (ghostBlink ? "#e0f2fe" : "#3b82f6")' in games_qml
    assert "property int deathTicks" in games_qml
    assert "function playSfx(kind)" in games_qml
    assert "djconnect.playGameSound(kind)" in games_qml
    assert "Layout.preferredHeight: 58" in games_qml


def test_qml_has_touch_readable_glass_controls_and_scrollable_settings() -> None:
    qml_root = files("djconnect_pi.qml")
    main_qml = qml_root.joinpath("Main.qml").read_text(encoding="utf-8")
    games_qml = qml_root.joinpath("GamesPanel.qml").read_text(encoding="utf-8")

    assert "component PurpleButton" in main_qml
    assert "component DangerButton" in main_qml
    assert "component ModalBlocker" in main_qml
    assert "component AppBackground" in main_qml
    assert "component PlaybackButton" in main_qml
    assert "component IconButton" in main_qml
    assert "component MediaPlayButton" in main_qml
    assert "component MediaListPanel" in main_qml
    media_list_component = main_qml[main_qml.index("component MediaListPanel") : main_qml.index("Timer {\n        id: idleTimer")]
    assert "onVisibleChanged:" in media_list_component
    assert "Qt.callLater(function()" in media_list_component
    assert "mediaScroll.contentItem.contentY = 0" in media_list_component
    assert "component GlassButton" in games_qml
    assert 'import "MoodTheme.js" as MoodTheme' in main_qml
    assert 'import "MoodTheme.js" as MoodTheme' in games_qml
    assert 'root.moodColor("chip")' in main_qml
    assert 'MoodTheme.color(djconnect.moodValue, "gradientStart")' in games_qml
    assert 'MoodTheme.color(djconnect.moodValue, "gradientEnd")' in games_qml
    assert 'color: BrandTheme.colors.text' in main_qml
    assert "id: settingsPanel" in main_qml
    assert "id: settingsScroll" in main_qml
    assert "if (visible && settingsScroll.contentItem)" in main_qml
    assert "settingsScroll.contentItem.contentY = 0" in main_qml
    assert "ScrollView" in main_qml
    assert "ScrollBar.horizontal.policy: ScrollBar.AlwaysOff" in main_qml
    assert "contentWidth: availableWidth" in main_qml
    assert 'color: BrandTheme.colors.background' in main_qml
    assert "font.pixelSize: 24" in main_qml
    assert "root.brightnessOverlayOpacity" in main_qml
    assert "z: 200" in main_qml
    now_start = main_qml.index("id: nowPanel")
    now_block = main_qml[now_start : main_qml.index("id: controlPanel", now_start)]
    assert "text: djconnect.statusText" not in now_block
    assert "anchors.leftMargin: 16" in now_block
    assert "anchors.topMargin: 16" in now_block
    assert "anchors.rightMargin: 16" in now_block
    assert "Layout.preferredHeight: 48" in now_block
    assert 'anchors.bottomMargin: root.edge + 96' in now_block
    assert "width: Math.min(parent.width, parent.height)" in now_block
    assert "cache: true" in now_block
    assert 'root.tr("about")' in main_qml
    assert "aboutScroll.availableWidth" in main_qml
    about_block = main_qml[main_qml.index("visible: root.aboutOpen") : main_qml.index("id: djResponseOverlay")]
    assert "if (visible && aboutScroll.contentItem)" in about_block
    assert "aboutScroll.contentItem.contentY = 0" in about_block
    assert 'root.tr("privacy")' not in about_block
    assert 'root.tr("pi_no_spotify_credentials")' not in about_block
    assert 'root.tr("protocol_version")' not in about_block
    assert 'root.tr("target_player")' not in about_block
    assert 'root.tr("capabilities")' not in about_block
    assert 'root.tr("connection_type")' in main_qml
    assert "djconnect.connectionType" in main_qml
    assert 'text: "https://djconnect.dev"' in main_qml
    assert 'root.tr("reset_pairing_confirm_title")' in main_qml
    assert 'root.tr("reset_pairing_confirm_message")' in main_qml
    assert 'root.tr("cancel")' in main_qml
    assert "root.resetPairingConfirmOpen = true" in main_qml
    assert "root.rebootConfirmOpen = true" in main_qml
    assert 'root.tr("reboot_confirm_title")' in main_qml
    assert 'root.tr("reboot_confirm_message")' in main_qml
    assert "component WarningButton" in main_qml
    assert 'WarningButton {\n                text: root.tr("reboot_device")' in main_qml
    assert "root.shutdownConfirmOpen = true" in main_qml
    assert 'root.tr("shutdown_confirm_title")' in main_qml
    assert 'root.tr("shutdown_confirm_message")' in main_qml
    assert "djconnect.shutdownDevice()" in main_qml
    assert "djconnect.checkForUpdates()" in main_qml
    assert 'root.tr("check_updates")' in main_qml
    settings_start = main_qml.index("id: settingsPanel")
    settings_block = main_qml[settings_start : main_qml.index("MediaListPanel {", settings_start)]
    assert 'root.tr("device_id")' not in settings_block
    assert 'root.tr("ha_url")' not in settings_block
    assert 'root.tr("music_dna_settings_status")' in settings_block
    assert 'root.tr("music_dna_settings_enabled_description")' in settings_block
    assert 'root.tr("music_dna_settings_disabled_description")' in settings_block
    assert 'root.tr("music_dna_settings_profile")' in settings_block
    assert 'root.tr("music_dna_disable")' in settings_block
    assert 'root.tr("music_dna_enable")' in settings_block
    assert 'root.tr("music_dna_clear")' in settings_block
    assert "root.musicDnaDisableConfirmOpen = true" in settings_block
    assert "djconnect.setMusicDnaEnabled(true)" in settings_block
    assert "djconnect.setMusicDnaEnabled(false)" not in settings_block
    assert "id: musicDnaDisableConfirmPanel" in main_qml
    assert 'root.tr("music_dna_disable_confirm_title")' in main_qml
    assert 'root.tr("music_dna_disable_confirm_message")' in main_qml
    assert "visible: root.musicDnaDisableConfirmOpen" in main_qml
    assert "djconnect.setMusicDnaEnabled(false)" in main_qml
    assert "root.musicDnaClearConfirmOpen = true" in settings_block
    assert "djconnect.clearMusicDna()" not in settings_block
    assert "id: musicDnaClearConfirmPanel" in main_qml
    assert 'root.tr("music_dna_clear_confirm_title")' in main_qml
    assert 'root.tr("music_dna_clear_confirm_message")' in main_qml
    assert "visible: root.musicDnaClearConfirmOpen" in main_qml
    assert "djconnect.clearMusicDna()" in main_qml
    assert 'root.tr("view_logs")' not in settings_block
    assert 'root.tr("about")' not in settings_block
    assert "djconnect.showLogs()" not in settings_block
    assert "root.aboutOpen = true" not in settings_block
    assert 'root.tr("dj_announcement_settings_title")' in settings_block
    assert 'root.tr("dj_announcement_output")' in settings_block
    assert "djconnect.djAnnouncementSpeakerAvailable ? [\"text_only\", \"ha_speaker\"] : [\"text_only\"]" in settings_block
    assert "djconnect.setDjAnnouncementOutput(outputChoices[index])" in settings_block
    assert 'root.tr("dj_announcement_speaker_unavailable")' in settings_block
    assert "speaker_entity_id" not in settings_block
    assert 'root.tr("save")' not in main_qml
    assert 'text: root.tr("no_voice")' not in main_qml
    assert "placeholderText: root.tr(\"ha_url\")" not in main_qml
    assert "ModalBlocker {}" in main_qml
    assert "onClicked: function(mouse)" in main_qml
    assert "onWheel: function(wheel)" in main_qml
    assert 'root.tr("queue")' in main_qml
    assert 'root.tr("playlists")' in main_qml
    assert "djconnect.queueItems" in main_qml
    assert "djconnect.playlistItems" in main_qml
    assert 'emptyText: root.tr("empty_queue")' in main_qml
    assert 'emptyText: root.tr("empty_playlists")' in main_qml
    queue_panel = main_qml[main_qml.index('visible: root.activeScreen === "queue"') : main_qml.index('visible: root.activeScreen === "playlists"')]
    playlists_panel = main_qml[main_qml.index('visible: root.activeScreen === "playlists"') : main_qml.index("Rectangle {\n        id: morePanel")]
    assert 'playCommand: "play_context_at"' in queue_panel
    assert 'playCommand: "start_queue_item"' not in queue_panel
    assert 'playCommand: "start_playlist"' in playlists_panel
    assert "function itemPayload(item)" in main_qml
    assert "JSON.stringify" in main_qml
    assert "artist: item.artist || \"\"" in main_qml
    assert "album: item.album || \"\"" in main_qml
    assert "text: modelData.album || \"\"" in main_qml
    assert "djconnect.playMediaItem(panel.playCommand, panel.itemPayload(modelData))" in main_qml
    assert 'onClicked: root.activeScreen = "now"' not in main_qml[main_qml.index('visible: root.activeScreen === "queue"') : main_qml.index('visible: root.activeScreen === "playlists"')]
    assert "enabled: modelData.uri && modelData.uri.length > 0" in main_qml
    assert "visible: panel.items.length === 0" in main_qml
    assert "djconnect.loadQueue()" in main_qml
    assert "djconnect.loadPlaylists()" in main_qml
    assert "onRefreshRequested: djconnect.loadQueue()" in main_qml
    assert "onRefreshRequested: djconnect.loadPlaylists()" in main_qml
    assert "djconnect.manualRefresh()" in main_qml
    assert "component RefreshIconButton" in main_qml
    assert main_qml.count("RefreshIconButton {") >= 8
    assert main_qml.count('text: root.tr("refresh")') == 1
    assert main_qml.count("Layout.preferredHeight: 48") >= 2
    assert "anchors.topMargin: 16" in main_qml
    assert 'djconnect.haUrl.length ? djconnect.haUrl : "http://homeassistant.local:8123"' in main_qml
    assert "djconnect.outputDeviceChoices" in main_qml
    assert 'textRole: "name"' in main_qml
    assert "choiceName(modelData)" in main_qml
    assert "property var deviceChoices" in main_qml
    assert 'property string noOutputDeviceLabel: root.tr("none")' in main_qml
    assert "djconnect.setOutputDevice" in main_qml
    assert "djconnect.adjustVolume(-10)" in main_qml
    assert "djconnect.adjustVolume(10)" in main_qml
    assert 'text: "-"' in main_qml
    assert 'text: "+"' in main_qml
    assert "id: nowPanel" in main_qml
    assert 'visible: root.activeScreen === "now"' in main_qml
    assert "property bool moodPopoverOpen: false" in main_qml
    assert "id: nowMoodButton" in main_qml
    assert 'iconName: "mood"' in main_qml
    assert 'ToolTip.text: root.tr("mood_select")' in main_qml
    assert "id: moodPopover" in main_qml
    assert 'visible: root.activeScreen === "now" && root.moodPopoverOpen' in main_qml
    mood_popover = main_qml[main_qml.index("id: moodPopover") : main_qml.index("id: controlPanel")]
    assert 'border.color: root.moodColor("focus")' in mood_popover
    assert 'root.moodColor("bannerMid")' in mood_popover
    assert 'root.moodColor("surface")' in mood_popover
    assert 'root.moodColor("bannerEnd")' in mood_popover
    assert 'root.moodColor("chip")' in mood_popover
    assert 'root.moodColor("accent")' in mood_popover
    assert 'color: "#141326"' not in mood_popover
    assert 'border.color: "#6a5bd8"' not in mood_popover
    assert '"#24263f"' not in mood_popover
    assert '"#3d4268"' not in mood_popover
    assert "djconnect.setMoodValue(0)" in main_qml
    assert "djconnect.setMoodValue(35)" in main_qml
    assert "djconnect.setMoodValue(70)" in main_qml
    assert "djconnect.setMoodValue(100)" in main_qml
    assert "id: controlPanel" in main_qml
    assert 'visible: root.activeScreen === "control"' in main_qml
    assert 'root.tr("control")' in main_qml
    assert "id: controlOutputDeviceCombo" in main_qml
    assert "function selectedIndex()" in main_qml
    assert "currentIndex: selectedIndex()" in main_qml
    assert 'text: "🔊"' not in main_qml
    assert "wrapMode: TextEdit.NoWrap" in main_qml
    assert 'text: root.tr("log") + ": " + djconnect.logFile' in main_qml
    assert "djconnect.cachedImageUrl(modelData.imageUrl)" not in main_qml
    assert "source: modelData.imageUrl && modelData.imageUrl.length > 0 ? modelData.imageUrl : \"\"" in main_qml
    assert "sourceSize.width: 68" in main_qml
    assert "sourceSize.height: 68" in main_qml
    assert "sourceSize.width: width" in main_qml
    assert "sourceSize.height: height" in main_qml
    assert main_qml.count("cache: false") >= 1
    assert "height: 92" in main_qml
    assert "color: BrandTheme.alpha(BrandTheme.colors.surface, \"99\")" not in main_qml
    assert "Layout.preferredHeight: 178" in main_qml
    assert "Layout.preferredHeight: 126" in main_qml
    assert "Layout.preferredHeight: 76" in main_qml
    assert 'color: djconnect.paired ? (djconnect.backendAvailable ? BrandTheme.colors.success : BrandTheme.colors.danger) : BrandTheme.colors.warning' in main_qml
    assert "width: 14" in main_qml
    assert "height: 14" in main_qml
    assert "id: ambient" not in main_qml
    assert main_qml.count("AppBackground {}") >= 4
    assert "id: mediaArt" in main_qml
    assert "id: mediaText" in main_qml
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
    assert "to: 60" in main_qml
    assert "Math.round(Math.min(60, djconnect.volume) / 60 * 100) + \"%\"" in main_qml
    assert "property var timeoutChoices: [30, 60, 90, 120, 180, 240, 300, 600]" in main_qml
    assert "property var returnToNowChoices: [30, 60, 120, 0]" in main_qml
    assert 'text: root.tr("return_to_now")' in main_qml
    assert "id: returnToNowBox" in main_qml
    assert "displayText: root.returnToNowLabel(djconnect.returnToNowSeconds)" in main_qml
    assert "djconnect.setReturnToNowSeconds(root.returnToNowChoices[index])" in main_qml
    assert "logsArea.cursorPosition = 0" in main_qml
    assert "logsArea.cursorPosition = logsArea.length" not in main_qml
    assert "function lineNumbers(text)" in main_qml
    assert "id: logLineNumbers" in main_qml
    assert "text: root.lineNumbers(djconnect.logsText)" in main_qml
    assert 'color: BrandTheme.colors.disabledText' in main_qml
    assert "wrapMode: TextEdit.NoWrap" in main_qml
    assert "djconnect.copyLogs()" not in main_qml
    assert 'root.tr("copy_logs")' not in main_qml
    logs_start = main_qml.index("visible: djconnect.logsVisible")
    logs_block = main_qml[logs_start : main_qml.index("id: clearLogsConfirmPanel", logs_start)]
    assert "Layout.maximumHeight: 56" in logs_block
    assert "Layout.fillHeight: false" in logs_block
    assert "Layout.minimumHeight: 360" in logs_block
    assert "id: clearLogsButton" in logs_block
    assert 'iconName: "trash"' in logs_block
    assert 'ToolTip.text: root.tr("clear_logs")' in logs_block
    assert 'color: clearLogsButton.down ? BrandTheme.colors.dangerPressed : BrandTheme.colors.dangerSurface' in logs_block
    assert 'PurpleButton {\n                    text: root.tr("clear_logs")' not in logs_block
    assert 'iconName === "trash"' in files("djconnect_pi.qml").joinpath("FeatureIcon.qml").read_text(encoding="utf-8")
    assert "root.clearLogsConfirmOpen = true" in main_qml
    assert 'root.tr("clear_logs_confirm_title")' in main_qml
    assert 'root.tr("clear_logs_confirm_message")' in main_qml
    assert "djconnect.clearLogs()" in main_qml
    assert "pairCodeField" not in main_qml
    assert "djconnect.pair(pairCodeField.text)" not in main_qml
    assert 'root.tr("pairing_blocked")' not in main_qml
    assert 'root.tr("dismiss")' not in main_qml
    assert 'text: "DJConnect Pi"' not in main_qml
    assert 'text: "DJ"' not in main_qml
    assert "djconnect.quitApp()" not in main_qml


def test_qml_has_bottom_navigation_bar() -> None:
    main = files("djconnect_pi.qml").joinpath("Main.qml").read_text(encoding="utf-8")
    icons = files("djconnect_pi.qml").joinpath("FeatureIcon.qml").read_text(encoding="utf-8")
    nav = main[main.index("id: bottomNav"):main.index("id: pairingPanel")]
    more = main[main.index("id: morePanel"):main.index("id: trackInsightPanel")]
    assert "component MenuIcon: FeatureIcon" in main
    for icon in ("trackInsight", "discover", "heart"):
        assert f'iconName === "{icon}"' in icons
    # Portrait iPad has exactly five primary destinations; the same model serves both Pi targets.
    destinations = ["session", "now", "trackinsight", "discover", "more"]
    offsets = [nav.index(f'screen: "{key}"') for key in destinations]
    assert offsets == sorted(offsets)
    assert nav.count("screen:") == 5
    assert "root.activeScreen = modelData.screen" in nav
    assert "radius: height / 2" in nav
    assert "GridLayout" in more and "columns: 2" in more
    more_keys = ["ask_dj", "session_history", "music_dna", "queue", "playlists", "games", "setup", "about"]
    offsets = [more.index(f'root.tr("{key}")') for key in more_keys]
    assert offsets == sorted(offsets)
    # Existing Pi utilities remain reachable after the common Apple destinations.
    assert 'root.activeScreen = "control"' in more
    assert "djconnect.showLogs()" in more
    assert "djconnect.loadQueue()" in more and "djconnect.loadPlaylists()" in more
    assert "djconnect.loadAskDjHistory()" in more and "djconnect.djSession.loadHistory()" in more


def test_qml_ask_dj_screen_is_readonly_actions_without_free_input() -> None:
    main_qml = files("djconnect_pi.qml").joinpath("Main.qml").read_text(encoding="utf-8")
    ask_dj_block = main_qml[main_qml.index("id: askDjPanel") : main_qml.index("GamesPanel {")]

    assert 'visible: root.activeScreen === "askdj"' in ask_dj_block
    assert "component AskDjGradientButton" in main_qml
    action_button = main_qml[main_qml.index("component AskDjGradientButton"):main_qml.index("component MenuIcon")]
    assert "background: GlassSurface" in action_button
    assert "pressed: askDjButton.down" in action_button
    assert "focused: askDjButton.activeFocus" in action_button
    assert "djconnect.refreshAskDjHistory()" in ask_dj_block
    assert "id: askDjRefreshButton" in ask_dj_block
    assert "RefreshIconButton" in ask_dj_block
    assert "id: askDjClearButton" in ask_dj_block
    assert 'ToolTip.text: root.tr("ask_dj_clear_chat")' in ask_dj_block
    assert 'iconName: "trash"' in ask_dj_block
    assert "enabled: !djconnect.askDjBusy && djconnect.askDjMessages.length > 0" in ask_dj_block
    assert "root.askDjClearConfirmOpen = true" in ask_dj_block
    assert "id: askDjClearConfirmPanel" in main_qml
    assert "visible: root.askDjClearConfirmOpen" in main_qml
    assert 'root.tr("ask_dj_clear_confirm_title")' in main_qml
    assert 'root.tr("ask_dj_clear_confirm_message")' in main_qml
    assert "djconnect.clearAskDjHistory()" in main_qml
    assert "visible: djconnect.askDjBusy" in main_qml
    assert "enabled: !djconnect.askDjBusy" in main_qml
    assert "root.askDjClearConfirmOpen && djconnect.askDjMessages.length === 0" in main_qml
    assert 'root.tr("ask_dj_readonly_hint")' not in ask_dj_block
    assert "djconnect.sendAskDjAction(modelData.payload" in ask_dj_block
    assert "TextField" not in ask_dj_block
    assert 'root.tr("ask_dj_input_placeholder")' not in ask_dj_block
    assert 'root.tr("send")' not in ask_dj_block
    assert "djconnect.sendAskDjMessage" not in ask_dj_block
    assert "djconnect.clearAskDjHistory" not in ask_dj_block
    assert "component AskDjKeyButton" not in main_qml
    assert "id: askDjKeyboard" not in ask_dj_block
    assert "property bool askDjKeyboardOpen" not in main_qml
    assert "function insertAskDjKey" not in ask_dj_block
    assert "function deleteAskDjText" not in ask_dj_block
    assert 'root.tr("replay_audio")' not in ask_dj_block
    assert "Qt.openUrlExternally(modelData.audioUrl)" not in ask_dj_block
    assert "modelData.announcementDelivery" in ask_dj_block
    assert 'root.tr("dj_announcement_delivered_ha_speaker")' in ask_dj_block
    assert "id: askDjPollTimer" in main_qml
    assert 'running: root.activeScreen === "askdj" && djconnect.paired && !djconnect.demoMode' in main_qml
    assert "onTriggered: djconnect.pollAskDjHistory()" in main_qml
    assert "function scrollAskDjToTop()" in main_qml
    assert 'if (root.activeScreen === "askdj")' in main_qml
    assert "function onAskDjChanged()" in main_qml
    assert "askDjScroll.contentItem.contentY = 0" in ask_dj_block or "askDjScroll.contentItem.contentY = 0" in main_qml
    assert "modelData.displayTime || \"\"" in ask_dj_block
    assert "id: askDjActionButton" in ask_dj_block
    assert "modelData.actions || []" in ask_dj_block
    assert "modelData.isMedia" in ask_dj_block
    assert "modelData.isOutput" in ask_dj_block
    assert "modelData.items || []" in ask_dj_block
    assert "modelData.time ||" in ask_dj_block
    assert 'source: modelData.imageUrl && modelData.imageUrl.length > 0 ? modelData.imageUrl : ""' in ask_dj_block
    assert 'text: modelData.isOutput ? root.tr("activate") : (modelData.isMedia ? root.tr("play_now") : (modelData.title || root.tr("start")))' in ask_dj_block
    assert 'onClicked: djconnect.sendAskDjAction(modelData.payload || "{}")' in ask_dj_block
    assert "requestAskDjIdleSuggestion" not in ask_dj_block
    assert "playAskDjAction" not in ask_dj_block


def test_qml_ask_dj_track_insight_has_compact_readonly_rendering() -> None:
    main_qml = files("djconnect_pi.qml").joinpath("Main.qml").read_text(encoding="utf-8")
    ask_dj_block = main_qml[main_qml.index("id: askDjPanel") : main_qml.index("GamesPanel {")]

    assert "modelData.trackInsight && modelData.musicDnaMatch" in ask_dj_block
    assert 'root.tr("music_dna_match") + " " + (modelData.musicDnaMatch || "")' in ask_dj_block
    assert "modelData.trackInsight && modelData.items && modelData.items.length > 0" in ask_dj_block
    assert 'color: "#00000000"' in ask_dj_block
    assert "modelData.value || \"\"" in ask_dj_block
    assert "[modelData.source || \"\", modelData.confidence || \"\"].filter" in ask_dj_block
    assert "modelData.analysis.sections && modelData.analysis.sections.length > 0" in ask_dj_block
    assert "root.trackInsightLabel(modelData.title || modelData.kind || \"\")" in ask_dj_block
    assert "root.trackInsightLabel(modelData.title || modelData.id || modelData.kind || \"\")" in ask_dj_block
    assert "!modelData.trackInsight && modelData.items && modelData.items.length > 0" in ask_dj_block
    assert ask_dj_block.count('border.color: root.moodColor("focus")') >= 4
    assert 'border.color: systemBubble ? BrandTheme.alpha(BrandTheme.colors.border, "6a") : (userBubble ? "#a5b4fc" : root.moodColor("accent"))' not in ask_dj_block
    assert 'border.color: modelData.musicDna ? BrandTheme.alpha(BrandTheme.colors.border, "6a") : root.moodColor("accent")' not in ask_dj_block
    assert 'border.color: modelData.metadataContext ? BrandTheme.alpha(BrandTheme.colors.border, "6a") : ((modelData.source === "inferred"' not in ask_dj_block


def test_qml_now_playing_hides_favorite_and_track_insight_buttons() -> None:
    main_qml = files("djconnect_pi.qml").joinpath("Main.qml").read_text(encoding="utf-8")
    now_block = main_qml[main_qml.index("id: nowPanel") : main_qml.index("id: controlPanel")]

    assert 'root.tr("add_to_favorites")' not in now_block
    assert "djconnect.saveCurrentTrack()" not in now_block
    assert 'root.tr("track_insight")' not in now_block
    assert 'root.activeScreen = "trackinsight"' not in now_block
    assert "djconnect.openTrackInsight()" not in now_block
    assert "id: nowRefreshButton" in now_block
    assert "RefreshIconButton" in now_block
    assert "onClicked: djconnect.manualRefresh()" in now_block


def test_qml_control_screen_has_favorite_icon_between_shuffle_and_repeat() -> None:
    main_qml = files("djconnect_pi.qml").joinpath("Main.qml").read_text(encoding="utf-8")
    control_block = main_qml[main_qml.index("id: controlPanel") : main_qml.index("id: settingsPanel")]

    assert 'iconName: "shuffle"' in control_block
    assert 'iconName: djconnect.currentTrackFavorite ? "heartFilled" : "heart"' in control_block
    assert 'iconName: djconnect.repeat === "track" ? "repeatOne" : djconnect.repeat === "context" ? "repeat" : "repeatOff"' in control_block
    assert "enabled: djconnect.favoriteAvailable && !djconnect.favoriteBusy" in control_block
    assert "onClicked: djconnect.saveCurrentTrack()" in control_block
    assert control_block.index('iconName: "shuffle"') < control_block.index('iconName: djconnect.currentTrackFavorite ? "heartFilled" : "heart"')
    assert control_block.index('iconName: djconnect.currentTrackFavorite ? "heartFilled" : "heart"') < control_block.index('iconName: djconnect.repeat === "track"')
    assert 'control.iconName === "heart" || control.iconName === "heartFilled"' in main_qml


def test_qml_track_insight_panel_renders_contract_fields() -> None:
    main_qml = files("djconnect_pi.qml").joinpath("Main.qml").read_text(encoding="utf-8")
    panel = main_qml[main_qml.index("id: trackInsightPanel") : main_qml.index("id: musicDiscoveryPanel")]

    assert 'visible: root.activeScreen === "trackinsight"' in panel
    assert "property bool autoInsightRequested: false" in panel
    assert "onVisibleChanged:" in panel
    assert "visible && !autoInsightRequested && djconnect.playing" in panel
    assert "djconnect.openTrackInsight()" in panel
    assert "function trackInsightLabel(value)" in main_qml
    assert '"summary": "track_insight_summary"' in main_qml
    assert '"energy": "track_insight_energy"' in main_qml
    assert "root.trackInsightLabel(modelData.title || modelData.kind || \"\")" in panel
    assert "root.trackInsightLabel(modelData.title || modelData.kind || modelData.id || \"\")" in panel
    assert panel.count('color: "#00000000"') >= 3
    assert 'color: BrandTheme.colors.surface' not in panel
    assert "visible: !trackInsightScroll.visible" in panel
    assert "Layout.fillHeight: true" in panel
    assert "djconnect.refreshTrackInsight()" in panel
    assert 'root.tr("track_insight_empty")' in panel
    assert "djconnect.trackInsightError" in panel
    assert "djconnect.trackInsightTitle" in panel
    assert "djconnect.trackInsightArtist" in panel
    assert "djconnect.trackInsightAlbum" in panel
    assert "djconnect.trackInsightImageUrl" in panel
    assert "djconnect.trackInsightText" in panel
    assert "djconnect.trackInsightItems" in panel
    assert "djconnect.trackInsightSections" in panel
    assert "id: trackInsightVisualizer" in panel
    assert "djconnect.trackInsightVisualizer.available === true" in panel
    assert "property var visualizerData: djconnect.trackInsightVisualizer" in panel
    assert "Layout.preferredHeight: 164" in panel
    assert "id: trackInsightVisualizerCanvas" in panel
    assert 'running: trackInsightVisualizer.visible && root.activeScreen === "trackinsight"' in panel
    assert "interval: 180" in panel
    assert "data.bars || []" in panel
    assert "data.colors || []" in panel
    assert 'root.moodColor("gradientStart")' in panel
    assert "modelData.value || \"\"" in panel
    assert "modelData.details || []" in panel
    assert panel.count('border.color: root.moodColor("focus")') >= 3
    assert 'border.color: BrandTheme.colors.border' not in panel
    assert 'border.color: modelData.musicDna ? BrandTheme.alpha(BrandTheme.colors.border, "6a") : root.moodColor("accent")' not in panel
    assert 'border.color: modelData.metadataContext ? BrandTheme.alpha(BrandTheme.colors.border, "6a") : BrandTheme.colors.border' not in panel
    assert "bpm" not in panel.casefold()
    assert "key-signature" not in panel.casefold()


def test_qml_music_discovery_nav_and_panel() -> None:
    main_qml = files("djconnect_pi.qml").joinpath("Main.qml").read_text(encoding="utf-8")
    nav_block = main_qml[main_qml.index("id: bottomNav") : main_qml.index("id: pairingPanel")]
    discover_block = main_qml[main_qml.index("id: musicDiscoveryPanel") : main_qml.index("id: musicDnaPanel")]

    assert '{screen: "discover", key: "music_discovery", icon: "discover"}' in nav_block
    assert "root.activeScreen === modelData.screen" in nav_block
    assert "root.activeScreen = modelData.screen" in nav_block
    assert "djconnect.loadMusicDiscovery()" in main_qml
    assert 'root.tr("music_discovery_requires_music_dna")' in discover_block
    assert "djconnect.acceptMusicDiscoveryConsent()" in discover_block
    assert "djconnect.rejectMusicDiscoveryConsent()" in discover_block
    assert "anchors.topMargin: 10" in discover_block
    assert "id: discoveryRefreshButton" in discover_block
    assert "RefreshIconButton" in discover_block
    assert "enabled: !djconnect.musicDiscoveryBusy" in discover_block
    assert "djconnect.refreshMusicDiscovery()" in discover_block
    assert "id: discoveryMusicDnaDisabledColumn" in discover_block
    assert "visible: !djconnect.musicDnaEnabled && djconnect.musicDiscoveryItems.length === 0 && !djconnect.musicDiscoveryBusy && !djconnect.musicDiscoveryConsentRejected" in discover_block
    assert 'root.tr("music_dna_opt_in")' in discover_block
    assert 'text: root.tr("music_discovery_enable")' in discover_block
    assert "enabled: !djconnect.musicDnaBusy && !djconnect.musicDiscoveryBusy" in discover_block
    assert "djconnect.setMusicDnaEnabled(true)" in discover_block
    assert "columns: 1" in discover_block
    assert "columns: width >= 640 ? 2 : 1" not in discover_block
    assert "Layout.preferredHeight: djconnect.musicDiscoveryFeedbackSupported ? 226 : 178" in discover_block
    assert "Layout.preferredWidth: 132" in discover_block
    assert "visible: !discoveryScroll.visible" in discover_block
    assert "visible: djconnect.musicDiscoveryItems.length > 0" in discover_block
    assert "visible: djconnect.musicDnaEnabled && djconnect.musicDiscoveryItems.length === 0 && !djconnect.musicDiscoveryBusy && !djconnect.musicDiscoveryConsentRejected" in discover_block
    assert "Layout.fillHeight: true" in discover_block
    assert "id: discoveryReasonPanel" in discover_block
    assert "visible: root.discoveryReasonOpen" in discover_block
    assert "root.discoveryReasonTitle = modelData.title || root.tr(\"music_discovery_reason\")" in discover_block
    assert "root.discoveryReasonText = modelData.reason || \"\"" in discover_block
    assert "root.discoveryReasonOpen = true" in discover_block
    assert "root.discoveryReasonOpen = false" in discover_block
    assert "djconnect.playMusicDiscoveryItem(modelData.payload || \"{}\")" in discover_block
    assert discover_block.count("djconnect.playMusicDiscoveryItem(modelData.payload || \"{}\")") == 1
    assert "modelData.sectionTitle" in discover_block
    assert "modelData.qualityBand" in discover_block
    assert "modelData.qualityScore" in discover_block
    assert "djconnect.musicDiscoveryFeedbackSupported" in discover_block
    assert 'djconnect.sendMusicDiscoveryFeedback(modelData.payload || "{}", "not_for_me")' in discover_block
    assert 'djconnect.sendMusicDiscoveryFeedback(modelData.payload || "{}", "less_like_this")' in discover_block
    assert 'djconnect.sendMusicDiscoveryFeedback(modelData.payload || "{}", "hide_artist")' in discover_block
    assert "modelData.relevance" not in discover_block
    assert "visible: modelData.playable" in discover_block
    assert "if (modelData.playable)" not in discover_block
    assert "onClicked: function(mouse) { mouse.accepted = true }" in discover_block
    assert "visible: modelData.hasReason" in discover_block
    assert "djconnect.showToastForContext(modelData.reason || \"\", \"discover\")" not in discover_block


def test_qml_music_dna_enable_is_available_in_disabled_screen() -> None:
    main_qml = files("djconnect_pi.qml").joinpath("Main.qml").read_text(encoding="utf-8")
    settings_block = main_qml[main_qml.index("id: settingsPanel") : main_qml.index("MediaListPanel {")]
    music_dna_block = main_qml[main_qml.index("id: musicDnaPanel") : main_qml.index("id: askDjPanel")]

    assert "root.musicDnaDisableConfirmOpen = true" in settings_block
    assert "djconnect.setMusicDnaEnabled(true)" in settings_block
    assert "root.musicDnaClearConfirmOpen = true" in settings_block
    assert "djconnect.clearMusicDna()" not in settings_block
    assert "djconnect.setMusicDnaEnabled(!djconnect.musicDnaEnabled)" not in music_dna_block
    assert "djconnect.clearMusicDna()" not in music_dna_block
    assert "djconnect.setMusicDnaEnabled(true)" in music_dna_block
    assert "djconnect.refreshMusicDna()" in music_dna_block
    assert "visible: !djconnect.musicDnaEnabled" in music_dna_block
    assert 'text: root.tr("music_dna_disabled")' in music_dna_block
    assert 'text: root.tr("music_dna_enable")' in music_dna_block
    assert "enabled: !djconnect.musicDnaBusy" in music_dna_block
    assert "Layout.preferredHeight: 56" in music_dna_block
    assert 'root.tr("music_dna_enabled")' not in music_dna_block
    assert "id: musicDnaRefreshButton" in music_dna_block
    assert "RefreshIconButton" in music_dna_block


def test_qml_stop_demo_button_returns_to_pairing_flow() -> None:
    main_qml = files("djconnect_pi.qml").joinpath("Main.qml").read_text(encoding="utf-8")

    assert 'text: djconnect.demoMode ? root.tr("exit_demo") : root.tr("demo_mode")' in main_qml
    assert "djconnect.exitDemoMode()" in main_qml
    assert 'root.activeScreen = "now"' in main_qml


def test_qml_screen_blanking_wakes_on_tap() -> None:
    main_qml = files("djconnect_pi.qml").joinpath("Main.qml").read_text(encoding="utf-8")

    assert "property bool forceScreenAwake: false" in main_qml
    assert "property bool forceBrightnessFull: false" in main_qml
    assert "property bool suppressNextNowPanelTap: false" in main_qml
    assert "property double lastWakeDisplayAt: 0" in main_qml
    assert "property int wakeDisplayDebounceMs: 800" in main_qml
    assert "property bool screenBlanked: djconnect.screenTimeoutSeconds > 0 && !idleTimer.running && !root.forceScreenAwake" in main_qml
    assert "root.screenBlanked || root.forceBrightnessFull" in main_qml
    assert "onTapped: root.wakeDisplay()" in main_qml
    assert "id: forcedWakeTimer" in main_qml
    assert "id: returnToNowTimer" in main_qml
    assert "interval: Math.max(1000, djconnect.returnToNowSeconds * 1000)" in main_qml
    assert "running: djconnect.returnToNowSeconds > 0" in main_qml
    assert "interval: 10000" in main_qml
    assert "root.activeScreen = \"now\"" in main_qml
    assert "function temporaryWake(seconds, navigateNow)" in main_qml
    temporary_wake = main_qml[main_qml.index("function temporaryWake(seconds, navigateNow)") : main_qml.index("component PurpleButton")]
    assert "var wasBlanked = root.screenBlanked" in temporary_wake
    assert "if (navigateNow && wasBlanked && djconnect.returnToNowSeconds > 0)" in temporary_wake
    assert "function onTemporaryWakeRequested(seconds, navigateNow)" in main_qml
    assert "id: djResponseOverlay" in main_qml
    assert "id: djResponseTimer" in main_qml
    assert "djconnect.djResponseVisible" in main_qml
    assert "djconnect.djResponseText" in main_qml
    assert "djconnect.clearDjResponse()" in main_qml
    assert "BrandLockup {" in main_qml
    assert "id: albumQuickPlay" not in main_qml
    assert "id: albumQuickPlayIcon" not in main_qml
    assert "function onScreenshotRequested()" in main_qml
    assert "function onDebugScreenRequested(screen)" in main_qml
    assert 'screen === "queue"' in main_qml
    assert 'screen === "playlists"' in main_qml
    assert 'screen === "logs"' in main_qml
    assert 'screen === "about"' in main_qml
    assert "function wakeDisplay()" in main_qml
    wake_display = main_qml[main_qml.index("function wakeDisplay()") : main_qml.index("onActiveScreenChanged: {")]
    assert "var now = Date.now()" in wake_display
    assert "now - root.lastWakeDisplayAt < root.wakeDisplayDebounceMs" in wake_display
    assert "root.lastWakeDisplayAt = now" in wake_display
    assert "djconnect.wakeDisplay()" in wake_display
    assert "root.recordActivity()" in wake_display
    record_activity = main_qml[main_qml.index("function recordActivity()") : main_qml.index("function wakeDisplay()", main_qml.index("function recordActivity()"))]
    assert "var wasBlanked = root.screenBlanked" in record_activity
    assert "root.restartIdleTimer()" in record_activity
    assert "root.restartReturnToNowTimer()" in record_activity
    assert "if (root.forceScreenAwake && forcedWakeTimer.running)" in record_activity
    assert "forcedWakeTimer.restart()" in record_activity
    assert "if (wasBlanked)" in record_activity
    assert "if (djconnect.returnToNowSeconds > 0)" in record_activity
    assert 'root.activeScreen = "now"' in record_activity
    assert "root.suppressNextNowPanelTap = true" in record_activity
    assert "root.hideTransientUi()" in record_activity
    assert "djconnect.refresh()" in record_activity
    assert "function restartIdleTimer()" in main_qml
    assert "function restartReturnToNowTimer()" in main_qml
    assert "onActiveScreenChanged: {" in main_qml
    assert "root.restartIdleTimer()" in main_qml
    assert "root.restartReturnToNowTimer()" in main_qml
    assert "if (root.suppressNextNowPanelTap)" in main_qml
    assert "root.suppressNextNowPanelTap = false" in main_qml
    assert "root.splashVisible = true" not in record_activity
    assert "splashTimer.restart()" not in record_activity
    assert "root.contentItem.grabToImage" in main_qml
    assert "Qt.size(root.width, root.height)" in main_qml
    assert "z: -1000" in main_qml
    activity_catcher = main_qml[main_qml.rindex("MouseArea {") : main_qml.index("Rectangle {\n        anchors.fill: parent\n        color: \"#000000\"")]
    assert "z: 199" in activity_catcher
    assert "if (root.screenBlanked)" in activity_catcher
    assert "root.wakeDisplay()" in activity_catcher
    assert "mouse.accepted = true" in activity_catcher
    assert "root.recordActivity()" in activity_catcher
    assert "mouse.accepted = false" in activity_catcher
    assert "color: root.color" in main_qml
    assert "result.saveToFile(djconnect.screenshotFile)" in main_qml
    assert "function onWakeScreenRequested()" in main_qml
    assert "forcedWakeTimer.restart()" in main_qml
    assert "opacity: root.screenBlanked ? 1 : root.brightnessOverlayOpacity" in main_qml


def test_qml_has_backend_toast_overlay() -> None:
    main_qml = files("djconnect_pi.qml").joinpath("Main.qml").read_text(encoding="utf-8")

    assert "id: toast" in main_qml
    assert "id: toastGlow" not in main_qml
    assert "djconnect.toastVisible" in main_qml
    assert "djconnect.toastText" in main_qml
    assert "djconnect.toastIcon" in main_qml
    toast_block = main_qml[main_qml.index("id: toast") : main_qml.index("id: versionMismatchPanel")]
    assert "MenuIcon {" in toast_block
    assert "iconName: djconnect.toastIcon" in toast_block
    assert "Canvas {" not in toast_block
    assert "Behavior on opacity" in main_qml
    assert "scale: djconnect.toastVisible ? 1 : 0.94" in toast_block
    assert "Behavior on scale" in toast_block
    assert "SequentialAnimation on border.color" in toast_block
    assert 'root.moodColor("toastStart")' in main_qml
    assert 'root.moodColor("toastEnd")' in main_qml


def test_qml_has_blocking_version_mismatch_view() -> None:
    main_qml = files("djconnect_pi.qml").joinpath("Main.qml").read_text(encoding="utf-8")

    assert "id: versionMismatchPanel" in main_qml
    assert "djconnect.versionMismatchVisible" in main_qml
    assert "djconnect.versionMismatchText" in main_qml


def test_qml_has_pi5_premium_splash_motion_contract() -> None:
    main_qml = files("djconnect_pi.qml").joinpath("Main.qml").read_text(encoding="utf-8")
    splash_block = main_qml[main_qml.index("id: splashPanel") : main_qml.index("id: toast")]

    assert "opacity: root.splashVisible ? 1 : 0" in splash_block
    assert "Behavior on opacity" in splash_block
    assert "SequentialAnimation on scale" in splash_block
    assert "easing.type: Easing.OutBack" in splash_block
    assert "LoadingSpinner {" in splash_block
    assert "running: splashPanel.visible" in splash_block
    assert 'root.tr("update_trying")' in main_qml


def test_qml_has_pi5_ambient_background_drift_contract() -> None:
    main_qml = files("djconnect_pi.qml").joinpath("Main.qml").read_text(encoding="utf-8")
    background = main_qml[main_qml.index("component AppBackground") : main_qml.index("component AppBanner")]

    assert background.count("property real driftX: 0") == 2
    assert background.count("property real driftY: 0") == 2
    assert "running: root.wallProfile && !root.screenBlanked" in background
    assert "duration: 18000" in background
    assert "duration: 21000" in background
    assert "duration: 20000" in background
    assert "duration: 17000" in background


def test_qml_has_update_progress_view_with_expandable_logs() -> None:
    qml_root = files("djconnect_pi.qml")
    main_qml = qml_root.joinpath("Main.qml").read_text(encoding="utf-8")
    update_qml = qml_root.joinpath("UpdateProgress.qml").read_text(encoding="utf-8")

    assert "id: updateProgressPanel" not in main_qml
    assert "djconnect.updateInProgress" not in main_qml
    assert "id: updateProgressRoot" in update_qml
    assert 'property bool wallProfile: updater.releaseProfile === "pi5-arm64"' in update_qml
    assert "width: wallProfile ? Screen.width : 720" in update_qml
    assert "SequentialAnimation on opacity" in update_qml
    assert "Component.onCompleted: updateEntrance.start()" in update_qml
    assert "id: updateProgressGlow" in update_qml


def test_qml_has_a_dedicated_pi5_wall_canvas_and_premium_banner_scale() -> None:
    qml_root = files("djconnect_pi.qml")
    main_qml = qml_root.joinpath("Main.qml").read_text(encoding="utf-8")
    update_qml = qml_root.joinpath("UpdateProgress.qml").read_text(encoding="utf-8")

    assert 'property bool wallProfile: djconnect.releaseProfile === "pi5-arm64"' in main_qml
    assert "width: wallProfile ? Screen.width : 720" in main_qml
    assert "property int titleSize: root.wallProfile ? 52 : 38" in main_qml
    assert "running: root.wallProfile && !root.screenBlanked" in main_qml
    assert "property int motionStandard: wallProfile ? 360 : 240" in main_qml
    assert "scale: djconnect.toastVisible ? 1 : 0.94" in main_qml
    assert "property bool liquidGlassEnabled: true" in main_qml
    assert "#82ffffff" in main_qml
    assert "#c8ffffff" in main_qml
    assert "BusyIndicator" not in update_qml
    assert "component AppBanner" in update_qml
    assert "AppBanner {}" in update_qml
    assert "Layout.preferredWidth: 128" not in update_qml
    assert "Layout.preferredHeight: 128" not in update_qml
    assert "updater.progress" in update_qml
    assert "updater.detailsOpen" in update_qml
    assert "updater.toggleDetails()" in update_qml
    assert "updater.logs" in update_qml
    assert "updater.currentVersion" in update_qml
    assert "updater.targetVersion" in update_qml
    assert 'updater.t("current_version")' in update_qml
    assert 'updater.t("target_version")' in update_qml
    assert 'text: "->"' in update_qml
    assert "id: updateProgressBar" in update_qml
    assert "updateProgressBar.visualPosition" in update_qml
    assert "Behavior on width" in update_qml
    assert "Layout.preferredHeight: updateProgressRoot.wallProfile ? 48 : 36" in update_qml
    assert "font.pixelSize: updateProgressRoot.wallProfile ? 28 : 22" in update_qml
    assert "id: detailsButton" in update_qml
    assert "Layout.preferredHeight: updateProgressRoot.wallProfile ? 72 : 54" in update_qml
    assert "property bool liquidGlassEnabled: true" in update_qml
    assert "#82ffffff" in update_qml
    assert "BrandTheme.colors.buttonEnd" in update_qml
    assert "id: updaterRebootButtonShell" in update_qml
    assert "anchors.bottom: remoteAccessPanel.top" in update_qml
    assert "id: updaterRebootButton" in update_qml
    assert 'text: updater.t("reboot_device")' in update_qml
    assert "updateProgressRoot.rebootConfirmOpen = true" in update_qml
    assert "visible: updateProgressRoot.rebootConfirmOpen" in update_qml
    assert 'updater.t("reboot_confirm_title")' in update_qml
    assert 'updater.t("reboot_confirm_message")' in update_qml
    assert "updater.rebootDevice()" in update_qml
    assert "id: cancelRebootButton" in update_qml
    assert 'updater.t("remote_viewing")' in update_qml
    assert "id: remoteAccessPanel" in update_qml
    assert "visible: !updater.detailsOpen" in update_qml
    assert "anchors.bottom: parent.bottom" in update_qml
    assert "updater.sshCommand" in update_qml
    assert "updater.vncCommand" in update_qml
    assert "updater.vncInstruction" in update_qml
    assert 'updater.tf("vnc_tunnel_label", updater.vncCommand)' in update_qml


def test_qml_uses_dark_djconnect_gradient_theme() -> None:
    qml_root = files("djconnect_pi.qml")
    main_qml = qml_root.joinpath("Main.qml").read_text(encoding="utf-8")
    games_qml = qml_root.joinpath("GamesPanel.qml").read_text(encoding="utf-8")

    for text in (main_qml, games_qml):
        assert "Gradient" in text
        assert "MoodTheme" in text
    assert "id: splashPanel" in main_qml
    mood_theme = qml_root.joinpath("MoodTheme.js").read_text(encoding="utf-8")
    assert 'function moodColor(value, token)' in mood_theme
    assert 'function color(value, token)' in mood_theme
    assert 'BrandTheme.colors[aliases[token]]' in mood_theme
    for mood in ("chill", "groove", "energy", "party"):
        assert '"' + mood + '"' in mood_theme


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
            "1500",
            "--config",
            os.path.join(tmpdir, "djconnect-pi-qml-test.json"),
            "--log-file",
            os.path.join(tmpdir, "djconnect-pi-qml-test.log"),
        ],
        env=env,
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )

    assert result.returncode == 0
    assert "Error:" not in result.stderr
