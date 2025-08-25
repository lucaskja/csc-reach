"""
Toolbar and menu customization manager for CSC-Reach application.
Provides customizable toolbar arrangements and menu configurations.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from PySide6.QtWidgets import (
    QToolBar, QAction, QWidget, QMainWindow, QMenu, QMenuBar,
    QPushButton, QLabel, QComboBox, QSeparator, QFrame
)
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QIcon, QKeySequence

from ..core.user_preferences import ToolbarPosition
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ToolbarItemType(Enum):
    """Toolbar item types."""
    ACTION = "action"
    SEPARATOR = "separator"
    WIDGET = "widget"
    SPACER = "spacer"


@dataclass
class ToolbarItem:
    """Represents an item in a toolbar."""
    id: str
    item_type: ToolbarItemType
    text: str = ""
    icon: str = ""
    tooltip: str = ""
    shortcut: str = ""
    callback: Optional[callable] = None
    widget: Optional[QWidget] = None
    visible: bool = True
    enabled: bool = True
    checkable: bool = False
    checked: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolbarConfiguration:
    """Toolbar configuration."""
    id: str
    name: str
    position: ToolbarPosition = ToolbarPosition.TOP
    visible: bool = True
    movable: bool = True
    icon_size: int = 24
    show_text: bool = True
    items: List[str] = field(default_factory=list)  # List of item IDs
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolbarManager(QObject):
    """Manages customizable toolbars and menus."""
    
    # Signals
    toolbar_changed = Signal(str)  # toolbar_id
    item_activated = Signal(str)   # item_id
    configuration_changed = Signal()
    
    def __init__(self, main_window: QMainWindow, preferences_manager=None):
        super().__init__()
        self.main_window = main_window
        self.preferences_manager = preferences_manager
        
        # Available toolbar items
        self.available_items: Dict[str, ToolbarItem] = {}
        
        # Toolbar configurations
        self.toolbar_configs: Dict[str, ToolbarConfiguration] = {}
        
        # Active toolbars
        self.active_toolbars: Dict[str, QToolBar] = {}
        
        # Initialize default items and toolbars
        self.initialize_default_items()
        self.initialize_default_toolbars()
    
    def initialize_default_items(self):
        """Initialize default toolbar items."""
        # File operations
        self.register_toolbar_item(ToolbarItem(
            id="import_csv",
            item_type=ToolbarItemType.ACTION,
            text="Import CSV",
            icon="document-open",
            tooltip="Import recipient data from CSV file",
            shortcut="Ctrl+O"
        ))
        
        self.register_toolbar_item(ToolbarItem(
            id="export_templates",
            item_type=ToolbarItemType.ACTION,
            text="Export Templates",
            icon="document-export",
            tooltip="Export all templates to file",
            shortcut="Ctrl+E"
        ))
        
        # Template operations
        self.register_toolbar_item(ToolbarItem(
            id="new_template",
            item_type=ToolbarItemType.ACTION,
            text="New Template",
            icon="document-new",
            tooltip="Create a new message template",
            shortcut="Ctrl+N"
        ))
        
        self.register_toolbar_item(ToolbarItem(
            id="save_template",
            item_type=ToolbarItemType.ACTION,
            text="Save Template",
            icon="document-save",
            tooltip="Save current template",
            shortcut="Ctrl+S"
        ))
        
        self.register_toolbar_item(ToolbarItem(
            id="template_library",
            item_type=ToolbarItemType.ACTION,
            text="Template Library",
            icon="folder-documents",
            tooltip="Open template library",
            shortcut="Ctrl+T"
        ))
        
        # Messaging operations
        self.register_toolbar_item(ToolbarItem(
            id="send_messages",
            item_type=ToolbarItemType.ACTION,
            text="Send Messages",
            icon="mail-send",
            tooltip="Send messages to selected recipients",
            shortcut="Ctrl+Return"
        ))
        
        self.register_toolbar_item(ToolbarItem(
            id="create_draft",
            item_type=ToolbarItemType.ACTION,
            text="Create Draft",
            icon="mail-draft",
            tooltip="Create draft email for testing",
            shortcut="Ctrl+D"
        ))
        
        self.register_toolbar_item(ToolbarItem(
            id="preview_message",
            item_type=ToolbarItemType.ACTION,
            text="Preview",
            icon="eye",
            tooltip="Preview message with sample data",
            shortcut="Ctrl+P"
        ))
        
        # Channel selection widget
        self.register_toolbar_item(ToolbarItem(
            id="channel_selector",
            item_type=ToolbarItemType.WIDGET,
            text="Channel:",
            tooltip="Select communication channel"
        ))
        
        # Language selection widget
        self.register_toolbar_item(ToolbarItem(
            id="language_selector",
            item_type=ToolbarItemType.WIDGET,
            text="Language:",
            tooltip="Select application language"
        ))
        
        # Tools
        self.register_toolbar_item(ToolbarItem(
            id="preferences",
            item_type=ToolbarItemType.ACTION,
            text="Preferences",
            icon="preferences-system",
            tooltip="Open application preferences",
            shortcut="Ctrl+,"
        ))
        
        self.register_toolbar_item(ToolbarItem(
            id="test_outlook",
            item_type=ToolbarItemType.ACTION,
            text="Test Outlook",
            icon="mail-test",
            tooltip="Test Outlook connection",
            shortcut="Ctrl+Shift+O"
        ))
        
        self.register_toolbar_item(ToolbarItem(
            id="message_analytics",
            item_type=ToolbarItemType.ACTION,
            text="Analytics",
            icon="chart-line",
            tooltip="View message analytics and logs",
            shortcut="Ctrl+L"
        ))
        
        # Separators and spacers
        self.register_toolbar_item(ToolbarItem(
            id="separator_1",
            item_type=ToolbarItemType.SEPARATOR
        ))
        
        self.register_toolbar_item(ToolbarItem(
            id="separator_2",
            item_type=ToolbarItemType.SEPARATOR
        ))
        
        self.register_toolbar_item(ToolbarItem(
            id="spacer_1",
            item_type=ToolbarItemType.SPACER
        ))
        
        logger.info(f"Initialized {len(self.available_items)} default toolbar items")
    
    def initialize_default_toolbars(self):
        """Initialize default toolbar configurations."""
        # Main toolbar
        main_toolbar = ToolbarConfiguration(
            id="main_toolbar",
            name="Main Toolbar",
            position=ToolbarPosition.TOP,
            visible=True,
            items=[
                "import_csv",
                "separator_1",
                "new_template",
                "save_template",
                "template_library",
                "separator_2",
                "send_messages",
                "create_draft",
                "preview_message",
                "spacer_1",
                "channel_selector",
                "language_selector"
            ]
        )
        
        # Tools toolbar
        tools_toolbar = ToolbarConfiguration(
            id="tools_toolbar",
            name="Tools Toolbar",
            position=ToolbarPosition.TOP,
            visible=False,  # Hidden by default
            items=[
                "preferences",
                "test_outlook",
                "message_analytics",
                "export_templates"
            ]
        )
        
        self.toolbar_configs["main_toolbar"] = main_toolbar
        self.toolbar_configs["tools_toolbar"] = tools_toolbar
        
        logger.info("Initialized default toolbar configurations")
    
    def register_toolbar_item(self, item: ToolbarItem):
        """Register a toolbar item."""
        self.available_items[item.id] = item
        logger.debug(f"Registered toolbar item: {item.id}")
    
    def unregister_toolbar_item(self, item_id: str):
        """Unregister a toolbar item."""
        if item_id in self.available_items:
            del self.available_items[item_id]
            logger.debug(f"Unregistered toolbar item: {item_id}")
    
    def create_toolbar(self, config: ToolbarConfiguration) -> QToolBar:
        """Create a toolbar from configuration."""
        toolbar = QToolBar(config.name, self.main_window)
        toolbar.setObjectName(config.id)
        
        # Set toolbar properties
        toolbar.setVisible(config.visible)
        toolbar.setMovable(config.movable)
        toolbar.setIconSize(toolbar.iconSize().scaled(config.icon_size, config.icon_size, Qt.KeepAspectRatio))
        
        # Set toolbar style
        if config.show_text:
            toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        else:
            toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        
        # Add items to toolbar
        for item_id in config.items:
            self.add_item_to_toolbar(toolbar, item_id)
        
        # Add toolbar to main window
        if config.position == ToolbarPosition.TOP:
            self.main_window.addToolBar(Qt.TopToolBarArea, toolbar)
        elif config.position == ToolbarPosition.BOTTOM:
            self.main_window.addToolBar(Qt.BottomToolBarArea, toolbar)
        elif config.position == ToolbarPosition.LEFT:
            self.main_window.addToolBar(Qt.LeftToolBarArea, toolbar)
        elif config.position == ToolbarPosition.RIGHT:
            self.main_window.addToolBar(Qt.RightToolBarArea, toolbar)
        
        self.active_toolbars[config.id] = toolbar
        logger.info(f"Created toolbar: {config.name}")
        
        return toolbar
    
    def add_item_to_toolbar(self, toolbar: QToolBar, item_id: str):
        """Add an item to a toolbar."""
        if item_id not in self.available_items:
            logger.warning(f"Toolbar item not found: {item_id}")
            return
        
        item = self.available_items[item_id]
        
        if item.item_type == ToolbarItemType.ACTION:
            action = QAction(item.text, toolbar)
            
            # Set icon if available
            if item.icon:
                # In a real implementation, you'd load the actual icon
                # action.setIcon(QIcon(f":/icons/{item.icon}.png"))
                pass
            
            action.setToolTip(item.tooltip)
            action.setStatusTip(item.tooltip)
            
            if item.shortcut:
                action.setShortcut(QKeySequence(item.shortcut))
            
            action.setCheckable(item.checkable)
            action.setChecked(item.checked)
            action.setEnabled(item.enabled)
            action.setVisible(item.visible)
            
            # Connect callback if available
            if item.callback:
                action.triggered.connect(item.callback)
            else:
                # Connect to default handler
                action.triggered.connect(lambda: self.item_activated.emit(item_id))
            
            toolbar.addAction(action)
            
        elif item.item_type == ToolbarItemType.SEPARATOR:
            toolbar.addSeparator()
            
        elif item.item_type == ToolbarItemType.SPACER:
            spacer = QWidget()
            spacer.setSizePolicy(spacer.sizePolicy().Expanding, spacer.sizePolicy().Preferred)
            toolbar.addWidget(spacer)
            
        elif item.item_type == ToolbarItemType.WIDGET:
            if item.widget:
                toolbar.addWidget(item.widget)
            else:
                # Create default widget based on item ID
                widget = self.create_default_widget(item_id)
                if widget:
                    toolbar.addWidget(widget)
    
    def create_default_widget(self, item_id: str) -> Optional[QWidget]:
        """Create default widget for toolbar items."""
        if item_id == "channel_selector":
            # This would be connected to the actual channel combo box
            label = QLabel("Channel:")
            return label
        elif item_id == "language_selector":
            # This would be connected to the actual language combo box
            label = QLabel("Language:")
            return label
        
        return None
    
    def update_toolbar_configuration(self, toolbar_id: str, config: ToolbarConfiguration):
        """Update toolbar configuration."""
        self.toolbar_configs[toolbar_id] = config
        
        # Recreate toolbar if it exists
        if toolbar_id in self.active_toolbars:
            old_toolbar = self.active_toolbars[toolbar_id]
            self.main_window.removeToolBar(old_toolbar)
            old_toolbar.deleteLater()
            
            new_toolbar = self.create_toolbar(config)
            self.active_toolbars[toolbar_id] = new_toolbar
        
        self.toolbar_changed.emit(toolbar_id)
        self.configuration_changed.emit()
        logger.info(f"Updated toolbar configuration: {toolbar_id}")
    
    def show_toolbar(self, toolbar_id: str):
        """Show a toolbar."""
        if toolbar_id in self.active_toolbars:
            self.active_toolbars[toolbar_id].setVisible(True)
            self.toolbar_configs[toolbar_id].visible = True
    
    def hide_toolbar(self, toolbar_id: str):
        """Hide a toolbar."""
        if toolbar_id in self.active_toolbars:
            self.active_toolbars[toolbar_id].setVisible(False)
            self.toolbar_configs[toolbar_id].visible = False
    
    def move_toolbar(self, toolbar_id: str, position: ToolbarPosition):
        """Move toolbar to a different position."""
        if toolbar_id not in self.active_toolbars:
            return
        
        toolbar = self.active_toolbars[toolbar_id]
        config = self.toolbar_configs[toolbar_id]
        
        # Remove from current position
        self.main_window.removeToolBar(toolbar)
        
        # Add to new position
        if position == ToolbarPosition.TOP:
            self.main_window.addToolBar(Qt.TopToolBarArea, toolbar)
        elif position == ToolbarPosition.BOTTOM:
            self.main_window.addToolBar(Qt.BottomToolBarArea, toolbar)
        elif position == ToolbarPosition.LEFT:
            self.main_window.addToolBar(Qt.LeftToolBarArea, toolbar)
        elif position == ToolbarPosition.RIGHT:
            self.main_window.addToolBar(Qt.RightToolBarArea, toolbar)
        
        # Update configuration
        config.position = position
        self.toolbar_changed.emit(toolbar_id)
    
    def customize_toolbar_items(self, toolbar_id: str, item_ids: List[str]):
        """Customize toolbar items."""
        if toolbar_id not in self.toolbar_configs:
            return
        
        config = self.toolbar_configs[toolbar_id]
        config.items = item_ids.copy()
        
        # Recreate toolbar
        self.update_toolbar_configuration(toolbar_id, config)
    
    def get_available_items(self) -> Dict[str, ToolbarItem]:
        """Get all available toolbar items."""
        return self.available_items.copy()
    
    def get_toolbar_configurations(self) -> Dict[str, ToolbarConfiguration]:
        """Get all toolbar configurations."""
        return self.toolbar_configs.copy()
    
    def export_toolbar_configuration(self) -> Dict[str, Any]:
        """Export toolbar configuration for saving."""
        config_data = {}
        
        for toolbar_id, config in self.toolbar_configs.items():
            config_data[toolbar_id] = {
                'name': config.name,
                'position': config.position.value,
                'visible': config.visible,
                'movable': config.movable,
                'icon_size': config.icon_size,
                'show_text': config.show_text,
                'items': config.items.copy(),
                'metadata': config.metadata.copy()
            }
        
        return config_data
    
    def import_toolbar_configuration(self, config_data: Dict[str, Any]):
        """Import toolbar configuration from saved data."""
        for toolbar_id, data in config_data.items():
            config = ToolbarConfiguration(
                id=toolbar_id,
                name=data.get('name', toolbar_id),
                position=ToolbarPosition(data.get('position', 'top')),
                visible=data.get('visible', True),
                movable=data.get('movable', True),
                icon_size=data.get('icon_size', 24),
                show_text=data.get('show_text', True),
                items=data.get('items', []),
                metadata=data.get('metadata', {})
            )
            
            self.toolbar_configs[toolbar_id] = config
        
        # Recreate all toolbars
        self.recreate_all_toolbars()
        self.configuration_changed.emit()
        logger.info("Imported toolbar configuration")
    
    def recreate_all_toolbars(self):
        """Recreate all toolbars from current configuration."""
        # Remove existing toolbars
        for toolbar in self.active_toolbars.values():
            self.main_window.removeToolBar(toolbar)
            toolbar.deleteLater()
        
        self.active_toolbars.clear()
        
        # Create toolbars from configuration
        for config in self.toolbar_configs.values():
            self.create_toolbar(config)
    
    def reset_to_defaults(self):
        """Reset toolbars to default configuration."""
        # Clear current configuration
        for toolbar in self.active_toolbars.values():
            self.main_window.removeToolBar(toolbar)
            toolbar.deleteLater()
        
        self.active_toolbars.clear()
        self.toolbar_configs.clear()
        
        # Reinitialize defaults
        self.initialize_default_toolbars()
        self.recreate_all_toolbars()
        
        self.configuration_changed.emit()
        logger.info("Reset toolbars to default configuration")
    
    def save_configuration(self):
        """Save toolbar configuration to preferences."""
        if self.preferences_manager:
            config_data = self.export_toolbar_configuration()
            self.preferences_manager.set_custom_setting("toolbar_configuration", config_data)
            logger.info("Saved toolbar configuration to preferences")
    
    def load_configuration(self):
        """Load toolbar configuration from preferences."""
        if self.preferences_manager:
            config_data = self.preferences_manager.get_custom_setting("toolbar_configuration")
            if config_data:
                self.import_toolbar_configuration(config_data)
                logger.info("Loaded toolbar configuration from preferences")
    
    def connect_main_window_actions(self, main_window):
        """Connect toolbar items to main window actions."""
        # This method would connect toolbar items to actual main window methods
        # For example:
        if hasattr(main_window, 'import_csv'):
            self.available_items["import_csv"].callback = main_window.import_csv
        
        if hasattr(main_window, 'send_messages'):
            self.available_items["send_messages"].callback = main_window.send_messages
        
        if hasattr(main_window, 'create_draft'):
            self.available_items["create_draft"].callback = main_window.create_draft
        
        if hasattr(main_window, 'preview_message'):
            self.available_items["preview_message"].callback = main_window.preview_message
        
        if hasattr(main_window, 'open_template_library'):
            self.available_items["template_library"].callback = main_window.open_template_library
        
        if hasattr(main_window, 'show_preferences'):
            self.available_items["preferences"].callback = main_window.show_preferences
        
        if hasattr(main_window, 'test_outlook_connection'):
            self.available_items["test_outlook"].callback = main_window.test_outlook_connection
        
        if hasattr(main_window, 'show_message_analytics'):
            self.available_items["message_analytics"].callback = main_window.show_message_analytics
        
        logger.info("Connected toolbar items to main window actions")