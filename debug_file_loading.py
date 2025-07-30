#!/usr/bin/env python3
"""
Debug script to check file loading in detail.
"""

import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def debug_file_loading():
    """Debug file loading in detail."""
    from multichannel_messaging.core.i18n_manager import I18nManager
    
    print("Debug File Loading")
    print("=" * 50)
    
    # Check file paths
    translations_dir = Path(__file__).parent / "src" / "multichannel_messaging" / "localization"
    print(f"Translations directory: {translations_dir}")
    print(f"Directory exists: {translations_dir.exists()}")
    
    # Check each file
    for lang in ["en", "es", "pt"]:
        file_path = translations_dir / f"{lang}.json"
        print(f"\n{lang.upper()} file: {file_path}")
        print(f"File exists: {file_path.exists()}")
        
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"Keys in file: {len(data)}")
            print(f"Sample keys:")
            sample_keys = ["app_title", "menu_file", "import_csv"]
            for key in sample_keys:
                print(f"  {key}: {data.get(key, '[MISSING]')}")
    
    print("\n" + "=" * 50)
    print("Now testing I18nManager loading:")
    
    # Test I18nManager
    i18n_manager = I18nManager()
    
    for lang in ["en", "es", "pt"]:
        print(f"\n{lang.upper()} in I18nManager:")
        lang_data = i18n_manager.translations.get(lang, {})
        print(f"Keys loaded: {len(lang_data)}")
        sample_keys = ["app_title", "menu_file", "import_csv"]
        for key in sample_keys:
            print(f"  {key}: {lang_data.get(key, '[MISSING]')}")

if __name__ == "__main__":
    debug_file_loading()