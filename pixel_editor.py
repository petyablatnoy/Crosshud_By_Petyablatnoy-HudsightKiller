from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QColorDialog, QLabel, QScrollArea
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QMouseEvent, QWheelEvent
from qt_widgets import DarkColorDialog

class CanvasWidget(QWidget):
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings = settings_manager
        self.min_zoom = 3
        self.max_zoom = self.min_zoom + 3 
        self.zoom = self.max_zoom 
        self.current_color = "#00FF00"
        self.pixels = {} 
        self.drawing = False
        self.erasing = False
        self.panning = False
        self.last_pan_pos = QPoint()
        self.grid_size = 101
        self.update_geometry_size()
        self.load_pixels()

    def update_grid_size(self):
        self.grid_size = 101
        self.update_geometry_size()
        self.update()

    def update_geometry_size(self):
        self.setFixedSize(self.grid_size * self.zoom, self.grid_size * self.zoom)

    def wheelEvent(self, e: QWheelEvent):
        if e.modifiers() & Qt.ControlModifier:
            delta = e.angleDelta().y()
            if delta > 0:
                self.zoom += 1
            else:
                self.zoom -= 1
            self.zoom = max(self.min_zoom, min(self.max_zoom, self.zoom))
            self.update_geometry_size()
            self.update()
            e.accept()
        else:
            e.ignore()

    def load_pixels(self):
        saved = self.settings.get('custom_pixels', [])
        center = self.grid_size // 2
        self.pixels = {}
        for px, py, c in saved:
            self.pixels[(center + px, center + py)] = c
        self.update()

    def save_pixels(self):
        center = self.grid_size // 2
        res = []
        for (x, y), c in self.pixels.items():
            res.append([x - center, y - center, c])
        self.settings.set('custom_pixels', res)

    def get_parent_scroll_area(self):
        p = self.parent()
        while p:
            if isinstance(p, QScrollArea):
                return p
            p = p.parent()
        return None

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.MiddleButton:
            self.panning = True
            self.last_pan_pos = e.globalPosition().toPoint()
            self.setCursor(Qt.ClosedHandCursor)
            e.accept()
        elif e.button() == Qt.LeftButton:
            self.drawing = True
            self.modify_pixel(e.pos())
        elif e.button() == Qt.RightButton:
            self.erasing = True
            self.modify_pixel(e.pos())

    def mouseMoveEvent(self, e: QMouseEvent):
        if self.panning:
            delta = e.globalPosition().toPoint() - self.last_pan_pos
            self.last_pan_pos = e.globalPosition().toPoint()
            scroll_area = self.get_parent_scroll_area()
            if scroll_area:
                hb = scroll_area.horizontalScrollBar()
                vb = scroll_area.verticalScrollBar()
                hb.setValue(hb.value() - delta.x())
                vb.setValue(vb.value() - delta.y())
            e.accept()
        elif self.drawing or self.erasing:
            self.modify_pixel(e.pos())

    def mouseReleaseEvent(self, e: QMouseEvent):
        if e.button() == Qt.MiddleButton:
            self.panning = False
            self.setCursor(Qt.ArrowCursor)
        elif e.button() in (Qt.LeftButton, Qt.RightButton):
            self.drawing = False
            self.erasing = False
            self.save_pixels()

    def modify_pixel(self, pos: QPoint):
        x = pos.x() // self.zoom
        y = pos.y() // self.zoom
        if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
            if self.drawing:
                self.pixels[(x, y)] = self.current_color
            elif self.erasing:
                if (x, y) in self.pixels:
                    del self.pixels[(x, y)]
            self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#1e1f22"))
        pen = QPen(QColor("#2b2d31"))
        pen.setWidth(1)
        p.setPen(pen)
        if self.zoom >= 4:
            for i in range(self.grid_size + 1):
                line_pos = i * self.zoom
                p.drawLine(line_pos, 0, line_pos, self.height())
                p.drawLine(0, line_pos, self.width(), line_pos)
        center_px = (self.grid_size // 2) * self.zoom
        p.setPen(QPen(QColor("#404249"), 2))
        p.drawRect(center_px, center_px, self.zoom, self.zoom)
        p.setPen(Qt.NoPen)
        for (x, y), c in self.pixels.items():
            p.setBrush(QColor(c))
            p.drawRect(x * self.zoom + 1, y * self.zoom + 1, self.zoom - 1, self.zoom - 1)

    def clear(self):
        self.pixels.clear()
        self.update()
        self.save_pixels()
        
    def pick_color(self):
        dlg = DarkColorDialog(QColor(self.canvas.current_color), self)
        if dlg.exec():
            c = dlg.selectedColor()
            if c.isValid():
                self.canvas.current_color = c.name()
                self.update_color_btn()

class PixelEditor(QWidget):
    on_apply = Signal()

    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings = settings_manager
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        self.canvas = CanvasWidget(settings_manager)
        layout.addWidget(self.canvas)
        controls = QVBoxLayout()
        controls.setAlignment(Qt.AlignTop)
        controls.setSpacing(10)
        self.color_btn = QPushButton("Цвет кисти")
        self.color_btn.clicked.connect(self.pick_color)
        self.update_color_btn()
        btn_clear = QPushButton("Очистить")
        btn_clear.clicked.connect(self.clear)
        btn_apply = QPushButton("Применить")
        btn_apply.clicked.connect(self.apply)
        controls.addWidget(self.color_btn)
        controls.addWidget(btn_clear)
        controls.addWidget(btn_apply)
        help_lbl = QLabel("ЛКМ - Рисовать\nПКМ - Стереть\nСр.Кн - Двигать\nCtrl+Scroll - Зум")
        help_lbl.setStyleSheet("color: gray; font-size: 11px;")
        controls.addWidget(help_lbl)
        controls.addStretch()
        layout.addLayout(controls)

    def pick_color(self):
        dlg = DarkColorDialog(QColor(self.canvas.current_color), self)
        if dlg.exec():
            c = dlg.selectedColor()
            if c.isValid():
                self.canvas.current_color = c.name()
                self.update_color_btn()

    def update_color_btn(self):
        fg_color = 'black' if QColor(self.canvas.current_color).lightness() > 128 else 'white'
        self.color_btn.setStyleSheet(f"""
            background-color: {self.canvas.current_color}; 
            color: {fg_color}; 
            border: 1px solid #404249;
        """)

    def apply(self):
        self.canvas.save_pixels()
        self.on_apply.emit()

    def clear(self):
        self.canvas.clear()
        self.on_apply.emit()
    
    def load_current_design(self):
        self.canvas.load_pixels()
    
    def open_editor(self):
        pass
    
    def update_grid_size(self):
        self.canvas.update_grid_size()
