"""
Unit tests for Local WhatsApp Business API service.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import tempfile
import os
from pathlib import Path
from datetime import datetime

from src.multichannel_messaging.services.whatsapp_local_service import LocalWhatsAppBusinessService
from src.multichannel_messaging.core.models import Customer, MessageTemplate, MessageStatus
from src.multichannel_messaging.utils.exceptions import WhatsAppConfigurationError


class TestLocalWhatsAppBusinessService(unittest.TestCase):
    """Test cases for Local WhatsApp Business service."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_credentials = {
            "access_token": "test_access_token",
            "phone_number_id": "test_phone_id",
            "business_account_id": "test_business_id",
            "created_at": datetime.now().isoformat()
        }
        
        self.test_customer = Customer(
            name="John Doe",
            company="Test Company",
            phone="+1234567890",
            email="john@test.com"
        )
        
        self.test_template = MessageTemplate(
            id="test_template",
            name="Test Template",
            channels=["whatsapp"],
            whatsapp_content="Hello {name} from {company}!",
            variables=["name", "company"]
        )
    
    @patch('src.multichannel_messaging.services.whatsapp_local_service.get_config_dir')
    def test_initialization_without_credentials(self, mock_get_config_dir):
        """Test service initialization without existing credentials."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_get_config_dir.return_value = Path(temp_dir)
            
            service = LocalWhatsAppBusinessService()
            
            self.assertIsNone(service.credentials)
            self.assertIsNone(service.api_client)
            self.assertFalse(service.is_configured())
    
    @patch('src.multichannel_messaging.services.whatsapp_local_service.get_config_dir')
    def test_credential_saving_and_loading(self, mock_get_config_dir):
        """Test saving and loading credentials."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_get_config_dir.return_value = Path(temp_dir)
            
            service = LocalWhatsAppBusinessService()
            
            # Save credentials
            success = service.save_credentials(
                access_token="test_token",
                phone_number_id="test_phone_id",
                business_account_id="test_business_id"
            )
            
            self.assertTrue(success)
            self.assertTrue(service.is_configured())
            self.assertEqual(service.credentials["access_token"], "test_token")
            self.assertEqual(service.credentials["phone_number_id"], "test_phone_id")
            
            # Test file was created
            credentials_file = Path(temp_dir) / "whatsapp_credentials.json"
            self.assertTrue(credentials_file.exists())
            
            # Test loading in new instance
            service2 = LocalWhatsAppBusinessService()
            self.assertTrue(service2.is_configured())
            self.assertEqual(service2.credentials["access_token"], "test_token")
    
    @patch('src.multichannel_messaging.services.whatsapp_local_service.get_config_dir')
    def test_credential_clearing(self, mock_get_config_dir):
        """Test clearing stored credentials."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_get_config_dir.return_value = Path(temp_dir)
            
            service = LocalWhatsAppBusinessService()
            
            # Save credentials first
            service.save_credentials("test_token", "test_phone_id")
            self.assertTrue(service.is_configured())
            
            # Clear credentials
            success = service.clear_credentials()
            self.assertTrue(success)
            self.assertFalse(service.is_configured())
            self.assertIsNone(service.credentials)
            self.assertIsNone(service.api_client)
    
    def test_phone_number_validation(self):
        """Test phone number validation."""
        service = LocalWhatsAppBusinessService()
        
        # Valid phone numbers
        self.assertTrue(service._validate_phone_number("+1234567890"))
        self.assertTrue(service._validate_phone_number("1234567890"))
        self.assertTrue(service._validate_phone_number("+44123456789"))
        self.assertTrue(service._validate_phone_number("+5511987654321"))
        
        # Invalid phone numbers
        self.assertFalse(service._validate_phone_number(""))
        self.assertFalse(service._validate_phone_number("123"))  # Too short
        self.assertFalse(service._validate_phone_number("12345678901234567"))  # Too long
        self.assertFalse(service._validate_phone_number("abc123"))  # Contains letters
        self.assertFalse(service._validate_phone_number("+1-234-567-890a"))  # Contains letter
    
    @patch('src.multichannel_messaging.services.whatsapp_local_service.get_config_dir')
    def test_usage_tracking(self, mock_get_config_dir):
        """Test usage tracking functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_get_config_dir.return_value = Path(temp_dir)
            
            service = LocalWhatsAppBusinessService(daily_message_limit=100)
            
            # Initial stats
            stats = service.get_usage_stats()
            self.assertEqual(stats['daily_messages_sent'], 0)
            self.assertEqual(stats['daily_limit'], 100)
            self.assertEqual(stats['remaining_daily'], 100)
            
            # Log some messages
            service._log_message_sent()
            service._log_message_sent()
            
            # Check updated stats
            stats = service.get_usage_stats()
            self.assertEqual(stats['daily_messages_sent'], 2)
            self.assertEqual(stats['remaining_daily'], 98)
            
            # Test usage file creation
            usage_file = Path(temp_dir) / "whatsapp_usage.json"
            self.assertTrue(usage_file.exists())
    
    @patch('src.multichannel_messaging.services.whatsapp_local_service.get_config_dir')
    def test_rate_limiting(self, mock_get_config_dir):
        """Test rate limiting functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_get_config_dir.return_value = Path(temp_dir)
            
            # Create service with low rate limit for testing
            service = LocalWhatsAppBusinessService(rate_limit_per_minute=2)
            
            # Initially should allow messages
            self.assertTrue(service._check_rate_limits())
            
            # Simulate sending messages to reach limit
            service._log_message_sent()
            service._log_message_sent()
            
            # Should now be at limit
            self.assertFalse(service._check_rate_limits())
    
    @patch('src.multichannel_messaging.services.whatsapp_local_service.get_config_dir')
    def test_daily_limit_enforcement(self, mock_get_config_dir):
        """Test daily message limit enforcement."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_get_config_dir.return_value = Path(temp_dir)
            
            # Create service with low daily limit
            service = LocalWhatsAppBusinessService(daily_message_limit=2)
            
            # Should allow messages initially
            self.assertTrue(service._check_rate_limits())
            
            # Send messages up to limit
            service._log_message_sent()
            self.assertTrue(service._check_rate_limits())
            
            service._log_message_sent()
            self.assertFalse(service._check_rate_limits())  # At limit
    
    def test_message_formatting(self):
        """Test WhatsApp message formatting."""
        service = LocalWhatsAppBusinessService()
        
        # Normal message
        formatted = service._format_whatsapp_message("Hello World!")
        self.assertEqual(formatted, "Hello World!")
        
        # Empty message
        formatted = service._format_whatsapp_message("")
        self.assertEqual(formatted, "")
        
        # Message with whitespace
        formatted = service._format_whatsapp_message("  Hello World!  ")
        self.assertEqual(formatted, "Hello World!")
        
        # Long message (should be truncated)
        long_message = "A" * 5000
        formatted = service._format_whatsapp_message(long_message)
        self.assertEqual(len(formatted), 4096)
        self.assertTrue(formatted.endswith("..."))
    
    @patch('src.multichannel_messaging.services.whatsapp_local_service.get_config_dir')
    @patch('requests.Session')
    def test_send_message_success(self, mock_session_class, mock_get_config_dir):
        """Test successful message sending."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_get_config_dir.return_value = Path(temp_dir)
            
            # Mock HTTP session
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'messages': [{'id': 'test_message_id'}]
            }
            mock_session.post.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            service = LocalWhatsAppBusinessService()
            service.save_credentials("test_token", "test_phone_id")
            
            # Test message sending
            success = service.send_message(self.test_customer, self.test_template)
            
            self.assertTrue(success)
            mock_session.post.assert_called_once()
            
            # Check usage was logged
            stats = service.get_usage_stats()
            self.assertEqual(stats['daily_messages_sent'], 1)
    
    @patch('src.multichannel_messaging.services.whatsapp_local_service.get_config_dir')
    @patch('requests.Session')
    def test_send_message_api_error(self, mock_session_class, mock_get_config_dir):
        """Test message sending with API error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_get_config_dir.return_value = Path(temp_dir)
            
            # Mock HTTP session with error response
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_session.post.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            service = LocalWhatsAppBusinessService()
            service.save_credentials("test_token", "test_phone_id")
            
            # Test message sending failure
            success = service.send_message(self.test_customer, self.test_template)
            
            self.assertFalse(success)
            
            # Check usage was not logged for failed message
            stats = service.get_usage_stats()
            self.assertEqual(stats['daily_messages_sent'], 0)
    
    @patch('src.multichannel_messaging.services.whatsapp_local_service.get_config_dir')
    def test_send_message_not_configured(self, mock_get_config_dir):
        """Test sending message when service is not configured."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_get_config_dir.return_value = Path(temp_dir)
            
            service = LocalWhatsAppBusinessService()
            
            # Should fail when not configured
            success = service.send_message(self.test_customer, self.test_template)
            self.assertFalse(success)
    
    @patch('src.multichannel_messaging.services.whatsapp_local_service.get_config_dir')
    @patch('requests.Session')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_bulk_message_sending(self, mock_sleep, mock_session_class, mock_get_config_dir):
        """Test bulk message sending functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_get_config_dir.return_value = Path(temp_dir)
            
            # Mock HTTP session
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'messages': [{'id': 'test_message_id'}]
            }
            mock_session.post.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            service = LocalWhatsAppBusinessService()
            service.save_credentials("test_token", "test_phone_id")
            
            # Create test customers
            customers = [
                Customer(name="Customer 1", company="Company 1", phone="+1111111111", email="c1@test.com"),
                Customer(name="Customer 2", company="Company 2", phone="+2222222222", email="c2@test.com")
            ]
            
            # Test bulk sending
            records = service.send_bulk_messages(customers, self.test_template, delay_between_messages=0)
            
            self.assertEqual(len(records), 2)
            self.assertEqual(records[0].status, MessageStatus.SENT)
            self.assertEqual(records[1].status, MessageStatus.SENT)
            self.assertEqual(records[0].channel, "whatsapp")
            self.assertEqual(records[1].channel, "whatsapp")
            
            # Check usage tracking
            stats = service.get_usage_stats()
            self.assertEqual(stats['daily_messages_sent'], 2)
    
    @patch('src.multichannel_messaging.services.whatsapp_local_service.get_config_dir')
    @patch('requests.Session')
    def test_connection_test_success(self, mock_session_class, mock_get_config_dir):
        """Test successful connection testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_get_config_dir.return_value = Path(temp_dir)
            
            # Mock HTTP session
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'display_phone_number': '+1234567890'
            }
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            service = LocalWhatsAppBusinessService()
            service.save_credentials("test_token", "test_phone_id")
            
            success, message = service.test_connection()
            
            self.assertTrue(success)
            self.assertIn("+1234567890", message)
    
    @patch('src.multichannel_messaging.services.whatsapp_local_service.get_config_dir')
    def test_connection_test_not_configured(self, mock_get_config_dir):
        """Test connection testing when not configured."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_get_config_dir.return_value = Path(temp_dir)
            
            service = LocalWhatsAppBusinessService()
            
            success, message = service.test_connection()
            
            self.assertFalse(success)
            self.assertIn("not configured", message)


if __name__ == '__main__':
    unittest.main()
