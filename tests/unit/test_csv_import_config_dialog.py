"""
Unit tests for CSV Import Configuration Dialog.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch
import pandas as pd

from src.multichannel_messaging.gui.csv_import_config_dialog import (
    CSVImportConfiguration, CSVImportConfigDialog
)
from src.multichannel_messaging.utils.exceptions import ValidationError


class TestCSVImportConfiguration:
    """Test CSV import configuration functionality."""
    
    def test_configuration_creation(self):
        """Test creating a basic configuration."""
        config = CSVImportConfiguration(
            template_name="Test Template",
            description="Test description",
            messaging_channels=["email"]
        )
        
        assert config.template_name == "Test Template"
        assert config.description == "Test description"
        assert config.messaging_channels == ["email"]
        assert config.encoding == "utf-8"
        assert config.delimiter == ","
        assert config.has_header is True
    
    def test_configuration_validation_email_only(self):
        """Test configuration validation for email-only messaging."""
        config = CSVImportConfiguration(
            template_name="Email Template",
            messaging_channels=["email"],
            column_mapping={"Name": "name", "Email": "email"}
        )
        
        errors = config.validate_configuration()
        assert len(errors) == 0
    
    def test_configuration_validation_whatsapp_only(self):
        """Test configuration validation for WhatsApp-only messaging."""
        config = CSVImportConfiguration(
            template_name="WhatsApp Template",
            messaging_channels=["whatsapp"],
            column_mapping={"Name": "name", "Phone": "phone"}
        )
        
        errors = config.validate_configuration()
        assert len(errors) == 0
    
    def test_configuration_validation_missing_fields(self):
        """Test configuration validation with missing required fields."""
        config = CSVImportConfiguration(
            template_name="Incomplete Template",
            messaging_channels=["email", "whatsapp"],
            column_mapping={"Name": "name"}  # Missing email and phone
        )
        
        errors = config.validate_configuration()
        assert len(errors) > 0
        assert any("Missing required fields" in str(error) for error in errors)
    
    def test_configuration_validation_empty_template_name(self):
        """Test configuration validation with empty template name."""
        config = CSVImportConfiguration(
            template_name="",
            messaging_channels=["email"],
            column_mapping={"Name": "name", "Email": "email"}
        )
        
        errors = config.validate_configuration()
        assert len(errors) > 0
        assert any("Template name is required" in str(error) for error in errors)
    
    def test_apply_to_csv(self):
        """Test applying configuration to CSV data."""
        # Create test DataFrame
        test_data = pd.DataFrame({
            "Full Name": ["John Doe", "Jane Smith"],
            "Email Address": ["john@example.com", "jane@example.com"],
            "Company Name": ["Acme Corp", "Tech Inc"],
            "Phone Number": ["+1234567890", "+0987654321"]
        })
        
        config = CSVImportConfiguration(
            template_name="Test Template",
            column_mapping={
                "Full Name": "name",
                "Email Address": "email",
                "Company Name": "company",
                "Phone Number": "phone"
            }
        )
        
        result = config.apply_to_csv(test_data)
        
        assert "name" in result.columns
        assert "email" in result.columns
        assert "company" in result.columns
        assert "phone" in result.columns
        assert len(result) == 2
        assert result.iloc[0]["name"] == "John Doe"
        assert result.iloc[0]["email"] == "john@example.com"
    
    def test_configuration_serialization(self):
        """Test configuration to/from dictionary conversion."""
        config = CSVImportConfiguration(
            template_name="Serialization Test",
            description="Test serialization",
            messaging_channels=["email", "whatsapp"],
            column_mapping={"Name": "name", "Email": "email", "Phone": "phone"},
            encoding="utf-8",
            delimiter=",",
            has_header=True,
            skip_rows=1
        )
        
        # Convert to dictionary
        config_dict = config.to_dict()
        
        # Verify dictionary structure
        assert config_dict["template_name"] == "Serialization Test"
        assert config_dict["description"] == "Test serialization"
        assert config_dict["messaging_channels"] == ["email", "whatsapp"]
        assert config_dict["column_mapping"] == {"Name": "name", "Email": "email", "Phone": "phone"}
        
        # Convert back from dictionary
        restored_config = CSVImportConfiguration.from_dict(config_dict)
        
        # Verify restored configuration
        assert restored_config.template_name == config.template_name
        assert restored_config.description == config.description
        assert restored_config.messaging_channels == config.messaging_channels
        assert restored_config.column_mapping == config.column_mapping
        assert restored_config.encoding == config.encoding
        assert restored_config.delimiter == config.delimiter
        assert restored_config.has_header == config.has_header
        assert restored_config.skip_rows == config.skip_rows


@pytest.fixture
def sample_csv_file():
    """Create a sample CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("Name,Email,Company,Phone\n")
        f.write("John Doe,john@example.com,Acme Corp,+1234567890\n")
        f.write("Jane Smith,jane@example.com,Tech Inc,+0987654321\n")
        f.write("Bob Johnson,bob@example.com,StartUp LLC,+1122334455\n")
        
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


