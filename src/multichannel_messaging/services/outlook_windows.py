"""
Windows Outlook integration using COM (Component Object Model).
"""

import time
from typing import List, Dict, Optional, Tuple

try:
    import win32com.client
    import pythoncom
    WIN32COM_AVAILABLE = True
except ImportError:
    WIN32COM_AVAILABLE = False

from ..core.models import Customer, MessageTemplate, MessageRecord, MessageStatus
from ..utils.exceptions import OutlookIntegrationError, ServiceUnavailableError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class OutlookWindowsService:
    """Windows Outlook integration service using COM."""
    
    def __init__(self):
        """Initialize Windows Outlook service."""
        self.outlook_app = None
        self.namespace = None
        self._check_outlook_availability()
    
    def _check_outlook_availability(self) -> None:
        """Check if Outlook is available on Windows."""
        if not WIN32COM_AVAILABLE:
            raise ServiceUnavailableError(
                "pywin32 is required for Windows Outlook integration. "
                "Please install it with: pip install pywin32"
            )
        
        try:
            # Try to connect to Outlook
            self._connect_to_outlook()
            logger.info("Outlook Windows service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Outlook Windows service: {e}")
            raise ServiceUnavailableError(f"Outlook is not available: {e}")
    
    def _connect_to_outlook(self) -> None:
        """Connect to Outlook COM object."""
        try:
            # Initialize COM
            pythoncom.CoInitialize()
            
            # Try to get existing Outlook instance first
            try:
                self.outlook_app = win32com.client.GetActiveObject("Outlook.Application")
                logger.debug("Connected to existing Outlook instance")
            except:
                # If no existing instance, create new one
                self.outlook_app = win32com.client.Dispatch("Outlook.Application")
                logger.debug("Created new Outlook instance")
            
            # Get the namespace
            self.namespace = self.outlook_app.GetNamespace("MAPI")
            
        except Exception as e:
            raise OutlookIntegrationError(f"Failed to connect to Outlook: {e}")
    
    def is_outlook_running(self) -> bool:
        """
        Check if Outlook is currently running.
        
        Returns:
            True if Outlook is running, False otherwise
        """
        try:
            if self.outlook_app is None:
                return False
            
            # Try to access Outlook to see if it's still alive
            _ = self.outlook_app.Version
            return True
            
        except Exception:
            return False
    
    def start_outlook(self) -> bool:
        """
        Start Outlook application.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.is_outlook_running():
                logger.info("Outlook is already running")
                return True
            
            # Reconnect to Outlook
            self._connect_to_outlook()
            
            # Wait a moment for Outlook to fully initialize
            time.sleep(2)
            
            if self.is_outlook_running():
                logger.info("Outlook started successfully")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to start Outlook: {e}")
            return False
    
    def send_email(self, customer: Customer, template: MessageTemplate) -> bool:
        """
        Send a single email using Outlook.
        
        Args:
            customer: Customer to send email to
            template: Email template to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure Outlook is running
            if not self.is_outlook_running():
                if not self.start_outlook():
                    raise OutlookIntegrationError("Cannot start Outlook")
            
            # Render template
            rendered = template.render(customer)
            subject = rendered.get('subject', '')
            content = rendered.get('content', '')
            
            # Format content with proper line breaks for Outlook
            formatted_content = self._format_email_content(content)
            
            # Create email item
            mail_item = self.outlook_app.CreateItem(0)  # 0 = olMailItem
            
            # Set email properties
            mail_item.To = customer.email
            mail_item.Subject = subject
            mail_item.Body = formatted_content
            
            # Send the email
            mail_item.Send()
            
            logger.info(f"Email sent to {customer.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {customer.email}: {e}")
            return False
    
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
        records = []
        
        try:
            # Ensure Outlook is running
            if not self.is_outlook_running():
                if not self.start_outlook():
                    raise OutlookIntegrationError("Cannot start Outlook")
            
            logger.info(f"Starting bulk email send to {len(customers)} recipients")
            
            for i, customer in enumerate(customers):
                try:
                    # Create message record
                    record = MessageRecord(customer=customer, template=template)
                    record.status = MessageStatus.SENDING
                    
                    # Send email
                    success = self.send_email(customer, template)
                    
                    if success:
                        record.mark_as_sent()
                        logger.debug(f"Email {i+1}/{len(customers)} sent successfully to {customer.email}")
                    else:
                        record.mark_as_failed("Failed to send email")
                        logger.warning(f"Email {i+1}/{len(customers)} failed to {customer.email}")
                    
                    records.append(record)
                    
                    # Add delay between emails
                    if delay_between_emails > 0 and i < len(customers) - 1:
                        time.sleep(delay_between_emails)
                    
                    # Batch processing pause
                    if (i + 1) % batch_size == 0 and i < len(customers) - 1:
                        logger.info(f"Processed batch of {batch_size} emails, pausing...")
                        time.sleep(2.0)  # Longer pause between batches
                
                except Exception as e:
                    record = MessageRecord(customer=customer, template=template)
                    record.mark_as_failed(str(e))
                    records.append(record)
                    logger.error(f"Failed to process email for {customer.email}: {e}")
            
            successful = sum(1 for r in records if r.status == MessageStatus.SENT)
            failed = sum(1 for r in records if r.status == MessageStatus.FAILED)
            
            logger.info(f"Bulk email send completed: {successful} successful, {failed} failed")
            
        except Exception as e:
            logger.error(f"Bulk email send failed: {e}")
            # Mark remaining customers as failed
            for customer in customers[len(records):]:
                record = MessageRecord(customer=customer, template=template)
                record.mark_as_failed(f"Bulk send failed: {e}")
                records.append(record)
        
        return records
    
    def create_draft_email(self, customer: Customer, template: MessageTemplate) -> bool:
        """
        Create a draft email in Outlook.
        
        Args:
            customer: Customer for the email
            template: Email template to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure Outlook is running
            if not self.is_outlook_running():
                if not self.start_outlook():
                    raise OutlookIntegrationError("Cannot start Outlook")
            
            # Render template
            rendered = template.render(customer)
            subject = rendered.get('subject', '')
            content = rendered.get('content', '')
            
            # Format content with proper line breaks
            formatted_content = self._format_email_content(content)
            
            # Create email item
            mail_item = self.outlook_app.CreateItem(0)  # 0 = olMailItem
            
            # Set email properties
            mail_item.To = customer.email
            mail_item.Subject = subject
            mail_item.Body = formatted_content
            
            # Save as draft (don't send)
            mail_item.Save()
            
            # Display the draft for user review
            mail_item.Display()
            
            logger.info(f"Draft email created for {customer.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create draft email for {customer.email}: {e}")
            return False
    
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
                self.start_outlook()
            
            version = self.outlook_app.Version
            logger.info(f"Outlook version: {version}")
            return version
            
        except Exception as e:
            logger.warning(f"Failed to get Outlook version: {e}")
            return None
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test connection to Outlook.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Try to connect
            if not self.is_outlook_running():
                if not self.start_outlook():
                    return False, "Cannot start Outlook"
            
            # Try to get version
            version = self.get_outlook_version()
            if version:
                return True, f"Connected to Outlook {version}"
            
            return True, "Connected to Outlook successfully"
            
        except Exception as e:
            return False, f"Connection test failed: {e}"
    
    def __del__(self):
        """Cleanup COM objects."""
        try:
            if WIN32COM_AVAILABLE:
                pythoncom.CoUninitialize()
        except:
            pass
