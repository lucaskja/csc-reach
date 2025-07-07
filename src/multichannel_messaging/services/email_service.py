"""
Unified email service that automatically detects platform and uses appropriate Outlook integration.
"""

from typing import List, Optional, Tuple, Union

from ..core.models import Customer, MessageTemplate, MessageRecord
from ..utils.exceptions import ServiceUnavailableError
from ..utils.platform_utils import is_windows, is_macos
from ..utils.logger import get_logger

logger = get_logger(__name__)


class EmailService:
    """Unified email service for cross-platform Outlook integration."""
    
    def __init__(self):
        """Initialize email service with platform-specific implementation."""
        self.outlook_service = None
        self._initialize_platform_service()
    
    def _initialize_platform_service(self) -> None:
        """Initialize the appropriate platform-specific Outlook service."""
        try:
            if is_windows():
                from .outlook_windows import OutlookWindowsService
                self.outlook_service = OutlookWindowsService()
                logger.info("Initialized Windows Outlook service")
                
            elif is_macos():
                from .outlook_macos import OutlookMacOSService
                self.outlook_service = OutlookMacOSService()
                logger.info("Initialized macOS Outlook service")
                
            else:
                raise ServiceUnavailableError(
                    "Outlook integration is only supported on Windows and macOS"
                )
                
        except Exception as e:
            logger.error(f"Failed to initialize platform-specific Outlook service: {e}")
            raise ServiceUnavailableError(f"Failed to initialize email service: {e}")
    
    def is_outlook_running(self) -> bool:
        """
        Check if Outlook is currently running.
        
        Returns:
            True if Outlook is running, False otherwise
        """
        if not self.outlook_service:
            return False
        return self.outlook_service.is_outlook_running()
    
    def start_outlook(self) -> bool:
        """
        Start Outlook application.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.outlook_service:
            return False
        return self.outlook_service.start_outlook()
    
    def send_email(self, customer: Customer, template: MessageTemplate) -> bool:
        """
        Send a single email using Outlook.
        
        Args:
            customer: Customer to send email to
            template: Email template to use
            
        Returns:
            True if successful, False otherwise
        """
        if not self.outlook_service:
            return False
        return self.outlook_service.send_email(customer, template)
    
    def send_bulk_emails(
        self, 
        customers: List[Customer], 
        template: MessageTemplate,
        batch_size: int = 10,
        delay_between_emails: float = 1.0
    ) -> List[MessageRecord]:
        """
        Send bulk emails using Outlook.
        
        Args:
            customers: List of customers to send emails to
            template: Email template to use
            batch_size: Number of emails to send in each batch
            delay_between_emails: Delay between emails in seconds
            
        Returns:
            List of message records with sending results
        """
        if not self.outlook_service:
            return []
        
        return self.outlook_service.send_bulk_emails(
            customers, template, batch_size, delay_between_emails
        )
    
    def create_draft_email(self, customer: Customer, template: MessageTemplate) -> bool:
        """
        Create a draft email in Outlook.
        
        Args:
            customer: Customer for the email
            template: Email template to use
            
        Returns:
            True if successful, False otherwise
        """
        if not self.outlook_service:
            return False
        return self.outlook_service.create_draft_email(customer, template)
    
    def get_outlook_version(self) -> Optional[str]:
        """
        Get Outlook version information.
        
        Returns:
            Outlook version string or None if unavailable
        """
        if not self.outlook_service:
            return None
        return self.outlook_service.get_outlook_version()
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test connection to Outlook.
        
        Returns:
            Tuple of (success, message)
        """
        if not self.outlook_service:
            return False, "Email service not initialized"
        
        return self.outlook_service.test_connection()
    
    def get_platform_info(self) -> str:
        """
        Get information about the current platform and service.
        
        Returns:
            Platform information string
        """
        if is_windows():
            return "Windows (COM Integration)"
        elif is_macos():
            return "macOS (AppleScript Integration)"
        else:
            return "Unsupported Platform"