class TestCSVImportConfigDialog:
    """Test CSV import configuration dialog functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_qt_app(self, qtbot):
        """Set up Qt application for testing."""
        self.qtbot = qtbot
    
    def test_dialog_creation(self, sample_csv_file):
        """Test creating the dialog with a CSV file."""
        with patch('src.multichannel_messaging.gui.csv_import_config_dialog.get_i18n_manager') as mock_i18n:
            mock_i18n.return_value.tr.side_effect = lambda x, **kwargs: x
            
            dialog = CSVImportConfigDialog(file_path=str(sample_csv_file))
            self.qtbot.addWidget(dialog)
            
            assert dialog.file_path == str(sample_csv_file)
            assert dialog.configuration.template_name == ""
            assert dialog.tab_widget.count() == 4  # 4 tabs
    
    def test_auto_detect_mapping(self, sample_csv_file):
        """Test automatic column mapping detection."""
        with patch('src.multichannel_messaging.gui.csv_import_config_dialog.get_i18n_manager') as mock_i18n:
            mock_i18n.return_value.tr.side_effect = lambda x, **kwargs: x
            
            dialog = CSVImportConfigDialog(file_path=str(sample_csv_file))
            self.qtbot.addWidget(dialog)
            
            # Test auto-detection
            assert dialog.auto_detect_mapping("Name") == "name"
            assert dialog.auto_detect_mapping("Email") == "email"
            assert dialog.auto_detect_mapping("Company") == "company"
            assert dialog.auto_detect_mapping("Phone") == "phone"
            
            # Test case insensitive detection
            assert dialog.auto_detect_mapping("FULL_NAME") == "name"
            assert dialog.auto_detect_mapping("email_address") == "email"
            assert dialog.auto_detect_mapping("company_name") == "company"
            assert dialog.auto_detect_mapping("phone_number") == "phone"
    
    def test_configuration_update_from_ui(self, sample_csv_file):
        """Test updating configuration from UI elements."""
        with patch('src.multichannel_messaging.gui.csv_import_config_dialog.get_i18n_manager') as mock_i18n:
            mock_i18n.return_value.tr.side_effect = lambda x, **kwargs: x
            
            dialog = CSVImportConfigDialog(file_path=str(sample_csv_file))
            self.qtbot.addWidget(dialog)
            
            # Set UI values
            dialog.template_name_edit.setText("Test Template")
            dialog.description_edit.setPlainText("Test Description")
            dialog.encoding_combo.setCurrentText("utf-8")
            dialog.delimiter_combo.setCurrentText(";")
            dialog.has_header_check.setChecked(False)
            dialog.skip_rows_spin.setValue(2)
            dialog.email_check.setChecked(True)
            dialog.whatsapp_check.setChecked(False)
            
            # Update configuration
            dialog.update_configuration_from_ui()
            
            # Verify configuration
            assert dialog.configuration.template_name == "Test Template"
            assert dialog.configuration.description == "Test Description"
            assert dialog.configuration.encoding == "utf-8"
            assert dialog.configuration.delimiter == ";"
            assert dialog.configuration.has_header is False
            assert dialog.configuration.skip_rows == 2
            assert dialog.configuration.messaging_channels == ["email"]
    
    def test_template_save_and_load(self, sample_csv_file, tmp_path):
        """Test saving and loading configuration templates."""
        with patch('src.multichannel_messaging.gui.csv_import_config_dialog.get_i18n_manager') as mock_i18n:
            mock_i18n.return_value.tr.side_effect = lambda x, **kwargs: x
            
            dialog = CSVImportConfigDialog(file_path=str(sample_csv_file))
            self.qtbot.addWidget(dialog)
            
            # Override templates directory for testing
            dialog.templates_dir = tmp_path
            
            # Set up configuration
            dialog.template_name_edit.setText("Test Template")
            dialog.description_edit.setPlainText("Test Description")
            dialog.email_check.setChecked(True)
            dialog.whatsapp_check.setChecked(False)
            dialog.update_configuration_from_ui()
            
            # Save template
            template_file = tmp_path / "Test Template.json"
            dialog.save_template_to_file(template_file)
            
            # Verify file was created
            assert template_file.exists()
            
            # Load and verify template content
            with open(template_file, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            assert template_data["template_name"] == "Test Template"
            assert template_data["description"] == "Test Description"
            assert template_data["messaging_channels"] == ["email"]
    
    def test_validation_error_display(self, sample_csv_file):
        """Test validation error display."""
        with patch('src.multichannel_messaging.gui.csv_import_config_dialog.get_i18n_manager') as mock_i18n:
            mock_i18n.return_value.tr.side_effect = lambda x, **kwargs: x
            
            dialog = CSVImportConfigDialog(file_path=str(sample_csv_file))
            self.qtbot.addWidget(dialog)
            
            # Set up invalid configuration (no template name, no channels)
            dialog.template_name_edit.setText("")
            dialog.email_check.setChecked(False)
            dialog.whatsapp_check.setChecked(False)
            dialog.update_configuration_from_ui()
            
            # Validate configuration
            is_valid = dialog.validate_configuration()
            
            # Should be invalid
            assert not is_valid
            
            # Validation text should show errors
            validation_text = dialog.validation_text.toPlainText()
            assert "Template name is required" in validation_text or len(validation_text) > 0


if __name__ == "__main__":
    pytest.main([__file__])