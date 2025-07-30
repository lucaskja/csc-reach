#!/usr/bin/env python3
"""
Demo script for the Message Logging and Analytics System.
This script demonstrates the key features of the logging system.
"""

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from multichannel_messaging.core.message_logger import MessageLogger
from multichannel_messaging.core.models import Customer, MessageTemplate, MessageRecord, MessageStatus
from multichannel_messaging.services.logged_email_service import LoggedEmailService


def create_sample_customers():
    """Create sample customers for testing."""
    return [
        Customer(
            name="John Doe",
            company="Acme Corp",
            email="john.doe@acme.com",
            phone="+1234567890"
        ),
        Customer(
            name="Jane Smith",
            company="Tech Solutions",
            email="jane.smith@techsolutions.com",
            phone="+1234567891"
        ),
        Customer(
            name="Bob Johnson",
            company="Global Industries",
            email="bob.johnson@global.com",
            phone="+1234567892"
        ),
        Customer(
            name="Alice Brown",
            company="Innovation Labs",
            email="alice.brown@innovation.com",
            phone="+1234567893"
        ),
        Customer(
            name="Charlie Wilson",
            company="Future Systems",
            email="charlie.wilson@future.com",
            phone="+1234567894"
        )
    ]


def create_sample_template():
    """Create a sample email template."""
    return MessageTemplate(
        id="welcome_template",
        name="Welcome Email",
        channels=["email"],
        subject="Welcome to CSC-Reach, {name}!",
        content="""
Dear {name},

Welcome to CSC-Reach! We're excited to have {company} as part of our community.

Our platform will help you streamline your communication processes and reach your customers more effectively.

Best regards,
The CSC-Reach Team
        """.strip(),
        variables=["name", "company"]
    )


def demo_basic_logging():
    """Demonstrate basic message logging functionality."""
    print("=" * 60)
    print("DEMO: Basic Message Logging")
    print("=" * 60)
    
    # Initialize message logger
    message_logger = MessageLogger(user_id="demo_user")
    
    # Create sample data
    customers = create_sample_customers()
    template = create_sample_template()
    
    # Start a session
    session_id = message_logger.start_session("email", template)
    print(f"Started session: {session_id}")
    
    # Log some messages
    for i, customer in enumerate(customers[:3]):
        message_record = MessageRecord(
            customer=customer,
            template=template,
            channel="email",
            status=MessageStatus.PENDING
        )
        
        # Log the message
        log_id = message_logger.log_message(
            message_record, 
            f"Welcome email to {customer.name}..."
        )
        print(f"Logged message {i+1}: {log_id}")
        
        # Simulate sending process
        time.sleep(0.1)  # Brief delay
        
        # Update status (simulate success/failure)
        if i == 1:  # Simulate one failure
            message_logger.update_message_status(
                log_id, MessageStatus.FAILED, 
                error_message="SMTP connection failed"
            )
            print(f"  → Failed: SMTP connection failed")
        else:
            message_logger.update_message_status(
                log_id, MessageStatus.SENT,
                message_id=f"msg_{i+1}_{int(time.time())}"
            )
            print(f"  → Sent successfully")
    
    # End session
    session_summary = message_logger.end_session()
    if session_summary:
        print(f"\nSession Summary:")
        print(f"  Total messages: {session_summary.total_messages}")
        print(f"  Successful: {session_summary.successful_messages}")
        print(f"  Failed: {session_summary.failed_messages}")
        print(f"  Success rate: {session_summary.success_rate:.1f}%")
    
    return message_logger


