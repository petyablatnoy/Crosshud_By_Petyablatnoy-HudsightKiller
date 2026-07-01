import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    radius: 8
    color: "#1E1F22"
    border.color: "#404249"
    border.width: 1
    Layout.preferredWidth: 340

    property var bridge

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 12

        Label {
            text: "ПРЕВЬЮ"
            color: "#949BA4"
            font.pixelSize: 11
            font.bold: true
            Layout.fillWidth: true
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: width
            Layout.maximumHeight: 340
            radius: 8
            color: "#111214"
            border.color: "#2B2D31"
            clip: true

            Canvas {
                anchors.fill: parent
                opacity: 0.55
                onPaint: {
                    var ctx = getContext("2d")
                    ctx.clearRect(0, 0, width, height)
                    ctx.strokeStyle = "#2B2D31"
                    ctx.lineWidth = 1
                    for (var x = 0; x < width; x += 16) {
                        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke()
                    }
                    for (var y = 0; y < height; y += 16) {
                        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke()
                    }
                }
            }

            Image {
                anchors.centerIn: parent
                width: parent.width
                height: parent.height
                source: "image://crosshair/preview/" + root.bridge.previewRevision
                sourceSize.width: 512
                sourceSize.height: 512
                cache: false
                fillMode: Image.PreserveAspectFit
            }
        }
    }
}
