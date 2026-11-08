import QtQuick
import QtQuick.Layouts

GlassSurface {
    id: dock
    objectName: "searchKeyboardDock"
    required property var backend
    required property var target
    property string keyboardName: "searchTouchKeyboard"
    signal edited()
    signal submitted()
    signal dismissed()
    readonly property bool compact: width < 900
    implicitHeight: keys.implicitHeight + 2 * inset
    readonly property int inset: compact ? 8 : 16
    radius: compact ? 18 : 30
    elevated: true
    TouchKeyboard {
        id: keys
        objectName: dock.keyboardName
        anchors.fill: parent
        anchors.margins: dock.inset
        backend: dock.backend
        target: dock.target
        docked: true
        keyHeight: dock.compact ? 44 : 80
        keyFontSize: dock.compact ? 19 : 27
        keyGap: dock.compact ? 4 : 8
        onEdited: dock.edited()
        onSubmitted: dock.submitted()
        onDismissed: dock.dismissed()
    }
}
