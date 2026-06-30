from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QStackedWidget, QPushButton, QScrollArea, 
                               QFileDialog, QInputDialog, QMessageBox, QFrame, QSpinBox, QComboBox, QSizePolicy, QSizeGrip)
from PySide6.QtCore import Qt, QSize, QUrl, QThread, Signal, QPropertyAnimation, QTimer
from PySide6.QtGui import QIcon, QAction, QDesktopServices
import sys
import os
import winreg
import logging
import json
import urllib.request
from urllib.parse import urlparse
import re
from theme_manager import ThemeManager
from qt_widgets import DiscordSwitch, ModernSlider, ColorButton, SettingCard, CustomTitleBar, FastSmoothScrollArea, DarkMessageBox, UnsavedChangesBar, NotificationBar, NoScrollComboBox
from pixel_editor import PixelEditor
from logger_tab import LoggerTab

class UpdateChecker(QThread):
    update_available = Signal(str)
    def run(self):
        try:
            url = "https://api.github.com/repos/petyablatnoy/Crosshud_By_Petyablatnoy-HudsightKiller/releases/latest"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode())
                latest_tag = data.get('tag_name', '')
                current_ver = "4"
                if self.is_newer(latest_tag, current_ver):
                    self.update_available.emit(data.get('html_url', ''))
        except Exception:
            logging.debug("Update check failed", exc_info=True)

    def is_newer(self, latest_str, current_str):
        try:
            def parse_version(v_str):
                match = re.search(r'(\d+(?:\.\d+)*)', v_str)
                if match:
                    return [int(x) for x in match.group(1).split('.')]
                return [0]
            
            l_parts = parse_version(latest_str)
            c_parts = parse_version(current_str)
            max_len = max(len(l_parts), len(c_parts))
            l_parts += [0] * (max_len - len(l_parts))
            c_parts += [0] * (max_len - len(c_parts))
            return l_parts > c_parts
        except: return False

