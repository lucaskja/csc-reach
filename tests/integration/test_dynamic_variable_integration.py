"""
Integration tests for Dynamic Variable Management System.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from src.multichannel_messaging.core.dynamic_variable_manager import DynamicVariableManager
from src.multichannel_messaging.gui.variables_panel import VariablesPanel


@pytest.fixture
def app():
    """Create QApplication for GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def sample_csv_data():
    """Create sample CSV data for testing."""
    return pd.DataFrame({
        'Customer Name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
        'Email Address': ['john@example.com', 'jane@example.com', 'bob@example.com'],
        'Phone Number': ['+1234567890', '+0987654321', '+1122334455'],
        'Company Name': ['Acme Corp', 'Tech Solutions', 'Global Industries'],
        'Purchase Amount': ['100.50', '250.00', '75.25']
    })


class TestDynamicVariableIntegration:
    """Integration tests for the complete dynamic variable system."""
    
    @patch('src.multichannel_messaging.core.dynamic_variable_manager.get_i18n_manager')
    @patch('src.multichannel_messaging.gui.variables_panel.get_i18n_manager')
    def test_csv_to_variables_workflow(self, mock_panel_i18n, mock_manager_i18n, app, sample_csv_data):
        """Test complete workflow from CSV import to variable display."""
        # Mock i18n managers
        mock_manager_i18n.return_value.tr.return_value = "test_translation"
        mock_panel_i18n.return_value.tr.return_value = "test_translation"
        
        # Create components
        manager = DynamicVariableManager()
        panel = VariablesPanel()
        
        # Connect the panel to use the same manager
        panel.variable_manager = manager
        manager.add_change_callback(panel.on_variables_changed)
        
        # Simulate CSV import
        csv_columns = list(sample_csv_data.columns)
        sample_data = sample_csv_data.iloc[0].to_dict()
        
        # Update variables from CSV
        manager.update_available_variables(csv_columns, sample_data)
        
        # Verify variables were created correctly
        variables = manager.get_available_variables()
        assert len(variables) == 5  # All CSV columns
        
        # Check variable names and types
        variable_names = [var.variable_name for var in variables]
        assert 'customer_name' in variable_names
        assert 'email_address' in variable_names
        assert 'phone_number' in variable_names
        assert 'company_name' in variable_names
        assert 'purchase_amount' in variable_names
        
        # Check data types were detected correctly
        email_var = next(var for var in variables if var.variable_name == 'email_address')
        assert email_var.data_type == 'email'
        
        phone_var = next(var for var in variables if var.variable_name == 'phone_number')
        assert phone_var.data_type == 'phone'
        
        amount_var = next(var for var in variables if var.variable_name == 'purchase_amount')
        assert amount_var.data_type == 'number'
        
        # Verify panel displays the variables
        assert panel.variable_list_widget.count() == 5
    
    @patch('src.multichannel_messaging.core.dynamic_variable_manager.get_i18n_manager')
    @patch('src.multichannel_messaging.gui.variables_panel.get_i18n_manager')
    def test_variable_search_and_selection(self, mock_panel_i18n, mock_manager_i18n, app, sample_csv_data):
        """Test variable search and selection functionality."""
        # Mock i18n managers
        mock_manager_i18n.return_value.tr.return_value = "test_translation"
        mock_panel_i18n.return_value.tr.return_value = "test_translation"
        
        # Create components
        manager = DynamicVariableManager()
        panel = VariablesPanel()
        
        # Connect the panel to use the same manager
        panel.variable_manager = manager
        manager.add_change_callback(panel.on_variables_changed)
        
        # Update with CSV data
        csv_columns = list(sample_csv_data.columns)
        sample_data = sample_csv_data.iloc[0].to_dict()
        manager.update_available_variables(csv_columns, sample_data)
        
        # Test search functionality
        panel.search_box.setText("email")
        panel.on_search_changed("email")
        
        # Should show only email-related variables
        assert panel.variable_list_widget.count() == 1
        item = panel.variable_list_widget.item(0)
        # Check for the actual variable name that was generated
        assert "email_address" in item.text()
        
        # Test selection
        panel.variable_list_widget.setCurrentRow(0)
        selected_var = panel.get_selected_variable()
        assert selected_var.variable_name == "email_address"
        
        # Clear search
        panel.clear_search()
        assert panel.variable_list_widget.count() == 5  # All variables back
    
    @patch('src.multichannel_messaging.core.dynamic_variable_manager.get_i18n_manager')
    @patch('src.multichannel_messaging.gui.variables_panel.get_i18n_manager')
    def test_template_variable_validation(self, mock_panel_i18n, mock_manager_i18n, app, sample_csv_data):
        """Test template variable validation with CSV data."""
        # Mock i18n managers
        mock_manager_i18n.return_value.tr.return_value = "test_translation"
        mock_panel_i18n.return_value.tr.return_value = "test_translation"
        
        # Create manager and update with CSV data
        manager = DynamicVariableManager()
        csv_columns = list(sample_csv_data.columns)
        sample_data = sample_csv_data.iloc[0].to_dict()
        manager.update_available_variables(csv_columns, sample_data)
        
        # Test valid template
        valid_template = "Hello {customer_name}, your order from {company_name} is ready!"
        missing_vars = manager.validate_template_variables(valid_template)
        assert len(missing_vars) == 0
        
        # Test template with missing variables
        invalid_template = "Hello {customer_name}, your {nonexistent_var} is ready!"
        missing_vars = manager.validate_template_variables(invalid_template)
        assert len(missing_vars) == 1
        assert "nonexistent_var" in missing_vars
        
        # Test template with mixed valid/invalid variables
        mixed_template = "Hello {customer_name}, your {email_address} and {invalid_var} are here!"
        missing_vars = manager.validate_template_variables(mixed_template)
        assert len(missing_vars) == 1
        assert "invalid_var" in missing_vars
    
    @patch('src.multichannel_messaging.core.dynamic_variable_manager.get_i18n_manager')
    @patch('src.multichannel_messaging.gui.variables_panel.get_i18n_manager')
    def test_variable_insertion_signal(self, mock_panel_i18n, mock_manager_i18n, app, sample_csv_data):
        """Test variable insertion signal emission."""
        # Mock i18n managers
        mock_manager_i18n.return_value.tr.return_value = "test_translation"
        mock_panel_i18n.return_value.tr.return_value = "test_translation"
        
        # Create components
        manager = DynamicVariableManager()
        panel = VariablesPanel()
        
        # Connect the panel to use the same manager
        panel.variable_manager = manager
        manager.add_change_callback(panel.on_variables_changed)
        
        # Update with CSV data
        csv_columns = list(sample_csv_data.columns)
        sample_data = sample_csv_data.iloc[0].to_dict()
        manager.update_available_variables(csv_columns, sample_data)
        
        # Track signal emissions
        signals_received = []
        
        def on_variable_selected(variable_format):
            signals_received.append(variable_format)
        
        panel.variable_selected.connect(on_variable_selected)
        
        # Test double-click insertion
        panel.variable_list_widget.setCurrentRow(0)  # Select first variable
        item = panel.variable_list_widget.item(0)
        panel.on_variable_double_clicked(item)
        
        assert len(signals_received) == 1
        # Check the actual variable that was generated
        first_var = manager.get_available_variables()[0]
        assert signals_received[0] == first_var.format_for_template()
        
        # Test button insertion
        panel.variable_list_widget.setCurrentRow(1)  # Select second variable
        panel.insert_selected_variable()
        
        assert len(signals_received) == 2
        second_var = manager.get_available_variables()[1]
        assert signals_received[1] == second_var.format_for_template()
    
    @patch('src.multichannel_messaging.core.dynamic_variable_manager.get_i18n_manager')
    @patch('src.multichannel_messaging.gui.variables_panel.get_i18n_manager')
    def test_variable_change_callbacks(self, mock_panel_i18n, mock_manager_i18n, app, sample_csv_data):
        """Test variable change callback system."""
        # Mock i18n managers
        mock_manager_i18n.return_value.tr.return_value = "test_translation"
        mock_panel_i18n.return_value.tr.return_value = "test_translation"
        
        # Create components
        manager = DynamicVariableManager()
        panel = VariablesPanel()
        
        # Track callback calls
        callback_calls = []
        
        def test_callback(variables):
            callback_calls.append(len(variables))
        
        manager.add_change_callback(test_callback)
        
        # Initial state should have default variables
        assert len(callback_calls) == 0  # No callback yet
        
        # Update with CSV data
        csv_columns = list(sample_csv_data.columns)
        sample_data = sample_csv_data.iloc[0].to_dict()
        manager.update_available_variables(csv_columns, sample_data)
        
        # Callback should have been called
        assert len(callback_calls) == 1
        assert callback_calls[0] == 5  # 5 CSV columns
        
        # Reset to defaults
        manager.update_available_variables([])
        
        # Callback should have been called again
        assert len(callback_calls) == 2
        assert callback_calls[1] == 4  # 4 default variables
    
    @patch('src.multichannel_messaging.core.dynamic_variable_manager.get_i18n_manager')
    def test_variable_suggestions(self, mock_manager_i18n, sample_csv_data):
        """Test variable suggestion system."""
        # Mock i18n manager
        mock_manager_i18n.return_value.tr.return_value = "test_translation"
        
        # Create manager and update with CSV data
        manager = DynamicVariableManager()
        csv_columns = list(sample_csv_data.columns)
        sample_data = sample_csv_data.iloc[0].to_dict()
        manager.update_available_variables(csv_columns, sample_data)
        
        # Test suggestions for partial matches
        suggestions = manager.get_variable_suggestions("cust")
        assert len(suggestions) >= 1
        assert any("customer" in var.variable_name for var in suggestions)
        
        suggestions = manager.get_variable_suggestions("email")
        assert len(suggestions) >= 1
        assert suggestions[0].variable_name == "email_address"  # Exact match first
        
        suggestions = manager.get_variable_suggestions("comp")
        assert len(suggestions) >= 1
        assert any("company" in var.variable_name for var in suggestions)
        
        # Test no matches
        suggestions = manager.get_variable_suggestions("xyz")
        assert len(suggestions) == 0
    
    @patch('src.multichannel_messaging.core.dynamic_variable_manager.get_i18n_manager')
    def test_data_type_detection_accuracy(self, mock_manager_i18n, sample_csv_data):
        """Test accuracy of data type detection."""
        # Mock i18n manager
        mock_manager_i18n.return_value.tr.return_value = "test_translation"
        
        # Create manager
        manager = DynamicVariableManager()
        
        # Test various column names and sample values
        test_cases = [
            ("Email", "john@example.com", "email"),
            ("Customer Email", "jane@test.org", "email"),
            ("Phone", "+1234567890", "phone"),
            ("Mobile Number", "(555) 123-4567", "phone"),
            ("WhatsApp", "+44 20 7946 0958", "phone"),
            ("Count", "42", "number"),
            ("Price", "99.99", "number"),
            ("Amount", "1,234.56", "number"),
            ("Name", "John Doe", "text"),
            ("Description", "Some text here", "text"),
            ("Unknown Column", "random value", "text"),
        ]
        
        for column_name, sample_value, expected_type in test_cases:
            detected_type = manager._detect_data_type(column_name, sample_value)
            assert detected_type == expected_type, f"Failed for {column_name}: expected {expected_type}, got {detected_type}"