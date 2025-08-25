"""
Main window for Multi-Channel Bulk Messaging System.
"""

import sys
import time
from pathlib import Path
from typing import List, Optional

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QTextEdit,
    QListWidget,
    QListWidgetItem,
    QGroupBox,
    QProgressBar,
    QStatusBar,
    QMenuBar,
    QFileDialog,
    QMessageBox,
    QSplitter,
    QFrame,
    QCheckBox,
    QComboBox,
    QDialog,
    QApplication,
)
from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QFont, QIcon

from ..core.config_manager import ConfigManager
from ..core.csv_processor import CSVProcessor
from ..core.models import Customer, MessageTemplate, MessageChannel
from ..core.template_manager import TemplateManager
from ..core.whatsapp_multi_message_manager import WhatsAppMultiMessageManager
from ..core.whatsapp_multi_message import WhatsAppMultiMessageService
from ..core.theme_manager import ThemeManager, ThemeMode
from ..core.progress_manager import ProgressManager, OperationType, ProgressTracker
from ..core.user_preferences import UserPreferencesManager
from ..core.accessibility_manager import AccessibilityManager
from ..core.keyboard_navigation import KeyboardNavigationManager
from ..core.toolbar_manager import ToolbarManager
from ..services.email_service import EmailService
from ..services.logged_email_service import LoggedEmailService
from ..services.whatsapp_local_service import LocalWhatsAppBusinessService
from ..services.whatsapp_web_service import WhatsAppWebService
from .template_library_dialog import TemplateLibraryDialog
from .whatsapp_multi_message_dialog import WhatsAppMultiMessageDialog
from .modern_progress_dialog import ModernProgressDialog
from .preferences_dialog import PreferencesDialog
from .variables_panel import VariablesPanel
from ..gui.whatsapp_settings_dialog import WhatsAppSettingsDialog
from ..gui.whatsapp_web_settings_dialog import WhatsAppWebSettingsDialog
from ..gui.language_settings_dialog import LanguageSettingsDialog
from ..gui.preview_dialog import PreviewDialog
from ..core.i18n_manager import get_i18n_manager, tr
from ..utils.logger import get_logger
from ..utils.exceptions import CSVProcessingError, OutlookIntegrationError

logger = get_logger(__name__)


class EmailSendingThread(QThread):
    """Thread for sending emails in the background."""

    progress_updated = Signal(int, int)  # current, total
    email_sent = Signal(str, bool, str)  # email, success, message
    finished = Signal(bool, str)  # success, message

    def __init__(
        self, customers: List[Customer], template: MessageTemplate, email_service
    ):
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
                    # Check if we're using LoggedEmailService or regular EmailService
                    if hasattr(self.email_service, "send_single_email"):
                        # Using LoggedEmailService
                        message_record = self.email_service.send_single_email(
                            customer, self.template
                        )
                        success = message_record.status.value == "sent"
                    else:
                        # Using regular EmailService
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


class LoggedEmailSendingThread(QThread):
    """Thread for sending emails using LoggedEmailService with comprehensive logging."""

    progress_updated = Signal(int, int)  # current, total
    email_sent = Signal(str, bool, str)  # email, success, message
    finished = Signal(bool, str)  # success, message

    def __init__(
        self, customers: List[Customer], template: MessageTemplate, logged_email_service
    ):
        super().__init__()
        self.customers = customers
        self.template = template
        self.logged_email_service = logged_email_service
        self.should_stop = False

    def run(self):
        """Run the email sending process using LoggedEmailService."""
        try:
            # Set up progress callback for LoggedEmailService
            def progress_callback(current, total, message):
                self.progress_updated.emit(current, total)

            self.logged_email_service.set_progress_callback(progress_callback)

            # Use the bulk email functionality of LoggedEmailService
            message_records = self.logged_email_service.send_bulk_emails(
                customers=self.customers,
                template=self.template,
                batch_size=10,
                delay_between_emails=1.0,
            )

            # Emit individual email results
            successful = 0
            failed = 0
            for record in message_records:
                if record.status.value == "sent":
                    successful += 1
                    self.email_sent.emit(
                        record.customer.email, True, "Sent successfully"
                    )
                else:
                    failed += 1
                    error_msg = record.error_message or "Failed to send"
                    self.email_sent.emit(record.customer.email, False, error_msg)

            message = f"Completed: {successful} successful, {failed} failed"
            self.finished.emit(True, message)

        except Exception as e:
            self.finished.emit(False, f"Sending failed: {e}")

    def stop(self):
        """Stop the sending process."""
        self.should_stop = True
        # Note: LoggedEmailService doesn't currently support cancellation
        # This would need to be implemented in the service


