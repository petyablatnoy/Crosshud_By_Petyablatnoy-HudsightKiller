import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

Item {
    id: root
    property var bridge

    function setting(key) {
        bridge.revision
        return bridge.getSetting(key)
    }

    ColorPickerDialog {
        id: colorDialog
        objectName: "aimColorDialog"
        property string settingKey: ""
        titleText: "Выбор цвета"
        onAccepted: function(color) { bridge.setSetting(settingKey, color) }
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 18

        PageFlickable {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumWidth: 520

            ColumnLayout {
                width: Math.max(520, parent.width - 24)
                spacing: 14

                SectionPanel {
                    title: "ГЛАВНЫЕ"

                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: "Включить прицел"; color: "#F2F3F5"; Layout.fillWidth: true }
                        Toggle {
                            checked: !!root.setting("enabled")
                            onUserToggled: bridge.setSetting("enabled", checked)
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: "Основной цвет"; color: "#F2F3F5"; Layout.fillWidth: true }
                        ColorSwatchButton {
                            bridge: root.bridge
                            settingKey: "color"
                            onCustomRequested: function(key) {
                                colorDialog.settingKey = key
                                colorDialog.openWith(root.setting(key))
                            }
                        }
                    }
                }

                SectionPanel {
                    title: "РАЗМЕРЫ И ФОРМА"
                    SliderRow { bridge: root.bridge; label: "Размер"; settingKey: "size"; from: 1; to: 100 }
                    SliderRow { bridge: root.bridge; label: "Толщина"; settingKey: "thickness"; from: 1; to: 20 }
                    SliderRow { bridge: root.bridge; label: "Зазор"; settingKey: "gap"; from: 0; to: 50 }
                    SliderRow { bridge: root.bridge; label: "Прозрачность"; settingKey: "opacity"; from: 1; to: 100; valueFactor: 100; suffix: "%" }
                }

                SectionPanel {
                    title: "ЭЛЕМЕНТЫ"

                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: "Центральная точка"; color: "#F2F3F5"; Layout.fillWidth: true }
                        Toggle {
                            checked: !!root.setting("center_dot")
                            onUserToggled: bridge.setSetting("center_dot", checked)
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: "Цвет точки"; color: "#F2F3F5"; Layout.fillWidth: true }
                        ColorSwatchButton {
                            bridge: root.bridge
                            settingKey: "center_dot_color"
                            onCustomRequested: function(key) {
                                colorDialog.settingKey = key
                                colorDialog.openWith(root.setting(key))
                            }
                        }
                    }

                    SliderRow { bridge: root.bridge; label: "Размер точки"; settingKey: "center_dot_size"; from: 1; to: 10 }

                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: "Обводка"; color: "#F2F3F5"; Layout.fillWidth: true }
                        Toggle {
                            checked: !!root.setting("outline_enabled")
                            onUserToggled: bridge.setSetting("outline_enabled", checked)
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: "Цвет обводки"; color: "#F2F3F5"; Layout.fillWidth: true }
                        ColorSwatchButton {
                            bridge: root.bridge
                            settingKey: "outline_color"
                            swatches: ["#000000", "#FFFFFF", "#5865F2", "#ED4245", "#23A559", "#FAA61A"]
                            onCustomRequested: function(key) {
                                colorDialog.settingKey = key
                                colorDialog.openWith(root.setting(key))
                            }
                        }
                    }

                    SliderRow { bridge: root.bridge; label: "Толщина обводки"; settingKey: "outline_width"; from: 0; to: 5 }
                }

                SectionPanel {
                    title: "RGB ЭФФЕКТЫ"

                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: "Радужный режим"; color: "#F2F3F5"; Layout.fillWidth: true }
                        Toggle {
                            checked: !!root.setting("rainbow_mode")
                            onUserToggled: bridge.setSetting("rainbow_mode", checked)
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: "Динамический цвет"; color: "#F2F3F5"; Layout.fillWidth: true }
                        Toggle {
                            checked: !!root.setting("dynamic_color")
                            onUserToggled: bridge.setSetting("dynamic_color", checked)
                        }
                    }
                }
            }
        }

        ColumnLayout {
            Layout.preferredWidth: 340
            Layout.minimumWidth: 340
            Layout.maximumWidth: 340
            Layout.fillHeight: true
            spacing: 14

            PreviewPanel {
                bridge: root.bridge
                Layout.preferredHeight: 400
                Layout.fillWidth: true
            }

            Item { Layout.fillHeight: true }
        }
    }
}
