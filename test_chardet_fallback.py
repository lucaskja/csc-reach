#!/usr/bin/env python3
"""
Test script to verify CSV processor fallback when chardet is not available.
"""

import sys
from pathlib import Path
from unittest.mock import patch

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

def test_fallback_mechanism():
    """Test CSV processor fallback when chardet is not available."""
    print("Testing CSV processor fallback mechanism...")
    
    # Mock chardet as None to simulate it not being available
    with patch('multichannel_messaging.core.csv_processor.chardet', None):
        try:
            from multichannel_messaging.core.csv_processor import CSVProcessor
            processor = CSVProcessor()
            print("✅ CSV processor imported successfully with chardet=None")
            
            # Create a test CSV file
            test_csv = Path("test_fallback.csv")
            test_csv.write_text("name,email,company\nJohn Doe,john@example.com,Test Corp\n", encoding='utf-8')
            
            # Test encoding detection fallback
            encoding = processor.detect_encoding(test_csv)
            print(f"✅ Fallback encoding detection works: {encoding}")
            
            # Clean up
            test_csv.unlink()
            
            return True
            
        except Exception as e:
            print(f"❌ Fallback test failed: {e}")
            return False

if __name__ == "__main__":
    print("🧪 CSC-Reach chardet Fallback Test")
    print("=" * 50)
    
    success = test_fallback_mechanism()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Fallback mechanism works! CSV processor can handle missing chardet.")
    else:
        print("❌ Fallback test failed.")
    
    sys.exit(0 if success else 1)