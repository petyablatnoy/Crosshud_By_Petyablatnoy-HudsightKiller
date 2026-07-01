import json
import logging
import os
import sys
import urllib.request
import winreg
from urllib.parse import urlparse

from PySide6.QtCore import QObject, Property, QThread, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication, QImage, QFont, QWindow
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider

from crosshair_renderer import render_crosshair_preview_image


class UpdateChecker(QThread):
    update_available = Signal(str)

    def run(self):
        try:
            url = "https://api.github.com/repos/petyablatnoy/Crosshud_By_Petyablatnoy-HudsightKiller/releases/latest"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode())
            latest_tag = data.get("tag_name", "")
            if self.is_newer(latest_tag, "4"):
                self.update_available.emit(data.get("html_url", ""))
        except Exception:
            logging.debug("Update check failed", exc_info=True)

    @staticmethod
    def is_newer(latest_str, current_str):
        try:
            def parse_version(v_str):
                import re
                match = re.search(r"(\d+(?:\.\d+)*)", v_str)
                if match:
                    return [int(x) for x in match.group(1).split(".")]
                return [0]

            latest = parse_version(latest_str)
            current = parse_version(current_str)
            max_len = max(len(latest), len(current))
            latest += [0] * (max_len - len(latest))
            current += [0] * (max_len - len(current))
            return latest > current
        except Exception:
            return False


