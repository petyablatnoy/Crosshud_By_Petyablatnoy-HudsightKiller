import QtQuick
import QtQuick.Controls

Item {
    id: root
    implicitWidth: compact ? 38 : Math.max(92, label.implicitWidth + 28)
    implicitHeight: compact ? 28 : 30
    opacity: enabled ? 1.0 : 0.45

    property string text: ""
    property bool compact: false
    property bool highlighted: false
    property bool danger: false
    signal clicked()

    Rectangle {
        anchors.fill: parent
        radius: 6
        color: {
            if (mouse.pressed)
                return root.danger ? "#A1282B" : (root.highlighted ? "#4752C4" : "#404249")
            if (mouse.containsMouse)
                return root.danger ? "#C9363A" : (root.highlighted ? "#5865F2" : "#35373C")
            return root.danger ? "#ED4245" : (root.highlighted ? "#5865F2" : "#2B2D31")
        }
        border.width: root.highlighted || root.danger ? 0 : 1
        border.color: "#404249"

        Behavior on color { ColorAnimation { duration: 140 } }
    }

    Label {
        id: label
        anchors.centerIn: parent
        width: parent.width - 12
        text: root.text
        color: "#F2F3F5"
        font.pixelSize: root.compact ? 16 : 12
        font.bold: true
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        enabled: root.enabled
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }
}
