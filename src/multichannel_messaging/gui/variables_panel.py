"""
Variables Panel GUI Component for CSC-Reach.

This module provides a GUI panel for displaying and managing template variables
with click-to-insert functionality.
"""

from typing import List, Optional, Callable
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, 
    QListWidgetItem, QGroupBox, QPushButton, QFrame, QSplitter,
    QTextEdit, QScrollArea, QSizePolicy, QToolTip
)
from PySide6.QtCore import Qt, Signal, QTimer, QPoint
from PySide6.QtGui import QFont, QIcon, QPalette, QCursor

from ..core.dynamic_variable_manager import DynamicVariableManager, TemplateVariable
from ..core.i18n_manager import get_i18n_manager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class VariableListItem(QListWidgetItem):
    """Custom list item for template variables."""
    
    def __init__(self, variable: TemplateVariable):
        super().__init__()
        self.variable = variable
        self.update_display()
    
    def update_display(self):
        """Update the display text for this item."""
        # Format: {variable_name} - Description (Type)
        display_text = f"{self.variable.format_for_template()}"
        if self.variable.description:
            display_text += f" - {self.variable.description}"
        # Always show data type for clarity
        display_text += f" ({self.variable.data_type})"
        
        self.setText(display_text)
        
        # Set tooltip with more details
        tooltip_parts = [
            f"Variable: {self.variable.format_for_template()}",
            f"Original Name: {self.variable.name}",
            f"Type: {self.variable.data_type}"
        ]
        if self.variable.sample_value:
            tooltip_parts.append(f"Sample: {self.variable.sample_value}")
        if self.variable.description:
            tooltip_parts.append(f"Description: {self.variable.description}")
        
        self.setToolTip("\n".join(tooltip_parts))


