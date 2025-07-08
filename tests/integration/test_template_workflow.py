#!/usr/bin/env python3
"""
Integration tests for Template Management Workflow.

Tests the complete template management workflow including
GUI integration, file operations, and user interactions.
"""

import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from multichannel_messaging.core.config_manager import ConfigManager
from multichannel_messaging.core.template_manager import TemplateManager
from multichannel_messaging.core.models import MessageTemplate, Customer
from multichannel_messaging.core.i18n_manager import get_i18n_manager


class TestTemplateWorkflow:
    """Integration tests for complete template workflows."""
    
    @pytest.fixture
    def temp_config(self):
        """Create temporary config for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_manager = ConfigManager()
            # Override templates path for testing
            config_manager.get_templates_path = lambda: temp_path / "templates"
            yield config_manager
    
    @pytest.fixture
    def template_manager(self, temp_config):
        """Create template manager with temporary config."""
        return TemplateManager(temp_config)
    
    @pytest.fixture
    def i18n_manager(self):
        """Get i18n manager instance."""
        return get_i18n_manager()
    
    @pytest.fixture
    def sample_customers(self):
        """Create sample customers for testing."""
        return [
            Customer(
                name="John Doe",
                company="Acme Corp",
                phone="+1-555-0123",
                email="john@acme.com"
            ),
            Customer(
                name="Jane Smith",
                company="Tech Solutions",
                phone="+1-555-0456",
                email="jane@techsolutions.com"
            )
        ]
    
    def test_complete_template_creation_workflow(self, template_manager, i18n_manager):
        """Test complete template creation workflow."""
        # Step 1: Create new template
        template = MessageTemplate(
            id="welcome_email",
            name="Welcome Email",
            channels=["email", "whatsapp"],
            subject="Welcome to {company}, {name}!",
            content="Dear {name},\n\nWelcome to our service at {company}!",
            whatsapp_content="Hi {name}! Welcome to {company}! 👋",
            variables=["name", "company"]
        )
        
        # Step 2: Save template with metadata
        success = template_manager.save_template(
            template,
            category_id="welcome",
            description="Welcome message for new customers",
            tags=["welcome", "onboarding"]
        )
        assert success is True
        
        # Step 3: Verify template was saved
        saved_template = template_manager.get_template("welcome_email")
        assert saved_template is not None
        assert saved_template.name == "Welcome Email"
        
        # Step 4: Verify metadata
        metadata = template_manager.get_template_metadata("welcome_email")
        assert metadata["category_id"] == "welcome"
        assert metadata["description"] == "Welcome message for new customers"
        assert "welcome" in metadata["tags"]
        
        # Step 5: Test template rendering
        customer = Customer(
            name="Test User",
            company="Test Company",
            phone="+1-555-0000",
            email="test@example.com"
        )
        
        rendered = saved_template.render(customer)
        assert "Test User" in rendered["subject"]
        assert "Test Company" in rendered["content"]
        assert "Test User" in rendered["whatsapp_content"]
    
    def test_template_library_management_workflow(self, template_manager):
        """Test template library management workflow."""
        # Step 1: Create multiple templates in different categories
        templates = [
            {
                "template": MessageTemplate(
                    id="welcome_new",
                    name="New Customer Welcome",
                    channels=["email"],
                    subject="Welcome {name}!",
                    content="Welcome to our service!"
                ),
                "category": "welcome"
            },
            {
                "template": MessageTemplate(
                    id="follow_up_1",
                    name="First Follow-up",
                    channels=["email", "whatsapp"],
                    subject="Following up with {name}",
                    content="Hi {name}, just following up...",
                    whatsapp_content="Hi {name}! Following up 📞"
                ),
                "category": "follow_up"
            },
            {
                "template": MessageTemplate(
                    id="promo_offer",
                    name="Special Offer",
                    channels=["whatsapp"],
                    whatsapp_content="Special offer for {company}! 🎉"
                ),
                "category": "promotional"
            }
        ]
        
        # Step 2: Save all templates
        for item in templates:
            success = template_manager.save_template(
                item["template"],
                category_id=item["category"]
            )
            assert success is True
        
        # Step 3: Test category filtering
        welcome_templates = template_manager.get_templates(category_id="welcome")
        assert len(welcome_templates) == 1
        assert welcome_templates[0].name == "New Customer Welcome"
        
        follow_up_templates = template_manager.get_templates(category_id="follow_up")
        assert len(follow_up_templates) == 1
        assert follow_up_templates[0].name == "First Follow-up"
        
        # Step 4: Test search functionality
        search_results = template_manager.search_templates("follow")
        assert len(search_results) == 1
        assert search_results[0].name == "First Follow-up"
        
        # Step 5: Test usage statistics
        stats = template_manager.get_template_usage_stats()
        assert stats["total_templates"] == 3
        assert stats["templates_by_category"]["welcome"] == 1
        assert stats["templates_by_category"]["follow_up"] == 1
        assert stats["templates_by_category"]["promotional"] == 1
    
    def test_template_import_export_workflow(self, template_manager):
        """Test template import/export workflow."""
        # Step 1: Create and save original template
        original_template = MessageTemplate(
            id="export_test",
            name="Export Test Template",
            channels=["email"],
            subject="Test Export {name}",
            content="This is a test template for {company}.",
            variables=["name", "company"]
        )
        
        template_manager.save_template(
            original_template,
            category_id="general",
            description="Template for export testing"
        )
        
        # Step 2: Export template
        export_path = template_manager.export_template("export_test")
        assert export_path is not None
        assert export_path.exists()
        
        # Step 3: Verify export file content
        import json
        with open(export_path, 'r', encoding='utf-8') as f:
            export_data = json.load(f)
        
        assert "template" in export_data
        assert "metadata" in export_data
        assert export_data["template"]["name"] == "Export Test Template"
        
        # Step 4: Import template with new ID
        imported_template = template_manager.import_template(
            export_path,
            new_id="imported_test",
            category_id="support"
        )
        
        assert imported_template is not None
        assert imported_template.id == "imported_test"
        assert imported_template.name == "Export Test Template"
        assert imported_template.content == original_template.content
        
        # Step 5: Verify imported template metadata
        imported_metadata = template_manager.get_template_metadata("imported_test")
        assert imported_metadata["category_id"] == "support"
    
    def test_template_duplication_and_modification_workflow(self, template_manager):
        """Test template duplication and modification workflow."""
        # Step 1: Create base template
        base_template = MessageTemplate(
            id="base_template",
            name="Base Template",
            channels=["email"],
            subject="Base Subject {name}",
            content="Base content for {company}.",
            variables=["name", "company"]
        )
        
        template_manager.save_template(base_template, category_id="general")
        
        # Step 2: Duplicate template
        duplicate = template_manager.duplicate_template(
            "base_template",
            "Modified Template",
            "modified_template"
        )
        
        assert duplicate is not None
        assert duplicate.id == "modified_template"
        assert duplicate.name == "Modified Template"
        assert duplicate.content == base_template.content
        
        # Step 3: Modify duplicated template
        duplicate.subject = "Modified Subject {name}"
        duplicate.content = "Modified content for {company}."
        duplicate.channels = ["email", "whatsapp"]
        duplicate.whatsapp_content = "Modified WhatsApp content for {company}!"
        
        # Step 4: Save modifications
        success = template_manager.save_template(
            duplicate,
            category_id="promotional",
            description="Modified version of base template"
        )
        assert success is True
        
        # Step 5: Verify both templates exist and are different
        base = template_manager.get_template("base_template")
        modified = template_manager.get_template("modified_template")
        
        assert base.subject != modified.subject
        assert base.content != modified.content
        assert len(base.channels) != len(modified.channels)
    
    def test_multilingual_template_workflow(self, template_manager, i18n_manager):
        """Test template workflow with multiple languages."""
        # Step 1: Create templates for different languages
        languages = ["en", "pt", "es"]
        templates = {}
        
        for lang in languages:
            i18n_manager.set_language(lang)
            
            # Create language-specific template
            template = MessageTemplate(
                id=f"welcome_{lang}",
                name=f"Welcome Template ({lang.upper()})",
                channels=["email"],
                subject=i18n_manager.tr("default_template_subject"),
                content=i18n_manager.tr("default_template_content"),
                language=lang,
                variables=["name", "company"]
            )
            
            templates[lang] = template
            
            # Save template
            success = template_manager.save_template(
                template,
                category_id="welcome",
                description=f"Welcome template in {lang}"
            )
            assert success is True
        
        # Step 2: Verify all templates were created
        all_templates = template_manager.get_templates()
        welcome_templates = [t for t in all_templates if t.id.startswith("welcome_")]
        assert len(welcome_templates) == 3
        
        # Step 3: Test language-specific content
        for lang in languages:
            template = template_manager.get_template(f"welcome_{lang}")
            assert template.language == lang
            
            # Content should be different for each language
            if lang == "pt":
                assert "Caro" in template.content or "Obrigado" in template.content
            elif lang == "es":
                assert "Estimado" in template.content or "Gracias" in template.content
    
    def test_template_backup_and_recovery_workflow(self, template_manager):
        """Test template backup and recovery workflow."""
        # Step 1: Create original template
        original = MessageTemplate(
            id="backup_test",
            name="Backup Test",
            channels=["email"],
            subject="Original Subject",
            content="Original content",
            variables=["name"]
        )
        
        template_manager.save_template(original, category_id="general")
        
        # Step 2: Modify template (this should create backup)
        modified = template_manager.get_template("backup_test")
        modified.subject = "Modified Subject"
        modified.content = "Modified content"
        
        template_manager.save_template(modified, category_id="general")
        
        # Step 3: Verify backup was created
        backups_dir = template_manager.templates_dir / "backups"
        backup_files = list(backups_dir.glob("backup_test_*.json"))
        assert len(backup_files) > 0
        
        # Step 4: Verify backup contains original content
        import json
        with open(backup_files[0], 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        assert backup_data["subject"] == "Original Subject"
        assert backup_data["content"] == "Original content"


if __name__ == "__main__":
    pytest.main([__file__])
