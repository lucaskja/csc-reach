"""
Theme management for CSC-Reach application.
Provides modern UI styling with light/dark mode support.
"""

import sys
from enum import Enum
from typing import Dict, Any, Optional
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, QSettings
from PySide6.QtGui import QPalette, QColor

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ThemeMode(Enum):
    """Theme mode enumeration."""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class ThemeManager(QObject):
    """Manages application themes and styling."""
    
    theme_changed = Signal(str)  # Emitted when theme changes
    
    def __init__(self, config_manager=None):
        super().__init__()
        self.config_manager = config_manager
        self.current_theme = ThemeMode.SYSTEM
        self._load_theme_preference()
    
    def _load_theme_preference(self):
        """Load theme preference from configuration."""
        if self.config_manager:
            theme_str = self.config_manager.get("app.theme", "system")
            try:
                self.current_theme = ThemeMode(theme_str)
            except ValueError:
                self.current_theme = ThemeMode.SYSTEM
                logger.warning(f"Invalid theme preference: {theme_str}, using system default")
    
    def get_current_theme(self) -> ThemeMode:
        """Get the current theme mode."""
        return self.current_theme
    
    def set_theme(self, theme: ThemeMode):
        """Set the application theme."""
        if theme != self.current_theme:
            self.current_theme = theme
            self._apply_theme()
            
            # Save preference
            if self.config_manager:
                self.config_manager.set("app.theme", theme.value)
            
            self.theme_changed.emit(theme.value)
            logger.info(f"Theme changed to: {theme.value}")
    
    def _apply_theme(self):
        """Apply the current theme to the application."""
        app = QApplication.instance()
        if not app:
            return
        
        if self.current_theme == ThemeMode.SYSTEM:
            self._apply_system_theme()
        elif self.current_theme == ThemeMode.LIGHT:
            self._apply_light_theme()
        elif self.current_theme == ThemeMode.DARK:
            self._apply_dark_theme()
    
    def _apply_system_theme(self):
        """Apply system theme (let OS decide)."""
        app = QApplication.instance()
        if app:
            # Reset to system default
            app.setStyleSheet("")
            app.setPalette(app.style().standardPalette())
    
    def _apply_light_theme(self):
        """Apply light theme."""
        app = QApplication.instance()
        if not app:
            return
        
        # Create light palette
        palette = QPalette()
        
        # Window colors
        palette.setColor(QPalette.Window, QColor(248, 249, 250))
        palette.setColor(QPalette.WindowText, QColor(33, 37, 41))
        
        # Base colors (input fields)
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, QColor(248, 249, 250))
        
        # Text colors
        palette.setColor(QPalette.Text, QColor(33, 37, 41))
        palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
        
        # Button colors
        palette.setColor(QPalette.Button, QColor(233, 236, 239))
        palette.setColor(QPalette.ButtonText, QColor(33, 37, 41))
        
        # Highlight colors
        palette.setColor(QPalette.Highlight, QColor(0, 123, 255))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        # Link colors
        palette.setColor(QPalette.Link, QColor(0, 123, 255))
        palette.setColor(QPalette.LinkVisited, QColor(108, 117, 125))
        
        app.setPalette(palette)
        app.setStyleSheet(self._get_light_stylesheet())
    
    def _apply_dark_theme(self):
        """Apply dark theme."""
        app = QApplication.instance()
        if not app:
            return
        
        # Create dark palette
        palette = QPalette()
        
        # Window colors
        palette.setColor(QPalette.Window, QColor(33, 37, 41))
        palette.setColor(QPalette.WindowText, QColor(248, 249, 250))
        
        # Base colors (input fields)
        palette.setColor(QPalette.Base, QColor(52, 58, 64))
        palette.setColor(QPalette.AlternateBase, QColor(73, 80, 87))
        
        # Text colors
        palette.setColor(QPalette.Text, QColor(248, 249, 250))
        palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
        
        # Button colors
        palette.setColor(QPalette.Button, QColor(73, 80, 87))
        palette.setColor(QPalette.ButtonText, QColor(248, 249, 250))
        
        # Highlight colors
        palette.setColor(QPalette.Highlight, QColor(0, 123, 255))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        # Link colors
        palette.setColor(QPalette.Link, QColor(108, 177, 255))
        palette.setColor(QPalette.LinkVisited, QColor(173, 181, 189))
        
        app.setPalette(palette)
        app.setStyleSheet(self._get_dark_stylesheet())
    
    def _get_light_stylesheet(self) -> str:
        """Get light theme stylesheet."""
        return """
        /* Main Window */
        QMainWindow {
            background-color: #f8f9fa;
            color: #212529;
        }
        
        /* Toolbar */
        QToolBar {
            background-color: #ffffff;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 8px;
            margin: 4px;
        }
        
        /* Buttons */
        QPushButton {
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 500;
            min-width: 80px;
        }
        
        QPushButton:hover {
            background-color: #0056b3;
        }
        
        QPushButton:pressed {
            background-color: #004085;
        }
        
        QPushButton:disabled {
            background-color: #6c757d;
            color: #adb5bd;
        }
        
        QPushButton.secondary {
            background-color: #6c757d;
        }
        
        QPushButton.secondary:hover {
            background-color: #545b62;
        }
        
        QPushButton.success {
            background-color: #28a745;
        }
        
        QPushButton.success:hover {
            background-color: #1e7e34;
        }
        
        QPushButton.danger {
            background-color: #dc3545;
        }
        
        QPushButton.danger:hover {
            background-color: #c82333;
        }
        
        /* Input Fields */
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #ffffff;
            border: 1px solid #ced4da;
            border-radius: 4px;
            padding: 8px 12px;
            color: #495057;
        }
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border-color: #80bdff;
            outline: 0;
            box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
        }
        
        /* ComboBox */
        QComboBox {
            background-color: #ffffff;
            border: 1px solid #ced4da;
            border-radius: 4px;
            padding: 8px 12px;
            color: #495057;
            min-width: 120px;
        }
        
        QComboBox:hover {
            border-color: #80bdff;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        
        QComboBox::down-arrow {
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDFMNiA2TDExIDEiIHN0cm9rZT0iIzZjNzU3ZCIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
        }
        
        /* Group Boxes */
        QGroupBox {
            font-weight: 600;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 12px;
            background-color: #ffffff;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 8px 0 8px;
            color: #495057;
            background-color: #ffffff;
        }
        
        /* Progress Bar */
        QProgressBar {
            border: 1px solid #dee2e6;
            border-radius: 4px;
            text-align: center;
            background-color: #e9ecef;
        }
        
        QProgressBar::chunk {
            background-color: #007bff;
            border-radius: 3px;
        }
        
        /* List Widget */
        QListWidget {
            background-color: #ffffff;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 4px;
        }
        
        QListWidget::item {
            padding: 8px;
            border-radius: 4px;
            margin: 2px;
        }
        
        QListWidget::item:selected {
            background-color: #007bff;
            color: white;
        }
        
        QListWidget::item:hover {
            background-color: #f8f9fa;
        }
        
        /* Status Bar */
        QStatusBar {
            background-color: #f8f9fa;
            border-top: 1px solid #dee2e6;
            color: #6c757d;
        }
        
        /* Menu Bar */
        QMenuBar {
            background-color: #ffffff;
            border-bottom: 1px solid #dee2e6;
            color: #495057;
        }
        
        QMenuBar::item {
            padding: 8px 12px;
            background-color: transparent;
        }
        
        QMenuBar::item:selected {
            background-color: #e9ecef;
            border-radius: 4px;
        }
        
        /* Splitter */
        QSplitter::handle {
            background-color: #dee2e6;
            width: 2px;
            height: 2px;
        }
        
        QSplitter::handle:hover {
            background-color: #007bff;
        }
        """
    
    def _get_dark_stylesheet(self) -> str:
        """Get dark theme stylesheet."""
        return """
        /* Main Window */
        QMainWindow {
            background-color: #212529;
            color: #f8f9fa;
        }
        
        /* Toolbar */
        QToolBar {
            background-color: #343a40;
            border: 1px solid #495057;
            border-radius: 6px;
            padding: 8px;
            margin: 4px;
        }
        
        /* Buttons */
        QPushButton {
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 500;
            min-width: 80px;
        }
        
        QPushButton:hover {
            background-color: #0056b3;
        }
        
        QPushButton:pressed {
            background-color: #004085;
        }
        
        QPushButton:disabled {
            background-color: #495057;
            color: #6c757d;
        }
        
        QPushButton.secondary {
            background-color: #6c757d;
        }
        
        QPushButton.secondary:hover {
            background-color: #545b62;
        }
        
        QPushButton.success {
            background-color: #28a745;
        }
        
        QPushButton.success:hover {
            background-color: #1e7e34;
        }
        
        QPushButton.danger {
            background-color: #dc3545;
        }
        
        QPushButton.danger:hover {
            background-color: #c82333;
        }
        
        /* Input Fields */
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #495057;
            border: 1px solid #6c757d;
            border-radius: 4px;
            padding: 8px 12px;
            color: #f8f9fa;
        }
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border-color: #80bdff;
            outline: 0;
        }
        
        /* ComboBox */
        QComboBox {
            background-color: #495057;
            border: 1px solid #6c757d;
            border-radius: 4px;
            padding: 8px 12px;
            color: #f8f9fa;
            min-width: 120px;
        }
        
        QComboBox:hover {
            border-color: #80bdff;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        
        QComboBox::down-arrow {
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDFMNiA2TDExIDEiIHN0cm9rZT0iI2Y4ZjlmYSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
        }
        
        /* Group Boxes */
        QGroupBox {
            font-weight: 600;
            border: 1px solid #495057;
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 12px;
            background-color: #343a40;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 8px 0 8px;
            color: #f8f9fa;
            background-color: #343a40;
        }
        
        /* Progress Bar */
        QProgressBar {
            border: 1px solid #495057;
            border-radius: 4px;
            text-align: center;
            background-color: #495057;
            color: #f8f9fa;
        }
        
        QProgressBar::chunk {
            background-color: #007bff;
            border-radius: 3px;
        }
        
        /* List Widget */
        QListWidget {
            background-color: #343a40;
            border: 1px solid #495057;
            border-radius: 4px;
            padding: 4px;
            color: #f8f9fa;
        }
        
        QListWidget::item {
            padding: 8px;
            border-radius: 4px;
            margin: 2px;
        }
        
        QListWidget::item:selected {
            background-color: #007bff;
            color: white;
        }
        
        QListWidget::item:hover {
            background-color: #495057;
        }
        
        /* Status Bar */
        QStatusBar {
            background-color: #343a40;
            border-top: 1px solid #495057;
            color: #adb5bd;
        }
        
        /* Menu Bar */
        QMenuBar {
            background-color: #343a40;
            border-bottom: 1px solid #495057;
            color: #f8f9fa;
        }
        
        QMenuBar::item {
            padding: 8px 12px;
            background-color: transparent;
        }
        
        QMenuBar::item:selected {
            background-color: #495057;
            border-radius: 4px;
        }
        
        /* Splitter */
        QSplitter::handle {
            background-color: #495057;
            width: 2px;
            height: 2px;
        }
        
        QSplitter::handle:hover {
            background-color: #007bff;
        }
        """
    
    def get_theme_options(self) -> Dict[str, str]:
        """Get available theme options for UI."""
        return {
            "system": "System Default",
            "light": "Light Mode", 
            "dark": "Dark Mode"
        }
    
    def is_dark_theme(self) -> bool:
        """Check if current theme is dark."""
        if self.current_theme == ThemeMode.DARK:
            return True
        elif self.current_theme == ThemeMode.SYSTEM:
            # Try to detect system theme
            app = QApplication.instance()
            if app:
                palette = app.palette()
                window_color = palette.color(QPalette.Window)
                # Consider dark if window background is darker
                return window_color.lightness() < 128
        return False
    
    def apply_button_style(self, button, style_class: str = "primary"):
        """Apply specific style class to a button."""
        if style_class == "secondary":
            button.setProperty("class", "secondary")
        elif style_class == "success":
            button.setProperty("class", "success")
        elif style_class == "danger":
            button.setProperty("class", "danger")
        
        # Refresh style
        button.style().unpolish(button)
        button.style().polish(button)