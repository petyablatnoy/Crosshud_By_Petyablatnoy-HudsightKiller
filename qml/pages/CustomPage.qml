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
    readonly property int minZoom: 6
    readonly property int maxZoom: 12
    property string brushColor: "#00FF00"
    property var pixels: []
    property var templates: []
    property int selectedTemplate: -1
    property var undoStack: []
    property var redoStack: []
    property int undoDepth: 0
    property int redoDepth: 0
    property string editSnapshot: ""

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

    function syncHistoryDepths() {
        undoDepth = undoStack.length
        redoDepth = redoStack.length
    }

    function pushUndoSnapshot(snapshot) {
        if (!snapshot || snapshot === JSON.stringify(pixels))
            return
        undoStack.push(snapshot)
        if (undoStack.length > 80)
            undoStack.shift()
        redoStack = []
        syncHistoryDepths()
    }

    function beginEdit() {
        editSnapshot = JSON.stringify(pixels)
    }

    function finishEdit() {
        pushUndoSnapshot(editSnapshot)
        editSnapshot = ""
    }

    function restorePixels(snapshot) {
        try {
            pixels = JSON.parse(snapshot)
        } catch (e) {
            pixels = []
        }
        commitPixels()
    }

    function undo() {
        if (undoStack.length === 0)
            return
        var current = JSON.stringify(pixels)
        var previous = undoStack.pop()
        redoStack.push(current)
        restorePixels(previous)
        syncHistoryDepths()
    }

    function redo() {
        if (redoStack.length === 0)
            return
        var current = JSON.stringify(pixels)
        var next = redoStack.pop()
        undoStack.push(current)
        restorePixels(next)
        syncHistoryDepths()
    }

    function loadTemplate(index) {
        var snapshot = JSON.stringify(pixels)
        bridge.loadTemplate(index)
        pushUndoSnapshot(snapshot)
    }

    function setZoom(value) {
        var nextZoom = Math.max(minZoom, Math.min(maxZoom, value))
        if (zoom === nextZoom)
            return
        zoom = nextZoom
        Qt.callLater(centerOnCrosshair)
    }

    function centerOnCrosshair() {
        if (!editorFlick || editorFlick.width <= 0 || editorFlick.height <= 0)
            return
        var crosshairCenterX = canvas.x + (center + 0.5) * zoom
        var crosshairCenterY = canvas.y + (center + 0.5) * zoom
        editorFlick.contentX = editorFlick.clampX(crosshairCenterX - editorFlick.width / 2)
        editorFlick.contentY = editorFlick.clampY(crosshairCenterY - editorFlick.height / 2)
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

    Shortcut {
        sequence: StandardKey.Undo
        enabled: root.visible
        onActivated: root.undo()
    }

    Shortcut {
        sequence: StandardKey.Redo
        enabled: root.visible
        onActivated: root.redo()
    }

    Shortcut {
        sequence: "Ctrl+Shift+Z"
        enabled: root.visible
        onActivated: root.redo()
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
                    ActionButton { text: "↶"; compact: true; enabled: root.undoDepth > 0; onClicked: root.undo() }
                    ActionButton { text: "↷"; compact: true; enabled: root.redoDepth > 0; onClicked: root.redo() }
                    ActionButton { text: "-"; compact: true; onClicked: root.setZoom(root.zoom - 1); }
                    Label { text: root.zoom + "x"; color: "#DBDEE1" }
                    ActionButton { text: "+"; compact: true; onClicked: root.setZoom(root.zoom + 1); }
                }

                Flickable {
                    id: editorFlick
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    contentWidth: Math.max(width, canvas.width)
                    contentHeight: Math.max(height, canvas.height)
                    boundsBehavior: Flickable.StopAtBounds
                    property bool smoothWheel: false
                    Component.onCompleted: Qt.callLater(root.centerOnCrosshair)
                    onWidthChanged: Qt.callLater(root.centerOnCrosshair)
                    onHeightChanged: Qt.callLater(root.centerOnCrosshair)

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
                        x: Math.round(Math.max(0, (editorFlick.width - width) / 2))
                        y: Math.round(Math.max(0, (editorFlick.height - height) / 2))
                        onWidthChanged: requestPaint()
                        onHeightChanged: requestPaint()

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
                            acceptedButtons: Qt.LeftButton | Qt.RightButton
                            preventStealing: true

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
                                root.beginEdit()
                                apply(mouse)
                            }
                            onPositionChanged: function(mouse) {
                                if (pressed)
                                    apply(mouse)
                            }
                            onReleased: root.finishEdit()
                            onCanceled: root.finishEdit()
                            onWheel: function(wheel) {
                                if (wheel.modifiers & Qt.ControlModifier) {
                                    root.setZoom(root.zoom + (wheel.angleDelta.y > 0 ? 1 : -1))
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

                        DragHandler {
                            id: panHandler
                            acceptedButtons: Qt.MiddleButton
                            target: null
                            property real startContentX: 0
                            property real startContentY: 0

                            onActiveChanged: {
                                if (active) {
                                    editorFlick.smoothWheel = false
                                    startContentX = editorFlick.contentX
                                    startContentY = editorFlick.contentY
                                }
                            }

                            onTranslationChanged: {
                                if (active) {
                                    editorFlick.contentX = editorFlick.clampX(startContentX - translation.x)
                                    editorFlick.contentY = editorFlick.clampY(startContentY - translation.y)
                                }
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
                    ActionButton { text: "Загрузить"; Layout.fillWidth: true; onClicked: root.loadTemplate(templateBox.currentIndex) }
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
