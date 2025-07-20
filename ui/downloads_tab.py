from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QLabel, QTabWidget, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
import os
import subprocess
import shutil
import time

def parse_size(size_str):
    if not size_str or size_str == '-':
        return 0
    size_str = size_str.replace(',', '').strip()
    units = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
    parts = size_str.split()
    if len(parts) == 2:
        num, unit = parts
        try:
            return int(float(num) * units[unit])
        except Exception:
            return 0
    try:
        return int(size_str)
    except Exception:
        return 0

class DownloadsTab(QWidget):
    # Signals for global actions
    pause_all = pyqtSignal()
    resume_all = pyqtSignal()
    cancel_all = pyqtSignal()
    # Signals for per-download actions: (row, action)
    pause_download = pyqtSignal(int)
    resume_download = pyqtSignal(int)
    cancel_download = pyqtSignal(int)
    retry_download = pyqtSignal(int, str)  # row, tab
    open_in_explorer = pyqtSignal(str)     # file path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_progress_times = {}  # For ETA calculation
        self.last_progress_bytes = {}
        self._last_eta = {}  # For persistent ETA display
        self._active_data = ([], [], [], [])
        self._timer = QTimer(self)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self._refresh_ui)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Active Tab
        self.active_tab = QWidget()
        self.active_layout = QVBoxLayout(self.active_tab)
        controls_layout = QHBoxLayout()
        self.pause_all_btn = QPushButton("Pause All")
        self.resume_all_btn = QPushButton("Resume All")
        self.cancel_all_btn = QPushButton("Cancel All")
        controls_layout.addWidget(self.pause_all_btn)
        controls_layout.addWidget(self.resume_all_btn)
        controls_layout.addWidget(self.cancel_all_btn)
        controls_layout.addStretch()
        self.active_layout.addLayout(controls_layout)
        self.active_table = QTableWidget(0, 6)
        self.active_table.setHorizontalHeaderLabels(["File Name", "Status", "Progress", "Size", "ETA", "Actions"])
        self.active_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.active_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.active_layout.addWidget(self.active_table)
        self.tabs.addTab(self.active_tab, "Active")

        # Completed Tab
        self.completed_tab = QWidget()
        self.completed_layout = QVBoxLayout(self.completed_tab)
        self.completed_table = QTableWidget(0, 3)
        self.completed_table.setHorizontalHeaderLabels(["File Name", "Size", "Open"])
        self.completed_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.completed_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.completed_layout.addWidget(self.completed_table)
        self.tabs.addTab(self.completed_tab, "Completed")

        # Failed Tab
        self.failed_tab = QWidget()
        self.failed_layout = QVBoxLayout(self.failed_tab)
        self.failed_table = QTableWidget(0, 4)
        self.failed_table.setHorizontalHeaderLabels(["File Name", "Status", "Size", "Retry"])
        self.failed_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.failed_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.failed_layout.addWidget(self.failed_table)
        self.tabs.addTab(self.failed_tab, "Failed")

        # Canceled Tab
        self.canceled_tab = QWidget()
        self.canceled_layout = QVBoxLayout(self.canceled_tab)
        self.canceled_table = QTableWidget(0, 4)
        self.canceled_table.setHorizontalHeaderLabels(["File Name", "Status", "Size", "Retry"])
        self.canceled_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.canceled_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.canceled_layout.addWidget(self.canceled_table)
        self.tabs.addTab(self.canceled_tab, "Canceled")

        # Connect global buttons
        self.pause_all_btn.clicked.connect(self.pause_all)
        self.resume_all_btn.clicked.connect(self.resume_all)
        self.cancel_all_btn.clicked.connect(self.cancel_all)

    def check_disk_space(self, file_path, file_size):
        try:
            drive = os.path.splitdrive(file_path)[0] or file_path
            total, used, free = shutil.disk_usage(drive)
            return free >= file_size, free
        except Exception:
            return True, None  # If check fails, allow download

    def update_downloads(self, active, completed, failed, canceled):
        self._active_data = (active, completed, failed, canceled)
        if active and not self._timer.isActive():
            self._timer.start()
        elif not active and self._timer.isActive():
            self._timer.stop()
        if not self._timer.isActive():
            self._refresh_ui()

    def _refresh_ui(self):
        active, completed, failed, canceled = self._active_data
        # Active
        self.active_table.setRowCount(len(active))
        now = time.time()
        for row, d in enumerate(active):
            self.active_table.setItem(row, 0, QTableWidgetItem(d['file_name']))
            self.active_table.setItem(row, 1, QTableWidgetItem(d['status']))
            progress_widget = QProgressBar()
            progress_widget.setValue(d['progress'])
            progress_widget.setTextVisible(True)
            self.active_table.setCellWidget(row, 2, progress_widget)
            self.active_table.setItem(row, 3, QTableWidgetItem(d['size']))
            # ETA calculation
            eta_str = self._last_eta.get(d['file_path'], "-")
            if d['status'] == 'Downloading' and d['progress'] > 0 and d['progress'] < 100:
                key = d['file_path']
                total_bytes = parse_size(d['size'])
                bytes_now = d['progress'] * total_bytes // 100 if total_bytes else 0
                if key in self.last_progress_times:
                    elapsed = now - self.last_progress_times[key]
                    bytes_delta = bytes_now - self.last_progress_bytes.get(key, 0)
                    speed = bytes_delta / elapsed if elapsed > 0 else 0
                    if speed > 0:
                        remaining = 100 - d['progress']
                        bytes_left = total_bytes * remaining // 100
                        eta = int(bytes_left / speed)
                        mins, secs = divmod(eta, 60)
                        eta_str = f"{mins}m {secs}s" if mins else f"{secs}s"
                        self._last_eta[key] = eta_str
                self.last_progress_times[key] = now
                self.last_progress_bytes[key] = bytes_now
            self.active_table.setItem(row, 4, QTableWidgetItem(eta_str))
            # Disk space check (only warn once per file)
            if d['status'] == 'Queued' and d['size'] != '-' and not hasattr(self, f'_warned_{d["file_path"]}'):
                file_size = parse_size(d['size'])
                enough, free = self.check_disk_space(d['file_path'], file_size)
                if not enough:
                    QMessageBox.warning(self, "Low Disk Space", f"Not enough disk space for {d['file_name']}!\nRequired: {d['size']}\nFree: {free // (1024*1024)} MB")
                    setattr(self, f'_warned_{d["file_path"]}', True)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            if d['can_pause']:
                pause_btn = QPushButton("Pause")
                pause_btn.clicked.connect(lambda _, r=row: self.pause_download.emit(r))
                actions_layout.addWidget(pause_btn)
            if d['can_resume']:
                resume_btn = QPushButton("Resume")
                resume_btn.clicked.connect(lambda _, r=row: self.resume_download.emit(r))
                actions_layout.addWidget(resume_btn)
            if d['can_cancel']:
                cancel_btn = QPushButton("Cancel")
                cancel_btn.clicked.connect(lambda _, r=row: self.cancel_download.emit(r))
                actions_layout.addWidget(cancel_btn)
            actions_layout.addStretch()
            self.active_table.setCellWidget(row, 5, actions_widget)

        # Completed
        self.completed_table.setRowCount(len(completed))
        for row, d in enumerate(completed):
            self.completed_table.setItem(row, 0, QTableWidgetItem(d['file_name']))
            self.completed_table.setItem(row, 1, QTableWidgetItem(d['size']))
            open_btn = QPushButton("Open")
            open_btn.clicked.connect(lambda _, path=d['file_path']: self.open_in_explorer.emit(path))
            self.completed_table.setCellWidget(row, 2, open_btn)

        # Failed
        self.failed_table.setRowCount(len(failed))
        for row, d in enumerate(failed):
            self.failed_table.setItem(row, 0, QTableWidgetItem(d['file_name']))
            self.failed_table.setItem(row, 1, QTableWidgetItem(d['status']))
            self.failed_table.setItem(row, 2, QTableWidgetItem(d['size']))
            retry_btn = QPushButton("Retry")
            retry_btn.clicked.connect(lambda _, r=row: self.retry_download.emit(r, 'failed'))
            self.failed_table.setCellWidget(row, 3, retry_btn)

        # Canceled
        self.canceled_table.setRowCount(len(canceled))
        for row, d in enumerate(canceled):
            self.canceled_table.setItem(row, 0, QTableWidgetItem(d['file_name']))
            self.canceled_table.setItem(row, 1, QTableWidgetItem(d['status']))
            self.canceled_table.setItem(row, 2, QTableWidgetItem(d['size']))
            retry_btn = QPushButton("Retry")
            retry_btn.clicked.connect(lambda _, r=row: self.retry_download.emit(r, 'canceled'))
            self.canceled_table.setCellWidget(row, 3, retry_btn) 