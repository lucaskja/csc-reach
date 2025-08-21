"""
Unit tests for enhanced WhatsApp Business API integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

from src.multichannel_messaging.services.api_clients.whatsapp_api_client import (
    WhatsAppAPIClient, APIHealthMetrics, EnhancedHTTPAdapter
)
from src.multichannel_messaging.core.rate_limiter import (
    IntelligentRateLimiter, QuotaType, QuotaConfig
)
from src.multichannel_messaging.core.whatsapp_template_manager import (
    WhatsAppTemplateManager, WhatsAppTemplate, TemplateCategory, TemplateStatus
)
from src.multichannel_messaging.core.webhook_manager import (
    WhatsAppDeliverySystem, DeliveryTracker, WebhookManager, MessageStatus
)
from src.multichannel_messaging.utils.exceptions import WhatsAppAPIError, QuotaExceededError


class TestEnhancedWhatsAppAPIClient:
    """Test enhanced WhatsApp API client functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = WhatsAppAPIClient(
            access_token="test_token",
            phone_number_id="test_phone_id",
            webhook_secret="test_secret",
            enable_delivery_tracking=True
        )
    
    def test_client_initialization(self):
        """Test client initialization with enhanced features."""
        assert self.client.access_token == "test_token"
        assert self.client.phone_number_id == "test_phone_id"
        assert self.client.rate_limiter is not None
        assert self.client.delivery_system is not None
        assert self.client.health_metrics is not None
    
    def test_health_metrics_tracking(self):
        """Test API health metrics tracking."""
        metrics = self.client.get_health_metrics()
        
        assert isinstance(metrics, APIHealthMetrics)
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
    
    def test_rate_limit_status(self):
        """Test rate limit status retrieval."""
        status = self.client.get_rate_limit_status()
        
        assert isinstance(status, dict)
        assert QuotaType.MESSAGES_PER_MINUTE.value in status
        assert QuotaType.MESSAGES_PER_HOUR.value in status
        assert QuotaType.MESSAGES_PER_DAY.value in status
    
    @patch('requests.Session.request')
    def test_send_text_message_with_tracking(self, mock_request):
        """Test sending text message with delivery tracking."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messages": [{"id": "test_message_id"}]
        }
        mock_request.return_value = mock_response
        
        # Send message
        result = self.client.send_text_message("+1234567890", "Test message")
        
        # Verify API call
        assert mock_request.called
        assert result["messages"][0]["id"] == "test_message_id"
        
        # Verify delivery tracking
        if self.client.delivery_system:
            record = self.client.delivery_system.delivery_tracker.get_message_status("test_message_id")
            assert record is not None
            assert record.phone_number == "+1234567890"
            assert record.status == MessageStatus.SENT
    
    def test_webhook_processing(self):
        """Test webhook payload processing."""
        webhook_payload = json.dumps({
            "entry": [{
                "changes": [{
                    "field": "messages",
                    "value": {
                        "statuses": [{
                            "id": "test_message_id",
                            "status": "delivered",
                            "timestamp": str(int(datetime.now().timestamp()))
                        }]
                    }
                }]
            }]
        })
        
        # Process webhook
        result = self.client.process_webhook(webhook_payload)
        assert result is True
    
    def test_analytics_retrieval(self):
        """Test delivery analytics retrieval."""
        analytics = self.client.get_delivery_analytics(days=7)
        
        assert isinstance(analytics, dict)
        assert "time_period" in analytics
        assert "total_messages" in analytics
        assert "delivery_rate" in analytics


class TestIntelligentRateLimiter:
    """Test intelligent rate limiter functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        quota_configs = [
            QuotaConfig(
                quota_type=QuotaType.MESSAGES_PER_MINUTE,
                limit=5,
                window_seconds=60,
                burst_capacity=2
            )
        ]
        self.rate_limiter = IntelligentRateLimiter(
            quota_configs=quota_configs,
            enable_persistence=False
        )
    
    def test_quota_checking(self):
        """Test quota checking functionality."""
        # Should allow requests within limit
        can_proceed, reason, details = self.rate_limiter.can_make_request(QuotaType.MESSAGES_PER_MINUTE)
        assert can_proceed is True
        assert details["current_usage"] == 0
        assert details["limit"] == 5
    
    def test_quota_enforcement(self):
        """Test quota enforcement."""
        # Use up regular capacity
        for i in range(5):
            self.rate_limiter.record_request(QuotaType.MESSAGES_PER_MINUTE)
        
        # Should still allow burst capacity
        can_proceed, reason, details = self.rate_limiter.can_make_request(QuotaType.MESSAGES_PER_MINUTE)
        assert can_proceed is True
        assert details["using_burst"] is True
        
        # Use up burst capacity
        for i in range(2):
            self.rate_limiter.record_request(QuotaType.MESSAGES_PER_MINUTE, use_burst=True)
        
        # Should now be blocked
        can_proceed, reason, details = self.rate_limiter.can_make_request(QuotaType.MESSAGES_PER_MINUTE)
        assert can_proceed is False
    
    def test_quota_reset(self):
        """Test quota reset functionality."""
        # Use up quota
        for i in range(5):
            self.rate_limiter.record_request(QuotaType.MESSAGES_PER_MINUTE)
        
        # Reset quota
        success = self.rate_limiter.reset_quota(QuotaType.MESSAGES_PER_MINUTE)
        assert success is True
        
        # Should allow requests again
        can_proceed, reason, details = self.rate_limiter.can_make_request(QuotaType.MESSAGES_PER_MINUTE)
        assert can_proceed is True


