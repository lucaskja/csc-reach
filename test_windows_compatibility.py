#!/usr/bin/env python3
"""
Windows compatibility test script for CSC-Reach.
This script tests for common Windows-specific issues that could prevent the app from starting.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_basic_imports():
    """Test basic PySide6 imports."""
    print("Testing basic PySide6 imports...")
    try:
        from PySide6.QtWidgets import QApplication, QMainWindow
        from PySide6.QtCore import Qt, Signal, QThread
        from PySide6.QtGui import QFont
        print("✅ Basic PySide6 imports successful")
        return True
    except ImportError as e:
        print(f"❌ Basic PySide6 import failed: {e}")
        return False

def test_charts_import():
    """Test QCharts import (optional)."""
    print("Testing QCharts import...")
    try:
        from PySide6.QtCharts import QChart, QChartView
        print("✅ QCharts available")
        return True
    except ImportError as e:
        print(f"⚠️  QCharts not available (this is OK): {e}")
        return False

def test_pyqt_signal():
    """Test pyqtSignal import."""
    print("Testing pyqtSignal import...")
    try:
        from PySide6.QtCore import pyqtSignal
        print("✅ pyqtSignal available")
        return True
    except ImportError as e:
        print(f"⚠️  pyqtSignal not available, using Signal fallback: {e}")
        try:
            from PySide6.QtCore import Signal as pyqtSignal
            print("✅ Signal fallback successful")
            return True
        except ImportError as e2:
            print(f"❌ Signal fallback failed: {e2}")
            return False

def test_core_imports():
    """Test core application imports."""
    print("Testing core application imports...")
    try:
        from multichannel_messaging.core.config_manager import ConfigManager
        print("✅ ConfigManager import successful")
        
        from multichannel_messaging.core.i18n_manager import I18nManager
        print("✅ I18nManager import successful")
        
        from multichannel_messaging.core.message_logger import MessageLogger
        print("✅ MessageLogger import successful")
        
        return True
    except ImportError as e:
        print(f"❌ Core import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui_imports():
    """Test GUI imports."""
    print("Testing GUI imports...")
    try:
        from multichannel_messaging.gui.main_window import MainWindow
        print("✅ MainWindow import successful")
        return True
    except ImportError as e:
        print(f"❌ MainWindow import failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    except SyntaxError as e:
        print(f"❌ Syntax error in GUI files: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dialog_imports():
    """Test dialog imports."""
    print("Testing dialog imports...")
    try:
        from multichannel_messaging.gui.whatsapp_settings_dialog import WhatsAppSettingsDialog
        print("✅ WhatsAppSettingsDialog import successful")
        
        from multichannel_messaging.gui.whatsapp_web_settings_dialog import WhatsAppWebSettingsDialog
        print("✅ WhatsAppWebSettingsDialog import successful")
        
        from multichannel_messaging.gui.message_analytics_dialog import MessageAnalyticsDialog
        print("✅ MessageAnalyticsDialog import successful")
        
        return True
    except ImportError as e:
        print(f"❌ Dialog import failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    except SyntaxError as e:
        print(f"❌ Syntax error in dialog files: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_application_manager():
    """Test application manager."""
    print("Testing application manager...")
    try:
        from multichannel_messaging.core.application_manager import initialize_application
        print("✅ Application manager import successful")
        return True
    except ImportError as e:
        print(f"❌ Application manager import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_platform_detection():
    """Test platform detection."""
    print("Testing platform detection...")
    try:
        from multichannel_messaging.utils.platform_utils import get_platform
        platform = get_platform()
        print(f"✅ Platform detected: {platform}")
        return True
    except Exception as e:
        print(f"❌ Platform detection failed: {e}")
        return False

def main():
    """Run all compatibility tests."""
    print("CSC-Reach Windows Compatibility Test")
    print("=" * 50)
    
    tests = [
        ("Basic PySide6 Imports", test_basic_imports),
        ("QCharts Import (Optional)", test_charts_import),
        ("pyqtSignal Import", test_pyqt_signal),
        ("Core Application Imports", test_core_imports),
        ("GUI Imports", test_gui_imports),
        ("Dialog Imports", test_dialog_imports),
        ("Application Manager", test_application_manager),
        ("Platform Detection", test_platform_detection),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("COMPATIBILITY TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("\n🎉 All tests passed! The app should work on this system.")
    else:
        print(f"\n⚠️  {len(results) - passed} tests failed. Check the errors above.")
        print("Common solutions:")
        print("- Install missing dependencies: pip install PySide6")
        print("- For charts: pip install PySide6-Addons")
        print("- Check Python version (3.8+ required)")
        print("- Verify virtual environment is activated")

if __name__ == "__main__":
    main()
