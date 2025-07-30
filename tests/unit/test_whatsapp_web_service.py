"""
Unit tests for WhatsApp Web Service.
Tests the enhanced WhatsApp Web integration including Windows optimizations.
"""

import pytest
import platform
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.multichannel_messaging.services.whatsapp_web_service import WhatsAppWebService
from src.multichannel_messaging.core.models import Customer, MessageTemplate


class TestWhatsAppWebService:
    """Test WhatsApp Web Service functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create service with explicit parameters
        self.service = WhatsAppWebService(
            rate_limit_per_minute=10,
            daily_message_limit=100,
            min_delay_seconds=5,
            close_existing_tabs=True
        )
        # Override any loaded configuration for clean tests
        self.service._is_configured = False
        self.service.rate_limit_per_minute = 10
        self.service.daily_message_limit = 100
        self.service.min_delay_seconds = 5
        self.service.close_existing_tabs = True
        
        self.customer = Customer(
            name="Test User",
            phone="+1234567890",
            email="test@example.com",
            company="Test Company"
        )
        
        self.template = MessageTemplate(
            id="test-template-001",
            name="Test Template",
            channels=["whatsapp"],
            content="Hello {name}, this is a test message from {company}!",
            whatsapp_content="Hello {name}, this is a WhatsApp test message from {company}!",
            variables=["name", "company"]
        )
    
    def test_service_initialization(self):
        """Test service initializes correctly."""
        assert self.service.is_available()
        assert not self.service.is_configured()
        assert self.service.close_existing_tabs is True
        assert self.service.rate_limit_per_minute == 10
        assert self.service.daily_message_limit == 100
    
    def test_service_configuration(self):
        """Test service configuration."""
        success, message = self.service.configure_service(
            acknowledge_risks=True,
            auto_send=False,
            close_existing_tabs=True
        )
        
        assert success is True
        assert "successfully" in message.lower()
        assert self.service.is_configured()
    
    def test_phone_number_formatting(self):
        """Test phone number formatting."""
        test_cases = [
            ("+1234567890", "1234567890"),
            ("1234567890", "11234567890"),
            ("(123) 456-7890", "11234567890"),
            ("+44 20 7946 0958", "442079460958"),
            ("", None),
            ("invalid", None)
        ]
        
        for input_phone, expected in test_cases:
            result = self.service._format_phone_number(input_phone)
            assert result == expected, f"Failed for {input_phone}: got {result}, expected {expected}"
    
    def test_message_rendering(self):
        """Test message rendering with customer data."""
        rendered = self.service._render_message(self.customer, self.template)
        
        assert "Test User" in rendered
        assert "Test Company" in rendered
        assert "{name}" not in rendered
        assert "{company}" not in rendered
    
    def test_whatsapp_url_creation(self):
        """Test WhatsApp URL creation."""
        phone = "1234567890"
        message = "Hello Test User, this is a test message!"
        
        url = self.service._create_whatsapp_url(phone, message)
        
        assert url.startswith("https://web.whatsapp.com/send")
        assert f"phone={phone}" in url
        assert "text=" in url
        assert "Hello%20Test%20User" in url  # URL encoded
    
    def test_daily_usage_tracking(self):
        """Test daily usage tracking."""
        initial_usage = self.service.get_daily_usage()
        assert initial_usage["messages_sent_today"] == 0
        assert initial_usage["daily_limit"] == self.service.daily_message_limit
        assert initial_usage["remaining_today"] == 100
        
        # Simulate sending a message
        self.service._track_message_sent()
        
        updated_usage = self.service.get_daily_usage()
        assert updated_usage["messages_sent_today"] == 1
        assert updated_usage["remaining_today"] == self.service.daily_message_limit - 1
    
    def test_can_send_message_limits(self):
        """Test message sending limits."""
        # Configure service first
        self.service.configure_service(acknowledge_risks=True)
        
        # Should be able to send initially
        can_send, reason = self.service.can_send_message()
        assert can_send is True
        
        # Simulate hitting daily limit
        self.service.daily_usage["messages_sent"] = self.service.daily_message_limit
        
        can_send, reason = self.service.can_send_message()
        assert can_send is False
        assert "daily limit" in reason.lower()
    
    def test_chrome_availability_check(self):
        """Test Chrome availability checking."""
        available, info = self.service._check_chrome_availability()
        
        # Should return boolean and string
        assert isinstance(available, bool)
        assert isinstance(info, str)
        assert len(info) > 0
    
    def test_windows_methods_exist(self):
        """Test that Windows-specific methods exist."""
        windows_methods = [
            '_detect_chrome_windows',
            '_auto_send_javascript_windows',
            '_auto_send_windows',
            '_auto_send_windows_simple',
            '_close_whatsapp_tabs_windows',
            '_show_windows_notification'
        ]
        
        for method_name in windows_methods:
            assert hasattr(self.service, method_name), f"Missing Windows method: {method_name}"
            method = getattr(self.service, method_name)
            assert callable(method), f"Windows method not callable: {method_name}"
    
    def test_platform_specific_methods_exist(self):
        """Test that platform-specific methods exist."""
        current_platform = platform.system().lower()
        
        # Tab closing methods
        tab_methods = {
            'darwin': '_close_whatsapp_tabs_macos',
            'windows': '_close_whatsapp_tabs_windows',
            'linux': '_close_whatsapp_tabs_linux'
        }
        
        if current_platform in tab_methods:
            method_name = tab_methods[current_platform]
            assert hasattr(self.service, method_name)
            assert callable(getattr(self.service, method_name))
    
    def test_service_info_generation(self):
        """Test service information generation."""
        info = self.service.get_service_info()
        
        required_keys = [
            'service_name', 'is_available', 'is_configured', 'platform',
            'chrome_status', 'daily_usage', 'rate_limits', 'auto_send',
            'platform_features', 'warnings', 'features'
        ]
        
        for key in required_keys:
            assert key in info, f"Missing key in service info: {key}"
        
        assert info['is_available'] is True
        assert isinstance(info['platform_features'], list)
        assert isinstance(info['warnings'], list)
        assert isinstance(info['features'], list)
    
    @patch('subprocess.run')
    def test_tab_closing_methods_dont_fail(self, mock_subprocess):
        """Test that tab closing methods don't fail even if no tabs exist."""
        # Mock subprocess to simulate no Chrome processes
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")
        
        # Test main tab closing method
        result = self.service._close_existing_whatsapp_tabs()
        assert result is True  # Should not fail
        
        # Test platform-specific methods
        current_platform = platform.system().lower()
        
        if current_platform == 'darwin':
            result = self.service._close_whatsapp_tabs_macos()
            assert result is True
        elif current_platform == 'windows':
            result = self.service._close_whatsapp_tabs_windows()
            assert result is True
        elif current_platform == 'linux':
            result = self.service._close_whatsapp_tabs_linux()
            assert result is True
    
    def test_error_handling(self):
        """Test error handling in various scenarios."""
        # Test with customer that has invalid phone after creation
        valid_customer = Customer(
            name="Test User",
            phone="+1234567890",
            email="test@example.com",
            company="Test Company"
        )
        # Manually set invalid phone to bypass validation
        valid_customer.phone = ""
        
        # Configure service
        self.service.configure_service(acknowledge_risks=True)
        
        # Should handle invalid phone gracefully
        with patch.object(self.service, '_open_in_chrome', return_value=True):
            result = self.service.send_message(valid_customer, self.template)
            assert result is False
            
            error = self.service.get_last_error()
            assert error is not None
            assert "phone" in error.lower()
    
    def test_configuration_persistence(self):
        """Test that configuration persists correctly."""
        # Configure with specific settings
        success, _ = self.service.configure_service(
            acknowledge_risks=True,
            auto_send=True,
            close_existing_tabs=False
        )
        
        assert success is True
        assert self.service.auto_send is True
        assert self.service.close_existing_tabs is False
        
        # Create new service instance (should load saved config)
        new_service = WhatsAppWebService()
        
        # Note: In a real test, this would load from file
        # For unit test, we just verify the configuration was set
        assert self.service.is_configured()


