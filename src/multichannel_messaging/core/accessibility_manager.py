"""
Accessibility manager for CSC-Reach application.
Provides screen reader support, keyboard navigation, and other accessibility features.
"""

import sys
from typing import Dict, Any, Optional, List
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QLineEdit, QTextEdit
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtGui import QFont, QPalette, QColor, QKeySequence, QAction

from ..utils.logger import get_logger

logger = get_logger(__name__)


class AccessibilityManager(QObject):
    """Manages accessibility features for the application."""
    
    # Signals
    accessibility_changed = Signal(str)  # feature_name
    focus_changed = Signal(QWidget)      # focused_widget
    
    def __init__(self, preferences_manager=None):
        super().__init__()
        self.preferences_manager = preferences_manager
        self.app = QApplication.instance()
        
        # Accessibility state
        self.screen_reader_enabled = False
        self.high_contrast_enabled = False
        self.large_fonts_enabled = False
        self.keyboard_only_mode = False
        self.enhanced_focus_enabled = False
        self.voice_control_enabled = False
        
        # Focus tracking
        self.current_focus_widget = None
        self.focus_history = []
        self.max_focus_history = 10
        
        # Keyboard navigation
        self.tab_order_widgets = []
        self.current_tab_index = -1
        
        # Load preferences
        self.load_accessibility_preferences()
        
        # Set up focus tracking
        if self.app:
            self.app.focusChanged.connect(self.on_focus_changed)
    
    def load_accessibility_preferences(self):
        """Load accessibility preferences."""
        if not self.preferences_manager:
            return
        
        accessibility_config = self.preferences_manager.get_accessibility_config()
        
        self.screen_reader_enabled = accessibility_config.screen_reader_support
        self.high_contrast_enabled = accessibility_config.high_contrast_mode
        self.large_fonts_enabled = accessibility_config.large_fonts
        self.keyboard_only_mode = accessibility_config.keyboard_navigation_only
        self.enhanced_focus_enabled = accessibility_config.focus_indicators_enhanced
        self.voice_control_enabled = accessibility_config.voice_control_enabled
        
        # Apply settings
        self.apply_accessibility_settings()
    
    def apply_accessibility_settings(self):
        """Apply current accessibility settings."""
        if self.high_contrast_enabled:
            self.enable_high_contrast_mode()
        
        if self.large_fonts_enabled:
            self.enable_large_fonts()
        
        if self.enhanced_focus_enabled:
            self.enable_enhanced_focus_indicators()
        
        if self.screen_reader_enabled:
            self.enable_screen_reader_support()
        
        if self.keyboard_only_mode:
            self.enable_keyboard_only_mode()
    
    def enable_screen_reader_support(self):
        """Enable screen reader support."""
        self.screen_reader_enabled = True
        
        if self.app:
            # Set accessible properties for the application
            self.app.setProperty("accessibleName", "CSC-Reach Communication Platform")
            self.app.setProperty("accessibleDescription", 
                               "Multi-channel messaging application for business communication")
        
        logger.info("Screen reader support enabled")
        self.accessibility_changed.emit("screen_reader")
    
    def disable_screen_reader_support(self):
        """Disable screen reader support."""
        self.screen_reader_enabled = False
        logger.info("Screen reader support disabled")
        self.accessibility_changed.emit("screen_reader")
    
    def enable_high_contrast_mode(self):
        """Enable high contrast mode."""
        self.high_contrast_enabled = True
        
        if self.app:
            # Create high contrast palette
            palette = QPalette()
            
            # High contrast colors
            palette.setColor(QPalette.Window, QColor(0, 0, 0))           # Black background
            palette.setColor(QPalette.WindowText, QColor(255, 255, 255)) # White text
            palette.setColor(QPalette.Base, QColor(0, 0, 0))             # Black input background
            palette.setColor(QPalette.AlternateBase, QColor(64, 64, 64)) # Dark gray alternate
            palette.setColor(QPalette.Text, QColor(255, 255, 255))       # White input text
            palette.setColor(QPalette.Button, QColor(64, 64, 64))        # Dark gray buttons
            palette.setColor(QPalette.ButtonText, QColor(255, 255, 255)) # White button text
            palette.setColor(QPalette.Highlight, QColor(255, 255, 0))    # Yellow highlight
            palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))  # Black highlighted text
            
            self.app.setPalette(palette)
        
        logger.info("High contrast mode enabled")
        self.accessibility_changed.emit("high_contrast")
    
    def disable_high_contrast_mode(self):
        """Disable high contrast mode."""
        self.high_contrast_enabled = False
        
        if self.app:
            # Reset to default palette
            self.app.setPalette(self.app.style().standardPalette())
        
        logger.info("High contrast mode disabled")
        self.accessibility_changed.emit("high_contrast")
    
    def enable_large_fonts(self):
        """Enable large fonts."""
        self.large_fonts_enabled = True
        
        if self.app:
            current_font = self.app.font()
            large_font = QFont(current_font)
            large_font.setPointSize(current_font.pointSize() + 4)  # Increase by 4 points
            self.app.setFont(large_font)
        
        logger.info("Large fonts enabled")
        self.accessibility_changed.emit("large_fonts")
    
    def disable_large_fonts(self):
        """Disable large fonts."""
        self.large_fonts_enabled = False
        
        if self.app:
            # Reset to default font
            default_font = QFont()
            self.app.setFont(default_font)
        
        logger.info("Large fonts disabled")
        self.accessibility_changed.emit("large_fonts")
    
    def enable_enhanced_focus_indicators(self):
        """Enable enhanced focus indicators."""
        self.enhanced_focus_enabled = True
        
        # Apply enhanced focus stylesheet
        if self.app:
            focus_stylesheet = """
            QWidget:focus {
                border: 3px solid #FFD700;
                background-color: rgba(255, 215, 0, 0.2);
            }
            
            QPushButton:focus {
                border: 3px solid #FFD700;
                background-color: rgba(255, 215, 0, 0.3);
            }
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border: 3px solid #FFD700;
                background-color: rgba(255, 215, 0, 0.1);
            }
            
            QComboBox:focus {
                border: 3px solid #FFD700;
                background-color: rgba(255, 215, 0, 0.2);
            }
            """
            
            current_stylesheet = self.app.styleSheet()
            self.app.setStyleSheet(current_stylesheet + focus_stylesheet)
        
        logger.info("Enhanced focus indicators enabled")
        self.accessibility_changed.emit("enhanced_focus")
    
    def disable_enhanced_focus_indicators(self):
        """Disable enhanced focus indicators."""
        self.enhanced_focus_enabled = False
        logger.info("Enhanced focus indicators disabled")
        self.accessibility_changed.emit("enhanced_focus")
    
    def enable_keyboard_only_mode(self):
        """Enable keyboard-only navigation mode."""
        self.keyboard_only_mode = True
        
        # Hide mouse cursor when in keyboard-only mode
        if self.app:
            self.app.setOverrideCursor(Qt.BlankCursor)
        
        logger.info("Keyboard-only mode enabled")
        self.accessibility_changed.emit("keyboard_only")
    
    def disable_keyboard_only_mode(self):
        """Disable keyboard-only navigation mode."""
        self.keyboard_only_mode = False
        
        # Restore mouse cursor
        if self.app:
            self.app.restoreOverrideCursor()
        
        logger.info("Keyboard-only mode disabled")
        self.accessibility_changed.emit("keyboard_only")
    
    def set_accessible_properties(self, widget: QWidget, name: str, description: str = "", role: str = ""):
        """Set accessible properties for a widget."""
        if not widget or not self.screen_reader_enabled:
            return
        
        widget.setAccessibleName(name)
        if description:
            widget.setAccessibleDescription(description)
        
        # Set role-specific properties
        if isinstance(widget, QPushButton):
            widget.setAccessibleDescription(f"Button: {description or name}")
        elif isinstance(widget, QLineEdit):
            widget.setAccessibleDescription(f"Text input: {description or name}")
        elif isinstance(widget, QTextEdit):
            widget.setAccessibleDescription(f"Text area: {description or name}")
        elif isinstance(widget, QLabel):
            widget.setAccessibleDescription(f"Label: {description or name}")
    
    def announce_to_screen_reader(self, message: str):
        """Announce a message to screen readers."""
        if not self.screen_reader_enabled:
            return
        
        # Create a temporary label for screen reader announcement
        if self.app:
            temp_label = QLabel(message)
            temp_label.setAccessibleName("Status announcement")
            temp_label.setAccessibleDescription(message)
            
            # Use QTimer to clean up the temporary label
            QTimer.singleShot(100, temp_label.deleteLater)
        
        logger.debug(f"Screen reader announcement: {message}")
    
    def on_focus_changed(self, old_widget: QWidget, new_widget: QWidget):
        """Handle focus change events."""
        if new_widget:
            self.current_focus_widget = new_widget
            
            # Add to focus history
            self.focus_history.append(new_widget)
            if len(self.focus_history) > self.max_focus_history:
                self.focus_history.pop(0)
            
            # Announce focus change to screen reader
            if self.screen_reader_enabled:
                widget_name = new_widget.accessibleName() or new_widget.objectName() or "Unnamed widget"
                widget_type = type(new_widget).__name__
                self.announce_to_screen_reader(f"Focus moved to {widget_type}: {widget_name}")
            
            self.focus_changed.emit(new_widget)
    
    def setup_keyboard_navigation(self, widgets: List[QWidget]):
        """Set up keyboard navigation for a list of widgets."""
        self.tab_order_widgets = widgets
        self.current_tab_index = -1
        
        # Set tab order
        for i in range(len(widgets) - 1):
            QWidget.setTabOrder(widgets[i], widgets[i + 1])
    
    def navigate_to_next_widget(self):
        """Navigate to the next widget in tab order."""
        if not self.tab_order_widgets:
            return
        
        self.current_tab_index = (self.current_tab_index + 1) % len(self.tab_order_widgets)
        next_widget = self.tab_order_widgets[self.current_tab_index]
        
        if next_widget and next_widget.isEnabled() and next_widget.isVisible():
            next_widget.setFocus()
    
    def navigate_to_previous_widget(self):
        """Navigate to the previous widget in tab order."""
        if not self.tab_order_widgets:
            return
        
        self.current_tab_index = (self.current_tab_index - 1) % len(self.tab_order_widgets)
        prev_widget = self.tab_order_widgets[self.current_tab_index]
        
        if prev_widget and prev_widget.isEnabled() and prev_widget.isVisible():
            prev_widget.setFocus()
    
    def get_accessibility_status(self) -> Dict[str, bool]:
        """Get current accessibility feature status."""
        return {
            "screen_reader": self.screen_reader_enabled,
            "high_contrast": self.high_contrast_enabled,
            "large_fonts": self.large_fonts_enabled,
            "keyboard_only": self.keyboard_only_mode,
            "enhanced_focus": self.enhanced_focus_enabled,
            "voice_control": self.voice_control_enabled
        }
    
    def toggle_accessibility_feature(self, feature: str):
        """Toggle an accessibility feature on/off."""
        if feature == "screen_reader":
            if self.screen_reader_enabled:
                self.disable_screen_reader_support()
            else:
                self.enable_screen_reader_support()
        elif feature == "high_contrast":
            if self.high_contrast_enabled:
                self.disable_high_contrast_mode()
            else:
                self.enable_high_contrast_mode()
        elif feature == "large_fonts":
            if self.large_fonts_enabled:
                self.disable_large_fonts()
            else:
                self.enable_large_fonts()
        elif feature == "keyboard_only":
            if self.keyboard_only_mode:
                self.disable_keyboard_only_mode()
            else:
                self.enable_keyboard_only_mode()
        elif feature == "enhanced_focus":
            if self.enhanced_focus_enabled:
                self.disable_enhanced_focus_indicators()
            else:
                self.enable_enhanced_focus_indicators()
    
    def create_accessibility_shortcuts(self, parent_widget: QWidget) -> List[QAction]:
        """Create accessibility keyboard shortcuts."""
        shortcuts = []
        
        # Toggle high contrast mode
        high_contrast_action = QAction("Toggle High Contrast", parent_widget)
        high_contrast_action.setShortcut(QKeySequence("Ctrl+Shift+H"))
        high_contrast_action.triggered.connect(lambda: self.toggle_accessibility_feature("high_contrast"))
        shortcuts.append(high_contrast_action)
        
        # Toggle large fonts
        large_fonts_action = QAction("Toggle Large Fonts", parent_widget)
        large_fonts_action.setShortcut(QKeySequence("Ctrl+Shift+F"))
        large_fonts_action.triggered.connect(lambda: self.toggle_accessibility_feature("large_fonts"))
        shortcuts.append(large_fonts_action)
        
        # Toggle enhanced focus
        enhanced_focus_action = QAction("Toggle Enhanced Focus", parent_widget)
        enhanced_focus_action.setShortcut(QKeySequence("Ctrl+Shift+E"))
        enhanced_focus_action.triggered.connect(lambda: self.toggle_accessibility_feature("enhanced_focus"))
        shortcuts.append(enhanced_focus_action)
        
        # Navigate to next widget
        next_widget_action = QAction("Next Widget", parent_widget)
        next_widget_action.setShortcut(QKeySequence("Ctrl+Tab"))
        next_widget_action.triggered.connect(self.navigate_to_next_widget)
        shortcuts.append(next_widget_action)
        
        # Navigate to previous widget
        prev_widget_action = QAction("Previous Widget", parent_widget)
        prev_widget_action.setShortcut(QKeySequence("Ctrl+Shift+Tab"))
        prev_widget_action.triggered.connect(self.navigate_to_previous_widget)
        shortcuts.append(prev_widget_action)
        
        return shortcuts
    
    def get_focus_path(self) -> str:
        """Get a description of the current focus path."""
        if not self.current_focus_widget:
            return "No widget focused"
        
        path_parts = []
        widget = self.current_focus_widget
        
        while widget:
            name = widget.accessibleName() or widget.objectName() or type(widget).__name__
            path_parts.append(name)
            widget = widget.parent()
        
        return " → ".join(reversed(path_parts))
    
    def save_accessibility_preferences(self):
        """Save current accessibility settings to preferences."""
        if not self.preferences_manager:
            return
        
        self.preferences_manager.set_accessibility_option("screen_reader_support", self.screen_reader_enabled)
        self.preferences_manager.set_accessibility_option("high_contrast_mode", self.high_contrast_enabled)
        self.preferences_manager.set_accessibility_option("large_fonts", self.large_fonts_enabled)
        self.preferences_manager.set_accessibility_option("keyboard_navigation_only", self.keyboard_only_mode)
        self.preferences_manager.set_accessibility_option("focus_indicators_enhanced", self.enhanced_focus_enabled)
        self.preferences_manager.set_accessibility_option("voice_control_enabled", self.voice_control_enabled)
        
        logger.info("Accessibility preferences saved")