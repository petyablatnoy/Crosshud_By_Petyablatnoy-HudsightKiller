import json
import logging
import os
import sys
import tempfile
import urllib.request
import winreg
from urllib.parse import urlparse

from PySide6.QtCore import QCoreApplication, QEvent, QObject, Property, QThread, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication, QFont, QWindow
from PySide6.QtQml import QQmlApplicationEngine

from app_metadata import APP_NAME, APP_VERSION, PROJECT_URL as PROJECT_PAGE_URL, UPDATE_API_URL, UPDATE_RELEASES_PATH
from diagnostics import DiagnosticService
from hotkeys import HOTKEY_NAMES


class UpdateChecker(QThread):
    update_available = Signal(str, str, str)

    def run(self):
        try:
            with urllib.request.urlopen(UPDATE_API_URL, timeout=5) as response:
                data = json.loads(response.read().decode())
            latest_tag = data.get("tag_name", "")
            if self.is_newer(latest_tag, APP_VERSION):
                self.update_available.emit(
                    data.get("html_url", ""),
                    self.display_version(latest_tag),
                    self.installer_url(data),
                )
        except Exception:
            logging.debug("Update check failed", exc_info=True)

    @staticmethod
    def installer_url(release_data):
        for asset in release_data.get("assets", []):
            name = asset.get("name", "").lower()
            url = asset.get("browser_download_url", "")
            if name.endswith(".exe") and "setup" in name and url:
                return url
        return ""

    @staticmethod
    def parse_version(v_str):
        import re
        match = re.search(r"(\d+(?:\.\d+)*)", v_str)
        if match:
            return [int(x) for x in match.group(1).split(".")]
        return [0]

    @staticmethod
    def display_version(v_str):
        parts = UpdateChecker.parse_version(v_str)
        while len(parts) > 1 and parts[-1] == 0:
            parts.pop()
        return ".".join(str(part) for part in parts)

    @staticmethod
    def is_newer(latest_str, current_str):
        try:
            latest = UpdateChecker.parse_version(latest_str)
            current = UpdateChecker.parse_version(current_str)
            max_len = max(len(latest), len(current))
            latest += [0] * (max_len - len(latest))
            current += [0] * (max_len - len(current))
            return latest > current
        except Exception:
            return False


class UpdateInstaller(QThread):
    progress_changed = Signal(int, str)
    install_ready = Signal(str)
    failed = Signal(str)

    def __init__(self, download_url, parent=None):
        super().__init__(parent)
        self.download_url = download_url

    def run(self):
        try:
            work_dir = tempfile.mkdtemp(prefix="crosshud-update-")
            setup_path = os.path.join(work_dir, os.path.basename(urlparse(self.download_url).path) or "CrossHud_Setup.exe")
            self._download(setup_path)
            script_path = self._write_installer_script(work_dir, setup_path)
            self.progress_changed.emit(100, "Запуск установщика")
            self.install_ready.emit(script_path)
        except Exception:
            logging.exception("Update install preparation failed")
            self.failed.emit("Не удалось подготовить обновление")

    def _download(self, setup_path):
        request = urllib.request.Request(self.download_url, headers={"User-Agent": APP_NAME})
        with urllib.request.urlopen(request, timeout=30) as response, open(setup_path, "wb") as output:
            total = int(response.headers.get("Content-Length") or 0)
            downloaded = 0
            while True:
                chunk = response.read(1024 * 256)
                if not chunk:
                    break
                output.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    progress = max(1, min(99, int(downloaded * 100 / total)))
                    self.progress_changed.emit(progress, f"Скачивание {progress}%")
        if os.path.getsize(setup_path) <= 0:
            raise RuntimeError("Downloaded installer is empty")

    def _write_installer_script(self, work_dir, setup_path):
        install_dir = os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), APP_NAME)
        installed_exe = sys.executable if getattr(sys, "frozen", False) else os.path.join(install_dir, f"{APP_NAME}.exe")
        script_path = os.path.join(work_dir, "install-crosshud-update.ps1")
        script = f"""$ErrorActionPreference = 'Stop'
$setup = {setup_path!r}
$app = {installed_exe!r}
Start-Sleep -Seconds 1
Start-Process -FilePath $setup -ArgumentList '/S' -Verb RunAs -Wait
if (Test-Path $app) {{
    Start-Process -FilePath $app
}}
Remove-Item -LiteralPath $setup -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $PSCommandPath -Force -ErrorAction SilentlyContinue
"""
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)
        return script_path


