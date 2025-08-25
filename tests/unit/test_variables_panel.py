"""
Unit tests for Variables Panel GUI component.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from src.multichannel_messaging.gui.variables_panel import (
    VariablesPanel,
    VariableListItem,
    CompactVariablesPanel
)
from src.multichannel_messaging.core.dynamic_variable_manager import TemplateVariable


@pytest.fixture
def app():
    """Create QApplication for GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def sample_variable():
    """Create a sample template variable."""
    return TemplateVariable(
        name="Customer Name",
        variable_name="customer_name",
        data_type="text",
        sample_value="John Doe",
        description="Customer's full name"
    )


class TestVariableListItem:
    """Test VariableListItem class."""
    
    def test_initialization(self, app, sample_variable):
        """Test item initialization."""
        item = VariableListItem(sample_variable)
        
        assert item.variable == sample_variable
        assert "{customer_name}" in item.text()
        assert "Customer's full name" in item.text()
        assert "text" in item.text()
    
    def test_update_display(self, app, sample_variable):
        """Test display update."""
        item = VariableListItem(sample_variable)
        
        # Modify variable
        sample_variable.description = "Updated description"
        item.update_display()
        
        assert "Updated description" in item.text()
    
    def test_tooltip(self, app, sample_variable):
        """Test tooltip content."""
        item = VariableListItem(sample_variable)
        
        tooltip = item.toolTip()
        assert "Variable: {customer_name}" in tooltip
        assert "Original Name: Customer Name" in tooltip
        assert "Type: text" in tooltip
        assert "Sample: John Doe" in tooltip
        assert "Description: Customer's full name" in tooltip


class TestVariablesPanel:
    """Test VariablesPanel class."""
    
    @patch('src.multichannel_messaging.gui.variables_panel.get_i18n_manager')
    def test_initialization(self, mock_i18n, app):
        """Test panel initialization."""
        mock_i18n.return_value.tr.return_value = "test_translation"
        
        panel = VariablesPanel()
        
        assert panel.variable_manager is not None
        assert panel.search_box is not None
        assert panel.variable_list_widget is not None
        assert panel.info_label is not None
        assert panel.insert_button is not None
        
        # Should start with default variables
        assert panel.variable_list_widget.count() == 4  # Default variables
    
    @patch('src.multichannel_messaging.gui.variables_panel.get_i18n_manager')
    def test_update_variables_display(self, mock_i18n, app, sample_variable):
        """Test updating variables display."""
        mock_i18n.return_value.tr.return_value = "test_translation"
        
        panel = VariablesPanel()
        variables = [sample_variable]
        
        panel.update_variables_display(variables)
        
        assert panel.variable_list_widget.count() == 1
        item = panel.variable_list_widget.item(0)
        assert isinstance(item, VariableListItem)
        assert item.variable == sample_variable
    
    @patch('src.multichannel_messaging.gui.variables_panel.get_i18n_manager')
    def test_search_functionality(self, mock_i18n, app):
        """Test search functionality."""
        mock_i18n.return_value.tr.return_value = "test_translation"
        
        panel = VariablesPanel()
        
        # Test search
        panel.search_box.setText("name")
        panel.on_search_changed("name")
        
        # Should filter to variables containing "name"
        assert panel.variable_list_widget.count() >= 1
        
        # Test clear search
        panel.clear_search()
        assert panel.search_box.text() == ""
    
    @patch('src.multichannel_messaging.gui.variables_panel.get_i18n_manager')
    def test_variable_selection_signal(self, mock_i18n, app, sample_variable):
        """Test variable selection signal emission."""
        mock_i18n.return_value.tr.return_value = "test_translation"
        
        panel = VariablesPanel()
        variables = [sample_variable]
        panel.update_variables_display(variables)
        
        # Mock signal connection
        signal_emitted = False
        emitted_value = None
        
        def on_signal(value):
            nonlocal signal_emitted, emitted_value
            signal_emitted = True
            emitted_value = value
        
        panel.variable_selected.connect(on_signal)
        
        # Simulate double-click
        item = panel.variable_list_widget.item(0)
        panel.on_variable_double_clicked(item)
        
        assert signal_emitted
        assert emitted_value == "{customer_name}"
    
    @patch('src.multichannel_messaging.gui.variables_panel.get_i18n_manager')
    def test_insert_selected_variable(self, mock_i18n, app, sample_variable):
        """Test inserting selected variable."""
        mock_i18n.return_value.tr.return_value = "test_translation"
        
        panel = VariablesPanel()
        variables = [sample_variable]
        panel.update_variables_display(variables)
        
        # Select first item
        panel.variable_list_widget.setCurrentRow(0)
        
        # Mock signal connection
        signal_emitted = False
        emitted_value = None
        
        def on_signal(value):
            nonlocal signal_emitted, emitted_value
            signal_emitted = True
            emitted_value = value
        
        panel.variable_selected.connect(on_signal)
        
        # Insert selected variable
        panel.insert_selected_variable()
        
        assert signal_emitted
        assert emitted_value == "{customer_name}"
    
    @patch('src.multichannel_messaging.gui.variables_panel.get_i18n_manager')
    def test_get_selected_variable(self, mock_i18n, app, sample_variable):
        """Test getting selected variable."""
        mock_i18n.return_value.tr.return_value = "test_translation"
        
        panel = VariablesPanel()
        variables = [sample_variable]
        panel.update_variables_display(variables)
        
        # No selection initially
        assert panel.get_selected_variable() is None
        
        # Select first item
        panel.variable_list_widget.setCurrentRow(0)
        selected = panel.get_selected_variable()
        
        assert selected == sample_variable
    
    @patch('src.multichannel_messaging.gui.variables_panel.get_i18n_manager')
    def test_select_variable_by_name(self, mock_i18n, app, sample_variable):
        """Test selecting variable by name."""
        mock_i18n.return_value.tr.return_value = "test_translation"
        
        panel = VariablesPanel()
        variables = [sample_variable]
        panel.update_variables_display(variables)
        
        # Select by name
        result = panel.select_variable_by_name("customer_name")
        assert result is True
        
        selected = panel.get_selected_variable()
        assert selected == sample_variable
        
        # Try non-existent variable
        result = panel.select_variable_by_name("nonexistent")
        assert result is False
    
    @patch('src.multichannel_messaging.gui.variables_panel.get_i18n_manager')
    def test_variables_change_callback(self, mock_i18n, app, sample_variable):
        """Test variables change callback."""
        mock_i18n.return_value.tr.return_value = "test_translation"
        
        panel = VariablesPanel()
        
        # Initial count (default variables)
        initial_count = panel.variable_list_widget.count()
        
        # Trigger variable change
        variables = [sample_variable]
        panel.on_variables_changed(variables)
        
        # Should update display
        assert panel.variable_list_widget.count() == 1
        assert panel.variable_list_widget.count() != initial_count


