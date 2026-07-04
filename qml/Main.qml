import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"
import "pages"

ApplicationWindow {
    id: app
    width: 1050
    height: 750
    minimumWidth: 1000
    minimumHeight: 650
    visible: false
    flags: Qt.FramelessWindowHint | Qt.Window
    color: "transparent"
    title: "CrossHud"

    property int currentPage: 0
    property var uiBridge: null
    property bool powerMenuOpen: false

    Component.onCompleted: uiBridge = bridge

    function saveClicked() {
        if (uiBridge.hasUnsavedCustomPixels())
            savePixelsDialog.open()
        else
            uiBridge.saveSettings(false)
    }

    onClosing: function(close) {
        close.accepted = false
        app.hide()
    }

    Connections {
        target: app.uiBridge
        function onToastRequested(text, kind) { toastLayer.show(text, kind) }
        function onExitSavePrompt() { exitSaveDialog.open() }
    }

    Timer {
        interval: 450
        running: true
        repeat: false
        onTriggered: app.uiBridge.showStartupWarnings()
    }

    Rectangle {
        id: shell
        anchors.fill: parent
        color: "#313338"
        radius: 16
        clip: true

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            Rectangle {
                id: titleBar
                Layout.fillWidth: true
                Layout.preferredHeight: 32
                color: "transparent"

                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.LeftButton
                    onPressed: app.startSystemMove()
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 16
                    anchors.rightMargin: 10
                    spacing: 8

                    Item {
                        Layout.preferredWidth: brandTitle.implicitWidth + 8 + authorLink.implicitWidth
                        Layout.preferredHeight: Math.max(brandTitle.implicitHeight, authorLink.implicitHeight)
                        Layout.alignment: Qt.AlignVCenter

                        Label {
                            id: brandTitle
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            text: "CROSSHUD"
                            color: "#F2F3F5"
                            font.pixelSize: 15
                            font.bold: true
                        }

                        Label {
                            id: authorLink
                            anchors.left: brandTitle.right
                            anchors.leftMargin: 8
                            anchors.baseline: brandTitle.baseline
                            text: "by PetyaBlatnoy"
                            color: authorMouse.containsMouse ? "#F2F3F5" : "#B5BAC1"
                            font.pixelSize: 10

                            MouseArea {
                                id: authorMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: app.uiBridge.openProjectPage()
                            }
                        }
                    }

                    Item {
                        Layout.fillWidth: true
                    }

                    WindowButton {
                        text: "–"
                        onClicked: app.showMinimized()
                    }

                    WindowButton {
                        text: "×"
                        danger: true
                        onClicked: app.hide()
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 0

                Sidebar {
                    bridge: app.uiBridge
                    currentPage: app.currentPage
                    powerMenuOpen: app.powerMenuOpen
                    onPageSelected: function(page) { app.currentPage = page }
                    onSaveRequested: app.saveClicked()
                    onResetRequested: app.uiBridge.resetSettings()
                    onPowerRequested: app.powerMenuOpen = !app.powerMenuOpen
                }

                StackLayout {
                    id: pages
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    currentIndex: app.currentPage
                    z: 0

                    AimPage { bridge: app.uiBridge }
                    SystemPage { bridge: app.uiBridge }
                    CustomPage { bridge: app.uiBridge }
                }
            }
        }

        Rectangle {
            anchors.fill: parent
            z: 1000
            radius: shell.radius
            color: "transparent"
            border.color: "#1E1F22"
            border.width: 1
            antialiasing: true
        }
    }

    MouseArea {
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 6
        cursorShape: Qt.SizeHorCursor
        onPressed: app.startSystemResize(Qt.RightEdge)
    }

    MouseArea {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 6
        cursorShape: Qt.SizeHorCursor
        onPressed: app.startSystemResize(Qt.LeftEdge)
    }

    MouseArea {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 6
        cursorShape: Qt.SizeVerCursor
        onPressed: app.startSystemResize(Qt.BottomEdge)
    }

    MouseArea {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        width: 12
        height: 12
        cursorShape: Qt.SizeFDiagCursor
        onPressed: app.startSystemResize(Qt.RightEdge | Qt.BottomEdge)
    }

    ToastLayer {
        id: toastLayer
        anchors.fill: parent
    }

    Item {
        id: powerMenuLayer
        anchors.fill: parent
        z: 20
        visible: app.powerMenuOpen

        MouseArea {
            anchors.fill: parent
            onClicked: app.powerMenuOpen = false
        }

        Rectangle {
            id: powerMenu
            x: 64
            y: app.height - height - 18
            width: 178
            height: 84
            radius: 8
            color: "#1E1F22"
            border.color: "#404249"
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 8

                ActionButton {
                    text: "Свернуть"
                    Layout.fillWidth: true
                    onClicked: {
                        app.powerMenuOpen = false
                        app.hide()
                    }
                }

                ActionButton {
                    text: "Выйти"
                    danger: true
                    Layout.fillWidth: true
                    onClicked: {
                        app.powerMenuOpen = false
                        app.uiBridge.requestExit()
                    }
                }
            }
        }
    }

    ConfirmDialog {
        id: savePixelsDialog
        x: Math.round((app.width - width) / 2)
        y: Math.round((app.height - height) / 2)
        title: "Сохранение настроек"
        message: "Пиксельный прицел изменен. Сохранить его вместе с настройками?"
        acceptText: "Сохранить прицел"
        neutralText: "Не сохранять"
        rejectText: "Отмена"
        onAccepted: app.uiBridge.saveSettings(true)
        onNeutral: app.uiBridge.saveSettings(false)
    }

    ConfirmDialog {
        id: exitSaveDialog
        x: Math.round((app.width - width) / 2)
        y: Math.round((app.height - height) / 2)
        title: "Выход из CrossHud"
        message: "Есть несохраненные настройки. Сохранить их перед выходом?"
        acceptText: "Сохранить"
        neutralText: "Выйти без сохранения"
        rejectText: "Отмена"
        onAccepted: app.uiBridge.confirmExit(true, true)
        onNeutral: app.uiBridge.confirmExit(true, false)
        onRejected: app.uiBridge.confirmExit(false, false)
    }
}
