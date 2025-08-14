#!/usr/bin/env python3
"""
Test script to verify dialog translations are working correctly.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from multichannel_messaging.core.i18n_manager import I18nManager, tr

def test_translations():
    """Test that all new translations are working."""
    
    print("Testing Dialog Translations")
    print("=" * 50)
    
    # Test different languages
    languages = ['en', 'pt', 'es']
    
    # Test keys that should be translated
    test_keys = [
        'message_analytics_logs',
        'whatsapp_business_api_configuration',
        'clear_credentials',
        'save_settings',
        'whatsapp_web_automation_settings',
        'important_warnings',
        'service_status',
        'risk_acknowledgment',
        'test_service',
        'save_configuration'
    ]
    
    for lang in languages:
        print(f"\n--- Testing {lang.upper()} translations ---")
        
        # Initialize i18n manager for this language
        i18n = I18nManager()
        i18n.set_language(lang)
        
        for key in test_keys:
            translation = i18n.tr(key)
            print(f"{key}: {translation}")
            
            # Check if translation is missing (returns the key itself)
            if translation == key:
                print(f"  ⚠️  WARNING: Missing translation for '{key}' in {lang}")
            else:
                print(f"  ✅ OK")
    
    print("\n" + "=" * 50)
    print("Translation test completed!")

if __name__ == "__main__":
    test_translations()
