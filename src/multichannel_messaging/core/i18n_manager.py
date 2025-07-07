"""
Internationalization (i18n) manager for CSC-Reach.
Handles multi-language support for English, Portuguese, and Spanish.
"""

import os
import sys
import json
from typing import Dict, Optional, List
from pathlib import Path
from PySide6.QtCore import QTranslator, QCoreApplication, QLocale

from ..utils.logger import get_logger
from ..utils.platform_utils import get_config_dir

logger = get_logger(__name__)


class I18nManager:
    """
    Manages internationalization for the application.
    
    Supports:
    - English (en) - Base language
    - Portuguese (pt) - Brazilian Portuguese
    - Spanish (es) - Spanish
    """
    
    # Supported languages
    SUPPORTED_LANGUAGES = {
        'en': {'name': 'English', 'native': 'English'},
        'pt': {'name': 'Portuguese', 'native': 'Português'},
        'es': {'name': 'Spanish', 'native': 'Español'}
    }
    
    def __init__(self):
        """Initialize the i18n manager."""
        self.current_language = 'en'  # Default to English
        self.translator = QTranslator()
        self.translations: Dict[str, Dict[str, str]] = {}
        
        # Paths
        self.config_dir = get_config_dir()
        
        # Handle PyInstaller bundle path resolution
        if getattr(sys, 'frozen', False):
            # Running in PyInstaller bundle
            bundle_dir = Path(sys._MEIPASS)
            self.translations_dir = bundle_dir / "multichannel_messaging" / "localization"
        else:
            # Running in development
            self.translations_dir = Path(__file__).parent.parent / "localization"
            
        self.config_file = self.config_dir / "language_config.json"
        
        # Load translations and configuration
        self._load_translations()
        self._load_language_config()
        
        logger.info(f"I18n manager initialized with language: {self.current_language}")
    
    def _load_translations(self):
        """Load all translation files."""
        try:
            logger.info(f"Loading translations from: {self.translations_dir}")
            logger.info(f"Translations directory exists: {self.translations_dir.exists()}")
            
            # Ensure translations directory exists (only in development)
            if not getattr(sys, 'frozen', False):
                self.translations_dir.mkdir(exist_ok=True)
            
            # Load translations for each supported language
            for lang_code in self.SUPPORTED_LANGUAGES.keys():
                translation_file = self.translations_dir / f"{lang_code}.json"
                logger.info(f"Looking for translation file: {translation_file}")
                
                if translation_file.exists():
                    with open(translation_file, 'r', encoding='utf-8') as f:
                        self.translations[lang_code] = json.load(f)
                    logger.info(f"Loaded translations for {lang_code}: {len(self.translations[lang_code])} keys")
                else:
                    logger.warning(f"Translation file not found: {translation_file}")
                    # Create empty translation file (only in development)
                    if not getattr(sys, 'frozen', False):
                        self.translations[lang_code] = {}
                        self._save_translation_file(lang_code)
                        logger.info(f"Created empty translation file for {lang_code}")
                    else:
                        # In bundle, use empty translations
                        self.translations[lang_code] = {}
            
            # Ensure base English translations exist
            self._ensure_base_translations()
            
        except Exception as e:
            logger.error(f"Failed to load translations: {e}")
            # Fallback to empty translations
            for lang_code in self.SUPPORTED_LANGUAGES.keys():
                self.translations[lang_code] = {}
    
    def _ensure_base_translations(self):
        """Ensure base English translations exist."""
        base_translations = {
            # Main Window
            "app_title": "CSC-Reach - Multi-Channel Communication Platform",
            "menu_file": "File",
            "menu_tools": "Tools",
            "menu_help": "Help",
            "import_csv": "Import CSV",
            "send_via": "Send via:",
            "send_messages": "Send Messages",
            "send_emails": "Send Emails",
            "send_whatsapp": "Send WhatsApp",
            "create_draft": "Create Draft",
            "preview_message": "Preview Message",
            
            # Channels
            "email_only": "Email Only",
            "whatsapp_business_api": "WhatsApp Business API",
            "whatsapp_web": "WhatsApp Web",
            "email_whatsapp_business": "Email + WhatsApp Business",
            "email_whatsapp_web": "Email + WhatsApp Web",
            
            # Status
            "email_ready": "Email: Ready",
            "email_not_ready": "Email: Not ready",
            "whatsapp_business_ready": "WhatsApp Business: Ready",
            "whatsapp_business_not_configured": "WhatsApp Business: Not configured",
            "whatsapp_web_ready": "WhatsApp Web: Ready",
            "whatsapp_web_not_configured": "WhatsApp Web: Not configured",
            
            # Recipients
            "recipients": "Recipients",
            "no_recipients_loaded": "No recipients loaded",
            "recipients_loaded": "recipients loaded",
            
            # Template
            "message_template": "Message Template",
            "email_content": "Email Content",
            "subject": "Subject:",
            "content": "Content:",
            "whatsapp_content": "WhatsApp Content",
            "whatsapp_message": "WhatsApp Message:",
            "characters": "Characters:",
            
            # Buttons
            "ok": "OK",
            "cancel": "Cancel",
            "save": "Save",
            "test": "Test",
            "close": "Close",
            "yes": "Yes",
            "no": "No",
            
            # Messages
            "no_recipients": "No Recipients",
            "please_import_csv": "Please import a CSV file first.",
            "please_select_recipients": "Please select at least one recipient.",
            "confirm_sending": "Confirm Sending",
            "send_messages_to": "Send messages to {count} recipients via {channel}?",
            
            # Settings
            "settings": "Settings",
            "language": "Language",
            "select_language": "Select Language:",
            "whatsapp_business_settings": "WhatsApp Business API Settings...",
            "whatsapp_web_settings": "WhatsApp Web Settings...",
            "test_whatsapp_business": "Test WhatsApp Business API",
            "test_whatsapp_web": "Test WhatsApp Web Service",
            
            # Default template
            "default_template_subject": "Welcome to our service, {name}!",
            "default_template_content": """Dear {name},

Thank you for your interest in our services. We're excited to have {company} join our community!

We'll be in touch soon with more information about how we can help your business grow.

Best regards,
The Team""",
            "default_template_whatsapp": """Hello {name}! 👋

Thank you for your interest in our services. We're excited to have {company} join our community!

We'll be in touch soon with more information.

Best regards! 🚀""",
        }
        
        # Update English translations with base translations
        if 'en' not in self.translations:
            self.translations['en'] = {}
        
        # Add missing translations
        updated = False
        for key, value in base_translations.items():
            if key not in self.translations['en']:
                self.translations['en'][key] = value
                updated = True
        
        if updated:
            self._save_translation_file('en')
            logger.info("Updated base English translations")
    
    def _load_language_config(self):
        """Load language configuration."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.current_language = config.get('language', 'en')
                    logger.info(f"Loaded language config: {self.current_language}")
            else:
                # Detect system language
                system_locale = QLocale.system().name()[:2]
                if system_locale in self.SUPPORTED_LANGUAGES:
                    self.current_language = system_locale
                    logger.info(f"Detected system language: {self.current_language}")
                else:
                    self.current_language = 'en'
                    logger.info("Using default language: en")
                
                self._save_language_config()
                
        except Exception as e:
            logger.error(f"Failed to load language config: {e}")
            self.current_language = 'en'
    
    def _save_language_config(self):
        """Save language configuration."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            config = {'language': self.current_language}
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to save language config: {e}")
    
    def _save_translation_file(self, lang_code: str):
        """Save translation file for a specific language."""
        try:
            translation_file = self.translations_dir / f"{lang_code}.json"
            
            with open(translation_file, 'w', encoding='utf-8') as f:
                json.dump(
                    self.translations.get(lang_code, {}), 
                    f, 
                    indent=2, 
                    ensure_ascii=False,
                    sort_keys=True
                )
                
        except Exception as e:
            logger.error(f"Failed to save translation file for {lang_code}: {e}")
    
    def get_supported_languages(self) -> Dict[str, Dict[str, str]]:
        """Get list of supported languages."""
        return self.SUPPORTED_LANGUAGES.copy()
    
    def get_current_language(self) -> str:
        """Get current language code."""
        return self.current_language
    
    def set_language(self, lang_code: str) -> bool:
        """
        Set current language.
        
        Args:
            lang_code: Language code (en, pt, es)
            
        Returns:
            True if successful, False otherwise
        """
        if lang_code not in self.SUPPORTED_LANGUAGES:
            logger.error(f"Unsupported language: {lang_code}")
            return False
        
        try:
            self.current_language = lang_code
            self._save_language_config()
            logger.info(f"Language changed to: {lang_code}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set language to {lang_code}: {e}")
            return False
    
    def translate(self, key: str, **kwargs) -> str:
        """
        Translate a key to current language.
        
        Args:
            key: Translation key
            **kwargs: Variables for string formatting
            
        Returns:
            Translated string
        """
        try:
            # Get translation for current language
            translation = self.translations.get(self.current_language, {}).get(key)
            
            # Fallback to English if not found
            if translation is None:
                translation = self.translations.get('en', {}).get(key)
            
            # Fallback to key if still not found
            if translation is None:
                logger.warning(f"Translation not found for key: {key}")
                translation = key
            
            # Format with variables if provided
            if kwargs:
                try:
                    translation = translation.format(**kwargs)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Failed to format translation for key {key}: {e}")
            
            return translation
            
        except Exception as e:
            logger.error(f"Translation error for key {key}: {e}")
            return key
    
    def tr(self, key: str, **kwargs) -> str:
        """Shorthand for translate method."""
        return self.translate(key, **kwargs)
    
    def add_translation(self, lang_code: str, key: str, value: str):
        """
        Add a translation for a specific language.
        
        Args:
            lang_code: Language code
            key: Translation key
            value: Translation value
        """
        if lang_code not in self.SUPPORTED_LANGUAGES:
            logger.error(f"Unsupported language: {lang_code}")
            return
        
        if lang_code not in self.translations:
            self.translations[lang_code] = {}
        
        self.translations[lang_code][key] = value
        self._save_translation_file(lang_code)
        logger.info(f"Added translation for {lang_code}.{key}")
    
    def get_missing_translations(self, lang_code: str) -> List[str]:
        """
        Get list of missing translations for a language.
        
        Args:
            lang_code: Language code to check
            
        Returns:
            List of missing translation keys
        """
        if lang_code not in self.SUPPORTED_LANGUAGES:
            return []
        
        english_keys = set(self.translations.get('en', {}).keys())
        target_keys = set(self.translations.get(lang_code, {}).keys())
        
        return list(english_keys - target_keys)


# Global i18n manager instance
_i18n_manager = None

def get_i18n_manager() -> I18nManager:
    """Get global i18n manager instance."""
    global _i18n_manager
    if _i18n_manager is None:
        _i18n_manager = I18nManager()
    return _i18n_manager

def tr(key: str, **kwargs) -> str:
    """Global translation function."""
    return get_i18n_manager().translate(key, **kwargs)
