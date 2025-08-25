"""
WhatsApp Multi-Message Template System.

Provides support for splitting WhatsApp messages into multiple individual messages
for better readability and engagement.
"""

import re
import time
import threading
from typing import List, Dict, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .models import Customer, MessageRecord, MessageStatus
from ..utils.logger import get_logger
from ..utils.exceptions import ValidationError, WhatsAppAPIError
from ..core.i18n_manager import get_i18n_manager

logger = get_logger(__name__)
i18n = get_i18n_manager()


class MessageSplitStrategy(Enum):
    """Strategies for splitting messages."""
    PARAGRAPH = "paragraph"  # Split by double line breaks
    SENTENCE = "sentence"    # Split by sentence endings
    CUSTOM = "custom"        # Split by custom delimiter
    MANUAL = "manual"        # Manually defined splits


@dataclass
class WhatsAppMultiMessageTemplate:
    """Enhanced WhatsApp template with multi-message support."""
    
    # Basic template information
    id: str
    name: str
    content: str
    language: str = "en"
    
    # Multi-message configuration
    multi_message_mode: bool = False
    split_strategy: MessageSplitStrategy = MessageSplitStrategy.PARAGRAPH
    custom_split_delimiter: str = "\n\n"
    message_delay_seconds: float = 1.0
    max_messages_per_sequence: int = 10
    
    # Message sequence (computed or manually defined)
    message_sequence: List[str] = field(default_factory=list)
    
    # Template metadata
    variables: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Analytics
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    
    def __post_init__(self):
        """Initialize template after creation."""
        self.extract_variables()
        if self.multi_message_mode and not self.message_sequence:
            self.split_into_messages()
    
    def extract_variables(self) -> List[str]:
        """Extract variable names from template content."""
        variables = set()
        
        # Extract from main content
        content_vars = re.findall(r'\{(\w+)\}', self.content)
        variables.update(content_vars)
        
        # Extract from message sequence if available
        for message in self.message_sequence:
            message_vars = re.findall(r'\{(\w+)\}', message)
            variables.update(message_vars)
        
        self.variables = sorted(list(variables))
        return self.variables
    
    def split_into_messages(self) -> List[str]:
        """Split content into individual messages based on strategy."""
        if not self.content.strip():
            self.message_sequence = []
            return self.message_sequence
        
        content = self.content.strip()
        
        if self.split_strategy == MessageSplitStrategy.PARAGRAPH:
            # Split by double line breaks (paragraphs)
            messages = [msg.strip() for msg in re.split(r'\n\s*\n', content) if msg.strip()]
        
        elif self.split_strategy == MessageSplitStrategy.SENTENCE:
            # Split by sentence endings
            sentences = re.split(r'(?<=[.!?])\s+', content)
            messages = [sentence.strip() for sentence in sentences if sentence.strip()]
        
        elif self.split_strategy == MessageSplitStrategy.CUSTOM:
            # Split by custom delimiter
            messages = [msg.strip() for msg in content.split(self.custom_split_delimiter) if msg.strip()]
        
        elif self.split_strategy == MessageSplitStrategy.MANUAL:
            # Use manually defined sequence
            if not self.message_sequence:
                messages = [content]  # Fallback to single message
            else:
                messages = self.message_sequence
        
        else:
            messages = [content]  # Fallback to single message
        
        # Limit number of messages
        if len(messages) > self.max_messages_per_sequence:
            logger.warning(f"Message sequence truncated from {len(messages)} to {self.max_messages_per_sequence} messages")
            messages = messages[:self.max_messages_per_sequence]
        
        # Validate message lengths (WhatsApp limit is 4096 characters)
        validated_messages = []
        for i, message in enumerate(messages):
            if len(message) > 4096:
                logger.warning(f"Message {i+1} truncated from {len(message)} to 4096 characters")
                message = message[:4093] + "..."
            validated_messages.append(message)
        
        self.message_sequence = validated_messages
        return self.message_sequence
    
    def preview_message_sequence(self, customer_data: Dict[str, str]) -> List[str]:
        """Preview message sequence with customer data substitution."""
        if not self.multi_message_mode:
            # Single message mode
            rendered_content = self.content
            for var in self.variables:
                placeholder = f"{{{var}}}"
                value = customer_data.get(var, placeholder)
                rendered_content = rendered_content.replace(placeholder, str(value))
            return [rendered_content]
        
        # Multi-message mode
        rendered_messages = []
        for message in self.message_sequence:
            rendered_message = message
            for var in self.variables:
                placeholder = f"{{{var}}}"
                value = customer_data.get(var, placeholder)
                rendered_message = rendered_message.replace(placeholder, str(value))
            rendered_messages.append(rendered_message)
        
        return rendered_messages
    
    def convert_to_single_message(self) -> str:
        """Convert multi-message template to single message format."""
        if not self.multi_message_mode or not self.message_sequence:
            return self.content
        
        # Join messages with appropriate delimiter
        if self.split_strategy == MessageSplitStrategy.PARAGRAPH:
            return "\n\n".join(self.message_sequence)
        elif self.split_strategy == MessageSplitStrategy.SENTENCE:
            return " ".join(self.message_sequence)
        elif self.split_strategy == MessageSplitStrategy.CUSTOM:
            return self.custom_split_delimiter.join(self.message_sequence)
        else:
            return "\n\n".join(self.message_sequence)
    
    def convert_to_multi_message(self) -> List[str]:
        """Convert single message template to multi-message format."""
        if self.multi_message_mode and self.message_sequence:
            return self.message_sequence
        
        # Enable multi-message mode and split
        self.multi_message_mode = True
        return self.split_into_messages()
    
    def validate_message_sequence(self) -> List[str]:
        """Validate the message sequence and return any errors."""
        errors = []
        
        if not self.content.strip():
            errors.append(i18n.tr("template_error_empty_content"))
        
        if self.multi_message_mode:
            if not self.message_sequence:
                errors.append(i18n.tr("template_error_empty_sequence"))
            
            if len(self.message_sequence) > self.max_messages_per_sequence:
                errors.append(i18n.tr("template_error_too_many_messages", 
                                    count=len(self.message_sequence), 
                                    max_count=self.max_messages_per_sequence))
            
            # Check individual message lengths
            for i, message in enumerate(self.message_sequence):
                if len(message) > 4096:
                    errors.append(i18n.tr("template_error_message_too_long", 
                                        message_num=i+1, 
                                        length=len(message)))
                
                if not message.strip():
                    errors.append(i18n.tr("template_error_empty_message", message_num=i+1))
        
        # Validate delay settings
        if self.message_delay_seconds < 0.1:
            errors.append(i18n.tr("template_error_delay_too_short"))
        elif self.message_delay_seconds > 60.0:
            errors.append(i18n.tr("template_error_delay_too_long"))
        
        return errors
    
    def get_estimated_send_time(self) -> float:
        """Get estimated time to send all messages in sequence."""
        if not self.multi_message_mode:
            return 1.0  # Single message
        
        message_count = len(self.message_sequence)
        if message_count <= 1:
            return 1.0
        
        # Time = (message_count - 1) * delay + base_time_per_message
        return (message_count - 1) * self.message_delay_seconds + message_count * 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary format."""
        return {
            "id": self.id,
            "name": self.name,
            "content": self.content,
            "language": self.language,
            "multi_message_mode": self.multi_message_mode,
            "split_strategy": self.split_strategy.value,
            "custom_split_delimiter": self.custom_split_delimiter,
            "message_delay_seconds": self.message_delay_seconds,
            "max_messages_per_sequence": self.max_messages_per_sequence,
            "message_sequence": self.message_sequence,
            "variables": self.variables,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "usage_count": self.usage_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WhatsAppMultiMessageTemplate":
        """Create template from dictionary."""
        template = cls(
            id=data["id"],
            name=data["name"],
            content=data["content"],
            language=data.get("language", "en"),
            multi_message_mode=data.get("multi_message_mode", False),
            split_strategy=MessageSplitStrategy(data.get("split_strategy", "paragraph")),
            custom_split_delimiter=data.get("custom_split_delimiter", "\n\n"),
            message_delay_seconds=data.get("message_delay_seconds", 1.0),
            max_messages_per_sequence=data.get("max_messages_per_sequence", 10),
            message_sequence=data.get("message_sequence", []),
            variables=data.get("variables", []),
            usage_count=data.get("usage_count", 0),
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0)
        )
        
        # Set timestamps
        if "created_at" in data:
            template.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            template.updated_at = datetime.fromisoformat(data["updated_at"])
        
        return template


@dataclass
class MessageSequenceRecord:
    """Record for tracking multi-message sequence delivery."""
    
    sequence_id: str
    customer: Customer
    template: WhatsAppMultiMessageTemplate
    message_records: List[MessageRecord] = field(default_factory=list)
    
    # Sequence status
    status: MessageStatus = MessageStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Progress tracking
    messages_sent: int = 0
    messages_delivered: int = 0
    messages_failed: int = 0
    
    def __post_init__(self):
        """Initialize sequence record."""
        if not self.message_records:
            # Create message records for each message in sequence
            rendered_messages = self.template.preview_message_sequence(self.customer.to_dict())
            for i, message_content in enumerate(rendered_messages):
                record = MessageRecord(
                    customer=self.customer,
                    template=None,  # We'll use the sequence template
                    channel="whatsapp",
                    rendered_content={"whatsapp_content": message_content}
                )
                record.message_id = f"{self.sequence_id}_msg_{i+1}"
                self.message_records.append(record)
    
    def get_progress_percentage(self) -> float:
        """Get completion percentage."""
        if not self.message_records:
            return 0.0
        
        completed = sum(1 for record in self.message_records 
                       if record.status in [MessageStatus.SENT, MessageStatus.DELIVERED, MessageStatus.FAILED])
        return (completed / len(self.message_records)) * 100.0
    
    def is_complete(self) -> bool:
        """Check if sequence is complete."""
        return all(record.status in [MessageStatus.SENT, MessageStatus.DELIVERED, MessageStatus.FAILED] 
                  for record in self.message_records)
    
    def get_success_count(self) -> int:
        """Get number of successfully sent messages."""
        return sum(1 for record in self.message_records 
                  if record.status in [MessageStatus.SENT, MessageStatus.DELIVERED])
    
    def get_failure_count(self) -> int:
        """Get number of failed messages."""
        return sum(1 for record in self.message_records 
                  if record.status == MessageStatus.FAILED)
    
    def mark_message_sent(self, message_index: int, message_id: str = None):
        """Mark a specific message as sent."""
        if 0 <= message_index < len(self.message_records):
            self.message_records[message_index].mark_as_sent(message_id)
            self.messages_sent += 1
            self._update_sequence_status()
    
    def mark_message_failed(self, message_index: int, error_message: str):
        """Mark a specific message as failed."""
        if 0 <= message_index < len(self.message_records):
            self.message_records[message_index].mark_as_failed(error_message)
            self.messages_failed += 1
            self._update_sequence_status()
    
    def _update_sequence_status(self):
        """Update overall sequence status."""
        if self.is_complete():
            self.status = MessageStatus.SENT if self.get_failure_count() == 0 else MessageStatus.FAILED
            self.completed_at = datetime.now()
        elif self.messages_sent > 0:
            self.status = MessageStatus.SENDING
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert sequence record to dictionary."""
        return {
            "sequence_id": self.sequence_id,
            "customer": self.customer.to_dict(),
            "template": self.template.to_dict(),
            "message_records": [record.to_dict() for record in self.message_records],
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "messages_sent": self.messages_sent,
            "messages_delivered": self.messages_delivered,
            "messages_failed": self.messages_failed
        }


