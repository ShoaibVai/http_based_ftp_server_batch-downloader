# ui/browser_tab.py
# Browser tab with web view functionality and bookmark integration

import os
import logging
from urllib.parse import quote, unquote
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
    QComboBox, QToolBar, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QUrl
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView
from core.bookmark_manager import BookmarkManager
from core.url_utils import ensure_url_encoded, is_valid_ftp_url, get_display_url

logger = logging.getLogger(__name__)

class BrowserTab(QWidget):
    """Browser tab with web view and bookmark functionality."""
    
    url_selected = pyqtSignal(str)  # Signal emitted when "Use This Link" is clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bookmark_manager = BookmarkManager()
        self.setup_ui()
        self.setup_connections()
        self.load_homepage()
    
    def setup_ui(self):
        """Set up the user interface for the browser tab."""
        layout = QVBoxLayout(self)
        
        # Navigation toolbar
        toolbar_layout = QHBoxLayout()
        
        # Navigation buttons
        self.back_button = QPushButton("◀ Back")
        self.back_button.setMaximumWidth(80)
        self.forward_button = QPushButton("Forward ▶")
        self.forward_button.setMaximumWidth(80)
        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.setMaximumWidth(80)
        self.home_button = QPushButton("🏠 Home")
        self.home_button.setMaximumWidth(80)
        
        # Address bar
        self.address_bar = QLineEdit()
        self.address_bar.setPlaceholderText("Enter URL or use bookmarks below...")
        
        # Server and category dropdowns
        self.server_dropdown = QComboBox()
        self.server_dropdown.addItem("Select Server...")
        self.server_dropdown.addItems(self.bookmark_manager.get_servers())
        self.server_dropdown.setMaximumWidth(150)
        
        self.category_dropdown = QComboBox()
        self.category_dropdown.addItem("Select Category...")
        self.category_dropdown.setMaximumWidth(200)
        
        # Use this link button
        self.use_link_button = QPushButton("📥 Use This Link")
        self.use_link_button.setMaximumWidth(120)
        self.use_link_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4CAF50, stop:1 #8BC34A);
                color: white;
                border-radius: 6px;
                font-weight: bold;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #45a049, stop:1 #7CB342);
            }
        """)
        
        # Add widgets to toolbar
        toolbar_layout.addWidget(self.back_button)
        toolbar_layout.addWidget(self.forward_button)
        toolbar_layout.addWidget(self.refresh_button)
        toolbar_layout.addWidget(self.home_button)
        toolbar_layout.addWidget(QLabel("URL:"))
        toolbar_layout.addWidget(self.address_bar)
        toolbar_layout.addWidget(self.server_dropdown)
        toolbar_layout.addWidget(self.category_dropdown)
        toolbar_layout.addWidget(self.use_link_button)
        
        layout.addLayout(toolbar_layout)
        
        # Web view
        self.browser_view = QWebEngineView()
        layout.addWidget(self.browser_view)
        
        # Apply styling
        self.setStyleSheet("""
            QPushButton {
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2196F3, stop:1 #FF9800);
                color: #fff;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1976D2, stop:1 #F57C00);
            }
            QPushButton:pressed {
                background: #FF9800;
            }
            QLineEdit {
                border: 2px solid #2196F3;
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 12px;
                background: #393E6B;
                color: #fff;
            }
            QComboBox {
                border: 2px solid #2196F3;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
                background: #393E6B;
                color: #fff;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #fff;
            }
        """)
    
    def setup_connections(self):
        """Set up signal connections."""
        self.back_button.clicked.connect(self.browser_view.back)
        self.forward_button.clicked.connect(self.browser_view.forward)
        self.refresh_button.clicked.connect(self.browser_view.reload)
        self.home_button.clicked.connect(self.load_homepage)
        self.address_bar.returnPressed.connect(self.navigate_to_url)
        self.server_dropdown.currentTextChanged.connect(self.on_server_changed)
        self.category_dropdown.currentTextChanged.connect(self.on_category_changed)
        self.use_link_button.clicked.connect(self.use_current_link)
        
        # Connect web view signals with enhanced handling
        self.browser_view.urlChanged.connect(self.on_url_changed)
        self.browser_view.loadFinished.connect(self.on_load_finished)
    
    def load_homepage(self):
        """Load the bookmark homepage."""
        try:
            html_content = self.bookmark_manager.generate_bookmarks_html()
            self.browser_view.setHtml(html_content)
            self.address_bar.setText("Bookmarks Homepage")
            self.use_link_button.setEnabled(False)  # Disable for homepage
        except Exception as e:
            logger.error(f"Error loading homepage: {e}")
            self.browser_view.setHtml("<h1>Error loading bookmarks</h1>")
            self.address_bar.setText("Error")
            self.use_link_button.setEnabled(False)
    
    def navigate_to_url(self):
        """Navigate to the URL in the address bar."""
        url = self.address_bar.text().strip()
        if url and url not in ("Bookmarks Homepage", "Error"):
            if not url.startswith(('http://', 'https://', 'ftp://')):
                url = 'http://' + url
            self.browser_view.setUrl(QUrl(url))
    
    def on_url_changed(self, qurl):
        """Handle URL changes and update UI state."""
        self.update_address_bar(qurl)
        
        # Enable/disable "Use This Link" button based on URL validity
        url_string = qurl.toString()
        if url_string and qurl.scheme() in ['ftp', 'http', 'https']:
            self.use_link_button.setEnabled(True)
        else:
            self.use_link_button.setEnabled(False)
    
    def update_address_bar(self, qurl):
        """Update the address bar with user-friendly URL display."""
        url_string = qurl.toString()
        if url_string == "about:blank":
            return
        elif url_string.startswith("data:"):
            # This is our bookmark homepage
            self.address_bar.setText("Bookmarks Homepage")
        else:
            # Display user-friendly (decoded) URL for readability
            display_url = get_display_url(url_string)
            self.address_bar.setText(display_url)
    
    def on_load_finished(self, success):
        """Handle page load completion."""
        if not success:
            self.handle_navigation_error()
        else:
            logger.debug("Page loaded successfully")
    
    def on_server_changed(self, server_name):
        """Handle server selection change."""
        if server_name == "Select Server...":
            self.category_dropdown.clear()
            self.category_dropdown.addItem("Select Category...")
            return
        
        # Populate categories for selected server
        self.category_dropdown.clear()
        self.category_dropdown.addItem("Select Category...")
        categories = self.bookmark_manager.get_categories(server_name)
        self.category_dropdown.addItems(categories)
    
    def on_category_changed(self, category_name):
        """Handle category selection change."""
        if category_name == "Select Category...":
            return
        
        server_name = self.server_dropdown.currentText()
        if server_name != "Select Server...":
            url = self.bookmark_manager.get_url(server_name, category_name)
            if url:
                self.browser_view.setUrl(QUrl(url))
    
    def get_encoded_url(self):
        """Get the current URL with proper percent-encoding for FTP operations."""
        current_qurl = self.browser_view.url()
        url_string = current_qurl.toString()
        
        # Handle special cases
        if (url_string == "about:blank" or 
            url_string.startswith("data:") or 
            url_string.startswith("bookmarks://")):
            return None
        
        # Get properly encoded URL
        try:
            encoded_url = ensure_url_encoded(url_string)
            logger.debug(f"Browser URL encoding: {url_string} -> {encoded_url}")
            return encoded_url
        except Exception as e:
            logger.error(f"Error getting encoded URL: {e}")
            return None
    
    def use_current_link(self):
        """Emit signal with current URL for use in downloader."""
        encoded_url = self.get_encoded_url()
        
        if encoded_url and is_valid_ftp_url(encoded_url):
            self.url_selected.emit(encoded_url)
            self.show_status_message(f"URL transferred to downloader", 3000)
            logger.info(f"URL transferred to downloader: {encoded_url}")
        elif encoded_url:
            self.show_status_message("Invalid FTP/HTTP URL for server operations", 3000)
            logger.warning(f"Invalid URL for FTP operations: {encoded_url}")
        else:
            self.show_status_message("Current page is not a valid FTP/HTTP directory", 3000)
            logger.warning("No valid URL to transfer")
    
    def show_status_message(self, message, duration=3000):
        """Show status message in main window status bar."""
        try:
            # Find the main window through parent hierarchy
            widget = self.parent()
            while widget and not hasattr(widget, 'statusBar'):
                widget = widget.parent()
            
            if widget and hasattr(widget, 'statusBar'):
                widget.statusBar.showMessage(message, duration)
            else:
                logger.info(f"Status: {message}")
        except Exception as e:
            logger.error(f"Error showing status message: {e}")
    
    def handle_navigation_error(self):
        """Handle navigation errors in browser view."""
        self.show_status_message("Navigation error. Please check the URL and try again.", 3000)
        self.use_link_button.setEnabled(False)
        logger.warning("Navigation error occurred")
    
    def set_url(self, url):
        """Set a specific URL in the browser."""
        if url:
            self.browser_view.setUrl(QUrl(url))
