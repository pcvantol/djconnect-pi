import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

Window {
    id: updateProgressRoot
    width: 720
    height: 720
    visible: true
    color: "#070b16"
    title: "DJConnect Update"
    visibility: startWindowed ? Window.Windowed : Window.FullScreen

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            orientation: Gradient.Vertical
            GradientStop { position: 0.0; color: "#24105c" }
            GradientStop { position: 0.5; color: "#0f2b68" }
            GradientStop { position: 1.0; color: "#070b16" }
        }
    }

    Rectangle {
        anchors.fill: parent
        opacity: 0.34
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "#2f8cff" }
            GradientStop { position: 0.5; color: "#00000000" }
            GradientStop { position: 1.0; color: "#8b5cf6" }
        }
    }

    ColumnLayout {
        anchors.centerIn: parent
        width: Math.min(parent.width - 56, 600)
        spacing: 16

        Image {
            source: "app-icon.png"
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 88
            Layout.preferredHeight: 88
            fillMode: Image.PreserveAspectFit
            smooth: true
            mipmap: true
        }

        Text {
            text: updater.title
            color: "#ffffff"
            font.pixelSize: 42
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true
        }

        Text {
            text: updater.message
            color: "#d7e2e4"
            font.pixelSize: 20
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 14

            BusyIndicator {
                running: true
                implicitWidth: 36
                implicitHeight: 36
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6

                ProgressBar {
                    from: 0
                    to: 100
                    value: updater.progress
                    Layout.fillWidth: true
                    Layout.preferredHeight: 18
                }

                Text {
                    text: "Voortgang: " + updater.progress + "%"
                    color: "#b9c9e8"
                    font.pixelSize: 16
                    font.bold: true
                    Layout.fillWidth: true
                }
            }
        }

        Button {
            text: updater.detailsOpen ? "Details verbergen" : "Meer details"
            font.pixelSize: 20
            Layout.fillWidth: true
            Layout.preferredHeight: 54
            onClicked: updater.toggleDetails()
        }

        ColumnLayout {
            visible: updater.detailsOpen
            Layout.fillWidth: true
            Layout.preferredHeight: visible ? 270 : 0
            spacing: 8

            Text {
                text: "Installer logs"
                color: "#f4f8f8"
                font.pixelSize: 18
                font.bold: true
                Layout.fillWidth: true
            }

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true

                TextArea {
                    id: updaterLogsArea
                    text: updater.logs
                    readOnly: true
                    wrapMode: TextEdit.WrapAnywhere
                    color: "#d7e2e4"
                    font.family: "monospace"
                    font.pixelSize: 13
                    background: Rectangle {
                        color: "#cc050816"
                        radius: 8
                        border.color: "#33405f"
                        border.width: 1
                    }
                    onTextChanged: Qt.callLater(function() { updaterLogsArea.cursorPosition = updaterLogsArea.length })
                }
            }
        }
    }
}
