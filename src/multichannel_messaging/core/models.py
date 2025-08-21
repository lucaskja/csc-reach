"""
Core data models for Multi-Channel Bulk Messaging System.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from ..utils.exceptions import ValidationError


class MessageChannel(Enum):
    """Message channel types."""
    EMAIL = "email"
    WHATSAPP = "whatsapp"


class MessageStatus(Enum):
    """Message sending status."""
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Customer:
    """Customer data model with multi-channel support."""
    name: str
    company: str
    phone: str
    email: str
    whatsapp_opt_in: bool = True  # Consent for WhatsApp messaging
    preferred_channel: str = "both"  # email, whatsapp, both
    
    def __post_init__(self):
        """Validate and format customer data after initialization."""
        # Clean and format data
        self.name = self.name.strip() if self.name else ""
        self.company = self.company.strip() if self.company else ""
        self.phone = self._format_phone_number(self.phone) if self.phone else ""
        self.email = self.email.strip().lower() if self.email else ""
        
        # Validate data
        self.validate()
    
    def _format_phone_number(self, phone: str) -> str:
        """
        Format phone number for WhatsApp compatibility.
        
        Args:
            phone: Raw phone number
            
        Returns:
            Formatted phone number
        """
        if not phone:
            return ""
        
        # Remove common formatting characters
        cleaned = re.sub(r'[^\d+]', '', phone.strip())
        
        # Ensure it starts with + for international format
        if cleaned and not cleaned.startswith('+'):
            # If it looks like a US number (10 digits), add +1
            if len(cleaned) == 10 and cleaned.isdigit():
                cleaned = '+1' + cleaned
            # If it looks like it's missing the +, add it
            elif len(cleaned) > 10 and cleaned.isdigit():
                cleaned = '+' + cleaned
        
        return cleaned
    
    def validate(self) -> None:
        """
        Validate customer data.
        
        Raises:
            ValidationError: If validation fails
        """
        errors = []
        
        # Validate name
        if not self.name or not self.name.strip():
            errors.append("Name is required")
        elif len(self.name.strip()) < 2:
            errors.append("Name must be at least 2 characters long")
        
        # Validate company
        if not self.company or not self.company.strip():
            errors.append("Company is required")
        
        # Validate email
        if not self.email or not self.email.strip():
            errors.append("Email is required")
        elif not self._is_valid_email(self.email):
            errors.append("Invalid email format")
        
        # Validate phone (basic validation)
        if not self.phone or not self.phone.strip():
            errors.append("Phone is required")
        elif not self._is_valid_phone(self.phone):
            errors.append("Invalid phone format")
        
        if errors:
            raise ValidationError(f"Customer validation failed: {'; '.join(errors)}")
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip()))
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone format (basic validation)."""
        # Remove common phone number characters
        cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
        # Check if it contains only digits and is reasonable length
        return cleaned.isdigit() and 8 <= len(cleaned) <= 15
    
    def to_dict(self) -> Dict[str, str]:
        """Convert customer to dictionary."""
        return {
            "name": self.name,
            "company": self.company,
            "phone": self.phone,
            "email": self.email
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "Customer":
        """Create customer from dictionary."""
        return cls(
            name=data.get("name", ""),
            company=data.get("company", ""),
            phone=data.get("phone", ""),
            email=data.get("email", "")
        )


@dataclass
class MessageTemplate:
    """Multi-channel message template model."""
    id: str
    name: str
    channels: List[str] = field(default_factory=lambda: ["email"])  # Supported channels
    subject: str = ""  # For email only
    content: str = ""  # Email content
    whatsapp_content: str = ""  # WhatsApp-specific content
    language: str = "en"
    variables: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate template after initialization."""
        # Ensure channels is a list
        if isinstance(self.channels, str):
            self.channels = [self.channels]
        
        # If no WhatsApp content specified, use regular content
        if not self.whatsapp_content and "whatsapp" in self.channels:
            self.whatsapp_content = self.content
        
        self.validate()
    
    def validate(self) -> None:
        """
        Validate template data.
        
        Raises:
            ValidationError: If validation fails
        """
        errors = []
        
        if not self.id or not self.id.strip():
            errors.append("Template ID is required")
        
        if not self.name or not self.name.strip():
            errors.append("Template name is required")
        
        if not self.channels:
            errors.append("At least one channel must be specified")
        
        # Validate channel-specific requirements
        if "email" in self.channels:
            if not self.subject.strip():
                errors.append("Email template must have a subject")
            if not self.content.strip():
                errors.append("Email template must have content")
        
        if "whatsapp" in self.channels:
            if not self.whatsapp_content.strip():
                errors.append("WhatsApp template must have content")
        
        if errors:
            raise ValidationError(f"Template validation failed: {'; '.join(errors)}")
    
    def render(self, customer: Customer) -> Dict[str, str]:
        """
        Render template with customer data for all channels.
        
        Args:
            customer: Customer data to use for rendering
            
        Returns:
            Dictionary with rendered content for each channel
        """
        customer_data = customer.to_dict()
        result = {}
        
        # Render email content
        if "email" in self.channels:
            rendered_subject = self.subject
            rendered_content = self.content
            
            for var in self.variables:
                placeholder = f"{{{var}}}"
                value = str(customer_data.get(var, placeholder))
                rendered_subject = rendered_subject.replace(placeholder, value)
                rendered_content = rendered_content.replace(placeholder, value)
            
            result["subject"] = rendered_subject
            result["content"] = rendered_content
        
        # Render WhatsApp content
        if "whatsapp" in self.channels:
            rendered_whatsapp = self.whatsapp_content
            
            for var in self.variables:
                placeholder = f"{{{var}}}"
                value = str(customer_data.get(var, placeholder))
                rendered_whatsapp = rendered_whatsapp.replace(placeholder, value)
            
            result["whatsapp_content"] = rendered_whatsapp
        
        return result
    
    def supports_channel(self, channel: str) -> bool:
        """
        Check if template supports a specific channel.
        
        Args:
            channel: Channel to check (email, whatsapp)
            
        Returns:
            True if channel is supported
        """
        return channel in self.channels
    
    def get_content_for_channel(self, channel: str) -> str:
        """
        Get content for a specific channel.
        
        Args:
            channel: Channel to get content for
            
        Returns:
            Content for the specified channel
        """
        if channel == "email":
            return self.content
        elif channel == "whatsapp":
            return self.whatsapp_content
        else:
            return ""
            if var in customer_data:
                rendered_content = rendered_content.replace(f"{{{var}}}", customer_data[var])
        
        result = {"content": rendered_content}
        
        # Render subject for email templates
        if self.channel == MessageChannel.EMAIL:
            rendered_subject = self.subject
            for var in self.variables:
                if var in customer_data:
                    rendered_subject = rendered_subject.replace(f"{{{var}}}", customer_data[var])
            result["subject"] = rendered_subject
        
        return result
    
    def extract_variables(self) -> List[str]:
        """
        Extract variable names from template content and subject.
        
        Returns:
            List of variable names found in the template
        """
        variables = set()
        
        # Extract from content
        content_vars = re.findall(r'\{(\w+)\}', self.content)
        variables.update(content_vars)
        
        # Extract from subject (for email templates)
        if self.channel == MessageChannel.EMAIL and self.subject:
            subject_vars = re.findall(r'\{(\w+)\}', self.subject)
            variables.update(subject_vars)
        
        return sorted(list(variables))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "channel": self.channel.value,
            "subject": self.subject,
            "content": self.content,
            "language": self.language,
            "variables": self.variables,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MessageTemplate":
        """Create template from dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            channel=MessageChannel(data.get("channel", "email")),
            subject=data.get("subject", ""),
            content=data.get("content", ""),
            language=data.get("language", "en"),
            variables=data.get("variables", []),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        )


