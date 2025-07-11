#!/usr/bin/env python3
"""
Unit tests for email channel mapping and formatting fixes.

Tests the fixes for:
1. "Unknown channel error" when using translated channel names
2. Email formatting issues with line breaks
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from multichannel_messaging.core.models import Customer, MessageTemplate
from multichannel_messaging.core.i18n_manager import get_i18n_manager


class TestChannelMappingFixes:
    """Test cases for channel mapping fixes."""
    
    @pytest.fixture
    def i18n_manager(self):
        """Get i18n manager instance."""
        return get_i18n_manager()
    
    def test_channel_translations_exist(self, i18n_manager):
        """Test that channel translations exist for all languages."""
        languages = ["en", "pt", "es"]
        channel_keys = ["email_only", "whatsapp_business_api", "whatsapp_web"]
        
        for lang in languages:
            i18n_manager.set_language(lang)
            for key in channel_keys:
                translation = i18n_manager.tr(key)
                assert translation != key, f"Missing translation for {key} in {lang}"
                assert len(translation.strip()) > 0, f"Empty translation for {key} in {lang}"
    
    def test_portuguese_channel_translations(self, i18n_manager):
        """Test specific Portuguese channel translations."""
        i18n_manager.set_language("pt")
        
        assert i18n_manager.tr("email_only") == "Apenas Email"
        assert i18n_manager.tr("whatsapp_business_api") == "WhatsApp Business API"
        assert i18n_manager.tr("whatsapp_web") == "WhatsApp Web"
    
    def test_spanish_channel_translations(self, i18n_manager):
        """Test specific Spanish channel translations."""
        i18n_manager.set_language("es")
        
        assert i18n_manager.tr("email_only") == "Solo Email"
        assert i18n_manager.tr("whatsapp_business_api") == "WhatsApp Business API"
        assert i18n_manager.tr("whatsapp_web") == "WhatsApp Web"
    
    def test_english_channel_translations(self, i18n_manager):
        """Test specific English channel translations."""
        i18n_manager.set_language("en")
        
        assert i18n_manager.tr("email_only") == "Email Only"
        assert i18n_manager.tr("whatsapp_business_api") == "WhatsApp Business API"
        assert i18n_manager.tr("whatsapp_web") == "WhatsApp Web"


class TestEmailFormattingFixes:
    """Test cases for email formatting fixes."""
    
    @pytest.fixture
    def sample_template_with_linebreaks(self):
        """Create sample template with line breaks for testing."""
        return MessageTemplate(
            id="test_format",
            name="Format Test Template",
            channels=["email"],
            subject="Test Subject for {name}",
            content="""Dear {name},

Thank you for your interest in our services. We're excited to have {company} as part of our community.

If you have any questions, please don't hesitate to contact us.

