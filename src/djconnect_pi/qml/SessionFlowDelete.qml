import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "BrandTheme.js" as BrandTheme

GlassButton {
    id: action
    required property Item card
    required property bool allowed
    required property string actionLabel
    property bool gesturesOnly: true
    property string scope: ""
    property bool revealed: false
    readonly property bool canReveal: gesturesOnly && allowed && enabled && card.visible

    signal deleteRequested()

    visible: allowed && (!gesturesOnly || revealed)
    iconName: "trash"
    tint: BrandTheme.colors.danger
    Layout.alignment: gesturesOnly ? Qt.AlignRight : Qt.AlignLeft
    Accessible.name: actionLabel

    onCanRevealChanged: if (!canReveal) dismiss()
    onScopeChanged: dismiss()
    onClicked: requestDelete()

    function dismiss() {
        revealed = false
        contextMenu.close()
    }

    function requestDelete() {
        if (!allowed || !enabled || !card.visible) return
        dismiss()
        deleteRequested()
    }

    DragHandler {
        parent: action.card
        target: null
        enabled: action.canReveal
        yAxis.enabled: false
        onActiveTranslationChanged: {
            if (!active || !action.canReveal) return
            if (activeTranslation.x <= -48) action.revealed = true
            if (activeTranslation.x >= 48) action.revealed = false
        }
    }

    TapHandler {
        parent: action.card
        enabled: action.canReveal
        onLongPressed: contextMenu.popup(card, point.position)
    }

    Menu {
        id: contextMenu
        objectName: "sessionFlowContextMenu"
        MenuItem {
            text: action.actionLabel
            onTriggered: action.requestDelete()
        }
    }
}