class UiBridge(QObject):
    UPDATE_REPO_PATH = "/petyablatnoy/Crosshud_By_Petyablatnoy-HudsightKiller/releases/"

    revisionChanged = Signal()
    dirtyChanged = Signal()
    templatesChanged = Signal()
    previewChanged = Signal()
    logsChanged = Signal()
    updateUrlChanged = Signal()
    toastRequested = Signal(str, str)
    exitSavePrompt = Signal()
    exitConfirmed = Signal()
    notifyUpdate = Signal(str, str, str)

    def __init__(self, settings_manager, overlay_manager, app_icon=None, parent=None):
        super().__init__(parent)
        self.settings = settings_manager
        self.overlay = overlay_manager
        self.app_icon = app_icon
        self._revision = 0
        self._preview_revision = 0
        self._preview_frame_width = 1
        self._preview_frame_height = 1
        self._crosshair_width = 0
        self._crosshair_height = 0
        self._dirty = False
        self._preview_hue = 0
        self._update_url = ""
        self._logs_text = ""
        self._update_thread = None
        self.update_preview_metrics()
        self.refresh_logs()
        if self.settings.get("check_updates", True):
            self.start_update_check()

    @Property(int, notify=revisionChanged)
    def revision(self):
        return self._revision

    @Property(int, notify=previewChanged)
    def previewRevision(self):
        return self._preview_revision

    @Property(int, notify=previewChanged)
    def previewFrameWidth(self):
        return self._preview_frame_width

    @Property(int, notify=previewChanged)
    def previewFrameHeight(self):
        return self._preview_frame_height

    @Property(str, notify=previewChanged)
    def previewSizeText(self):
        return f"Прицел {self._crosshair_width} x {self._crosshair_height} px"

    @Property(bool, notify=dirtyChanged)
    def dirty(self):
        return self._dirty

    @Property(str, notify=templatesChanged)
    def templatesJson(self):
        return json.dumps(self.settings.get("custom_templates", []), ensure_ascii=False)

    @Property(str, notify=revisionChanged)
    def customPixelsJson(self):
        return json.dumps(self.settings.get("custom_pixels", []), ensure_ascii=False)

    @Property(str, notify=logsChanged)
    def logsText(self):
        return self._logs_text

    @Property(str, constant=True)
    def logsPath(self):
        return self.log_file_path()

    @Property(str, notify=updateUrlChanged)
    def updateUrl(self):
        return self._update_url

    @Slot(str, result="QVariant")
    def getSetting(self, key):
        return self.settings.get(key)

    @Slot(str, result=str)
    def iconUrl(self, filename):
        return QUrl.fromLocalFile(os.path.join(self.asset_dir(), "icons", "lucide", filename)).toString()

    @Slot(str, result=bool)
    def isValidUpdateUrl(self, url):
        return self._is_valid_update_url(url)

    @Slot(str, "QVariant")
    def setSetting(self, key, value):
        if key == "rainbow_mode" and bool(value):
            self.settings.set("dynamic_color", False)
        if key == "dynamic_color" and bool(value):
            self.settings.set("rainbow_mode", False)

        self.settings.set(key, value)
        if key == "enabled":
            if self.settings.get("enabled", False):
                self.overlay.show()
            else:
                self.overlay.hide()
        elif key == "hotkey":
            self.overlay.update_hotkey()
        elif key in ("screen_width", "screen_height", "overlay_size"):
            self.overlay.request_recreation()
        else:
            self.overlay.refresh()
        self.mark_dirty()
        self.bump_revision()

    @Slot(int, int, result=bool)
    def setResolution(self, width, height):
        width = int(width)
        height = int(height)
        if not self.settings.set_resolution(width, height):
            self.show_toast("Разрешение вне допустимого диапазона", "warning")
            self.bump_revision()
            return False
        self.overlay.request_recreation()
        self.mark_dirty()
        self.bump_revision()
        return True

    @Slot(str)
    def setCustomPixelsJson(self, pixels_json):
        try:
            pixels = json.loads(pixels_json)
        except json.JSONDecodeError:
            self.show_toast("Неверный формат пикселей", "error")
            return
        self.settings.set("custom_pixels", pixels)
        self.overlay.refresh()
        self.mark_dirty()
        self.bump_revision()

    @Slot(bool, result=bool)
    def saveSettings(self, include_custom_pixels=False):
        if self.settings.save_settings(include_custom_pixels=include_custom_pixels):
            self._dirty = False
            self.dirtyChanged.emit()
            self.bump_revision()
            self.show_toast("Настройки сохранены", "success")
            return True
        self.show_toast("Не удалось сохранить настройки", "error")
        return False

    @Slot(result=bool)
    def resetSettings(self):
        if not self.settings.load_settings():
            self.show_toast("Не удалось сбросить настройки", "error")
            return False
        self.overlay.refresh()
        self._dirty = False
        self.dirtyChanged.emit()
        self.bump_revision()
        self.settings.load_templates_from_disk()
        self.templatesChanged.emit()
        self.show_toast("Настройки сброшены", "success")
        return True

    @Slot(result=bool)
    def hasUnsavedCustomPixels(self):
        return self.settings.has_unsaved_custom_pixels()

    @Slot()
    def requestExit(self):
        if self.settings.has_unsaved_custom_pixels():
            self.exitSavePrompt.emit()
            return
        self.settings.save_settings(include_custom_pixels=False)
        self.exitConfirmed.emit()

    @Slot(bool, bool)
    def confirmExit(self, proceed, include_custom_pixels):
        if not proceed:
            return
        if self.settings.save_settings(include_custom_pixels=include_custom_pixels):
            self.exitConfirmed.emit()
        else:
            self.show_toast("Не удалось сохранить настройки", "error")

    @Slot(bool)
    def setAutostart(self, state):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = None
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            if state:
                if getattr(sys, "frozen", False):
                    path = f'"{sys.executable}"'
                else:
                    path = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'
                winreg.SetValueEx(key, "CrossHud_PetyaBlatnoy", 0, winreg.REG_SZ, path)
            else:
                try:
                    winreg.DeleteValue(key, "CrossHud_PetyaBlatnoy")
                except FileNotFoundError:
                    pass
            self.settings.set("autostart", state)
            self.mark_dirty()
            self.bump_revision()
        except Exception:
            logging.exception("Failed to update autostart")
            self.settings.set("autostart", not state)
            self.bump_revision()
            self.show_toast("Не удалось изменить автозапуск", "error")
        finally:
            if key:
                winreg.CloseKey(key)

    @Slot(int)
    def loadTemplate(self, index):
        templates = self.settings.get("custom_templates", [])
        if index < 0 or index >= len(templates):
            return
        self.settings.set("custom_pixels", templates[index].get("pixels", []))
        self.overlay.refresh()
        self.mark_dirty()
        self.bump_revision()
        self.show_toast("Шаблон загружен", "success")

    @Slot(str, result=bool)
    def saveTemplate(self, name):
        if not name.strip():
            self.show_toast("Введите имя шаблона", "warning")
            return False
        filename = self.settings.save_template({"name": name.strip(), "pixels": self.settings.get("custom_pixels", [])})
        if not filename:
            self.show_toast("Не удалось сохранить шаблон", "error")
            return False
        self.settings.load_templates_from_disk()
        self.templatesChanged.emit()
        self.show_toast("Шаблон сохранен", "success")
        return True

    @Slot(int, result=bool)
    def deleteTemplate(self, index):
        templates = self.settings.get("custom_templates", [])
        if index < 0 or index >= len(templates):
            return False
        if not self.settings.delete_template(templates[index]):
            self.show_toast("Не удалось удалить шаблон", "error")
            return False
        self.settings.load_templates_from_disk()
        self.templatesChanged.emit()
        self.show_toast("Шаблон удален", "success")
        return True

    @Slot()
    def refreshLogs(self):
        self.refresh_logs()
        self.logsChanged.emit()

    @Slot()
    def openLogsFolder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(self.log_file_path())))

    @Slot()
    def showStartupWarnings(self):
        warnings = self.settings.consume_warnings()
        if warnings:
            self.show_toast("Настройки исправлены. Подробности в логах.", "warning")

    @Slot()
    def advancePreviewAnimation(self):
        if self.settings.get("rainbow_mode", False) or self.settings.get("dynamic_color", False):
            self._preview_hue = (self._preview_hue + 2) % 360
            self.bump_preview()

    @Slot()
    def openUpdate(self):
        if self._is_valid_update_url(self._update_url):
            QDesktopServices.openUrl(QUrl(self._update_url))
        else:
            self.show_toast("Ссылка обновления отклонена", "warning")

    def mark_dirty(self):
        if not self._dirty:
            self._dirty = True
            self.dirtyChanged.emit()

    def bump_revision(self):
        self._revision += 1
        self.revisionChanged.emit()
        self.update_preview_metrics()
        self.bump_preview()

    def bump_preview(self):
        self._preview_revision += 1
        self.previewChanged.emit()

    def update_preview_metrics(self):
        _img, crosshair_size, frame_size = render_crosshair_preview_image(self.settings, size=512, hue=self._preview_hue)
        self._crosshair_width, self._crosshair_height = crosshair_size
        self._preview_frame_width, self._preview_frame_height = frame_size

    def show_toast(self, text, kind="success"):
        logging.info("%s: %s", kind, text)
        self.toastRequested.emit(text, kind)

    def start_update_check(self):
        self._update_thread = UpdateChecker(self)
        self._update_thread.update_available.connect(self._on_update_available)
        self._update_thread.start()

    def _on_update_available(self, url):
        if not self._is_valid_update_url(url):
            logging.warning("Ignored unexpected update URL: %s", url)
            return
        self._update_url = url
        self.updateUrlChanged.emit()
        self.show_toast("Доступно обновление", "success")
        self.notifyUpdate.emit("Доступно обновление!", "Вышла новая версия CrossHud. Нажмите, чтобы скачать.", url)

    def _is_valid_update_url(self, url):
        try:
            parsed = urlparse(url)
            return parsed.scheme == "https" and parsed.netloc.lower() == "github.com" and parsed.path.startswith(self.UPDATE_REPO_PATH)
        except Exception:
            return False

    def refresh_logs(self):
        log_file = self.log_file_path()
        try:
            with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
            self._logs_text = text[-30000:]
        except FileNotFoundError:
            self._logs_text = "Логи пока не созданы."
        except Exception:
            logging.exception("Failed to read logs")
            self._logs_text = "Не удалось прочитать лог."

    def log_file_path(self):
        return os.path.join(os.path.expanduser("~"), "CrossHud_By_PetyaBlatnoy", "logs", "crosshud.log")

    def resource_dir(self):
        if getattr(sys, "frozen", False):
            return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        return os.path.dirname(os.path.abspath(__file__))

    def asset_dir(self):
        return os.path.join(self.resource_dir(), "assets")

    def qml_dir(self):
        return os.path.join(self.resource_dir(), "qml")


