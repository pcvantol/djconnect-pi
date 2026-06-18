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
        anchors.top: parent.top
        anchors.topMargin: 28
        anchors.horizontalCenter: parent.horizontalCenter
        width: Math.min(parent.width - 56, 600)
        spacing: 10

        Image {
            source: "app-icon.png"
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 128
            Layout.preferredHeight: 128
            fillMode: Image.PreserveAspectFit
            smooth: true
            mipmap: true
        }

        Text {
            text: updater.title
            color: "#ffffff"
            font.pixelSize: 32
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true
        }

        Text {
            text: updater.message
            color: "#d7e2e4"
            font.pixelSize: 17
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true
        }

        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 18

            ColumnLayout {
                spacing: 2

                Text {
                    text: "Huidige versie"
                    color: "#b9c9e8"
                    font.pixelSize: 12
                    font.bold: true
                }

                Text {
                    text: updater.currentVersion ? updater.currentVersion : "-"
                    color: "#ffffff"
                    font.pixelSize: 20
                    font.bold: true
                }
            }

            Text {
                text: "->"
                color: "#93c5fd"
                font.pixelSize: 20
                font.bold: true
                Layout.alignment: Qt.AlignBottom
            }

            ColumnLayout {
                spacing: 2

                Text {
                    text: "Updaten naar"
                    color: "#b9c9e8"
                    font.pixelSize: 12
                    font.bold: true
                }

                Text {
                    text: updater.targetVersion ? updater.targetVersion : "-"
                    color: "#ffffff"
                    font.pixelSize: 20
                    font.bold: true
                }
            }
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
                    id: updateProgressBar
                    from: 0
                    to: 100
                    value: updater.progress
                    Layout.fillWidth: true
                    Layout.preferredHeight: 36

                    background: Rectangle {
                        color: "#2b174a"
                        radius: 18
                        border.color: "#8d75ff"
                        border.width: 2
                    }

                    contentItem: Item {
                        Rectangle {
                            width: updateProgressBar.visualPosition * parent.width
                            height: parent.height
                            radius: 18
                            gradient: Gradient {
                                orientation: Gradient.Horizontal
                                GradientStop { position: 0.0; color: "#7c3cff" }
                                GradientStop { position: 0.5; color: "#d433ff" }
                                GradientStop { position: 1.0; color: "#f04dff" }
                            }
                        }
                    }
                }

                Text {
                    text: "Voortgang: " + updater.progress + "%"
                    color: "#b9c9e8"
                    font.pixelSize: 22
                    font.bold: true
                    Layout.fillWidth: true
                }
            }
        }

        Button {
            id: detailsButton
            text: updater.detailsOpen ? "Details verbergen" : "Meer details"
            font.pixelSize: 18
            font.bold: true
            Layout.fillWidth: true
            Layout.preferredHeight: 54
            onClicked: updater.toggleDetails()

            background: Rectangle {
                radius: 8
                color: "#3b1677"
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: detailsButton.down ? "#5422a6" : "#6f35ff" }
                    GradientStop { position: 0.48; color: detailsButton.down ? "#8d21bf" : "#c02eff" }
                    GradientStop { position: 1.0; color: detailsButton.down ? "#4a168f" : "#8228f2" }
                }
                border.color: "#d8c8ff"
                border.width: 2
            }

            contentItem: Text {
                text: detailsButton.text
                color: "#ffffff"
                font: detailsButton.font
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }

        ColumnLayout {
            visible: updater.detailsOpen
            Layout.fillWidth: true
            Layout.preferredHeight: visible ? 250 : 0
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

    Rectangle {
        visible: !updater.detailsOpen
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 24
        width: Math.min(parent.width - 56, 600)
        height: 68
        radius: 8
        color: "#99050816"
        border.color: "#42537c"
        border.width: 1

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 4

            Text {
                text: "Remote meekijken"
                color: "#f4f8f8"
                font.pixelSize: 14
                font.bold: true
                Layout.fillWidth: true
            }

            Text {
                text: updater.deviceAddress + "  |  " + updater.sshCommand
                color: "#d7e2e4"
                font.family: "monospace"
                font.pixelSize: 16
                elide: Text.ElideRight
                Layout.fillWidth: true
            }
        }
    }
}