class TestCompactVariablesPanel:
    """Test CompactVariablesPanel class."""
    
    @patch('src.multichannel_messaging.gui.variables_panel.get_i18n_manager')
    def test_initialization(self, mock_i18n, app):
        """Test compact panel initialization."""
        mock_i18n.return_value.tr.return_value = "test_translation"
        
        panel = CompactVariablesPanel()
        
        assert panel.variable_manager is not None
        assert panel.variable_list_widget is not None
        
        # Should start with default variables
        assert panel.variable_list_widget.count() == 4  # Default variables
    
    @patch('src.multichannel_messaging.gui.variables_panel.get_i18n_manager')
    def test_compact_display(self, mock_i18n, app, sample_variable):
        """Test compact display functionality."""
        mock_i18n.return_value.tr.return_value = "test_translation"
        
        panel = CompactVariablesPanel()
        variables = [sample_variable]
        
        panel.update_variables_display(variables)
        
        assert panel.variable_list_widget.count() == 1
        item = panel.variable_list_widget.item(0)
        assert item.text() == "{customer_name}"
        assert "Customer Name" in item.toolTip()
    
    @patch('src.multichannel_messaging.gui.variables_panel.get_i18n_manager')
    def test_compact_variable_selection(self, mock_i18n, app, sample_variable):
        """Test compact panel variable selection."""
        mock_i18n.return_value.tr.return_value = "test_translation"
        
        panel = CompactVariablesPanel()
        variables = [sample_variable]
        panel.update_variables_display(variables)
        
        # Mock signal connection
        signal_emitted = False
        emitted_value = None
        
        def on_signal(value):
            nonlocal signal_emitted, emitted_value
            signal_emitted = True
            emitted_value = value
        
        panel.variable_selected.connect(on_signal)
        
        # Simulate double-click
        item = panel.variable_list_widget.item(0)
        panel.on_variable_double_clicked(item)
        
        assert signal_emitted
        assert emitted_value == "{customer_name}"