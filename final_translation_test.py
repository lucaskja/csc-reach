#!/usr/bin/env python3
"""
Final comprehensive test of the translation system.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_translations_comprehensive():
    """Comprehensive test of the translation system."""
    from multichannel_messaging.core.i18n_manager import I18nManager
    
    print("CSC-Reach Translation System - Final Test")
    print("=" * 60)
    
    # Create manager instance
    i18n_manager = I18nManager()
    
    # Test key UI elements for each language
    ui_test_cases = [
        # Menu items
        ("menu_file", "File menu"),
        ("menu_tools", "Tools menu"),
        ("menu_help", "Help menu"),
        ("menu_templates", "Templates menu"),
        
        # Toolbar buttons
        ("import_csv", "Import CSV button"),
        ("send_messages", "Send Messages button"),
        ("create_draft", "Create Draft button"),
        ("stop_sending", "Stop Sending button"),
        
        # Main sections
        ("recipients", "Recipients section"),
        ("message_template", "Message Template section"),
        ("email_content_group", "Email Content group"),
        ("whatsapp_content_group", "WhatsApp Content group"),
        ("sending_progress", "Sending Progress section"),
        
        # Common buttons
        ("select_all", "Select All button"),
        ("select_none", "Select None button"),
        ("library", "Library button"),
        ("save", "Save button"),
        ("preview_message", "Preview Message button"),
        
        # Status messages
        ("ready_to_send", "Ready to send status"),
        ("email_ready_status", "Email ready status"),
        ("whatsapp_business_not_configured_status", "WhatsApp Business not configured"),
        ("whatsapp_web_not_configured_status", "WhatsApp Web not configured"),
    ]
    
    # Test each language
    languages = [
        ("en", "English"),
        ("es", "Spanish"),
        ("pt", "Portuguese")
    ]
    
    for lang_code, lang_name in languages:
        print(f"\n{lang_name.upper()} TRANSLATIONS:")
        print("-" * 40)
        
        # Set language
        success = i18n_manager.set_language(lang_code)
        if not success:
            print(f"❌ Failed to set language to {lang_code}")
            continue
        
        print(f"✅ Language set to: {i18n_manager.get_current_language()}")
        
        # Test each UI element
        all_good = True
        for key, description in ui_test_cases:
            translation = i18n_manager.translate(key)
            
            # Check if translation is different from key (indicating it was translated)
            if translation == key:
                print(f"❌ {description}: [NOT TRANSLATED] ({key})")
                all_good = False
            else:
                print(f"✅ {description}: {translation}")
        
        # Test parameterized translations
        print(f"\nParameterized translations:")
        param_tests = [
            ("characters_count", {"count": 150}, "Character count"),
            ("quota_status", {"current": 25, "total": 100}, "Quota status"),
            ("send_messages_to", {"count": 5, "channel": "Email"}, "Send confirmation"),
        ]
        
        for key, params, description in param_tests:
            try:
                translation = i18n_manager.translate(key, **params)
                print(f"✅ {description}: {translation}")
            except Exception as e:
                print(f"❌ {description}: ERROR - {e}")
                all_good = False
        
        if all_good:
            print(f"\n🎉 All translations for {lang_name} are working correctly!")
        else:
            print(f"\n⚠️  Some translations for {lang_name} need attention.")
    
    print(f"\n{'=' * 60}")
    print("Translation system test completed!")
    print("The UI should now be fully translatable to Spanish and Portuguese.")
    print("=" * 60)

if __name__ == "__main__":
    test_translations_comprehensive()