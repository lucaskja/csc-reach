"""
Internationalization (i18n) manager for CSC-Reach.
Handles multi-language support for English, Portuguese, and Spanish.
"""

import os
import sys
import json
import re
from typing import Dict, Optional, List, Callable, Any, Union
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import QTranslator, QCoreApplication, QLocale, QObject, Signal

from ..utils.logger import get_logger
from ..utils.platform_utils import get_config_dir

logger = get_logger(__name__)


class I18nManager(QObject):
    """
    Enhanced internationalization manager for the application.
    
    Features:
    - Dynamic language switching without restart
    - Pluralization support for different language rules
    - Context-aware translations
    - Translation key validation and management
    - Right-to-left language support framework
    - Locale-specific formatting
    
    Supports:
    - English (en) - Base language
    - Portuguese (pt) - Brazilian Portuguese with European variant support
    - Spanish (es) - Spanish with regional considerations
    """
    
    # Signal emitted when language changes
    language_changed = Signal(str)
    
    # Supported languages with detailed metadata
    SUPPORTED_LANGUAGES = {
        'en': {
            'name': 'English', 
            'native': 'English',
            'direction': 'ltr',
            'region': 'US',
            'pluralization_rule': 'english'
        },
        'pt': {
            'name': 'Portuguese', 
            'native': 'Português',
            'direction': 'ltr',
            'region': 'BR',
            'pluralization_rule': 'portuguese',
            'variants': {
                'pt-BR': 'Português (Brasil)',
                'pt-PT': 'Português (Portugal)'
            }
        },
        'es': {
            'name': 'Spanish', 
            'native': 'Español',
            'direction': 'ltr',
            'region': 'ES',
            'pluralization_rule': 'spanish',
            'variants': {
                'es-ES': 'Español (España)',
                'es-MX': 'Español (México)',
                'es-AR': 'Español (Argentina)'
            }
        }
    }
    
    # Pluralization rules for different languages
    PLURALIZATION_RULES = {
        'english': lambda n: 0 if n == 1 else 1,
        'portuguese': lambda n: 0 if n == 1 else 1,
        'spanish': lambda n: 0 if n == 1 else 1
    }
    
    def __init__(self):
        """Initialize the enhanced i18n manager."""
        super().__init__()
        
        self.current_language = 'en'  # Default to English
        self.current_variant = None  # Language variant (e.g., 'pt-BR')
        self.translator = QTranslator()
        self.translations: Dict[str, Dict[str, Union[str, Dict]]] = {}
        self.translation_contexts: Dict[str, Dict[str, str]] = {}
        self.missing_keys: Dict[str, set] = {}
        self.validation_errors: List[str] = []
        
        # Dynamic language switching callbacks
        self.language_change_callbacks: List[Callable[[str], None]] = []
        
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
        self._detect_system_locale()
        
        logger.info(f"Enhanced I18n manager initialized with language: {self.current_language}")
    
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
        """Load language configuration with variant support."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.current_language = config.get('language', 'en')
                    self.current_variant = config.get('variant')
                    logger.info(f"Loaded language config: {self.current_language}" + 
                               (f" ({self.current_variant})" if self.current_variant else ""))
            else:
                # Will be handled by _detect_system_locale
                self.current_language = 'en'
                self.current_variant = None
                
        except Exception as e:
            logger.error(f"Failed to load language config: {e}")
            self.current_language = 'en'
            self.current_variant = None
    
    def _save_language_config(self):
        """Save language configuration with variant support."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            config = {
                'language': self.current_language,
                'variant': self.current_variant,
                'last_updated': datetime.now().isoformat()
            }
            
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
    
    def set_language(self, lang_code: str, variant: Optional[str] = None) -> bool:
        """
        Set current language with dynamic switching support.
        
        Args:
            lang_code: Language code (en, pt, es)
            variant: Language variant (e.g., 'pt-BR', 'es-MX')
            
        Returns:
            True if successful, False otherwise
        """
        if lang_code not in self.SUPPORTED_LANGUAGES:
            logger.error(f"Unsupported language: {lang_code}")
            return False
        
        # Validate variant if provided
        if variant:
            lang_info = self.SUPPORTED_LANGUAGES[lang_code]
            if 'variants' not in lang_info or variant not in lang_info['variants']:
                logger.warning(f"Unsupported variant {variant} for language {lang_code}")
                variant = None
        
        try:
            old_language = self.current_language
            self.current_language = lang_code
            self.current_variant = variant
            
            # Save configuration
            self._save_language_config()
            
            # Emit signal for dynamic UI updates
            self.language_changed.emit(lang_code)
            
            # Call registered callbacks
            for callback in self.language_change_callbacks:
                try:
                    callback(lang_code)
                except Exception as e:
                    logger.error(f"Error in language change callback: {e}")
            
            logger.info(f"Language changed from {old_language} to: {lang_code}" + 
                       (f" ({variant})" if variant else ""))
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
            # Handle None or invalid key types
            if key is None:
                return str(key)
            
            if not isinstance(key, str):
                key = str(key)
            
            # Handle empty key
            if not key:
                return key
            
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
            return str(key) if key is not None else "None"
    
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
    
    def register_language_change_callback(self, callback: Callable[[str], None]):
        """
        Register a callback to be called when language changes.
        
        Args:
            callback: Function to call with new language code
        """
        if callback not in self.language_change_callbacks:
            self.language_change_callbacks.append(callback)
    
    def unregister_language_change_callback(self, callback: Callable[[str], None]):
        """
        Unregister a language change callback.
        
        Args:
            callback: Function to remove from callbacks
        """
        if callback in self.language_change_callbacks:
            self.language_change_callbacks.remove(callback)
    
    def translate_plural(self, key: str, count: int, **kwargs) -> str:
        """
        Translate with pluralization support.
        
        Args:
            key: Translation key (should have _one and _other variants)
            count: Number for pluralization
            **kwargs: Variables for string formatting
            
        Returns:
            Translated string with correct plural form
        """
        try:
            # Get pluralization rule for current language
            lang_info = self.SUPPORTED_LANGUAGES.get(self.current_language, {})
            rule_name = lang_info.get('pluralization_rule', 'english')
            rule_func = self.PLURALIZATION_RULES.get(rule_name, self.PLURALIZATION_RULES['english'])
            
            # Determine plural form (0 = singular, 1 = plural)
            plural_form = rule_func(count)
            
            # Try to get the appropriate plural form
            if plural_form == 0:
                plural_key = f"{key}_one"
            else:
                plural_key = f"{key}_other"
            
            # Get translation for plural form
            translation = self.translations.get(self.current_language, {}).get(plural_key)
            
            # Fallback to English if not found
            if translation is None:
                translation = self.translations.get('en', {}).get(plural_key)
            
            # Fallback to base key if plural forms not found
            if translation is None:
                translation = self.translate(key, **kwargs)
            else:
                # Add count to kwargs for formatting
                kwargs['count'] = count
                try:
                    translation = translation.format(**kwargs)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Failed to format plural translation for key {plural_key}: {e}")
            
            return translation
            
        except Exception as e:
            logger.error(f"Pluralization error for key {key}: {e}")
            return self.translate(key, **kwargs)
    
    def translate_context(self, key: str, context: str, **kwargs) -> str:
        """
        Translate with context awareness.
        
        Args:
            key: Translation key
            context: Context identifier (e.g., 'button', 'menu', 'dialog')
            **kwargs: Variables for string formatting
            
        Returns:
            Context-aware translated string
        """
        try:
            # Try context-specific key first
            context_key = f"{context}.{key}"
            
            # Check if context-specific translation exists
            translation = self.translations.get(self.current_language, {}).get(context_key)
            
            # Fallback to English context-specific
            if translation is None:
                translation = self.translations.get('en', {}).get(context_key)
            
            # Fallback to regular translation
            if translation is None:
                return self.translate(key, **kwargs)
            
            # Format with variables if provided
            if kwargs:
                try:
                    translation = translation.format(**kwargs)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Failed to format context translation for key {context_key}: {e}")
            
            return translation
            
        except Exception as e:
            logger.error(f"Context translation error for key {key} in context {context}: {e}")
            return self.translate(key, **kwargs)
    
    def validate_translation_keys(self) -> List[str]:
        """
        Validate all translation keys for consistency and completeness.
        
        Returns:
            List of validation errors
        """
        errors = []
        
        try:
            # Get all English keys as reference
            english_keys = set(self.translations.get('en', {}).keys())
            
            for lang_code in self.SUPPORTED_LANGUAGES.keys():
                if lang_code == 'en':
                    continue
                
                lang_keys = set(self.translations.get(lang_code, {}).keys())
                
                # Check for missing translations
                missing = english_keys - lang_keys
                if missing:
                    errors.append(f"Language '{lang_code}' missing keys: {', '.join(sorted(missing))}")
                
                # Check for extra translations
                extra = lang_keys - english_keys
                if extra:
                    errors.append(f"Language '{lang_code}' has extra keys: {', '.join(sorted(extra))}")
                
                # Check for empty translations
                for key in lang_keys:
                    value = self.translations[lang_code].get(key, '')
                    if not value or (isinstance(value, str) and not value.strip()):
                        errors.append(f"Language '{lang_code}' has empty translation for key: {key}")
            
            # Check for variable consistency
            for key in english_keys:
                english_text = self.translations.get('en', {}).get(key, '')
                if isinstance(english_text, str):
                    english_vars = set(re.findall(r'\{(\w+)\}', english_text))
                    
                    for lang_code in self.SUPPORTED_LANGUAGES.keys():
                        if lang_code == 'en':
                            continue
                        
                        lang_text = self.translations.get(lang_code, {}).get(key, '')
                        if isinstance(lang_text, str):
                            lang_vars = set(re.findall(r'\{(\w+)\}', lang_text))
                            
                            if english_vars != lang_vars:
                                errors.append(
                                    f"Variable mismatch in '{lang_code}.{key}': "
                                    f"English has {english_vars}, {lang_code} has {lang_vars}"
                                )
            
            self.validation_errors = errors
            return errors
            
        except Exception as e:
            error_msg = f"Translation validation error: {e}"
            logger.error(error_msg)
            return [error_msg]
    
    def get_language_info(self, lang_code: str) -> Dict[str, Any]:
        """
        Get detailed information about a language.
        
        Args:
            lang_code: Language code
            
        Returns:
            Dictionary with language information
        """
        if lang_code not in self.SUPPORTED_LANGUAGES:
            return {}
        
        info = self.SUPPORTED_LANGUAGES[lang_code].copy()
        info['code'] = lang_code
        info['is_rtl'] = info.get('direction', 'ltr') == 'rtl'
        info['translation_count'] = len(self.translations.get(lang_code, {}))
        info['missing_count'] = len(self.get_missing_translations(lang_code))
        info['completion_percentage'] = 0
        
        # Calculate completion percentage
        english_count = len(self.translations.get('en', {}))
        if english_count > 0:
            info['completion_percentage'] = (
                (info['translation_count'] - info['missing_count']) / english_count * 100
            )
        
        return info
    
    def _detect_system_locale(self):
        """Detect and set system locale if not already configured."""
        try:
            if self.current_language == 'en' and not self.config_file.exists():
                # Only auto-detect if no configuration exists
                system_locale = QLocale.system()
                locale_name = system_locale.name()
                
                # Extract language code
                lang_code = locale_name.split('_')[0].lower()
                
                # Check if we support this language
                if lang_code in self.SUPPORTED_LANGUAGES:
                    # Check for specific variants
                    if lang_code == 'pt':
                        if 'BR' in locale_name:
                            self.current_variant = 'pt-BR'
                        elif 'PT' in locale_name:
                            self.current_variant = 'pt-PT'
                    elif lang_code == 'es':
                        if 'MX' in locale_name:
                            self.current_variant = 'es-MX'
                        elif 'AR' in locale_name:
                            self.current_variant = 'es-AR'
                        else:
                            self.current_variant = 'es-ES'
                    
                    self.current_language = lang_code
                    logger.info(f"Auto-detected system language: {lang_code}" + 
                               (f" ({self.current_variant})" if self.current_variant else ""))
                
        except Exception as e:
            logger.error(f"Failed to detect system locale: {e}")
    
    def export_translations(self, lang_code: str, file_path: Path) -> bool:
        """
        Export translations for a specific language.
        
        Args:
            lang_code: Language code to export
            file_path: Path to export file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if lang_code not in self.SUPPORTED_LANGUAGES:
                logger.error(f"Cannot export unsupported language: {lang_code}")
                return False
            
            translations = self.translations.get(lang_code, {})
            
            export_data = {
                'language': lang_code,
                'variant': self.current_variant if lang_code == self.current_language else None,
                'exported_at': datetime.now().isoformat(),
                'translation_count': len(translations),
                'translations': translations
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, sort_keys=True)
            
            logger.info(f"Exported {len(translations)} translations for {lang_code} to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export translations for {lang_code}: {e}")
            return False
    
    def import_translations(self, file_path: Path, merge: bool = True) -> bool:
        """
        Import translations from a file.
        
        Args:
            file_path: Path to import file
            merge: Whether to merge with existing translations
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            lang_code = import_data.get('language')
            if not lang_code or lang_code not in self.SUPPORTED_LANGUAGES:
                logger.error(f"Invalid or unsupported language in import file: {lang_code}")
                return False
            
            imported_translations = import_data.get('translations', {})
            
            if merge and lang_code in self.translations:
                # Merge with existing translations
                self.translations[lang_code].update(imported_translations)
            else:
                # Replace all translations
                self.translations[lang_code] = imported_translations
            
            # Save to file
            self._save_translation_file(lang_code)
            
            logger.info(f"Imported {len(imported_translations)} translations for {lang_code}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import translations from {file_path}: {e}")
            return False


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
