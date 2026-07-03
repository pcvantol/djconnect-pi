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
    assert 'id: pairingPanel\n        anchors.fill: parent\n        color: "#070b16"' in main_qml
    assert 'id: pairingSuccessPanel\n        anchors.fill: parent\n        color: "#070b16"' in main_qml
    assert "id: splashPanel" in main_qml
    assert 'source: "app-icon.png"' in main_qml
    assert "component AppBanner" in main_qml
    assert 'radius: 24\n        color: "#171029"' in main_qml
    assert 'GradientStop { position: 0.72; color: "#37145a" }' in main_qml
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
    assert 'color: "#cc0a0522"' in games_qml
    assert 'GradientStop { position: 0.0; color: gameSegment.checked ? "#247fff" : "#00000000" }' in games_qml
    assert 'GradientStop { position: 1.0; color: gameSegment.checked ? "#c33cff" : "#00000000" }' in games_qml
    assert "root.tr(modelData.titleKey)" in games_qml
    assert "MouseArea" in games_qml
    assert "preventStealing: true" in games_qml
    assert "propagateComposedEvents: false" in games_qml
    assert "onClicked: function(mouse)" in games_qml
    assert "handleTouch" in games_qml
    assert "onPressed: function(mouse) { root.handleTouch(mouse.x, mouse.y) }" in games_qml
    assert "mouthOpen" in games_qml
    assert "ghostX - 4" in games_qml
    assert "property var powerPellets: [0, 7, 24, 31]" in games_qml
    assert "property int ghostVulnerableTicks" in games_qml
    assert "ghostVulnerableTicks = 210" in games_qml
    assert "for (var i = 0; i < 32; i++) pellets.push(i)" in games_qml
    assert "powerPellets = [0, 7, 24, 31]" in games_qml
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
    assert "component GlassButton" in games_qml
    assert "#3324145f" in main_qml
    assert "#247fff" in games_qml
    assert "#c33cff" in games_qml
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
    assert settings_block.index('root.tr("view_logs")') < settings_block.index('root.tr("check_updates")')
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
    assert 'playCommand: "play_context_at"' in main_qml
    assert 'playCommand: "start_playlist"' in main_qml
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
    assert main_qml.count("Layout.preferredWidth: 142") >= 2
    assert main_qml.count("Layout.preferredHeight: 48") >= 2
    assert "anchors.topMargin: 16" in main_qml
    assert 'djconnect.haUrl.length ? djconnect.haUrl : "http://homeassistant.local:8123"' in main_qml
    assert "djconnect.outputDevices" in main_qml
    assert "property var deviceChoices" in main_qml
    assert 'property string noOutputDeviceLabel: root.tr("none")' in main_qml
    assert "djconnect.setOutputDevice" in main_qml
    assert "djconnect.adjustVolume(-10)" in main_qml
    assert "djconnect.adjustVolume(10)" in main_qml
    assert 'text: "-"' in main_qml
    assert 'text: "+"' in main_qml
    assert "id: nowPanel" in main_qml
    assert 'visible: root.activeScreen === "now"' in main_qml
    assert "id: controlPanel" in main_qml
    assert 'visible: root.activeScreen === "control"' in main_qml
    assert 'root.tr("control")' in main_qml
    assert "id: controlOutputDeviceCombo" in main_qml
    assert "function selectedIndex()" in main_qml
    assert "currentIndex: selectedIndex()" in main_qml
    assert 'text: "🔊"' not in main_qml
    assert "wrapMode: TextEdit.Wrap" in main_qml
    assert 'text: root.tr("log") + ": " + djconnect.logFile' in main_qml
    assert "djconnect.cachedImageUrl(modelData.imageUrl)" not in main_qml
    assert "source: modelData.imageUrl && modelData.imageUrl.length > 0 ? modelData.imageUrl : \"\"" in main_qml
    assert "sourceSize.width: 68" in main_qml
    assert "sourceSize.height: 68" in main_qml
    assert "sourceSize.width: width" in main_qml
    assert "sourceSize.height: height" in main_qml
    assert main_qml.count("cache: false") >= 1
    assert "height: 92" not in main_qml
    assert "color: \"#990b1012\"" not in main_qml
    assert "Layout.preferredHeight: 178" in main_qml
    assert "Layout.preferredHeight: 126" in main_qml
    assert "Layout.preferredHeight: 76" in main_qml
    assert 'color: djconnect.paired ? (djconnect.backendAvailable ? "#32d35a" : "#ff3b30") : "#e0a83a"' in main_qml
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
    assert "logsArea.cursorPosition = logsArea.length" in main_qml
    assert "djconnect.copyLogs()" not in main_qml
    assert 'root.tr("copy_logs")' not in main_qml
    logs_start = main_qml.index("visible: djconnect.logsVisible")
    logs_block = main_qml[logs_start : main_qml.index("id: clearLogsConfirmPanel", logs_start)]
    assert "Layout.maximumHeight: 56" in logs_block
    assert "Layout.fillHeight: false" in logs_block
    assert "Layout.minimumHeight: 360" in logs_block
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
    main_qml = files("djconnect_pi.qml").joinpath("Main.qml").read_text(encoding="utf-8")
    bottom_nav = main_qml[main_qml.index("id: bottomNav") : main_qml.index("id: pairingPanel")]
    more_panel = main_qml[main_qml.index("id: morePanel") : main_qml.index("id: askDjPanel")]

    assert "id: bottomNav" in main_qml
    assert "component MenuIcon: Canvas" in main_qml
    assert "component NavButton" in main_qml
    assert "component MoreMenuButton" in main_qml
    assert "id: morePanel" in main_qml
    assert "height: 104" in main_qml
    assert "border.width: navControl.checked ? 2 : 0" in main_qml
    nav_button = main_qml[main_qml.index("component NavButton") : main_qml.index("component MoreMenuButton")]
    assert "anchors.top: parent.top" not in nav_button
    assert "visible: navControl.checked" not in nav_button
    assert 'iconName: "music"' in bottom_nav
    assert 'iconName: "control"' in bottom_nav
    assert 'iconName: "chat"' in bottom_nav
    assert 'iconName: "queue"' in bottom_nav
    assert 'iconName: "more"' in bottom_nav
    assert 'iconName: "playlists"' in more_panel
    assert 'iconName: "gamepad"' in more_panel
    assert 'iconName: "settings"' in more_panel
    assert 'iconName: "logs"' in more_panel
    assert 'iconName: "info"' in more_panel
    assert "iconSymbol" not in main_qml
    assert 'root.tr("now_playing")' in main_qml
    assert 'root.tr("control")' in bottom_nav
    assert 'root.tr("ask_dj")' in bottom_nav
    assert 'root.tr("queue")' in bottom_nav
    assert 'root.tr("more")' in bottom_nav
    assert 'root.tr("playlists")' in more_panel
    assert 'root.tr("games")' in main_qml
    assert 'root.tr("setup")' in main_qml
    assert 'root.tr("logs")' in more_panel
    assert 'root.tr("about")' in more_panel
    assert bottom_nav.index('text: root.tr("now_playing")') < bottom_nav.index('text: root.tr("control")')
    assert bottom_nav.index('text: root.tr("control")') < bottom_nav.index('text: root.tr("ask_dj")')
    assert bottom_nav.index('text: root.tr("ask_dj")') < bottom_nav.index('text: root.tr("queue")')
    assert bottom_nav.index('text: root.tr("queue")') < bottom_nav.index('text: root.tr("more")')
    assert more_panel.index('text: root.tr("playlists")') < more_panel.index('text: root.tr("games")')
    assert more_panel.index('text: root.tr("games")') < more_panel.index('text: root.tr("setup")')
    assert more_panel.index('text: root.tr("setup")') < more_panel.index('text: root.tr("logs")')
    assert more_panel.index('text: root.tr("logs")') < more_panel.index('text: root.tr("about")')
    assert 'root.activeScreen = "now"' in main_qml
    assert 'root.activeScreen = "control"' in main_qml
    assert 'root.activeScreen = "playlists"' in main_qml
    assert 'root.activeScreen = "games"' in main_qml
    assert 'root.activeScreen = "settings"' in main_qml
    assert 'root.activeScreen = "more"' in main_qml


