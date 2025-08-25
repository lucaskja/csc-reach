"""
Enhanced CSV Import Configuration Dialog for Multi-Channel Bulk Messaging System.
Provides flexible column selection, template management, and validation.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QPushButton, QLabel, QComboBox, QCheckBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QTabWidget, QWidget,
    QLineEdit, QTextEdit, QMessageBox, QFileDialog, QProgressBar,
    QSplitter, QFrame, QScrollArea, QButtonGroup, QRadioButton,
    QSpinBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont, QColor

from ..core.i18n_manager import get_i18n_manager
from ..core.csv_processor import AdvancedTableProcessor, FileStructure, ValidationIssue
from ..core.models import Customer, MessageChannel
from ..utils.logger import get_logger
from ..utils.exceptions import CSVProcessingError, ValidationError

logger = get_logger(__name__)


@dataclass
class CSVImportConfiguration:
    """Configuration for CSV import with flexible column mapping."""
    
    # Preset information (optional)
    preset_name: str = ""
    description: str = ""
    
    @property
    def template_name(self) -> str:
        """Backward compatibility property for template_name."""
        return self.preset_name
    
    @template_name.setter
    def template_name(self, value: str):
        """Backward compatibility setter for template_name."""
        self.preset_name = value
    
    # Column mapping configuration
    column_mapping: Dict[str, str] = field(default_factory=dict)  # CSV column -> field mapping
    custom_fields: Dict[str, str] = field(default_factory=dict)  # Custom field definitions
    
    # Import settings
    encoding: str = "utf-8"
    delimiter: str = ","
    has_header: bool = True
    skip_rows: int = 0
    
    # Validation rules
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    
    # Channel requirements
    messaging_channels: List[str] = field(default_factory=lambda: ["email"])  # Required channels
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    
    def validate_configuration(self) -> List[ValidationError]:
        """Validate the import configuration."""
        errors = []
        
        # Get mapped fields
        mapped_fields = set(self.column_mapping.values())
        
        # Name is always required
        if "name" not in mapped_fields:
            errors.append(ValidationError("Name field is required"))
        
        # Must have at least email OR phone for messaging
        has_email = "email" in mapped_fields
        has_phone = "phone" in mapped_fields
        
        if not has_email and not has_phone:
            errors.append(ValidationError("Either email or phone field is required for messaging"))
        
        # Check channel-specific requirements
        if "email" in self.messaging_channels and not has_email:
            errors.append(ValidationError("Email field is required for email messaging"))
        
        if "whatsapp" in self.messaging_channels and not has_phone:
            errors.append(ValidationError("Phone field is required for WhatsApp messaging"))
        
        return errors
    
    def apply_to_csv(self, csv_data: pd.DataFrame) -> pd.DataFrame:
        """Apply configuration to CSV data and return processed DataFrame."""
        # Apply column mapping
        mapped_data = pd.DataFrame()
        
        for csv_column, field_name in self.column_mapping.items():
            if csv_column in csv_data.columns:
                mapped_data[field_name] = csv_data[csv_column]
        
        # Skip rows if specified
        if self.skip_rows > 0:
            mapped_data = mapped_data.iloc[self.skip_rows:]
        
        return mapped_data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return {
            "preset_name": self.preset_name,
            "description": self.description,
            "column_mapping": self.column_mapping,
            "custom_fields": self.custom_fields,
            "encoding": self.encoding,
            "delimiter": self.delimiter,
            "has_header": self.has_header,
            "skip_rows": self.skip_rows,
            "validation_rules": self.validation_rules,
            "messaging_channels": self.messaging_channels,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat(),
            "usage_count": self.usage_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CSVImportConfiguration":
        """Create configuration from dictionary."""
        config = cls(
            preset_name=data.get("preset_name", data.get("template_name", "")),  # Backward compatibility
            description=data.get("description", ""),
            column_mapping=data.get("column_mapping", {}),
            custom_fields=data.get("custom_fields", {}),
            encoding=data.get("encoding", "utf-8"),
            delimiter=data.get("delimiter", ","),
            has_header=data.get("has_header", True),
            skip_rows=data.get("skip_rows", 0),
            validation_rules=data.get("validation_rules", {}),
            messaging_channels=data.get("messaging_channels", ["email"])
        )
        
        # Parse datetime fields
        if "created_at" in data:
            try:
                config.created_at = datetime.fromisoformat(data["created_at"])
            except (ValueError, TypeError):
                config.created_at = datetime.now()
        
        if "last_used" in data:
            try:
                config.last_used = datetime.fromisoformat(data["last_used"])
            except (ValueError, TypeError):
                config.last_used = datetime.now()
        
        config.usage_count = data.get("usage_count", 0)
        
        return config


class CSVPreviewThread(QThread):
    """Thread for loading and previewing CSV data."""
    
    preview_ready = Signal(object, object)  # file_structure, preview_data
    error_occurred = Signal(str)
    
    def __init__(self, file_path: str, configuration: CSVImportConfiguration):
        super().__init__()
        self.file_path = file_path
        self.configuration = configuration
        self.processor = AdvancedTableProcessor()
    
    def run(self):
        """Load and process CSV file for preview."""
        try:
            file_path = Path(self.file_path)
            
            # Analyze file structure
            structure = self.processor.analyze_file_structure(file_path)
            
            # Load preview data
            if structure.file_format.value in ['csv', 'tsv']:
                preview_data = pd.read_csv(
                    file_path,
                    encoding=self.configuration.encoding,
                    delimiter=self.configuration.delimiter,
                    nrows=100  # Limit preview to 100 rows
                )
            else:
                # Handle other formats
                preview_data = pd.read_csv(file_path, nrows=100)
            
            self.preview_ready.emit(structure, preview_data)
            
        except Exception as e:
            logger.error(f"CSV preview failed: {e}")
            self.error_occurred.emit(str(e))


class CSVImportConfigDialog(QDialog):
    """Enhanced CSV import configuration dialog."""
    
    configuration_ready = Signal(object, object)  # configuration, processed_data
    
    def __init__(self, parent=None, file_path: Optional[str] = None):
        super().__init__(parent)
        self.file_path = file_path
        self.configuration = CSVImportConfiguration()
        self.file_structure: Optional[FileStructure] = None
        self.preview_data: Optional[pd.DataFrame] = None
        self.processed_data: Optional[pd.DataFrame] = None
        
        # Initialize i18n
        self.i18n = get_i18n_manager()
        
        # Preset management (renamed from templates)
        self.presets_dir = Path.home() / ".csc-reach" / "csv_presets"
        self.presets_dir.mkdir(parents=True, exist_ok=True)
        
        self.setup_ui()
        self.load_available_presets()
        
        # Load file if provided
        if self.file_path:
            self.load_csv_file()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle(self.i18n.tr("csv_import_configuration"))
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Create tab widget for different configuration sections
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_file_tab()
        self.create_columns_tab()
        self.create_preview_tab()
        self.create_presets_tab()
        
        # Button layout
        button_layout = QHBoxLayout()
        
        self.load_preset_btn = QPushButton(self.i18n.tr("load_preset"))
        self.load_preset_btn.clicked.connect(self.load_preset)
        button_layout.addWidget(self.load_preset_btn)
        
        self.save_preset_btn = QPushButton(self.i18n.tr("save_as_preset"))
        self.save_preset_btn.clicked.connect(self.save_as_preset)
        button_layout.addWidget(self.save_preset_btn)
        
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton(self.i18n.tr("cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.import_btn = QPushButton(self.i18n.tr("import_data"))
        self.import_btn.clicked.connect(self.import_data)
        self.import_btn.setEnabled(False)
        button_layout.addWidget(self.import_btn)
        
        layout.addLayout(button_layout)
    
    def create_file_tab(self):
        """Create the file configuration tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # File selection
        file_group = QGroupBox(self.i18n.tr("file_selection"))
        file_layout = QGridLayout(file_group)
        
        file_layout.addWidget(QLabel(self.i18n.tr("csv_file")), 0, 0)
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        if self.file_path:
            self.file_path_edit.setText(self.file_path)
        file_layout.addWidget(self.file_path_edit, 0, 1)
        
        self.browse_btn = QPushButton(self.i18n.tr("browse"))
        self.browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.browse_btn, 0, 2)
        
        layout.addWidget(file_group)
        
        # File format settings
        format_group = QGroupBox(self.i18n.tr("file_format_settings"))
        format_layout = QGridLayout(format_group)
        
        format_layout.addWidget(QLabel(self.i18n.tr("encoding")), 0, 0)
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems(["utf-8", "utf-8-sig", "cp1252", "iso-8859-1", "ascii"])
        self.encoding_combo.currentTextChanged.connect(self.on_format_changed)
        format_layout.addWidget(self.encoding_combo, 0, 1)
        
        format_layout.addWidget(QLabel(self.i18n.tr("delimiter")), 1, 0)
        self.delimiter_combo = QComboBox()
        self.delimiter_combo.addItems([",", ";", "\t", "|"])
        self.delimiter_combo.setCurrentText(",")
        self.delimiter_combo.currentTextChanged.connect(self.on_format_changed)
        format_layout.addWidget(self.delimiter_combo, 1, 1)
        
        self.has_header_check = QCheckBox(self.i18n.tr("first_row_headers"))
        self.has_header_check.setChecked(True)
        self.has_header_check.toggled.connect(self.on_format_changed)
        format_layout.addWidget(self.has_header_check, 2, 0, 1, 2)
        
        format_layout.addWidget(QLabel(self.i18n.tr("skip_rows")), 3, 0)
        self.skip_rows_spin = QSpinBox()
        self.skip_rows_spin.setMinimum(0)
        self.skip_rows_spin.setMaximum(100)
        self.skip_rows_spin.valueChanged.connect(self.on_format_changed)
        format_layout.addWidget(self.skip_rows_spin, 3, 1)
        
        layout.addWidget(format_group)
        
        # Channel requirements
        channel_group = QGroupBox(self.i18n.tr("messaging_channels"))
        channel_layout = QVBoxLayout(channel_group)
        
        channel_info = QLabel(self.i18n.tr("csv_channel_requirements_info"))
        channel_info.setWordWrap(True)
        channel_layout.addWidget(channel_info)
        
        self.email_check = QCheckBox(self.i18n.tr("email_messaging"))
        self.email_check.setChecked(True)
        self.email_check.toggled.connect(self.on_channels_changed)
        channel_layout.addWidget(self.email_check)
        
        self.whatsapp_check = QCheckBox(self.i18n.tr("whatsapp_messaging"))
        self.whatsapp_check.toggled.connect(self.on_channels_changed)
        channel_layout.addWidget(self.whatsapp_check)
        
        layout.addWidget(channel_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, self.i18n.tr("file_settings"))
    
    def create_columns_tab(self):
        """Create the column mapping tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Instructions
        instructions = QLabel(self.i18n.tr("csv_column_mapping_instructions"))
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Column mapping table
        self.column_table = QTableWidget()
        self.column_table.setColumnCount(4)
        self.column_table.setHorizontalHeaderLabels([
            self.i18n.tr("csv_column"),
            self.i18n.tr("field_mapping"),
            self.i18n.tr("required"),
            self.i18n.tr("preview_data")
        ])
        
        # Set column widths
        header = self.column_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.column_table)
        
        # Required fields info
        self.required_fields_label = QLabel()
        self.update_required_fields_info()
        layout.addWidget(self.required_fields_label)
        
        self.tab_widget.addTab(tab, self.i18n.tr("column_mapping"))
    
    def create_preview_tab(self):
        """Create the data preview tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Preview controls
        controls_layout = QHBoxLayout()
        
        self.refresh_preview_btn = QPushButton(self.i18n.tr("refresh_preview"))
        self.refresh_preview_btn.clicked.connect(self.refresh_preview)
        controls_layout.addWidget(self.refresh_preview_btn)
        
        controls_layout.addStretch()
        
        self.preview_info_label = QLabel()
        controls_layout.addWidget(self.preview_info_label)
        
        layout.addLayout(controls_layout)
        
        # Preview table
        self.preview_table = QTableWidget()
        layout.addWidget(self.preview_table)
        
        # Validation results
        validation_group = QGroupBox(self.i18n.tr("validation_results"))
        validation_layout = QVBoxLayout(validation_group)
        
        self.validation_text = QTextEdit()
        self.validation_text.setMaximumHeight(150)
        self.validation_text.setReadOnly(True)
        validation_layout.addWidget(self.validation_text)
        
        layout.addWidget(validation_group)
        
        self.tab_widget.addTab(tab, self.i18n.tr("preview_validation"))
    
    def create_presets_tab(self):
        """Create the preset management tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Info about presets
        info_label = QLabel(self.i18n.tr("csv_presets_info"))
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Preset info (optional)
        preset_group = QGroupBox(self.i18n.tr("preset_information_optional"))
        preset_layout = QGridLayout(preset_group)
        
        preset_layout.addWidget(QLabel(self.i18n.tr("preset_name")), 0, 0)
        self.preset_name_edit = QLineEdit()
        self.preset_name_edit.setPlaceholderText(self.i18n.tr("preset_name_placeholder"))
        self.preset_name_edit.textChanged.connect(self.on_preset_info_changed)
        preset_layout.addWidget(self.preset_name_edit, 0, 1)
        
        preset_layout.addWidget(QLabel(self.i18n.tr("description")), 1, 0)
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText(self.i18n.tr("preset_description_placeholder"))
        self.description_edit.textChanged.connect(self.on_preset_info_changed)
        preset_layout.addWidget(self.description_edit, 1, 1)
        
        layout.addWidget(preset_group)
        
        # Available presets
        available_group = QGroupBox(self.i18n.tr("available_presets"))
        available_layout = QVBoxLayout(available_group)
        
        self.presets_table = QTableWidget()
        self.presets_table.setColumnCount(4)
        self.presets_table.setHorizontalHeaderLabels([
            self.i18n.tr("name"),
            self.i18n.tr("description"),
            self.i18n.tr("last_used"),
            self.i18n.tr("usage_count")
        ])
        
        # Set column widths
        header = self.presets_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self.presets_table.itemSelectionChanged.connect(self.on_preset_selected)
        available_layout.addWidget(self.presets_table)
        
        # Preset management buttons
        preset_buttons = QHBoxLayout()
        
        self.delete_preset_btn = QPushButton(self.i18n.tr("delete_preset"))
        self.delete_preset_btn.clicked.connect(self.delete_preset)
        self.delete_preset_btn.setEnabled(False)
        preset_buttons.addWidget(self.delete_preset_btn)
        
        preset_buttons.addStretch()
        
        available_layout.addLayout(preset_buttons)
        
        layout.addWidget(available_group)
        
        self.tab_widget.addTab(tab, self.i18n.tr("presets"))    

    def browse_file(self):
        """Browse for CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.i18n.tr("select_csv_file"),
            "",
            "CSV Files (*.csv);;TSV Files (*.tsv);;All Files (*)"
        )
        
        if file_path:
            self.file_path = file_path
            self.file_path_edit.setText(file_path)
            self.load_csv_file()
    
    def load_csv_file(self):
        """Load and analyze the CSV file."""
        if not self.file_path:
            return
        
        try:
            # Update configuration with current settings
            self.update_configuration_from_ui()
            
            # Start preview thread
            self.preview_thread = CSVPreviewThread(self.file_path, self.configuration)
            self.preview_thread.preview_ready.connect(self.on_preview_ready)
            self.preview_thread.error_occurred.connect(self.on_preview_error)
            self.preview_thread.start()
            
        except Exception as e:
            logger.error(f"Failed to load CSV file: {e}")
            QMessageBox.critical(self, self.i18n.tr("error"), str(e))
    
    def on_preview_ready(self, file_structure: FileStructure, preview_data: pd.DataFrame):
        """Handle preview data ready."""
        self.file_structure = file_structure
        self.preview_data = preview_data
        
        # Update encoding and delimiter from detected values
        if file_structure.encoding:
            self.encoding_combo.setCurrentText(file_structure.encoding.encoding)
        if file_structure.delimiter:
            self.delimiter_combo.setCurrentText(file_structure.delimiter.delimiter)
        
        # Update column mapping table
        self.update_column_mapping_table()
        
        # Enable import button
        self.import_btn.setEnabled(True)
        
        # Switch to columns tab
        self.tab_widget.setCurrentIndex(1)
    
    def on_preview_error(self, error_message: str):
        """Handle preview error."""
        QMessageBox.critical(self, self.i18n.tr("preview_error"), error_message)
        self.import_btn.setEnabled(False)
    
    def update_column_mapping_table(self):
        """Update the column mapping table with CSV columns."""
        if not self.preview_data is not None:
            return
        
        columns = list(self.preview_data.columns)
        self.column_table.setRowCount(len(columns))
        
        # Available field mappings
        field_options = ["", "name", "email", "phone", "company"]
        
        for i, column in enumerate(columns):
            # CSV column name
            column_item = QTableWidgetItem(str(column))
            column_item.setFlags(column_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.column_table.setItem(i, 0, column_item)
            
            # Field mapping combo
            mapping_combo = QComboBox()
            mapping_combo.addItems(field_options)
            
            # Try to auto-detect mapping
            auto_mapping = self.auto_detect_mapping(str(column))
            if auto_mapping:
                mapping_combo.setCurrentText(auto_mapping)
            
            mapping_combo.currentTextChanged.connect(self.on_mapping_changed)
            self.column_table.setCellWidget(i, 1, mapping_combo)
            
            # Required indicator
            required_item = QTableWidgetItem("")
            required_item.setFlags(required_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.column_table.setItem(i, 2, required_item)
            
            # Preview data
            preview_values = []
            for j in range(min(3, len(self.preview_data))):
                if j < len(self.preview_data):
                    value = str(self.preview_data.iloc[j][column])
                    if len(value) > 30:
                        value = value[:27] + "..."
                    preview_values.append(value)
            
            preview_item = QTableWidgetItem(", ".join(preview_values))
            preview_item.setFlags(preview_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.column_table.setItem(i, 3, preview_item)
        
        # Update required indicators
        self.update_required_indicators()
    
    def auto_detect_mapping(self, column_name: str) -> Optional[str]:
        """Auto-detect field mapping for a column name."""
        column_lower = column_name.lower().strip()
        
        # Name patterns
        if any(pattern in column_lower for pattern in ['name', 'nome', 'nombre', 'client', 'customer']):
            return "name"
        
        # Email patterns
        if any(pattern in column_lower for pattern in ['email', 'e-mail', 'mail', 'correo']):
            return "email"
        
        # Phone patterns
        if any(pattern in column_lower for pattern in ['phone', 'tel', 'mobile', 'cell', 'telefone', 'teléfono']):
            return "phone"
        
        # Company patterns
        if any(pattern in column_lower for pattern in ['company', 'organization', 'org', 'business', 'empresa', 'compañía']):
            return "company"
        
        return None
    
    def on_mapping_changed(self):
        """Handle mapping change."""
        self.update_required_indicators()
        self.update_configuration_from_ui()
        self.validate_configuration()
    
    def update_required_indicators(self):
        """Update required field indicators in the table."""
        # Get current mappings
        current_mappings = set()
        for i in range(self.column_table.rowCount()):
            combo = self.column_table.cellWidget(i, 1)
            if combo and combo.currentText():
                current_mappings.add(combo.currentText())
        
        # Name is always required
        required_fields = {"name"}
        
        # Add channel-specific requirements
        if self.email_check.isChecked():
            required_fields.add("email")
        if self.whatsapp_check.isChecked():
            required_fields.add("phone")
        
        # Update required indicators
        for i in range(self.column_table.rowCount()):
            combo = self.column_table.cellWidget(i, 1)
            required_item = self.column_table.item(i, 2)
            
            if combo and required_item:
                field_name = combo.currentText()
                if field_name in required_fields:
                    required_item.setText("✓")
                    required_item.setBackground(QColor(200, 255, 200))  # Light green
                else:
                    required_item.setText("")
                    required_item.setBackground(QColor(255, 255, 255))  # White
        
        # Update required fields info
        self.update_required_fields_info()
    
    def update_required_fields_info(self):
        """Update the required fields information label."""
        # Name is always required
        required_fields = {"name"}
        
        # Add channel-specific requirements
        if self.email_check.isChecked():
            required_fields.add("email")
        if self.whatsapp_check.isChecked():
            required_fields.add("phone")
        
        # Check if we have at least email OR phone for basic messaging
        has_email_or_phone = self.email_check.isChecked() or self.whatsapp_check.isChecked()
        
        if has_email_or_phone:
            fields_text = ", ".join(sorted(required_fields))
            self.required_fields_label.setText(
                self.i18n.tr("csv_required_fields_info", fields=fields_text)
            )
        else:
            self.required_fields_label.setText(self.i18n.tr("csv_no_channels_selected"))
    
    def on_format_changed(self):
        """Handle file format settings change."""
        self.update_configuration_from_ui()
        if self.file_path:
            self.load_csv_file()
    
    def on_channels_changed(self):
        """Handle messaging channels change."""
        self.update_required_indicators()
        self.update_configuration_from_ui()
    
    def on_preset_info_changed(self):
        """Handle preset information change."""
        self.update_configuration_from_ui()
    
    def update_configuration_from_ui(self):
        """Update configuration object from UI values."""
        if hasattr(self, 'preset_name_edit'):
            self.configuration.preset_name = self.preset_name_edit.text().strip()
        if hasattr(self, 'description_edit'):
            self.configuration.description = self.description_edit.toPlainText().strip()
        self.configuration.encoding = self.encoding_combo.currentText()
        self.configuration.delimiter = self.delimiter_combo.currentText()
        self.configuration.has_header = self.has_header_check.isChecked()
        self.configuration.skip_rows = self.skip_rows_spin.value()
        
        # Update messaging channels
        channels = []
        if self.email_check.isChecked():
            channels.append("email")
        if self.whatsapp_check.isChecked():
            channels.append("whatsapp")
        self.configuration.messaging_channels = channels
        
        # Update column mapping
        column_mapping = {}
        if hasattr(self, 'column_table'):
            for i in range(self.column_table.rowCount()):
                csv_column_item = self.column_table.item(i, 0)
                mapping_combo = self.column_table.cellWidget(i, 1)
                
                if csv_column_item and mapping_combo:
                    csv_column = csv_column_item.text()
                    field_mapping = mapping_combo.currentText()
                    
                    if field_mapping:  # Only include non-empty mappings
                        column_mapping[csv_column] = field_mapping
        
        self.configuration.column_mapping = column_mapping
    
    def validate_configuration(self) -> bool:
        """Validate the current configuration."""
        errors = self.configuration.validate_configuration()
        
        if errors:
            error_text = "\n".join([str(error) for error in errors])
            self.validation_text.setPlainText(error_text)
            self.validation_text.setStyleSheet("color: red;")
            return False
        else:
            self.validation_text.setPlainText(self.i18n.tr("configuration_valid"))
            self.validation_text.setStyleSheet("color: green;")
            return True
    
    def refresh_preview(self):
        """Refresh the data preview."""
        if not self.preview_data is not None or not self.configuration.column_mapping:
            return
        
        try:
            # Apply configuration to preview data
            processed_data = self.configuration.apply_to_csv(self.preview_data)
            
            # Update preview table
            self.preview_table.setRowCount(min(50, len(processed_data)))  # Show max 50 rows
            self.preview_table.setColumnCount(len(processed_data.columns))
            self.preview_table.setHorizontalHeaderLabels(list(processed_data.columns))
            
            for i in range(min(50, len(processed_data))):
                for j, column in enumerate(processed_data.columns):
                    value = str(processed_data.iloc[i][column])
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.preview_table.setItem(i, j, item)
            
            # Update preview info
            total_rows = len(processed_data)
            shown_rows = min(50, total_rows)
            self.preview_info_label.setText(
                self.i18n.tr("preview_info", shown=shown_rows, total=total_rows)
            )
            
            # Store processed data
            self.processed_data = processed_data
            
            # Validate configuration
            self.validate_configuration()
            
        except Exception as e:
            logger.error(f"Preview refresh failed: {e}")
            self.validation_text.setPlainText(f"Preview error: {str(e)}")
            self.validation_text.setStyleSheet("color: red;")
    
    def load_available_presets(self):
        """Load available configuration presets."""
        self.presets_table.setRowCount(0)
        
        try:
            preset_files = list(self.presets_dir.glob("*.json"))
            self.presets_table.setRowCount(len(preset_files))
            
            for i, preset_file in enumerate(preset_files):
                try:
                    with open(preset_file, 'r', encoding='utf-8') as f:
                        preset_data = json.load(f)
                    
                    config = CSVImportConfiguration.from_dict(preset_data)
                    
                    # Name
                    name_item = QTableWidgetItem(config.preset_name)
                    name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.presets_table.setItem(i, 0, name_item)
                    
                    # Description
                    desc_item = QTableWidgetItem(config.description)
                    desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.presets_table.setItem(i, 1, desc_item)
                    
                    # Last used
                    last_used_item = QTableWidgetItem(config.last_used.strftime("%Y-%m-%d %H:%M"))
                    last_used_item.setFlags(last_used_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.presets_table.setItem(i, 2, last_used_item)
                    
                    # Usage count
                    usage_item = QTableWidgetItem(str(config.usage_count))
                    usage_item.setFlags(usage_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.presets_table.setItem(i, 3, usage_item)
                    
                except Exception as e:
                    logger.warning(f"Failed to load preset {preset_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to load presets: {e}")
    
    def on_preset_selected(self):
        """Handle preset selection."""
        selected_items = self.presets_table.selectedItems()
        self.delete_preset_btn.setEnabled(len(selected_items) > 0)
    
    def load_preset(self):
        """Load selected preset."""
        current_row = self.presets_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, self.i18n.tr("info"), self.i18n.tr("select_preset_to_load"))
            return
        
        try:
            name_item = self.presets_table.item(current_row, 0)
            if not name_item:
                return
            
            preset_name = name_item.text()
            preset_file = self.presets_dir / f"{preset_name}.json"
            
            if not preset_file.exists():
                QMessageBox.warning(self, self.i18n.tr("warning"), self.i18n.tr("preset_file_not_found"))
                return
            
            with open(preset_file, 'r', encoding='utf-8') as f:
                preset_data = json.load(f)
            
            # Load configuration
            self.configuration = CSVImportConfiguration.from_dict(preset_data)
            
            # Update usage count and last used
            self.configuration.usage_count += 1
            self.configuration.last_used = datetime.now()
            
            # Update UI
            self.update_ui_from_configuration()
            
            # Save updated preset
            self.save_preset_to_file(preset_file)
            
            # Refresh presets list
            self.load_available_presets()
            
            QMessageBox.information(self, self.i18n.tr("success"), self.i18n.tr("preset_loaded_successfully"))
            
        except Exception as e:
            logger.error(f"Failed to load preset: {e}")
            QMessageBox.critical(self, self.i18n.tr("error"), str(e))
    
    def update_ui_from_configuration(self):
        """Update UI controls from configuration object."""
        self.preset_name_edit.setText(self.configuration.preset_name)
        self.description_edit.setPlainText(self.configuration.description)
        self.encoding_combo.setCurrentText(self.configuration.encoding)
        self.delimiter_combo.setCurrentText(self.configuration.delimiter)
        self.has_header_check.setChecked(self.configuration.has_header)
        self.skip_rows_spin.setValue(self.configuration.skip_rows)
        
        # Update channel checkboxes
        self.email_check.setChecked("email" in self.configuration.messaging_channels)
        self.whatsapp_check.setChecked("whatsapp" in self.configuration.messaging_channels)
        
        # Update column mappings if we have preview data
        if hasattr(self, 'column_table') and self.preview_data is not None:
            for i in range(self.column_table.rowCount()):
                csv_column_item = self.column_table.item(i, 0)
                mapping_combo = self.column_table.cellWidget(i, 1)
                
                if csv_column_item and mapping_combo:
                    csv_column = csv_column_item.text()
                    if csv_column in self.configuration.column_mapping:
                        field_mapping = self.configuration.column_mapping[csv_column]
                        mapping_combo.setCurrentText(field_mapping)
        
        self.update_required_indicators()
    
    def save_as_preset(self):
        """Save current configuration as preset."""
        self.update_configuration_from_ui()
        
        if not self.configuration.preset_name.strip():
            QMessageBox.warning(self, self.i18n.tr("warning"), self.i18n.tr("preset_name_required"))
            return
        
        try:
            preset_file = self.presets_dir / f"{self.configuration.preset_name}.json"
            
            # Check if preset already exists
            if preset_file.exists():
                reply = QMessageBox.question(
                    self,
                    self.i18n.tr("confirm"),
                    self.i18n.tr("preset_exists_overwrite"),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            # Save preset
            self.save_preset_to_file(preset_file)
            
            # Refresh presets list
            self.load_available_presets()
            
            QMessageBox.information(self, self.i18n.tr("success"), self.i18n.tr("preset_saved_successfully"))
            
        except Exception as e:
            logger.error(f"Failed to save preset: {e}")
            QMessageBox.critical(self, self.i18n.tr("error"), str(e))
    
    def save_preset_to_file(self, file_path: Path):
        """Save configuration to preset file."""
        preset_data = self.configuration.to_dict()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(preset_data, f, indent=2, ensure_ascii=False)
    
    def delete_preset(self):
        """Delete selected preset."""
        current_row = self.presets_table.currentRow()
        if current_row < 0:
            return
        
        try:
            name_item = self.presets_table.item(current_row, 0)
            if not name_item:
                return
            
            preset_name = name_item.text()
            
            reply = QMessageBox.question(
                self,
                self.i18n.tr("confirm"),
                self.i18n.tr("confirm_delete_preset", name=preset_name),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                preset_file = self.presets_dir / f"{preset_name}.json"
                if preset_file.exists():
                    preset_file.unlink()
                
                # Refresh presets list
                self.load_available_presets()
                
                QMessageBox.information(self, self.i18n.tr("success"), self.i18n.tr("preset_deleted_successfully"))
                
        except Exception as e:
            logger.error(f"Failed to delete preset: {e}")
            QMessageBox.critical(self, self.i18n.tr("error"), str(e))
    
    def import_data(self):
        """Import data with current configuration."""
        self.update_configuration_from_ui()
        
        # Validate configuration
        if not self.validate_configuration():
            QMessageBox.warning(self, self.i18n.tr("warning"), self.i18n.tr("fix_configuration_errors"))
            return
        
        if self.processed_data is None:
            self.refresh_preview()
        
        if self.processed_data is None:
            QMessageBox.warning(self, self.i18n.tr("warning"), self.i18n.tr("no_data_to_import"))
            return
        
        # Emit signal with configuration and processed data
        self.configuration_ready.emit(self.configuration, self.processed_data)
        self.accept()