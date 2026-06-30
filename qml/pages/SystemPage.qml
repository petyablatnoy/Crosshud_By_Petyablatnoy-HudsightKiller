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

    function setting(key) {
        bridge.revision
        return bridge.getSetting(key)
    }

    ScrollView {
        anchors.fill: parent
        anchors.margins: 24
        clip: true
        ScrollBar.vertical: ThemedScrollBar {}

        ColumnLayout {
            width: Math.max(640, parent.width - 24)
            spacing: 14

            SectionPanel {
                title: "МОНИТОР И ОВЕРЛЕЙ"

                SliderRow { bridge: root.bridge; label: "Ширина экрана"; settingKey: "screen_width"; from: 800; to: 7680; stepSize: 10 }
                SliderRow { bridge: root.bridge; label: "Высота экрана"; settingKey: "screen_height"; from: 600; to: 4320; stepSize: 10 }
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

                TextArea {
                    text: bridge.logsText
                    readOnly: true
                    wrapMode: TextEdit.NoWrap
                    color: "#DBDEE1"
                    font.family: "Consolas"
                    font.pixelSize: 11
                    Layout.fillWidth: true
                    Layout.preferredHeight: 260
                    background: Rectangle { color: "#111214"; radius: 6; border.color: "#1F2023" }
                }
            }
        }
    }
}
