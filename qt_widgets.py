from PySide6.QtWidgets import (QWidget, QCheckBox, QSlider, QLabel, QHBoxLayout, QVBoxLayout, 
                               QFrame, QGridLayout, QPushButton, QComboBox, QScrollArea, QScrollBar, QColorDialog, QDialog)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, Property, QSize, Signal, QPoint, QEvent, QTimer
from PySide6.QtGui import QPainter, QColor, QBrush, QPaintEvent, QPen, QIcon, QWheelEvent, QFontMetrics
import logging

class SmoothScrollBar(QScrollBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.anim = QPropertyAnimation(self, b"value")
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.setDuration(250)
    def wheelEvent(self, e): super().wheelEvent(e)

class FastSmoothScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scroll_bar = SmoothScrollBar()
        self.setVerticalScrollBar(self._scroll_bar)
    def wheelEvent(self, e: QWheelEvent):
        if e.modifiers() != Qt.NoModifier:
            super().wheelEvent(e); return
        delta = e.angleDelta().y()
        if delta == 0: return
        scrollbar = self.verticalScrollBar()
        current = scrollbar.value()
        start = scrollbar.anim.endValue() if scrollbar.anim.state() == QPropertyAnimation.Running else current
        step = 150
        target = max(scrollbar.minimum(), min(scrollbar.maximum(), start - step if delta > 0 else start + step))
        if target != current:
            scrollbar.anim.stop(); scrollbar.anim.setStartValue(current); scrollbar.anim.setEndValue(target); scrollbar.anim.start()
        e.accept()

class WindowButton(QPushButton):
    def __init__(self, btn_type, parent=None):
        super().__init__(parent)
        self.btn_type = btn_type 
        self.setFixedSize(40, 28)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("TitleBtn" if btn_type == 'min' else "TitleBtnClose")
        self.setFocusPolicy(Qt.NoFocus)
    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        from PySide6.QtWidgets import QStyleOptionButton, QStyle
        opt = QStyleOptionButton(); opt.initFrom(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)
        p.setPen(QPen(QColor("white") if self.underMouse() else QColor("#b5bac1"), 1.5))
        w, h = self.width(), self.height(); cx, cy = w / 2, h / 2
        if self.btn_type == 'min': p.drawLine(cx - 5, cy + 1, cx + 5, cy + 1)
        elif self.btn_type == 'close': p.drawLine(cx - 4, cy - 4, cx + 4, cy + 4); p.drawLine(cx + 4, cy - 4, cx - 4, cy + 4)

class CustomTitleBar(QWidget):
    def __init__(self, parent=None, title="", show_btns=True):
        super().__init__(parent); self.setFixedHeight(28); self.setStyleSheet("background-color: transparent;") 
        layout = QHBoxLayout(self); layout.setContentsMargins(15, 0, 0, 0); layout.setSpacing(0)
        if title:
            self.lbl = QLabel(title); self.lbl.setStyleSheet("color: #949ba4; font-weight: bold; font-size: 11px; text-transform: uppercase;")
            layout.addWidget(self.lbl)
        layout.addStretch()
        if show_btns:
            self.btn_min = WindowButton('min'); self.btn_min.clicked.connect(self.window().showMinimized)
            self.btn_close = WindowButton('close'); self.btn_close.clicked.connect(self.window().close)
            layout.addWidget(self.btn_min); layout.addWidget(self.btn_close)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self.window().window_moving = True; self.window().offset = event.position().toPoint()
    def mouseMoveEvent(self, event):
        if hasattr(self.window(), 'window_moving') and self.window().window_moving: self.window().move(event.globalPosition().toPoint() - self.window().offset)
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and not isinstance(self.window(), QDialog):
            if self.window().isMaximized(): self.window().showNormal()
            else: self.window().showMaximized()
    def mouseReleaseEvent(self, event):
        if hasattr(self.window(), 'window_moving'): self.window().window_moving = False

class DarkColorDialog(QColorDialog):
    def __init__(self, initial, parent=None):
        super().__init__(initial, parent); self.setOptions(QColorDialog.DontUseNativeDialog)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog); self.window_moving = False; self.offset = None
        self.setStyleSheet("QColorDialog { background-color: #313338; border: 1px solid #1e1f22; } QColorDialog QWidget { color: #dbdee1; }")
        main_layout = self.layout()
        if main_layout:
            self.title_bar = CustomTitleBar(self, "Выбор цвета", show_btns=False)
            if isinstance(main_layout, QVBoxLayout): main_layout.insertWidget(0, self.title_bar)
            elif isinstance(main_layout, QGridLayout): main_layout.addWidget(self.title_bar, 0, 0, 1, -1)
            main_layout.setContentsMargins(5, 5, 5, 15)

