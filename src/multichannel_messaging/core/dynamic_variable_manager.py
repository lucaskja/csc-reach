"""
Dynamic Variable Management System for CSC-Reach.

This module provides dynamic template variable management based on CSV column names
and automatic variable generation for template creation.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable
from datetime import datetime

from ..utils.logger import get_logger
from ..core.i18n_manager import get_i18n_manager

logger = get_logger(__name__)


@dataclass
class TemplateVariable:
    """Represents a template variable with metadata."""
    
    name: str  # Original column name from CSV
    variable_name: str  # Formatted variable name for templates (e.g., {column_name})
    data_type: str  # "text", "email", "phone", "number"
    sample_value: str = ""
    description: str = ""
    is_required: bool = False
    
    def format_for_template(self) -> str:
        """Return the variable in template format."""
        return f"{{{self.variable_name}}}"
    
    def validate_value(self, value: str) -> bool:
        """Validate a value against this variable's data type."""
        if not value and self.is_required:
            return False
        
        # If value is empty and not required, it's valid
        if not value and not self.is_required:
            return True
            
        if self.data_type == "email":
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return re.match(email_pattern, value) is not None
        elif self.data_type == "phone":
            # Basic phone validation - digits, spaces, dashes, parentheses, plus
            phone_pattern = r'^[\+]?[\d\s\-\(\)]{7,}$'
            return re.match(phone_pattern, value) is not None
        elif self.data_type == "number":
            try:
                float(value)
                return True
            except ValueError:
                return False
        
        return True  # Text type or any other type is always valid


