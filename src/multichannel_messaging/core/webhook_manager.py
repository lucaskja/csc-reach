"""
WhatsApp webhook and delivery tracking system.

This module provides comprehensive webhook handling and delivery status tracking including:
- Webhook endpoint for receiving delivery status updates
- Message status tracking with real-time updates
- Delivery analytics and reporting dashboard
- Failed message retry and error handling
"""

import json
import time
import threading
import hashlib
import hmac
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import sqlite3
from contextlib import contextmanager

from ..utils.logger import get_logger
from ..utils.exceptions import WhatsAppAPIError, ValidationError, ConfigurationError
from ..core.i18n_manager import get_i18n_manager

logger = get_logger(__name__)
i18n = get_i18n_manager()


class MessageStatus(Enum):
    """WhatsApp message delivery status."""
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    DELETED = "deleted"
    UNKNOWN = "unknown"


class WebhookEventType(Enum):
    """Types of webhook events."""
    MESSAGE_STATUS = "message_status"
    MESSAGE_RECEIVED = "message_received"
    TEMPLATE_STATUS = "template_status"
    ACCOUNT_UPDATE = "account_update"
    ERROR = "error"


@dataclass
class MessageDeliveryRecord:
    """Record of message delivery status and tracking."""
    message_id: str
    phone_number: str
    template_name: Optional[str] = None
    message_content: Optional[str] = None
    
    # Status tracking
    status: MessageStatus = MessageStatus.QUEUED
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    
    # Error information
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    conversation_id: Optional[str] = None
    pricing_model: Optional[str] = None
    
    def update_status(self, new_status: MessageStatus, timestamp: Optional[datetime] = None, error_info: Optional[Dict[str, str]] = None):
        """Update message status with timestamp."""
        if timestamp is None:
            timestamp = datetime.now()
        
        self.status = new_status
        self.updated_at = timestamp
        
        if new_status == MessageStatus.SENT:
            self.sent_at = timestamp
        elif new_status == MessageStatus.DELIVERED:
            self.delivered_at = timestamp
        elif new_status == MessageStatus.READ:
            self.read_at = timestamp
        elif new_status == MessageStatus.FAILED:
            self.failed_at = timestamp
            if error_info:
                self.error_code = error_info.get('code')
                self.error_message = error_info.get('message')
    
    def can_retry(self) -> bool:
        """Check if message can be retried."""
        return (
            self.status == MessageStatus.FAILED and
            self.retry_count < self.max_retries
        )
    
    def get_delivery_time(self) -> Optional[timedelta]:
        """Get time from sent to delivered."""
        if self.sent_at and self.delivered_at:
            return self.delivered_at - self.sent_at
        return None
    
    def get_read_time(self) -> Optional[timedelta]:
        """Get time from delivered to read."""
        if self.delivered_at and self.read_at:
            return self.read_at - self.delivered_at
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary."""
        return {
            "message_id": self.message_id,
            "phone_number": self.phone_number,
            "template_name": self.template_name,
            "message_content": self.message_content,
            "status": self.status.value,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "conversation_id": self.conversation_id,
            "pricing_model": self.pricing_model
        }


@dataclass
class WebhookEvent:
    """Webhook event data."""
    event_type: WebhookEventType
    timestamp: datetime
    data: Dict[str, Any]
    signature: Optional[str] = None
    verified: bool = False
    processed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "signature": self.signature,
            "verified": self.verified,
            "processed": self.processed
        }


@dataclass
class DeliveryAnalytics:
    """Delivery analytics and reporting."""
    time_period: str
    total_messages: int = 0
    sent_messages: int = 0
    delivered_messages: int = 0
    read_messages: int = 0
    failed_messages: int = 0
    
    # Rates
    delivery_rate: float = 0.0
    read_rate: float = 0.0
    failure_rate: float = 0.0
    
    # Timing
    avg_delivery_time: Optional[timedelta] = None
    avg_read_time: Optional[timedelta] = None
    
    # Error analysis
    error_breakdown: Dict[str, int] = field(default_factory=dict)
    
    def calculate_rates(self):
        """Calculate delivery and read rates."""
        if self.total_messages > 0:
            self.delivery_rate = (self.delivered_messages / self.total_messages) * 100.0
            self.read_rate = (self.read_messages / self.total_messages) * 100.0
            self.failure_rate = (self.failed_messages / self.total_messages) * 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert analytics to dictionary."""
        return {
            "time_period": self.time_period,
            "total_messages": self.total_messages,
            "sent_messages": self.sent_messages,
            "delivered_messages": self.delivered_messages,
            "read_messages": self.read_messages,
            "failed_messages": self.failed_messages,
            "delivery_rate": self.delivery_rate,
            "read_rate": self.read_rate,
            "failure_rate": self.failure_rate,
            "avg_delivery_time": self.avg_delivery_time.total_seconds() if self.avg_delivery_time else None,
            "avg_read_time": self.avg_read_time.total_seconds() if self.avg_read_time else None,
            "error_breakdown": self.error_breakdown
        }


