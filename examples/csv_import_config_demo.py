#!/usr/bin/env python3
"""
Demo script for the enhanced CSV Import Configuration Dialog.

This script demonstrates the key features of the new CSV import configuration system:
1. Flexible column selection based on messaging channels
2. Template saving and reuse
3. Validation based on channel requirements
4. Preview functionality

Usage:
    python examples/csv_import_config_demo.py
"""

import sys
import tempfile
import pandas as pd
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from multichannel_messaging.gui.csv_import_config_dialog import CSVImportConfiguration


def create_sample_csv_file():
    """Create a sample CSV file for demonstration."""
    sample_data = pd.DataFrame(
        {
            "Customer Name": [
                "John Doe",
                "Jane Smith",
                "Bob Johnson",
                "Alice Brown",
                "Charlie Wilson",
            ],
            "Email Address": [
                "john@acme.com",
                "jane@techcorp.com",
                "bob@startup.io",
                "alice@bigco.com",
                "charlie@smallbiz.net",
            ],
            "Company Name": [
                "Acme Corp",
                "Tech Corp",
                "StartUp Inc",
                "Big Company",
                "Small Business",
            ],
            "Phone Number": [
                "+1-555-0101",
                "+1-555-0102",
                "+1-555-0103",
                "+1-555-0104",
                "+1-555-0105",
            ],
            "Department": ["Sales", "Engineering", "Marketing", "HR", "Finance"],
            "Country": ["USA", "Canada", "USA", "UK", "Australia"],
        }
    )

    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        sample_data.to_csv(f, index=False)
        return Path(f.name)


def demo_configuration_scenarios():
    """Demonstrate different configuration scenarios."""
    print("=== CSV Import Configuration Demo ===\n")

    # Create sample data
    sample_data = pd.DataFrame(
        {
            "Customer Name": ["John Doe", "Jane Smith", "Bob Johnson"],
            "Email Address": ["john@acme.com", "jane@techcorp.com", "bob@startup.io"],
            "Company Name": ["Acme Corp", "Tech Corp", "StartUp Inc"],
            "Phone Number": ["+1-555-0101", "+1-555-0102", "+1-555-0103"],
        }
    )

    print("Sample CSV Data:")
    print(sample_data.to_string(index=False))
    print("\n" + "=" * 60 + "\n")

    # Scenario 1: Email-only configuration
    print("Scenario 1: Email-Only Messaging Configuration")
    print("-" * 50)

    email_config = CSVImportConfiguration(
        template_name="Email Only Template",
        description="Configuration for email-only campaigns",
        messaging_channels=["email"],
        column_mapping={
            "Customer Name": "name",
            "Email Address": "email",
            "Company Name": "company",
        },
    )

    print(f"Template Name: {email_config.template_name}")
    print(f"Messaging Channels: {email_config.messaging_channels}")
    print(f"Column Mapping: {email_config.column_mapping}")

    # Validate configuration
    errors = email_config.validate_configuration()
    if errors:
        print(f"Validation Errors: {[str(e) for e in errors]}")
    else:
        print("✓ Configuration is valid")

    # Apply configuration
    processed_data = email_config.apply_to_csv(sample_data)
    print("\nProcessed Data (Email Only):")
    print(processed_data.to_string(index=False))
    print("\n" + "=" * 60 + "\n")

    # Scenario 2: WhatsApp-only configuration
    print("Scenario 2: WhatsApp-Only Messaging Configuration")
    print("-" * 50)

    whatsapp_config = CSVImportConfiguration(
        template_name="WhatsApp Only Template",
        description="Configuration for WhatsApp-only campaigns",
        messaging_channels=["whatsapp"],
        column_mapping={
            "Customer Name": "name",
            "Phone Number": "phone",
            "Company Name": "company",
        },
    )

    print(f"Template Name: {whatsapp_config.template_name}")
    print(f"Messaging Channels: {whatsapp_config.messaging_channels}")
    print(f"Column Mapping: {whatsapp_config.column_mapping}")

    # Validate configuration
    errors = whatsapp_config.validate_configuration()
    if errors:
        print(f"Validation Errors: {[str(e) for e in errors]}")
    else:
        print("✓ Configuration is valid")

    # Apply configuration
    processed_data = whatsapp_config.apply_to_csv(sample_data)
    print("\nProcessed Data (WhatsApp Only):")
    print(processed_data.to_string(index=False))
    print("\n" + "=" * 60 + "\n")

    # Scenario 3: Multi-channel configuration
    print("Scenario 3: Multi-Channel Messaging Configuration")
    print("-" * 50)

    multi_config = CSVImportConfiguration(
        template_name="Multi-Channel Template",
        description="Configuration for both email and WhatsApp campaigns",
        messaging_channels=["email", "whatsapp"],
        column_mapping={
            "Customer Name": "name",
            "Email Address": "email",
            "Phone Number": "phone",
            "Company Name": "company",
        },
    )

    print(f"Template Name: {multi_config.template_name}")
    print(f"Messaging Channels: {multi_config.messaging_channels}")
    print(f"Column Mapping: {multi_config.column_mapping}")

    # Validate configuration
    errors = multi_config.validate_configuration()
    if errors:
        print(f"Validation Errors: {[str(e) for e in errors]}")
    else:
        print("✓ Configuration is valid")

    # Apply configuration
    processed_data = multi_config.apply_to_csv(sample_data)
    print("\nProcessed Data (Multi-Channel):")
    print(processed_data.to_string(index=False))
    print("\n" + "=" * 60 + "\n")

    # Scenario 4: Selective column import
    print("Scenario 4: Selective Column Import")
    print("-" * 50)

    selective_config = CSVImportConfiguration(
        template_name="Selective Import Template",
        description="Import only name and email columns",
        messaging_channels=["email"],
        column_mapping={
            "Customer Name": "name",
            "Email Address": "email",
            # Deliberately omitting company and phone
        },
    )

    print(f"Template Name: {selective_config.template_name}")
    print(f"Messaging Channels: {selective_config.messaging_channels}")
    print(f"Column Mapping: {selective_config.column_mapping}")

    # Apply configuration
    processed_data = selective_config.apply_to_csv(sample_data)
    print("\nProcessed Data (Selective Import - Name & Email Only):")
    print(processed_data.to_string(index=False))
    print(f"Columns imported: {list(processed_data.columns)}")
    print("\n" + "=" * 60 + "\n")

    # Scenario 5: Invalid configuration
    print("Scenario 5: Invalid Configuration (Missing Required Fields)")
    print("-" * 50)

    invalid_config = CSVImportConfiguration(
        template_name="Invalid Template",
        description="Configuration missing required fields",
        messaging_channels=["email", "whatsapp"],
        column_mapping={
            "Customer Name": "name"
            # Missing email and phone for multi-channel
        },
    )

    print(f"Template Name: {invalid_config.template_name}")
    print(f"Messaging Channels: {invalid_config.messaging_channels}")
    print(f"Column Mapping: {invalid_config.column_mapping}")

    # Validate configuration
    errors = invalid_config.validate_configuration()
    if errors:
        print(f"❌ Validation Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✓ Configuration is valid")

    print("\n" + "=" * 60 + "\n")


