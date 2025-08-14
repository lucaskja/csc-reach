#!/usr/bin/env python3
"""
Integration tests for the comprehensive message logging system.
This test verifies end-to-end functionality including email counting and logging.
"""

import sys
import time
import pytest
from pathlib import Path

from multichannel_messaging.core.message_logger import MessageLogger
from multichannel_messaging.core.models import Customer, MessageTemplate, MessageRecord, MessageStatus
from multichannel_messaging.services.logged_email_service import LoggedEmailService


def create_test_customers():
    """Create test customers."""
    return [
        Customer(name="Alice Johnson", company="Tech Corp", email="alice@techcorp.com", phone="+1111111111"),
        Customer(name="Bob Smith", company="Global Inc", email="bob@global.com", phone="+2222222222"),
        Customer(name="Carol Davis", company="Innovation Labs", email="carol@innovation.com", phone="+3333333333"),
        Customer(name="David Wilson", company="Future Systems", email="david@future.com", phone="+4444444444"),
        Customer(name="Eva Brown", company="Smart Solutions", email="eva@smart.com", phone="+5555555555"),
    ]


def create_test_template():
    """Create test template."""
    return MessageTemplate(
        id="final_test_template",
        name="Final Test Email",
        channels=["email"],
        subject="Important Update for {company}",
        content="""
Dear {name},

We hope this email finds you well. We wanted to reach out to {company} with an important update about our services.

Our team has been working hard to improve our platform, and we're excited to share these enhancements with you.

Best regards,
The CSC-Reach Team
        """.strip(),
        variables=["name", "company"]
    )


