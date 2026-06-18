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
        spacing: 10

        Image {
            source: "app-icon.png"
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 64
            Layout.preferredHeight: 64
            fillMode: Image.PreserveAspectFit
            smooth: true
            mipmap: true
        }

        Text {
            text: updater.title
            color: "#ffffff"
            font.pixelSize: 34
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

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 68
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
                    Layout.preferredHeight: 26

                    background: Rectangle {
                        color: "#33112643"
                        radius: 13
                        border.color: "#6248d6"
                        border.width: 1
                    }

                    contentItem: Item {
                        Rectangle {
                            width: updateProgressBar.visualPosition * parent.width
                            height: parent.height
                            radius: 13
                            gradient: Gradient {
                                orientation: Gradient.Horizontal
                                GradientStop { position: 0.0; color: "#ff5a2e" }
                                GradientStop { position: 0.55; color: "#d433ff" }
                                GradientStop { position: 1.0; color: "#7c3cff" }
                            }
                        }
                    }
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
            id: detailsButton
            text: updater.detailsOpen ? "Details verbergen" : "Meer details"
            font.pixelSize: 18
            font.bold: true
            Layout.fillWidth: true
            Layout.preferredHeight: 46
            onClicked: updater.toggleDetails()

            background: Rectangle {
                radius: 8
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: detailsButton.down ? "#df4f30" : "#ff6a45" }
                    GradientStop { position: 0.55; color: detailsButton.down ? "#b72bdc" : "#d433ff" }
                    GradientStop { position: 1.0; color: detailsButton.down ? "#6332d6" : "#7c3cff" }
                }
                border.color: "#c7b9ff"
                border.width: 1
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
            Layout.preferredHeight: visible ? 190 : 0
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
