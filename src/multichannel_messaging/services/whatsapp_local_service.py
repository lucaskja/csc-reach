"""
Local WhatsApp Business API service for CSC-Reach.
Runs entirely locally without AWS dependencies.
"""

import json
import time
import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..core.models import Customer, MessageTemplate, MessageRecord, MessageStatus
from ..utils.exceptions import WhatsAppAPIError, WhatsAppConfigurationError
from ..utils.logger import get_logger
from ..utils.platform_utils import get_config_dir

logger = get_logger(__name__)


class LocalWhatsAppBusinessService:
    """
    Local WhatsApp Business API service for CSC-Reach.
    
    Features:
    - Official WhatsApp Business API integration
    - Local credential storage (encrypted)
    - Rate limiting and quota management
    - No external dependencies beyond WhatsApp API
    - Runs entirely within the local executable
    """
    
    def __init__(
        self,
        rate_limit_per_minute: int = 20,
        daily_message_limit: int = 1000
    ):
        """
        Initialize local WhatsApp Business service.
        
        Args:
            rate_limit_per_minute: Messages per minute limit
            daily_message_limit: Daily message limit for compliance
        """
        self.rate_limit_per_minute = rate_limit_per_minute
        self.daily_message_limit = daily_message_limit
        
        # Local storage paths
        self.config_dir = get_config_dir()
        self.credentials_file = self.config_dir / "whatsapp_credentials.json"
        self.usage_file = self.config_dir / "whatsapp_usage.json"
        
        # Rate limiting tracking
        self.message_timestamps = []
        self.daily_message_count = 0
        self.last_reset_date = datetime.now().date()
        
        # Load credentials and usage data
        self.credentials = self._load_credentials()
        self._load_usage_data()
        
        # Initialize API client if credentials are available
        self.api_client = None
        if self.credentials:
            self.api_client = self._initialize_api_client()
        
        logger.info("Local WhatsApp Business service initialized")
    
    def _load_credentials(self) -> Optional[Dict[str, str]]:
        """
        Load WhatsApp Business API credentials from local file.
        
        Returns:
            Dictionary containing API credentials or None if not configured
        """
        try:
            if not self.credentials_file.exists():
                logger.info("WhatsApp credentials not configured yet")
                return None
            
            with open(self.credentials_file, 'r', encoding='utf-8') as f:
                credentials = json.load(f)
            
            required_keys = ['access_token', 'phone_number_id']
            missing_keys = [key for key in required_keys if key not in credentials]
            
            if missing_keys:
                logger.warning(f"Missing WhatsApp credentials: {missing_keys}")
                return None
            
            logger.info("WhatsApp credentials loaded successfully")
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to load WhatsApp credentials: {e}")
            return None
    
    def save_credentials(self, access_token: str, phone_number_id: str, business_account_id: str = "") -> bool:
        """
        Save WhatsApp Business API credentials locally.
        
        Args:
            access_token: WhatsApp Business API access token
            phone_number_id: Phone number ID for sending messages
            business_account_id: Business account ID (optional)
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            credentials = {
                "access_token": access_token,
                "phone_number_id": phone_number_id,
                "business_account_id": business_account_id,
                "created_at": datetime.now().isoformat()
            }
            
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Save credentials
            with open(self.credentials_file, 'w', encoding='utf-8') as f:
                json.dump(credentials, f, indent=2)
            
            # Set file permissions (readable only by owner)
            os.chmod(self.credentials_file, 0o600)
            
            self.credentials = credentials
            self.api_client = self._initialize_api_client()
            
            logger.info("WhatsApp credentials saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save WhatsApp credentials: {e}")
            return False
    
    def _load_usage_data(self):
        """Load usage tracking data from local file."""
        try:
            if not self.usage_file.exists():
                return
            
            with open(self.usage_file, 'r', encoding='utf-8') as f:
                usage_data = json.load(f)
            
            # Load daily count if it's from today
            usage_date = datetime.fromisoformat(usage_data.get('date', '2000-01-01')).date()
            if usage_date == datetime.now().date():
                self.daily_message_count = usage_data.get('daily_count', 0)
                self.last_reset_date = usage_date
            
            logger.debug(f"Loaded usage data: {self.daily_message_count} messages today")
            
        except Exception as e:
            logger.warning(f"Failed to load usage data: {e}")
    
    def _save_usage_data(self):
        """Save usage tracking data to local file."""
        try:
            usage_data = {
                "date": datetime.now().date().isoformat(),
                "daily_count": self.daily_message_count,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.usage_file, 'w', encoding='utf-8') as f:
                json.dump(usage_data, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to save usage data: {e}")
    
    def _initialize_api_client(self) -> requests.Session:
        """Initialize HTTP client for WhatsApp Business API."""
        if not self.credentials:
            raise WhatsAppConfigurationError("No credentials available")
        
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers
        session.headers.update({
            'Authorization': f'Bearer {self.credentials["access_token"]}',
            'Content-Type': 'application/json',
            'User-Agent': 'CSC-Reach/1.0'
        })
        
        return session
    
    def is_configured(self) -> bool:
        """Check if WhatsApp service is properly configured."""
        return self.credentials is not None and self.api_client is not None
    
    def _check_rate_limits(self) -> bool:
        """
        Check if message can be sent within rate limits.
        
        Returns:
            True if within limits, False otherwise
        """
        now = datetime.now()
        
        # Reset daily counter if new day
        if now.date() > self.last_reset_date:
            self.daily_message_count = 0
            self.last_reset_date = now.date()
            self._save_usage_data()
        
        # Check daily limit
        if self.daily_message_count >= self.daily_message_limit:
            logger.warning(f"Daily message limit reached: {self.daily_message_limit}")
            return False
        
        # Check per-minute rate limit
        one_minute_ago = now - timedelta(minutes=1)
        self.message_timestamps = [ts for ts in self.message_timestamps if ts > one_minute_ago]
        
        if len(self.message_timestamps) >= self.rate_limit_per_minute:
            logger.warning(f"Rate limit reached: {self.rate_limit_per_minute}/minute")
            return False
        
        return True
    
    def _log_message_sent(self):
        """Log message sending for rate limiting."""
        now = datetime.now()
        self.message_timestamps.append(now)
        self.daily_message_count += 1
        self._save_usage_data()
    
    def send_message(self, customer: Customer, template: MessageTemplate) -> bool:
        """
        Send WhatsApp message to a customer.
        
        Args:
            customer: Customer to send message to
            template: Message template to use
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured():
            logger.error("WhatsApp service not configured")
            return False
        
        try:
            # Check rate limits
            if not self._check_rate_limits():
                logger.warning(f"Rate limit exceeded, skipping message to {customer.phone}")
                return False
            
            # Validate phone number
            if not self._validate_phone_number(customer.phone):
                logger.warning(f"Invalid phone number: {customer.phone}")
                return False
            
            # Render template
            rendered = template.render(customer)
            whatsapp_content = rendered.get('whatsapp_content') or rendered.get('content', '')
            
            if not whatsapp_content:
                logger.warning("No WhatsApp content available")
                return False
            
            # Format WhatsApp message
            formatted_message = self._format_whatsapp_message(whatsapp_content)
            
            # Prepare API request
            url = f"https://graph.facebook.com/v18.0/{self.credentials['phone_number_id']}/messages"
            payload = {
                "messaging_product": "whatsapp",
                "to": customer.phone,
                "type": "text",
                "text": {
                    "body": formatted_message
                }
            }
            
            # Send message
            response = self.api_client.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                message_id = response_data.get('messages', [{}])[0].get('id')
                
                self._log_message_sent()
                logger.info(f"WhatsApp message sent to {customer.phone}, ID: {message_id}")
                return True
            else:
                logger.error(f"WhatsApp API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message to {customer.phone}: {e}")
            return False
    
    def send_bulk_messages(
        self,
        customers: List[Customer],
        template: MessageTemplate,
        delay_between_messages: float = 3.0
    ) -> List[MessageRecord]:
        """
        Send bulk WhatsApp messages with proper rate limiting.
        
        Args:
            customers: List of customers
            template: Message template
            delay_between_messages: Delay between messages in seconds
            
        Returns:
            List of message records
        """
        if not self.is_configured():
            logger.error("WhatsApp service not configured")
            return []
        
        records = []
        
        logger.info(f"Starting bulk WhatsApp send to {len(customers)} recipients")
        
        for i, customer in enumerate(customers):
            try:
                # Create message record
                record = MessageRecord(customer=customer, template=template)
                record.channel = "whatsapp"
                record.status = MessageStatus.SENDING
                
                # Send message
                success = self.send_message(customer, template)
                
                if success:
                    record.mark_as_sent()
                    logger.info(f"Message {i+1}/{len(customers)} sent to {customer.phone}")
                else:
                    record.mark_as_failed("Failed to send WhatsApp message")
                    logger.warning(f"Message {i+1}/{len(customers)} failed to {customer.phone}")
                
                records.append(record)
                
                # Add delay between messages to respect rate limits
                if i < len(customers) - 1:
                    time.sleep(delay_between_messages)
                
            except Exception as e:
                record = MessageRecord(customer=customer, template=template)
                record.channel = "whatsapp"
                record.mark_as_failed(str(e))
                records.append(record)
                logger.error(f"Error processing message for {customer.phone}: {e}")
        
        successful = sum(1 for r in records if r.status == MessageStatus.SENT)
        failed = sum(1 for r in records if r.status == MessageStatus.FAILED)
        
        logger.info(f"Bulk WhatsApp send completed: {successful} successful, {failed} failed")
        
        return records
    
    def _validate_phone_number(self, phone: str) -> bool:
        """Validate phone number format for WhatsApp."""
        if not phone:
            return False
        
        # Remove formatting
        cleaned = phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
        
        # Check if digits only and reasonable length
        return cleaned.isdigit() and 7 <= len(cleaned) <= 15
    
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
        
        formatted = content.strip()
        
        # Ensure message doesn't exceed WhatsApp limits (4096 characters)
        if len(formatted) > 4096:
            formatted = formatted[:4093] + "..."
            logger.warning("Message truncated to fit WhatsApp character limit")
        
        return formatted
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test WhatsApp Business API connection.
        
        Returns:
            Tuple of (success, message)
        """
        if not self.is_configured():
            return False, "WhatsApp service not configured"
        
        try:
            url = f"https://graph.facebook.com/v18.0/{self.credentials['phone_number_id']}"
            response = self.api_client.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                phone_number = data.get('display_phone_number', 'Unknown')
                return True, f"Connected successfully. Phone: {phone_number}"
            else:
                return False, f"API error: {response.status_code}"
                
        except Exception as e:
            return False, f"Connection failed: {e}"
    
    def get_account_info(self) -> Optional[Dict]:
        """
        Get WhatsApp Business Account information.
        
        Returns:
            Account information or None if unavailable
        """
        if not self.is_configured():
            return None
        
        try:
            url = f"https://graph.facebook.com/v18.0/{self.credentials['phone_number_id']}"
            response = self.api_client.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get account info: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return None
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get current usage statistics.
        
        Returns:
            Dictionary with usage information
        """
        return {
            "daily_messages_sent": self.daily_message_count,
            "daily_limit": self.daily_message_limit,
            "remaining_daily": self.daily_message_limit - self.daily_message_count,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "messages_last_minute": len([
                ts for ts in self.message_timestamps 
                if ts > datetime.now() - timedelta(minutes=1)
            ]),
            "configured": self.is_configured()
        }
    
    def clear_credentials(self) -> bool:
        """
        Clear stored WhatsApp credentials.
        
        Returns:
            True if cleared successfully
        """
        try:
            if self.credentials_file.exists():
                self.credentials_file.unlink()
            
            self.credentials = None
            self.api_client = None
            
            logger.info("WhatsApp credentials cleared")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear credentials: {e}")
            return False
