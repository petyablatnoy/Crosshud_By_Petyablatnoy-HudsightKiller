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
    property var uiBridge: bridge
    property bool powerMenuOpen: false

    function saveClicked() {
        if (bridge.hasUnsavedCustomPixels())
            savePixelsDialog.open()
        else
            bridge.saveSettings(false)
    }

    onClosing: function(close) {
        close.accepted = false
        app.hide()
    }

    Connections {
        target: bridge
        function onToastRequested(text, kind) { toastLayer.show(text, kind) }
        function onExitSavePrompt() { exitSaveDialog.open() }
    }

    Timer {
        interval: 450
        running: true
        repeat: false
        onTriggered: bridge.showStartupWarnings()
    }

    Timer {
        interval: 66
        running: {
            bridge.revision
            return !!bridge.getSetting("rainbow_mode") || !!bridge.getSetting("dynamic_color")
        }
        repeat: true
        onTriggered: bridge.advancePreviewAnimation()
    }

    Rectangle {
        id: shell
        anchors.fill: parent
        color: "#313338"
        radius: 16
        border.color: "#1E1F22"
        border.width: 1
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
                    spacing: 8

                    Label {
                        text: "CROSSHUD"
                        color: "#F2F3F5"
                        font.pixelSize: 13
                        font.bold: true
                        Layout.fillWidth: true
                    }

                    ActionButton {
                        text: "–"
                        compact: true
                        Layout.preferredWidth: 36
                        Layout.preferredHeight: 28
                        onClicked: app.showMinimized()
                    }

                    ActionButton {
                        text: "×"
                        compact: true
                        danger: true
                        Layout.preferredWidth: 36
                        Layout.preferredHeight: 28
                        onClicked: app.hide()
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 0

                Rectangle {
                    id: sidebar
                    Layout.preferredWidth: 56
                    Layout.fillHeight: true
                    color: "#2B2D31"
                    z: 30

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.topMargin: 12
                        anchors.bottomMargin: 12
                        spacing: 6

                        IconButton {
                            iconSource: bridge.iconUrl("crosshair.svg")
                            tooltipText: "Прицел"
                            selected: app.currentPage === 0
                            onClicked: app.currentPage = 0
                        }
                        IconButton {
                            iconSource: bridge.iconUrl("settings.svg")
                            tooltipText: "Система"
                            selected: app.currentPage === 1
                            onClicked: app.currentPage = 1
                        }
                        IconButton {
                            iconSource: bridge.iconUrl("layout-grid.svg")
                            tooltipText: "Кастомный прицел"
                            selected: app.currentPage === 2
                            onClicked: app.currentPage = 2
                        }

                        Item { Layout.fillHeight: true }

                        IconButton {
                            iconSource: bridge.iconUrl("save.svg")
                            tooltipText: bridge.dirty ? "Сохранить настройки" : "Настройки сохранены"
                            selected: bridge.dirty
                            onClicked: app.saveClicked()
                        }
                        IconButton {
                            iconSource: bridge.iconUrl("rotate-ccw.svg")
                            tooltipText: "Сбросить несохраненное"
                            onClicked: bridge.resetSettings()
                        }
                        IconButton {
                            id: powerButton
                            iconSource: bridge.iconUrl("power.svg")
                            tooltipText: "Питание"
                            onClicked: app.powerMenuOpen = !app.powerMenuOpen
                        }
                    }
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
                        bridge.requestExit()
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
        onAccepted: bridge.saveSettings(true)
        onNeutral: bridge.saveSettings(false)
    }

    ConfirmDialog {
        id: exitSaveDialog
        x: Math.round((app.width - width) / 2)
        y: Math.round((app.height - height) / 2)
        title: "Выход из CrossHud"
        message: "Пиксельный прицел изменен. Сохранить его перед выходом?"
        acceptText: "Сохранить прицел"
        neutralText: "Не сохранять"
        rejectText: "Отмена"
        onAccepted: bridge.confirmExit(true, true)
        onNeutral: bridge.confirmExit(true, false)
        onRejected: bridge.confirmExit(false, false)
    }
}
