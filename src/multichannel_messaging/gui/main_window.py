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
    QMessageBox, QSplitter, QFrame, QCheckBox, QComboBox
)
from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QFont, QIcon

from ..core.config_manager import ConfigManager
from ..core.csv_processor import CSVProcessor
from ..core.models import Customer, MessageTemplate, MessageChannel
from ..services.outlook_macos import OutlookMacOSService
from ..utils.logger import get_logger
from ..utils.exceptions import CSVProcessingError, OutlookIntegrationError

logger = get_logger(__name__)


class EmailSendingThread(QThread):
    """Thread for sending emails in the background."""
    
    progress_updated = Signal(int, int)  # current, total
    email_sent = Signal(str, bool, str)  # email, success, message
    finished = Signal(bool, str)  # success, message
    
    def __init__(self, customers: List[Customer], template: MessageTemplate, outlook_service: OutlookMacOSService):
        super().__init__()
        self.customers = customers
        self.template = template
        self.outlook_service = outlook_service
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
                    success = self.outlook_service.send_email(customer, self.template)
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
        self.outlook_service = None
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
        self.setWindowTitle("Multi-Channel Bulk Messaging System - Email MVP")
        self.setMinimumSize(1000, 700)
        
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
        
        self.send_btn = QPushButton("Send Emails")
        self.send_btn.clicked.connect(self.send_emails)
        self.send_btn.setEnabled(False)
        toolbar_layout.addWidget(self.send_btn)
        
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
        template_group = QGroupBox("Email Template")
        template_layout = QVBoxLayout(template_group)
        
        # Template selector (placeholder for now)
        template_selector_layout = QHBoxLayout()
        template_selector_layout.addWidget(QLabel("Template:"))
        self.template_combo = QComboBox()
        self.template_combo.addItem("Default Welcome Email")
        template_selector_layout.addWidget(self.template_combo)
        
        # Add preview button
        self.preview_btn = QPushButton("Preview Email")
        self.preview_btn.clicked.connect(self.preview_email)
        template_selector_layout.addWidget(self.preview_btn)
        
        template_layout.addLayout(template_selector_layout)
        
        # Subject field
        template_layout.addWidget(QLabel("Subject:"))
        self.subject_edit = QTextEdit()
        self.subject_edit.setMaximumHeight(60)
        template_layout.addWidget(self.subject_edit)
        
        # Content field
        template_layout.addWidget(QLabel("Content:"))
        self.content_edit = QTextEdit()
        template_layout.addWidget(self.content_edit)
        
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
        self.quota_label = QLabel("Quota: 0/100")
        self.status_bar.addPermanentWidget(self.quota_label)
    
    def setup_services(self):
        """Set up external services."""
        try:
            self.outlook_service = OutlookMacOSService()
            self.outlook_status_label.setText("Outlook: Connected")
            self.outlook_status_label.setStyleSheet("color: green;")
            logger.info("Outlook service initialized successfully")
        except Exception as e:
            self.outlook_status_label.setText("Outlook: Error")
            self.outlook_status_label.setStyleSheet("color: red;")
            logger.error(f"Failed to initialize Outlook service: {e}")
            QMessageBox.warning(
                self, 
                "Outlook Connection Error", 
                f"Failed to connect to Outlook:\n{e}\n\nPlease ensure Microsoft Outlook is installed and try again."
            )
    
    def load_default_template(self):
        """Load default email template."""
        self.current_template = MessageTemplate(
            id="default_welcome",
            name="Default Welcome Email",
            channel=MessageChannel.EMAIL,
            subject="Welcome to our service, {name}!",
            content="""Dear {name},

Thank you for your interest in our services. We're excited to have {company} as part of our community.

If you have any questions, please don't hesitate to contact us.

Best regards,
The Team""",
            variables=["name", "company"]
        )
        
        self.subject_edit.setPlainText(self.current_template.subject)
        self.content_edit.setPlainText(self.current_template.content)
    
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
    
    def update_send_button_state(self):
        """Update the send button enabled state."""
        selected_customers = self.get_selected_customers()
        has_outlook = self.outlook_service is not None
        not_sending = self.sending_thread is None or not self.sending_thread.isRunning()
        
        self.send_btn.setEnabled(len(selected_customers) > 0 and has_outlook and not_sending)
        self.update_recipients_info()
    
    def send_emails(self):
        """Start sending emails."""
        if not self.outlook_service:
            QMessageBox.warning(self, "Service Error", "Outlook service is not available.")
            return
        
        selected_customers = self.get_selected_customers()
        if not selected_customers:
            QMessageBox.information(self, "No Recipients", "Please select at least one recipient.")
            return
        
        # Update template with current content
        self.current_template.subject = self.subject_edit.toPlainText()
        self.current_template.content = self.content_edit.toPlainText()
        
        # Confirm sending
        reply = QMessageBox.question(
            self,
            "Confirm Sending",
            f"Send emails to {len(selected_customers)} recipients?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Start sending in background thread
        self.sending_thread = EmailSendingThread(selected_customers, self.current_template, self.outlook_service)
        self.sending_thread.progress_updated.connect(self.update_progress)
        self.sending_thread.email_sent.connect(self.on_email_sent)
        self.sending_thread.finished.connect(self.on_sending_finished)
        
        self.sending_thread.start()
        
        # Update UI state
        self.send_btn.setEnabled(False)
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
        self.stop_btn.setEnabled(False)
        self.progress_label.setText("Sending completed")
        
        self.log_message(f"Sending finished: {message}")
        
        if success:
            QMessageBox.information(self, "Sending Complete", message)
        else:
            QMessageBox.warning(self, "Sending Error", message)
        
        self.update_send_button_state()
    
    def preview_email(self):
        """Preview email with sample customer data."""
        if not self.customers:
            # Use sample customer data for preview
            sample_customer = Customer(
                name="John Doe",
                company="Example Corp",
                phone="+1-555-0123",
                email="john.doe@example.com"
            )
        else:
            # Use first customer from the list
            sample_customer = self.customers[0]
        
        # Update template with current content
        self.current_template.subject = self.subject_edit.toPlainText()
        self.current_template.content = self.content_edit.toPlainText()
        
        # Render template
        rendered = self.current_template.render(sample_customer)
        subject = rendered.get('subject', '')
        content = rendered.get('content', '')
        
        # Convert content to HTML for better display
        html_content = self._convert_text_to_html(content)
        
        # Create preview dialog
        preview_dialog = QMessageBox(self)
        preview_dialog.setWindowTitle("Email Preview")
        preview_dialog.setTextFormat(Qt.RichText)
        
        preview_text = f"""
        <h3>Subject:</h3>
        <p><strong>{subject}</strong></p>
        
        <h3>Content:</h3>
        <div style="border: 1px solid #ccc; padding: 10px; background-color: #f9f9f9;">
        {html_content}
        </div>
        
        <p><em>Preview using: {sample_customer.name} ({sample_customer.email})</em></p>
        """
        
        preview_dialog.setText(preview_text)
        preview_dialog.setStandardButtons(QMessageBox.Ok)
        preview_dialog.exec()
    
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
        if not self.outlook_service:
            QMessageBox.warning(self, "Service Error", "Outlook service is not initialized.")
            return
        
        try:
            success, message = self.outlook_service.test_connection()
            if success:
                QMessageBox.information(self, "Connection Test", f"Success: {message}")
                self.outlook_status_label.setText("Outlook: Connected")
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
            "About Multi-Channel Bulk Messaging System",
            """Multi-Channel Bulk Messaging System - Email MVP
            
Version 1.0.0

A cross-platform desktop application for bulk messaging through email and WhatsApp.

This MVP version focuses on email functionality using Microsoft Outlook integration.

© 2024 Multi-Channel Messaging Team"""
        )
    
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
