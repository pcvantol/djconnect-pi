import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

Window {
    id: updateProgressRoot
    width: wallProfile ? Screen.width : 720
    height: wallProfile ? Screen.height : 720
    visible: true
    color: "#070b16"
    title: "DJConnect Update"
    visibility: startWindowed ? Window.Windowed : Window.FullScreen
    property bool rebootConfirmOpen: false
    property bool wallProfile: updater.releaseProfile === "pi5-arm64"
    property bool liquidGlassEnabled: wallProfile
    property real typeScale: wallProfile ? Math.min(width / 900, height / 1440) : 1
    property real contentWidth: wallProfile ? Math.min(width - 128, 920) : Math.min(width - 56, 600)
    opacity: 0

    Component.onCompleted: updateEntrance.start()

    NumberAnimation {
        id: updateEntrance
        target: updateProgressRoot
        property: "opacity"
        to: 1
        duration: updateProgressRoot.wallProfile ? 520 : 260
        easing.type: Easing.OutCubic
    }

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
        opacity: wallProfile ? 0.48 : 0.34
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "#2f8cff" }
            GradientStop { position: 0.5; color: "#00000000" }
            GradientStop { position: 1.0; color: "#8b5cf6" }
        }
        SequentialAnimation on opacity {
            running: updateProgressRoot.wallProfile
            loops: Animation.Infinite
            NumberAnimation { to: 0.62; duration: 3200; easing.type: Easing.InOutSine }
            NumberAnimation { to: 0.42; duration: 3200; easing.type: Easing.InOutSine }
        }
    }

    component AppBanner: Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: updateProgressRoot.wallProfile ? 190 : 132
        radius: updateProgressRoot.wallProfile ? 32 : 24
        color: updateProgressRoot.liquidGlassEnabled ? "#8a101426" : "#171029"
        border.color: updateProgressRoot.liquidGlassEnabled ? "#82ffffff" : "#3b2a63"
        border.width: 1
        clip: true
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: updateProgressRoot.liquidGlassEnabled ? "#8c12091d" : "#12091d" }
            GradientStop { position: 0.42; color: updateProgressRoot.liquidGlassEnabled ? "#7826103f" : "#26103f" }
            GradientStop { position: 0.72; color: updateProgressRoot.liquidGlassEnabled ? "#7037145a" : "#37145a" }
            GradientStop { position: 1.0; color: updateProgressRoot.liquidGlassEnabled ? "#88141125" : "#141125" }
        }

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 1
            height: updateProgressRoot.liquidGlassEnabled ? 2 : 0
            radius: height / 2
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: "#18ffffff" }
                GradientStop { position: 0.5; color: "#c8ffffff" }
                GradientStop { position: 1.0; color: "#18ffffff" }
            }
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: updateProgressRoot.wallProfile ? 38 : 28
            anchors.rightMargin: updateProgressRoot.wallProfile ? 38 : 28
            anchors.topMargin: updateProgressRoot.wallProfile ? 28 : 18
            anchors.bottomMargin: updateProgressRoot.wallProfile ? 28 : 18
            spacing: updateProgressRoot.wallProfile ? 30 : 22

            Image {
                source: "app-icon.png"
                Layout.preferredWidth: updateProgressRoot.wallProfile ? 128 : 84
                Layout.preferredHeight: updateProgressRoot.wallProfile ? 128 : 84
                fillMode: Image.PreserveAspectFit
                smooth: true
                mipmap: true
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6

                Text {
                    text: "DJConnect"
                    color: "#ffffff"
                    font.pixelSize: updateProgressRoot.wallProfile ? 52 : 38
                    font.bold: true
                    elide: Text.ElideRight
                    maximumLineCount: 1
                    Layout.fillWidth: true
                }

                Text {
                    text: updater.title
                    color: "#c9c3d8"
                    font.pixelSize: updateProgressRoot.wallProfile ? 26 : 20
                    font.bold: true
                    elide: Text.ElideRight
                    maximumLineCount: 1
                    Layout.fillWidth: true
                }
            }
        }
    }

    ColumnLayout {
        anchors.top: parent.top
        anchors.topMargin: updateProgressRoot.wallProfile ? 92 : 28
        anchors.horizontalCenter: parent.horizontalCenter
        width: updateProgressRoot.contentWidth
        spacing: updateProgressRoot.wallProfile ? 20 : 10

        AppBanner {}

        Text {
            text: updater.message
            color: "#d7e2e4"
            font.pixelSize: updateProgressRoot.wallProfile ? 24 : 17
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true
        }

        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: updateProgressRoot.wallProfile ? 42 : 18

            ColumnLayout {
                spacing: 2

                Text {
                    text: updater.t("current_version")
                    color: "#b9c9e8"
                    font.pixelSize: updateProgressRoot.wallProfile ? 16 : 12
                    font.bold: true
                }

                Text {
                    text: updater.currentVersion ? updater.currentVersion : "-"
                    color: "#ffffff"
                    font.pixelSize: updateProgressRoot.wallProfile ? 28 : 20
                    font.bold: true
                }
            }

            Text {
                text: "->"
                color: "#93c5fd"
                font.pixelSize: updateProgressRoot.wallProfile ? 28 : 20
                font.bold: true
                Layout.alignment: Qt.AlignBottom
            }

            ColumnLayout {
                spacing: 2

                Text {
                    text: updater.t("target_version")
                    color: "#b9c9e8"
                    font.pixelSize: updateProgressRoot.wallProfile ? 16 : 12
                    font.bold: true
                }

                Text {
                    text: updater.targetVersion ? updater.targetVersion : "-"
                    color: "#ffffff"
                    font.pixelSize: updateProgressRoot.wallProfile ? 28 : 20
                    font.bold: true
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6

                ProgressBar {
                    id: updateProgressBar
                    from: 0
                    to: 100
                    value: updater.progress
                    Layout.fillWidth: true
                    Layout.preferredHeight: updateProgressRoot.wallProfile ? 48 : 36

                    background: Rectangle {
                        color: "#2b174a"
                        radius: 18
                        border.color: "#8d75ff"
                        border.width: 2
                    }

                    contentItem: Item {
                        clip: true

                        Rectangle {
                            id: updateProgressFill
                            width: updateProgressBar.visualPosition * parent.width
                            height: parent.height
                            radius: 18
                            gradient: Gradient {
                                orientation: Gradient.Horizontal
                                GradientStop { position: 0.0; color: "#7c3cff" }
                                GradientStop { position: 0.5; color: "#d433ff" }
                                GradientStop { position: 1.0; color: "#f04dff" }
                            }

                            Behavior on width {
                                NumberAnimation {
                                    duration: updateProgressRoot.wallProfile ? 520 : 260
                                    easing.type: Easing.OutCubic
                                }
                            }
                        }

                        Rectangle {
                            id: updateProgressGlow
                            width: parent.width * 0.24
                            height: parent.height
                            radius: height / 2
                            opacity: updateProgressRoot.wallProfile ? 0.22 : 0
                            gradient: Gradient {
                                orientation: Gradient.Horizontal
                                GradientStop { position: 0.0; color: "#00ffffff" }
                                GradientStop { position: 0.5; color: "#eaffffff" }
                                GradientStop { position: 1.0; color: "#00ffffff" }
                            }

                            SequentialAnimation on x {
                                running: updateProgressRoot.wallProfile && updateProgressBar.value < 100
                                loops: Animation.Infinite
                                NumberAnimation { from: -updateProgressGlow.width; to: parent.width; duration: 1800; easing.type: Easing.InOutSine }
                                PauseAnimation { duration: 900 }
                            }
                        }
                    }
                }

                Text {
                    text: updater.tf("progress_percent", updater.progress.toString())
                    color: "#b9c9e8"
                    font.pixelSize: updateProgressRoot.wallProfile ? 28 : 22
                    font.bold: true
                    Layout.fillWidth: true
                }
            }
        }

        Button {
            id: detailsButton
            text: updater.detailsOpen ? updater.t("hide_update_details") : updater.t("update_details")
            font.pixelSize: updateProgressRoot.wallProfile ? 24 : 18
            font.bold: true
            Layout.fillWidth: true
            Layout.preferredHeight: updateProgressRoot.wallProfile ? 72 : 54
            onClicked: updater.toggleDetails()

            background: Rectangle {
                radius: Math.min(width, height) / 2
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: "#247fff" }
                    GradientStop { position: 0.58; color: "#7757ff" }
                    GradientStop { position: 1.0; color: "#c33cff" }
                }
                border.width: 0
                opacity: detailsButton.down ? 0.78 : 1.0
                scale: detailsButton.down ? 0.975 : 1
                Behavior on scale { NumberAnimation { duration: 110; easing.type: Easing.OutCubic } }
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
            Layout.preferredHeight: visible ? (updateProgressRoot.wallProfile ? 430 : 250) : 0
            spacing: 8

            Text {
                text: updater.t("installer_logs")
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
        id: updaterRebootButtonShell
        visible: !updater.detailsOpen
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: remoteAccessPanel.top
        anchors.bottomMargin: updateProgressRoot.wallProfile ? 20 : 12
        width: updateProgressRoot.contentWidth
        height: updateProgressRoot.wallProfile ? 72 : 54
        color: "transparent"

        Button {
            id: updaterRebootButton
            text: updater.t("reboot_device")
            font.pixelSize: updateProgressRoot.wallProfile ? 24 : 18
            font.bold: true
            anchors.fill: parent
            onClicked: updateProgressRoot.rebootConfirmOpen = true

            background: Rectangle {
                radius: 8
                color: updaterRebootButton.down ? "#7a2a20" : "#9f3a2e"
                border.color: "#f0a08f"
                border.width: 1
                scale: updaterRebootButton.down ? 0.975 : 1
                Behavior on scale { NumberAnimation { duration: 110; easing.type: Easing.OutCubic } }
            }

            contentItem: Text {
                text: updaterRebootButton.text
                color: "#ffffff"
                font: updaterRebootButton.font
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
            }
        }
    }

    Rectangle {
        id: remoteAccessPanel
        visible: !updater.detailsOpen
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: updateProgressRoot.wallProfile ? 48 : 24
        width: updateProgressRoot.contentWidth
        height: updateProgressRoot.wallProfile ? 148 : 116
        radius: updateProgressRoot.wallProfile ? 16 : 8
        color: "#99050816"
        border.color: "#42537c"
        border.width: 1

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: updateProgressRoot.wallProfile ? 20 : 12
            spacing: updateProgressRoot.wallProfile ? 8 : 4

            Text {
                text: updater.t("remote_viewing")
                color: "#f4f8f8"
                font.pixelSize: updateProgressRoot.wallProfile ? 18 : 14
                font.bold: true
                Layout.fillWidth: true
            }

            Text {
                text: updater.tf("ssh_label", updater.sshCommand)
                color: "#d7e2e4"
                font.family: "monospace"
                font.pixelSize: updateProgressRoot.wallProfile ? 17 : 14
                elide: Text.ElideRight
                Layout.fillWidth: true
            }

            Text {
                text: updater.tf("vnc_tunnel_label", updater.vncCommand)
                color: "#d7e2e4"
                font.family: "monospace"
                font.pixelSize: updateProgressRoot.wallProfile ? 17 : 14
                elide: Text.ElideRight
                Layout.fillWidth: true
            }

            Text {
                text: updater.vncInstruction
                color: "#b9c9e8"
                font.pixelSize: updateProgressRoot.wallProfile ? 16 : 13
                font.bold: true
                elide: Text.ElideRight
                Layout.fillWidth: true
            }
        }
    }

    Rectangle {
        visible: updateProgressRoot.rebootConfirmOpen
        anchors.fill: parent
        color: "#cc050816"
        z: 50

        MouseArea {
            anchors.fill: parent
            onClicked: updateProgressRoot.rebootConfirmOpen = false
        }

        Rectangle {
            anchors.centerIn: parent
            width: updateProgressRoot.wallProfile ? Math.min(parent.width - 128, 760) : Math.min(parent.width - 56, 520)
            implicitHeight: rebootConfirmContent.implicitHeight + (updateProgressRoot.wallProfile ? 72 : 44)
            radius: updateProgressRoot.wallProfile ? 20 : 8
            color: "#171029"
            border.color: "#f0a08f"
            border.width: 1

            ColumnLayout {
                id: rebootConfirmContent
                anchors.fill: parent
                anchors.margins: updateProgressRoot.wallProfile ? 36 : 22
                spacing: updateProgressRoot.wallProfile ? 22 : 14

                Text {
                    text: updater.t("reboot_confirm_title")
                    color: "#ffffff"
                    font.pixelSize: updateProgressRoot.wallProfile ? 38 : 28
                    font.bold: true
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                Text {
                    text: updater.t("reboot_confirm_message")
                    color: "#d7e2e4"
                    font.pixelSize: updateProgressRoot.wallProfile ? 24 : 18
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: updateProgressRoot.wallProfile ? 18 : 12

                    Button {
                        id: confirmRebootButton
                        text: updater.t("reboot_device")
                        font.pixelSize: updateProgressRoot.wallProfile ? 24 : 18
                        font.bold: true
                        Layout.fillWidth: true
                        Layout.preferredHeight: updateProgressRoot.wallProfile ? 72 : 54
                        onClicked: {
                            updateProgressRoot.rebootConfirmOpen = false
                            updater.rebootDevice()
                        }

                        background: Rectangle {
                            radius: 8
                            color: confirmRebootButton.down ? "#7a2a20" : "#9f3a2e"
                            border.color: "#f0a08f"
                            border.width: 1
                        }

                        contentItem: Text {
                            text: confirmRebootButton.text
                            color: "#ffffff"
                            font: confirmRebootButton.font
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }

                    Button {
                        id: cancelRebootButton
                        text: updater.t("cancel")
                        font.pixelSize: updateProgressRoot.wallProfile ? 24 : 18
                        font.bold: true
                        Layout.fillWidth: true
                        Layout.preferredHeight: updateProgressRoot.wallProfile ? 72 : 54
                        onClicked: updateProgressRoot.rebootConfirmOpen = false

                        background: Rectangle {
                            radius: 8
                            color: cancelRebootButton.down ? "#1f2a44" : "#26365b"
                            border.color: "#6c7eb2"
                            border.width: 1
                        }

                        contentItem: Text {
                            text: cancelRebootButton.text
                            color: "#ffffff"
                            font: cancelRebootButton.font
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }
            }
        }
    }
}
