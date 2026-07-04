import sys
import os
import logging
import atexit
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction, QPixmap, QFont
from PySide6.QtCore import Signal, QObject, Qt, QTimer
from settings_manager import SettingsManager
from overlay_manager import OverlayManager
from qml_ui import QmlWindowController
from resolution_detector import ResolutionDetector

class Signaler(QObject):
    toggle_trigger = Signal()

class CrossHudApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setFont(QFont("Segoe UI", 9))
        self.app.setQuitOnLastWindowClosed(False)
        self.main_icon = self.get_best_icon()
        self.app.setWindowIcon(self.main_icon)
        self.settings = SettingsManager()
        self.res_detector_active = True
        self.signaler = Signaler()
        self.signaler.toggle_trigger.connect(self.toggle_crosshair_logic)
        self.overlay = OverlayManager(self.settings, self.signaler.toggle_trigger.emit)
        self.window = QmlWindowController(self.settings, self.overlay, self.main_icon)
        self.window.notify_update.connect(self.show_notification)
        self.window.exit_confirmed.connect(self._schedule_exit)
        self.single_instance = None
        self.tray = None
        self.exiting = False
        self.res = ResolutionDetector.get_resolution()
        self.settings.set_resolution(*self.res)
        ResolutionDetector.monitor_resolution_changes(self.on_res_change)
        logging.info("Application initialized; detected_resolution=%sx%s", self.res[0], self.res[1])
        
    def get_best_icon(self):
        icon_path = "icon.ico"
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
            icon_path = os.path.join(base_dir, "icon.ico")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            if not icon.isNull():
                return icon
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.green)
        return QIcon(pixmap)

    def setup_tray(self):
        if self.tray: return
        self.tray = QSystemTrayIcon(self.app)
        self.tray.setIcon(self.main_icon)
        self.tray.setToolTip("CrossHud")
        menu = QMenu()
        show_action = QAction("Меню", menu)
        show_action.triggered.connect(self.toggle_window)
        exit_action = QAction("Выход", menu)
        exit_action.triggered.connect(self.exit_app)
        menu.addAction(show_action)
        menu.addAction(exit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_click)
        self.tray.messageClicked.connect(self.on_notification_click)
        self.tray.show()
        logging.info("System tray initialized")

    def on_notification_click(self):
        self.show_main_window()

    def on_tray_click(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_window()

    def show_notification(self, title, msg, url=None):
        if url: self.update_url = url
        if self.tray and self.tray.isVisible():
            self.tray.showMessage(title, msg, QSystemTrayIcon.Information, 5000)

    def toggle_window(self):
        if self.window.isVisible():
            self.window.hide()
        else:
            self.show_main_window()

    def show_main_window(self):
        self.window.show()
        if self.window.isMinimized():
            self.window.showNormal()
        self.window.activateWindow()
        self.window.raise_()

    def toggle_crosshair_logic(self):
        new_state = not self.settings.get('enabled', False)
        self.settings.set('enabled', new_state)
        if new_state:
            self.overlay.show()
        else:
            self.overlay.hide()
        self.window.update_enable_switch(new_state)

    def on_res_change(self, o, n):
        self.settings.set_resolution(*n)
        self.overlay.request_recreation()
        logging.info("Resolution changed: %sx%s -> %sx%s", o[0], o[1], n[0], n[1])

    def exit_app(self):
        if self.exiting:
            return
        if self.window.bridge.dirty:
            self.show_main_window()
        self.window.request_exit()

    def _schedule_exit(self):
        if self.exiting:
            return
        self.exiting = True
        logging.info("Exit requested")
        QTimer.singleShot(0, self._finish_exit)

    def _finish_exit(self):
        try:
            self.window.shutdown()
            self.overlay.cleanup()
        except Exception:
            logging.exception("Error while exiting CrossHud")
        logging.info("Application stopped")
        self.app.quit()

    def run(self, start_minimized=False):
        def startup_logic():
            self.setup_tray()
            if not start_minimized:
                self.window.show()
                self.window.raise_()
                logging.info("Main window shown")
            else:
                logging.info("Started minimized")
            QTimer.singleShot(500, lambda: self.overlay.show() if self.settings.get('enabled', True) else None)
        QTimer.singleShot(200, startup_logic)
        sys.exit(self.app.exec())
