

import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from gui.app import MainWindow
from gui.pages.about_page import APP_NAME

def _icon_path():

    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "assets", "icon.ico")

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ReviewGather")
    app.setApplicationDisplayName(APP_NAME)
    icon = QIcon(_icon_path())
    app.setWindowIcon(icon)
    window = MainWindow()
    window.setWindowIcon(icon)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()