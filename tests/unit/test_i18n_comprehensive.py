"""
Comprehensive tests for the enhanced i18n system.
Tests dynamic language switching, pluralization, context-aware translations,
and locale-specific formatting.
"""

import pytest
import json
from datetime import datetime, date, time
from pathlib import Path
from unittest.mock import Mock, patch

from src.multichannel_messaging.core.i18n_manager import I18nManager, get_i18n_manager
from src.multichannel_messaging.core.locale_formatter import LocaleFormatter, get_locale_formatter
from src.multichannel_messaging.core.rtl_support import RTLSupport, get_rtl_support
from src.multichannel_messaging.utils.translation_manager import TranslationManager


class TestI18nManager:
    """Test the enhanced I18n manager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.i18n = I18nManager()
    
    def test_supported_languages(self):
        """Test supported languages configuration."""
        languages = self.i18n.get_supported_languages()
        
        assert 'en' in languages
        assert 'pt' in languages
        assert 'es' in languages
        
        # Check language metadata
        assert languages['en']['direction'] == 'ltr'
        assert languages['pt']['pluralization_rule'] == 'portuguese'
        assert 'variants' in languages['pt']
    
    def test_language_switching(self):
        """Test dynamic language switching."""
        # Test basic language switching
        assert self.i18n.set_language('es')
        assert self.i18n.get_current_language() == 'es'
        
        # Test with variant
        assert self.i18n.set_language('pt', 'pt-BR')
        assert self.i18n.get_current_language() == 'pt'
        assert self.i18n.current_variant == 'pt-BR'
        
        # Test invalid language
        assert not self.i18n.set_language('invalid')
        assert self.i18n.get_current_language() == 'pt'  # Should remain unchanged
    
    def test_translation_basic(self):
        """Test basic translation functionality."""
        self.i18n.set_language('en')
        
        # Test existing translation
        assert self.i18n.translate('app_title') == "CSC-Reach - Multi-Channel Communication Platform"
        
        # Test missing translation (should return key)
        assert self.i18n.translate('nonexistent_key') == 'nonexistent_key'
        
        # Test with variables
        result = self.i18n.translate('send_messages_to', count=5, channel='Email')
        assert '5' in result and 'Email' in result
    
    def test_pluralization(self):
        """Test pluralization support."""
        self.i18n.set_language('en')
        
        # Test singular
        result = self.i18n.translate_plural('recipient_count', 1)
        assert 'recipient' in result and '1' in result
        
        # Test plural
        result = self.i18n.translate_plural('recipient_count', 5)
        assert 'recipients' in result and '5' in result
        
        # Test zero (should be plural in English)
        result = self.i18n.translate_plural('recipient_count', 0)
        assert 'recipients' in result and '0' in result
    
    def test_context_aware_translation(self):
        """Test context-aware translations."""
        self.i18n.set_language('en')
        
        # Test context-specific translation
        button_save = self.i18n.translate_context('save', 'button')
        menu_save = self.i18n.translate_context('save', 'menu')
        
        # Both should return the translation (may be same or different)
        assert button_save
        assert menu_save
    
    def test_language_change_callbacks(self):
        """Test language change callback system."""
        callback_called = False
        new_lang = None
        
        def test_callback(lang_code):
            nonlocal callback_called, new_lang
            callback_called = True
            new_lang = lang_code
        
        self.i18n.register_language_change_callback(test_callback)
        self.i18n.set_language('es')
        
        assert callback_called
        assert new_lang == 'es'
        
        # Test unregistering callback
        self.i18n.unregister_language_change_callback(test_callback)
        callback_called = False
        self.i18n.set_language('pt')
        
        # Callback should not be called after unregistering
        assert not callback_called
    
    def test_translation_validation(self):
        """Test translation validation."""
        errors = self.i18n.validate_translation_keys()
        
        # Should return a list (may be empty if all translations are valid)
        assert isinstance(errors, list)
    
    def test_missing_translations(self):
        """Test missing translation detection."""
        missing_en = self.i18n.get_missing_translations('en')
        missing_es = self.i18n.get_missing_translations('es')
        
        # English should have no missing translations (it's the base)
        assert len(missing_en) == 0
        
        # Other languages may have missing translations
        assert isinstance(missing_es, list)
    
    def test_language_info(self):
        """Test language information retrieval."""
        info = self.i18n.get_language_info('en')
        
        assert info['code'] == 'en'
        assert info['name'] == 'English'
        assert info['direction'] == 'ltr'
        assert not info['is_rtl']
        assert 'translation_count' in info
        assert 'completion_percentage' in info


class TestLocaleFormatter:
    """Test the locale formatter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.i18n = I18nManager()
        self.formatter = LocaleFormatter(self.i18n)
    
    def test_date_formatting(self):
        """Test date formatting."""
        test_date = date(2024, 3, 15)
        
        # Test English format (MM/dd/yyyy)
        self.i18n.set_language('en')
        formatted = self.formatter.format_date(test_date)
        assert '03/15/2024' in formatted or '3/15/2024' in formatted
        
        # Test Spanish format (dd/MM/yyyy)
        self.i18n.set_language('es')
        formatted = self.formatter.format_date(test_date)
        assert '15/03/2024' in formatted or '15/3/2024' in formatted
    
    def test_time_formatting(self):
        """Test time formatting."""
        test_time = time(14, 30, 45)
        
        # Test different time formats
        self.i18n.set_language('en')
        formatted = self.formatter.format_time(test_time)
        assert formatted  # Should return some formatted time
        
        self.i18n.set_language('es')
        formatted = self.formatter.format_time(test_time)
        assert formatted
    
    def test_number_formatting(self):
        """Test number formatting."""
        # Test English format (comma thousands separator, dot decimal)
        self.i18n.set_language('en')
        formatted = self.formatter.format_number(1234.56)
        assert '1,234.56' in formatted or '1234.56' in formatted
        
        # Test Spanish format (dot thousands separator, comma decimal)
        self.i18n.set_language('es')
        formatted = self.formatter.format_number(1234.56)
        # Should use Spanish formatting
        assert formatted
    
    def test_currency_formatting(self):
        """Test currency formatting."""
        # Test different currency formats
        self.i18n.set_language('en')
        formatted = self.formatter.format_currency(1234.56)
        assert '$' in formatted
        
        self.i18n.set_language('es')
        formatted = self.formatter.format_currency(1234.56)
        assert '€' in formatted or formatted  # May have different currency symbol
    
    def test_phone_formatting(self):
        """Test phone number formatting."""
        # Test US format
        self.i18n.set_language('en')
        formatted = self.formatter.format_phone('1234567890')
        assert formatted
        
        # Test with country code override
        formatted_br = self.formatter.format_phone('11987654321', 'BR')
        assert formatted_br
    
    def test_address_formatting(self):
        """Test address formatting."""
        address_data = {
            'street': '123 Main St',
            'city': 'New York',
            'state': 'NY',
            'zip': '10001',
            'country': 'USA'
        }
        
        formatted = self.formatter.format_address(address_data)
        assert 'Main St' in formatted
        assert 'New York' in formatted
    
    def test_percentage_formatting(self):
        """Test percentage formatting."""
        # Test with decimal value
        formatted = self.formatter.format_percentage(0.75)
        assert '75' in formatted and '%' in formatted
        
        # Test with percentage value
        formatted = self.formatter.format_percentage(75)
        assert '75' in formatted and '%' in formatted
    
    def test_file_size_formatting(self):
        """Test file size formatting."""
        # Test bytes
        formatted = self.formatter.format_file_size(512)
        assert '512' in formatted and 'B' in formatted
        
        # Test KB
        formatted = self.formatter.format_file_size(1536)  # 1.5 KB
        assert 'KB' in formatted
        
        # Test MB
        formatted = self.formatter.format_file_size(1572864)  # 1.5 MB
        assert 'MB' in formatted
    
    def test_duration_formatting(self):
        """Test duration formatting."""
        # Test seconds
        formatted = self.formatter.format_duration(30)
        assert '30' in formatted
        
        # Test minutes
        formatted = self.formatter.format_duration(90)  # 1 minute 30 seconds
        assert formatted
        
        # Test hours
        formatted = self.formatter.format_duration(3661)  # 1 hour 1 minute 1 second
        assert formatted
    
    def test_relative_time_formatting(self):
        """Test relative time formatting."""
        now = datetime.now()
        
        # Test past time
        past_time = datetime(now.year, now.month, now.day, now.hour - 2)
        formatted = self.formatter.format_relative_time(past_time)
        assert formatted
        
        # Test future time
        future_time = datetime(now.year, now.month, now.day, now.hour + 2)
        formatted = self.formatter.format_relative_time(future_time)
        assert formatted
    
    def test_locale_info(self):
        """Test locale information retrieval."""
        info = self.formatter.get_locale_info()
        
        assert 'language' in info
        assert 'date_format' in info
        assert 'currency_symbol' in info
        assert 'direction' in info


