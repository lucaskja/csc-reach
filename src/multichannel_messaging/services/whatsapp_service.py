"""
WhatsApp Business service for sending messages through WhatsApp Business API.
"""

import time
from typing import List, Dict, Optional, Tuple

from .api_clients.whatsapp_api_client import WhatsAppAPIClient
from ..core.models import Customer, MessageTemplate, MessageRecord, MessageStatus
from ..utils.exceptions import WhatsAppAPIError, WhatsAppConfigurationError, ServiceUnavailableError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class WhatsAppService:
    """WhatsApp Business service for message sending and management."""
    
    def __init__(
        self, 
        access_token: str, 
        phone_number_id: str,
        api_version: str = "v18.0",
        base_url: Optional[str] = None
    ):
        """
        Initialize WhatsApp service.
        
        Args:
            access_token: WhatsApp Business API access token
            phone_number_id: Phone number ID for sending messages
            api_version: API version to use
            base_url: Custom base URL for on-premises API
        """
        if not access_token or not phone_number_id:
            raise WhatsAppConfigurationError("WhatsApp access token and phone number ID are required")
        
        try:
            self.api_client = WhatsAppAPIClient(
                access_token=access_token,
                phone_number_id=phone_number_id,
                api_version=api_version,
                base_url=base_url
            )
            
            # Test connection on initialization
            success, message = self.test_connection()
            if not success:
                raise WhatsAppConfigurationError(f"WhatsApp connection test failed: {message}")
            
            logger.info("WhatsApp service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WhatsApp service: {e}")
            raise ServiceUnavailableError(f"WhatsApp service initialization failed: {e}")
    
    def send_message(self, customer: Customer, template: MessageTemplate) -> bool:
        """
        Send a WhatsApp message to a single customer.
        
        Args:
            customer: Customer to send message to
            template: Message template to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate customer phone number
            if not customer.phone or not self.api_client.validate_phone_number(customer.phone):
                logger.warning(f"Invalid phone number for customer {customer.name}: {customer.phone}")
                return False
            
            # Render template for WhatsApp
            rendered = template.render(customer)
            whatsapp_content = rendered.get('whatsapp_content') or rendered.get('content', '')
            
            if not whatsapp_content:
                logger.warning(f"No WhatsApp content available for template {template.name}")
                return False
            
            # Format WhatsApp message
            formatted_message = self._format_whatsapp_message(whatsapp_content)
            
            # Send message via API
            response = self.api_client.send_text_message(
                to=customer.phone,
                message=formatted_message
            )
            
            # Check if message was sent successfully
            if 'messages' in response and response['messages']:
                message_id = response['messages'][0].get('id')
                logger.info(f"WhatsApp message sent to {customer.phone}. Message ID: {message_id}")
                return True
            else:
                logger.warning(f"Unexpected response format when sending to {customer.phone}")
                return False
                
        except WhatsAppAPIError as e:
            logger.error(f"WhatsApp API error sending to {customer.phone}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending WhatsApp message to {customer.phone}: {e}")
            return False
    
    def send_bulk_messages(
        self, 
        customers: List[Customer], 
        template: MessageTemplate,
        batch_size: int = 10,
        delay_between_messages: float = 1.0
    ) -> List[MessageRecord]:
        """
        Send bulk WhatsApp messages.
        
        Args:
            customers: List of customers to send messages to
            template: Message template to use
            batch_size: Number of messages to send in each batch
            delay_between_messages: Delay between messages in seconds
            
        Returns:
            List of message records with sending results
        """
        records = []
        
        try:
            logger.info(f"Starting bulk WhatsApp send to {len(customers)} recipients")
            
            for i, customer in enumerate(customers):
                try:
                    # Create message record
                    record = MessageRecord(customer=customer, template=template)
                    record.status = MessageStatus.SENDING
                    record.channel = "whatsapp"
                    
                    # Send message
                    success = self.send_message(customer, template)
                    
                    if success:
                        record.mark_as_sent()
                        logger.debug(f"WhatsApp message {i+1}/{len(customers)} sent successfully to {customer.phone}")
                    else:
                        record.mark_as_failed("Failed to send WhatsApp message")
                        logger.warning(f"WhatsApp message {i+1}/{len(customers)} failed to {customer.phone}")
                    
                    records.append(record)
                    
                    # Add delay between messages to respect rate limits
                    if delay_between_messages > 0 and i < len(customers) - 1:
                        time.sleep(delay_between_messages)
                    
                    # Batch processing pause
                    if (i + 1) % batch_size == 0 and i < len(customers) - 1:
                        logger.info(f"Processed batch of {batch_size} WhatsApp messages, pausing...")
                        time.sleep(2.0)  # Longer pause between batches
                
                except Exception as e:
                    record = MessageRecord(customer=customer, template=template)
                    record.channel = "whatsapp"
                    record.mark_as_failed(str(e))
                    records.append(record)
                    logger.error(f"Failed to process WhatsApp message for {customer.phone}: {e}")
            
            successful = sum(1 for r in records if r.status == MessageStatus.SENT)
            failed = sum(1 for r in records if r.status == MessageStatus.FAILED)
            
            logger.info(f"Bulk WhatsApp send completed: {successful} successful, {failed} failed")
            
        except Exception as e:
            logger.error(f"Bulk WhatsApp send failed: {e}")
            # Mark remaining customers as failed
            for customer in customers[len(records):]:
                record = MessageRecord(customer=customer, template=template)
                record.channel = "whatsapp"
                record.mark_as_failed(f"Bulk send failed: {e}")
                records.append(record)
        
        return records
    
    def create_draft_message(self, customer: Customer, template: MessageTemplate) -> bool:
        """
        Create a draft WhatsApp message (for preview/testing purposes).
        
        Note: WhatsApp doesn't have a draft concept like email, so this
        validates the message format and returns the formatted content.
        
        Args:
            customer: Customer for the message
            template: Message template to use
            
        Returns:
            True if message format is valid, False otherwise
        """
        try:
            # Validate phone number
            if not customer.phone or not self.api_client.validate_phone_number(customer.phone):
                logger.warning(f"Invalid phone number for draft: {customer.phone}")
                return False
            
            # Render and format message
            rendered = template.render(customer)
            whatsapp_content = rendered.get('whatsapp_content') or rendered.get('content', '')
            
            if not whatsapp_content:
                logger.warning("No WhatsApp content available for draft")
                return False
            
            formatted_message = self._format_whatsapp_message(whatsapp_content)
            
            # Log the draft message for review
            logger.info(f"WhatsApp draft created for {customer.phone}")
            logger.info(f"Draft content: {formatted_message}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create WhatsApp draft for {customer.phone}: {e}")
            return False
    
    def validate_phone_number(self, phone: str) -> bool:
        """
        Validate phone number for WhatsApp.
        
        Args:
            phone: Phone number to validate
            
        Returns:
            True if valid, False otherwise
        """
        return self.api_client.validate_phone_number(phone)
    
    def get_account_info(self) -> Optional[Dict]:
        """
        Get WhatsApp Business Account information.
        
        Returns:
            Account information or None if unavailable
        """
        try:
            return self.api_client.get_account_info()
        except Exception as e:
            logger.error(f"Failed to get WhatsApp account info: {e}")
            return None
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test connection to WhatsApp Business API.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            return self.api_client.test_connection()
        except Exception as e:
            return False, f"Connection test failed: {e}"
    
    def get_business_profile(self) -> Optional[Dict]:
        """
        Get WhatsApp Business Profile information.
        
        Returns:
            Business profile data or None if unavailable
        """
        try:
            return self.api_client.get_business_profile()
        except Exception as e:
            logger.error(f"Failed to get WhatsApp business profile: {e}")
            return None
    
    def _format_whatsapp_message(self, content: str) -> str:
        """
        Format message content for WhatsApp.
        
        Args:
            content: Raw message content
            
        Returns:
            Formatted WhatsApp message
        """
        if not content:
            return ""
        
        # WhatsApp supports basic formatting
        # Convert common formatting to WhatsApp format
        formatted = content.strip()
        
        # Ensure message doesn't exceed WhatsApp limits
        # WhatsApp text messages can be up to 4096 characters
        if len(formatted) > 4096:
            formatted = formatted[:4093] + "..."
            logger.warning("Message truncated to fit WhatsApp character limit")
        
        return formatted
    
    def get_message_character_count(self, content: str) -> int:
        """
        Get character count for WhatsApp message.
        
        Args:
            content: Message content
            
        Returns:
            Character count
        """
        return len(self._format_whatsapp_message(content))
    
    def is_message_valid(self, content: str) -> Tuple[bool, str]:
        """
        Validate WhatsApp message content.
        
        Args:
            content: Message content to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not content or not content.strip():
            return False, "Message content cannot be empty"
        
        formatted = self._format_whatsapp_message(content)
        
        if len(formatted) > 4096:
            return False, f"Message too long ({len(formatted)} characters). Maximum is 4096."
        
        return True, "Message is valid"