def test_comprehensive_logging():
    """Test comprehensive logging with multiple scenarios."""
    
    # Initialize fresh message logger
    db_path = Path("integration_test_logs.db")
    if db_path.exists():
        db_path.unlink()  # Remove existing test database
    
    message_logger = MessageLogger(user_id="integration_test_user", db_path=str(db_path))
    
    # Create mock email service with controlled success/failure
    class ControlledMockEmailService:
        def __init__(self):
            self.call_count = 0
            self.success_pattern = [True, True, False, True, False]  # 3 success, 2 failures
        
        def send_email(self, customer, template):
            result = self.success_pattern[self.call_count % len(self.success_pattern)]
            self.call_count += 1
            time.sleep(0.1)  # Simulate sending time
            return result
        
        def create_draft_email(self, customer, template):
            return True
        
        def is_outlook_running(self):
            return True
        
        def start_outlook(self):
            return True
        
        def test_connection(self):
            return True, "Mock connection successful"
        
        def get_outlook_version(self):
            return "Mock Outlook 2021"
        
        def get_platform_info(self):
            return "Test Platform"
    
    # Create logged email service
    logged_service = LoggedEmailService(message_logger)
    logged_service.email_service = ControlledMockEmailService()
    
    # Test data
    customers = create_test_customers()
    template = create_test_template()
    
    print(f"Testing with {len(customers)} customers...")
    print("Expected pattern: Success, Success, Failure, Success, Failure")
    print()
    
    # Test 1: Individual email sending
    print("TEST 1: Individual Email Sending")
    print("-" * 40)
    
    individual_results = []
    for i, customer in enumerate(customers[:3]):  # Test first 3 individually
        print(f"Sending to {customer.name} ({customer.email})...")
        result = logged_service.send_single_email(customer, template)
        individual_results.append(result)
        
        status = "✓ SUCCESS" if result.status == MessageStatus.SENT else "✗ FAILED"
        error = f" ({result.error_message})" if result.error_message else ""
        print(f"  Result: {status}{error}")
    
    print(f"\nIndividual sending summary:")
    individual_success = len([r for r in individual_results if r.status == MessageStatus.SENT])
    print(f"  Successful: {individual_success}/{len(individual_results)}")
    print(f"  Success rate: {(individual_success/len(individual_results)*100):.1f}%")
    
    # Test 2: Bulk email sending
    print(f"\nTEST 2: Bulk Email Sending")
    print("-" * 40)
    
    remaining_customers = customers[3:]  # Send to remaining customers
    print(f"Bulk sending to {len(remaining_customers)} customers...")
    
    bulk_results = logged_service.send_bulk_emails(
        customers=remaining_customers,
        template=template,
        batch_size=2,
        delay_between_emails=0.2
    )
    
    bulk_success = len([r for r in bulk_results if r.status == MessageStatus.SENT])
    print(f"\nBulk sending summary:")
    print(f"  Successful: {bulk_success}/{len(bulk_results)}")
    print(f"  Success rate: {(bulk_success/len(bulk_results)*100):.1f}%")
    
    # Test 3: Verify logging and statistics
    print(f"\nTEST 3: Logging and Statistics Verification")
    print("-" * 40)
    
    # Get overall statistics
    stats = logged_service.get_sending_statistics(days=1)
    print(f"Overall statistics:")
    print(f"  Total emails sent: {stats['total_emails']}")
    print(f"  Successful emails: {stats['successful_emails']}")
    print(f"  Failed emails: {stats['failed_emails']}")
    print(f"  Success rate: {stats['success_rate']}%")
    print(f"  Unique recipients: {stats['unique_recipients']}")
    
    # Get message history
    message_history = message_logger.get_message_history(days=1, channel="email")
    print(f"\nMessage history:")
    print(f"  Total logged messages: {len(message_history)}")
    
    for msg in message_history:
        status_icon = "✓" if msg.message_status == "sent" else "✗"
        print(f"  {status_icon} {msg.recipient_name} ({msg.recipient_email}) - {msg.message_status}")
    
    # Get session history
    session_history = message_logger.get_session_history(days=1)
    print(f"\nSession history:")
    print(f"  Total sessions: {len(session_history)}")
    
    total_session_messages = 0
    total_session_success = 0
    
    for session in session_history:
        print(f"  Session: {session.session_id}")
        print(f"    Messages: {session.successful_messages}/{session.total_messages}")
        print(f"    Success rate: {session.success_rate:.1f}%")
        print(f"    Duration: {session.start_time} to {session.end_time}")
        
        total_session_messages += session.total_messages
        total_session_success += session.successful_messages
    
    # Verification
    print(f"\nVERIFICATION:")
    print("-" * 40)
    
    expected_total = len(customers)
    expected_success = 3  # Based on our success pattern
    expected_failures = 2
    
    print(f"Expected totals:")
    print(f"  Total emails: {expected_total}")
    print(f"  Expected successes: {expected_success}")
    print(f"  Expected failures: {expected_failures}")
    
    print(f"\nActual totals:")
    print(f"  Logged messages: {len(message_history)}")
    print(f"  Session messages: {total_session_messages}")
    print(f"  Statistics total: {stats['total_emails']}")
    print(f"  Statistics success: {stats['successful_emails']}")
    print(f"  Statistics failures: {stats['failed_emails']}")
    
    # Check if counts match
    counts_match = (
        len(message_history) == expected_total and
        stats['total_emails'] == expected_total and
        stats['successful_emails'] == expected_success and
        stats['failed_emails'] == expected_failures
    )
    
    if counts_match:
        print(f"\n✅ SUCCESS: All counts match expected values!")
        print("The message logging system is working correctly.")
        print("Emails are being counted and logged properly.")
    else:
        print(f"\n❌ FAILURE: Counts do not match expected values!")
        print("There may be an issue with the logging system.")
        return False
    
    # Test 4: Export functionality
    print(f"\nTEST 4: Data Export")
    print("-" * 40)
    
    export_data = message_logger.export_data("json", days=1)
    export_file = Path("final_test_export.json")
    with open(export_file, "w") as f:
        f.write(export_data)
    
    print(f"✓ Data exported to: {export_file}")
    print(f"  File size: {export_file.stat().st_size} bytes")
    
    # Parse and verify export
    import json
    exported = json.loads(export_data)
    print(f"  Exported messages: {len(exported['messages'])}")
    print(f"  Exported sessions: {len(exported['sessions'])}")
    
    return True


def main():
    """Run the comprehensive test."""
    try:
        if test_comprehensive_logging():
            print("\n" + "=" * 70)
            print("🎉 ALL TESTS PASSED! 🎉")
            print("=" * 70)
            print("The message logging system is fully functional:")
            print("✓ Individual email sending with logging")
            print("✓ Bulk email sending with logging")
            print("✓ Accurate message counting")
            print("✓ Session tracking")
            print("✓ Statistics generation")
            print("✓ Message history")
            print("✓ Data export")
            print()
            print("You can now use the application with confidence that")
            print("all email activity will be properly logged and counted.")
            return 0
        else:
            print("\n❌ TESTS FAILED")
            return 1
            
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())