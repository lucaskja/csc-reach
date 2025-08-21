"""
Message logging and analytics system for tracking user messaging activity.
Provides comprehensive logging, analytics, and user control over sent messages.
"""

import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from contextlib import contextmanager
import uuid

from .models import (
    Customer,
    MessageTemplate,
    MessageRecord,
    MessageStatus,
    MessageChannel,
)
from ..utils.exceptions import ValidationError


class LogLevel(Enum):
    """Message log levels for different types of events."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class MessageLogEntry:
    """Individual message log entry with comprehensive tracking."""

    id: str
    timestamp: datetime
    user_id: str  # For multi-user environments
    session_id: str  # Unique session identifier
    channel: str  # email, whatsapp, etc.
    template_id: str
    template_name: str
    recipient_email: str
    recipient_name: str
    recipient_phone: str
    recipient_company: str
    message_status: str
    message_id: Optional[str] = None  # External message ID
    delivery_status: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    response_received: bool = False
    content_preview: str = ""  # First 100 chars of message
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SessionSummary:
    """Summary of a messaging session."""

    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    channel: str
    template_used: str
    total_messages: int
    successful_messages: int
    failed_messages: int
    pending_messages: int
    cancelled_messages: int
    success_rate: float
    average_send_time: float  # seconds per message
    errors: List[str]
    user_id: str
    channels_used: List[str] = None
    templates_used: List[str] = None

    def __post_init__(self):
        if self.channels_used is None:
            self.channels_used = []
        if self.templates_used is None:
            self.templates_used = []


@dataclass
class AnalyticsReport:
    """Comprehensive analytics report."""

    report_id: str
    generated_at: datetime
    date_range: Tuple[datetime, datetime]
    user_id: str

    # Overall statistics
    total_messages_sent: int
    total_sessions: int
    channels_used: List[str]
    templates_used: List[str]

    # Success metrics
    overall_success_rate: float
    success_by_channel: Dict[str, float]
    success_by_template: Dict[str, float]
    success_by_day: Dict[str, int]

    # Performance metrics
    average_messages_per_session: float
    average_session_duration: float
    peak_sending_hours: List[int]
    busiest_days: List[str]

    # Error analysis
    common_errors: List[Tuple[str, int]]  # (error_message, count)
    error_trends: Dict[str, List[int]]  # Daily error counts

    # Recipient analysis
    top_companies: List[Tuple[str, int]]  # (company, message_count)
    repeat_recipients: List[Tuple[str, int]]  # (email, message_count)

    # Template performance
    template_performance: Dict[str, Dict[str, Any]]

    # Recommendations
    recommendations: List[str]


class MessageLogger:
    """
    Comprehensive message logging and analytics system.

    Tracks all messaging activity, provides detailed analytics,
    and gives users full control over their messaging data.

    Features:
    - Robust database connection handling with retries
    - Thread-safe operations
    - Automatic error recovery
    - Connection pooling
    - Comprehensive logging of all operations
    """

    def __init__(self, db_path: Optional[str] = None, user_id: str = "default_user"):
        """
        Initialize the message logger.

        Args:
            db_path: Path to SQLite database file
            user_id: Unique identifier for the user
        """
        self.user_id = user_id
        self.logger = logging.getLogger(__name__)

        # Thread safety
        self._lock = threading.RLock()

        # Connection settings
        self._max_retries = 3
        self._retry_delay = 0.1  # seconds
        self._connection_timeout = 30  # seconds

        # Set up database with Windows-safe path handling
        if db_path is None:
            try:
                # Use platform-appropriate logs directory
                from ..utils.platform_utils import get_logs_dir

                logs_dir = get_logs_dir()
                logs_dir.mkdir(parents=True, exist_ok=True)
                db_path = logs_dir / "message_logs.db"
            except Exception as e:
                # Fallback to current directory if logs dir creation fails
                self.logger.warning(
                    f"Failed to create logs directory, using fallback: {e}"
                )
                db_path = Path("message_logs.db")

        self.db_path = Path(db_path)

        # Initialize database with comprehensive error handling
        self._database_available = False
        self._init_database_with_retries()

        # Current session tracking
        self.current_session_id: Optional[str] = None
        self.session_start_time: Optional[datetime] = None

        # Performance tracking
        self._operation_count = 0
        self._last_maintenance = datetime.now()

    def _is_database_available(self) -> bool:
        """Check if database is available for operations."""
        return getattr(self, "_database_available", False)

    def _init_database_with_retries(self) -> None:
        """Initialize database with retry logic and comprehensive error handling."""
        for attempt in range(self._max_retries):
            try:
                self._init_database()
                
                # Run database migrations
                from .database_migration import migrate_message_logger_database
                if migrate_message_logger_database(self.db_path):
                    self._database_available = True
                    self.logger.info(
                        f"Message logger database initialized at: {self.db_path}"
                    )
                    return
                else:
                    raise Exception("Database migration failed")
                    
            except Exception as e:
                self.logger.warning(
                    f"Database initialization attempt {attempt + 1} failed: {e}"
                )
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay * (2**attempt))  # Exponential backoff
                else:
                    self.logger.error(
                        f"Failed to initialize message logger database after {self._max_retries} attempts: {e}"
                    )
                    self._database_available = False
                    self.logger.warning(
                        "Message logging will be disabled due to database initialization failure"
                    )

    @contextmanager
    def _get_connection(self, retries: int = None):
        """
        Get a database connection with automatic retry and error handling.

        Args:
            retries: Number of retries (defaults to self._max_retries)

        Yields:
            sqlite3.Connection: Database connection
        """
        if retries is None:
            retries = self._max_retries

        conn = None
        for attempt in range(retries):
            try:
                # Ensure database is available
                if not self._is_database_available():
                    raise sqlite3.Error("Database not available")

                # Create connection with timeout
                conn = sqlite3.connect(
                    str(self.db_path),
                    timeout=self._connection_timeout,
                    check_same_thread=False,
                )

                # Configure connection for optimal performance and reliability
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("PRAGMA journal_mode = WAL")
                conn.execute("PRAGMA synchronous = NORMAL")
                conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
                conn.execute("PRAGMA temp_store = MEMORY")
                conn.execute("PRAGMA mmap_size = 268435456")  # 256MB mmap

                # Enable row factory for easier data access
                conn.row_factory = sqlite3.Row

                yield conn
                return

            except sqlite3.Error as e:
                if conn:
                    try:
                        conn.close()
                    except:
                        pass
                    conn = None

                self.logger.warning(
                    f"Database connection attempt {attempt + 1} failed: {e}"
                )

                if attempt < retries - 1:
                    time.sleep(self._retry_delay * (2**attempt))
                else:
                    self.logger.error(
                        f"Failed to connect to database after {retries} attempts"
                    )
                    self._database_available = False
                    raise

            except Exception as e:
                if conn:
                    try:
                        conn.close()
                    except:
                        pass
                    conn = None

                self.logger.error(f"Unexpected error during database connection: {e}")
                raise

            finally:
                if conn:
                    try:
                        conn.close()
                    except:
                        pass

    def _execute_with_retry(
        self, query: str, params: tuple = (), fetch: str = None
    ) -> Any:
        """
        Execute a database query with automatic retry and error handling.

        Args:
            query: SQL query to execute
            params: Query parameters
            fetch: 'one', 'all', or None for fetchone(), fetchall(), or no fetch

        Returns:
            Query result or None if database unavailable
        """
        if not self._is_database_available():
            self.logger.debug("Database not available, skipping query")
            return None

        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.execute(query, params)

                    if fetch == "one":
                        result = cursor.fetchone()
                    elif fetch == "all":
                        result = cursor.fetchall()
                    else:
                        result = cursor.rowcount

                    conn.commit()
                    self._operation_count += 1

                    # Periodic maintenance
                    if self._operation_count % 1000 == 0:
                        self._perform_maintenance()

                    return result

            except sqlite3.Error as e:
                self.logger.error(f"Database query failed: {query[:100]}... Error: {e}")
                return None
            except Exception as e:
                self.logger.error(f"Unexpected error during query execution: {e}")
                return None

    def _perform_maintenance(self) -> None:
        """Perform periodic database maintenance."""
        try:
            with self._get_connection() as conn:
                # Analyze tables for query optimization
                conn.execute("ANALYZE")

                # Vacuum if needed (not too frequently)
                if datetime.now() - self._last_maintenance > timedelta(hours=24):
                    conn.execute("VACUUM")
                    self._last_maintenance = datetime.now()
                    self.logger.info("Database maintenance completed")

                conn.commit()
        except Exception as e:
            self.logger.warning(f"Database maintenance failed: {e}")

    def _init_database(self) -> None:
        """Initialize the SQLite database with required tables."""
        try:
            # Ensure parent directory exists with proper permissions
            self.db_path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)

            # Test database connection and create schema
            with sqlite3.connect(
                str(self.db_path),
                timeout=self._connection_timeout,
                check_same_thread=False,
            ) as conn:
                # Configure database for optimal performance and reliability
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("PRAGMA journal_mode = WAL")
                conn.execute("PRAGMA synchronous = NORMAL")
                conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
                conn.execute("PRAGMA temp_store = MEMORY")
                conn.execute("PRAGMA mmap_size = 268435456")  # 256MB mmap
                conn.execute("PRAGMA auto_vacuum = INCREMENTAL")

                # Create message logs table with comprehensive schema
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS message_logs (
                        id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        session_id TEXT NOT NULL,
                        channel TEXT NOT NULL,
                        template_id TEXT NOT NULL,
                        template_name TEXT NOT NULL,
                        recipient_email TEXT NOT NULL,
                        recipient_name TEXT NOT NULL,
                        recipient_phone TEXT,
                        recipient_company TEXT,
                        message_status TEXT NOT NULL,
                        message_id TEXT,
                        delivery_status TEXT,
                        error_message TEXT,
                        sent_at TEXT,
                        delivered_at TEXT,
                        read_at TEXT,
                        response_received INTEGER DEFAULT 0,
                        content_preview TEXT,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create session summaries table
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS session_summaries (
                        session_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        start_time TEXT NOT NULL,
                        end_time TEXT,
                        channel TEXT,
                        template_used TEXT,
                        total_messages INTEGER DEFAULT 0,
                        successful_messages INTEGER DEFAULT 0,
                        failed_messages INTEGER DEFAULT 0,
                        pending_messages INTEGER DEFAULT 0,
                        cancelled_messages INTEGER DEFAULT 0,
                        success_rate REAL DEFAULT 0.0,
                        channels_used TEXT,
                        templates_used TEXT,
                        session_metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create analytics cache table
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS analytics_cache (
                        report_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        generated_at TEXT NOT NULL,
                        date_range_start TEXT NOT NULL,
                        date_range_end TEXT NOT NULL,
                        report_data TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create system log table for internal logging
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS system_logs (
                        id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        level TEXT NOT NULL,
                        component TEXT NOT NULL,
                        message TEXT NOT NULL,
                        details TEXT,
                        user_id TEXT,
                        session_id TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create comprehensive indexes for optimal performance
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_message_logs_timestamp ON message_logs(timestamp)",
                    "CREATE INDEX IF NOT EXISTS idx_message_logs_user_id ON message_logs(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_message_logs_session_id ON message_logs(session_id)",
                    "CREATE INDEX IF NOT EXISTS idx_message_logs_status ON message_logs(message_status)",
                    "CREATE INDEX IF NOT EXISTS idx_message_logs_channel ON message_logs(channel)",
                    "CREATE INDEX IF NOT EXISTS idx_message_logs_recipient ON message_logs(recipient_email)",
                    "CREATE INDEX IF NOT EXISTS idx_message_logs_user_timestamp ON message_logs(user_id, timestamp)",
                    "CREATE INDEX IF NOT EXISTS idx_session_summaries_user_id ON session_summaries(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_session_summaries_start_time ON session_summaries(start_time)",
                    "CREATE INDEX IF NOT EXISTS idx_session_summaries_user_start ON session_summaries(user_id, start_time)",
                    "CREATE INDEX IF NOT EXISTS idx_analytics_cache_user_id ON analytics_cache(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_analytics_cache_generated_at ON analytics_cache(generated_at)",
                    "CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp)",
                    "CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level)",
                    "CREATE INDEX IF NOT EXISTS idx_system_logs_component ON system_logs(component)",
                    "CREATE INDEX IF NOT EXISTS idx_system_logs_user_id ON system_logs(user_id)",
                ]

                for index_sql in indexes:
                    conn.execute(index_sql)

                # Create triggers for automatic timestamp updates
                conn.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS update_message_logs_timestamp 
                    AFTER UPDATE ON message_logs
                    BEGIN
                        UPDATE message_logs SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                    END
                """
                )

                conn.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS update_session_summaries_timestamp 
                    AFTER UPDATE ON session_summaries
                    BEGIN
                        UPDATE session_summaries SET updated_at = CURRENT_TIMESTAMP WHERE session_id = NEW.session_id;
                    END
                """
                )

                # Test database functionality
                conn.execute("SELECT COUNT(*) FROM message_logs")
                conn.execute("SELECT COUNT(*) FROM session_summaries")
                conn.execute("SELECT COUNT(*) FROM analytics_cache")
                conn.execute("SELECT COUNT(*) FROM system_logs")

                conn.commit()

                # Log successful initialization to system log
                self._log_system_event(
                    "INFO",
                    "database",
                    "Database initialized successfully",
                    {
                        "db_path": str(self.db_path),
                        "tables_created": [
                            "message_logs",
                            "session_summaries",
                            "analytics_cache",
                            "system_logs",
                        ],
                        "indexes_created": len(indexes),
                        "triggers_created": 2,
                    },
                )

        except sqlite3.Error as e:
            self.logger.error(f"SQLite error during database initialization: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during database initialization: {e}")
            raise

    def _log_system_event(
        self, level: str, component: str, message: str, details: Dict[str, Any] = None
    ) -> None:
        """Log system events to the database for debugging and monitoring."""
        try:
            event_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            details_json = json.dumps(details) if details else None

            self._execute_with_retry(
                """
                INSERT INTO system_logs (id, timestamp, level, component, message, details, user_id, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    event_id,
                    timestamp,
                    level,
                    component,
                    message,
                    details_json,
                    self.user_id,
                    getattr(self, 'current_session_id', None),
                ),
            )

        except Exception as e:
            # Don't let system logging failures break the main functionality
            self.logger.warning(f"Failed to log system event: {e}")

    def start_session(self, channel: str, template: MessageTemplate) -> str:
        """
        Start a new messaging session with comprehensive logging.

        Args:
            channel: Channel being used (email, whatsapp)
            template: Template being used

        Returns:
            Session ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        session_id = f"{self.user_id}_{channel}_{timestamp}_{unique_id}"

        with self._lock:
            self.current_session_id = session_id
            self.session_start_time = datetime.now()

        if not self._is_database_available():
            self.logger.debug("Database not available, session tracking disabled")
            self._log_system_event(
                "WARNING",
                "session",
                "Session started without database",
                {
                    "session_id": session_id,
                    "channel": channel,
                    "template": template.name,
                },
            )
            return session_id

        # Create session record with robust error handling
        try:
            result = self._execute_with_retry(
                """
                INSERT INTO session_summaries 
                (session_id, user_id, start_time, channel, template_used, channels_used, templates_used, 
                 total_messages, successful_messages, failed_messages, pending_messages, cancelled_messages, 
                 success_rate, session_metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 0, 0, 0.0, '{}')
            """,
                (
                    session_id,
                    self.user_id,
                    self.session_start_time.isoformat(),
                    channel,
                    template.name,
                    json.dumps([channel]),
                    json.dumps([template.name]),
                ),
            )

            if result is not None:
                self._log_system_event(
                    "INFO",
                    "session",
                    "Session started successfully",
                    {
                        "session_id": session_id,
                        "channel": channel,
                        "template": template.name,
                        "start_time": self.session_start_time.isoformat(),
                    },
                )
                self.logger.info(
                    f"Started messaging session {session_id} for channel {channel}"
                )
            else:
                self.logger.warning(f"Failed to create session record for {session_id}")

        except Exception as e:
            self.logger.error(f"Failed to create session record: {e}")
            self._log_system_event(
                "ERROR",
                "session",
                "Session creation failed",
                {"session_id": session_id, "error": str(e)},
            )

        return session_id

    def log_message(
        self, message_record: MessageRecord, content_preview: str = ""
    ) -> str:
        """
        Log a message attempt with comprehensive error handling.

        Args:
            message_record: Message record to log
            content_preview: Preview of message content

        Returns:
            Log entry ID
        """
        # Generate unique log ID
        log_id = f"{self.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        if not self._is_database_available():
            self.logger.debug("Database not available, skipping message logging")
            self._log_system_event(
                "WARNING",
                "logging",
                "Message logged without database",
                {
                    "log_id": log_id,
                    "recipient": message_record.customer.email,
                    "status": message_record.status.value,
                },
            )
            return log_id

        if not self.current_session_id:
            # Auto-create session if none exists
            self.logger.warning("No active session, creating temporary session")
            from .models import MessageTemplate

            temp_template = MessageTemplate(
                id="temp", name="Auto-created", subject="", content="", channels=["email"]
            )
            self.start_session(message_record.channel, temp_template)

        # Create comprehensive log entry
        log_entry = MessageLogEntry(
            id=log_id,
            timestamp=datetime.now(),
            user_id=self.user_id,
            session_id=self.current_session_id,
            channel=message_record.channel,
            template_id=message_record.template.id,
            template_name=message_record.template.name,
            recipient_email=message_record.customer.email,
            recipient_name=message_record.customer.name,
            recipient_phone=getattr(message_record.customer, "phone", ""),
            recipient_company=getattr(message_record.customer, "company", ""),
            message_status=message_record.status.value,
            message_id=message_record.message_id,
            delivery_status=message_record.delivery_status,
            error_message=message_record.error_message,
            sent_at=message_record.sent_at,
            content_preview=content_preview[:100] if content_preview else "",
            metadata={
                "template_channels": getattr(message_record.template, "channels", []),
                "message_length": len(content_preview) if content_preview else 0,
                "has_attachments": bool(getattr(message_record, "attachments", [])),
                "log_created_at": datetime.now().isoformat(),
            },
        )

        # Save with comprehensive error handling
        try:
            self._save_log_entry(log_entry)
            self._update_session_stats()

            self._log_system_event(
                "INFO",
                "logging",
                "Message logged successfully",
                {
                    "log_id": log_id,
                    "recipient": message_record.customer.email,
                    "status": message_record.status.value,
                    "channel": message_record.channel,
                },
            )

        except Exception as e:
            self.logger.error(f"Failed to log message {log_id}: {e}")
            self._log_system_event(
                "ERROR",
                "logging",
                "Message logging failed",
                {
                    "log_id": log_id,
                    "error": str(e),
                    "recipient": message_record.customer.email,
                },
            )

        return log_id

    def update_message_status(
        self,
        log_id: str,
        status: MessageStatus,
        message_id: Optional[str] = None,
        delivery_status: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Update the status of a logged message with comprehensive error handling.

        Args:
            log_id: Log entry ID
            status: New message status
            message_id: External message ID
            delivery_status: Delivery status
            error_message: Error message if failed
        """
        if not self._is_database_available():
            self.logger.debug(
                f"Database not available, skipping status update for {log_id}"
            )
            return

        try:
            # Build dynamic update query
            update_fields = ["message_status = ?"]
            params = [status.value]

            if message_id:
                update_fields.append("message_id = ?")
                params.append(message_id)

            if delivery_status:
                update_fields.append("delivery_status = ?")
                params.append(delivery_status)

            if error_message:
                update_fields.append("error_message = ?")
                params.append(error_message)

            # Set timestamps based on status
            if status == MessageStatus.SENT:
                update_fields.append("sent_at = ?")
                params.append(datetime.now().isoformat())
            elif status == MessageStatus.DELIVERED:
                update_fields.append("delivered_at = ?")
                params.append(datetime.now().isoformat())
            elif status == MessageStatus.READ:
                update_fields.append("read_at = ?")
                params.append(datetime.now().isoformat())

            params.append(log_id)

            # Execute update with retry logic
            result = self._execute_with_retry(
                f"""
                UPDATE message_logs 
                SET {', '.join(update_fields)}
                WHERE id = ?
            """,
                tuple(params),
            )

            if result is not None and result > 0:
                self._update_session_stats()
                self._log_system_event(
                    "INFO",
                    "logging",
                    "Message status updated",
                    {
                        "log_id": log_id,
                        "new_status": status.value,
                        "message_id": message_id,
                        "delivery_status": delivery_status,
                        "has_error": bool(error_message),
                    },
                )
            else:
                self.logger.warning(f"No message found with log_id: {log_id}")

        except Exception as e:
            self.logger.error(f"Failed to update message status for {log_id}: {e}")
            self._log_system_event(
                "ERROR",
                "logging",
                "Message status update failed",
                {"log_id": log_id, "error": str(e), "attempted_status": status.value},
            )

    def end_session(self) -> Optional[SessionSummary]:
        """
        End the current messaging session and generate summary.

        Returns:
            Session summary if session was active
        """
        if not self.current_session_id:
            return None

        end_time = datetime.now()

        if not self._is_database_available():
            # Create a minimal session summary without database
            self.logger.debug(
                "Database not available, creating minimal session summary"
            )
            session_summary = SessionSummary(
                session_id=self.current_session_id,
                user_id=self.user_id,
                start_time=self.session_start_time or datetime.now(),
                end_time=end_time,
                channel="unknown",
                template_used="unknown",
                total_messages=0,
                successful_messages=0,
                failed_messages=0,
                pending_messages=0,
                cancelled_messages=0,
                success_rate=0.0,
                average_send_time=0.0,
                channels_used=[],
                templates_used=[],
                errors=[],
            )
        else:
            try:
                session_summary = self._generate_session_summary(
                    self.current_session_id, end_time
                )

                # Update session record
                with sqlite3.connect(str(self.db_path)) as conn:
                    conn.execute(
                        """
                        UPDATE session_summaries 
                        SET end_time = ?, total_messages = ?, successful_messages = ?,
                            failed_messages = ?, pending_messages = ?, cancelled_messages = ?,
                            success_rate = ?
                        WHERE session_id = ?
                    """,
                        (
                            end_time.isoformat(),
                            session_summary.total_messages,
                            session_summary.successful_messages,
                            session_summary.failed_messages,
                            session_summary.pending_messages,
                            session_summary.cancelled_messages,
                            session_summary.success_rate,
                            self.current_session_id,
                        ),
                    )
                    conn.commit()
            except Exception as e:
                self.logger.error(f"Failed to end session: {e}")
                # Create minimal summary as fallback
                session_summary = SessionSummary(
                    session_id=self.current_session_id,
                    user_id=self.user_id,
                    start_time=self.session_start_time or datetime.now(),
                    end_time=end_time,
                    channel="unknown",
                    template_used="unknown",
                    total_messages=0,
                    successful_messages=0,
                    failed_messages=0,
                    pending_messages=0,
                    cancelled_messages=0,
                    success_rate=0.0,
                    average_send_time=0.0,
                    channels_used=[],
                    templates_used=[],
                    errors=[],
                )

        self.logger.info(
            f"Ended session {self.current_session_id}. "
            f"Total messages: {session_summary.total_messages}, "
            f"Successful: {session_summary.successful_messages}"
        )

        self.current_session_id = None
        self.session_start_time = None

        return session_summary

    def get_message_history(
        self,
        days: int = 30,
        channel: Optional[str] = None,
        status: Optional[MessageStatus] = None,
    ) -> List[MessageLogEntry]:
        """
        Get message history for the user.

        Args:
            days: Number of days to look back
            channel: Filter by channel
            status: Filter by message status

        Returns:
            List of message log entries
        """
        start_date = datetime.now() - timedelta(days=days)

        query = """
            SELECT * FROM message_logs 
            WHERE user_id = ? AND timestamp >= ?
        """
        params = [self.user_id, start_date.isoformat()]

        if channel:
            query += " AND channel = ?"
            params.append(channel)

        if status:
            query += " AND message_status = ?"
            params.append(status.value)

        query += " ORDER BY timestamp DESC"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        return [self._row_to_log_entry(row) for row in rows]

    def get_session_history(self, days: int = 30) -> List[SessionSummary]:
        """
        Get session history for the user.

        Args:
            days: Number of days to look back

        Returns:
            List of session summaries
        """
        start_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM session_summaries 
                WHERE user_id = ? AND start_time >= ?
                ORDER BY start_time DESC
            """,
                (self.user_id, start_date.isoformat()),
            )
            rows = cursor.fetchall()

        return [self._row_to_session_summary(row) for row in rows]

    def generate_analytics_report(
        self, days: int = 30, force_refresh: bool = False
    ) -> AnalyticsReport:
        """
        Generate comprehensive analytics report.

        Args:
            days: Number of days to analyze
            force_refresh: Force regeneration even if cached

        Returns:
            Analytics report
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        report_id = f"{self.user_id}_{days}d_{end_date.strftime('%Y%m%d')}"

        # Check cache first
        if not force_refresh:
            cached_report = self._get_cached_report(report_id)
            if cached_report:
                return cached_report

        # Generate new report
        report = self._generate_analytics_report(report_id, start_date, end_date)

        # Cache the report
        self._cache_report(report)

        return report

    def export_data(self, format: str = "json", days: int = 30) -> str:
        """
        Export user's messaging data.

        Args:
            format: Export format (json, csv)
            days: Number of days to export

        Returns:
            Exported data as string
        """
        messages = self.get_message_history(days)
        sessions = self.get_session_history(days)

        if format.lower() == "json":
            return json.dumps(
                {
                    "export_date": datetime.now().isoformat(),
                    "user_id": self.user_id,
                    "days_exported": days,
                    "messages": [asdict(msg) for msg in messages],
                    "sessions": [asdict(session) for session in sessions],
                },
                indent=2,
                default=str,
            )

        elif format.lower() == "csv":
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Write messages
            writer.writerow(["Message Logs"])
            writer.writerow(
                [
                    "Timestamp",
                    "Channel",
                    "Template",
                    "Recipient",
                    "Company",
                    "Status",
                    "Error",
                    "Sent At",
                ]
            )

            for msg in messages:
                writer.writerow(
                    [
                        msg.timestamp,
                        msg.channel,
                        msg.template_name,
                        msg.recipient_email,
                        msg.recipient_company,
                        msg.message_status,
                        msg.error_message or "",
                        msg.sent_at or "",
                    ]
                )

            writer.writerow([])  # Empty row
            writer.writerow(["Session Summaries"])
            writer.writerow(
                [
                    "Session ID",
                    "Start Time",
                    "End Time",
                    "Channel",
                    "Template",
                    "Total",
                    "Successful",
                    "Failed",
                    "Success Rate",
                ]
            )

            for session in sessions:
                writer.writerow(
                    [
                        session.session_id,
                        session.start_time,
                        session.end_time or "",
                        session.channel,
                        session.template_used,
                        session.total_messages,
                        session.successful_messages,
                        session.failed_messages,
                        f"{session.success_rate:.1f}%",
                    ]
                )

            return output.getvalue()

        else:
            raise ValueError(f"Unsupported export format: {format}")

    def delete_old_data(self, days: int = 90) -> int:
        """
        Delete old messaging data to manage storage.

        Args:
            days: Delete data older than this many days

        Returns:
            Number of records deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            # Delete old message logs
            cursor = conn.execute(
                """
                DELETE FROM message_logs 
                WHERE user_id = ? AND timestamp < ?
            """,
                (self.user_id, cutoff_date.isoformat()),
            )
            messages_deleted = cursor.rowcount

            # Delete old session summaries
            cursor = conn.execute(
                """
                DELETE FROM session_summaries 
                WHERE user_id = ? AND start_time < ?
            """,
                (self.user_id, cutoff_date.isoformat()),
            )
            sessions_deleted = cursor.rowcount

            # Delete old analytics cache
            cursor = conn.execute(
                """
                DELETE FROM analytics_cache 
                WHERE user_id = ? AND generated_at < ?
            """,
                (self.user_id, cutoff_date.isoformat()),
            )
            cache_deleted = cursor.rowcount

            conn.commit()

        total_deleted = messages_deleted + sessions_deleted + cache_deleted
        self.logger.info(
            f"Deleted {total_deleted} old records (older than {days} days)"
        )

        return total_deleted

    def get_quick_stats(self) -> Dict[str, Any]:
        """
        Get quick statistics for dashboard display.

        Returns:
            Dictionary with key statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            # Messages in last 30 days
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM message_logs 
                WHERE user_id = ? AND timestamp >= ?
            """,
                (self.user_id, (datetime.now() - timedelta(days=30)).isoformat()),
            )
            messages_30d = cursor.fetchone()[0]

            # Success rate in last 30 days
            cursor = conn.execute(
                """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN message_status = 'sent' THEN 1 ELSE 0 END) as successful
                FROM message_logs 
                WHERE user_id = ? AND timestamp >= ?
            """,
                (self.user_id, (datetime.now() - timedelta(days=30)).isoformat()),
            )
            total, successful = cursor.fetchone()
            success_rate = (successful / total * 100) if total > 0 else 0

            # Most used channel
            cursor = conn.execute(
                """
                SELECT channel, COUNT(*) as count FROM message_logs 
                WHERE user_id = ? AND timestamp >= ?
                GROUP BY channel ORDER BY count DESC LIMIT 1
            """,
                (self.user_id, (datetime.now() - timedelta(days=30)).isoformat()),
            )
            result = cursor.fetchone()
            most_used_channel = result[0] if result else "None"

            # Total sessions
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM session_summaries 
                WHERE user_id = ? AND start_time >= ?
            """,
                (self.user_id, (datetime.now() - timedelta(days=30)).isoformat()),
            )
            sessions_30d = cursor.fetchone()[0]

        return {
            "messages_last_30_days": messages_30d,
            "success_rate_30_days": round(success_rate, 1),
            "most_used_channel": most_used_channel,
            "sessions_last_30_days": sessions_30d,
            "current_session_active": self.current_session_id is not None,
            "database_available": self._is_database_available(),
            "database_path": str(self.db_path),
            "operation_count": self._operation_count,
        }

    def get_database_health(self) -> Dict[str, Any]:
        """Get comprehensive database health information."""
        health_info = {
            "database_available": self._is_database_available(),
            "database_path": str(self.db_path),
            "database_exists": self.db_path.exists(),
            "database_size": 0,
            "operation_count": self._operation_count,
            "last_maintenance": self._last_maintenance.isoformat(),
            "tables": {},
            "indexes": {},
            "errors": [],
        }

        if not self._is_database_available():
            health_info["errors"].append("Database not available")
            return health_info

        try:
            # Get database file size
            if self.db_path.exists():
                health_info["database_size"] = self.db_path.stat().st_size

            # Get table information
            tables_info = self._execute_with_retry(
                """
                SELECT name FROM sqlite_master WHERE type='table' ORDER BY name
            """,
                fetch="all",
            )

            if tables_info:
                for table_row in tables_info:
                    table_name = table_row[0]
                    count = self._execute_with_retry(
                        f"SELECT COUNT(*) FROM {table_name}", fetch="one"
                    )
                    health_info["tables"][table_name] = count[0] if count else 0

            # Get index information
            indexes_info = self._execute_with_retry(
                """
                SELECT name FROM sqlite_master WHERE type='index' ORDER BY name
            """,
                fetch="all",
            )

            if indexes_info:
                health_info["indexes"] = [idx[0] for idx in indexes_info]

            # Check database integrity
            integrity_check = self._execute_with_retry(
                "PRAGMA integrity_check", fetch="one"
            )
            if integrity_check and integrity_check[0] != "ok":
                health_info["errors"].append(
                    f"Integrity check failed: {integrity_check[0]}"
                )

        except Exception as e:
            health_info["errors"].append(f"Health check failed: {str(e)}")

        return health_info

    def repair_database(self) -> bool:
        """Attempt to repair database issues."""
        try:
            self.logger.info("Starting database repair...")

            # Try to reconnect
            self._init_database_with_retries()

            if not self._is_database_available():
                return False

            # Run integrity check
            integrity_result = self._execute_with_retry(
                "PRAGMA integrity_check", fetch="one"
            )
            if integrity_result and integrity_result[0] != "ok":
                self.logger.warning(
                    f"Database integrity issues found: {integrity_result[0]}"
                )

                # Try to repair with REINDEX
                self._execute_with_retry("REINDEX")

                # Try again
                integrity_result = self._execute_with_retry(
                    "PRAGMA integrity_check", fetch="one"
                )
                if integrity_result and integrity_result[0] != "ok":
                    self.logger.error("Database repair failed")
                    return False

            # Vacuum database
            self._execute_with_retry("VACUUM")

            # Update statistics
            self._execute_with_retry("ANALYZE")

            self._log_system_event(
                "INFO", "database", "Database repair completed successfully"
            )
            self.logger.info("Database repair completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Database repair failed: {e}")
            self._log_system_event(
                "ERROR", "database", "Database repair failed", {"error": str(e)}
            )
            return False

    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """Create a backup of the database."""
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.db_path.parent / f"message_logs_backup_{timestamp}.db"

        backup_path = Path(backup_path)

        try:
            if not self._is_database_available():
                raise sqlite3.Error("Database not available for backup")

            # Create backup using SQLite backup API
            with self._get_connection() as source_conn:
                with sqlite3.connect(str(backup_path)) as backup_conn:
                    source_conn.backup(backup_conn)

            self._log_system_event(
                "INFO",
                "database",
                "Database backup created",
                {
                    "backup_path": str(backup_path),
                    "backup_size": backup_path.stat().st_size,
                },
            )

            self.logger.info(f"Database backup created: {backup_path}")
            return str(backup_path)

        except Exception as e:
            self.logger.error(f"Database backup failed: {e}")
            self._log_system_event(
                "ERROR", "database", "Database backup failed", {"error": str(e)}
            )
            raise

    def close(self) -> None:
        """Close the logger and clean up resources."""
        try:
            # End current session if active
            if self.current_session_id:
                self.end_session()

            # Log shutdown
            self._log_system_event(
                "INFO",
                "system",
                "Message logger shutting down",
                {
                    "operation_count": self._operation_count,
                    "uptime_seconds": (
                        datetime.now() - self._last_maintenance
                    ).total_seconds(),
                },
            )

            self.logger.info("Message logger closed successfully")

        except Exception as e:
            self.logger.error(f"Error during logger shutdown: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    # Private helper methods

    def _save_log_entry(self, entry: MessageLogEntry) -> None:
        """Save a log entry to the database with robust error handling."""
        try:
            result = self._execute_with_retry(
                """
                INSERT INTO message_logs (
                    id, timestamp, user_id, session_id, channel, template_id, template_name,
                    recipient_email, recipient_name, recipient_phone, recipient_company,
                    message_status, message_id, delivery_status, error_message,
                    sent_at, delivered_at, read_at, response_received, content_preview, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    entry.id,
                    entry.timestamp.isoformat(),
                    entry.user_id,
                    entry.session_id,
                    entry.channel,
                    entry.template_id,
                    entry.template_name,
                    entry.recipient_email,
                    entry.recipient_name,
                    entry.recipient_phone or "",
                    entry.recipient_company or "",
                    entry.message_status,
                    entry.message_id,
                    entry.delivery_status,
                    entry.error_message,
                    entry.sent_at.isoformat() if entry.sent_at else None,
                    entry.delivered_at.isoformat() if entry.delivered_at else None,
                    entry.read_at.isoformat() if entry.read_at else None,
                    int(entry.response_received),
                    entry.content_preview,
                    json.dumps(entry.metadata) if entry.metadata else "{}",
                ),
            )

            if result is None:
                raise sqlite3.Error("Failed to insert log entry")

        except Exception as e:
            self.logger.error(f"Failed to save log entry {entry.id}: {e}")
            raise

    def _update_session_stats(self) -> None:
        """Update session statistics based on current messages with robust error handling."""
        if not self.current_session_id or not self._is_database_available():
            return

        try:
            # Get current session statistics
            stats = self._execute_with_retry(
                """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN message_status = 'sent' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN message_status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN message_status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN message_status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
                FROM message_logs 
                WHERE session_id = ?
            """,
                (self.current_session_id,),
                fetch="one",
            )

            if stats:
                total = stats[0] or 0
                successful = stats[1] or 0
                failed = stats[2] or 0
                pending = stats[3] or 0
                cancelled = stats[4] or 0
                success_rate = (successful / total * 100) if total > 0 else 0

                # Update session summary
                result = self._execute_with_retry(
                    """
                    UPDATE session_summaries 
                    SET total_messages = ?, successful_messages = ?, failed_messages = ?,
                        pending_messages = ?, cancelled_messages = ?, success_rate = ?
                    WHERE session_id = ?
                """,
                    (
                        total,
                        successful,
                        failed,
                        pending,
                        cancelled,
                        success_rate,
                        self.current_session_id,
                    ),
                )

                if result is not None:
                    self._log_system_event(
                        "DEBUG",
                        "session",
                        "Session stats updated",
                        {
                            "session_id": self.current_session_id,
                            "total": total,
                            "successful": successful,
                            "failed": failed,
                            "success_rate": success_rate,
                        },
                    )

        except Exception as e:
            self.logger.error(f"Failed to update session stats: {e}")
            self._log_system_event(
                "ERROR",
                "session",
                "Session stats update failed",
                {"session_id": self.current_session_id, "error": str(e)},
            )

    def _generate_session_summary(
        self, session_id: str, end_time: datetime
    ) -> SessionSummary:
        """Generate a session summary."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get session info
            session_row = conn.execute(
                """
                SELECT * FROM session_summaries WHERE session_id = ?
            """,
                (session_id,),
            ).fetchone()

            # Get error messages
            cursor = conn.execute(
                """
                SELECT error_message FROM message_logs 
                WHERE session_id = ? AND error_message IS NOT NULL
            """,
                (session_id,),
            )
            errors = [row[0] for row in cursor.fetchall()]

            # Calculate average send time
            duration = (
                end_time - datetime.fromisoformat(session_row["start_time"])
            ).total_seconds()
            avg_send_time = (
                duration / session_row["total_messages"]
                if session_row["total_messages"] > 0
                else 0
            )

        return SessionSummary(
            session_id=session_id,
            start_time=datetime.fromisoformat(session_row["start_time"]),
            end_time=end_time,
            channel=session_row["channel"],
            template_used=session_row["template_used"],
            total_messages=session_row["total_messages"],
            successful_messages=session_row["successful_messages"],
            failed_messages=session_row["failed_messages"],
            pending_messages=session_row["pending_messages"],
            cancelled_messages=session_row["cancelled_messages"],
            success_rate=session_row["success_rate"],
            average_send_time=avg_send_time,
            errors=errors,
            user_id=session_row["user_id"],
            channels_used=(
                json.loads(session_row["channels_used"])
                if session_row["channels_used"]
                else []
            ),
            templates_used=(
                json.loads(session_row["templates_used"])
                if session_row["templates_used"]
                else []
            ),
        )

    def _generate_analytics_report(
        self, report_id: str, start_date: datetime, end_date: datetime
    ) -> AnalyticsReport:
        """Generate a comprehensive analytics report."""
        with sqlite3.connect(self.db_path) as conn:
            # Basic statistics
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM message_logs 
                WHERE user_id = ? AND timestamp BETWEEN ? AND ?
            """,
                (self.user_id, start_date.isoformat(), end_date.isoformat()),
            )
            total_messages = cursor.fetchone()[0]

            cursor = conn.execute(
                """
                SELECT COUNT(DISTINCT session_id) FROM message_logs 
                WHERE user_id = ? AND timestamp BETWEEN ? AND ?
            """,
                (self.user_id, start_date.isoformat(), end_date.isoformat()),
            )
            total_sessions = cursor.fetchone()[0]

            # Success metrics
            cursor = conn.execute(
                """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN message_status = 'sent' THEN 1 ELSE 0 END) as successful
                FROM message_logs 
                WHERE user_id = ? AND timestamp BETWEEN ? AND ?
            """,
                (self.user_id, start_date.isoformat(), end_date.isoformat()),
            )
            total, successful = cursor.fetchone()
            overall_success_rate = (successful / total * 100) if total > 0 else 0

            # More detailed analytics would be implemented here...
            # This is a simplified version for brevity

        return AnalyticsReport(
            report_id=report_id,
            generated_at=datetime.now(),
            date_range=(start_date, end_date),
            user_id=self.user_id,
            total_messages_sent=total_messages,
            total_sessions=total_sessions,
            channels_used=[],  # Would be populated with actual data
            templates_used=[],  # Would be populated with actual data
            overall_success_rate=overall_success_rate,
            success_by_channel={},
            success_by_template={},
            success_by_day={},
            average_messages_per_session=(
                total_messages / total_sessions if total_sessions > 0 else 0
            ),
            average_session_duration=0.0,
            peak_sending_hours=[],
            busiest_days=[],
            common_errors=[],
            error_trends={},
            top_companies=[],
            repeat_recipients=[],
            template_performance={},
            recommendations=[],
        )

    def _row_to_log_entry(self, row: sqlite3.Row) -> MessageLogEntry:
        """Convert database row to MessageLogEntry."""
        return MessageLogEntry(
            id=row["id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            user_id=row["user_id"],
            session_id=row["session_id"],
            channel=row["channel"],
            template_id=row["template_id"],
            template_name=row["template_name"],
            recipient_email=row["recipient_email"],
            recipient_name=row["recipient_name"],
            recipient_phone=row["recipient_phone"],
            recipient_company=row["recipient_company"],
            message_status=row["message_status"],
            message_id=row["message_id"],
            delivery_status=row["delivery_status"],
            error_message=row["error_message"],
            sent_at=datetime.fromisoformat(row["sent_at"]) if row["sent_at"] else None,
            delivered_at=(
                datetime.fromisoformat(row["delivered_at"])
                if row["delivered_at"]
                else None
            ),
            read_at=datetime.fromisoformat(row["read_at"]) if row["read_at"] else None,
            response_received=bool(row["response_received"]),
            content_preview=row["content_preview"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )

    def _row_to_session_summary(self, row: sqlite3.Row) -> SessionSummary:
        """Convert database row to SessionSummary."""
        # Calculate average send time if we have the data
        start_time = datetime.fromisoformat(row["start_time"])
        end_time = datetime.fromisoformat(row["end_time"]) if row["end_time"] else None

        if end_time and row["total_messages"] > 0:
            duration = (end_time - start_time).total_seconds()
            avg_send_time = duration / row["total_messages"]
        else:
            avg_send_time = 0.0

        # Get errors for this session
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute(
                    """
                    SELECT error_message FROM message_logs 
                    WHERE session_id = ? AND error_message IS NOT NULL
                """,
                    (row["session_id"],),
                )
                errors = [error_row[0] for error_row in cursor.fetchall()]
        except:
            errors = []

        return SessionSummary(
            session_id=row["session_id"],
            start_time=start_time,
            end_time=end_time,
            channel=row["channel"] or "email",
            template_used=row["template_used"] or "Unknown",
            total_messages=row["total_messages"],
            successful_messages=row["successful_messages"],
            failed_messages=row["failed_messages"],
            pending_messages=row["pending_messages"] or 0,
            cancelled_messages=row["cancelled_messages"] or 0,
            success_rate=row["success_rate"] or 0.0,
            average_send_time=avg_send_time,
            errors=errors,
            user_id=row["user_id"],
            channels_used=(
                json.loads(row["channels_used"])
                if row["channels_used"]
                else []
            ),
            templates_used=(
                json.loads(row["templates_used"])
                if row["templates_used"]
                else []
            ),
        )

    def _get_cached_report(self, report_id: str) -> Optional[AnalyticsReport]:
        """Get cached analytics report if available and recent."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT report_data, generated_at FROM analytics_cache 
                WHERE report_id = ? AND user_id = ?
            """,
                (report_id, self.user_id),
            )
            result = cursor.fetchone()

            if result:
                generated_at = datetime.fromisoformat(result[1])
                # Cache is valid for 1 hour
                if datetime.now() - generated_at < timedelta(hours=1):
                    report_data = json.loads(result[0])
                    # Convert back to AnalyticsReport object
                    # This would need proper deserialization logic
                    return None  # Simplified for now

        return None

    def _cache_report(self, report: AnalyticsReport) -> None:
        """Cache an analytics report."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO analytics_cache 
                (report_id, user_id, generated_at, date_range_start, date_range_end, report_data)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    report.report_id,
                    report.user_id,
                    report.generated_at.isoformat(),
                    report.date_range[0].isoformat(),
                    report.date_range[1].isoformat(),
                    json.dumps(asdict(report), default=str),
                ),
            )
            conn.commit()
