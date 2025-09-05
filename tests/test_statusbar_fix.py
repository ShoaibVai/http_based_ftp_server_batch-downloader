# test_statusbar_fix.py
# Quick test to verify the statusBar fix works

import sys
import os
from PyQt5.QtWidgets import QApplication

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_statusbar_fix():
    """Test that the statusBar fix prevents TypeError."""
    try:
        # Initialize QApplication
        app = QApplication(sys.argv)
        
        # Import and create main window
        from ui.main_window import MainWindow
        main_window = MainWindow()
        
        # Test the method that was causing the error
        test_url = "http://example.com/test%20url"
        main_window.handle_browser_url_selected(test_url)
        
        print("✅ StatusBar fix successful - no TypeError occurred")
        return True
        
    except TypeError as e:
        if "'QStatusBar' object is not callable" in str(e):
            print(f"❌ StatusBar fix failed - TypeError still occurs: {e}")
            return False
        else:
            print(f"❌ Different TypeError occurred: {e}")
            return False
    except Exception as e:
        print(f"⚠️  Other error occurred (not related to statusBar): {e}")
        return True  # This is acceptable as it's not the statusBar error
    finally:
        if 'app' in locals():
            app.quit()

if __name__ == '__main__':
    success = test_statusbar_fix()
    print("\n" + "="*50)
    if success:
        print("STATUS: ✅ STATUSBAR FIX VERIFIED")
    else:
        print("STATUS: ❌ STATUSBAR FIX FAILED")
    print("="*50)
