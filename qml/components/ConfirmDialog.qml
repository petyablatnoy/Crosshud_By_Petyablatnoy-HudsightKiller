import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: root
    modal: true
    focus: true
    width: 460
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

    Overlay.modal: Rectangle {
        radius: 16
        color: "#111214"
        opacity: 0.72
    }

    background: Rectangle {
        color: "#2B2D31"
        radius: 12
        border.color: "#404249"
        border.width: 1
    }

    contentItem: ColumnLayout {
        spacing: 18

        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
        }

        Label {
            text: root.title
            color: "#F2F3F5"
            font.pixelSize: 16
            font.bold: true
            Layout.fillWidth: true
            Layout.leftMargin: 24
            Layout.rightMargin: 24
            elide: Text.ElideRight
        }

        Label {
            text: root.message
            color: "#B5BAC1"
            font.pixelSize: 13
            lineHeight: 1.15
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
            Layout.leftMargin: 24
            Layout.rightMargin: 24
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 24
            Layout.rightMargin: 24
            spacing: 10

            ActionButton {
                visible: root.neutralText.length > 0
                text: root.neutralText
                Layout.fillWidth: true
                onClicked: { root.close(); root.neutral() }
            }

            ActionButton {
                text: root.rejectText
                Layout.fillWidth: true
                onClicked: { root.close(); root.rejected() }
            }

            ActionButton {
                text: root.acceptText
                highlighted: true
                Layout.fillWidth: true
                onClicked: { root.close(); root.accepted() }
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
        }
    }
}
