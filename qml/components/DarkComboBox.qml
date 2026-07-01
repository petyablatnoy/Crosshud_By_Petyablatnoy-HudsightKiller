import QtQuick
import QtQuick.Controls

ComboBox {
    id: control
    implicitHeight: 30
    font.pixelSize: 12

    delegate: ItemDelegate {
        width: control.width
        height: 30
        highlighted: control.highlightedIndex === index

        contentItem: Label {
            text: modelData
            color: "#F2F3F5"
            font.pixelSize: 12
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }

        background: Rectangle {
            color: highlighted ? "#404249" : "transparent"
            radius: 5
        }
    }

    indicator: Canvas {
        x: control.width - width - 10
        y: Math.round((control.height - height) / 2)
        width: 10
        height: 6
        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            ctx.strokeStyle = "#B5BAC1"
            ctx.lineWidth = 2
            ctx.beginPath()
            ctx.moveTo(1, 1)
            ctx.lineTo(width / 2, height - 1)
            ctx.lineTo(width - 1, 1)
            ctx.stroke()
        }
    }

    contentItem: Label {
        leftPadding: 10
        rightPadding: 28
        text: control.displayText
        color: "#F2F3F5"
        font.pixelSize: 12
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        color: "#1E1F22"
        radius: 6
        border.color: control.activeFocus ? "#5865F2" : "#404249"
        border.width: 1
    }

    popup: Popup {
        y: control.height + 4
        width: control.width
        implicitHeight: Math.min(contentItem.implicitHeight + 8, 240)
        padding: 4

        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ThemedScrollBar { active: true }
        }

        background: Rectangle {
            color: "#1E1F22"
            radius: 8
            border.color: "#404249"
            border.width: 1
        }
    }
}
