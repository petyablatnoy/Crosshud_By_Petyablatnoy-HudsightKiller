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
        Layout.preferredWidth: 170
        onMoved: root.bridge.setSetting(root.settingKey, value / root.valueFactor)
    }
}
