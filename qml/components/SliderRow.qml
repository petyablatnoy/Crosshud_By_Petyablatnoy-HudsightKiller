import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

RowLayout {
    id: root
    spacing: 14
    Layout.fillWidth: true

    property var bridge
    property string label: ""
    property string settingKey: ""
    property real from: 0
    property real to: 100
    property real stepSize: 1
    property real valueFactor: 1
    property string suffix: ""

    function settingValue() {
        bridge.revision
        return Number(bridge.getSetting(settingKey)) * valueFactor
    }

    Label {
        text: root.label
        color: "#F2F3F5"
        font.pixelSize: 13
        Layout.fillWidth: true
        elide: Text.ElideRight
    }

    Label {
        text: Math.round(slider.value) + root.suffix
        color: "#DBDEE1"
        font.bold: true
        horizontalAlignment: Text.AlignRight
        Layout.preferredWidth: 46
    }

    Slider {
        id: slider
        from: root.from
        to: root.to
        stepSize: root.stepSize
        value: root.settingValue()
        padding: 0
        implicitHeight: 28
        Layout.preferredWidth: 170
        onMoved: root.bridge.setSetting(root.settingKey, value / root.valueFactor)

        background: Item {
            x: slider.leftPadding + sliderHandle.width / 2
            y: slider.topPadding + Math.round((slider.availableHeight - height) / 2)
            width: slider.availableWidth - sliderHandle.width
            height: 8

            Rectangle {
                anchors.fill: parent
                radius: 4
                color: "#18191C"
            }

            Rectangle {
                width: slider.visualPosition * parent.width
                height: parent.height
                radius: 4
                color: "#5865F2"
            }
        }

        handle: Rectangle {
            id: sliderHandle
            x: slider.leftPadding + slider.visualPosition * (slider.availableWidth - width)
            y: slider.topPadding + Math.round((slider.availableHeight - height) / 2)
            width: 16
            height: 16
            radius: 8
            color: slider.pressed ? "#F2F3F5" : "#B5BAC1"
            border.color: "#5865F2"
            border.width: 2
        }
    }
}
