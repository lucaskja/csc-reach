"""
Language settings dialog for CSC-Reach internationalization.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ..core.i18n_manager import get_i18n_manager, tr
from ..utils.logger import get_logger

logger = get_logger(__name__)


class LanguageSettingsDialog(QDialog):
    """
    Dialog for selecting application language.
    """
    
    language_changed = Signal(str)  # Emitted when language changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.i18n_manager = get_i18n_manager()
        self.setup_ui()
        self.load_current_settings()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle(tr("language_settings"))
        self.setMinimumSize(400, 200)
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Language selection section
        self.create_language_section(layout)
        
        # Information section
        self.create_info_section(layout)
        
        # Button section
        self.create_button_section(layout)
    
    def create_language_section(self, layout):
        """Create the language selection section."""
        lang_group = QGroupBox(tr("language"))
        lang_layout = QGridLayout(lang_group)
        
        # Language selection
        lang_layout.addWidget(QLabel(tr("select_language")), 0, 0)
        
        self.language_combo = QComboBox()
        self.populate_language_combo()
        lang_layout.addWidget(self.language_combo, 0, 1)
        
        layout.addWidget(lang_group)
    
    def create_info_section(self, layout):
        """Create the information section."""
        info_group = QGroupBox("Information")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QLabel(
            "• Language changes will take effect after restarting the application\n"
            "• All interface text will be translated to the selected language\n"
            "• Default message templates will be updated accordingly"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #666; font-style: italic;")
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
    
    def create_button_section(self, layout):
        """Create the button section."""
        button_layout = QHBoxLayout()
        
        button_layout.addStretch()
        
        # Cancel button
        cancel_btn = QPushButton(tr("cancel"))
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # Save button
        save_btn = QPushButton(tr("save"))
        save_btn.clicked.connect(self.save_language)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def populate_language_combo(self):
        """Populate the language combo box."""
        supported_languages = self.i18n_manager.get_supported_languages()
        
        for lang_code, lang_info in supported_languages.items():
            display_name = f"{lang_info['native']} ({lang_info['name']})"
            self.language_combo.addItem(display_name, lang_code)
    
    def load_current_settings(self):
        """Load current language settings."""
        current_lang = self.i18n_manager.get_current_language()
        
        # Find and select current language in combo
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == current_lang:
                self.language_combo.setCurrentIndex(i)
                break
    
    def save_language(self):
        """Save the selected language."""
        try:
            # Get selected language
            selected_lang = self.language_combo.currentData()
            current_lang = self.i18n_manager.get_current_language()
            
            if selected_lang == current_lang:
                # No change
                self.accept()
                return
            
            # Set new language
            success = self.i18n_manager.set_language(selected_lang)
            
            if success:
                # Emit signal
                self.language_changed.emit(selected_lang)
                
                # Show restart message
                lang_info = self.i18n_manager.get_supported_languages()[selected_lang]
                QMessageBox.information(
                    self,
                    "Language Changed",
                    f"Language has been changed to {lang_info['native']}.\n\n"
                    "Please restart the application for the changes to take effect."
                )
                
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    "Failed to change language. Please try again."
                )
                
        except Exception as e:
            logger.error(f"Failed to save language: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while changing language:\n\n{e}"
            )
