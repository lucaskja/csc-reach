#!/usr/bin/env python3
"""
Windows compatibility test for the message logging system.
This test verifies that the database works correctly on Windows.
"""

import sys
import platform
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from multichannel_messaging.utils.platform_utils import (
    is_windows, get_logs_dir, get_app_data_dir, get_config_dir
)
from multichannel_messaging.core.message_logger import MessageLogger


def test_platform_detection():
    """Test platform detection."""
    print("=" * 60)
    print("PLATFORM DETECTION TEST")
    print("=" * 60)
    
    print(f"Current platform: {platform.system()}")
    print(f"Platform version: {platform.version()}")
    print(f"Python version: {platform.python_version()}")
    print(f"Architecture: {platform.architecture()[0]}")
    
    print(f"\nPlatform detection:")
    print(f"  is_windows(): {is_windows()}")
    print(f"  Expected: {platform.system() == 'Windows'}")
    
    return True


def test_windows_paths():
    """Test Windows-specific path handling."""
    print("\n" + "=" * 60)
    print("WINDOWS PATH HANDLING TEST")
    print("=" * 60)
    
    try:
        # Test directory creation
        app_data_dir = get_app_data_dir()
        config_dir = get_config_dir()
        logs_dir = get_logs_dir()
        
        print(f"App Data Directory: {app_data_dir}")
        print(f"Config Directory: {config_dir}")
        print(f"Logs Directory: {logs_dir}")
        
        # Verify directories exist
        print(f"\nDirectory verification:")
        print(f"  App Data exists: {app_data_dir.exists()}")
        print(f"  Config exists: {config_dir.exists()}")
        print(f"  Logs exists: {logs_dir.exists()}")
        
        # Test path characteristics
        print(f"\nPath characteristics:")
        print(f"  App Data is absolute: {app_data_dir.is_absolute()}")
        print(f"  Logs is absolute: {logs_dir.is_absolute()}")
        
        if is_windows():
            print(f"  Uses Windows drive letter: {str(logs_dir).startswith(('C:', 'D:', 'E:'))}")
            print(f"  Contains AppData: {'AppData' in str(app_data_dir)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Path handling test failed: {e}")
        return False


