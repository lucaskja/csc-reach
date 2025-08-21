"""
Windows Outlook integration using COM (Component Object Model).
Enhanced with better lifecycle management, version detection, and error handling.
"""

import time
import threading
import weakref
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

try:
    import win32com.client
    import pythoncom
    import pywintypes
    from win32com.client import constants as outlook_constants
    WIN32COM_AVAILABLE = True
except ImportError:
    WIN32COM_AVAILABLE = False

from ..core.models import Customer, MessageTemplate, MessageRecord, MessageStatus
from ..utils.exceptions import OutlookIntegrationError, ServiceUnavailableError
from ..utils.logger import get_logger
from ..core.i18n_manager import get_i18n_manager

logger = get_logger(__name__)


class OutlookVersion(Enum):
    """Outlook version enumeration."""
    UNKNOWN = "unknown"
    OUTLOOK_2016 = "16.0"
    OUTLOOK_2019 = "16.0"
    OUTLOOK_2021 = "16.0"
    OUTLOOK_365 = "16.0"
    OUTLOOK_2013 = "15.0"
    OUTLOOK_2010 = "14.0"


@dataclass
class OutlookProfile:
    """Outlook profile information."""
    name: str
    is_default: bool
    email_address: Optional[str] = None
    display_name: Optional[str] = None


@dataclass
class OutlookCapabilities:
    """Outlook capabilities and features."""
    supports_html: bool = True
    supports_rtf: bool = True
    supports_attachments: bool = True
    supports_scheduling: bool = False
    supports_tracking: bool = False
    max_recipients: int = 500


