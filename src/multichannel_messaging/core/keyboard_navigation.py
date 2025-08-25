"""
Keyboard navigation helper for CSC-Reach application.
Provides comprehensive keyboard navigation support.
"""

from typing import Dict, List, Optional, Callable
from PySide6.QtWidgets import QWidget, QApplication, QMainWindow
from PySide6.QtCore import QObject, Signal, QEvent, Qt
from PySide6.QtGui import QKeyEvent, QKeySequence

from ..utils.logger import get_logger

logger = get_logger(__name__)


class KeyboardNavigationManager(QObject):
    """Manages keyboard navigation throughout the application."""
    
    # Signals
    navigation_changed = Signal(str, QWidget)  # direction, widget
    shortcut_activated = Signal(str)           # shortcut_name
    
    def __init__(self):
        super().__init__()
        self.app = QApplication.instance()
        
        # Navigation state
        self.navigation_enabled = True
        self.current_focus_widget = None
        self.navigation_groups = {}  # group_name -> list of widgets
        self.current_group = None
        self.group_index = 0
        
        # Keyboard shortcuts
        self.shortcuts = {}
        self.global_shortcuts = {}
        
        # Navigation history
        self.focus_history = []
        self.max_history = 20
        
        # Install event filter for global keyboard handling
        if self.app:
            self.app.installEventFilter(self)
    
    def register_navigation_group(self, group_name: str, widgets: List[QWidget], circular: bool = True):
        """Register a group of widgets for keyboard navigation."""
        self.navigation_groups[group_name] = {
            'widgets': widgets,
            'circular': circular,
            'current_index': 0
        }
        
        # Set up tab order within the group
        for i in range(len(widgets) - 1):
            if widgets[i] and widgets[i + 1]:
                QWidget.setTabOrder(widgets[i], widgets[i + 1])
        
        logger.debug(f"Registered navigation group '{group_name}' with {len(widgets)} widgets")
    
    def set_active_navigation_group(self, group_name: str):
        """Set the active navigation group."""
        if group_name in self.navigation_groups:
            self.current_group = group_name
            self.group_index = 0
            logger.debug(f"Set active navigation group to '{group_name}'")
    
    def navigate_within_group(self, direction: str):
        """Navigate within the current group."""
        if not self.current_group or self.current_group not in self.navigation_groups:
            return False
        
        group = self.navigation_groups[self.current_group]
        widgets = group['widgets']
        
        if not widgets:
            return False
        
        if direction == "next":
            self.group_index = (self.group_index + 1) % len(widgets)
        elif direction == "previous":
            self.group_index = (self.group_index - 1) % len(widgets)
        elif direction == "first":
            self.group_index = 0
        elif direction == "last":
            self.group_index = len(widgets) - 1
        else:
            return False
        
        # Focus the widget
        target_widget = widgets[self.group_index]
        if target_widget and target_widget.isEnabled() and target_widget.isVisible():
            target_widget.setFocus()
            self.add_to_focus_history(target_widget)
            self.navigation_changed.emit(direction, target_widget)
            return True
        
        return False
    
    def navigate_to_widget_by_name(self, widget_name: str) -> bool:
        """Navigate to a specific widget by name."""
        for group_name, group in self.navigation_groups.items():
            for i, widget in enumerate(group['widgets']):
                if widget and (widget.objectName() == widget_name or 
                              widget.accessibleName() == widget_name):
                    self.current_group = group_name
                    self.group_index = i
                    widget.setFocus()
                    self.add_to_focus_history(widget)
                    self.navigation_changed.emit("direct", widget)
                    return True
        return False
    
    def register_keyboard_shortcut(self, key_sequence: str, callback: Callable, 
                                 description: str = "", global_shortcut: bool = False):
        """Register a keyboard shortcut."""
        shortcut_data = {
            'sequence': QKeySequence(key_sequence),
            'callback': callback,
            'description': description
        }
        
        if global_shortcut:
            self.global_shortcuts[key_sequence] = shortcut_data
        else:
            self.shortcuts[key_sequence] = shortcut_data
        
        logger.debug(f"Registered {'global ' if global_shortcut else ''}shortcut: {key_sequence}")
    
    def unregister_keyboard_shortcut(self, key_sequence: str, global_shortcut: bool = False):
        """Unregister a keyboard shortcut."""
        target_dict = self.global_shortcuts if global_shortcut else self.shortcuts
        if key_sequence in target_dict:
            del target_dict[key_sequence]
            logger.debug(f"Unregistered shortcut: {key_sequence}")
    
    def handle_key_event(self, event: QKeyEvent) -> bool:
        """Handle key events for navigation and shortcuts."""
        if not self.navigation_enabled:
            return False
        
        key_sequence = QKeySequence(event.key() | int(event.modifiers()))
        key_string = key_sequence.toString()
        
        # Check global shortcuts first
        if key_string in self.global_shortcuts:
            shortcut_data = self.global_shortcuts[key_string]
            try:
                shortcut_data['callback']()
                self.shortcut_activated.emit(key_string)
                return True
            except Exception as e:
                logger.error(f"Error executing global shortcut {key_string}: {e}")
        
        # Check regular shortcuts
        if key_string in self.shortcuts:
            shortcut_data = self.shortcuts[key_string]
            try:
                shortcut_data['callback']()
                self.shortcut_activated.emit(key_string)
                return True
            except Exception as e:
                logger.error(f"Error executing shortcut {key_string}: {e}")
        
        # Handle navigation keys
        if event.key() == Qt.Key_Tab:
            if event.modifiers() & Qt.ShiftModifier:
                return self.navigate_within_group("previous")
            else:
                return self.navigate_within_group("next")
        
        elif event.key() == Qt.Key_Home and event.modifiers() & Qt.ControlModifier:
            return self.navigate_within_group("first")
        
        elif event.key() == Qt.Key_End and event.modifiers() & Qt.ControlModifier:
            return self.navigate_within_group("last")
        
        # Arrow key navigation within groups
        elif event.key() == Qt.Key_Right and event.modifiers() & Qt.ControlModifier:
            return self.navigate_within_group("next")
        
        elif event.key() == Qt.Key_Left and event.modifiers() & Qt.ControlModifier:
            return self.navigate_within_group("previous")
        
        return False
    
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Event filter for global keyboard handling."""
        if event.type() == QEvent.KeyPress and isinstance(event, QKeyEvent):
            if self.handle_key_event(event):
                return True
        
        return super().eventFilter(obj, event)
    
    def add_to_focus_history(self, widget: QWidget):
        """Add widget to focus history."""
        if widget in self.focus_history:
            self.focus_history.remove(widget)
        
        self.focus_history.append(widget)
        
        if len(self.focus_history) > self.max_history:
            self.focus_history.pop(0)
        
        self.current_focus_widget = widget
    
    def go_back_in_focus_history(self) -> bool:
        """Go back to the previous widget in focus history."""
        if len(self.focus_history) < 2:
            return False
        
        # Remove current widget and get previous
        self.focus_history.pop()  # Remove current
        if self.focus_history:
            previous_widget = self.focus_history[-1]
            if previous_widget and previous_widget.isEnabled() and previous_widget.isVisible():
                previous_widget.setFocus()
                self.navigation_changed.emit("back", previous_widget)
                return True
        
        return False
    
    def create_navigation_help(self) -> Dict[str, str]:
        """Create navigation help information."""
        help_info = {
            "Basic Navigation": {
                "Tab": "Move to next element",
                "Shift+Tab": "Move to previous element",
                "Ctrl+Home": "Move to first element in group",
                "Ctrl+End": "Move to last element in group",
                "Ctrl+Right": "Move to next element in group",
                "Ctrl+Left": "Move to previous element in group"
            },
            "Registered Shortcuts": {}
        }
        
        # Add registered shortcuts
        for key_sequence, shortcut_data in self.shortcuts.items():
            description = shortcut_data.get('description', 'No description')
            help_info["Registered Shortcuts"][key_sequence] = description
        
        # Add global shortcuts
        if self.global_shortcuts:
            help_info["Global Shortcuts"] = {}
            for key_sequence, shortcut_data in self.global_shortcuts.items():
                description = shortcut_data.get('description', 'No description')
                help_info["Global Shortcuts"][key_sequence] = description
        
        return help_info
    
    def enable_navigation(self):
        """Enable keyboard navigation."""
        self.navigation_enabled = True
        logger.debug("Keyboard navigation enabled")
    
    def disable_navigation(self):
        """Disable keyboard navigation."""
        self.navigation_enabled = False
        logger.debug("Keyboard navigation disabled")
    
    def get_current_navigation_state(self) -> Dict[str, any]:
        """Get current navigation state information."""
        return {
            "enabled": self.navigation_enabled,
            "current_group": self.current_group,
            "group_index": self.group_index,
            "current_widget": self.current_focus_widget.objectName() if self.current_focus_widget else None,
            "groups_count": len(self.navigation_groups),
            "shortcuts_count": len(self.shortcuts),
            "global_shortcuts_count": len(self.global_shortcuts),
            "focus_history_length": len(self.focus_history)
        }
    
    def setup_main_window_navigation(self, main_window: QMainWindow):
        """Set up navigation for main window components."""
        # Get main window widgets for navigation
        central_widget = main_window.centralWidget()
        if not central_widget:
            return
        
        # Find navigable widgets
        navigable_widgets = []
        
        def find_navigable_widgets(widget):
            """Recursively find navigable widgets."""
            if widget.focusPolicy() != Qt.NoFocus and widget.isEnabled() and widget.isVisible():
                navigable_widgets.append(widget)
            
            for child in widget.findChildren(QWidget):
                if child.focusPolicy() != Qt.NoFocus and child.isEnabled() and child.isVisible():
                    navigable_widgets.append(child)
        
        find_navigable_widgets(central_widget)
        
        # Register main navigation group
        if navigable_widgets:
            self.register_navigation_group("main_window", navigable_widgets)
            self.set_active_navigation_group("main_window")
        
        # Register common shortcuts for main window
        self.register_keyboard_shortcut("Ctrl+1", 
                                      lambda: self.navigate_to_widget_by_name("recipients_list"),
                                      "Focus recipients list")
        
        self.register_keyboard_shortcut("Ctrl+2", 
                                      lambda: self.navigate_to_widget_by_name("template_combo"),
                                      "Focus template selector")
        
        self.register_keyboard_shortcut("Ctrl+3", 
                                      lambda: self.navigate_to_widget_by_name("log_text"),
                                      "Focus log area")
        
        self.register_keyboard_shortcut("Alt+Left", 
                                      self.go_back_in_focus_history,
                                      "Go back in focus history")
        
        logger.info(f"Set up main window navigation with {len(navigable_widgets)} widgets")
    
    def announce_navigation_state(self) -> str:
        """Get announcement text for current navigation state."""
        if not self.current_focus_widget:
            return "No widget focused"
        
        widget_name = (self.current_focus_widget.accessibleName() or 
                      self.current_focus_widget.objectName() or 
                      type(self.current_focus_widget).__name__)
        
        group_info = ""
        if self.current_group:
            group = self.navigation_groups[self.current_group]
            total_widgets = len(group['widgets'])
            group_info = f" ({self.group_index + 1} of {total_widgets} in {self.current_group})"
        
        return f"Focused on {widget_name}{group_info}"