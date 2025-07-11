#!/usr/bin/env python3
"""
Unit tests for new email formatting approaches.

Tests the multiple approaches for handling email line breaks:
1. File-based content transfer
2. Simple text with linefeed
3. Ultra-safe escaping
"""

import sys
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from multichannel_messaging.core.models import Customer, MessageTemplate


class TestEmailFormattingApproaches:
    """Test cases for new email formatting approaches."""
    
    @pytest.fixture
    def sample_content_with_formatting(self):
        """Create sample content with complex formatting for testing."""
        return """Dear Lucas Alves,

I hope this message finds you well. I'm reaching out from CSC-Reach to introduce our "comprehensive" communication platform.

At Example Corp, we understand the importance of effective communication. Our platform offers:

• Seamless email integration with Microsoft Outlook
• Multi-channel messaging capabilities
• Professional template management

I'd love to schedule a brief call to discuss how CSC-Reach can benefit your organization.

Best regards,
CSC-Reach Team

P.S. Feel free to reply to this email or call us directly. We're here to help!"""
    
    @pytest.fixture
    def sample_customer(self):
        """Create sample customer for testing."""
        return Customer(
            name="Lucas Alves",
            company="Example Corp",
            phone="+1-555-0123",
            email="lucaskle@amazon.com"
        )
    
    def test_file_based_email_script_generation(self, sample_content_with_formatting, sample_customer):
        """Test file-based email script generation."""
        try:
            from multichannel_messaging.services.outlook_macos import OutlookMacOSService
            
            service = OutlookMacOSService()
            
            # Test file-based approach
            script = service._build_file_based_email_script(
                "Test Subject", 
                sample_content_with_formatting, 
                sample_customer.email, 
                False
            )
            
            # Check that file-based approach is used
            assert "POSIX file" in script, "Should use POSIX file for content"
            assert "read contentFile" in script, "Should read content from file"
            assert "«class utf8»" in script, "Should specify UTF-8 encoding"
            assert "rm '" in script, "Should clean up temporary file"
            
            # Check that subject and email are properly escaped
            assert "Test Subject" in script, "Subject should be present"
            assert sample_customer.email in script, "Email should be present"
            
        except ImportError:
            pytest.skip("macOS Outlook service not available")
    
    def test_simple_text_email_script_generation(self, sample_content_with_formatting, sample_customer):
        """Test simple text email script generation."""
        try:
            from multichannel_messaging.services.outlook_macos import OutlookMacOSService
            
            service = OutlookMacOSService()
            
            # Test simple text approach
            script = service._build_simple_text_email_script(
                "Test Subject", 
                sample_content_with_formatting, 
                sample_customer.email, 
                False
            )
            
            # Check that linefeed is used for line breaks
            assert "linefeed" in script, "Should use linefeed for line breaks"
            assert "& linefeed &" in script, "Should concatenate with linefeed"
            
            # Check that quotes are replaced with single quotes
            assert '"comprehensive"' not in script, "Should not contain double quotes in content"
            assert "'comprehensive'" in script or "comprehensive" in script, "Should handle quotes safely"
            
        except ImportError:
            pytest.skip("macOS Outlook service not available")
    
    def test_ultra_safe_escaping(self):
        """Test ultra-safe AppleScript escaping."""
        try:
            from multichannel_messaging.services.outlook_macos import OutlookMacOSService
            
            service = OutlookMacOSService()
            
            # Test various problematic inputs
            test_cases = [
                ('Simple text', 'Simple text'),
                ('Text with "quotes"', "Text with 'quotes'"),
                ('Text with \\ backslash', 'Text with  backslash'),
                ('Text\nwith\nline\nbreaks', 'Text\nwith\nline\nbreaks'),
                ('Text\twith\ttabs', 'Text with tabs'),
            ]
            
            for input_text, expected_pattern in test_cases:
                escaped = service._escape_for_applescript_ultra_safe(input_text)
                
                # Check that no double quotes remain
                assert '"' not in escaped, f"Should not contain double quotes: {escaped}"
                
                # Check that backslashes are removed
                assert '\\' not in escaped, f"Should not contain backslashes: {escaped}"
                
                # Check that line breaks are preserved
                if '\n' in input_text:
                    assert '\n' in escaped, f"Should preserve line breaks: {escaped}"
            
        except ImportError:
            pytest.skip("macOS Outlook service not available")
    
    def test_email_script_fallback_mechanism(self, sample_content_with_formatting, sample_customer):
        """Test that email script generation uses fallback mechanisms."""
        try:
            from multichannel_messaging.services.outlook_macos import OutlookMacOSService
            
            service = OutlookMacOSService()
            
            # Test that main method tries file-based first
            with patch.object(service, '_build_file_based_email_script') as mock_file_based:
                with patch.object(service, '_build_simple_text_email_script') as mock_simple:
                    mock_file_based.side_effect = Exception("File-based failed")
                    mock_simple.return_value = "simple script"
                    
                    result = service._build_email_script(
                        "Test Subject",
                        sample_content_with_formatting,
                        sample_customer.email,
                        False
                    )
                    
                    # Check that file-based was tried first
                    mock_file_based.assert_called_once()
                    
                    # Check that simple text was used as fallback
                    mock_simple.assert_called_once()
                    
                    assert result == "simple script", "Should return fallback result"
            
        except ImportError:
            pytest.skip("macOS Outlook service not available")
    
    def test_line_break_preservation_in_approaches(self):
        """Test that line breaks are preserved in different approaches."""
        try:
            from multichannel_messaging.services.outlook_macos import OutlookMacOSService
            
            service = OutlookMacOSService()
            
            test_content = "Line 1\n\nLine 3\nLine 4"
            
            # Test simple text approach
            simple_script = service._build_simple_text_email_script(
                "Test", test_content, "test@example.com", False
            )
            
            # Should use linefeed for line breaks
            linefeed_count = simple_script.count("linefeed")
            original_linebreak_count = test_content.count('\n')
            
            assert linefeed_count == original_linebreak_count, \
                f"Should have {original_linebreak_count} linefeeds, got {linefeed_count}"
            
        except ImportError:
            pytest.skip("macOS Outlook service not available")
    
    def test_content_length_limits(self):
        """Test that content length limits are enforced."""
        try:
            from multichannel_messaging.services.outlook_macos import OutlookMacOSService
            
            service = OutlookMacOSService()
            
            # Create very long content
            long_content = "A" * 15000  # Longer than 10000 char limit
            
            escaped = service._escape_for_applescript_ultra_safe(long_content)
            
            # Should be truncated
            assert len(escaped) <= 10003, "Should be truncated to limit + '...'"
            assert escaped.endswith("..."), "Should end with ellipsis when truncated"
            
        except ImportError:
            pytest.skip("macOS Outlook service not available")
    
    def test_special_character_handling(self):
        """Test handling of special characters that could break AppleScript."""
        try:
            from multichannel_messaging.services.outlook_macos import OutlookMacOSService
            
            service = OutlookMacOSService()
            
            # Test various special characters
            special_chars = [
                'Text with "double quotes"',
                "Text with 'single quotes'",
                'Text with \\ backslashes',
                'Text with \t tabs',
                'Text with \x00 null chars',
                'Text with \x01 control chars',
            ]
            
            for test_text in special_chars:
                escaped = service._escape_for_applescript_ultra_safe(test_text)
                
                # Should not contain problematic characters
                assert '"' not in escaped, f"Should not contain double quotes: {escaped}"
                assert '\\' not in escaped, f"Should not contain backslashes: {escaped}"
                assert '\x00' not in escaped, f"Should not contain null chars: {escaped}"
                assert '\x01' not in escaped, f"Should not contain control chars: {escaped}"
                
                # Should still be readable
                assert len(escaped) > 0, "Should not be empty after escaping"
                assert "Text with" in escaped, "Should preserve main content"
            
        except ImportError:
            pytest.skip("macOS Outlook service not available")


