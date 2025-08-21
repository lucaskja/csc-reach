"""
Unit tests for enhanced Outlook integration features.
"""

import unittest
import tempfile
import os
from datetime import datetime
from pathlib import Path

from multichannel_messaging.core.email_composer import EmailComposer, EmailComposition, EmailFormat
from multichannel_messaging.core.email_analytics import EmailAnalyticsManager, EmailTrackingEvent, EmailEvent
from multichannel_messaging.core.models import Customer, MessageTemplate
from multichannel_messaging.services.email_service import EmailService


class TestEmailComposer(unittest.TestCase):
    """Test cases for EmailComposer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.composer = EmailComposer()
        self.customer = Customer(
            name="John Doe",
            company="Test Company",
            phone="+1234567890",
            email="john.doe@example.com"
        )
        self.template = MessageTemplate(
            id="test-template-1",
            name="Test Template",
            subject="Test Subject for {name}",
            content="Hello {name} from {company}!\n\nThis is a test email.",
            variables=["name", "company"]
        )
    
    def test_compose_plain_text_email(self):
        """Test composing a plain text email."""
        composition = self.composer.compose_email(
            customer=self.customer,
            template=self.template,
            format_type=EmailFormat.PLAIN_TEXT
        )
        
        self.assertEqual(composition.to_address, "john.doe@example.com")
        self.assertIn("John Doe", composition.subject)
        self.assertIn("Test Company", composition.content)
        self.assertTrue(composition.is_valid())
        self.assertEqual(composition.format_type, EmailFormat.PLAIN_TEXT)
    
    def test_compose_html_email(self):
        """Test composing an HTML email."""
        composition = self.composer.compose_email(
            customer=self.customer,
            template=self.template,
            format_type=EmailFormat.HTML
        )
        
        self.assertEqual(composition.format_type, EmailFormat.HTML)
        self.assertIsNotNone(composition.html_content)
        self.assertIn("<p>", composition.html_content)
        self.assertTrue(composition.is_valid())
    
    def test_email_preview(self):
        """Test email preview generation."""
        composition = self.composer.compose_email(
            customer=self.customer,
            template=self.template,
            format_type=EmailFormat.HTML
        )
        
        from multichannel_messaging.core.email_composer import DeviceType
        preview = self.composer.create_preview(composition, DeviceType.MOBILE)
        
        self.assertEqual(preview['device_type'], 'mobile')
        self.assertEqual(preview['to_address'], 'john.doe@example.com')
        self.assertTrue(preview['is_valid'])


class TestEmailAnalytics(unittest.TestCase):
    """Test cases for EmailAnalytics."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        self.analytics = EmailAnalyticsManager(db_path=self.temp_db.name)
        self.customer = Customer(
            name="Test User",
            company="Test Company",
            phone="+1234567890",
            email="test@example.com"
        )
        self.template = MessageTemplate(
            id="test-template-2",
            name="Analytics Test Template",
            subject="Test",
            content="Test content"
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_campaign_creation(self):
        """Test creating an email campaign."""
        campaign_id = self.analytics.start_campaign("Test Campaign")
        self.assertIsNotNone(campaign_id)
        self.assertTrue(len(campaign_id) > 0)
    
    def test_email_tracking(self):
        """Test email event tracking."""
        from multichannel_messaging.core.models import MessageRecord
        
        # Start campaign
        campaign_id = self.analytics.start_campaign("Test Campaign")
        
        # Track email sent
        message_record = MessageRecord(customer=self.customer, template=self.template)
        message_id = self.analytics.track_email_sent(message_record, campaign_id)
        self.assertIsNotNone(message_id)
        
        # Track delivery
        success = self.analytics.track_email_delivered(message_id)
        self.assertTrue(success)
        
        # Track open
        success = self.analytics.track_email_opened(message_id)
        self.assertTrue(success)
        
        # Get message timeline
        events = self.analytics.get_message_timeline(message_id)
        self.assertGreaterEqual(len(events), 2)  # At least sent and delivered
    
    def test_campaign_performance(self):
        """Test campaign performance analysis."""
        from multichannel_messaging.core.models import MessageRecord
        
        # Create campaign and send some emails
        campaign_id = self.analytics.start_campaign("Performance Test Campaign")
        
        message_record = MessageRecord(customer=self.customer, template=self.template)
        message_id = self.analytics.track_email_sent(message_record, campaign_id)
        self.analytics.track_email_delivered(message_id)
        
        # Get campaign stats
        stats = self.analytics.get_campaign_performance(campaign_id)
        self.assertIsNotNone(stats)
        self.assertEqual(stats.total_sent, 1)
        self.assertEqual(stats.total_delivered, 1)


class TestEmailService(unittest.TestCase):
    """Test cases for EmailService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = EmailService()
    
    def test_platform_detection(self):
        """Test platform detection."""
        platform_info = self.service.get_platform_info()
        self.assertIsNotNone(platform_info)
        self.assertTrue(len(platform_info) > 0)
    
    def test_email_composer_integration(self):
        """Test email composer integration."""
        customer = Customer(
            name="Integration Test",
            company="Test Company",
            phone="+1234567890",
            email="integration@example.com"
        )
        template = MessageTemplate(
            id="integration-template",
            name="Integration Template",
            subject="Integration Test",
            content="This is an integration test."
        )
        
        # Test email preview creation
        composition = self.service.create_email_preview(
            customer=customer,
            template=template,
            use_html=True
        )
        
        self.assertIsNotNone(composition)
        self.assertEqual(composition.to_address, "integration@example.com")
        self.assertTrue(composition.is_valid())
    
    def test_analytics_integration(self):
        """Test analytics integration."""
        analytics_manager = self.service.get_analytics_manager()
        self.assertIsNotNone(analytics_manager)
        
        # Test campaign creation
        campaign_id = self.service.start_email_campaign("Integration Test Campaign")
        self.assertIsNotNone(campaign_id)


if __name__ == '__main__':
    unittest.main()