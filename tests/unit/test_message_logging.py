#!/usr/bin/env python3
"""
Unit tests for the message logging system core functionality.
"""

import sys
import time
import pytest
from pathlib import Path

from multichannel_messaging.core.message_logger import MessageLogger
from multichannel_messaging.core.models import Customer, MessageTemplate, MessageRecord, MessageStatus
from multichannel_messaging.services.logged_email_service import LoggedEmailService


def test_basic_logging():
    """Test basic logging functionality."""
    # Initialize message logger with temporary database
    db_path = Path("test_logs_unit.db")
    if db_path.exists():
        db_path.unlink()
    
    message_logger = MessageLogger(user_id="test_user", db_path=str(db_path))
    
    # Create sample data
    customer = Customer(
        name="Test User",
        company="Test Company",
        email="test@example.com",
        phone="+1234567890"
    )
    
    template = MessageTemplate(
        id="test_template",
        name="Test Template",
        channels=["email"],
        subject="Test Subject",
        content="Hello {name} from {company}!",
        variables=["name", "company"]
    )
    
    # Start a session
    session_id = message_logger.start_session("email", template)
    assert session_id is not None
    assert "test_user_email" in session_id
    
    # Log a message
    message_record = MessageRecord(
        customer=customer,
        template=template,
        channel="email",
        status=MessageStatus.PENDING
    )
    
    log_id = message_logger.log_message(message_record, "Test message content")
    assert log_id is not None
    assert session_id in log_id
    
    # Update status to sent
    message_logger.update_message_status(log_id, MessageStatus.SENT, message_id="test_msg_123")
    
    # End session
    session_summary = message_logger.end_session()
    assert session_summary is not None
    assert session_summary.total_messages == 1
    assert session_summary.successful_messages == 1
    assert session_summary.success_rate == 100.0
    
    # Get quick stats
    stats = message_logger.get_quick_stats()
    assert stats['messages_last_30_days'] == 1
    assert stats['success_rate_30_days'] == 100.0
    
    # Cleanup
    if db_path.exists():
        db_path.unlink()


def test_logged_email_service():
    """Test the LoggedEmailService integration."""
    # Initialize message logger with temporary database
    db_path = Path("test_logs_service.db")
    if db_path.exists():
        db_path.unlink()
    
    message_logger = MessageLogger(user_id="test_user_2", db_path=str(db_path))
    
    # Create mock email service for testing
    class MockEmailService:
        def send_email(self, customer, template):
            # Simulate 80% success rate
            import random
            return random.random() > 0.2
        
        def create_draft_email(self, customer, template):
            return True
        
        def is_outlook_running(self):
            return True
        
        def start_outlook(self):
            return True
        
        def test_connection(self):
            return True, "Mock connection successful"
        
        def get_outlook_version(self):
            return "Mock Outlook 2021"
        
        def get_platform_info(self):
            return "Mock Platform"
    
    # Create logged email service
    logged_service = LoggedEmailService(message_logger)
    logged_service.email_service = MockEmailService()  # Replace with mock
    
    # Create test customers
    customers = [
        Customer(name="John Doe", company="Acme Corp", email="john@acme.com", phone="+1111111111"),
        Customer(name="Jane Smith", company="Tech Co", email="jane@tech.com", phone="+2222222222"),
        Customer(name="Bob Johnson", company="Global Inc", email="bob@global.com", phone="+3333333333"),
    ]
    
    template = MessageTemplate(
        id="bulk_test",
        name="Bulk Test Template",
        channels=["email"],
        subject="Bulk Test: {name}",
        content="Hello {name} from {company}!",
        variables=["name", "company"]
    )
    
    # Send bulk emails
    results = logged_service.send_bulk_emails(
        customers=customers,
        template=template,
        batch_size=2,
        delay_between_emails=0.1
    )
    
    # Check results
    successful = len([r for r in results if r.status == MessageStatus.SENT])
    failed = len([r for r in results if r.status == MessageStatus.FAILED])
    
    assert len(results) == 3
    assert successful >= 1  # At least some should succeed with 80% success rate
    assert failed >= 0
    
    # Get sending statistics
    stats = logged_service.get_sending_statistics(days=1)
    assert stats['total_emails'] == 3
    assert stats['unique_recipients'] == 3
    assert 0 <= stats['success_rate'] <= 100
    
    # Cleanup
    if db_path.exists():
        db_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__])