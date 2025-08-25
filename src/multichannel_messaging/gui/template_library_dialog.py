"""
Template Library Dialog for managing message templates.

Provides a comprehensive interface for:
- Browsing templates by category
- Creating and editing templates
- Importing and exporting templates
- Template preview and validation
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox,
    QListWidget, QListWidgetItem, QGroupBox, QSplitter,
    QTabWidget, QWidget, QMessageBox, QFileDialog,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QMenu,
    QInputDialog, QColorDialog, QCheckBox, QSpinBox,
    QProgressBar, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPalette, QAction, QIcon

from ..core.template_manager import TemplateManager, TemplateCategory
from ..core.models import MessageTemplate, Customer
from ..core.i18n_manager import get_i18n_manager, tr
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TemplatePreviewWidget(QWidget):
    """Widget for previewing templates with sample data."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.i18n = get_i18n_manager()
        self.setup_ui()
        
        # Sample customer for preview
        self.sample_customer = Customer(
            name="John Smith",
            company="Acme Corporation",
            phone="+1-555-0123",
            email="john.smith@acme.com"
        )
        # Validate with all fields for sample data
        self.sample_customer.validate(["name", "company", "phone", "email"])
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Preview controls
        controls_layout = QHBoxLayout()
        
        self.channel_combo = QComboBox()
        self.channel_combo.addItem(self.i18n.tr("preview_email"))
        self.channel_combo.addItem(self.i18n.tr("preview_whatsapp"))
        self.channel_combo.currentTextChanged.connect(self.update_preview)
        
        controls_layout.addWidget(QLabel(self.i18n.tr("preview_channel")))
        controls_layout.addWidget(self.channel_combo)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Preview area
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(200)
        layout.addWidget(self.preview_text)
        
        # Variables info
        self.variables_label = QLabel(self.i18n.tr("variables_none"))
        self.variables_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.variables_label)
    
    def set_template(self, template: Optional[MessageTemplate]):
        """Set the template to preview."""
        self.template = template
        self.update_preview()
    
    def update_preview(self):
        """Update the preview display."""
        if not hasattr(self, 'template') or not self.template:
            self.preview_text.clear()
            self.variables_label.setText(self.i18n.tr("variables_none"))
            return
        
        try:
            # Render template with sample data
            rendered = self.template.render(self.sample_customer)
            channel = self.channel_combo.currentText().lower()
            
            preview_content = ""
            if channel == self.i18n.tr("preview_email").lower() and "email" in self.template.channels:
                if "subject" in rendered:
                    preview_content += f"{self.i18n.tr('subject')} {rendered['subject']}\n\n"
                if "content" in rendered:
                    preview_content += rendered["content"]
            elif channel == self.i18n.tr("preview_whatsapp").lower() and "whatsapp" in self.template.channels:
                if "whatsapp_content" in rendered:
                    preview_content = rendered["whatsapp_content"]
            
            self.preview_text.setPlainText(preview_content)
            
            # Update variables info
            if self.template.variables:
                vars_text = self.i18n.tr("variables_list", variables=', '.join(self.template.variables))
            else:
                vars_text = self.i18n.tr("variables_none")
            self.variables_label.setText(vars_text)
            
        except Exception as e:
            error_text = self.i18n.tr("preview_error", error=str(e))
            self.preview_text.setPlainText(error_text)
            logger.error(f"Template preview error: {e}")


