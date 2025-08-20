"""
Unit tests for the Advanced Table Processor supporting multiple formats.
"""

import pytest
import json
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.multichannel_messaging.core.csv_processor import (
    AdvancedTableProcessor,
    FileFormat,
    FileStructure,
    TableValidationReport,
    EncodingResult,
    EncodingConfidence,
    DelimiterResult
)
from src.multichannel_messaging.core.models import Customer
from src.multichannel_messaging.utils.exceptions import CSVProcessingError


class TestAdvancedTableProcessor:
    """Test cases for AdvancedTableProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create processor instance for testing."""
        return AdvancedTableProcessor()
    
    @pytest.fixture
    def sample_csv_file(self, tmp_path):
        """Create a sample CSV file for testing."""
        csv_content = """name,company,phone,email
John Doe,Example Corp,+1-555-0123,john.doe@example.com
Jane Smith,Sample Inc,+1-555-0456,jane.smith@sample.com
Carlos Rodriguez,Demo LLC,+1-555-0789,carlos.rodriguez@demo.com"""
        
        csv_file = tmp_path / "sample.csv"
        csv_file.write_text(csv_content, encoding='utf-8')
        return csv_file
    
    @pytest.fixture
    def sample_excel_file(self, tmp_path):
        """Create a sample Excel file for testing."""
        data = {
            'name': ['John Doe', 'Jane Smith', 'Carlos Rodriguez'],
            'company': ['Example Corp', 'Sample Inc', 'Demo LLC'],
            'phone': ['+1-555-0123', '+1-555-0456', '+1-555-0789'],
            'email': ['john.doe@example.com', 'jane.smith@sample.com', 'carlos.rodriguez@demo.com']
        }
        df = pd.DataFrame(data)
        excel_file = tmp_path / "sample.xlsx"
        df.to_excel(excel_file, index=False, engine='openpyxl')
        return excel_file
    
    @pytest.fixture
    def sample_json_file(self, tmp_path):
        """Create a sample JSON file for testing."""
        data = [
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
            }
        ]
        
        json_file = tmp_path / "sample.json"
        json_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
        return json_file
    
    @pytest.fixture
    def sample_jsonl_file(self, tmp_path):
        """Create a sample JSONL file for testing."""
        data = [
            {'name': 'John Doe', 'company': 'Example Corp', 'phone': '+1-555-0123', 'email': 'john.doe@example.com'},
            {'name': 'Jane Smith', 'company': 'Sample Inc', 'phone': '+1-555-0456', 'email': 'jane.smith@sample.com'},
            {'name': 'Carlos Rodriguez', 'company': 'Demo LLC', 'phone': '+1-555-0789', 'email': 'carlos.rodriguez@demo.com'}
        ]
        
        jsonl_file = tmp_path / "sample.jsonl"
        with open(jsonl_file, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item) + '\n')
        return jsonl_file
    
    def test_detect_file_format_csv(self, processor, sample_csv_file):
        """Test CSV format detection."""
        format_detected = processor.detect_file_format(sample_csv_file)
        assert format_detected == FileFormat.CSV
    
    def test_detect_file_format_excel(self, processor, sample_excel_file):
        """Test Excel format detection."""
        format_detected = processor.detect_file_format(sample_excel_file)
        assert format_detected == FileFormat.EXCEL_XLSX
    
    def test_detect_file_format_json(self, processor, sample_json_file):
        """Test JSON format detection."""
        format_detected = processor.detect_file_format(sample_json_file)
        assert format_detected == FileFormat.JSON
    
    def test_detect_file_format_jsonl(self, processor, sample_jsonl_file):
        """Test JSONL format detection."""
        format_detected = processor.detect_file_format(sample_jsonl_file)
        assert format_detected == FileFormat.JSONL
    
    def test_analyze_csv_structure(self, processor, sample_csv_file):
        """Test CSV structure analysis."""
        structure = processor.analyze_file_structure(sample_csv_file)
        
        assert structure.file_format == FileFormat.CSV
        assert structure.headers == ['name', 'company', 'phone', 'email']
        assert structure.total_rows == 3
        assert len(structure.sample_rows) == 3
        assert structure.has_header is True
    
    @pytest.mark.skipif(not hasattr(pd, 'read_excel'), reason="pandas Excel support not available")
    def test_analyze_excel_structure(self, processor, sample_excel_file):
        """Test Excel structure analysis."""
        structure = processor.analyze_file_structure(sample_excel_file)
        
        assert structure.file_format == FileFormat.EXCEL_XLSX
        assert structure.headers == ['name', 'company', 'phone', 'email']
        assert structure.total_rows == 3
        assert len(structure.sample_rows) == 3
        assert structure.has_header is True
        assert structure.sheet_names is not None
    
    def test_analyze_json_structure(self, processor, sample_json_file):
        """Test JSON structure analysis."""
        structure = processor.analyze_file_structure(sample_json_file)
        
        assert structure.file_format == FileFormat.JSON
        assert set(structure.headers) == {'name', 'company', 'phone', 'email'}
        assert structure.total_rows == 3
        assert len(structure.sample_rows) == 3
        assert structure.has_header is True
    
    def test_analyze_jsonl_structure(self, processor, sample_jsonl_file):
        """Test JSONL structure analysis."""
        structure = processor.analyze_file_structure(sample_jsonl_file)
        
        assert structure.file_format == FileFormat.JSONL
        assert set(structure.headers) == {'name', 'company', 'phone', 'email'}
        assert structure.total_rows == 3
        assert len(structure.sample_rows) == 3
        assert structure.has_header is True
    
    def test_stream_csv_rows(self, processor, sample_csv_file):
        """Test streaming CSV rows."""
        chunks = list(processor.stream_table_rows(sample_csv_file, chunk_size=2))
        
        assert len(chunks) == 2  # 3 rows in chunks of 2
        assert len(chunks[0]) == 2
        assert len(chunks[1]) == 1
        
        # Check first row
        first_row = chunks[0][0]
        assert first_row['name'] == 'John Doe'
        assert first_row['company'] == 'Example Corp'
        assert '_row_number' in first_row
    
    def test_stream_json_rows(self, processor, sample_json_file):
        """Test streaming JSON rows."""
        chunks = list(processor.stream_table_rows(sample_json_file, chunk_size=2))
        
        assert len(chunks) == 2  # 3 rows in chunks of 2
        assert len(chunks[0]) == 2
        assert len(chunks[1]) == 1
        
        # Check first row
        first_row = chunks[0][0]
        assert first_row['name'] == 'John Doe'
        assert first_row['company'] == 'Example Corp'
        assert '_row_number' in first_row
    
    def test_validate_table_comprehensive_csv(self, processor, sample_csv_file):
        """Test comprehensive table validation for CSV."""
        report = processor.validate_table_comprehensive(sample_csv_file)
        
        assert isinstance(report, TableValidationReport)
        assert report.file_format == FileFormat.CSV
        assert report.total_rows == 3
        assert report.valid_rows >= 0
        assert report.success_rate >= 0
    
    def test_validate_table_comprehensive_json(self, processor, sample_json_file):
        """Test comprehensive table validation for JSON."""
        report = processor.validate_table_comprehensive(sample_json_file)
        
        assert isinstance(report, TableValidationReport)
        assert report.file_format == FileFormat.JSON
        assert report.total_rows == 3
        assert report.valid_rows >= 0
    
    def test_load_customers_advanced_csv(self, processor, sample_csv_file):
        """Test advanced customer loading from CSV."""
        customers, report = processor.load_customers_advanced(sample_csv_file)
        
        assert len(customers) == 3
        assert isinstance(customers[0], Customer)
        assert customers[0].name == 'John Doe'
        assert customers[0].company == 'Example Corp'
        assert isinstance(report, TableValidationReport)
    
    def test_load_customers_advanced_json(self, processor, sample_json_file):
        """Test advanced customer loading from JSON."""
        customers, report = processor.load_customers_advanced(sample_json_file)
        
        assert len(customers) == 3
        assert isinstance(customers[0], Customer)
        assert customers[0].name == 'John Doe'
        assert customers[0].company == 'Example Corp'
        assert isinstance(report, TableValidationReport)
    
    def test_validate_table_format_csv(self, processor, sample_csv_file):
        """Test table format validation for CSV."""
        result = processor.validate_table_format(sample_csv_file)
        
        assert result['valid'] is True
        assert result['analysis']['file_format'] == 'csv'
        assert result['analysis']['total_rows'] == 3
        assert result['analysis']['required_columns_found'] is True
    
    def test_validate_table_format_json(self, processor, sample_json_file):
        """Test table format validation for JSON."""
        result = processor.validate_table_format(sample_json_file)
        
        assert result['valid'] is True
        assert result['analysis']['file_format'] == 'json'
        assert result['analysis']['total_rows'] == 3
        assert result['analysis']['required_columns_found'] is True
    
    def test_backward_compatibility_csv_methods(self, processor, sample_csv_file):
        """Test backward compatibility with CSV-specific methods."""
        # Test that old CSV methods still work
        structure = processor.analyze_file_structure(sample_csv_file)
        assert isinstance(structure, FileStructure)
        
        # Test streaming with old method name
        chunks = list(processor.stream_csv_rows(sample_csv_file))
        assert len(chunks) > 0
        
        # Test validation with old method name
        report = processor.validate_csv_comprehensive(sample_csv_file)
        assert isinstance(report, TableValidationReport)
        
        # Test format validation with old method name
        result = processor.validate_csv_format(sample_csv_file)
        assert result['valid'] is True
    
    def test_unsupported_file_format(self, processor, tmp_path):
        """Test handling of unsupported file formats."""
        unsupported_file = tmp_path / "test.unknown"
        unsupported_file.write_text("some content", encoding='utf-8')
        
        result = processor.validate_table_format(unsupported_file)
        assert result['valid'] is False
        # The system defaults to CSV for unknown formats, so it should fail on missing required columns
        assert any('Cannot map required columns' in error for error in result['errors'])
    
    def test_empty_file_handling(self, processor, tmp_path):
        """Test handling of empty files."""
        empty_file = tmp_path / "empty.csv"
        empty_file.write_text("", encoding='utf-8')
        
        structure = processor.analyze_file_structure(empty_file)
        assert structure.total_rows == 0
        assert len(structure.headers) == 0
    
    def test_malformed_json_handling(self, processor, tmp_path):
        """Test handling of malformed JSON files."""
        malformed_json = tmp_path / "malformed.json"
        malformed_json.write_text('{"invalid": json}', encoding='utf-8')
        
        with pytest.raises(CSVProcessingError):
            processor.analyze_file_structure(malformed_json)
    
    def test_tsv_format_detection(self, processor, tmp_path):
        """Test TSV format detection and processing."""
        tsv_content = "name\tcompany\tphone\temail\nJohn Doe\tExample Corp\t+1-555-0123\tjohn.doe@example.com"
        tsv_file = tmp_path / "sample.tsv"
        tsv_file.write_text(tsv_content, encoding='utf-8')
        
        format_detected = processor.detect_file_format(tsv_file)
        assert format_detected == FileFormat.TSV
        
        structure = processor.analyze_file_structure(tsv_file)
        assert structure.file_format == FileFormat.TSV
        assert structure.delimiter.delimiter == '\t'
    
    def test_pipe_delimited_format(self, processor, tmp_path):
        """Test pipe-delimited format detection and processing."""
        pipe_content = "name|company|phone|email\nJohn Doe|Example Corp|+1-555-0123|john.doe@example.com"
        pipe_file = tmp_path / "sample.txt"
        pipe_file.write_text(pipe_content, encoding='utf-8')
        
        # Content-based detection should identify pipe delimiter
        structure = processor.analyze_file_structure(pipe_file)
        assert structure.delimiter.delimiter == '|'
    
    def test_semicolon_delimited_format(self, processor, tmp_path):
        """Test semicolon-delimited format detection and processing."""
        semicolon_content = "name;company;phone;email\nJohn Doe;Example Corp;+1-555-0123;john.doe@example.com"
        semicolon_file = tmp_path / "sample.txt"
        semicolon_file.write_text(semicolon_content, encoding='utf-8')
        
        # Content-based detection should identify semicolon delimiter
        structure = processor.analyze_file_structure(semicolon_file)
        assert structure.delimiter.delimiter == ';'


