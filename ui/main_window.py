# ui/main_window.py
# This file defines the main window of the application using PyQt5.

import os
import logging
from functools import partial
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QTreeWidget, QTreeWidgetItem, QProgressBar, QLabel, QFileDialog, QMessageBox, 
    QSplitter, QFrame, QAction, QToolBar, QStatusBar, QSpinBox, QDialog, 
    QTextEdit, QApplication, QStyle, QTreeWidgetItemIterator, QSizePolicy, QTabWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QMovie, QPalette, QColor

from core.lister import DirectoryLister
from core.downloader import DownloadManager
from config.manager import ConfigManager
from utils.logger import setup_logger
from ui.downloads_tab import DownloadsTab
from ui.settings_tab import SettingsTab
from ui.browser_tab import BrowserTab
import sys
import subprocess
from urllib.parse import unquote

logger = setup_logger()

def format_bytes(size):
    """Formats bytes into KB, MB, GB, etc."""
    if size <= 0: return "0 B"
    power, n, labels = 1024, 0, {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size >= power and n < len(labels) -1:
        size /= power
        n += 1
    return f"{size:.2f} {labels[n]}B"

class MainWindow(QMainWindow):
    """The main window for the FTP Batch Downloader application."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FTP Batch Downloader")
        
        # Set window icon
        try:
            self.setWindowIcon(QIcon("resources/icons/favicon.ico"))
        except Exception as e:
            logger.warning(f"Could not load window icon: {e}")
        
        self.setGeometry(100, 100, 1200, 800)
        self.setAcceptDrops(True)
        self.config_manager = ConfigManager()
        self.download_manager = DownloadManager(self.config_manager)
        self.init_ui()
        self.create_toolbars()
        self.create_status_bar()
        self.lister_thread, self.path_to_item_map, self.file_progress_widgets = None, {}, {}
        self.is_downloading = False
        self.connect_signals()
        # Connect download manager to downloads tab
        self.download_manager.downloads_updated.connect(self.update_downloads_tab)
        self.downloads_tab.pause_all.connect(self.download_manager.pause_all)
        self.downloads_tab.resume_all.connect(self.download_manager.resume_all)
        self.downloads_tab.cancel_all.connect(self.download_manager.cancel_all)
        self.downloads_tab.pause_download.connect(lambda row: self._downloads_tab_action(row, 'pause'))
        self.downloads_tab.resume_download.connect(lambda row: self._downloads_tab_action(row, 'resume'))
        self.downloads_tab.cancel_download.connect(lambda row: self._downloads_tab_action(row, 'cancel'))
        self.downloads_tab.retry_download.connect(self._downloads_tab_retry)
        self.downloads_tab.open_in_explorer.connect(self.open_in_explorer)

    def init_ui(self):
        central_widget = QWidget(); self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        # Tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        # Main downloader tab
        self.downloader_tab = QWidget()
        self.init_downloader_tab(self.downloader_tab)
        self.tab_widget.addTab(self.downloader_tab, "Downloader")
        # Downloads tab
        self.downloads_tab = DownloadsTab()
        self.tab_widget.addTab(self.downloads_tab, "Downloads")
        # Settings tab
        theme_name = self.config_manager.get("theme_name", "Colorful")
        self.settings_tab = SettingsTab(
            concurrent=self.config_manager.get("max_concurrent_downloads"),
            depth=self.config_manager.get("listing_depth"),
            theme_name=theme_name
        )
        self.settings_tab.concurrent_changed.connect(lambda val: self.config_manager.set("max_concurrent_downloads", val))
        self.settings_tab.depth_changed.connect(lambda val: self.config_manager.set("listing_depth", val))
        self.settings_tab.view_log.connect(self.show_error_log)
        self.settings_tab.theme_changed.connect(self.apply_theme)
        self.tab_widget.addTab(self.settings_tab, "Settings")
        
        # Browser tab
        self.browser_tab = BrowserTab()
        self.tab_widget.addTab(self.browser_tab, "Browser")
        
        self.apply_theme(theme_name)

    def init_downloader_tab(self, tab_widget):
        main_layout = QVBoxLayout(tab_widget)
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit(); self.url_input.setPlaceholderText("Drag & Drop or Paste FTP/HTTP URL...")
        self.url_input.setClearButtonEnabled(True)
        self.url_input.setMinimumHeight(32)
        self.fetch_button = QPushButton("Fetch"); self.fetch_button.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.fetch_button.setMinimumHeight(32)
        self.cancel_fetch_button = QPushButton("Cancel Fetch"); self.cancel_fetch_button.setEnabled(False)
        self.cancel_fetch_button.setMinimumHeight(32)
        url_layout.addWidget(self.url_input); url_layout.addWidget(self.fetch_button); url_layout.addWidget(self.cancel_fetch_button); main_layout.addLayout(url_layout)
        splitter = QSplitter(Qt.Vertical); main_layout.addWidget(splitter)
        self.tree_widget = QTreeWidget(); self.tree_widget.setHeaderLabels(["Name", "Size", "Type", "Modified"])
        self.tree_widget.setColumnWidth(0, 500); self.tree_widget.setColumnWidth(1, 120); self.tree_widget.setColumnWidth(2, 120)
        self.tree_widget.setAlternatingRowColors(True)
        self.tree_widget.setStyleSheet("QTreeWidget { font-size: 14px; } QTreeWidget::item:selected { background: #e0f7fa; }")
        splitter.addWidget(self.tree_widget)
        # Remove progress_frame and per-file progress bars
        # Remove overall_progress and per_file_progress_layout
        download_controls_layout = QHBoxLayout()
        self.download_path_input = QLineEdit(self.config_manager.get("default_download_path"))
        self.download_path_input.setMinimumHeight(32)
        self.browse_button = QPushButton("Browse..."); self.browse_button.setMinimumHeight(32)
        self.download_button = QPushButton("Download")
        self.download_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowDown))
        self.download_button.setMinimumHeight(32)
        self.download_button.setStyleSheet("QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00bcd4, stop:1 #8bc34a); color: white; border-radius: 8px; font-weight: bold; } QPushButton:hover { background: #26c6da; }")
        download_controls_layout.addWidget(QLabel("Download To:")); download_controls_layout.addWidget(self.download_path_input)
        download_controls_layout.addWidget(self.browse_button); download_controls_layout.addWidget(self.download_button)
        main_layout.addLayout(download_controls_layout)
        self.spinner_label = QLabel()
        self.spinner_label.setFixedSize(32, 32)
        self.spinner_movie = QMovie(":/qt-project.org/styles/commonstyle/images/standardbutton-apply-32.png")
        self.spinner_label.setMovie(self.spinner_movie)
        self.spinner_label.setVisible(False)
        main_layout.addWidget(self.spinner_label, alignment=Qt.AlignRight)
        self.setStyleSheet('''
            QMainWindow { background: #232946; }
            QPushButton {
                border-radius: 8px;
                padding: 6px 16px;
                font-size: 14px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2196F3, stop:1 #FF9800);
                color: #fff;
                font-weight: bold;
            }
            QPushButton:pressed {
                background: #FF9800;
                color: #fff;
            }
            QPushButton:hover {
                background: #4CAF50;
                color: #fff;
            }
            QLineEdit {
                border: 1.5px solid #2196F3;
                border-radius: 8px;
                padding: 4px 8px;
                font-size: 14px;
                background: #393E6B;
                color: #fff;
                selection-background-color: #FF9800;
                selection-color: #232946;
            }
            QLabel {
                font-size: 14px;
                color: #E0E0E0;
            }
            QToolBar {
                background: #232946;
                border-bottom: 2px solid #2196F3;
            }
            QStatusBar {
                background: #232946;
                border-top: 2px solid #2196F3;
                color: #fff;
            }
            QTreeWidget {
                font-size: 14px;
                background: #393E6B;
                color: #fff;
                alternate-background-color: #232946;
            }
            QTreeWidget::item:selected {
                background: #2196F3;
                color: #fff;
            }
            QTreeWidget::item:hover {
                background: #FF9800;
                color: #fff;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2196F3, stop:1 #FF9800);
                color: #fff;
                border: none;
                font-weight: bold;
            }
            QProgressBar {
                border-radius: 8px;
                background: #232946;
                color: #fff;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4CAF50, stop:1 #2196F3);
                border-radius: 8px;
            }
            QTabWidget::pane {
                border: 2px solid #2196F3;
                background: #232946;
            }
            QTabBar::tab {
                background: #393E6B;
                color: #fff;
                padding: 6px 16px;
                min-width: 80px;
                min-height: 28px;
                font-size: 13px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
                margin-right: 4px;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2196F3, stop:1 #FF9800);
                color: #fff;
            }
            QTabBar::tab:hover {
                background: #FF9800;
                color: #fff;
            }
        ''')

    def connect_signals(self):
        self.browse_button.clicked.connect(self.browse_download_path)
        self.download_button.clicked.connect(self.start_download)
        self.fetch_button.clicked.connect(self.fetch_directory_listing)
        self.cancel_fetch_button.clicked.connect(self.cancel_fetch)
        self.tree_widget.itemChanged.connect(self.handle_item_check)
        self.download_manager.file_started.connect(self.on_file_download_started)
        self.download_manager.file_progress.connect(self.on_file_progress)
        self.download_manager.file_finished.connect(self.on_file_download_finished)
        self.download_manager.file_status_changed.connect(self.on_file_status_changed)
        self.download_manager.overall_progress.connect(self.on_overall_progress)
        self.download_manager.all_finished.connect(self.on_all_downloads_finished)
        
        # Connect browser tab signals
        self.browser_tab.url_selected.connect(self.handle_browser_url_selected)
        self.download_manager.error.connect(self.on_download_error)
        self.download_manager.size_calc_progress.connect(self.on_size_calc_progress)
        self.download_manager.size_calc_finished.connect(self.on_size_calc_finished)

    def create_actions(self):
        self.pause_all_action = QAction(self.style().standardIcon(QStyle.SP_MediaPause), "Pause All", self)
        self.resume_all_action = QAction(self.style().standardIcon(QStyle.SP_MediaPlay), "Resume All", self)
        self.cancel_action = QAction(self.style().standardIcon(QStyle.SP_MediaStop), "Cancel All", self)
        self.view_log_action = QAction(self.style().standardIcon(QStyle.SP_FileIcon), "View Log", self)
        self.pause_all_action.triggered.connect(self.download_manager.pause_all)
        self.resume_all_action.triggered.connect(self.download_manager.resume_all)
        self.cancel_action.triggered.connect(self.cancel_downloads)
        self.view_log_action.triggered.connect(self.show_error_log)

    def create_toolbars(self):
        toolbar = QToolBar("Main Toolbar"); self.addToolBar(toolbar)
        # Create view_log_action here (not needed, now in settings tab)
        # Remove concurrent and depth spinboxes from toolbar
        toolbar.addSeparator()

    def create_status_bar(self):
        self.statusBar = QStatusBar(); self.setStatusBar(self.statusBar); self.statusBar.showMessage("Ready")

    def set_ui_state(self, downloading: bool, message: str = ""):
        self.is_downloading = downloading
        # Only disable pause/resume/cancel actions during download
        # (No longer needed: for action in [self.cancel_action, self.pause_all_action, self.resume_all_action]: action.setEnabled(downloading))
        # Do NOT disable download_button, url_input, or browse_button during downloads
        # Only disable fetch/cancel fetch buttons as needed (handled elsewhere)
        if downloading:
            self.spinner_label.setVisible(True)
            self.spinner_movie.start()
        else:
            self.spinner_label.setVisible(False)
            self.spinner_movie.stop()
        if message: self.statusBar.showMessage(message)

    def start_download(self):
        # Allow queuing new downloads even if already downloading
        selected_files = self.get_checked_items()
        if not selected_files: self.show_message("No Files", "Please select files to download.", QMessageBox.Warning); return
        download_path = self.download_path_input.text()
        if not os.path.isdir(download_path): self.show_message("Invalid Path", "Download directory does not exist.", QMessageBox.Critical); return
        # Create a folder named after the selected directory (unless already exists)
        root_url = self.url_input.text().strip()
        root_dir_name = unquote(os.path.basename(root_url.rstrip('/')))
        base_folder = os.path.join(download_path, root_dir_name)
        os.makedirs(base_folder, exist_ok=True)
        self.set_ui_state(True, "Calculating total download size...")
        # Do NOT clear previous progress widgets or layout here
        # Only add new widgets for new files in on_file_download_started
        # Pass (url, rel_path) and base_folder to the download manager
        self.download_manager.start_downloads(selected_files, base_folder)

    def on_size_calc_progress(self, processed, total): self.statusBar.showMessage(f"Calculating size... ({processed}/{total} files)")
    def on_size_calc_finished(self): self.statusBar.showMessage("Starting downloads...")

    def on_overall_progress(self, downloaded_bytes, total_bytes):
        self.statusBar.showMessage(f"Downloading... {format_bytes(downloaded_bytes)} / {format_bytes(total_bytes)}")

    def on_all_downloads_finished(self):
        if self.is_downloading:
            self.statusBar.showMessage("All downloads finished.", 5000)
            # Removed: if self.overall_progress.value() >= self.overall_progress.maximum():
            # Removed: self.show_message("Complete", "All downloads completed successfully.", QMessageBox.Information)
        self.set_ui_state(False, "Ready")
        # Removed: self.overall_progress.setValue(0); self.overall_progress.setFormat("%p%")

    def on_file_download_started(self, worker_id, filename):
        # No per-file progress UI in main window anymore
        pass

    def on_file_progress(self, worker_id, downloaded_bytes, total_bytes):
        if worker_id in self.file_progress_widgets:
            widgets = self.file_progress_widgets[worker_id]
            if total_bytes > 0:
                if widgets['progress'].maximum() != total_bytes: widgets['progress'].setMaximum(total_bytes)
                widgets['progress'].setValue(downloaded_bytes)
                widgets['progress'].setFormat(f"%p% ({format_bytes(downloaded_bytes)}/{format_bytes(total_bytes)})")
            else: widgets['progress'].setFormat(f"{format_bytes(downloaded_bytes)} downloaded")

    def on_file_status_changed(self, worker_id, status):
        if worker_id in self.file_progress_widgets:
            widgets = self.file_progress_widgets[worker_id]
            widgets['label'].setText(f"{os.path.basename(worker_id)}: {status}")
            widgets['pause'].setEnabled(status in ["Downloading", "Retrying..."])
            widgets['resume'].setEnabled(status == "Paused")
            widgets['cancel'].setEnabled(status not in ["Completed", "Canceled", "Error"])

    def on_file_download_finished(self, worker_id, filename):
        self.on_file_status_changed(worker_id, "Completed"); logger.info(f"Finished downloading {filename}")
    def on_download_error(self, filename, message): logger.error(f"Error downloading {filename}: {message}")
    def cancel_downloads(self): self.statusBar.showMessage("Canceling..."); self.download_manager.cancel_all()

    def fetch_directory_listing(self):
        # Allow fetching new directory listings even if downloads are in progress
        url = self.url_input.text().strip()
        if not url: 
            self.show_message("Warning", "Please enter a URL.", QMessageBox.Warning)
            return
        
        # Validate URL before proceeding
        from core.url_utils import ensure_url_encoded, is_valid_ftp_url
        
        encoded_url = ensure_url_encoded(url)
        if not encoded_url or not is_valid_ftp_url(encoded_url):
            self.show_message("Error", f"Invalid FTP/HTTP URL: {url}", QMessageBox.Critical)
            return
        
        # Update URL input with properly encoded URL if different
        if encoded_url != url:
            self.url_input.setText(encoded_url)
            url = encoded_url
        
        self.tree_widget.clear()
        self.path_to_item_map.clear()
        self.set_ui_state(False, f"Fetching from {url}...")
        self.fetch_button.setEnabled(False)
        self.cancel_fetch_button.setEnabled(True)
        
        self.lister_thread = DirectoryLister(url, self.config_manager)
        self.lister_thread.item_found.connect(self.add_tree_item)
        self.lister_thread.error.connect(self.on_listing_error)
        self.lister_thread.finished.connect(self.on_listing_finished)
        self.lister_thread.cache_status.connect(self.on_cache_status)
        self.lister_thread.start()

    def add_tree_item(self, item_data):
        # Normalize paths: remove trailing slashes except for root
        def norm_path(path):
            if path == '/':
                return '/'
            return path.rstrip('/')

        # On first call, ensure the root directory is mapped to the invisible root
        if not self.path_to_item_map:
            root_path = os.path.dirname(norm_path(item_data['path']))
            self.path_to_item_map[root_path] = self.tree_widget.invisibleRootItem()

        parent_path = os.path.dirname(norm_path(item_data['path']))
        parent_item = self.path_to_item_map.get(parent_path, self.tree_widget.invisibleRootItem())
        tree_item = QTreeWidgetItem(parent_item, [item_data['name'], str(item_data['size']), item_data['type'], item_data['modified']])
        tree_item.setFlags(tree_item.flags() | Qt.ItemIsUserCheckable); tree_item.setCheckState(0, Qt.Unchecked)
        
        # Store the full URL for downloads (HTTP) or path (FTP)
        download_url = item_data.get('full_url', item_data['path'])
        tree_item.setData(0, Qt.UserRole, download_url)
        if item_data['type'] == 'Directory':
            self.path_to_item_map[norm_path(item_data['path'])] = tree_item
    
    def on_listing_finished(self):
        self.statusBar.showMessage("Listing complete.", 5000); self.fetch_button.setEnabled(True); self.cancel_fetch_button.setEnabled(False); self.tree_widget.expandToDepth(0)
    
    def on_listing_error(self, msg): 
        self.show_message("Listing Error", f"Could not fetch directory:\n{msg}", QMessageBox.Critical); self.statusBar.showMessage(f"Error: {msg}", 5000); self.fetch_button.setEnabled(True); self.cancel_fetch_button.setEnabled(False)
    
    def on_cache_status(self, status):
        """Handle cache status updates from directory lister."""
        self.statusBar.showMessage(status, 2000)

    def handle_item_check(self, item, column):
        if column == 0:
            self.tree_widget.blockSignals(True)
            check_state = item.checkState(0)
            def set_check_state_recursive(parent, check_state):
                for i in range(parent.childCount()):
                    child = parent.child(i)
                    child.setCheckState(0, check_state)
                    set_check_state_recursive(child, check_state)
            set_check_state_recursive(item, check_state)
            self.tree_widget.blockSignals(False)

    def get_checked_items(self):
        checked = []
        iterator = QTreeWidgetItemIterator(self.tree_widget, QTreeWidgetItemIterator.All)
        # Determine the root path (the directory the user fetched)
        root_url = self.url_input.text().strip()
        root_path = root_url if root_url.endswith('/') else root_url + '/'
        while iterator.value():
            item = iterator.value()
            if item.checkState(0) == Qt.Checked and item.text(2) != "Directory":
                url = item.data(0, Qt.UserRole)
                # Compute relative path from the root directory
                if url.startswith(root_path):
                    rel_path = url[len(root_path):].lstrip('/')
                else:
                    rel_path = os.path.basename(url)
                checked.append((url, rel_path))
            iterator += 1
        return checked

    def browse_download_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Download Directory", self.download_path_input.text())
        if path: self.download_path_input.setText(path); self.config_manager.set("default_download_path", path)

    def show_error_log(self):
        log_dialog = QDialog(self); log_dialog.setWindowTitle("Error Log"); log_dialog.setGeometry(200, 200, 800, 600)
        layout = QVBoxLayout(log_dialog); log_view = QTextEdit(); log_view.setReadOnly(True)
        try:
            with open('logs/app.log', 'r') as f: log_content = f.read()
        except Exception as e: log_content = f"Could not read log file: {e}"
        log_view.setText(log_content); layout.addWidget(log_view)
        # Apply colorful palette to dialog and text edit
        log_dialog.setStyleSheet('''
            QDialog { background: #232946; border: 2px solid #2196F3; }
            QTextEdit { background: #393E6B; color: #fff; font-size: 14px; border: 1.5px solid #2196F3; border-radius: 8px; }
        ''')
        log_dialog.exec_()

    def show_message(self, title, message, icon=QMessageBox.Information):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        # Apply comprehensive dark palette
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor('#23272b'))
        dark_palette.setColor(QPalette.Base, QColor('#23272b'))
        dark_palette.setColor(QPalette.Text, QColor('#8B0000'))
        dark_palette.setColor(QPalette.WindowText, QColor('#8B0000'))
        dark_palette.setColor(QPalette.Button, QColor('#37474f'))
        dark_palette.setColor(QPalette.ButtonText, QColor('#8B0000'))
        dark_palette.setColor(QPalette.Light, QColor('#263238'))
        dark_palette.setColor(QPalette.Midlight, QColor('#263238'))
        dark_palette.setColor(QPalette.Dark, QColor('#181c1f'))
        dark_palette.setColor(QPalette.Mid, QColor('#263238'))
        dark_palette.setColor(QPalette.AlternateBase, QColor('#21252b'))
        msg_box.setPalette(dark_palette)
        msg_box.exec_()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()
    def dropEvent(self, event):
        if event.mimeData().urls(): self.url_input.setText(event.mimeData().urls()[0].toString()); self.fetch_directory_listing()
        
    def closeEvent(self, event):
        if self.is_downloading:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle('Confirm Exit')
            msg_box.setText("Downloads are in progress. Are you sure you want to exit?")
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)
            # Apply dark palette
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.Window, QColor('#23272b'))
            dark_palette.setColor(QPalette.Base, QColor('#23272b'))
            dark_palette.setColor(QPalette.Text, QColor('#8B0000'))
            dark_palette.setColor(QPalette.WindowText, QColor('#8B0000'))
            dark_palette.setColor(QPalette.Button, QColor('#37474f'))
            dark_palette.setColor(QPalette.ButtonText, QColor('#8B0000'))
            dark_palette.setColor(QPalette.Light, QColor('#263238'))
            dark_palette.setColor(QPalette.Midlight, QColor('#263238'))
            dark_palette.setColor(QPalette.Dark, QColor('#181c1f'))
            dark_palette.setColor(QPalette.Mid, QColor('#263238'))
            dark_palette.setColor(QPalette.AlternateBase, QColor('#21252b'))
            msg_box.setPalette(dark_palette)
            if msg_box.exec_() == QMessageBox.No:
                event.ignore(); return
        self.cancel_downloads()
        if self.lister_thread and self.lister_thread.isRunning(): self.lister_thread.quit(); self.lister_thread.wait()
        self.config_manager.save_settings()
        logger.info("Application closing."); event.accept()

    def cancel_fetch(self):
        if self.lister_thread:
            self.lister_thread.cancel()
        self.cancel_fetch_button.setEnabled(False)
        self.fetch_button.setEnabled(True)
        self.statusBar.showMessage("Fetch cancelled.")

    def update_downloads_tab(self):
        active, completed, failed, canceled = self.download_manager.get_downloads_by_status()
        # Format for UI
        def fmt(d):
            return {
                'file_name': os.path.basename(d['file_path']),
                'status': d['status'],
                'progress': d.get('progress', 0),
                'size': format_bytes(d.get('size', 0)),
                'file_path': d['file_path'],
                'can_pause': d['status'] == 'Downloading',
                'can_resume': d['status'] == 'Paused',
                'can_cancel': d['status'] in ('Queued','Downloading','Paused'),
            }
        self.downloads_tab.update_downloads(
            [fmt(d) for d in active],
            [fmt(d) for d in completed],
            [fmt(d) for d in failed],
            [fmt(d) for d in canceled],
        )
        # Update Downloads tab indicator
        self.set_downloads_tab_indicator(len(active) > 0)

    def set_downloads_tab_indicator(self, active):
        # Add a small dot to the Downloads tab label if there are active downloads
        dot = " ●" if active else ""
        self.tab_widget.setTabText(1, f"Downloads{dot}")

    def _downloads_tab_action(self, row, action):
        # Find the download by row in the current active list
        active, _, _, _ = self.download_manager.get_downloads_by_status()
        if 0 <= row < len(active):
            url = active[row]['url']
            if action == 'pause':
                self.download_manager.pause_file(url)
            elif action == 'resume':
                self.download_manager.resume_file(url)
            elif action == 'cancel':
                self.download_manager.cancel_file(url)

    def _downloads_tab_retry(self, row, tab):
        # Find the download by row in the failed/canceled list
        _, _, failed, canceled = self.download_manager.get_downloads_by_status()
        if tab == 'failed' and 0 <= row < len(failed):
            self.download_manager.retry_download(failed[row]['url'])
        elif tab == 'canceled' and 0 <= row < len(canceled):
            self.download_manager.retry_download(canceled[row]['url'])

    def open_in_explorer(self, file_path):
        if os.path.exists(file_path):
            if sys.platform.startswith('win'):
                os.startfile(os.path.dirname(file_path))
            elif sys.platform.startswith('darwin'):
                subprocess.run(['open', '--', os.path.dirname(file_path)])
            else:
                subprocess.run(['xdg-open', os.path.dirname(file_path)])

    def apply_theme(self, theme_name):
        self.config_manager.set("theme_name", theme_name)
        styles = {
            "Colorful": '''
                QMainWindow { background: #232946; }
                QPushButton { border-radius: 8px; padding: 6px 16px; font-size: 14px; background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2196F3, stop:1 #FF9800); color: #fff; font-weight: bold; }
                QPushButton:pressed { background: #FF9800; color: #fff; }
                QPushButton:hover { background: #4CAF50; color: #fff; }
                QLineEdit { border: 1.5px solid #2196F3; border-radius: 8px; padding: 4px 8px; font-size: 14px; background: #393E6B; color: #fff; selection-background-color: #FF9800; selection-color: #232946; }
                QLabel { font-size: 14px; color: #E0E0E0; }
                QToolBar { background: #232946; border-bottom: 2px solid #2196F3; }
                QStatusBar { background: #232946; border-top: 2px solid #2196F3; color: #fff; }
                QTreeWidget { font-size: 14px; background: #393E6B; color: #fff; alternate-background-color: #232946; }
                QTreeWidget::item:selected { background: #2196F3; color: #fff; }
                QTreeWidget::item:hover { background: #FF9800; color: #fff; }
                QHeaderView::section { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2196F3, stop:1 #FF9800); color: #fff; border: none; font-weight: bold; }
                QProgressBar { border-radius: 8px; background: #232946; color: #fff; text-align: center; }
                QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4CAF50, stop:1 #2196F3); border-radius: 8px; }
                QTabWidget::pane { border: 2px solid #2196F3; background: #232946; }
                QTabBar::tab { background: #393E6B; color: #fff; padding: 6px 16px; min-width: 80px; min-height: 28px; font-size: 13px; border-top-left-radius: 6px; border-top-right-radius: 6px; font-weight: bold; margin-right: 4px; }
                QTabWidget::tab-bar { alignment: center; }
                QTabBar::tab:selected { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2196F3, stop:1 #FF9800); color: #fff; }
                QTabBar::tab:hover { background: #FF9800; color: #fff; }
            ''',
            "Dark": '''
                QMainWindow { background: #181818; }
                QPushButton { border-radius: 8px; padding: 6px 16px; font-size: 14px; background: #232323; color: #fff; font-weight: bold; }
                QPushButton:pressed { background: #333; color: #fff; }
                QPushButton:hover { background: #444; color: #fff; }
                QLineEdit { border: 1.5px solid #444; border-radius: 8px; padding: 4px 8px; font-size: 14px; background: #232323; color: #fff; selection-background-color: #2196F3; selection-color: #181818; }
                QLabel { font-size: 14px; color: #fff; }
                QToolBar, QStatusBar { background: #181818; color: #fff; }
                QTreeWidget, QTabBar::tab, QTabWidget::pane { background: #232323; color: #fff; }
                QTreeWidget::item:selected, QTabBar::tab:selected { background: #2196F3; color: #fff; }
                QTreeWidget::item:hover, QTabBar::tab:hover { background: #FF9800; color: #fff; }
                QHeaderView::section { background: #232323; color: #fff; border: none; font-weight: bold; }
                QProgressBar { border-radius: 8px; background: #181818; color: #fff; text-align: center; }
                QProgressBar::chunk { background: #2196F3; border-radius: 8px; }
            ''',
            "Light": '''
                QMainWindow { background: #f5f5f5; }
                QPushButton { border-radius: 8px; padding: 6px 16px; font-size: 14px; background: #2196F3; color: #fff; font-weight: bold; }
                QPushButton:pressed { background: #1976D2; color: #fff; }
                QPushButton:hover { background: #FF9800; color: #fff; }
                QLineEdit { border: 1.5px solid #2196F3; border-radius: 8px; padding: 4px 8px; font-size: 14px; background: #fff; color: #232946; selection-background-color: #2196F3; selection-color: #fff; }
                QLabel { font-size: 14px; color: #232946; }
                QToolBar, QStatusBar { background: #e0e0e0; color: #232946; }
                QTreeWidget, QTabBar::tab, QTabWidget::pane { background: #fff; color: #232946; }
                QTreeWidget::item:selected, QTabBar::tab:selected { background: #2196F3; color: #fff; }
                QTreeWidget::item:hover, QTabBar::tab:hover { background: #FF9800; color: #fff; }
                QHeaderView::section { background: #2196F3; color: #fff; border: none; font-weight: bold; }
                QProgressBar { border-radius: 8px; background: #e0e0e0; color: #232946; text-align: center; }
                QProgressBar::chunk { background: #2196F3; border-radius: 8px; }
            ''',
            "Solarized": '''
                QMainWindow { background: #002b36; }
                QPushButton { border-radius: 8px; padding: 6px 16px; font-size: 14px; background: #268bd2; color: #fdf6e3; font-weight: bold; }
                QPushButton:pressed { background: #b58900; color: #fdf6e3; }
                QPushButton:hover { background: #2aa198; color: #fdf6e3; }
                QLineEdit { border: 1.5px solid #268bd2; border-radius: 8px; padding: 4px 8px; font-size: 14px; background: #073642; color: #fdf6e3; selection-background-color: #b58900; selection-color: #002b36; }
                QLabel { font-size: 14px; color: #fdf6e3; }
                QToolBar, QStatusBar { background: #073642; color: #fdf6e3; }
                QTreeWidget, QTabBar::tab, QTabWidget::pane { background: #073642; color: #fdf6e3; }
                QTreeWidget::item:selected, QTabBar::tab:selected { background: #268bd2; color: #fdf6e3; }
                QTreeWidget::item:hover, QTabBar::tab:hover { background: #b58900; color: #fdf6e3; }
                QHeaderView::section { background: #268bd2; color: #fdf6e3; border: none; font-weight: bold; }
                QProgressBar { border-radius: 8px; background: #002b36; color: #fdf6e3; text-align: center; }
                QProgressBar::chunk { background: #2aa198; border-radius: 8px; }
            ''',
            "Classic": '''
                QMainWindow { background: #ececec; }
                QPushButton { border-radius: 8px; padding: 6px 16px; font-size: 14px; background: #d3d3d3; color: #232946; font-weight: bold; }
                QPushButton:pressed { background: #b0b0b0; color: #232946; }
                QPushButton:hover { background: #2196F3; color: #fff; }
                QLineEdit { border: 1.5px solid #2196F3; border-radius: 8px; padding: 4px 8px; font-size: 14px; background: #fff; color: #232946; selection-background-color: #2196F3; selection-color: #fff; }
                QLabel { font-size: 14px; color: #232946; }
                QToolBar, QStatusBar { background: #ececec; color: #232946; }
                QTreeWidget, QTabBar::tab, QTabWidget::pane { background: #fff; color: #232946; }
                QTreeWidget::item:selected, QTabBar::tab:selected { background: #2196F3; color: #fff; }
                QTreeWidget::item:hover, QTabBar::tab:hover { background: #FF9800; color: #fff; }
                QHeaderView::section { background: #d3d3d3; color: #232946; border: none; font-weight: bold; }
                QProgressBar { border-radius: 8px; background: #ececec; color: #232946; text-align: center; }
                QProgressBar::chunk { background: #2196F3; border-radius: 8px; }
            '''
        }
        self.setStyleSheet(styles.get(theme_name, styles["Colorful"]))
    
    def handle_browser_url_selected(self, url):
        """Handle URL selection from browser tab with proper validation."""
        from core.url_utils import ensure_url_encoded, is_valid_ftp_url
        
        # Validate and encode the URL
        encoded_url = ensure_url_encoded(url)
        
        if encoded_url and is_valid_ftp_url(encoded_url):
            # Switch to downloader tab
            self.tab_widget.setCurrentIndex(0)
            
            # Set URL in the input field
            self.url_input.setText(encoded_url)
            
            # Show status message
            self.statusBar.showMessage(f"URL transferred from browser: {encoded_url}", 5000)
            
            # Automatically start fetching directory listing
            self.fetch_directory_listing()
        else:
            # Show error message
            self.statusBar.showMessage("Invalid URL received from browser", 5000)
            logger.error(f"Invalid URL from browser: {url}")
    
    def set_url_from_browser(self, url):
        """Set URL in downloader from browser (alternative method)."""
        self.handle_browser_url_selected(url)
