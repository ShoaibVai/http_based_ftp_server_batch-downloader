# main.py
# This is the main entry point for the FTP Batch Downloader application.

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QProgressBar
from PyQt5.QtCore import Qt

# Before importing our modules, ensure the necessary directories exist.
# This helps prevent import errors if the script is run from a clean state.
if not os.path.exists('logs'):
    os.makedirs('logs')
if not os.path.exists('config'):
    os.makedirs('config')
if not os.path.exists('core'):
    os.makedirs('core')
if not os.path.exists('ui'):
    os.makedirs('ui')
if not os.path.exists('utils'):
    os.makedirs('utils')

from ui.main_window import MainWindow

def main():
    """
    Initializes and runs the PyQt5 application.
    """
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