class TestEmailFormattingIntegration:
    """Integration tests for email formatting with real templates."""
    
    def test_complete_email_formatting_workflow(self):
        """Test complete workflow from template to AppleScript."""
        try:
            from multichannel_messaging.services.outlook_macos import OutlookMacOSService
            from multichannel_messaging.core.models import MessageTemplate, Customer
            
            # Create template with complex formatting
            template = MessageTemplate(
                id="integration_test",
                name="Integration Test Template",
                channels=["email"],
                subject="Welcome {name} to our platform!",
                content="""Dear {name},

Welcome to our comprehensive communication platform! We're excited to have {company} join our community.

Our platform offers:

• Professional email templates
• Multi-channel messaging
• Real-time analytics
• 24/7 support

We look forward to helping you achieve your communication goals.

Best regards,
The CSC-Reach Team

P.S. Questions? Just reply to this email!""",
                variables=["name", "company"]
            )
            
            customer = Customer(
                name="John Doe",
                company="Acme Corp",
                phone="+1-555-0123",
                email="john@acme.com"
            )
            
            # Render template
            rendered = template.render(customer)
            
            # Generate AppleScript
            service = OutlookMacOSService()
            script = service._build_email_script(
                subject=rendered.get('subject', ''),
                content=rendered.get('content', ''),
                email=customer.email,
                send=False
            )
            
            # Verify the script contains expected elements
            assert "John Doe" in script, "Should contain customer name"
            assert "Acme Corp" in script, "Should contain company name"
            assert "john@acme.com" in script, "Should contain email address"
            assert "Welcome John Doe to our platform!" in script, "Should contain rendered subject"
            
            # Verify line break handling
            original_content = rendered.get('content', '')
            line_break_count = original_content.count('\n')
            
            # Should have some mechanism for line breaks
            has_line_breaks = (
                "linefeed" in script or  # Simple text approach
                "POSIX file" in script   # File-based approach
            )
            assert has_line_breaks, "Should use some line break mechanism"
            
        except ImportError:
            pytest.skip("macOS Outlook service not available")


if __name__ == "__main__":
    pytest.main([__file__])
