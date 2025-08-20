"""
Integration tests for multi-format table processing.
"""

import pytest
import json
import pandas as pd
from pathlib import Path

from src.multichannel_messaging.core.csv_processor import AdvancedTableProcessor, FileFormat
from src.multichannel_messaging.core.models import Customer


class TestMultiFormatIntegration:
    """Integration tests for processing multiple file formats."""
    
    @pytest.fixture
    def processor(self):
        """Create processor instance for testing."""
        return AdvancedTableProcessor()
    
    @pytest.fixture
    def sample_data(self):
        """Sample customer data for testing."""
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
            }
        ]
    
    def create_csv_file(self, tmp_path, data):
        """Create CSV file from data."""
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame(data)
        df.to_csv(csv_file, index=False)
        return csv_file
    
    def create_excel_file(self, tmp_path, data):
        """Create Excel file from data."""
        excel_file = tmp_path / "test.xlsx"
        df = pd.DataFrame(data)
        df.to_excel(excel_file, index=False, engine='openpyxl')
        return excel_file
    
    def create_json_file(self, tmp_path, data):
        """Create JSON file from data."""
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
        return json_file
    
    def create_jsonl_file(self, tmp_path, data):
        """Create JSONL file from data."""
        jsonl_file = tmp_path / "test.jsonl"
        with open(jsonl_file, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item) + '\n')
        return jsonl_file
    
    def create_tsv_file(self, tmp_path, data):
        """Create TSV file from data."""
        tsv_file = tmp_path / "test.tsv"
        df = pd.DataFrame(data)
        df.to_csv(tsv_file, index=False, sep='\t')
        return tsv_file
    
    def test_csv_end_to_end(self, processor, tmp_path, sample_data):
        """Test complete CSV processing workflow."""
        csv_file = self.create_csv_file(tmp_path, sample_data)
        
        # Detect format
        format_detected = processor.detect_file_format(csv_file)
        assert format_detected == FileFormat.CSV
        
        # Analyze structure
        structure = processor.analyze_file_structure(csv_file)
        assert structure.file_format == FileFormat.CSV
        assert len(structure.headers) == 4
        assert structure.total_rows == 3
        
        # Validate
        validation_result = processor.validate_table_format(csv_file)
        assert validation_result['valid'] is True
        
        # Load customers
        customers, report = processor.load_customers_advanced(csv_file)
        assert len(customers) == 3
        assert all(isinstance(c, Customer) for c in customers)
        assert customers[0].name == 'John Doe'
    
    @pytest.mark.skipif(not hasattr(pd, 'read_excel'), reason="pandas Excel support not available")
    def test_excel_end_to_end(self, processor, tmp_path, sample_data):
        """Test complete Excel processing workflow."""
        excel_file = self.create_excel_file(tmp_path, sample_data)
        
        # Detect format
        format_detected = processor.detect_file_format(excel_file)
        assert format_detected == FileFormat.EXCEL_XLSX
        
        # Analyze structure
        structure = processor.analyze_file_structure(excel_file)
        assert structure.file_format == FileFormat.EXCEL_XLSX
        assert len(structure.headers) == 4
        assert structure.total_rows == 3
        assert structure.sheet_names is not None
        
        # Validate
        validation_result = processor.validate_table_format(excel_file)
        assert validation_result['valid'] is True
        
        # Load customers
        customers, report = processor.load_customers_advanced(excel_file)
        assert len(customers) == 3
        assert all(isinstance(c, Customer) for c in customers)
        assert customers[0].name == 'John Doe'
    
    def test_json_end_to_end(self, processor, tmp_path, sample_data):
        """Test complete JSON processing workflow."""
        json_file = self.create_json_file(tmp_path, sample_data)
        
        # Detect format
        format_detected = processor.detect_file_format(json_file)
        assert format_detected == FileFormat.JSON
        
        # Analyze structure
        structure = processor.analyze_file_structure(json_file)
        assert structure.file_format == FileFormat.JSON
        assert len(structure.headers) == 4
        assert structure.total_rows == 3
        
        # Validate
        validation_result = processor.validate_table_format(json_file)
        assert validation_result['valid'] is True
        
        # Load customers
        customers, report = processor.load_customers_advanced(json_file)
        assert len(customers) == 3
        assert all(isinstance(c, Customer) for c in customers)
        assert customers[0].name == 'John Doe'
    
    def test_jsonl_end_to_end(self, processor, tmp_path, sample_data):
        """Test complete JSONL processing workflow."""
        jsonl_file = self.create_jsonl_file(tmp_path, sample_data)
        
        # Detect format
        format_detected = processor.detect_file_format(jsonl_file)
        assert format_detected == FileFormat.JSONL
        
        # Analyze structure
        structure = processor.analyze_file_structure(jsonl_file)
        assert structure.file_format == FileFormat.JSONL
        assert len(structure.headers) == 4
        assert structure.total_rows == 3
        
        # Validate
        validation_result = processor.validate_table_format(jsonl_file)
        assert validation_result['valid'] is True
        
        # Load customers
        customers, report = processor.load_customers_advanced(jsonl_file)
        assert len(customers) == 3
        assert all(isinstance(c, Customer) for c in customers)
        assert customers[0].name == 'John Doe'
    
    def test_tsv_end_to_end(self, processor, tmp_path, sample_data):
        """Test complete TSV processing workflow."""
        tsv_file = self.create_tsv_file(tmp_path, sample_data)
        
        # Detect format
        format_detected = processor.detect_file_format(tsv_file)
        assert format_detected == FileFormat.TSV
        
        # Analyze structure
        structure = processor.analyze_file_structure(tsv_file)
        assert structure.file_format == FileFormat.TSV
        assert structure.delimiter.delimiter == '\t'
        assert len(structure.headers) == 4
        assert structure.total_rows == 3
        
        # Validate
        validation_result = processor.validate_table_format(tsv_file)
        assert validation_result['valid'] is True
        
        # Load customers
        customers, report = processor.load_customers_advanced(tsv_file)
        assert len(customers) == 3
        assert all(isinstance(c, Customer) for c in customers)
        assert customers[0].name == 'John Doe'
    
    def test_format_consistency(self, processor, tmp_path, sample_data):
        """Test that all formats produce consistent results."""
        # Create files in different formats
        csv_file = self.create_csv_file(tmp_path, sample_data)
        json_file = self.create_json_file(tmp_path, sample_data)
        jsonl_file = self.create_jsonl_file(tmp_path, sample_data)
        tsv_file = self.create_tsv_file(tmp_path, sample_data)
        
        files_and_formats = [
            (csv_file, FileFormat.CSV),
            (json_file, FileFormat.JSON),
            (jsonl_file, FileFormat.JSONL),
            (tsv_file, FileFormat.TSV)
        ]
        
        all_customers = []
        
        for file_path, expected_format in files_and_formats:
            # Load customers from each format
            customers, report = processor.load_customers_advanced(file_path)
            
            # Verify format detection
            assert processor.detect_file_format(file_path) == expected_format
            
            # Verify consistent customer data
            assert len(customers) == 3
            all_customers.append(customers)
        
        # Verify all formats produce the same customer data
        reference_customers = all_customers[0]
        for customers in all_customers[1:]:
            for i, customer in enumerate(customers):
                ref_customer = reference_customers[i]
                assert customer.name == ref_customer.name
                assert customer.company == ref_customer.company
                assert customer.phone == ref_customer.phone
                assert customer.email == ref_customer.email
    
    def test_streaming_consistency(self, processor, tmp_path, sample_data):
        """Test that streaming and batch loading produce consistent results."""
        # Create a larger dataset for meaningful streaming test
        large_data = sample_data * 100  # 300 rows
        csv_file = self.create_csv_file(tmp_path, large_data)
        
        # Load with batch processing
        customers_batch, _ = processor.load_customers_advanced(
            csv_file, 
            stream_processing=False
        )
        
        # Load with streaming
        customers_stream, _ = processor.load_customers_advanced(
            csv_file, 
            stream_processing=True
        )
        
        # Verify same number of customers
        assert len(customers_batch) == len(customers_stream)
        
        # Verify customer data consistency
        for i, (batch_customer, stream_customer) in enumerate(zip(customers_batch, customers_stream)):
            assert batch_customer.name == stream_customer.name
            assert batch_customer.company == stream_customer.company
            assert batch_customer.phone == stream_customer.phone
            assert batch_customer.email == stream_customer.email
    
    def test_backward_compatibility(self, processor, tmp_path, sample_data):
        """Test that backward compatibility methods work correctly."""
        csv_file = self.create_csv_file(tmp_path, sample_data)
        
        # Test old CSV-specific methods still work
        customers, errors = processor.load_customers(csv_file)
        assert len(customers) == 3
        assert isinstance(errors, list)
        
        # Test old validation method
        validation_result = processor.validate_csv_format(csv_file)
        assert validation_result['valid'] is True
        
        # Test old streaming method
        chunks = list(processor.stream_csv_rows(csv_file, chunk_size=2))
        assert len(chunks) == 2  # 3 rows in chunks of 2
    
    def test_error_handling(self, processor, tmp_path):
        """Test error handling for various edge cases."""
        # Test non-existent file
        non_existent = tmp_path / "does_not_exist.csv"
        validation_result = processor.validate_table_format(non_existent)
        assert validation_result['valid'] is False
        assert any('does not exist' in error.lower() for error in validation_result['errors'])
        
        # Test empty file
        empty_file = tmp_path / "empty.csv"
        empty_file.write_text("", encoding='utf-8')
        structure = processor.analyze_file_structure(empty_file)
        assert structure.total_rows == 0
        
        # Test malformed JSON
        malformed_json = tmp_path / "malformed.json"
        malformed_json.write_text('{"invalid": json}', encoding='utf-8')
        validation_result = processor.validate_table_format(malformed_json)
        assert validation_result['valid'] is False