@dataclass
class MessageRecord:
    """Individual message record with multi-channel support."""
    customer: Customer
    template: MessageTemplate
    channel: str = "email"  # Channel used for this message
    status: MessageStatus = MessageStatus.PENDING
    rendered_content: Dict[str, str] = field(default_factory=dict)
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    message_id: Optional[str] = None  # External message ID (WhatsApp, email, etc.)
    delivery_status: Optional[str] = None  # Channel-specific delivery status
    
    def __post_init__(self):
        """Initialize message record."""
        if isinstance(self.status, str):
            self.status = MessageStatus(self.status)
        
        # Render content if not already rendered
        if not self.rendered_content:
            self.rendered_content = self.template.render(self.customer)
    
    def mark_as_sent(self, message_id: Optional[str] = None) -> None:
        """Mark message as sent."""
        self.status = MessageStatus.SENT
        self.sent_at = datetime.now()
        self.error_message = None
        if message_id:
            self.message_id = message_id
    
    def mark_as_failed(self, error_message: str) -> None:
        """Mark message as failed."""
        self.status = MessageStatus.FAILED
        self.error_message = error_message
    
    def update_delivery_status(self, delivery_status: str) -> None:
        """Update delivery status (for WhatsApp, etc.)."""
        self.delivery_status = delivery_status
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message record to dictionary."""
        return {
            "customer": self.customer.to_dict(),
            "template_id": self.template.id,
            "channel": self.channel,
            "status": self.status.value,
            "rendered_content": self.rendered_content,
            "error_message": self.error_message,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "message_id": self.message_id,
            "delivery_status": self.delivery_status
        }


@dataclass
class SendingReport:
    """Sending operation report."""
    timestamp: datetime
    channel: MessageChannel
    template_id: str
    total_recipients: int
    successful_sends: int = 0
    failed_sends: int = 0
    cancelled_sends: int = 0
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    
    def __post_init__(self):
        """Initialize sending report."""
        if isinstance(self.channel, str):
            self.channel = MessageChannel(self.channel)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_recipients == 0:
            return 0.0
        return (self.successful_sends / self.total_recipients) * 100
    
    def add_error(self, error: str) -> None:
        """Add an error to the report."""
        self.errors.append(error)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "channel": self.channel.value,
            "template_id": self.template_id,
            "total_recipients": self.total_recipients,
            "successful_sends": self.successful_sends,
            "failed_sends": self.failed_sends,
            "cancelled_sends": self.cancelled_sends,
            "success_rate": self.success_rate,
            "errors": self.errors,
            "duration_seconds": self.duration_seconds
        }