class VariablesPanel(QWidget):
    """GUI component for displaying and managing template variables."""
    
    # Signal emitted when a variable is selected for insertion
    variable_selected = Signal(str)  # variable format string like "{name}"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.variable_manager = DynamicVariableManager()
        self.i18n_manager = get_i18n_manager()
        
        # UI components
        self.search_box: Optional[QLineEdit] = None
        self.variable_list_widget: Optional[QListWidget] = None
        self.info_label: Optional[QLabel] = None
        self.insert_button: Optional[QPushButton] = None
        self.clear_search_button: Optional[QPushButton] = None
        
        # State
        self.filtered_variables: List[TemplateVariable] = []
        
        self.setup_ui()
        self.connect_signals()
        
        # Register for variable changes
        self.variable_manager.add_change_callback(self.on_variables_changed)
        
        # Initialize with default variables
        self.update_variables_display(self.variable_manager.get_available_variables())
    
    def setup_ui(self):
        """Set up the variables panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Title
        title_label = QLabel(self.i18n_manager.tr("template_variables"))
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Search box
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(self.i18n_manager.tr("search_variables"))
        search_layout.addWidget(self.search_box)
        
        self.clear_search_button = QPushButton("×")
        self.clear_search_button.setMaximumWidth(25)
        self.clear_search_button.setToolTip(self.i18n_manager.tr("clear_search"))
        search_layout.addWidget(self.clear_search_button)
        
        layout.addLayout(search_layout)
        
        # Variables list
        self.variable_list_widget = QListWidget()
        self.variable_list_widget.setAlternatingRowColors(True)
        self.variable_list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.variable_list_widget)
        
        # Info label
        self.info_label = QLabel(self.i18n_manager.tr("click_to_insert_variable"))
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self.info_label)
        
        # Insert button
        self.insert_button = QPushButton(self.i18n_manager.tr("insert_selected_variable"))
        self.insert_button.setEnabled(False)
        layout.addWidget(self.insert_button)
        
        # Set minimum width for the panel
        self.setMinimumWidth(200)
        self.setMaximumWidth(300)
    
    def connect_signals(self):
        """Connect UI signals."""
        if self.search_box:
            self.search_box.textChanged.connect(self.on_search_changed)
        
        if self.clear_search_button:
            self.clear_search_button.clicked.connect(self.clear_search)
        
        if self.variable_list_widget:
            self.variable_list_widget.itemClicked.connect(self.on_variable_clicked)
            self.variable_list_widget.itemDoubleClicked.connect(self.on_variable_double_clicked)
            self.variable_list_widget.itemSelectionChanged.connect(self.on_selection_changed)
        
        if self.insert_button:
            self.insert_button.clicked.connect(self.insert_selected_variable)
    
    def update_variables_display(self, variables: List[TemplateVariable]):
        """Update the display with new variables."""
        if not self.variable_list_widget:
            return
        
        self.variable_list_widget.clear()
        self.filtered_variables = variables.copy()
        
        for variable in variables:
            item = VariableListItem(variable)
            self.variable_list_widget.addItem(item)
        
        # Update info label
        count = len(variables)
        if count == 0:
            info_text = self.i18n_manager.tr("no_variables_available")
        else:
            info_text = self.i18n_manager.tr("variables_count", count=count)
        
        if self.info_label:
            self.info_label.setText(info_text + "\n" + self.i18n_manager.tr("click_to_insert_variable"))
        
        logger.debug(f"Updated variables display with {count} variables")
    
    def on_variables_changed(self, variables: List[TemplateVariable]):
        """Handle variable manager changes."""
        self.update_variables_display(variables)
    
    def on_search_changed(self, text: str):
        """Handle search text changes."""
        if not text.strip():
            # Show all variables
            self.update_variables_display(self.variable_manager.get_available_variables())
        else:
            # Filter variables
            filtered = self.variable_manager.search_variables(text.strip())
            self.update_variables_display(filtered)
    
    def clear_search(self):
        """Clear the search box."""
        if self.search_box:
            self.search_box.clear()
    
    def on_variable_clicked(self, item: QListWidgetItem):
        """Handle variable item click."""
        if isinstance(item, VariableListItem):
            logger.debug(f"Variable clicked: {item.variable.variable_name}")
    
    def on_variable_double_clicked(self, item: QListWidgetItem):
        """Handle variable item double-click - insert the variable."""
        if isinstance(item, VariableListItem):
            variable_format = item.variable.format_for_template()
            self.variable_selected.emit(variable_format)
            logger.info(f"Variable double-clicked for insertion: {variable_format}")
    
    def on_selection_changed(self):
        """Handle selection changes."""
        has_selection = bool(self.variable_list_widget and self.variable_list_widget.currentItem())
        if self.insert_button:
            self.insert_button.setEnabled(has_selection)
    
    def insert_selected_variable(self):
        """Insert the currently selected variable."""
        if not self.variable_list_widget:
            return
        
        current_item = self.variable_list_widget.currentItem()
        if isinstance(current_item, VariableListItem):
            variable_format = current_item.variable.format_for_template()
            self.variable_selected.emit(variable_format)
            logger.info(f"Variable inserted via button: {variable_format}")
    
    def get_variable_manager(self) -> DynamicVariableManager:
        """Get the variable manager instance."""
        return self.variable_manager
    
    def refresh_variables(self):
        """Refresh the variables display."""
        self.update_variables_display(self.variable_manager.get_available_variables())
    
    def select_variable_by_name(self, variable_name: str) -> bool:
        """Select a variable by its name."""
        if not self.variable_list_widget:
            return False
        
        for i in range(self.variable_list_widget.count()):
            item = self.variable_list_widget.item(i)
            if isinstance(item, VariableListItem) and item.variable.variable_name == variable_name:
                self.variable_list_widget.setCurrentItem(item)
                return True
        
        return False
    
    def get_selected_variable(self) -> Optional[TemplateVariable]:
        """Get the currently selected variable."""
        if not self.variable_list_widget:
            return None
        
        current_item = self.variable_list_widget.currentItem()
        if isinstance(current_item, VariableListItem):
            return current_item.variable
        
        return None


class CompactVariablesPanel(QWidget):
    """Compact version of the variables panel for smaller spaces."""
    
    variable_selected = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.variable_manager = DynamicVariableManager()
        self.i18n_manager = get_i18n_manager()
        
        self.variable_list_widget: Optional[QListWidget] = None
        
        self.setup_ui()
        self.connect_signals()
        
        # Register for variable changes
        self.variable_manager.add_change_callback(self.on_variables_changed)
        
        # Initialize with default variables
        self.update_variables_display(self.variable_manager.get_available_variables())
    
    def setup_ui(self):
        """Set up the compact UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Compact title
        title_label = QLabel(self.i18n_manager.tr("variables"))
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(9)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Compact variables list
        self.variable_list_widget = QListWidget()
        self.variable_list_widget.setMaximumHeight(120)
        layout.addWidget(self.variable_list_widget)
        
        # Set compact size
        self.setMaximumWidth(180)
        self.setMaximumHeight(150)
    
    def connect_signals(self):
        """Connect UI signals."""
        if self.variable_list_widget:
            self.variable_list_widget.itemDoubleClicked.connect(self.on_variable_double_clicked)
    
    def update_variables_display(self, variables: List[TemplateVariable]):
        """Update the compact display."""
        if not self.variable_list_widget:
            return
        
        self.variable_list_widget.clear()
        
        for variable in variables:
            item = QListWidgetItem(variable.format_for_template())
            item.setToolTip(f"{variable.name} - {variable.description}")
            item.setData(Qt.UserRole, variable)
            self.variable_list_widget.addItem(item)
    
    def on_variables_changed(self, variables: List[TemplateVariable]):
        """Handle variable manager changes."""
        self.update_variables_display(variables)
    
    def on_variable_double_clicked(self, item: QListWidgetItem):
        """Handle variable double-click."""
        variable = item.data(Qt.UserRole)
        if isinstance(variable, TemplateVariable):
            self.variable_selected.emit(variable.format_for_template())
    
    def get_variable_manager(self) -> DynamicVariableManager:
        """Get the variable manager instance."""
        return self.variable_manager