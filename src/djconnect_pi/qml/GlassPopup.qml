import QtQuick
import QtQuick.Controls

// Animate pixels, not Popup lifecycle: opened/closed and owner fences stay immediate.
Popup {
    id: popup
    property real presentationProgress: 1
    NumberAnimation {
        id: presentation
        target: popup; property: "presentationProgress"
        from: 0; to: 1
        duration: GlassStyle.motionEnabled ? GlassStyle.popupDuration : 0
        easing.type: Easing.OutCubic
    }
    Connections {
        target: popup
        function onAboutToShow() { presentation.restart() }
        function onAboutToHide() { presentation.stop(); popup.presentationProgress = 1 }
    }
    Binding { target: popup.background; property: "opacity"; value: popup.presentationProgress; when: !!popup.background }
    Binding { target: popup.background; property: "scale"; value: 0.97 + 0.03 * popup.presentationProgress; when: !!popup.background }
    Binding { target: popup.background; property: "transformOrigin"; value: Item.Top; when: !!popup.background }
    Binding { target: popup.contentItem; property: "opacity"; value: popup.presentationProgress; when: !!popup.contentItem }
    Binding { target: popup.contentItem; property: "scale"; value: 0.97 + 0.03 * popup.presentationProgress; when: !!popup.contentItem }
    Binding { target: popup.contentItem; property: "transformOrigin"; value: Item.Top; when: !!popup.contentItem }
}
