"""
Right-to-Left (RTL) language support framework for CSC-Reach.
Provides utilities for handling RTL languages and layout adjustments.
"""

from typing import Dict, List, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QLayout, QHBoxLayout, QVBoxLayout

from ..utils.logger import get_logger

logger = get_logger(__name__)


class RTLSupport:
    """
    Framework for supporting right-to-left languages.
    """
    
    # RTL language codes
    RTL_LANGUAGES = {
        'ar': 'Arabic',
        'he': 'Hebrew',
        'fa': 'Persian/Farsi',
        'ur': 'Urdu'
    }
    
    def __init__(self, i18n_manager):
        """
        Initialize RTL support.
        
        Args:
            i18n_manager: I18n manager instance
        """
        self.i18n_manager = i18n_manager
        self.current_direction = 'ltr'
        self._update_direction()
        
        # Register for language changes
        self.i18n_manager.register_language_change_callback(self._on_language_changed)
    
    def _update_direction(self):
        """Update text direction based on current language."""
        current_lang = self.i18n_manager.get_current_language()
        lang_info = self.i18n_manager.SUPPORTED_LANGUAGES.get(current_lang, {})
        self.current_direction = lang_info.get('direction', 'ltr')
    
    def _on_language_changed(self, new_language: str):
        """Handle language change event."""
        old_direction = self.current_direction
        self._update_direction()
        
        if old_direction != self.current_direction:
            logger.info(f"Text direction changed from {old_direction} to {self.current_direction}")
    
    def is_rtl(self, lang_code: Optional[str] = None) -> bool:
        """
        Check if a language is right-to-left.
        
        Args:
            lang_code: Language code to check (current language if None)
            
        Returns:
            True if RTL, False if LTR
        """
        if lang_code is None:
            return self.current_direction == 'rtl'
        
        return lang_code in self.RTL_LANGUAGES
    
    def get_text_alignment(self, lang_code: Optional[str] = None) -> Qt.AlignmentFlag:
        """
        Get appropriate text alignment for a language.
        
        Args:
            lang_code: Language code (current language if None)
            
        Returns:
            Qt alignment flag
        """
        if self.is_rtl(lang_code):
            return Qt.AlignmentFlag.AlignRight
        else:
            return Qt.AlignmentFlag.AlignLeft
    
    def get_layout_direction(self, lang_code: Optional[str] = None) -> Qt.LayoutDirection:
        """
        Get layout direction for a language.
        
        Args:
            lang_code: Language code (current language if None)
            
        Returns:
            Qt layout direction
        """
        if self.is_rtl(lang_code):
            return Qt.LayoutDirection.RightToLeft
        else:
            return Qt.LayoutDirection.LeftToRight
    
    def apply_rtl_layout(self, widget: QWidget, lang_code: Optional[str] = None):
        """
        Apply RTL layout to a widget.
        
        Args:
            widget: Widget to apply RTL layout to
            lang_code: Language code (current language if None)
        """
        try:
            layout_direction = self.get_layout_direction(lang_code)
            widget.setLayoutDirection(layout_direction)
            
            # Apply to child widgets recursively
            for child in widget.findChildren(QWidget):
                child.setLayoutDirection(layout_direction)
            
        except Exception as e:
            logger.error(f"Error applying RTL layout: {e}")
    
    def reverse_layout_order(self, layout: QLayout):
        """
        Reverse the order of items in a layout for RTL support.
        
        Args:
            layout: Layout to reverse
        """
        try:
            if isinstance(layout, QHBoxLayout):
                # For horizontal layouts, reverse the order of items
                items = []
                while layout.count():
                    item = layout.takeAt(0)
                    items.append(item)
                
                for item in reversed(items):
                    layout.addItem(item)
            
        except Exception as e:
            logger.error(f"Error reversing layout order: {e}")
    
    def format_text_direction(self, text: str, lang_code: Optional[str] = None) -> str:
        """
        Format text with appropriate direction markers.
        
        Args:
            text: Text to format
            lang_code: Language code (current language if None)
            
        Returns:
            Text with direction markers
        """
        if self.is_rtl(lang_code):
            # Add RTL mark at the beginning
            return f"\u200F{text}"
        else:
            # Add LTR mark at the beginning
            return f"\u200E{text}"
    
    def get_supported_rtl_languages(self) -> Dict[str, str]:
        """
        Get list of supported RTL languages.
        
        Returns:
            Dictionary of RTL language codes and names
        """
        return self.RTL_LANGUAGES.copy()
    
    def prepare_for_rtl_expansion(self, supported_languages: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Prepare language configuration for future RTL language support.
        
        Args:
            supported_languages: Current supported languages configuration
            
        Returns:
            Updated configuration with RTL preparation
        """
        updated_config = supported_languages.copy()
        
        # Add RTL language placeholders (disabled by default)
        rtl_placeholders = {
            'ar': {
                'name': 'Arabic',
                'native': 'العربية',
                'direction': 'rtl',
                'region': 'SA',
                'pluralization_rule': 'arabic',
                'enabled': False  # Disabled until translations are available
            },
            'he': {
                'name': 'Hebrew',
                'native': 'עברית',
                'direction': 'rtl',
                'region': 'IL',
                'pluralization_rule': 'hebrew',
                'enabled': False
            }
        }
        
        for lang_code, config in rtl_placeholders.items():
            if lang_code not in updated_config:
                updated_config[lang_code] = config
        
        return updated_config


class RTLAwareWidget:
    """
    Mixin class for widgets that need RTL awareness.
    """
    
    def __init__(self, rtl_support: RTLSupport):
        """
        Initialize RTL-aware widget.
        
        Args:
            rtl_support: RTL support instance
        """
        self.rtl_support = rtl_support
    
    def setup_rtl_layout(self):
        """Set up RTL-aware layout for the widget."""
        if hasattr(self, 'widget') and isinstance(self.widget, QWidget):
            self.rtl_support.apply_rtl_layout(self.widget)
    
    def get_rtl_aware_text(self, text: str) -> str:
        """
        Get RTL-aware formatted text.
        
        Args:
            text: Original text
            
        Returns:
            RTL-aware formatted text
        """
        return self.rtl_support.format_text_direction(text)
    
    def get_text_alignment(self) -> Qt.AlignmentFlag:
        """Get appropriate text alignment for current language."""
        return self.rtl_support.get_text_alignment()


# Global RTL support instance
_rtl_support = None

def get_rtl_support():
    """Get global RTL support instance."""
    global _rtl_support
    if _rtl_support is None:
        from .i18n_manager import get_i18n_manager
        _rtl_support = RTLSupport(get_i18n_manager())
    return _rtl_support