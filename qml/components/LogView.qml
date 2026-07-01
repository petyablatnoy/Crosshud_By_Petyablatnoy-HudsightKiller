import QtQuick
import QtQuick.Controls

Rectangle {
    id: root
    radius: 6
    color: "#111214"
    border.color: "#1F2023"
    border.width: 1
    clip: true

    property string text: ""

    Flickable {
        id: flick
        anchors.fill: parent
        anchors.margins: 8
        clip: true
        contentWidth: logText.implicitWidth
        contentHeight: logText.implicitHeight
        boundsBehavior: Flickable.StopAtBounds

        Text {
            id: logText
            text: root.text
            color: "#DBDEE1"
            font.family: "Consolas"
            font.pixelSize: 11
            wrapMode: Text.NoWrap
        }
    }
}
