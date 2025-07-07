"""
Unit tests for WhatsApp Business API service.
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
import json
from datetime import datetime

from src.multichannel_messaging.services.whatsapp_business_service import AWSWhatsAppBusinessService
from src.multichannel_messaging.core.models import Customer, MessageTemplate, MessageStatus
from src.multichannel_messaging.utils.exceptions import WhatsAppConfigurationError


class TestAWSWhatsAppBusinessService(unittest.TestCase):
    """Test cases for AWS WhatsApp Business service."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_credentials = {
            "access_token": "test_access_token",
            "phone_number_id": "test_phone_id",
            "business_account_id": "test_business_id"
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
    
    @patch('boto3.client')
    def test_credential_loading_success(self, mock_boto_client):
        """Test successful credential loading from AWS Secrets Manager."""
        # Mock Secrets Manager client
        mock_secrets_client = MagicMock()
        mock_secrets_client.get_secret_value.return_value = {
            'SecretString': json.dumps(self.mock_credentials)
        }
        
        # Mock CloudWatch client
        mock_cloudwatch_client = MagicMock()
        
        mock_boto_client.side_effect = [mock_secrets_client, mock_cloudwatch_client]
        
        # Mock the API client initialization and connection test
        with patch.object(AWSWhatsAppBusinessService, '_initialize_api_client') as mock_init_api, \
             patch.object(AWSWhatsAppBusinessService, 'test_connection') as mock_test_conn:
            
            mock_init_api.return_value = MagicMock()
            mock_test_conn.return_value = (True, "Connected successfully")
            
            service = AWSWhatsAppBusinessService()
            
            self.assertEqual(service.credentials, self.mock_credentials)
            mock_secrets_client.get_secret_value.assert_called_once()
    
    @patch('boto3.client')
    def test_credential_loading_failure(self, mock_boto_client):
        """Test credential loading failure."""
        mock_secrets_client = MagicMock()
        mock_secrets_client.get_secret_value.side_effect = Exception("Secret not found")
        mock_boto_client.return_value = mock_secrets_client
        
        with self.assertRaises(WhatsAppConfigurationError):
            AWSWhatsAppBusinessService()
    
    @patch('boto3.client')
    def test_phone_number_validation(self, mock_boto_client):
        """Test phone number validation."""
        # Mock AWS clients
        mock_secrets_client = MagicMock()
        mock_secrets_client.get_secret_value.return_value = {
            'SecretString': json.dumps(self.mock_credentials)
        }
        mock_cloudwatch_client = MagicMock()
        mock_boto_client.side_effect = [mock_secrets_client, mock_cloudwatch_client]
        
        with patch.object(AWSWhatsAppBusinessService, '_initialize_api_client') as mock_init_api, \
             patch.object(AWSWhatsAppBusinessService, 'test_connection') as mock_test_conn:
            
            mock_init_api.return_value = MagicMock()
            mock_test_conn.return_value = (True, "Connected")
            
            service = AWSWhatsAppBusinessService()
            
            # Test valid phone numbers
            self.assertTrue(service._validate_phone_number("+1234567890"))
            self.assertTrue(service._validate_phone_number("1234567890"))
            self.assertTrue(service._validate_phone_number("+44123456789"))
            
            # Test invalid phone numbers
            self.assertFalse(service._validate_phone_number(""))
            self.assertFalse(service._validate_phone_number("123"))  # Too short
            self.assertFalse(service._validate_phone_number("12345678901234567"))  # Too long
            self.assertFalse(service._validate_phone_number("abc123"))  # Contains letters
    
    @patch('boto3.client')
    @patch('requests.Session')
    def test_send_message_success(self, mock_session_class, mock_boto_client):
        """Test successful message sending."""
        # Mock AWS clients
        mock_secrets_client = MagicMock()
        mock_secrets_client.get_secret_value.return_value = {
            'SecretString': json.dumps(self.mock_credentials)
        }
        mock_cloudwatch_client = MagicMock()
        mock_boto_client.side_effect = [mock_secrets_client, mock_cloudwatch_client]
        
        # Mock HTTP session
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'messages': [{'id': 'test_message_id'}]
        }
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        with patch.object(AWSWhatsAppBusinessService, 'test_connection') as mock_test_conn:
            mock_test_conn.return_value = (True, "Connected")
            
            service = AWSWhatsAppBusinessService()
            
            # Test message sending
            success = service.send_message(self.test_customer, self.test_template)
            
            self.assertTrue(success)
            mock_session.post.assert_called_once()
    
    @patch('boto3.client')
    @patch('requests.Session')
    def test_send_message_api_error(self, mock_session_class, mock_boto_client):
        """Test message sending with API error."""
        # Mock AWS clients
        mock_secrets_client = MagicMock()
        mock_secrets_client.get_secret_value.return_value = {
            'SecretString': json.dumps(self.mock_credentials)
        }
        mock_cloudwatch_client = MagicMock()
        mock_boto_client.side_effect = [mock_secrets_client, mock_cloudwatch_client]
        
        # Mock HTTP session with error response
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        with patch.object(AWSWhatsAppBusinessService, 'test_connection') as mock_test_conn:
            mock_test_conn.return_value = (True, "Connected")
            
            service = AWSWhatsAppBusinessService()
            
            # Test message sending failure
            success = service.send_message(self.test_customer, self.test_template)
            
            self.assertFalse(success)
    
    @patch('boto3.client')
    def test_rate_limiting(self, mock_boto_client):
        """Test rate limiting functionality."""
        # Mock AWS clients
        mock_secrets_client = MagicMock()
        mock_secrets_client.get_secret_value.return_value = {
            'SecretString': json.dumps(self.mock_credentials)
        }
        mock_cloudwatch_client = MagicMock()
        mock_boto_client.side_effect = [mock_secrets_client, mock_cloudwatch_client]
        
        with patch.object(AWSWhatsAppBusinessService, '_initialize_api_client') as mock_init_api, \
             patch.object(AWSWhatsAppBusinessService, 'test_connection') as mock_test_conn:
            
            mock_init_api.return_value = MagicMock()
            mock_test_conn.return_value = (True, "Connected")
            
            # Create service with low rate limit for testing
            service = AWSWhatsAppBusinessService(rate_limit_per_minute=2)
            
            # Initially should allow messages
            self.assertTrue(service._check_rate_limits())
            
            # Simulate sending messages to reach limit
            service._log_message_sent()
            service._log_message_sent()
            
            # Should now be at limit
            self.assertFalse(service._check_rate_limits())
    
    @patch('boto3.client')
    def test_usage_stats(self, mock_boto_client):
        """Test usage statistics tracking."""
        # Mock AWS clients
        mock_secrets_client = MagicMock()
        mock_secrets_client.get_secret_value.return_value = {
            'SecretString': json.dumps(self.mock_credentials)
        }
        mock_cloudwatch_client = MagicMock()
        mock_boto_client.side_effect = [mock_secrets_client, mock_cloudwatch_client]
        
        with patch.object(AWSWhatsAppBusinessService, '_initialize_api_client') as mock_init_api, \
             patch.object(AWSWhatsAppBusinessService, 'test_connection') as mock_test_conn:
            
            mock_init_api.return_value = MagicMock()
            mock_test_conn.return_value = (True, "Connected")
            
            service = AWSWhatsAppBusinessService(daily_message_limit=100)
            
            # Get initial stats
            stats = service.get_usage_stats()
            
            self.assertEqual(stats['daily_messages_sent'], 0)
            self.assertEqual(stats['daily_limit'], 100)
            self.assertEqual(stats['remaining_daily'], 100)
            
            # Simulate sending a message
            service._log_message_sent()
            
            # Check updated stats
            stats = service.get_usage_stats()
            self.assertEqual(stats['daily_messages_sent'], 1)
            self.assertEqual(stats['remaining_daily'], 99)
    
    @patch('boto3.client')
    @patch('requests.Session')
    def test_bulk_message_sending(self, mock_session_class, mock_boto_client):
        """Test bulk message sending functionality."""
        # Mock AWS clients
        mock_secrets_client = MagicMock()
        mock_secrets_client.get_secret_value.return_value = {
            'SecretString': json.dumps(self.mock_credentials)
        }
        mock_cloudwatch_client = MagicMock()
        mock_boto_client.side_effect = [mock_secrets_client, mock_cloudwatch_client]
        
        # Mock HTTP session
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'messages': [{'id': 'test_message_id'}]
        }
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        with patch.object(AWSWhatsAppBusinessService, 'test_connection') as mock_test_conn:
            mock_test_conn.return_value = (True, "Connected")
            
            service = AWSWhatsAppBusinessService()
            
            # Create test customers
            customers = [
                Customer(name="Customer 1", company="Company 1", phone="+1111111111", email="c1@test.com"),
                Customer(name="Customer 2", company="Company 2", phone="+2222222222", email="c2@test.com")
            ]
            
            # Test bulk sending
            with patch('time.sleep'):  # Skip actual delays in tests
                records = service.send_bulk_messages(customers, self.test_template, delay_between_messages=0)
            
            self.assertEqual(len(records), 2)
            self.assertEqual(records[0].status, MessageStatus.SENT)
            self.assertEqual(records[1].status, MessageStatus.SENT)
            self.assertEqual(records[0].channel, "whatsapp")
            self.assertEqual(records[1].channel, "whatsapp")


if __name__ == '__main__':
    unittest.main()
