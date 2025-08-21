"""
macOS Outlook integration using AppleScript and ScriptingBridge.
Enhanced with better error handling, permission management, and AppleScript optimization.
"""

import subprocess
import time
import threading
import tempfile
import os
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

try:
    from ScriptingBridge import SBApplication
    from Foundation import NSAppleScript, NSString, NSAppleEventDescriptor
    import objc

    SCRIPTING_BRIDGE_AVAILABLE = True
except ImportError:
    SCRIPTING_BRIDGE_AVAILABLE = False

from ..core.models import Customer, MessageTemplate, MessageRecord, MessageStatus
from ..utils.exceptions import OutlookIntegrationError, ServiceUnavailableError
from ..utils.logger import get_logger
from ..core.i18n_manager import get_i18n_manager

logger = get_logger(__name__)


class OutlookMacVersion(Enum):
    """Outlook for Mac version enumeration."""

    UNKNOWN = "unknown"
    OUTLOOK_2016 = "16.16"
    OUTLOOK_2019 = "16.17"
    OUTLOOK_2021 = "16.54"
    OUTLOOK_365 = "16.60"


class AppleScriptMethod(Enum):
    """AppleScript execution methods."""

    FOUNDATION = "foundation"
    OSASCRIPT = "osascript"
    SCRIPTING_BRIDGE = "scripting_bridge"


@dataclass
class MacOSPermissions:
    """macOS permissions status."""

    automation_permission: bool = False
    accessibility_permission: bool = False
    outlook_installed: bool = False
    scripting_bridge_available: bool = False


@dataclass
class OutlookMacCapabilities:
    """Outlook for Mac capabilities."""

    supports_html: bool = True
    supports_rtf: bool = True
    supports_attachments: bool = True
    supports_applescript: bool = True
    max_recipients: int = 500
    version: OutlookMacVersion = OutlookMacVersion.UNKNOWN


