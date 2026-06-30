import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    radius: 8
    color: "#2B2D31"
    border.color: "#1F2023"
    border.width: 1

    property string title: ""
    default property alias content: body.data

    implicitHeight: body.implicitHeight + 40
    Layout.fillWidth: true

    ColumnLayout {
        id: body
        anchors.fill: parent
        anchors.margins: 18
        spacing: 14

        Label {
            text: root.title
            color: "#949BA4"
            font.pixelSize: 11
            font.bold: true
            Layout.fillWidth: true
            elide: Text.ElideRight
        }
    }
}
