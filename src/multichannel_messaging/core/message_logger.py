"""
Message logging and analytics system for tracking user messaging activity.
Provides comprehensive logging, analytics, and user control over sent messages.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from .models import Customer, MessageTemplate, MessageRecord, MessageStatus, MessageChannel
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
        
        # Set up database
        if db_path is None:
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            db_path = logs_dir / "message_logs.db"
        
        self.db_path = Path(db_path)
        self._init_database()
        
        # Current session tracking
        self.current_session_id: Optional[str] = None
        self.session_start_time: Optional[datetime] = None
        
    def _init_database(self) -> None:
        """Initialize the SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
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
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_summaries (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    channel TEXT NOT NULL,
                    template_used TEXT NOT NULL,
                    total_messages INTEGER NOT NULL,
                    successful_messages INTEGER DEFAULT 0,
                    failed_messages INTEGER DEFAULT 0,
                    pending_messages INTEGER DEFAULT 0,
                    cancelled_messages INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0,
                    average_send_time REAL DEFAULT 0.0,
                    errors TEXT,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analytics_cache (
                    report_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    date_range_start TEXT NOT NULL,
                    date_range_end TEXT NOT NULL,
                    report_data TEXT NOT NULL
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_message_logs_user_timestamp ON message_logs(user_id, timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_message_logs_session ON message_logs(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_message_logs_status ON message_logs(message_status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session_summaries_user ON session_summaries(user_id)")
            
            conn.commit()
    
    def start_session(self, channel: str, template: MessageTemplate) -> str:
        """
        Start a new messaging session.
        
        Args:
            channel: Channel being used (email, whatsapp)
            template: Template being used
            
        Returns:
            Session ID
        """
        session_id = f"{self.user_id}_{channel}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_session_id = session_id
        self.session_start_time = datetime.now()
        
        # Create session record
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO session_summaries 
                (session_id, user_id, start_time, channel, template_used, total_messages, errors, metadata)
                VALUES (?, ?, ?, ?, ?, 0, '[]', '{}')
            """, (session_id, self.user_id, self.session_start_time.isoformat(), 
                  channel, template.name))
            conn.commit()
        
        self.logger.info(f"Started messaging session {session_id} for channel {channel}")
        return session_id
    
    def log_message(self, message_record: MessageRecord, content_preview: str = "") -> str:
        """
        Log a message attempt.
        
        Args:
            message_record: Message record to log
            content_preview: Preview of message content
            
        Returns:
            Log entry ID
        """
        if not self.current_session_id:
            raise ValidationError("No active session. Call start_session() first.")
        
        log_id = f"{self.current_session_id}_{datetime.now().strftime('%H%M%S_%f')}"
        
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
            recipient_phone=message_record.customer.phone,
            recipient_company=message_record.customer.company,
            message_status=message_record.status.value,
            message_id=message_record.message_id,
            delivery_status=message_record.delivery_status,
            error_message=message_record.error_message,
            sent_at=message_record.sent_at,
            content_preview=content_preview[:100] if content_preview else "",
            metadata={}
        )
        
        self._save_log_entry(log_entry)
        self._update_session_stats()
        
        return log_id
    
    def update_message_status(self, log_id: str, status: MessageStatus, 
                            message_id: Optional[str] = None,
                            delivery_status: Optional[str] = None,
                            error_message: Optional[str] = None) -> None:
        """
        Update the status of a logged message.
        
        Args:
            log_id: Log entry ID
            status: New message status
            message_id: External message ID
            delivery_status: Delivery status
            error_message: Error message if failed
        """
        with sqlite3.connect(self.db_path) as conn:
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
            
            if status == MessageStatus.SENT:
                update_fields.append("sent_at = ?")
                params.append(datetime.now().isoformat())
            
            params.append(log_id)
            
            conn.execute(f"""
                UPDATE message_logs 
                SET {', '.join(update_fields)}
                WHERE id = ?
            """, params)
            conn.commit()
        
        self._update_session_stats()
    
    def end_session(self) -> Optional[SessionSummary]:
        """
        End the current messaging session and generate summary.
        
        Returns:
            Session summary if session was active
        """
        if not self.current_session_id:
            return None
        
        end_time = datetime.now()
        session_summary = self._generate_session_summary(self.current_session_id, end_time)
        
        # Update session record
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE session_summaries 
                SET end_time = ?, total_messages = ?, successful_messages = ?,
                    failed_messages = ?, pending_messages = ?, cancelled_messages = ?,
                    success_rate = ?, average_send_time = ?, errors = ?
                WHERE session_id = ?
            """, (
                end_time.isoformat(),
                session_summary.total_messages,
                session_summary.successful_messages,
                session_summary.failed_messages,
                session_summary.pending_messages,
                session_summary.cancelled_messages,
                session_summary.success_rate,
                session_summary.average_send_time,
                json.dumps(session_summary.errors),
                self.current_session_id
            ))
            conn.commit()
        
        self.logger.info(f"Ended session {self.current_session_id}. "
                        f"Sent {session_summary.successful_messages}/{session_summary.total_messages} messages")
        
        self.current_session_id = None
        self.session_start_time = None
        
        return session_summary
    
    def get_message_history(self, days: int = 30, channel: Optional[str] = None,
                          status: Optional[MessageStatus] = None) -> List[MessageLogEntry]:
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
            cursor = conn.execute("""
                SELECT * FROM session_summaries 
                WHERE user_id = ? AND start_time >= ?
                ORDER BY start_time DESC
            """, (self.user_id, start_date.isoformat()))
            rows = cursor.fetchall()
        
        return [self._row_to_session_summary(row) for row in rows]
    
    def generate_analytics_report(self, days: int = 30, 
                                force_refresh: bool = False) -> AnalyticsReport:
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
            return json.dumps({
                "export_date": datetime.now().isoformat(),
                "user_id": self.user_id,
                "days_exported": days,
                "messages": [asdict(msg) for msg in messages],
                "sessions": [asdict(session) for session in sessions]
            }, indent=2, default=str)
        
        elif format.lower() == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write messages
            writer.writerow(["Message Logs"])
            writer.writerow([
                "Timestamp", "Channel", "Template", "Recipient", "Company", 
                "Status", "Error", "Sent At"
            ])
            
            for msg in messages:
                writer.writerow([
                    msg.timestamp, msg.channel, msg.template_name,
                    msg.recipient_email, msg.recipient_company,
                    msg.message_status, msg.error_message or "", msg.sent_at or ""
                ])
            
            writer.writerow([])  # Empty row
            writer.writerow(["Session Summaries"])
            writer.writerow([
                "Session ID", "Start Time", "End Time", "Channel", "Template",
                "Total", "Successful", "Failed", "Success Rate"
            ])
            
            for session in sessions:
                writer.writerow([
                    session.session_id, session.start_time, session.end_time or "",
                    session.channel, session.template_used, session.total_messages,
                    session.successful_messages, session.failed_messages,
                    f"{session.success_rate:.1f}%"
                ])
            
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
            cursor = conn.execute("""
                DELETE FROM message_logs 
                WHERE user_id = ? AND timestamp < ?
            """, (self.user_id, cutoff_date.isoformat()))
            messages_deleted = cursor.rowcount
            
            # Delete old session summaries
            cursor = conn.execute("""
                DELETE FROM session_summaries 
                WHERE user_id = ? AND start_time < ?
            """, (self.user_id, cutoff_date.isoformat()))
            sessions_deleted = cursor.rowcount
            
            # Delete old analytics cache
            cursor = conn.execute("""
                DELETE FROM analytics_cache 
                WHERE user_id = ? AND generated_at < ?
            """, (self.user_id, cutoff_date.isoformat()))
            cache_deleted = cursor.rowcount
            
            conn.commit()
        
        total_deleted = messages_deleted + sessions_deleted + cache_deleted
        self.logger.info(f"Deleted {total_deleted} old records (older than {days} days)")
        
        return total_deleted
    
    def get_quick_stats(self) -> Dict[str, Any]:
        """
        Get quick statistics for dashboard display.
        
        Returns:
            Dictionary with key statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            # Messages in last 30 days
            cursor = conn.execute("""
                SELECT COUNT(*) FROM message_logs 
                WHERE user_id = ? AND timestamp >= ?
            """, (self.user_id, (datetime.now() - timedelta(days=30)).isoformat()))
            messages_30d = cursor.fetchone()[0]
            
            # Success rate in last 30 days
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN message_status = 'sent' THEN 1 ELSE 0 END) as successful
                FROM message_logs 
                WHERE user_id = ? AND timestamp >= ?
            """, (self.user_id, (datetime.now() - timedelta(days=30)).isoformat()))
            total, successful = cursor.fetchone()
            success_rate = (successful / total * 100) if total > 0 else 0
            
            # Most used channel
            cursor = conn.execute("""
                SELECT channel, COUNT(*) as count FROM message_logs 
                WHERE user_id = ? AND timestamp >= ?
                GROUP BY channel ORDER BY count DESC LIMIT 1
            """, (self.user_id, (datetime.now() - timedelta(days=30)).isoformat()))
            result = cursor.fetchone()
            most_used_channel = result[0] if result else "None"
            
            # Total sessions
            cursor = conn.execute("""
                SELECT COUNT(*) FROM session_summaries 
                WHERE user_id = ? AND start_time >= ?
            """, (self.user_id, (datetime.now() - timedelta(days=30)).isoformat()))
            sessions_30d = cursor.fetchone()[0]
        
        return {
            "messages_last_30_days": messages_30d,
            "success_rate_30_days": round(success_rate, 1),
            "most_used_channel": most_used_channel,
            "sessions_last_30_days": sessions_30d,
            "current_session_active": self.current_session_id is not None
        }
    
    # Private helper methods
    
    def _save_log_entry(self, entry: MessageLogEntry) -> None:
        """Save a log entry to the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO message_logs VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                entry.id, entry.timestamp.isoformat(), entry.user_id, entry.session_id,
                entry.channel, entry.template_id, entry.template_name,
                entry.recipient_email, entry.recipient_name, entry.recipient_phone,
                entry.recipient_company, entry.message_status, entry.message_id,
                entry.delivery_status, entry.error_message,
                entry.sent_at.isoformat() if entry.sent_at else None,
                entry.delivered_at.isoformat() if entry.delivered_at else None,
                entry.read_at.isoformat() if entry.read_at else None,
                int(entry.response_received), entry.content_preview,
                json.dumps(entry.metadata)
            ))
            conn.commit()
    
    def _update_session_stats(self) -> None:
        """Update session statistics based on current messages."""
        if not self.current_session_id:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN message_status = 'sent' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN message_status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN message_status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN message_status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
                FROM message_logs 
                WHERE session_id = ?
            """, (self.current_session_id,))
            
            total, successful, failed, pending, cancelled = cursor.fetchone()
            success_rate = (successful / total * 100) if total > 0 else 0
            
            conn.execute("""
                UPDATE session_summaries 
                SET total_messages = ?, successful_messages = ?, failed_messages = ?,
                    pending_messages = ?, cancelled_messages = ?, success_rate = ?
                WHERE session_id = ?
            """, (total, successful or 0, failed or 0, pending or 0, 
                  cancelled or 0, success_rate, self.current_session_id))
            conn.commit()
    
    def _generate_session_summary(self, session_id: str, end_time: datetime) -> SessionSummary:
        """Generate a session summary."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get session info
            session_row = conn.execute("""
                SELECT * FROM session_summaries WHERE session_id = ?
            """, (session_id,)).fetchone()
            
            # Get error messages
            cursor = conn.execute("""
                SELECT error_message FROM message_logs 
                WHERE session_id = ? AND error_message IS NOT NULL
            """, (session_id,))
            errors = [row[0] for row in cursor.fetchall()]
            
            # Calculate average send time
            duration = (end_time - datetime.fromisoformat(session_row['start_time'])).total_seconds()
            avg_send_time = duration / session_row['total_messages'] if session_row['total_messages'] > 0 else 0
        
        return SessionSummary(
            session_id=session_id,
            start_time=datetime.fromisoformat(session_row['start_time']),
            end_time=end_time,
            channel=session_row['channel'],
            template_used=session_row['template_used'],
            total_messages=session_row['total_messages'],
            successful_messages=session_row['successful_messages'],
            failed_messages=session_row['failed_messages'],
            pending_messages=session_row['pending_messages'],
            cancelled_messages=session_row['cancelled_messages'],
            success_rate=session_row['success_rate'],
            average_send_time=avg_send_time,
            errors=errors,
            user_id=session_row['user_id']
        )
    
    def _generate_analytics_report(self, report_id: str, start_date: datetime, 
                                 end_date: datetime) -> AnalyticsReport:
        """Generate a comprehensive analytics report."""
        with sqlite3.connect(self.db_path) as conn:
            # Basic statistics
            cursor = conn.execute("""
                SELECT COUNT(*) FROM message_logs 
                WHERE user_id = ? AND timestamp BETWEEN ? AND ?
            """, (self.user_id, start_date.isoformat(), end_date.isoformat()))
            total_messages = cursor.fetchone()[0]
            
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT session_id) FROM message_logs 
                WHERE user_id = ? AND timestamp BETWEEN ? AND ?
            """, (self.user_id, start_date.isoformat(), end_date.isoformat()))
            total_sessions = cursor.fetchone()[0]
            
            # Success metrics
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN message_status = 'sent' THEN 1 ELSE 0 END) as successful
                FROM message_logs 
                WHERE user_id = ? AND timestamp BETWEEN ? AND ?
            """, (self.user_id, start_date.isoformat(), end_date.isoformat()))
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
            average_messages_per_session=total_messages / total_sessions if total_sessions > 0 else 0,
            average_session_duration=0.0,
            peak_sending_hours=[],
            busiest_days=[],
            common_errors=[],
            error_trends={},
            top_companies=[],
            repeat_recipients=[],
            template_performance={},
            recommendations=[]
        )
    
    def _row_to_log_entry(self, row: sqlite3.Row) -> MessageLogEntry:
        """Convert database row to MessageLogEntry."""
        return MessageLogEntry(
            id=row['id'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            user_id=row['user_id'],
            session_id=row['session_id'],
            channel=row['channel'],
            template_id=row['template_id'],
            template_name=row['template_name'],
            recipient_email=row['recipient_email'],
            recipient_name=row['recipient_name'],
            recipient_phone=row['recipient_phone'],
            recipient_company=row['recipient_company'],
            message_status=row['message_status'],
            message_id=row['message_id'],
            delivery_status=row['delivery_status'],
            error_message=row['error_message'],
            sent_at=datetime.fromisoformat(row['sent_at']) if row['sent_at'] else None,
            delivered_at=datetime.fromisoformat(row['delivered_at']) if row['delivered_at'] else None,
            read_at=datetime.fromisoformat(row['read_at']) if row['read_at'] else None,
            response_received=bool(row['response_received']),
            content_preview=row['content_preview'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {}
        )
    
    def _row_to_session_summary(self, row: sqlite3.Row) -> SessionSummary:
        """Convert database row to SessionSummary."""
        return SessionSummary(
            session_id=row['session_id'],
            start_time=datetime.fromisoformat(row['start_time']),
            end_time=datetime.fromisoformat(row['end_time']) if row['end_time'] else None,
            channel=row['channel'],
            template_used=row['template_used'],
            total_messages=row['total_messages'],
            successful_messages=row['successful_messages'],
            failed_messages=row['failed_messages'],
            pending_messages=row['pending_messages'],
            cancelled_messages=row['cancelled_messages'],
            success_rate=row['success_rate'],
            average_send_time=row['average_send_time'],
            errors=json.loads(row['errors']) if row['errors'] else [],
            user_id=row['user_id']
        )
    
    def _get_cached_report(self, report_id: str) -> Optional[AnalyticsReport]:
        """Get cached analytics report if available and recent."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT report_data, generated_at FROM analytics_cache 
                WHERE report_id = ? AND user_id = ?
            """, (report_id, self.user_id))
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
            conn.execute("""
                INSERT OR REPLACE INTO analytics_cache 
                (report_id, user_id, generated_at, date_range_start, date_range_end, report_data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                report.report_id, report.user_id, report.generated_at.isoformat(),
                report.date_range[0].isoformat(), report.date_range[1].isoformat(),
                json.dumps(asdict(report), default=str)
            ))
            conn.commit()