class CrosshairImageProvider(QQuickImageProvider):
    def __init__(self, bridge: UiBridge):
        super().__init__(QQuickImageProvider.Image)
        self.bridge = bridge

    def requestImage(self, image_id, size, requested_size):
        img, _crosshair_size, _frame_size = render_crosshair_preview_image(
            self.bridge.settings,
            size=512,
            hue=self.bridge._preview_hue,
            apply_opacity=True,
        )
        if img is None:
            return QImage(1, 1, QImage.Format_RGBA8888)
        data = img.tobytes("raw", "RGBA")
        qimage = QImage(data, img.width, img.height, QImage.Format_RGBA8888).copy()
        size.setWidth(qimage.width())
        size.setHeight(qimage.height())
        return qimage


class QmlWindowController(QObject):
    notify_update = Signal(str, str, str)
    exit_confirmed = Signal()

    def __init__(self, settings_manager, overlay_manager, app_icon=None, parent=None):
        super().__init__(parent)
        app = QGuiApplication.instance()
        if app:
            app.setFont(QFont("Segoe UI", 9))
        self.bridge = UiBridge(settings_manager, overlay_manager, app_icon, self)
        self.bridge.notifyUpdate.connect(self.notify_update)
        self.bridge.exitConfirmed.connect(self.exit_confirmed)
        self.engine = QQmlApplicationEngine(self)
        self.engine.rootContext().setContextProperty("bridge", self.bridge)
        self.engine.addImageProvider("crosshair", CrosshairImageProvider(self.bridge))
        qml_file = os.path.join(self.bridge.qml_dir(), "Main.qml")
        self.engine.load(QUrl.fromLocalFile(qml_file))
        if not self.engine.rootObjects():
            raise RuntimeError(f"Failed to load QML UI: {qml_file}")
        self.root = self.engine.rootObjects()[0]

    def show(self):
        self.root.show()
        self.activateWindow()

    def hide(self):
        self.root.hide()

    def isVisible(self):
        return bool(self.root.isVisible())

    def isMinimized(self):
        return bool(self.root.visibility() == QWindow.Minimized)

    def showNormal(self):
        if hasattr(self.root, "showNormal"):
            self.root.showNormal()
        else:
            self.root.show()

    def activateWindow(self):
        if hasattr(self.root, "requestActivate"):
            self.root.requestActivate()

    def raise_(self):
        if hasattr(self.root, "raise_"):
            self.root.raise_()

    def request_exit(self):
        self.bridge.requestExit()

    def confirm_save_custom_pixels_on_exit(self):
        self.request_exit()
        return False

    def update_enable_switch(self, state):
        self.bridge.bump_revision()

    def show_warning(self, text):
        self.bridge.show_toast(text, "warning")
