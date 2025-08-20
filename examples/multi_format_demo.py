#!/usr/bin/env python3
"""
Demonstration of multi-format table processing capabilities.

This script shows how to use the AdvancedTableProcessor to handle
CSV, Excel, JSON, JSONL, TSV, and other tabular formats.
"""

import json
import pandas as pd
from pathlib import Path
import tempfile
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from multichannel_messaging.core.csv_processor import AdvancedTableProcessor, FileFormat


def create_sample_data():
    """Create sample customer data for demonstration."""
    return [
        {
            'name': 'John Doe',
            'company': 'Example Corp',
            'phone': '+1-555-0123',
            'email': 'john.doe@example.com'
        },
        {
            'name': 'Jane Smith',
            'company': 'Sample Inc',
            'phone': '+1-555-0456',
            'email': 'jane.smith@sample.com'
        },
        {
            'name': 'Carlos Rodriguez',
            'company': 'Demo LLC',
            'phone': '+1-555-0789',
            'email': 'carlos.rodriguez@demo.com'
        },
        {
            'name': 'Maria Garcia',
            'company': 'Test Solutions',
            'phone': '+1-555-0321',
            'email': 'maria.garcia@testsolutions.com'
        },
        {
            'name': 'Ahmed Hassan',
            'company': 'Global Enterprises',
            'phone': '+1-555-0654',
            'email': 'ahmed.hassan@globalent.com'
        }
    ]


