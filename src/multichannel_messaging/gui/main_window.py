"""
Main window for Multi-Channel Bulk Messaging System.
"""

import sys
from pathlib import Path
from typing import List, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QTextEdit, QListWidget, QListWidgetItem,
    QGroupBox, QProgressBar, QStatusBar, QMenuBar, QFileDialog,
    QMessageBox, QSplitter, QFrame, QCheckBox, QComboBox, QDialog
)
from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QFont, QIcon

from ..core.config_manager import ConfigManager
from ..core.csv_processor import CSVProcessor
from ..core.models import Customer, MessageTemplate, MessageChannel
from ..services.email_service import EmailService
from ..services.whatsapp_local_service import LocalWhatsAppBusinessService
from ..gui.whatsapp_settings_dialog import WhatsAppSettingsDialog
from ..utils.logger import get_logger
from ..utils.exceptions import CSVProcessingError, OutlookIntegrationError

logger = get_logger(__name__)


class EmailSendingThread(QThread):
    """Thread for sending emails in the background."""
    
    progress_updated = Signal(int, int)  # current, total
    email_sent = Signal(str, bool, str)  # email, success, message
    finished = Signal(bool, str)  # success, message
    
    def __init__(self, customers: List[Customer], template: MessageTemplate, email_service):
        super().__init__()
        self.customers = customers
        self.template = template
        self.email_service = email_service
        self.should_stop = False
    
    def run(self):
        """Run the email sending process."""
        try:
            successful = 0
            failed = 0
            
            for i, customer in enumerate(self.customers):
                if self.should_stop:
                    self.finished.emit(False, "Sending cancelled by user")
                    return
                
                try:
                    success = self.email_service.send_email(customer, self.template)
                    if success:
                        successful += 1
                        self.email_sent.emit(customer.email, True, "Sent successfully")
                    else:
                        failed += 1
                        self.email_sent.emit(customer.email, False, "Failed to send")
                    
                    self.progress_updated.emit(i + 1, len(self.customers))
                    
                    # Small delay between emails
                    self.msleep(1000)  # 1 second delay
                    
                except Exception as e:
                    failed += 1
                    self.email_sent.emit(customer.email, False, str(e))
                    logger.error(f"Failed to send email to {customer.email}: {e}")
            
            message = f"Completed: {successful} successful, {failed} failed"
            self.finished.emit(True, message)
            
        except Exception as e:
            self.finished.emit(False, f"Sending failed: {e}")
    
    def stop(self):
        """Stop the sending process."""
        self.should_stop = True


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.csv_processor = CSVProcessor()
        self.email_service = None
        self.whatsapp_service = LocalWhatsAppBusinessService()  # Add WhatsApp service
        self.customers: List[Customer] = []
        self.current_template: Optional[MessageTemplate] = None
        self.sending_thread: Optional[EmailSendingThread] = None
        
        self.setup_ui()
        self.setup_services()
        self.load_default_template()
        
        # Set window geometry from config
        geometry = self.config_manager.get_window_geometry()
        self.resize(geometry['width'], geometry['height'])
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("CSC-Reach - Email Communication Platform")
        self.setMinimumSize(1000, 700)
        
        # Set window icon
        self.set_window_icon()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar(main_layout)
        
        # Create main content area
        self.create_main_content(main_layout)
        
        # Create status bar
        self.create_status_bar()
    
    def create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        import_action = QAction("Import CSV...", self)
        import_action.setShortcut("Ctrl+O")
        import_action.triggered.connect(self.import_csv)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        test_outlook_action = QAction("Test Outlook Connection", self)
        test_outlook_action.triggered.connect(self.test_outlook_connection)
        tools_menu.addAction(test_outlook_action)
        
        tools_menu.addSeparator()
        
        whatsapp_settings_action = QAction("WhatsApp Settings...", self)
        whatsapp_settings_action.triggered.connect(self.show_whatsapp_settings)
        tools_menu.addAction(whatsapp_settings_action)
        
        test_whatsapp_action = QAction("Test WhatsApp Connection", self)
        test_whatsapp_action.triggered.connect(self.test_whatsapp_connection)
        tools_menu.addAction(test_whatsapp_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self, parent_layout):
        """Create the toolbar."""
        toolbar_layout = QHBoxLayout()
        
        self.import_btn = QPushButton("Import CSV")
        self.import_btn.clicked.connect(self.import_csv)
        toolbar_layout.addWidget(self.import_btn)
        
        # Channel selection
        toolbar_layout.addWidget(QLabel("Send via:"))
        self.channel_combo = QComboBox()
        self.channel_combo.addItems(["Email Only", "WhatsApp Only", "Both Channels"])
        self.channel_combo.setCurrentText("Email Only")  # Default to email for backward compatibility
        self.channel_combo.currentTextChanged.connect(self.on_channel_changed)
        toolbar_layout.addWidget(self.channel_combo)
        
        toolbar_layout.addWidget(QFrame())  # Separator
        
        self.send_btn = QPushButton("Send Messages")
        self.send_btn.clicked.connect(self.send_messages)
        self.send_btn.setEnabled(False)
        toolbar_layout.addWidget(self.send_btn)
        
        self.draft_btn = QPushButton("Create Draft")
        self.draft_btn.clicked.connect(self.create_draft)
        self.draft_btn.setEnabled(False)
        toolbar_layout.addWidget(self.draft_btn)
        
        self.stop_btn = QPushButton("Stop Sending")
        self.stop_btn.clicked.connect(self.stop_sending)
        self.stop_btn.setEnabled(False)
        toolbar_layout.addWidget(self.stop_btn)
        
        toolbar_layout.addStretch()
        
        # Status indicators
        self.outlook_status_label = QLabel("Outlook: Not Connected")
        toolbar_layout.addWidget(self.outlook_status_label)
        
        parent_layout.addLayout(toolbar_layout)
    
    def create_main_content(self, parent_layout):
        """Create the main content area."""
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Recipients
        left_panel = self.create_recipients_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Template and Status
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([400, 600])
        
        parent_layout.addWidget(splitter)
    
    def create_recipients_panel(self) -> QWidget:
        """Create the recipients panel."""
        panel = QGroupBox("Recipients")
        layout = QVBoxLayout(panel)
        
        # Recipients list
        self.recipients_list = QListWidget()
        self.recipients_list.itemChanged.connect(self.update_send_button_state)
        layout.addWidget(self.recipients_list)
        
        # Recipients info
        self.recipients_info_label = QLabel("No recipients loaded")
        layout.addWidget(self.recipients_info_label)
        
        # Select all/none buttons
        buttons_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_recipients)
        buttons_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton("Select None")
        select_none_btn.clicked.connect(self.select_no_recipients)
        buttons_layout.addWidget(select_none_btn)
        
        layout.addLayout(buttons_layout)
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Create the right panel with template and status."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Template section
        template_group = QGroupBox("Message Template")
        template_layout = QVBoxLayout(template_group)
        
        # Template selector (placeholder for now)
        template_selector_layout = QHBoxLayout()
        template_selector_layout.addWidget(QLabel("Template:"))
        self.template_combo = QComboBox()
        self.template_combo.addItem("Default Welcome Message")
        template_selector_layout.addWidget(self.template_combo)
        
        # Add preview button
        self.preview_btn = QPushButton("Preview Message")
        self.preview_btn.clicked.connect(self.preview_message)
        template_selector_layout.addWidget(self.preview_btn)
        
        template_layout.addLayout(template_selector_layout)
        
        # Email fields
        email_group = QGroupBox("Email Content")
        email_layout = QVBoxLayout(email_group)
        
        email_layout.addWidget(QLabel("Subject:"))
        self.subject_edit = QTextEdit()
        self.subject_edit.setMaximumHeight(60)
        email_layout.addWidget(self.subject_edit)
        
        email_layout.addWidget(QLabel("Email Content:"))
        self.content_edit = QTextEdit()
        self.content_edit.setMaximumHeight(200)
        email_layout.addWidget(self.content_edit)
        
        template_layout.addWidget(email_group)
        
        # WhatsApp fields
        whatsapp_group = QGroupBox("WhatsApp Content")
        whatsapp_layout = QVBoxLayout(whatsapp_group)
        
        whatsapp_layout.addWidget(QLabel("WhatsApp Message:"))
        self.whatsapp_content_edit = QTextEdit()
        self.whatsapp_content_edit.setMaximumHeight(150)
        self.whatsapp_content_edit.setPlaceholderText("Enter WhatsApp message content (leave empty to use email content)")
        whatsapp_layout.addWidget(self.whatsapp_content_edit)
        
        # Character count for WhatsApp
        self.whatsapp_char_label = QLabel("Characters: 0/4096")
        self.whatsapp_char_label.setStyleSheet("color: gray;")
        self.whatsapp_content_edit.textChanged.connect(self.update_whatsapp_char_count)
        whatsapp_layout.addWidget(self.whatsapp_char_label)
        
        template_layout.addWidget(whatsapp_group)
        
        layout.addWidget(template_group)
        
        # Progress section
        progress_group = QGroupBox("Sending Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("Ready to send")
        progress_layout.addWidget(self.progress_label)
        
        # Log area
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        progress_layout.addWidget(self.log_text)
        
        layout.addWidget(progress_group)
        
        return panel
    
    def create_status_bar(self):
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add permanent widgets to status bar
        self.email_status_label = QLabel("Email: Ready")
        self.status_bar.addPermanentWidget(self.email_status_label)
        
        self.whatsapp_status_label = QLabel("WhatsApp: Not configured")
        self.status_bar.addPermanentWidget(self.whatsapp_status_label)
        
        self.quota_label = QLabel("Quota: 0/100")
        self.status_bar.addPermanentWidget(self.quota_label)
    
    def set_window_icon(self):
        """Set the window icon."""
        try:
            # Try to find the icon file
            icon_paths = [
                # When running from source
                Path(__file__).parent.parent.parent.parent / "assets" / "icons" / "csc-reach.png",
                # When running from built app
                Path(sys.executable).parent / "assets" / "icons" / "csc-reach.png",
                # Alternative paths
                Path("assets/icons/csc-reach.png"),
                Path("../assets/icons/csc-reach.png"),
            ]
            
            for icon_path in icon_paths:
                if icon_path.exists():
                    icon = QIcon(str(icon_path))
                    if not icon.isNull():
                        self.setWindowIcon(icon)
                        logger.debug(f"Set window icon from: {icon_path}")
                        return
            
            logger.warning("Could not find application icon")
            
        except Exception as e:
            logger.warning(f"Failed to set window icon: {e}")
    
    def setup_services(self):
        """Set up external services."""
        try:
            self.email_service = EmailService()
            platform_info = self.email_service.get_platform_info()
            logger.info(f"Email service initialized successfully for {platform_info}")
        except Exception as e:
            logger.error(f"Failed to initialize email service: {e}")
            QMessageBox.warning(
                self, 
                "Outlook Connection Error", 
                f"Failed to connect to Outlook:\n{e}\n\nPlease ensure Microsoft Outlook is installed and try again."
            )
        
        # Update status display
        self.update_status_display()
    
    def load_default_template(self):
        """Load default multi-channel template."""
        self.current_template = MessageTemplate(
            id="default_welcome",
            name="Default Welcome Message",
            channels=["email", "whatsapp"],
            subject="Welcome to our service, {name}!",
            content="""Dear {name},

Thank you for your interest in our services. We're excited to have {company} as part of our community.

If you have any questions, please don't hesitate to contact us.

Best regards,
The Team""",
            whatsapp_content="""Hello {name}! 👋

Thank you for your interest in our services. We're excited to have {company} join our community!

Feel free to reach out if you have any questions.

Best regards,
The Team""",
            variables=["name", "company"]
        )
        
        self.subject_edit.setPlainText(self.current_template.subject)
        self.content_edit.setPlainText(self.current_template.content)
        self.whatsapp_content_edit.setPlainText(self.current_template.whatsapp_content)
        self.update_whatsapp_char_count()
    
    def import_csv(self):
        """Import CSV file with customer data."""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Import CSV File",
                "",
                "CSV Files (*.csv);;Text Files (*.txt);;All Files (*)"
            )
            
            if not file_path:
                return
            
            file_path = Path(file_path)
            
            # Validate CSV file
            validation = self.csv_processor.validate_csv_format(file_path)
            if not validation['valid']:
                QMessageBox.critical(
                    self,
                    "Invalid CSV File",
                    f"The selected file is not valid:\n\n" + "\n".join(validation['errors'])
                )
                return
            
            # Load customers
            customers, errors = self.csv_processor.load_customers(file_path)
            
            if errors:
                error_msg = f"Found {len(errors)} errors while processing CSV:\n\n"
                for error in errors[:5]:  # Show first 5 errors
                    error_msg += f"Row {error['row_number']}: {error['error']}\n"
                if len(errors) > 5:
                    error_msg += f"... and {len(errors) - 5} more errors"
                
                QMessageBox.warning(self, "CSV Processing Errors", error_msg)
            
            if not customers:
                QMessageBox.information(self, "No Valid Data", "No valid customer records found in the CSV file.")
                return
            
            # Update UI with loaded customers
            self.customers = customers
            self.update_recipients_list()
            self.update_send_button_state()
            
            self.status_bar.showMessage(f"Loaded {len(customers)} customers from CSV", 3000)
            self.log_message(f"Imported {len(customers)} customers from {file_path.name}")
            
        except CSVProcessingError as e:
            QMessageBox.critical(self, "CSV Processing Error", str(e))
        except Exception as e:
            logger.error(f"Failed to import CSV: {e}")
            QMessageBox.critical(self, "Import Error", f"Failed to import CSV file:\n{e}")
    
    def update_recipients_list(self):
        """Update the recipients list widget."""
        self.recipients_list.clear()
        
        for customer in self.customers:
            item = QListWidgetItem(f"{customer.name} ({customer.email})")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            item.setData(Qt.UserRole, customer)
            self.recipients_list.addItem(item)
        
        self.update_recipients_info()
    
    def update_recipients_info(self):
        """Update recipients information label."""
        total = self.recipients_list.count()
        selected = sum(1 for i in range(total) if self.recipients_list.item(i).checkState() == Qt.Checked)
        self.recipients_info_label.setText(f"Selected: {selected} of {total}")
    
    def select_all_recipients(self):
        """Select all recipients."""
        for i in range(self.recipients_list.count()):
            self.recipients_list.item(i).setCheckState(Qt.Checked)
        self.update_recipients_info()
        self.update_send_button_state()
    
    def select_no_recipients(self):
        """Deselect all recipients."""
        for i in range(self.recipients_list.count()):
            self.recipients_list.item(i).setCheckState(Qt.Unchecked)
        self.update_recipients_info()
        self.update_send_button_state()
    
    def get_selected_customers(self) -> List[Customer]:
        """Get list of selected customers."""
        selected = []
        for i in range(self.recipients_list.count()):
            item = self.recipients_list.item(i)
            if item.checkState() == Qt.Checked:
                customer = item.data(Qt.UserRole)
                selected.append(customer)
        return selected
    
    def create_draft(self):
        """Create a draft email for the first selected customer."""
        if not self.email_service:
            QMessageBox.warning(self, "Service Error", "Email service is not available.")
            return
        
        selected_customers = self.get_selected_customers()
        if not selected_customers:
            QMessageBox.information(self, "No Recipients", "Please select at least one recipient.")
            return
        
        # Use first selected customer for draft
        customer = selected_customers[0]
        
        # Update template with current content
        self.current_template.subject = self.subject_edit.toPlainText()
        self.current_template.content = self.content_edit.toPlainText()
        
        try:
            success = self.email_service.create_draft_email(customer, self.current_template)
            if success:
                QMessageBox.information(
                    self, 
                    "Draft Created", 
                    f"Draft email created for {customer.name} ({customer.email})\n\nCheck your Outlook drafts folder."
                )
                self.log_message(f"Draft email created for {customer.email}")
            else:
                QMessageBox.warning(self, "Draft Failed", "Failed to create draft email.")
        except Exception as e:
            QMessageBox.critical(self, "Draft Error", f"Failed to create draft email:\n{e}")
    
    def update_send_button_state(self):
        """Update the send button enabled state."""
        selected_customers = self.get_selected_customers()
        has_email_service = self.email_service is not None
        not_sending = self.sending_thread is None or not self.sending_thread.isRunning()
        
        self.send_btn.setEnabled(len(selected_customers) > 0 and has_email_service and not_sending)
        self.draft_btn.setEnabled(len(selected_customers) > 0 and has_email_service and not_sending)
        self.update_recipients_info()
    
    def send_emails(self):
        """Start sending emails - backward compatibility method."""
        # Set channel to email only and call new method
        self.channel_combo.setCurrentText("Email Only")
        self.send_messages()
        self.stop_btn.setEnabled(True)
        self.progress_bar.setMaximum(len(selected_customers))
        self.progress_bar.setValue(0)
        self.progress_label.setText("Sending emails...")
        
        self.log_message(f"Started sending emails to {len(selected_customers)} recipients")
    
    def stop_sending(self):
        """Stop the email sending process."""
        if self.sending_thread and self.sending_thread.isRunning():
            self.sending_thread.stop()
            self.log_message("Stopping email sending...")
    
    def update_progress(self, current: int, total: int):
        """Update progress bar."""
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"Sending emails... {current}/{total}")
    
    def on_email_sent(self, email: str, success: bool, message: str):
        """Handle individual email sent event."""
        status = "✓" if success else "✗"
        self.log_message(f"{status} {email}: {message}")
    
    def on_sending_finished(self, success: bool, message: str):
        """Handle sending finished event."""
        self.send_btn.setEnabled(True)
        self.draft_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_label.setText("Sending completed")
        
        self.log_message(f"Sending finished: {message}")
        
        if success:
            QMessageBox.information(self, "Sending Complete", message)
        else:
            QMessageBox.warning(self, "Sending Error", message)
        
        self.update_send_button_state()
    
    def preview_email(self):
        """Preview email - backward compatibility method."""
        # Set channel to email and call new preview method
        original_channel = self.channel_combo.currentText()
        self.channel_combo.setCurrentText("Email Only")
        self.preview_message()
        self.channel_combo.setCurrentText(original_channel)
        subject_label = QLabel("Subject:")
        subject_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(subject_label)
        
        subject_display = QLabel(subject)
        subject_display.setStyleSheet("padding: 5px; border: 1px solid #ccc; background-color: #f9f9f9; margin-bottom: 10px;")
        subject_display.setWordWrap(True)
        layout.addWidget(subject_display)
        
        # Content section
        content_label = QLabel("Content:")
        content_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(content_label)
        
        content_display = QTextEdit()
        content_display.setPlainText(content)
        content_display.setReadOnly(True)
        content_display.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc;
                background-color: white;
                color: black;
                padding: 10px;
                font-family: Arial, sans-serif;
                font-size: 12px;
                line-height: 1.4;
            }
        """)
        layout.addWidget(content_display)
        
        # Sample info
        info_label = QLabel(f"Preview using: {sample_customer.name} ({sample_customer.email})")
        info_label.setStyleSheet("font-style: italic; color: #666; margin-top: 10px;")
        layout.addWidget(info_label)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        
        dialog.exec()
    
    def _convert_text_to_html(self, text: str) -> str:
        """Convert plain text to HTML for display."""
        if not text:
            return ""
        
        # Escape HTML special characters
        html_text = (text
                    .replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;'))
        
        # Convert line breaks to HTML
        html_text = html_text.replace('\n\n', '</p><p>').replace('\n', '<br>')
        
        # Wrap in paragraph tags
        return f'<p>{html_text}</p>'
    
    def log_message(self, message: str):
        """Add message to log area."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def test_outlook_connection(self):
        """Test Outlook connection."""
        if not self.email_service:
            QMessageBox.warning(self, "Service Error", "Email service is not initialized.")
            return
        
        try:
            success, message = self.email_service.test_connection()
            if success:
                platform_info = self.email_service.get_platform_info()
                QMessageBox.information(self, "Connection Test", f"Success: {message}\nPlatform: {platform_info}")
                self.outlook_status_label.setText(f"Outlook: Connected ({platform_info})")
                self.outlook_status_label.setStyleSheet("color: green;")
            else:
                QMessageBox.warning(self, "Connection Test", f"Failed: {message}")
                self.outlook_status_label.setText("Outlook: Error")
                self.outlook_status_label.setStyleSheet("color: red;")
        except Exception as e:
            QMessageBox.critical(self, "Connection Test", f"Test failed: {e}")
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About CSC-Reach",
            """CSC-Reach - Email Communication Platform
            
Version 1.0.0

A cross-platform desktop application for bulk email communication through Microsoft Outlook integration.

CSC-Reach streamlines business communication processes with professional email templates, CSV data processing, and real-time sending progress.

© 2024 CSC-Reach Team"""
        )
    
    # New multi-channel methods
    def update_whatsapp_char_count(self):
        """Update WhatsApp character count display."""
        content = self.whatsapp_content_edit.toPlainText()
        char_count = len(content)
        self.whatsapp_char_label.setText(f"Characters: {char_count}/4096")
        
        if char_count > 4096:
            self.whatsapp_char_label.setStyleSheet("color: red;")
        elif char_count > 3500:
            self.whatsapp_char_label.setStyleSheet("color: orange;")
        else:
            self.whatsapp_char_label.setStyleSheet("color: gray;")
    
    def on_channel_changed(self, channel_text: str):
        """Handle channel selection change."""
        self.update_send_button_text()
        self.update_status_display()
    
    def update_send_button_text(self):
        """Update send button text based on selected channel."""
        channel = self.channel_combo.currentText()
        if channel == "Email Only":
            self.send_btn.setText("Send Emails")
        elif channel == "WhatsApp Only":
            self.send_btn.setText("Send WhatsApp")
        else:
            self.send_btn.setText("Send Messages")
    
    def update_status_display(self):
        """Update status bar based on service availability."""
        # Update email status
        if self.email_service:
            self.email_status_label.setText("Email: Ready")
            self.email_status_label.setStyleSheet("color: green;")
        else:
            self.email_status_label.setText("Email: Not ready")
            self.email_status_label.setStyleSheet("color: red;")
        
        # Update WhatsApp status
        if self.whatsapp_service.is_configured():
            self.whatsapp_status_label.setText("WhatsApp: Ready")
            self.whatsapp_status_label.setStyleSheet("color: green;")
        else:
            self.whatsapp_status_label.setText("WhatsApp: Not configured")
            self.whatsapp_status_label.setStyleSheet("color: orange;")
    
    def show_whatsapp_settings(self):
        """Show WhatsApp settings dialog."""
        dialog = WhatsAppSettingsDialog(self)
        if dialog.exec() == QDialog.Accepted:
            # Refresh WhatsApp service
            self.whatsapp_service = LocalWhatsAppBusinessService()
            self.update_status_display()
            
            if self.whatsapp_service.is_configured():
                QMessageBox.information(
                    self,
                    "WhatsApp Configured",
                    "WhatsApp Business API has been configured successfully!"
                )
    
    def test_whatsapp_connection(self):
        """Test WhatsApp connection."""
        if not self.whatsapp_service.is_configured():
            QMessageBox.warning(
                self, 
                "WhatsApp Not Configured", 
                "Please configure WhatsApp settings first.\n\nGo to Tools → WhatsApp Settings to set up your credentials."
            )
            return
        
        try:
            success, message = self.whatsapp_service.test_connection()
            if success:
                QMessageBox.information(self, "WhatsApp Connection Test", f"✅ {message}")
                self.whatsapp_status_label.setText("WhatsApp: Connected")
                self.whatsapp_status_label.setStyleSheet("color: green;")
            else:
                QMessageBox.warning(self, "WhatsApp Connection Test", f"❌ {message}")
                self.whatsapp_status_label.setText("WhatsApp: Connection failed")
                self.whatsapp_status_label.setStyleSheet("color: red;")
        except Exception as e:
            QMessageBox.critical(self, "WhatsApp Connection Test", f"Test failed: {e}")
    
    def preview_message(self):
        """Preview message for selected channel(s)."""
        if not self.customers:
            QMessageBox.warning(self, "No Recipients", "Please import a CSV file first.")
            return
        
        # Use first customer for preview
        customer = self.customers[0]
        
        # Update current template with UI content
        self.update_current_template()
        
        # Generate preview content
        rendered = self.current_template.render(customer)
        
        channel = self.channel_combo.currentText()
        preview_text = ""
        
        if channel in ["Email Only", "Both Channels"]:
            preview_text += "📧 EMAIL PREVIEW:\n"
            preview_text += f"To: {customer.email}\n"
            preview_text += f"Subject: {rendered.get('subject', '')}\n\n"
            preview_text += rendered.get('content', '')
            preview_text += "\n" + "="*50 + "\n\n"
        
        if channel in ["WhatsApp Only", "Both Channels"]:
            preview_text += "📱 WHATSAPP PREVIEW:\n"
            preview_text += f"To: {customer.phone}\n\n"
            whatsapp_content = rendered.get('whatsapp_content', rendered.get('content', ''))
            preview_text += whatsapp_content
        
        # Show preview dialog
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Message Preview")
        dialog.setText(f"Preview for: {customer.name} ({customer.company})")
        dialog.setDetailedText(preview_text)
        dialog.setStandardButtons(QMessageBox.Ok)
        dialog.exec()
    
    def update_current_template(self):
        """Update current template with UI content."""
        if self.current_template:
            self.current_template.subject = self.subject_edit.toPlainText()
            self.current_template.content = self.content_edit.toPlainText()
            self.current_template.whatsapp_content = self.whatsapp_content_edit.toPlainText()
    
    def send_messages(self):
        """Send messages via selected channel(s) - replaces send_emails."""
        selected_customers = self.get_selected_customers()
        if not selected_customers:
            QMessageBox.warning(self, "No Recipients", "Please select at least one recipient.")
            return
        
        channel = self.channel_combo.currentText()
        
        # Validate channel availability
        if channel in ["Email Only", "Both Channels"] and not self.email_service:
            QMessageBox.warning(self, "Email Service Error", "Email service is not available.")
            return
        
        if channel in ["WhatsApp Only", "Both Channels"] and not self.whatsapp_service.is_configured():
            QMessageBox.warning(
                self, 
                "WhatsApp Not Configured", 
                "Please configure WhatsApp settings first.\n\nGo to Tools → WhatsApp Settings."
            )
            return
        
        # Update template
        self.update_current_template()
        
        # Confirm sending
        channel_text = channel.lower().replace(" only", "").replace("both channels", "email and WhatsApp")
        reply = QMessageBox.question(
            self,
            "Confirm Sending",
            f"Send messages to {len(selected_customers)} recipients via {channel_text}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Start sending
        self.start_multi_channel_sending(selected_customers, channel)
    
    def start_multi_channel_sending(self, customers: List[Customer], channel: str):
        """Start multi-channel message sending."""
        # For now, use the existing email thread for email-only
        # TODO: Create a proper multi-channel sending thread
        if channel == "Email Only":
            self.start_email_sending(customers)
        elif channel == "WhatsApp Only":
            self.start_whatsapp_sending(customers)
        else:  # Both channels
            self.start_both_channels_sending(customers)
    
    def start_email_sending(self, customers: List[Customer]):
        """Start email-only sending (existing functionality)."""
        if self.sending_thread and self.sending_thread.isRunning():
            return
        
        self.sending_thread = EmailSendingThread(customers, self.current_template, self.email_service)
        self.sending_thread.progress_updated.connect(self.update_progress)
        self.sending_thread.email_sent.connect(self.on_email_sent)
        self.sending_thread.finished.connect(self.on_sending_finished)
        
        self.send_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setMaximum(len(customers))
        self.progress_bar.setValue(0)
        
        self.sending_thread.start()
    
    def start_whatsapp_sending(self, customers: List[Customer]):
        """Start WhatsApp-only sending."""
        # Simple synchronous sending for now
        # TODO: Implement proper threaded WhatsApp sending
        self.send_btn.setEnabled(False)
        self.progress_bar.setMaximum(len(customers))
        self.progress_bar.setValue(0)
        
        successful = 0
        failed = 0
        
        for i, customer in enumerate(customers):
            if not customer.phone:
                self.log_message(f"Skipping {customer.name}: No phone number")
                failed += 1
                continue
            
            success = self.whatsapp_service.send_message(customer, self.current_template)
            
            if success:
                self.log_message(f"✅ WhatsApp sent to {customer.name} ({customer.phone})")
                successful += 1
            else:
                self.log_message(f"❌ WhatsApp failed to {customer.name} ({customer.phone})")
                failed += 1
            
            self.progress_bar.setValue(i + 1)
            self.progress_label.setText(f"Sent: {successful}, Failed: {failed}")
            
            # Process events to keep UI responsive
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
        
        self.send_btn.setEnabled(True)
        self.log_message(f"WhatsApp sending completed: {successful} successful, {failed} failed")
    
    def start_both_channels_sending(self, customers: List[Customer]):
        """Start sending via both email and WhatsApp."""
        # Simple implementation - send email first, then WhatsApp
        self.log_message("Starting multi-channel sending...")
        
        # Filter customers for each channel
        email_customers = [c for c in customers if c.email]
        whatsapp_customers = [c for c in customers if c.phone and self.whatsapp_service.is_configured()]
        
        self.log_message(f"Email recipients: {len(email_customers)}, WhatsApp recipients: {len(whatsapp_customers)}")
        
        # For now, just send WhatsApp (email sending is more complex with threading)
        if whatsapp_customers:
            self.start_whatsapp_sending(whatsapp_customers)
        
        # TODO: Implement proper multi-channel threaded sending
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Save window geometry
        geometry = self.geometry()
        self.config_manager.set_window_geometry(geometry.width(), geometry.height())
        
        # Stop any running threads
        if self.sending_thread and self.sending_thread.isRunning():
            self.sending_thread.stop()
            self.sending_thread.wait(3000)  # Wait up to 3 seconds
        
        event.accept()
