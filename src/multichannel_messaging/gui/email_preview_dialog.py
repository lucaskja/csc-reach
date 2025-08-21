"""
Email preview dialog with multi-device format simulation and composition features.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QTextEdit,
    QLabel, QPushButton, QComboBox, QGroupBox, QListWidget, QListWidgetItem,
    QSplitter, QFrame, QScrollArea, QGridLayout, QProgressBar, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap, QPalette
from PySide6.QtWebEngineWidgets import QWebEngineView
from typing import Dict, List, Optional, Any
import html

from ..core.models import Customer, MessageTemplate
from ..core.email_composer import EmailComposer, EmailComposition, EmailFormat, DeviceType
from ..core.i18n_manager import get_i18n_manager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class EmailPreviewDialog(QDialog):
    """Advanced email preview dialog with multi-device simulation."""
    
    # Signals
    send_requested = Signal(EmailComposition)
    draft_requested = Signal(EmailComposition)
    
    def __init__(self, parent=None):
        """Initialize the email preview dialog."""
        super().__init__(parent)
        self.i18n_manager = get_i18n_manager()
        self.email_composer = EmailComposer()
        
        # Current state
        self.current_composition = None
        self.current_customer = None
        self.current_template = None
        
        self._setup_ui()
        self._connect_signals()
        self._apply_styles()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle(self.i18n_manager.tr("email_preview_title"))
        self.setModal(True)
        self.resize(1000, 700)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Top toolbar
        toolbar_layout = self._create_toolbar()
        main_layout.addLayout(toolbar_layout)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Preview options and stats
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Preview area
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([300, 700])
        
        # Bottom buttons
        button_layout = self._create_button_layout()
        main_layout.addLayout(button_layout)
    
    def _create_toolbar(self) -> QHBoxLayout:
        """Create the top toolbar."""
        layout = QHBoxLayout()
        
        # Device type selector
        device_label = QLabel(self.i18n_manager.tr("preview_device_type"))
        self.device_combo = QComboBox()
        self.device_combo.addItems([
            self.i18n_manager.tr("device_desktop"),
            self.i18n_manager.tr("device_tablet"),
            self.i18n_manager.tr("device_mobile")
        ])
        
        # Format selector
        format_label = QLabel(self.i18n_manager.tr("email_format"))
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            self.i18n_manager.tr("format_plain_text"),
            self.i18n_manager.tr("format_html")
        ])
        
        # Refresh button
        self.refresh_btn = QPushButton(self.i18n_manager.tr("refresh_preview"))
        
        layout.addWidget(device_label)
        layout.addWidget(self.device_combo)
        layout.addSpacing(20)
        layout.addWidget(format_label)
        layout.addWidget(self.format_combo)
        layout.addSpacing(20)
        layout.addWidget(self.refresh_btn)
        layout.addStretch()
        
        return layout
    
    def _create_left_panel(self) -> QWidget:
        """Create the left panel with options and statistics."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Email information group
        info_group = QGroupBox(self.i18n_manager.tr("email_information"))
        info_layout = QGridLayout(info_group)
        
        self.to_label = QLabel()
        self.subject_label = QLabel()
        self.format_label = QLabel()
        
        info_layout.addWidget(QLabel(self.i18n_manager.tr("to_address")), 0, 0)
        info_layout.addWidget(self.to_label, 0, 1)
        info_layout.addWidget(QLabel(self.i18n_manager.tr("subject")), 1, 0)
        info_layout.addWidget(self.subject_label, 1, 1)
        info_layout.addWidget(QLabel(self.i18n_manager.tr("format")), 2, 0)
        info_layout.addWidget(self.format_label, 2, 1)
        
        layout.addWidget(info_group)
        
        # Statistics group
        stats_group = QGroupBox(self.i18n_manager.tr("email_statistics"))
        stats_layout = QGridLayout(stats_group)
        
        self.char_count_label = QLabel()
        self.word_count_label = QLabel()
        self.size_label = QLabel()
        self.attachment_count_label = QLabel()
        
        stats_layout.addWidget(QLabel(self.i18n_manager.tr("character_count")), 0, 0)
        stats_layout.addWidget(self.char_count_label, 0, 1)
        stats_layout.addWidget(QLabel(self.i18n_manager.tr("word_count")), 1, 0)
        stats_layout.addWidget(self.word_count_label, 1, 1)
        stats_layout.addWidget(QLabel(self.i18n_manager.tr("estimated_size")), 2, 0)
        stats_layout.addWidget(self.size_label, 2, 1)
        stats_layout.addWidget(QLabel(self.i18n_manager.tr("attachments")), 3, 0)
        stats_layout.addWidget(self.attachment_count_label, 3, 1)
        
        layout.addWidget(stats_group)
        
        # Attachments list
        attachments_group = QGroupBox(self.i18n_manager.tr("attachments"))
        attachments_layout = QVBoxLayout(attachments_group)
        
        self.attachments_list = QListWidget()
        attachments_layout.addWidget(self.attachments_list)
        
        layout.addWidget(attachments_group)
        
        # Validation results
        validation_group = QGroupBox(self.i18n_manager.tr("validation_results"))
        validation_layout = QVBoxLayout(validation_group)
        
        self.validation_list = QListWidget()
        validation_layout.addWidget(self.validation_list)
        
        layout.addWidget(validation_group)
        
        layout.addStretch()
        return panel
    
    def _create_right_panel(self) -> QWidget:
        """Create the right panel with preview area."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Preview tabs
        self.preview_tabs = QTabWidget()
        
        # Plain text preview
        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        self.text_preview.setFont(QFont("Courier", 10))
        self.preview_tabs.addTab(self.text_preview, self.i18n_manager.tr("plain_text_preview"))
        
        # HTML preview
        self.html_preview = QWebEngineView()
        self.preview_tabs.addTab(self.html_preview, self.i18n_manager.tr("html_preview"))
        
        # Raw HTML source
        self.html_source = QTextEdit()
        self.html_source.setReadOnly(True)
        self.html_source.setFont(QFont("Courier", 9))
        self.preview_tabs.addTab(self.html_source, self.i18n_manager.tr("html_source"))
        
        layout.addWidget(self.preview_tabs)
        
        return panel
    
    def _create_button_layout(self) -> QHBoxLayout:
        """Create the bottom button layout."""
        layout = QHBoxLayout()
        
        # Validation status
        self.validation_status = QLabel()
        layout.addWidget(self.validation_status)
        
        layout.addStretch()
        
        # Action buttons
        self.create_draft_btn = QPushButton(self.i18n_manager.tr("create_draft"))
        self.send_email_btn = QPushButton(self.i18n_manager.tr("send_email"))
        self.close_btn = QPushButton(self.i18n_manager.tr("close"))
        
        layout.addWidget(self.create_draft_btn)
        layout.addWidget(self.send_email_btn)
        layout.addWidget(self.close_btn)
        
        return layout
    
    def _connect_signals(self) -> None:
        """Connect UI signals."""
        self.device_combo.currentTextChanged.connect(self._on_device_changed)
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        self.refresh_btn.clicked.connect(self._refresh_preview)
        
        self.create_draft_btn.clicked.connect(self._on_create_draft)
        self.send_email_btn.clicked.connect(self._on_send_email)
        self.close_btn.clicked.connect(self.close)
    
    def _apply_styles(self) -> None:
        """Apply custom styles to the dialog."""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 3px;
                background-color: #fafafa;
            }
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 3px;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                border: 1px solid #cccccc;
                background-color: #f0f0f0;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
    
    def preview_email(
        self,
        customer: Customer,
        template: MessageTemplate,
        attachments: Optional[List[str]] = None,
        custom_variables: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Preview an email composition.
        
        Args:
            customer: Customer information
            template: Email template
            attachments: Optional list of attachment paths
            custom_variables: Optional custom variables
        """
        try:
            self.current_customer = customer
            self.current_template = template
            
            # Get current format selection
            format_type = EmailFormat.HTML if self.format_combo.currentIndex() == 1 else EmailFormat.PLAIN_TEXT
            
            # Compose email
            self.current_composition = self.email_composer.compose_email(
                customer=customer,
                template=template,
                format_type=format_type,
                attachments=attachments,
                custom_variables=custom_variables
            )
            
            # Update UI
            self._update_preview()
            
            logger.info(f"Email preview generated for {customer.email}")
            
        except Exception as e:
            logger.error(f"Failed to generate email preview: {e}")
            self._show_error(f"Preview generation failed: {e}")
    
    def _update_preview(self) -> None:
        """Update the preview display."""
        if not self.current_composition:
            return
        
        try:
            # Update information panel
            self._update_info_panel()
            
            # Update statistics
            self._update_statistics()
            
            # Update attachments list
            self._update_attachments_list()
            
            # Update validation results
            self._update_validation_results()
            
            # Update preview content
            self._update_preview_content()
            
        except Exception as e:
            logger.error(f"Failed to update preview: {e}")
    
    def _update_info_panel(self) -> None:
        """Update the information panel."""
        comp = self.current_composition
        
        self.to_label.setText(comp.to_address)
        self.subject_label.setText(comp.subject)
        self.format_label.setText(comp.format_type.value.upper())
    
    def _update_statistics(self) -> None:
        """Update the statistics display."""
        stats = self.email_composer.get_composition_stats(self.current_composition)
        
        self.char_count_label.setText(str(stats['character_count']))
        self.word_count_label.setText(str(stats['word_count']))
        self.size_label.setText(f"{stats['estimated_size_kb']:.1f} KB")
        self.attachment_count_label.setText(f"{stats['valid_attachments']}/{stats['attachment_count']}")
    
    def _update_attachments_list(self) -> None:
        """Update the attachments list."""
        self.attachments_list.clear()
        
        for attachment in self.current_composition.attachments:
            item_text = f"{attachment.display_name} ({attachment.size_bytes / 1024:.1f} KB)"
            if not attachment.is_valid:
                item_text += f" - ERROR: {attachment.error_message}"
            
            item = QListWidgetItem(item_text)
            if not attachment.is_valid:
                item.setForeground(Qt.red)
            
            self.attachments_list.addItem(item)
    
    def _update_validation_results(self) -> None:
        """Update the validation results."""
        self.validation_list.clear()
        
        if self.current_composition.is_valid():
            item = QListWidgetItem(self.i18n_manager.tr("validation_passed"))
            item.setForeground(Qt.green)
            self.validation_list.addItem(item)
            
            self.validation_status.setText(self.i18n_manager.tr("email_valid"))
            self.validation_status.setStyleSheet("color: green; font-weight: bold;")
            self.send_email_btn.setEnabled(True)
        else:
            for error in self.current_composition.validation_errors:
                item = QListWidgetItem(error)
                item.setForeground(Qt.red)
                self.validation_list.addItem(item)
            
            self.validation_status.setText(self.i18n_manager.tr("email_invalid"))
            self.validation_status.setStyleSheet("color: red; font-weight: bold;")
            self.send_email_btn.setEnabled(False)
    
    def _update_preview_content(self) -> None:
        """Update the preview content based on current settings."""
        # Get device type
        device_map = {
            0: DeviceType.DESKTOP,
            1: DeviceType.TABLET,
            2: DeviceType.MOBILE
        }
        device_type = device_map.get(self.device_combo.currentIndex(), DeviceType.DESKTOP)
        
        # Create preview
        preview = self.email_composer.create_preview(self.current_composition, device_type)
        
        # Update plain text preview
        self.text_preview.setPlainText(preview['content'])
        
        # Update HTML preview if available
        if preview.get('html_content'):
            self.html_preview.setHtml(preview['html_content'])
            self.html_source.setPlainText(preview['html_content'])
        else:
            # Show plain text in HTML preview as well
            simple_html = f"<pre>{html.escape(preview['content'])}</pre>"
            self.html_preview.setHtml(simple_html)
            self.html_source.setPlainText(simple_html)
    
    def _on_device_changed(self) -> None:
        """Handle device type change."""
        self._update_preview_content()
    
    def _on_format_changed(self) -> None:
        """Handle format change."""
        if self.current_customer and self.current_template:
            # Regenerate composition with new format
            format_type = EmailFormat.HTML if self.format_combo.currentIndex() == 1 else EmailFormat.PLAIN_TEXT
            
            self.current_composition = self.email_composer.compose_email(
                customer=self.current_customer,
                template=self.current_template,
                format_type=format_type,
                attachments=[att.file_path for att in self.current_composition.attachments] if self.current_composition.attachments else None
            )
            
            self._update_preview()
    
    def _refresh_preview(self) -> None:
        """Refresh the preview."""
        if self.current_customer and self.current_template:
            self.preview_email(self.current_customer, self.current_template)
    
    def _on_create_draft(self) -> None:
        """Handle create draft button click."""
        if self.current_composition:
            self.draft_requested.emit(self.current_composition)
    
    def _on_send_email(self) -> None:
        """Handle send email button click."""
        if self.current_composition and self.current_composition.is_valid():
            self.send_requested.emit(self.current_composition)
    
    def _show_error(self, message: str) -> None:
        """Show error message in the preview area."""
        self.text_preview.setPlainText(f"ERROR: {message}")
        self.html_preview.setHtml(f"<h3 style='color: red;'>ERROR</h3><p>{message}</p>")
        self.html_source.setPlainText("")