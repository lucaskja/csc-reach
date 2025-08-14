#!/usr/bin/env python3
"""
Fixed debug script to check translation loading.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def debug_translations_fixed():
    """Debug translation loading properly."""
    from multichannel_messaging.core.i18n_manager import I18nManager, tr
    
    print("Debug Translation Loading (Fixed)")
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
        
        # Check if translations are loaded for this language
        lang_translations = i18n_manager.translations.get(lang, {})
        print(f"Number of translations loaded for {lang}: {len(lang_translations)}")
        
        # Test a few key translations using the tr function
        test_keys = ["app_title", "menu_file", "import_csv", "recipients"]
        for key in test_keys:
            translation = tr(key)
            print(f"  {key}: {translation}")
        
        # Test parameterized translation
        char_count = tr("characters_count", count=150)
        print(f"  characters_count: {char_count}")

if __name__ == "__main__":
    debug_translations_fixed()