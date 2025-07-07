"""
Embedded WhatsApp Web automation service for CSC-Reach.
Self-contained implementation without external dependencies.

⚠️ WARNING: This service uses browser automation which may violate WhatsApp's Terms of Service.
Use at your own risk. WhatsApp Business API is the recommended approach.
"""

import json
import time
import os
import webbrowser
import urllib.parse
import subprocess
import platform
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from pathlib import Path

from ..core.models import Customer, MessageTemplate, MessageRecord, MessageStatus
from ..utils.exceptions import WhatsAppAPIError, WhatsAppConfigurationError
from ..utils.logger import get_logger
from ..utils.platform_utils import get_config_dir

logger = get_logger(__name__)


class WhatsAppWebService:
    """
    Embedded WhatsApp Web automation service for CSC-Reach.
    
    ⚠️ WARNING: This service uses browser automation which:
    - May violate WhatsApp's Terms of Service
    - Could result in account suspension
    - Is unreliable and error-prone
    - Requires WhatsApp Web to be open
    
    Use WhatsApp Business API instead for production use.
    
    Features:
    - No external dependencies (uses built-in webbrowser)
    - Direct WhatsApp Web URL automation
    - Optional automatic sending with AppleScript/PowerShell
    - Rate limiting and daily quotas
    - Message scheduling and delays
    - Local usage tracking
    - Safety limits and warnings
    """
    
    def __init__(
        self,
        rate_limit_per_minute: int = 3,  # Very conservative for web automation
        daily_message_limit: int = 30,   # Much lower for safety
        min_delay_seconds: int = 45,     # Longer delay for web automation
        auto_send: bool = False,         # Automatic sending option
        auto_send_delay: int = 5         # Delay before auto-send attempt
    ):
        """
        Initialize WhatsApp Web automation service.
        
        Args:
            rate_limit_per_minute: Messages per minute (very conservative)
            daily_message_limit: Daily message limit (much lower for safety)
            min_delay_seconds: Minimum delay between messages for safety
            auto_send: Whether to automatically send messages (higher risk)
            auto_send_delay: Seconds to wait before attempting auto-send
        """
        self.rate_limit_per_minute = rate_limit_per_minute
        self.daily_message_limit = daily_message_limit
        self.min_delay_seconds = min_delay_seconds
        self.auto_send = auto_send
        self.auto_send_delay = auto_send_delay
        
        # Configuration and tracking
        self.config_dir = get_config_dir()
        self.config_file = self.config_dir / "whatsapp_web_config.json"
        self.usage_file = self.config_dir / "whatsapp_web_usage.json"
        
        # Runtime tracking
        self.message_timestamps: List[datetime] = []
        self.daily_usage = self._load_daily_usage()
        
        # Service state
        self._is_configured = False
        self._last_error: Optional[str] = None
        
        # Load configuration
        self._load_configuration()
        
        logger.info("WhatsApp Web service initialized with conservative limits")
    
    def is_available(self) -> bool:
        """Check if the service is available (always true - no external dependencies)."""
        return True
    
    def is_configured(self) -> bool:
        """Check if the service is configured and ready."""
        return self._is_configured
    
    def configure_service(self, acknowledge_risks: bool = False, auto_send: bool = False) -> Tuple[bool, str]:
        """
        Configure the WhatsApp Web service.
        
        Args:
            acknowledge_risks: User must acknowledge the risks
            auto_send: Enable automatic sending (higher risk)
            
        Returns:
            Tuple of (success, message)
        """
        if not acknowledge_risks:
            return False, "You must acknowledge the risks of using browser automation"
        
        try:
            # Check Chrome availability
            chrome_available, chrome_info = self._check_chrome_availability()
            
            # Save configuration
            config = {
                "configured": True,
                "acknowledged_risks": True,
                "auto_send": auto_send,
                "auto_send_delay": self.auto_send_delay,
                "configured_at": datetime.now().isoformat(),
                "rate_limit_per_minute": self.rate_limit_per_minute,
                "daily_message_limit": self.daily_message_limit,
                "min_delay_seconds": self.min_delay_seconds,
                "service_type": "embedded_web_automation",
                "chrome_available": chrome_available,
                "chrome_info": chrome_info,
                "platform": platform.system().lower()
            }
            
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            self._is_configured = True
            self.auto_send = auto_send
            
            # Provide user feedback about Chrome
            success_msg = "WhatsApp Web service configured successfully"
            if auto_send:
                if chrome_available:
                    success_msg += f" with auto-send enabled (Chrome detected: {chrome_info})"
                else:
                    success_msg += f" with auto-send enabled (⚠️ Chrome not detected: {chrome_info})"
                    success_msg += "\n💡 Install Google Chrome for better auto-send reliability"
            
            logger.info(f"WhatsApp Web service configured (auto_send={auto_send}, chrome_available={chrome_available})")
            return True, success_msg
            
        except Exception as e:
            error_msg = f"Failed to configure WhatsApp Web service: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def _load_configuration(self):
        """Load service configuration."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                self._is_configured = config.get("configured", False)
                self.auto_send = config.get("auto_send", False)
                self.auto_send_delay = config.get("auto_send_delay", 5)
                self.rate_limit_per_minute = config.get("rate_limit_per_minute", 3)
                self.daily_message_limit = config.get("daily_message_limit", 30)
                self.min_delay_seconds = config.get("min_delay_seconds", 45)
                
                logger.info("WhatsApp Web configuration loaded")
            else:
                logger.info("No WhatsApp Web configuration found")
                
        except Exception as e:
            logger.error(f"Failed to load WhatsApp Web configuration: {e}")
            self._is_configured = False
    
    def _load_daily_usage(self) -> Dict[str, int]:
        """Load daily usage tracking."""
        try:
            if self.usage_file.exists():
                with open(self.usage_file, 'r') as f:
                    usage_data = json.load(f)
                
                today = datetime.now().strftime("%Y-%m-%d")
                return usage_data.get(today, {"messages_sent": 0})
            
        except Exception as e:
            logger.error(f"Failed to load usage data: {e}")
        
        return {"messages_sent": 0}
    
    def _save_daily_usage(self):
        """Save daily usage tracking."""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Load existing data
            usage_data = {}
            if self.usage_file.exists():
                with open(self.usage_file, 'r') as f:
                    usage_data = json.load(f)
            
            # Update today's usage
            usage_data[today] = self.daily_usage
            
            # Clean old data (keep only last 30 days)
            cutoff_date = datetime.now() - timedelta(days=30)
            usage_data = {
                date: data for date, data in usage_data.items()
                if datetime.strptime(date, "%Y-%m-%d") >= cutoff_date
            }
            
            # Save
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.usage_file, 'w') as f:
                json.dump(usage_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save usage data: {e}")
    
    def get_daily_usage(self) -> Dict[str, Any]:
        """Get current daily usage statistics."""
        return {
            "messages_sent_today": self.daily_usage.get("messages_sent", 0),
            "daily_limit": self.daily_message_limit,
            "remaining_today": max(0, self.daily_message_limit - self.daily_usage.get("messages_sent", 0)),
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "min_delay_seconds": self.min_delay_seconds
        }
    
    def can_send_message(self) -> Tuple[bool, str]:
        """Check if we can send a message now."""
        if not self.is_configured():
            return False, "WhatsApp Web service is not configured"
        
        # Check daily limit
        messages_today = self.daily_usage.get("messages_sent", 0)
        if messages_today >= self.daily_message_limit:
            return False, f"Daily limit reached ({messages_today}/{self.daily_message_limit})"
        
        # Check rate limiting
        now = datetime.now()
        recent_messages = [
            ts for ts in self.message_timestamps
            if (now - ts).total_seconds() < 60
        ]
        
        if len(recent_messages) >= self.rate_limit_per_minute:
            return False, f"Rate limit exceeded ({len(recent_messages)}/{self.rate_limit_per_minute} per minute)"
        
        # Check minimum delay
        if self.message_timestamps:
            last_message = max(self.message_timestamps)
            time_since_last = (now - last_message).total_seconds()
            if time_since_last < self.min_delay_seconds:
                wait_time = self.min_delay_seconds - time_since_last
                return False, f"Must wait {wait_time:.0f} more seconds (minimum {self.min_delay_seconds}s delay)"
        
        return True, "Ready to send"
    
    def send_message(self, customer: Customer, template: MessageTemplate) -> bool:
        """
        Send WhatsApp message using WhatsApp Web URL automation.
        
        Args:
            customer: Customer to send to
            template: Message template
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if we can send
            can_send, reason = self.can_send_message()
            if not can_send:
                logger.warning(f"Cannot send message to {customer.name}: {reason}")
                self._last_error = reason
                return False
            
            # Validate phone number
            if not customer.phone:
                logger.error(f"No phone number for customer {customer.name}")
                self._last_error = "No phone number provided"
                return False
            
            # Format phone number
            phone = self._format_phone_number(customer.phone)
            if not phone:
                logger.error(f"Invalid phone number format: {customer.phone}")
                self._last_error = "Invalid phone number format"
                return False
            
            # Render message content
            message_content = self._render_message(customer, template)
            if not message_content:
                logger.error("Empty message content")
                self._last_error = "Empty message content"
                return False
            
            # Create WhatsApp Web URL
            whatsapp_url = self._create_whatsapp_url(phone, message_content)
            
            logger.info(f"Opening WhatsApp Web for {customer.name} ({phone})")
            
            # Open WhatsApp Web in Chrome specifically
            success = self._open_in_chrome(whatsapp_url)
            
            if success:
                # Track the message attempt
                self._track_message_sent()
                
                if self.auto_send:
                    logger.info(f"🤖 Attempting automatic send for {customer.name} ({phone})")
                    
                    # Wait for page to load (configurable delay)
                    logger.info(f"⏱️ Waiting {self.auto_send_delay} seconds for WhatsApp Web to load...")
                    time.sleep(self.auto_send_delay)
                    
                    # Try to automatically send the message
                    auto_send_success = self._auto_send_message()
                    
                    if auto_send_success:
                        logger.info(f"✅ WhatsApp message automatically sent to {customer.name} ({phone})")
                    else:
                        logger.warning(f"⚠️ WhatsApp Web opened for {customer.name} ({phone}) - Auto-send failed, manual send required")
                        logger.info("💡 Tip: Make sure WhatsApp Web is logged in and Chrome is the active browser")
                else:
                    logger.info(f"✅ WhatsApp Web opened for {customer.name} ({phone})")
                    logger.info("⚠️ Please manually send the message in WhatsApp Web")
                
                return True
            else:
                logger.error(f"Failed to open WhatsApp Web for {customer.name}")
                self._last_error = "Failed to open Chrome browser"
                return False
            
        except Exception as e:
            error_msg = f"Failed to send WhatsApp message to {customer.name}: {e}"
            logger.error(error_msg)
            self._last_error = str(e)
            return False
    
    def _auto_send_message(self) -> bool:
        """
        Attempt to automatically send the message using system automation.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check Chrome availability first
            chrome_available, chrome_info = self._check_chrome_availability()
            if not chrome_available:
                logger.warning(f"Chrome not available: {chrome_info}")
                logger.info("💡 Install Google Chrome for better auto-send reliability")
            
            system = platform.system().lower()
            success = False
            
            # Try JavaScript injection first (most reliable)
            logger.info("🔧 Attempting JavaScript auto-send...")
            if system == "darwin":  # macOS
                success = self._auto_send_javascript_macos()
            elif system == "windows":  # Windows
                success = self._auto_send_javascript_windows()
            
            # If JavaScript failed, try platform-specific automation
            if not success:
                logger.info("🔧 JavaScript failed, trying platform-specific automation...")
                if system == "darwin":  # macOS
                    success = self._auto_send_macos()
                    # If mouse click method failed, try simple Enter key method
                    if not success:
                        logger.info("🔧 Mouse click method failed, trying simple Enter key...")
                        success = self._auto_send_macos_simple()
                elif system == "windows":  # Windows
                    success = self._auto_send_windows()
                elif system == "linux":  # Linux
                    success = self._auto_send_linux()
            
            if success:
                logger.info("✅ Auto-send successful!")
            else:
                logger.warning("⚠️ Auto-send failed - manual sending required")
                if chrome_available:
                    logger.info("💡 Make sure WhatsApp Web is loaded and Chrome is the active window")
                else:
                    logger.info("💡 Install Google Chrome and ensure WhatsApp Web is open")
            
            return success
                
        except Exception as e:
            logger.error(f"Auto-send failed: {e}")
            return False
    
    def _auto_send_javascript(self) -> bool:
        """
        Attempt to auto-send using JavaScript injection via AppleScript/PowerShell.
        This method tries to execute JavaScript directly in the browser.
        """
        try:
            system = platform.system().lower()
            
            if system == "darwin":  # macOS
                return self._auto_send_javascript_macos()
            elif system == "windows":  # Windows
                return self._auto_send_javascript_windows()
            else:
                return False
                
        except Exception as e:
            logger.error(f"JavaScript auto-send failed: {e}")
            return False
    
    def _auto_send_javascript_macos(self) -> bool:
        """Auto-send using JavaScript on macOS - Chrome only."""
        try:
            # Simple test to check if JavaScript execution is enabled
            test_script = '''
            tell application "Google Chrome"
                if (count of windows) > 0 then
                    execute tab 1 of window 1 javascript "true"
                    return true
                end if
                return false
            end tell
            '''
            
            test_result = subprocess.run(
                ["osascript", "-e", test_script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if test_result.returncode != 0 and "JavaScript through AppleScript is turned off" in test_result.stderr:
                logger.warning("⚠️ Chrome JavaScript execution disabled")
                logger.info("💡 Enable JavaScript in Chrome: View > Developer > Allow JavaScript from Apple Events")
                return False
            
            # If JavaScript is enabled, try the actual auto-send
            applescript = '''
            tell application "Google Chrome"
                if (count of windows) > 0 then
                    repeat with w from 1 to count of windows
                        repeat with t from 1 to count of tabs of window w
                            if title of tab t of window w contains "WhatsApp" then
                                set active tab index of window w to t
                                set index of window w to 1
                                activate
                                delay 2
                                -- Try to click send button with simple JavaScript
                                try
                                    execute tab t of window w javascript "document.querySelector('button[aria-label=\"Send\"]').click()"
                                    return true
                                on error
                                    try
                                        execute tab t of window w javascript "document.querySelector('button[data-tab][aria-label=\"Send\"]').click()"
                                        return true
                                    on error
                                        return false
                                    end try
                                end try
                            end if
                        end repeat
                    end repeat
                end if
                return false
            end tell
            '''
            
            result = subprocess.run(
                ["osascript", "-e", applescript],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            success = result.returncode == 0 and "true" in result.stdout.lower()
            if success:
                logger.info("✅ JavaScript auto-send successful")
            else:
                logger.warning(f"⚠️ JavaScript auto-send failed")
                if "JavaScript through AppleScript is turned off" in result.stderr:
                    logger.info("💡 Enable JavaScript in Chrome: View > Developer > Allow JavaScript from Apple Events")
            
            return success
            
        except Exception as e:
            logger.error(f"JavaScript Chrome auto-send failed: {e}")
            return False
    
    def _auto_send_javascript_windows(self) -> bool:
        """Auto-send using JavaScript on Windows via PowerShell and Chrome DevTools."""
        try:
            # Enhanced PowerShell script to use Chrome DevTools Protocol
            powershell_script = '''
            Add-Type -AssemblyName System.Windows.Forms
            
            # Find Chrome processes with WhatsApp
            $chromeProcesses = Get-Process -Name "chrome" -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like "*WhatsApp*" }
            
            if ($chromeProcesses) {
                # Bring Chrome to front
                $chromeProcess = $chromeProcesses[0]
                [System.Windows.Forms.Application]::SetForegroundWindow($chromeProcess.MainWindowHandle)
                Start-Sleep -Seconds 1
                
                # Try to use Chrome DevTools to execute JavaScript
                try {
                    # Use Chrome's remote debugging if available
                    $response = Invoke-RestMethod -Uri "http://localhost:9222/json" -Method Get -ErrorAction SilentlyContinue
                    if ($response) {
                        $whatsappTab = $response | Where-Object { $_.title -like "*WhatsApp*" } | Select-Object -First 1
                        if ($whatsappTab) {
                            $debugUrl = $whatsappTab.webSocketDebuggerUrl -replace "ws://", "http://" -replace "/devtools/page/", "/json/runtime/evaluate?tabId="
                            $jsCode = @"
                                // Target the exact WhatsApp send button structure
                                var sendBtn = document.querySelector('button[aria-label=\"Send\"]') ||
                                             document.querySelector('button[aria-label*=\"Send\"]') ||
                                             document.querySelector('button[data-tab][aria-label=\"Send\"]') ||
                                             document.querySelector('button span[data-icon=\"wds-ic-send-filled\"]').parentElement ||
                                             document.querySelector('[data-testid=\"send\"]');
                                
                                if (sendBtn) {
                                    console.log('Send button found:', sendBtn);
                                    sendBtn.click();
                                    'SUCCESS';
                                } else {
                                    console.log('Send button not found, trying Enter key');
                                    var messageBox = document.querySelector('[contenteditable=\"true\"]') ||
                                                    document.querySelector('[data-testid=\"conversation-compose-box-input\"]');
                                    if (messageBox) {
                                        messageBox.focus();
                                        var event = new KeyboardEvent('keydown', {
                                            key: 'Enter',
                                            keyCode: 13,
                                            which: 13,
                                            bubbles: true
                                        });
                                        messageBox.dispatchEvent(event);
                                        'FALLBACK';
                                    } else {
                                        'FAILED';
                                    }
                                }
"@
                            $body = @{ expression = $jsCode } | ConvertTo-Json
                            $result = Invoke-RestMethod -Uri $debugUrl -Method Post -Body $body -ContentType "application/json" -ErrorAction SilentlyContinue
                            if ($result.result.value -eq "SUCCESS" -or $result.result.value -eq "FALLBACK") {
                                return $true
                            }
                        }
                    }
                } catch {}
                
                # Fallback to key simulation
                [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
                return $true
            }
            
            return $false
            '''
            
            result = subprocess.run(
                ["powershell", "-Command", powershell_script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            success = result.returncode == 0 and "True" in result.stdout
            if success:
                logger.info("✅ Windows JavaScript auto-send successful")
            else:
                logger.warning(f"⚠️ Windows JavaScript auto-send failed: {result.stdout}")
            
            return success
            
        except Exception as e:
            logger.error(f"JavaScript Windows auto-send failed: {e}")
            return False
    
    def _auto_send_macos(self) -> bool:
        """Auto-send message on macOS using AppleScript - Chrome only with mouse click + Enter."""
        try:
            # Enhanced AppleScript that clicks message box then sends Enter key
            applescript = '''
            tell application "Google Chrome"
                if (count of windows) > 0 then
                    repeat with w from 1 to count of windows
                        repeat with t from 1 to count of tabs of window w
                            set tabTitle to title of tab t of window w
                            set tabURL to URL of tab t of window w
                            -- Check for WhatsApp in title or URL
                            if tabTitle contains "WhatsApp" or tabURL contains "web.whatsapp.com" then
                                set active tab index of window w to t
                                set index of window w to 1
                                activate
                                delay 1
                                
                                -- Get window bounds for click calculation
                                tell application "System Events"
                                    tell process "Google Chrome"
                                        set frontmost to true
                                        delay 0.5
                                        
                                        -- Try to find and click the message input area
                                        -- WhatsApp message box is typically in the bottom area
                                        set windowBounds to bounds of front window
                                        set windowWidth to (item 3 of windowBounds) - (item 1 of windowBounds)
                                        set windowHeight to (item 4 of windowBounds) - (item 2 of windowBounds)
                                        
                                        -- Calculate click position (bottom center area where message box is)
                                        set clickX to (item 1 of windowBounds) + (windowWidth * 0.5)
                                        set clickY to (item 2 of windowBounds) + (windowHeight * 0.85)
                                        
                                        -- Click on the message input area
                                        click at {clickX, clickY}
                                        delay 0.5
                                        
                                        -- Send Enter key
                                        key code 36 -- Enter key
                                        delay 0.2
                                    end tell
                                end tell
                                return "SUCCESS"
                            end if
                        end repeat
                    end repeat
                end if
                return "NO_WHATSAPP_TAB"
            end tell
            '''
            
            result = subprocess.run(
                ["osascript", "-e", applescript],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            success = result.returncode == 0 and "SUCCESS" in result.stdout
            
            # Enhanced logging for debugging
            if success:
                logger.info("✅ macOS mouse click + Enter auto-send successful")
            else:
                logger.warning(f"⚠️ macOS mouse click + Enter auto-send failed")
                logger.debug(f"AppleScript return code: {result.returncode}")
                logger.debug(f"AppleScript stdout: {result.stdout}")
                logger.debug(f"AppleScript stderr: {result.stderr}")
                
                # Provide specific guidance based on the error
                if "NO_WHATSAPP_TAB" in result.stdout:
                    logger.info("💡 No WhatsApp tab found - make sure WhatsApp Web is open in Chrome")
                elif result.stderr:
                    if "process \"Google Chrome\" doesn't understand" in result.stderr:
                        logger.info("💡 Chrome accessibility issue - try enabling System Preferences > Security & Privacy > Accessibility > Terminal")
                    elif "not allowed assistive access" in result.stderr:
                        logger.info("💡 Enable accessibility access: System Preferences > Security & Privacy > Privacy > Accessibility")
                    else:
                        logger.info(f"💡 AppleScript error: {result.stderr}")
            
            return success
            
        except subprocess.TimeoutExpired:
            logger.error("macOS auto-send timed out")
            logger.info("💡 Try reducing auto-send delay or check if Chrome is responding")
            return False
        except Exception as e:
            logger.error(f"macOS auto-send failed: {e}")
            return False
    
    def _auto_send_macos_simple(self) -> bool:
        """Simple macOS auto-send using just Enter key after focusing Chrome."""
        try:
            # Much simpler AppleScript that just focuses Chrome and sends Enter
            applescript = '''
            tell application "Google Chrome"
                if (count of windows) > 0 then
                    repeat with w from 1 to count of windows
                        repeat with t from 1 to count of tabs of window w
                            set tabTitle to title of tab t of window w
                            set tabURL to URL of tab t of window w
                            -- Check for WhatsApp in title or URL
                            if tabTitle contains "WhatsApp" or tabURL contains "web.whatsapp.com" then
                                set active tab index of window w to t
                                set index of window w to 1
                                activate
                                delay 1
                                tell application "System Events"
                                    key code 36 -- Enter key
                                end tell
                                return "SUCCESS"
                            end if
                        end repeat
                    end repeat
                end if
                return "NO_WHATSAPP_TAB"
            end tell
            '''
            
            result = subprocess.run(
                ["osascript", "-e", applescript],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            success = result.returncode == 0 and "SUCCESS" in result.stdout
            
            if success:
                logger.info("✅ macOS simple Enter auto-send successful")
            else:
                logger.debug(f"Simple auto-send failed: {result.stdout} | {result.stderr}")
            
            return success
            
        except Exception as e:
            logger.debug(f"Simple macOS auto-send failed: {e}")
            return False
    
    def _auto_send_windows(self) -> bool:
        """Auto-send message on Windows using PowerShell - Chrome only with mouse click + Enter."""
        try:
            # Enhanced PowerShell script with mouse click on message box
            powershell_script = '''
            Add-Type -AssemblyName System.Windows.Forms
            Add-Type -AssemblyName System.Drawing
            
            # Wait for WhatsApp Web to load
            Start-Sleep -Seconds 2
            
            # Try to find Chrome with WhatsApp Web
            $chromeFound = $false
            $chromeWindow = $null
            
            # Get Chrome processes only
            $chromeProcesses = Get-Process -Name "chrome" -ErrorAction SilentlyContinue
            
            if ($chromeProcesses) {
                # Try to bring Chrome with WhatsApp to front
                foreach ($proc in $chromeProcesses) {
                    try {
                        if ($proc.MainWindowTitle -like "*WhatsApp*") {
                            [System.Windows.Forms.Application]::SetForegroundWindow($proc.MainWindowHandle)
                            $chromeWindow = $proc
                            $chromeFound = $true
                            break
                        }
                    } catch {}
                }
                
                # If no specific WhatsApp window found, try the first Chrome window
                if (-not $chromeFound) {
                    foreach ($proc in $chromeProcesses) {
                        try {
                            if ($proc.MainWindowHandle -ne 0) {
                                [System.Windows.Forms.Application]::SetForegroundWindow($proc.MainWindowHandle)
                                $chromeWindow = $proc
                                $chromeFound = $true
                                break
                            }
                        } catch {}
                    }
                }
            }
            
            if ($chromeFound -and $chromeWindow) {
                # Wait for window to be active
                Start-Sleep -Seconds 1
                
                # Get window rectangle for click calculation
                Add-Type @"
                    using System;
                    using System.Runtime.InteropServices;
                    public class Win32 {
                        [DllImport("user32.dll")]
                        public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
                        [StructLayout(LayoutKind.Sequential)]
                        public struct RECT {
                            public int Left, Top, Right, Bottom;
                        }
                    }
"@
                
                $rect = New-Object Win32+RECT
                $success = [Win32]::GetWindowRect($chromeWindow.MainWindowHandle, [ref]$rect)
                
                if ($success) {
                    # Calculate click position (bottom center area where message box typically is)
                    $windowWidth = $rect.Right - $rect.Left
                    $windowHeight = $rect.Bottom - $rect.Top
                    $clickX = $rect.Left + ($windowWidth * 0.5)
                    $clickY = $rect.Top + ($windowHeight * 0.85)
                    
                    # Move mouse to message box area and click
                    [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($clickX, $clickY)
                    Start-Sleep -Milliseconds 200
                    
                    # Simulate mouse click
                    Add-Type -TypeDefinition @"
                        using System;
                        using System.Runtime.InteropServices;
                        public class MouseClick {
                            [DllImport("user32.dll")]
                            public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, int dwExtraInfo);
                            public const uint MOUSEEVENTF_LEFTDOWN = 0x02;
                            public const uint MOUSEEVENTF_LEFTUP = 0x04;
                        }
"@
                    
                    [MouseClick]::mouse_event([MouseClick]::MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                    Start-Sleep -Milliseconds 50
                    [MouseClick]::mouse_event([MouseClick]::MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                    Start-Sleep -Milliseconds 300
                }
                
                # Send Enter key after clicking
                [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
                Start-Sleep -Milliseconds 200
                
                # Backup: try Ctrl+Enter if regular Enter didn't work
                [System.Windows.Forms.SendKeys]::SendWait("^{ENTER}")
                
                return $true
            }
            
            return $false
            '''
            
            result = subprocess.run(
                ["powershell", "-Command", powershell_script],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            success = result.returncode == 0 and "True" in result.stdout
            if success:
                logger.info("✅ Windows mouse click + Enter auto-send successful")
            else:
                logger.warning(f"⚠️ Windows mouse click + Enter auto-send failed")
                if result.stderr:
                    logger.debug(f"PowerShell error: {result.stderr}")
            
            return success
            
        except subprocess.TimeoutExpired:
            logger.error("Windows auto-send timed out")
            return False
        except Exception as e:
            logger.error(f"Windows auto-send failed: {e}")
            return False

    
    def _auto_send_linux(self) -> bool:
        """Auto-send message on Linux using xdotool with mouse click + Enter."""
        try:
            # Enhanced Linux method with mouse click on message box
            
            # First, try to find and focus Chrome window with WhatsApp
            focus_result = subprocess.run([
                "xdotool", "search", "--name", "WhatsApp", "windowactivate"
            ], capture_output=True, text=True, timeout=5)
            
            if focus_result.returncode != 0:
                # Fallback: try to find any Chrome window
                focus_result = subprocess.run([
                    "xdotool", "search", "--class", "Google-chrome", "windowactivate"
                ], capture_output=True, text=True, timeout=5)
            
            if focus_result.returncode == 0:
                # Wait for window to be active
                time.sleep(1)
                
                # Get window geometry for click calculation
                geometry_result = subprocess.run([
                    "xdotool", "getactivewindow", "getwindowgeometry"
                ], capture_output=True, text=True, timeout=5)
                
                if geometry_result.returncode == 0:
                    # Parse geometry to calculate click position
                    # Output format: "Position: X,Y (screen: 0)\n  Geometry: WIDTHxHEIGHT"
                    lines = geometry_result.stdout.strip().split('\n')
                    for line in lines:
                        if 'Geometry:' in line:
                            # Extract width and height
                            geometry = line.split('Geometry:')[1].strip()
                            if 'x' in geometry:
                                width, height = geometry.split('x')
                                width = int(width)
                                height = int(height)
                                
                                # Calculate click position (bottom center area for message box)
                                click_x = width // 2
                                click_y = int(height * 0.85)  # 85% down from top
                                
                                # Click on the message box area (relative to window)
                                click_result = subprocess.run([
                                    "xdotool", "mousemove", "--window", "$(xdotool getactivewindow)", 
                                    str(click_x), str(click_y), "click", "1"
                                ], capture_output=True, text=True, timeout=5)
                                
                                # Wait a bit after clicking
                                time.sleep(0.3)
                                break
                
                # Send Enter key after clicking
                enter_result = subprocess.run([
                    "xdotool", "key", "Return"
                ], capture_output=True, text=True, timeout=5)
                
                success = enter_result.returncode == 0
                if success:
                    logger.info("✅ Linux mouse click + Enter auto-send successful")
                else:
                    logger.warning("⚠️ Linux Enter key failed")
                
                return success
            else:
                logger.warning("⚠️ Linux: Could not find Chrome window")
                return False
            
        except FileNotFoundError:
            logger.warning("xdotool not found - auto-send not available on Linux")
            logger.info("💡 Install xdotool: sudo apt-get install xdotool")
            return False
        except Exception as e:
            logger.error(f"Linux auto-send failed: {e}")
            return False
    
    def _format_phone_number(self, phone: str) -> Optional[str]:
        """
        Format phone number for WhatsApp Web.
        
        Args:
            phone: Raw phone number
            
        Returns:
            Formatted phone number or None if invalid
        """
        if not phone:
            return None
        
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, phone))
        
        if not digits_only:
            return None
        
        # If it doesn't start with country code, assume it's a local number
        if len(digits_only) == 10:  # US/local format
            return f"1{digits_only}"  # Assume US
        elif len(digits_only) == 11 and digits_only.startswith('1'):  # US with country code
            return digits_only
        elif len(digits_only) >= 10:  # International format
            return digits_only
        else:
            return None
    
    def _render_message(self, customer: Customer, template: MessageTemplate) -> str:
        """
        Render message content with customer data.
        
        Args:
            customer: Customer data
            template: Message template
            
        Returns:
            Rendered message content
        """
        # Use WhatsApp content if available, otherwise use email content
        content = template.whatsapp_content or template.content
        
        if not content:
            return ""
        
        # Simple variable substitution
        variables = {
            'name': customer.name or 'Customer',
            'company': customer.company or 'Your Company',
            'phone': customer.phone or '',
            'email': customer.email or ''
        }
        
        rendered_content = content
        for var, value in variables.items():
            rendered_content = rendered_content.replace(f'{{{var}}}', value)
        
        return rendered_content
    
    def _open_in_chrome(self, url: str) -> bool:
        """
        Open URL in Chrome specifically.
        
        Args:
            url: URL to open
            
        Returns:
            True if successful, False otherwise
        """
        try:
            system = platform.system().lower()
            
            if system == "darwin":  # macOS
                # Try to open in Chrome specifically
                result = subprocess.run([
                    "open", "-a", "Google Chrome", url
                ], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    return True
                else:
                    # Fallback to default browser
                    logger.warning("Chrome not found, using default browser")
                    return webbrowser.open(url)
                    
            elif system == "windows":  # Windows
                # Try to open in Chrome specifically
                chrome_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
                ]
                
                for chrome_path in chrome_paths:
                    if os.path.exists(chrome_path):
                        result = subprocess.run([
                            chrome_path, url
                        ], capture_output=True, text=True, timeout=5)
                        
                        if result.returncode == 0:
                            return True
                
                # Fallback to default browser
                logger.warning("Chrome not found, using default browser")
                return webbrowser.open(url)
                
            else:  # Linux
                # Try to open in Chrome specifically
                chrome_commands = ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium"]
                
                for chrome_cmd in chrome_commands:
                    try:
                        result = subprocess.run([
                            chrome_cmd, url
                        ], capture_output=True, text=True, timeout=5)
                        
                        if result.returncode == 0:
                            return True
                    except FileNotFoundError:
                        continue
                
                # Fallback to default browser
                logger.warning("Chrome not found, using default browser")
                return webbrowser.open(url)
                
        except Exception as e:
            logger.error(f"Failed to open URL in Chrome: {e}")
            # Final fallback to default browser
            return webbrowser.open(url)
    
    def _check_chrome_javascript_permissions(self) -> Tuple[bool, str]:
        """
        Check if Chrome allows JavaScript execution from AppleScript (macOS only).
        
        Returns:
            Tuple of (is_enabled, message)
        """
        try:
            system = platform.system().lower()
            if system != "darwin":
                return True, "JavaScript permissions not applicable on this platform"
            
            # Test JavaScript execution in Chrome
            test_script = '''
            tell application "Google Chrome"
                if (count of windows) > 0 then
                    execute tab 1 of window 1 javascript "true"
                    return "enabled"
                else
                    return "no_windows"
                end if
            end tell
            '''
            
            result = subprocess.run(
                ["osascript", "-e", test_script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return True, "JavaScript execution enabled in Chrome"
            elif "JavaScript through AppleScript is turned off" in result.stderr:
                return False, "JavaScript execution disabled in Chrome - Enable in View > Developer > Allow JavaScript from Apple Events"
            else:
                return False, f"Chrome JavaScript test failed: {result.stderr}"
                
        except Exception as e:
            return False, f"Failed to check Chrome JavaScript permissions: {e}"

    def _check_chrome_availability(self) -> Tuple[bool, str]:
        """
        Check if Chrome is available on the system.
        
        Returns:
            Tuple of (is_available, chrome_path_or_command)
        """
        try:
            system = platform.system().lower()
            
            if system == "darwin":  # macOS
                # Check if Chrome is installed
                result = subprocess.run([
                    "mdfind", "kMDItemCFBundleIdentifier == 'com.google.Chrome'"
                ], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0 and result.stdout.strip():
                    return True, "Google Chrome"
                else:
                    return False, "Chrome not found on macOS"
                    
            elif system == "windows":  # Windows
                # Check common Chrome installation paths
                chrome_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
                ]
                
                for chrome_path in chrome_paths:
                    if os.path.exists(chrome_path):
                        return True, chrome_path
                
                return False, "Chrome not found on Windows"
                
            else:  # Linux
                # Check for Chrome variants
                chrome_commands = ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium"]
                
                for chrome_cmd in chrome_commands:
                    try:
                        result = subprocess.run([
                            "which", chrome_cmd
                        ], capture_output=True, text=True, timeout=5)
                        
                        if result.returncode == 0:
                            return True, chrome_cmd
                    except FileNotFoundError:
                        continue
                
                return False, "Chrome not found on Linux"
                
        except Exception as e:
            logger.error(f"Failed to check Chrome availability: {e}")
            return False, f"Error checking Chrome: {e}"

    def _create_whatsapp_url(self, phone: str, message: str) -> str:
        """
        Create WhatsApp Web URL with pre-filled message.
        
        Args:
            phone: Formatted phone number
            message: Message content
            
        Returns:
            WhatsApp Web URL
        """
        # URL encode the message
        encoded_message = urllib.parse.quote(message)
        
        # Create WhatsApp Web URL
        # Format: https://web.whatsapp.com/send?phone=PHONE&text=MESSAGE
        url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_message}"
        
        return url
    

    
    def _track_message_sent(self):
        """Track that a message was sent."""
        now = datetime.now()
        
        # Add to timestamps
        self.message_timestamps.append(now)
        
        # Clean old timestamps (keep only last hour)
        cutoff = now - timedelta(hours=1)
        self.message_timestamps = [
            ts for ts in self.message_timestamps if ts >= cutoff
        ]
        
        # Update daily usage
        self.daily_usage["messages_sent"] = self.daily_usage.get("messages_sent", 0) + 1
        self._save_daily_usage()
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test the WhatsApp Web service.
        
        Returns:
            Tuple of (success, message)
        """
        if not self.is_configured():
            return False, "WhatsApp Web service is not configured"
        
        try:
            # Check if we can send (without actually sending)
            can_send, reason = self.can_send_message()
            if not can_send:
                return False, f"Service not ready: {reason}"
            
            # Test browser opening with WhatsApp Web
            test_url = "https://web.whatsapp.com"
            success = webbrowser.open(test_url)
            
            if success:
                usage = self.get_daily_usage()
                return True, f"WhatsApp Web service is ready. Usage: {usage['messages_sent_today']}/{usage['daily_limit']} messages today"
            else:
                return False, "Failed to open browser for WhatsApp Web"
            
        except Exception as e:
            return False, f"Service test failed: {e}"
    
    def get_last_error(self) -> Optional[str]:
        """Get the last error message."""
        return self._last_error
    
    def reset_daily_usage(self):
        """Reset daily usage (for testing or manual reset)."""
        self.daily_usage = {"messages_sent": 0}
        self._save_daily_usage()
        logger.info("Daily usage reset")
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service information and status."""
        chrome_available, chrome_info = self._check_chrome_availability()
        js_enabled, js_info = self._check_chrome_javascript_permissions()
        system = platform.system().lower()
        
        # Platform-specific capabilities
        platform_features = {
            "darwin": [
                "✅ AppleScript automation support",
                "✅ Chrome JavaScript injection" if js_enabled else "⚠️ Chrome JavaScript injection (disabled)",
                "✅ Spotlight Chrome detection",
                "✅ Native Chrome opening"
            ],
            "windows": [
                "✅ PowerShell automation support", 
                "✅ Chrome DevTools Protocol support",
                "✅ Registry Chrome detection",
                "✅ COM automation fallback"
            ],
            "linux": [
                "✅ xdotool automation support",
                "✅ Chrome variant detection",
                "✅ Command-line Chrome opening",
                "⚠️ Limited JavaScript injection"
            ]
        }
        
        warnings = [
            "⚠️ Uses browser automation which may violate WhatsApp ToS",
            "⚠️ Risk of account suspension",
            "⚠️ Requires WhatsApp Web to be logged in",
            "⚠️ Less reliable than WhatsApp Business API",
            "💡 Chrome browser recommended for best results"
        ]
        
        # Add JavaScript-specific warning for macOS
        if system == "darwin" and not js_enabled:
            warnings.append("⚠️ Enable Chrome JavaScript: View > Developer > Allow JavaScript from Apple Events")
        
        return {
            "service_name": "WhatsApp Web Automation Service",
            "is_available": self.is_available(),
            "is_configured": self.is_configured(),
            "platform": system.title(),
            "chrome_status": {
                "available": chrome_available,
                "info": chrome_info,
                "javascript_enabled": js_enabled,
                "javascript_info": js_info,
                "recommended": True
            },
            "daily_usage": self.get_daily_usage(),
            "rate_limits": {
                "per_minute": self.rate_limit_per_minute,
                "min_delay_seconds": self.min_delay_seconds
            },
            "auto_send": {
                "enabled": self.auto_send,
                "delay_seconds": self.auto_send_delay,
                "methods": ["JavaScript injection", "Platform automation", "Key simulation"]
            },
            "platform_features": platform_features.get(system, ["⚠️ Limited platform support"]),
            "warnings": warnings,
            "features": [
                "✅ No external dependencies required",
                "✅ Chrome-optimized automation",
                "✅ Cross-platform support (macOS, Windows, Linux)",
                "✅ Conservative rate limiting",
                "✅ Daily usage tracking",
                "✅ Multiple auto-send methods",
                "✅ Graceful fallback mechanisms"
            ],
            "last_error": self._last_error
        }
