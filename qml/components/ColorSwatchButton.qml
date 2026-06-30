import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

RowLayout {
    id: root
    spacing: 8

    property var bridge
    property string settingKey: ""
    property var swatches: ["#00FF00", "#FFFFFF", "#FF3131", "#5865F2", "#FFD43B", "#00D1FF"]
    signal customRequested(string settingKey)

    Repeater {
        model: root.swatches
        delegate: Rectangle {
            width: 24
            height: 24
            radius: 5
            color: modelData
            border.width: {
                bridge.revision
                return bridge.getSetting(root.settingKey) === modelData ? 2 : 1
            }
            border.color: {
                bridge.revision
                return bridge.getSetting(root.settingKey) === modelData ? "#F2F3F5" : "#404249"
            }

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: root.bridge.setSetting(root.settingKey, modelData)
            }
        }
    }

    ActionButton {
        text: "..."
        compact: true
        onClicked: root.customRequested(root.settingKey)
    }
}
