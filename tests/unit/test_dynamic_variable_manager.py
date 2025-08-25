"""
Unit tests for Dynamic Variable Manager.
"""

import pytest
from unittest.mock import Mock, patch

from src.multichannel_messaging.core.dynamic_variable_manager import (
    DynamicVariableManager,
    TemplateVariable
)


class TestTemplateVariable:
    """Test TemplateVariable class."""
    
    def test_format_for_template(self):
        """Test variable formatting for templates."""
        variable = TemplateVariable(
            name="Customer Name",
            variable_name="customer_name",
            data_type="text"
        )
        
        assert variable.format_for_template() == "{customer_name}"
    
    def test_validate_email(self):
        """Test email validation."""
        variable = TemplateVariable(
            name="Email",
            variable_name="email",
            data_type="email"
        )
        
        assert variable.validate_value("test@example.com") is True
        assert variable.validate_value("invalid-email") is False
        assert variable.validate_value("") is True  # Not required
        
        variable.is_required = True
        assert variable.validate_value("") is False  # Required but empty
    
    def test_validate_phone(self):
        """Test phone validation."""
        variable = TemplateVariable(
            name="Phone",
            variable_name="phone",
            data_type="phone"
        )
        
        assert variable.validate_value("+1234567890") is True
        assert variable.validate_value("(555) 123-4567") is True
        assert variable.validate_value("123") is False  # Too short
        assert variable.validate_value("abc") is False  # Invalid format
    
    def test_validate_number(self):
        """Test number validation."""
        variable = TemplateVariable(
            name="Count",
            variable_name="count",
            data_type="number"
        )
        
        assert variable.validate_value("123") is True
        assert variable.validate_value("123.45") is True
        assert variable.validate_value("abc") is False


