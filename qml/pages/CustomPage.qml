import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

Item {
    id: root
    property var bridge
    property int gridSize: 101
    property int center: 50
    property int zoom: 6
    property string brushColor: "#00FF00"
    property var pixels: []
    property var templates: []
    property int selectedTemplate: -1

    function loadPixels() {
        try { pixels = JSON.parse(bridge.customPixelsJson) } catch (e) { pixels = [] }
        canvas.requestPaint()
    }

    function loadTemplates() {
        try { templates = JSON.parse(bridge.templatesJson) } catch (e) { templates = [] }
        templateBox.model = templates.map(function(t) { return t.name })
        if (selectedTemplate >= templates.length)
            selectedTemplate = templates.length - 1
    }

    function commitPixels() {
        bridge.setCustomPixelsJson(JSON.stringify(pixels))
        canvas.requestPaint()
    }

    function setting(key) {
        bridge.revision
        return bridge.getSetting(key)
    }

    function setPixel(gx, gy, color) {
        var px = gx - center
        var py = gy - center
        for (var i = pixels.length - 1; i >= 0; i--) {
            if (pixels[i][0] === px && pixels[i][1] === py)
                pixels.splice(i, 1)
        }
        pixels.push([px, py, color])
        commitPixels()
    }

    function erasePixel(gx, gy) {
        var px = gx - center
        var py = gy - center
        for (var i = pixels.length - 1; i >= 0; i--) {
            if (pixels[i][0] === px && pixels[i][1] === py)
                pixels.splice(i, 1)
        }
        commitPixels()
    }

    Component.onCompleted: {
        brushColor = bridge.getSetting("color")
        loadPixels()
        loadTemplates()
    }

    Connections {
        target: bridge
        function onRevisionChanged() { root.loadPixels() }
        function onTemplatesChanged() { root.loadTemplates() }
    }

    ColorPickerDialog {
        id: brushColorDialog
        objectName: "customColorDialog"
        titleText: "Цвет кисти"
        onAccepted: function(color) { root.brushColor = color }
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 18

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumWidth: 520
            spacing: 14

            SectionPanel {
                title: "ПИКСЕЛИ"
                Layout.fillHeight: true

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Пиксельный прицел"; color: "#F2F3F5"; Layout.fillWidth: true }
                    Toggle {
                        checked: !!root.setting("pixel_perfect")
                        onUserToggled: bridge.setSetting("pixel_perfect", checked)
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Цвет кисти"; color: "#F2F3F5"; Layout.fillWidth: true }
                    Repeater {
                        model: ["#00FF00", "#FFFFFF", "#FF3131", "#5865F2", "#FFD43B", "#00D1FF"]
                        delegate: Rectangle {
                            width: 24; height: 24; radius: 5
                            color: modelData
                            border.width: root.brushColor === modelData ? 2 : 1
                            border.color: root.brushColor === modelData ? "#F2F3F5" : "#404249"
                            MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.brushColor = modelData }
                        }
                    }
                    ActionButton {
                        text: "..."
                        compact: true
                        onClicked: {
                            brushColorDialog.openWith(root.brushColor)
                        }
                    }
                    ActionButton { text: "-"; compact: true; onClicked: root.zoom = Math.max(3, root.zoom - 1); }
                    Label { text: root.zoom + "x"; color: "#DBDEE1" }
                    ActionButton { text: "+"; compact: true; onClicked: root.zoom = Math.min(9, root.zoom + 1); }
                }

                Flickable {
                    id: editorFlick
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    contentWidth: canvas.width
                    contentHeight: canvas.height
                    boundsBehavior: Flickable.StopAtBounds
                    property bool smoothWheel: false

                    function clampX(value) {
                        return Math.max(0, Math.min(contentWidth - width, value))
                    }

                    function clampY(value) {
                        return Math.max(0, Math.min(contentHeight - height, value))
                    }

                    Behavior on contentX {
                        enabled: editorFlick.smoothWheel
                        NumberAnimation { duration: 90; easing.type: Easing.OutCubic }
                    }

                    Behavior on contentY {
                        enabled: editorFlick.smoothWheel
                        NumberAnimation { duration: 90; easing.type: Easing.OutCubic }
                    }

                    Timer {
                        id: wheelSmoothingReset
                        interval: 120
                        repeat: false
                        onTriggered: editorFlick.smoothWheel = false
                    }

                    Canvas {
                        id: canvas
                        width: root.gridSize * root.zoom
                        height: root.gridSize * root.zoom

                        onPaint: {
                            var ctx = getContext("2d")
                            ctx.fillStyle = "#1E1F22"
                            ctx.fillRect(0, 0, width, height)
                            if (root.zoom >= 4) {
                                ctx.strokeStyle = "#2B2D31"
                                ctx.lineWidth = 1
                                for (var i = 0; i <= root.gridSize; i++) {
                                    var p = i * root.zoom
                                    ctx.beginPath(); ctx.moveTo(p, 0); ctx.lineTo(p, height); ctx.stroke()
                                    ctx.beginPath(); ctx.moveTo(0, p); ctx.lineTo(width, p); ctx.stroke()
                                }
                            }
                            ctx.strokeStyle = "#5865F2"
                            ctx.lineWidth = 2
                            ctx.strokeRect(root.center * root.zoom, root.center * root.zoom, root.zoom, root.zoom)
                            for (var j = 0; j < root.pixels.length; j++) {
                                var item = root.pixels[j]
                                ctx.fillStyle = item[2]
                                ctx.fillRect((item[0] + root.center) * root.zoom + 1, (item[1] + root.center) * root.zoom + 1, root.zoom - 1, root.zoom - 1)
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
                            preventStealing: true
                            property real lastX: 0
                            property real lastY: 0

                            function apply(mouse) {
                                var gx = Math.floor(mouse.x / root.zoom)
                                var gy = Math.floor(mouse.y / root.zoom)
                                if (gx < 0 || gy < 0 || gx >= root.gridSize || gy >= root.gridSize)
                                    return
                                if (mouse.buttons & Qt.RightButton)
                                    root.erasePixel(gx, gy)
                                else
                                    root.setPixel(gx, gy, root.brushColor)
                            }

                            onPressed: function(mouse) {
                                lastX = mouse.x
                                lastY = mouse.y
                                if (mouse.button !== Qt.MiddleButton)
                                    apply(mouse)
                            }
                            onPositionChanged: function(mouse) {
                                if (mouse.buttons & Qt.MiddleButton) {
                                    editorFlick.smoothWheel = false
                                    editorFlick.contentX = editorFlick.clampX(editorFlick.contentX - (mouse.x - lastX))
                                    editorFlick.contentY = editorFlick.clampY(editorFlick.contentY - (mouse.y - lastY))
                                    lastX = mouse.x
                                    lastY = mouse.y
                                } else if (pressed) {
                                    apply(mouse)
                                }
                            }
                            onWheel: function(wheel) {
                                if (wheel.modifiers & Qt.ControlModifier) {
                                    root.zoom = Math.max(3, Math.min(9, root.zoom + (wheel.angleDelta.y > 0 ? 1 : -1)))
                                    wheel.accepted = true
                                    canvas.requestPaint()
                                    return
                                }
                                var dx = wheel.pixelDelta.x !== 0 ? -wheel.pixelDelta.x : -wheel.angleDelta.x / 120 * 58
                                var dy = wheel.pixelDelta.y !== 0 ? -wheel.pixelDelta.y : -wheel.angleDelta.y / 120 * 58
                                if ((wheel.modifiers & Qt.ShiftModifier) && Math.abs(dx) < 1) {
                                    dx = dy
                                    dy = 0
                                }
                                editorFlick.smoothWheel = true
                                editorFlick.contentX = editorFlick.clampX(editorFlick.contentX + dx)
                                editorFlick.contentY = editorFlick.clampY(editorFlick.contentY + dy)
                                wheelSmoothingReset.restart()
                                wheel.accepted = true
                            }
                        }
                    }

                }
            }
        }

        ColumnLayout {
            Layout.preferredWidth: 320
            Layout.minimumWidth: 320
            Layout.maximumWidth: 320
            Layout.fillHeight: true
            spacing: 14

            SectionPanel {
                title: "ШАБЛОНЫ"

                DarkComboBox {
                    id: templateBox
                    Layout.fillWidth: true
                    onActivated: root.selectedTemplate = currentIndex
                }

                DarkTextField {
                    id: templateName
                    Layout.fillWidth: true
                    placeholderText: "Имя шаблона"
                }

                RowLayout {
                    Layout.fillWidth: true
                    ActionButton { text: "Загрузить"; Layout.fillWidth: true; onClicked: bridge.loadTemplate(templateBox.currentIndex) }
                    ActionButton { text: "Сохранить"; Layout.fillWidth: true; highlighted: true; onClicked: bridge.saveTemplate(templateName.text) }
                }

                ActionButton {
                    text: "Удалить"
                    danger: true
                    Layout.fillWidth: true
                    onClicked: deleteDialog.open()
                }
            }
        }
    }

    ConfirmDialog {
        id: deleteDialog
        title: "Удаление"
        message: "Удалить выбранный шаблон?"
        acceptText: "Удалить"
        rejectText: "Отмена"
        onAccepted: bridge.deleteTemplate(templateBox.currentIndex)
    }
}
