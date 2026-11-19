import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "BrandTheme.js" as BrandTheme

ColumnLayout {
    id: keyboard
    objectName: "sessionTouchKeyboard"
    property var target
    property var backend
    property bool docked: false
    property string submitIcon: "search"
    property string submitLabel: keyboard.tr("session_search")
    property int keyHeight: 44
    property int keyFontSize: 19
    property int keyGap: 4
    property bool shifted: false
    property bool numbers: false
    property bool accents: false
    signal edited()
    signal submitted()
    signal dismissed()
    spacing: keyboard.keyGap
    function tr(key) { backend.translationVersion; return backend.t(key) }
    function insertKey(value) {
        if (!target || !target.enabled) return
        var at = Math.min(target.selectionStart, target.selectionEnd)
        if (target.selectionStart !== target.selectionEnd)
            target.remove(target.selectionStart, target.selectionEnd)
        target.insert(at, value)
        target.cursorPosition = at + value.length
        target.forceActiveFocus()
        edited()
    }
    function deleteKey() {
        if (!target || !target.enabled) return
        if (target.selectionStart !== target.selectionEnd) {
            var at = Math.min(target.selectionStart, target.selectionEnd)
            target.remove(target.selectionStart, target.selectionEnd)
            target.cursorPosition = at
        } else if (target.cursorPosition > 0) {
            var end = target.cursorPosition
            var start = end - 1
            var code = target.text.charCodeAt(start)
            if (code >= 0xdc00 && code <= 0xdfff && start > 0) {
                var previous = target.text.charCodeAt(start - 1)
                if (previous >= 0xd800 && previous <= 0xdbff) start -= 1
            }
            target.remove(start, end)
            target.cursorPosition = start
        }
        target.forceActiveFocus()
        edited()
    }
    function rows() {
        if (accents) return ["áàäâãåéèëê", "íìïîóòöôø", "úùüûñçßœæ"]
        if (numbers) return ["1234567890", "-/:;()€&@", ".,?!'\"+*=#"]
        if (backend.language === "fr") return ["azertyuiop", "qsdfghjklm", "wxcvbn"]
        if (backend.language === "de") return ["qwertzuiop", "asdfghjkl", "yxcvbnm"]
        return ["qwertyuiop", "asdfghjkl", "zxcvbnm"]
    }
    component KeyButton: GlassButton {
        cornerRadius: keyboard.docked ? 12 : height / 2
    }
    Repeater {
        model: keyboard.rows()
        RowLayout {
            id: keyRow
            required property string modelData
            Layout.fillWidth: true
            spacing: keyboard.keyGap
            Repeater {
                model: keyRow.modelData.split("")
                KeyButton {
                    required property string modelData
                    Layout.fillWidth: true; Layout.preferredWidth: 1; Layout.minimumWidth: 44
                    implicitHeight: keyboard.keyHeight; padding: 4; font.pixelSize: keyboard.keyFontSize
                    text: keyboard.shifted ? modelData.toUpperCase() : modelData
                    focusPolicy: Qt.NoFocus
                    onClicked: keyboard.insertKey(text)
                }
            }
        }
    }
    RowLayout {
        Layout.fillWidth: true; spacing: keyboard.keyGap
        KeyButton {
            text: "⇧"; Accessible.name: keyboard.tr("keyboard_shift")
            checked: keyboard.shifted; focusPolicy: Qt.NoFocus
            implicitHeight: keyboard.keyHeight; Layout.minimumWidth: keyboard.keyHeight; padding: 6; Layout.preferredWidth: 48
            onClicked: keyboard.shifted = !keyboard.shifted
        }
        KeyButton {
            text: keyboard.numbers ? "ABC" : "123"
            Accessible.name: keyboard.tr("keyboard_symbols")
            focusPolicy: Qt.NoFocus; implicitHeight: keyboard.keyHeight; Layout.minimumWidth: keyboard.keyHeight; padding: 6; Layout.preferredWidth: 58
            onClicked: { keyboard.numbers = !keyboard.numbers; keyboard.accents = false }
        }
        KeyButton {
            text: "é"; Accessible.name: keyboard.tr("keyboard_accents")
            checked: keyboard.accents; focusPolicy: Qt.NoFocus
            implicitHeight: keyboard.keyHeight; Layout.minimumWidth: keyboard.keyHeight; padding: 6; Layout.preferredWidth: 44
            onClicked: keyboard.accents = !keyboard.accents
        }
        KeyButton {
            text: keyboard.tr("keyboard_space"); focusPolicy: Qt.NoFocus
            implicitHeight: keyboard.keyHeight; Layout.minimumWidth: keyboard.keyHeight; padding: 6; Layout.fillWidth: true
            onClicked: keyboard.insertKey(" ")
        }
        KeyButton {
            text: "⌫"; Accessible.name: keyboard.tr("keyboard_delete")
            focusPolicy: Qt.NoFocus; implicitHeight: keyboard.keyHeight; Layout.minimumWidth: keyboard.keyHeight; padding: 6; Layout.preferredWidth: 54
            onClicked: keyboard.deleteKey()
        }
        KeyButton {
            iconName: keyboard.submitIcon; Accessible.name: keyboard.submitLabel
            checked: keyboard.docked
            selectionFill: keyboard.docked ? BrandTheme.colors.actionBlue : "transparent"
            focusPolicy: Qt.NoFocus; implicitHeight: keyboard.keyHeight; Layout.minimumWidth: keyboard.keyHeight; padding: 6; Layout.preferredWidth: 48
            onClicked: keyboard.submitted()
        }
        KeyButton {
            text: "⌄"; Accessible.name: keyboard.tr("keyboard_hide")
            focusPolicy: Qt.NoFocus; implicitHeight: keyboard.keyHeight; Layout.minimumWidth: keyboard.keyHeight; padding: 6; Layout.preferredWidth: 44
            onClicked: keyboard.dismissed()
        }
    }
}
