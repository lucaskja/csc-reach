#!/usr/bin/env python3
"""
Quick test script to verify chardet import and functionality.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

def test_chardet_import():
    """Test chardet import and basic functionality."""
    print("Testing chardet import...")
    
    try:
        import chardet
        print(f"✅ chardet imported successfully: {chardet.__version__}")
        
        # Test basic functionality
        test_data = "Hello, world! This is a test string.".encode('utf-8')
        result = chardet.detect(test_data)
        print(f"✅ chardet.detect() works: {result}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import chardet: {e}")
        return False
    except Exception as e:
        print(f"❌ chardet functionality test failed: {e}")
        return False

def test_csv_processor():
    """Test CSV processor with chardet integration."""
    print("\nTesting CSV processor...")
    
    try:
        from multichannel_messaging.core.csv_processor import CSVProcessor
        processor = CSVProcessor()
        print("✅ CSV processor imported successfully")
        
        # Create a test CSV file
        test_csv = Path("test_sample.csv")
        test_csv.write_text("name,email,company\nJohn Doe,john@example.com,Test Corp\n", encoding='utf-8')
        
        # Test encoding detection
        encoding = processor.detect_encoding(test_csv)
        print(f"✅ Encoding detection works: {encoding}")
        
        # Clean up
        test_csv.unlink()
        
        return True
        
    except Exception as e:
        print(f"❌ CSV processor test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 CSC-Reach chardet Integration Test")
    print("=" * 50)
    
    success = True
    success &= test_chardet_import()
    success &= test_csv_processor()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! chardet integration is working.")
    else:
        print("❌ Some tests failed. Check the output above.")
    
    sys.exit(0 if success else 1)