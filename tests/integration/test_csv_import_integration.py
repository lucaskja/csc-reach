"""
Integration tests for CSV import functionality.
"""

import pytest
import tempfile
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch

from src.multichannel_messaging.gui.csv_import_config_dialog import CSVImportConfiguration
from src.multichannel_messaging.core.models import Customer


class TestCSVImportIntegration:
    """Test CSV import integration functionality."""
    
    @pytest.fixture
    def sample_csv_data(self):
        """Create sample CSV data for testing."""
        return pd.DataFrame({
            "Full Name": ["John Doe", "Jane Smith", "Bob Johnson"],
            "Email Address": ["john@example.com", "jane@example.com", "bob@example.com"],
            "Company Name": ["Acme Corp", "Tech Inc", "StartUp LLC"],
            "Phone Number": ["+1234567890", "+0987654321", "+1122334455"]
        })
    
    @pytest.fixture
    def sample_csv_file(self, sample_csv_data):
        """Create a sample CSV file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_csv_data.to_csv(f, index=False)
            temp_path = Path(f.name)
        
        yield temp_path
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
    
    def test_end_to_end_csv_processing(self, sample_csv_data):
        """Test end-to-end CSV processing with configuration."""
        # Create configuration
        config = CSVImportConfiguration(
            template_name="Integration Test",
            description="Test end-to-end processing",
            messaging_channels=["email", "whatsapp"],
            column_mapping={
                "Full Name": "name",
                "Email Address": "email",
                "Company Name": "company",
                "Phone Number": "phone"
            }
        )
        
        # Apply configuration to data
        processed_data = config.apply_to_csv(sample_csv_data)
        
        # Verify processed data structure
        assert "name" in processed_data.columns
        assert "email" in processed_data.columns
        assert "company" in processed_data.columns
        assert "phone" in processed_data.columns
        assert len(processed_data) == 3
        
        # Convert to Customer objects (simulating main window processing)
        customers = []
        for index, row in processed_data.iterrows():
            customer = Customer(
                name=str(row["name"]).strip(),
                company=str(row["company"]).strip(),
                email=str(row["email"]).strip(),
                phone=str(row["phone"]).strip()
            )
            customers.append(customer)
        
        # Verify Customer objects
        assert len(customers) == 3
        assert customers[0].name == "John Doe"
        assert customers[0].email == "john@example.com"
        assert customers[0].company == "Acme Corp"
        assert customers[0].phone == "+1234567890"
        
        assert customers[1].name == "Jane Smith"
        assert customers[1].email == "jane@example.com"
        assert customers[1].company == "Tech Inc"
        assert customers[1].phone == "+0987654321"
    
    def test_email_only_configuration(self, sample_csv_data):
        """Test configuration for email-only messaging."""
        config = CSVImportConfiguration(
            template_name="Email Only Test",
            messaging_channels=["email"],
            column_mapping={
                "Full Name": "name",
                "Email Address": "email",
                "Company Name": "company"
            }
        )
        
        # Validate configuration
        errors = config.validate_configuration()
        assert len(errors) == 0
        
        # Apply configuration
        processed_data = config.apply_to_csv(sample_csv_data)
        
        # Verify only required fields are present
        assert "name" in processed_data.columns
        assert "email" in processed_data.columns
        assert "company" in processed_data.columns
        # Phone is not required for email-only, but may be present if mapped
    
    def test_whatsapp_only_configuration(self, sample_csv_data):
        """Test configuration for WhatsApp-only messaging."""
        config = CSVImportConfiguration(
            template_name="WhatsApp Only Test",
            messaging_channels=["whatsapp"],
            column_mapping={
                "Full Name": "name",
                "Phone Number": "phone",
                "Company Name": "company"
            }
        )
        
        # Validate configuration
        errors = config.validate_configuration()
        assert len(errors) == 0
        
        # Apply configuration
        processed_data = config.apply_to_csv(sample_csv_data)
        
        # Verify required fields are present
        assert "name" in processed_data.columns
        assert "phone" in processed_data.columns
        assert "company" in processed_data.columns
    
    def test_selective_column_import(self, sample_csv_data):
        """Test importing only selected columns."""
        # Configuration that only imports name and email
        config = CSVImportConfiguration(
            template_name="Selective Import Test",
            messaging_channels=["email"],
            column_mapping={
                "Full Name": "name",
                "Email Address": "email"
                # Deliberately omitting company and phone
            }
        )
        
        # Apply configuration
        processed_data = config.apply_to_csv(sample_csv_data)
        
        # Verify only mapped columns are present
        assert "name" in processed_data.columns
        assert "email" in processed_data.columns
        assert "company" not in processed_data.columns
        assert "phone" not in processed_data.columns
        assert len(processed_data.columns) == 2
        
        # Verify data integrity
        assert processed_data.iloc[0]["name"] == "John Doe"
        assert processed_data.iloc[0]["email"] == "john@example.com"
    
    def test_configuration_validation_scenarios(self):
        """Test various configuration validation scenarios."""
        # Valid email configuration
        email_config = CSVImportConfiguration(
            template_name="Valid Email Config",
            messaging_channels=["email"],
            column_mapping={"Name": "name", "Email": "email"}
        )
        assert len(email_config.validate_configuration()) == 0
        
        # Valid WhatsApp configuration
        whatsapp_config = CSVImportConfiguration(
            template_name="Valid WhatsApp Config",
            messaging_channels=["whatsapp"],
            column_mapping={"Name": "name", "Phone": "phone"}
        )
        assert len(whatsapp_config.validate_configuration()) == 0
        
        # Valid multi-channel configuration
        multi_config = CSVImportConfiguration(
            template_name="Valid Multi Config",
            messaging_channels=["email", "whatsapp"],
            column_mapping={"Name": "name", "Email": "email", "Phone": "phone"}
        )
        assert len(multi_config.validate_configuration()) == 0
        
        # Invalid: missing required fields
        invalid_config = CSVImportConfiguration(
            template_name="Invalid Config",
            messaging_channels=["email", "whatsapp"],
            column_mapping={"Name": "name"}  # Missing email and phone
        )
        errors = invalid_config.validate_configuration()
        assert len(errors) > 0
        assert any("Missing required fields" in str(error) for error in errors)
        
        # Invalid: empty template name
        empty_name_config = CSVImportConfiguration(
            template_name="",
            messaging_channels=["email"],
            column_mapping={"Name": "name", "Email": "email"}
        )
        errors = empty_name_config.validate_configuration()
        assert len(errors) > 0
        assert any("Template name is required" in str(error) for error in errors)
    
    def test_template_persistence(self, tmp_path):
        """Test saving and loading configuration templates."""
        # Create configuration
        config = CSVImportConfiguration(
            template_name="Persistence Test",
            description="Test template persistence",
            messaging_channels=["email", "whatsapp"],
            column_mapping={
                "Name": "name",
                "Email": "email",
                "Phone": "phone",
                "Company": "company"
            },
            encoding="utf-8",
            delimiter=",",
            has_header=True,
            skip_rows=0
        )
        
        # Save to file
        template_file = tmp_path / "test_template.json"
        template_data = config.to_dict()
        
        import json
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, indent=2)
        
        # Load from file
        with open(template_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        loaded_config = CSVImportConfiguration.from_dict(loaded_data)
        
        # Verify loaded configuration matches original
        assert loaded_config.template_name == config.template_name
        assert loaded_config.description == config.description
        assert loaded_config.messaging_channels == config.messaging_channels
        assert loaded_config.column_mapping == config.column_mapping
        assert loaded_config.encoding == config.encoding
        assert loaded_config.delimiter == config.delimiter
        assert loaded_config.has_header == config.has_header
        assert loaded_config.skip_rows == config.skip_rows
    
    def test_error_handling_scenarios(self, sample_csv_data):
        """Test error handling in various scenarios."""
        # Test with missing required data
        incomplete_data = sample_csv_data.copy()
        incomplete_data.loc[1, "Email Address"] = ""  # Missing email for one row
        
        config = CSVImportConfiguration(
            template_name="Error Test",
            messaging_channels=["email"],
            column_mapping={
                "Full Name": "name",
                "Email Address": "email"
            }
        )
        
        processed_data = config.apply_to_csv(incomplete_data)
        
        # Simulate error detection during Customer creation
        customers = []
        errors = []
        
        for index, row in processed_data.iterrows():
            try:
                name = str(row["name"]).strip()
                email = str(row["email"]).strip()
                
                if not name or name == "nan":
                    errors.append(f"Row {index + 1}: Name is required")
                    continue
                
                if not email or email == "nan" or email == "":
                    errors.append(f"Row {index + 1}: Email is required for email messaging")
                    continue
                
                customer = Customer(
                    name=name,
                    company="Test Company",  # Provide required company
                    email=email,
                    phone="+1234567890"  # Provide required phone
                )
                customers.append(customer)
                
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")
        
        # Verify error detection
        assert len(errors) > 0
        assert any("Email is required" in error for error in errors)
        assert len(customers) == 2  # Should have 2 valid customers (rows 0 and 2)


if __name__ == "__main__":
    pytest.main([__file__])