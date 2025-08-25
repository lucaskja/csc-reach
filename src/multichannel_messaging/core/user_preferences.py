"""
User preferences management for CSC-Reach application.
Handles customizable interface settings and user preferences.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from enum import Enum
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QKeySequence

from ..utils.logger import get_logger
from ..utils.platform_utils import get_config_dir

logger = get_logger(__name__)


class ToolbarPosition(Enum):
    """Toolbar position options."""
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


class WindowLayout(Enum):
    """Window layout options."""
    STANDARD = "standard"
    COMPACT = "compact"
    WIDE = "wide"
    MINIMAL = "minimal"


@dataclass
class KeyboardShortcut:
    """Keyboard shortcut configuration."""
    action: str
    sequence: str
    description: str
    category: str = "general"
    
    def to_qkeysequence(self) -> QKeySequence:
        """Convert to QKeySequence."""
        return QKeySequence(self.sequence)


@dataclass
class ToolbarConfig:
    """Toolbar configuration."""
    position: ToolbarPosition = ToolbarPosition.TOP
    visible: bool = True
    icon_size: int = 24
    show_text: bool = True
    buttons: List[str] = field(default_factory=lambda: [
        "import_csv", "send_messages", "create_draft", "template_library", "settings"
    ])


@dataclass
class WindowConfig:
    """Window configuration."""
    layout: WindowLayout = WindowLayout.STANDARD
    remember_geometry: bool = True
    remember_splitter_state: bool = True
    width: int = 1200
    height: int = 800
    x: int = -1
    y: int = -1
    maximized: bool = False
    splitter_sizes: List[int] = field(default_factory=lambda: [400, 800])


@dataclass
class InterfaceConfig:
    """Interface configuration."""
    theme: str = "system"
    font_family: str = ""
    font_size: int = 9
    high_contrast: bool = False
    animations_enabled: bool = True
    show_tooltips: bool = True
    compact_mode: bool = False
    show_status_bar: bool = True
    show_progress_details: bool = True


@dataclass
class AccessibilityConfig:
    """Accessibility configuration."""
    screen_reader_support: bool = False
    high_contrast_mode: bool = False
    large_fonts: bool = False
    keyboard_navigation_only: bool = False
    voice_control_enabled: bool = False
    focus_indicators_enhanced: bool = False


@dataclass
class UserPreferences:
    """Complete user preferences."""
    version: str = "1.0"
    toolbar: ToolbarConfig = field(default_factory=ToolbarConfig)
    window: WindowConfig = field(default_factory=WindowConfig)
    interface: InterfaceConfig = field(default_factory=InterfaceConfig)
    accessibility: AccessibilityConfig = field(default_factory=AccessibilityConfig)
    keyboard_shortcuts: List[KeyboardShortcut] = field(default_factory=list)
    custom_settings: Dict[str, Any] = field(default_factory=dict)


class UserPreferencesManager(QObject):
    """Manages user preferences and customization settings."""
    
    # Signals
    preferences_changed = Signal(str)  # preference_category
    theme_changed = Signal(str)        # theme_name
    layout_changed = Signal(str)       # layout_name
    shortcuts_changed = Signal()
    
    def __init__(self, config_manager=None):
        super().__init__()
        self.config_manager = config_manager
        self.config_dir = get_config_dir()
        self.preferences_file = self.config_dir / "user_preferences.json"
        
        # Default preferences
        self.preferences = UserPreferences()
        
        # Load preferences
        self.load_preferences()
        
        # Initialize default shortcuts
        if not self.preferences.keyboard_shortcuts:
            self._initialize_default_shortcuts()
    
    def load_preferences(self):
        """Load preferences from file."""
        try:
            if self.preferences_file.exists():
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert dict back to dataclass
                self.preferences = self._dict_to_preferences(data)
                logger.info("Loaded user preferences")
            else:
                # Create default preferences file
                self.save_preferences()
                logger.info("Created default user preferences")
                
        except Exception as e:
            logger.error(f"Failed to load user preferences: {e}")
            # Use defaults
            self.preferences = UserPreferences()
    
    def save_preferences(self):
        """Save preferences to file."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Convert dataclass to dict
            data = self._preferences_to_dict(self.preferences)
            
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.debug("Saved user preferences")
            
        except Exception as e:
            logger.error(f"Failed to save user preferences: {e}")
    
    def _preferences_to_dict(self, prefs: UserPreferences) -> Dict[str, Any]:
        """Convert preferences dataclass to dictionary."""
        data = asdict(prefs)
        
        # Convert enums to strings
        data['toolbar']['position'] = prefs.toolbar.position.value
        data['window']['layout'] = prefs.window.layout.value
        
        return data
    
    def _dict_to_preferences(self, data: Dict[str, Any]) -> UserPreferences:
        """Convert dictionary to preferences dataclass."""
        # Handle toolbar config
        toolbar_data = data.get('toolbar', {})
        toolbar = ToolbarConfig(
            position=ToolbarPosition(toolbar_data.get('position', 'top')),
            visible=toolbar_data.get('visible', True),
            icon_size=toolbar_data.get('icon_size', 24),
            show_text=toolbar_data.get('show_text', True),
            buttons=toolbar_data.get('buttons', ToolbarConfig().buttons)
        )
        
        # Handle window config
        window_data = data.get('window', {})
        window = WindowConfig(
            layout=WindowLayout(window_data.get('layout', 'standard')),
            remember_geometry=window_data.get('remember_geometry', True),
            remember_splitter_state=window_data.get('remember_splitter_state', True),
            width=window_data.get('width', 1200),
            height=window_data.get('height', 800),
            x=window_data.get('x', -1),
            y=window_data.get('y', -1),
            maximized=window_data.get('maximized', False),
            splitter_sizes=window_data.get('splitter_sizes', [400, 800])
        )
        
        # Handle interface config
        interface_data = data.get('interface', {})
        interface = InterfaceConfig(
            theme=interface_data.get('theme', 'system'),
            font_family=interface_data.get('font_family', ''),
            font_size=interface_data.get('font_size', 9),
            high_contrast=interface_data.get('high_contrast', False),
            animations_enabled=interface_data.get('animations_enabled', True),
            show_tooltips=interface_data.get('show_tooltips', True),
            compact_mode=interface_data.get('compact_mode', False),
            show_status_bar=interface_data.get('show_status_bar', True),
            show_progress_details=interface_data.get('show_progress_details', True)
        )
        
        # Handle accessibility config
        accessibility_data = data.get('accessibility', {})
        accessibility = AccessibilityConfig(
            screen_reader_support=accessibility_data.get('screen_reader_support', False),
            high_contrast_mode=accessibility_data.get('high_contrast_mode', False),
            large_fonts=accessibility_data.get('large_fonts', False),
            keyboard_navigation_only=accessibility_data.get('keyboard_navigation_only', False),
            voice_control_enabled=accessibility_data.get('voice_control_enabled', False),
            focus_indicators_enhanced=accessibility_data.get('focus_indicators_enhanced', False)
        )
        
        # Handle keyboard shortcuts
        shortcuts_data = data.get('keyboard_shortcuts', [])
        shortcuts = []
        for shortcut_data in shortcuts_data:
            shortcuts.append(KeyboardShortcut(
                action=shortcut_data['action'],
                sequence=shortcut_data['sequence'],
                description=shortcut_data['description'],
                category=shortcut_data.get('category', 'general')
            ))
        
        return UserPreferences(
            version=data.get('version', '1.0'),
            toolbar=toolbar,
            window=window,
            interface=interface,
            accessibility=accessibility,
            keyboard_shortcuts=shortcuts,
            custom_settings=data.get('custom_settings', {})
        )
    
    def _initialize_default_shortcuts(self):
        """Initialize default keyboard shortcuts."""
        default_shortcuts = [
            # File operations
            KeyboardShortcut("import_csv", "Ctrl+O", "Import CSV file", "file"),
            KeyboardShortcut("export_templates", "Ctrl+E", "Export templates", "file"),
            KeyboardShortcut("quit", "Ctrl+Q", "Quit application", "file"),
            
            # Template operations
            KeyboardShortcut("new_template", "Ctrl+N", "Create new template", "templates"),
            KeyboardShortcut("save_template", "Ctrl+S", "Save current template", "templates"),
            KeyboardShortcut("template_library", "Ctrl+T", "Open template library", "templates"),
            
            # Messaging operations
            KeyboardShortcut("send_messages", "Ctrl+Return", "Send messages", "messaging"),
            KeyboardShortcut("create_draft", "Ctrl+D", "Create draft", "messaging"),
            KeyboardShortcut("preview_message", "Ctrl+P", "Preview message", "messaging"),
            
            # View operations
            KeyboardShortcut("toggle_fullscreen", "F11", "Toggle fullscreen", "view"),
            KeyboardShortcut("zoom_in", "Ctrl++", "Zoom in", "view"),
            KeyboardShortcut("zoom_out", "Ctrl+-", "Zoom out", "view"),
            KeyboardShortcut("reset_zoom", "Ctrl+0", "Reset zoom", "view"),
            
            # Navigation
            KeyboardShortcut("focus_recipients", "Ctrl+1", "Focus recipients list", "navigation"),
            KeyboardShortcut("focus_template", "Ctrl+2", "Focus template editor", "navigation"),
            KeyboardShortcut("focus_log", "Ctrl+3", "Focus log area", "navigation"),
            
            # Tools
            KeyboardShortcut("preferences", "Ctrl+,", "Open preferences", "tools"),
            KeyboardShortcut("test_outlook", "Ctrl+Shift+O", "Test Outlook connection", "tools"),
            KeyboardShortcut("message_analytics", "Ctrl+L", "Open message analytics", "tools"),
        ]
        
        self.preferences.keyboard_shortcuts = default_shortcuts
        self.save_preferences()
    
    # Getter methods
    def get_toolbar_config(self) -> ToolbarConfig:
        """Get toolbar configuration."""
        return self.preferences.toolbar
    
    def get_window_config(self) -> WindowConfig:
        """Get window configuration."""
        return self.preferences.window
    
    def get_interface_config(self) -> InterfaceConfig:
        """Get interface configuration."""
        return self.preferences.interface
    
    def get_accessibility_config(self) -> AccessibilityConfig:
        """Get accessibility configuration."""
        return self.preferences.accessibility
    
    def get_keyboard_shortcuts(self) -> List[KeyboardShortcut]:
        """Get keyboard shortcuts."""
        return self.preferences.keyboard_shortcuts
    
    def get_shortcut_for_action(self, action: str) -> Optional[KeyboardShortcut]:
        """Get keyboard shortcut for specific action."""
        for shortcut in self.preferences.keyboard_shortcuts:
            if shortcut.action == action:
                return shortcut
        return None
    
    # Setter methods
    def set_theme(self, theme: str):
        """Set application theme."""
        if theme != self.preferences.interface.theme:
            self.preferences.interface.theme = theme
            self.save_preferences()
            self.theme_changed.emit(theme)
            self.preferences_changed.emit("interface")
    
    def set_window_layout(self, layout: WindowLayout):
        """Set window layout."""
        if layout != self.preferences.window.layout:
            self.preferences.window.layout = layout
            self.save_preferences()
            self.layout_changed.emit(layout.value)
            self.preferences_changed.emit("window")
    
    def set_toolbar_position(self, position: ToolbarPosition):
        """Set toolbar position."""
        if position != self.preferences.toolbar.position:
            self.preferences.toolbar.position = position
            self.save_preferences()
            self.preferences_changed.emit("toolbar")
    
    def set_toolbar_buttons(self, buttons: List[str]):
        """Set toolbar buttons."""
        self.preferences.toolbar.buttons = buttons
        self.save_preferences()
        self.preferences_changed.emit("toolbar")
    
    def set_window_geometry(self, width: int, height: int, x: int = -1, y: int = -1, maximized: bool = False):
        """Set window geometry."""
        self.preferences.window.width = width
        self.preferences.window.height = height
        self.preferences.window.x = x
        self.preferences.window.y = y
        self.preferences.window.maximized = maximized
        self.save_preferences()
    
    def set_splitter_sizes(self, sizes: List[int]):
        """Set splitter sizes."""
        self.preferences.window.splitter_sizes = sizes
        self.save_preferences()
    
    def set_font_settings(self, family: str = "", size: int = 9):
        """Set font settings."""
        changed = False
        if family and family != self.preferences.interface.font_family:
            self.preferences.interface.font_family = family
            changed = True
        if size != self.preferences.interface.font_size:
            self.preferences.interface.font_size = size
            changed = True
        
        if changed:
            self.save_preferences()
            self.preferences_changed.emit("interface")
    
    def set_accessibility_option(self, option: str, value: bool):
        """Set accessibility option."""
        if hasattr(self.preferences.accessibility, option):
            setattr(self.preferences.accessibility, option, value)
            self.save_preferences()
            self.preferences_changed.emit("accessibility")
    
    def update_keyboard_shortcut(self, action: str, sequence: str):
        """Update keyboard shortcut."""
        for shortcut in self.preferences.keyboard_shortcuts:
            if shortcut.action == action:
                shortcut.sequence = sequence
                break
        else:
            # Add new shortcut if not found
            self.preferences.keyboard_shortcuts.append(
                KeyboardShortcut(action, sequence, f"Custom shortcut for {action}")
            )
        
        self.save_preferences()
        self.shortcuts_changed.emit()
        self.preferences_changed.emit("shortcuts")
    
    def reset_shortcuts_to_default(self):
        """Reset keyboard shortcuts to default."""
        self.preferences.keyboard_shortcuts.clear()
        self._initialize_default_shortcuts()
        self.shortcuts_changed.emit()
        self.preferences_changed.emit("shortcuts")
    
    def set_custom_setting(self, key: str, value: Any):
        """Set custom setting."""
        self.preferences.custom_settings[key] = value
        self.save_preferences()
        self.preferences_changed.emit("custom")
    
    def get_custom_setting(self, key: str, default: Any = None) -> Any:
        """Get custom setting."""
        return self.preferences.custom_settings.get(key, default)
    
    # Utility methods
    def export_preferences(self, file_path: Path):
        """Export preferences to file."""
        try:
            data = self._preferences_to_dict(self.preferences)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Exported preferences to {file_path}")
        except Exception as e:
            logger.error(f"Failed to export preferences: {e}")
            raise
    
    def import_preferences(self, file_path: Path):
        """Import preferences from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.preferences = self._dict_to_preferences(data)
            self.save_preferences()
            
            # Emit signals for all categories
            self.preferences_changed.emit("all")
            self.theme_changed.emit(self.preferences.interface.theme)
            self.layout_changed.emit(self.preferences.window.layout.value)
            self.shortcuts_changed.emit()
            
            logger.info(f"Imported preferences from {file_path}")
        except Exception as e:
            logger.error(f"Failed to import preferences: {e}")
            raise
    
    def reset_to_defaults(self):
        """Reset all preferences to defaults."""
        self.preferences = UserPreferences()
        self._initialize_default_shortcuts()
        self.save_preferences()
        
        # Emit signals for all categories
        self.preferences_changed.emit("all")
        self.theme_changed.emit(self.preferences.interface.theme)
        self.layout_changed.emit(self.preferences.window.layout.value)
        self.shortcuts_changed.emit()
        
        logger.info("Reset preferences to defaults")
    
    def get_available_themes(self) -> List[str]:
        """Get available theme options."""
        return ["system", "light", "dark"]
    
    def get_available_layouts(self) -> List[WindowLayout]:
        """Get available window layouts."""
        return list(WindowLayout)
    
    def get_shortcut_categories(self) -> List[str]:
        """Get keyboard shortcut categories."""
        categories = set()
        for shortcut in self.preferences.keyboard_shortcuts:
            categories.add(shortcut.category)
        return sorted(list(categories))