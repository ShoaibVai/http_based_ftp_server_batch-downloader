#!/usr/bin/env python3
"""
Test script to verify the statusBar fix by triggering the browser URL transfer.
"""

import sys
import os
import traceback

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

def test_statusbar_access():
    """Test that statusBar is accessed correctly."""
    try:
        print("Testing statusBar fix...")
        
        # Import after path setup
        from PyQt5.QtWidgets import QApplication
        from ui.main_window import MainWindow
        
        # Create application
        app = QApplication(sys.argv)
        
        # Create main window
        window = MainWindow()
        
        # Test the problematic method directly
        test_url = "ftp://test.example.com/path"
        print(f"Testing handle_browser_url_selected with URL: {test_url}")
        
        # This should not raise a TypeError
        window.handle_browser_url_selected(test_url)
        
        print("✅ statusBar fix successful - no TypeError occurred")
        return True
        
    except TypeError as e:
        print(f"❌ statusBar TypeError still exists: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"⚠️  Other error occurred: {e}")
        traceback.print_exc()
        return False
    finally:
        try:
            app.quit()
        except:
            pass

if __name__ == "__main__":
    success = test_statusbar_access()
    sys.exit(0 if success else 1)
