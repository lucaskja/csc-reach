"""
Toolbar customization dialog for CSC-Reach application.
Allows users to customize toolbar layout and items.
"""

from typing import Dict, List, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, 
    QListWidgetItem, QPushButton, QGroupBox, QComboBox,
    QCheckBox, QSpinBox, QSplitter, QMessageBox, QFrame,
    QGridLayout, QScrollArea, QWidget
)
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QDrag, QPainter, QPixmap

from ..core.toolbar_manager import ToolbarManager, ToolbarConfiguration, ToolbarItem, ToolbarItemType
from ..core.user_preferences import ToolbarPosition
from ..core.i18n_manager import get_i18n_manager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DraggableListWidget(QListWidget):
    """List widget that supports drag and drop for toolbar customization."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QListWidget.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setAcceptDrops(True)
    
    def startDrag(self, supportedActions):
        """Start drag operation."""
        item = self.currentItem()
        if item:
            drag = QDrag(self)
            mimeData = QMimeData()
            mimeData.setText(item.data(Qt.UserRole))  # Store item ID
            drag.setMimeData(mimeData)
            
            # Create drag pixmap
            pixmap = QPixmap(item.sizeHint())
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.drawText(pixmap.rect(), Qt.AlignCenter, item.text())
            painter.end()
            
            drag.setPixmap(pixmap)
            drag.exec_(supportedActions)
    
    def dropEvent(self, event):
        """Handle drop event."""
        if event.source() == self:
            # Internal move
            super().dropEvent(event)
        else:
            # External drop
            item_id = event.mimeData().text()
            if item_id:
                # Create new item
                item = QListWidgetItem(item_id)
                item.setData(Qt.UserRole, item_id)
                
                # Insert at drop position
                drop_row = self.indexAt(event.pos()).row()
                if drop_row == -1:
                    self.addItem(item)
                else:
                    self.insertItem(drop_row, item)
                
                event.accept()


class ToolbarCustomizationDialog(QDialog):
    """Dialog for customizing toolbars."""
    
    # Signals
    configuration_changed = Signal()
    
    def __init__(self, toolbar_manager: ToolbarManager, parent=None):
        super().__init__(parent)
        self.toolbar_manager = toolbar_manager
        self.i18n = get_i18n_manager()
        
        # Current configuration (working copy)
        self.current_configs = {}
        self.load_current_configurations()
        
        self.setup_ui()
        self.load_toolbar_list()
        self.connect_signals()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle(self.i18n.tr("customize_toolbars"))
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Create main splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Toolbar selection and properties
        self.create_left_panel(splitter)
        
        # Right panel - Available items and current toolbar items
        self.create_right_panel(splitter)
        
        # Button layout
        self.create_button_layout(layout)
        
        splitter.setSizes([300, 500])
    
    def create_left_panel(self, parent):
        """Create the left panel with toolbar selection and properties."""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Toolbar selection
        toolbar_group = QGroupBox(self.i18n.tr("toolbars"))
        toolbar_layout = QVBoxLayout(toolbar_group)
        
        self.toolbar_list = QListWidget()
        self.toolbar_list.currentItemChanged.connect(self.on_toolbar_selected)
        toolbar_layout.addWidget(self.toolbar_list)
        
        # Toolbar management buttons
        toolbar_buttons = QHBoxLayout()
        
        self.new_toolbar_btn = QPushButton(self.i18n.tr("new_toolbar"))
        self.new_toolbar_btn.clicked.connect(self.create_new_toolbar)
        toolbar_buttons.addWidget(self.new_toolbar_btn)
        
        self.delete_toolbar_btn = QPushButton(self.i18n.tr("delete_toolbar"))
        self.delete_toolbar_btn.clicked.connect(self.delete_toolbar)
        toolbar_buttons.addWidget(self.delete_toolbar_btn)
        
        toolbar_layout.addLayout(toolbar_buttons)
        left_layout.addWidget(toolbar_group)
        
        # Toolbar properties
        properties_group = QGroupBox(self.i18n.tr("toolbar_properties"))
        properties_layout = QGridLayout(properties_group)
        
        # Name
        properties_layout.addWidget(QLabel(self.i18n.tr("name") + ":"), 0, 0)
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self.on_property_changed)
        properties_layout.addWidget(self.name_edit, 0, 1)
        
        # Position
        properties_layout.addWidget(QLabel(self.i18n.tr("position") + ":"), 1, 0)
        self.position_combo = QComboBox()
        position_options = {
            ToolbarPosition.TOP: self.i18n.tr("top"),
            ToolbarPosition.BOTTOM: self.i18n.tr("bottom"),
            ToolbarPosition.LEFT: self.i18n.tr("left"),
            ToolbarPosition.RIGHT: self.i18n.tr("right")
        }
        for pos_enum, text in position_options.items():
            self.position_combo.addItem(text, pos_enum)
        self.position_combo.currentTextChanged.connect(self.on_property_changed)
        properties_layout.addWidget(self.position_combo, 1, 1)
        
        # Visible
        self.visible_check = QCheckBox(self.i18n.tr("visible"))
        self.visible_check.toggled.connect(self.on_property_changed)
        properties_layout.addWidget(self.visible_check, 2, 0, 1, 2)
        
        # Movable
        self.movable_check = QCheckBox(self.i18n.tr("movable"))
        self.movable_check.toggled.connect(self.on_property_changed)
        properties_layout.addWidget(self.movable_check, 3, 0, 1, 2)
        
        # Show text
        self.show_text_check = QCheckBox(self.i18n.tr("show_text"))
        self.show_text_check.toggled.connect(self.on_property_changed)
        properties_layout.addWidget(self.show_text_check, 4, 0, 1, 2)
        
        # Icon size
        properties_layout.addWidget(QLabel(self.i18n.tr("icon_size") + ":"), 5, 0)
        self.icon_size_spin = QSpinBox()
        self.icon_size_spin.setRange(16, 64)
        self.icon_size_spin.setSuffix(" px")
        self.icon_size_spin.valueChanged.connect(self.on_property_changed)
        properties_layout.addWidget(self.icon_size_spin, 5, 1)
        
        left_layout.addWidget(properties_group)
        left_layout.addStretch()
        
        parent.addWidget(left_widget)
    
    def create_right_panel(self, parent):
        """Create the right panel with available and current items."""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Instructions
        instructions = QLabel(self.i18n.tr("toolbar_customization_instructions"))
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; font-style: italic; margin-bottom: 10px;")
        right_layout.addWidget(instructions)
        
        # Create horizontal splitter for items
        items_splitter = QSplitter(Qt.Horizontal)
        right_layout.addWidget(items_splitter)
        
        # Available items
        available_group = QGroupBox(self.i18n.tr("available_items"))
        available_layout = QVBoxLayout(available_group)
        
        self.available_items_list = DraggableListWidget()
        self.available_items_list.setDragDropMode(QListWidget.DragOnly)
        available_layout.addWidget(self.available_items_list)
        
        items_splitter.addWidget(available_group)
        
        # Current toolbar items
        current_group = QGroupBox(self.i18n.tr("current_toolbar_items"))
        current_layout = QVBoxLayout(current_group)
        
        self.current_items_list = DraggableListWidget()
        self.current_items_list.itemChanged.connect(self.on_current_items_changed)
        current_layout.addWidget(self.current_items_list)
        
        # Item management buttons
        item_buttons = QHBoxLayout()
        
        self.move_up_btn = QPushButton("↑")
        self.move_up_btn.setToolTip(self.i18n.tr("move_up"))
        self.move_up_btn.clicked.connect(self.move_item_up)
        item_buttons.addWidget(self.move_up_btn)
        
        self.move_down_btn = QPushButton("↓")
        self.move_down_btn.setToolTip(self.i18n.tr("move_down"))
        self.move_down_btn.clicked.connect(self.move_item_down)
        item_buttons.addWidget(self.move_down_btn)
        
        item_buttons.addStretch()
        
        self.remove_item_btn = QPushButton(self.i18n.tr("remove"))
        self.remove_item_btn.clicked.connect(self.remove_current_item)
        item_buttons.addWidget(self.remove_item_btn)
        
        current_layout.addLayout(item_buttons)
        
        items_splitter.addWidget(current_group)
        items_splitter.setSizes([300, 300])
        
        parent.addWidget(right_widget)
    
    def create_button_layout(self, parent_layout):
        """Create the button layout."""
        button_layout = QHBoxLayout()
        
        # Reset button
        self.reset_btn = QPushButton(self.i18n.tr("reset_to_defaults"))
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_btn)
        
        button_layout.addStretch()
        
        # Preview button
        self.preview_btn = QPushButton(self.i18n.tr("preview"))
        self.preview_btn.clicked.connect(self.preview_changes)
        button_layout.addWidget(self.preview_btn)
        
        # Standard buttons
        self.apply_btn = QPushButton(self.i18n.tr("apply"))
        self.apply_btn.clicked.connect(self.apply_changes)
        button_layout.addWidget(self.apply_btn)
        
        self.ok_btn = QPushButton(self.i18n.tr("ok"))
        self.ok_btn.clicked.connect(self.accept_changes)
        button_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton(self.i18n.tr("cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        parent_layout.addLayout(button_layout)
    
    def connect_signals(self):
        """Connect signals."""
        pass
    
    def load_current_configurations(self):
        """Load current toolbar configurations."""
        self.current_configs = self.toolbar_manager.get_toolbar_configurations()
    
    def load_toolbar_list(self):
        """Load the list of toolbars."""
        self.toolbar_list.clear()
        
        for toolbar_id, config in self.current_configs.items():
            item = QListWidgetItem(config.name)
            item.setData(Qt.UserRole, toolbar_id)
            self.toolbar_list.addItem(item)
        
        # Select first toolbar if available
        if self.toolbar_list.count() > 0:
            self.toolbar_list.setCurrentRow(0)
    
    def load_available_items(self):
        """Load available toolbar items."""
        self.available_items_list.clear()
        
        available_items = self.toolbar_manager.get_available_items()
        
        for item_id, item in available_items.items():
            display_text = item.text or item_id
            if item.item_type == ToolbarItemType.SEPARATOR:
                display_text = "--- Separator ---"
            elif item.item_type == ToolbarItemType.SPACER:
                display_text = "<<< Spacer >>>"
            
            list_item = QListWidgetItem(display_text)
            list_item.setData(Qt.UserRole, item_id)
            list_item.setToolTip(item.tooltip)
            self.available_items_list.addItem(list_item)
    
    def load_current_toolbar_items(self, toolbar_id: str):
        """Load current toolbar items."""
        self.current_items_list.clear()
        
        if toolbar_id not in self.current_configs:
            return
        
        config = self.current_configs[toolbar_id]
        available_items = self.toolbar_manager.get_available_items()
        
        for item_id in config.items:
            if item_id in available_items:
                item = available_items[item_id]
                display_text = item.text or item_id
                
                if item.item_type == ToolbarItemType.SEPARATOR:
                    display_text = "--- Separator ---"
                elif item.item_type == ToolbarItemType.SPACER:
                    display_text = "<<< Spacer >>>"
                
                list_item = QListWidgetItem(display_text)
                list_item.setData(Qt.UserRole, item_id)
                list_item.setToolTip(item.tooltip)
                self.current_items_list.addItem(list_item)
    
    def on_toolbar_selected(self, current, previous):
        """Handle toolbar selection change."""
        if not current:
            return
        
        toolbar_id = current.data(Qt.UserRole)
        if toolbar_id not in self.current_configs:
            return
        
        config = self.current_configs[toolbar_id]
        
        # Update properties
        self.name_edit.setText(config.name)
        
        position_index = self.position_combo.findData(config.position)
        if position_index >= 0:
            self.position_combo.setCurrentIndex(position_index)
        
        self.visible_check.setChecked(config.visible)
        self.movable_check.setChecked(config.movable)
        self.show_text_check.setChecked(config.show_text)
        self.icon_size_spin.setValue(config.icon_size)
        
        # Load available items (only once)
        if self.available_items_list.count() == 0:
            self.load_available_items()
        
        # Load current toolbar items
        self.load_current_toolbar_items(toolbar_id)
    
    def on_property_changed(self):
        """Handle property change."""
        current_item = self.toolbar_list.currentItem()
        if not current_item:
            return
        
        toolbar_id = current_item.data(Qt.UserRole)
        if toolbar_id not in self.current_configs:
            return
        
        config = self.current_configs[toolbar_id]
        
        # Update configuration
        config.name = self.name_edit.text()
        config.position = self.position_combo.currentData()
        config.visible = self.visible_check.isChecked()
        config.movable = self.movable_check.isChecked()
        config.show_text = self.show_text_check.isChecked()
        config.icon_size = self.icon_size_spin.value()
        
        # Update list item text
        current_item.setText(config.name)
    
    def on_current_items_changed(self):
        """Handle changes to current toolbar items."""
        current_toolbar = self.toolbar_list.currentItem()
        if not current_toolbar:
            return
        
        toolbar_id = current_toolbar.data(Qt.UserRole)
        if toolbar_id not in self.current_configs:
            return
        
        # Update configuration with current items
        config = self.current_configs[toolbar_id]
        config.items = []
        
        for i in range(self.current_items_list.count()):
            item = self.current_items_list.item(i)
            item_id = item.data(Qt.UserRole)
            config.items.append(item_id)
    
    def move_item_up(self):
        """Move selected item up."""
        current_row = self.current_items_list.currentRow()
        if current_row > 0:
            item = self.current_items_list.takeItem(current_row)
            self.current_items_list.insertItem(current_row - 1, item)
            self.current_items_list.setCurrentRow(current_row - 1)
            self.on_current_items_changed()
    
    def move_item_down(self):
        """Move selected item down."""
        current_row = self.current_items_list.currentRow()
        if current_row < self.current_items_list.count() - 1:
            item = self.current_items_list.takeItem(current_row)
            self.current_items_list.insertItem(current_row + 1, item)
            self.current_items_list.setCurrentRow(current_row + 1)
            self.on_current_items_changed()
    
    def remove_current_item(self):
        """Remove selected item from current toolbar."""
        current_row = self.current_items_list.currentRow()
        if current_row >= 0:
            self.current_items_list.takeItem(current_row)
            self.on_current_items_changed()
    
    def create_new_toolbar(self):
        """Create a new toolbar."""
        from PySide6.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(
            self, 
            self.i18n.tr("new_toolbar"),
            self.i18n.tr("toolbar_name") + ":"
        )
        
        if ok and name:
            toolbar_id = name.lower().replace(" ", "_")
            
            # Check if ID already exists
            counter = 1
            original_id = toolbar_id
            while toolbar_id in self.current_configs:
                toolbar_id = f"{original_id}_{counter}"
                counter += 1
            
            # Create new configuration
            config = ToolbarConfiguration(
                id=toolbar_id,
                name=name,
                position=ToolbarPosition.TOP,
                visible=True,
                items=[]
            )
            
            self.current_configs[toolbar_id] = config
            
            # Add to list
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, toolbar_id)
            self.toolbar_list.addItem(item)
            self.toolbar_list.setCurrentItem(item)
    
    def delete_toolbar(self):
        """Delete selected toolbar."""
        current_item = self.toolbar_list.currentItem()
        if not current_item:
            return
        
        toolbar_id = current_item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            self.i18n.tr("delete_toolbar"),
            self.i18n.tr("delete_toolbar_confirm", name=current_item.text()),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Remove from configuration
            if toolbar_id in self.current_configs:
                del self.current_configs[toolbar_id]
            
            # Remove from list
            row = self.toolbar_list.row(current_item)
            self.toolbar_list.takeItem(row)
    
    def preview_changes(self):
        """Preview toolbar changes."""
        # Apply changes temporarily
        self.apply_changes()
        
        QMessageBox.information(
            self,
            self.i18n.tr("preview"),
            self.i18n.tr("toolbar_changes_applied_preview")
        )
    
    def apply_changes(self):
        """Apply toolbar changes."""
        # Update toolbar manager with current configurations
        for toolbar_id, config in self.current_configs.items():
            self.toolbar_manager.update_toolbar_configuration(toolbar_id, config)
        
        # Save configuration
        self.toolbar_manager.save_configuration()
        
        self.configuration_changed.emit()
    
    def accept_changes(self):
        """Accept and apply changes."""
        self.apply_changes()
        self.accept()
    
    def reset_to_defaults(self):
        """Reset toolbars to default configuration."""
        reply = QMessageBox.question(
            self,
            self.i18n.tr("reset_to_defaults"),
            self.i18n.tr("reset_toolbars_confirm"),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.toolbar_manager.reset_to_defaults()
            self.load_current_configurations()
            self.load_toolbar_list()
            self.configuration_changed.emit()