import QtQuick
import QtQuick.Controls

Item {
    id: root
    width: 44
    height: 44

    property url iconSource
    property string tooltipText: ""
    property bool selected: false
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

    ToolTip.visible: mouse.containsMouse && root.tooltipText.length > 0
    ToolTip.delay: 450
    ToolTip.text: root.tooltipText
}
