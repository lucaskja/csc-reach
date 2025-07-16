#!/usr/bin/env python3
"""
GUI tests for the main application window.
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from multichannel_messaging.gui.main_window import MainWindow
from multichannel_messaging.core.config_manager import ConfigManager


@pytest.mark.gui
class TestMainWindow:
    """Test cases for the main application window."""
    
    @pytest.fixture
    def app(self):
        """Create QApplication for testing."""
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        yield app
        app.processEvents()
    
    @pytest.fixture
    def main_window(self, app, mock_config_manager):
        """Create main window for testing."""
        with patch('multichannel_messaging.gui.main_window.ConfigManager', return_value=mock_config_manager):
            window = MainWindow()
            yield window
            window.close()
    
    def test_main_window_initialization(self, main_window):
        """Test main window initializes correctly."""
        assert main_window is not None
        assert main_window.windowTitle() == "CSC-Reach - Multi-Channel Messaging"
        assert main_window.isVisible() is False  # Not shown by default in tests
    
    def test_main_window_show(self, main_window):
        """Test main window can be shown."""
        main_window.show()
        assert main_window.isVisible() is True
    
    def test_main_window_menus(self, main_window):
        """Test main window has required menus."""
        menubar = main_window.menuBar()
        assert menubar is not None
        
        # Check for main menus
        menu_titles = [action.text() for action in menubar.actions()]
        expected_menus = ["&File", "&Edit", "&View", "&Tools", "&Help"]
        
        for expected_menu in expected_menus:
            assert any(expected_menu in title for title in menu_titles)
    
    def test_main_window_toolbar(self, main_window):
        """Test main window has toolbar with required actions."""
        toolbars = main_window.findChildren(main_window.__class__.toolbar_class)
        assert len(toolbars) > 0
        
        # Check for main toolbar actions
        main_toolbar = toolbars[0]
        actions = main_toolbar.actions()
        assert len(actions) > 0
    
    def test_main_window_status_bar(self, main_window):
        """Test main window has status bar."""
        status_bar = main_window.statusBar()
        assert status_bar is not None
        assert status_bar.isVisible() is True
    
    @pytest.mark.slow
    def test_main_window_resize(self, main_window):
        """Test main window can be resized."""
        original_size = main_window.size()
        
        # Resize window
        new_width = original_size.width() + 100
        new_height = original_size.height() + 100
        main_window.resize(new_width, new_height)
        
        # Process events to ensure resize is applied
        QApplication.processEvents()
        
        new_size = main_window.size()
        assert new_size.width() >= new_width - 10  # Allow for window manager differences
        assert new_size.height() >= new_height - 10
    
    def test_main_window_keyboard_shortcuts(self, main_window):
        """Test main window keyboard shortcuts."""
        # Test Ctrl+N for new
        QTest.keySequence(main_window, Qt.CTRL | Qt.Key_N)
        QApplication.processEvents()
        
        # Test Ctrl+O for open
        QTest.keySequence(main_window, Qt.CTRL | Qt.Key_O)
        QApplication.processEvents()
        
        # Test Ctrl+S for save
        QTest.keySequence(main_window, Qt.CTRL | Qt.Key_S)
        QApplication.processEvents()
        
        # No assertions here as we're just testing that shortcuts don't crash
        assert True


if __name__ == "__main__":
    pytest.main([__file__])