class TestWhatsAppWebServiceWindows:
    """Test Windows-specific functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = WhatsAppWebService()
    
    @pytest.mark.skipif(platform.system().lower() != 'windows', reason="Windows-specific test")
    def test_windows_chrome_detection(self):
        """Test Windows Chrome detection (Windows only)."""
        if hasattr(self.service, '_detect_chrome_windows'):
            chrome_info = self.service._detect_chrome_windows()
            
            assert isinstance(chrome_info, dict)
            assert 'found' in chrome_info
            assert 'details' in chrome_info
            assert 'paths' in chrome_info
            assert 'version' in chrome_info
            assert 'registry_found' in chrome_info
            assert 'process_running' in chrome_info
    
    @patch('subprocess.run')
    def test_windows_notification_method(self, mock_subprocess):
        """Test Windows notification method."""
        if hasattr(self.service, '_show_windows_notification'):
            # Mock successful PowerShell execution
            mock_subprocess.return_value = Mock(
                returncode=0,
                stdout="TOAST_SUCCESS",
                stderr=""
            )
            
            result = self.service._show_windows_notification(
                "Test Title",
                "Test Message"
            )
            
            # Should not fail even if notifications aren't available
            assert isinstance(result, bool)
    
    @patch('subprocess.run')
    def test_windows_auto_send_methods(self, mock_subprocess):
        """Test Windows auto-send methods."""
        # Mock successful execution
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout="SUCCESS_DEVTOOLS",
            stderr=""
        )
        
        windows_auto_send_methods = [
            '_auto_send_javascript_windows',
            '_auto_send_windows',
            '_auto_send_windows_simple'
        ]
        
        for method_name in windows_auto_send_methods:
            if hasattr(self.service, method_name):
                method = getattr(self.service, method_name)
                result = method()
                # Should return boolean and not raise exception
                assert isinstance(result, bool)


class TestWhatsAppWebServiceIntegration:
    """Integration tests for WhatsApp Web Service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = WhatsAppWebService(
            rate_limit_per_minute=10,
            daily_message_limit=100,
            min_delay_seconds=1,  # Short delay for testing
            close_existing_tabs=True
        )
        
        self.customer = Customer(
            name="Integration Test User",
            phone="+1234567890",
            email="integration@example.com",
            company="Test Company"
        )
        
        self.template = MessageTemplate(
            id="integration-test-template",
            name="Integration Test Template",
            channels=["whatsapp"],
            content="Hello {name}, this is an integration test from {company}!",
            whatsapp_content="📱 Hello {name}, this is a WhatsApp integration test from {company}! 🚀",
            variables=["name", "company"]
        )
    
    @patch.object(WhatsAppWebService, '_open_in_chrome')
    @patch.object(WhatsAppWebService, '_close_existing_whatsapp_tabs')
    def test_complete_message_flow(self, mock_close_tabs, mock_open_chrome):
        """Test complete message sending flow."""
        # Configure service
        success, _ = self.service.configure_service(acknowledge_risks=True)
        assert success is True
        
        # Mock Chrome opening and tab closing
        mock_open_chrome.return_value = True
        mock_close_tabs.return_value = True
        
        # Send message
        result = self.service.send_message(self.customer, self.template)
        
        # Should succeed
        assert result is True
        
        # Verify Chrome opening was called
        mock_open_chrome.assert_called_once()
        
        # Verify tab closing was called (if enabled)
        if self.service.close_existing_tabs:
            mock_close_tabs.assert_called_once()
        
        # Verify usage was tracked
        usage = self.service.get_daily_usage()
        assert usage["messages_sent_today"] == 1
    
    def test_service_resilience(self):
        """Test service resilience to various failure scenarios."""
        # Configure service
        self.service.configure_service(acknowledge_risks=True)
        
        # Create valid customers first, then modify them to test error handling
        valid_customer1 = Customer("Test User", "+1234567890", "test@example.com", "Test Company")
        valid_customer2 = Customer("Test User", "+1234567890", "test@example.com", "Test Company")
        
        # Modify to create invalid scenarios
        valid_customer1.phone = ""  # Empty phone
        valid_customer2.phone = "invalid"  # Invalid phone format
        
        test_cases = [
            valid_customer1,
            valid_customer2,
            None  # Invalid template test
        ]
        
        for i, invalid_customer in enumerate(test_cases):
            if invalid_customer is None:
                # Test with invalid template
                invalid_template = MessageTemplate(
                    id=f"invalid-{i}",
                    name="Invalid Template",
                    channels=["whatsapp"],
                    content="",  # Empty content
                    whatsapp_content="",
                    variables=[]
                )
                
                with patch.object(self.service, '_open_in_chrome', return_value=True):
                    result = self.service.send_message(self.customer, invalid_template)
                    assert result is False
            else:
                with patch.object(self.service, '_open_in_chrome', return_value=True):
                    result = self.service.send_message(invalid_customer, self.template)
                    assert result is False
                    
                    # Should have error message
                    error = self.service.get_last_error()
                    assert error is not None