class DynamicVariableManager:
    """Manages dynamic template variables based on CSV data."""
    
    def __init__(self):
        self.change_callbacks: List[Callable[[List[TemplateVariable]], None]] = []
        self.i18n_manager = get_i18n_manager()
        self.default_variables: List[TemplateVariable] = self._create_default_variables()
        self.available_variables: List[TemplateVariable] = self.default_variables.copy()
        
    def add_change_callback(self, callback: Callable[[List[TemplateVariable]], None]):
        """Add a callback to be called when variables change."""
        self.change_callbacks.append(callback)
    
    def remove_change_callback(self, callback: Callable[[List[TemplateVariable]], None]):
        """Remove a change callback."""
        if callback in self.change_callbacks:
            self.change_callbacks.remove(callback)
    
    def _notify_change(self):
        """Notify all callbacks that variables have changed."""
        for callback in self.change_callbacks:
            try:
                callback(self.available_variables)
            except Exception as e:
                logger.error(f"Error in variable change callback: {e}")
        
    def generate_variables_from_csv(self, csv_columns: List[str], sample_data: Dict[str, str] = None) -> List[TemplateVariable]:
        """Generate template variables from CSV column names."""
        variables = []
        for column in csv_columns:
            variable = TemplateVariable(
                name=column,
                variable_name=self._format_variable_name(column),
                data_type=self._detect_data_type(column, sample_data.get(column) if sample_data else None),
                sample_value=sample_data.get(column, "") if sample_data else "",
                description=self.i18n_manager.tr("variable_from_column", column=column)
            )
            variables.append(variable)
        return variables
    
    def update_available_variables(self, csv_columns: List[str], sample_data: Dict[str, str] = None):
        """Update the list of available variables based on current CSV data."""
        if csv_columns:
            self.available_variables = self.generate_variables_from_csv(csv_columns, sample_data)
            logger.info(f"Updated variables from CSV columns: {csv_columns}")
        else:
            self.available_variables = self.default_variables.copy()
            logger.info("Reset to default variables (no CSV loaded)")
        
        self._notify_change()
    
    def get_available_variables(self) -> List[TemplateVariable]:
        """Get the current list of available variables."""
        return self.available_variables
    
    def get_variable_by_name(self, variable_name: str) -> Optional[TemplateVariable]:
        """Get a specific variable by its name."""
        for var in self.available_variables:
            if var.variable_name == variable_name:
                return var
        return None
    
    def get_variables_by_type(self, data_type: str) -> List[TemplateVariable]:
        """Get all variables of a specific data type."""
        return [var for var in self.available_variables if var.data_type == data_type]
    
    def search_variables(self, query: str) -> List[TemplateVariable]:
        """Search variables by name or description."""
        query_lower = query.lower()
        return [
            var for var in self.available_variables
            if query_lower in var.name.lower() 
            or query_lower in var.variable_name.lower()
            or query_lower in var.description.lower()
        ]
    
    def _format_variable_name(self, column_name: str) -> str:
        """Format column name into a valid variable name."""
        # Convert to lowercase, replace spaces and special chars with underscores
        formatted = re.sub(r'[^a-zA-Z0-9_]', '_', column_name.lower())
        # Remove multiple consecutive underscores
        formatted = re.sub(r'_+', '_', formatted)
        # Remove leading/trailing underscores
        formatted = formatted.strip('_')
        
        # Ensure it doesn't start with a number
        if formatted and formatted[0].isdigit():
            formatted = f"col_{formatted}"
        
        # Ensure it's not empty
        if not formatted:
            formatted = "unnamed_column"
            
        return formatted
    
    def _detect_data_type(self, column_name: str, sample_value: str = None) -> str:
        """Detect the data type based on column name and sample value."""
        column_lower = column_name.lower()
        
        # Check column name patterns
        if 'email' in column_lower or 'e-mail' in column_lower or 'mail' in column_lower:
            return 'email'
        elif any(word in column_lower for word in ['phone', 'tel', 'mobile', 'cell', 'whatsapp']):
            return 'phone'
        elif any(word in column_lower for word in ['number', 'count', 'qty', 'quantity', 'amount', 'price', 'cost']):
            return 'number'
        
        # Check sample value if available
        if sample_value:
            # Email pattern
            if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', sample_value):
                return 'email'
            # Phone pattern (basic)
            elif re.match(r'^[\+]?[\d\s\-\(\)]{7,}$', sample_value.strip()):
                return 'phone'
            # Number pattern
            elif re.match(r'^[\d\.,]+$', sample_value.strip()):
                return 'number'
        
        return 'text'
    
    def _create_default_variables(self) -> List[TemplateVariable]:
        """Create default variables when no CSV is loaded."""
        return [
            TemplateVariable(
                name="Name", 
                variable_name="name", 
                data_type="text", 
                sample_value="John Doe", 
                description=self.i18n_manager.tr("default_variable_name_desc"),
                is_required=True
            ),
            TemplateVariable(
                name="Email", 
                variable_name="email", 
                data_type="email", 
                sample_value="john@example.com", 
                description=self.i18n_manager.tr("default_variable_email_desc")
            ),
            TemplateVariable(
                name="Phone", 
                variable_name="phone", 
                data_type="phone", 
                sample_value="+1234567890", 
                description=self.i18n_manager.tr("default_variable_phone_desc")
            ),
            TemplateVariable(
                name="Company", 
                variable_name="company", 
                data_type="text", 
                sample_value="Example Corp", 
                description=self.i18n_manager.tr("default_variable_company_desc")
            ),
        ]
    
    def validate_template_variables(self, template_content: str) -> List[str]:
        """Validate that all variables in template content are available."""
        # Find all variables in the template (format: {variable_name})
        variable_pattern = r'\{([^}]+)\}'
        found_variables = re.findall(variable_pattern, template_content)
        
        # Check which variables are not available
        available_names = {var.variable_name for var in self.available_variables}
        missing_variables = [var for var in found_variables if var not in available_names]
        
        return missing_variables
    
    def get_variable_suggestions(self, partial_name: str) -> List[TemplateVariable]:
        """Get variable suggestions for autocomplete."""
        partial_lower = partial_name.lower()
        suggestions = []
        
        for var in self.available_variables:
            if var.variable_name.lower().startswith(partial_lower):
                suggestions.append(var)
        
        # Sort by relevance (exact match first, then alphabetical)
        suggestions.sort(key=lambda v: (v.variable_name.lower() != partial_lower, v.variable_name))
        
        return suggestions[:10]  # Limit to 10 suggestions