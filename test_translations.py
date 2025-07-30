#!/usr/bin/env python3
"""
Test script to verify that all UI elements are properly translated.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from multichannel_messaging.core.i18n_manager import I18nManager, tr

def test_translations():
    """Test that all translation keys work properly."""
    print("Testing CSC-Reach Translation System")
    print("=" * 50)
    
    # Initialize i18n manager
    i18n_manager = I18nManager()
    
    # Test each language
    languages = ["en", "es", "pt"]
    
    for lang in languages:
        print(f"\nTesting {lang.upper()} translations:")
        print("-" * 30)
        
        # Set language
        success = i18n_manager.set_language(lang)
        if not success:
            print(f"❌ Failed to set language to {lang}")
            continue
        
        # Test key UI elements
        test_keys = [
            "app_title",
            "menu_file",
            "menu_tools", 
            "menu_help",
            "import_csv",
            "send_messages",
            "message_template",
            "email_content_group",
            "whatsapp_content_group",
            "recipients",
            "sending_progress",
            "select_all",
            "select_none",
            "template_library",
            "save_template",
            "preview_message",
            "characters_count",
            "ready_to_send",
            "email_ready_status",
            "whatsapp_business_not_configured_status",
            "quota_status"
        ]
        
        all_good = True
        for key in test_keys:
            try:
                if key == "characters_count":
                    translation = tr(key, count=150)
                elif key == "quota_status":
                    translation = tr(key, current=25, total=100)
                else:
                    translation = tr(key)
                
                if translation == key:  # Translation not found
                    print(f"❌ Missing translation for '{key}'")
                    all_good = False
                else:
                    print(f"✅ {key}: {translation}")
            except Exception as e:
                print(f"❌ Error translating '{key}': {e}")
                all_good = False
        
        if all_good:
            print(f"✅ All tested translations for {lang.upper()} are working!")
        else:
            print(f"❌ Some translations for {lang.upper()} are missing or broken!")

if __name__ == "__main__":
    test_translations()