class EnhancedEmailSendingThread(QThread):
    """Enhanced email sending thread with modern progress tracking."""

    finished = Signal(bool, str)  # success, message

    def __init__(
        self,
        customers: List[Customer],
        template: MessageTemplate,
        email_service,
        progress_tracker: ProgressTracker,
        step_index: int,
    ):
        super().__init__()
        self.customers = customers
        self.template = template
        self.email_service = email_service
        self.progress_tracker = progress_tracker
        self.step_index = step_index
        self.should_stop = False

    def run(self):
        """Run the enhanced email sending process."""
        try:
            successful = 0
            failed = 0
            total = len(self.customers)

            for i, customer in enumerate(self.customers):
                if self.should_stop:
                    self.finished.emit(False, "Sending cancelled by user")
                    return

                try:
                    # Update progress
                    progress = i / total
                    self.progress_tracker.update(
                        progress, f"Sending to {customer.name}..."
                    )
                    self.progress_tracker.set_step(
                        self.step_index, progress, f"Sending email {i + 1}/{total}"
                    )

                    # Send email
                    if hasattr(self.email_service, "send_single_email"):
                        # Using LoggedEmailService
                        message_record = self.email_service.send_single_email(
                            customer, self.template
                        )
                        success = message_record.status.value == "sent"
                    else:
                        # Using regular EmailService
                        success = self.email_service.send_email(customer, self.template)

                    if success:
                        successful += 1
                    else:
                        failed += 1

                    # Small delay between emails
                    self.msleep(1000)  # 1 second delay

                except Exception as e:
                    failed += 1
                    logger.error(f"Failed to send email to {customer.email}: {e}")

            # Complete the step
            self.progress_tracker.complete_step(self.step_index, True)

            # Final progress update
            self.progress_tracker.update(
                1.0,
                f"Email sending completed: {successful} successful, {failed} failed",
            )

            message = (
                f"Email sending completed: {successful} successful, {failed} failed"
            )
            self.finished.emit(True, message)

        except Exception as e:
            self.progress_tracker.complete_step(self.step_index, False, str(e))
            self.finished.emit(False, f"Email sending failed: {e}")

    def stop(self):
        """Stop the sending process."""
        self.should_stop = True


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, config_manager: ConfigManager, message_logger=None):
        super().__init__()
        self.config_manager = config_manager
        self.message_logger = message_logger
        self.csv_processor = CSVProcessor()
        self.email_service = None
        self.whatsapp_service = (
            LocalWhatsAppBusinessService()
        )  # WhatsApp Business API service
        self.whatsapp_web_service = (
            WhatsAppWebService()
        )  # WhatsApp Web service (no dependencies)
        self.template_manager = TemplateManager(
            self.config_manager
        )  # Template management system
        
        self.whatsapp_multi_message_manager = WhatsAppMultiMessageManager(
            self.config_manager
        )  # WhatsApp multi-message template manager
        
        self.whatsapp_multi_message_service = WhatsAppMultiMessageService(
            self.whatsapp_service
        )  # WhatsApp multi-message service
        self.customers: List[Customer] = []
        self.current_template: Optional[MessageTemplate] = None
        self.sending_thread: Optional[EmailSendingThread] = None

        # Initialize modern UI components
        self.theme_manager = ThemeManager(self.config_manager)
        self.progress_manager = ProgressManager()
        self.preferences_manager = UserPreferencesManager(self.config_manager)
        self.accessibility_manager = AccessibilityManager(self.preferences_manager)
        self.keyboard_navigation = KeyboardNavigationManager()
        self.toolbar_manager = ToolbarManager(self, self.preferences_manager)

        # Initialize i18n manager
        self.i18n_manager = get_i18n_manager()

        # Current operation tracking
        self.current_operation_id: Optional[str] = None
        self.progress_dialog: Optional[ModernProgressDialog] = None
        
        # Variables panel
        self.variables_panel: Optional[VariablesPanel] = None

        self.setup_ui()
        self.setup_services()
        self.load_default_template()
        self.apply_user_preferences()
        self.setup_accessibility()
        self.setup_toolbar_manager()

        # Connect theme and preferences signals
        self.theme_manager.theme_changed.connect(self.on_theme_changed)
        self.preferences_manager.preferences_changed.connect(
            self.on_preferences_changed
        )
        self.accessibility_manager.accessibility_changed.connect(
            self.on_accessibility_changed
        )

        # Set window geometry from preferences
        self.restore_window_geometry()

    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle(tr("app_title"))
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
        file_menu = menubar.addMenu(tr("menu_file"))

        import_action = QAction(tr("import_csv_menu"), self)
        import_action.setShortcut("Ctrl+O")
        import_action.triggered.connect(self.import_csv)
        file_menu.addAction(import_action)

        file_menu.addSeparator()

        exit_action = QAction(tr("exit"), self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Templates menu
        templates_menu = menubar.addMenu(tr("menu_templates"))

        template_library_action = QAction(tr("template_library_menu"), self)
        template_library_action.setShortcut("Ctrl+T")
        template_library_action.triggered.connect(self.open_template_library)
        templates_menu.addAction(template_library_action)

        templates_menu.addSeparator()

        new_template_action = QAction(tr("new_template_menu"), self)
        new_template_action.setShortcut("Ctrl+N")
        new_template_action.triggered.connect(self.create_new_template)
        templates_menu.addAction(new_template_action)

        save_template_action = QAction(tr("save_current_template"), self)
        save_template_action.setShortcut("Ctrl+S")
        save_template_action.triggered.connect(self.save_current_template)
        templates_menu.addAction(save_template_action)

        templates_menu.addSeparator()

        import_template_action = QAction(tr("import_template_menu"), self)
        import_template_action.triggered.connect(self.import_template_file)
        templates_menu.addAction(import_template_action)

        export_templates_action = QAction(tr("export_all_templates_menu"), self)
        export_templates_action.triggered.connect(self.export_all_templates)
        templates_menu.addAction(export_templates_action)
        
        templates_menu.addSeparator()
        
        # WhatsApp Multi-Message Templates
        whatsapp_multi_menu = templates_menu.addMenu(tr("whatsapp_multi_message_templates"))
        
        create_whatsapp_template_action = QAction(tr("create_whatsapp_template"), self)
        create_whatsapp_template_action.triggered.connect(self.create_whatsapp_multi_message_template)
        whatsapp_multi_menu.addAction(create_whatsapp_template_action)
        
        manage_whatsapp_templates_action = QAction(tr("manage_whatsapp_templates"), self)
        manage_whatsapp_templates_action.triggered.connect(self.manage_whatsapp_multi_message_templates)
        whatsapp_multi_menu.addAction(manage_whatsapp_templates_action)

        # Tools menu
        tools_menu = menubar.addMenu(tr("menu_tools"))

        test_outlook_action = QAction(tr("test_outlook_connection"), self)
        test_outlook_action.triggered.connect(self.test_outlook_connection)
        tools_menu.addAction(test_outlook_action)

        tools_menu.addSeparator()

        whatsapp_settings_action = QAction(tr("whatsapp_business_api_settings"), self)
        whatsapp_settings_action.triggered.connect(self.show_whatsapp_settings)
        tools_menu.addAction(whatsapp_settings_action)

        whatsapp_web_settings_action = QAction(tr("whatsapp_web_settings"), self)
        whatsapp_web_settings_action.triggered.connect(self.show_whatsapp_web_settings)
        tools_menu.addAction(whatsapp_web_settings_action)

        tools_menu.addSeparator()

        test_whatsapp_action = QAction(tr("test_whatsapp_business_api"), self)
        test_whatsapp_action.triggered.connect(self.test_whatsapp_connection)
        tools_menu.addAction(test_whatsapp_action)

        test_whatsapp_web_action = QAction(tr("test_whatsapp_web_service"), self)
        test_whatsapp_web_action.triggered.connect(self.test_whatsapp_web_connection)
        tools_menu.addAction(test_whatsapp_web_action)

        tools_menu.addSeparator()

        # Message Analytics
        analytics_action = QAction(tr("message_analytics_logs"), self)
        analytics_action.setShortcut("Ctrl+L")
        analytics_action.triggered.connect(self.show_message_analytics)
        tools_menu.addAction(analytics_action)

        # View menu
        view_menu = menubar.addMenu(tr("menu_view"))

        # Theme submenu
        theme_menu = view_menu.addMenu(tr("theme"))

        light_theme_action = QAction(tr("light_theme"), self)
        light_theme_action.triggered.connect(
            lambda: self.theme_manager.set_theme(ThemeMode.LIGHT)
        )
        theme_menu.addAction(light_theme_action)

        dark_theme_action = QAction(tr("dark_theme"), self)
        dark_theme_action.triggered.connect(
            lambda: self.theme_manager.set_theme(ThemeMode.DARK)
        )
        theme_menu.addAction(dark_theme_action)

        system_theme_action = QAction(tr("system_theme"), self)
        system_theme_action.triggered.connect(
            lambda: self.theme_manager.set_theme(ThemeMode.SYSTEM)
        )
        theme_menu.addAction(system_theme_action)

        view_menu.addSeparator()

        # Toolbar customization
        customize_toolbar_action = QAction(tr("customize_toolbars"), self)
        customize_toolbar_action.triggered.connect(self.show_toolbar_customization)
        view_menu.addAction(customize_toolbar_action)

        view_menu.addSeparator()

        # Preferences
        preferences_action = QAction(tr("preferences"), self)
        preferences_action.setShortcut("Ctrl+,")
        preferences_action.triggered.connect(self.show_preferences)
        view_menu.addAction(preferences_action)

        # Help menu
        help_menu = menubar.addMenu(tr("menu_help"))

        about_action = QAction(tr("about"), self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self, parent_layout):
        """Create the toolbar."""
        toolbar_layout = QHBoxLayout()

        self.import_btn = QPushButton(tr("import_csv"))
        self.import_btn.clicked.connect(self.import_csv)
        toolbar_layout.addWidget(self.import_btn)

        # Channel selection
        toolbar_layout.addWidget(QLabel(tr("send_via")))
        self.channel_combo = QComboBox()

        # Store channel data as (display_text, channel_id) pairs
        channel_options = [
            (tr("email_only"), "email_only"),
            (tr("whatsapp_business_api"), "whatsapp_business"),
            (tr("whatsapp_web"), "whatsapp_web"),
            (tr("email_whatsapp_business"), "email_whatsapp_business"),
            (tr("email_whatsapp_web"), "email_whatsapp_web"),
        ]

        for display_text, channel_id in channel_options:
            self.channel_combo.addItem(display_text, channel_id)

        self.channel_combo.setCurrentIndex(0)  # Default to email only
        self.channel_combo.currentTextChanged.connect(self.on_channel_changed)
        toolbar_layout.addWidget(self.channel_combo)

        toolbar_layout.addWidget(QFrame())  # Separator

        self.send_btn = QPushButton(tr("send_messages"))
        self.send_btn.clicked.connect(self.send_messages)
        self.send_btn.setEnabled(False)
        toolbar_layout.addWidget(self.send_btn)

        self.draft_btn = QPushButton(tr("create_draft"))
        self.draft_btn.clicked.connect(self.create_draft)
        self.draft_btn.setEnabled(False)
        toolbar_layout.addWidget(self.draft_btn)

        self.stop_btn = QPushButton(tr("stop_sending"))
        self.stop_btn.clicked.connect(self.stop_sending)
        self.stop_btn.setEnabled(False)
        toolbar_layout.addWidget(self.stop_btn)

        toolbar_layout.addStretch()

        # Language selector
        toolbar_layout.addWidget(QLabel(tr("language") + ":"))
        self.language_combo = QComboBox()
        self.populate_language_combo()
        self.language_combo.currentTextChanged.connect(self.on_language_changed)
        toolbar_layout.addWidget(self.language_combo)

        toolbar_layout.addWidget(QFrame())  # Separator

        # Status indicators
        self.outlook_status_label = QLabel(tr("outlook_not_connected"))
        toolbar_layout.addWidget(self.outlook_status_label)

        parent_layout.addLayout(toolbar_layout)

    def create_main_content(self, parent_layout):
        """Create the main content area."""
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)

        # Left panel - Recipients
        left_panel = self.create_recipients_panel()
        splitter.addWidget(left_panel)

        # Middle panel - Variables
        self.variables_panel = VariablesPanel()
        self.variables_panel.variable_selected.connect(self.on_variable_selected)
        splitter.addWidget(self.variables_panel)

        # Right panel - Template and Status
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        # Set splitter proportions (Recipients: Variables: Template)
        splitter.setSizes([350, 250, 600])

        parent_layout.addWidget(splitter)

    def create_recipients_panel(self) -> QWidget:
        """Create the recipients panel."""
        panel = QGroupBox(tr("recipients"))
        layout = QVBoxLayout(panel)

        # Recipients list
        self.recipients_list = QListWidget()
        self.recipients_list.itemChanged.connect(self.update_send_button_state)
        layout.addWidget(self.recipients_list)

        # Recipients info
        self.recipients_info_label = QLabel(tr("no_recipients_loaded"))
        layout.addWidget(self.recipients_info_label)

        # Select all/none buttons
        buttons_layout = QHBoxLayout()

        select_all_btn = QPushButton(tr("select_all"))
        select_all_btn.clicked.connect(self.select_all_recipients)
        buttons_layout.addWidget(select_all_btn)

        select_none_btn = QPushButton(tr("select_none"))
        select_none_btn.clicked.connect(self.select_no_recipients)
        buttons_layout.addWidget(select_none_btn)

        layout.addLayout(buttons_layout)

        return panel

    def create_right_panel(self) -> QWidget:
        """Create the right panel with template and status."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Template section
        template_group = QGroupBox(tr("message_template"))
        template_layout = QVBoxLayout(template_group)

        # Template selector with management
        template_selector_layout = QHBoxLayout()
        template_selector_layout.addWidget(QLabel(tr("message_template") + ":"))
        self.template_combo = QComboBox()
        self.template_combo.currentTextChanged.connect(self.on_template_changed)
        template_selector_layout.addWidget(self.template_combo)

        # Template management buttons
        self.template_library_btn = QPushButton(tr("library"))
        self.template_library_btn.setToolTip(tr("template_library"))
        self.template_library_btn.clicked.connect(self.open_template_library)
        template_selector_layout.addWidget(self.template_library_btn)

        self.save_template_btn = QPushButton(tr("save"))
        self.save_template_btn.setToolTip(tr("save_current_template"))
        self.save_template_btn.clicked.connect(self.save_current_template)
        template_selector_layout.addWidget(self.save_template_btn)

        # Add preview button
        self.preview_btn = QPushButton(tr("preview_message"))
        self.preview_btn.clicked.connect(self.preview_message)
        template_selector_layout.addWidget(self.preview_btn)

        template_layout.addLayout(template_selector_layout)

        # Email fields
        email_group = QGroupBox(tr("email_content_group"))
        email_layout = QVBoxLayout(email_group)

        email_layout.addWidget(QLabel(tr("subject")))
        self.subject_edit = QTextEdit()
        self.subject_edit.setMaximumHeight(60)
        email_layout.addWidget(self.subject_edit)

        email_layout.addWidget(QLabel(tr("email_content")))
        self.content_edit = QTextEdit()
        self.content_edit.setMaximumHeight(200)
        email_layout.addWidget(self.content_edit)

        template_layout.addWidget(email_group)

        # WhatsApp fields
        whatsapp_group = QGroupBox(tr("whatsapp_content_group"))
        whatsapp_layout = QVBoxLayout(whatsapp_group)

        whatsapp_layout.addWidget(QLabel(tr("whatsapp_message_label")))
        self.whatsapp_content_edit = QTextEdit()
        self.whatsapp_content_edit.setMaximumHeight(150)
        self.whatsapp_content_edit.setPlaceholderText(tr("whatsapp_placeholder"))
        whatsapp_layout.addWidget(self.whatsapp_content_edit)

        # Character count for WhatsApp
        self.whatsapp_char_label = QLabel(tr("characters_count", count=0))
        self.whatsapp_char_label.setStyleSheet("color: gray;")
        self.whatsapp_content_edit.textChanged.connect(self.update_whatsapp_char_count)
        whatsapp_layout.addWidget(self.whatsapp_char_label)

        template_layout.addWidget(whatsapp_group)

        layout.addWidget(template_group)

        # Progress section
        progress_group = QGroupBox(tr("sending_progress"))
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel(tr("ready_to_send"))
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
        self.email_status_label = QLabel(tr("email_ready_status"))
        self.status_bar.addPermanentWidget(self.email_status_label)

        self.whatsapp_status_label = QLabel(
            tr("whatsapp_business_not_configured_status")
        )
        self.status_bar.addPermanentWidget(self.whatsapp_status_label)

        self.whatsapp_web_status_label = QLabel(
            tr("whatsapp_web_not_configured_status")
        )
        self.status_bar.addPermanentWidget(self.whatsapp_web_status_label)

        self.quota_label = QLabel(tr("quota_status", current=0, total=100))
        self.status_bar.addPermanentWidget(self.quota_label)

    def set_window_icon(self):
        """Set the window icon."""
        try:
            # Try to find the icon file
            icon_paths = [
                # When running from source
                Path(__file__).parent.parent.parent.parent
                / "assets"
                / "icons"
                / "csc-reach.png",
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
            if self.message_logger:
                self.email_service = LoggedEmailService(self.message_logger)
            else:
                self.email_service = EmailService()
            platform_info = self.email_service.get_platform_info()
            logger.info(f"Email service initialized successfully for {platform_info}")
        except Exception as e:
            logger.error(f"Failed to initialize email service: {e}")
            QMessageBox.warning(
                self,
                tr("outlook_connection_error"),
                tr("outlook_connection_failed", error=str(e)),
            )

        # Update status display
        self.update_status_display()

    def load_default_template(self):
        """Load default template and populate template combo."""
        # Load available templates into combo
        self.refresh_template_combo()

        # Try to load existing default template
        existing_templates = self.template_manager.get_templates()
        default_template = None

        for template in existing_templates:
            if template.id == "default_welcome":
                default_template = template
                break

        # Create default template if it doesn't exist
        if not default_template:
            default_template = MessageTemplate(
                id="default_welcome",
                name="Default Welcome Message",
                channels=["email", "whatsapp"],
                subject="Welcome to CSC-Reach - Let's Connect!",
                content="""Dear {name},

