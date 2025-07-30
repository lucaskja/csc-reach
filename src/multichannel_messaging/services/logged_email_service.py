"""
Enhanced email service with comprehensive message logging and analytics.
Wraps the existing email service to provide detailed tracking and user control.
"""

import time
from typing import List, Optional, Tuple, Callable
from datetime import datetime

from .email_service import EmailService
from ..core.models import Customer, MessageTemplate, MessageRecord, MessageStatus
from ..core.message_logger import MessageLogger
from ..utils.logger import get_logger
from ..utils.exceptions import ServiceUnavailableError

logger = get_logger(__name__)


class LoggedEmailService:
    """
    Enhanced email service with comprehensive logging and analytics.
    
    This service wraps the existing EmailService to provide:
    - Detailed message logging for every send attempt
    - Session tracking for bulk operations
    - Real-time progress reporting
    - Comprehensive error tracking
    - User analytics and insights
    """
    
    def __init__(self, message_logger: MessageLogger):
        """
        Initialize the logged email service.
        
        Args:
            message_logger: Message logger instance for tracking
        """
        self.email_service = EmailService()
        self.message_logger = message_logger
        self.logger = get_logger(__name__)
        
        # Progress tracking
        self.progress_callback: Optional[Callable[[int, int, str], None]] = None
        self.current_session_id: Optional[str] = None
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]) -> None:
        """
        Set callback for progress updates during bulk operations.
        
        Args:
            callback: Function that receives (current, total, status_message)
        """
        self.progress_callback = callback
    
    def is_outlook_running(self) -> bool:
        """Check if Outlook is currently running."""
        return self.email_service.is_outlook_running()
    
    def start_outlook(self) -> bool:
        """Start Outlook application."""
        return self.email_service.start_outlook()
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test connection to Outlook."""
        return self.email_service.test_connection()
    
    def get_outlook_version(self) -> Optional[str]:
        """Get Outlook version information."""
        return self.email_service.get_outlook_version()
    
    def get_platform_info(self) -> str:
        """Get platform information."""
        return self.email_service.get_platform_info()
    
    def send_single_email(self, customer: Customer, template: MessageTemplate) -> MessageRecord:
        """
        Send a single email with comprehensive logging.
        
        Args:
            customer: Customer to send email to
            template: Email template to use
            
        Returns:
            MessageRecord with detailed sending results
        """
        # Create message record
        message_record = MessageRecord(
            customer=customer,
            template=template,
            channel="email",
            status=MessageStatus.PENDING
        )
        
        # Start a single-message session if none exists
        session_started = False
        if not self.message_logger.current_session_id:
            self.message_logger.start_session("email", template)
            session_started = True
        
        try:
            # Log the attempt
            content_preview = message_record.rendered_content.get("content", "")[:100]
            log_id = self.message_logger.log_message(message_record, content_preview)
            
            # Update status to sending
            message_record.status = MessageStatus.SENDING
            self.message_logger.update_message_status(log_id, MessageStatus.SENDING)
            
            # Attempt to send
            success = self.email_service.send_email(customer, template)
            
            if success:
                message_record.mark_as_sent()
                self.message_logger.update_message_status(log_id, MessageStatus.SENT)
                self.logger.info(f"Successfully sent email to {customer.email}")
            else:
                error_msg = "Email sending failed (unknown error)"
                message_record.mark_as_failed(error_msg)
                self.message_logger.update_message_status(
                    log_id, MessageStatus.FAILED, error_message=error_msg
                )
                self.logger.warning(f"Failed to send email to {customer.email}")
            
        except Exception as e:
            error_msg = f"Email sending exception: {str(e)}"
            message_record.mark_as_failed(error_msg)
            self.message_logger.update_message_status(
                log_id, MessageStatus.FAILED, error_message=error_msg
            )
            self.logger.error(f"Exception sending email to {customer.email}: {e}")
        
        finally:
            # End session if we started it
            if session_started:
                self.message_logger.end_session()
        
        return message_record
    
    def send_bulk_emails(
        self,
        customers: List[Customer],
        template: MessageTemplate,
        batch_size: int = 10,
        delay_between_emails: float = 1.0,
        create_drafts_only: bool = False
    ) -> List[MessageRecord]:
        """
        Send bulk emails with comprehensive logging and progress tracking.
        
        Args:
            customers: List of customers to send emails to
            template: Email template to use
            batch_size: Number of emails to send in each batch
            delay_between_emails: Delay between emails in seconds
            create_drafts_only: If True, create drafts instead of sending
            
        Returns:
            List of message records with detailed results
        """
        if not customers:
            return []
        
        # Start session
        session_id = self.message_logger.start_session("email", template)
        self.current_session_id = session_id
        
        message_records = []
        successful_sends = 0
        failed_sends = 0
        
        try:
            total_customers = len(customers)
            self.logger.info(f"Starting bulk email operation: {total_customers} recipients")
            
            # Update progress
            if self.progress_callback:
                self.progress_callback(0, total_customers, "Starting bulk email operation...")
            
            for i, customer in enumerate(customers):
                try:
                    # Create message record
                    message_record = MessageRecord(
                        customer=customer,
                        template=template,
                        channel="email",
                        status=MessageStatus.PENDING
                    )
                    
                    # Log the attempt
                    content_preview = message_record.rendered_content.get("content", "")[:100]
                    log_id = self.message_logger.log_message(message_record, content_preview)
                    
                    # Update progress
                    if self.progress_callback:
                        self.progress_callback(
                            i + 1, total_customers, 
                            f"Processing {customer.email}..."
                        )
                    
                    # Update status to sending
                    message_record.status = MessageStatus.SENDING
                    self.message_logger.update_message_status(log_id, MessageStatus.SENDING)
                    
                    # Send email or create draft
                    if create_drafts_only:
                        success = self.email_service.create_draft_email(customer, template)
                        action = "draft created"
                    else:
                        success = self.email_service.send_email(customer, template)
                        action = "sent"
                    
                    if success:
                        message_record.mark_as_sent()
                        self.message_logger.update_message_status(log_id, MessageStatus.SENT)
                        successful_sends += 1
                        self.logger.debug(f"Successfully {action} email to {customer.email}")
                    else:
                        error_msg = f"Email {action.split()[0]}ing failed (unknown error)"
                        message_record.mark_as_failed(error_msg)
                        self.message_logger.update_message_status(
                            log_id, MessageStatus.FAILED, error_message=error_msg
                        )
                        failed_sends += 1
                        self.logger.warning(f"Failed to {action.split()[0]} email to {customer.email}")
                    
                    message_records.append(message_record)
                    
                    # Delay between emails (except for the last one)
                    if i < total_customers - 1 and delay_between_emails > 0:
                        time.sleep(delay_between_emails)
                    
                    # Batch processing pause
                    if (i + 1) % batch_size == 0 and i < total_customers - 1:
                        self.logger.debug(f"Completed batch {(i + 1) // batch_size}, pausing briefly...")
                        time.sleep(0.5)  # Brief pause between batches
                
                except Exception as e:
                    error_msg = f"Exception processing {customer.email}: {str(e)}"
                    
                    # Create failed message record
                    message_record = MessageRecord(
                        customer=customer,
                        template=template,
                        channel="email",
                        status=MessageStatus.FAILED,
                        error_message=error_msg
                    )
                    
                    # Log the failure
                    log_id = self.message_logger.log_message(message_record, "")
                    self.message_logger.update_message_status(
                        log_id, MessageStatus.FAILED, error_message=error_msg
                    )
                    
                    message_records.append(message_record)
                    failed_sends += 1
                    
                    self.logger.error(f"Exception processing {customer.email}: {e}")
            
            # Final progress update
            if self.progress_callback:
                action_word = "Draft creation" if create_drafts_only else "Bulk email"
                self.progress_callback(
                    total_customers, total_customers,
                    f"{action_word} completed: {successful_sends} successful, {failed_sends} failed"
                )
            
            self.logger.info(
                f"Bulk email operation completed: {successful_sends} successful, "
                f"{failed_sends} failed out of {total_customers} total"
            )
        
        except Exception as e:
            self.logger.error(f"Critical error in bulk email operation: {e}")
            
            # Mark remaining customers as failed if we haven't processed them
            for customer in customers[len(message_records):]:
                error_msg = f"Bulk operation failed: {str(e)}"
                message_record = MessageRecord(
                    customer=customer,
                    template=template,
                    channel="email",
                    status=MessageStatus.FAILED,
                    error_message=error_msg
                )
                
                log_id = self.message_logger.log_message(message_record, "")
                self.message_logger.update_message_status(
                    log_id, MessageStatus.FAILED, error_message=error_msg
                )
                
                message_records.append(message_record)
        
        finally:
            # End session and get summary
            session_summary = self.message_logger.end_session()
            self.current_session_id = None
            
            if session_summary:
                self.logger.info(f"Session {session_id} summary: "
                               f"{session_summary.successful_messages}/{session_summary.total_messages} "
                               f"successful ({session_summary.success_rate:.1f}% success rate)")
        
        return message_records
    
    def create_draft_emails(
        self,
        customers: List[Customer],
        template: MessageTemplate,
        batch_size: int = 10
    ) -> List[MessageRecord]:
        """
        Create draft emails for all customers.
        
        Args:
            customers: List of customers to create drafts for
            template: Email template to use
            batch_size: Number of drafts to create in each batch
            
        Returns:
            List of message records with results
        """
        return self.send_bulk_emails(
            customers=customers,
            template=template,
            batch_size=batch_size,
            delay_between_emails=0.1,  # Shorter delay for drafts
            create_drafts_only=True
        )
    
    def get_session_stats(self) -> Optional[dict]:
        """
        Get statistics for the current session.
        
        Returns:
            Dictionary with session statistics or None if no active session
        """
        if not self.current_session_id:
            return None
        
        # Get quick stats from message logger
        stats = self.message_logger.get_quick_stats()
        
        return {
            "session_id": self.current_session_id,
            "session_active": True,
            "total_messages_30d": stats["messages_last_30_days"],
            "success_rate_30d": stats["success_rate_30_days"],
            "most_used_channel": stats["most_used_channel"]
        }
    
    def cancel_current_operation(self) -> bool:
        """
        Cancel the current bulk operation (if possible).
        
        Returns:
            True if cancellation was successful
        """
        # This would need to be implemented with proper threading
        # and cancellation tokens for a real implementation
        self.logger.warning("Operation cancellation requested but not implemented")
        return False
    
    def get_recent_activity(self, limit: int = 10) -> List[dict]:
        """
        Get recent email activity for display.
        
        Args:
            limit: Maximum number of recent activities to return
            
        Returns:
            List of recent activity dictionaries
        """
        try:
            recent_logs = self.message_logger.get_message_history(days=7, channel="email")
            
            activities = []
            for log in recent_logs[:limit]:
                activities.append({
                    "timestamp": log.timestamp,
                    "recipient": log.recipient_email,
                    "template": log.template_name,
                    "status": log.message_status,
                    "error": log.error_message
                })
            
            return activities
        
        except Exception as e:
            self.logger.error(f"Failed to get recent activity: {e}")
            return []
    
    def get_sending_statistics(self, days: int = 30) -> dict:
        """
        Get email sending statistics for the specified period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with statistics
        """
        try:
            logs = self.message_logger.get_message_history(days=days, channel="email")
            
            total_sent = len(logs)
            successful = len([log for log in logs if log.message_status == "sent"])
            failed = len([log for log in logs if log.message_status == "failed"])
            
            success_rate = (successful / total_sent * 100) if total_sent > 0 else 0
            
            # Get unique recipients
            unique_recipients = len(set(log.recipient_email for log in logs))
            
            # Get template usage
            template_usage = {}
            for log in logs:
                template_usage[log.template_name] = template_usage.get(log.template_name, 0) + 1
            
            return {
                "period_days": days,
                "total_emails": total_sent,
                "successful_emails": successful,
                "failed_emails": failed,
                "success_rate": round(success_rate, 1),
                "unique_recipients": unique_recipients,
                "most_used_template": max(template_usage.items(), key=lambda x: x[1])[0] if template_usage else None,
                "template_usage": template_usage
            }
        
        except Exception as e:
            self.logger.error(f"Failed to get sending statistics: {e}")
            return {
                "period_days": days,
                "total_emails": 0,
                "successful_emails": 0,
                "failed_emails": 0,
                "success_rate": 0.0,
                "unique_recipients": 0,
                "most_used_template": None,
                "template_usage": {}
            }