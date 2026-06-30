import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: root
    modal: true
    focus: true
    width: 420
    padding: 0
    closePolicy: Popup.NoAutoClose

    property string title: ""
    property string message: ""
    property string acceptText: "OK"
    property string rejectText: "Отмена"
    property string neutralText: ""

    signal accepted()
    signal rejected()
    signal neutral()

    background: Rectangle {
        color: "#313338"
        radius: 10
        border.color: "#1E1F22"
        border.width: 1
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 22
        spacing: 16

        Label {
            text: root.title
            color: "#F2F3F5"
            font.pixelSize: 16
            font.bold: true
            Layout.fillWidth: true
            elide: Text.ElideRight
        }

        Label {
            text: root.message
            color: "#B5BAC1"
            font.pixelSize: 13
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Item { Layout.fillWidth: true }

            ActionButton {
                visible: root.neutralText.length > 0
                text: root.neutralText
                onClicked: { root.close(); root.neutral() }
            }
            ActionButton {
                text: root.rejectText
                onClicked: { root.close(); root.rejected() }
            }
            ActionButton {
                text: root.acceptText
                highlighted: true
                onClicked: { root.close(); root.accepted() }
            }
        }
    }
}
