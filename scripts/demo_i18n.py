#!/usr/bin/env python3
"""
Demonstration script for the enhanced CSC-Reach i18n system.
Shows dynamic language switching, pluralization, context-aware translations,
and locale-specific formatting.
"""

import sys
from pathlib import Path
from datetime import datetime, date

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from multichannel_messaging.core.i18n_manager import get_i18n_manager
from multichannel_messaging.core.locale_formatter import get_locale_formatter
from multichannel_messaging.core.rtl_support import get_rtl_support
from multichannel_messaging.utils.translation_manager import TranslationManager


def demo_basic_translations():
    """Demonstrate basic translation functionality."""
    print("=== Basic Translation Demo ===")
    
    i18n = get_i18n_manager()
    
    # Test different languages
    for lang in ['en', 'es', 'pt']:
        i18n.set_language(lang)
        print(f"\n{lang.upper()}:")
        print(f"  App Title: {i18n.translate('app_title')}")
        print(f"  Send Messages: {i18n.translate('send_messages')}")
        print(f"  Settings: {i18n.translate('settings')}")


def demo_pluralization():
    """Demonstrate pluralization support."""
    print("\n=== Pluralization Demo ===")
    
    i18n = get_i18n_manager()
    
    for lang in ['en', 'es', 'pt']:
        i18n.set_language(lang)
        print(f"\n{lang.upper()}:")
        
        for count in [0, 1, 2, 5]:
            result = i18n.translate_plural('recipient_count', count)
            print(f"  {result}")


def demo_context_aware():
    """Demonstrate context-aware translations."""
    print("\n=== Context-Aware Translation Demo ===")
    
    i18n = get_i18n_manager()
    
    for lang in ['en', 'es', 'pt']:
        i18n.set_language(lang)
        print(f"\n{lang.upper()}:")
        
        # Same key, different contexts
        button_save = i18n.translate_context('save', 'button')
        menu_save = i18n.translate_context('save', 'menu')
        
        print(f"  Button Save: {button_save}")
        print(f"  Menu Save: {menu_save}")


def demo_locale_formatting():
    """Demonstrate locale-specific formatting."""
    print("\n=== Locale-Specific Formatting Demo ===")
    
    i18n = get_i18n_manager()
    formatter = get_locale_formatter()
    
    test_date = date(2024, 3, 15)
    test_number = 1234.56
    test_currency = 1234.56
    test_phone = "1234567890"
    
    for lang in ['en', 'es', 'pt']:
        i18n.set_language(lang)
        print(f"\n{lang.upper()}:")
        
        print(f"  Date: {formatter.format_date(test_date)}")
        print(f"  Number: {formatter.format_number(test_number)}")
        print(f"  Currency: {formatter.format_currency(test_currency)}")
        print(f"  Phone: {formatter.format_phone(test_phone)}")
        print(f"  Percentage: {formatter.format_percentage(0.75)}")
        print(f"  File Size: {formatter.format_file_size(1572864)}")  # 1.5 MB


def demo_rtl_support():
    """Demonstrate RTL language support framework."""
    print("\n=== RTL Support Demo ===")
    
    rtl = get_rtl_support()
    
    print("RTL Languages:")
    for lang_code, lang_name in rtl.get_supported_rtl_languages().items():
        print(f"  {lang_code}: {lang_name}")
        print(f"    Is RTL: {rtl.is_rtl(lang_code)}")
        print(f"    Text Direction: {rtl.format_text_direction('Hello World', lang_code)}")


def demo_translation_management():
    """Demonstrate translation management tools."""
    print("\n=== Translation Management Demo ===")
    
    manager = TranslationManager()
    
    # Generate translation report
    report = manager.generate_translation_report()
    
    print(f"Translation Report Summary:")
    print(f"  Total Languages: {report['summary']['total_languages']}")
    print(f"  Total Keys: {report['summary']['total_keys']}")
    print(f"  Overall Completion: {report['summary']['overall_completion']:.1f}%")
    
    print(f"\nLanguage Details:")
    for lang_code, lang_data in report['languages'].items():
        print(f"  {lang_code} ({lang_data['name']}):")
        print(f"    Completion: {lang_data['completion_percentage']:.1f}%")
        print(f"    Missing Keys: {lang_data['missing_keys']}")
        print(f"    Validation Issues: {lang_data['issue_count']}")


def demo_dynamic_switching():
    """Demonstrate dynamic language switching with callbacks."""
    print("\n=== Dynamic Language Switching Demo ===")
    
    i18n = get_i18n_manager()
    
    # Register callback
    def language_change_callback(new_lang):
        print(f"  Language changed to: {new_lang}")
    
    i18n.register_language_change_callback(language_change_callback)
    
    print("Switching languages (with callback):")
    for lang in ['en', 'es', 'pt', 'en']:
        i18n.set_language(lang)
        print(f"    Current: {i18n.translate('language')} ({lang})")
    
    # Unregister callback
    i18n.unregister_language_change_callback(language_change_callback)


def demo_error_handling():
    """Demonstrate error handling."""
    print("\n=== Error Handling Demo ===")
    
    i18n = get_i18n_manager()
    formatter = get_locale_formatter()
    
    print("Testing error handling:")
    
    # Test invalid translation keys
    print(f"  Invalid key: '{i18n.translate('nonexistent_key')}'")
    print(f"  Empty key: '{i18n.translate('')}'")
    print(f"  None key: '{i18n.translate(None)}'")
    
    # Test invalid formatting
    print(f"  Invalid date: '{formatter.format_date('invalid')}'")
    print(f"  Invalid number: '{formatter.format_number('not_a_number')}'")


def main():
    """Run all demonstrations."""
    print("CSC-Reach Enhanced I18n System Demonstration")
    print("=" * 50)
    
    try:
        demo_basic_translations()
        demo_pluralization()
        demo_context_aware()
        demo_locale_formatting()
        demo_rtl_support()
        demo_translation_management()
        demo_dynamic_switching()
        demo_error_handling()
        
        print("\n" + "=" * 50)
        print("Demonstration completed successfully!")
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()