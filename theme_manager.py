class ThemeManager:
    @staticmethod
    def get_stylesheet():
        return """
        * {
            font-family: 'gg sans', 'Segoe UI', sans-serif;
            font-size: 13px;
            border: none;
            outline: none;
        }
        QMainWindow { background-color: transparent; }
        QWidget#MainContent {
            background-color: #313338;
            color: #dbdee1;
            border-radius: 16px;
            border: 1px solid #1e1f22;
        }
        QDialog {
            background-color: #313338;
            color: #dbdee1;
            border: 1px solid #1e1f22;
        }
        QColorDialog {
            background-color: #313338;
            color: #dbdee1;
        }
        QColorDialog QWidget {
            background-color: #313338;
            color: #dbdee1;
        }
        QColorDialog QPushButton {
            background-color: #4e5058;
            border: 1px solid #404249;
            margin: 5px;
            padding: 6px 12px;
        }
        QColorDialog QLabel {
            background-color: transparent;
            color: #949ba4;
            font-weight: bold;
        }
        QColorDialog QSpinBox {
            background-color: #111214;
            border: 1px solid #1e1f22;
            border-radius: 4px;
        }
        QWidget#Sidebar {
            background-color: #2b2d31;
            border-bottom-left-radius: 16px;
        }
        QPushButton#TitleBtn, QPushButton#TitleBtnClose {
            background-color: transparent;
            border: none !important;
            outline: none !important;
            border-radius: 0px;
        }
        QPushButton#TitleBtnClose { border-top-right-radius: 16px; }
        QPushButton#TitleBtn:hover { background-color: #3f4147; }
        QPushButton#TitleBtnClose:hover { background-color: #ed4245; }
        QLabel#LogoLabel {
            font-family: 'Segoe UI Black', sans-serif;
            font-weight: 900;
            font-size: 24px;
            color: #f2f3f5;
            padding: 25px 15px 25px 15px;
            letter-spacing: 1px;
        }
        QFrame#Card {
            background-color: #2b2d31;
            border-radius: 12px;
            margin-bottom: 12px;
            border: 1px solid #1f2023;
        }
        QLabel#CardTitle {
            color: #949ba4; font-size: 11px; font-weight: 700;
            margin-bottom: 4px; letter-spacing: 0.5px;
        }
        QLabel#ControlLabel { color: #f2f3f5; font-size: 14px; font-weight: 500; }
        QLabel#DescriptionLabel { color: #b5bac1; font-size: 12px; }
        QPushButton#NavButton {
            background-color: transparent;
            text-align: left;
            padding: 10px 12px;
            color: #949ba4;
            font-size: 15px;
            font-weight: 600;
            border-radius: 6px;
            margin: 4px 8px;
            border: 1px solid transparent; 
        }
        QPushButton#NavButton:hover { background-color: #35373c; color: #dbdee1; }
        QPushButton#NavButton[active="true"] { background-color: #404249; color: #ffffff; }
        QPushButton {
            background-color: #5865f2; color: white;
            border-radius: 4px; padding: 8px 20px;
            font-weight: 600; font-size: 13px;
            border: 1px solid #4752c4;
        }
        QPushButton:hover { background-color: #4752c4; border-color: #3c45a5; }
        QPushButton:pressed { background-color: #3c45a5; border-color: #2d3480; }
        QPushButton#GhostButton { background-color: #4e5058; border-color: #404249; }
        QPushButton#GhostButton:hover { background-color: #6d6f78; border-color: #5a5d65; }
        QLineEdit, QSpinBox, QComboBox {
            background-color: #0b0c0e; color: #f2f3f5;
            border: 1px solid #1f2023; border-radius: 4px;
            padding: 8px; font-weight: 500;
            selection-background-color: #5865f2;
        }
        QLineEdit:hover, QSpinBox:hover, QComboBox:hover { border-color: #4e5058; }
        QLineEdit:focus, QSpinBox:focus, QComboBox:focus { border-color: #5865f2; background-color: #000000; }
        QSpinBox::up-button, QSpinBox::down-button { width: 0px; border: none; }
        QComboBox::drop-down { border: none; width: 24px; }
        QComboBox QAbstractItemView {
            background-color: #2b2d31; color: #dbdee1;
            selection-background-color: #5865f2; selection-color: white;
            border: 1px solid #1e1f22; outline: none; padding: 4px;
        }
        QScrollArea { background: transparent; border: none; }
        QScrollBar:vertical {
            background-color: #2b2d31;
            width: 10px;
            margin: 16px 0px 16px 0px; 
            border-radius: 5px;
            border: none;
        }
        QScrollBar::handle:vertical {
            background-color: #1a1b1e;
            min-height: 40px;
            border-radius: 5px;
            margin: 0px;
        }
        QScrollBar::handle:vertical:hover { background-color: #111214; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical, QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical,
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none; height: 0px; border: none;
        }
        QTextEdit {
            background-color: #0b0c0e; color: #00fa9a;
            border: 1px solid #1f2023; border-radius: 8px;
            padding: 12px; font-family: 'Consolas', monospace; font-size: 12px;
        }
        QWidget#UnsavedBar {
            background-color: #111214;
            border-radius: 8px;
            border: 1px solid #1e1f22;
        }
        QLabel#UnsavedLabel {
            color: #f2f3f5;
            font-weight: bold;
            font-size: 14px;
        }
        QPushButton#SaveButton {
            background-color: #23a559;
            border: 1px solid #23a559;
            color: white;
        }
        QPushButton#SaveButton:hover { background-color: #1a7f42; border-color: #1a7f42; }
        QPushButton#ResetButton {
            background-color: transparent;
            color: #dbdee1;
            border: none;
        }
        QPushButton#ResetButton:hover { text-decoration: underline; }
        """
        