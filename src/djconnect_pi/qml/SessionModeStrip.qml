import QtQuick
import QtQuick.Layouts
import "BrandTheme.js" as BrandTheme
import "MoodTheme.js" as MoodTheme

GlassSurface {
    id: modeSwitch
    objectName: inVibeScape ? "vibeScapeModeStrip" : "sessionModeStrip"
    required property var translate
    required property string mood
    property bool forecastAvailable: false
    property bool vibeScapeAvailable: false
    property bool showingForecast: false
    property bool inVibeScape: false
    function focusFlow() { flowButton.forceActiveFocus(Qt.TabFocusReason) }
    signal flowRequested()
    signal forecastRequested()
    signal vibeScapeRequested()
    readonly property var selectionStyle: MoodTheme.sessionSelection(mood)
    readonly property color selectedFill: {
        var tint = Qt.color(selectionStyle.tint)
        return selectionStyle.filled ? Qt.rgba(tint.r, tint.g, tint.b, 0.9) : "transparent"
    }
    width: Math.min(420, Math.max(0, parent.width - 40))
    height: 64
    radius: height / 2
    RowLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 4
        GlassButton {
            id: flowButton
            objectName: modeSwitch.inVibeScape ? "vibeScapeFlow" : "sessionFlowMode"; text: modeSwitch.translate("session_flow")
            Layout.fillWidth: true; Layout.preferredWidth: 1; Layout.preferredHeight: 48; padding: 8
            checked: !modeSwitch.inVibeScape && !modeSwitch.showingForecast
            tint: modeSwitch.selectionStyle.tint; selectionFill: modeSwitch.selectedFill
            foregroundColor: checked ? modeSwitch.selectionStyle.foreground : BrandTheme.colors.muted
            onClicked: modeSwitch.flowRequested()
        }
        GlassButton {
            objectName: modeSwitch.inVibeScape ? "vibeScapeForecast" : "sessionForecastMode"
            visible: modeSwitch.forecastAvailable; text: modeSwitch.translate("session_forecast_tab")
            Layout.fillWidth: true; Layout.preferredWidth: 1; Layout.preferredHeight: 48; padding: 8
            checked: !modeSwitch.inVibeScape && modeSwitch.showingForecast
            tint: modeSwitch.selectionStyle.tint; selectionFill: modeSwitch.selectedFill
            foregroundColor: checked ? modeSwitch.selectionStyle.foreground : BrandTheme.colors.muted
            onClicked: modeSwitch.forecastRequested()
        }
        GlassButton {
            objectName: modeSwitch.inVibeScape ? "vibeScapeSelectedMode" : "sessionVibeScapeMode"
            visible: modeSwitch.vibeScapeAvailable
            text: modeSwitch.translate("vibescape_title")
            checked: modeSwitch.inVibeScape
            tint: modeSwitch.selectionStyle.tint; selectionFill: modeSwitch.selectedFill
            foregroundColor: checked ? modeSwitch.selectionStyle.foreground : BrandTheme.colors.muted
            Layout.fillWidth: true; Layout.preferredWidth: 1; Layout.preferredHeight: 48; padding: 8
            onClicked: modeSwitch.vibeScapeRequested()
        }
    }
}