class DarkMessageBox(QDialog):
    def __init__(self, text, parent=None):
        super().__init__(parent); self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog); self.setAttribute(Qt.WA_TranslucentBackground)
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0)
        bg = QFrame(); bg.setObjectName("MsgBoxBG"); bg.setStyleSheet("QFrame#MsgBoxBG { background-color: #313338; border: 1px solid #1e1f22; border-radius: 12px; }")
        layout.addWidget(bg); l_bg = QVBoxLayout(bg); l_bg.setContentsMargins(25, 25, 25, 25); l_bg.setSpacing(20)
        lbl = QLabel(text); lbl.setAlignment(Qt.AlignCenter); lbl.setWordWrap(True); lbl.setStyleSheet("color: #dbdee1; font-size: 14px; font-weight: 500; border: none; background: transparent;")
        l_bg.addWidget(lbl); btn_ok = QPushButton("OK"); btn_ok.setFixedSize(100, 32); btn_ok.setCursor(Qt.PointingHandCursor); btn_ok.setFocusPolicy(Qt.NoFocus)
        btn_ok.setStyleSheet("QPushButton { background-color: #5865f2; color: white; border-radius: 4px; font-weight: bold; font-size: 13px; border: none; } QPushButton:hover { background-color: #4752c4; }")
        btn_ok.clicked.connect(self.accept); l_btn = QHBoxLayout(); l_btn.addStretch(); l_btn.addWidget(btn_ok); l_btn.addStretch(); l_bg.addLayout(l_btn); self.setFixedSize(320, 150)

class UnsavedChangesBar(QFrame):
    saveClicked = Signal()
    resetClicked = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("UnsavedBar")
        self.setFixedSize(340, 50) 
        self.hide()
        self.setStyleSheet("""
            QFrame#UnsavedBar {
                background-color: #111214;
                border-radius: 8px;
                border: 1px solid #ed4245;
            }
            QLabel { color: #f2f3f5; font-size: 13px; font-weight: bold; border: none; background: transparent; }
            QPushButton#ResetBtn { color: #dbdee1; background: transparent; border: none; font-weight: 600; font-size: 12px; }
            QPushButton#ResetBtn:hover { text-decoration: underline; }
            QPushButton#SaveBtn { background-color: #23a559; color: white; border-radius: 4px; font-weight: bold; border: none; padding: 6px 14px; font-size: 12px; }
            QPushButton#SaveBtn:hover { background-color: #1a7f42; }
        """)
        layout = QHBoxLayout(self); layout.setContentsMargins(15, 0, 15, 0); layout.setSpacing(10)
        lbl = QLabel("Не сохранено"); layout.addWidget(lbl); layout.addStretch()
        self.btn_reset = QPushButton("Сброс")
        self.btn_reset.setObjectName("ResetBtn")
        self.btn_reset.setCursor(Qt.PointingHandCursor)
        self.btn_reset.clicked.connect(self.resetClicked.emit)
        self.btn_save = QPushButton("Сохранить")
        self.btn_save.setObjectName("SaveBtn")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.clicked.connect(self.saveClicked.emit)
        layout.addWidget(self.btn_reset); layout.addWidget(self.btn_save)
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.OutBack)

    def show_animated(self, parent_rect):
        tx = parent_rect.width() - self.width() - 20
        ty = parent_rect.height() - self.height() - 20
        target_pos = QPoint(tx, ty)

        if self.isVisible():
            if self.pos() == target_pos: return
            if self.anim.state() == QPropertyAnimation.Running and self.anim.endValue() == target_pos: return
        
        if not self.isVisible():
            self.move(tx, parent_rect.height() + 10)
            self.show()
            self.raise_()

        self.anim.stop()
        self.anim.setStartValue(self.pos())
        self.anim.setEndValue(target_pos)
        
        try: self.anim.finished.disconnect()
        except Exception: logging.debug("No previous unsaved-bar animation callback to disconnect", exc_info=True)
        
        self.anim.start()

    def hide_animated(self, parent_rect):
        if not self.isVisible(): return
        cx = self.pos().x()
        off_y = parent_rect.height() + 10
        self.anim.stop()
        self.anim.setStartValue(self.pos())
        self.anim.setEndValue(QPoint(cx, off_y))
        try: self.anim.finished.disconnect()
        except Exception: logging.debug("No previous unsaved-bar animation callback to disconnect", exc_info=True)
        self.anim.finished.connect(self.hide)
        self.anim.start()

class NotificationBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SuccessBar")
        self.setFixedHeight(50)
        self.setMinimumWidth(260)
        self.setMaximumWidth(520)
        self.hide()
        self.setStyleSheet("""
            QFrame#SuccessBar {
                background-color: #111214;
                border-radius: 8px;
                border: 1px solid #23a559;
            }
            QLabel { color: #f2f3f5; font-size: 13px; font-weight: bold; border: none; background: transparent; }
        """)
        layout = QHBoxLayout(self); layout.setContentsMargins(16, 0, 16, 0)
        self.lbl = QLabel("Сохранено"); self.lbl.setAlignment(Qt.AlignCenter)
        self.lbl.setTextFormat(Qt.PlainText)
        layout.addWidget(self.lbl)
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.OutBack)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_animated)
        self.parent_rect_cache = None

    def show_message(self, text, parent_rect, kind="success"):
        max_width = max(260, min(520, parent_rect.width() - 40))
        metrics = QFontMetrics(self.lbl.font())
        display_text = metrics.elidedText(text, Qt.ElideRight, max_width - 32)
        self.setFixedWidth(max_width)
        self.lbl.setText(display_text)
        border_color = "#faa61a" if kind == "warning" else "#23a559"
        self.setStyleSheet(f"""
            QFrame#SuccessBar {{
                background-color: #111214;
                border-radius: 8px;
                border: 1px solid {border_color};
            }}
            QLabel {{ color: #f2f3f5; font-size: 13px; font-weight: bold; border: none; background: transparent; }}
        """)
        self.parent_rect_cache = parent_rect
        tx = parent_rect.width() - self.width() - 20
        ty = parent_rect.height() - self.height() - 20
        self.anim.stop()
        self.timer.stop()
        self.move(tx, parent_rect.height() + 10)
        self.show()
        self.raise_()
        try: self.anim.finished.disconnect()
        except Exception: logging.debug("No previous notification animation callback to disconnect", exc_info=True)
        self.anim.setStartValue(self.pos())
        self.anim.setEndValue(QPoint(tx, ty))
        self.anim.start()
        self.timer.start(2000)

    def hide_animated(self):
        if not self.isVisible() or not self.parent_rect_cache: return
        cx = self.pos().x()
        off_y = self.parent_rect_cache.height() + 10
        self.anim.stop()
        self.anim.setStartValue(self.pos())
        self.anim.setEndValue(QPoint(cx, off_y))
        try: self.anim.finished.disconnect()
        except Exception: logging.debug("No previous notification animation callback to disconnect", exc_info=True)
        self.anim.finished.connect(self.hide)
        self.anim.start()