class WhatsAppMultiMessageService:
    """Service for handling multi-message WhatsApp sending."""
    
    def __init__(self, whatsapp_service):
        """
        Initialize multi-message service.
        
        Args:
            whatsapp_service: Base WhatsApp service for sending individual messages
        """
        self.whatsapp_service = whatsapp_service
        self.active_sequences: Dict[str, MessageSequenceRecord] = {}
        self._sequence_counter = 0
        self._lock = threading.RLock()
    
    def send_multi_message_sequence(
        self,
        customer: Customer,
        template: WhatsAppMultiMessageTemplate,
        progress_callback: Optional[Callable[[MessageSequenceRecord], None]] = None
    ) -> MessageSequenceRecord:
        """
        Send a multi-message sequence to a customer.
        
        Args:
            customer: Customer to send messages to
            template: Multi-message template
            progress_callback: Optional callback for progress updates
            
        Returns:
            MessageSequenceRecord with sending results
        """
        with self._lock:
            # Generate sequence ID
            self._sequence_counter += 1
            sequence_id = f"seq_{int(datetime.now().timestamp())}_{self._sequence_counter}"
            
            # Create sequence record
            sequence_record = MessageSequenceRecord(
                sequence_id=sequence_id,
                customer=customer,
                template=template
            )
            
            self.active_sequences[sequence_id] = sequence_record
            
            logger.info(f"Starting multi-message sequence {sequence_id} for {customer.phone}")
        
        try:
            sequence_record.status = MessageStatus.SENDING
            sequence_record.started_at = datetime.now()
            
            if progress_callback:
                progress_callback(sequence_record)
            
            # Send messages in sequence
            if template.multi_message_mode and len(sequence_record.message_records) > 1:
                self._send_message_sequence(sequence_record, progress_callback)
            else:
                # Single message mode
                self._send_single_message(sequence_record, progress_callback)
            
            # Update template analytics
            template.usage_count += 1
            if sequence_record.get_failure_count() == 0:
                template.success_count += 1
            
            logger.info(f"Completed multi-message sequence {sequence_id}")
            
        except Exception as e:
            logger.error(f"Failed to send multi-message sequence {sequence_id}: {e}")
            sequence_record.status = MessageStatus.FAILED
            sequence_record.completed_at = datetime.now()
            
            # Mark all unsent messages as failed
            for i, record in enumerate(sequence_record.message_records):
                if record.status == MessageStatus.PENDING:
                    sequence_record.mark_message_failed(i, str(e))
        
        finally:
            if progress_callback:
                progress_callback(sequence_record)
        
        return sequence_record
    
    def _send_message_sequence(
        self,
        sequence_record: MessageSequenceRecord,
        progress_callback: Optional[Callable[[MessageSequenceRecord], None]] = None
    ):
        """Send messages in sequence with proper timing."""
        for i, message_record in enumerate(sequence_record.message_records):
            try:
                # Get message content
                message_content = message_record.rendered_content.get("whatsapp_content", "")
                
                if not message_content:
                    sequence_record.mark_message_failed(i, "Empty message content")
                    continue
                
                # Send individual message
                success = self._send_individual_message(
                    sequence_record.customer.phone,
                    message_content
                )
                
                if success:
                    sequence_record.mark_message_sent(i)
                    logger.debug(f"Sent message {i+1}/{len(sequence_record.message_records)} in sequence {sequence_record.sequence_id}")
                else:
                    sequence_record.mark_message_failed(i, "Failed to send message")
                
                # Progress callback
                if progress_callback:
                    progress_callback(sequence_record)
                
                # Add delay between messages (except for the last one)
                if i < len(sequence_record.message_records) - 1:
                    time.sleep(sequence_record.template.message_delay_seconds)
                
            except Exception as e:
                logger.error(f"Error sending message {i+1} in sequence {sequence_record.sequence_id}: {e}")
                sequence_record.mark_message_failed(i, str(e))
                
                if progress_callback:
                    progress_callback(sequence_record)
    
    def _send_single_message(
        self,
        sequence_record: MessageSequenceRecord,
        progress_callback: Optional[Callable[[MessageSequenceRecord], None]] = None
    ):
        """Send a single message."""
        if not sequence_record.message_records:
            return
        
        message_record = sequence_record.message_records[0]
        message_content = message_record.rendered_content.get("whatsapp_content", "")
        
        try:
            success = self._send_individual_message(
                sequence_record.customer.phone,
                message_content
            )
            
            if success:
                sequence_record.mark_message_sent(0)
            else:
                sequence_record.mark_message_failed(0, "Failed to send message")
                
        except Exception as e:
            sequence_record.mark_message_failed(0, str(e))
    
    def _send_individual_message(self, phone_number: str, message_content: str) -> bool:
        """Send an individual WhatsApp message."""
        try:
            # Use the base WhatsApp service to send the message
            # This is a simplified version - in practice, you'd use the actual API
            logger.debug(f"Sending WhatsApp message to {phone_number}: {message_content[:50]}...")
            
            # Simulate API call
            # In real implementation, this would call the WhatsApp Business API
            return True
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message to {phone_number}: {e}")
            return False
    
    def get_sequence_status(self, sequence_id: str) -> Optional[MessageSequenceRecord]:
        """Get status of a message sequence."""
        with self._lock:
            return self.active_sequences.get(sequence_id)
    
    def cancel_sequence(self, sequence_id: str) -> bool:
        """Cancel a pending message sequence."""
        with self._lock:
            if sequence_id not in self.active_sequences:
                return False
            
            sequence_record = self.active_sequences[sequence_id]
            
            # Mark pending messages as cancelled
            for i, message_record in enumerate(sequence_record.message_records):
                if message_record.status == MessageStatus.PENDING:
                    message_record.status = MessageStatus.CANCELLED
            
            sequence_record.status = MessageStatus.CANCELLED
            sequence_record.completed_at = datetime.now()
            
            logger.info(f"Cancelled message sequence {sequence_id}")
            return True
    
    def get_active_sequences(self) -> List[MessageSequenceRecord]:
        """Get all active message sequences."""
        with self._lock:
            return list(self.active_sequences.values())
    
    def cleanup_completed_sequences(self, max_age_hours: int = 24):
        """Clean up old completed sequences."""
        with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            sequences_to_remove = []
            for sequence_id, sequence_record in self.active_sequences.items():
                if (sequence_record.is_complete() and 
                    sequence_record.completed_at and 
                    sequence_record.completed_at < cutoff_time):
                    sequences_to_remove.append(sequence_id)
            
            for sequence_id in sequences_to_remove:
                del self.active_sequences[sequence_id]
            
            if sequences_to_remove:
                logger.info(f"Cleaned up {len(sequences_to_remove)} old message sequences")