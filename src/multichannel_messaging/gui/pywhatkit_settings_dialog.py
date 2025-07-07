"""
PyWhatKit settings dialog for CSC-Reach.
Allows users to configure pywhatkit service with proper warnings.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QCheckBox,
    QGroupBox, QSpinBox, QMessageBox, QFrame, QScrollArea,
    QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QIcon

from ..services.pywhatkit_service import PyWhatKitService
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PyWhatKitSettingsDialog(QDialog):
    """
    Settings dialog for PyWhatKit WhatsApp service.
    Includes comprehensive warnings about risks and limitations.
    """
    
    settings_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = PyWhatKitService()
        self.setup_ui()
        self.load_current_settings()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("PyWhatKit WhatsApp Settings")
        self.setMinimumSize(600, 700)
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Create scroll area for long content
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Warning section
        self.create_warning_section(scroll_layout)
        
        # Service status section
        self.create_status_section(scroll_layout)
        
        # Configuration section
        self.create_configuration_section(scroll_layout)
        
        # Risk acknowledgment section
        self.create_acknowledgment_section(scroll_layout)
        
        # Set up scroll area
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Button section
        self.create_button_section(layout)
    
    def create_warning_section(self, layout):
        """Create the warning section."""
        warning_group = QGroupBox("⚠️ IMPORTANT WARNINGS")
        warning_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #d32f2f;
                border: 2px solid #d32f2f;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        warning_layout = QVBoxLayout(warning_group)
        
        warnings = [
            "🚫 Browser Automation Risks:",
            "   • May violate WhatsApp's Terms of Service",
            "   • High risk of account suspension or ban",
            "   • WhatsApp actively detects and blocks automation",
            "",
            "🔧 Technical Limitations:",
            "   • Requires WhatsApp Web to be open in browser",
            "   • Unreliable - browser automation can fail",
            "   • No professional error handling or recovery",
            "   • Cannot guarantee message delivery",
            "",
            "📊 Usage Restrictions:",
            "   • Very low daily limits (50 messages max)",
            "   • Slow sending (30+ second delays required)",
            "   • No bulk sending capabilities",
            "   • Limited to basic text messages only",
            "",
            "🏢 Not Suitable for Business:",
            "   • No compliance with business messaging standards",
            "   • No delivery confirmations or read receipts",
            "   • No customer support or SLA guarantees",
            "   • May damage your business reputation",
            "",
            "✅ RECOMMENDED ALTERNATIVE:",
            "   Use WhatsApp Business API instead - it's official,",
            "   reliable, compliant, and designed for business use."
        ]
        
        warning_text = QTextEdit()
        warning_text.setPlainText("\n".join(warnings))
        warning_text.setReadOnly(True)
        warning_text.setMaximumHeight(300)
        warning_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffebee;
                border: 1px solid #d32f2f;
                color: #b71c1c;
                font-family: monospace;
            }
        """)
        
        warning_layout.addWidget(warning_text)
        layout.addWidget(warning_group)
    
    def create_status_section(self, layout):
        """Create the service status section."""
        status_group = QGroupBox("Service Status")
        status_layout = QGridLayout(status_group)
        
        # PyWhatKit availability
        self.pywhatkit_status = QLabel()
        status_layout.addWidget(QLabel("PyWhatKit Package:"), 0, 0)
        status_layout.addWidget(self.pywhatkit_status, 0, 1)
        
        # Configuration status
        self.config_status = QLabel()
        status_layout.addWidget(QLabel("Configuration:"), 1, 0)
        status_layout.addWidget(self.config_status, 1, 1)
        
        # Daily usage
        self.usage_status = QLabel()
        status_layout.addWidget(QLabel("Daily Usage:"), 2, 0)
        status_layout.addWidget(self.usage_status, 2, 1)
        
        layout.addWidget(status_group)
    
    def create_configuration_section(self, layout):
        """Create the configuration section."""
        config_group = QGroupBox("Configuration Settings")
        config_layout = QGridLayout(config_group)
        
        # Rate limiting
        config_layout.addWidget(QLabel("Messages per minute:"), 0, 0)
        self.rate_limit_spin = QSpinBox()
        self.rate_limit_spin.setRange(1, 10)
        self.rate_limit_spin.setValue(5)
        self.rate_limit_spin.setSuffix(" msg/min")
        config_layout.addWidget(self.rate_limit_spin, 0, 1)
        
        # Daily limit
        config_layout.addWidget(QLabel("Daily message limit:"), 1, 0)
        self.daily_limit_spin = QSpinBox()
        self.daily_limit_spin.setRange(1, 100)
        self.daily_limit_spin.setValue(50)
        self.daily_limit_spin.setSuffix(" messages")
        config_layout.addWidget(self.daily_limit_spin, 1, 1)
        
        # Minimum delay
        config_layout.addWidget(QLabel("Minimum delay between messages:"), 2, 0)
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(15, 120)
        self.delay_spin.setValue(30)
        self.delay_spin.setSuffix(" seconds")
        config_layout.addWidget(self.delay_spin, 2, 1)
        
        # Help text
        help_text = QLabel(
            "Conservative limits are enforced to reduce the risk of account suspension.\n"
            "These limits cannot be increased beyond safe thresholds."
        )
        help_text.setStyleSheet("color: #666; font-style: italic;")
        help_text.setWordWrap(True)
        config_layout.addWidget(help_text, 3, 0, 1, 2)
        
        layout.addWidget(config_group)
    
    def create_acknowledgment_section(self, layout):
        """Create the risk acknowledgment section."""
        ack_group = QGroupBox("Risk Acknowledgment")
        ack_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #ff9800;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        ack_layout = QVBoxLayout(ack_group)
        
        # Checkboxes for acknowledgment
        self.ack_tos = QCheckBox("I understand this may violate WhatsApp's Terms of Service")
        self.ack_ban = QCheckBox("I accept the risk of account suspension or ban")
        self.ack_unreliable = QCheckBox("I understand this method is unreliable and not suitable for business")
        self.ack_alternative = QCheckBox("I acknowledge that WhatsApp Business API is the recommended alternative")
        self.ack_responsibility = QCheckBox("I take full responsibility for any consequences")
        
        for checkbox in [self.ack_tos, self.ack_ban, self.ack_unreliable, 
                        self.ack_alternative, self.ack_responsibility]:
            checkbox.setStyleSheet("QCheckBox { color: #e65100; font-weight: bold; }")
            ack_layout.addWidget(checkbox)
        
        # Final confirmation
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        ack_layout.addWidget(separator)
        
        self.final_ack = QCheckBox("I have read all warnings and choose to proceed at my own risk")
        self.final_ack.setStyleSheet("""
            QCheckBox { 
                color: #d32f2f; 
                font-weight: bold; 
                font-size: 12px;
            }
        """)
        ack_layout.addWidget(self.final_ack)
        
        layout.addWidget(ack_group)
    
    def create_button_section(self, layout):
        """Create the button section."""
        button_layout = QHBoxLayout()
        
        # Test connection button
        self.test_btn = QPushButton("Test Service")
        self.test_btn.clicked.connect(self.test_service)
        button_layout.addWidget(self.test_btn)
        
        # Reset usage button
        self.reset_btn = QPushButton("Reset Daily Usage")
        self.reset_btn.clicked.connect(self.reset_usage)
        button_layout.addWidget(self.reset_btn)
        
        button_layout.addStretch()
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # Save button
        self.save_btn = QPushButton("Save Configuration")
        self.save_btn.clicked.connect(self.save_settings)
        self.save_btn.setEnabled(False)  # Disabled until all acknowledgments are checked
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
        
        # Connect acknowledgment checkboxes to enable/disable save button
        for checkbox in [self.ack_tos, self.ack_ban, self.ack_unreliable, 
                        self.ack_alternative, self.ack_responsibility, self.final_ack]:
            checkbox.toggled.connect(self.update_save_button)
    
    def load_current_settings(self):
        """Load current service settings."""
        # Update status displays
        self.update_status_display()
        
        # Load configuration values
        if self.service.is_configured():
            self.rate_limit_spin.setValue(self.service.rate_limit_per_minute)
            self.daily_limit_spin.setValue(self.service.daily_message_limit)
            self.delay_spin.setValue(self.service.min_delay_seconds)
    
    def update_status_display(self):
        """Update the status display."""
        # PyWhatKit availability
        if self.service.is_available():
            self.pywhatkit_status.setText("✅ Installed")
            self.pywhatkit_status.setStyleSheet("color: green;")
        else:
            self.pywhatkit_status.setText("❌ Not installed (pip install pywhatkit)")
            self.pywhatkit_status.setStyleSheet("color: red;")
        
        # Configuration status
        if self.service.is_configured():
            self.config_status.setText("✅ Configured")
            self.config_status.setStyleSheet("color: green;")
        else:
            self.config_status.setText("❌ Not configured")
            self.config_status.setStyleSheet("color: orange;")
        
        # Usage status
        usage = self.service.get_daily_usage()
        usage_text = f"{usage['messages_sent_today']}/{usage['daily_limit']} messages today"
        self.usage_status.setText(usage_text)
        
        if usage['messages_sent_today'] >= usage['daily_limit']:
            self.usage_status.setStyleSheet("color: red;")
        elif usage['messages_sent_today'] > usage['daily_limit'] * 0.8:
            self.usage_status.setStyleSheet("color: orange;")
        else:
            self.usage_status.setStyleSheet("color: green;")
    
    def update_save_button(self):
        """Update save button state based on acknowledgments."""
        all_checked = all([
            self.ack_tos.isChecked(),
            self.ack_ban.isChecked(),
            self.ack_unreliable.isChecked(),
            self.ack_alternative.isChecked(),
            self.ack_responsibility.isChecked(),
            self.final_ack.isChecked()
        ])
        
        self.save_btn.setEnabled(all_checked and self.service.is_available())
    
    def test_service(self):
        """Test the PyWhatKit service."""
        if not self.service.is_available():
            QMessageBox.warning(
                self,
                "Service Not Available",
                "PyWhatKit package is not installed.\n\nInstall with: pip install pywhatkit"
            )
            return
        
        if not self.service.is_configured():
            QMessageBox.warning(
                self,
                "Service Not Configured",
                "Please configure the service first by acknowledging all risks and saving the configuration."
            )
            return
        
        try:
            success, message = self.service.test_connection()
            if success:
                QMessageBox.information(self, "Service Test", f"✅ {message}")
            else:
                QMessageBox.warning(self, "Service Test", f"❌ {message}")
        except Exception as e:
            QMessageBox.critical(self, "Service Test", f"Test failed: {e}")
    
    def reset_usage(self):
        """Reset daily usage."""
        reply = QMessageBox.question(
            self,
            "Reset Daily Usage",
            "Are you sure you want to reset today's message count?\n\n"
            "This should only be used for testing purposes.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.service.reset_daily_usage()
            self.update_status_display()
            QMessageBox.information(self, "Usage Reset", "Daily usage has been reset.")
    
    def save_settings(self):
        """Save the service settings."""
        if not self.service.is_available():
            QMessageBox.warning(
                self,
                "Cannot Save",
                "PyWhatKit package is not installed."
            )
            return
        
        if not all([
            self.ack_tos.isChecked(),
            self.ack_ban.isChecked(),
            self.ack_unreliable.isChecked(),
            self.ack_alternative.isChecked(),
            self.ack_responsibility.isChecked(),
            self.final_ack.isChecked()
        ]):
            QMessageBox.warning(
                self,
                "Acknowledgment Required",
                "You must acknowledge all risks before proceeding."
            )
            return
        
        try:
            # Update service settings
            self.service.rate_limit_per_minute = self.rate_limit_spin.value()
            self.service.daily_message_limit = self.daily_limit_spin.value()
            self.service.min_delay_seconds = self.delay_spin.value()
            
            # Configure the service
            success, message = self.service.configure_service(acknowledge_risks=True)
            
            if success:
                self.settings_changed.emit()
                QMessageBox.information(
                    self,
                    "Configuration Saved",
                    f"PyWhatKit service has been configured.\n\n"
                    f"⚠️ Remember: Use at your own risk!\n\n"
                    f"Settings:\n"
                    f"• Rate limit: {self.rate_limit_spin.value()} msg/min\n"
                    f"• Daily limit: {self.daily_limit_spin.value()} messages\n"
                    f"• Min delay: {self.delay_spin.value()} seconds"
                )
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    "Configuration Failed",
                    f"Failed to configure PyWhatKit service:\n\n{message}"
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Configuration Error",
                f"An error occurred while saving settings:\n\n{e}"
            )
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        # Update status one more time
        self.update_status_display()
        super().closeEvent(event)
