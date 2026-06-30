import QtQuick
import QtQuick.Controls

ScrollBar {
    id: root
    implicitWidth: 8
    implicitHeight: 8
    policy: ScrollBar.AsNeeded

    background: Rectangle {
        radius: 4
        color: "#1E1F22"
        opacity: 0.45
    }

    contentItem: Rectangle {
        radius: 4
        color: root.pressed ? "#B5BAC1" : "#80848E"
        opacity: root.size < 1.0 ? 0.9 : 0
    }
}