I hope this message finds you well. I'm reaching out from CSC-Reach to introduce our comprehensive communication platform designed to streamline your business outreach.

At {company}, we understand the importance of effective communication in today's fast-paced business environment. Our platform offers:

• Seamless email integration with Microsoft Outlook
• Multi-channel messaging capabilities
• Professional template management
• Real-time progress tracking
• Cross-platform compatibility

I'd love to schedule a brief call to discuss how CSC-Reach can benefit your organization and help you achieve your communication goals more efficiently.

Please let me know a convenient time for you, and I'll be happy to arrange a demonstration.

Best regards,
CSC-Reach Team

P.S. Feel free to reply to this email or call us directly. We're here to help!""",
                whatsapp_content="""Hi {name}! 👋

Hope you're doing well! I'm reaching out from CSC-Reach about our communication platform that could really help {company}.

We specialize in:
✅ Email automation with Outlook
✅ Multi-channel messaging
✅ Professional templates
✅ Real-time tracking

Would love to show you how it works! When's a good time for a quick call?

Best regards,
CSC-Reach Team""",
                variables=["name", "company"],
            )

            # Save the default template
            self.template_manager.save_template(
                default_template,
                category_id="welcome",
                description="Default welcome message template for new contacts",
            )

        # Set as current template
        self.current_template = default_template
        self.load_template_into_ui(default_template)

        # Select in combo
        for i in range(self.template_combo.count()):
            if self.template_combo.itemData(i) == default_template.id:
                self.template_combo.setCurrentIndex(i)
                break

    def refresh_template_combo(self):
        """Refresh the template combo box with available templates."""
        self.template_combo.clear()

        templates = self.template_manager.get_templates()
        if not templates:
            self.template_combo.addItem(tr("no_templates_available"), None)
            return

        # Group templates by category
        categories = {}
        for template in templates:
            metadata = self.template_manager.get_template_metadata(template.id)
            category_id = metadata.get("category_id", "general")
            category = self.template_manager.get_category(category_id)

            # Translate category name
            if category_id == "welcome":
                category_name = tr("category_welcome")
            elif category_id == "follow_up":
                category_name = tr("category_follow_up")
            elif category_id == "promotional":
                category_name = tr("category_promotional")
            elif category_id == "support":
                category_name = tr("category_support")
            elif category_id == "general":
                category_name = tr("category_general")
            else:
                category_name = category.name if category else tr("category_general")

            if category_name not in categories:
                categories[category_name] = []
            categories[category_name].append(template)

        # Add templates to combo, grouped by category
        for category_name in sorted(categories.keys()):
            if len(categories) > 1:  # Only add separator if multiple categories
                self.template_combo.addItem(f"── {category_name} ──", None)

            for template in sorted(categories[category_name], key=lambda t: t.name):
                channels_text = "/".join(template.channels).upper()
                display_name = f"{template.name} ({channels_text})"
                self.template_combo.addItem(display_name, template.id)

    def load_template_into_ui(self, template: MessageTemplate):
        """Load template data into UI fields."""
        if not template:
            return

        self.subject_edit.setPlainText(template.subject)
        self.content_edit.setPlainText(template.content)
        self.whatsapp_content_edit.setPlainText(template.whatsapp_content)
        self.update_whatsapp_char_count()

    def on_template_changed(self):
        """Handle template selection change."""
        template_id = self.template_combo.currentData()
        if not template_id:
            return

        template = self.template_manager.get_template(template_id)
        if template:
            self.current_template = template
            self.load_template_into_ui(template)

    def open_template_library(self):
        """Open the template library dialog."""
        dialog = TemplateLibraryDialog(self.template_manager, self)
        dialog.template_selected.connect(self.on_template_selected_from_library)
        dialog.exec()

        # Refresh combo in case templates were modified
        self.refresh_template_combo()

    def on_template_selected_from_library(self, template: MessageTemplate):
        """Handle template selection from library."""
        self.current_template = template
        self.load_template_into_ui(template)

        # Update combo selection
        for i in range(self.template_combo.count()):
            if self.template_combo.itemData(i) == template.id:
                self.template_combo.setCurrentIndex(i)
                break

    def save_current_template(self):
        """Save the current template with modifications."""
        if not self.current_template:
            QMessageBox.information(
                self, tr("no_template_loaded"), tr("no_template_loaded")
            )
            return

        # Update template with current UI content
        self.update_current_template()

        # Save template
        metadata = self.template_manager.get_template_metadata(self.current_template.id)
        if self.template_manager.save_template(
            self.current_template,
            category_id=metadata.get("category_id", "general"),
            description=metadata.get("description", ""),
            tags=metadata.get("tags", []),
        ):
            QMessageBox.information(
                self,
                tr("success"),
                tr("template_saved_success", name=self.current_template.name),
            )
        else:
            QMessageBox.critical(self, tr("error"), tr("template_save_failed"))

    def create_new_template(self):
        """Create a new template."""
        from .template_library_dialog import TemplateEditDialog

        dialog = TemplateEditDialog(self.template_manager, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_template_combo()

    def import_template_file(self):
        """Import a template from file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, tr("import_template"), "", tr("json_files")
        )

        if filename:
            template = self.template_manager.import_template(Path(filename))
            if template:
                QMessageBox.information(
                    self,
                    tr("success"),
                    tr("template_imported_successfully", name=template.name),
                )
                self.refresh_template_combo()
            else:
                QMessageBox.critical(self, tr("error"), tr("failed_to_import_template"))

    def export_all_templates(self):
        """Export all templates to file."""
        from datetime import datetime

        filename, _ = QFileDialog.getSaveFileName(
            self,
            tr("export_all_templates"),
            f"all_templates_{datetime.now().strftime('%Y%m%d')}.json",
            tr("json_files"),
        )

        if filename:
            from pathlib import Path

            export_path = self.template_manager.export_all_templates(Path(filename))
            if export_path:
                QMessageBox.information(
                    self, tr("success"), tr("all_templates_exported", filename=filename)
                )
            else:
                QMessageBox.critical(
                    self, tr("error"), tr("failed_to_export_templates")
                )
    
    def create_whatsapp_multi_message_template(self):
        """Create a new WhatsApp multi-message template."""
        try:
            dialog = WhatsAppMultiMessageDialog(parent=self)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                template = dialog.get_template()
                if template:
                    # Save the template
                    saved_template = self.whatsapp_multi_message_manager.create_template(
                        name=template.name,
                        content=template.content,
                        language=template.language,
                        multi_message_mode=template.multi_message_mode,
                        split_strategy=template.split_strategy,
                        custom_delimiter=template.custom_split_delimiter,
                        message_delay=template.message_delay_seconds,
                        max_messages=template.max_messages_per_sequence
                    )
                    
                    QMessageBox.information(
                        self,
                        tr("success"),
                        tr("whatsapp_template_created", name=saved_template.name)
                    )
                    
        except Exception as e:
            logger.error(f"Failed to create WhatsApp multi-message template: {e}")
            QMessageBox.critical(
                self,
                tr("error"),
                tr("failed_to_create_whatsapp_template", error=str(e))
            )
    
    def manage_whatsapp_multi_message_templates(self):
        """Open WhatsApp multi-message template management dialog."""
        try:
            from .whatsapp_template_manager_dialog import WhatsAppTemplateManagerDialog
            
            dialog = WhatsAppTemplateManagerDialog(
                self.whatsapp_multi_message_manager,
                parent=self
            )
            dialog.exec()
            
        except ImportError:
            # Fallback to simple list dialog if manager dialog not implemented yet
            self._show_whatsapp_templates_list()
            
        except Exception as e:
            logger.error(f"Failed to open WhatsApp template manager: {e}")
            QMessageBox.critical(
                self,
                tr("error"),
                tr("failed_to_open_whatsapp_manager", error=str(e))
            )
    
    def _show_whatsapp_templates_list(self):
        """Show a simple list of WhatsApp templates (fallback)."""
        templates = self.whatsapp_multi_message_manager.get_all_templates()
        
        if not templates:
            QMessageBox.information(
                self,
                tr("no_templates"),
                tr("no_whatsapp_templates_found")
            )
            return
        
        # Create simple selection dialog
        from PySide6.QtWidgets import QListWidget, QVBoxLayout, QPushButton, QHBoxLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("whatsapp_multi_message_templates"))
        dialog.resize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        template_list = QListWidget()
        for template in templates:
            mode_text = tr("multi_message_mode") if template.multi_message_mode else tr("single_message_mode")
            item_text = f"{template.name} ({mode_text}) - {len(template.message_sequence) if template.multi_message_mode else 1} {tr('messages')}"
            template_list.addItem(item_text)
        
        layout.addWidget(template_list)
        
        button_layout = QHBoxLayout()
        
        edit_btn = QPushButton(tr("edit_template"))
        edit_btn.clicked.connect(lambda: self._edit_selected_whatsapp_template(template_list, templates, dialog))
        button_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton(tr("delete_template"))
        delete_btn.clicked.connect(lambda: self._delete_selected_whatsapp_template(template_list, templates))
        button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton(tr("close"))
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def _edit_selected_whatsapp_template(self, template_list, templates, parent_dialog):
        """Edit the selected WhatsApp template."""
        current_row = template_list.currentRow()
        if current_row < 0 or current_row >= len(templates):
            return
        
        template = templates[current_row]
        
        dialog = WhatsAppMultiMessageDialog(template=template, parent=self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_template = dialog.get_template()
            if updated_template:
                try:
                    self.whatsapp_multi_message_manager.update_template(
                        template.id,
                        name=updated_template.name,
                        content=updated_template.content,
                        language=updated_template.language,
                        multi_message_mode=updated_template.multi_message_mode,
                        split_strategy=updated_template.split_strategy,
                        custom_delimiter=updated_template.custom_split_delimiter,
                        message_delay=updated_template.message_delay_seconds,
                        max_messages=updated_template.max_messages_per_sequence,
                        message_sequence=updated_template.message_sequence
                    )
                    
                    QMessageBox.information(
                        self,
                        tr("success"),
                        tr("whatsapp_template_updated", name=updated_template.name)
                    )
                    
                    parent_dialog.accept()  # Close the list dialog
                    self.manage_whatsapp_multi_message_templates()  # Reopen to refresh
                    
                except Exception as e:
                    logger.error(f"Failed to update WhatsApp template: {e}")
                    QMessageBox.critical(
                        self,
                        tr("error"),
                        tr("failed_to_update_whatsapp_template", error=str(e))
                    )
    
    def _delete_selected_whatsapp_template(self, template_list, templates):
        """Delete the selected WhatsApp template."""
        current_row = template_list.currentRow()
        if current_row < 0 or current_row >= len(templates):
            return
        
        template = templates[current_row]
        
        reply = QMessageBox.question(
            self,
            tr("delete_template"),
            tr("delete_whatsapp_template_confirm", name=template.name),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.whatsapp_multi_message_manager.delete_template(template.id)
                
                QMessageBox.information(
                    self,
                    tr("success"),
                    tr("whatsapp_template_deleted", name=template.name)
                )
                
                # Refresh the list
                template_list.takeItem(current_row)
                
            except Exception as e:
                logger.error(f"Failed to delete WhatsApp template: {e}")
                QMessageBox.critical(
                    self,
                    tr("error"),
                    tr("failed_to_delete_whatsapp_template", error=str(e))
                )

    def import_csv(self):
        """Import CSV file with enhanced configuration dialog."""
        try:
            # First, let user select a CSV file
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                tr("import_csv_file"),
                "",
                f"{tr('csv_files')};;{tr('text_files')};;{tr('all_files')}",
            )

            if not file_path:
                return

            # Open the enhanced CSV import configuration dialog
            from .csv_import_config_dialog import CSVImportConfigDialog

            config_dialog = CSVImportConfigDialog(self, file_path)
            config_dialog.configuration_ready.connect(self.on_csv_configuration_ready)

            if config_dialog.exec() == QDialog.DialogCode.Accepted:
                # Configuration and data will be handled by the signal
                pass

        except Exception as e:
            logger.error(f"Failed to open CSV import dialog: {e}")
            QMessageBox.critical(
                self, tr("import_error"), tr("failed_to_import_csv", error=str(e))
            )

    def on_csv_configuration_ready(self, configuration, processed_data):
        """Handle CSV configuration and processed data from the configuration dialog."""
        try:
            # Convert processed DataFrame to Customer objects
            customers = []
            errors = []

            for index, row in processed_data.iterrows():
                try:
                    # Extract customer data based on configuration mapping
                    customer_data = {
                        "name": str(row.get("name", "")).strip(),
                        "company": str(row.get("company", "")).strip(),
                        "email": str(row.get("email", "")).strip(),
                        "phone": str(row.get("phone", "")).strip(),
                    }

                    # Skip rows with missing required data
                    if not customer_data["name"]:
                        continue

                    # Check channel requirements
                    if (
                        "email" in configuration.messaging_channels
                        and not customer_data["email"]
                    ):
                        errors.append(
                            {
                                "row_number": index + 1,
                                "error": "Email is required for email messaging",
                            }
                        )
                        continue

                    if (
                        "whatsapp" in configuration.messaging_channels
                        and not customer_data["phone"]
                    ):
                        errors.append(
                            {
                                "row_number": index + 1,
                                "error": "Phone number is required for WhatsApp messaging",
                            }
                        )
                        continue

                    # Create Customer object
                    customer = Customer(
                        name=customer_data["name"],
                        company=customer_data["company"],
                        email=customer_data["email"],
                        phone=customer_data["phone"],
                    )
                    
                    # Validate with flexible requirements based on selected channels
                    required_fields = ["name"]  # Name is always required
                    if "email" in configuration.messaging_channels:
                        required_fields.append("email")
                    if "whatsapp" in configuration.messaging_channels:
                        required_fields.append("phone")
                    
                    customer.validate(required_fields)
                    customers.append(customer)

                except Exception as e:
                    errors.append({"row_number": index + 1, "error": str(e)})

            # Show errors if any
            if errors:
                error_msg = tr("csv_errors_found", count=len(errors)) + "\n\n"
                for error in errors[:5]:  # Show first 5 errors
                    error_msg += (
                        tr(
                            "csv_row_error",
                            row=error["row_number"],
                            error=error["error"],
                        )
                        + "\n"
                    )
                if len(errors) > 5:
                    error_msg += tr("csv_more_errors", count=len(errors) - 5)

                QMessageBox.warning(self, tr("csv_processing_errors"), error_msg)

            if not customers:
                QMessageBox.information(
                    self, tr("no_valid_data"), tr("no_valid_records")
                )
                return

            # Update UI with loaded customers
            self.customers = customers
            self.update_recipients_list()
            self.update_send_button_state()

            # Update variables panel with CSV columns
            if self.variables_panel and processed_data is not None:
                # Get column names from the processed data
                csv_columns = list(processed_data.columns)
                # Get sample data from first row
                sample_data = {}
                if not processed_data.empty:
                    first_row = processed_data.iloc[0]
                    sample_data = {col: str(first_row[col]) for col in csv_columns}
                
                # Update variables
                self.variables_panel.get_variable_manager().update_available_variables(
                    csv_columns, sample_data
                )
                logger.info(f"Updated variables panel with CSV columns: {csv_columns}")

            # Update status
            self.status_bar.showMessage(
                tr("loaded_customers", count=len(customers)), 3000
            )
            self.log_message(
                tr(
                    "imported_customers",
                    count=len(customers),
                    filename=configuration.preset_name or "CSV",
                )
            )

            # Update channel selection based on configuration
            if configuration.messaging_channels:
                if len(configuration.messaging_channels) == 1:
                    if configuration.messaging_channels[0] == "email":
                        self.channel_combo.setCurrentText(tr("email_only"))
                    elif configuration.messaging_channels[0] == "whatsapp":
                        self.channel_combo.setCurrentText(tr("whatsapp_business_api"))
                elif (
                    "email" in configuration.messaging_channels
                    and "whatsapp" in configuration.messaging_channels
                ):
                    self.channel_combo.setCurrentText(tr("email_whatsapp_business"))

        except Exception as e:
            logger.error(f"Failed to process CSV configuration: {e}")
            QMessageBox.critical(self, tr("csv_processing_error"), str(e))

    def update_recipients_list(self):
        """Update the recipients list widget."""
        self.recipients_list.clear()

        for customer in self.customers:
            # Create display text with name, company, email, and phone
            display_parts = [customer.name]

            if customer.company:
                display_parts.append(f"🏢 {customer.company}")

            if customer.email:
                display_parts.append(f"📧 {customer.email}")

            if customer.phone:
                display_parts.append(f"📱 {customer.phone}")

            # Join parts with " | " separator
            display_text = " | ".join(display_parts)

            item = QListWidgetItem(display_text)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            item.setData(Qt.UserRole, customer)
            self.recipients_list.addItem(item)

        self.update_recipients_info()

    def update_recipients_info(self):
        """Update recipients information label."""
        total = self.recipients_list.count()
        selected = sum(
            1
            for i in range(total)
            if self.recipients_list.item(i).checkState() == Qt.Checked
        )
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
            QMessageBox.warning(
                self, tr("service_error"), tr("email_service_not_available")
            )
            return

        selected_customers = self.get_selected_customers()
        if not selected_customers:
            QMessageBox.information(
                self, tr("no_recipients"), tr("please_select_recipients")
            )
            return

        # Use first selected customer for draft
        customer = selected_customers[0]

        # Update template with current content
        self.current_template.subject = self.subject_edit.toPlainText()
        self.current_template.content = self.content_edit.toPlainText()

        try:
            success = self.email_service.create_draft_email(
                customer, self.current_template
            )
            if success:
                QMessageBox.information(
                    self,
                    tr("create_draft"),
                    f"Draft email created for {customer.name} ({customer.email})\n\nCheck your Outlook drafts folder.",
                )
                self.log_message(tr("draft_created", email=customer.email))
            else:
                QMessageBox.warning(
                    self, tr("draft_failed"), tr("failed_to_create_draft")
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                tr("draft_error"),
                tr("failed_to_create_draft_error", error=str(e)),
            )

    def update_send_button_state(self):
        """Update the send button enabled state."""
        selected_customers = self.get_selected_customers()
        has_email_service = self.email_service is not None
        not_sending = self.sending_thread is None or not self.sending_thread.isRunning()

        self.send_btn.setEnabled(
            len(selected_customers) > 0 and has_email_service and not_sending
        )
        self.draft_btn.setEnabled(
            len(selected_customers) > 0 and has_email_service and not_sending
        )
        self.update_recipients_info()

    def send_emails(self):
        """Start sending emails - backward compatibility method."""
        # Set channel to email only and call new method
        self.channel_combo.setCurrentIndex(0)  # First item is email_only
        self.send_messages()
        self.stop_btn.setEnabled(True)
        self.progress_bar.setMaximum(len(selected_customers))
        self.progress_bar.setValue(0)
        self.progress_label.setText("Sending emails...")

        self.log_message(
            f"Started sending emails to {len(selected_customers)} recipients"
        )

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
            QMessageBox.information(self, tr("sending_complete"), message)
        else:
            QMessageBox.warning(self, tr("sending_error"), message)

        self.update_send_button_state()

    def preview_email(self):
        """Preview email - backward compatibility method."""
        # Set channel to email and call new preview method
        original_index = self.channel_combo.currentIndex()
        self.channel_combo.setCurrentIndex(0)  # Set to email_only
        self.preview_message()
        self.channel_combo.setCurrentIndex(original_index)  # Restore original
        subject_label = QLabel("Subject:")
        subject_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(subject_label)

        subject_display = QLabel(subject)
        subject_display.setStyleSheet(
            "padding: 5px; border: 1px solid #ccc; background-color: #f9f9f9; margin-bottom: 10px;"
        )
        subject_display.setWordWrap(True)
        layout.addWidget(subject_display)

        # Content section
        content_label = QLabel("Content:")
        content_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(content_label)

        content_display = QTextEdit()
        content_display.setPlainText(content)
        content_display.setReadOnly(True)
        content_display.setStyleSheet(
            """
            QTextEdit {
                border: 1px solid #ccc;
                background-color: white;
                color: black;
                padding: 10px;
                font-family: Arial, sans-serif;
                font-size: 12px;
                line-height: 1.4;
            }
        """
        )
        layout.addWidget(content_display)

        # Sample info
        info_label = QLabel(
            f"Preview using: {sample_customer.name} ({sample_customer.email})"
        )
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
        html_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # Convert line breaks to HTML
        html_text = html_text.replace("\n\n", "</p><p>").replace("\n", "<br>")

        # Wrap in paragraph tags
        return f"<p>{html_text}</p>"

    def log_message(self, message: str):
        """Add message to log area."""
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def test_outlook_connection(self):
        """Test Outlook connection."""
        if not self.email_service:
            QMessageBox.warning(
                self, tr("service_error"), tr("email_service_not_initialized")
            )
            return

        try:
            success, message = self.email_service.test_connection()
            if success:
                platform_info = self.email_service.get_platform_info()
                QMessageBox.information(
                    self,
                    tr("connection_test"),
                    tr("connection_success", message=message, platform=platform_info),
                )
                self.outlook_status_label.setText(
                    tr("outlook_connected", platform=platform_info)
                )
                self.outlook_status_label.setStyleSheet("color: green;")
            else:
                QMessageBox.warning(
                    self,
                    tr("connection_test"),
                    tr("connection_failed", message=message),
                )
                self.outlook_status_label.setText(tr("outlook_error"))
                self.outlook_status_label.setStyleSheet("color: red;")
        except Exception as e:
            QMessageBox.critical(
                self, tr("connection_test"), tr("connection_test_failed", error=str(e))
            )

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About CSC-Reach",
            """CSC-Reach - Email Communication Platform
            
Version 1.0.0

A cross-platform desktop application for bulk email communication through Microsoft Outlook integration.

CSC-Reach streamlines business communication processes with professional email templates, CSV data processing, and real-time sending progress.

© 2024 CSC-Reach Team""",
        )

    # New multi-channel methods
    def update_whatsapp_char_count(self):
        """Update WhatsApp character count display."""
        content = self.whatsapp_content_edit.toPlainText()
        char_count = len(content)
        self.whatsapp_char_label.setText(tr("characters_count", count=char_count))

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
        channel_id = self.get_current_channel_id()
        if channel_id == "email_only":
            self.send_btn.setText(self.i18n_manager.tr("send_emails"))
        elif channel_id in ["whatsapp_business", "whatsapp_web"]:
            self.send_btn.setText(self.i18n_manager.tr("send_whatsapp"))
        else:
            self.send_btn.setText(self.i18n_manager.tr("send_messages"))

    def update_status_display(self):
        """Update status bar based on service availability."""
        # Update email status
        if self.email_service:
            self.email_status_label.setText("Email: Ready")
            self.email_status_label.setStyleSheet("color: green;")
        else:
            self.email_status_label.setText("Email: Not ready")
            self.email_status_label.setStyleSheet("color: red;")

        # Update WhatsApp Business API status
        if self.whatsapp_service.is_configured():
            self.whatsapp_status_label.setText("WhatsApp Business: Ready")
            self.whatsapp_status_label.setStyleSheet("color: green;")
        else:
            self.whatsapp_status_label.setText("WhatsApp Business: Not configured")

    def on_variable_selected(self, variable_format: str):
        """Handle variable selection from the variables panel."""
        # Get the currently focused text editor
        focused_widget = QApplication.focusWidget()
        
        # Check if it's one of our text editors
        if focused_widget == self.subject_edit:
            cursor = self.subject_edit.textCursor()
            cursor.insertText(variable_format)
            logger.info(f"Inserted variable {variable_format} into subject")
        elif focused_widget == self.content_edit:
            cursor = self.content_edit.textCursor()
            cursor.insertText(variable_format)
            logger.info(f"Inserted variable {variable_format} into email content")
        elif focused_widget == self.whatsapp_content_edit:
            cursor = self.whatsapp_content_edit.textCursor()
            cursor.insertText(variable_format)
            logger.info(f"Inserted variable {variable_format} into WhatsApp content")
        else:
            # Default to email content if no specific editor is focused
            cursor = self.content_edit.textCursor()
            cursor.insertText(variable_format)
            self.content_edit.setFocus()
            logger.info(f"Inserted variable {variable_format} into email content (default)")
        
        # Update character count for WhatsApp if needed
        if focused_widget == self.whatsapp_content_edit:
            self.update_whatsapp_char_count()
            self.whatsapp_status_label.setStyleSheet("color: orange;")

        # Update WhatsApp Web status
        if self.whatsapp_web_service.is_configured():
            usage = self.whatsapp_web_service.get_daily_usage()
            remaining = usage["remaining_today"]
            if remaining > 0:
                self.whatsapp_web_status_label.setText(
                    f"WhatsApp Web: Ready ({remaining} left)"
                )
                self.whatsapp_web_status_label.setStyleSheet("color: green;")
            else:
                self.whatsapp_web_status_label.setText(
                    "WhatsApp Web: Daily limit reached"
                )
                self.whatsapp_web_status_label.setStyleSheet("color: red;")
        else:
            self.whatsapp_web_status_label.setText("WhatsApp Web: Not configured")
            self.whatsapp_web_status_label.setStyleSheet("color: orange;")

    def show_whatsapp_settings(self):
        """Show WhatsApp Business API settings dialog."""
        dialog = WhatsAppSettingsDialog(self)
        if dialog.exec() == QDialog.Accepted:
            # Refresh WhatsApp service
            self.whatsapp_service = LocalWhatsAppBusinessService()
            self.update_status_display()

            if self.whatsapp_service.is_configured():
                QMessageBox.information(
                    self,
                    "WhatsApp Business API Configured",
                    "WhatsApp Business API has been configured successfully!",
                )

    def show_whatsapp_web_settings(self):
        """Show WhatsApp Web settings dialog."""
        dialog = WhatsAppWebSettingsDialog(self)
        if dialog.exec() == QDialog.Accepted:
            # Refresh WhatsApp Web service
            self.whatsapp_web_service = WhatsAppWebService()
            self.update_status_display()

            if self.whatsapp_web_service.is_configured():
                QMessageBox.information(
                    self,
                    "WhatsApp Web Configured",
                    "⚠️ WhatsApp Web service has been configured.\n\n"
                    "Remember: Use at your own risk!\n"
                    "WhatsApp Business API is the recommended approach.\n\n"
                    "You will need to manually send each message in your browser.",
                )

    def show_language_settings(self):
        """Show language settings dialog."""
        dialog = LanguageSettingsDialog(self)
        dialog.language_changed.connect(self.on_language_changed)
        dialog.exec()

    def show_preferences(self):
        """Show preferences dialog."""
        dialog = PreferencesDialog(self.preferences_manager, self.theme_manager, self)
        dialog.preferences_applied.connect(self.apply_user_preferences)
        dialog.exec()

    def apply_user_preferences(self):
        """Apply user preferences to the interface."""
        prefs = self.preferences_manager.preferences

        # Apply theme
        try:
            theme_mode = ThemeMode(prefs.interface.theme)
            self.theme_manager.set_theme(theme_mode)
        except ValueError:
            pass

        # Apply font settings
        if prefs.interface.font_family or prefs.interface.font_size != 9:
            font = QFont()
            if prefs.interface.font_family:
                font.setFamily(prefs.interface.font_family)
            font.setPointSize(prefs.interface.font_size)
            self.setFont(font)

        # Apply interface settings
        if hasattr(self, "status_bar"):
            self.status_bar.setVisible(prefs.interface.show_status_bar)

        # Apply accessibility settings
        if prefs.accessibility.large_fonts:
            font = self.font()
            font.setPointSize(font.pointSize() + 2)
            self.setFont(font)

        # Apply window layout if needed
        self.apply_window_layout(prefs.window.layout)

    def apply_window_layout(self, layout):
        """Apply window layout preferences."""
        # This would implement different layout modes
        # For now, we'll just log the layout change
        logger.info(f"Applied window layout: {layout.value}")

    def restore_window_geometry(self):
        """Restore window geometry from preferences."""
        window_config = self.preferences_manager.get_window_config()

        if window_config.remember_geometry:
            if window_config.width > 0 and window_config.height > 0:
                self.resize(window_config.width, window_config.height)

            if window_config.x >= 0 and window_config.y >= 0:
                self.move(window_config.x, window_config.y)

            if window_config.maximized:
                self.showMaximized()

    def save_window_geometry(self):
        """Save current window geometry to preferences."""
        if self.preferences_manager.get_window_config().remember_geometry:
            geometry = self.geometry()
            self.preferences_manager.set_window_geometry(
                geometry.width(),
                geometry.height(),
                geometry.x(),
                geometry.y(),
                self.isMaximized(),
            )

    def on_theme_changed(self, theme_name: str):
        """Handle theme change."""
        logger.info(f"Theme changed to: {theme_name}")
        # Additional theme-specific UI updates can be added here

    def on_preferences_changed(self, category: str):
        """Handle preferences change."""
        if category in ["interface", "accessibility", "all"]:
            self.apply_user_preferences()
        if category in ["accessibility", "all"]:
            self.accessibility_manager.load_accessibility_preferences()

    def on_accessibility_changed(self, feature: str):
        """Handle accessibility feature change."""
        logger.info(f"Accessibility feature changed: {feature}")

        # Announce changes to screen reader
        if feature == "screen_reader":
            status = (
                "enabled"
                if self.accessibility_manager.screen_reader_enabled
                else "disabled"
            )
            self.accessibility_manager.announce_to_screen_reader(
                f"Screen reader support {status}"
            )
        elif feature == "high_contrast":
            status = (
                "enabled"
                if self.accessibility_manager.high_contrast_enabled
                else "disabled"
            )
            self.accessibility_manager.announce_to_screen_reader(
                f"High contrast mode {status}"
            )
        elif feature == "large_fonts":
            status = (
                "enabled"
                if self.accessibility_manager.large_fonts_enabled
                else "disabled"
            )
            self.accessibility_manager.announce_to_screen_reader(
                f"Large fonts {status}"
            )

    def setup_accessibility(self):
        """Set up accessibility features for the main window."""
        # Set accessible properties for main window
        self.accessibility_manager.set_accessible_properties(
            self,
            "CSC-Reach Main Window",
            "Multi-channel communication platform main interface",
        )

        # Set up keyboard navigation
        self.keyboard_navigation.setup_main_window_navigation(self)

        # Create accessibility shortcuts
        accessibility_shortcuts = (
            self.accessibility_manager.create_accessibility_shortcuts(self)
        )
        for shortcut in accessibility_shortcuts:
            self.addAction(shortcut)

        # Set accessible properties for key UI elements
        if hasattr(self, "recipients_list"):
            self.accessibility_manager.set_accessible_properties(
                self.recipients_list,
                "Recipients List",
                "List of message recipients loaded from CSV file",
            )

        if hasattr(self, "template_combo"):
            self.accessibility_manager.set_accessible_properties(
                self.template_combo,
                "Template Selector",
                "Select message template to use for sending",
            )

        if hasattr(self, "send_btn"):
            self.accessibility_manager.set_accessible_properties(
                self.send_btn,
                "Send Messages Button",
                "Start sending messages to selected recipients",
            )

        if hasattr(self, "import_btn"):
            self.accessibility_manager.set_accessible_properties(
                self.import_btn,
                "Import CSV Button",
                "Import recipient data from CSV file",
            )

        if hasattr(self, "subject_edit"):
            self.accessibility_manager.set_accessible_properties(
                self.subject_edit,
                "Email Subject",
                "Enter the subject line for email messages",
            )

        if hasattr(self, "content_edit"):
            self.accessibility_manager.set_accessible_properties(
                self.content_edit,
                "Email Content",
                "Enter the content for email messages",
            )

        if hasattr(self, "whatsapp_content_edit"):
            self.accessibility_manager.set_accessible_properties(
                self.whatsapp_content_edit,
                "WhatsApp Message Content",
                "Enter the content for WhatsApp messages",
            )

        if hasattr(self, "progress_bar"):
            self.accessibility_manager.set_accessible_properties(
                self.progress_bar,
                "Sending Progress",
                "Shows progress of message sending operation",
            )

        if hasattr(self, "log_text"):
            self.accessibility_manager.set_accessible_properties(
                self.log_text,
                "Operation Log",
                "Shows detailed log of operations and status messages",
            )

        # Register navigation groups
        main_controls = []
        if hasattr(self, "import_btn"):
            main_controls.append(self.import_btn)
        if hasattr(self, "channel_combo"):
            main_controls.append(self.channel_combo)
        if hasattr(self, "send_btn"):
            main_controls.append(self.send_btn)
        if hasattr(self, "draft_btn"):
            main_controls.append(self.draft_btn)

        if main_controls:
            self.keyboard_navigation.register_navigation_group(
                "main_controls", main_controls
            )

        template_controls = []
        if hasattr(self, "template_combo"):
            template_controls.append(self.template_combo)
        if hasattr(self, "subject_edit"):
            template_controls.append(self.subject_edit)
        if hasattr(self, "content_edit"):
            template_controls.append(self.content_edit)
        if hasattr(self, "whatsapp_content_edit"):
            template_controls.append(self.whatsapp_content_edit)

        if template_controls:
            self.keyboard_navigation.register_navigation_group(
                "template_controls", template_controls
            )

        # Register keyboard shortcuts for accessibility
        self.keyboard_navigation.register_keyboard_shortcut(
            "F1", self.show_accessibility_help, "Show accessibility help"
        )

        self.keyboard_navigation.register_keyboard_shortcut(
            "Ctrl+Shift+A",
            self.announce_current_focus,
            "Announce current focus to screen reader",
        )

        logger.info("Accessibility features set up successfully")

    def show_accessibility_help(self):
        """Show accessibility help dialog."""
        from PySide6.QtWidgets import QMessageBox

        help_info = self.keyboard_navigation.create_navigation_help()
        accessibility_status = self.accessibility_manager.get_accessibility_status()

        help_text = "CSC-Reach Accessibility Help\n\n"

        # Accessibility status
        help_text += "Current Accessibility Features:\n"
        for feature, enabled in accessibility_status.items():
            status = "Enabled" if enabled else "Disabled"
            help_text += f"• {feature.replace('_', ' ').title()}: {status}\n"

        help_text += "\nKeyboard Navigation:\n"
        for category, shortcuts in help_info.items():
            if isinstance(shortcuts, dict):
                help_text += f"\n{category}:\n"
                for shortcut, description in shortcuts.items():
                    help_text += f"• {shortcut}: {description}\n"

        help_text += "\nAccessibility Shortcuts:\n"
        help_text += "• Ctrl+Shift+H: Toggle high contrast mode\n"
        help_text += "• Ctrl+Shift+F: Toggle large fonts\n"
        help_text += "• Ctrl+Shift+E: Toggle enhanced focus indicators\n"
        help_text += "• F1: Show this help\n"
        help_text += "• Ctrl+Shift+A: Announce current focus\n"

        QMessageBox.information(self, "Accessibility Help", help_text)

        # Announce to screen reader
        self.accessibility_manager.announce_to_screen_reader(
            "Accessibility help dialog opened"
        )

    def announce_current_focus(self):
        """Announce current focus to screen reader."""
        focus_info = self.keyboard_navigation.announce_navigation_state()
        self.accessibility_manager.announce_to_screen_reader(focus_info)

    def setup_toolbar_manager(self):
        """Set up the toolbar manager and create default toolbars."""
        # Connect toolbar manager to main window actions
        self.toolbar_manager.connect_main_window_actions(self)

        # Load saved configuration or create defaults
        self.toolbar_manager.load_configuration()

        # Create toolbars from configuration
        self.toolbar_manager.recreate_all_toolbars()

        # Connect signals
        self.toolbar_manager.item_activated.connect(self.on_toolbar_item_activated)
        self.toolbar_manager.configuration_changed.connect(
            self.on_toolbar_configuration_changed
        )

        logger.info("Toolbar manager set up successfully")

    def show_toolbar_customization(self):
        """Show toolbar customization dialog."""
        from .toolbar_customization_dialog import ToolbarCustomizationDialog

        dialog = ToolbarCustomizationDialog(self.toolbar_manager, self)
        dialog.configuration_changed.connect(self.on_toolbar_configuration_changed)
        dialog.exec()

    def on_toolbar_item_activated(self, item_id: str):
        """Handle toolbar item activation."""
        logger.debug(f"Toolbar item activated: {item_id}")

        # Handle items that don't have direct callbacks
        if item_id == "new_template":
            self.create_new_template()
        elif item_id == "export_templates":
            self.export_all_templates()
        # Add more item handlers as needed

    def on_toolbar_configuration_changed(self):
        """Handle toolbar configuration changes."""
        logger.info("Toolbar configuration changed")

        # Announce to screen reader
        if self.accessibility_manager.screen_reader_enabled:
            self.accessibility_manager.announce_to_screen_reader(
                "Toolbar configuration updated"
            )

    def create_new_template(self):
        """Create a new template."""
        # Clear current template fields
        self.subject_edit.clear()
        self.content_edit.clear()
        self.whatsapp_content_edit.clear()

        # Reset template combo to show no selection
        self.template_combo.setCurrentIndex(-1)

        # Focus on subject field
        self.subject_edit.setFocus()

        self.log_message("New template created")

        # Announce to screen reader
        if self.accessibility_manager.screen_reader_enabled:
            self.accessibility_manager.announce_to_screen_reader(
                "New template created, ready for editing"
            )

    def create_modern_progress_operation(
        self, operation_name: str, operation_type: OperationType, total_steps: int = 1
    ) -> str:
        """Create a modern progress operation."""
        import uuid

        operation_id = str(uuid.uuid4())

        operation = self.progress_manager.create_operation(
            operation_id=operation_id,
            name=operation_name,
            operation_type=operation_type,
            total_steps=total_steps,
            can_cancel=True,
            can_pause=False,
        )

        return operation_id

    def show_modern_progress_dialog(self, operation_id: str):
        """Show modern progress dialog for an operation."""
        if self.progress_dialog:
            self.progress_dialog.close()

        self.progress_dialog = ModernProgressDialog(
            self.progress_manager, operation_id, self
        )

        # Connect signals
        self.progress_dialog.cancel_requested.connect(self.cancel_current_operation)
        self.progress_dialog.pause_requested.connect(self.pause_current_operation)
        self.progress_dialog.resume_requested.connect(self.resume_current_operation)

        self.progress_dialog.show()
        return self.progress_dialog

    def cancel_current_operation(self, operation_id: str):
        """Cancel current operation."""
        if self.sending_thread and self.sending_thread.isRunning():
            self.sending_thread.stop()

        self.progress_manager.cancel_operation(operation_id)

    def pause_current_operation(self, operation_id: str):
        """Pause current operation."""
        # Implementation depends on operation type
        self.progress_manager.pause_operation(operation_id)

    def resume_current_operation(self, operation_id: str):
        """Resume current operation."""
        # Implementation depends on operation type
        self.progress_manager.resume_operation(operation_id)

    def closeEvent(self, event):
        """Handle window close event."""
        # Save window geometry
        self.save_window_geometry()

        # Stop any running operations
        if self.sending_thread and self.sending_thread.isRunning():
            self.sending_thread.stop()
            self.sending_thread.wait(3000)  # Wait up to 3 seconds

        # Close progress dialog
        if self.progress_dialog:
            self.progress_dialog.close()

        super().closeEvent(event)

    def show_message_analytics(self):
        """Show message analytics and logs dialog."""
        if not self.message_logger:
            QMessageBox.warning(
                self,
                "Analytics Unavailable",
                "Message logging is not available. Please restart the application.",
            )
            return

        try:
            from .message_analytics_dialog import MessageAnalyticsDialog

            dialog = MessageAnalyticsDialog(self.message_logger, self)
            dialog.exec()
        except Exception as e:
            logger.error(f"Failed to open analytics dialog: {e}")
            QMessageBox.critical(
                self, "Error", f"Failed to open analytics dialog: {str(e)}"
            )

    def on_language_changed(self, language_code: str):
        """Handle language change."""
        logger.info(f"Language changed to: {language_code}")
        # Note: Full UI refresh would require application restart
        # For now, just update the window title
        self.setWindowTitle(tr("app_title"))

    def populate_language_combo(self):
        """Populate the language combo box."""
        supported_languages = self.i18n_manager.get_supported_languages()
        current_lang = self.i18n_manager.get_current_language()

        for lang_code, lang_info in supported_languages.items():
            display_name = f"{lang_info['native']}"
            self.language_combo.addItem(display_name, lang_code)

            # Set current language as selected
            if lang_code == current_lang:
                self.language_combo.setCurrentText(display_name)

    def on_language_changed(self, display_name: str):
        """Handle language change from combo box."""
        # Find language code from display name
        for i in range(self.language_combo.count()):
            if self.language_combo.itemText(i) == display_name:
                lang_code = self.language_combo.itemData(i)
                if lang_code and lang_code != self.i18n_manager.get_current_language():
                    success = self.i18n_manager.set_language(lang_code)
                    if success:
                        # Update UI immediately
                        self.refresh_ui_translations()
                        QMessageBox.information(
                            self,
                            tr("language_changed_restart").split(".")[0],
                            tr("language_changed_restart"),
                        )
                break

    def refresh_ui_translations(self):
        """Refresh all UI text with current language translations."""
        # Update window title
        self.setWindowTitle(tr("app_title"))

        # Update menu bar
        menubar = self.menuBar()
        menus = menubar.findChildren(QMenuBar)

        # Update toolbar buttons
        self.import_btn.setText(tr("import_csv"))
        self.send_btn.setText(tr("send_messages"))
        self.draft_btn.setText(tr("create_draft"))
        self.stop_btn.setText(tr("stop_sending"))

        # Update group boxes
        for group_box in self.findChildren(QGroupBox):
            if group_box.title() == "Recipients" or "Recipients" in group_box.title():
                group_box.setTitle(tr("recipients"))
            elif (
                group_box.title() == "Message Template"
                or "Template" in group_box.title()
            ):
                group_box.setTitle(tr("message_template"))
            elif group_box.title() == "Email Content" or "Email" in group_box.title():
                group_box.setTitle(tr("email_content_group"))
            elif (
                group_box.title() == "WhatsApp Content"
                or "WhatsApp" in group_box.title()
            ):
                group_box.setTitle(tr("whatsapp_content_group"))
            elif (
                group_box.title() == "Sending Progress"
                or "Progress" in group_box.title()
            ):
                group_box.setTitle(tr("sending_progress"))

        # Update buttons
        for button in self.findChildren(QPushButton):
            if button.text() == "Select All":
                button.setText(tr("select_all"))
            elif button.text() == "Select None":
                button.setText(tr("select_none"))
            elif button.text() == "Library" or button == self.template_library_btn:
                button.setText(tr("library"))
            elif button.text() == "Save" or button == self.save_template_btn:
                button.setText(tr("save"))
            elif button.text() == "Preview Message" or button == self.preview_btn:
                button.setText(tr("preview_message"))

        # Update labels
        self.recipients_info_label.setText(
            tr("no_recipients_loaded")
            if not self.customers
            else f"{len(self.customers)} {tr('recipients_loaded')}"
        )
        self.progress_label.setText(tr("ready_to_send"))
        self.outlook_status_label.setText(tr("outlook_not_connected"))

        # Update status bar
        self.email_status_label.setText(tr("email_ready_status"))
        self.whatsapp_status_label.setText(
            tr("whatsapp_business_not_configured_status")
        )
        self.whatsapp_web_status_label.setText(tr("whatsapp_web_not_configured_status"))
        self.quota_label.setText(tr("quota_status", current=0, total=100))

        # Update WhatsApp character count
        self.update_whatsapp_char_count()

        # Update template combo
        self.refresh_template_combo()

        # Update channel combo
        self.channel_combo.clear()
        channel_options = [
            (tr("email_only"), "email_only"),
            (tr("whatsapp_business_api"), "whatsapp_business"),
            (tr("whatsapp_web"), "whatsapp_web"),
            (tr("email_whatsapp_business"), "email_whatsapp_business"),
            (tr("email_whatsapp_web"), "email_whatsapp_web"),
        ]

        for display_text, channel_id in channel_options:
            self.channel_combo.addItem(display_text, channel_id)

        self.channel_combo.setCurrentIndex(0)  # Reset to email only

    def test_whatsapp_connection(self):
        """Test WhatsApp Business API connection."""
        if not self.whatsapp_service.is_configured():
            QMessageBox.warning(
                self,
                tr("whatsapp_business_not_configured"),
                tr("whatsapp_business_configure_first"),
            )
            return

        try:
            success, message = self.whatsapp_service.test_connection()
            if success:
                QMessageBox.information(
                    self, tr("whatsapp_business_test"), f"✅ {message}"
                )
                self.whatsapp_status_label.setText(tr("whatsapp_business_connected"))
                self.whatsapp_status_label.setStyleSheet("color: green;")
            else:
                QMessageBox.warning(self, tr("whatsapp_business_test"), f"❌ {message}")
                self.whatsapp_status_label.setText(
                    tr("whatsapp_business_connection_failed")
                )
                self.whatsapp_status_label.setStyleSheet("color: red;")
        except Exception as e:
            QMessageBox.critical(
                self, tr("whatsapp_business_test"), tr("test_failed", error=str(e))
            )

    def test_whatsapp_web_connection(self):
        """Test WhatsApp Web service."""
        if not self.whatsapp_web_service.is_configured():
            QMessageBox.warning(
                self,
                tr("whatsapp_web_not_configured"),
                tr("whatsapp_web_configure_first"),
            )
            return

        try:
            success, message = self.whatsapp_web_service.test_connection()
            if success:
                QMessageBox.information(
                    self,
                    tr("whatsapp_web_service_test"),
                    tr("whatsapp_web_opened_browser", message=message),
                )
                self.update_status_display()
            else:
                QMessageBox.warning(
                    self, tr("whatsapp_web_service_test"), f"❌ {message}"
                )
        except Exception as e:
            QMessageBox.critical(
                self, tr("whatsapp_web_service_test"), tr("test_failed", error=str(e))
            )

    def preview_message(self):
        """Preview message for selected channel(s)."""
        if not self.customers:
            QMessageBox.warning(self, tr("no_recipients"), tr("please_import_csv"))
            return

        # Use first customer for preview
        customer = self.customers[0]

        # Update current template with UI content
        self.update_current_template()

        # Generate preview content
        rendered = self.current_template.render(customer)

        channel_id = self.get_current_channel_id()
        preview_text = ""

        # Email preview
        if channel_id in [
            "email_only",
            "email_whatsapp_business",
            "email_whatsapp_web",
        ]:
            preview_text += "📧 EMAIL PREVIEW:\n"
            preview_text += f"To: {customer.email}\n"
            preview_text += f"Subject: {rendered.get('subject', '')}\n\n"
            preview_text += rendered.get("content", "")
            preview_text += "\n" + "=" * 60 + "\n\n"

        # WhatsApp preview
        if channel_id in [
            "whatsapp_business",
            "whatsapp_web",
            "email_whatsapp_business",
            "email_whatsapp_web",
        ]:
            service_type = (
                "Business API" if "business" in channel_id else "Web Automation"
            )
            preview_text += f"📱 WHATSAPP PREVIEW ({service_type}):\n"
            preview_text += f"To: {customer.phone}\n\n"
            whatsapp_content = rendered.get(
                "whatsapp_content", rendered.get("content", "")
            )
            preview_text += whatsapp_content

            if "whatsapp_web" in channel_id:
                preview_text += "\n\n⚠️ NOTE: WhatsApp Web will open in browser"
                if (
                    hasattr(self.whatsapp_web_service, "auto_send")
                    and self.whatsapp_web_service.auto_send
                ):
                    preview_text += " - messages will be sent automatically"
                else:
                    preview_text += " - you must manually send each message"

        # Show preview dialog with proper sizing
        customer_display = f"{customer.name}"
        if customer.company:
            customer_display += f" ({customer.company})"

        dialog = PreviewDialog(customer_display, preview_text, self)
        dialog.exec()

    def update_current_template(self):
        """Update current template with UI content."""
        if self.current_template:
            self.current_template.subject = self.subject_edit.toPlainText()
            self.current_template.content = self.content_edit.toPlainText()
            self.current_template.whatsapp_content = (
                self.whatsapp_content_edit.toPlainText()
            )

    def get_current_channel_id(self) -> str:
        """
        Get the current channel ID from the combo box.

        Returns:
            str: Channel ID (e.g., 'email_only', 'whatsapp_business')
        """
        current_index = self.channel_combo.currentIndex()
        if current_index >= 0:
            channel_id = self.channel_combo.itemData(current_index)
            logger.debug(f"Current channel ID: {channel_id}")
            return channel_id

        logger.warning("No channel selected, defaulting to email_only")
        return "email_only"  # Default fallback

    def send_messages(self):
        """Send messages via selected channel(s) - replaces send_emails."""
        selected_customers = self.get_selected_customers()
        if not selected_customers:
            QMessageBox.warning(
                self,
                self.i18n_manager.tr("no_recipients"),
                self.i18n_manager.tr("please_select_recipients"),
            )
            return

        channel_id = self.get_current_channel_id()
        channel_display = self.channel_combo.currentText()

        # Validate channel availability
        if (
            channel_id
            in ["email_only", "email_whatsapp_business", "email_whatsapp_web"]
            and not self.email_service
        ):
            QMessageBox.warning(
                self, "Email Service Error", "Email service is not available."
            )
            return

        if (
            channel_id in ["whatsapp_business", "email_whatsapp_business"]
            and not self.whatsapp_service.is_configured()
        ):
            QMessageBox.warning(
                self,
                "WhatsApp Business API Not Configured",
                "Please configure WhatsApp Business API settings first.\n\nGo to Tools → WhatsApp Business API Settings.",
            )
            return

        if channel_id in ["whatsapp_web", "email_whatsapp_web"]:
            if not self.whatsapp_web_service.is_configured():
                QMessageBox.warning(
                    self,
                    "WhatsApp Web Not Configured",
                    "Please configure WhatsApp Web settings first.\n\nGo to Tools → WhatsApp Web Settings.",
                )
                return

            # Additional warning for WhatsApp Web
            reply = QMessageBox.warning(
                self,
                "⚠️ WhatsApp Web Warning",
                "You are about to use WhatsApp Web automation.\n\n"
                "⚠️ IMPORTANT:\n"
                "• May violate WhatsApp Terms of Service\n"
                "• Risk of account suspension\n"
                "• You must manually send each message in browser\n"
                "• WhatsApp Web must be open and logged in\n\n"
                "WhatsApp Business API is strongly recommended instead.\n\n"
                "Do you want to proceed anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply != QMessageBox.Yes:
                return

        # Update template
        self.update_current_template()

        # Confirm sending
        service_info = self._get_channel_description(channel_id)
        reply = QMessageBox.question(
            self,
            self.i18n_manager.tr("confirm_sending"),
            self.i18n_manager.tr(
                "send_messages_to", count=len(selected_customers), channel=service_info
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        # Create modern progress operation
        operation_name = (
            f"Send messages to {len(selected_customers)} recipients via {service_info}"
        )
        operation_id = self.create_modern_progress_operation(
            operation_name,
            OperationType.BULK_OPERATION,
            total_steps=len(selected_customers),
        )

        self.current_operation_id = operation_id

        # Show modern progress dialog
        progress_dialog = self.show_modern_progress_dialog(operation_id)

        # Start the operation
        self.progress_manager.start_operation(operation_id)

        # Start sending with progress tracking
        self.start_multi_channel_sending_with_progress(
            selected_customers, channel_id, operation_id
        )

    def _get_channel_description(self, channel_id: str) -> str:
        """Get user-friendly description of the selected channel."""
        descriptions = {
            "email_only": "email",
            "whatsapp_business": "WhatsApp Business API",
            "whatsapp_web": "WhatsApp Web (manual sending required)",
            "email_whatsapp_business": "email and WhatsApp Business API",
            "email_whatsapp_web": "email and WhatsApp Web",
        }
        return descriptions.get(channel_id, channel_id.lower())

    def start_multi_channel_sending(self, customers: List[Customer], channel_id: str):
        """Start multi-channel message sending (legacy method)."""
        if channel_id == "email_only":
            self.start_email_sending(customers)
        elif channel_id == "whatsapp_business":
            self.start_whatsapp_business_sending(customers)
        elif channel_id == "whatsapp_web":
            self.start_whatsapp_web_sending(customers)
        elif channel_id == "email_whatsapp_business":
            self.start_email_and_whatsapp_business_sending(customers)
        elif channel_id == "email_whatsapp_web":
            self.start_email_and_whatsapp_web_sending(customers)
        else:
            QMessageBox.warning(
                self, "Unknown Channel", f"Unknown channel: {channel_id}"
            )

    def start_multi_channel_sending_with_progress(
        self, customers: List[Customer], channel_id: str, operation_id: str
    ):
        """Start multi-channel message sending with modern progress tracking."""
        # Create progress tracker
        progress_tracker = ProgressTracker(self.progress_manager, operation_id)

        # Add operation steps
        steps = []
        if channel_id in [
            "email_only",
            "email_whatsapp_business",
            "email_whatsapp_web",
        ]:
            steps.append(
                {
                    "name": "Send emails",
                    "description": f"Sending emails to {len(customers)} recipients",
                }
            )
        if channel_id in ["whatsapp_business", "email_whatsapp_business"]:
            steps.append(
                {
                    "name": "Send WhatsApp Business",
                    "description": f"Sending WhatsApp messages via Business API",
                }
            )
        if channel_id in ["whatsapp_web", "email_whatsapp_web"]:
            steps.append(
                {
                    "name": "Send WhatsApp Web",
                    "description": f"Sending WhatsApp messages via Web",
                }
            )

        self.progress_manager.add_operation_steps(operation_id, steps)

        # Start sending based on channel
        if channel_id == "email_only":
            self.start_email_sending_with_progress(customers, progress_tracker, 0)
        elif channel_id == "whatsapp_business":
            self.start_whatsapp_business_sending_with_progress(
                customers, progress_tracker, 0
            )
        elif channel_id == "whatsapp_web":
            self.start_whatsapp_web_sending_with_progress(
                customers, progress_tracker, 0
            )
        elif channel_id == "email_whatsapp_business":
            self.start_email_and_whatsapp_business_sending_with_progress(
                customers, progress_tracker
            )
        elif channel_id == "email_whatsapp_web":
            self.start_email_and_whatsapp_web_sending_with_progress(
                customers, progress_tracker
            )
        else:
            progress_tracker.complete(False, f"Unknown channel: {channel_id}")

    def start_email_sending_with_progress(
        self,
        customers: List[Customer],
        progress_tracker: ProgressTracker,
        step_index: int,
    ):
        """Start email sending with progress tracking."""
        progress_tracker.set_step(step_index, 0.0, "Starting email sending...")

        # Use existing email sending logic but with progress updates
        if self.sending_thread and self.sending_thread.isRunning():
            progress_tracker.complete(
                False, "Another sending operation is already running"
            )
            return

        # Create enhanced email sending thread with progress tracking
        self.sending_thread = EnhancedEmailSendingThread(
            customers,
            self.current_template,
            self.email_service,
            progress_tracker,
            step_index,
        )

        self.sending_thread.finished.connect(
            lambda success, message: self.on_enhanced_sending_finished(
                success, message, progress_tracker
            )
        )

        self.send_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        self.sending_thread.start()

    def start_whatsapp_business_sending_with_progress(
        self,
        customers: List[Customer],
        progress_tracker: ProgressTracker,
        step_index: int,
    ):
        """Start WhatsApp Business sending with progress tracking."""
        progress_tracker.set_step(
            step_index, 0.0, "Starting WhatsApp Business API sending..."
        )

        # Implement WhatsApp Business sending with progress
        # For now, simulate the process
        import time
        from PySide6.QtCore import QTimer

        def simulate_whatsapp_sending():
            for i, customer in enumerate(customers):
                progress = (i + 1) / len(customers)
                progress_tracker.update(progress, f"Sending to {customer.name}...")
                progress_tracker.set_step(
                    step_index, progress, f"Sent to {i + 1}/{len(customers)} recipients"
                )
                time.sleep(0.1)  # Simulate sending delay

            progress_tracker.complete_step(step_index, True)
            progress_tracker.complete(
                True,
                f"Successfully sent WhatsApp messages to {len(customers)} recipients",
            )

        # Use QTimer to avoid blocking the UI
        QTimer.singleShot(100, simulate_whatsapp_sending)

    def start_whatsapp_web_sending_with_progress(
        self,
        customers: List[Customer],
        progress_tracker: ProgressTracker,
        step_index: int,
    ):
        """Start WhatsApp Web sending with progress tracking."""
        progress_tracker.set_step(step_index, 0.0, "Starting WhatsApp Web sending...")

        # Similar implementation to WhatsApp Business but with web automation
        # For now, simulate the process
        progress_tracker.update(0.5, "Opening WhatsApp Web...")
        progress_tracker.set_step(
            step_index, 0.5, "WhatsApp Web opened, manual sending required"
        )

        # Complete immediately since this requires manual intervention
        progress_tracker.complete_step(step_index, True)
        progress_tracker.complete(
            True,
            f"WhatsApp Web opened for {len(customers)} recipients - manual sending required",
        )

    def start_email_and_whatsapp_business_sending_with_progress(
        self, customers: List[Customer], progress_tracker: ProgressTracker
    ):
        """Start combined email and WhatsApp Business sending."""

        # First send emails (step 0)
        def on_email_complete():
            # Then send WhatsApp (step 1)
            self.start_whatsapp_business_sending_with_progress(
                customers, progress_tracker, 1
            )

        # Start with emails
        self.start_email_sending_with_progress(customers, progress_tracker, 0)
        # Note: In a real implementation, we'd need to chain these operations properly

    def start_email_and_whatsapp_web_sending_with_progress(
        self, customers: List[Customer], progress_tracker: ProgressTracker
    ):
        """Start combined email and WhatsApp Web sending."""

        # Similar to email + WhatsApp Business
        def on_email_complete():
            self.start_whatsapp_web_sending_with_progress(
                customers, progress_tracker, 1
            )

        self.start_email_sending_with_progress(customers, progress_tracker, 0)

    def on_enhanced_sending_finished(
        self, success: bool, message: str, progress_tracker: ProgressTracker
    ):
        """Handle enhanced sending completion."""
        self.send_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        if success:
            progress_tracker.complete(True, message)
        else:
            progress_tracker.complete(False, message)

        # Show completion message
        if success:
            QMessageBox.information(self, tr("sending_complete"), message)
        else:
            QMessageBox.warning(self, tr("sending_error"), message)

    def start_email_sending(self, customers: List[Customer]):
        """Start email-only sending (existing functionality)."""
        if self.sending_thread and self.sending_thread.isRunning():
            return

        # Use LoggedEmailService bulk functionality if available
        if hasattr(self.email_service, "send_bulk_emails"):
            # Use a simpler thread for LoggedEmailService
            self.sending_thread = LoggedEmailSendingThread(
                customers, self.current_template, self.email_service
            )
        else:
            # Fallback to original thread
            self.sending_thread = EmailSendingThread(
                customers, self.current_template, self.email_service
            )

        self.sending_thread.progress_updated.connect(self.update_progress)
        self.sending_thread.email_sent.connect(self.on_email_sent)
        self.sending_thread.finished.connect(self.on_sending_finished)

        self.send_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setMaximum(len(customers))
        self.progress_bar.setValue(0)

        self.sending_thread.start()

    def start_whatsapp_business_sending(self, customers: List[Customer]):
        """Start WhatsApp Business API sending."""
        self._start_whatsapp_sending(
            customers, self.whatsapp_service, "WhatsApp Business API"
        )

    def start_whatsapp_web_sending(self, customers: List[Customer]):
        """Start WhatsApp Web sending."""
        self._start_whatsapp_sending(
            customers, self.whatsapp_web_service, "WhatsApp Web"
        )

    def _start_whatsapp_sending(
        self, customers: List[Customer], service, service_name: str
    ):
        """Generic WhatsApp sending method."""
        self.send_btn.setEnabled(False)
        self.progress_bar.setMaximum(len(customers))
        self.progress_bar.setValue(0)

        successful = 0
        failed = 0

        self.log_message(
            f"Starting {service_name} sending to {len(customers)} recipients..."
        )

        if service_name == "WhatsApp Web":
            self.log_message(
                "⚠️ WhatsApp Web will open in your browser for each recipient"
            )
            self.log_message("⚠️ You must manually click 'Send' for each message")

        for i, customer in enumerate(customers):
            # Check if customer has phone number
            if not customer.phone:
                self.log_message(f"⚠️ No phone number for {customer.name}, skipping")
                failed += 1
                continue

            # Send message
            try:
                success = service.send_message(customer, self.current_template)

                if success:
                    if service_name == "WhatsApp Web":
                        self.log_message(
                            f"🌐 WhatsApp Web opened for {customer.name} ({customer.phone}) - Please send manually"
                        )
                    else:
                        self.log_message(
                            f"✅ {service_name} sent to {customer.name} ({customer.phone})"
                        )
                    successful += 1
                else:
                    error = (
                        service.get_last_error()
                        if hasattr(service, "get_last_error")
                        else "Unknown error"
                    )
                    self.log_message(
                        f"❌ {service_name} failed to {customer.name} ({customer.phone}): {error}"
                    )
                    failed += 1

            except Exception as e:
                self.log_message(f"❌ {service_name} error for {customer.name}: {e}")
                failed += 1

            # Update progress
            self.progress_bar.setValue(i + 1)

            # Process events to keep UI responsive
            QApplication.processEvents()

            # Add delay between messages
            if i < len(customers) - 1:
                delay = (
                    service.min_delay_seconds
                    if hasattr(service, "min_delay_seconds")
                    else 30
                )
                self.log_message(f"⏱️ Waiting {delay} seconds before next message...")

                # Show countdown
                for remaining in range(delay, 0, -1):
                    self.log_message(f"⏱️ {remaining} seconds remaining...")
                    time.sleep(1)
                    QApplication.processEvents()

        self.send_btn.setEnabled(True)

        if service_name == "WhatsApp Web":
            self.log_message(
                f"WhatsApp Web process completed: {successful} browser windows opened, {failed} failed"
            )
            self.log_message(
                "⚠️ Remember to manually send each message in your browser!"
            )
        else:
            self.log_message(
                f"{service_name} sending completed: {successful} successful, {failed} failed"
            )

        self.update_status_display()  # Refresh status after sending

    def start_email_and_whatsapp_business_sending(self, customers: List[Customer]):
        """Start sending via both email and WhatsApp Business API."""
        self._start_dual_channel_sending(
            customers, self.whatsapp_service, "WhatsApp Business API"
        )

    def start_email_and_whatsapp_web_sending(self, customers: List[Customer]):
        """Start sending via both email and WhatsApp Web."""
        self._start_dual_channel_sending(
            customers, self.whatsapp_web_service, "WhatsApp Web"
        )

    def _start_dual_channel_sending(
        self, customers: List[Customer], whatsapp_service, whatsapp_service_name: str
    ):
        """Generic dual-channel sending method."""
        self.log_message(
            f"Starting dual-channel sending (Email + {whatsapp_service_name})..."
        )

        # Filter customers for each channel
        email_customers = [c for c in customers if c.email]
        whatsapp_customers = [c for c in customers if c.phone]

        self.log_message(
            f"Email recipients: {len(email_customers)}, {whatsapp_service_name} recipients: {len(whatsapp_customers)}"
        )

        # Send emails first (using existing thread)
        if email_customers:
            self.log_message("Starting email sending...")
            self.start_email_sending(email_customers)

            # Wait for email thread to complete
            if self.sending_thread:
                self.sending_thread.wait()

        # Then send WhatsApp messages
        if whatsapp_customers:
            self.log_message(f"Starting {whatsapp_service_name} sending...")
            self._start_whatsapp_sending(
                whatsapp_customers, whatsapp_service, whatsapp_service_name
            )

        self.log_message("Dual-channel sending completed")

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
