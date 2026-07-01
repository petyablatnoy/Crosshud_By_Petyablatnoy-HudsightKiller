import QtQuick
import QtQuick.Controls

Item {
    id: root
    implicitWidth: 32
    implicitHeight: 24

    property string text: ""
    property bool danger: false
    signal clicked()

    Rectangle {
        anchors.fill: parent
        radius: 6
        color: {
            if (mouse.pressed)
                return root.danger ? "#A1282B" : "#404249"
            if (mouse.containsMouse)
                return root.danger ? "#ED4245" : "#35373C"
            return "transparent"
        }
        border.width: mouse.containsMouse && !root.danger ? 1 : 0
        border.color: "#404249"

        Behavior on color { ColorAnimation { duration: 120 } }
    }

    Label {
        anchors.centerIn: parent
        text: root.text
        color: "#F2F3F5"
        font.pixelSize: root.text === "–" ? 16 : 13
        font.bold: true
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }
}
