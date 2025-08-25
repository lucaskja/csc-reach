#!/usr/bin/env python3
"""
Demo script for Dynamic Variable Management System.

This script demonstrates the key features of the dynamic variable management system:
1. Automatic variable generation from CSV column names
2. Data type detection
3. Template variable validation
4. Variable search and filtering
"""

import sys
import pandas as pd
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from multichannel_messaging.core.dynamic_variable_manager import DynamicVariableManager


def demo_basic_functionality():
    """Demonstrate basic variable management functionality."""
    print("=== Dynamic Variable Management Demo ===\n")
    
    # Create the variable manager
    manager = DynamicVariableManager()
    
    print("1. Default Variables:")
    print("   When no CSV is loaded, the system provides default variables:")
    for var in manager.get_available_variables():
        print(f"   - {var.format_for_template()} ({var.data_type}): {var.description}")
    print()


def demo_csv_variable_generation():
    """Demonstrate CSV-based variable generation."""
    print("2. CSV-Based Variable Generation:")
    print("   When CSV data is imported, variables are automatically generated:")
    
    # Create sample CSV data
    sample_data = {
        'Customer Name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
        'Email Address': ['john@example.com', 'jane@example.com', 'bob@example.com'],
        'Phone Number': ['+1234567890', '+0987654321', '+1122334455'],
        'Company Name': ['Acme Corp', 'Tech Solutions', 'Global Industries'],
        'Purchase Amount': ['100.50', '250.00', '75.25'],
        'Registration Date': ['2023-01-15', '2023-02-20', '2023-03-10']
    }
    
    df = pd.DataFrame(sample_data)
    csv_columns = list(df.columns)
    sample_row = df.iloc[0].to_dict()
    
    print(f"   CSV Columns: {csv_columns}")
    print(f"   Sample Data: {sample_row}")
    print()
    
    # Create manager and update with CSV data
    manager = DynamicVariableManager()
    manager.update_available_variables(csv_columns, sample_row)
    
    print("   Generated Variables:")
    for var in manager.get_available_variables():
        print(f"   - {var.format_for_template()} ({var.data_type})")
        print(f"     Original: '{var.name}' -> Variable: '{var.variable_name}'")
        print(f"     Sample: '{var.sample_value}'")
        print()


def demo_data_type_detection():
    """Demonstrate data type detection capabilities."""
    print("3. Data Type Detection:")
    print("   The system automatically detects data types based on column names and sample values:")
    
    test_cases = [
        ("Customer Email", "john@example.com"),
        ("Phone Number", "+1-555-123-4567"),
        ("Mobile", "(555) 987-6543"),
        ("WhatsApp Number", "+44 20 7946 0958"),
        ("Order Count", "42"),
        ("Total Amount", "1,234.56"),
        ("Customer Name", "John Doe"),
        ("Description", "Some descriptive text"),
        ("Unknown Column", "random value")
    ]
    
    manager = DynamicVariableManager()
    
    for column_name, sample_value in test_cases:
        detected_type = manager._detect_data_type(column_name, sample_value)
        formatted_name = manager._format_variable_name(column_name)
        print(f"   '{column_name}' + '{sample_value}' -> {{{formatted_name}}} ({detected_type})")
    print()


def demo_template_validation():
    """Demonstrate template variable validation."""
    print("4. Template Variable Validation:")
    print("   The system can validate template content against available variables:")
    
    # Set up manager with sample variables
    manager = DynamicVariableManager()
    csv_columns = ['Customer Name', 'Email Address', 'Company Name']
    sample_data = {
        'Customer Name': 'John Doe',
        'Email Address': 'john@example.com', 
        'Company Name': 'Acme Corp'
    }
    manager.update_available_variables(csv_columns, sample_data)
    
    test_templates = [
        "Hello {customer_name}, welcome to our service!",
        "Dear {customer_name}, your order from {company_name} is ready.",
        "Contact us at {email_address} for more information.",
        "Hello {customer_name}, your {nonexistent_variable} is ready!",
        "Welcome {customer_name}! Your {email_address} and {invalid_var} are confirmed."
    ]
    
    for template in test_templates:
        missing_vars = manager.validate_template_variables(template)
        status = "✓ Valid" if not missing_vars else f"✗ Missing: {missing_vars}"
        print(f"   Template: '{template}'")
        print(f"   Status: {status}")
        print()


def demo_variable_search():
    """Demonstrate variable search functionality."""
    print("5. Variable Search and Filtering:")
    print("   Variables can be searched and filtered:")
    
    # Set up manager with diverse variables
    manager = DynamicVariableManager()
    csv_columns = [
        'Customer Name', 'Customer Email', 'Customer Phone',
        'Company Name', 'Company Email', 'Company Address',
        'Order Number', 'Order Date', 'Order Amount'
    ]
    manager.update_available_variables(csv_columns)
    
    search_terms = ['customer', 'email', 'order', 'company']
    
    for term in search_terms:
        results = manager.search_variables(term)
        print(f"   Search '{term}': {len(results)} results")
        for var in results:
            print(f"     - {var.format_for_template()} ({var.name})")
        print()


def demo_variable_suggestions():
    """Demonstrate variable suggestion system."""
    print("6. Variable Suggestions (Autocomplete):")
    print("   The system provides suggestions for partial variable names:")
    
    manager = DynamicVariableManager()
    csv_columns = ['Customer Name', 'Customer Email', 'Company Name', 'Email Address']
    manager.update_available_variables(csv_columns)
    
    partial_names = ['cust', 'email', 'comp', 'name']
    
    for partial in partial_names:
        suggestions = manager.get_variable_suggestions(partial)
        print(f"   '{partial}' -> {[var.variable_name for var in suggestions]}")
    print()


def main():
    """Run all demo functions."""
    try:
        demo_basic_functionality()
        demo_csv_variable_generation()
        demo_data_type_detection()
        demo_template_validation()
        demo_variable_search()
        demo_variable_suggestions()
        
        print("=== Demo Complete ===")
        print("\nKey Features Demonstrated:")
        print("✓ Automatic variable generation from CSV columns")
        print("✓ Intelligent data type detection")
        print("✓ Template variable validation")
        print("✓ Variable search and filtering")
        print("✓ Autocomplete suggestions")
        print("✓ Proper variable name formatting")
        
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())