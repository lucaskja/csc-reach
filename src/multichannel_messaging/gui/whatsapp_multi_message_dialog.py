"""
WhatsApp Multi-Message Template Dialog.

Provides interface for creating and editing WhatsApp templates with multi-message support.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox,
    QCheckBox, QSpinBox, QDoubleSpinBox, QListWidget, QListWidgetItem,
    QSplitter, QTabWidget, QWidget, QMessageBox, QScrollArea,
    QFrame, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPalette

from ..core.whatsapp_multi_message import (
    WhatsAppMultiMessageTemplate, MessageSplitStrategy
)
from ..core.models import Customer
from ..core.i18n_manager import get_i18n_manager
from ..utils.logger import get_logger

logger = get_logger(__name__)
i18n = get_i18n_manager()


class MessageSequenceWidget(QWidget):
    """Widget for displaying and editing message sequence."""
    
    sequence_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.messages: List[str] = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.sequence_label = QLabel(i18n.tr("message_sequence"))
        font = QFont()
        font.setBold(True)
        self.sequence_label.setFont(font)
        header_layout.addWidget(self.sequence_label)
        
        header_layout.addStretch()
        
        self.message_count_label = QLabel("0 " + i18n.tr("messages"))
        self.message_count_label.setStyleSheet("color: #666;")
        header_layout.addWidget(self.message_count_label)
        
        layout.addLayout(header_layout)
        
        # Message list
        self.message_list = QListWidget()
        self.message_list.setMaximumHeight(200)
        self.message_list.setAlternatingRowColors(True)
        layout.addWidget(self.message_list)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.add_message_btn = QPushButton(i18n.tr("add_message"))
        self.add_message_btn.clicked.connect(self.add_message)
        controls_layout.addWidget(self.add_message_btn)
        
        self.edit_message_btn = QPushButton(i18n.tr("edit_message"))
        self.edit_message_btn.clicked.connect(self.edit_message)
        self.edit_message_btn.setEnabled(False)
        controls_layout.addWidget(self.edit_message_btn)
        
        self.remove_message_btn = QPushButton(i18n.tr("remove_message"))
        self.remove_message_btn.clicked.connect(self.remove_message)
        self.remove_message_btn.setEnabled(False)
        controls_layout.addWidget(self.remove_message_btn)
        
        controls_layout.addStretch()
        
        self.move_up_btn = QPushButton("↑")
        self.move_up_btn.setMaximumWidth(30)
        self.move_up_btn.clicked.connect(self.move_message_up)
        self.move_up_btn.setEnabled(False)
        controls_layout.addWidget(self.move_up_btn)
        
        self.move_down_btn = QPushButton("↓")
        self.move_down_btn.setMaximumWidth(30)
        self.move_down_btn.clicked.connect(self.move_message_down)
        self.move_down_btn.setEnabled(False)
        controls_layout.addWidget(self.move_down_btn)
        
        layout.addLayout(controls_layout)
        
        # Connect signals
        self.message_list.currentRowChanged.connect(self.on_selection_changed)
        self.message_list.itemDoubleClicked.connect(self.edit_message)
    
    def set_messages(self, messages: List[str]):
        """Set the message sequence."""
        self.messages = messages.copy()
        self.update_display()
    
    def get_messages(self) -> List[str]:
        """Get the current message sequence."""
        return self.messages.copy()
    
    def update_display(self):
        """Update the display with current messages."""
        self.message_list.clear()
        
        for i, message in enumerate(self.messages):
            # Truncate long messages for display
            display_text = message[:100] + "..." if len(message) > 100 else message
            display_text = display_text.replace('\n', ' ')  # Single line display
            
            item_text = f"{i+1}. {display_text}"
            item = QListWidgetItem(item_text)
            item.setToolTip(message)  # Full message in tooltip
            
            # Color code by message length
            if len(message) > 3000:
                item.setBackground(QColor(255, 200, 200))  # Light red for long messages
            elif len(message) > 1000:
                item.setBackground(QColor(255, 255, 200))  # Light yellow for medium messages
            
            self.message_list.addItem(item)
        
        # Update count
        self.message_count_label.setText(f"{len(self.messages)} " + i18n.tr("messages"))
        
        # Update button states
        self.on_selection_changed()
    
    def on_selection_changed(self):
        """Handle selection change."""
        current_row = self.message_list.currentRow()
        has_selection = current_row >= 0
        
        self.edit_message_btn.setEnabled(has_selection)
        self.remove_message_btn.setEnabled(has_selection)
        self.move_up_btn.setEnabled(has_selection and current_row > 0)
        self.move_down_btn.setEnabled(has_selection and current_row < len(self.messages) - 1)
    
    def add_message(self):
        """Add a new message."""
        from PySide6.QtWidgets import QInputDialog
        
        text, ok = QInputDialog.getMultiLineText(
            self,
            i18n.tr("add_message"),
            i18n.tr("enter_message_content"),
            ""
        )
        
        if ok and text.strip():
            self.messages.append(text.strip())
            self.update_display()
            self.sequence_changed.emit()
    
    def edit_message(self):
        """Edit the selected message."""
        current_row = self.message_list.currentRow()
        if current_row < 0 or current_row >= len(self.messages):
            return
        
        from PySide6.QtWidgets import QInputDialog
        
        current_text = self.messages[current_row]
        text, ok = QInputDialog.getMultiLineText(
            self,
            i18n.tr("edit_message"),
            i18n.tr("edit_message_content"),
            current_text
        )
        
        if ok and text.strip():
            self.messages[current_row] = text.strip()
            self.update_display()
            self.sequence_changed.emit()
    
    def remove_message(self):
        """Remove the selected message."""
        current_row = self.message_list.currentRow()
        if current_row < 0 or current_row >= len(self.messages):
            return
        
        reply = QMessageBox.question(
            self,
            i18n.tr("remove_message"),
            i18n.tr("remove_message_confirm"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            del self.messages[current_row]
            self.update_display()
            self.sequence_changed.emit()
    
    def move_message_up(self):
        """Move selected message up."""
        current_row = self.message_list.currentRow()
        if current_row <= 0:
            return
        
        # Swap messages
        self.messages[current_row], self.messages[current_row - 1] = \
            self.messages[current_row - 1], self.messages[current_row]
        
        self.update_display()
        self.message_list.setCurrentRow(current_row - 1)
        self.sequence_changed.emit()
    
    def move_message_down(self):
        """Move selected message down."""
        current_row = self.message_list.currentRow()
        if current_row < 0 or current_row >= len(self.messages) - 1:
            return
        
        # Swap messages
        self.messages[current_row], self.messages[current_row + 1] = \
            self.messages[current_row + 1], self.messages[current_row]
        
        self.update_display()
        self.message_list.setCurrentRow(current_row + 1)
        self.sequence_changed.emit()


class MessagePreviewWidget(QWidget):
    """Widget for previewing message sequence."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.template: Optional[WhatsAppMultiMessageTemplate] = None
        self.sample_customer = Customer(
            name="John Smith",
            company="Acme Corporation", 
            phone="+1-555-0123",
            email="john.smith@acme.com"
        )
        # Validate with all fields for sample data
        self.sample_customer.validate(["name", "company", "phone", "email"])
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        preview_label = QLabel(i18n.tr("message_preview"))
        font = QFont()
        font.setBold(True)
        preview_label.setFont(font)
        header_layout.addWidget(preview_label)
        
        header_layout.addStretch()
        
        self.timing_label = QLabel("")
        self.timing_label.setStyleSheet("color: #666;")
        header_layout.addWidget(self.timing_label)
        
        layout.addLayout(header_layout)
        
        # Preview area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(300)
        
        self.preview_widget = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_widget)
        
        scroll_area.setWidget(self.preview_widget)
        layout.addWidget(scroll_area)
        
        # Sample data info
        info_label = QLabel(i18n.tr("preview_sample_data_info"))
        info_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(info_label)
    
    def set_template(self, template: Optional[WhatsAppMultiMessageTemplate]):
        """Set the template to preview."""
        self.template = template
        self.update_preview()
    
    def update_preview(self):
        """Update the preview display."""
        # Clear existing preview
        for i in reversed(range(self.preview_layout.count())):
            child = self.preview_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        if not self.template:
            no_template_label = QLabel(i18n.tr("no_template_selected"))
            no_template_label.setAlignment(Qt.AlignCenter)
            no_template_label.setStyleSheet("color: #999; font-style: italic;")
            self.preview_layout.addWidget(no_template_label)
            self.timing_label.setText("")
            return
        
        # Get rendered messages
        customer_data = self.sample_customer.to_dict()
        rendered_messages = self.template.preview_message_sequence(customer_data)
        
        # Display messages
        for i, message in enumerate(rendered_messages):
            message_frame = QFrame()
            message_frame.setFrameStyle(QFrame.Box)
            message_frame.setStyleSheet("""
                QFrame {
                    background-color: #e8f5e8;
                    border: 1px solid #c3e6c3;
                    border-radius: 8px;
                    padding: 8px;
                    margin: 2px;
                }
            """)
            
            message_layout = QVBoxLayout(message_frame)
            
            # Message header
            header_layout = QHBoxLayout()
            
            message_num_label = QLabel(f"{i18n.tr('message')} {i+1}")
            message_num_label.setStyleSheet("font-weight: bold; color: #2e7d32;")
            header_layout.addWidget(message_num_label)
            
            header_layout.addStretch()
            
            char_count_label = QLabel(f"{len(message)} {i18n.tr('characters')}")
            char_count_label.setStyleSheet("color: #666; font-size: 11px;")
            header_layout.addWidget(char_count_label)
            
            message_layout.addLayout(header_layout)
            
            # Message content
            message_text = QLabel(message)
            message_text.setWordWrap(True)
            message_text.setStyleSheet("color: #1b5e20; padding: 4px;")
            message_layout.addWidget(message_text)
            
            # Timing info for multi-message
            if len(rendered_messages) > 1 and i < len(rendered_messages) - 1:
                delay_label = QLabel(f"⏱ {i18n.tr('delay')} {self.template.message_delay_seconds}s")
                delay_label.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
                delay_label.setAlignment(Qt.AlignCenter)
                message_layout.addWidget(delay_label)
            
            self.preview_layout.addWidget(message_frame)
        
        # Add stretch to push messages to top
        self.preview_layout.addStretch()
        
        # Update timing info
        if len(rendered_messages) > 1:
            estimated_time = self.template.get_estimated_send_time()
            self.timing_label.setText(f"{i18n.tr('estimated_send_time')}: {estimated_time:.1f}s")
        else:
            self.timing_label.setText("")


