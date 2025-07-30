#!/usr/bin/env python3
"""
Debug script to test translation directly.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def debug_direct_translate():
    """Debug translation directly."""
    from multichannel_messaging.core.i18n_manager import I18nManager
    
    print("Debug Direct Translation")
    print("=" * 50)
    
    # Create a new instance
    i18n_manager = I18nManager()
    
    # Test each language
    for lang in ["en", "es", "pt"]:
        print(f"\n--- Testing {lang.upper()} ---")
        
        # Set language
        success = i18n_manager.set_language(lang)
        print(f"Set language success: {success}")
        print(f"Current language: {i18n_manager.get_current_language()}")
        
        # Test direct translation method
        translation = i18n_manager.translate("app_title")
        print(f"Direct translate('app_title'): {translation}")
        
        translation = i18n_manager.translate("menu_file")
        print(f"Direct translate('menu_file'): {translation}")
        
        translation = i18n_manager.translate("import_csv")
        print(f"Direct translate('import_csv'): {translation}")
        
        # Check what's in the translations dict for this language
        lang_translations = i18n_manager.translations.get(lang, {})
        print(f"Direct from dict - app_title: {lang_translations.get('app_title', '[MISSING]')}")
        print(f"Direct from dict - menu_file: {lang_translations.get('menu_file', '[MISSING]')}")

if __name__ == "__main__":
    debug_direct_translate()