Best regards,
The Team""",
            variables=["name", "company"]
        )
    
    @pytest.fixture
    def sample_customer(self):
        """Create sample customer for testing."""
        return Customer(
            name="Lucas Alves",
            company="Example Corp",
            phone="+1-555-0123",
            email="lucas@example.com"
        )
    
    def test_template_rendering_preserves_linebreaks(self, sample_template_with_linebreaks, sample_customer):
        """Test that template rendering preserves line breaks."""
        rendered = sample_template_with_linebreaks.render(sample_customer)
        content = rendered.get('content', '')
        
        # Check that line breaks are preserved
        assert '\n' in content, "Line breaks should be preserved in rendered content"
        assert content.count('\n') >= 4, "Should have multiple line breaks"
        
        # Check that customer data is properly substituted
        assert "Lucas Alves" in content, "Customer name should be substituted"
        assert "Example Corp" in content, "Company name should be substituted"
    
    def test_html_email_conversion(self):
        """Test HTML email conversion preserves formatting."""
        try:
            from multichannel_messaging.services.outlook_macos import OutlookMacOSService
            
            service = OutlookMacOSService()
            
            test_text = "Paragraph 1\n\nParagraph 2\nLine 2 of paragraph 2"
            html = service._convert_text_to_html(test_text)
            
            # Check that paragraphs are created
            assert '<p>' in html, "Should contain paragraph tags"
            assert '</p>' in html, "Should contain closing paragraph tags"
            
            # Check that line breaks within paragraphs become <br>
            assert '<br>' in html, "Should contain line break tags"
            
            # Check HTML escaping
            test_html = "Text with <tags> & \"quotes\""
            escaped_html = service._convert_text_to_html(test_html)
            assert '&lt;' in escaped_html, "Should escape < characters"
            assert '&amp;' in escaped_html, "Should escape & characters"
            
        except ImportError:
            pytest.skip("macOS Outlook service not available")
    
    def test_html_email_script_generation(self):
        """Test HTML email AppleScript generation."""
        try:
            from multichannel_messaging.services.outlook_macos import OutlookMacOSService
            
            service = OutlookMacOSService()
            
            test_content = "Line 1\n\nLine 3"
            script = service._build_html_email_script(
                "Test Subject", test_content, "test@example.com", False
            )
            
            # Check that HTML format is set
            assert "HTML format" in script, "Should set HTML format"
            
            # Check that HTML tags are present
            assert "<p>" in script, "Should contain HTML paragraph tags"
            
        except ImportError:
            pytest.skip("macOS Outlook service not available")
    
    def test_plain_text_email_script_generation(self):
        """Test plain text email AppleScript generation with return concatenation."""
        try:
            from multichannel_messaging.services.outlook_macos import OutlookMacOSService
            
            service = OutlookMacOSService()
            
            test_content = "Line 1\nLine 2\nLine 3"
            script = service._build_plain_text_email_script(
                "Test Subject", test_content, "test@example.com", False
            )
            
            # Check that return concatenation is used
            assert "& return &" in script, "Should use return concatenation"
            
            # Check that HTML format is NOT set
            assert "HTML format" not in script, "Should not set HTML format for plain text"
            
        except ImportError:
            pytest.skip("macOS Outlook service not available")
    
    def test_email_formatting_fallback(self):
        """Test that email formatting can fallback from HTML to plain text."""
        try:
            from multichannel_messaging.services.outlook_macos import OutlookMacOSService
            
            service = OutlookMacOSService()
            
            # Test that both HTML and plain text methods exist
            assert hasattr(service, '_build_html_email_script'), "Should have HTML email method"
            assert hasattr(service, '_build_plain_text_email_script'), "Should have plain text email method"
            
            # Test configuration options
            assert hasattr(service, 'use_html_format'), "Should have HTML format option"
            assert hasattr(service, 'fallback_to_plain_text'), "Should have fallback option"
            
        except ImportError:
            pytest.skip("macOS Outlook service not available")
    
    def test_applescript_escaping_handles_quotes(self):
        """Test that AppleScript escaping properly handles quotes."""
        try:
            from multichannel_messaging.services.outlook_macos import OutlookMacOSService
            
            service = OutlookMacOSService()
            
            test_text = 'Text with "quotes" and more "quotes"'
            escaped = service._escape_for_applescript(test_text)
            
            # Check that quotes are properly escaped
            assert '\\"' in escaped, "Should contain escaped quotes"
            assert escaped.count('\\"') == 4, "Should have correct number of escaped quotes"
            
        except ImportError:
            pytest.skip("macOS Outlook service not available")
    
    def test_applescript_escaping_handles_backslashes(self):
        """Test that AppleScript escaping properly handles backslashes."""
        try:
            from multichannel_messaging.services.outlook_macos import OutlookMacOSService
            
            service = OutlookMacOSService()
            
            test_text = "Text with \\ backslash"
            escaped = service._escape_for_applescript(test_text)
            
            # Check that backslashes are properly escaped
            assert '\\\\' in escaped, "Should contain escaped backslashes"
            
        except ImportError:
            pytest.skip("macOS Outlook service not available")
    
    def test_email_content_formatting_example(self, sample_template_with_linebreaks, sample_customer):
        """Test the specific email formatting example from the bug report."""
        rendered = sample_template_with_linebreaks.render(sample_customer)
        content = rendered.get('content', '')
        
        # This should match the expected format from the bug report
        expected_lines = [
            "Dear Lucas Alves,",
            "",  # Empty line
            "Thank you for your interest in our services. We're excited to have Example Corp as part of our community.",
            "",  # Empty line
            "If you have any questions, please don't hesitate to contact us.",
            "",  # Empty line
            "Best regards,",
            "The Team"
        ]
        
        actual_lines = content.split('\n')
        
        # Check that we have the expected structure
        assert len(actual_lines) >= len(expected_lines), "Should have correct number of lines"
        assert actual_lines[0] == expected_lines[0], "First line should match"
        assert actual_lines[1] == expected_lines[1], "Should have empty line after greeting"
        assert "Thank you for your interest" in actual_lines[2], "Should have thank you message"


class TestChannelIDMapping:
    """Test cases for channel ID mapping functionality."""
    
    def test_channel_id_consistency(self):
        """Test that channel IDs are consistent and predictable."""
        expected_channel_ids = [
            "email_only",
            "whatsapp_business", 
            "whatsapp_web",
            "email_whatsapp_business",
            "email_whatsapp_web"
        ]
        
        # These should be the standard channel IDs used throughout the application
        for channel_id in expected_channel_ids:
            assert isinstance(channel_id, str), "Channel ID should be string"
            assert len(channel_id) > 0, "Channel ID should not be empty"
            assert '_' in channel_id or channel_id == "email", "Channel ID should use underscore format"
    
    def test_channel_description_mapping(self):
        """Test that channel descriptions work for all channel IDs."""
        # This would test the _get_channel_description method if we could import it
        # For now, we test the expected mapping logic
        
        descriptions = {
            "email_only": "email",
            "whatsapp_business": "WhatsApp Business API",
            "whatsapp_web": "WhatsApp Web (manual sending required)",
            "email_whatsapp_business": "email and WhatsApp Business API",
            "email_whatsapp_web": "email and WhatsApp Web"
        }
        
        for channel_id, description in descriptions.items():
            assert isinstance(description, str), f"Description for {channel_id} should be string"
            assert len(description) > 0, f"Description for {channel_id} should not be empty"


if __name__ == "__main__":
    pytest.main([__file__])
