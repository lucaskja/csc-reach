"""
Unified email service that automatically detects platform and uses appropriate Outlook integration.
"""

from typing import List, Optional, Tuple, Union, Dict, Any
from inspect import signature
from datetime import datetime
import time

from ..core.models import Customer, MessageTemplate, MessageRecord
from ..core.email_composer import EmailComposer, EmailComposition, EmailFormat
from ..core.email_analytics import EmailAnalyticsManager
from ..utils.exceptions import ServiceUnavailableError
from ..utils.platform_utils import is_windows, is_macos
from ..utils.logger import get_logger

logger = get_logger(__name__)


class EmailService:
    """Unified email service for cross-platform Outlook integration."""
    
    def __init__(self):
        """Initialize email service with platform-specific implementation."""
        self.outlook_service = None
        self.email_composer = EmailComposer()
        self.analytics_manager = EmailAnalyticsManager()
        self._current_campaign_id = None
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
    
    def send_email_advanced(
        self,
        customer: Customer,
        template: MessageTemplate,
        use_html: bool = False,
        attachments: Optional[List[str]] = None,
        custom_variables: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send email with advanced composition features.
        
        Args:
            customer: Customer to send email to
            template: Email template to use
            use_html: Whether to use HTML formatting
            attachments: List of attachment file paths
            custom_variables: Additional template variables
            
        Returns:
            True if successful, False otherwise
        """
        if not self.outlook_service:
            return False
        
        try:
            # Compose email with advanced features
            format_type = EmailFormat.HTML if use_html else EmailFormat.PLAIN_TEXT
            composition = self.email_composer.compose_email(
                customer=customer,
                template=template,
                format_type=format_type,
                attachments=attachments,
                custom_variables=custom_variables
            )
            
            # Validate composition
            if not composition.is_valid():
                logger.error(f"Invalid email composition for {customer.email}: {composition.validation_errors}")
                return False
            
            # Send using platform-specific service with enhanced features
            if hasattr(self.outlook_service, 'send_email') and len(signature(self.outlook_service.send_email).parameters) > 2:
                # Enhanced service with additional parameters
                return self.outlook_service.send_email(
                    customer=customer,
                    template=template,
                    use_html=use_html,
                    attachments=attachments
                )
            else:
                # Fallback to basic service
                return self.outlook_service.send_email(customer, template)
                
        except Exception as e:
            logger.error(f"Failed to send advanced email to {customer.email}: {e}")
            return False
    
    def create_email_preview(
        self,
        customer: Customer,
        template: MessageTemplate,
        use_html: bool = False,
        attachments: Optional[List[str]] = None,
        custom_variables: Optional[Dict[str, str]] = None
    ) -> EmailComposition:
        """
        Create email preview with advanced composition.
        
        Args:
            customer: Customer information
            template: Email template
            use_html: Whether to use HTML formatting
            attachments: List of attachment file paths
            custom_variables: Additional template variables
            
        Returns:
            EmailComposition object for preview
        """
        try:
            format_type = EmailFormat.HTML if use_html else EmailFormat.PLAIN_TEXT
            return self.email_composer.compose_email(
                customer=customer,
                template=template,
                format_type=format_type,
                attachments=attachments,
                custom_variables=custom_variables
            )
        except Exception as e:
            logger.error(f"Failed to create email preview for {customer.email}: {e}")
            # Return basic composition with error
            return EmailComposition(
                to_address=customer.email,
                subject="Preview Error",
                content=f"Error creating preview: {e}",
                validation_errors=[str(e)]
            )
    
    def create_draft_email_advanced(
        self,
        customer: Customer,
        template: MessageTemplate,
        use_html: bool = False,
        attachments: Optional[List[str]] = None,
        custom_variables: Optional[Dict[str, str]] = None,
        display_draft: bool = True
    ) -> bool:
        """
        Create draft email with advanced composition features.
        
        Args:
            customer: Customer for the email
            template: Email template to use
            use_html: Whether to use HTML formatting
            attachments: List of attachment file paths
            custom_variables: Additional template variables
            display_draft: Whether to display the draft for review
            
        Returns:
            True if successful, False otherwise
        """
        if not self.outlook_service:
            return False
        
        try:
            # Create composition
            format_type = EmailFormat.HTML if use_html else EmailFormat.PLAIN_TEXT
            composition = self.email_composer.compose_email(
                customer=customer,
                template=template,
                format_type=format_type,
                attachments=attachments,
                custom_variables=custom_variables
            )
            
            # Validate composition
            if not composition.is_valid():
                logger.warning(f"Creating draft with validation errors for {customer.email}: {composition.validation_errors}")
            
            # Create draft using platform-specific service
            if hasattr(self.outlook_service, 'create_draft_email') and len(signature(self.outlook_service.create_draft_email).parameters) > 2:
                # Enhanced service with additional parameters
                return self.outlook_service.create_draft_email(
                    customer=customer,
                    template=template,
                    use_html=use_html,
                    attachments=attachments,
                    display_draft=display_draft
                )
            else:
                # Fallback to basic service
                return self.outlook_service.create_draft_email(customer, template)
                
        except Exception as e:
            logger.error(f"Failed to create advanced draft for {customer.email}: {e}")
            return False
    
    def get_outlook_capabilities(self) -> Dict[str, Any]:
        """
        Get Outlook capabilities and features.
        
        Returns:
            Dictionary with capability information
        """
        if not self.outlook_service:
            return {}
        
        try:
            if hasattr(self.outlook_service, 'get_outlook_capabilities'):
                return self.outlook_service.get_outlook_capabilities().__dict__
            elif hasattr(self.outlook_service, 'get_connection_health'):
                health = self.outlook_service.get_connection_health()
                return health.get('capabilities', {})
            else:
                # Basic capabilities for older services
                return {
                    'supports_html': True,
                    'supports_attachments': True,
                    'max_recipients': 100
                }
        except Exception as e:
            logger.error(f"Failed to get Outlook capabilities: {e}")
            return {}
    
    def start_email_campaign(
        self,
        campaign_name: str,
        template: Optional[MessageTemplate] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start a new email campaign for analytics tracking.
        
        Args:
            campaign_name: Name of the campaign
            template: Email template being used
            metadata: Additional campaign metadata
            
        Returns:
            Campaign ID
        """
        self._current_campaign_id = self.analytics_manager.start_campaign(
            campaign_name=campaign_name,
            template=template,
            metadata=metadata
        )
        
        logger.info(f"Started email campaign: {campaign_name} ({self._current_campaign_id})")
        return self._current_campaign_id
    
    def send_email_with_tracking(
        self,
        customer: Customer,
        template: MessageTemplate,
        campaign_id: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Send email with analytics tracking.
        
        Args:
            customer: Customer to send email to
            template: Email template to use
            campaign_id: Optional campaign ID for tracking
            
        Returns:
            Tuple of (success, message_id)
        """
        if not self.outlook_service:
            return False, None
        
        try:
            # Create message record for tracking
            message_record = MessageRecord(customer=customer, template=template)
            
            # Track email sending
            message_id = self.analytics_manager.track_email_sent(
                message_record=message_record,
                campaign_id=campaign_id or self._current_campaign_id
            )
            
            # Send the email
            success = self.outlook_service.send_email(customer, template)
            
            if success:
                # Track delivery (immediate for Outlook since it handles delivery)
                self.analytics_manager.track_email_delivered(message_id)
                logger.info(f"Email sent and tracked: {message_id} to {customer.email}")
            else:
                # Track as bounced if sending failed
                from ..core.email_analytics import BounceType
                self.analytics_manager.track_email_bounced(
                    message_id=message_id,
                    bounce_type=BounceType.SOFT,
                    bounce_reason="Failed to send via Outlook"
                )
                logger.warning(f"Email send failed and tracked: {message_id} to {customer.email}")
            
            return success, message_id
            
        except Exception as e:
            logger.error(f"Failed to send email with tracking to {customer.email}: {e}")
            return False, None
    
    def send_bulk_emails_with_tracking(
        self,
        customers: List[Customer],
        template: MessageTemplate,
        campaign_name: Optional[str] = None,
        batch_size: int = 10,
        delay_between_emails: float = 1.0,
        progress_callback: Optional[callable] = None
    ) -> Tuple[List[MessageRecord], str]:
        """
        Send bulk emails with comprehensive tracking.
        
        Args:
            customers: List of customers to send emails to
            template: Email template to use
            campaign_name: Name for the campaign
            batch_size: Number of emails to send in each batch
            delay_between_emails: Delay between emails in seconds
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (message_records, campaign_id)
        """
        if not self.outlook_service:
            return [], ""
        
        # Start campaign if not already started
        if not campaign_name:
            campaign_name = f"Bulk Email Campaign - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        campaign_id = self.start_email_campaign(
            campaign_name=campaign_name,
            template=template,
            metadata={
                'total_recipients': len(customers),
                'batch_size': batch_size,
                'template_id': template.id if hasattr(template, 'id') else None
            }
        )
        
        records = []
        
        try:
            logger.info(f"Starting tracked bulk email send to {len(customers)} recipients")
            
            for i, customer in enumerate(customers):
                try:
                    # Update progress if callback provided
                    if progress_callback:
                        progress_callback(i, len(customers), customer.email)
                    
                    # Send email with tracking
                    success, message_id = self.send_email_with_tracking(
                        customer=customer,
                        template=template,
                        campaign_id=campaign_id
                    )
                    
                    # Create message record
                    record = MessageRecord(customer=customer, template=template)
                    if success:
                        record.mark_as_sent()
                    else:
                        record.mark_as_failed("Failed to send email")
                    
                    # Store message ID for future reference
                    if message_id:
                        record.metadata = record.metadata or {}
                        record.metadata['message_id'] = message_id
                    
                    records.append(record)
                    
                    # Add delay between emails
                    if delay_between_emails > 0 and i < len(customers) - 1:
                        time.sleep(delay_between_emails)
                    
                    # Batch processing pause
                    if (i + 1) % batch_size == 0 and i < len(customers) - 1:
                        logger.info(f"Processed batch of {batch_size} emails, pausing...")
                        time.sleep(2.0)
                
                except Exception as e:
                    record = MessageRecord(customer=customer, template=template)
                    record.mark_as_failed(str(e))
                    records.append(record)
                    logger.error(f"Failed to process email for {customer.email}: {e}")
            
            # Final progress update
            if progress_callback:
                progress_callback(len(customers), len(customers), "Complete")
            
            successful = sum(1 for r in records if r.status.value == "sent")
            failed = sum(1 for r in records if r.status.value == "failed")
            
            logger.info(f"Tracked bulk email send completed: {successful} successful, {failed} failed")
            
        except Exception as e:
            logger.error(f"Bulk email send with tracking failed: {e}")
            # Mark remaining customers as failed
            for customer in customers[len(records):]:
                record = MessageRecord(customer=customer, template=template)
                record.mark_as_failed(f"Bulk send failed: {e}")
                records.append(record)
        
        return records, campaign_id
    
    def get_analytics_manager(self) -> EmailAnalyticsManager:
        """
        Get the analytics manager instance.
        
        Returns:
            EmailAnalyticsManager instance
        """
        return self.analytics_manager
    
    def get_campaign_performance(self, campaign_id: str) -> Optional[Any]:
        """
        Get performance statistics for a campaign.
        
        Args:
            campaign_id: Campaign ID to get stats for
            
        Returns:
            Campaign statistics or None if not found
        """
        return self.analytics_manager.get_campaign_performance(campaign_id)
    
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