def test_qml_ask_dj_screen_sends_text_without_audio_controls() -> None:
    main_qml = files("djconnect_pi.qml").joinpath("Main.qml").read_text(encoding="utf-8")
    ask_dj_block = main_qml[main_qml.index("id: askDjPanel") : main_qml.index("GamesPanel {")]

    assert 'visible: root.activeScreen === "askdj"' in ask_dj_block
    assert "component AskDjGradientButton" in main_qml
    assert 'GradientStop { position: 0.0; color: askDjButton.enabled ? "#247fff" : "#33415f" }' in main_qml
    assert 'GradientStop { position: 1.0; color: askDjButton.enabled ? "#c33cff" : "#4b3d65" }' in main_qml
    assert "djconnect.refreshAskDjHistory()" in ask_dj_block
    assert "id: askDjRefreshButton" in ask_dj_block
    assert "AskDjGradientButton" in ask_dj_block
    assert "Layout.preferredWidth: 132" in ask_dj_block
    assert "djconnect.clearAskDjHistory()" in ask_dj_block
    assert 'root.tr("ask_dj_readonly_hint")' in ask_dj_block
    assert "TextField" in ask_dj_block
    assert 'root.tr("ask_dj_input_placeholder")' in ask_dj_block
    assert 'root.tr("send")' in ask_dj_block
    assert "djconnect.sendAskDjMessage(message)" in ask_dj_block
    assert "component AskDjKeyButton" in main_qml
    key_button_block = main_qml[main_qml.index("component AskDjKeyButton") : main_qml.index("component MenuIcon")]
    assert "propagateComposedEvents: false" in key_button_block
    assert "preventStealing: true" in key_button_block
    assert "keyButton.clicked()" in key_button_block
    assert "id: askDjKeyboard" in ask_dj_block
    keyboard_block = ask_dj_block[ask_dj_block.index("id: askDjKeyboard") : ask_dj_block.index("GamesPanel {") if "GamesPanel {" in ask_dj_block else len(ask_dj_block)]
    assert "propagateComposedEvents: false" in keyboard_block
    assert "preventStealing: true" in keyboard_block
    assert "askDjInput.forceActiveFocus()" in keyboard_block
    assert "property bool askDjKeyboardOpen: false" in main_qml
    assert "root.askDjKeyboardOpen = true" in ask_dj_block
    assert "root.askDjKeyboardOpen = false" in ask_dj_block
    assert "TapHandler" in ask_dj_block
    assert "visible: root.askDjKeyboardOpen" in ask_dj_block
    assert "askDjInput.mapToItem(askDjPanel, 0, askDjInput.height).y + 8" in ask_dj_block
    assert "height: 216" in ask_dj_block
    assert "z: 40" in ask_dj_block
    assert "function insertAskDjKey(value)" in ask_dj_block
    assert "function deleteAskDjText()" in ask_dj_block
    insert_block = ask_dj_block[ask_dj_block.index("function insertAskDjText") : ask_dj_block.index("function insertAskDjKey")]
    delete_block = ask_dj_block[ask_dj_block.index("function deleteAskDjText") : ask_dj_block.index("AppBackground {}")]
    text_field_block = ask_dj_block[ask_dj_block.index("id: askDjInput") : ask_dj_block.index("AskDjGradientButton {\n                        text: root.tr(\"send\")")]
    assert "djconnect.askDjBusy" not in insert_block
    assert "djconnect.askDjBusy" not in delete_block
    assert "enabled: !djconnect.askDjBusy" not in text_field_block
    assert 'model: ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"]' in ask_dj_block
    assert 'displayText: root.tr("keyboard_space")' in ask_dj_block
    assert 'root.tr("replay_audio")' in ask_dj_block
    assert "visible: modelData.audioUrl && modelData.audioUrl.length > 0" in ask_dj_block
    assert "Qt.openUrlExternally(modelData.audioUrl)" in ask_dj_block
    assert "id: askDjPollTimer" in main_qml
    assert 'running: root.activeScreen === "askdj" && djconnect.paired && !djconnect.demoMode' in main_qml
    assert "onTriggered: djconnect.pollAskDjHistory()" in main_qml
    assert "function scrollAskDjToBottom()" in main_qml
    assert 'if (root.activeScreen === "askdj")' in main_qml
    assert "function onAskDjChanged()" in main_qml
    assert "askDjScroll.contentItem.contentY = Math.max" in ask_dj_block or "askDjScroll.contentItem.contentY = Math.max" in main_qml
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
    assert "modelData.musicDna ? \"#33334857\" : \"#3324145f\"" in ask_dj_block
    assert "modelData.value || \"\"" in ask_dj_block
    assert "[modelData.source || \"\", modelData.confidence || \"\"].filter" in ask_dj_block
    assert "modelData.analysis.sections && modelData.analysis.sections.length > 0" in ask_dj_block
    assert "modelData.title || modelData.id || modelData.kind" in ask_dj_block
    assert "modelData.metadataContext ? \"#33334857\" : \"#3324145f\"" in ask_dj_block
    assert "!modelData.trackInsight && modelData.items && modelData.items.length > 0" in ask_dj_block


