from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton
from PyQt5.QtCore import pyqtSignal

class SettingsTab(QWidget):
    # Signals to update config
    concurrent_changed = pyqtSignal(int)
    depth_changed = pyqtSignal(int)
    view_log = pyqtSignal()

    def __init__(self, concurrent, depth, parent=None):
        super().__init__(parent)
        self.init_ui(concurrent, depth)

    def init_ui(self, concurrent, depth):
        layout = QVBoxLayout(self)
        # Concurrent downloads
        hbox1 = QHBoxLayout()
        hbox1.addWidget(QLabel("Concurrent Downloads:"))
        self.concurrent_spinbox = QSpinBox()
        self.concurrent_spinbox.setRange(1, 16)
        self.concurrent_spinbox.setValue(concurrent)
        self.concurrent_spinbox.valueChanged.connect(self.concurrent_changed.emit)
        hbox1.addWidget(self.concurrent_spinbox)
        layout.addLayout(hbox1)
        # Listing depth
        hbox2 = QHBoxLayout()
        hbox2.addWidget(QLabel("Listing Depth:"))
        self.depth_spinbox = QSpinBox()
        self.depth_spinbox.setRange(1, 10)
        self.depth_spinbox.setValue(depth)
        self.depth_spinbox.valueChanged.connect(self.depth_changed.emit)
        hbox2.addWidget(self.depth_spinbox)
        layout.addLayout(hbox2)
        # Log viewer
        self.log_btn = QPushButton("View Log")
        self.log_btn.clicked.connect(self.view_log.emit)
        layout.addWidget(self.log_btn)
        layout.addStretch() 