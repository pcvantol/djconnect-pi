import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "BrandTheme.js" as BrandTheme

Item {
    id: view
    objectName: "logsView"
    required property var backend
    property bool confirmationOpen: false
    signal clearRequested()

    readonly property bool compact: width < 900
    readonly property int inset: compact ? 14 : 26
    readonly property var lines: backend.logsText ? backend.logsText.split("\n") : []
    property bool searching: false
    property bool keyboardOpen: false
    property int matchIndex: -1
    readonly property var matches: findMatches(lines, searchInput.text)
    readonly property var currentMatch: matches[matchIndex] || null

    function tr(key) { backend.translationVersion; return backend.t(key) }
    function findMatches(rows, query) {
        if (!query.trim()) return []
        var result = []
        var pattern = new RegExp(query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "giu")
        for (var row = 0; row < rows.length; row++) {
            pattern.lastIndex = 0
            var hit
            while ((hit = pattern.exec(rows[row])) !== null)
                result.push({row: row, start: hit.index, end: hit.index + hit[0].length})
        }
        return result
    }
    function escapeText(value) {
        return value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    }
    function lineText(row, text) {
        var hit = currentMatch
        if (!hit || hit.row !== row) return escapeText(text)
        return escapeText(text.slice(0, hit.start))
            + '<b><font color="' + BrandTheme.colors.actionAccent + '">' + escapeText(text.slice(hit.start, hit.end))
            + '</font></b>' + escapeText(text.slice(hit.end))
    }
    function moveMatch(step) {
        if (!matches.length) return
        matchIndex = (matchIndex + step + matches.length) % matches.length
        logRows.positionViewAtIndex(currentMatch.row, ListView.Contain)
    }
    function showSearch() {
        searching = true
        keyboardOpen = true
        searchInput.forceActiveFocus()
    }
    function closeSearch() {
        keyboardOpen = false
        searching = false
        searchInput.clear()
    }
    function submitSearch() {
        keyboardOpen = false
        if (currentMatch) logRows.positionViewAtIndex(currentMatch.row, ListView.Contain)
    }
    onMatchesChanged: {
        matchIndex = matches.length ? 0 : -1
        if (currentMatch) logRows.positionViewAtIndex(currentMatch.row, ListView.Contain)
    }
    onVisibleChanged: if (!visible) closeSearch()

    component LogAction: GlassButton {
        implicitWidth: 48; implicitHeight: 48; padding: 9
    }
    ColumnLayout {
        anchors.fill: parent
        spacing: 12

        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 58
            Layout.leftMargin: view.inset; Layout.rightMargin: view.inset
            Layout.topMargin: view.inset
            LogAction {
                anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter
                iconName: "back"; Accessible.name: view.tr("close")
                onClicked: view.backend.hideLogs()
            }
            Text {
                anchors.centerIn: parent
                text: view.tr("logs"); font.pixelSize: view.compact ? 24 : 29
                font.bold: true; color: BrandTheme.colors.text
            }
            GlassSurface {
                anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
                width: tools.implicitWidth + 12; height: 54; radius: height / 2
                RowLayout {
                    id: tools
                    anchors.centerIn: parent
                    spacing: 0
                    LogAction {
                        objectName: "logsSearchOpen"
                        iconName: "search"; Accessible.name: view.tr("logs_search")
                        checked: view.searching
                        background: Item {}
                        foregroundColor: checked ? BrandTheme.colors.actionAccent : BrandTheme.colors.text
                        onClicked: view.showSearch()
                    }
                    LogAction {
                        iconName: "refresh"; Accessible.name: view.tr("refresh")
                        background: Item {}
                        onClicked: { view.backend.showLogs(); if (!view.currentMatch) logRows.positionViewAtBeginning() }
                    }
                    LogAction {
                        objectName: "logsCopy"
                        iconName: "copy"; Accessible.name: view.tr("copy_logs")
                        enabled: view.lines.length > 0; background: Item {}
                        onClicked: view.backend.copyLogs()
                    }
                    LogAction {
                        objectName: "logsClear"
                        iconName: "trash"; Accessible.name: view.tr("clear_logs")
                        tint: BrandTheme.colors.actionDanger; background: Item {}
                        onClicked: view.clearRequested()
                    }
                }
            }
        }
        GlassCard {
            Layout.fillWidth: true; Layout.fillHeight: true; Layout.minimumHeight: 0
            Layout.leftMargin: view.inset; Layout.rightMargin: view.inset
            padding: view.compact ? 12 : 20
            spacing: 10

            Control {
                visible: view.searching
                Layout.fillWidth: true
                padding: 4
                background: GlassSurface {
                    radius: 20; interactive: true; focused: searchInput.activeFocus
                }
                contentItem: RowLayout {
                    spacing: 2
                    FeatureIcon { iconName: "search"; Layout.preferredWidth: 24; Layout.preferredHeight: 24 }
                    TextField {
                        id: searchInput
                        objectName: "logsSearchInput"
                        Layout.fillWidth: true
                        Layout.minimumHeight: 48
                        background: Item {}
                        placeholderText: view.tr("logs_search")
                        Accessible.name: placeholderText
                        font.pixelSize: view.compact ? 18 : 21
                        maximumLength: 120
                        selectByMouse: true
                        onActiveFocusChanged: if (activeFocus && view.searching) view.keyboardOpen = true
                        TapHandler { onTapped: view.keyboardOpen = true }
                        Keys.onEscapePressed: if (view.keyboardOpen) view.submitSearch(); else view.closeSearch()
                        onAccepted: {
                            if (view.keyboardOpen) view.submitSearch()
                            else view.moveMatch(1)
                        }
                    }
                    Text {
                        visible: searchInput.text.length > 0
                        text: view.matches.length ? (view.matchIndex + 1) + " / " + view.matches.length : view.tr("logs_no_matches")
                        color: BrandTheme.colors.muted; font.pixelSize: 15
                    }
                    LogAction {
                        objectName: "logsPreviousMatch"
                        iconName: "arrow_up"; Accessible.name: view.tr("logs_previous_match")
                        enabled: view.matches.length > 0
                        background: Item {}
                        onClicked: view.moveMatch(-1)
                    }
                    LogAction {
                        objectName: "logsNextMatch"
                        iconName: "arrow_down"; Accessible.name: view.tr("logs_next_match")
                        enabled: view.matches.length > 0
                        background: Item {}
                        onClicked: view.moveMatch(1)
                    }
                    LogAction {
                        iconName: "end"; Accessible.name: view.tr("close")
                        background: Item {}
                        onClicked: view.closeSearch()
                    }
                }
            }
            ListView {
                id: logRows
                objectName: "logRows"
                Layout.fillWidth: true; Layout.fillHeight: true; Layout.minimumHeight: 0
                model: view.lines
                clip: true
                spacing: 3
                ScrollBar.vertical: ScrollBar {}
                delegate: RowLayout {
                    id: entry
                    required property int index
                    required property string modelData
                    width: logRows.width - 10
                    spacing: 12
                    Text {
                        text: entry.index + 1
                        font.family: "monospace"; font.pixelSize: view.compact ? 16 : 20
                        color: BrandTheme.colors.disabledText
                        horizontalAlignment: Text.AlignRight
                        Layout.preferredWidth: 46; Layout.alignment: Qt.AlignTop
                    }
                    Text {
                        text: view.lineText(entry.index, entry.modelData)
                        textFormat: Text.StyledText
                        font.family: "monospace"; font.pixelSize: view.compact ? 16 : 20
                        color: BrandTheme.colors.text
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }
                }
            }
        }
        Text {
            visible: !view.keyboardOpen
            Layout.fillWidth: true
            Layout.leftMargin: view.inset; Layout.rightMargin: view.inset
            Layout.bottomMargin: view.inset
            text: view.tr("log") + ": " + view.backend.logFile
            textFormat: Text.PlainText
            elide: Text.ElideMiddle
            font.pixelSize: 15
            color: BrandTheme.colors.muted
        }
        SearchKeyboardDock {
            objectName: "logsSearchDock"
            keyboardName: "logsTouchKeyboard"
            visible: view.keyboardOpen && !view.confirmationOpen
            Layout.fillWidth: true
            backend: view.backend
            target: searchInput
            onSubmitted: view.submitSearch()
            onDismissed: view.keyboardOpen = false
        }
    }
}
