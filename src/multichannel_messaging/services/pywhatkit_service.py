"""
PyWhatKit WhatsApp service for CSC-Reach.
Alternative WhatsApp implementation using browser automation.

⚠️ WARNING: This service uses browser automation which may violate WhatsApp's Terms of Service.
Use at your own risk. WhatsApp Business API is the recommended approach.
"""

import json
import time
import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from pathlib import Path

try:
    import pywhatkit as pwk
    PYWHATKIT_AVAILABLE = True
except ImportError:
    PYWHATKIT_AVAILABLE = False

from ..core.models import Customer, MessageTemplate, MessageRecord, MessageStatus
from ..utils.exceptions import WhatsAppAPIError, WhatsAppConfigurationError
from ..utils.logger import get_logger
from ..utils.platform_utils import get_config_dir

logger = get_logger(__name__)


class PyWhatKitService:
    """
    PyWhatKit-based WhatsApp service for CSC-Reach.
    
    ⚠️ WARNING: This service uses browser automation which:
    - May violate WhatsApp's Terms of Service
    - Could result in account suspension
    - Is unreliable and error-prone
    - Requires WhatsApp Web to be open
    
    Use WhatsApp Business API instead for production use.
    
    Features:
    - Browser automation via pywhatkit
    - Rate limiting and daily quotas
    - Message scheduling and delays
    - Local usage tracking
    - Safety limits and warnings
    """
    
    def __init__(
        self,
        rate_limit_per_minute: int = 5,  # Very conservative for pywhatkit
        daily_message_limit: int = 50,   # Much lower than Business API
        min_delay_seconds: int = 30      # Minimum delay between messages
    ):
        """
        Initialize PyWhatKit WhatsApp service.
        
        Args:
            rate_limit_per_minute: Messages per minute (very conservative)
            daily_message_limit: Daily message limit (much lower than Business API)
            min_delay_seconds: Minimum delay between messages for safety
        """
        self.rate_limit_per_minute = rate_limit_per_minute
        self.daily_message_limit = daily_message_limit
        self.min_delay_seconds = min_delay_seconds
        
        # Configuration and tracking
        self.config_dir = get_config_dir()
        self.config_file = self.config_dir / "pywhatkit_config.json"
        self.usage_file = self.config_dir / "pywhatkit_usage.json"
        
        # Runtime tracking
        self.message_timestamps: List[datetime] = []
        self.daily_usage = self._load_daily_usage()
        
        # Service state
        self._is_configured = False
        self._last_error: Optional[str] = None
        
        # Load configuration
        self._load_configuration()
        
        logger.info("PyWhatKit service initialized with conservative limits")
    
    def is_available(self) -> bool:
        """Check if pywhatkit is available."""
        return PYWHATKIT_AVAILABLE
    
    def is_configured(self) -> bool:
        """Check if the service is configured and ready."""
        if not PYWHATKIT_AVAILABLE:
            return False
        
        # For pywhatkit, we just need the user to acknowledge the risks
        return self._is_configured
    
    def configure_service(self, acknowledge_risks: bool = False) -> Tuple[bool, str]:
        """
        Configure the PyWhatKit service.
        
        Args:
            acknowledge_risks: User must acknowledge the risks
            
        Returns:
            Tuple of (success, message)
        """
        if not PYWHATKIT_AVAILABLE:
            return False, "pywhatkit package is not installed. Install with: pip install pywhatkit"
        
        if not acknowledge_risks:
            return False, "You must acknowledge the risks of using browser automation"
        
        try:
            # Save configuration
            config = {
                "configured": True,
                "acknowledged_risks": True,
                "configured_at": datetime.now().isoformat(),
                "rate_limit_per_minute": self.rate_limit_per_minute,
                "daily_message_limit": self.daily_message_limit,
                "min_delay_seconds": self.min_delay_seconds
            }
            
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            self._is_configured = True
            logger.info("PyWhatKit service configured successfully")
            return True, "PyWhatKit service configured successfully"
            
        except Exception as e:
            error_msg = f"Failed to configure PyWhatKit service: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def _load_configuration(self):
        """Load service configuration."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                self._is_configured = config.get("configured", False)
                self.rate_limit_per_minute = config.get("rate_limit_per_minute", 5)
                self.daily_message_limit = config.get("daily_message_limit", 50)
                self.min_delay_seconds = config.get("min_delay_seconds", 30)
                
                logger.info("PyWhatKit configuration loaded")
            else:
                logger.info("No PyWhatKit configuration found")
                
        except Exception as e:
            logger.error(f"Failed to load PyWhatKit configuration: {e}")
            self._is_configured = False
    
    def _load_daily_usage(self) -> Dict[str, int]:
        """Load daily usage tracking."""
        try:
            if self.usage_file.exists():
                with open(self.usage_file, 'r') as f:
                    usage_data = json.load(f)
                
                today = datetime.now().strftime("%Y-%m-%d")
                return usage_data.get(today, {"messages_sent": 0})
            
        except Exception as e:
            logger.error(f"Failed to load usage data: {e}")
        
        return {"messages_sent": 0}
    
    def _save_daily_usage(self):
        """Save daily usage tracking."""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Load existing data
            usage_data = {}
            if self.usage_file.exists():
                with open(self.usage_file, 'r') as f:
                    usage_data = json.load(f)
            
            # Update today's usage
            usage_data[today] = self.daily_usage
            
            # Clean old data (keep only last 30 days)
            cutoff_date = datetime.now() - timedelta(days=30)
            usage_data = {
                date: data for date, data in usage_data.items()
                if datetime.strptime(date, "%Y-%m-%d") >= cutoff_date
            }
            
            # Save
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.usage_file, 'w') as f:
                json.dump(usage_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save usage data: {e}")
    
    def get_daily_usage(self) -> Dict[str, Any]:
        """Get current daily usage statistics."""
        return {
            "messages_sent_today": self.daily_usage.get("messages_sent", 0),
            "daily_limit": self.daily_message_limit,
            "remaining_today": max(0, self.daily_message_limit - self.daily_usage.get("messages_sent", 0)),
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "min_delay_seconds": self.min_delay_seconds
        }
    
    def can_send_message(self) -> Tuple[bool, str]:
        """Check if we can send a message now."""
        if not self.is_configured():
            return False, "PyWhatKit service is not configured"
        
        # Check daily limit
        messages_today = self.daily_usage.get("messages_sent", 0)
        if messages_today >= self.daily_message_limit:
            return False, f"Daily limit reached ({messages_today}/{self.daily_message_limit})"
        
        # Check rate limiting
        now = datetime.now()
        recent_messages = [
            ts for ts in self.message_timestamps
            if (now - ts).total_seconds() < 60
        ]
        
        if len(recent_messages) >= self.rate_limit_per_minute:
            return False, f"Rate limit exceeded ({len(recent_messages)}/{self.rate_limit_per_minute} per minute)"
        
        # Check minimum delay
        if self.message_timestamps:
            last_message = max(self.message_timestamps)
            time_since_last = (now - last_message).total_seconds()
            if time_since_last < self.min_delay_seconds:
                wait_time = self.min_delay_seconds - time_since_last
                return False, f"Must wait {wait_time:.0f} more seconds (minimum {self.min_delay_seconds}s delay)"
        
        return True, "Ready to send"
    
    def send_message(self, customer: Customer, template: MessageTemplate) -> bool:
        """
        Send WhatsApp message using pywhatkit.
        
        Args:
            customer: Customer to send to
            template: Message template
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if we can send
            can_send, reason = self.can_send_message()
            if not can_send:
                logger.warning(f"Cannot send message to {customer.name}: {reason}")
                self._last_error = reason
                return False
            
            # Validate phone number
            if not customer.phone:
                logger.error(f"No phone number for customer {customer.name}")
                self._last_error = "No phone number provided"
                return False
            
            # Format phone number (pywhatkit expects +country_code format)
            phone = self._format_phone_number(customer.phone)
            if not phone:
                logger.error(f"Invalid phone number format: {customer.phone}")
                self._last_error = "Invalid phone number format"
                return False
            
            # Render message content
            message_content = self._render_message(customer, template)
            if not message_content:
                logger.error("Empty message content")
                self._last_error = "Empty message content"
                return False
            
            # Calculate send time (immediate + small delay for safety)
            now = datetime.now()
            send_time = now + timedelta(seconds=5)  # 5 second delay for safety
            
            logger.info(f"Scheduling WhatsApp message to {customer.name} ({phone}) at {send_time}")
            
            # Send message using pywhatkit
            pwk.sendwhatmsg(
                phone_no=phone,
                message=message_content,
                time_hour=send_time.hour,
                time_min=send_time.minute,
                wait_time=10,  # Wait 10 seconds for WhatsApp Web to load
                tab_close=True,  # Close tab after sending
                close_time=5     # Close after 5 seconds
            )
            
            # Track the message
            self._track_message_sent()
            
            logger.info(f"✅ WhatsApp message sent to {customer.name} ({phone})")
            return True
            
        except Exception as e:
            error_msg = f"Failed to send WhatsApp message to {customer.name}: {e}"
            logger.error(error_msg)
            self._last_error = str(e)
            return False
    
    def _format_phone_number(self, phone: str) -> Optional[str]:
        """
        Format phone number for pywhatkit.
        
        Args:
            phone: Raw phone number
            
        Returns:
            Formatted phone number or None if invalid
        """
        if not phone:
            return None
        
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, phone))
        
        if not digits_only:
            return None
        
        # If it doesn't start with country code, assume it's a local number
        # This is a simple implementation - you may need to adjust based on your region
        if len(digits_only) == 10:  # US/local format
            return f"+1{digits_only}"  # Assume US
        elif len(digits_only) == 11 and digits_only.startswith('1'):  # US with country code
            return f"+{digits_only}"
        elif len(digits_only) >= 10:  # International format
            return f"+{digits_only}"
        else:
            return None
    
    def _render_message(self, customer: Customer, template: MessageTemplate) -> str:
        """
        Render message content with customer data.
        
        Args:
            customer: Customer data
            template: Message template
            
        Returns:
            Rendered message content
        """
        # Use WhatsApp content if available, otherwise use email content
        content = template.whatsapp_content or template.content
        
        if not content:
            return ""
        
        # Simple variable substitution
        variables = {
            'name': customer.name or 'Customer',
            'company': customer.company or 'Your Company',
            'phone': customer.phone or '',
            'email': customer.email or ''
        }
        
        rendered_content = content
        for var, value in variables.items():
            rendered_content = rendered_content.replace(f'{{{var}}}', value)
        
        return rendered_content
    
    def _track_message_sent(self):
        """Track that a message was sent."""
        now = datetime.now()
        
        # Add to timestamps
        self.message_timestamps.append(now)
        
        # Clean old timestamps (keep only last hour)
        cutoff = now - timedelta(hours=1)
        self.message_timestamps = [
            ts for ts in self.message_timestamps if ts >= cutoff
        ]
        
        # Update daily usage
        self.daily_usage["messages_sent"] = self.daily_usage.get("messages_sent", 0) + 1
        self._save_daily_usage()
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test the PyWhatKit service.
        
        Returns:
            Tuple of (success, message)
        """
        if not PYWHATKIT_AVAILABLE:
            return False, "pywhatkit package is not installed"
        
        if not self.is_configured():
            return False, "PyWhatKit service is not configured"
        
        try:
            # Check if we can send (without actually sending)
            can_send, reason = self.can_send_message()
            if not can_send:
                return False, f"Service not ready: {reason}"
            
            # Basic functionality test
            test_phone = "+1234567890"
            test_message = "Test message"
            
            # Just validate the formatting without sending
            formatted_phone = self._format_phone_number(test_phone)
            if not formatted_phone:
                return False, "Phone number formatting failed"
            
            usage = self.get_daily_usage()
            return True, f"PyWhatKit service is ready. Usage: {usage['messages_sent_today']}/{usage['daily_limit']} messages today"
            
        except Exception as e:
            return False, f"Service test failed: {e}"
    
    def get_last_error(self) -> Optional[str]:
        """Get the last error message."""
        return self._last_error
    
    def reset_daily_usage(self):
        """Reset daily usage (for testing or manual reset)."""
        self.daily_usage = {"messages_sent": 0}
        self._save_daily_usage()
        logger.info("Daily usage reset")
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service information and status."""
        return {
            "service_name": "PyWhatKit WhatsApp Service",
            "is_available": self.is_available(),
            "is_configured": self.is_configured(),
            "daily_usage": self.get_daily_usage(),
            "rate_limits": {
                "per_minute": self.rate_limit_per_minute,
                "min_delay_seconds": self.min_delay_seconds
            },
            "warnings": [
                "⚠️ Uses browser automation which may violate WhatsApp ToS",
                "⚠️ Risk of account suspension",
                "⚠️ Requires WhatsApp Web to be open",
                "⚠️ Less reliable than WhatsApp Business API"
            ],
            "last_error": self._last_error
        }