class OutlookWindowsService:
    """Enhanced Windows Outlook integration service using COM."""
    
    def __init__(self):
        """Initialize Windows Outlook service with enhanced capabilities."""
        self.outlook_app = None
        self.namespace = None
        self.i18n_manager = get_i18n_manager()
        
        # Enhanced COM management
        self._com_initialized = False
        self._outlook_version = OutlookVersion.UNKNOWN
        self._outlook_capabilities = OutlookCapabilities()
        self._available_profiles = []
        self._current_profile = None
        
        # Thread safety
        self._lock = threading.RLock()
        self._com_thread_id = None
        
        # Connection management
        self._connection_attempts = 0
        self._max_connection_attempts = 3
        self._last_connection_error = None
        
        self._check_outlook_availability()
    
    def _check_outlook_availability(self) -> None:
        """Check if Outlook is available on Windows with enhanced detection."""
        if not WIN32COM_AVAILABLE:
            error_msg = self.i18n_manager.tr("outlook_windows_pywin32_required")
            logger.error(error_msg)
            raise ServiceUnavailableError(error_msg)
        
        try:
            # Initialize COM for this thread
            self._initialize_com()
            
            # Try to connect to Outlook and detect capabilities
            self._connect_to_outlook()
            self._detect_outlook_version()
            self._detect_outlook_capabilities()
            self._discover_profiles()
            
            logger.info(f"Outlook Windows service initialized successfully - Version: {self._outlook_version.value}")
            
        except Exception as e:
            self._last_connection_error = str(e)
            logger.error(f"Failed to initialize Outlook Windows service: {e}")
            raise ServiceUnavailableError(f"Outlook is not available: {e}")
    
    def _initialize_com(self) -> None:
        """Initialize COM for the current thread with proper cleanup."""
        try:
            with self._lock:
                if not self._com_initialized:
                    pythoncom.CoInitialize()
                    self._com_initialized = True
                    self._com_thread_id = threading.get_ident()
                    logger.debug("COM initialized for thread")
                elif self._com_thread_id != threading.get_ident():
                    # Different thread, need to initialize COM again
                    pythoncom.CoInitialize()
                    logger.debug("COM initialized for new thread")
        except Exception as e:
            logger.warning(f"COM initialization warning: {e}")
            # COM might already be initialized, continue
    
    def _connect_to_outlook(self) -> None:
        """Connect to Outlook COM object with enhanced error handling."""
        with self._lock:
            try:
                self._connection_attempts += 1
                
                # Try to get existing Outlook instance first
                try:
                    self.outlook_app = win32com.client.GetActiveObject("Outlook.Application")
                    logger.debug("Connected to existing Outlook instance")
                except pywintypes.com_error:
                    # No existing instance, create new one
                    self.outlook_app = win32com.client.Dispatch("Outlook.Application")
                    logger.debug("Created new Outlook instance")
                    
                    # Wait for Outlook to initialize
                    time.sleep(2)
                
                # Get the namespace with retry logic
                for attempt in range(3):
                    try:
                        self.namespace = self.outlook_app.GetNamespace("MAPI")
                        break
                    except pywintypes.com_error as e:
                        if attempt == 2:
                            raise
                        logger.debug(f"Namespace connection attempt {attempt + 1} failed, retrying...")
                        time.sleep(1)
                
                # Test the connection
                _ = self.outlook_app.Version  # This will fail if connection is bad
                self._connection_attempts = 0  # Reset on success
                
            except pywintypes.com_error as e:
                error_msg = f"COM error connecting to Outlook: {e}"
                logger.error(error_msg)
                raise OutlookIntegrationError(error_msg)
            except Exception as e:
                error_msg = f"Failed to connect to Outlook: {e}"
                logger.error(error_msg)
                raise OutlookIntegrationError(error_msg)
    
    def _detect_outlook_version(self) -> None:
        """Detect Outlook version and set capabilities accordingly."""
        try:
            if not self.outlook_app:
                return
                
            version_string = self.outlook_app.Version
            logger.info(f"Detected Outlook version: {version_string}")
            
            # Parse version string (e.g., "16.0.12345.67890")
            major_version = version_string.split('.')[0]
            
            version_map = {
                "16": OutlookVersion.OUTLOOK_365,  # 2016/2019/2021/365
                "15": OutlookVersion.OUTLOOK_2013,
                "14": OutlookVersion.OUTLOOK_2010,
            }
            
            self._outlook_version = version_map.get(major_version, OutlookVersion.UNKNOWN)
            
            # Try to detect specific Office 365 vs standalone
            try:
                # Office 365 typically has more frequent updates
                build_number = int(version_string.split('.')[2])
                if major_version == "16" and build_number > 10000:
                    self._outlook_version = OutlookVersion.OUTLOOK_365
            except (IndexError, ValueError):
                pass
                
        except Exception as e:
            logger.warning(f"Could not detect Outlook version: {e}")
            self._outlook_version = OutlookVersion.UNKNOWN
    
    def _detect_outlook_capabilities(self) -> None:
        """Detect Outlook capabilities based on version and features."""
        try:
            capabilities = OutlookCapabilities()
            
            # All modern versions support HTML and RTF
            capabilities.supports_html = True
            capabilities.supports_rtf = True
            capabilities.supports_attachments = True
            
            # Version-specific capabilities
            if self._outlook_version in [OutlookVersion.OUTLOOK_365, OutlookVersion.OUTLOOK_2019, OutlookVersion.OUTLOOK_2021]:
                capabilities.supports_scheduling = True
                capabilities.supports_tracking = True
                capabilities.max_recipients = 1000
            elif self._outlook_version == OutlookVersion.OUTLOOK_2016:
                capabilities.supports_scheduling = True
                capabilities.supports_tracking = False
                capabilities.max_recipients = 500
            else:
                capabilities.supports_scheduling = False
                capabilities.supports_tracking = False
                capabilities.max_recipients = 100
            
            self._outlook_capabilities = capabilities
            logger.debug(f"Outlook capabilities detected: {capabilities}")
            
        except Exception as e:
            logger.warning(f"Could not detect Outlook capabilities: {e}")
    
    def _discover_profiles(self) -> None:
        """Discover available Outlook profiles."""
        try:
            if not self.namespace:
                return
                
            profiles = []
            
            # Get current profile information
            try:
                current_profile_name = self.namespace.CurrentProfileName
                current_user = self.namespace.CurrentUser
                
                profile = OutlookProfile(
                    name=current_profile_name,
                    is_default=True,
                    display_name=getattr(current_user, 'Name', None),
                    email_address=getattr(current_user, 'Address', None)
                )
                profiles.append(profile)
                self._current_profile = profile
                
                logger.info(f"Current Outlook profile: {current_profile_name}")
                
            except Exception as e:
                logger.warning(f"Could not get current profile information: {e}")
            
            self._available_profiles = profiles
            
        except Exception as e:
            logger.warning(f"Could not discover Outlook profiles: {e}")
            self._available_profiles = []
    
    def is_outlook_running(self) -> bool:
        """
        Check if Outlook is currently running with enhanced detection.
        
        Returns:
            True if Outlook is running, False otherwise
        """
        with self._lock:
            try:
                if self.outlook_app is None:
                    return False
                
                # Try multiple methods to verify Outlook is alive
                try:
                    # Method 1: Check version (lightweight)
                    _ = self.outlook_app.Version
                    
                    # Method 2: Check namespace (more thorough)
                    if self.namespace:
                        _ = self.namespace.CurrentProfileName
                    
                    return True
                    
                except pywintypes.com_error as e:
                    # COM error indicates Outlook is not responding
                    logger.debug(f"Outlook COM error during status check: {e}")
                    self._cleanup_com_objects()
                    return False
                except Exception as e:
                    logger.debug(f"Outlook status check failed: {e}")
                    return False
                    
            except Exception as e:
                logger.debug(f"Error checking Outlook status: {e}")
                return False
    
    def _cleanup_com_objects(self) -> None:
        """Clean up COM objects to prevent memory leaks."""
        try:
            if self.namespace:
                self.namespace = None
            if self.outlook_app:
                self.outlook_app = None
            logger.debug("COM objects cleaned up")
        except Exception as e:
            logger.debug(f"Error during COM cleanup: {e}")
    
    def get_connection_health(self) -> Dict[str, Any]:
        """
        Get detailed connection health information.
        
        Returns:
            Dictionary with connection health details
        """
        health = {
            'is_connected': False,
            'outlook_version': self._outlook_version.value,
            'connection_attempts': self._connection_attempts,
            'last_error': self._last_connection_error,
            'current_profile': None,
            'capabilities': None,
            'com_initialized': self._com_initialized,
            'thread_id': self._com_thread_id
        }
        
        try:
            health['is_connected'] = self.is_outlook_running()
            
            if self._current_profile:
                health['current_profile'] = {
                    'name': self._current_profile.name,
                    'email': self._current_profile.email_address,
                    'display_name': self._current_profile.display_name
                }
            
            health['capabilities'] = {
                'supports_html': self._outlook_capabilities.supports_html,
                'supports_rtf': self._outlook_capabilities.supports_rtf,
                'supports_scheduling': self._outlook_capabilities.supports_scheduling,
                'supports_tracking': self._outlook_capabilities.supports_tracking,
                'max_recipients': self._outlook_capabilities.max_recipients
            }
            
        except Exception as e:
            health['last_error'] = str(e)
        
        return health
    
    def start_outlook(self) -> bool:
        """
        Start Outlook application with enhanced initialization.
        
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                if self.is_outlook_running():
                    logger.info("Outlook is already running")
                    return True
                
                logger.info("Starting Outlook application...")
                
                # Clean up any stale COM objects first
                self._cleanup_com_objects()
                
                # Reinitialize COM if needed
                if not self._com_initialized or self._com_thread_id != threading.get_ident():
                    self._initialize_com()
                
                # Attempt to connect with retry logic
                max_attempts = self._max_connection_attempts
                for attempt in range(max_attempts):
                    try:
                        self._connect_to_outlook()
                        
                        # Wait for Outlook to fully initialize
                        initialization_timeout = 30  # seconds
                        start_time = time.time()
                        
                        while time.time() - start_time < initialization_timeout:
                            if self.is_outlook_running():
                                # Re-detect capabilities after successful start
                                self._detect_outlook_version()
                                self._detect_outlook_capabilities()
                                self._discover_profiles()
                                
                                logger.info(f"Outlook started successfully (attempt {attempt + 1})")
                                return True
                            time.sleep(1)
                        
                        # If we get here, Outlook didn't start properly
                        if attempt < max_attempts - 1:
                            logger.warning(f"Outlook start attempt {attempt + 1} timed out, retrying...")
                            self._cleanup_com_objects()
                            time.sleep(2)
                        
                    except Exception as e:
                        if attempt < max_attempts - 1:
                            logger.warning(f"Outlook start attempt {attempt + 1} failed: {e}, retrying...")
                            self._cleanup_com_objects()
                            time.sleep(2)
                        else:
                            raise
                
                logger.error("Failed to start Outlook after all attempts")
                return False
                
            except Exception as e:
                self._last_connection_error = str(e)
                logger.error(f"Failed to start Outlook: {e}")
                return False
    
    def restart_outlook_connection(self) -> bool:
        """
        Restart the Outlook connection (useful for recovery).
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Restarting Outlook connection...")
        
        with self._lock:
            try:
                # Clean up existing connection
                self._cleanup_com_objects()
                
                # Reset connection state
                self._connection_attempts = 0
                self._last_connection_error = None
                
                # Reinitialize
                return self.start_outlook()
                
            except Exception as e:
                logger.error(f"Failed to restart Outlook connection: {e}")
                return False
    
    def send_email(
        self, 
        customer: Customer, 
        template: MessageTemplate, 
        use_html: bool = False,
        attachments: Optional[List[str]] = None,
        schedule_time: Optional[Any] = None
    ) -> bool:
        """
        Send a single email using Outlook with enhanced features.
        
        Args:
            customer: Customer to send email to
            template: Email template to use
            use_html: Whether to use HTML formatting
            attachments: List of file paths to attach
            schedule_time: When to send the email (if supported)
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                # Ensure Outlook is running
                if not self.is_outlook_running():
                    if not self.start_outlook():
                        raise OutlookIntegrationError(
                            self.i18n_manager.tr("outlook_cannot_start")
                        )
                
                # Render template
                rendered = template.render(customer)
                subject = rendered.get('subject', '')
                content = rendered.get('content', '')
                
                # Create email item with error handling
                try:
                    mail_item = self.outlook_app.CreateItem(0)  # 0 = olMailItem
                except pywintypes.com_error as e:
                    logger.error(f"Failed to create mail item: {e}")
                    # Try to restart connection and retry once
                    if self.restart_outlook_connection():
                        mail_item = self.outlook_app.CreateItem(0)
                    else:
                        raise OutlookIntegrationError("Cannot create email item")
                
                # Set basic email properties
                mail_item.To = customer.email
                mail_item.Subject = subject
                
                # Set content based on format preference
                if use_html and self._outlook_capabilities.supports_html:
                    html_content = self._convert_to_html(content)
                    mail_item.HTMLBody = html_content
                    logger.debug(f"Using HTML format for email to {customer.email}")
                else:
                    formatted_content = self._format_email_content(content)
                    mail_item.Body = formatted_content
                    logger.debug(f"Using plain text format for email to {customer.email}")
                
                # Add attachments if provided and supported
                if attachments and self._outlook_capabilities.supports_attachments:
                    self._add_attachments(mail_item, attachments)
                
                # Handle scheduling if supported and requested
                if schedule_time and self._outlook_capabilities.supports_scheduling:
                    try:
                        mail_item.DeferredDeliveryTime = schedule_time
                        logger.debug(f"Email scheduled for {schedule_time}")
                    except Exception as e:
                        logger.warning(f"Failed to schedule email: {e}")
                
                # Send the email
                mail_item.Send()
                
                logger.info(f"Email sent to {customer.email}")
                return True
                
            except pywintypes.com_error as e:
                error_msg = f"COM error sending email to {customer.email}: {e}"
                logger.error(error_msg)
                
                # Try to recover from COM errors
                if "RPC server" in str(e) or "connection" in str(e).lower():
                    logger.info("Attempting to recover from COM connection error...")
                    if self.restart_outlook_connection():
                        logger.info("Connection recovered, but email send failed")
                
                return False
                
            except Exception as e:
                logger.error(f"Failed to send email to {customer.email}: {e}")
                return False
    
    def _convert_to_html(self, plain_text: str) -> str:
        """
        Convert plain text to HTML format with proper formatting.
        
        Args:
            plain_text: Plain text content
            
        Returns:
            HTML formatted content
        """
        if not plain_text:
            return ""
        
        # Escape HTML special characters
        html_content = (plain_text
                       .replace('&', '&amp;')
                       .replace('<', '&lt;')
                       .replace('>', '&gt;')
                       .replace('"', '&quot;')
                       .replace("'", '&#x27;'))
        
        # Convert line breaks to HTML
        html_content = html_content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Convert double line breaks to paragraphs
        paragraphs = html_content.split('\n\n')
        if len(paragraphs) > 1:
            html_content = '</p><p>'.join(paragraphs)
            html_content = f'<p>{html_content}</p>'
        else:
            # Single line breaks become <br> tags
            html_content = html_content.replace('\n', '<br>')
            html_content = f'<p>{html_content}</p>'
        
        # Clean up empty paragraphs
        html_content = html_content.replace('<p></p>', '')
        
        return html_content
    
    def _add_attachments(self, mail_item: Any, attachments: List[str]) -> None:
        """
        Add attachments to email with validation.
        
        Args:
            mail_item: Outlook mail item
            attachments: List of file paths to attach
        """
        import os
        
        for attachment_path in attachments:
            try:
                if not os.path.exists(attachment_path):
                    logger.warning(f"Attachment file not found: {attachment_path}")
                    continue
                
                # Check file size (limit to 25MB for most email systems)
                file_size = os.path.getsize(attachment_path)
                if file_size > 25 * 1024 * 1024:  # 25MB
                    logger.warning(f"Attachment too large ({file_size} bytes): {attachment_path}")
                    continue
                
                mail_item.Attachments.Add(attachment_path)
                logger.debug(f"Added attachment: {attachment_path}")
                
            except Exception as e:
                logger.error(f"Failed to add attachment {attachment_path}: {e}")
    
    def send_bulk_emails(
        self, 
        customers: List[Customer], 
        template: MessageTemplate,
        batch_size: int = 10,
        delay_between_emails: float = 1.0,
        use_html: bool = False,
        progress_callback: Optional[callable] = None
    ) -> List[MessageRecord]:
        """
        Send bulk emails using Outlook with enhanced features.
        
        Args:
            customers: List of customers to send emails to
            template: Email template to use
            batch_size: Number of emails to send in each batch
            delay_between_emails: Delay between emails in seconds
            use_html: Whether to use HTML formatting
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of message records with sending results
        """
        records = []
        
        with self._lock:
            try:
                # Validate batch size against Outlook capabilities
                max_recipients = self._outlook_capabilities.max_recipients
                if len(customers) > max_recipients:
                    logger.warning(f"Customer list ({len(customers)}) exceeds Outlook limit ({max_recipients})")
                
                # Ensure Outlook is running
                if not self.is_outlook_running():
                    if not self.start_outlook():
                        raise OutlookIntegrationError(
                            self.i18n_manager.tr("outlook_cannot_start")
                        )
                
                logger.info(f"Starting bulk email send to {len(customers)} recipients")
                
                # Track statistics
                start_time = time.time()
                successful_count = 0
                failed_count = 0
                
                for i, customer in enumerate(customers):
                    try:
                        # Create message record
                        record = MessageRecord(customer=customer, template=template)
                        record.status = MessageStatus.SENDING
                        
                        # Update progress if callback provided
                        if progress_callback:
                            progress_callback(i, len(customers), customer.email)
                        
                        # Send email with enhanced options
                        success = self.send_email(
                            customer, 
                            template, 
                            use_html=use_html
                        )
                        
                        if success:
                            record.mark_as_sent()
                            successful_count += 1
                            logger.debug(f"Email {i+1}/{len(customers)} sent successfully to {customer.email}")
                        else:
                            record.mark_as_failed("Failed to send email")
                            failed_count += 1
                            logger.warning(f"Email {i+1}/{len(customers)} failed to {customer.email}")
                        
                        records.append(record)
                        
                        # Add delay between emails to prevent overwhelming Outlook
                        if delay_between_emails > 0 and i < len(customers) - 1:
                            time.sleep(delay_between_emails)
                        
                        # Batch processing pause with connection health check
                        if (i + 1) % batch_size == 0 and i < len(customers) - 1:
                            logger.info(f"Processed batch of {batch_size} emails, checking connection...")
                            
                            # Check if Outlook is still healthy
                            if not self.is_outlook_running():
                                logger.warning("Outlook connection lost during bulk send, attempting recovery...")
                                if not self.restart_outlook_connection():
                                    raise OutlookIntegrationError("Lost connection to Outlook")
                            
                            time.sleep(2.0)  # Longer pause between batches
                    
                    except Exception as e:
                        record = MessageRecord(customer=customer, template=template)
                        record.mark_as_failed(str(e))
                        records.append(record)
                        failed_count += 1
                        logger.error(f"Failed to process email for {customer.email}: {e}")
                        
                        # If we have too many consecutive failures, stop
                        if failed_count > successful_count and failed_count > 5:
                            logger.error("Too many consecutive failures, stopping bulk send")
                            break
                
                # Final progress update
                if progress_callback:
                    progress_callback(len(customers), len(customers), "Complete")
                
                # Log final statistics
                elapsed_time = time.time() - start_time
                logger.info(
                    f"Bulk email send completed: {successful_count} successful, "
                    f"{failed_count} failed in {elapsed_time:.1f} seconds"
                )
                
            except Exception as e:
                logger.error(f"Bulk email send failed: {e}")
                # Mark remaining customers as failed
                for customer in customers[len(records):]:
                    record = MessageRecord(customer=customer, template=template)
                    record.mark_as_failed(f"Bulk send failed: {e}")
                    records.append(record)
        
        return records
    
    def create_draft_email(
        self, 
        customer: Customer, 
        template: MessageTemplate,
        use_html: bool = False,
        attachments: Optional[List[str]] = None,
        display_draft: bool = True
    ) -> bool:
        """
        Create a draft email in Outlook with enhanced features.
        
        Args:
            customer: Customer for the email
            template: Email template to use
            use_html: Whether to use HTML formatting
            attachments: List of file paths to attach
            display_draft: Whether to display the draft for review
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                # Ensure Outlook is running
                if not self.is_outlook_running():
                    if not self.start_outlook():
                        raise OutlookIntegrationError(
                            self.i18n_manager.tr("outlook_cannot_start")
                        )
                
                # Render template
                rendered = template.render(customer)
                subject = rendered.get('subject', '')
                content = rendered.get('content', '')
                
                # Create email item
                mail_item = self.outlook_app.CreateItem(0)  # 0 = olMailItem
                
                # Set email properties
                mail_item.To = customer.email
                mail_item.Subject = subject
                
                # Set content based on format preference
                if use_html and self._outlook_capabilities.supports_html:
                    html_content = self._convert_to_html(content)
                    mail_item.HTMLBody = html_content
                else:
                    formatted_content = self._format_email_content(content)
                    mail_item.Body = formatted_content
                
                # Add attachments if provided
                if attachments and self._outlook_capabilities.supports_attachments:
                    self._add_attachments(mail_item, attachments)
                
                # Save as draft (don't send)
                mail_item.Save()
                
                # Display the draft for user review if requested
                if display_draft:
                    mail_item.Display()
                
                logger.info(f"Draft email created for {customer.email}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to create draft email for {customer.email}: {e}")
                return False
    
    def get_available_profiles(self) -> List[OutlookProfile]:
        """
        Get list of available Outlook profiles.
        
        Returns:
            List of available profiles
        """
        return self._available_profiles.copy()
    
    def get_current_profile(self) -> Optional[OutlookProfile]:
        """
        Get current Outlook profile information.
        
        Returns:
            Current profile or None if not available
        """
        return self._current_profile
    
    def get_outlook_capabilities(self) -> OutlookCapabilities:
        """
        Get Outlook capabilities and features.
        
        Returns:
            Outlook capabilities object
        """
        return self._outlook_capabilities
    
    def create_email_preview(
        self, 
        customer: Customer, 
        template: MessageTemplate,
        use_html: bool = False
    ) -> Dict[str, str]:
        """
        Create email preview without sending or creating draft.
        
        Args:
            customer: Customer for the email
            template: Email template to use
            use_html: Whether to use HTML formatting
            
        Returns:
            Dictionary with preview content
        """
        try:
            # Render template
            rendered = template.render(customer)
            subject = rendered.get('subject', '')
            content = rendered.get('content', '')
            
            preview = {
                'to': customer.email,
                'subject': subject,
                'content': content,
                'format': 'html' if use_html else 'plain'
            }
            
            if use_html and self._outlook_capabilities.supports_html:
                preview['html_content'] = self._convert_to_html(content)
            else:
                preview['formatted_content'] = self._format_email_content(content)
            
            return preview
            
        except Exception as e:
            logger.error(f"Failed to create email preview: {e}")
            return {
                'error': str(e),
                'to': customer.email if customer else 'Unknown',
                'subject': 'Preview Error',
                'content': f'Error creating preview: {e}'
            }
    
    def _format_email_content(self, content: str) -> str:
        """
        Format email content for proper display in Outlook.
        
        Args:
            content: Plain text content
            
        Returns:
            Formatted content
        """
        if not content:
            return ""
        
        # Normalize line endings
        formatted = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Convert to Windows line endings for Outlook
        formatted = formatted.replace('\n', '\r\n')
        
        return formatted
    
    def get_outlook_version(self) -> Optional[str]:
        """
        Get Outlook version information.
        
        Returns:
            Outlook version string or None if unavailable
        """
        try:
            if not self.is_outlook_running():
                if not self.start_outlook():
                    return None
            
            version = self.outlook_app.Version
            logger.info(f"Outlook version: {version}")
            return version
            
        except Exception as e:
            logger.warning(f"Failed to get Outlook version: {e}")
            return None
    
    def get_detailed_version_info(self) -> Dict[str, Any]:
        """
        Get detailed Outlook version and capability information.
        
        Returns:
            Dictionary with detailed version information
        """
        info = {
            'version_string': None,
            'version_enum': self._outlook_version.value,
            'build_number': None,
            'product_name': None,
            'capabilities': None,
            'is_office_365': False
        }
        
        try:
            if self.outlook_app:
                version_string = self.outlook_app.Version
                info['version_string'] = version_string
                
                # Parse build number
                try:
                    parts = version_string.split('.')
                    if len(parts) >= 3:
                        info['build_number'] = int(parts[2])
                        # Office 365 typically has higher build numbers
                        info['is_office_365'] = info['build_number'] > 10000
                except (ValueError, IndexError):
                    pass
                
                # Try to get product name
                try:
                    info['product_name'] = getattr(self.outlook_app, 'Name', 'Microsoft Outlook')
                except:
                    info['product_name'] = 'Microsoft Outlook'
            
            info['capabilities'] = {
                'supports_html': self._outlook_capabilities.supports_html,
                'supports_rtf': self._outlook_capabilities.supports_rtf,
                'supports_attachments': self._outlook_capabilities.supports_attachments,
                'supports_scheduling': self._outlook_capabilities.supports_scheduling,
                'supports_tracking': self._outlook_capabilities.supports_tracking,
                'max_recipients': self._outlook_capabilities.max_recipients
            }
            
        except Exception as e:
            logger.warning(f"Failed to get detailed version info: {e}")
            info['error'] = str(e)
        
        return info
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test connection to Outlook with comprehensive diagnostics.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Test COM availability
            if not WIN32COM_AVAILABLE:
                return False, self.i18n_manager.tr("outlook_windows_pywin32_required")
            
            # Test Outlook connection
            if not self.is_outlook_running():
                if not self.start_outlook():
                    return False, self.i18n_manager.tr("outlook_cannot_start")
            
            # Test basic functionality
            try:
                version = self.get_outlook_version()
                profile = self.get_current_profile()
                
                message_parts = [f"Connected to Outlook {version}"]
                
                if profile:
                    message_parts.append(f"Profile: {profile.name}")
                    if profile.email_address:
                        message_parts.append(f"Email: {profile.email_address}")
                
                message_parts.append(f"Capabilities: HTML={self._outlook_capabilities.supports_html}")
                
                return True, " | ".join(message_parts)
                
            except Exception as e:
                return False, f"Connection test failed during functionality check: {e}"
            
        except Exception as e:
            return False, f"Connection test failed: {e}"
    
    def cleanup(self) -> None:
        """
        Explicit cleanup method for proper resource management.
        """
        logger.debug("Cleaning up Outlook Windows service...")
        
        with self._lock:
            try:
                # Clean up COM objects
                self._cleanup_com_objects()
                
                # Reset state
                self._connection_attempts = 0
                self._last_connection_error = None
                
                # Uninitialize COM if we initialized it
                if self._com_initialized:
                    try:
                        pythoncom.CoUninitialize()
                        self._com_initialized = False
                        logger.debug("COM uninitialized")
                    except Exception as e:
                        logger.debug(f"COM uninitialize warning: {e}")
                
            except Exception as e:
                logger.debug(f"Error during cleanup: {e}")
    
    def __del__(self):
        """Cleanup COM objects on destruction."""
        try:
            self.cleanup()
        except:
            pass  # Ignore errors during destruction