class TestDynamicVariableManager:
    """Test DynamicVariableManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('src.multichannel_messaging.core.dynamic_variable_manager.get_i18n_manager') as mock_i18n:
            mock_i18n.return_value.tr.return_value = "test_translation"
            self.manager = DynamicVariableManager()
    
    def test_initialization(self):
        """Test manager initialization."""
        assert len(self.manager.available_variables) == 4  # Default variables
        assert len(self.manager.default_variables) == 4
        
        # Check default variables
        variable_names = [var.variable_name for var in self.manager.available_variables]
        assert "name" in variable_names
        assert "email" in variable_names
        assert "phone" in variable_names
        assert "company" in variable_names
    
    def test_format_variable_name(self):
        """Test variable name formatting."""
        # Test basic formatting
        assert self.manager._format_variable_name("Customer Name") == "customer_name"
        assert self.manager._format_variable_name("Email Address") == "email_address"
        assert self.manager._format_variable_name("Phone Number") == "phone_number"
        
        # Test special characters
        assert self.manager._format_variable_name("Customer's Name!") == "customer_s_name"
        assert self.manager._format_variable_name("Email@Domain") == "email_domain"
        
        # Test multiple underscores
        assert self.manager._format_variable_name("Customer   Name") == "customer_name"
        
        # Test leading numbers
        assert self.manager._format_variable_name("1st Name") == "col_1st_name"
        
        # Test empty string
        assert self.manager._format_variable_name("") == "unnamed_column"
    
    def test_detect_data_type(self):
        """Test data type detection."""
        # Test by column name
        assert self.manager._detect_data_type("Email") == "email"
        assert self.manager._detect_data_type("Phone Number") == "phone"
        assert self.manager._detect_data_type("Customer Count") == "number"
        assert self.manager._detect_data_type("Customer Name") == "text"
        
        # Test by sample value
        assert self.manager._detect_data_type("Unknown", "test@example.com") == "email"
        assert self.manager._detect_data_type("Unknown", "+1234567890") == "phone"
        assert self.manager._detect_data_type("Unknown", "123.45") == "number"
        assert self.manager._detect_data_type("Unknown", "John Doe") == "text"
    
    def test_generate_variables_from_csv(self):
        """Test variable generation from CSV columns."""
        csv_columns = ["Customer Name", "Email Address", "Phone Number", "Company"]
        sample_data = {
            "Customer Name": "John Doe",
            "Email Address": "john@example.com",
            "Phone Number": "+1234567890",
            "Company": "Example Corp"
        }
        
        variables = self.manager.generate_variables_from_csv(csv_columns, sample_data)
        
        assert len(variables) == 4
        
        # Check variable names
        variable_names = [var.variable_name for var in variables]
        assert "customer_name" in variable_names
        assert "email_address" in variable_names
        assert "phone_number" in variable_names
        assert "company" in variable_names
        
        # Check data types
        email_var = next(var for var in variables if var.variable_name == "email_address")
        assert email_var.data_type == "email"
        
        phone_var = next(var for var in variables if var.variable_name == "phone_number")
        assert phone_var.data_type == "phone"
    
    def test_update_available_variables(self):
        """Test updating available variables."""
        # Test with CSV columns
        csv_columns = ["Name", "Email"]
        sample_data = {"Name": "John", "Email": "john@example.com"}
        
        callback_called = False
        def test_callback(variables):
            nonlocal callback_called
            callback_called = True
        
        self.manager.add_change_callback(test_callback)
        self.manager.update_available_variables(csv_columns, sample_data)
        
        assert len(self.manager.available_variables) == 2
        assert callback_called
        
        # Test with empty columns (should reset to defaults)
        self.manager.update_available_variables([])
        assert len(self.manager.available_variables) == 4  # Default variables
    
    def test_get_variable_by_name(self):
        """Test getting variable by name."""
        variable = self.manager.get_variable_by_name("name")
        assert variable is not None
        assert variable.variable_name == "name"
        
        variable = self.manager.get_variable_by_name("nonexistent")
        assert variable is None
    
    def test_get_variables_by_type(self):
        """Test getting variables by type."""
        email_vars = self.manager.get_variables_by_type("email")
        assert len(email_vars) == 1
        assert email_vars[0].variable_name == "email"
        
        text_vars = self.manager.get_variables_by_type("text")
        assert len(text_vars) >= 2  # name and company
    
    def test_search_variables(self):
        """Test variable search."""
        results = self.manager.search_variables("name")
        assert len(results) >= 1
        assert any(var.variable_name == "name" for var in results)
        
        results = self.manager.search_variables("email")
        assert len(results) >= 1
        assert any(var.variable_name == "email" for var in results)
        
        results = self.manager.search_variables("nonexistent")
        assert len(results) == 0
    
    def test_validate_template_variables(self):
        """Test template variable validation."""
        template_content = "Hello {name}, welcome to {company}!"
        missing = self.manager.validate_template_variables(template_content)
        assert len(missing) == 0  # Both variables exist in defaults
        
        template_content = "Hello {name}, your {nonexistent_var} is ready!"
        missing = self.manager.validate_template_variables(template_content)
        assert len(missing) == 1
        assert "nonexistent_var" in missing
    
    def test_get_variable_suggestions(self):
        """Test variable suggestions for autocomplete."""
        suggestions = self.manager.get_variable_suggestions("na")
        assert len(suggestions) >= 1
        assert any(var.variable_name.startswith("na") for var in suggestions)
        
        suggestions = self.manager.get_variable_suggestions("email")
        assert len(suggestions) >= 1
        assert suggestions[0].variable_name == "email"  # Exact match first
    
    def test_change_callbacks(self):
        """Test change callback management."""
        callback1_called = False
        callback2_called = False
        
        def callback1(variables):
            nonlocal callback1_called
            callback1_called = True
        
        def callback2(variables):
            nonlocal callback2_called
            callback2_called = True
        
        # Add callbacks
        self.manager.add_change_callback(callback1)
        self.manager.add_change_callback(callback2)
        
        # Trigger change
        self.manager.update_available_variables(["Test"])
        
        assert callback1_called
        assert callback2_called
        
        # Remove callback
        callback1_called = False
        callback2_called = False
        self.manager.remove_change_callback(callback1)
        
        # Trigger change again
        self.manager.update_available_variables(["Test2"])
        
        assert not callback1_called
        assert callback2_called