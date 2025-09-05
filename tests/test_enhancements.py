# test_enhancements.py
# Simple test to verify the new enhancements work correctly

import sys
import os
import unittest
from unittest.mock import Mock, patch
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QTimer

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.bookmark_manager import BookmarkManager
from core.cache_manager import DirectoryCache
from ui.browser_tab import BrowserTab
from ui.main_window import MainWindow

class TestEnhancements(unittest.TestCase):
    """Test suite for the new enhancements."""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for GUI tests."""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up test fixtures."""
        self.bookmark_manager = BookmarkManager()
        self.cache_manager = DirectoryCache("test_cache")
    
    def test_bookmark_manager_initialization(self):
        """Test that BookmarkManager initializes correctly."""
        self.assertIsInstance(self.bookmark_manager, BookmarkManager)
        servers = self.bookmark_manager.get_servers()
        self.assertIsInstance(servers, list)
        self.assertGreater(len(servers), 0)
    
    def test_bookmark_manager_get_categories(self):
        """Test getting categories for a server."""
        servers = self.bookmark_manager.get_servers()
        if servers:
            categories = self.bookmark_manager.get_categories(servers[0])
            self.assertIsInstance(categories, list)
    
    def test_bookmark_manager_get_url(self):
        """Test getting URL for a server and category."""
        servers = self.bookmark_manager.get_servers()
        if servers:
            categories = self.bookmark_manager.get_categories(servers[0])
            if categories:
                url = self.bookmark_manager.get_url(servers[0], categories[0])
                self.assertIsInstance(url, str)
                self.assertGreater(len(url), 0)
    
    def test_bookmark_manager_html_generation(self):
        """Test HTML generation for bookmarks."""
        html = self.bookmark_manager.generate_bookmarks_html()
        self.assertIsInstance(html, str)
        self.assertIn('<!DOCTYPE html>', html)
        self.assertIn('FTP Server Bookmarks', html)
    
    def test_cache_manager_initialization(self):
        """Test that DirectoryCache initializes correctly."""
        self.assertIsInstance(self.cache_manager, DirectoryCache)
        self.assertTrue(os.path.exists("test_cache"))
    
    def test_cache_manager_set_get(self):
        """Test cache set and get operations."""
        test_url = "http://example.com/test"
        test_data = [{"name": "test.txt", "size": "100", "type": "File"}]
        
        # Set cache
        self.cache_manager.set(test_url, test_data)
        
        # Get cache
        cached_data = self.cache_manager.get(test_url)
        self.assertEqual(cached_data, test_data)
    
    def test_cache_manager_expiration(self):
        """Test cache expiration handling."""
        test_url = "http://example.com/expired"
        test_data = [{"name": "expired.txt", "size": "200", "type": "File"}]
        
        # Mock expired cache
        with patch('core.cache_manager.datetime') as mock_datetime:
            from datetime import datetime, timedelta
            mock_datetime.now.return_value = datetime.now() - timedelta(hours=25)
            self.cache_manager.set(test_url, test_data)
            
            # Reset datetime to current
            mock_datetime.now.return_value = datetime.now()
            cached_data = self.cache_manager.get(test_url)
            self.assertIsNone(cached_data)
    
    def test_cache_manager_stats(self):
        """Test cache statistics."""
        stats = self.cache_manager.get_cache_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn('total_files', stats)
        self.assertIn('valid_files', stats)
        self.assertIn('expired_files', stats)
        self.assertIn('total_size_bytes', stats)
        self.assertIn('total_size_mb', stats)
    
    def test_browser_tab_initialization(self):
        """Test that BrowserTab initializes correctly."""
        browser_tab = BrowserTab()
        self.assertIsInstance(browser_tab, BrowserTab)
        self.assertIsNotNone(browser_tab.bookmark_manager)
        self.assertIsNotNone(browser_tab.browser_view)
        self.assertIsNotNone(browser_tab.address_bar)
    
    def test_main_window_initialization(self):
        """Test that MainWindow initializes with all tabs."""
        main_window = MainWindow()
        self.assertIsInstance(main_window, MainWindow)
        
        # Check that all tabs are present
        tab_count = main_window.tab_widget.count()
        self.assertEqual(tab_count, 4)  # Downloader, Downloads, Settings, Browser
        
        # Check tab names
        tab_names = []
        for i in range(tab_count):
            tab_names.append(main_window.tab_widget.tabText(i))
        
        expected_tabs = ["Downloader", "Downloads", "Settings", "Browser"]
        for expected_tab in expected_tabs:
            self.assertIn(expected_tab, tab_names)
    
    def test_favicon_loading(self):
        """Test that favicon can be loaded."""
        from PyQt5.QtGui import QIcon
        
        icon_path = "resources/icons/favicon.ico"
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.assertFalse(icon.isNull())
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up test cache
        import shutil
        if os.path.exists("test_cache"):
            shutil.rmtree("test_cache")

if __name__ == '__main__':
    # Create a test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEnhancements)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