class TemplateEditDialog(QDialog):
    """Dialog for creating and editing templates."""
    
    def __init__(self, template_manager: TemplateManager, template: MessageTemplate = None, parent=None):
        super().__init__(parent)
        self.template_manager = template_manager
        self.template = template
        self.is_editing = template is not None
        self.i18n = get_i18n_manager()
        
        title = self.i18n.tr("edit_template_title") if self.is_editing else self.i18n.tr("new_template_title")
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(600, 500)
        
        self.setup_ui()
        if self.is_editing:
            self.load_template_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Basic info
        info_group = QGroupBox(self.i18n.tr("template_information"))
        info_layout = QGridLayout(info_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(self.i18n.tr("template_name_placeholder"))
        info_layout.addWidget(QLabel(self.i18n.tr("template_name")), 0, 0)
        info_layout.addWidget(self.name_edit, 0, 1)
        
        self.category_combo = QComboBox()
        self.load_categories()
        info_layout.addWidget(QLabel(self.i18n.tr("template_category")), 1, 0)
        info_layout.addWidget(self.category_combo, 1, 1)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText(self.i18n.tr("template_description_placeholder"))
        info_layout.addWidget(QLabel(self.i18n.tr("template_description")), 2, 0)
        info_layout.addWidget(self.description_edit, 2, 1)
        
        layout.addWidget(info_group)
        
        # Channels
        channels_group = QGroupBox(self.i18n.tr("supported_channels"))
        channels_layout = QHBoxLayout(channels_group)
        
        self.email_check = QCheckBox(self.i18n.tr("channel_email"))
        self.email_check.setChecked(True)
        self.email_check.toggled.connect(self.on_channel_changed)
        
        self.whatsapp_check = QCheckBox(self.i18n.tr("channel_whatsapp"))
        self.whatsapp_check.toggled.connect(self.on_channel_changed)
        
        channels_layout.addWidget(self.email_check)
        channels_layout.addWidget(self.whatsapp_check)
        channels_layout.addStretch()
        
        layout.addWidget(channels_group)
        
        # Content tabs
        self.content_tabs = QTabWidget()
        
        # Email tab
        email_tab = QWidget()
        email_layout = QVBoxLayout(email_tab)
        
        email_layout.addWidget(QLabel(self.i18n.tr("subject")))
        self.subject_edit = QLineEdit()
        self.subject_edit.setPlaceholderText(self.i18n.tr("email_subject_placeholder"))
        email_layout.addWidget(self.subject_edit)
        
        email_layout.addWidget(QLabel(self.i18n.tr("content")))
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText(self.i18n.tr("email_content_placeholder"))
        email_layout.addWidget(self.content_edit)
        
        self.content_tabs.addTab(email_tab, self.i18n.tr("channel_email"))
        
        # WhatsApp tab
        whatsapp_tab = QWidget()
        whatsapp_layout = QVBoxLayout(whatsapp_tab)
        
        whatsapp_layout.addWidget(QLabel(self.i18n.tr("whatsapp_message")))
        self.whatsapp_edit = QTextEdit()
        self.whatsapp_edit.setPlaceholderText(self.i18n.tr("whatsapp_content_placeholder"))
        self.whatsapp_edit.setMaximumHeight(150)
        whatsapp_layout.addWidget(self.whatsapp_edit)
        
        # Character count
        self.char_count_label = QLabel(self.i18n.tr("whatsapp_char_limit", count=0))
        self.char_count_label.setStyleSheet("color: #666; font-size: 11px;")
        self.whatsapp_edit.textChanged.connect(self.update_char_count)
        whatsapp_layout.addWidget(self.char_count_label)
        
        whatsapp_layout.addStretch()
        self.content_tabs.addTab(whatsapp_tab, self.i18n.tr("channel_whatsapp"))
        
        layout.addWidget(self.content_tabs)
        
        # Preview
        preview_group = QGroupBox(self.i18n.tr("template_preview"))
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_widget = TemplatePreviewWidget()
        preview_layout.addWidget(self.preview_widget)
        
        # Auto-update preview
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.update_preview)
        
        # Connect text changes to preview update
        for widget in [self.name_edit, self.subject_edit, self.content_edit, self.whatsapp_edit]:
            if hasattr(widget, 'textChanged'):
                widget.textChanged.connect(lambda: self.preview_timer.start(500))
        
        layout.addWidget(preview_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton(self.i18n.tr("save_template"))
        self.save_btn.clicked.connect(self.save_template)
        
        self.cancel_btn = QPushButton(self.i18n.tr("cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.save_btn)
        
        layout.addLayout(buttons_layout)
        
        # Initial state
        self.on_channel_changed()
    
    def load_categories(self):
        """Load categories into combo box."""
        self.category_combo.clear()
        categories = self.template_manager.get_categories()
        for category in categories:
            self.category_combo.addItem(category.name, category.id)
    
    def load_template_data(self):
        """Load existing template data into form."""
        if not self.template:
            return
        
        self.name_edit.setText(self.template.name)
        self.subject_edit.setText(self.template.subject)
        self.content_edit.setPlainText(self.template.content)
        self.whatsapp_edit.setPlainText(self.template.whatsapp_content)
        
        # Set channels
        self.email_check.setChecked("email" in self.template.channels)
        self.whatsapp_check.setChecked("whatsapp" in self.template.channels)
        
        # Set category
        metadata = self.template_manager.get_template_metadata(self.template.id)
        category_id = metadata.get("category_id", "general")
        for i in range(self.category_combo.count()):
            if self.category_combo.itemData(i) == category_id:
                self.category_combo.setCurrentIndex(i)
                break
        
        self.description_edit.setText(metadata.get("description", ""))
        
        self.update_char_count()
        self.update_preview()
    
    def on_channel_changed(self):
        """Handle channel selection changes."""
        email_enabled = self.email_check.isChecked()
        whatsapp_enabled = self.whatsapp_check.isChecked()
        
        # Enable/disable tabs
        self.content_tabs.setTabEnabled(0, email_enabled)  # Email tab
        self.content_tabs.setTabEnabled(1, whatsapp_enabled)  # WhatsApp tab
        
        # Switch to enabled tab if current is disabled
        current_tab = self.content_tabs.currentIndex()
        if (current_tab == 0 and not email_enabled) or (current_tab == 1 and not whatsapp_enabled):
            if email_enabled:
                self.content_tabs.setCurrentIndex(0)
            elif whatsapp_enabled:
                self.content_tabs.setCurrentIndex(1)
        
        self.update_preview()
    
    def update_char_count(self):
        """Update WhatsApp character count."""
        text = self.whatsapp_edit.toPlainText()
        count = len(text)
        self.char_count_label.setText(self.i18n.tr("whatsapp_char_limit", count=count))
        
        # Color coding for WhatsApp limits
        if count > 4096:  # WhatsApp limit
            self.char_count_label.setStyleSheet("color: red; font-size: 11px;")
        elif count > 3500:  # Warning threshold
            self.char_count_label.setStyleSheet("color: orange; font-size: 11px;")
        else:
            self.char_count_label.setStyleSheet("color: #666; font-size: 11px;")
    
    def update_preview(self):
        """Update template preview."""
        try:
            # Create temporary template for preview
            channels = []
            if self.email_check.isChecked():
                channels.append("email")
            if self.whatsapp_check.isChecked():
                channels.append("whatsapp")
            
            if not channels:
                self.preview_widget.set_template(None)
                return
            
            temp_template = MessageTemplate(
                id="preview",
                name=self.name_edit.text() or "Preview Template",
                channels=channels,
                subject=self.subject_edit.text(),
                content=self.content_edit.toPlainText(),
                whatsapp_content=self.whatsapp_edit.toPlainText()
            )
            
            self.preview_widget.set_template(temp_template)
            
        except Exception as e:
            logger.error(f"Preview update error: {e}")
    
    def save_template(self):
        """Save the template."""
        try:
            # Validate input
            name = self.name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, tr("validation_error"), tr("template_name_required"))
                return
            
            channels = []
            if self.email_check.isChecked():
                channels.append("email")
            if self.whatsapp_check.isChecked():
                channels.append("whatsapp")
            
            if not channels:
                QMessageBox.warning(self, tr("validation_error"), tr("channel_required"))
                return
            
            # Email validation
            if "email" in channels:
                if not self.subject_edit.text().strip():
                    QMessageBox.warning(self, tr("validation_error"), tr("email_subject_required"))
                    return
                if not self.content_edit.toPlainText().strip():
                    QMessageBox.warning(self, tr("validation_error"), tr("email_content_required"))
                    return
            
            # WhatsApp validation
            if "whatsapp" in channels:
                if not self.whatsapp_edit.toPlainText().strip():
                    QMessageBox.warning(self, tr("validation_error"), tr("whatsapp_content_required"))
                    return
            
            # Create or update template
            if self.is_editing:
                template_id = self.template.id
            else:
                # Generate ID from name
                template_id = name.lower().replace(" ", "_").replace("-", "_")
                template_id = "".join(c for c in template_id if c.isalnum() or c == "_")
                
                # Ensure unique ID
                counter = 1
                original_id = template_id
                while self.template_manager.get_template(template_id):
                    template_id = f"{original_id}_{counter}"
                    counter += 1
            
            template = MessageTemplate(
                id=template_id,
                name=name,
                channels=channels,
                subject=self.subject_edit.text(),
                content=self.content_edit.toPlainText(),
                whatsapp_content=self.whatsapp_edit.toPlainText()
            )
            
            # Get category and description
            category_id = self.category_combo.currentData() or "general"
            description = self.description_edit.text().strip()
            
            # Save template
            if self.template_manager.save_template(template, category_id, description):
                QMessageBox.information(self, tr("success"), tr("template_saved_success", name=name))
                self.accept()
            else:
                QMessageBox.critical(self, tr("error"), tr("template_save_failed"))
                
        except Exception as e:
            logger.error(f"Template save error: {e}")
            QMessageBox.critical(self, tr("error"), tr("template_save_failed") + f": {str(e)}")


class TemplateLibraryDialog(QDialog):
    """Main template library dialog."""
    
    template_selected = Signal(MessageTemplate)
    
    def __init__(self, template_manager: TemplateManager, parent=None):
        super().__init__(parent)
        self.template_manager = template_manager
        
        self.setWindowTitle("Template Library")
        self.setModal(True)
        self.resize(900, 600)
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        # Search
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search templates...")
        self.search_edit.textChanged.connect(self.filter_templates)
        toolbar_layout.addWidget(self.search_edit)
        
        # Category filter
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories", None)
        self.category_filter.currentTextChanged.connect(self.filter_templates)
        toolbar_layout.addWidget(self.category_filter)
        
        toolbar_layout.addStretch()
        
        # Action buttons
        self.new_btn = QPushButton("New Template")
        self.new_btn.clicked.connect(self.new_template)
        
        self.import_btn = QPushButton("Import")
        self.import_btn.clicked.connect(self.import_template)
        
        self.export_btn = QPushButton("Export All")
        self.export_btn.clicked.connect(self.export_all_templates)
        
        toolbar_layout.addWidget(self.new_btn)
        toolbar_layout.addWidget(self.import_btn)
        toolbar_layout.addWidget(self.export_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Main content
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Template list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        self.template_tree = QTreeWidget()
        self.template_tree.setHeaderLabels(["Name", "Category", "Channels", "Updated"])
        self.template_tree.itemSelectionChanged.connect(self.on_template_selected)
        self.template_tree.itemDoubleClicked.connect(self.edit_template)
        
        # Context menu
        self.template_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.template_tree.customContextMenuRequested.connect(self.show_context_menu)
        
        left_layout.addWidget(self.template_tree)
        splitter.addWidget(left_panel)
        
        # Right panel - Preview and details
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Template details
        details_group = QGroupBox("Template Details")
        details_layout = QVBoxLayout(details_group)
        
        self.details_label = QLabel("Select a template to view details")
        self.details_label.setWordWrap(True)
        details_layout.addWidget(self.details_label)
        
        right_layout.addWidget(details_group)
        
        # Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_widget = TemplatePreviewWidget()
        preview_layout.addWidget(self.preview_widget)
        
        right_layout.addWidget(preview_group)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 500])
        
        layout.addWidget(splitter)
        
        # Bottom buttons
        buttons_layout = QHBoxLayout()
        
        self.use_btn = QPushButton("Use Template")
        self.use_btn.clicked.connect(self.use_template)
        self.use_btn.setEnabled(False)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.use_btn)
        buttons_layout.addWidget(self.close_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_data(self):
        """Load templates and categories."""
        # Load categories
        self.category_filter.clear()
        self.category_filter.addItem("All Categories", None)
        
        categories = self.template_manager.get_categories()
        for category in categories:
            self.category_filter.addItem(category.name, category.id)
        
        # Load templates
        self.refresh_templates()
    
    def refresh_templates(self):
        """Refresh the template list."""
        self.template_tree.clear()
        
        templates = self.template_manager.get_templates()
        
        for template in templates:
            metadata = self.template_manager.get_template_metadata(template.id)
            category_id = metadata.get("category_id", "general")
            category = self.template_manager.get_category(category_id)
            category_name = category.name if category else "General"
            
            channels_text = ", ".join(template.channels).title()
            updated_text = template.updated_at.strftime("%Y-%m-%d")
            
            item = QTreeWidgetItem([
                template.name,
                category_name,
                channels_text,
                updated_text
            ])
            item.setData(0, Qt.UserRole, template)
            
            self.template_tree.addTopLevelItem(item)
        
        # Resize columns
        header = self.template_tree.header()
        header.resizeSection(0, 200)  # Name
        header.resizeSection(1, 100)  # Category
        header.resizeSection(2, 100)  # Channels
        header.setStretchLastSection(True)
    
    def filter_templates(self):
        """Filter templates based on search and category."""
        search_text = self.search_edit.text().lower()
        category_id = self.category_filter.currentData()
        
        for i in range(self.template_tree.topLevelItemCount()):
            item = self.template_tree.topLevelItem(i)
            template = item.data(0, Qt.UserRole)
            
            # Check search filter
            search_match = True
            if search_text:
                searchable = f"{template.name} {template.subject} {template.content}".lower()
                search_match = search_text in searchable
            
            # Check category filter
            category_match = True
            if category_id:
                metadata = self.template_manager.get_template_metadata(template.id)
                template_category = metadata.get("category_id", "general")
                category_match = template_category == category_id
            
            item.setHidden(not (search_match and category_match))
    
    def on_template_selected(self):
        """Handle template selection."""
        items = self.template_tree.selectedItems()
        if not items:
            self.details_label.setText("Select a template to view details")
            self.preview_widget.set_template(None)
            self.use_btn.setEnabled(False)
            return
        
        template = items[0].data(0, Qt.UserRole)
        metadata = self.template_manager.get_template_metadata(template.id)
        
        # Update details
        details_text = f"""
<b>Name:</b> {template.name}<br>
<b>Channels:</b> {', '.join(template.channels).title()}<br>
<b>Language:</b> {template.language.upper()}<br>
<b>Variables:</b> {', '.join(template.variables) if template.variables else 'None'}<br>
<b>Created:</b> {template.created_at.strftime('%Y-%m-%d %H:%M')}<br>
<b>Updated:</b> {template.updated_at.strftime('%Y-%m-%d %H:%M')}<br>
<b>Usage Count:</b> {metadata.get('usage_count', 0)}<br>
"""
        
        if metadata.get("description"):
            details_text += f"<b>Description:</b> {metadata['description']}<br>"
        
        self.details_label.setText(details_text)
        
        # Update preview
        self.preview_widget.set_template(template)
        self.use_btn.setEnabled(True)
    
    def show_context_menu(self, position):
        """Show context menu for template operations."""
        item = self.template_tree.itemAt(position)
        if not item:
            return
        
        template = item.data(0, Qt.UserRole)
        
        menu = QMenu(self)
        
        edit_action = menu.addAction("Edit Template")
        edit_action.triggered.connect(lambda: self.edit_template(item))
        
        duplicate_action = menu.addAction("Duplicate Template")
        duplicate_action.triggered.connect(lambda: self.duplicate_template(template))
        
        export_action = menu.addAction("Export Template")
        export_action.triggered.connect(lambda: self.export_template(template))
        
        menu.addSeparator()
        
        delete_action = menu.addAction("Delete Template")
        delete_action.triggered.connect(lambda: self.delete_template(template))
        
        menu.exec(self.template_tree.mapToGlobal(position))
    
    def new_template(self):
        """Create a new template."""
        dialog = TemplateEditDialog(self.template_manager, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_templates()
    
    def edit_template(self, item=None):
        """Edit selected template."""
        if item is None:
            items = self.template_tree.selectedItems()
            if not items:
                return
            item = items[0]
        
        template = item.data(0, Qt.UserRole)
        dialog = TemplateEditDialog(self.template_manager, template, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_templates()
    
    def duplicate_template(self, template: MessageTemplate):
        """Duplicate a template."""
        new_name, ok = QInputDialog.getText(
            self, "Duplicate Template", 
            f"Enter name for duplicate of '{template.name}':",
            text=f"{template.name} (Copy)"
        )
        
        if ok and new_name.strip():
            duplicate = self.template_manager.duplicate_template(template.id, new_name.strip())
            if duplicate:
                QMessageBox.information(self, tr("success"), tr("template_duplicated_success", name=new_name))
                self.refresh_templates()
            else:
                QMessageBox.critical(self, tr("error"), tr("template_duplicate_failed"))
    
    def delete_template(self, template: MessageTemplate):
        """Delete a template."""
        reply = QMessageBox.question(
            self, tr("delete_template"),
            tr("confirm_delete_template", name=template.name),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.template_manager.delete_template(template.id):
                QMessageBox.information(self, tr("success"), tr("template_deleted_success"))
                self.refresh_templates()
            else:
                QMessageBox.critical(self, tr("error"), tr("template_delete_failed"))
    
    def export_template(self, template: MessageTemplate):
        """Export a single template."""
        filename, _ = QFileDialog.getSaveFileName(
            self, tr("export_template"),
            f"{template.name.replace(' ', '_')}_template.json",
            tr("json_files")
        )
        
        if filename:
            export_path = self.template_manager.export_template(template.id, Path(filename))
            if export_path:
                QMessageBox.information(self, tr("success"), tr("template_exported_success", path=filename))
            else:
                QMessageBox.critical(self, tr("error"), tr("template_export_failed"))
    
    def import_template(self):
        """Import a template from file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, tr("import_template"),
            "", tr("json_files")
        )
        
        if filename:
            template = self.template_manager.import_template(Path(filename))
            if template:
                QMessageBox.information(self, tr("success"), tr("template_imported_success", name=template.name))
                self.refresh_templates()
            else:
                QMessageBox.critical(self, tr("error"), tr("template_import_failed"))
    
    def export_all_templates(self):
        """Export all templates."""
        filename, _ = QFileDialog.getSaveFileName(
            self, tr("export_all_templates"),
            f"all_templates_{datetime.now().strftime('%Y%m%d')}.json",
            tr("json_files")
        )
        
        if filename:
            export_path = self.template_manager.export_all_templates(Path(filename))
            if export_path:
                QMessageBox.information(self, tr("success"), tr("templates_exported_success", path=filename))
            else:
                QMessageBox.critical(self, tr("error"), tr("templates_export_failed"))
    
    def use_template(self):
        """Use the selected template."""
        items = self.template_tree.selectedItems()
        if not items:
            return
        
        template = items[0].data(0, Qt.UserRole)
        
        # Increment usage count
        self.template_manager.increment_template_usage(template.id)
        
        # Emit signal and close
        self.template_selected.emit(template)
        self.accept()
