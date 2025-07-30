#!/usr/bin/env python3
"""
Comprehensive test script to verify UI translations are working properly.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_translation_completeness():
    """Test that all languages have the same translation keys."""
    from multichannel_messaging.core.i18n_manager import I18nManager
    
    print("Testing Translation Completeness")
    print("=" * 50)
    
    i18n_manager = I18nManager()
    supported_languages = i18n_manager.get_supported_languages()
    
    # Get all translation keys from English (reference)
    i18n_manager.set_language("en")
    en_translations = i18n_manager.translations
    
    # Test each language
    for lang_code in supported_languages.keys():
        if lang_code == "en":
            continue
            
        print(f"\nTesting {lang_code.upper()} completeness:")
        print("-" * 30)
        
        i18n_manager.set_language(lang_code)
        lang_translations = i18n_manager.translations
        
        missing_keys = []
        for key in en_translations.keys():
            if key not in lang_translations:
                missing_keys.append(key)
        
        if missing_keys:
            print(f"❌ Missing {len(missing_keys)} translation keys:")
            for key in missing_keys[:10]:  # Show first 10
                print(f"   - {key}")
            if len(missing_keys) > 10:
                print(f"   ... and {len(missing_keys) - 10} more")
        else:
            print(f"✅ All {len(en_translations)} translation keys present")

def test_key_ui_translations():
    """Test key UI element translations."""
    from multichannel_messaging.core.i18n_manager import I18nManager, tr
    
    print("\n\nTesting Key UI Translations")
    print("=" * 50)
    
    i18n_manager = I18nManager()
    
    # Key UI elements that should be translated
    ui_elements = {
        "Menu Bar": [
            "menu_file", "menu_tools", "menu_help", "menu_templates"
        ],
        "Toolbar": [
            "import_csv", "send_messages", "create_draft", "stop_sending",
            "language", "send_via"
        ],
        "Main Sections": [
            "recipients", "message_template", "email_content_group", 
            "whatsapp_content_group", "sending_progress"
        ],
        "Buttons": [
            "select_all", "select_none", "library", "save", "preview_message"
        ],
        "Status": [
            "ready_to_send", "email_ready_status", 
            "whatsapp_business_not_configured_status", 
            "whatsapp_web_not_configured_status"
        ],
        "Labels": [
            "subject", "characters", "no_recipients_loaded", "recipients_loaded"
        ]
    }
    
    languages = ["en", "es", "pt"]
    
    for lang in languages:
        print(f"\n{lang.upper()} Translations:")
        print("-" * 20)
        
        i18n_manager.set_language(lang)
        
        for category, keys in ui_elements.items():
            print(f"\n{category}:")
            for key in keys:
                try:
                    if key == "characters":
                        translation = tr("characters")
                    elif key == "recipients_loaded":
                        translation = tr("recipients_loaded")
                    else:
                        translation = tr(key)
                    
                    # Check if translation is different from key (indicating it was translated)
                    if translation != key:
                        print(f"  ✅ {key}: {translation}")
                    else:
                        print(f"  ❌ {key}: [NOT TRANSLATED]")
                        
                except Exception as e:
                    print(f"  ❌ {key}: [ERROR: {e}]")

def test_parameterized_translations():
    """Test translations with parameters."""
    from multichannel_messaging.core.i18n_manager import I18nManager, tr
    
    print("\n\nTesting Parameterized Translations")
    print("=" * 50)
    
    i18n_manager = I18nManager()
    
    test_cases = [
        ("characters_count", {"count": 150}),
        ("quota_status", {"current": 25, "total": 100}),
        ("send_messages_to", {"count": 5, "channel": "Email"}),
        ("template_saved_success", {"name": "Test Template"}),
        ("csv_errors_found", {"count": 3}),
        ("loaded_customers", {"count": 10})
    ]
    
    for lang in ["en", "es", "pt"]:
        print(f"\n{lang.upper()} Parameterized:")
        print("-" * 20)
        
        i18n_manager.set_language(lang)
        
        for key, params in test_cases:
            try:
                translation = tr(key, **params)
                print(f"  ✅ {key}: {translation}")
            except Exception as e:
                print(f"  ❌ {key}: [ERROR: {e}]")

if __name__ == "__main__":
    test_translation_completeness()
    test_key_ui_translations()
    test_parameterized_translations()
    
    print("\n\n" + "=" * 50)
    print("Translation testing complete!")
    print("=" * 50)