class OutlookMacOSService:
    """Enhanced macOS Outlook integration service."""

    def __init__(self):
        """Initialize macOS Outlook service with enhanced capabilities."""
        self.outlook_app = None
        self.i18n_manager = get_i18n_manager()

        # Enhanced AppleScript management
        self._preferred_method = AppleScriptMethod.FOUNDATION
        self._fallback_methods = [
            AppleScriptMethod.OSASCRIPT,
            AppleScriptMethod.SCRIPTING_BRIDGE,
        ]
        self._applescript_cache = {}

        # Permission and capability tracking
        self._permissions = MacOSPermissions()
        self._capabilities = OutlookMacCapabilities()
        self._outlook_version = OutlookMacVersion.UNKNOWN

        # Thread safety and connection management
        self._lock = threading.RLock()
        self._connection_attempts = 0
        self._max_connection_attempts = 3
        self._last_error = None

        # Email formatting preferences with enhanced fallbacks
        self.formatting_strategies = [
            "file_based_content",  # Most reliable
            "direct_applescript",  # Good for simple content
            "escaped_content",  # Fallback for complex content
            "minimal_content",  # Last resort
        ]

        self._check_outlook_availability()

    def _check_outlook_availability(self) -> None:
        """Check if Outlook is available on macOS with comprehensive validation."""
        try:
            # Check system permissions and capabilities
            self._check_system_permissions()

            # Detect Outlook installation
            self._detect_outlook_installation()

            # Detect Outlook version and capabilities
            self._detect_outlook_version()

            # Test AppleScript connectivity
            self._test_applescript_connectivity()

            logger.info(
                f"Outlook macOS service initialized - Version: {self._outlook_version.value}"
            )

        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Failed to initialize Outlook macOS service: {e}")
            raise ServiceUnavailableError(f"Outlook is not available: {e}")

    def _check_system_permissions(self) -> None:
        """Check macOS system permissions required for Outlook integration."""
        permissions = MacOSPermissions()

        # Check if ScriptingBridge is available
        permissions.scripting_bridge_available = SCRIPTING_BRIDGE_AVAILABLE

        # Check automation permission by testing a simple AppleScript
        try:
            test_script = """
            try
                tell application "System Events"
                    return "accessible"
                end tell
            on error errMsg
                return "error: " & errMsg
            end try
            """
            result = self._run_applescript_safe(test_script)
            permissions.automation_permission = "accessible" in result.lower()
        except Exception:
            permissions.automation_permission = False

        # Check Outlook-specific automation permission
        try:
            outlook_test_script = """
            try
                tell application "Microsoft Outlook"
                    return "outlook_accessible"
                end tell
            on error errMsg
                return "error: " & errMsg
            end try
            """
            result = self._run_applescript_safe(outlook_test_script)
            outlook_accessible = "outlook_accessible" in result.lower()

            if not outlook_accessible and "not authorized" in result.lower():
                logger.warning("Outlook automation permission not granted")
                permissions.automation_permission = False
        except Exception as e:
            logger.debug(f"Outlook permission test failed: {e}")

        self._permissions = permissions

        if not permissions.automation_permission:
            logger.warning(
                "Automation permissions may be required for full functionality"
            )

    def _detect_outlook_installation(self) -> None:
        """Detect Outlook installation and validate it."""
        outlook_paths = [
            Path("/Applications/Microsoft Outlook.app"),
            Path("/System/Applications/Microsoft Outlook.app"),
            Path(os.path.expanduser("~/Applications/Microsoft Outlook.app")),
        ]

        outlook_installed = False
        for outlook_path in outlook_paths:
            if outlook_path.exists():
                outlook_installed = True
                logger.debug(f"Found Outlook at: {outlook_path}")
                break

        if not outlook_installed:
            raise ServiceUnavailableError(
                self.i18n_manager.tr("outlook_macos_not_installed")
            )

        self._permissions.outlook_installed = True

    def _detect_outlook_version(self) -> None:
        """Detect Outlook version and set capabilities."""
        try:
            # Try to get version via AppleScript
            version_script = """
            try
                tell application "Microsoft Outlook"
                    return version
                end tell
            on error
                return "unknown"
            end try
            """

            version_result = self._run_applescript_safe(version_script)
            logger.info(f"Detected Outlook version: {version_result}")

            # Parse version string
            if "16.60" in version_result or "365" in version_result:
                self._outlook_version = OutlookMacVersion.OUTLOOK_365
            elif "16.54" in version_result:
                self._outlook_version = OutlookMacVersion.OUTLOOK_2021
            elif "16.17" in version_result or "16.1" in version_result:
                self._outlook_version = OutlookMacVersion.OUTLOOK_2019
            elif "16.16" in version_result:
                self._outlook_version = OutlookMacVersion.OUTLOOK_2016
            else:
                self._outlook_version = OutlookMacVersion.UNKNOWN

            # Set capabilities based on version
            self._set_version_capabilities()

        except Exception as e:
            logger.warning(f"Could not detect Outlook version: {e}")
            self._outlook_version = OutlookMacVersion.UNKNOWN
            self._set_default_capabilities()

    def _set_version_capabilities(self) -> None:
        """Set capabilities based on detected Outlook version."""
        capabilities = OutlookMacCapabilities()
        capabilities.version = self._outlook_version

        # All modern versions support basic features
        capabilities.supports_html = True
        capabilities.supports_rtf = True
        capabilities.supports_attachments = True
        capabilities.supports_applescript = True

        # Version-specific capabilities
        if self._outlook_version in [
            OutlookMacVersion.OUTLOOK_365,
            OutlookMacVersion.OUTLOOK_2021,
        ]:
            capabilities.max_recipients = 1000
        elif self._outlook_version == OutlookMacVersion.OUTLOOK_2019:
            capabilities.max_recipients = 500
        else:
            capabilities.max_recipients = 100

        self._capabilities = capabilities
        logger.debug(f"Outlook capabilities set: {capabilities}")

    def _set_default_capabilities(self) -> None:
        """Set default capabilities when version detection fails."""
        capabilities = OutlookMacCapabilities()
        capabilities.version = OutlookMacVersion.UNKNOWN
        capabilities.supports_html = True
        capabilities.supports_rtf = True
        capabilities.supports_attachments = True
        capabilities.supports_applescript = True
        capabilities.max_recipients = 100

        self._capabilities = capabilities

    def _test_applescript_connectivity(self) -> None:
        """Test AppleScript connectivity and determine best method."""
        methods_to_test = [AppleScriptMethod.FOUNDATION, AppleScriptMethod.OSASCRIPT]

        if SCRIPTING_BRIDGE_AVAILABLE:
            methods_to_test.append(AppleScriptMethod.SCRIPTING_BRIDGE)

        working_methods = []

        for method in methods_to_test:
            try:
                test_script = 'return "test"'
                result = self._run_applescript_with_method(test_script, method)
                if "test" in result.lower():
                    working_methods.append(method)
                    logger.debug(f"AppleScript method {method.value} is working")
            except Exception as e:
                logger.debug(f"AppleScript method {method.value} failed: {e}")

        if working_methods:
            self._preferred_method = working_methods[0]
            self._fallback_methods = working_methods[1:]
            logger.info(f"Using AppleScript method: {self._preferred_method.value}")
        else:
            raise ServiceUnavailableError("No working AppleScript methods available")

    def _run_applescript_safe(self, script: str) -> str:
        """
        Run AppleScript safely with error handling.

        Args:
            script: AppleScript code to execute

        Returns:
            Script output or error message
        """
        try:
            return self._run_applescript_with_method(script, self._preferred_method)
        except Exception as e:
            # Try fallback methods
            for method in self._fallback_methods:
                try:
                    return self._run_applescript_with_method(script, method)
                except Exception:
                    continue

            # If all methods fail, return error
            return f"error: {e}"

    def _run_applescript_with_method(
        self, script: str, method: AppleScriptMethod
    ) -> str:
        """
        Run AppleScript using specified method.

        Args:
            script: AppleScript code to execute
            method: Method to use for execution

        Returns:
            Script output
        """
        if method == AppleScriptMethod.FOUNDATION and SCRIPTING_BRIDGE_AVAILABLE:
            return self._run_applescript_foundation(script)
        elif method == AppleScriptMethod.OSASCRIPT:
            return self._run_applescript_osascript(script)
        elif (
            method == AppleScriptMethod.SCRIPTING_BRIDGE and SCRIPTING_BRIDGE_AVAILABLE
        ):
            return self._run_applescript_scripting_bridge(script)
        else:
            raise OutlookIntegrationError(
                f"AppleScript method {method.value} not available"
            )

    def _run_applescript_foundation(self, script: str) -> str:
        """Run AppleScript using Foundation NSAppleScript."""
        try:
            apple_script = NSAppleScript.alloc().initWithSource_(script)
            result, error = apple_script.executeAndReturnError_(None)

            if error:
                error_msg = str(error.get("NSAppleScriptErrorMessage", error))
                if "not authorized" in error_msg.lower():
                    raise OutlookIntegrationError(
                        self.i18n_manager.tr("outlook_macos_permission_denied")
                    )
                raise OutlookIntegrationError(f"AppleScript error: {error_msg}")

            if result:
                return str(result.stringValue())
            return ""

        except Exception as e:
            if "not authorized" in str(e).lower():
                raise OutlookIntegrationError(
                    self.i18n_manager.tr("outlook_macos_permission_denied")
                )
            raise OutlookIntegrationError(f"Foundation AppleScript failed: {e}")

    def _run_applescript_osascript(self, script: str) -> str:
        """Run AppleScript using osascript command."""
        try:
            result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True, timeout=30
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip()
                if "not authorized" in error_msg.lower():
                    raise OutlookIntegrationError(
                        self.i18n_manager.tr("outlook_macos_permission_denied")
                    )
                raise OutlookIntegrationError(f"osascript failed: {error_msg}")

            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            raise OutlookIntegrationError("AppleScript execution timed out")
        except Exception as e:
            raise OutlookIntegrationError(f"osascript execution failed: {e}")

    def _run_applescript_scripting_bridge(self, script: str) -> str:
        """Run AppleScript using ScriptingBridge (limited functionality)."""
        try:
            if not self.outlook_app:
                self.outlook_app = SBApplication.applicationWithBundleIdentifier_(
                    "com.microsoft.Outlook"
                )

            # ScriptingBridge has limited script execution capabilities
            # This is mainly for basic operations
            if "return true" in script or "return false" in script:
                try:
                    # Test if Outlook responds
                    _ = self.outlook_app.isRunning()
                    return "true"
                except:
                    return "false"

            # For other scripts, fall back to osascript
            return self._run_applescript_osascript(script)

        except Exception as e:
            raise OutlookIntegrationError(f"ScriptingBridge execution failed: {e}")

    def is_outlook_running(self) -> bool:
        """
        Check if Outlook is currently running with enhanced detection.

        Returns:
            True if Outlook is running, False otherwise
        """
        with self._lock:
            try:
                # Method 1: Direct Outlook AppleScript (most reliable)
                script = """
                try
                    tell application "Microsoft Outlook"
                        return "running"
                    end tell
                on error
                    return "not_running"
                end try
                """

                result = self._run_applescript_safe(script)
                if "running" in result.lower():
                    return True

                # Method 2: Process check (no permissions needed)
                try:
                    result = subprocess.run(
                        ["pgrep", "-f", "Microsoft Outlook"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if result.returncode == 0:
                        return True
                except Exception as e:
                    logger.debug(f"Process check failed: {e}")

                # Method 3: ScriptingBridge check (if available)
                if SCRIPTING_BRIDGE_AVAILABLE and self.outlook_app:
                    try:
                        return bool(self.outlook_app.isRunning())
                    except Exception as e:
                        logger.debug(f"ScriptingBridge check failed: {e}")

                return False

            except Exception as e:
                logger.warning(f"Failed to check if Outlook is running: {e}")
                # Try one more fallback using ps command
                try:
                    result = subprocess.run(
                        ["ps", "aux"], capture_output=True, text=True, timeout=5
                    )
                    return "Microsoft Outlook" in result.stdout
                except Exception:
                    return False

    def start_outlook(self) -> bool:
        """
        Start Outlook application with enhanced initialization and error handling.

        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                if self.is_outlook_running():
                    logger.info("Outlook is already running")
                    return True

                logger.info("Starting Outlook application...")
                self._connection_attempts += 1

                # Check permissions before attempting to start
                if not self._permissions.automation_permission:
                    logger.warning("Automation permissions may not be granted")

                # Start Outlook using AppleScript with enhanced error handling
                start_script = """
                try
                    tell application "Microsoft Outlook"
                        activate
                        return "started"
                    end tell
                on error errMsg number errNum
                    return "error: " & errMsg & " (" & errNum & ")"
                end try
                """

                result = self._run_applescript_safe(start_script)

                if "error:" in result.lower():
                    if "not authorized" in result.lower() or "-1743" in result:
                        raise OutlookIntegrationError(
                            self.i18n_manager.tr("outlook_macos_permission_denied")
                        )
                    else:
                        raise OutlookIntegrationError(
                            f"Failed to start Outlook: {result}"
                        )

                # Wait for Outlook to fully initialize with progress tracking
                max_wait = 45  # Increased timeout for slower systems
                wait_time = 0
                check_interval = 1

                logger.debug("Waiting for Outlook to initialize...")

                while wait_time < max_wait:
                    if self.is_outlook_running():
                        # Additional check to ensure Outlook is fully ready
                        ready_script = """
                        try
                            tell application "Microsoft Outlook"
                                return "ready"
                            end tell
                        on error
                            return "not_ready"
                        end try
                        """

                        ready_result = self._run_applescript_safe(ready_script)
                        if "ready" in ready_result.lower():
                            logger.info(
                                f"Outlook started successfully after {wait_time} seconds"
                            )
                            self._connection_attempts = 0  # Reset on success
                            return True

                    time.sleep(check_interval)
                    wait_time += check_interval

                    # Log progress for long waits
                    if wait_time % 10 == 0:
                        logger.debug(f"Still waiting for Outlook... ({wait_time}s)")

                logger.error(f"Timeout waiting for Outlook to start ({max_wait}s)")
                return False

            except OutlookIntegrationError as e:
                self._last_error = str(e)
                if "not authorized" in str(e).lower() or "permission" in str(e).lower():
                    logger.error(
                        "Permission denied: CSC-Reach needs automation permissions"
                    )
                    logger.error(
                        "Please grant automation permissions in System Preferences > Privacy & Security > Automation"
                    )
                    logger.error(
                        "See docs/user/macos_permissions_guide.md for detailed instructions"
                    )
                else:
                    logger.error(f"Failed to start Outlook: {e}")
                return False

            except Exception as e:
                self._last_error = str(e)
                logger.error(f"Unexpected error starting Outlook: {e}")
                return False

    def restart_outlook_connection(self) -> bool:
        """
        Restart Outlook connection (useful for recovery from errors).

        Returns:
            True if successful, False otherwise
        """
        logger.info("Restarting Outlook connection...")

        with self._lock:
            try:
                # Reset connection state
                self._connection_attempts = 0
                self._last_error = None

                # Clear any cached AppleScript objects
                self._applescript_cache.clear()

                # Re-check permissions and capabilities
                self._check_system_permissions()

                # Attempt to restart
                return self.start_outlook()

            except Exception as e:
                logger.error(f"Failed to restart Outlook connection: {e}")
                return False

    def check_permissions(self) -> Tuple[bool, List[str]]:
        """
        Check if CSC-Reach has the necessary permissions to work with Outlook.
        Enhanced with comprehensive permission checking.

        Returns:
            Tuple of (has_permissions, list_of_issues)
        """
        issues = []

        # Check Outlook installation
        if not self._permissions.outlook_installed:
            issues.append(self.i18n_manager.tr("outlook_macos_not_installed"))

        # Check automation permissions
        if not self._permissions.automation_permission:
            issues.append(
                self.i18n_manager.tr("outlook_macos_automation_permission_required")
            )

        # Check ScriptingBridge availability
        if not self._permissions.scripting_bridge_available:
            issues.append(
                "ScriptingBridge not available - install pyobjc-framework-ScriptingBridge"
            )

        # Test actual Outlook access
        try:
            test_script = """
            try
                tell application "Microsoft Outlook"
                    return "accessible"
                end tell
            on error errMsg number errNum
                return "error: " & errMsg & " (" & errNum & ")"
            end try
            """
            result = self._run_applescript_safe(test_script)

            if "error:" in result.lower():
                if "not authorized" in result.lower() or "-1743" in result:
                    issues.append(
                        self.i18n_manager.tr("outlook_macos_permission_denied")
                    )
                else:
                    issues.append(f"Outlook access test failed: {result}")

        except Exception as e:
            issues.append(f"Cannot test Outlook access: {e}")

        return len(issues) == 0, issues

    def get_permissions_status(self) -> MacOSPermissions:
        """
        Get detailed permissions status.

        Returns:
            MacOSPermissions object with current status
        """
        return self._permissions

    def get_outlook_capabilities(self) -> OutlookMacCapabilities:
        """
        Get Outlook capabilities and features.

        Returns:
            OutlookMacCapabilities object
        """
        return self._capabilities

    def get_connection_health(self) -> Dict[str, Any]:
        """
        Get detailed connection health information.

        Returns:
            Dictionary with connection health details
        """
        health = {
            "is_connected": False,
            "outlook_version": self._outlook_version.value,
            "connection_attempts": self._connection_attempts,
            "last_error": self._last_error,
            "permissions": {
                "automation_permission": self._permissions.automation_permission,
                "outlook_installed": self._permissions.outlook_installed,
                "scripting_bridge_available": self._permissions.scripting_bridge_available,
            },
            "capabilities": {
                "supports_html": self._capabilities.supports_html,
                "supports_rtf": self._capabilities.supports_rtf,
                "supports_attachments": self._capabilities.supports_attachments,
                "max_recipients": self._capabilities.max_recipients,
            },
            "applescript_method": self._preferred_method.value,
            "fallback_methods": [method.value for method in self._fallback_methods],
        }

        try:
            health["is_connected"] = self.is_outlook_running()
        except Exception as e:
            health["connection_error"] = str(e)

        return health

    def _format_plain_text(self, text: str) -> str:
        """
        Format plain text - now just normalizes line endings without modification.

        Args:
            text: Plain text content

        Returns:
            Text with normalized line endings
        """
        if not text:
            return ""

        # Just normalize line endings to \n - don't modify them
        # The AppleScript builder will handle line breaks properly
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")

        logger.debug(
            f"Formatted plain text: {len(text)} chars, {text.count(chr(10))} line breaks"
        )

        return normalized

    def _build_email_script(
        self, subject: str, content: str, email: str, send: bool = True
    ) -> str:
        """
        Build AppleScript for creating/sending email with proper line break handling.

        Uses multiple approaches with fallbacks following development guide principles.

        Args:
            subject: Email subject
            content: Email content with line breaks
            email: Recipient email address
            send: Whether to send the email or just create draft

        Returns:
            AppleScript code

        Raises:
            OutlookIntegrationError: If all approaches fail
        """
        logger.info(
            f"Building email script for {email}, content length: {len(content)}"
        )

        # Try file-based approach first (most reliable)
        try:
            logger.debug("Attempting file-based content approach")
            return self._build_file_based_email_script(subject, content, email, send)
        except Exception as e:
            logger.warning(f"File-based approach failed: {e}")

        # Try simple text approach as fallback
        try:
            logger.debug("Falling back to simple text approach")
            return self._build_simple_text_email_script(subject, content, email, send)
        except Exception as e:
            logger.error(f"Simple text approach failed: {e}")
            raise OutlookIntegrationError("All email formatting approaches failed")

    def _build_plain_text_email_script(
        self, subject: str, content: str, email: str, send: bool = True
    ) -> str:
        """
        Build AppleScript for plain text email with proper line breaks.

        Uses actual line break characters in the string instead of AppleScript return concatenation.

        Args:
            subject: Email subject
            content: Email content with line breaks
            email: Recipient email address
            send: Whether to send the email or just create draft

        Returns:
            AppleScript code for plain text email
        """
        # Escape basic characters for AppleScript strings
        subject_escaped = self._escape_for_applescript_safe(subject)
        email_escaped = self._escape_for_applescript_safe(email)

        # Convert line breaks to the format Outlook expects
        # Try using \r (carriage return) which is what AppleScript/Mac typically uses
        content_with_breaks = content.replace("\n", "\r")
        content_escaped = self._escape_for_applescript_safe(content_with_breaks)

        # Build the complete AppleScript with direct string content
        action = "send newMessage" if send else "open newMessage"

        script = f"""tell application "Microsoft Outlook"
    set newMessage to make new outgoing message
    set subject of newMessage to "{subject_escaped}"
    set content of newMessage to "{content_escaped}"
    make new recipient at newMessage with properties {{email address:{{address:"{email_escaped}"}}}}
    {action}
end tell"""

        logger.debug(f"Generated plain text email AppleScript with direct line breaks")
        return script

    def _escape_for_applescript_safe(self, text: str) -> str:
        """
        Ultra-safe AppleScript escaping that preserves line breaks correctly.

        Args:
            text: Text to escape

        Returns:
            Safely escaped text for AppleScript with proper line break handling
        """
        if not text:
            return ""

        # Start with the original text
        escaped = text

        # Escape backslashes first (but be careful with line breaks)
        escaped = escaped.replace("\\", "\\\\")

        # Escape quotes
        escaped = escaped.replace('"', '\\"')

        # Handle line breaks properly for AppleScript
        # Convert \r to \\r so AppleScript interprets it as a carriage return character
        escaped = escaped.replace("\r", "\\r")

        # Remove tabs and replace with spaces
        escaped = escaped.replace("\t", " ")

        # Remove null characters
        escaped = escaped.replace("\x00", "")

        # Remove other problematic control characters but keep \r for line breaks
        escaped = "".join(
            char for char in escaped if ord(char) >= 32 or char in ["\r", "\\"]
        )

        logger.debug(
            f"AppleScript escaping: {len(text)} chars -> {len(escaped)} chars, line breaks: {text.count(chr(13))}"
        )

        return escaped

    def _build_html_email_script(
        self, subject: str, content: str, email: str, send: bool = True
    ) -> str:
        """
        Build AppleScript for HTML email with proper formatting.

        Args:
            subject: Email subject
            content: Email content with line breaks
            email: Recipient email address
            send: Whether to send the email or just create draft

        Returns:
            AppleScript code for HTML email
        """
        # Escape basic characters for AppleScript strings
        subject_escaped = self._escape_for_applescript_simple(subject)
        email_escaped = self._escape_for_applescript_simple(email)

        # Convert plain text to HTML to preserve formatting
        html_content = self._convert_text_to_html(content)
        html_escaped = self._escape_for_applescript_simple(html_content)

        # Build the complete AppleScript using HTML content
        action = "send newMessage" if send else "open newMessage"

        script = f"""
        tell application "Microsoft Outlook"
            set newMessage to make new outgoing message
            set subject of newMessage to "{subject_escaped}"
            set content of newMessage to "{html_escaped}"
            set format of newMessage to HTML format
            make new recipient at newMessage with properties {{email address:{{address:"{email_escaped}"}}}}
            {action}
        end tell
        """

        logger.debug(f"Generated HTML email AppleScript")
        return script

    def _build_file_based_email_script(
        self, subject: str, content: str, email: str, send: bool = True
    ) -> str:
        """
        Build AppleScript using temporary file for content transfer.

        This approach writes content to a temporary file and uses AppleScript
        to read it, avoiding string escaping issues entirely.

        Args:
            subject: Email subject
            content: Email content with line breaks
            email: Recipient email address
            send: Whether to send the email or just create draft

        Returns:
            AppleScript code using file-based content
        """
        import tempfile

        # Create temporary file with content
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_file_path = f.name

        # Escape for AppleScript
        subject_escaped = self._escape_for_applescript_ultra_safe(subject)
        email_escaped = self._escape_for_applescript_ultra_safe(email)
        file_path_escaped = temp_file_path.replace("\\", "\\\\").replace('"', '\\"')

        action = "send newMessage" if send else "open newMessage"

        script = f'''tell application "Microsoft Outlook"
    set contentFile to POSIX file "{file_path_escaped}"
    set fileContent to read contentFile as «class utf8»
    set newMessage to make new outgoing message
    set subject of newMessage to "{subject_escaped}"
    set content of newMessage to fileContent
    make new recipient at newMessage with properties {{email address:{{address:"{email_escaped}"}}}}
    {action}
end tell

-- Clean up temporary file
do shell script "rm '{file_path_escaped}'"'''

        logger.debug(
            f"Generated file-based email AppleScript using temp file: {temp_file_path}"
        )
        return script

    def _build_simple_text_email_script(
        self, subject: str, content: str, email: str, send: bool = True
    ) -> str:
        """
        Build AppleScript using the simplest possible approach.

        This is the fallback method that uses minimal escaping and
        relies on AppleScript's basic text handling.

        Args:
            subject: Email subject
            content: Email content with line breaks
            email: Recipient email address
            send: Whether to send the email or just create draft

        Returns:
            AppleScript code for simple text email
        """
        # Ultra-minimal escaping - replace quotes with single quotes
        subject_clean = subject.replace('"', "'").replace("\\", "")
        email_clean = email.replace('"', "'").replace("\\", "")
        content_clean = content.replace('"', "'").replace("\\", "")

        # Replace line breaks with AppleScript line break constant
        content_clean = content_clean.replace("\n", '" & linefeed & "')

        action = "send newMessage" if send else "open newMessage"

        script = f"""tell application "Microsoft Outlook"
    set newMessage to make new outgoing message
    set subject of newMessage to "{subject_clean}"
    set content of newMessage to "{content_clean}"
    make new recipient at newMessage with properties {{email address:{{address:"{email_clean}"}}}}
    {action}
end tell"""

        logger.debug("Generated simple text email AppleScript")
        return script

    def _escape_for_applescript_ultra_safe(self, text: str) -> str:
        """
        Ultra-safe AppleScript escaping following development guide error handling.

        Args:
            text: Text to escape

        Returns:
            Safely escaped text for AppleScript

        Raises:
            ValueError: If text contains characters that cannot be safely escaped
        """
        if not text:
            return ""

        try:
            # Remove or replace problematic characters
            safe_text = text

            # Replace quotes with single quotes to avoid escaping issues
            safe_text = safe_text.replace('"', "'")

            # Remove backslashes entirely
            safe_text = safe_text.replace("\\", "")

            # Remove control characters except line breaks
            safe_text = "".join(
                char for char in safe_text if ord(char) >= 32 or char in ["\n", "\r"]
            )

            # Limit length to prevent AppleScript issues
            if len(safe_text) > 10000:
                safe_text = safe_text[:10000] + "..."
                logger.warning("Text truncated to prevent AppleScript issues")

            logger.debug(f"Ultra-safe escaping: {len(text)} -> {len(safe_text)} chars")
            return safe_text

        except Exception as e:
            logger.error(f"Failed to escape text for AppleScript: {e}")
            raise ValueError(f"Cannot safely escape text for AppleScript: {e}")

    # Update the main _build_email_script method to use new approaches
    def _build_email_script_new(
        self, subject: str, content: str, email: str, send: bool = True
    ) -> str:
        """
        Build AppleScript using new approaches with fallbacks.

        Args:
            subject: Email subject
            content: Email content with line breaks
            email: Recipient email address
            send: Whether to send the email or just create draft

        Returns:
            AppleScript code
        """
        self.logger.info(
            f"Building email script for {email}, content length: {len(content)}"
        )

        # Try file-based approach first (most reliable)
        try:
            self.logger.debug("Attempting file-based content approach")
            return self._build_file_based_email_script(subject, content, email, send)
        except Exception as e:
            self.logger.warning(f"File-based approach failed: {e}")

        # Try simple text approach as fallback
        try:
            self.logger.debug("Falling back to simple text approach")
            return self._build_simple_text_email_script(subject, content, email, send)
        except Exception as e:
            self.logger.error(f"Simple text approach failed: {e}")
            raise OutlookIntegrationError("All email formatting approaches failed")
        """
        Convert plain text to HTML, preserving line breaks and formatting.
        
        Args:
            text: Plain text content
            
        Returns:
            HTML formatted content
        """
        if not text:
            return ""

        # Escape HTML special characters
        html = text.replace("&", "&amp;")
        html = html.replace("<", "&lt;")
        html = html.replace(">", "&gt;")

        # Convert line breaks to HTML
        # Double line breaks become paragraph breaks
        html = html.replace("\n\n", "</p><p>")

        # Single line breaks become <br> tags
        html = html.replace("\n", "<br>")

        # Wrap in paragraph tags
        html = f"<p>{html}</p>"

        # Clean up empty paragraphs
        html = html.replace("<p></p>", "")
        html = html.replace("<p><br></p>", "<p>&nbsp;</p>")

        logger.debug(f"Converted text to HTML: {len(text)} chars -> {len(html)} chars")

        return html

    def _escape_for_applescript_simple(self, text: str) -> str:
        """
        Simple AppleScript escaping - now uses the safer version.

        Args:
            text: Text to escape

        Returns:
            Escaped text safe for AppleScript
        """
        return self._escape_for_applescript_safe(text)

    def _build_html_email_script(
        self, subject: str, content: str, email: str, send: bool = True
    ) -> str:
        """
        Build AppleScript for HTML email with proper formatting.

        Args:
            subject: Email subject
            content: Email content with line breaks
            email: Recipient email address
            send: Whether to send the email or just create draft

        Returns:
            AppleScript code for HTML email
        """
        # Escape basic characters for AppleScript strings
        subject_escaped = self._escape_for_applescript_simple(subject)
        email_escaped = self._escape_for_applescript_simple(email)

        # Convert plain text to HTML to preserve formatting
        html_content = self._convert_text_to_html(content)

        # For HTML content, we need extra careful escaping
        html_escaped = self._escape_html_for_applescript(html_content)

        # Build the complete AppleScript using HTML content
        action = "send newMessage" if send else "open newMessage"

        # Use a more robust AppleScript structure
        script = f"""tell application "Microsoft Outlook"
    set newMessage to make new outgoing message
    set subject of newMessage to "{subject_escaped}"
    set content of newMessage to "{html_escaped}"
    set format of newMessage to HTML format
    make new recipient at newMessage with properties {{email address:{{address:"{email_escaped}"}}}}
    {action}
end tell"""

        logger.debug(f"Generated HTML email AppleScript")
        return script

    def _escape_html_for_applescript(self, html_content: str) -> str:
        """
        Special escaping for HTML content in AppleScript.

        HTML content has additional characters that need careful handling.

        Args:
            html_content: HTML content to escape

        Returns:
            HTML content safely escaped for AppleScript
        """
        if not html_content:
            return ""

        # Start with basic escaping
        escaped = self._escape_for_applescript_simple(html_content)

        # Additional HTML-specific escaping
        # Handle angle brackets that might confuse AppleScript
        escaped = escaped.replace("<", "\\<")
        escaped = escaped.replace(">", "\\>")

        # Handle ampersands in HTML entities
        escaped = escaped.replace("&", "\\&")

        logger.debug(
            f"HTML AppleScript escaping: {len(html_content)} chars -> {len(escaped)} chars"
        )

        return escaped

    def _escape_for_applescript(self, text: str) -> str:
        """
        Legacy method - now uses simple escaping.

        Args:
            text: Text to escape

        Returns:
            Escaped text safe for AppleScript
        """
        return self._escape_for_applescript_simple(text)
        # Escape tabs
        escaped = escaped.replace("\t", "\\t")

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
        html_text = (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )

        # Convert line breaks to HTML
        # First, normalize line endings
        html_text = html_text.replace("\r\n", "\n").replace("\r", "\n")

        # Split into paragraphs (double line breaks)
        paragraphs = html_text.split("\n\n")

        # Process each paragraph
        formatted_paragraphs = []
        for paragraph in paragraphs:
            if paragraph.strip():
                # Convert single line breaks within paragraphs to <br>
                formatted_paragraph = paragraph.replace("\n", "<br>")
                formatted_paragraphs.append(f"<p>{formatted_paragraph}</p>")

        # Join paragraphs
        html_content = "\n".join(formatted_paragraphs)

        # If no paragraphs were created (single line), just convert line breaks
        if not formatted_paragraphs and html_text.strip():
            html_content = html_text.replace("\n", "<br>")

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
                ["osascript", "-e", script], capture_output=True, text=True, timeout=30
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
            # Check permissions first
            has_permissions, issues = self.check_permissions()
            if not has_permissions:
                for issue in issues:
                    logger.error(f"Permission issue: {issue}")
                if "automation permission" in str(issues):
                    logger.error(
                        "Please grant automation permissions in System Preferences"
                    )
                    logger.error("See docs/user/macos_permissions_guide.md for help")
                raise OutlookIntegrationError("Missing required permissions")

            # Ensure Outlook is running
            if not self.is_outlook_running():
                if not self.start_outlook():
                    raise OutlookIntegrationError("Cannot start Outlook")

            # Render template
            rendered = template.render(customer)
            subject = rendered.get("subject", "")
            content = rendered.get("content", "")

            # Format content for AppleScript
            formatted_content = self._format_plain_text(content)

            # Build AppleScript with proper line break handling
            script = self._build_email_script(
                subject, formatted_content, customer.email, send=True
            )

            self._run_applescript(script)
            logger.info(f"Email sent to {customer.email}")
            return True

        except OutlookIntegrationError as e:
            logger.error(f"Failed to send email to {customer.email}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email to {customer.email}: {e}")
            return False

    def send_bulk_emails(
        self,
        customers: List[Customer],
        template: MessageTemplate,
        batch_size: int = 10,
        delay_between_emails: float = 1.0,
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
                        logger.debug(
                            f"Email {i+1}/{len(customers)} sent successfully to {customer.email}"
                        )
                    else:
                        record.mark_as_failed("Failed to send email")
                        logger.warning(
                            f"Email {i+1}/{len(customers)} failed to {customer.email}"
                        )

                    records.append(record)

                    # Add delay between emails
                    if delay_between_emails > 0 and i < len(customers) - 1:
                        time.sleep(delay_between_emails)

                    # Batch processing pause
                    if (i + 1) % batch_size == 0 and i < len(customers) - 1:
                        logger.info(
                            f"Processed batch of {batch_size} emails, pausing..."
                        )
                        time.sleep(2.0)  # Longer pause between batches

                except Exception as e:
                    record = MessageRecord(customer=customer, template=template)
                    record.mark_as_failed(str(e))
                    records.append(record)
                    logger.error(f"Failed to process email for {customer.email}: {e}")

            successful = sum(1 for r in records if r.status == MessageStatus.SENT)
            failed = sum(1 for r in records if r.status == MessageStatus.FAILED)

            logger.info(
                f"Bulk email send completed: {successful} successful, {failed} failed"
            )

        except Exception as e:
            logger.error(f"Bulk email send failed: {e}")
            # Mark remaining customers as failed
            for customer in customers[len(records) :]:
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
            subject = rendered.get("subject", "")
            content = rendered.get("content", "")

            # Format content for AppleScript
            formatted_content = self._format_plain_text(content)

            # Build AppleScript with proper line break handling
            script = self._build_email_script(
                subject, formatted_content, customer.email, send=False
            )

            self._run_applescript(script)
            logger.info(f"Draft email created for {customer.email}")
            return True

        except Exception as e:
            logger.error(f"Failed to create draft email for {customer.email}: {e}")
            return False

    def test_email_formatting(
        self, customer: Customer, template: MessageTemplate
    ) -> str:
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
        subject = rendered.get("subject", "")
        content = rendered.get("content", "")

        # Format content for AppleScript
        formatted_content = self._format_plain_text(content)

        # Build AppleScript
        script = self._build_email_script(
            subject, formatted_content, customer.email, send=False
        )

        logger.info(f"Generated AppleScript:\n{script}")
        return script

    def get_outlook_version(self) -> Optional[str]:
        """
        Get Outlook version information.

        Returns:
            Outlook version string or None if unavailable
        """
        try:
            script = """
            tell application "Microsoft Outlook"
                return version
            end tell
            """

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