class DeliveryTracker:
    """
    Message delivery tracking and analytics system.
    
    Features:
    - Real-time message status tracking
    - Delivery analytics and reporting
    - Failed message retry handling
    - Performance metrics and insights
    """
    
    def __init__(self, database_path: Optional[Path] = None):
        """
        Initialize delivery tracker.
        
        Args:
            database_path: Path to SQLite database for storing delivery records
        """
        self.database_path = database_path or Path("delivery_tracking.db")
        self._lock = threading.RLock()
        
        # Initialize database
        self._init_database()
        
        # In-memory cache for recent records
        self.recent_records: Dict[str, MessageDeliveryRecord] = {}
        self.cache_limit = 1000
        
        logger.info(i18n.tr("delivery_tracker_initialized"))
    
    def track_message(
        self,
        message_id: str,
        phone_number: str,
        template_name: Optional[str] = None,
        message_content: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> MessageDeliveryRecord:
        """
        Start tracking a new message.
        
        Args:
            message_id: Unique message identifier
            phone_number: Recipient phone number
            template_name: Template name if using template
            message_content: Message content
            conversation_id: Conversation identifier
            
        Returns:
            Message delivery record
        """
        with self._lock:
            record = MessageDeliveryRecord(
                message_id=message_id,
                phone_number=phone_number,
                template_name=template_name,
                message_content=message_content,
                conversation_id=conversation_id
            )
            
            # Store in database
            self._save_record(record)
            
            # Cache recent record
            self.recent_records[message_id] = record
            self._cleanup_cache()
            
            logger.debug(f"Started tracking message: {message_id}")
            return record
    
    def update_message_status(
        self,
        message_id: str,
        status: MessageStatus,
        timestamp: Optional[datetime] = None,
        error_info: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Update message delivery status.
        
        Args:
            message_id: Message identifier
            status: New status
            timestamp: Status timestamp
            error_info: Error information if status is failed
            
        Returns:
            True if updated successfully
        """
        with self._lock:
            # Get record from cache or database
            record = self.recent_records.get(message_id)
            if not record:
                record = self._load_record(message_id)
                if not record:
                    logger.warning(f"Message record not found: {message_id}")
                    return False
            
            # Update status
            record.update_status(status, timestamp, error_info)
            
            # Save to database
            self._save_record(record)
            
            # Update cache
            self.recent_records[message_id] = record
            
            logger.debug(f"Updated message {message_id} status to {status.value}")
            return True
    
    def get_message_status(self, message_id: str) -> Optional[MessageDeliveryRecord]:
        """
        Get current status of a message.
        
        Args:
            message_id: Message identifier
            
        Returns:
            Message delivery record or None if not found
        """
        with self._lock:
            # Check cache first
            if message_id in self.recent_records:
                return self.recent_records[message_id]
            
            # Load from database
            return self._load_record(message_id)
    
    def get_failed_messages(self, limit: int = 100) -> List[MessageDeliveryRecord]:
        """
        Get failed messages that can be retried.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of failed message records
        """
        with self._lock:
            query = """
                SELECT * FROM delivery_records 
                WHERE status = ? AND retry_count < max_retries
                ORDER BY failed_at DESC
                LIMIT ?
            """
            
            records = []
            with self._get_db_connection() as conn:
                cursor = conn.execute(query, (MessageStatus.FAILED.value, limit))
                for row in cursor.fetchall():
                    record = self._row_to_record(row)
                    records.append(record)
            
            return records
    
    def retry_failed_message(self, message_id: str) -> bool:
        """
        Mark a failed message for retry.
        
        Args:
            message_id: Message identifier
            
        Returns:
            True if marked for retry successfully
        """
        with self._lock:
            record = self.get_message_status(message_id)
            if not record or not record.can_retry():
                return False
            
            record.retry_count += 1
            record.status = MessageStatus.QUEUED
            record.updated_at = datetime.now()
            
            self._save_record(record)
            
            logger.info(f"Marked message {message_id} for retry (attempt {record.retry_count})")
            return True
    
    def get_delivery_analytics(self, days: int = 30) -> DeliveryAnalytics:
        """
        Get delivery analytics for specified time period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Delivery analytics
        """
        with self._lock:
            start_date = datetime.now() - timedelta(days=days)
            
            analytics = DeliveryAnalytics(time_period=f"Last {days} days")
            
            # Query message counts by status
            query = """
                SELECT status, COUNT(*) as count
                FROM delivery_records
                WHERE created_at >= ?
                GROUP BY status
            """
            
            with self._get_db_connection() as conn:
                cursor = conn.execute(query, (start_date.isoformat(),))
                for row in cursor.fetchall():
                    status, count = row
                    analytics.total_messages += count
                    
                    if status == MessageStatus.SENT.value:
                        analytics.sent_messages = count
                    elif status == MessageStatus.DELIVERED.value:
                        analytics.delivered_messages = count
                    elif status == MessageStatus.READ.value:
                        analytics.read_messages = count
                    elif status == MessageStatus.FAILED.value:
                        analytics.failed_messages = count
                
                # Get error breakdown
                error_query = """
                    SELECT error_code, COUNT(*) as count
                    FROM delivery_records
                    WHERE created_at >= ? AND status = ? AND error_code IS NOT NULL
                    GROUP BY error_code
                """
                
                cursor = conn.execute(error_query, (start_date.isoformat(), MessageStatus.FAILED.value))
                for row in cursor.fetchall():
                    error_code, count = row
                    analytics.error_breakdown[error_code] = count
                
                # Calculate timing metrics
                timing_query = """
                    SELECT 
                        AVG(JULIANDAY(delivered_at) - JULIANDAY(sent_at)) * 86400 as avg_delivery_seconds,
                        AVG(JULIANDAY(read_at) - JULIANDAY(delivered_at)) * 86400 as avg_read_seconds
                    FROM delivery_records
                    WHERE created_at >= ? AND delivered_at IS NOT NULL
                """
                
                cursor = conn.execute(timing_query, (start_date.isoformat(),))
                row = cursor.fetchone()
                if row and row[0]:
                    analytics.avg_delivery_time = timedelta(seconds=row[0])
                if row and row[1]:
                    analytics.avg_read_time = timedelta(seconds=row[1])
            
            analytics.calculate_rates()
            return analytics
    
    def cleanup_old_records(self, days: int = 90) -> int:
        """
        Clean up old delivery records.
        
        Args:
            days: Keep records newer than this many days
            
        Returns:
            Number of records deleted
        """
        with self._lock:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            query = "DELETE FROM delivery_records WHERE created_at < ?"
            
            with self._get_db_connection() as conn:
                cursor = conn.execute(query, (cutoff_date.isoformat(),))
                deleted_count = cursor.rowcount
                conn.commit()
            
            logger.info(f"Cleaned up {deleted_count} old delivery records")
            return deleted_count
    
    def _init_database(self):
        """Initialize SQLite database."""
        with self._get_db_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS delivery_records (
                    message_id TEXT PRIMARY KEY,
                    phone_number TEXT NOT NULL,
                    template_name TEXT,
                    message_content TEXT,
                    status TEXT NOT NULL,
                    sent_at TEXT,
                    delivered_at TEXT,
                    read_at TEXT,
                    failed_at TEXT,
                    error_code TEXT,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    conversation_id TEXT,
                    pricing_model TEXT
                )
            """)
            
            # Create indexes for better query performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON delivery_records(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON delivery_records(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_phone_number ON delivery_records(phone_number)")
            
            conn.commit()
    
    @contextmanager
    def _get_db_connection(self):
        """Get database connection with proper cleanup."""
        conn = sqlite3.connect(str(self.database_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _save_record(self, record: MessageDeliveryRecord):
        """Save record to database."""
        query = """
            INSERT OR REPLACE INTO delivery_records (
                message_id, phone_number, template_name, message_content,
                status, sent_at, delivered_at, read_at, failed_at,
                error_code, error_message, retry_count, max_retries,
                created_at, updated_at, conversation_id, pricing_model
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        values = (
            record.message_id,
            record.phone_number,
            record.template_name,
            record.message_content,
            record.status.value,
            record.sent_at.isoformat() if record.sent_at else None,
            record.delivered_at.isoformat() if record.delivered_at else None,
            record.read_at.isoformat() if record.read_at else None,
            record.failed_at.isoformat() if record.failed_at else None,
            record.error_code,
            record.error_message,
            record.retry_count,
            record.max_retries,
            record.created_at.isoformat(),
            record.updated_at.isoformat(),
            record.conversation_id,
            record.pricing_model
        )
        
        with self._get_db_connection() as conn:
            conn.execute(query, values)
            conn.commit()
    
    def _load_record(self, message_id: str) -> Optional[MessageDeliveryRecord]:
        """Load record from database."""
        query = "SELECT * FROM delivery_records WHERE message_id = ?"
        
        with self._get_db_connection() as conn:
            cursor = conn.execute(query, (message_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_record(row)
        
        return None
    
    def _row_to_record(self, row) -> MessageDeliveryRecord:
        """Convert database row to MessageDeliveryRecord."""
        return MessageDeliveryRecord(
            message_id=row['message_id'],
            phone_number=row['phone_number'],
            template_name=row['template_name'],
            message_content=row['message_content'],
            status=MessageStatus(row['status']),
            sent_at=datetime.fromisoformat(row['sent_at']) if row['sent_at'] else None,
            delivered_at=datetime.fromisoformat(row['delivered_at']) if row['delivered_at'] else None,
            read_at=datetime.fromisoformat(row['read_at']) if row['read_at'] else None,
            failed_at=datetime.fromisoformat(row['failed_at']) if row['failed_at'] else None,
            error_code=row['error_code'],
            error_message=row['error_message'],
            retry_count=row['retry_count'],
            max_retries=row['max_retries'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            conversation_id=row['conversation_id'],
            pricing_model=row['pricing_model']
        )
    
    def _cleanup_cache(self):
        """Clean up in-memory cache to prevent memory issues."""
        if len(self.recent_records) > self.cache_limit:
            # Remove oldest records
            sorted_records = sorted(
                self.recent_records.items(),
                key=lambda x: x[1].updated_at
            )
            
            # Keep only the most recent records
            keep_count = int(self.cache_limit * 0.8)  # Keep 80% of limit
            to_keep = dict(sorted_records[-keep_count:])
            self.recent_records = to_keep


class WebhookManager:
    """
    WhatsApp webhook management system.
    
    Features:
    - Webhook signature verification
    - Event processing and routing
    - Delivery status updates
    - Error handling and retry logic
    """
    
    def __init__(
        self,
        webhook_secret: str,
        delivery_tracker: DeliveryTracker,
        event_callback: Optional[Callable[[WebhookEvent], None]] = None
    ):
        """
        Initialize webhook manager.
        
        Args:
            webhook_secret: Secret for webhook signature verification
            delivery_tracker: Delivery tracker instance
            event_callback: Optional callback for webhook events
        """
        self.webhook_secret = webhook_secret
        self.delivery_tracker = delivery_tracker
        self.event_callback = event_callback
        
        # Event processing
        self.processed_events: Dict[str, datetime] = {}
        self.event_cache_limit = 10000
        
        logger.info(i18n.tr("webhook_manager_initialized"))
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verify webhook signature.
        
        Args:
            payload: Raw webhook payload
            signature: Signature from webhook headers
            
        Returns:
            True if signature is valid
        """
        try:
            # WhatsApp uses HMAC-SHA256 with the webhook secret
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Remove 'sha256=' prefix if present
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return False
    
    def process_webhook(self, payload: str, signature: Optional[str] = None) -> bool:
        """
        Process incoming webhook payload.
        
        Args:
            payload: JSON webhook payload
            signature: Optional signature for verification
            
        Returns:
            True if processed successfully
        """
        try:
            # Verify signature if provided
            if signature and not self.verify_webhook_signature(payload, signature):
                logger.warning("Webhook signature verification failed")
                return False
            
            # Parse payload
            data = json.loads(payload)
            
            # Process webhook data
            return self._process_webhook_data(data, signature)
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid webhook JSON payload: {e}")
            return False
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            return False
    
    def _process_webhook_data(self, data: Dict[str, Any], signature: Optional[str] = None) -> bool:
        """Process parsed webhook data."""
        try:
            # WhatsApp webhook structure
            if 'entry' not in data:
                logger.warning("Invalid webhook structure: missing 'entry'")
                return False
            
            for entry in data['entry']:
                if 'changes' not in entry:
                    continue
                
                for change in entry['changes']:
                    if change.get('field') == 'messages':
                        self._process_message_webhook(change['value'])
                    elif change.get('field') == 'message_template_status_update':
                        self._process_template_status_webhook(change['value'])
            
            return True
            
        except Exception as e:
            logger.error(f"Webhook data processing failed: {e}")
            return False
    
    def _process_message_webhook(self, value: Dict[str, Any]):
        """Process message-related webhook events."""
        # Process message status updates
        if 'statuses' in value:
            for status_update in value['statuses']:
                self._process_status_update(status_update)
        
        # Process incoming messages (for read receipts, etc.)
        if 'messages' in value:
            for message in value['messages']:
                self._process_incoming_message(message)
    
    def _process_status_update(self, status_update: Dict[str, Any]):
        """Process message status update."""
        try:
            message_id = status_update.get('id')
            status_str = status_update.get('status')
            timestamp_str = status_update.get('timestamp')
            
            if not message_id or not status_str:
                logger.warning("Invalid status update: missing id or status")
                return
            
            # Map WhatsApp status to our enum
            status_mapping = {
                'sent': MessageStatus.SENT,
                'delivered': MessageStatus.DELIVERED,
                'read': MessageStatus.READ,
                'failed': MessageStatus.FAILED
            }
            
            status = status_mapping.get(status_str, MessageStatus.UNKNOWN)
            
            # Parse timestamp
            timestamp = None
            if timestamp_str:
                try:
                    timestamp = datetime.fromtimestamp(int(timestamp_str))
                except (ValueError, TypeError):
                    timestamp = datetime.now()
            
            # Extract error information if status is failed
            error_info = None
            if status == MessageStatus.FAILED and 'errors' in status_update:
                errors = status_update['errors']
                if errors:
                    error = errors[0]  # Take first error
                    error_info = {
                        'code': str(error.get('code', 'unknown')),
                        'message': error.get('title', 'Unknown error')
                    }
            
            # Update delivery tracker
            success = self.delivery_tracker.update_message_status(
                message_id=message_id,
                status=status,
                timestamp=timestamp,
                error_info=error_info
            )
            
            if success:
                logger.debug(f"Updated message {message_id} status to {status.value}")
            
            # Create webhook event
            event = WebhookEvent(
                event_type=WebhookEventType.MESSAGE_STATUS,
                timestamp=timestamp or datetime.now(),
                data=status_update,
                verified=True,
                processed=True
            )
            
            # Trigger callback
            if self.event_callback:
                self.event_callback(event)
            
        except Exception as e:
            logger.error(f"Status update processing failed: {e}")
    
    def _process_incoming_message(self, message: Dict[str, Any]):
        """Process incoming message (for analytics, etc.)."""
        try:
            # This could be used for tracking responses, read receipts, etc.
            message_id = message.get('id')
            from_number = message.get('from')
            timestamp_str = message.get('timestamp')
            
            logger.debug(f"Received message {message_id} from {from_number}")
            
            # Create webhook event
            event = WebhookEvent(
                event_type=WebhookEventType.MESSAGE_RECEIVED,
                timestamp=datetime.fromtimestamp(int(timestamp_str)) if timestamp_str else datetime.now(),
                data=message,
                verified=True,
                processed=True
            )
            
            # Trigger callback
            if self.event_callback:
                self.event_callback(event)
            
        except Exception as e:
            logger.error(f"Incoming message processing failed: {e}")
    
    def _process_template_status_webhook(self, value: Dict[str, Any]):
        """Process template status update webhook."""
        try:
            # This would handle template approval/rejection notifications
            template_name = value.get('message_template_name')
            status = value.get('event')
            
            logger.info(f"Template {template_name} status update: {status}")
            
            # Create webhook event
            event = WebhookEvent(
                event_type=WebhookEventType.TEMPLATE_STATUS,
                timestamp=datetime.now(),
                data=value,
                verified=True,
                processed=True
            )
            
            # Trigger callback
            if self.event_callback:
                self.event_callback(event)
            
        except Exception as e:
            logger.error(f"Template status webhook processing failed: {e}")


# Integration class that combines delivery tracking and webhook management
class WhatsAppDeliverySystem:
    """
    Complete WhatsApp delivery tracking and webhook system.
    
    Combines delivery tracking, webhook management, and analytics
    into a unified system for comprehensive message monitoring.
    """
    
    def __init__(
        self,
        webhook_secret: str,
        database_path: Optional[Path] = None,
        event_callback: Optional[Callable[[WebhookEvent], None]] = None
    ):
        """
        Initialize complete delivery system.
        
        Args:
            webhook_secret: Webhook verification secret
            database_path: Database path for delivery records
            event_callback: Callback for webhook events
        """
        self.delivery_tracker = DeliveryTracker(database_path)
        self.webhook_manager = WebhookManager(
            webhook_secret=webhook_secret,
            delivery_tracker=self.delivery_tracker,
            event_callback=event_callback
        )
        
        logger.info(i18n.tr("whatsapp_delivery_system_initialized"))
    
    def track_message(self, message_id: str, phone_number: str, **kwargs) -> MessageDeliveryRecord:
        """Track a new message."""
        return self.delivery_tracker.track_message(message_id, phone_number, **kwargs)
    
    def process_webhook(self, payload: str, signature: Optional[str] = None) -> bool:
        """Process webhook payload."""
        return self.webhook_manager.process_webhook(payload, signature)
    
    def get_analytics(self, days: int = 30) -> DeliveryAnalytics:
        """Get delivery analytics."""
        return self.delivery_tracker.get_delivery_analytics(days)
    
    def get_failed_messages(self, limit: int = 100) -> List[MessageDeliveryRecord]:
        """Get failed messages for retry."""
        return self.delivery_tracker.get_failed_messages(limit)
    
    def retry_failed_message(self, message_id: str) -> bool:
        """Retry a failed message."""
        return self.delivery_tracker.retry_failed_message(message_id)
    
    def cleanup_old_records(self, days: int = 90) -> int:
        """Clean up old records."""
        return self.delivery_tracker.cleanup_old_records(days)