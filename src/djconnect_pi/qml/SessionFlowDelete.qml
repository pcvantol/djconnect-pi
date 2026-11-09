import QtQuick
import QtQuick.Controls
import "BrandTheme.js" as BrandTheme

GlassButton {
    id: action
    required property Item card
    required property bool allowed
    required property string actionLabel
    property bool gesturesOnly: true
    property Item dismissalSurface: null
    property string scope: ""
    property bool revealed: false
    readonly property real revealWidth: revealed ? width + 8 : 0
    readonly property bool canReveal: gesturesOnly && allowed && enabled && card.visible

    signal deleteRequested()

    parent: gesturesOnly ? card : card.contentItem
    anchors.right: gesturesOnly && parent === card ? parent.right : undefined
    anchors.rightMargin: 4
    anchors.verticalCenter: gesturesOnly && parent === card ? parent.verticalCenter : undefined
    z: gesturesOnly ? 1 : 0
    visible: allowed && (!gesturesOnly || revealed)
    iconName: "trash"
    tint: BrandTheme.colors.danger
    Accessible.name: actionLabel

    onCanRevealChanged: if (!canReveal) dismiss()
    onScopeChanged: dismiss()
    onRevealedChanged: {
        if (!dismissalSurface) return
        if (revealed) {
            if (dismissalSurface.revealedFlowAction)
                dismissalSurface.revealedFlowAction.dismiss()
            dismissalSurface.revealedFlowAction = action
        } else if (dismissalSurface.revealedFlowAction === action) {
            dismissalSurface.revealedFlowAction = null
        }
    }
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
        onGrabChanged: (transition, point) => {
            if (transition !== PointerDevice.UngrabExclusive
                    || point.state !== EventPoint.Released || !action.canReveal) return
            const dx = point.scenePosition.x - point.scenePressPosition.x
            const dy = point.scenePosition.y - point.scenePressPosition.y
            if (Math.abs(dx) <= 1.5 * Math.abs(dy)) return
            if (dx < -64) action.revealed = true
            else if (dx > 32) action.revealed = false
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
