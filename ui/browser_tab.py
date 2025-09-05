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
        
        # Connect web view signals
        self.browser_view.urlChanged.connect(self.update_address_bar)
    
    def load_homepage(self):
        """Load the bookmark homepage."""
        try:
            html_content = self.bookmark_manager.generate_bookmarks_html()
            self.browser_view.setHtml(html_content)
            self.address_bar.setText("bookmarks://home")
        except Exception as e:
            logger.error(f"Error loading homepage: {e}")
            self.browser_view.setHtml("<h1>Error loading bookmarks</h1>")
    
    def navigate_to_url(self):
        """Navigate to the URL in the address bar."""
        url = self.address_bar.text().strip()
        if url and url != "bookmarks://home":
            if not url.startswith(('http://', 'https://', 'ftp://')):
                url = 'http://' + url
            self.browser_view.setUrl(QUrl(url))
    
    def update_address_bar(self, qurl):
        """Update the address bar when the URL changes."""
        url = qurl.toString()
        if url != "about:blank":
            self.address_bar.setText(url)
    
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
        """Get the current URL with proper percent-encoding."""
        current_url = self.browser_view.url().toString()
        if current_url == "about:blank" or current_url.startswith("bookmarks://"):
            return ""
        return current_url
    
    def use_current_link(self):
        """Emit signal with current URL for use in downloader."""
        url = self.get_encoded_url()
        if url:
            self.url_selected.emit(url)
            QMessageBox.information(
                self, 
                "Link Transferred", 
                f"URL transferred to downloader:\n{url}"
            )
        else:
            QMessageBox.warning(
                self, 
                "No URL", 
                "Please navigate to a valid URL first."
            )
    
    def set_url(self, url):
        """Set a specific URL in the browser."""
        if url:
            self.browser_view.setUrl(QUrl(url))
