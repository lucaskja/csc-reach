"""
Unit tests for WhatsApp Multi-Message Template System.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.multichannel_messaging.core.whatsapp_multi_message import (
    WhatsAppMultiMessageTemplate,
    MessageSplitStrategy,
    MessageSequenceRecord,
    WhatsAppMultiMessageService
)
from src.multichannel_messaging.core.models import Customer, MessageStatus


class TestWhatsAppMultiMessageTemplate:
    """Test WhatsApp multi-message template functionality."""
    
    def test_create_single_message_template(self):
        """Test creating a single message template."""
        template = WhatsAppMultiMessageTemplate(
            id="test_1",
            name="Test Template",
            content="Hello {name}! Welcome to {company}.",
            multi_message_mode=False
        )
        
        assert template.id == "test_1"
        assert template.name == "Test Template"
        assert not template.multi_message_mode
        assert len(template.variables) == 2
        assert "name" in template.variables
        assert "company" in template.variables
    
    def test_create_multi_message_template_paragraph_split(self):
        """Test creating a multi-message template with paragraph splitting."""
        content = "Hello {name}!\n\nWelcome to our service.\n\nWe're excited to have you!"
        
        template = WhatsAppMultiMessageTemplate(
            id="test_2",
            name="Multi Message Test",
            content=content,
            multi_message_mode=True,
            split_strategy=MessageSplitStrategy.PARAGRAPH
        )
        
        assert template.multi_message_mode
        assert len(template.message_sequence) == 3
        assert template.message_sequence[0] == "Hello {name}!"
        assert template.message_sequence[1] == "Welcome to our service."
        assert template.message_sequence[2] == "We're excited to have you!"
    
    def test_create_multi_message_template_sentence_split(self):
        """Test creating a multi-message template with sentence splitting."""
        content = "Hello {name}! Welcome to our service. We're excited to have you!"
        
        template = WhatsAppMultiMessageTemplate(
            id="test_3",
            name="Sentence Split Test",
            content=content,
            multi_message_mode=True,
            split_strategy=MessageSplitStrategy.SENTENCE
        )
        
        assert template.multi_message_mode
        assert len(template.message_sequence) == 3
        assert "Hello {name}!" in template.message_sequence[0]
        assert "Welcome to our service." in template.message_sequence[1]
        assert "We're excited to have you!" in template.message_sequence[2]
    
    def test_create_multi_message_template_custom_split(self):
        """Test creating a multi-message template with custom delimiter."""
        content = "Message 1|||Message 2|||Message 3"
        
        template = WhatsAppMultiMessageTemplate(
            id="test_4",
            name="Custom Split Test",
            content=content,
            multi_message_mode=True,
            split_strategy=MessageSplitStrategy.CUSTOM,
            custom_split_delimiter="|||"
        )
        
        assert template.multi_message_mode
        assert len(template.message_sequence) == 3
        assert template.message_sequence[0] == "Message 1"
        assert template.message_sequence[1] == "Message 2"
        assert template.message_sequence[2] == "Message 3"
    
    def test_preview_message_sequence(self):
        """Test previewing message sequence with customer data."""
        template = WhatsAppMultiMessageTemplate(
            id="test_5",
            name="Preview Test",
            content="Hello {name}!\n\nWelcome to {company}.",
            multi_message_mode=True,
            split_strategy=MessageSplitStrategy.PARAGRAPH
        )
        
        customer_data = {
            "name": "John Smith",
            "company": "Acme Corp"
        }
        
        rendered_messages = template.preview_message_sequence(customer_data)
        
        assert len(rendered_messages) == 2
        assert rendered_messages[0] == "Hello John Smith!"
        assert rendered_messages[1] == "Welcome to Acme Corp."
    
    def test_convert_to_single_message(self):
        """Test converting multi-message template to single message."""
        template = WhatsAppMultiMessageTemplate(
            id="test_6",
            name="Convert Test",
            content="Message 1\n\nMessage 2\n\nMessage 3",
            multi_message_mode=True,
            split_strategy=MessageSplitStrategy.PARAGRAPH
        )
        
        single_message = template.convert_to_single_message()
        
        assert single_message == "Message 1\n\nMessage 2\n\nMessage 3"
    
    def test_convert_to_multi_message(self):
        """Test converting single message template to multi-message."""
        template = WhatsAppMultiMessageTemplate(
            id="test_7",
            name="Convert Test",
            content="Message 1\n\nMessage 2\n\nMessage 3",
            multi_message_mode=False
        )
        
        messages = template.convert_to_multi_message()
        
        assert template.multi_message_mode
        assert len(messages) == 3
        assert messages[0] == "Message 1"
        assert messages[1] == "Message 2"
        assert messages[2] == "Message 3"
    
    def test_validate_message_sequence_valid(self):
        """Test validation of valid message sequence."""
        template = WhatsAppMultiMessageTemplate(
            id="test_8",
            name="Valid Test",
            content="Hello world!\n\nThis is a test.",
            multi_message_mode=True,
            split_strategy=MessageSplitStrategy.PARAGRAPH
        )
        
        errors = template.validate_message_sequence()
        assert len(errors) == 0
    
    def test_validate_message_sequence_empty_content(self):
        """Test validation with empty content."""
        template = WhatsAppMultiMessageTemplate(
            id="test_9",
            name="Empty Test",
            content="",
            multi_message_mode=True
        )
        
        errors = template.validate_message_sequence()
        assert len(errors) > 0
        assert any("empty" in error.lower() for error in errors)
    
    def test_validate_message_sequence_too_many_messages(self):
        """Test validation with too many messages."""
        # Create content that will split into many messages
        content = "\n\n".join([f"Message {i}" for i in range(15)])
        
        template = WhatsAppMultiMessageTemplate(
            id="test_10",
            name="Too Many Test",
            content=content,
            multi_message_mode=True,
            split_strategy=MessageSplitStrategy.PARAGRAPH,
            max_messages_per_sequence=10
        )
        
        errors = template.validate_message_sequence()
        # Should be truncated to max_messages, so no error
        assert len(template.message_sequence) == 10
    
    def test_get_estimated_send_time(self):
        """Test estimated send time calculation."""
        template = WhatsAppMultiMessageTemplate(
            id="test_11",
            name="Timing Test",
            content="Message 1\n\nMessage 2\n\nMessage 3",
            multi_message_mode=True,
            split_strategy=MessageSplitStrategy.PARAGRAPH,
            message_delay_seconds=2.0
        )
        
        estimated_time = template.get_estimated_send_time()
        
        # 3 messages: (3-1) * 2.0 + 3 * 0.5 = 4.0 + 1.5 = 5.5
        assert estimated_time == 5.5
    
    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        original = WhatsAppMultiMessageTemplate(
            id="test_12",
            name="Serialization Test",
            content="Hello {name}!\n\nWelcome!",
            language="en",
            multi_message_mode=True,
            split_strategy=MessageSplitStrategy.PARAGRAPH,
            message_delay_seconds=1.5,
            max_messages_per_sequence=5
        )
        
        # Convert to dict
        data = original.to_dict()
        
        # Convert back from dict
        restored = WhatsAppMultiMessageTemplate.from_dict(data)
        
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.content == original.content
        assert restored.language == original.language
        assert restored.multi_message_mode == original.multi_message_mode
        assert restored.split_strategy == original.split_strategy
        assert restored.message_delay_seconds == original.message_delay_seconds
        assert restored.max_messages_per_sequence == original.max_messages_per_sequence
        assert restored.message_sequence == original.message_sequence


class TestMessageSequenceRecord:
    """Test message sequence record functionality."""
    
    def test_create_sequence_record(self):
        """Test creating a message sequence record."""
        customer = Customer(
            name="John Smith",
            company="Acme Corp",
            phone="+1234567890",
            email="john@acme.com"
        )
        
        template = WhatsAppMultiMessageTemplate(
            id="test_seq_1",
            name="Sequence Test",
            content="Hello {name}!\n\nWelcome to {company}!",
            multi_message_mode=True,
            split_strategy=MessageSplitStrategy.PARAGRAPH
        )
        
        sequence_record = MessageSequenceRecord(
            sequence_id="seq_123",
            customer=customer,
            template=template
        )
        
        assert sequence_record.sequence_id == "seq_123"
        assert sequence_record.customer == customer
        assert sequence_record.template == template
        assert len(sequence_record.message_records) == 2
        assert sequence_record.status == MessageStatus.PENDING
    
    def test_sequence_progress_tracking(self):
        """Test sequence progress tracking."""
        customer = Customer(
            name="John Smith",
            company="Acme Corp",
            phone="+1234567890",
            email="john@acme.com"
        )
        
        template = WhatsAppMultiMessageTemplate(
            id="test_seq_2",
            name="Progress Test",
            content="Msg 1\n\nMsg 2\n\nMsg 3",
            multi_message_mode=True,
            split_strategy=MessageSplitStrategy.PARAGRAPH
        )
        
        sequence_record = MessageSequenceRecord(
            sequence_id="seq_456",
            customer=customer,
            template=template
        )
        
        # Initially no progress
        assert sequence_record.get_progress_percentage() == 0.0
        assert not sequence_record.is_complete()
        
        # Mark first message as sent
        sequence_record.mark_message_sent(0, "msg_1")
        assert sequence_record.get_progress_percentage() == 33.33333333333333
        assert sequence_record.messages_sent == 1
        assert not sequence_record.is_complete()
        
        # Mark second message as failed
        sequence_record.mark_message_failed(1, "Network error")
        assert sequence_record.get_progress_percentage() == 66.66666666666666
        assert sequence_record.messages_failed == 1
        assert not sequence_record.is_complete()
        
        # Mark third message as sent
        sequence_record.mark_message_sent(2, "msg_3")
        assert sequence_record.get_progress_percentage() == 100.0
        assert sequence_record.is_complete()
        assert sequence_record.get_success_count() == 2
        assert sequence_record.get_failure_count() == 1


class TestWhatsAppMultiMessageService:
    """Test WhatsApp multi-message service functionality."""
    
    def test_create_service(self):
        """Test creating the multi-message service."""
        mock_whatsapp_service = Mock()
        
        service = WhatsAppMultiMessageService(mock_whatsapp_service)
        
        assert service.whatsapp_service == mock_whatsapp_service
        assert len(service.active_sequences) == 0
    
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_send_multi_message_sequence(self, mock_sleep):
        """Test sending a multi-message sequence."""
        mock_whatsapp_service = Mock()
        service = WhatsAppMultiMessageService(mock_whatsapp_service)
        
        # Mock the _send_individual_message method to return success
        service._send_individual_message = Mock(return_value=True)
        
        customer = Customer(
            name="John Smith",
            company="Acme Corp",
            phone="+1234567890",
            email="john@acme.com"
        )
        
        template = WhatsAppMultiMessageTemplate(
            id="test_service_1",
            name="Service Test",
            content="Hello {name}!\n\nWelcome to {company}!",
            multi_message_mode=True,
            split_strategy=MessageSplitStrategy.PARAGRAPH,
            message_delay_seconds=0.1  # Short delay for testing
        )
        
        # Track progress
        progress_updates = []
        def progress_callback(sequence_record):
            progress_updates.append(sequence_record.get_progress_percentage())
        
        # Send sequence
        sequence_record = service.send_multi_message_sequence(
            customer=customer,
            template=template,
            progress_callback=progress_callback
        )
        
        # Verify results
        assert sequence_record.is_complete()
        assert sequence_record.get_success_count() == 2
        assert sequence_record.get_failure_count() == 0
        assert len(progress_updates) > 0
        
        # Verify individual message sending was called
        assert service._send_individual_message.call_count == 2
        
        # Verify sleep was called for delay between messages
        mock_sleep.assert_called_with(0.1)
    
    def test_get_sequence_status(self):
        """Test getting sequence status."""
        mock_whatsapp_service = Mock()
        service = WhatsAppMultiMessageService(mock_whatsapp_service)
        
        # No sequence initially
        assert service.get_sequence_status("nonexistent") is None
        
        # Add a mock sequence
        customer = Customer(
            name="Test User",
            company="Test Corp",
            phone="+1234567890",
            email="test@test.com"
        )
        
        template = WhatsAppMultiMessageTemplate(
            id="test_status",
            name="Status Test",
            content="Test message",
            multi_message_mode=False
        )
        
        sequence_record = MessageSequenceRecord(
            sequence_id="test_seq",
            customer=customer,
            template=template
        )
        
        service.active_sequences["test_seq"] = sequence_record
        
        # Should return the sequence
        retrieved = service.get_sequence_status("test_seq")
        assert retrieved == sequence_record
    
    def test_cancel_sequence(self):
        """Test cancelling a sequence."""
        mock_whatsapp_service = Mock()
        service = WhatsAppMultiMessageService(mock_whatsapp_service)
        
        customer = Customer(
            name="Test User",
            company="Test Corp",
            phone="+1234567890",
            email="test@test.com"
        )
        
        template = WhatsAppMultiMessageTemplate(
            id="test_cancel",
            name="Cancel Test",
            content="Msg 1\n\nMsg 2",
            multi_message_mode=True,
            split_strategy=MessageSplitStrategy.PARAGRAPH
        )
        
        sequence_record = MessageSequenceRecord(
            sequence_id="cancel_seq",
            customer=customer,
            template=template
        )
        
        service.active_sequences["cancel_seq"] = sequence_record
        
        # Cancel the sequence
        result = service.cancel_sequence("cancel_seq")
        
        assert result is True
        assert sequence_record.status == MessageStatus.CANCELLED
        
        # Check that pending messages were cancelled
        cancelled_count = sum(
            1 for record in sequence_record.message_records 
            if record.status == MessageStatus.CANCELLED
        )
        assert cancelled_count == 2  # Both messages should be cancelled


if __name__ == "__main__":
    pytest.main([__file__])