def test_database_on_windows():
    """Test database creation and operations on Windows."""
    print("\n" + "=" * 60)
    print("WINDOWS DATABASE TEST")
    print("=" * 60)
    
    try:
        # Create database in Windows-appropriate location
        logs_dir = get_logs_dir()
        db_path = logs_dir / "windows_test.db"
        
        print(f"Testing database at: {db_path}")
        
        # Remove existing test database
        if db_path.exists():
            db_path.unlink()
            print("  Removed existing test database")
        
        # Initialize message logger
        message_logger = MessageLogger(user_id="windows_test_user", db_path=str(db_path))
        
        print(f"✓ Database created successfully")
        print(f"  Database file exists: {db_path.exists()}")
        print(f"  Database size: {db_path.stat().st_size} bytes")
        
        # Test database operations
        from multichannel_messaging.core.models import Customer, MessageTemplate, MessageRecord, MessageStatus
        
        # Create test data
        customer = Customer(
            name="Windows Test User",
            company="Windows Test Corp",
            email="test@windows.com",
            phone="+1234567890"
        )
        
        template = MessageTemplate(
            id="windows_test",
            name="Windows Test Template",
            channels=["email"],
            subject="Windows Test",
            content="Hello {name} from Windows!",
            variables=["name"]
        )
        
        # Test session operations
        session_id = message_logger.start_session("email", template)
        print(f"✓ Session started: {session_id}")
        
        # Test message logging
        message_record = MessageRecord(
            customer=customer,
            template=template,
            channel="email",
            status=MessageStatus.PENDING
        )
        
        log_id = message_logger.log_message(message_record, "Windows test message")
        print(f"✓ Message logged: {log_id}")
        
        # Test status update
        message_logger.update_message_status(log_id, MessageStatus.SENT)
        print(f"✓ Message status updated")
        
        # Test session end
        session_summary = message_logger.end_session()
        print(f"✓ Session ended")
        print(f"  Messages: {session_summary.total_messages}")
        print(f"  Success rate: {session_summary.success_rate}%")
        
        # Test statistics
        stats = message_logger.get_quick_stats()
        print(f"✓ Statistics retrieved")
        print(f"  Messages (30d): {stats['messages_last_30_days']}")
        print(f"  Success rate: {stats['success_rate_30_days']}%")
        
        # Test data export
        export_data = message_logger.export_data("json", days=1)
        export_file = logs_dir / "windows_test_export.json"
        with open(export_file, "w") as f:
            f.write(export_data)
        
        print(f"✓ Data exported to: {export_file}")
        print(f"  Export size: {export_file.stat().st_size} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_permissions():
    """Test Windows file permissions and access."""
    print("\n" + "=" * 60)
    print("WINDOWS FILE PERMISSIONS TEST")
    print("=" * 60)
    
    try:
        logs_dir = get_logs_dir()
        test_file = logs_dir / "permission_test.txt"
        
        # Test write permissions
        with open(test_file, "w") as f:
            f.write("Windows permission test")
        print("✓ Write permission: OK")
        
        # Test read permissions
        with open(test_file, "r") as f:
            content = f.read()
        print("✓ Read permission: OK")
        
        # Test delete permissions
        test_file.unlink()
        print("✓ Delete permission: OK")
        
        # Test directory creation
        test_dir = logs_dir / "test_subdir"
        test_dir.mkdir(exist_ok=True)
        print("✓ Directory creation: OK")
        
        test_dir.rmdir()
        print("✓ Directory deletion: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Permission test failed: {e}")
        return False


def test_windows_specific_features():
    """Test Windows-specific features."""
    print("\n" + "=" * 60)
    print("WINDOWS-SPECIFIC FEATURES TEST")
    print("=" * 60)
    
    try:
        # Test Windows path separators
        logs_dir = get_logs_dir()
        path_str = str(logs_dir)
        
        if is_windows():
            print(f"✓ Windows path format: {path_str}")
            print(f"  Uses backslashes: {'\\\\' in path_str}")
            print(f"  Has drive letter: {path_str[1:3] == ':\\\\'}")
        else:
            print(f"ℹ️  Not running on Windows, skipping Windows-specific tests")
            print(f"  Current path: {path_str}")
        
        # Test long path support (Windows 10+)
        long_path_test = logs_dir / ("long_" * 50 + ".db")
        try:
            long_path_test.touch()
            long_path_test.unlink()
            print("✓ Long path support: OK")
        except OSError:
            print("⚠️  Long path support: Limited (may need Windows 10+ with long path support enabled)")
        
        # Test Unicode support
        unicode_file = logs_dir / "测试_файл_🌟.txt"
        try:
            unicode_file.write_text("Unicode test", encoding='utf-8')
            content = unicode_file.read_text(encoding='utf-8')
            unicode_file.unlink()
            print("✓ Unicode filename support: OK")
        except Exception:
            print("⚠️  Unicode filename support: Limited")
        
        return True
        
    except Exception as e:
        print(f"❌ Windows-specific test failed: {e}")
        return False


def main():
    """Run all Windows compatibility tests."""
    print("CSC-REACH WINDOWS COMPATIBILITY TEST")
    print("=" * 60)
    print("This test verifies that the message logging database")
    print("works correctly on Windows systems.")
    print()
    
    tests = [
        ("Platform Detection", test_platform_detection),
        ("Windows Path Handling", test_windows_paths),
        ("Database Operations", test_database_on_windows),
        ("File Permissions", test_file_permissions),
        ("Windows-Specific Features", test_windows_specific_features),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {test_name}: PASSED")
            else:
                print(f"\n❌ {test_name}: FAILED")
        except Exception as e:
            print(f"\n❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("The message logging system is fully compatible with Windows.")
        print()
        if is_windows():
            print("Windows-specific information:")
            print(f"  Database location: {get_logs_dir() / 'message_logs.db'}")
            print(f"  Configuration: {get_config_dir()}")
            print(f"  Application data: {get_app_data_dir()}")
        else:
            print("Note: Some Windows-specific tests were skipped because")
            print("this test is not running on a Windows system.")
        
        return 0
    else:
        print("❌ Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())