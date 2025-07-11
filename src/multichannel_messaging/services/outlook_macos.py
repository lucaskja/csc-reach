"""
macOS Outlook integration using AppleScript and ScriptingBridge.
"""

import subprocess
import time
from typing import List, Dict, Optional, Tuple
from pathlib import Path

try:
    from ScriptingBridge import SBApplication
    from Foundation import NSAppleScript, NSString
    SCRIPTING_BRIDGE_AVAILABLE = True
except ImportError:
    SCRIPTING_BRIDGE_AVAILABLE = False

from ..core.models import Customer, MessageTemplate, MessageRecord, MessageStatus
from ..utils.exceptions import OutlookIntegrationError, ServiceUnavailableError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class OutlookMacOSService:
    """macOS Outlook integration service."""
    
    def __init__(self):
        """Initialize macOS Outlook service."""
        self.outlook_app = None
        self._check_outlook_availability()
    
    def _check_outlook_availability(self) -> None:
        """Check if Outlook is available on macOS."""
        try:
            # Check if Outlook app exists
            outlook_path = Path("/Applications/Microsoft Outlook.app")
            if not outlook_path.exists():
                raise ServiceUnavailableError("Microsoft Outlook is not installed")
            
            # Try to connect to Outlook
            if SCRIPTING_BRIDGE_AVAILABLE:
                try:
                    self.outlook_app = SBApplication.applicationWithBundleIdentifier_("com.microsoft.Outlook")
                    if not self.outlook_app:
                        raise ServiceUnavailableError("Cannot connect to Outlook via ScriptingBridge")
                except Exception as e:
                    logger.warning(f"ScriptingBridge connection failed: {e}")
                    self.outlook_app = None
            
            logger.info("Outlook macOS service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Outlook macOS service: {e}")
            raise ServiceUnavailableError(f"Outlook is not available: {e}")
    
    def is_outlook_running(self) -> bool:
        """
        Check if Outlook is currently running.
        
        Returns:
            True if Outlook is running, False otherwise
        """
        try:
            # Use AppleScript to check if Outlook is running
            script = '''
            tell application "System Events"
                return (name of processes) contains "Microsoft Outlook"
            end tell
            '''
            
            result = self._run_applescript(script)
            return result.strip().lower() == "true"
            
        except Exception as e:
            logger.warning(f"Failed to check if Outlook is running: {e}")
            return False
    
    def start_outlook(self) -> bool:
        """
        Start Outlook application.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.is_outlook_running():
                logger.info("Outlook is already running")
                return True
            
            # Start Outlook using AppleScript
            script = '''
            tell application "Microsoft Outlook"
                activate
            end tell
            '''
            
            self._run_applescript(script)
            
            # Wait for Outlook to start
            max_wait = 30  # seconds
            wait_time = 0
            while wait_time < max_wait:
                if self.is_outlook_running():
                    logger.info("Outlook started successfully")
                    return True
                time.sleep(1)
                wait_time += 1
            
            logger.error("Timeout waiting for Outlook to start")
            return False
            
        except Exception as e:
            logger.error(f"Failed to start Outlook: {e}")
            return False
    
    def _format_plain_text(self, text: str) -> str:
        """
        Format plain text to ensure proper line breaks are preserved.
        
        Args:
            text: Plain text content
            
        Returns:
            Formatted text with proper line breaks
        """
        if not text:
            return ""
        
        # Normalize line endings to \n first
        formatted = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # For AppleScript, we need to use the return character constant
        # Instead of literal \r, we'll use AppleScript's return constant
        return formatted
    
    def _build_email_script(self, subject: str, content: str, email: str, send: bool = True) -> str:
        """
        Build AppleScript for creating/sending email with proper line break handling.
        
        Args:
            subject: Email subject
            content: Email content with line breaks
            email: Recipient email address
            send: Whether to send the email or just create draft
            
        Returns:
            AppleScript code
        """
        # Escape basic characters for AppleScript strings
        subject_escaped = self._escape_for_applescript(subject)
        email_escaped = self._escape_for_applescript(email)
        
        # For content, we need to properly handle line breaks
        # Replace \n with AppleScript's return character
        content_escaped = self._escape_for_applescript(content)
        
        # Build the complete AppleScript with proper line break handling
        action = "send newMessage" if send else "open newMessage"
        
        script = f'''
        tell application "Microsoft Outlook"
            set newMessage to make new outgoing message
            set subject of newMessage to "{subject_escaped}"
            set content of newMessage to "{content_escaped}"
            make new recipient at newMessage with properties {{email address:{{address:"{email_escaped}"}}}}
            {action}
        end tell
        '''
        
        return script
    
    def _escape_for_applescript(self, text: str) -> str:
        """
        Properly escape text for AppleScript, preserving line breaks.
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text safe for AppleScript with proper line breaks
        """
        if not text:
            return ""
        
        # First, normalize line endings to \n
        normalized = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Escape backslashes first (but not the ones we'll add for \r)
        escaped = normalized.replace('\\', '\\\\')
        
        # Escape quotes
        escaped = escaped.replace('"', '\\"')
        
        # Convert \n to \r for AppleScript (carriage return)
        # This is the key fix - AppleScript uses \r for line breaks
        escaped = escaped.replace('\n', '\\r')
        
        return escaped
        # Escape tabs
        escaped = escaped.replace('\t', '\\t')
        
        return escaped
    
    def _convert_to_html(self, text: str) -> str:
        """
        Convert plain text to HTML format, preserving line breaks and formatting.
        
        Args:
            text: Plain text content
            
        Returns:
            HTML formatted content
        """
        if not text:
            return ""
        
        # Escape HTML special characters
        html_text = (text
                    .replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;')
                    .replace('"', '&quot;')
                    .replace("'", '&#x27;'))
        
        # Convert line breaks to HTML
        # First, normalize line endings
        html_text = html_text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Split into paragraphs (double line breaks)
        paragraphs = html_text.split('\n\n')
        
        # Process each paragraph
        formatted_paragraphs = []
        for paragraph in paragraphs:
            if paragraph.strip():
                # Convert single line breaks within paragraphs to <br>
                formatted_paragraph = paragraph.replace('\n', '<br>')
                formatted_paragraphs.append(f'<p>{formatted_paragraph}</p>')
        
        # Join paragraphs
        html_content = '\n'.join(formatted_paragraphs)
        
        # If no paragraphs were created (single line), just convert line breaks
        if not formatted_paragraphs and html_text.strip():
            html_content = html_text.replace('\n', '<br>')
        
        return html_content
    
    def _run_applescript(self, script: str) -> str:
        """
        Run AppleScript and return the result.
        
        Args:
            script: AppleScript code to execute
            
        Returns:
            Script output
        """
        try:
            # Use NSAppleScript if available
            if SCRIPTING_BRIDGE_AVAILABLE:
                apple_script = NSAppleScript.alloc().initWithSource_(script)
                result, error = apple_script.executeAndReturnError_(None)
                
                if error:
                    raise OutlookIntegrationError(f"AppleScript error: {error}")
                
                if result:
                    return str(result.stringValue())
                return ""
            
            # Fallback to osascript command
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise OutlookIntegrationError(f"AppleScript failed: {result.stderr}")
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            raise OutlookIntegrationError("AppleScript execution timed out")
        except Exception as e:
            raise OutlookIntegrationError(f"Failed to run AppleScript: {e}")
    
    def send_email(self, customer: Customer, template: MessageTemplate) -> bool:
        """
        Send a single email using Outlook.
        
        Args:
            customer: Customer to send email to
            template: Email template to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure Outlook is running
            if not self.is_outlook_running():
                if not self.start_outlook():
                    raise OutlookIntegrationError("Cannot start Outlook")
            
            # Render template
            rendered = template.render(customer)
            subject = rendered.get('subject', '')
            content = rendered.get('content', '')
            
            # Format content for AppleScript
            formatted_content = self._format_plain_text(content)
            
            # Build AppleScript with proper line break handling
            script = self._build_email_script(subject, formatted_content, customer.email, send=True)
            
            self._run_applescript(script)
            logger.info(f"Email sent to {customer.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {customer.email}: {e}")
            return False
    
    def send_bulk_emails(
        self, 
        customers: List[Customer], 
        template: MessageTemplate,
        batch_size: int = 10,
        delay_between_emails: float = 1.0
    ) -> List[MessageRecord]:
        """
        Send bulk emails using Outlook.
        
        Args:
            customers: List of customers to send emails to
            template: Email template to use
            batch_size: Number of emails to send in each batch
            delay_between_emails: Delay between emails in seconds
            
        Returns:
            List of message records with sending results
        """
        records = []
        
        try:
            # Ensure Outlook is running
            if not self.is_outlook_running():
                if not self.start_outlook():
                    raise OutlookIntegrationError("Cannot start Outlook")
            
            logger.info(f"Starting bulk email send to {len(customers)} recipients")
            
            for i, customer in enumerate(customers):
                try:
                    # Create message record
                    record = MessageRecord(customer=customer, template=template)
                    record.status = MessageStatus.SENDING
                    
                    # Send email
                    success = self.send_email(customer, template)
                    
                    if success:
                        record.mark_as_sent()
                        logger.debug(f"Email {i+1}/{len(customers)} sent successfully to {customer.email}")
                    else:
                        record.mark_as_failed("Failed to send email")
                        logger.warning(f"Email {i+1}/{len(customers)} failed to {customer.email}")
                    
                    records.append(record)
                    
                    # Add delay between emails
                    if delay_between_emails > 0 and i < len(customers) - 1:
                        time.sleep(delay_between_emails)
                    
                    # Batch processing pause
                    if (i + 1) % batch_size == 0 and i < len(customers) - 1:
                        logger.info(f"Processed batch of {batch_size} emails, pausing...")
                        time.sleep(2.0)  # Longer pause between batches
                
                except Exception as e:
                    record = MessageRecord(customer=customer, template=template)
                    record.mark_as_failed(str(e))
                    records.append(record)
                    logger.error(f"Failed to process email for {customer.email}: {e}")
            
            successful = sum(1 for r in records if r.status == MessageStatus.SENT)
            failed = sum(1 for r in records if r.status == MessageStatus.FAILED)
            
            logger.info(f"Bulk email send completed: {successful} successful, {failed} failed")
            
        except Exception as e:
            logger.error(f"Bulk email send failed: {e}")
            # Mark remaining customers as failed
            for customer in customers[len(records):]:
                record = MessageRecord(customer=customer, template=template)
                record.mark_as_failed(f"Bulk send failed: {e}")
                records.append(record)
        
        return records
    
    def create_draft_email(self, customer: Customer, template: MessageTemplate) -> bool:
        """
        Create a draft email in Outlook.
        
        Args:
            customer: Customer for the email
            template: Email template to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure Outlook is running
            if not self.is_outlook_running():
                if not self.start_outlook():
                    raise OutlookIntegrationError("Cannot start Outlook")
            
            # Render template
            rendered = template.render(customer)
            subject = rendered.get('subject', '')
            content = rendered.get('content', '')
            
            # Format content for AppleScript
            formatted_content = self._format_plain_text(content)
            
            # Build AppleScript with proper line break handling
            script = self._build_email_script(subject, formatted_content, customer.email, send=False)
            
            self._run_applescript(script)
            logger.info(f"Draft email created for {customer.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create draft email for {customer.email}: {e}")
            return False
    
    def test_email_formatting(self, customer: Customer, template: MessageTemplate) -> str:
        """
        Test email formatting by generating the AppleScript without executing it.
        
        Args:
            customer: Customer for the email
            template: Email template to use
            
        Returns:
            Generated AppleScript code
        """
        # Render template
        rendered = template.render(customer)
        subject = rendered.get('subject', '')
        content = rendered.get('content', '')
        
        # Format content for AppleScript
        formatted_content = self._format_plain_text(content)
        
        # Build AppleScript
        script = self._build_email_script(subject, formatted_content, customer.email, send=False)
        
        logger.info(f"Generated AppleScript:\n{script}")
        return script
    
    def get_outlook_version(self) -> Optional[str]:
        """
        Get Outlook version information.
        
        Returns:
            Outlook version string or None if unavailable
        """
        try:
            script = '''
            tell application "Microsoft Outlook"
                return version
            end tell
            '''
            
            version = self._run_applescript(script)
            logger.info(f"Outlook version: {version}")
            return version
            
        except Exception as e:
            logger.warning(f"Failed to get Outlook version: {e}")
            return None
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test connection to Outlook.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if Outlook app exists
            outlook_path = Path("/Applications/Microsoft Outlook.app")
            if not outlook_path.exists():
                return False, "Microsoft Outlook is not installed"
            
            # Try to get version
            version = self.get_outlook_version()
            if version:
                return True, f"Connected to Outlook {version}"
            
            # Try to start Outlook
            if self.start_outlook():
                return True, "Connected to Outlook successfully"
            
            return False, "Cannot connect to Outlook"
            
        except Exception as e:
            return False, f"Connection test failed: {e}"