class UIComponents(QMainWindow):
    notify_update = Signal(str, str, str) 
    UPDATE_REPO_PATH = "/petyablatnoy/Crosshud_By_Petyablatnoy-HudsightKiller/releases/"

    def __init__(self, settings_manager, overlay_manager, app_icon=None):
        super().__init__()
        self.settings = settings_manager
        self.overlay = overlay_manager
        self.is_loading = False 
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(1050, 750)
        self.setMinimumSize(950, 650)
        self.window_moving = False
        self.offset = None
        self.setStyleSheet(ThemeManager.get_stylesheet())
        if app_icon:
            self.setWindowIcon(app_icon)
        self.central_container = QWidget()
        self.central_container.setObjectName("RootContainer")
        self.setCentralWidget(self.central_container)
        self.central_layout = QVBoxLayout(self.central_container)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.main_content = QWidget()
        self.main_content.setObjectName("MainContent")
        self.main_content.setAutoFillBackground(True)
        self.central_layout.addWidget(self.main_content)
        self.window_layout = QVBoxLayout(self.main_content)
        self.window_layout.setContentsMargins(0, 0, 0, 0)
        self.window_layout.setSpacing(0)
        self.title_bar = CustomTitleBar(self)
        self.window_layout.addWidget(self.title_bar)
        self.body_widget = QWidget()
        self.body_layout = QHBoxLayout(self.body_widget)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(0)
        self.create_sidebar()
        self.create_content_area()
        self.window_layout.addWidget(self.body_widget)
        self.grip = QSizeGrip(self.main_content)
        self.grip.setStyleSheet("background: transparent;")
        self.unsaved_bar = UnsavedChangesBar(self.central_container)
        self.unsaved_bar.saveClicked.connect(self.save_settings)
        self.unsaved_bar.resetClicked.connect(self.reset_changes)
        self.success_bar = NotificationBar(self.central_container)
        self.warning_bar = NotificationBar(self.central_container)
        self.setup_pages()
        self.overlay.request_recreation()
        QTimer.singleShot(500, self.show_settings_warnings)
        
        if self.settings.get('check_updates', True):
            self.update_thread = UpdateChecker()
            self.update_thread.update_available.connect(self.on_update_found)
            self.update_thread.start()

    def on_update_found(self, url):
        if not self.is_valid_update_url(url):
            logging.warning("Ignored unexpected update URL: %s", url)
            return
        self.show_update_btn(url)
        self.notify_update.emit("Доступно обновление!", "Вышла новая версия CrossHud. Нажмите, чтобы скачать.", url)

    def show_update_btn(self, url):
        self.update_btn.setProperty("url", url)
        self.update_btn.show()

    def open_update(self):
        url = self.update_btn.property("url")
        if url and self.is_valid_update_url(url):
            QDesktopServices.openUrl(QUrl(url))
        else:
            self.show_warning("Ссылка обновления отклонена")

    def is_valid_update_url(self, url):
        try:
            parsed = urlparse(url)
            return parsed.scheme == "https" and parsed.netloc.lower() == "github.com" and parsed.path.startswith(self.UPDATE_REPO_PATH)
        except Exception:
            return False

    def resizeEvent(self, event):
        rect = self.rect()
        self.grip.move(rect.right() - 20, rect.bottom() - 20)
        if self.unsaved_bar.isVisible():
            self.unsaved_bar.move(rect.width() - self.unsaved_bar.width() - 20, rect.height() - self.unsaved_bar.height() - 20)
        if self.success_bar.isVisible():
            self.success_bar.move(rect.width() - self.success_bar.width() - 20, rect.height() - self.success_bar.height() - 20)
        if self.warning_bar.isVisible():
            self.warning_bar.move(rect.width() - self.warning_bar.width() - 20, rect.height() - self.warning_bar.height() - 20)
        super().resizeEvent(event)

    def show_settings_warnings(self):
        warnings = self.settings.consume_warnings()
        if warnings:
            self.show_warning("Настройки исправлены. Подробности в логах.")

    def show_warning(self, text):
        logging.warning(text)
        self.warning_bar.show_message(text, self.rect(), kind="warning")

    def mark_dirty(self):
        if self.is_loading: return
        self.unsaved_bar.show_animated(self.rect())

    def reset_changes(self):
        self.is_loading = True
        if self.settings.load_settings():
            self.overlay.refresh()
            self.unsaved_bar.hide_animated(self.rect())
            idx = self.stack.currentIndex()
            self.setup_pages()
            self.switch_page(list(self.nav_buttons.keys())[idx])
        self.is_loading = False

    def create_sidebar(self):
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(240)
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(5)
        logo = QLabel("CROSSHUD")
        logo.setObjectName("LogoLabel")
        layout.addWidget(logo)
        layout.addSpacing(10)
        self.nav_buttons = {}
        nav_items = [('general', 'ОСНОВНОЕ'), ('system', 'СИСТЕМА'), ('pixel', 'КАСТОМНЫЙ ПРИЦЕЛ'), ('logs', 'ЛОГИ')]
        for key, text in nav_items:
            btn = QPushButton(text)
            btn.setObjectName("NavButton")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, k=key: self.switch_page(k))
            layout.addWidget(btn)
            self.nav_buttons[key] = btn
        layout.addStretch()
        dev = QLabel('v4 | <a href="https://github.com/petyablatnoy/Crosshud_By_Petyablatnoy-HudsightKiller" style="color: #949ba4; text-decoration: none;">Dev: PetyaBlatnoy</a>')
        dev.setStyleSheet("color: #4e5058; font-size: 11px; font-weight: bold; padding: 10px;")
        dev.setAlignment(Qt.AlignCenter)
        dev.setOpenExternalLinks(True)
        dev.setCursor(Qt.PointingHandCursor)
        layout.addWidget(dev)
        
        self.update_btn = QPushButton("ДОСТУПНО ОБНОВЛЕНИЕ")
        self.update_btn.setFixedHeight(45)
        self.update_btn.setCursor(Qt.PointingHandCursor)
        self.update_btn.setStyleSheet("""
            QPushButton { 
                background-color: #23a559; 
                color: #ffffff; 
                border: none; 
                font-weight: 900; 
                border-radius: 4px; 
                font-size: 13px;
                letter-spacing: 0.5px;
            }
            QPushButton:hover { background-color: #1a7f42; }
        """)
        
        self.update_btn.clicked.connect(self.open_update)
        self.update_btn.hide()
        layout.addWidget(self.update_btn)
        
        save_btn = QPushButton("СОХРАНИТЬ НАСТРОЙКИ")
        save_btn.setFixedHeight(45)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        self.body_layout.addWidget(self.sidebar)

    def create_content_area(self):
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background-color: transparent;") 
        l = QVBoxLayout(self.content_widget)
        l.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        l.addWidget(self.stack)
        self.body_layout.addWidget(self.content_widget)

    def switch_page(self, key):
        if key in self.pages:
            self.stack.setCurrentWidget(self.pages[key])
            for k, btn in self.nav_buttons.items():
                btn.setProperty("active", str(k == key).lower())
                btn.style().unpolish(btn)
                btn.style().polish(btn)

    def setup_pages(self):
        self.is_loading = True
        while self.stack.count():
            w = self.stack.widget(0)
            self.stack.removeWidget(w)
            w.deleteLater()
        self.pages = {'general': self.create_general_page(), 'system': self.create_system_page(), 'pixel': self.create_pixel_page(), 'logs': self.create_logs_page()}
        for p in self.pages.values(): self.stack.addWidget(p)
        self.switch_page('general')
        self.is_loading = False

    def create_scrollable_page(self):
        page = QWidget()
        l = QVBoxLayout(page)
        l.setContentsMargins(0, 0, 0, 0)
        scroll = FastSmoothScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QWidget()
        content.setStyleSheet("background-color: transparent;") 
        self.page_layout = QVBoxLayout(content)
        self.page_layout.setAlignment(Qt.AlignTop)
        self.page_layout.setContentsMargins(40, 40, 40, 40)
        self.page_layout.setSpacing(20)
        scroll.setWidget(content)
        l.addWidget(scroll)
        return page, self.page_layout

    def create_general_page(self):
        page, layout = self.create_scrollable_page()
        card_main = SettingCard("ГЛАВНЫЕ")
        self.sw_enable = DiscordSwitch()
        self.sw_enable.setChecked(self.settings.get('enabled', False))
        self.sw_enable.toggled.connect(self.toggle_enable)
        card_main.add_control("Включить прицел", self.sw_enable)
        col_btn = ColorButton(self.settings.get('color', '#00FF00'))
        col_btn.colorChanged.connect(lambda c: self.update_setting('color', c))
        card_main.add_control("Основной цвет", col_btn)
        layout.addWidget(card_main)
        card_dim = SettingCard("РАЗМЕРЫ И ФОРМА")
        card_dim.add_control("Размер", self.create_slider('size', 1, 100))
        card_dim.add_control("Толщина линий", self.create_slider('thickness', 1, 20))
        card_dim.add_control("Зазор центра", self.create_slider('gap', 0, 50))
        card_dim.add_control("Прозрачность", self.create_slider('opacity', 1, 100, float_scale=True))
        layout.addWidget(card_dim)
        card_elem = SettingCard("ЭЛЕМЕНТЫ")
        sw_dot = DiscordSwitch()
        sw_dot.setChecked(self.settings.get('center_dot', False))
        sw_dot.toggled.connect(lambda v: self.update_setting('center_dot', v))
        card_elem.add_control("Центральная точка", sw_dot)
        col_dot = ColorButton(self.settings.get('center_dot_color', '#FF0000'))
        col_dot.colorChanged.connect(lambda c: self.update_setting('center_dot_color', c))
        card_elem.add_control("Цвет точки", col_dot)
        card_elem.add_control("Размер точки", self.create_slider('center_dot_size', 1, 10))
        sw_out = DiscordSwitch()
        sw_out.setChecked(self.settings.get('outline_enabled', False))
        sw_out.toggled.connect(lambda v: self.update_setting('outline_enabled', v))
        card_elem.add_control("Обводка (Outline)", sw_out)
        col_out = ColorButton(self.settings.get('outline_color', '#000000'))
        col_out.colorChanged.connect(lambda c: self.update_setting('outline_color', c))
        card_elem.add_control("Цвет обводки", col_out)
        card_elem.add_control("Толщина обводки", self.create_slider('outline_width', 0, 5))
        layout.addWidget(card_elem)
        card_fx = SettingCard("RGB ЭФФЕКТЫ")
        sw_rain, sw_dyn = DiscordSwitch(), DiscordSwitch()
        sw_rain.setChecked(self.settings.get('rainbow_mode', False))
        sw_dyn.setChecked(self.settings.get('dynamic_color', False))
        def on_rain(v):
            if v: sw_dyn.setChecked(False)
            self.update_setting('rainbow_mode', v)
        def on_dyn(v):
            if v: sw_rain.setChecked(False)
            self.update_setting('dynamic_color', v)
        sw_rain.toggled.connect(on_rain); sw_dyn.toggled.connect(on_dyn)
        card_fx.add_control("Радужный режим", sw_rain); card_fx.add_control("Динамический цвет", sw_dyn)
        layout.addWidget(card_fx)
        layout.addStretch()
        return page

    def create_system_page(self):
        page, layout = self.create_scrollable_page()
        card_mon = SettingCard("МОНИТОР И ОВЕРЛЕЙ")
        sz_row = QWidget()
        sl = QHBoxLayout(sz_row); sl.setContentsMargins(0,0,0,0)
        w_sp, h_sp = QSpinBox(), QSpinBox()
        w_sp.setRange(800, 7680); w_sp.setValue(self.settings.get('screen_width', 1920)); w_sp.setFixedWidth(90)
        h_sp.setRange(600, 4320); h_sp.setValue(self.settings.get('screen_height', 1080)); h_sp.setFixedWidth(90)
        w_sp.valueChanged.connect(lambda v: self.update_setting('screen_width', v))
        h_sp.valueChanged.connect(lambda v: self.update_setting('screen_height', v))
        sl.addWidget(w_sp); sl.addWidget(QLabel(" x ")); sl.addWidget(h_sp); sl.addStretch()
        card_mon.add_control("Разрешение экрана", sz_row)
        layout.addWidget(card_mon)
        card_beh = SettingCard("ПОВЕДЕНИЕ И КЛАВИШИ")
        rmb_combo = NoScrollComboBox()
        for k, v in {'disabled': 'Ничего', 'hold': 'Скрывать (Hold)', 'toggle': 'Переключать (Toggle)'}.items(): rmb_combo.addItem(v, k)
        rmb_combo.setCurrentIndex(rmb_combo.findData(self.settings.get('rmb_hide_mode', 'disabled')))
        rmb_combo.currentIndexChanged.connect(lambda: [self.settings.set('rmb_hide_mode', rmb_combo.currentData()), self.overlay.refresh(), self.mark_dirty()])
        card_beh.add_control("Режим ПКМ", rmb_combo)
        hk_combo = NoScrollComboBox()
        for k in self.overlay.VK_MAP.keys(): hk_combo.addItem(k)
        hk_combo.setCurrentText(self.settings.get('hotkey', 'Insert'))
        hk_combo.currentTextChanged.connect(self.change_hotkey)
        card_beh.add_control("Горячая клавиша", hk_combo, "Клавиша быстрого скрытия прицела")
        sw_auto = DiscordSwitch()
        sw_auto.setChecked(self.settings.get('autostart', False))
        sw_auto.toggled.connect(self.toggle_autostart)
        card_beh.add_control("Автозапуск", sw_auto, "Запускать вместе с Windows")
        sw_min = DiscordSwitch()
        sw_min.setChecked(self.settings.get('start_minimized', False))
        sw_min.toggled.connect(self.toggle_minimized)
        card_beh.add_control("Скрытый запуск", sw_min, "Запускать свернутым в трей")
        
        sw_upd = DiscordSwitch()
        sw_upd.setChecked(self.settings.get('check_updates', True))
        sw_upd.toggled.connect(lambda v: [self.update_setting('check_updates', v)])
        card_beh.add_control("Авто-обновление", sw_upd, "Уведомлять о новых версиях")
        
        layout.addWidget(card_beh)
        layout.addStretch()
        return page

    def change_hotkey(self, key_name):
        self.settings.set('hotkey', key_name)
        self.overlay.update_hotkey()
        self.mark_dirty()

    def toggle_autostart(self, state):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = None
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            if state:
                if getattr(sys, 'frozen', False): path = f'"{sys.executable}"'
                else: path = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'
                winreg.SetValueEx(key, "CrossHud_PetyaBlatnoy", 0, winreg.REG_SZ, path)
            else:
                try: winreg.DeleteValue(key, "CrossHud_PetyaBlatnoy")
                except FileNotFoundError: pass
            self.settings.set('autostart', state)
            self.mark_dirty()
        except Exception:
            logging.exception("Failed to update autostart")
            self.settings.set('autostart', not state)
            sender = self.sender()
            if sender and hasattr(sender, "blockSignals"):
                sender.blockSignals(True)
                sender.setChecked(not state)
                sender.blockSignals(False)
            self.show_warning("Не удалось изменить автозапуск")
        finally:
            if key:
                winreg.CloseKey(key)
            
    def toggle_minimized(self, state):
        self.settings.set('start_minimized', state)
        self.mark_dirty()

    def create_pixel_page(self):
        page, layout = self.create_scrollable_page()
        card = SettingCard("КАСТОМНЫЙ ПРИЦЕЛ")
        self.editor = PixelEditor(self.settings)
        self.editor.on_apply.connect(lambda: [self.overlay.refresh(), self.mark_dirty()])
        ed_c = QWidget(); l_ed = QHBoxLayout(ed_c); l_ed.setContentsMargins(0,0,0,0); l_ed.addWidget(self.editor)
        card.add_row(ed_c)
        sw_use = DiscordSwitch()
        sw_use.setChecked(self.settings.get('pixel_perfect', False))
        sw_use.toggled.connect(lambda v: self.update_setting('pixel_perfect', v))
        card.add_control("Включить режим", sw_use)
        layout.addWidget(card)
        card_tpl = SettingCard("ШАБЛОНЫ")
        tpl_r = QWidget(); l_tpl = QHBoxLayout(tpl_r); l_tpl.setContentsMargins(0,0,0,0); l_tpl.setSpacing(10)
        self.combo_tpl = NoScrollComboBox()
        self.refresh_template_combo()
        b_l, b_d, b_s = QPushButton("Загрузить"), QPushButton("Удалить"), QPushButton("Сохранить")
        b_d.setObjectName("GhostButton"); b_s.setObjectName("GhostButton")
        b_l.clicked.connect(self.load_from_combo); b_d.clicked.connect(self.delete_from_combo); b_s.clicked.connect(self.save_template)
        l_tpl.addWidget(self.combo_tpl, 1); l_tpl.addWidget(b_l); l_tpl.addWidget(b_s); l_tpl.addWidget(b_d)
        card_tpl.add_row(tpl_r)
        layout.addWidget(card_tpl)
        layout.addStretch()
        return page

    def create_logs_page(self):
        page = QWidget(); l = QVBoxLayout(page); l.setContentsMargins(20, 20, 20, 20)
        self.logger_tab = LoggerTab()
        l.addWidget(self.logger_tab)
        return page

    def create_slider(self, key, min_v, max_v, float_scale=False, extra_callback=None):
        c = QWidget(); l = QHBoxLayout(c); l.setContentsMargins(0, 0, 0, 0); l.setSpacing(15)
        val = self.settings.get(key, min_v)
        s = ModernSlider(Qt.Horizontal)
        if float_scale: s.setRange(min_v, max_v); s.setValue(int(val * 100))
        else: s.setRange(min_v, max_v); s.setValue(int(val))
        s.setFixedWidth(150)
        lbl = QLabel(str(s.value() / 100.0 if float_scale else s.value()))
        lbl.setFixedWidth(30); lbl.setAlignment(Qt.AlignCenter); lbl.setStyleSheet("color: #dbdee1; font-weight: bold;")
        def on_c(v):
            rv = v / 100.0 if float_scale else v
            lbl.setText(str(rv)); self.update_setting(key, rv)
            if extra_callback: extra_callback()
        s.valueChanged.connect(on_c); l.addWidget(lbl); l.addWidget(s)
        return c

    def update_setting(self, key, value): 
        logging.info(f"Setting updated: {key} = {value}")
        self.settings.set(key, value)
        self.overlay.refresh()
        self.mark_dirty()

    def update_enable_switch(self, state): self.sw_enable.blockSignals(True); self.sw_enable.setChecked(state); self.sw_enable.blockSignals(False)
    
    def toggle_enable(self, checked):
        self.settings.set('enabled', checked)
        if checked: self.overlay.show()
        else: self.overlay.hide()
        self.mark_dirty()

    def save_settings(self): 
        include_custom_pixels = self.ask_custom_pixels_save("Сохранение настроек")
        if include_custom_pixels is None:
            return
        if not self.settings.save_settings(include_custom_pixels=include_custom_pixels):
            self.show_warning("Не удалось сохранить настройки")
            return
        self.unsaved_bar.hide_animated(self.rect()) 
        self.success_bar.show_message("Настройки сохранены", self.rect())

    def confirm_save_custom_pixels_on_exit(self):
        include_custom_pixels = self.ask_custom_pixels_save("Выход из CrossHud")
        if include_custom_pixels is None:
            return False
        if not self.settings.save_settings(include_custom_pixels=include_custom_pixels):
            self.show_warning("Не удалось сохранить настройки")
            return False
        return True

    def ask_custom_pixels_save(self, title):
        if not self.settings.has_unsaved_custom_pixels():
            return False
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText("Пиксельный прицел изменен. Сохранить его вместе с настройками?")
        save_btn = box.addButton("Сохранить прицел", QMessageBox.AcceptRole)
        discard_btn = box.addButton("Не сохранять", QMessageBox.DestructiveRole)
        cancel_btn = box.addButton("Отмена", QMessageBox.RejectRole)
        box.setDefaultButton(save_btn)
        box.exec()
        clicked = box.clickedButton()
        if clicked == save_btn:
            return True
        if clicked == discard_btn:
            return False
        if clicked == cancel_btn:
            return None
        return None

    def refresh_template_combo(self):
        self.combo_tpl.clear()
        for t in self.settings.get('custom_templates', []): self.combo_tpl.addItem(t['name'], t)
    
    def load_from_combo(self):
        idx = self.combo_tpl.currentIndex()
        if idx >= 0:
            d = self.combo_tpl.itemData(idx)
            self.settings.set('custom_pixels', d['pixels']); self.editor.load_current_design(); self.overlay.refresh(); self.mark_dirty()
            
    def delete_from_combo(self):
        idx = self.combo_tpl.currentIndex()
        if idx >= 0:
            d = self.combo_tpl.itemData(idx)
            if QMessageBox.question(self, "Удаление", f"Удалить шаблон '{d['name']}'?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                self.settings.delete_template(d); self.settings.load_templates_from_disk(); self.refresh_template_combo()
                
    def save_template(self):
        text, ok = QInputDialog.getText(self, "Сохранение", "Имя шаблона:")
        if ok and text: 
            self.settings.save_template({'name': text, 'pixels': self.settings.get('custom_pixels', [])}); self.settings.load_templates_from_disk(); self.refresh_template_combo()
    
    def on_resolution_change(self): pass
