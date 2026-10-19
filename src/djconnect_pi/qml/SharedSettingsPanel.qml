import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: editor
    property var backend
    property var draft: ({})
    property string editToken: ""
    property bool dirty: false
    property var changedFields: ({})
    property bool saving: false
    property var fields: ["persona", "voice", "gender", "mood", "presence", "announcement_output"]
    spacing: 12

    function tr(key) { backend.translationVersion; return backend.t(key) }
    function loadConfirmed() {
        var state = backend.sharedSettings
        draft = JSON.parse(JSON.stringify(state.values || {}))
        editToken = state.edit_token || ""
        dirty = false
        changedFields = ({})
    }
    function options(field) {
        var list = (backend.sharedSettings.options || {})[field] || []
        if (field === "voice") return list
        return list.map(function(value) { return { value: value, label_key: "shared_" + field + "_" + value } })
    }
    function label(item) { return item.label_key ? tr(item.label_key) : item.label }
    function selectedIndex(field) {
        var list = options(field)
        for (var i = 0; i < list.length; ++i)
            if (sameValue(list[i].value, draft[field])) return i
        return -1
    }
    function sameValue(a, b) {
        if (a && typeof a === "object" && b && typeof b === "object")
            return a.kind === b.kind && a.provider_id === b.provider_id && a.voice_id === b.voice_id
        return a === b
    }
    function choose(field, value) {
        var next = JSON.parse(JSON.stringify(draft))
        next[field] = value
        draft = next
        var changed = Object.assign({}, changedFields)
        changed[field] = true
        changedFields = changed
        dirty = true
    }
    function errorText() {
        var error = backend.sharedSettings.error || ""
        if (error === "unsupported") return tr("shared_error_unsupported")
        if (error === "denied") return tr("shared_error_denied")
        if (error === "conflict") return tr("shared_error_conflict")
        if (error === "selection_required") return tr("shared_selection_required")
        if (error === "uncertain" || backend.sharedSettings.operation_pending || backend.sharedSettings.operation_unknown)
            return tr("shared_error_uncertain")
        if (error === "offline") return tr("shared_error_offline")
        if (error) return tr("shared_error_rejected")
        return ""
    }

    Connections {
        target: editor.backend
        function onSharedSettingsChanged() {
            if (editor.saving && !editor.backend.sharedSettingsBusy) {
                editor.saving = false
                if (editor.backend.sharedSettings.available && !editor.backend.sharedSettings.operation_pending &&
                    !editor.backend.sharedSettings.operation_unknown)
                    editor.loadConfirmed()
            } else if (!editor.dirty) editor.loadConfirmed()
            if (!editor.backend.sharedSettings.values) editor.loadConfirmed()
        }
    }
    Component.onCompleted: loadConfirmed()

    Label {
        text: editor.tr("shared_title")
        color: "#f4f8f8"
        font.pixelSize: 28
        font.bold: true
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        Accessible.role: Accessible.Heading
    }
    Label {
        text: editor.tr(editor.backend.sharedSettings.active ? "shared_scope_active" : "shared_scope_defaults")
        color: "#d7e2e4"
        font.pixelSize: 20
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
    }
    Label {
        visible: editor.backend.sharedSettings.selection_required || false
        text: editor.tr("shared_selection_required")
        color: "#ffdca8"
        font.pixelSize: 20
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
    }
    Label {
        visible: editor.errorText().length > 0
        text: editor.errorText()
        color: "#ffdca8"
        font.pixelSize: 20
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        Accessible.role: Accessible.AlertMessage
    }
    Label {
        visible: editor.dirty && editor.editToken !== (editor.backend.sharedSettings.edit_token || "")
        text: editor.tr("shared_error_conflict")
        color: "#ffdca8"
        font.pixelSize: 20
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
    }
    Repeater {
        model: editor.backend.sharedSettings.values ? editor.fields : []
        delegate: ColumnLayout {
            id: fieldRow
            required property string modelData
            Layout.fillWidth: true
            spacing: 6
            Label {
                text: editor.tr("shared_field_" + fieldRow.modelData)
                color: "#d7e2e4"
                font.pixelSize: 22
            }
            ComboBox {
                id: choice
                objectName: "shared_choice_" + fieldRow.modelData
                Layout.fillWidth: true
                Layout.minimumHeight: 54
                font.pixelSize: 24
                model: editor.options(fieldRow.modelData)
                currentIndex: editor.selectedIndex(fieldRow.modelData)
                displayText: currentIndex >= 0 ? editor.label(model[currentIndex]) : editor.tr("shared_unavailable_selection")
                enabled: !!editor.backend.sharedSettings.available && !editor.backend.sharedSettingsBusy &&
                         !editor.backend.sharedSettings.operation_pending &&
                         (editor.backend.sharedSettings.writable || []).indexOf(fieldRow.modelData) >= 0
                Accessible.name: editor.tr("shared_field_" + fieldRow.modelData)
                delegate: ItemDelegate {
                    required property var modelData
                    required property int index
                    width: choice.width
                    text: editor.label(modelData)
                    font.pixelSize: 24
                    highlighted: choice.highlightedIndex === index
                }
                onActivated: function(index) { editor.choose(fieldRow.modelData, model[index].value) }
            }
        }
    }
    Label {
        text: editor.tr("shared_pi_no_audio")
        color: "#b9b5d4"
        font.pixelSize: 18
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
    }
    Label {
        visible: !!editor.backend.sharedSettings.values && !editor.backend.sharedSettings.speaker_available &&
                 ["ha_speaker", "both"].indexOf((editor.backend.sharedSettings.values || {}).announcement_output) >= 0
        text: editor.tr("dj_announcement_speaker_unavailable")
        color: "#b9b5d4"
        font.pixelSize: 18
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
    }
    Label {
        visible: !!editor.backend.sharedSettings.values && !editor.backend.sharedSettings.voice_available
        text: editor.tr("shared_voice_unavailable")
        color: "#b9b5d4"
        font.pixelSize: 18
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
    }
    RowLayout {
        Layout.fillWidth: true
        Button {
            text: editor.tr("shared_reload")
            Layout.fillWidth: true
            Layout.minimumHeight: 54
            font.pixelSize: 22
            enabled: !editor.backend.sharedSettingsBusy
            onClicked: {
                editor.dirty = false
                editor.backend.pollSharedSettings()
            }
        }
        Button {
            text: editor.tr("shared_apply")
            Layout.fillWidth: true
            Layout.minimumHeight: 54
            font.pixelSize: 22
            enabled: !!editor.backend.sharedSettings.available && !editor.backend.sharedSettingsBusy &&
                     !editor.backend.sharedSettings.operation_pending && editor.editToken.length > 0 &&
                     (editor.dirty || editor.backend.sharedSettings.selection_required)
            onClicked: {
                var patch = {}
                var fields = editor.backend.sharedSettings.selection_required ? editor.fields : Object.keys(editor.changedFields)
                for (var i = 0; i < fields.length; ++i) patch[fields[i]] = editor.draft[fields[i]]
                patch._edit_token = editor.editToken
                editor.saving = true
                editor.backend.saveSharedSettings(patch)
            }
        }
    }
}
