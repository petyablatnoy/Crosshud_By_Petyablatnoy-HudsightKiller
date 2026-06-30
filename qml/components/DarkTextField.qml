import QtQuick
import QtQuick.Controls

TextField {
    id: control
    implicitHeight: 30
    color: "#F2F3F5"
    placeholderTextColor: "#949BA4"
    selectedTextColor: "#FFFFFF"
    selectionColor: "#5865F2"
    font.pixelSize: 12
    leftPadding: 10
    rightPadding: 10

    background: Rectangle {
        color: "#1E1F22"
        radius: 6
        border.color: control.activeFocus ? "#5865F2" : "#404249"
        border.width: 1
    }
}