def demo_analytics(message_logger):
    """Demonstrate analytics functionality."""
    print("\n" + "=" * 60)
    print("DEMO: Analytics and Reporting")
    print("=" * 60)
    
    # Get quick stats
    stats = message_logger.get_quick_stats()
    print("Quick Statistics:")
    print(f"  Messages (30d): {stats['messages_last_30_days']}")
    print(f"  Success rate: {stats['success_rate_30_days']}%")
    print(f"  Most used channel: {stats['most_used_channel']}")
    print(f"  Sessions (30d): {stats['sessions_last_30_days']}")
    print(f"  Active session: {stats['current_session_active']}")
    
    # Get message history
    print("\nRecent Message History:")
    recent_messages = message_logger.get_message_history(days=1)
    for msg in recent_messages[:5]:  # Show last 5
        status_icon = "✓" if msg.message_status == "sent" else "✗"
        print(f"  {status_icon} {msg.timestamp.strftime('%H:%M:%S')} - "
              f"{msg.recipient_email} - {msg.message_status}")
    
    # Get session history
    print("\nSession History:")
    sessions = message_logger.get_session_history(days=1)
    for session in sessions:
        print(f"  {session.session_id}")
        print(f"    Started: {session.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"    Messages: {session.successful_messages}/{session.total_messages}")
        print(f"    Success rate: {session.success_rate:.1f}%")


def demo_data_export(message_logger):
    """Demonstrate data export functionality."""
    print("\n" + "=" * 60)
    print("DEMO: Data Export")
    print("=" * 60)
    
    # Export as JSON
    print("Exporting data as JSON...")
    json_data = message_logger.export_data("json", days=1)
    
    # Save to file
    export_file = Path("demo_export.json")
    with open(export_file, "w") as f:
        f.write(json_data)
    
    print(f"Exported to: {export_file}")
    print(f"File size: {export_file.stat().st_size} bytes")
    
    # Show preview of exported data
    import json
    data = json.loads(json_data)
    print(f"\nExport contains:")
    print(f"  Messages: {len(data['messages'])}")
    print(f"  Sessions: {len(data['sessions'])}")
    print(f"  Export date: {data['export_date']}")
    print(f"  User ID: {data['user_id']}")
    
    return export_file


def demo_enhanced_email_service():
    """Demonstrate the enhanced email service with logging."""
    print("\n" + "=" * 60)
    print("DEMO: Enhanced Email Service (Simulation)")
    print("=" * 60)
    
    # Note: This is a simulation since we don't have Outlook running
    message_logger = MessageLogger(user_id="demo_user_2")
    
    # Create mock email service for demo
    class MockEmailService:
        def send_email(self, customer, template):
            # Simulate random success/failure
            import random
            return random.random() > 0.2  # 80% success rate
        
        def create_draft_email(self, customer, template):
            return True  # Drafts always succeed
    
    # Replace the real email service with mock for demo
    logged_service = LoggedEmailService(message_logger)
    logged_service.email_service = MockEmailService()
    
    # Create sample data
    customers = create_sample_customers()
    template = create_sample_template()
    
    print("Simulating bulk email send...")
    
    # Set up progress callback
    def progress_callback(current, total, message):
        progress = (current / total) * 100
        print(f"  Progress: {progress:.1f}% - {message}")
    
    logged_service.set_progress_callback(progress_callback)
    
    # Send bulk emails (simulated)
    results = logged_service.send_bulk_emails(
        customers=customers,
        template=template,
        batch_size=2,
        delay_between_emails=0.1
    )
    
    # Show results
    print(f"\nResults:")
    successful = len([r for r in results if r.status == MessageStatus.SENT])
    failed = len([r for r in results if r.status == MessageStatus.FAILED])
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Success rate: {(successful/len(results)*100):.1f}%")
    
    # Show recent activity
    print("\nRecent Activity:")
    activity = logged_service.get_recent_activity(limit=5)
    for item in activity:
        status_icon = "✓" if item['status'] == "sent" else "✗"
        print(f"  {status_icon} {item['timestamp'].strftime('%H:%M:%S')} - "
              f"{item['recipient']} - {item['status']}")
    
    # Show statistics
    print("\nSending Statistics:")
    stats = logged_service.get_sending_statistics(days=1)
    print(f"  Total emails: {stats['total_emails']}")
    print(f"  Success rate: {stats['success_rate']}%")
    print(f"  Unique recipients: {stats['unique_recipients']}")
    if stats['most_used_template']:
        print(f"  Most used template: {stats['most_used_template']}")


def demo_data_management(message_logger):
    """Demonstrate data management features."""
    print("\n" + "=" * 60)
    print("DEMO: Data Management")
    print("=" * 60)
    
    # Show database info
    db_path = message_logger.db_path
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"Database file: {db_path}")
        print(f"Database size: {size_mb:.2f} MB")
    
    # Show cleanup options
    print(f"\nData retention options:")
    print(f"  Current data age: varies")
    print(f"  Cleanup threshold: 90 days (configurable)")
    print(f"  Auto-cleanup: enabled")
    
    # Note: We won't actually delete data in the demo
    print(f"\nNote: In production, you can:")
    print(f"  - Set custom retention periods")
    print(f"  - Schedule automatic cleanup")
    print(f"  - Export data before cleanup")
    print(f"  - Monitor database performance")


def main():
    """Run the complete demo."""
    print("CSC-Reach Message Logging and Analytics System Demo")
    print("=" * 60)
    print("This demo showcases the comprehensive logging and analytics")
    print("capabilities of the CSC-Reach messaging system.")
    print()
    
    try:
        # Demo 1: Basic logging
        message_logger = demo_basic_logging()
        
        # Demo 2: Analytics
        demo_analytics(message_logger)
        
        # Demo 3: Data export
        export_file = demo_data_export(message_logger)
        
        # Demo 4: Enhanced email service
        demo_enhanced_email_service()
        
        # Demo 5: Data management
        demo_data_management(message_logger)
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("Key features demonstrated:")
        print("✓ Comprehensive message logging")
        print("✓ Session tracking and management")
        print("✓ Real-time analytics and reporting")
        print("✓ Data export and portability")
        print("✓ Enhanced email service integration")
        print("✓ Data management and cleanup")
        print()
        print("Files created:")
        print(f"  - {message_logger.db_path} (SQLite database)")
        print(f"  - {export_file} (JSON export)")
        print()
        print("Next steps:")
        print("  1. Run the application to see the GUI analytics")
        print("  2. Check the database file for stored data")
        print("  3. Review the exported JSON file")
        print("  4. Explore the analytics dialog in the main application")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())