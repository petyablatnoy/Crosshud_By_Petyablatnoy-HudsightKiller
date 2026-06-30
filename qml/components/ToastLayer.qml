import QtQuick
import QtQuick.Controls

Item {
    id: root
    anchors.fill: parent

    property string message: ""
    property string kind: "success"

    function show(text, toastKind) {
        message = text
        kind = toastKind
        toast.visible = true
        hideTimer.restart()
    }

    Rectangle {
        id: toast
        visible: false
        width: Math.min(420, root.width - 40)
        height: 48
        radius: 8
        color: "#111214"
        border.width: 1
        border.color: root.kind === "error" ? "#ED4245" : (root.kind === "warning" ? "#FAA61A" : "#23A559")
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 20
        opacity: visible ? 1 : 0

        Behavior on opacity { NumberAnimation { duration: 160 } }

        Label {
            anchors.fill: parent
            anchors.leftMargin: 16
            anchors.rightMargin: 16
            verticalAlignment: Text.AlignVCenter
            text: root.message
            color: "#F2F3F5"
            font.pixelSize: 13
            font.bold: true
            elide: Text.ElideRight
        }
    }

    Timer {
        id: hideTimer
        interval: 2600
        onTriggered: toast.visible = false
    }
}
