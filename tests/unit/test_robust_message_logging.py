"""
Comprehensive tests for the robust message logging system.
Tests all aspects of the logging system including error recovery,
database operations, and concurrent access.
"""

import pytest
import sqlite3
import tempfile
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.multichannel_messaging.core.message_logger import MessageLogger, MessageLogEntry, SessionSummary
from src.multichannel_messaging.core.models import MessageTemplate, Customer, MessageRecord, MessageStatus, MessageChannel


class TestRobustMessageLogging:
    """Test suite for robust message logging functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / "test_logs.db"
        self.logger = MessageLogger(str(self.db_path), "test_user")
        
        # Create test template and customer
        self.template = MessageTemplate(
            id="test_template",
            name="Test Template",
            subject="Test Subject",
            content="Hello {name}",
            channels=["email"]
        )
        
        self.customer = Customer(
            name="John Doe",
            email="john@example.com",
            phone="+1234567890",
            company="Test Corp"
        )
    
    def teardown_method(self):
        """Clean up test environment."""
        try:
            self.logger.close()
        except:
            pass
        
        # Clean up temp files
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass
    
    def test_database_initialization(self):
        """Test database initialization with all tables and indexes."""
        assert self.logger._is_database_available()
        assert self.db_path.exists()
        
        # Check all tables exist
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master WHERE type='table' ORDER BY name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['analytics_cache', 'message_logs', 'session_summaries', 'system_logs']
            for table in expected_tables:
                assert table in tables, f"Table {table} not found"
    
    def test_session_management(self):
        """Test session creation, tracking, and ending."""
        # Start session
        session_id = self.logger.start_session("email", self.template)
        assert session_id is not None
        assert self.logger.current_session_id == session_id
        assert self.logger.session_start_time is not None
        
        # End session
        summary = self.logger.end_session()
        assert summary is not None
        assert summary.session_id == session_id
        assert self.logger.current_session_id is None
    
    def test_message_logging(self):
        """Test comprehensive message logging."""
        # Start session
        session_id = self.logger.start_session("email", self.template)
        
        # Create message record
        message_record = MessageRecord(
            customer=self.customer,
            template=self.template,
            channel="email",
            status=MessageStatus.PENDING
        )
        
        # Log message
        log_id = self.logger.log_message(message_record, "Test message content")
        assert log_id is not None
        
        # Update status
        self.logger.update_message_status(log_id, MessageStatus.SENT, "msg_123")
        
        # Verify in database
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM message_logs WHERE id = ?", (log_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row['message_status'] == 'sent'
            assert row['message_id'] == 'msg_123'
            assert row['recipient_email'] == self.customer.email
    
    def test_database_error_recovery(self):
        """Test error recovery when database operations fail."""
        # Simulate database unavailable
        self.logger._database_available = False
        
        # Should still work without crashing
        session_id = self.logger.start_session("email", self.template)
        assert session_id is not None
        
        message_record = MessageRecord(
            customer=self.customer,
            template=self.template,
            channel="email",
            status=MessageStatus.PENDING
        )
        
        log_id = self.logger.log_message(message_record)
        assert log_id is not None
        assert log_id.startswith("test_user_")
    
    def test_concurrent_access(self):
        """Test thread-safe concurrent access to the logger."""
        session_id = self.logger.start_session("email", self.template)
        results = []
        errors = []
        
        def log_messages(thread_id):
            try:
                for i in range(10):
                    customer = Customer(
                        name=f"User {thread_id}-{i}",
                        email=f"user{thread_id}_{i}@example.com",
                        company=f"Company {thread_id}",
                        phone=f"+123456789{thread_id}"
                    )
                    
                    message_record = MessageRecord(
                        customer=customer,
                        template=self.template,
                        channel="email",
                        status=MessageStatus.PENDING
                    )
                    
                    log_id = self.logger.log_message(message_record)
                    results.append(log_id)
                    
                    # Simulate some processing time
                    time.sleep(0.001)
                    
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=log_messages, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 50  # 5 threads * 10 messages each
        assert len(set(results)) == 50  # All IDs should be unique
    
    def test_database_health_check(self):
        """Test database health monitoring."""
        health = self.logger.get_database_health()
        
        assert health['database_available'] is True
        assert health['database_exists'] is True
        assert health['database_size'] > 0
        assert 'message_logs' in health['tables']
        assert 'session_summaries' in health['tables']
        assert len(health['errors']) == 0
    
    def test_database_backup(self):
        """Test database backup functionality."""
        # Add some data first
        session_id = self.logger.start_session("email", self.template)
        
        message_record = MessageRecord(
            customer=self.customer,
            template=self.template,
            channel="email",
            status=MessageStatus.SENT
        )
        
        self.logger.log_message(message_record)
        
        # Create backup
        backup_path = self.logger.backup_database()
        backup_file = Path(backup_path)
        
        assert backup_file.exists()
        assert backup_file.stat().st_size > 0
        
        # Verify backup contains data
        with sqlite3.connect(backup_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM message_logs")
            count = cursor.fetchone()[0]
            assert count > 0
    
    def test_database_repair(self):
        """Test database repair functionality."""
        # Add some data
        session_id = self.logger.start_session("email", self.template)
        
        message_record = MessageRecord(
            customer=self.customer,
            template=self.template,
            channel="email",
            status=MessageStatus.SENT
        )
        
        self.logger.log_message(message_record)
        
        # Test repair
        result = self.logger.repair_database()
        assert result is True
        
        # Verify database still works
        health = self.logger.get_database_health()
        assert health['database_available'] is True
        assert len(health['errors']) == 0
    
    def test_system_logging(self):
        """Test internal system event logging."""
        # Start session to generate system events
        session_id = self.logger.start_session("email", self.template)
        
        # Check system logs
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM system_logs ORDER BY timestamp DESC LIMIT 5")
            logs = cursor.fetchall()
            
            assert len(logs) > 0
            
            # Check for session start event
            session_events = [log for log in logs if 'session' in log['component']]
            assert len(session_events) > 0
    
    def test_analytics_and_reporting(self):
        """Test analytics and reporting functionality."""
        # Create test data
        session_id = self.logger.start_session("email", self.template)
        
        # Log multiple messages with different statuses
        for i in range(5):
            customer = Customer(
                name=f"User {i}",
                email=f"user{i}@example.com",
                company=f"Company {i}",
                phone=f"+12345678{i:02d}"
            )
            
            message_record = MessageRecord(
                customer=customer,
                template=self.template,
                channel="email",
                status=MessageStatus.SENT if i < 3 else MessageStatus.FAILED
            )
            
            self.logger.log_message(message_record)
        
        # Get quick stats
        stats = self.logger.get_quick_stats()
        assert stats['messages_last_30_days'] == 5
        assert stats['success_rate_30_days'] == 60.0  # 3 out of 5 successful
        assert stats['current_session_active'] is True
        
        # End session and check summary
        summary = self.logger.end_session()
        assert summary.total_messages == 5
        assert summary.successful_messages == 3
        assert summary.failed_messages == 2
        assert summary.success_rate == 60.0
    
    def test_data_export(self):
        """Test data export functionality."""
        # Create test data
        session_id = self.logger.start_session("email", self.template)
        
        message_record = MessageRecord(
            customer=self.customer,
            template=self.template,
            channel="email",
            status=MessageStatus.SENT
        )
        
        self.logger.log_message(message_record)
        self.logger.end_session()
        
        # Test JSON export
        json_data = self.logger.export_data("json", 30)
        assert json_data is not None
        assert "messages" in json_data
        assert "sessions" in json_data
        
        # Test CSV export
        csv_data = self.logger.export_data("csv", 30)
        assert csv_data is not None
        assert "Message Logs" in csv_data
        assert "Session Summaries" in csv_data
    
    def test_old_data_cleanup(self):
        """Test old data cleanup functionality."""
        # Create old data by manipulating timestamps
        session_id = self.logger.start_session("email", self.template)
        
        message_record = MessageRecord(
            customer=self.customer,
            template=self.template,
            channel="email",
            status=MessageStatus.SENT
        )
        
        log_id = self.logger.log_message(message_record)
        
        # Manually update timestamp to be old
        old_timestamp = (datetime.now() - timedelta(days=100)).isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("UPDATE message_logs SET timestamp = ? WHERE id = ?", (old_timestamp, log_id))
            conn.execute("UPDATE session_summaries SET start_time = ? WHERE session_id = ?", (old_timestamp, session_id))
            conn.commit()
        
        # Test cleanup
        deleted_count = self.logger.delete_old_data(90)
        assert deleted_count > 0
        
        # Verify data was deleted
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM message_logs WHERE id = ?", (log_id,))
            count = cursor.fetchone()[0]
            assert count == 0
    
    def test_context_manager(self):
        """Test context manager functionality."""
        with MessageLogger(str(self.temp_dir / "context_test.db"), "context_user") as logger:
            assert logger._is_database_available()
            
            session_id = logger.start_session("email", self.template)
            assert session_id is not None
        
        # Logger should be properly closed after context exit
        # This is mainly to ensure no exceptions are raised


def test_logger_with_invalid_database_path():
    """Test logger behavior with invalid database path."""
    # Try to create logger with invalid path
    invalid_path = "/invalid/path/that/does/not/exist/test.db"
    logger = MessageLogger(invalid_path, "test_user")
    
    # Should handle gracefully
    assert not logger._is_database_available()
    
    # Should still work without database
    session_id = logger.start_session("email", MessageTemplate(
        id="test", name="Test", subject="Test Subject", content="Test Content", channels=["email"]
    ))
    assert session_id is not None


def test_logger_initialization_retry():
    """Test database initialization retry logic."""
    temp_dir = Path(tempfile.mkdtemp())
    db_path = temp_dir / "retry_test.db"
    
    # Create a file where the database should be (to cause initial failure)
    db_path.write_text("invalid database content")
    
    # This should eventually succeed after retries
    logger = MessageLogger(str(db_path), "retry_user")
    
    # Clean up
    try:
        logger.close()
        import shutil
        shutil.rmtree(temp_dir)
    except:
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])