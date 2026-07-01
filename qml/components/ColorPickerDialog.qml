import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: root
    width: 430
    modal: true
    focus: true
    padding: 14
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    property string titleText: "Выбор цвета"
    property string selectedColor: "#00FF00"
    property string pendingColor: "#00FF00"
    property real hue: 120
    property real saturation: 1
    property real brightness: 1
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

    function clamp(value, minValue, maxValue) {
        return Math.max(minValue, Math.min(maxValue, value))
    }

    function hsvToRgb(h, s, v) {
        h = ((h % 360) + 360) % 360
        var c = v * s
        var x = c * (1 - Math.abs((h / 60) % 2 - 1))
        var m = v - c
        var r = 0
        var g = 0
        var b = 0
        if (h < 60) {
            r = c; g = x; b = 0
        } else if (h < 120) {
            r = x; g = c; b = 0
        } else if (h < 180) {
            r = 0; g = c; b = x
        } else if (h < 240) {
            r = 0; g = x; b = c
        } else if (h < 300) {
            r = x; g = 0; b = c
        } else {
            r = c; g = 0; b = x
        }
        return [
            Math.round((r + m) * 255),
            Math.round((g + m) * 255),
            Math.round((b + m) * 255)
        ]
    }

    function channelToHex(value) {
        var text = value.toString(16).toUpperCase()
        return text.length === 1 ? "0" + text : text
    }

    function hsvToHex(h, s, v) {
        var rgb = hsvToRgb(h, s, v)
        return "#" + channelToHex(rgb[0]) + channelToHex(rgb[1]) + channelToHex(rgb[2])
    }

    function rgbToHsv(hex) {
        var normalized = normalizeHex(hex)
        if (!normalized.length)
            return [120, 1, 1]
        var r = parseInt(normalized.substring(1, 3), 16) / 255
        var g = parseInt(normalized.substring(3, 5), 16) / 255
        var b = parseInt(normalized.substring(5, 7), 16) / 255
        var maxValue = Math.max(r, g, b)
        var minValue = Math.min(r, g, b)
        var delta = maxValue - minValue
        var h = 0
        if (delta > 0) {
            if (maxValue === r)
                h = 60 * (((g - b) / delta) % 6)
            else if (maxValue === g)
                h = 60 * (((b - r) / delta) + 2)
            else
                h = 60 * (((r - g) / delta) + 4)
        }
        if (h < 0)
            h += 360
        var s = maxValue === 0 ? 0 : delta / maxValue
        return [h, s, maxValue]
    }

    function syncCanvases() {
        svCanvas.requestPaint()
        hueCanvas.requestPaint()
    }

    function setPendingFromHsv() {
        pendingColor = hsvToHex(hue, saturation, brightness)
        hexField.text = pendingColor
        syncCanvases()
    }

    function setPendingFromHex(color) {
        var normalized = normalizeHex(color)
        if (!normalized.length)
            return
        var hsv = rgbToHsv(normalized)
        hue = hsv[0]
        saturation = hsv[1]
        brightness = hsv[2]
        pendingColor = normalized
        hexField.text = normalized
        syncCanvases()
    }

    function openWith(color) {
        var normalized = normalizeHex(color)
        pendingColor = normalized.length ? normalized : "#FFFFFF"
        selectedColor = pendingColor
        setPendingFromHex(pendingColor)
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
            Layout.preferredHeight: 180
            radius: 8
            border.color: "#404249"
            border.width: 1
            clip: true

            Canvas {
                id: svCanvas
                anchors.fill: parent
                onPaint: {
                    var ctx = getContext("2d")
                    ctx.clearRect(0, 0, width, height)
                    ctx.fillStyle = root.hsvToHex(root.hue, 1, 1)
                    ctx.fillRect(0, 0, width, height)

                    var whiteGradient = ctx.createLinearGradient(0, 0, width, 0)
                    whiteGradient.addColorStop(0, "rgba(255, 255, 255, 1)")
                    whiteGradient.addColorStop(1, "rgba(255, 255, 255, 0)")
                    ctx.fillStyle = whiteGradient
                    ctx.fillRect(0, 0, width, height)

                    var blackGradient = ctx.createLinearGradient(0, 0, 0, height)
                    blackGradient.addColorStop(0, "rgba(0, 0, 0, 0)")
                    blackGradient.addColorStop(1, "rgba(0, 0, 0, 1)")
                    ctx.fillStyle = blackGradient
                    ctx.fillRect(0, 0, width, height)
                }
            }

            Rectangle {
                width: 18
                height: 18
                radius: 9
                x: root.clamp(root.saturation * parent.width - width / 2, -width / 2, parent.width - width / 2)
                y: root.clamp((1 - root.brightness) * parent.height - height / 2, -height / 2, parent.height - height / 2)
                color: "transparent"
                border.color: "#F2F3F5"
                border.width: 2
            }

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.CrossCursor

                function pick(mouse) {
                    root.saturation = root.clamp(mouse.x / Math.max(1, width), 0, 1)
                    root.brightness = root.clamp(1 - mouse.y / Math.max(1, height), 0, 1)
                    root.setPendingFromHsv()
                }

                onPressed: function(mouse) { pick(mouse) }
                onPositionChanged: function(mouse) {
                    if (pressed)
                        pick(mouse)
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 24
            radius: 12
            color: "#111214"
            clip: true

            Canvas {
                id: hueCanvas
                anchors.fill: parent
                anchors.margins: 5
                onPaint: {
                    var ctx = getContext("2d")
                    ctx.clearRect(0, 0, width, height)
                    var gradient = ctx.createLinearGradient(0, 0, width, 0)
                    gradient.addColorStop(0.00, "#FF0000")
                    gradient.addColorStop(0.17, "#FFFF00")
                    gradient.addColorStop(0.33, "#00FF00")
                    gradient.addColorStop(0.50, "#00FFFF")
                    gradient.addColorStop(0.67, "#0000FF")
                    gradient.addColorStop(0.83, "#FF00FF")
                    gradient.addColorStop(1.00, "#FF0000")
                    ctx.fillStyle = gradient
                    ctx.fillRect(0, 0, width, height)
                }
            }

            Rectangle {
                width: 18
                height: 18
                radius: 9
                x: 5 + root.clamp(root.hue / 360 * hueCanvas.width - width / 2, -width / 2, hueCanvas.width - width / 2)
                y: 3
                color: root.hsvToHex(root.hue, 1, 1)
                border.color: "#F2F3F5"
                border.width: 2
            }

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor

                function pick(mouse) {
                    root.hue = root.clamp((mouse.x - 5) / Math.max(1, hueCanvas.width), 0, 1) * 360
                    root.setPendingFromHsv()
                }

                onPressed: function(mouse) { pick(mouse) }
                onPositionChanged: function(mouse) {
                    if (pressed)
                        pick(mouse)
                }
            }
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
                            root.setPendingFromHex(modelData)
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
                        root.setPendingFromHex(normalized)
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