def test_qml_now_playing_can_save_current_track() -> None:
    main_qml = files("djconnect_pi.qml").joinpath("Main.qml").read_text(encoding="utf-8")
    now_block = main_qml[main_qml.index("id: nowPanel") : main_qml.index("id: controlPanel")]

    assert 'root.tr("add_to_favorites")' in now_block
    assert "djconnect.saveCurrentTrack()" in now_block
    assert 'root.tr("track_insight")' in now_block
    assert "djconnect.openTrackInsight()" in now_block


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
    assert "property bool screenBlanked: djconnect.screenTimeoutSeconds > 0 && !idleTimer.running && !root.forceScreenAwake" in main_qml
    assert "root.screenBlanked || root.forceBrightnessFull" in main_qml
    assert "onTapped: root.wakeDisplay()" in main_qml
    assert "id: forcedWakeTimer" in main_qml
    assert "interval: 10000" in main_qml
    assert "root.activeScreen = \"now\"" in main_qml
    assert "function temporaryWake(seconds, navigateNow)" in main_qml
    assert "function onTemporaryWakeRequested(seconds, navigateNow)" in main_qml
    assert "id: djResponseOverlay" in main_qml
    assert "id: djResponseTimer" in main_qml
    assert "djconnect.djResponseVisible" in main_qml
    assert "djconnect.djResponseText" in main_qml
    assert "djconnect.clearDjResponse()" in main_qml
    assert "source: \"app-icon.png\"" in main_qml
    assert "id: albumQuickPlay" not in main_qml
    assert "id: albumQuickPlayIcon" not in main_qml
    assert "function onScreenshotRequested()" in main_qml
    assert "function onDebugScreenRequested(screen)" in main_qml
    assert 'screen === "queue"' in main_qml
    assert 'screen === "playlists"' in main_qml
    assert 'screen === "logs"' in main_qml
    assert 'screen === "about"' in main_qml
    assert "function wakeDisplay()" in main_qml
    record_activity = main_qml[main_qml.index("function recordActivity()") : main_qml.index("function wakeDisplay()", main_qml.index("function recordActivity()"))]
    assert "var wasBlanked = root.screenBlanked" in record_activity
    assert "root.restartIdleTimer()" in record_activity
    assert "if (wasBlanked)" in record_activity
    assert 'root.activeScreen = "now"' in record_activity
    assert "root.suppressNextNowPanelTap = true" in record_activity
    assert "root.hideTransientUi()" in record_activity
    assert "djconnect.refresh()" in record_activity
    assert "function restartIdleTimer()" in main_qml
    assert "onActiveScreenChanged: {" in main_qml
    assert "root.restartIdleTimer()" in main_qml
    assert "if (root.suppressNextNowPanelTap)" in main_qml
    assert "root.suppressNextNowPanelTap = false" in main_qml
    assert "root.splashVisible = true" not in record_activity
    assert "splashTimer.restart()" not in record_activity
    assert "root.contentItem.grabToImage" in main_qml
    assert "Qt.size(root.width, root.height)" in main_qml
    assert "z: -1000" in main_qml
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
    assert "Behavior on opacity" in main_qml
    assert "#ff5a2e" in main_qml
    assert "#b731ff" in main_qml


def test_qml_has_blocking_version_mismatch_view() -> None:
    main_qml = files("djconnect_pi.qml").joinpath("Main.qml").read_text(encoding="utf-8")

    assert "id: versionMismatchPanel" in main_qml
    assert "djconnect.versionMismatchVisible" in main_qml
    assert "djconnect.versionMismatchText" in main_qml
    assert 'root.tr("update_trying")' in main_qml


def test_qml_has_update_progress_view_with_expandable_logs() -> None:
    qml_root = files("djconnect_pi.qml")
    main_qml = qml_root.joinpath("Main.qml").read_text(encoding="utf-8")
    update_qml = qml_root.joinpath("UpdateProgress.qml").read_text(encoding="utf-8")

    assert "id: updateProgressPanel" not in main_qml
    assert "djconnect.updateInProgress" not in main_qml
    assert "id: updateProgressRoot" in update_qml
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
    assert "Layout.preferredHeight: 36" in update_qml
    assert "font.pixelSize: 22" in update_qml
    assert "id: detailsButton" in update_qml
    assert "Layout.preferredHeight: 54" in update_qml
    assert "#d433ff" in update_qml
    assert 'updater.t("remote_viewing")' in update_qml
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
