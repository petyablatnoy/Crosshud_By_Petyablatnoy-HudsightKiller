from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QComboBox, QCheckBox, QPushButton
from PySide6.QtCore import Signal, QObject, Slot
import html
import logging
import sys
from datetime import datetime

class LogSignal(QObject):
    log_received = Signal(object)

class QueueHandler(logging.Handler):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def emit(self, record):
        self.signal.log_received.emit(record)

class StreamToLogger(object):
    def __init__(self, logger):
        self.logger = logger

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            if not line.strip(): continue
            lower = line.lower()
            if "warning" in lower:
                lvl = logging.WARNING
            elif "error" in lower or "exception" in lower or "fatal" in lower:
                lvl = logging.ERROR
            else:
                lvl = logging.INFO
            self.logger.log(lvl, line.rstrip())

    def flush(self):
        pass

class LoggerTab(QWidget):
    _original_stderr = None

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self.level_combo = QComboBox()
        self.level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.level_combo.setCurrentText("INFO")
        self.level_combo.currentTextChanged.connect(self.set_level)
        self.auto_scroll = QCheckBox("Auto Scroll")
        self.auto_scroll.setChecked(True)
        btn_clear = QPushButton("Clear")
        btn_clear.setFixedWidth(80)
        btn_clear.clicked.connect(self.clear_log)
        top.addWidget(self.level_combo)
        top.addWidget(self.auto_scroll)
        top.addStretch()
        top.addWidget(btn_clear)
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        layout.addLayout(top)
        layout.addWidget(self.text_area)
        self.log_signal = LogSignal()
        self.log_signal.log_received.connect(self.append_log)
        self.handler = QueueHandler(self.log_signal)
        logging.getLogger().addHandler(self.handler)
        self.set_level("INFO")
        self.stderr_stream = StreamToLogger(logging.getLogger('SYSTEM'))
        if not isinstance(sys.stderr, StreamToLogger):
            LoggerTab._original_stderr = sys.stderr
            sys.stderr = self.stderr_stream
        self.destroyed.connect(lambda *_: self.cleanup())

    def set_level(self, text):
        logging.getLogger().setLevel(getattr(logging, text))

    def clear_log(self):
        self.text_area.clear()

    def cleanup(self):
        root_logger = logging.getLogger()
        if getattr(self, 'handler', None) in root_logger.handlers:
            root_logger.removeHandler(self.handler)
        if sys.stderr is getattr(self, 'stderr_stream', None) and LoggerTab._original_stderr:
            sys.stderr = LoggerTab._original_stderr

    @Slot(object)
    def append_log(self, record):
        t = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        msg = html.escape(f"[{t}] {record.levelname}: {record.getMessage()}")
        color = "#dbdee1"
        if record.levelno >= logging.ERROR:
            color = "#ed4245"
        elif record.levelno == logging.WARNING:
            color = "#faa61a"
        elif record.levelno == logging.DEBUG:
            color = "#72767d"
        self.text_area.append(f'<span style="color:{color};">{msg}</span>')
        if self.auto_scroll.isChecked():
            sb = self.text_area.verticalScrollBar()
            sb.setValue(sb.maximum())