class TestFileFormatEnum:
    """Test FileFormat enum."""
    
    def test_file_format_values(self):
        """Test FileFormat enum values."""
        assert FileFormat.CSV.value == "csv"
        assert FileFormat.TSV.value == "tsv"
        assert FileFormat.EXCEL_XLSX.value == "xlsx"
        assert FileFormat.EXCEL_XLS.value == "xls"
        assert FileFormat.JSON.value == "json"
        assert FileFormat.JSONL.value == "jsonl"
        assert FileFormat.PIPE_DELIMITED.value == "pipe"
        assert FileFormat.SEMICOLON_DELIMITED.value == "semicolon"
        assert FileFormat.UNKNOWN.value == "unknown"


class TestTableValidationReport:
    """Test TableValidationReport class."""
    
    def test_validation_report_properties(self):
        """Test validation report properties."""
        report = TableValidationReport(
            total_rows=10,
            valid_rows=8,
            file_format=FileFormat.CSV
        )
        
        assert report.total_rows == 10
        assert report.valid_rows == 8
        assert report.file_format == FileFormat.CSV
        assert report.success_rate == 80.0
        assert report.error_count == 0
        assert report.warning_count == 0
    
    def test_validation_report_with_issues(self):
        """Test validation report with issues."""
        from src.multichannel_messaging.core.csv_processor import ValidationIssue
        
        issues = [
            ValidationIssue(1, "email", "invalid", "format", "Invalid email", "error"),
            ValidationIssue(2, "phone", "123", "format", "Invalid phone", "warning")
        ]
        
        report = TableValidationReport(
            total_rows=10,
            valid_rows=8,
            file_format=FileFormat.JSON,
            issues=issues
        )
        
        assert report.error_count == 1
        assert report.warning_count == 1