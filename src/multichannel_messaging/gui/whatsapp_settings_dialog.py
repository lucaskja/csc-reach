"""
WhatsApp Business API settings dialog for CSC-Reach.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton, QLabel,
    QTextEdit, QMessageBox, QProgressBar, QCheckBox
)
from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QFont

from ..services.whatsapp_local_service import LocalWhatsAppBusinessService
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ConnectionTestThread(QThread):
    """Thread for testing WhatsApp API connection."""
    
    result_ready = Signal(bool, str)
    
    def __init__(self, service: LocalWhatsAppBusinessService):
        super().__init__()
        self.service = service
    
    def run(self):
        """Test the connection in a separate thread."""
        try:
            success, message = self.service.test_connection()
            self.result_ready.emit(success, message)
        except Exception as e:
            self.result_ready.emit(False, f"Connection test failed: {e}")


class WhatsAppSettingsDialog(QDialog):
    """Dialog for configuring WhatsApp Business API settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = LocalWhatsAppBusinessService()
        self.connection_test_thread = None
        
        self.setWindowTitle("WhatsApp Business API Settings")
        self.setModal(True)
        self.resize(600, 500)
        
        self.setup_ui()
        self.load_current_settings()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("WhatsApp Business API Configuration")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # API Credentials Group
        credentials_group = QGroupBox("API Credentials")
        credentials_layout = QFormLayout(credentials_group)
        
        self.access_token_edit = QLineEdit()
        self.access_token_edit.setEchoMode(QLineEdit.Password)
        self.access_token_edit.setPlaceholderText("Enter your WhatsApp Business API access token")
        credentials_layout.addRow("Access Token:", self.access_token_edit)
        
        self.phone_number_id_edit = QLineEdit()
        self.phone_number_id_edit.setPlaceholderText("Enter your phone number ID")
        credentials_layout.addRow("Phone Number ID:", self.phone_number_id_edit)
        
        self.business_account_id_edit = QLineEdit()
        self.business_account_id_edit.setPlaceholderText("Enter your business account ID (optional)")
        credentials_layout.addRow("Business Account ID:", self.business_account_id_edit)
        
        # Show/Hide password checkbox
        self.show_token_checkbox = QCheckBox("Show Access Token")
        self.show_token_checkbox.toggled.connect(self.toggle_token_visibility)
        credentials_layout.addRow("", self.show_token_checkbox)
        
        layout.addWidget(credentials_group)
        
        # Rate Limiting Group
        limits_group = QGroupBox("Rate Limiting & Quotas")
        limits_layout = QFormLayout(limits_group)
        
        self.rate_limit_spin = QSpinBox()
        self.rate_limit_spin.setRange(1, 100)
        self.rate_limit_spin.setValue(20)
        self.rate_limit_spin.setSuffix(" messages/minute")
        limits_layout.addRow("Rate Limit:", self.rate_limit_spin)
        
        self.daily_limit_spin = QSpinBox()
        self.daily_limit_spin.setRange(1, 10000)
        self.daily_limit_spin.setValue(1000)
        self.daily_limit_spin.setSuffix(" messages/day")
        limits_layout.addRow("Daily Limit:", self.daily_limit_spin)
        
        self.delay_spin = QDoubleSpinBox()
        self.delay_spin.setRange(0.1, 60.0)
        self.delay_spin.setValue(3.0)
        self.delay_spin.setSuffix(" seconds")
        self.delay_spin.setDecimals(1)
        limits_layout.addRow("Delay Between Messages:", self.delay_spin)
        
        layout.addWidget(limits_group)
        
        # Connection Test Group
        test_group = QGroupBox("Connection Test")
        test_layout = QVBoxLayout(test_group)
        
        test_button_layout = QHBoxLayout()
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self.test_connection)
        test_button_layout.addWidget(self.test_button)
        
        self.test_progress = QProgressBar()
        self.test_progress.setVisible(False)
        test_button_layout.addWidget(self.test_progress)
        
        test_layout.addLayout(test_button_layout)
        
        self.test_result_text = QTextEdit()
        self.test_result_text.setMaximumHeight(100)
        self.test_result_text.setReadOnly(True)
        test_layout.addWidget(self.test_result_text)
        
        layout.addWidget(test_group)
        
        # Current Status Group
        status_group = QGroupBox("Current Status")
        status_layout = QFormLayout(status_group)
        
        self.status_label = QLabel("Not configured")
        status_layout.addRow("Configuration Status:", self.status_label)
        
        self.usage_label = QLabel("N/A")
        status_layout.addRow("Today's Usage:", self.usage_label)
        
        layout.addWidget(status_group)
        
        # Setup Instructions
        instructions_group = QGroupBox("Setup Instructions")
        instructions_layout = QVBoxLayout(instructions_group)
        
        instructions_text = QTextEdit()
        instructions_text.setReadOnly(True)
        instructions_text.setMaximumHeight(120)
        instructions_text.setPlainText(
            "1. Create a Meta Business Account at business.facebook.com\n"
            "2. Apply for WhatsApp Business API access\n"
            "3. Get your phone number verified and approved\n"
            "4. Obtain your Access Token and Phone Number ID from the Meta Developer Console\n"
            "5. Enter the credentials above and test the connection"
        )
        instructions_layout.addWidget(instructions_text)
        
        layout.addWidget(instructions_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("Clear Credentials")
        self.clear_button.clicked.connect(self.clear_credentials)
        button_layout.addWidget(self.clear_button)
        
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_settings)
        self.save_button.setDefault(True)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
    
    def toggle_token_visibility(self, checked: bool):
        """Toggle access token visibility."""
        if checked:
            self.access_token_edit.setEchoMode(QLineEdit.Normal)
        else:
            self.access_token_edit.setEchoMode(QLineEdit.Password)
    
    def load_current_settings(self):
        """Load current WhatsApp settings."""
        try:
            # Load credentials if available
            if self.service.credentials:
                self.access_token_edit.setText(self.service.credentials.get('access_token', ''))
                self.phone_number_id_edit.setText(self.service.credentials.get('phone_number_id', ''))
                self.business_account_id_edit.setText(self.service.credentials.get('business_account_id', ''))
            
            # Load rate limiting settings
            self.rate_limit_spin.setValue(self.service.rate_limit_per_minute)
            self.daily_limit_spin.setValue(self.service.daily_message_limit)
            
            # Update status
            self.update_status()
            
        except Exception as e:
            logger.error(f"Failed to load WhatsApp settings: {e}")
    
    def update_status(self):
        """Update the status display."""
        try:
            if self.service.is_configured():
                self.status_label.setText("✅ Configured and ready")
                self.status_label.setStyleSheet("color: green;")
            else:
                self.status_label.setText("❌ Not configured")
                self.status_label.setStyleSheet("color: red;")
            
            # Update usage stats
            stats = self.service.get_usage_stats()
            usage_text = f"{stats['daily_messages_sent']}/{stats['daily_limit']} messages"
            self.usage_label.setText(usage_text)
            
        except Exception as e:
            logger.error(f"Failed to update status: {e}")
    
    def test_connection(self):
        """Test the WhatsApp API connection."""
        # Validate inputs first
        access_token = self.access_token_edit.text().strip()
        phone_number_id = self.phone_number_id_edit.text().strip()
        
        if not access_token or not phone_number_id:
            QMessageBox.warning(
                self,
                "Missing Information",
                "Please enter both Access Token and Phone Number ID before testing."
            )
            return
        
        # Save credentials temporarily for testing
        temp_service = LocalWhatsAppBusinessService()
        if not temp_service.save_credentials(access_token, phone_number_id, self.business_account_id_edit.text().strip()):
            QMessageBox.critical(
                self,
                "Error",
                "Failed to save credentials for testing."
            )
            return
        
        # Start connection test
        self.test_button.setEnabled(False)
        self.test_progress.setVisible(True)
        self.test_progress.setRange(0, 0)  # Indeterminate progress
        self.test_result_text.clear()
        self.test_result_text.append("Testing connection...")
        
        # Start test thread
        self.connection_test_thread = ConnectionTestThread(temp_service)
        self.connection_test_thread.result_ready.connect(self.on_connection_test_result)
        self.connection_test_thread.start()
    
    def on_connection_test_result(self, success: bool, message: str):
        """Handle connection test result."""
        self.test_button.setEnabled(True)
        self.test_progress.setVisible(False)
        
        if success:
            self.test_result_text.append(f"✅ {message}")
            self.test_result_text.setStyleSheet("color: green;")
        else:
            self.test_result_text.append(f"❌ {message}")
            self.test_result_text.setStyleSheet("color: red;")
        
        # Clean up thread
        if self.connection_test_thread:
            self.connection_test_thread.deleteLater()
            self.connection_test_thread = None
    
    def save_settings(self):
        """Save WhatsApp settings."""
        try:
            # Validate inputs
            access_token = self.access_token_edit.text().strip()
            phone_number_id = self.phone_number_id_edit.text().strip()
            
            if not access_token or not phone_number_id:
                QMessageBox.warning(
                    self,
                    "Missing Information",
                    "Please enter both Access Token and Phone Number ID."
                )
                return
            
            # Save credentials
            business_account_id = self.business_account_id_edit.text().strip()
            if not self.service.save_credentials(access_token, phone_number_id, business_account_id):
                QMessageBox.critical(
                    self,
                    "Error",
                    "Failed to save WhatsApp credentials."
                )
                return
            
            # Update rate limiting settings
            self.service.rate_limit_per_minute = self.rate_limit_spin.value()
            self.service.daily_message_limit = self.daily_limit_spin.value()
            
            QMessageBox.information(
                self,
                "Settings Saved",
                "WhatsApp Business API settings have been saved successfully."
            )
            
            self.accept()
            
        except Exception as e:
            logger.error(f"Failed to save WhatsApp settings: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save settings: {e}"
            )
    
    def clear_credentials(self):
        """Clear stored WhatsApp credentials."""
        reply = QMessageBox.question(
            self,
            "Clear Credentials",
            "Are you sure you want to clear all WhatsApp credentials?\n"
            "This will disable WhatsApp functionality until reconfigured.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.service.clear_credentials():
                self.access_token_edit.clear()
                self.phone_number_id_edit.clear()
                self.business_account_id_edit.clear()
                self.test_result_text.clear()
                self.update_status()
                
                QMessageBox.information(
                    self,
                    "Credentials Cleared",
                    "WhatsApp credentials have been cleared successfully."
                )
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    "Failed to clear WhatsApp credentials."
                )
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        # Clean up connection test thread if running
        if self.connection_test_thread and self.connection_test_thread.isRunning():
            self.connection_test_thread.terminate()
            self.connection_test_thread.wait()
        
        event.accept()