def demo_template_persistence():
    """Demonstrate template saving and loading."""
    print("Template Persistence Demo")
    print("-" * 30)

    # Create a configuration
    config = CSVImportConfiguration(
        template_name="Demo Template",
        description="A template for demonstration purposes",
        messaging_channels=["email", "whatsapp"],
        column_mapping={
            "Name": "name",
            "Email": "email",
            "Phone": "phone",
            "Company": "company",
        },
        encoding="utf-8",
        delimiter=",",
        has_header=True,
        skip_rows=0,
    )

    print("Original Configuration:")
    print(f"  Template Name: {config.template_name}")
    print(f"  Description: {config.description}")
    print(f"  Channels: {config.messaging_channels}")
    print(f"  Column Mapping: {config.column_mapping}")
    print(f"  Encoding: {config.encoding}")
    print(f"  Delimiter: '{config.delimiter}'")
    print(f"  Has Header: {config.has_header}")
    print(f"  Skip Rows: {config.skip_rows}")

    # Convert to dictionary (for saving)
    config_dict = config.to_dict()
    print(f"\nSerialized to dictionary with {len(config_dict)} keys")

    # Convert back from dictionary (for loading)
    loaded_config = CSVImportConfiguration.from_dict(config_dict)

    print("\nLoaded Configuration:")
    print(f"  Template Name: {loaded_config.template_name}")
    print(f"  Description: {loaded_config.description}")
    print(f"  Channels: {loaded_config.messaging_channels}")
    print(f"  Column Mapping: {loaded_config.column_mapping}")
    print(f"  Encoding: {loaded_config.encoding}")
    print(f"  Delimiter: '{loaded_config.delimiter}'")
    print(f"  Has Header: {loaded_config.has_header}")
    print(f"  Skip Rows: {loaded_config.skip_rows}")

    # Verify they match
    matches = (
        loaded_config.template_name == config.template_name
        and loaded_config.description == config.description
        and loaded_config.messaging_channels == config.messaging_channels
        and loaded_config.column_mapping == config.column_mapping
        and loaded_config.encoding == config.encoding
        and loaded_config.delimiter == config.delimiter
        and loaded_config.has_header == config.has_header
        and loaded_config.skip_rows == config.skip_rows
    )

    print(f"\n✓ Template persistence works correctly: {matches}")
    print("\n" + "=" * 60 + "\n")


def main():
    """Run the demo."""
    print("Enhanced CSV Import Configuration System Demo")
    print("=" * 60)
    print()
    print("This demo showcases the new CSV import configuration features:")
    print("• Flexible column selection based on messaging channels")
    print("• Template saving and reuse functionality")
    print("• Validation based on channel requirements")
    print("• Preview and selective import capabilities")
    print()
    print("=" * 60)
    print()

    # Run configuration scenarios demo
    demo_configuration_scenarios()

    # Run template persistence demo
    demo_template_persistence()

    print("Demo completed successfully!")
    print()
    print("Key Benefits of the Enhanced CSV Import System:")
    print("• Users can select only the columns they need")
    print("• Configuration templates can be saved and reused")
    print("• Validation ensures required fields are mapped correctly")
    print("• Supports both email-only and WhatsApp-only workflows")
    print("• Provides clear error messages for invalid configurations")
    print("• Allows preview of processed data before import")


if __name__ == "__main__":
    main()
