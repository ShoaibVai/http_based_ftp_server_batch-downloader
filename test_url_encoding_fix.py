# test_url_encoding_fix.py
# Test suite to verify URL encoding fixes work correctly

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.url_utils import (
    ensure_url_encoded, is_valid_ftp_url, get_display_url,
    normalize_ftp_url, extract_filename_from_url, is_directory_url
)

class TestURLEncodingFix(unittest.TestCase):
    """Test suite for URL encoding fixes."""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for GUI tests."""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def test_ensure_url_encoded(self):
        """Test URL encoding functionality."""
        # Test URL with spaces
        url_with_spaces = "http://example.com/folder with spaces/file.txt"
        encoded = ensure_url_encoded(url_with_spaces)
        self.assertIn("%20", encoded)
        
        # Test URL with special characters (ampersand gets encoded manually)
        url_with_special = "http://example.com/folder & special/file.txt"
        encoded = ensure_url_encoded(url_with_special)
        self.assertIn("%20", encoded)
        self.assertIn("%26", encoded)  # Should be manually encoded
        
        # Test already encoded URL
        already_encoded = "http://example.com/folder%20with%20spaces/file.txt"
        encoded = ensure_url_encoded(already_encoded)
        self.assertEqual(encoded, already_encoded)
        
        # Test invalid URL
        invalid_url = "not-a-url"
        encoded = ensure_url_encoded(invalid_url)
        self.assertIsNone(encoded)
    
    def test_is_valid_ftp_url(self):
        """Test FTP URL validation."""
        # Valid HTTP URLs
        self.assertTrue(is_valid_ftp_url("http://example.com/path"))
        self.assertTrue(is_valid_ftp_url("https://example.com/path"))
        
        # Valid FTP URLs
        self.assertTrue(is_valid_ftp_url("ftp://ftp.example.com/path"))
        
        # Invalid URLs
        self.assertFalse(is_valid_ftp_url(""))
        self.assertFalse(is_valid_ftp_url("not-a-url"))
        self.assertFalse(is_valid_ftp_url("mailto:test@example.com"))
        
        # FTP URL without host should be invalid
        self.assertFalse(is_valid_ftp_url("ftp:///path/only"))
    
    def test_get_display_url(self):
        """Test display URL functionality."""
        # Test encoded URL should return decoded version
        encoded_url = "http://example.com/folder%20with%20spaces/file.txt"
        display = get_display_url(encoded_url)
        self.assertIn(" ", display)
        self.assertNotIn("%20", display)
        
        # Test normal URL
        normal_url = "http://example.com/normal/path"
        display = get_display_url(normal_url)
        self.assertEqual(display, normal_url)
    
    def test_normalize_ftp_url(self):
        """Test FTP URL normalization."""
        # Test directory URL gets trailing slash
        dir_url = "http://example.com/directory"
        normalized = normalize_ftp_url(dir_url)
        self.assertTrue(normalized.endswith("/"))
        
        # Test file URL doesn't get trailing slash
        file_url = "http://example.com/file.txt"
        normalized = normalize_ftp_url(file_url)
        self.assertFalse(normalized.endswith("/"))
    
    def test_extract_filename_from_url(self):
        """Test filename extraction."""
        # Test file URL
        file_url = "http://example.com/path/file.txt"
        filename = extract_filename_from_url(file_url)
        self.assertEqual(filename, "file.txt")
        
        # Test directory URL
        dir_url = "http://example.com/path/"
        filename = extract_filename_from_url(dir_url)
        self.assertEqual(filename, "")
        
        # Test URL with encoded filename
        encoded_url = "http://example.com/path/file%20with%20spaces.txt"
        filename = extract_filename_from_url(encoded_url)
        self.assertIn("file", filename)
    
    def test_is_directory_url(self):
        """Test directory URL detection."""
        # Test obvious directory (ends with /)
        dir_url = "http://example.com/directory/"
        self.assertTrue(is_directory_url(dir_url))
        
        # Test obvious file (has extension)
        file_url = "http://example.com/file.txt"
        self.assertFalse(is_directory_url(file_url))
        
        # Test likely directory (no extension)
        likely_dir = "http://example.com/directory"
        self.assertTrue(is_directory_url(likely_dir))
    
    def test_real_world_urls(self):
        """Test with real-world FTP server URLs."""
        # CircleFTP URL with encoded characters
        circleftp_url = "http://ftp5.circleftp.net/FILE/Animation%20Movies/"
        
        # Test encoding preservation
        encoded = ensure_url_encoded(circleftp_url)
        self.assertIsNotNone(encoded)
        self.assertIn("%20", encoded)
        
        # Test validation
        self.assertTrue(is_valid_ftp_url(circleftp_url))
        
        # Test display version
        display = get_display_url(circleftp_url)
        self.assertIn(" ", display)  # Should show spaces for readability
        
        # Dhakaflix URL with encoded characters including ampersand
        dhakaflix_url = "http://172.16.50.9/DHAKA-FLIX-9/Anime & Cartoon TV Series/"
        
        encoded = ensure_url_encoded(dhakaflix_url)
        self.assertIsNotNone(encoded)
        self.assertIn("%20", encoded)
        self.assertIn("%26", encoded)  # Ampersand should be manually encoded
        
        self.assertTrue(is_valid_ftp_url(dhakaflix_url))
    
    def test_url_encoding_workflow(self):
        """Test the complete URL encoding workflow."""
        # Simulate browser displaying a decoded URL
        displayed_url = "http://172.16.50.9/DHAKA-FLIX-9/Anime & Cartoon TV Series/"
        
        # User clicks "Use This Link" - should get encoded version
        encoded_for_downloader = ensure_url_encoded(displayed_url)
        
        # Verify the encoded version is proper for FTP operations
        self.assertIsNotNone(encoded_for_downloader)
        self.assertIn("%20", encoded_for_downloader)
        self.assertIn("%26", encoded_for_downloader)
        self.assertTrue(is_valid_ftp_url(encoded_for_downloader))
        
        # Verify we can get back to display version
        display_again = get_display_url(encoded_for_downloader)
        self.assertIn(" ", display_again)
        # Note: QUrl may keep %26 encoded in display, which is acceptable
        self.assertTrue("&" in display_again or "%26" in display_again)
    
    def test_browser_tab_url_encoding_logic(self):
        """Test browser tab URL encoding logic without GUI components."""
        # Test the core logic that would be used in browser tab
        test_url = "http://example.com/folder with spaces/"
        
        # This simulates what get_encoded_url should return
        encoded = ensure_url_encoded(test_url)
        self.assertIsNotNone(encoded)
        self.assertIn("%20", encoded)
        
        # Test validation that would happen in use_current_link
        self.assertTrue(is_valid_ftp_url(encoded))
        
        # Test display that would happen in address bar
        display = get_display_url(encoded)
        self.assertIn(" ", display)
    
    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        # Test empty/None URLs
        self.assertIsNone(ensure_url_encoded(""))
        self.assertIsNone(ensure_url_encoded(None))
        self.assertFalse(is_valid_ftp_url(""))
        self.assertFalse(is_valid_ftp_url(None))
        
        # Test malformed URLs (these are handled by is_valid_ftp_url separately)
        # QUrl considers "http://" valid, but is_valid_ftp_url should reject it
        self.assertFalse(is_valid_ftp_url("http://"))
        
        # Test URLs with only special characters
        special_only = "http://example.com/%%%%/"
        encoded = ensure_url_encoded(special_only)
        self.assertIsNotNone(encoded)
    
    def test_unicode_handling(self):
        """Test Unicode character handling."""
        # Test URL with Unicode characters
        unicode_url = "http://example.com/ñoño/文件/"
        encoded = ensure_url_encoded(unicode_url)
        self.assertIsNotNone(encoded)
        
        # Should contain percent-encoded Unicode
        self.assertIn("%", encoded)

if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
