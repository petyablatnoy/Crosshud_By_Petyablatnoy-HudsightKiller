import QtQuick
import QtQuick.Controls

ScrollBar {
    id: root
    implicitWidth: 8
    implicitHeight: 8
    policy: ScrollBar.AsNeeded
    padding: 1
    minimumSize: 0.08

    background: Rectangle {
        radius: 4
        color: root.size < 1.0 ? "#1E1F22" : "transparent"
        opacity: root.size < 1.0 ? 0.75 : 0
    }

    contentItem: Rectangle {
        implicitWidth: 6
        implicitHeight: 6
        radius: 3
        color: root.pressed ? "#5865F2" : "#80848E"
        opacity: root.size < 1.0 ? 0.9 : 0
    }
}
