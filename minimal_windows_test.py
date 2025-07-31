#!/usr/bin/env python3
"""
Minimal Windows test script for CSC-Reach.
This script attempts to start the app with minimal initialization to isolate Windows issues.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def minimal_app_test():
    """Test minimal app startup."""
    print("Starting minimal app test...")
    
    try:
        # Test basic Qt
        from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
        from PySide6.QtCore import Qt
        
        print("✅ Qt imports successful")
        
        # Create minimal app
        app = QApplication(sys.argv)
        print("✅ QApplication created")
        
        # Create minimal window
        window = QMainWindow()
        window.setWindowTitle("CSC-Reach - Minimal Test")
        window.resize(400, 300)
        
        # Add simple content
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        label = QLabel("CSC-Reach Minimal Test\n\nIf you see this window, basic Qt is working!")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        window.setCentralWidget(central_widget)
        print("✅ Minimal window created")
        
        # Show window
        window.show()
        print("✅ Window shown")
        
        print("\n🎉 Minimal test successful!")
        print("Close the window to continue...")
        
        # Run event loop for 5 seconds or until closed
        import time
        start_time = time.time()
        while window.isVisible() and (time.time() - start_time) < 30:
            app.processEvents()
            time.sleep(0.1)
        
        return True
        
    except Exception as e:
        print(f"❌ Minimal test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_manager():
    """Test config manager initialization."""
    print("\nTesting config manager...")
    try:
        from multichannel_messaging.core.config_manager import ConfigManager
        config = ConfigManager()
        print("✅ ConfigManager created successfully")
        return True
    except Exception as e:
        print(f"❌ ConfigManager failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_window_import():
    """Test main window import without instantiation."""
    print("\nTesting main window import...")
    try:
        from multichannel_messaging.gui.main_window import MainWindow
        print("✅ MainWindow import successful")
        return True
    except Exception as e:
        print(f"❌ MainWindow import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_window_creation():
    """Test main window creation."""
    print("\nTesting main window creation...")
    try:
        from multichannel_messaging.core.config_manager import ConfigManager
        from multichannel_messaging.gui.main_window import MainWindow
        
        config = ConfigManager()
        
        # Create main window with minimal setup
        window = MainWindow(config, message_logger=None)
        print("✅ MainWindow created successfully")
        
        window.show()
        print("✅ MainWindow shown")
        
        # Close immediately
        window.close()
        print("✅ MainWindow closed")
        
        return True
    except Exception as e:
        print(f"❌ MainWindow creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run minimal tests."""
    print("CSC-Reach Minimal Windows Test")
    print("=" * 40)
    
    # Test 1: Minimal Qt app
    if not minimal_app_test():
        print("\n❌ Basic Qt test failed. Check PySide6 installation.")
        return
    
    # Test 2: Config manager
    if not test_config_manager():
        print("\n❌ Config manager test failed.")
        return
    
    # Test 3: Main window import
    if not test_main_window_import():
        print("\n❌ Main window import failed.")
        return
    
    # Test 4: Main window creation
    if not test_main_window_creation():
        print("\n❌ Main window creation failed.")
        return
    
    print("\n🎉 All minimal tests passed!")
    print("The app should work. Try running the full application.")

if __name__ == "__main__":
    main()