class TestWhatsAppTemplateManager:
    """Test WhatsApp template manager functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.api_client = Mock()
        self.template_manager = WhatsAppTemplateManager(
            api_client=self.api_client
        )
        # Clear any existing templates for clean test state
        self.template_manager.templates.clear()
    
    def test_template_creation(self):
        """Test template creation."""
        template = self.template_manager.create_template(
            name="test_template",
            language="en",
            category=TemplateCategory.UTILITY,
            body_text="Hello {{1}}, welcome to {{2}}!"
        )
        
        assert template.name == "test_template"
        assert template.language == "en"
        assert template.category == TemplateCategory.UTILITY
        assert template.status == TemplateStatus.DRAFT
        assert len(template.components) == 1  # Body component
    
    def test_template_validation(self):
        """Test template validation."""
        # Valid template
        template = WhatsAppTemplate(
            name="valid_template",
            language="en",
            category=TemplateCategory.UTILITY,
            components=[]
        )
        
        errors = template.validate()
        assert "Template must have at least one component" in errors
        
        # Invalid name
        template.name = "Invalid Name!"
        errors = template.validate()
        assert any("lowercase letters, numbers, and underscores" in error for error in errors)
    
    def test_template_preview(self):
        """Test template preview functionality."""
        # Create template with parameters
        self.template_manager.create_template(
            name="preview_test",
            language="en",
            category=TemplateCategory.UTILITY,
            body_text="Hello {{1}}, your order {{2}} is ready!"
        )
        
        # Preview with parameters
        preview = self.template_manager.preview_template(
            "preview_test",
            {"param_1": "John", "param_2": "#12345"}
        )
        
        assert "body" in preview
        assert "Hello John, your order #12345 is ready!" in preview["body"]


class TestDeliveryTracker:
    """Test delivery tracking functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tracker = DeliveryTracker()
    
    def test_message_tracking(self):
        """Test message tracking."""
        record = self.tracker.track_message(
            message_id="test_msg_123",
            phone_number="+1234567890",
            message_content="Test message"
        )
        
        assert record.message_id == "test_msg_123"
        assert record.phone_number == "+1234567890"
        assert record.status == MessageStatus.QUEUED
    
    def test_status_updates(self):
        """Test status updates."""
        # Track message
        self.tracker.track_message("test_msg_123", "+1234567890")
        
        # Update status
        success = self.tracker.update_message_status(
            "test_msg_123",
            MessageStatus.DELIVERED,
            datetime.now()
        )
        
        assert success is True
        
        # Verify status
        record = self.tracker.get_message_status("test_msg_123")
        assert record.status == MessageStatus.DELIVERED
        assert record.delivered_at is not None
    
    def test_analytics_generation(self):
        """Test analytics generation."""
        # Track some messages
        for i in range(10):
            self.tracker.track_message(f"msg_{i}", f"+123456789{i}")
            self.tracker.update_message_status(f"msg_{i}", MessageStatus.DELIVERED)
        
        # Generate analytics
        analytics = self.tracker.get_delivery_analytics(days=1)
        
        assert analytics.total_messages >= 10
        assert analytics.delivered_messages >= 10
        assert analytics.delivery_rate > 0


class TestWebhookManager:
    """Test webhook manager functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.delivery_tracker = DeliveryTracker()
        self.webhook_manager = WebhookManager(
            webhook_secret="test_secret",
            delivery_tracker=self.delivery_tracker
        )
    
    def test_signature_verification(self):
        """Test webhook signature verification."""
        payload = '{"test": "data"}'
        
        # Generate valid signature
        import hmac
        import hashlib
        signature = hmac.new(
            "test_secret".encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Verify signature
        is_valid = self.webhook_manager.verify_webhook_signature(payload, signature)
        assert is_valid is True
        
        # Test invalid signature
        is_valid = self.webhook_manager.verify_webhook_signature(payload, "invalid_signature")
        assert is_valid is False
    
    def test_webhook_processing(self):
        """Test webhook payload processing."""
        # Track a message first
        self.delivery_tracker.track_message("test_msg_123", "+1234567890")
        
        # Create webhook payload
        payload = json.dumps({
            "entry": [{
                "changes": [{
                    "field": "messages",
                    "value": {
                        "statuses": [{
                            "id": "test_msg_123",
                            "status": "delivered",
                            "timestamp": str(int(datetime.now().timestamp()))
                        }]
                    }
                }]
            }]
        })
        
        # Process webhook
        result = self.webhook_manager.process_webhook(payload)
        assert result is True
        
        # Verify status was updated
        record = self.delivery_tracker.get_message_status("test_msg_123")
        assert record.status == MessageStatus.DELIVERED


if __name__ == "__main__":
    pytest.main([__file__])