class WhatsAppMultiMessageDialog(QDialog):
    """Dialog for creating and editing WhatsApp multi-message templates."""
    
    def __init__(self, template: Optional[WhatsAppMultiMessageTemplate] = None, parent=None):
        super().__init__(parent)
        self.template = template
        self.is_editing = template is not None
        
        self.setWindowTitle(
            i18n.tr("edit_whatsapp_template") if self.is_editing 
            else i18n.tr("create_whatsapp_template")
        )
        self.setModal(True)
        self.resize(800, 700)
        
        self.setup_ui()
        self.load_template_data()
        self.connect_signals()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Create main splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Template configuration
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Basic information
        basic_group = QGroupBox(i18n.tr("basic_information"))
        basic_layout = QFormLayout(basic_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(i18n.tr("template_name_placeholder"))
        basic_layout.addRow(i18n.tr("template_name"), self.name_edit)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["en", "es", "pt"])
        basic_layout.addRow(i18n.tr("language"), self.language_combo)
        
        left_layout.addWidget(basic_group)
        
        # Multi-message configuration
        multi_group = QGroupBox(i18n.tr("multi_message_configuration"))
        multi_layout = QVBoxLayout(multi_group)
        
        self.multi_message_checkbox = QCheckBox(i18n.tr("enable_multi_message_mode"))
        multi_layout.addWidget(self.multi_message_checkbox)
        
        # Multi-message settings (initially hidden)
        self.multi_settings_widget = QWidget()
        multi_settings_layout = QFormLayout(self.multi_settings_widget)
        
        self.split_strategy_combo = QComboBox()
        self.split_strategy_combo.addItem(i18n.tr("split_by_paragraphs"), MessageSplitStrategy.PARAGRAPH)
        self.split_strategy_combo.addItem(i18n.tr("split_by_sentences"), MessageSplitStrategy.SENTENCE)
        self.split_strategy_combo.addItem(i18n.tr("split_by_custom_delimiter"), MessageSplitStrategy.CUSTOM)
        self.split_strategy_combo.addItem(i18n.tr("manual_split"), MessageSplitStrategy.MANUAL)
        multi_settings_layout.addRow(i18n.tr("split_strategy"), self.split_strategy_combo)
        
        self.custom_delimiter_edit = QLineEdit()
        self.custom_delimiter_edit.setText("\\n\\n")
        self.custom_delimiter_edit.setPlaceholderText(i18n.tr("custom_delimiter_placeholder"))
        multi_settings_layout.addRow(i18n.tr("custom_delimiter"), self.custom_delimiter_edit)
        
        self.delay_spin = QDoubleSpinBox()
        self.delay_spin.setRange(0.1, 60.0)
        self.delay_spin.setValue(1.0)
        self.delay_spin.setSuffix(" " + i18n.tr("seconds"))
        self.delay_spin.setDecimals(1)
        multi_settings_layout.addRow(i18n.tr("delay_between_messages"), self.delay_spin)
        
        self.max_messages_spin = QSpinBox()
        self.max_messages_spin.setRange(1, 20)
        self.max_messages_spin.setValue(10)
        multi_settings_layout.addRow(i18n.tr("max_messages_per_sequence"), self.max_messages_spin)
        
        multi_layout.addWidget(self.multi_settings_widget)
        left_layout.addWidget(multi_group)
        
        # Content area
        content_group = QGroupBox(i18n.tr("template_content"))
        content_layout = QVBoxLayout(content_group)
        
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText(i18n.tr("whatsapp_content_placeholder"))
        self.content_edit.setMaximumHeight(200)
        content_layout.addWidget(self.content_edit)
        
        # Auto-split button
        auto_split_layout = QHBoxLayout()
        self.auto_split_btn = QPushButton(i18n.tr("auto_split_messages"))
        self.auto_split_btn.clicked.connect(self.auto_split_content)
        auto_split_layout.addWidget(self.auto_split_btn)
        auto_split_layout.addStretch()
        content_layout.addLayout(auto_split_layout)
        
        left_layout.addWidget(content_group)
        
        # Message sequence (for manual mode)
        self.sequence_widget = MessageSequenceWidget()
        left_layout.addWidget(self.sequence_widget)
        
        splitter.addWidget(left_panel)
        
        # Right panel - Preview
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        self.preview_widget = MessagePreviewWidget()
        right_layout.addWidget(self.preview_widget)
        
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([400, 400])
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.validate_btn = QPushButton(i18n.tr("validate_template"))
        self.validate_btn.clicked.connect(self.validate_template)
        button_layout.addWidget(self.validate_btn)
        
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton(i18n.tr("cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton(i18n.tr("save_template"))
        self.save_btn.clicked.connect(self.save_template)
        self.save_btn.setDefault(True)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
        
        # Initially hide multi-message settings
        self.multi_settings_widget.setVisible(False)
        self.sequence_widget.setVisible(False)
    
    def connect_signals(self):
        """Connect UI signals."""
        self.multi_message_checkbox.toggled.connect(self.on_multi_message_toggled)
        self.split_strategy_combo.currentTextChanged.connect(self.on_split_strategy_changed)
        self.content_edit.textChanged.connect(self.on_content_changed)
        self.sequence_widget.sequence_changed.connect(self.update_preview)
        
        # Update preview when settings change
        self.name_edit.textChanged.connect(self.update_preview)
        self.language_combo.currentTextChanged.connect(self.update_preview)
        self.delay_spin.valueChanged.connect(self.update_preview)
        self.max_messages_spin.valueChanged.connect(self.update_preview)
        self.custom_delimiter_edit.textChanged.connect(self.update_preview)
    
    def load_template_data(self):
        """Load template data if editing."""
        if not self.template:
            return
        
        self.name_edit.setText(self.template.name)
        self.language_combo.setCurrentText(self.template.language)
        self.content_edit.setPlainText(self.template.content)
        
        self.multi_message_checkbox.setChecked(self.template.multi_message_mode)
        
        # Set split strategy
        for i in range(self.split_strategy_combo.count()):
            if self.split_strategy_combo.itemData(i) == self.template.split_strategy:
                self.split_strategy_combo.setCurrentIndex(i)
                break
        
        self.custom_delimiter_edit.setText(self.template.custom_split_delimiter)
        self.delay_spin.setValue(self.template.message_delay_seconds)
        self.max_messages_spin.setValue(self.template.max_messages_per_sequence)
        
        if self.template.message_sequence:
            self.sequence_widget.set_messages(self.template.message_sequence)
        
        self.update_preview()
    
    def on_multi_message_toggled(self, checked: bool):
        """Handle multi-message mode toggle."""
        self.multi_settings_widget.setVisible(checked)
        self.auto_split_btn.setVisible(checked)
        
        # Show/hide sequence widget based on strategy
        self.on_split_strategy_changed()
        self.update_preview()
    
    def on_split_strategy_changed(self):
        """Handle split strategy change."""
        if not self.multi_message_checkbox.isChecked():
            self.sequence_widget.setVisible(False)
            self.custom_delimiter_edit.setEnabled(False)
            return
        
        strategy = self.split_strategy_combo.currentData()
        
        # Show/hide custom delimiter
        self.custom_delimiter_edit.setEnabled(strategy == MessageSplitStrategy.CUSTOM)
        
        # Show/hide sequence widget for manual mode
        self.sequence_widget.setVisible(strategy == MessageSplitStrategy.MANUAL)
        
        self.update_preview()
    
    def on_content_changed(self):
        """Handle content change."""
        # Auto-split if not in manual mode
        if (self.multi_message_checkbox.isChecked() and 
            self.split_strategy_combo.currentData() != MessageSplitStrategy.MANUAL):
            self.auto_split_content()
        else:
            self.update_preview()
    
    def auto_split_content(self):
        """Automatically split content based on current strategy."""
        if not self.multi_message_checkbox.isChecked():
            return
        
        content = self.content_edit.toPlainText().strip()
        if not content:
            return
        
        # Create temporary template to use splitting logic
        temp_template = WhatsAppMultiMessageTemplate(
            id="temp",
            name="temp",
            content=content,
            multi_message_mode=True,
            split_strategy=self.split_strategy_combo.currentData(),
            custom_split_delimiter=self.custom_delimiter_edit.text().replace('\\n', '\n'),
            max_messages_per_sequence=self.max_messages_spin.value()
        )
        
        messages = temp_template.split_into_messages()
        
        # Update sequence widget if in manual mode
        if self.split_strategy_combo.currentData() == MessageSplitStrategy.MANUAL:
            self.sequence_widget.set_messages(messages)
        
        self.update_preview()
    
    def update_preview(self):
        """Update the preview display."""
        template = self.create_template_from_ui()
        self.preview_widget.set_template(template)
    
    def create_template_from_ui(self) -> WhatsAppMultiMessageTemplate:
        """Create template object from UI values."""
        content = self.content_edit.toPlainText().strip()
        
        template = WhatsAppMultiMessageTemplate(
            id=self.template.id if self.template else f"template_{int(datetime.now().timestamp())}",
            name=self.name_edit.text().strip(),
            content=content,
            language=self.language_combo.currentText(),
            multi_message_mode=self.multi_message_checkbox.isChecked(),
            split_strategy=self.split_strategy_combo.currentData(),
            custom_split_delimiter=self.custom_delimiter_edit.text().replace('\\n', '\n'),
            message_delay_seconds=self.delay_spin.value(),
            max_messages_per_sequence=self.max_messages_spin.value()
        )
        
        # Set manual sequence if in manual mode
        if (template.multi_message_mode and 
            template.split_strategy == MessageSplitStrategy.MANUAL):
            template.message_sequence = self.sequence_widget.get_messages()
        
        return template
    
    def validate_template(self):
        """Validate the current template."""
        template = self.create_template_from_ui()
        errors = template.validate_message_sequence()
        
        if errors:
            error_text = "\n".join(f"• {error}" for error in errors)
            QMessageBox.warning(
                self,
                i18n.tr("template_validation_failed"),
                i18n.tr("template_validation_errors") + "\n\n" + error_text
            )
        else:
            QMessageBox.information(
                self,
                i18n.tr("template_validation_passed"),
                i18n.tr("template_validation_success")
            )
    
    def save_template(self):
        """Save the template."""
        # Validate required fields
        if not self.name_edit.text().strip():
            QMessageBox.warning(
                self,
                i18n.tr("missing_information"),
                i18n.tr("template_name_required")
            )
            self.name_edit.setFocus()
            return
        
        if not self.content_edit.toPlainText().strip():
            QMessageBox.warning(
                self,
                i18n.tr("missing_information"),
                i18n.tr("template_content_required")
            )
            self.content_edit.setFocus()
            return
        
        # Validate template
        template = self.create_template_from_ui()
        errors = template.validate_message_sequence()
        
        if errors:
            error_text = "\n".join(f"• {error}" for error in errors)
            reply = QMessageBox.question(
                self,
                i18n.tr("template_validation_failed"),
                i18n.tr("template_has_errors_save_anyway") + "\n\n" + error_text,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
        
        # Store the template for retrieval
        self.template = template
        self.accept()
    
    def get_template(self) -> Optional[WhatsAppMultiMessageTemplate]:
        """Get the created/edited template."""
        return self.template