class UiBridge(QObject):
    UPDATE_REPO_PATH = UPDATE_RELEASES_PATH
    PROJECT_URL = PROJECT_PAGE_URL

    revisionChanged = Signal()
    dirtyChanged = Signal()
    templatesChanged = Signal()
    logsChanged = Signal()
    updateUrlChanged = Signal()
    updateInstallChanged = Signal()
    toastRequested = Signal(str, str)
    exitSavePrompt = Signal()
    exitConfirmed = Signal()
    notifyUpdate = Signal(str, str, str)
    runUpdateInstaller = Signal(str)

    def __init__(self, settings_manager, overlay_manager, app_icon=None, parent=None):
        super().__init__(parent)
        self.settings = settings_manager
        self.overlay = overlay_manager
        self.app_icon = app_icon
        self._revision = 0
        self._dirty = False
        self._update_url = ""
        self._update_version = ""
        self._update_download_url = ""
        self._update_progress = 0
        self._update_status = ""
        self._update_installing = False
        self._logs_text = ""
        self._update_thread = None
        self._update_installer_thread = None
        self._update_check_started = False
        self.diagnostics = DiagnosticService(
            self.settings.app_data_dir,
            self.settings.settings_file,
            self.log_file_path(),
            self.settings,
        )
        self.update_dirty_state()
        self.refresh_logs()

    @Property(int, notify=revisionChanged)
    def revision(self):
        return self._revision

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

    @Property(str, notify=revisionChanged)
    def diagnosticsJson(self):
        return self.diagnostics.rows_json()

    @Property(str, constant=True)
    def clientId(self):
        return self.diagnostics.client_id()

    @Property(str, notify=updateUrlChanged)
    def updateUrl(self):
        return self._update_url

    @Property(str, notify=updateUrlChanged)
    def updateVersion(self):
        return self._update_version

    @Property(int, notify=updateInstallChanged)
    def updateProgress(self):
        return self._update_progress

    @Property(str, notify=updateInstallChanged)
    def updateStatus(self):
        return self._update_status

    @Property(bool, notify=updateInstallChanged)
    def updateInstalling(self):
        return self._update_installing

    @Property(str, constant=True)
    def hotkeysJson(self):
        return json.dumps(HOTKEY_NAMES)

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

        if not self.settings.set(key, value):
            self.bump_revision()
            self.show_toast("Настройка отклонена", "warning")
            return
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
        self.update_dirty_state()
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
        self.update_dirty_state()
        self.bump_revision()
        return True

    @Slot(str)
    def setCustomPixelsJson(self, pixels_json):
        try:
            pixels = json.loads(pixels_json)
        except json.JSONDecodeError:
            self.show_toast("Неверный формат пикселей", "error")
            return
        if not self.settings.set("custom_pixels", pixels):
            self.show_toast("Неверный формат пикселей", "error")
            self.bump_revision()
            return
        self.overlay.refresh()
        self.update_dirty_state()
        self.bump_revision()

    @Slot(bool, result=bool)
    def saveSettings(self, include_custom_pixels=False):
        if self.settings.save_settings(include_custom_pixels=include_custom_pixels):
            logging.info("Settings saved; include_custom_pixels=%s", include_custom_pixels)
            self.update_dirty_state()
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
        self.update_dirty_state()
        self.bump_revision()
        self.settings.load_templates_from_disk()
        self.templatesChanged.emit()
        logging.info("Unsaved settings reset from disk")
        self.show_toast("Настройки сброшены", "success")
        return True

    @Slot(result=bool)
    def hasUnsavedCustomPixels(self):
        return self.settings.has_unsaved_custom_pixels()

    @Slot()
    def requestExit(self):
        if self.settings.has_unsaved_settings():
            logging.info("Exit requires confirmation: unsaved settings")
            self.exitSavePrompt.emit()
            return
        self.exitConfirmed.emit()

    @Slot(bool, bool)
    def confirmExit(self, proceed, include_custom_pixels):
        if not proceed:
            return
        if include_custom_pixels and not self.settings.save_settings(include_custom_pixels=True):
            self.show_toast("Не удалось сохранить настройки", "error")
            return
        logging.info("Exit confirmed; saved_before_exit=%s", include_custom_pixels)
        self._dirty = False
        self.dirtyChanged.emit()
        self.exitConfirmed.emit()

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
            if not self.settings.set("autostart", state):
                self.show_toast("Не удалось изменить автозапуск", "error")
                self.bump_revision()
                return
            self.update_dirty_state()
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
        if not self.settings.set("custom_pixels", templates[index].get("pixels", [])):
            self.show_toast("Не удалось загрузить шаблон", "error")
            self.bump_revision()
            return
        self.overlay.refresh()
        self.update_dirty_state()
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
    def copyClientId(self):
        clipboard = QGuiApplication.clipboard()
        if clipboard:
            clipboard.setText(self.diagnostics.client_id())
            self.show_toast("UID скопирован", "success")

    @Slot()
    def copyDiagnostics(self):
        clipboard = QGuiApplication.clipboard()
        if clipboard:
            clipboard.setText(self.diagnostics.report_text())
            self.show_toast("Сведения скопированы", "success")

    @Slot()
    def createSupportArchive(self):
        try:
            archive_path = self.diagnostics.create_support_archive()
            clipboard = QGuiApplication.clipboard()
            if clipboard:
                clipboard.setText(archive_path)
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(archive_path)))
            logging.info("Support archive created: %s", archive_path)
            self.show_toast("Отчет создан, путь скопирован", "success")
        except Exception:
            logging.exception("Failed to create support archive")
            self.show_toast("Не удалось создать отчет", "error")

    @Slot()
    def showStartupWarnings(self):
        warnings = self.settings.consume_warnings()
        if warnings:
            self.show_toast("Настройки исправлены. Подробности в логах.", "warning")

    @Slot()
    def openUpdate(self):
        if self._is_valid_update_url(self._update_url):
            QDesktopServices.openUrl(QUrl(self._update_url))
        else:
            self.show_toast("Ссылка обновления отклонена", "warning")

    @Slot()
    def openLatestRelease(self):
        QDesktopServices.openUrl(QUrl(f"{self.PROJECT_URL}/releases/latest"))

    @Slot()
    def installUpdate(self):
        if self._update_installing:
            return
        if not self._is_valid_update_url(self._update_download_url):
            self.show_toast("Установщик обновления недоступен", "warning")
            return
        self._update_installing = True
        self._update_progress = 0
        self._update_status = "Подготовка загрузки"
        self.updateInstallChanged.emit()
        self._update_installer_thread = UpdateInstaller(self._update_download_url, self)
        self._update_installer_thread.progress_changed.connect(self._on_update_progress)
        self._update_installer_thread.install_ready.connect(self._on_update_install_ready)
        self._update_installer_thread.failed.connect(self._on_update_install_failed)
        self._update_installer_thread.start()

    @Slot()
    def openProjectPage(self):
        QDesktopServices.openUrl(QUrl(self.PROJECT_URL))

    def update_dirty_state(self):
        dirty = self.settings.has_unsaved_settings()
        if self._dirty != dirty:
            self._dirty = dirty
            self.dirtyChanged.emit()

    def bump_revision(self):
        self._revision += 1
        self.revisionChanged.emit()

    def show_toast(self, text, kind="success"):
        logging.info("%s: %s", kind, text)
        self.toastRequested.emit(text, kind)

    def start_update_check(self):
        if self._update_check_started:
            return
        if not self.settings.get("check_updates", True):
            logging.info("Update check skipped: disabled in settings")
            return
        self._update_check_started = True
        logging.info("Update check started")
        self._update_thread = UpdateChecker(self)
        self._update_thread.update_available.connect(self._on_update_available)
        self._update_thread.start()

    def _on_update_available(self, url, version, download_url):
        if not self._is_valid_update_url(url) or not self._is_valid_update_url(download_url):
            logging.warning("Ignored unexpected update URLs: release=%s download=%s", url, download_url)
            return
        self._update_url = url
        self._update_version = version
        self._update_download_url = download_url
        self.updateUrlChanged.emit()
        logging.info("Update available: version=%s url=%s", version, url)
        self.notifyUpdate.emit("Доступна новая версия", f"CrossHud {version}. Откройте приложение для обновления.", url)

    def _on_update_progress(self, progress, status):
        self._update_progress = progress
        self._update_status = status
        self.updateInstallChanged.emit()

    def _on_update_install_ready(self, script_path):
        self._update_progress = 100
        self._update_status = "Запуск установщика"
        self.updateInstallChanged.emit()
        self.runUpdateInstaller.emit(script_path)

    def _on_update_install_failed(self, message):
        self._update_installing = False
        self._update_status = message
        self.updateInstallChanged.emit()
        self.show_toast(message, "error")

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


