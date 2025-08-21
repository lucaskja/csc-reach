"""
Email tracking and analytics system for monitoring email performance and delivery.
"""

import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path

from .models import Customer, MessageTemplate, MessageRecord, MessageStatus
from ..utils.logger import get_logger
from ..core.i18n_manager import get_i18n_manager

logger = get_logger(__name__)


class EmailEvent(Enum):
    """Email tracking event types."""
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    COMPLAINED = "complained"
    UNSUBSCRIBED = "unsubscribed"


class BounceType(Enum):
    """Email bounce types."""
    HARD = "hard"
    SOFT = "soft"
    TRANSIENT = "transient"


@dataclass
class EmailTrackingEvent:
    """Email tracking event record."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_id: str = ""
    customer_email: str = ""
    event_type: EmailEvent = EmailEvent.SENT
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Event-specific data
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    location: Optional[str] = None
    device_type: Optional[str] = None
    
    # Bounce/complaint details
    bounce_type: Optional[BounceType] = None
    bounce_reason: Optional[str] = None
    
    # Click tracking
    clicked_url: Optional[str] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        if self.bounce_type:
            data['bounce_type'] = self.bounce_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmailTrackingEvent':
        """Create from dictionary."""
        # Convert timestamp
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        # Convert enums
        if 'event_type' in data:
            data['event_type'] = EmailEvent(data['event_type'])
        if 'bounce_type' in data and data['bounce_type']:
            data['bounce_type'] = BounceType(data['bounce_type'])
        
        return cls(**data)


@dataclass
class EmailCampaignStats:
    """Email campaign statistics."""
    campaign_id: str
    campaign_name: str
    start_date: datetime
    end_date: Optional[datetime] = None
    
    # Basic metrics
    total_sent: int = 0
    total_delivered: int = 0
    total_bounced: int = 0
    total_opened: int = 0
    total_clicked: int = 0
    total_complained: int = 0
    total_unsubscribed: int = 0
    
    # Calculated rates
    delivery_rate: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0
    bounce_rate: float = 0.0
    complaint_rate: float = 0.0
    unsubscribe_rate: float = 0.0
    
    # Advanced metrics
    unique_opens: int = 0
    unique_clicks: int = 0
    click_to_open_rate: float = 0.0
    
    def calculate_rates(self) -> None:
        """Calculate percentage rates."""
        if self.total_sent > 0:
            self.delivery_rate = (self.total_delivered / self.total_sent) * 100
            self.bounce_rate = (self.total_bounced / self.total_sent) * 100
            self.complaint_rate = (self.total_complained / self.total_sent) * 100
            self.unsubscribe_rate = (self.total_unsubscribed / self.total_sent) * 100
        
        if self.total_delivered > 0:
            self.open_rate = (self.total_opened / self.total_delivered) * 100
            self.click_rate = (self.total_clicked / self.total_delivered) * 100
        
        if self.unique_opens > 0:
            self.click_to_open_rate = (self.unique_clicks / self.unique_opens) * 100


@dataclass
class EmailPerformanceReport:
    """Comprehensive email performance report."""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: datetime = field(default_factory=datetime.now)
    period_start: datetime = field(default_factory=lambda: datetime.now() - timedelta(days=30))
    period_end: datetime = field(default_factory=datetime.now)
    
    # Overall statistics
    total_campaigns: int = 0
    total_emails_sent: int = 0
    average_delivery_rate: float = 0.0
    average_open_rate: float = 0.0
    average_click_rate: float = 0.0
    
    # Campaign statistics
    campaign_stats: List[EmailCampaignStats] = field(default_factory=list)
    
    # Top performers
    best_performing_templates: List[Dict[str, Any]] = field(default_factory=list)
    worst_performing_templates: List[Dict[str, Any]] = field(default_factory=list)
    
    # Trends and insights
    delivery_trend: List[Tuple[datetime, float]] = field(default_factory=list)
    open_rate_trend: List[Tuple[datetime, float]] = field(default_factory=list)
    click_rate_trend: List[Tuple[datetime, float]] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)


class EmailAnalyticsDatabase:
    """Database manager for email analytics."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the analytics database."""
        if db_path is None:
            # Default to user data directory
            from ..core.config_manager import ConfigManager
            config_manager = ConfigManager()
            db_path = config_manager.get_app_data_path() / "email_analytics.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Initialize database tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Email tracking events table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS email_events (
                        event_id TEXT PRIMARY KEY,
                        message_id TEXT NOT NULL,
                        customer_email TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        user_agent TEXT,
                        ip_address TEXT,
                        location TEXT,
                        device_type TEXT,
                        bounce_type TEXT,
                        bounce_reason TEXT,
                        clicked_url TEXT,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Email campaigns table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS email_campaigns (
                        campaign_id TEXT PRIMARY KEY,
                        campaign_name TEXT NOT NULL,
                        template_id TEXT,
                        start_date TEXT NOT NULL,
                        end_date TEXT,
                        total_recipients INTEGER DEFAULT 0,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Email messages table (links events to campaigns)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS email_messages (
                        message_id TEXT PRIMARY KEY,
                        campaign_id TEXT,
                        customer_email TEXT NOT NULL,
                        template_id TEXT,
                        subject TEXT,
                        sent_at TEXT,
                        status TEXT,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (campaign_id) REFERENCES email_campaigns (campaign_id)
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_message_id ON email_events (message_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_customer_email ON email_events (customer_email)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON email_events (timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_type ON email_events (event_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_campaign ON email_messages (campaign_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_customer ON email_messages (customer_email)')
                
                conn.commit()
                logger.info("Email analytics database initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize analytics database: {e}")
            raise
    
    def record_event(self, event: EmailTrackingEvent) -> bool:
        """Record an email tracking event."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                event_data = event.to_dict()
                cursor.execute('''
                    INSERT OR REPLACE INTO email_events (
                        event_id, message_id, customer_email, event_type, timestamp,
                        user_agent, ip_address, location, device_type,
                        bounce_type, bounce_reason, clicked_url, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.event_id,
                    event.message_id,
                    event.customer_email,
                    event.event_type.value,
                    event.timestamp.isoformat(),
                    event.user_agent,
                    event.ip_address,
                    event.location,
                    event.device_type,
                    event.bounce_type.value if event.bounce_type else None,
                    event.bounce_reason,
                    event.clicked_url,
                    json.dumps(event.metadata) if event.metadata else None
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to record email event: {e}")
            return False
    
    def create_campaign(
        self,
        campaign_name: str,
        template_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new email campaign."""
        campaign_id = str(uuid.uuid4())
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO email_campaigns (
                        campaign_id, campaign_name, template_id, start_date, metadata
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    campaign_id,
                    campaign_name,
                    template_id,
                    datetime.now().isoformat(),
                    json.dumps(metadata) if metadata else None
                ))
                
                conn.commit()
                logger.info(f"Created email campaign: {campaign_name} ({campaign_id})")
                return campaign_id
                
        except Exception as e:
            logger.error(f"Failed to create email campaign: {e}")
            raise
    
    def record_message(
        self,
        message_id: str,
        campaign_id: str,
        customer_email: str,
        template_id: Optional[str] = None,
        subject: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Record an email message."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO email_messages (
                        message_id, campaign_id, customer_email, template_id,
                        subject, sent_at, status, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    message_id,
                    campaign_id,
                    customer_email,
                    template_id,
                    subject,
                    datetime.now().isoformat(),
                    MessageStatus.SENT.value,
                    json.dumps(metadata) if metadata else None
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to record email message: {e}")
            return False
    
    def get_campaign_stats(self, campaign_id: str) -> Optional[EmailCampaignStats]:
        """Get statistics for a specific campaign."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get campaign info
                cursor.execute('''
                    SELECT campaign_name, start_date, end_date
                    FROM email_campaigns
                    WHERE campaign_id = ?
                ''', (campaign_id,))
                
                campaign_row = cursor.fetchone()
                if not campaign_row:
                    return None
                
                campaign_name, start_date_str, end_date_str = campaign_row
                start_date = datetime.fromisoformat(start_date_str)
                end_date = datetime.fromisoformat(end_date_str) if end_date_str else None
                
                # Get event counts
                cursor.execute('''
                    SELECT 
                        e.event_type,
                        COUNT(*) as count,
                        COUNT(DISTINCT e.customer_email) as unique_count
                    FROM email_events e
                    JOIN email_messages m ON e.message_id = m.message_id
                    WHERE m.campaign_id = ?
                    GROUP BY e.event_type
                ''', (campaign_id,))
                
                event_counts = {}
                unique_counts = {}
                for event_type, count, unique_count in cursor.fetchall():
                    event_counts[event_type] = count
                    unique_counts[event_type] = unique_count
                
                # Create stats object
                stats = EmailCampaignStats(
                    campaign_id=campaign_id,
                    campaign_name=campaign_name,
                    start_date=start_date,
                    end_date=end_date,
                    total_sent=event_counts.get('sent', 0),
                    total_delivered=event_counts.get('delivered', 0),
                    total_bounced=event_counts.get('bounced', 0),
                    total_opened=event_counts.get('opened', 0),
                    total_clicked=event_counts.get('clicked', 0),
                    total_complained=event_counts.get('complained', 0),
                    total_unsubscribed=event_counts.get('unsubscribed', 0),
                    unique_opens=unique_counts.get('opened', 0),
                    unique_clicks=unique_counts.get('clicked', 0)
                )
                
                stats.calculate_rates()
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get campaign stats: {e}")
            return None
    
    def get_events_for_message(self, message_id: str) -> List[EmailTrackingEvent]:
        """Get all events for a specific message."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT event_id, message_id, customer_email, event_type, timestamp,
                           user_agent, ip_address, location, device_type,
                           bounce_type, bounce_reason, clicked_url, metadata
                    FROM email_events
                    WHERE message_id = ?
                    ORDER BY timestamp
                ''', (message_id,))
                
                events = []
                for row in cursor.fetchall():
                    event_data = {
                        'event_id': row[0],
                        'message_id': row[1],
                        'customer_email': row[2],
                        'event_type': row[3],
                        'timestamp': row[4],
                        'user_agent': row[5],
                        'ip_address': row[6],
                        'location': row[7],
                        'device_type': row[8],
                        'bounce_type': row[9],
                        'bounce_reason': row[10],
                        'clicked_url': row[11],
                        'metadata': json.loads(row[12]) if row[12] else {}
                    }
                    
                    events.append(EmailTrackingEvent.from_dict(event_data))
                
                return events
                
        except Exception as e:
            logger.error(f"Failed to get events for message {message_id}: {e}")
            return []


class EmailAnalyticsManager:
    """Main email analytics and tracking manager."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the analytics manager."""
        self.i18n_manager = get_i18n_manager()
        self.database = EmailAnalyticsDatabase(db_path)
        self._current_campaign_id = None
    
    def start_campaign(
        self,
        campaign_name: str,
        template: Optional[MessageTemplate] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start a new email campaign."""
        template_id = template.id if template else None
        campaign_id = self.database.create_campaign(
            campaign_name=campaign_name,
            template_id=template_id,
            metadata=metadata
        )
        
        self._current_campaign_id = campaign_id
        logger.info(f"Started email campaign: {campaign_name}")
        return campaign_id
    
    def track_email_sent(
        self,
        message_record: MessageRecord,
        campaign_id: Optional[str] = None
    ) -> str:
        """Track when an email is sent."""
        if not campaign_id:
            campaign_id = self._current_campaign_id
        
        if not campaign_id:
            # Create a default campaign
            campaign_id = self.start_campaign("Default Campaign")
        
        # Generate unique message ID
        message_id = str(uuid.uuid4())
        
        # Record the message
        self.database.record_message(
            message_id=message_id,
            campaign_id=campaign_id,
            customer_email=message_record.customer.email,
            template_id=message_record.template.id if message_record.template else None,
            subject=message_record.template.subject if message_record.template else None
        )
        
        # Record sent event
        event = EmailTrackingEvent(
            message_id=message_id,
            customer_email=message_record.customer.email,
            event_type=EmailEvent.SENT
        )
        
        self.database.record_event(event)
        
        logger.debug(f"Tracked email sent: {message_id} to {message_record.customer.email}")
        return message_id
    
    def track_email_delivered(self, message_id: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Track when an email is delivered."""
        event = EmailTrackingEvent(
            message_id=message_id,
            event_type=EmailEvent.DELIVERED,
            metadata=metadata or {}
        )
        
        return self.database.record_event(event)
    
    def track_email_opened(
        self,
        message_id: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track when an email is opened."""
        event = EmailTrackingEvent(
            message_id=message_id,
            event_type=EmailEvent.OPENED,
            user_agent=user_agent,
            ip_address=ip_address,
            metadata=metadata or {}
        )
        
        return self.database.record_event(event)
    
    def track_email_clicked(
        self,
        message_id: str,
        clicked_url: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track when a link in an email is clicked."""
        event = EmailTrackingEvent(
            message_id=message_id,
            event_type=EmailEvent.CLICKED,
            clicked_url=clicked_url,
            user_agent=user_agent,
            ip_address=ip_address,
            metadata=metadata or {}
        )
        
        return self.database.record_event(event)
    
    def track_email_bounced(
        self,
        message_id: str,
        bounce_type: BounceType,
        bounce_reason: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track when an email bounces."""
        event = EmailTrackingEvent(
            message_id=message_id,
            event_type=EmailEvent.BOUNCED,
            bounce_type=bounce_type,
            bounce_reason=bounce_reason,
            metadata=metadata or {}
        )
        
        return self.database.record_event(event)
    
    def get_campaign_performance(self, campaign_id: str) -> Optional[EmailCampaignStats]:
        """Get performance statistics for a campaign."""
        return self.database.get_campaign_stats(campaign_id)
    
    def get_message_timeline(self, message_id: str) -> List[EmailTrackingEvent]:
        """Get the complete timeline of events for a message."""
        return self.database.get_events_for_message(message_id)
    
    def generate_performance_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> EmailPerformanceReport:
        """Generate a comprehensive performance report."""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        report = EmailPerformanceReport(
            period_start=start_date,
            period_end=end_date
        )
        
        try:
            # Get all campaigns in the period
            with sqlite3.connect(self.database.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT campaign_id
                    FROM email_campaigns
                    WHERE start_date >= ? AND start_date <= ?
                ''', (start_date.isoformat(), end_date.isoformat()))
                
                campaign_ids = [row[0] for row in cursor.fetchall()]
                
                # Get stats for each campaign
                total_sent = 0
                total_delivery_rate = 0
                total_open_rate = 0
                total_click_rate = 0
                valid_campaigns = 0
                
                for campaign_id in campaign_ids:
                    stats = self.database.get_campaign_stats(campaign_id)
                    if stats:
                        report.campaign_stats.append(stats)
                        total_sent += stats.total_sent
                        
                        if stats.total_sent > 0:
                            total_delivery_rate += stats.delivery_rate
                            total_open_rate += stats.open_rate
                            total_click_rate += stats.click_rate
                            valid_campaigns += 1
                
                # Calculate averages
                report.total_campaigns = len(campaign_ids)
                report.total_emails_sent = total_sent
                
                if valid_campaigns > 0:
                    report.average_delivery_rate = total_delivery_rate / valid_campaigns
                    report.average_open_rate = total_open_rate / valid_campaigns
                    report.average_click_rate = total_click_rate / valid_campaigns
                
                # Generate recommendations
                report.recommendations = self._generate_recommendations(report)
                
        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
        
        return report
    
    def _generate_recommendations(self, report: EmailPerformanceReport) -> List[str]:
        """Generate recommendations based on performance data."""
        recommendations = []
        
        # Delivery rate recommendations
        if report.average_delivery_rate < 95:
            recommendations.append(
                self.i18n_manager.tr("recommendation_improve_delivery_rate")
            )
        
        # Open rate recommendations
        if report.average_open_rate < 20:
            recommendations.append(
                self.i18n_manager.tr("recommendation_improve_subject_lines")
            )
        
        # Click rate recommendations
        if report.average_click_rate < 2:
            recommendations.append(
                self.i18n_manager.tr("recommendation_improve_content_engagement")
            )
        
        # Campaign frequency recommendations
        if report.total_campaigns < 4:  # Less than weekly in a month
            recommendations.append(
                self.i18n_manager.tr("recommendation_increase_frequency")
            )
        
        return recommendations
    
    def cleanup_old_data(self, days_to_keep: int = 365) -> int:
        """Clean up old tracking data."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        try:
            with sqlite3.connect(self.database.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete old events
                cursor.execute('''
                    DELETE FROM email_events
                    WHERE timestamp < ?
                ''', (cutoff_date.isoformat(),))
                
                deleted_events = cursor.rowcount
                
                # Delete old messages without events
                cursor.execute('''
                    DELETE FROM email_messages
                    WHERE message_id NOT IN (
                        SELECT DISTINCT message_id FROM email_events
                    ) AND sent_at < ?
                ''', (cutoff_date.isoformat(),))
                
                deleted_messages = cursor.rowcount
                
                # Delete old campaigns without messages
                cursor.execute('''
                    DELETE FROM email_campaigns
                    WHERE campaign_id NOT IN (
                        SELECT DISTINCT campaign_id FROM email_messages
                        WHERE campaign_id IS NOT NULL
                    ) AND start_date < ?
                ''', (cutoff_date.isoformat(),))
                
                deleted_campaigns = cursor.rowcount
                
                conn.commit()
                
                total_deleted = deleted_events + deleted_messages + deleted_campaigns
                logger.info(f"Cleaned up {total_deleted} old analytics records")
                
                return total_deleted
                
        except Exception as e:
            logger.error(f"Failed to cleanup old analytics data: {e}")
            return 0