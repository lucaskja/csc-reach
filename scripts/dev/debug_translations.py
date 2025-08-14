#!/usr/bin/env python3
"""
Debug script to check translation loading.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def debug_translations():
    """Debug translation loading."""
    from multichannel_messaging.core.i18n_manager import I18nManager
    
    print("Debug Translation Loading")
    print("=" * 50)
    
    i18n_manager = I18nManager()
    
    # Check supported languages
    supported = i18n_manager.get_supported_languages()
    print(f"Supported languages: {list(supported.keys())}")
    
    # Check current language
    current = i18n_manager.get_current_language()
    print(f"Current language: {current}")
    
    # Test each language
    for lang in ["en", "es", "pt"]:
        print(f"\n--- Testing {lang.upper()} ---")
        
        # Set language
        success = i18n_manager.set_language(lang)
        print(f"Set language success: {success}")
        
        # Check current language after setting
        current_after = i18n_manager.get_current_language()
        print(f"Current language after setting: {current_after}")
        
        # Check if translations are loaded
        translations = i18n_manager.translations
        print(f"Number of translations loaded: {len(translations)}")
        
        # Test a few key translations
        test_keys = ["app_title", "menu_file", "import_csv", "recipients"]
        for key in test_keys:
            value = translations.get(key, f"[MISSING: {key}]")
            print(f"  {key}: {value}")

if __name__ == "__main__":
    debug_translations()