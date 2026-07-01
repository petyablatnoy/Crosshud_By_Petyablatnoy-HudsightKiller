import QtQuick
import QtQuick.Controls

ScrollBar {
    id: root
    implicitWidth: 6
    implicitHeight: 6
    policy: ScrollBar.AsNeeded

    background: Rectangle {
        radius: 4
        color: "transparent"
    }

    contentItem: Rectangle {
        radius: 4
        color: root.pressed ? "#B5BAC1" : "#80848E"
        opacity: root.size < 1.0 ? 0.9 : 0
    }
}
