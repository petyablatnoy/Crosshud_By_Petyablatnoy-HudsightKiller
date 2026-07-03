import QtQuick
import QtQuick.Layouts

Rectangle {
    id: root
    Layout.preferredWidth: 56
    Layout.fillHeight: true
    color: "transparent"
    z: 30

    property var bridge
    property int currentPage: 0
    property bool powerMenuOpen: false

    signal pageSelected(int page)
    signal saveRequested()
    signal resetRequested()
    signal powerRequested()

    Rectangle {
        anchors.fill: parent
        color: "#2B2D31"
        topLeftRadius: 16
        bottomLeftRadius: 16
        topRightRadius: 0
        bottomRightRadius: 0
        antialiasing: true
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.topMargin: 12
        anchors.bottomMargin: 12
        spacing: 0

        ColumnLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignHCenter
            spacing: 6

            IconButton {
                Layout.alignment: Qt.AlignHCenter
                iconSource: root.bridge.iconUrl("crosshair.svg")
                tooltipText: "Прицел"
                selected: root.currentPage === 0
                onClicked: root.pageSelected(0)
            }
            IconButton {
                Layout.alignment: Qt.AlignHCenter
                iconSource: root.bridge.iconUrl("settings.svg")
                tooltipText: "Система"
                selected: root.currentPage === 1
                onClicked: root.pageSelected(1)
            }
            IconButton {
                Layout.alignment: Qt.AlignHCenter
                iconSource: root.bridge.iconUrl("layout-grid.svg")
                tooltipText: "Кастомный прицел"
                selected: root.currentPage === 2
                onClicked: root.pageSelected(2)
            }
        }

        Item { Layout.fillHeight: true }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignHCenter
            spacing: 6

            IconButton {
                Layout.alignment: Qt.AlignHCenter
                iconSource: root.bridge.iconUrl("save.svg")
                tooltipText: root.bridge.dirty ? "Сохранить настройки" : "Настройки сохранены"
                selected: root.bridge.dirty
                onClicked: root.saveRequested()
            }
            IconButton {
                Layout.alignment: Qt.AlignHCenter
                iconSource: root.bridge.iconUrl("rotate-ccw.svg")
                tooltipText: "Сбросить несохраненное"
                onClicked: root.resetRequested()
            }
            IconButton {
                Layout.alignment: Qt.AlignHCenter
                iconSource: root.bridge.iconUrl("power.svg")
                tooltipText: "Питание"
                tooltipEnabled: !root.powerMenuOpen
                onClicked: root.powerRequested()
            }
        }
    }
}
