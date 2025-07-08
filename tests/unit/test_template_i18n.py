#!/usr/bin/env python3
"""
Unit tests for Template Management Internationalization.

Tests that all template management features have proper translations
in English, Portuguese, and Spanish.
"""

import sys
import pytest
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from multichannel_messaging.core.i18n_manager import get_i18n_manager


class TestTemplateInternationalization:
    """Test cases for template management internationalization."""
    
    @pytest.fixture
    def i18n_manager(self):
        """Get i18n manager instance."""
        return get_i18n_manager()
    
    @pytest.fixture
    def template_keys(self):
        """Key template management translation keys to test."""
        return [
            "template_library",
            "new_template",
            "save_template",
            "template_information",
            "template_name",
            "template_category",
            "supported_channels",
            "category_welcome",
            "category_follow_up",
            "category_promotional",
            "category_support",
            "category_general",
            "search_templates",
            "template_preview",
            "edit_template",
            "delete_template",
            "use_template",
            "validation_error",
            "template_saved_success",
            "template_import_failed",
            "confirm_delete_template"
        ]
    
    @pytest.mark.parametrize("language", ["en", "pt", "es"])
    def test_template_translations_exist(self, i18n_manager, template_keys, language):
        """Test that all template management translations exist for each language."""
        i18n_manager.set_language(language)
        
        missing_translations = []
        for key in template_keys:
            translation = i18n_manager.tr(key)
            if translation == key:  # Translation not found
                missing_translations.append(key)
        
        assert len(missing_translations) == 0, f"Missing translations in {language}: {missing_translations}"
    
    def test_english_translations(self, i18n_manager):
        """Test specific English translations."""
        i18n_manager.set_language("en")
        
        assert i18n_manager.tr("template_library") == "Template Library"
        assert i18n_manager.tr("new_template") == "New Template"
        assert i18n_manager.tr("save_template") == "Save Template"
        assert i18n_manager.tr("category_welcome") == "Welcome Messages"
        assert i18n_manager.tr("validation_error") == "Validation Error"
    
    def test_portuguese_translations(self, i18n_manager):
        """Test specific Portuguese translations."""
        i18n_manager.set_language("pt")
        
        assert i18n_manager.tr("template_library") == "Biblioteca de Modelos"
        assert i18n_manager.tr("new_template") == "Novo Modelo"
        assert i18n_manager.tr("save_template") == "Salvar Modelo"
        assert i18n_manager.tr("category_welcome") == "Mensagens de Boas-vindas"
        assert i18n_manager.tr("validation_error") == "Erro de Validação"
    
    def test_spanish_translations(self, i18n_manager):
        """Test specific Spanish translations."""
        i18n_manager.set_language("es")
        
        assert i18n_manager.tr("template_library") == "Biblioteca de Plantillas"
        assert i18n_manager.tr("new_template") == "Nueva Plantilla"
        assert i18n_manager.tr("save_template") == "Guardar Plantilla"
        assert i18n_manager.tr("category_welcome") == "Mensajes de Bienvenida"
        assert i18n_manager.tr("validation_error") == "Error de Validación"
    
    def test_variable_substitution(self, i18n_manager):
        """Test variable substitution in translations."""
        i18n_manager.set_language("en")
        
        # Test template saved success message
        success_msg = i18n_manager.tr("template_saved_success", name="Test Template")
        assert "Test Template" in success_msg
        assert "saved successfully" in success_msg
        
        # Test variables list
        vars_msg = i18n_manager.tr("variables_list", variables="name, company, email")
        assert "name, company, email" in vars_msg
        
        # Test character count
        char_msg = i18n_manager.tr("whatsapp_char_limit", count=150)
        assert "150" in char_msg
    
    def test_category_translations_consistency(self, i18n_manager):
        """Test that category translations are consistent across languages."""
        categories = ["welcome", "follow_up", "promotional", "support", "general"]
        languages = ["en", "pt", "es"]
        
        for language in languages:
            i18n_manager.set_language(language)
            for category in categories:
                key = f"category_{category}"
                translation = i18n_manager.tr(key)
                
                # Should not be the same as the key (translation should exist)
                assert translation != key, f"Missing translation for {key} in {language}"
                
                # Should not be empty
                assert len(translation.strip()) > 0, f"Empty translation for {key} in {language}"
    
    def test_placeholder_translations(self, i18n_manager):
        """Test placeholder text translations."""
        i18n_manager.set_language("en")
        
        placeholders = [
            "template_name_placeholder",
            "template_description_placeholder",
            "email_subject_placeholder",
            "email_content_placeholder",
            "whatsapp_content_placeholder"
        ]
        
        for placeholder in placeholders:
            translation = i18n_manager.tr(placeholder)
            assert translation != placeholder, f"Missing placeholder translation: {placeholder}"
            assert "..." in translation or "placeholder" in translation.lower()
    
    def test_error_message_translations(self, i18n_manager):
        """Test error message translations."""
        error_keys = [
            "template_name_required",
            "channel_required",
            "email_subject_required",
            "email_content_required",
            "whatsapp_content_required",
            "template_save_failed",
            "template_import_failed",
            "template_delete_failed"
        ]
        
        for language in ["en", "pt", "es"]:
            i18n_manager.set_language(language)
            for key in error_keys:
                translation = i18n_manager.tr(key)
                assert translation != key, f"Missing error translation {key} in {language}"
                assert len(translation.strip()) > 0
    
    def test_success_message_translations(self, i18n_manager):
        """Test success message translations."""
        success_keys = [
            "template_saved_success",
            "template_imported_success",
            "template_exported_success",
            "template_deleted_success",
            "template_duplicated_success"
        ]
        
        for language in ["en", "pt", "es"]:
            i18n_manager.set_language(language)
            for key in success_keys:
                translation = i18n_manager.tr(key)
                assert translation != key, f"Missing success translation {key} in {language}"
                assert len(translation.strip()) > 0


if __name__ == "__main__":
    pytest.main([__file__])
