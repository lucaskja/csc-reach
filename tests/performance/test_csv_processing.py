#!/usr/bin/env python3
"""
Performance tests for CSV processing functionality.
"""

import sys
import time
import pytest
from pathlib import Path
from unittest.mock import Mock

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from multichannel_messaging.core.csv_processor import CSVProcessor
from multichannel_messaging.core.models import Customer


@pytest.mark.performance
@pytest.mark.slow
class TestCSVProcessingPerformance:
    """Performance tests for CSV processing."""
    
    @pytest.fixture
    def large_csv_data(self, temp_dir):
        """Create large CSV file for performance testing."""
        csv_file = temp_dir / "large_customers.csv"
        
        # Generate large CSV data
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write("name,company,email,phone,whatsapp\n")
            
            for i in range(10000):  # 10k records
                f.write(f"Customer {i},Company {i % 100},customer{i}@company{i % 100}.com,+1-555-{i:04d},+1-555-{i:04d}\n")
        
        return csv_file
    
    @pytest.fixture
    def csv_processor(self, mock_config_manager):
        """Create CSV processor for testing."""
        return CSVProcessor(mock_config_manager)
    
    def test_large_csv_parsing_performance(self, csv_processor, large_csv_data, performance_timer):
        """Test performance of parsing large CSV files."""
        performance_timer.start()
        
        # Parse the large CSV file
        customers = csv_processor.parse_csv(large_csv_data)
        
        performance_timer.stop()
        
        # Verify results
        assert len(customers) == 10000
        assert all(isinstance(customer, Customer) for customer in customers)
        
        # Performance assertions
        elapsed_time = performance_timer.elapsed
        assert elapsed_time < 5.0, f"CSV parsing took too long: {elapsed_time:.2f}s"
        
        # Memory efficiency check (rough estimate)
        import sys
        memory_per_record = sys.getsizeof(customers) / len(customers)
        assert memory_per_record < 1000, f"Memory usage too high: {memory_per_record} bytes per record"
        
        print(f"✅ Parsed {len(customers)} records in {elapsed_time:.2f}s ({len(customers)/elapsed_time:.0f} records/sec)")
    
    def test_csv_validation_performance(self, csv_processor, large_csv_data, performance_timer):
        """Test performance of CSV validation."""
        # First parse the CSV
        customers = csv_processor.parse_csv(large_csv_data)
        
        performance_timer.start()
        
        # Validate all customers
        validation_results = []
        for customer in customers:
            validation_results.append(csv_processor.validate_customer(customer))
        
        performance_timer.stop()
        
        # Verify results
        assert len(validation_results) == len(customers)
        
        # Performance assertions
        elapsed_time = performance_timer.elapsed
        assert elapsed_time < 3.0, f"CSV validation took too long: {elapsed_time:.2f}s"
        
        print(f"✅ Validated {len(customers)} records in {elapsed_time:.2f}s ({len(customers)/elapsed_time:.0f} records/sec)")
    
    def test_memory_usage_with_large_dataset(self, csv_processor, large_csv_data):
        """Test memory usage with large datasets."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Parse large CSV
        customers = csv_processor.parse_csv(large_csv_data)
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Clean up
        del customers
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Memory assertions
        assert memory_increase < 100, f"Memory usage too high: {memory_increase:.1f} MB"
        
        print(f"✅ Memory usage: {memory_increase:.1f} MB increase, {final_memory:.1f} MB final")
    
    @pytest.mark.parametrize("record_count", [1000, 5000, 10000])
    def test_scalability_with_different_sizes(self, csv_processor, temp_dir, record_count, performance_timer):
        """Test scalability with different dataset sizes."""
        # Create CSV with specific record count
        csv_file = temp_dir / f"customers_{record_count}.csv"
        
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write("name,company,email,phone,whatsapp\n")
            
            for i in range(record_count):
                f.write(f"Customer {i},Company {i % 100},customer{i}@company{i % 100}.com,+1-555-{i:04d},+1-555-{i:04d}\n")
        
        performance_timer.start()
        customers = csv_processor.parse_csv(csv_file)
        performance_timer.stop()
        
        # Verify results
        assert len(customers) == record_count
        
        # Calculate performance metrics
        elapsed_time = performance_timer.elapsed
        records_per_second = record_count / elapsed_time
        
        # Performance should scale reasonably
        expected_min_rps = 2000  # Minimum 2000 records per second
        assert records_per_second >= expected_min_rps, f"Performance too slow: {records_per_second:.0f} records/sec"
        
        print(f"✅ {record_count} records: {elapsed_time:.2f}s ({records_per_second:.0f} records/sec)")


if __name__ == "__main__":
    pytest.main([__file__])