"""
WhatsApp Web settings dialog for CSC-Reach.
Simplified configuration without external dependencies.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTextEdit, QCheckBox,
    QGroupBox, QSpinBox, QMessageBox, QFrame, QScrollArea,
    QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QIcon

from ..services.whatsapp_web_service import WhatsAppWebService
from ..utils.logger import get_logger

logger = get_logger(__name__)


class WhatsAppWebSettingsDialog(QDialog):
    """
    Settings dialog for WhatsApp Web automation service.
    Simplified interface with comprehensive warnings about risks.
    """
    
    settings_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = WhatsAppWebService()
        self.setup_ui()
        self.load_current_settings()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("WhatsApp Web Automation Settings")
        self.setMinimumSize(550, 600)
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
        
        # How it works section
        self.create_how_it_works_section(scroll_layout)
        
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
            "   • WhatsApp actively detects automation",
            "",
            "📱 Manual Interaction Required:",
            "   • Opens WhatsApp Web in your browser",
            "   • You must manually click 'Send' for each message",
            "   • Requires you to be logged into WhatsApp Web",
            "",
            "⏱️ Usage Restrictions:",
            "   • Very low daily limits (30 messages max)",
            "   • Slow sending (45+ second delays required)",
            "   • Only 3 messages per minute maximum",
            "",
            "✅ RECOMMENDED ALTERNATIVE:",
            "   Use WhatsApp Business API instead - it's official,",
            "   reliable, compliant, and designed for business use."
        ]
        
        warning_text = QTextEdit()
        warning_text.setPlainText("\n".join(warnings))
        warning_text.setReadOnly(True)
        warning_text.setMaximumHeight(250)
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
        
        # Service availability
        self.service_status = QLabel("✅ Available (No external dependencies)")
        self.service_status.setStyleSheet("color: green;")
        status_layout.addWidget(QLabel("Service:"), 0, 0)
        status_layout.addWidget(self.service_status, 0, 1)
        
        # Configuration status
        self.config_status = QLabel()
        status_layout.addWidget(QLabel("Configuration:"), 1, 0)
        status_layout.addWidget(self.config_status, 1, 1)
        
        # Daily usage
        self.usage_status = QLabel()
        status_layout.addWidget(QLabel("Daily Usage:"), 2, 0)
        status_layout.addWidget(self.usage_status, 2, 1)
        
        layout.addWidget(status_group)
    
    def create_how_it_works_section(self, layout):
        """Create the how it works section."""
        how_group = QGroupBox("How It Works")
        how_layout = QVBoxLayout(how_group)
        
        steps = [
            "1. You select recipients and compose your message",
            "2. CSC-Reach opens WhatsApp Web in your browser for each recipient",
            "3. The message is pre-filled in the chat window",
            "4. You manually click 'Send' to send each message",
            "5. Process repeats for each recipient with delays between"
        ]
        
        steps_text = QTextEdit()
        steps_text.setPlainText("\n".join(steps))
        steps_text.setReadOnly(True)
        steps_text.setMaximumHeight(120)
        steps_text.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ccc;
                color: #333;
            }
        """)
        
        how_layout.addWidget(steps_text)
        
        note_label = QLabel("Note: You must be logged into WhatsApp Web and keep your browser open during the process.")
        note_label.setStyleSheet("color: #666; font-style: italic;")
        note_label.setWordWrap(True)
        how_layout.addWidget(note_label)
        
        layout.addWidget(how_group)
    
    def create_configuration_section(self, layout):
        """Create the configuration section."""
        config_group = QGroupBox("Configuration Settings")
        config_layout = QGridLayout(config_group)
        
        # Auto-send option
        self.auto_send_checkbox = QCheckBox("Enable automatic sending (HIGHER RISK)")
        self.auto_send_checkbox.setStyleSheet("QCheckBox { color: #d32f2f; font-weight: bold; }")
        config_layout.addWidget(self.auto_send_checkbox, 0, 0, 1, 2)
        
        auto_send_help = QLabel(
            "⚠️ Automatic sending uses system automation to press Enter key.\n"
            "This increases the risk of account suspension significantly!"
        )
        auto_send_help.setStyleSheet("color: #d32f2f; font-style: italic; font-size: 10px;")
        auto_send_help.setWordWrap(True)
        config_layout.addWidget(auto_send_help, 1, 0, 1, 2)
        
        # Close existing tabs option
        self.close_tabs_checkbox = QCheckBox("Close existing WhatsApp Web tabs before opening new ones")
        self.close_tabs_checkbox.setChecked(True)  # Default to True
        self.close_tabs_checkbox.setToolTip("Prevents multiple WhatsApp Web tabs from opening simultaneously")
        config_layout.addWidget(self.close_tabs_checkbox, 2, 0, 1, 2)
        
        close_tabs_help = QLabel(
            "✅ Recommended: Prevents browser from opening multiple WhatsApp Web tabs.\n"
            "Especially important on Windows to avoid performance issues."
        )
        close_tabs_help.setStyleSheet("color: #2e7d32; font-style: italic; font-size: 10px;")
        close_tabs_help.setWordWrap(True)
        config_layout.addWidget(close_tabs_help, 3, 0, 1, 2)

        # Auto-send delay
        config_layout.addWidget(QLabel("Auto-send delay:"), 4, 0)
        self.auto_send_delay_spin = QSpinBox()
        self.auto_send_delay_spin.setRange(3, 15)
        self.auto_send_delay_spin.setValue(5)
        self.auto_send_delay_spin.setSuffix(" seconds")
        self.auto_send_delay_spin.setToolTip("Time to wait for WhatsApp Web to load before attempting auto-send")
        config_layout.addWidget(self.auto_send_delay_spin, 4, 1)
        
        # Rate limiting
        config_layout.addWidget(QLabel("Messages per minute:"), 5, 0)
        self.rate_limit_spin = QSpinBox()
        self.rate_limit_spin.setRange(1, 5)
        self.rate_limit_spin.setValue(3)
        self.rate_limit_spin.setSuffix(" msg/min")
        config_layout.addWidget(self.rate_limit_spin, 5, 1)
        
        # Daily limit
        config_layout.addWidget(QLabel("Daily message limit:"), 6, 0)
        self.daily_limit_spin = QSpinBox()
        self.daily_limit_spin.setRange(1, 50)
        self.daily_limit_spin.setValue(30)
        self.daily_limit_spin.setSuffix(" messages")
        config_layout.addWidget(self.daily_limit_spin, 6, 1)
        
        # Minimum delay
        config_layout.addWidget(QLabel("Minimum delay between messages:"), 7, 0)
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(30, 180)
        self.delay_spin.setValue(45)
        self.delay_spin.setSuffix(" seconds")
        config_layout.addWidget(self.delay_spin, 7, 1)
        
        # Help text
        help_text = QLabel(
            "Very conservative limits are enforced to reduce account suspension risk.\n"
            "These limits are much lower than other services for safety."
        )
        help_text.setStyleSheet("color: #666; font-style: italic;")
        help_text.setWordWrap(True)
        config_layout.addWidget(help_text, 8, 0, 1, 2)
        
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
        self.ack_manual = QCheckBox("I understand I must manually send each message (unless auto-send is enabled)")
        self.ack_alternative = QCheckBox("I acknowledge that WhatsApp Business API is the recommended alternative")
        self.ack_responsibility = QCheckBox("I take full responsibility for any consequences")
        
        # Auto-send specific acknowledgment
        self.ack_auto_send = QCheckBox("I understand automatic sending significantly increases risks")
        self.ack_auto_send.setStyleSheet("QCheckBox { color: #d32f2f; font-weight: bold; }")
        
        for checkbox in [self.ack_tos, self.ack_ban, self.ack_manual, 
                        self.ack_alternative, self.ack_responsibility]:
            checkbox.setStyleSheet("QCheckBox { color: #e65100; font-weight: bold; }")
            ack_layout.addWidget(checkbox)
        
        # Add auto-send acknowledgment
        ack_layout.addWidget(self.ack_auto_send)
        
        # Connect auto-send checkbox to show/hide auto-send acknowledgment
        self.auto_send_checkbox.toggled.connect(self.on_auto_send_toggled)
        
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
        for checkbox in [self.ack_tos, self.ack_ban, self.ack_manual, 
                        self.ack_alternative, self.ack_responsibility, self.ack_auto_send, self.final_ack]:
            checkbox.toggled.connect(self.update_save_button)
    
    def on_auto_send_toggled(self, checked: bool):
        """Handle auto-send checkbox toggle."""
        # Show/hide auto-send acknowledgment based on auto-send checkbox
        self.ack_auto_send.setVisible(checked)
        if not checked:
            self.ack_auto_send.setChecked(False)
        self.update_save_button()
    
    def load_current_settings(self):
        """Load current service settings."""
        # Update status displays
        self.update_status_display()
        
        # Load configuration values
        if self.service.is_configured():
            self.auto_send_checkbox.setChecked(self.service.auto_send)
            self.auto_send_delay_spin.setValue(getattr(self.service, 'auto_send_delay', 5))
            self.close_tabs_checkbox.setChecked(getattr(self.service, 'close_existing_tabs', True))
            self.rate_limit_spin.setValue(self.service.rate_limit_per_minute)
            self.daily_limit_spin.setValue(self.service.daily_message_limit)
            self.delay_spin.setValue(self.service.min_delay_seconds)
    
    def update_status_display(self):
        """Update the status display."""
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
        basic_checks = all([
            self.ack_tos.isChecked(),
            self.ack_ban.isChecked(),
            self.ack_manual.isChecked(),
            self.ack_alternative.isChecked(),
            self.ack_responsibility.isChecked(),
            self.final_ack.isChecked()
        ])
        
        # If auto-send is enabled, require auto-send acknowledgment too
        auto_send_check = True
        if self.auto_send_checkbox.isChecked():
            auto_send_check = self.ack_auto_send.isChecked()
        
        self.save_btn.setEnabled(basic_checks and auto_send_check)
    
    def test_service(self):
        """Test the WhatsApp Web service."""
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
                QMessageBox.information(
                    self, 
                    "Service Test", 
                    f"✅ {message}\n\nWhatsApp Web should have opened in your browser."
                )
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
        basic_acknowledgments = all([
            self.ack_tos.isChecked(),
            self.ack_ban.isChecked(),
            self.ack_manual.isChecked(),
            self.ack_alternative.isChecked(),
            self.ack_responsibility.isChecked(),
            self.final_ack.isChecked()
        ])
        
        if not basic_acknowledgments:
            QMessageBox.warning(
                self,
                "Acknowledgment Required",
                "You must acknowledge all basic risks before proceeding."
            )
            return
        
        # Additional warning for auto-send
        auto_send_enabled = self.auto_send_checkbox.isChecked()
        if auto_send_enabled:
            if not self.ack_auto_send.isChecked():
                QMessageBox.warning(
                    self,
                    "Auto-Send Acknowledgment Required",
                    "You must acknowledge the additional risks of automatic sending."
                )
                return
            
            reply = QMessageBox.warning(
                self,
                "⚠️ AUTOMATIC SENDING WARNING",
                "You have enabled automatic sending!\n\n"
                "🚨 EXTREME RISKS:\n"
                "• Much higher chance of account suspension\n"
                "• Uses system automation (key presses)\n"
                "• May be detected as bot behavior\n"
                "• Could violate WhatsApp ToS more severely\n\n"
                "Manual sending is STRONGLY recommended.\n\n"
                "Are you absolutely sure you want to enable auto-send?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
        
        try:
            # Update service settings
            self.service.rate_limit_per_minute = self.rate_limit_spin.value()
            self.service.daily_message_limit = self.daily_limit_spin.value()
            self.service.min_delay_seconds = self.delay_spin.value()
            self.service.auto_send_delay = self.auto_send_delay_spin.value()
            
            # Configure the service
            success, message = self.service.configure_service(
                acknowledge_risks=True, 
                auto_send=auto_send_enabled,
                close_existing_tabs=self.close_tabs_checkbox.isChecked()
            )
            
            if success:
                self.settings_changed.emit()
                
                config_message = (
                    f"WhatsApp Web service has been configured.\n\n"
                    f"⚠️ Remember: Use at your own risk!\n\n"
                    f"Settings:\n"
                    f"• Auto-send: {'ENABLED (HIGH RISK)' if auto_send_enabled else 'Disabled (Manual)'}\n"
                    f"• Close existing tabs: {'Yes' if self.close_tabs_checkbox.isChecked() else 'No'}\n"
                    f"• Rate limit: {self.rate_limit_spin.value()} msg/min\n"
                    f"• Daily limit: {self.daily_limit_spin.value()} messages\n"
                    f"• Min delay: {self.delay_spin.value()} seconds\n\n"
                )
                
                if auto_send_enabled:
                    config_message += (
                        "🤖 Automatic Sending Process:\n"
                        "1. Select recipients and compose message\n"
                        "2. Choose 'WhatsApp Web' channel\n"
                        "3. Click 'Send Messages'\n"
                        "4. Messages will be sent automatically\n\n"
                        "⚠️ Monitor closely for any issues!"
                    )
                else:
                    config_message += (
                        "👤 Manual Sending Process:\n"
                        "1. Select recipients and compose message\n"
                        "2. Choose 'WhatsApp Web' channel\n"
                        "3. Click 'Send Messages'\n"
                        "4. Manually send each message in browser"
                    )
                
                QMessageBox.information(self, "Configuration Saved", config_message)
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    "Configuration Failed",
                    f"Failed to configure WhatsApp Web service:\n\n{message}"
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
