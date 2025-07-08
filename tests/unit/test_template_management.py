#!/usr/bin/env python3
"""
Unit tests for Template Management System.

Tests the core functionality of the template management system
including CRUD operations, categories, and data validation.
"""

import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from multichannel_messaging.core.config_manager import ConfigManager
from multichannel_messaging.core.template_manager import TemplateManager, TemplateCategory
from multichannel_messaging.core.models import MessageTemplate, Customer
from multichannel_messaging.utils.exceptions import ValidationError


class TestTemplateManager:
    """Test cases for TemplateManager class."""
    
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
    def sample_template(self):
        """Create sample template for testing."""
        return MessageTemplate(
            id="test_email",
            name="Test Email Template",
            channels=["email"],
            subject="Test Subject for {name}",
            content="Hello {name} from {company}! This is a test email.",
            variables=["name", "company"]
        )
    
    @pytest.fixture
    def sample_customer(self):
        """Create sample customer for testing."""
        return Customer(
            name="John Doe",
            company="Test Corp",
            phone="+1-555-0123",
            email="john@testcorp.com"
        )
    
    def test_template_manager_initialization(self, template_manager):
        """Test template manager initializes correctly."""
        assert template_manager is not None
        assert template_manager.templates_dir.exists()
        
        # Should create default categories
        categories = template_manager.get_categories()
        assert len(categories) == 5
        
        category_ids = [cat.id for cat in categories]
        expected_categories = ["welcome", "follow_up", "promotional", "support", "general"]
        for expected in expected_categories:
            assert expected in category_ids
    
    def test_save_and_retrieve_template(self, template_manager, sample_template):
        """Test saving and retrieving templates."""
        # Save template
        success = template_manager.save_template(
            sample_template,
            category_id="general",
            description="Test template for validation"
        )
        assert success is True
        
        # Retrieve template
        retrieved = template_manager.get_template("test_email")
        assert retrieved is not None
        assert retrieved.name == "Test Email Template"
        assert retrieved.channels == ["email"]
        assert retrieved.variables == ["name", "company"]
    
    def test_template_rendering(self, template_manager, sample_template, sample_customer):
        """Test template rendering with customer data."""
        # Save template first
        template_manager.save_template(sample_template, category_id="general")
        
        # Retrieve and render
        template = template_manager.get_template("test_email")
        rendered = template.render(sample_customer)
        
        assert "subject" in rendered
        assert "content" in rendered
        assert "John Doe" in rendered["subject"]
        assert "Test Corp" in rendered["content"]
    
    def test_template_search(self, template_manager, sample_template):
        """Test template search functionality."""
        # Save template
        template_manager.save_template(sample_template, category_id="general")
        
        # Search for template
        results = template_manager.search_templates("test")
        assert len(results) == 1
        assert results[0].name == "Test Email Template"
        
        # Search with no results
        results = template_manager.search_templates("nonexistent")
        assert len(results) == 0
    
    def test_template_categories(self, template_manager):
        """Test category management."""
        # Get default categories
        categories = template_manager.get_categories()
        assert len(categories) >= 5
        
        # Create new category
        new_category = template_manager.create_category(
            "test_category",
            "Test Category",
            "Category for testing",
            "#FF0000"
        )
        assert new_category.id == "test_category"
        assert new_category.name == "Test Category"
        
        # Retrieve category
        retrieved = template_manager.get_category("test_category")
        assert retrieved is not None
        assert retrieved.name == "Test Category"
    
    def test_template_export_import(self, template_manager, sample_template):
        """Test template export and import functionality."""
        # Save template
        template_manager.save_template(sample_template, category_id="general")
        
        # Export template
        export_path = template_manager.export_template("test_email")
        assert export_path is not None
        assert export_path.exists()
        
        # Import template with new ID
        imported = template_manager.import_template(export_path, new_id="imported_test")
        assert imported is not None
        assert imported.id == "imported_test"
        assert imported.name == sample_template.name
    
    def test_template_duplication(self, template_manager, sample_template):
        """Test template duplication."""
        # Save original template
        template_manager.save_template(sample_template, category_id="general")
        
        # Duplicate template
        duplicate = template_manager.duplicate_template(
            "test_email",
            "Duplicated Template",
            "duplicated_test"
        )
        assert duplicate is not None
        assert duplicate.id == "duplicated_test"
        assert duplicate.name == "Duplicated Template"
        assert duplicate.content == sample_template.content
    
    def test_template_deletion(self, template_manager, sample_template):
        """Test template deletion."""
        # Save template
        template_manager.save_template(sample_template, category_id="general")
        
        # Verify template exists
        assert template_manager.get_template("test_email") is not None
        
        # Delete template
        success = template_manager.delete_template("test_email")
        assert success is True
        
        # Verify template is deleted
        assert template_manager.get_template("test_email") is None
    
    def test_template_usage_statistics(self, template_manager, sample_template):
        """Test template usage statistics."""
        # Save template
        template_manager.save_template(sample_template, category_id="general")
        
        # Get initial stats
        stats = template_manager.get_template_usage_stats()
        assert stats["total_templates"] == 1
        assert stats["total_categories"] >= 5
        
        # Increment usage
        template_manager.increment_template_usage("test_email")
        
        # Check usage count
        metadata = template_manager.get_template_metadata("test_email")
        assert metadata["usage_count"] == 1
    
    def test_template_validation(self, template_manager):
        """Test template validation."""
        # Test invalid template (no name) - should raise ValidationError during creation
        with pytest.raises(ValidationError):
            MessageTemplate(
                id="invalid",
                name="",  # Empty name should fail validation
                channels=["email"],
                subject="Test",
                content="Test content"
            )
        
        # Test invalid template (no subject for email) - should raise ValidationError during creation
        with pytest.raises(ValidationError):
            MessageTemplate(
                id="invalid2",
                name="Valid Name",
                channels=["email"],
                subject="",  # Empty subject should fail validation for email
                content="Test content"
            )
        
        # Test valid template should work
        valid_template = MessageTemplate(
            id="valid",
            name="Valid Template",
            channels=["email"],
            subject="Valid Subject",
            content="Valid content"
        )
        
        # Should save successfully
        success = template_manager.save_template(valid_template, category_id="general")
        assert success is True


class TestTemplateCategory:
    """Test cases for TemplateCategory class."""
    
    def test_category_creation(self):
        """Test category creation and serialization."""
        category = TemplateCategory(
            "test_id",
            "Test Category",
            "Test description",
            "#FF0000"
        )
        
        assert category.id == "test_id"
        assert category.name == "Test Category"
        assert category.description == "Test description"
        assert category.color == "#FF0000"
    
    def test_category_serialization(self):
        """Test category to/from dict conversion."""
        category = TemplateCategory("test", "Test", "Description", "#FF0000")
        
        # Convert to dict
        data = category.to_dict()
        assert data["id"] == "test"
        assert data["name"] == "Test"
        assert data["description"] == "Description"
        assert data["color"] == "#FF0000"
        
        # Convert back from dict
        restored = TemplateCategory.from_dict(data)
        assert restored.id == category.id
        assert restored.name == category.name
        assert restored.description == category.description
        assert restored.color == category.color


if __name__ == "__main__":
    pytest.main([__file__])