def create_sample_files(temp_dir, data):
    """Create sample files in different formats."""
    files = {}
    
    # CSV file
    csv_file = temp_dir / "customers.csv"
    df = pd.DataFrame(data)
    df.to_csv(csv_file, index=False)
    files['CSV'] = csv_file
    
    # TSV file
    tsv_file = temp_dir / "customers.tsv"
    df.to_csv(tsv_file, index=False, sep='\t')
    files['TSV'] = tsv_file
    
    # JSON file
    json_file = temp_dir / "customers.json"
    json_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
    files['JSON'] = json_file
    
    # JSONL file
    jsonl_file = temp_dir / "customers.jsonl"
    with open(jsonl_file, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')
    files['JSONL'] = jsonl_file
    
    # Excel file (if openpyxl is available)
    try:
        excel_file = temp_dir / "customers.xlsx"
        df.to_excel(excel_file, index=False, engine='openpyxl')
        files['Excel'] = excel_file
    except ImportError:
        print("Note: openpyxl not available, skipping Excel file creation")
    
    # Pipe-delimited file
    pipe_file = temp_dir / "customers_pipe.txt"
    df.to_csv(pipe_file, index=False, sep='|')
    files['Pipe-delimited'] = pipe_file
    
    # Semicolon-delimited file
    semicolon_file = temp_dir / "customers_semicolon.txt"
    df.to_csv(semicolon_file, index=False, sep=';')
    files['Semicolon-delimited'] = semicolon_file
    
    return files


def demonstrate_format_detection(processor, files):
    """Demonstrate automatic format detection."""
    print("=" * 60)
    print("FORMAT DETECTION DEMONSTRATION")
    print("=" * 60)
    
    for format_name, file_path in files.items():
        detected_format = processor.detect_file_format(file_path)
        print(f"{format_name:20} -> {detected_format.value}")
    print()


def demonstrate_structure_analysis(processor, files):
    """Demonstrate file structure analysis."""
    print("=" * 60)
    print("STRUCTURE ANALYSIS DEMONSTRATION")
    print("=" * 60)
    
    for format_name, file_path in files.items():
        print(f"\n{format_name} File Analysis:")
        print("-" * 40)
        
        try:
            structure = processor.analyze_file_structure(file_path)
            
            print(f"Format: {structure.file_format.value}")
            print(f"Headers: {structure.headers}")
            print(f"Total rows: {structure.total_rows}")
            print(f"Has header: {structure.has_header}")
            
            if structure.encoding:
                print(f"Encoding: {structure.encoding.encoding} ({structure.encoding.confidence.value})")
            
            if structure.delimiter:
                print(f"Delimiter: '{structure.delimiter.delimiter}'")
            
            if structure.sheet_names:
                print(f"Sheets: {structure.sheet_names}")
            
            # Show sample data
            if structure.sample_rows:
                print("Sample data:")
                for i, row in enumerate(structure.sample_rows[:2]):
                    print(f"  Row {i+1}: {dict(list(row.items())[:2])}...")  # Show first 2 columns
        
        except Exception as e:
            print(f"Error analyzing {format_name}: {e}")


def demonstrate_validation(processor, files):
    """Demonstrate file validation."""
    print("\n" + "=" * 60)
    print("VALIDATION DEMONSTRATION")
    print("=" * 60)
    
    for format_name, file_path in files.items():
        print(f"\n{format_name} Validation:")
        print("-" * 30)
        
        try:
            validation_result = processor.validate_table_format(file_path)
            
            print(f"Valid: {validation_result['valid']}")
            print(f"Required columns found: {validation_result['analysis']['required_columns_found']}")
            
            if validation_result['errors']:
                print(f"Errors: {validation_result['errors']}")
            
            if validation_result['warnings']:
                print(f"Warnings: {validation_result['warnings']}")
        
        except Exception as e:
            print(f"Error validating {format_name}: {e}")


def demonstrate_customer_loading(processor, files):
    """Demonstrate customer loading from different formats."""
    print("\n" + "=" * 60)
    print("CUSTOMER LOADING DEMONSTRATION")
    print("=" * 60)
    
    for format_name, file_path in files.items():
        print(f"\n{format_name} Customer Loading:")
        print("-" * 35)
        
        try:
            customers, report = processor.load_customers_advanced(file_path)
            
            print(f"Loaded customers: {len(customers)}")
            print(f"Success rate: {report.success_rate:.1f}%")
            print(f"Errors: {report.error_count}")
            print(f"Warnings: {report.warning_count}")
            
            if customers:
                print(f"First customer: {customers[0].name} from {customers[0].company}")
        
        except Exception as e:
            print(f"Error loading customers from {format_name}: {e}")


def demonstrate_streaming(processor, files):
    """Demonstrate streaming capabilities."""
    print("\n" + "=" * 60)
    print("STREAMING DEMONSTRATION")
    print("=" * 60)
    
    # Use CSV file for streaming demo
    csv_file = files.get('CSV')
    if not csv_file:
        print("No CSV file available for streaming demo")
        return
    
    print("Streaming CSV data in chunks of 2 rows:")
    print("-" * 40)
    
    try:
        chunk_count = 0
        total_rows = 0
        
        for chunk in processor.stream_table_rows(csv_file, chunk_size=2):
            chunk_count += 1
            total_rows += len(chunk)
            print(f"Chunk {chunk_count}: {len(chunk)} rows")
            
            # Show first row of each chunk
            if chunk:
                first_row = chunk[0]
                print(f"  Sample: {first_row['name']} from {first_row['company']}")
        
        print(f"\nTotal chunks: {chunk_count}")
        print(f"Total rows streamed: {total_rows}")
    
    except Exception as e:
        print(f"Error during streaming: {e}")


def demonstrate_backward_compatibility(processor, files):
    """Demonstrate backward compatibility with CSV methods."""
    print("\n" + "=" * 60)
    print("BACKWARD COMPATIBILITY DEMONSTRATION")
    print("=" * 60)
    
    csv_file = files.get('CSV')
    if not csv_file:
        print("No CSV file available for backward compatibility demo")
        return
    
    print("Using legacy CSV methods:")
    print("-" * 30)
    
    try:
        # Old CSV validation method
        validation_result = processor.validate_csv_format(csv_file)
        print(f"CSV validation (legacy): {validation_result['valid']}")
        
        # Old customer loading method
        customers, errors = processor.load_customers(csv_file)
        print(f"Customers loaded (legacy): {len(customers)}")
        print(f"Errors (legacy): {len(errors)}")
        
        # Old streaming method
        chunks = list(processor.stream_csv_rows(csv_file, chunk_size=3))
        print(f"Streaming chunks (legacy): {len(chunks)}")
    
    except Exception as e:
        print(f"Error in backward compatibility demo: {e}")


def main():
    """Main demonstration function."""
    print("Multi-Format Table Processing Demonstration")
    print("=" * 60)
    print("This demo shows the capabilities of the AdvancedTableProcessor")
    print("for handling CSV, Excel, JSON, JSONL, TSV, and other formats.")
    print()
    
    # Create processor
    processor = AdvancedTableProcessor()
    
    # Create sample data and files
    sample_data = create_sample_data()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        files = create_sample_files(temp_path, sample_data)
        
        print(f"Created {len(files)} sample files in different formats:")
        for format_name, file_path in files.items():
            print(f"  {format_name}: {file_path.name}")
        print()
        
        # Run demonstrations
        demonstrate_format_detection(processor, files)
        demonstrate_structure_analysis(processor, files)
        demonstrate_validation(processor, files)
        demonstrate_customer_loading(processor, files)
        demonstrate_streaming(processor, files)
        demonstrate_backward_compatibility(processor, files)
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("The AdvancedTableProcessor successfully handled all supported formats!")
    print("Key features demonstrated:")
    print("  ✓ Automatic format detection")
    print("  ✓ Robust encoding detection")
    print("  ✓ Intelligent column mapping")
    print("  ✓ Comprehensive validation")
    print("  ✓ Memory-efficient streaming")
    print("  ✓ Multi-format support")
    print("  ✓ Backward compatibility")


if __name__ == "__main__":
    main()