class DiscordSwitch(QWidget):
    toggled = Signal(bool)
    def __init__(self, parent=None):
        super().__init__(parent); self.setFixedSize(42, 26); self.setCursor(Qt.PointingHandCursor); self._checked, self._bg_color, self._circle_pos = False, QColor("#80848e"), 4
    @Property(float)
    def circle_pos(self): return self._circle_pos
    @circle_pos.setter
    def circle_pos(self, pos): self._circle_pos = pos; self.update()
    @Property(QColor)
    def bg_color(self): return self._bg_color
    @bg_color.setter
    def bg_color(self, color): self._bg_color = color; self.update()
    def setChecked(self, checked): self._checked = checked; self.start_animation(); self.toggled.emit(checked)
    def isChecked(self): return self._checked
    def mousePressEvent(self, e): self.setChecked(not self._checked)
    def start_animation(self):
        self.ap = QPropertyAnimation(self, b"circle_pos"); self.ap.setDuration(200); self.ap.setEasingCurve(QEasingCurve.OutQuad)
        self.ap.setStartValue(self._circle_pos); self.ap.setEndValue(20 if self._checked else 4); self.ap.start()
        self.ab = QPropertyAnimation(self, b"bg_color"); self.ab.setDuration(200)
        self.ab.setStartValue(self._bg_color); self.ab.setEndValue(QColor("#23a559") if self._checked else QColor("#80848e")); self.ab.start()
    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing); p.setPen(Qt.NoPen)
        p.setBrush(QBrush(self._bg_color)); p.drawRoundedRect(0, 0, 42, 26, 13, 13)
        p.setBrush(QBrush(QColor("white"))); p.drawEllipse(int(self._circle_pos), 4, 18, 18)

class ModernSlider(QSlider):
    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent); self.setFixedHeight(30)
        self.setStyleSheet("""
            QSlider::groove:horizontal { border: none; height: 8px; background: #4e5058; border-radius: 4px; }
            QSlider::sub-page:horizontal { background: #5865f2; border-radius: 4px; }
            QSlider::handle:horizontal { background: white; border: 2px solid #313338; width: 18px; height: 18px; margin: -5px 0; border-radius: 9px; }
            QSlider::handle:horizontal:hover { background: #f2f3f5; width: 20px; height: 20px; margin: -6px 0; border-radius: 10px; }
        """)
    def wheelEvent(self, event):
        event.ignore()

class NoScrollComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
    def wheelEvent(self, event):
        event.ignore()

class ColorButton(QWidget):
    colorChanged = Signal(str)
    def __init__(self, color, parent=None):
        super().__init__(parent); self.setFixedSize(50, 26); self.color = color; self.setCursor(Qt.PointingHandCursor)
    def set_color(self, c): self.color = c; self.update()
    def mousePressEvent(self, e):
        dlg = DarkColorDialog(QColor(self.color), self)
        if dlg.exec():
            c = dlg.selectedColor()
            if c.isValid(): self.color = c.name(); self.update(); self.colorChanged.emit(self.color)
    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing); p.setPen(QPen(QColor("#1e1f22"), 2)); p.setBrush(QBrush(QColor(self.color)))
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 4, 4)

class SettingCard(QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent); self.setObjectName("Card"); self.setAttribute(Qt.WA_StyledBackground, True) 
        self.ml = QVBoxLayout(self); self.ml.setContentsMargins(20, 20, 20, 20); self.ml.setSpacing(15)
        self.tl = QLabel(title); self.tl.setObjectName("CardTitle"); self.ml.addWidget(self.tl)
        self.grid = QGridLayout(); self.grid.setColumnStretch(0, 1); self.grid.setColumnStretch(1, 0); self.grid.setVerticalSpacing(20); self.grid.setHorizontalSpacing(20)
        self.ml.addLayout(self.grid); self.row_idx = 0
    def add_row(self, widget): self.ml.addWidget(widget)
    def add_control(self, label_text, control_widget, description=None):
        tc = QWidget(); tl = QVBoxLayout(tc); tl.setContentsMargins(0, 0, 0, 0); tl.setSpacing(4)
        lbl = QLabel(label_text); lbl.setObjectName("ControlLabel"); tl.addWidget(lbl)
        if description: ds = QLabel(description); ds.setObjectName("DescriptionLabel"); ds.setWordWrap(True); tl.addWidget(ds)
        self.grid.addWidget(tc, self.row_idx, 0)
        cc = QWidget(); cl = QHBoxLayout(cc); cl.setContentsMargins(0, 0, 0, 0); cl.setAlignment(Qt.AlignRight | Qt.AlignVCenter); cl.addWidget(control_widget)
        self.grid.addWidget(cc, self.row_idx, 1); self.row_idx += 1
