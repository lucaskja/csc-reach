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
        auto_send_delay: int = 5,        # Delay before auto-send attempt
        close_existing_tabs: bool = True # Close existing WhatsApp Web tabs before opening new ones
    ):
        """
        Initialize WhatsApp Web automation service.
        
        Args:
            rate_limit_per_minute: Messages per minute (very conservative)
            daily_message_limit: Daily message limit (much lower for safety)
            min_delay_seconds: Minimum delay between messages for safety
            auto_send: Whether to automatically send messages (higher risk)
            auto_send_delay: Seconds to wait before attempting auto-send
            close_existing_tabs: Whether to close existing WhatsApp Web tabs before opening new ones
        """
        self.rate_limit_per_minute = rate_limit_per_minute
        self.daily_message_limit = daily_message_limit
        self.min_delay_seconds = min_delay_seconds
        self.auto_send = auto_send
        self.auto_send_delay = auto_send_delay
        self.close_existing_tabs = close_existing_tabs
        
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
    
    def configure_service(self, acknowledge_risks: bool = False, auto_send: bool = False, close_existing_tabs: bool = True) -> Tuple[bool, str]:
        """
        Configure the WhatsApp Web service.
        
        Args:
            acknowledge_risks: User must acknowledge the risks
            auto_send: Enable automatic sending (higher risk)
            close_existing_tabs: Whether to close existing WhatsApp Web tabs before opening new ones
            
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
                "close_existing_tabs": close_existing_tabs,
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
            self.close_existing_tabs = close_existing_tabs
            
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
                self.close_existing_tabs = config.get("close_existing_tabs", True)
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
                        # Show Windows notification on success
                        if platform.system().lower() == "windows":
                            self._show_windows_notification(
                                "WhatsApp Message Sent",
                                f"Message sent to {customer.name}"
                            )
                    else:
                        logger.warning(f"⚠️ WhatsApp Web opened for {customer.name} ({phone}) - Auto-send failed, manual send required")
                        logger.info("💡 Tip: Make sure WhatsApp Web is logged in and Chrome is the active browser")
                        # Show Windows notification for manual action needed
                        if platform.system().lower() == "windows":
                            self._show_windows_notification(
                                "Manual Action Required",
                                f"Please manually send message to {customer.name}"
                            )
                else:
                    logger.info(f"✅ WhatsApp Web opened for {customer.name} ({phone})")
                    logger.info("⚠️ Please manually send the message in WhatsApp Web")
                    # Show Windows notification for manual sending
                    if platform.system().lower() == "windows":
                        self._show_windows_notification(
                            "WhatsApp Web Opened",
                            f"Please manually send message to {customer.name}"
                        )
                
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
                    # If mouse click method failed, try simple Enter key method
                    if not success:
                        logger.info("🔧 Mouse click method failed, trying simple Enter key...")
                        success = self._auto_send_windows_simple()
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
        """Enhanced auto-send using JavaScript on Windows via PowerShell and Chrome DevTools."""
        try:
            # Enhanced PowerShell script with multiple fallback methods
            powershell_script = '''
            Add-Type -AssemblyName System.Windows.Forms
            Add-Type -AssemblyName System.Drawing
            
            # Enhanced Chrome process detection
            function Find-ChromeWithWhatsApp {
                $chromeProcesses = Get-Process -Name "chrome" -ErrorAction SilentlyContinue
                $whatsappProcesses = @()
                
                foreach ($proc in $chromeProcesses) {
                    try {
                        if ($proc.MainWindowTitle -like "*WhatsApp*" -and $proc.MainWindowHandle -ne 0) {
                            $whatsappProcesses += $proc
                        }
                    } catch {}
                }
                
                return $whatsappProcesses
            }
            
            # Enhanced DevTools communication
            function Invoke-ChromeDevTools {
                param($jsCode)
                
                try {
                    # Try multiple DevTools ports (Chrome can use different ports)
                    $ports = @(9222, 9223, 9224)
                    
                    foreach ($port in $ports) {
                        try {
                            $response = Invoke-RestMethod -Uri "http://localhost:$port/json" -Method Get -ErrorAction SilentlyContinue -TimeoutSec 2
                            if ($response) {
                                $whatsappTab = $response | Where-Object { 
                                    $_.title -like "*WhatsApp*" -or $_.url -like "*web.whatsapp.com*" 
                                } | Select-Object -First 1
                                
                                if ($whatsappTab) {
                                    # Use Runtime.evaluate API
                                    $evalUrl = "http://localhost:$port/json/runtime/evaluate"
                                    $body = @{
                                        expression = $jsCode
                                        returnByValue = $true
                                        awaitPromise = $false
                                    } | ConvertTo-Json -Depth 3
                                    
                                    $headers = @{
                                        'Content-Type' = 'application/json'
                                        'Target' = $whatsappTab.id
                                    }
                                    
                                    $result = Invoke-RestMethod -Uri $evalUrl -Method Post -Body $body -Headers $headers -ErrorAction SilentlyContinue -TimeoutSec 3
                                    
                                    if ($result.result.value -eq "SUCCESS" -or $result.result.value -eq "FALLBACK") {
                                        Write-Host "DevTools success on port $port"
                                        return $true
                                    }
                                }
                            }
                        } catch {
                            # Try next port
                            continue
                        }
                    }
                } catch {}
                
                return $false
            }
            
            # Enhanced JavaScript code for WhatsApp Web
            $jsCode = @"
                (function() {
                    try {
                        // Wait for page to be fully loaded
                        if (document.readyState !== 'complete') {
                            return 'PAGE_NOT_READY';
                        }
                        
                        // Multiple selectors for send button (WhatsApp updates frequently)
                        const sendSelectors = [
                            'button[aria-label*="Send"]',
                            'button[data-testid="send"]',
                            'button span[data-icon="send"]',
                            'button span[data-icon="wds-ic-send-filled"]',
                            '[role="button"][aria-label*="Send"]',
                            'button[title*="Send"]',
                            'div[role="button"][aria-label*="Send"]'
                        ];
                        
                        let sendBtn = null;
                        for (const selector of sendSelectors) {
                            sendBtn = document.querySelector(selector);
                            if (sendBtn) break;
                        }
                        
                        if (sendBtn && sendBtn.offsetParent !== null) {
                            // Ensure button is visible and clickable
                            sendBtn.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            
                            // Simulate human-like click
                            const rect = sendBtn.getBoundingClientRect();
                            const clickEvent = new MouseEvent('click', {
                                view: window,
                                bubbles: true,
                                cancelable: true,
                                clientX: rect.left + rect.width / 2,
                                clientY: rect.top + rect.height / 2
                            });
                            
                            sendBtn.dispatchEvent(clickEvent);
                            
                            // Also try direct click as backup
                            setTimeout(() => sendBtn.click(), 100);
                            
                            return 'SUCCESS';
                        } else {
                            // Fallback: Try Enter key on message input
                            const messageSelectors = [
                                '[contenteditable="true"][data-testid="conversation-compose-box-input"]',
                                '[contenteditable="true"]',
                                'div[role="textbox"]',
                                '[data-testid="conversation-compose-box-input"]'
                            ];
                            
                            let messageBox = null;
                            for (const selector of messageSelectors) {
                                messageBox = document.querySelector(selector);
                                if (messageBox) break;
                            }
                            
                            if (messageBox) {
                                messageBox.focus();
                                
                                // Simulate Enter key press
                                const enterEvent = new KeyboardEvent('keydown', {
                                    key: 'Enter',
                                    keyCode: 13,
                                    which: 13,
                                    bubbles: true,
                                    cancelable: true
                                });
                                
                                messageBox.dispatchEvent(enterEvent);
                                
                                return 'FALLBACK';
                            } else {
                                return 'NO_ELEMENTS_FOUND';
                            }
                        }
                    } catch (error) {
                        return 'ERROR: ' + error.message;
                    }
                })();
"@
            
            # Find Chrome processes with WhatsApp
            $chromeProcesses = Find-ChromeWithWhatsApp
            
            if ($chromeProcesses.Count -gt 0) {
                # Bring Chrome to front
                $chromeProcess = $chromeProcesses[0]
                [System.Windows.Forms.Application]::SetForegroundWindow($chromeProcess.MainWindowHandle)
                
                # Wait for window to be active
                Start-Sleep -Milliseconds 800
                
                # Try DevTools first (most reliable)
                $devToolsSuccess = Invoke-ChromeDevTools -jsCode $jsCode
                
                if ($devToolsSuccess) {
                    Write-Host "SUCCESS_DEVTOOLS"
                    return $true
                }
                
                # Fallback to keyboard simulation
                Write-Host "DevTools failed, trying keyboard simulation..."
                
                # Focus on the Chrome window first
                [System.Windows.Forms.Application]::SetForegroundWindow($chromeProcess.MainWindowHandle)
                Start-Sleep -Milliseconds 500
                
                # Try multiple key combinations
                [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
                Start-Sleep -Milliseconds 200
                
                # Backup: Ctrl+Enter (sometimes needed for WhatsApp Web)
                [System.Windows.Forms.SendKeys]::SendWait("^{ENTER}")
                Start-Sleep -Milliseconds 200
                
                # Final backup: Tab to send button and press Enter
                [System.Windows.Forms.SendKeys]::SendWait("{TAB}")
                Start-Sleep -Milliseconds 100
                [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
                
                Write-Host "SUCCESS_KEYBOARD"
                return $true
            } else {
                Write-Host "NO_CHROME_WHATSAPP_FOUND"
                return $false
            }
            '''
            
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-Command", powershell_script],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            success = result.returncode == 0 and ("SUCCESS_DEVTOOLS" in result.stdout or "SUCCESS_KEYBOARD" in result.stdout)
            
            if success:
                if "SUCCESS_DEVTOOLS" in result.stdout:
                    logger.info("✅ Windows JavaScript auto-send successful (DevTools)")
                else:
                    logger.info("✅ Windows JavaScript auto-send successful (Keyboard)")
            else:
                logger.warning(f"⚠️ Windows JavaScript auto-send failed")
                if "NO_CHROME_WHATSAPP_FOUND" in result.stdout:
                    logger.info("💡 No Chrome window with WhatsApp found")
                elif result.stderr:
                    logger.debug(f"PowerShell error: {result.stderr}")
            
            return success
            
        except subprocess.TimeoutExpired:
            logger.error("Windows JavaScript auto-send timed out")
            return False
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
        """Enhanced auto-send message on Windows using advanced PowerShell automation."""
        try:
            # Advanced PowerShell script with comprehensive Windows automation
            powershell_script = '''
            Add-Type -AssemblyName System.Windows.Forms
            Add-Type -AssemblyName System.Drawing
            Add-Type -AssemblyName UIAutomationClient
            
            # Enhanced Windows API integration
            Add-Type @"
                using System;
                using System.Runtime.InteropServices;
                using System.Text;
                
                public class Win32API {
                    [DllImport("user32.dll")]
                    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
                    
                    [DllImport("user32.dll")]
                    public static extern bool SetForegroundWindow(IntPtr hWnd);
                    
                    [DllImport("user32.dll")]
                    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
                    
                    [DllImport("user32.dll")]
                    public static extern bool IsWindowVisible(IntPtr hWnd);
                    
                    [DllImport("user32.dll")]
                    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
                    
                    [DllImport("user32.dll")]
                    public static extern bool EnumWindows(EnumWindowsProc enumProc, IntPtr lParam);
                    
                    [DllImport("user32.dll")]
                    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
                    
                    [DllImport("user32.dll")]
                    public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, int dwExtraInfo);
                    
                    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
                    
                    public const uint MOUSEEVENTF_LEFTDOWN = 0x02;
                    public const uint MOUSEEVENTF_LEFTUP = 0x04;
                    public const int SW_RESTORE = 9;
                    public const int SW_SHOW = 5;
                    
                    [StructLayout(LayoutKind.Sequential)]
                    public struct RECT {
                        public int Left, Top, Right, Bottom;
                    }
                }
"@
            
            # Enhanced Chrome window detection
            function Find-WhatsAppChromeWindow {
                $chromeProcesses = Get-Process -Name "chrome" -ErrorAction SilentlyContinue
                $whatsappWindows = @()
                
                foreach ($proc in $chromeProcesses) {
                    try {
                        if ($proc.MainWindowHandle -ne 0) {
                            $windowTitle = New-Object System.Text.StringBuilder 256
                            [Win32API]::GetWindowText($proc.MainWindowHandle, $windowTitle, 256)
                            $title = $windowTitle.ToString()
                            
                            if ($title -like "*WhatsApp*" -or $title -like "*web.whatsapp.com*") {
                                $whatsappWindows += @{
                                    Process = $proc
                                    Handle = $proc.MainWindowHandle
                                    Title = $title
                                    Visible = [Win32API]::IsWindowVisible($proc.MainWindowHandle)
                                }
                            }
                        }
                    } catch {}
                }
                
                # Sort by visibility and title relevance
                return $whatsappWindows | Sort-Object @{Expression={$_.Visible}; Descending=$true}, @{Expression={$_.Title -like "*WhatsApp*"}; Descending=$true}
            }
            
            # Enhanced window activation
            function Activate-ChromeWindow {
                param($windowInfo)
                
                try {
                    # Restore window if minimized
                    [Win32API]::ShowWindow($windowInfo.Handle, [Win32API]::SW_RESTORE)
                    Start-Sleep -Milliseconds 200
                    
                    # Bring to foreground
                    [Win32API]::SetForegroundWindow($windowInfo.Handle)
                    Start-Sleep -Milliseconds 300
                    
                    # Verify it's active
                    $activeWindow = [System.Windows.Forms.Application]::ActiveForm
                    return $true
                } catch {
                    return $false
                }
            }
            
            # Smart click position calculation
            function Get-SendButtonPosition {
                param($windowHandle)
                
                $rect = New-Object Win32API+RECT
                $success = [Win32API]::GetWindowRect($windowHandle, [ref]$rect)
                
                if ($success) {
                    $windowWidth = $rect.Right - $rect.Left
                    $windowHeight = $rect.Bottom - $rect.Top
                    
                    # Multiple potential send button positions
                    $positions = @(
                        @{ X = $rect.Left + ($windowWidth * 0.95); Y = $rect.Top + ($windowHeight * 0.85); Name = "Bottom-right (send button)" },
                        @{ X = $rect.Left + ($windowWidth * 0.90); Y = $rect.Top + ($windowHeight * 0.85); Name = "Bottom-right-center" },
                        @{ X = $rect.Left + ($windowWidth * 0.85); Y = $rect.Top + ($windowHeight * 0.85); Name = "Bottom-center-right" },
                        @{ X = $rect.Left + ($windowWidth * 0.50); Y = $rect.Top + ($windowHeight * 0.85); Name = "Bottom-center (message box)" }
                    )
                    
                    return $positions
                }
                
                return @()
            }
            
            # Enhanced mouse automation
            function Send-SmartClick {
                param($x, $y, $description)
                
                try {
                    # Move mouse smoothly
                    $currentPos = [System.Windows.Forms.Cursor]::Position
                    $steps = 5
                    
                    for ($i = 1; $i -le $steps; $i++) {
                        $newX = $currentPos.X + (($x - $currentPos.X) * $i / $steps)
                        $newY = $currentPos.Y + (($y - $currentPos.Y) * $i / $steps)
                        [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($newX, $newY)
                        Start-Sleep -Milliseconds 20
                    }
                    
                    # Perform click
                    [Win32API]::mouse_event([Win32API]::MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                    Start-Sleep -Milliseconds 50
                    [Win32API]::mouse_event([Win32API]::MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                    
                    Write-Host "Clicked at $description ($x, $y)"
                    return $true
                } catch {
                    Write-Host "Click failed at $description"
                    return $false
                }
            }
            
            # Main execution
            Write-Host "Starting enhanced Windows WhatsApp automation..."
            
            # Find WhatsApp Chrome windows
            $whatsappWindows = Find-WhatsAppChromeWindow
            
            if ($whatsappWindows.Count -eq 0) {
                Write-Host "NO_WHATSAPP_WINDOWS"
                return $false
            }
            
            # Use the best window
            $targetWindow = $whatsappWindows[0]
            Write-Host "Found WhatsApp window: $($targetWindow.Title)"
            
            # Activate the window
            $activated = Activate-ChromeWindow -windowInfo $targetWindow
            if (-not $activated) {
                Write-Host "WINDOW_ACTIVATION_FAILED"
                return $false
            }
            
            # Wait for window to be fully active
            Start-Sleep -Milliseconds 800
            
            # Get potential click positions
            $positions = Get-SendButtonPosition -windowHandle $targetWindow.Handle
            
            if ($positions.Count -gt 0) {
                # Try clicking on send button area first
                $sendButtonPos = $positions[0]
                $clickSuccess = Send-SmartClick -x $sendButtonPos.X -y $sendButtonPos.Y -description $sendButtonPos.Name
                
                if ($clickSuccess) {
                    Start-Sleep -Milliseconds 300
                }
                
                # Try message box area as backup
                if ($positions.Count -gt 3) {
                    $messageBoxPos = $positions[3]
                    Send-SmartClick -x $messageBoxPos.X -y $messageBoxPos.Y -description $messageBoxPos.Name
                    Start-Sleep -Milliseconds 200
                }
            }
            
            # Enhanced keyboard automation
            Write-Host "Sending keyboard commands..."
            
            # Ensure window is still focused
            [Win32API]::SetForegroundWindow($targetWindow.Handle)
            Start-Sleep -Milliseconds 200
            
            # Try multiple key combinations
            $keySequences = @(
                "{ENTER}",
                "^{ENTER}",
                "{TAB}{ENTER}",
                "{TAB}{TAB}{ENTER}",
                " {BACKSPACE}{ENTER}"
            )
            
            foreach ($sequence in $keySequences) {
                try {
                    [System.Windows.Forms.SendKeys]::SendWait($sequence)
                    Start-Sleep -Milliseconds 300
                    Write-Host "Sent: $sequence"
                } catch {
                    Write-Host "Failed to send: $sequence"
                }
            }
            
            Write-Host "WINDOWS_AUTOMATION_COMPLETE"
            return $true
            '''
            
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-Command", powershell_script],
                capture_output=True,
                text=True,
                timeout=20
            )
            
            success = result.returncode == 0 and "WINDOWS_AUTOMATION_COMPLETE" in result.stdout
            
            if success:
                logger.info("✅ Windows enhanced auto-send successful")
                # Log specific success details
                if "Clicked at" in result.stdout:
                    logger.debug("Mouse automation executed successfully")
                if "Sent:" in result.stdout:
                    logger.debug("Keyboard automation executed successfully")
            else:
                logger.warning(f"⚠️ Windows enhanced auto-send failed")
                if "NO_WHATSAPP_WINDOWS" in result.stdout:
                    logger.info("💡 No WhatsApp Chrome windows found")
                elif "WINDOW_ACTIVATION_FAILED" in result.stdout:
                    logger.info("💡 Failed to activate Chrome window")
                elif result.stderr:
                    logger.debug(f"PowerShell error: {result.stderr}")
            
            return success
            
        except subprocess.TimeoutExpired:
            logger.error("Windows enhanced auto-send timed out")
            return False
        except Exception as e:
            logger.error(f"Windows enhanced auto-send failed: {e}")
            return False
    
    def _auto_send_windows_simple(self) -> bool:
        """Simple Windows auto-send using just Enter key after focusing Chrome."""
        try:
            # Simple PowerShell script that just focuses Chrome and sends Enter
            powershell_script = '''
            Add-Type -AssemblyName System.Windows.Forms
            
            # Find Chrome processes
            $chromeProcesses = Get-Process -Name "chrome" -ErrorAction SilentlyContinue
            
            if ($chromeProcesses) {
                # Try to bring any Chrome window to front
                foreach ($proc in $chromeProcesses) {
                    try {
                        if ($proc.MainWindowHandle -ne 0) {
                            [System.Windows.Forms.Application]::SetForegroundWindow($proc.MainWindowHandle)
                            Start-Sleep -Seconds 1
                            
                            # Send Enter key
                            [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
                            Start-Sleep -Milliseconds 200
                            
                            # Backup: try Ctrl+Enter
                            [System.Windows.Forms.SendKeys]::SendWait("^{ENTER}")
                            
                            return $true
                        }
                    } catch {}
                }
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
                logger.info("✅ Windows simple Enter auto-send successful")
            else:
                logger.debug(f"Windows simple auto-send failed: {result.stdout} | {result.stderr}")
            
            return success
            
        except Exception as e:
            logger.debug(f"Simple Windows auto-send failed: {e}")
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
    
    def _close_existing_whatsapp_tabs(self) -> bool:
        """
        Close all existing WhatsApp Web tabs in Chrome to prevent multiple instances.
        
        Returns:
            True if successful or no tabs found, False if error occurred
        """
        try:
            system = platform.system().lower()
            
            if system == "darwin":  # macOS
                return self._close_whatsapp_tabs_macos()
            elif system == "windows":  # Windows
                return self._close_whatsapp_tabs_windows()
            else:  # Linux
                return self._close_whatsapp_tabs_linux()
                
        except Exception as e:
            logger.warning(f"Failed to close existing WhatsApp tabs: {e}")
            # Don't fail the entire operation if we can't close tabs
            return True
    
    def _close_whatsapp_tabs_macos(self) -> bool:
        """Close WhatsApp Web tabs on macOS using AppleScript."""
        try:
            applescript = '''
            tell application "Google Chrome"
                if (count of windows) > 0 then
                    repeat with w from 1 to count of windows
                        set tabsToClose to {}
                        repeat with t from 1 to count of tabs of window w
                            set tabTitle to title of tab t of window w
                            set tabURL to URL of tab t of window w
                            -- Check for WhatsApp in title or URL
                            if tabTitle contains "WhatsApp" or tabURL contains "web.whatsapp.com" then
                                set end of tabsToClose to t
                            end if
                        end repeat
                        
                        -- Close tabs in reverse order to maintain indices
                        repeat with i from (count of tabsToClose) to 1 by -1
                            set tabIndex to item i of tabsToClose
                            close tab tabIndex of window w
                        end repeat
                    end repeat
                    return "SUCCESS"
                end if
                return "NO_CHROME_WINDOWS"
            end tell
            '''
            
            result = subprocess.run(
                ["osascript", "-e", applescript],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            success = result.returncode == 0
            if success and "SUCCESS" in result.stdout:
                logger.info("✅ Closed existing WhatsApp Web tabs on macOS")
            elif "NO_CHROME_WINDOWS" in result.stdout:
                logger.debug("No Chrome windows found to close WhatsApp tabs")
            else:
                logger.debug(f"macOS tab closing result: {result.stdout} | {result.stderr}")
            
            return True  # Don't fail if we can't close tabs
            
        except Exception as e:
            logger.warning(f"Failed to close WhatsApp tabs on macOS: {e}")
            return True
    
    def _close_whatsapp_tabs_windows(self) -> bool:
        """Close WhatsApp Web tabs on Windows using PowerShell."""
        try:
            powershell_script = '''
            Add-Type -AssemblyName System.Windows.Forms
            
            # Find Chrome processes
            $chromeProcesses = Get-Process -Name "chrome" -ErrorAction SilentlyContinue
            
            if ($chromeProcesses) {
                # Try to use Chrome DevTools to close WhatsApp tabs
                try {
                    $response = Invoke-RestMethod -Uri "http://localhost:9222/json" -Method Get -ErrorAction SilentlyContinue -TimeoutSec 3
                    if ($response) {
                        $whatsappTabs = $response | Where-Object { 
                            $_.title -like "*WhatsApp*" -or $_.url -like "*web.whatsapp.com*" 
                        }
                        
                        foreach ($tab in $whatsappTabs) {
                            try {
                                $closeUrl = "http://localhost:9222/json/close/" + $tab.id
                                Invoke-RestMethod -Uri $closeUrl -Method Get -ErrorAction SilentlyContinue -TimeoutSec 2
                                Write-Host "Closed WhatsApp tab: $($tab.title)"
                            } catch {
                                # Ignore individual tab close failures
                            }
                        }
                        return $true
                    }
                } catch {
                    # Chrome DevTools not available, try alternative method
                }
                
                # Alternative: Use keyboard shortcuts to close tabs
                # This is less reliable but works when DevTools is not available
                foreach ($proc in $chromeProcesses) {
                    try {
                        if ($proc.MainWindowTitle -like "*WhatsApp*") {
                            [System.Windows.Forms.Application]::SetForegroundWindow($proc.MainWindowHandle)
                            Start-Sleep -Milliseconds 500
                            # Send Ctrl+W to close the current tab
                            [System.Windows.Forms.SendKeys]::SendWait("^w")
                            Start-Sleep -Milliseconds 200
                        }
                    } catch {
                        # Ignore individual process failures
                    }
                }
                
                return $true
            }
            
            return $true
            '''
            
            result = subprocess.run(
                ["powershell", "-Command", powershell_script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info("✅ Attempted to close existing WhatsApp Web tabs on Windows")
            else:
                logger.debug(f"Windows tab closing result: {result.stdout} | {result.stderr}")
            
            return True  # Don't fail if we can't close tabs
            
        except Exception as e:
            logger.warning(f"Failed to close WhatsApp tabs on Windows: {e}")
            return True
    
    def _close_whatsapp_tabs_linux(self) -> bool:
        """Close WhatsApp Web tabs on Linux using xdotool."""
        try:
            # Find Chrome windows with WhatsApp
            search_result = subprocess.run([
                "xdotool", "search", "--name", "WhatsApp"
            ], capture_output=True, text=True, timeout=5)
            
            if search_result.returncode == 0 and search_result.stdout.strip():
                window_ids = search_result.stdout.strip().split('\n')
                
                for window_id in window_ids:
                    try:
                        # Activate the window and close it with Ctrl+W
                        subprocess.run([
                            "xdotool", "windowactivate", window_id
                        ], capture_output=True, text=True, timeout=3)
                        
                        time.sleep(0.2)
                        
                        subprocess.run([
                            "xdotool", "key", "ctrl+w"
                        ], capture_output=True, text=True, timeout=3)
                        
                    except Exception:
                        # Ignore individual window close failures
                        continue
                
                logger.info("✅ Attempted to close existing WhatsApp Web tabs on Linux")
            else:
                logger.debug("No WhatsApp windows found on Linux")
            
            return True  # Don't fail if we can't close tabs
            
        except FileNotFoundError:
            logger.debug("xdotool not found - cannot close WhatsApp tabs on Linux")
            return True
        except Exception as e:
            logger.warning(f"Failed to close WhatsApp tabs on Linux: {e}")
            return True

    def _open_in_chrome(self, url: str) -> bool:
        """
        Open URL in Chrome specifically, after closing existing WhatsApp Web tabs.
        
        Args:
            url: URL to open
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # First, close any existing WhatsApp Web tabs to prevent multiple instances (if enabled)
            if self.close_existing_tabs:
                logger.info("🧹 Closing existing WhatsApp Web tabs...")
                self._close_existing_whatsapp_tabs()
                
                # Small delay to ensure tabs are closed before opening new one
                time.sleep(0.5)
            else:
                logger.debug("Skipping tab cleanup (close_existing_tabs=False)")
            
            system = platform.system().lower()
            
            if system == "darwin":  # macOS
                # Try to open in Chrome specifically
                result = subprocess.run([
                    "open", "-a", "Google Chrome", url
                ], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    logger.info("✅ Opened WhatsApp Web in Chrome (macOS)")
                    return True
                else:
                    # Fallback to default browser
                    logger.warning("Chrome not found, using default browser")
                    return webbrowser.open(url)
                    
            elif system == "windows":  # Windows
                # Use enhanced Chrome detection
                chrome_info = self._detect_chrome_windows()
                
                if chrome_info["found"] and chrome_info["paths"]:
                    # Try each detected Chrome path
                    for chrome_path in chrome_info["paths"]:
                        try:
                            # Enhanced Chrome launching with better arguments
                            chrome_args = [
                                chrome_path,
                                url,
                                "--new-window",  # Open in new window for better automation
                                "--disable-web-security",  # Help with automation
                                "--disable-features=VizDisplayCompositor",  # Improve compatibility
                                "--no-first-run",  # Skip first run setup
                                "--no-default-browser-check"  # Skip default browser check
                            ]
                            
                            result = subprocess.run(
                                chrome_args,
                                capture_output=True,
                                text=True,
                                timeout=8
                            )
                            
                            if result.returncode == 0:
                                logger.info(f"✅ Opened WhatsApp Web in Chrome (Windows) - {chrome_path}")
                                return True
                            else:
                                logger.debug(f"Chrome launch failed with args: {result.stderr}")
                                
                                # Fallback: try without extra arguments
                                result = subprocess.run([
                                    chrome_path, url
                                ], capture_output=True, text=True, timeout=5)
                                
                                if result.returncode == 0:
                                    logger.info(f"✅ Opened WhatsApp Web in Chrome (Windows, basic) - {chrome_path}")
                                    return True
                                    
                        except Exception as e:
                            logger.debug(f"Failed to launch Chrome at {chrome_path}: {e}")
                            continue
                
                # Enhanced fallback: try PowerShell method
                try:
                    logger.info("Trying PowerShell Chrome launch method...")
                    powershell_script = f'''
                    $url = "{url}"
                    
                    # Try to find Chrome via registry
                    try {{
                        $chromePath = (Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\chrome.exe" -ErrorAction SilentlyContinue)."(default)"
                        if ($chromePath -and (Test-Path $chromePath)) {{
                            Start-Process -FilePath $chromePath -ArgumentList $url
                            Write-Host "SUCCESS_REGISTRY"
                            exit 0
                        }}
                    }} catch {{}}
                    
                    # Try common paths
                    $paths = @(
                        "$env:ProgramFiles\\Google\\Chrome\\Application\\chrome.exe",
                        "${{env:ProgramFiles(x86)}}\\Google\\Chrome\\Application\\chrome.exe",
                        "$env:LOCALAPPDATA\\Google\\Chrome\\Application\\chrome.exe"
                    )
                    
                    foreach ($path in $paths) {{
                        if (Test-Path $path) {{
                            Start-Process -FilePath $path -ArgumentList $url
                            Write-Host "SUCCESS_PATH"
                            exit 0
                        }}
                    }}
                    
                    # Final fallback: use default browser
                    Start-Process $url
                    Write-Host "SUCCESS_DEFAULT"
                    '''
                    
                    result = subprocess.run([
                        "powershell", "-Command", powershell_script
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        if "SUCCESS_REGISTRY" in result.stdout:
                            logger.info("✅ Opened WhatsApp Web via PowerShell (Registry)")
                        elif "SUCCESS_PATH" in result.stdout:
                            logger.info("✅ Opened WhatsApp Web via PowerShell (Path)")
                        else:
                            logger.info("✅ Opened WhatsApp Web via PowerShell (Default)")
                        return True
                        
                except Exception as e:
                    logger.debug(f"PowerShell Chrome launch failed: {e}")
                
                # Final fallback to default browser
                logger.warning("Chrome not found or failed to launch, using default browser")
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
                            logger.info("✅ Opened WhatsApp Web in Chrome (Linux)")
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
                # Enhanced Chrome detection using multiple methods
                chrome_info = self._detect_chrome_windows()
                if chrome_info["found"]:
                    return True, chrome_info["details"]
                else:
                    return False, chrome_info["details"]
                
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

    def _detect_chrome_windows(self) -> Dict[str, Any]:
        """Enhanced Chrome detection for Windows using multiple methods."""
        try:
            chrome_info = {
                "found": False,
                "details": "Chrome not detected",
                "paths": [],
                "version": None,
                "registry_found": False,
                "process_running": False
            }
            
            # Method 1: Check common installation paths
            common_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
                os.path.expanduser(r"~\AppData\Local\Google\Chrome\chrome.exe")
            ]
            
            for chrome_path in common_paths:
                if os.path.exists(chrome_path):
                    chrome_info["paths"].append(chrome_path)
                    chrome_info["found"] = True
            
            # Method 2: Check Windows Registry
            try:
                import winreg
                
                # Check HKEY_LOCAL_MACHINE
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Google\Chrome\BLBeacon") as key:
                        version, _ = winreg.QueryValueEx(key, "version")
                        chrome_info["version"] = version
                        chrome_info["registry_found"] = True
                        chrome_info["found"] = True
                except (FileNotFoundError, OSError):
                    pass
                
                # Check HKEY_CURRENT_USER
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Google\Chrome\BLBeacon") as key:
                        version, _ = winreg.QueryValueEx(key, "version")
                        chrome_info["version"] = version
                        chrome_info["registry_found"] = True
                        chrome_info["found"] = True
                except (FileNotFoundError, OSError):
                    pass
                
                # Check for Chrome executable path in registry
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe") as key:
                        chrome_path, _ = winreg.QueryValueEx(key, "")
                        if os.path.exists(chrome_path) and chrome_path not in chrome_info["paths"]:
                            chrome_info["paths"].append(chrome_path)
                            chrome_info["found"] = True
                except (FileNotFoundError, OSError):
                    pass
                    
            except ImportError:
                # winreg not available (shouldn't happen on Windows, but just in case)
                pass
            
            # Method 3: Check if Chrome process is running
            try:
                result = subprocess.run([
                    "tasklist", "/FI", "IMAGENAME eq chrome.exe", "/FO", "CSV"
                ], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0 and "chrome.exe" in result.stdout:
                    chrome_info["process_running"] = True
                    chrome_info["found"] = True
            except Exception:
                pass
            
            # Method 4: Try PowerShell Get-ItemProperty
            try:
                powershell_script = '''
                try {
                    $chromeReg = Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Google\\Chrome\\BLBeacon" -ErrorAction SilentlyContinue
                    if ($chromeReg) {
                        Write-Host "Registry: $($chromeReg.version)"
                    }
                    
                    $chromePath = Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\chrome.exe" -ErrorAction SilentlyContinue
                    if ($chromePath) {
                        Write-Host "Path: $($chromePath.'(default)')"
                    }
                    
                    $chromeProcess = Get-Process -Name "chrome" -ErrorAction SilentlyContinue
                    if ($chromeProcess) {
                        Write-Host "Process: Running"
                    }
                } catch {}
                '''
                
                result = subprocess.run([
                    "powershell", "-Command", powershell_script
                ], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0 and result.stdout.strip():
                    chrome_info["found"] = True
                    if "Registry:" in result.stdout:
                        version_line = [line for line in result.stdout.split('\n') if 'Registry:' in line]
                        if version_line:
                            chrome_info["version"] = version_line[0].split('Registry:')[1].strip()
                    
                    if "Process: Running" in result.stdout:
                        chrome_info["process_running"] = True
                        
            except Exception:
                pass
            
            # Build details string
            if chrome_info["found"]:
                details_parts = []
                
                if chrome_info["paths"]:
                    details_parts.append(f"Found at: {chrome_info['paths'][0]}")
                
                if chrome_info["version"]:
                    details_parts.append(f"Version: {chrome_info['version']}")
                
                if chrome_info["registry_found"]:
                    details_parts.append("Registry: ✅")
                
                if chrome_info["process_running"]:
                    details_parts.append("Running: ✅")
                
                chrome_info["details"] = " | ".join(details_parts) if details_parts else "Chrome detected"
            else:
                chrome_info["details"] = "Chrome not found - Install Google Chrome for best WhatsApp Web experience"
            
            return chrome_info
            
        except Exception as e:
            logger.error(f"Chrome detection failed: {e}")
            return {
                "found": False,
                "details": f"Chrome detection error: {e}",
                "paths": [],
                "version": None,
                "registry_found": False,
                "process_running": False
            }

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
    
    def _show_windows_notification(self, title: str, message: str) -> bool:
        """Show Windows toast notification."""
        try:
            # Use PowerShell to show Windows 10/11 toast notification
            powershell_script = f'''
            Add-Type -AssemblyName System.Windows.Forms
            
            # Try Windows 10/11 toast notification first
            try {{
                [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
                
                $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
                $textNodes = $template.GetElementsByTagName("text")
                $textNodes.Item(0).AppendChild($template.CreateTextNode("{title}")) | Out-Null
                $textNodes.Item(1).AppendChild($template.CreateTextNode("{message}")) | Out-Null
                
                $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
                $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("CSC-Reach")
                $notifier.Show($toast)
                
                Write-Host "TOAST_SUCCESS"
            }} catch {{
                # Fallback to balloon tip
                Add-Type -AssemblyName System.Windows.Forms
                $balloon = New-Object System.Windows.Forms.NotifyIcon
                $balloon.Icon = [System.Drawing.SystemIcons]::Information
                $balloon.BalloonTipTitle = "{title}"
                $balloon.BalloonTipText = "{message}"
                $balloon.BalloonTipIcon = "Info"
                $balloon.Visible = $true
                $balloon.ShowBalloonTip(5000)
                
                Start-Sleep -Seconds 1
                $balloon.Dispose()
                
                Write-Host "BALLOON_SUCCESS"
            }}
            '''
            
            result = subprocess.run([
                "powershell", "-Command", powershell_script
            ], capture_output=True, text=True, timeout=5)
            
            success = result.returncode == 0 and ("TOAST_SUCCESS" in result.stdout or "BALLOON_SUCCESS" in result.stdout)
            
            if success:
                logger.debug(f"Windows notification shown: {title}")
            
            return success
            
        except Exception as e:
            logger.debug(f"Windows notification failed: {e}")
            return False

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
