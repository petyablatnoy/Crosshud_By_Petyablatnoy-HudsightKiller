import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

Item {
    id: root
    property var bridge
    property var rmbLabels: ["Ничего", "Скрывать (Hold)", "Переключать (Toggle)"]
    property var rmbValues: ["disabled", "hold", "toggle"]
    property var hotkeys: ["Insert", "Home", "End", "PageUp", "PageDown", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"]
    property var resolutionLabels: ["HD 1280x720", "Full HD 1920x1080", "QHD 2560x1440", "4K 3840x2160", "Свой размер"]
    property var resolutionValues: [[1280, 720], [1920, 1080], [2560, 1440], [3840, 2160], [0, 0]]

    function setting(key) {
        bridge.revision
        return bridge.getSetting(key)
    }

    function currentResolutionIndex() {
        var width = Number(root.setting("screen_width"))
        var height = Number(root.setting("screen_height"))
        for (var i = 0; i < root.resolutionValues.length - 1; i++) {
            if (root.resolutionValues[i][0] === width && root.resolutionValues[i][1] === height)
                return i
        }
        return root.resolutionValues.length - 1
    }

    PageFlickable {
        anchors.fill: parent
        anchors.margins: 24

        ColumnLayout {
            x: Math.round((parent.width - width) / 2)
            width: Math.min(880, parent.width)
            spacing: 14

            SectionPanel {
                title: "МОНИТОР И ОВЕРЛЕЙ"

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Разрешение"; color: "#F2F3F5"; Layout.fillWidth: true }
                    DarkComboBox {
                        model: root.resolutionLabels
                        currentIndex: root.currentResolutionIndex()
                        Layout.preferredWidth: 220
                        onActivated: {
                            if (currentIndex < root.resolutionValues.length - 1)
                                bridge.setResolution(root.resolutionValues[currentIndex][0], root.resolutionValues[currentIndex][1])
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Свой размер"; color: "#F2F3F5"; Layout.fillWidth: true }
                    DarkTextField {
                        id: widthField
                        text: String(root.setting("screen_width"))
                        Layout.preferredWidth: 96
                        validator: IntValidator { bottom: 800; top: 7680 }
                    }
                    Label { text: "×"; color: "#949BA4"; font.bold: true }
                    DarkTextField {
                        id: heightField
                        text: String(root.setting("screen_height"))
                        Layout.preferredWidth: 96
                        validator: IntValidator { bottom: 600; top: 4320 }
                    }
                    ActionButton {
                        text: "Применить"
                        highlighted: true
                        onClicked: bridge.setResolution(Number(widthField.text), Number(heightField.text))
                    }
                }
            }

            SectionPanel {
                title: "ПОВЕДЕНИЕ И КЛАВИШИ"

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Режим ПКМ"; color: "#F2F3F5"; Layout.fillWidth: true }
                    DarkComboBox {
                        model: root.rmbLabels
                        currentIndex: Math.max(0, root.rmbValues.indexOf(root.setting("rmb_hide_mode")))
                        Layout.preferredWidth: 210
                        onActivated: bridge.setSetting("rmb_hide_mode", root.rmbValues[currentIndex])
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Горячая клавиша"; color: "#F2F3F5"; Layout.fillWidth: true }
                    DarkComboBox {
                        id: hotkeyBox
                        model: root.hotkeys
                        currentIndex: Math.max(0, root.hotkeys.indexOf(root.setting("hotkey")))
                        Layout.preferredWidth: 160
                        onActivated: bridge.setSetting("hotkey", currentText)
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Автозапуск"; color: "#F2F3F5"; Layout.fillWidth: true }
                    Toggle {
                        checked: !!root.setting("autostart")
                        onUserToggled: bridge.setAutostart(checked)
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Скрытый запуск"; color: "#F2F3F5"; Layout.fillWidth: true }
                    Toggle {
                        checked: !!root.setting("start_minimized")
                        onUserToggled: bridge.setSetting("start_minimized", checked)
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Проверять обновления"; color: "#F2F3F5"; Layout.fillWidth: true }
                    Toggle {
                        checked: !!root.setting("check_updates")
                        onUserToggled: bridge.setSetting("check_updates", checked)
                    }
                }

                ActionButton {
                    visible: bridge.updateUrl.length > 0
                    text: "Открыть обновление"
                    highlighted: true
                    onClicked: bridge.openUpdate()
                }
            }

            SectionPanel {
                title: "ДИАГНОСТИКА"

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Логи приложения"; color: "#F2F3F5"; Layout.fillWidth: true }
                    ActionButton { text: "Обновить"; onClicked: bridge.refreshLogs() }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Файл логов"; color: "#B5BAC1"; Layout.preferredWidth: 96 }
                    DarkTextField {
                        text: bridge.logsPath
                        readOnly: true
                        Layout.fillWidth: true
                    }
                    ActionButton {
                        text: "Папка"
                        onClicked: bridge.openLogsFolder()
                    }
                }

                LogView {
                    text: bridge.logsText
                    Layout.fillWidth: true
                    Layout.preferredHeight: 260
                }
            }
        }
    }
}