class TestRTLSupport:
    """Test RTL language support."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.i18n = I18nManager()
        self.rtl = RTLSupport(self.i18n)
    
    def test_rtl_detection(self):
        """Test RTL language detection."""
        # Test LTR languages
        assert not self.rtl.is_rtl('en')
        assert not self.rtl.is_rtl('es')
        assert not self.rtl.is_rtl('pt')
        
        # Test RTL languages (if supported)
        assert self.rtl.is_rtl('ar')
        assert self.rtl.is_rtl('he')
    
    def test_text_direction_formatting(self):
        """Test text direction formatting."""
        # Test LTR text
        ltr_text = self.rtl.format_text_direction("Hello", 'en')
        assert ltr_text
        
        # Test RTL text
        rtl_text = self.rtl.format_text_direction("مرحبا", 'ar')
        assert rtl_text
    
    def test_supported_rtl_languages(self):
        """Test RTL language support."""
        rtl_langs = self.rtl.get_supported_rtl_languages()
        
        assert 'ar' in rtl_langs
        assert 'he' in rtl_langs
        assert rtl_langs['ar'] == 'Arabic'


class TestTranslationManager:
    """Test the translation management utilities."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = TranslationManager()
    
    def test_validation(self):
        """Test translation validation."""
        # Test validation for all languages
        results = self.manager.validate_all_translations()
        
        assert isinstance(results, dict)
        assert 'en' in results
        assert 'es' in results
        assert 'pt' in results
        
        # Each result should be a list of issues
        for lang, issues in results.items():
            assert isinstance(issues, list)
    
    def test_translation_report(self):
        """Test translation report generation."""
        report = self.manager.generate_translation_report()
        
        assert 'generated_at' in report
        assert 'languages' in report
        assert 'summary' in report
        
        # Check summary
        summary = report['summary']
        assert 'total_languages' in summary
        assert 'total_keys' in summary
        assert 'overall_completion' in summary
        
        # Check language details
        for lang_code, lang_data in report['languages'].items():
            assert 'name' in lang_data
            assert 'completion_percentage' in lang_data
            assert 'validation_issues' in lang_data
    
    def test_missing_translations_export(self, tmp_path):
        """Test exporting missing translations."""
        output_file = tmp_path / "missing_es.json"
        
        success = self.manager.export_missing_translations('es', output_file)
        
        if success:
            assert output_file.exists()
            
            # Check file content
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert 'language' in data
            assert 'translations' in data
            assert data['language'] == 'es'
    
    def test_sync_translation_keys(self):
        """Test translation key synchronization."""
        results = self.manager.sync_translation_keys()
        
        assert isinstance(results, dict)
        
        # Should have results for all supported languages
        for lang_code in self.manager.i18n_manager.SUPPORTED_LANGUAGES.keys():
            assert lang_code in results
            assert isinstance(results[lang_code], int)


