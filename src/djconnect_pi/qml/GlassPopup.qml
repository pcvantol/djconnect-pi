import QtQuick
import QtQuick.Controls

// Presentation only. Owners retain their immediate aboutToHide revocation.
Popup {
    id: popup
    property bool animateExit: true
    transformOrigin: Item.Top
    enter: Transition {
        ParallelAnimation {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: GlassStyle.motionEnabled ? GlassStyle.popupDuration : 0; easing.type: Easing.OutCubic }
            NumberAnimation { property: "scale"; from: GlassStyle.motionEnabled ? 0.97 : 1; to: 1; duration: GlassStyle.motionEnabled ? GlassStyle.popupDuration : 0; easing.type: Easing.OutCubic }
        }
    }
    exit: Transition {
        ParallelAnimation {
            NumberAnimation { property: "opacity"; to: 0; duration: popup.animateExit && GlassStyle.motionEnabled ? GlassStyle.pressDuration : 0; easing.type: Easing.OutCubic }
            NumberAnimation { property: "scale"; to: GlassStyle.motionEnabled ? 0.985 : 1; duration: popup.animateExit && GlassStyle.motionEnabled ? GlassStyle.pressDuration : 0; easing.type: Easing.OutCubic }
        }
    }
}
