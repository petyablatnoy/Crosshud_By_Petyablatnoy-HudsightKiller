import QtQuick
import QtQuick.Controls

Item {
    id: root
    width: 44
    height: 44

    property url iconSource
    property string tooltipText: ""
    property bool selected: false
    property bool tooltipEnabled: true
    signal clicked()

    Rectangle {
        anchors.fill: parent
        anchors.margins: 4
        radius: 8
        color: root.selected ? "#404249" : (mouse.containsMouse ? "#35373C" : "transparent")
        border.width: root.selected ? 1 : 0
        border.color: "#5865F2"

        Behavior on color { ColorAnimation { duration: 140 } }
    }

    Image {
        anchors.centerIn: parent
        width: 22
        height: 22
        source: root.iconSource
        opacity: root.selected ? 1.0 : 0.82
        fillMode: Image.PreserveAspectFit
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }

    Rectangle {
        id: tooltip
        x: root.width + 8
        y: Math.round((root.height - height) / 2)
        z: 1000
        width: tooltipLabel.implicitWidth + 18
        height: 30
        radius: 7
        color: "#1E1F22"
        border.color: "#404249"
        border.width: 1
        visible: root.tooltipEnabled && mouse.containsMouse && root.tooltipText.length > 0
        opacity: visible ? 1 : 0

        Behavior on opacity { NumberAnimation { duration: 120 } }

        Label {
            id: tooltipLabel
            anchors.centerIn: parent
            text: root.tooltipText
            color: "#F2F3F5"
            font.pixelSize: 12
            font.bold: true
            elide: Text.ElideRight
        }
    }
}