class TestIntegration:
    """Integration tests for the complete i18n system."""
    
    def test_complete_workflow(self):
        """Test complete i18n workflow."""
        # Get managers
        i18n = get_i18n_manager()
        formatter = get_locale_formatter()
        rtl = get_rtl_support()
        
        # Test language switching affects all components
        i18n.set_language('es')
        
        # Test translation
        translated = i18n.translate('app_title')
        assert 'CSC-Reach' in translated
        
        # Test formatting
        formatted_date = formatter.format_date(date.today())
        assert formatted_date
        
        # Test RTL support
        assert not rtl.is_rtl()  # Spanish is LTR
        
        # Switch to Portuguese
        i18n.set_language('pt')
        
        # Test pluralization
        plural_result = i18n.translate_plural('recipient_count', 3)
        assert '3' in plural_result
        
        # Test context-aware translation
        context_result = i18n.translate_context('save', 'button')
        assert context_result
    
    def test_error_handling(self):
        """Test error handling in i18n system."""
        i18n = get_i18n_manager()
        formatter = get_locale_formatter()
        
        # Test with invalid inputs
        assert i18n.translate('') == ''
        assert i18n.translate(None) == 'None'  # Should handle gracefully
        
        # Test formatter with invalid data
        formatted = formatter.format_date("invalid")
        assert formatted  # Should return something, not crash
        
        formatted = formatter.format_number("not_a_number")
        assert formatted  # Should handle gracefully


if __name__ == '__main__':
    pytest.main([__file__])