class QmlWindowController(QObject):
    notify_update = Signal(str, str, str)
    exit_confirmed = Signal()
    run_update_installer = Signal(str)

    def __init__(self, settings_manager, overlay_manager, app_icon=None, parent=None):
        super().__init__(parent)
        app = QGuiApplication.instance()
        if app:
            app.setFont(QFont("Segoe UI", 9))
        self.bridge = UiBridge(settings_manager, overlay_manager, app_icon, self)
        self.bridge.notifyUpdate.connect(self.notify_update)
        self.bridge.exitConfirmed.connect(self.exit_confirmed)
        self.bridge.runUpdateInstaller.connect(self.run_update_installer)
        self.engine = QQmlApplicationEngine(self)
        self.engine.rootContext().setContextProperty("bridge", self.bridge)
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

    def start_update_check(self):
        self.bridge.start_update_check()

    def confirm_save_custom_pixels_on_exit(self):
        self.request_exit()
        return False

    def update_enable_switch(self, state):
        self.bridge.bump_revision()

    def show_warning(self, text):
        self.bridge.show_toast(text, "warning")

    def shutdown(self):
        if self.root is not None:
            self.root.hide()
            self.root.deleteLater()
            self.root = None
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

        if self.engine is not None:
            self.engine.deleteLater()
            self.engine = None
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

        app = QCoreApplication.instance()
        if app:
            app.processEvents()
