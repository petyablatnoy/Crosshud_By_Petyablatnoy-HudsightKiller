import QtQuick

Item {
    id: root
    width: 42
    height: 26

    property bool checked: false
    signal userToggled(bool checked)

    Rectangle {
        anchors.fill: parent
        radius: 13
        color: root.checked ? "#23A559" : "#80848E"
        Behavior on color { ColorAnimation { duration: 160 } }
    }

    Rectangle {
        width: 18
        height: 18
        radius: 9
        y: 4
        x: root.checked ? 20 : 4
        color: "#FFFFFF"
        Behavior on x { NumberAnimation { duration: 160; easing.type: Easing.OutQuad } }
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: root.userToggled(!root.checked)
    }
}
