import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: root
    width: 360
    modal: true
    focus: true
    padding: 14
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    property string titleText: "Выбор цвета"
    property string selectedColor: "#00FF00"
    property string pendingColor: "#00FF00"
    property var swatches: ["#00FF00", "#FFFFFF", "#FF3131", "#5865F2", "#FFD43B", "#00D1FF", "#000000", "#23A559", "#FAA61A", "#ED4245"]

    signal accepted(string color)

    x: parent ? Math.round((parent.width - width) / 2) : 0
    y: parent ? Math.round((parent.height - height) / 2) : 0

    function normalizeHex(value) {
        var text = String(value || "").trim().toUpperCase()
        if (text.length === 0)
            return ""
        if (text.charAt(0) !== "#")
            text = "#" + text
        if (/^#[0-9A-F]{8}$/.test(text))
            text = "#" + text.substring(text.length - 6)
        return /^#[0-9A-F]{6}$/.test(text) ? text : ""
    }

    function openWith(color) {
        var normalized = normalizeHex(color)
        pendingColor = normalized.length ? normalized : "#FFFFFF"
        selectedColor = pendingColor
        hexField.text = pendingColor
        open()
        hexField.forceActiveFocus()
        hexField.selectAll()
    }

    function commit() {
        var normalized = normalizeHex(hexField.text)
        if (!normalized.length)
            return
        selectedColor = normalized
        pendingColor = normalized
        accepted(normalized)
        close()
    }

    Overlay.modal: Rectangle {
        color: "#000000"
        opacity: 0.35
    }

    background: Rectangle {
        radius: 10
        color: "#1E1F22"
        border.color: "#404249"
        border.width: 1
    }

    contentItem: ColumnLayout {
        id: content
        spacing: 14

        RowLayout {
            Layout.fillWidth: true

            Label {
                text: root.titleText
                color: "#F2F3F5"
                font.pixelSize: 13
                font.bold: true
                Layout.fillWidth: true
                elide: Text.ElideRight
            }

            ActionButton {
                text: "×"
                compact: true
                onClicked: root.close()
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 72
            radius: 8
            color: root.pendingColor
            border.color: "#404249"
            border.width: 1
        }

        GridLayout {
            Layout.fillWidth: true
            columns: 10
            rowSpacing: 8
            columnSpacing: 8

            Repeater {
                model: root.swatches

                Rectangle {
                    width: 24
                    height: 24
                    radius: 5
                    color: modelData
                    border.width: root.pendingColor === modelData ? 2 : 1
                    border.color: root.pendingColor === modelData ? "#F2F3F5" : "#404249"

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            root.pendingColor = modelData
                            hexField.text = modelData
                        }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Label {
                text: "Hex"
                color: "#B5BAC1"
                font.pixelSize: 12
            }

            DarkTextField {
                id: hexField
                Layout.fillWidth: true
                text: root.pendingColor
                maximumLength: 7
                validator: RegularExpressionValidator { regularExpression: /^#?[0-9A-Fa-f]{0,6}$/ }
                onTextChanged: {
                    var normalized = root.normalizeHex(text)
                    if (normalized.length)
                        root.pendingColor = normalized
                }
                Keys.onReturnPressed: root.commit()
                Keys.onEnterPressed: root.commit()
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Item { Layout.fillWidth: true }

            ActionButton {
                text: "Отмена"
                onClicked: root.close()
            }

            ActionButton {
                text: "OK"
                highlighted: true
                enabled: root.normalizeHex(hexField.text).length > 0
                onClicked: root.commit()
            }
        }
    }
}
