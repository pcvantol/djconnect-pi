import QtQuick
import "BrandTheme.js" as BrandTheme
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

BrandWindow {
    id: updateProgressRoot
    width: wallProfile ? Screen.width : 720
    height: wallProfile ? Screen.height : 720
    visible: true
    color: BrandTheme.colors.background
    title: "DJConnect Update"
    visibility: startWindowed ? Window.Windowed : Window.FullScreen
    property bool rebootConfirmOpen: false
    property bool wallProfile: updater.releaseProfile === "pi5-arm64"
    property bool liquidGlassEnabled: true
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
            GradientStop { position: 0.0; color: BrandTheme.colors.backgroundStart }
            GradientStop { position: 0.5; color: BrandTheme.colors.backgroundStart }
            GradientStop { position: 1.0; color: BrandTheme.colors.background }
        }
    }

    Rectangle {
        anchors.fill: parent
        opacity: wallProfile ? 0.48 : 0.34
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: BrandTheme.colors.cyan }
            GradientStop { position: 0.5; color: "#00000000" }
            GradientStop { position: 1.0; color: BrandTheme.colors.purple }
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
        color: updateProgressRoot.liquidGlassEnabled ? BrandTheme.alpha(BrandTheme.colors.surface, "8a") : BrandTheme.colors.background
        border.color: updateProgressRoot.liquidGlassEnabled ? "#82ffffff" : BrandTheme.colors.surfaceRaised
        border.width: 1
        clip: true
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: updateProgressRoot.liquidGlassEnabled ? BrandTheme.alpha(BrandTheme.colors.surface, "8c") : BrandTheme.colors.surface }
            GradientStop { position: 0.42; color: updateProgressRoot.liquidGlassEnabled ? BrandTheme.alpha(BrandTheme.colors.surface, "78") : BrandTheme.colors.surface }
            GradientStop { position: 0.72; color: updateProgressRoot.liquidGlassEnabled ? BrandTheme.alpha(BrandTheme.colors.surface, "70") : BrandTheme.colors.surface }
            GradientStop { position: 1.0; color: updateProgressRoot.liquidGlassEnabled ? BrandTheme.alpha(BrandTheme.colors.surface, "88") : BrandTheme.colors.surface }
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
                    color: BrandTheme.colors.text
                    font.pixelSize: updateProgressRoot.wallProfile ? 52 : 38
                    font.bold: true
                    elide: Text.ElideRight
                    maximumLineCount: 1
                    Layout.fillWidth: true
                }

                Text {
                    text: updater.title
                    color: BrandTheme.colors.muted
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
            color: BrandTheme.colors.muted
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
                    color: BrandTheme.colors.muted
                    font.pixelSize: updateProgressRoot.wallProfile ? 16 : 12
                    font.bold: true
                }

                Text {
                    text: updater.currentVersion ? updater.currentVersion : "-"
                    color: BrandTheme.colors.text
                    font.pixelSize: updateProgressRoot.wallProfile ? 28 : 20
                    font.bold: true
                }
            }

            Text {
                text: "->"
                color: BrandTheme.colors.cyan
                font.pixelSize: updateProgressRoot.wallProfile ? 28 : 20
                font.bold: true
                Layout.alignment: Qt.AlignBottom
            }

            ColumnLayout {
                spacing: 2

                Text {
                    text: updater.t("target_version")
                    color: BrandTheme.colors.muted
                    font.pixelSize: updateProgressRoot.wallProfile ? 16 : 12
                    font.bold: true
                }

                Text {
                    text: updater.targetVersion ? updater.targetVersion : "-"
                    color: BrandTheme.colors.text
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
                        color: BrandTheme.colors.surface
                        radius: 18
                        border.color: BrandTheme.colors.buttonStart
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
                                GradientStop { position: 0.0; color: BrandTheme.colors.buttonMid }
                                GradientStop { position: 0.5; color: BrandTheme.colors.buttonEnd }
                                GradientStop { position: 1.0; color: BrandTheme.colors.buttonEnd }
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
                                NumberAnimation { from: -updateProgressGlow.width; to: updateProgressGlow.parent.width; duration: 1800; easing.type: Easing.InOutSine }
                                PauseAnimation { duration: 900 }
                            }
                        }
                    }
                }

                Text {
                    text: updater.tf("progress_percent", updater.progress.toString())
                    color: BrandTheme.colors.muted
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
                    GradientStop { position: 0.0; color: BrandTheme.colors.buttonStart }
                    GradientStop { position: 0.58; color: BrandTheme.colors.buttonMid }
                    GradientStop { position: 1.0; color: BrandTheme.colors.buttonEnd }
                }
                border.width: 0
                opacity: detailsButton.down ? 0.78 : 1.0
                scale: detailsButton.down ? 0.975 : 1
                Behavior on scale { NumberAnimation { duration: 110; easing.type: Easing.OutCubic } }
            }

            contentItem: Text {
                text: detailsButton.text
                color: BrandTheme.colors.text
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
                color: BrandTheme.colors.text
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
                    color: BrandTheme.colors.muted
                    font.family: "monospace"
                    font.pixelSize: 13
                    background: Rectangle {
                        color: BrandTheme.alpha(BrandTheme.colors.surface, "cc")
                        radius: 8
                        border.color: BrandTheme.colors.border
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
                color: updaterRebootButton.down ? BrandTheme.colors.dangerPressed : BrandTheme.colors.dangerSurface
                border.color: BrandTheme.colors.danger
                border.width: 1
                scale: updaterRebootButton.down ? 0.975 : 1
                Behavior on scale { NumberAnimation { duration: 110; easing.type: Easing.OutCubic } }
            }

            contentItem: Text {
                text: updaterRebootButton.text
                color: BrandTheme.colors.text
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
        color: BrandTheme.alpha(BrandTheme.colors.surface, "99")
        border.color: BrandTheme.colors.border
        border.width: 1

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: updateProgressRoot.wallProfile ? 20 : 12
            spacing: updateProgressRoot.wallProfile ? 8 : 4

            Text {
                text: updater.t("remote_viewing")
                color: BrandTheme.colors.text
                font.pixelSize: updateProgressRoot.wallProfile ? 18 : 14
                font.bold: true
                Layout.fillWidth: true
            }

            Text {
                text: updater.tf("ssh_label", updater.sshCommand)
                color: BrandTheme.colors.muted
                font.family: "monospace"
                font.pixelSize: updateProgressRoot.wallProfile ? 17 : 14
                elide: Text.ElideRight
                Layout.fillWidth: true
            }

            Text {
                text: updater.tf("vnc_tunnel_label", updater.vncCommand)
                color: BrandTheme.colors.muted
                font.family: "monospace"
                font.pixelSize: updateProgressRoot.wallProfile ? 17 : 14
                elide: Text.ElideRight
                Layout.fillWidth: true
            }

            Text {
                text: updater.vncInstruction
                color: BrandTheme.colors.muted
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
        color: BrandTheme.alpha(BrandTheme.colors.surface, "cc")
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
            color: BrandTheme.colors.background
            border.color: BrandTheme.colors.danger
            border.width: 1

            ColumnLayout {
                id: rebootConfirmContent
                anchors.fill: parent
                anchors.margins: updateProgressRoot.wallProfile ? 36 : 22
                spacing: updateProgressRoot.wallProfile ? 22 : 14

                Text {
                    text: updater.t("reboot_confirm_title")
                    color: BrandTheme.colors.text
                    font.pixelSize: updateProgressRoot.wallProfile ? 38 : 28
                    font.bold: true
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                Text {
                    text: updater.t("reboot_confirm_message")
                    color: BrandTheme.colors.muted
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
                            color: confirmRebootButton.down ? BrandTheme.colors.dangerPressed : BrandTheme.colors.dangerSurface
                            border.color: BrandTheme.colors.danger
                            border.width: 1
                        }

                        contentItem: Text {
                            text: confirmRebootButton.text
                            color: BrandTheme.colors.text
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
                            color: cancelRebootButton.down ? BrandTheme.colors.surfaceRaised : BrandTheme.colors.surfaceRaised
                            border.color: BrandTheme.colors.border
                            border.width: 1
                        }

                        contentItem: Text {
                            text: cancelRebootButton.text
                            color: BrandTheme.colors.text
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
