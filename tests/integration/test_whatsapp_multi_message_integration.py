"""
Integration tests for WhatsApp Multi-Message Template System.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from src.multichannel_messaging.core.whatsapp_multi_message import (
    WhatsAppMultiMessageTemplate, MessageSplitStrategy
)
from src.multichannel_messaging.core.whatsapp_multi_message_manager import WhatsAppMultiMessageManager
from src.multichannel_messaging.gui.whatsapp_multi_message_dialog import WhatsAppMultiMessageDialog
from src.multichannel_messaging.core.config_manager import ConfigManager


@pytest.fixture
def app():
    """Create QApplication for GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def temp_config_manager():
    """Create a temporary config manager for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = Mock()
        config_manager.get_app_data_path.return_value = Path(temp_dir)
        yield config_manager


class TestWhatsAppMultiMessageManager:
    """Test WhatsApp multi-message manager integration."""
    
    def test_manager_lifecycle(self, temp_config_manager):
        """Test complete manager lifecycle."""
        manager = WhatsAppMultiMessageManager(temp_config_manager)
        
        # Initially empty
        assert len(manager.get_all_templates()) == 0
        
        # Create a template
        template = manager.create_template(
            name="Test Template",
            content="Hello {name}!\n\nWelcome to {company}!",
            multi_message_mode=True,
            split_strategy=MessageSplitStrategy.PARAGRAPH
        )
        
        assert template.name == "Test Template"
        assert template.multi_message_mode
        assert len(template.message_sequence) == 2
        
        # Verify it's stored
        all_templates = manager.get_all_templates()
        assert len(all_templates) == 1
        assert all_templates[0].name == "Test Template"
        
        # Update the template
        updated = manager.update_template(
            template.id,
            name="Updated Template",
            content="New content here!"
        )
        
        assert updated.name == "Updated Template"
        assert updated.content == "New content here!"
        
        # Delete the template
        success = manager.delete_template(template.id)
        assert success
        assert len(manager.get_all_templates()) == 0
    
    def test_manager_persistence(self, temp_config_manager):
        """Test that templates are persisted across manager instances."""
        # Create first manager and add template
        manager1 = WhatsAppMultiMessageManager(temp_config_manager)
        template = manager1.create_template(
            name="Persistent Template",
            content="This should persist",
            multi_message_mode=False
        )
        
        # Create second manager (simulating app restart)
        manager2 = WhatsAppMultiMessageManager(temp_config_manager)
        
        # Verify template was loaded
        templates = manager2.get_all_templates()
        assert len(templates) == 1
        assert templates[0].name == "Persistent Template"
        assert templates[0].content == "This should persist"
    
    def test_manager_search_and_filter(self, temp_config_manager):
        """Test search and filter functionality."""
        manager = WhatsAppMultiMessageManager(temp_config_manager)
        
        # Create multiple templates
        manager.create_template(
            name="Welcome Message",
            content="Welcome to our service!",
            language="en"
        )
        
        manager.create_template(
            name="Bienvenido Mensaje",
            content="¡Bienvenido a nuestro servicio!",
            language="es"
        )
        
        manager.create_template(
            name="Follow Up",
            content="Following up on your inquiry",
            language="en"
        )
        
        # Test search
        welcome_templates = manager.search_templates("welcome")
        assert len(welcome_templates) == 2  # Should find both welcome templates
        
        follow_templates = manager.search_templates("follow")
        assert len(follow_templates) == 1
        assert follow_templates[0].name == "Follow Up"
        
        # Test language filter
        english_templates = manager.get_templates_by_language("en")
        assert len(english_templates) == 2
        
        spanish_templates = manager.get_templates_by_language("es")
        assert len(spanish_templates) == 1
        assert spanish_templates[0].name == "Bienvenido Mensaje"
    
    def test_manager_export_import(self, temp_config_manager):
        """Test export and import functionality."""
        manager = WhatsAppMultiMessageManager(temp_config_manager)
        
        # Create templates
        template1 = manager.create_template(
            name="Export Test 1",
            content="First template",
            multi_message_mode=True,
            split_strategy=MessageSplitStrategy.PARAGRAPH
        )
        
        template2 = manager.create_template(
            name="Export Test 2",
            content="Second template",
            multi_message_mode=False
        )
        
        # Export templates
        export_data = manager.export_templates()
        
        assert export_data['template_count'] == 2
        assert len(export_data['templates']) == 2
        
        # Clear manager
        manager.delete_template(template1.id)
        manager.delete_template(template2.id)
        assert len(manager.get_all_templates()) == 0
        
        # Import templates
        imported = manager.import_templates(export_data)
        
        assert len(imported) == 2
        assert len(manager.get_all_templates()) == 2
        
        # Verify imported templates
        imported_names = [t.name for t in imported]
        assert "Export Test 1" in imported_names
        assert "Export Test 2" in imported_names


@pytest.mark.gui
class TestWhatsAppMultiMessageDialog:
    """Test WhatsApp multi-message dialog GUI."""
    
    def test_dialog_creation(self, app):
        """Test creating the dialog."""
        dialog = WhatsAppMultiMessageDialog()
        
        assert dialog.windowTitle() in ["Create WhatsApp Template", "Edit WhatsApp Template"]
        assert not dialog.is_editing
        assert dialog.template is None
        
        dialog.close()
    
    def test_dialog_with_existing_template(self, app):
        """Test dialog with existing template."""
        template = WhatsAppMultiMessageTemplate(
            id="test_dialog",
            name="Dialog Test",
            content="Hello {name}!\n\nWelcome!",
            multi_message_mode=True,
            split_strategy=MessageSplitStrategy.PARAGRAPH,
            message_delay_seconds=2.0
        )
        
        dialog = WhatsAppMultiMessageDialog(template=template)
        
        assert dialog.is_editing
        assert dialog.template == template
        assert dialog.name_edit.text() == "Dialog Test"
        assert dialog.multi_message_checkbox.isChecked()
        assert dialog.delay_spin.value() == 2.0
        
        dialog.close()
    
    def test_dialog_ui_interactions(self, app):
        """Test basic UI interactions."""
        dialog = WhatsAppMultiMessageDialog()
        
        # Set template name
        dialog.name_edit.setText("Test Template")
        assert dialog.name_edit.text() == "Test Template"
        
        # Set content
        test_content = "Hello {name}!\n\nWelcome to {company}!"
        dialog.content_edit.setPlainText(test_content)
        assert dialog.content_edit.toPlainText() == test_content
        
        # Enable multi-message mode
        dialog.multi_message_checkbox.setChecked(True)
        assert dialog.multi_message_checkbox.isChecked()
        assert dialog.multi_settings_widget.isVisible()
        
        # Test auto-split
        dialog.auto_split_btn.click()
        
        # Verify preview is updated
        assert dialog.preview_widget.template is not None
        
        dialog.close()
    
    def test_dialog_validation(self, app):
        """Test dialog validation."""
        dialog = WhatsAppMultiMessageDialog()
        
        # Try to save empty template (should fail)
        with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:
            dialog.save_template()
            mock_warning.assert_called()
        
        # Set required fields
        dialog.name_edit.setText("Valid Template")
        dialog.content_edit.setPlainText("Valid content here")
        
        # Should succeed now
        with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:
            with patch.object(dialog, 'accept') as mock_accept:
                dialog.save_template()
                mock_accept.assert_called()
                mock_warning.assert_not_called()
        
        dialog.close()
    
    def test_message_sequence_widget(self, app):
        """Test message sequence widget functionality."""
        dialog = WhatsAppMultiMessageDialog()
        
        # Enable multi-message mode and manual split
        dialog.multi_message_checkbox.setChecked(True)
        dialog.split_strategy_combo.setCurrentText("Manual Split")
        
        # Should show sequence widget
        assert dialog.sequence_widget.isVisible()
        
        # Add messages manually
        test_messages = ["Message 1", "Message 2", "Message 3"]
        dialog.sequence_widget.set_messages(test_messages)
        
        retrieved_messages = dialog.sequence_widget.get_messages()
        assert retrieved_messages == test_messages
        
        dialog.close()


@pytest.mark.integration
class TestWhatsAppMultiMessageIntegration:
    """Test complete integration of multi-message system."""
    
    def test_end_to_end_template_creation(self, temp_config_manager, app):
        """Test complete template creation workflow."""
        manager = WhatsAppMultiMessageManager(temp_config_manager)
        
        # Create template through dialog
        dialog = WhatsAppMultiMessageDialog()
        
        # Fill in template data
        dialog.name_edit.setText("Integration Test")
        dialog.content_edit.setPlainText("Hello {name}!\n\nWelcome to {company}!\n\nThank you for joining us.")
        dialog.multi_message_checkbox.setChecked(True)
        dialog.delay_spin.setValue(1.5)
        
        # Trigger auto-split
        dialog.auto_split_btn.click()
        
        # Get the created template
        template = dialog.create_template_from_ui()
        
        assert template.name == "Integration Test"
        assert template.multi_message_mode
        assert len(template.message_sequence) == 3
        assert template.message_delay_seconds == 1.5
        
        # Save through manager
        saved_template = manager.create_template(
            name=template.name,
            content=template.content,
            multi_message_mode=template.multi_message_mode,
            split_strategy=template.split_strategy,
            message_delay=template.message_delay_seconds
        )
        
        # Verify it's saved
        retrieved = manager.get_template_by_name("Integration Test")
        assert retrieved is not None
        assert retrieved.name == "Integration Test"
        assert len(retrieved.message_sequence) == 3
        
        dialog.close()
    
    def test_template_conversion_workflow(self, temp_config_manager):
        """Test converting between single and multi-message modes."""
        manager = WhatsAppMultiMessageManager(temp_config_manager)
        
        # Create single message template
        single_template = manager.create_template(
            name="Single Message",
            content="Hello {name}! Welcome to {company}! We're excited to have you join us!",
            multi_message_mode=False
        )
        
        # Convert to multi-message
        multi_content = single_template.convert_to_multi_message()
        assert len(multi_content) > 1  # Should be split
        
        # Update template to multi-message mode
        updated = manager.update_template(
            single_template.id,
            multi_message_mode=True,
            split_strategy=MessageSplitStrategy.SENTENCE
        )
        
        assert updated.multi_message_mode
        assert len(updated.message_sequence) > 1
        
        # Convert back to single message
        single_content = updated.convert_to_single_message()
        assert isinstance(single_content, str)
        
        # Update back to single mode
        final = manager.update_template(
            updated.id,
            multi_message_mode=False
        )
        
        assert not final.multi_message_mode


if __name__ == "__main__":
    pytest.main([__file__, "-v"])