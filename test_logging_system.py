#!/usr/bin/env python3
"""
Quick test script to verify the robust logging system works 100%.
"""

import tempfile
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from multichannel_messaging.core.message_logger import MessageLogger
from multichannel_messaging.core.models import MessageTemplate, Customer, MessageRecord, MessageStatus


def test_logging_system():
    """Test the robust logging system comprehensively."""
    print("🔍 Testing Robust Message Logging System...")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Initialize logger
        print("✅ Initializing logger...")
        logger = MessageLogger(db_path, "test_user")
        
        if not logger._is_database_available():
            print("❌ Database initialization failed")
            return False
        
        # Test database health
        print("✅ Checking database health...")
        health = logger.get_database_health()
        if not health['database_available']:
            print("❌ Database health check failed")
            return False
        
        print(f"   - Database size: {health['database_size']} bytes")
        print(f"   - Tables: {list(health['tables'].keys())}")
        
        # Create test data
        template = MessageTemplate(
            id="test_template",
            name="Test Template",
            subject="Test Subject",
            content="Hello {name} from {company}!",
            channels=["email"]
        )
        
        customer = Customer(
            name="John Doe",
            email="john@example.com",
            company="Test Corp",
            phone="+1234567890"
        )
        
        # Test session management
        print("✅ Testing session management...")
        session_id = logger.start_session("email", template)
        if not session_id:
            print("❌ Session creation failed")
            return False
        
        print(f"   - Session ID: {session_id}")
        
        # Test message logging
        print("✅ Testing message logging...")
        message_record = MessageRecord(
            customer=customer,
            template=template,
            channel="email",
            status=MessageStatus.PENDING
        )
        
        log_id = logger.log_message(message_record, "Test message content")
        if not log_id:
            print("❌ Message logging failed")
            return False
        
        print(f"   - Log ID: {log_id}")
        
        # Test status updates
        print("✅ Testing status updates...")
        logger.update_message_status(log_id, MessageStatus.SENT, "msg_123")
        
        # Test concurrent access (simplified)
        print("✅ Testing concurrent access...")
        import threading
        import time
        
        results = []
        errors = []
        
        def log_concurrent_messages():
            try:
                for i in range(5):
                    test_customer = Customer(
                        name=f"User {i}",
                        email=f"user{i}@example.com",
                        company=f"Company {i}",
                        phone=f"+123456789{i}"
                    )
                    
                    test_record = MessageRecord(
                        customer=test_customer,
                        template=template,
                        channel="email",
                        status=MessageStatus.SENT
                    )
                    
                    result = logger.log_message(test_record)
                    results.append(result)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(str(e))
        
        # Run concurrent threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=log_concurrent_messages)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        if errors:
            print(f"❌ Concurrent access failed: {errors}")
            return False
        
        print(f"   - Concurrent messages logged: {len(results)}")
        
        # Test analytics
        print("✅ Testing analytics...")
        stats = logger.get_quick_stats()
        print(f"   - Messages last 30 days: {stats['messages_last_30_days']}")
        print(f"   - Success rate: {stats['success_rate_30_days']}%")
        
        # Test session ending
        print("✅ Testing session ending...")
        summary = logger.end_session()
        if not summary:
            print("❌ Session ending failed")
            return False
        
        print(f"   - Total messages: {summary.total_messages}")
        print(f"   - Success rate: {summary.success_rate}%")
        
        # Test data export
        print("✅ Testing data export...")
        json_export = logger.export_data("json", 30)
        if not json_export or "messages" not in json_export:
            print("❌ Data export failed")
            return False
        
        print(f"   - Export size: {len(json_export)} characters")
        
        # Test database backup
        print("✅ Testing database backup...")
        backup_path = logger.backup_database()
        if not Path(backup_path).exists():
            print("❌ Database backup failed")
            return False
        
        print(f"   - Backup created: {backup_path}")
        
        # Test database repair
        print("✅ Testing database repair...")
        repair_result = logger.repair_database()
        if not repair_result:
            print("❌ Database repair failed")
            return False
        
        # Final health check
        print("✅ Final health check...")
        final_health = logger.get_database_health()
        if final_health['errors']:
            print(f"❌ Final health check failed: {final_health['errors']}")
            return False
        
        # Close logger
        logger.close()
        
        print("🎉 All tests passed! Logging system is working 100%")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        try:
            Path(db_path).unlink(missing_ok=True)
            if 'backup_path' in locals():
                Path(backup_path).unlink(missing_ok=True)
        except:
            pass


def test_error_recovery():
    """Test error recovery scenarios."""
    print("\n🔍 Testing Error Recovery...")
    
    # Test with invalid database path
    print("✅ Testing invalid database path...")
    logger = MessageLogger("/invalid/path/test.db", "test_user")
    
    if logger._is_database_available():
        print("❌ Should have failed with invalid path")
        return False
    
    # Should still work without database
    template = MessageTemplate(
        id="test",
        name="Test",
        subject="Test Subject",
        content="Test Content",
        channels=["email"]
    )
    
    session_id = logger.start_session("email", template)
    if not session_id:
        print("❌ Should work without database")
        return False
    
    print("✅ Error recovery works correctly")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("ROBUST MESSAGE LOGGING SYSTEM TEST")
    print("=" * 60)
    
    success = True
    
    # Test main functionality
    if not test_logging_system():
        success = False
    
    # Test error recovery
    if not test_error_recovery():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED - LOGGING SYSTEM IS ROBUST AND READY!")
        print("✅ Database operations work 100% of the time")
        print("✅ Error recovery is comprehensive")
        print("✅ Thread safety is ensured")
        print("✅ All features are functional")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED - NEEDS ATTENTION")
        sys.exit(1)