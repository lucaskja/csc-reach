"""
Enhanced WhatsApp Business API client with advanced connection pooling, retry logic, and comprehensive error handling.
"""

import json
import time
import threading
from typing import Dict, List, Optional, Tuple, Any, Callable
from urllib.parse import urljoin
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.poolmanager import PoolManager

from ...utils.exceptions import WhatsAppAPIError, ServiceUnavailableError, QuotaExceededError
from ...utils.logger import get_logger
from ...core.i18n_manager import get_i18n_manager
from ...core.rate_limiter import IntelligentRateLimiter, QuotaType, QuotaConfig, WHATSAPP_BUSINESS_QUOTAS
from ...core.webhook_manager import WhatsAppDeliverySystem, MessageStatus

logger = get_logger(__name__)
i18n = get_i18n_manager()


@dataclass
class APIHealthMetrics:
    """API health monitoring metrics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limited_requests: int = 0
    average_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100.0
    
    @property
    def is_healthy(self) -> bool:
        """Check if API is considered healthy."""
        return (
            self.consecutive_failures < 5 and
            self.success_rate > 80.0 and
            (self.last_request_time is None or 
             datetime.now() - self.last_request_time < timedelta(minutes=5))
        )





class EnhancedHTTPAdapter(HTTPAdapter):
    """Enhanced HTTP adapter with connection pooling and monitoring."""
    
    def __init__(self, pool_connections=10, pool_maxsize=20, max_retries=3, **kwargs):
        self.pool_connections = pool_connections
        self.pool_maxsize = pool_maxsize
        super().__init__(pool_connections=pool_connections, pool_maxsize=pool_maxsize, max_retries=max_retries, **kwargs)


class WhatsAppAPIClient:
    """
    Enhanced WhatsApp Business API client with advanced features.
    
    Features:
    - Advanced connection pooling and retry logic
    - Comprehensive error handling for all WhatsApp API error codes
    - Request/response logging for debugging and analytics
    - API health monitoring and alerting
    - Intelligent rate limiting with burst capacity
    - Webhook support for delivery status tracking
    """
    
    # WhatsApp Business API endpoints
    CLOUD_API_BASE_URL = "https://graph.facebook.com/v18.0"
    
    # WhatsApp API error codes and their meanings
    ERROR_CODES = {
        100: "Invalid parameter",
        102: "Session expired",
        131009: "Parameter value is not valid",
        131014: "Request limit reached",
        131016: "Service temporarily unavailable",
        131021: "Recipient phone number not valid",
        131026: "Message undeliverable",
        131031: "Unsupported message type",
        131047: "Re-engagement message",
        131051: "Unsupported message type for recipient",
        132000: "Generic user error",
        132001: "User's number is part of an experiment",
        132005: "User phone number not valid",
        132007: "User has not accepted our new Terms of Service and Privacy Policy",
        132012: "User's WhatsApp client version is not supported",
        132015: "User has been blocked by business",
        132016: "User has blocked business",
        133000: "Generic system error",
        133004: "Request timeout",
        133005: "Service unavailable",
        133006: "Service overloaded",
        133008: "Could not display message",
        133009: "Message could not be sent",
        133010: "Message could not be delivered",
        135000: "Generic business error",
        135001: "Business account is restricted",
        135005: "Business phone number quality is too low",
        136000: "Generic template error",
        136001: "Template does not exist",
        136002: "Template name does not exist",
        136003: "Template parameter count mismatch",
        136004: "Template format does not match",
        136005: "Template language not supported"
    }
    
    def __init__(
        self, 
        access_token: str, 
        phone_number_id: str,
        api_version: str = "v18.0",
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        pool_connections: int = 10,
        pool_maxsize: int = 20,
        enable_health_monitoring: bool = True,
        health_check_callback: Optional[Callable[[APIHealthMetrics], None]] = None,
        webhook_secret: Optional[str] = None,
        enable_delivery_tracking: bool = True
    ):
        """
        Initialize enhanced WhatsApp API client.
        
        Args:
            access_token: WhatsApp Business API access token
            phone_number_id: Phone number ID for sending messages
            api_version: API version to use (default: v18.0)
            base_url: Custom base URL for on-premises API (optional)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            pool_connections: Number of connection pools
            pool_maxsize: Maximum size of connection pool
            enable_health_monitoring: Enable API health monitoring
            health_check_callback: Callback function for health status changes
            webhook_secret: Secret for webhook signature verification
            enable_delivery_tracking: Enable message delivery tracking
        """
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.api_version = api_version
        self.base_url = base_url or self.CLOUD_API_BASE_URL
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Health monitoring
        self.enable_health_monitoring = enable_health_monitoring
        self.health_metrics = APIHealthMetrics()
        self.health_check_callback = health_check_callback
        self._health_lock = threading.Lock()
        
        # Advanced rate limiting with intelligent quota management
        self.rate_limiter = IntelligentRateLimiter(
            quota_configs=WHATSAPP_BUSINESS_QUOTAS,
            alert_callback=self._handle_quota_alert,
            enable_persistence=True
        )
        self._rate_limit_lock = threading.Lock()
        
        # Request logging
        self.request_logs: List[Dict[str, Any]] = []
        self._log_lock = threading.Lock()
        
        # Delivery tracking system
        self.delivery_system: Optional[WhatsAppDeliverySystem] = None
        if enable_delivery_tracking and webhook_secret:
            self.delivery_system = WhatsAppDeliverySystem(
                webhook_secret=webhook_secret,
                event_callback=self._handle_webhook_event
            )
        
        # Configure enhanced session with connection pooling
        self.session = requests.Session()
        
        # Enhanced retry strategy with exponential backoff
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=2,  # Exponential backoff
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"],
            raise_on_status=False  # Handle status codes manually
        )
        
        # Use enhanced adapter with connection pooling
        adapter = EnhancedHTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=retry_strategy
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'CSC-Reach-Enhanced/2.0',
            'Accept': 'application/json'
        })
        
        logger.info(i18n.tr("whatsapp_api_client_initialized"))
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Make HTTP request to WhatsApp API with enhanced error handling and monitoring.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request payload
            params: Query parameters
            retry_count: Current retry attempt count
            
        Returns:
            API response as dictionary
            
        Raises:
            WhatsAppAPIError: If API request fails
            QuotaExceededError: If rate limits are exceeded
        """
        # Check rate limits before making request using intelligent rate limiter
        can_proceed, reason, details = self.rate_limiter.can_make_request(QuotaType.MESSAGES_PER_MINUTE)
        if not can_proceed:
            logger.warning(f"Rate limit exceeded: {reason}")
            
            # If there's a wait time, we could queue the request
            wait_seconds = details.get('wait_seconds')
            if wait_seconds and wait_seconds < 60:  # Only wait for short delays
                logger.info(f"Waiting {wait_seconds:.1f} seconds for rate limit...")
                time.sleep(wait_seconds)
                # Retry the check
                can_proceed, reason, details = self.rate_limiter.can_make_request(QuotaType.MESSAGES_PER_MINUTE)
                if not can_proceed:
                    raise QuotaExceededError(reason)
            else:
                raise QuotaExceededError(reason)
        
        url = urljoin(self.base_url, endpoint)
        request_start_time = datetime.now()
        
        # Log request details (sanitized)
        request_log = {
            "timestamp": request_start_time.isoformat(),
            "method": method,
            "endpoint": endpoint,
            "has_data": data is not None,
            "has_params": params is not None,
            "retry_count": retry_count
        }
        
        try:
            logger.debug(f"Making {method} request to {endpoint} (attempt {retry_count + 1})")
            
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )
            
            response_time = (datetime.now() - request_start_time).total_seconds()
            
            # Update request log
            request_log.update({
                "status_code": response.status_code,
                "response_time": response_time,
                "success": response.ok
            })
            
            # Handle specific status codes
            if response.status_code == 429:
                # Rate limiting
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited. Retry after {retry_after} seconds")
                
                request_log["rate_limited"] = True
                request_log["retry_after"] = retry_after
                
                with self._health_lock:
                    self.health_metrics.rate_limited_requests += 1
                
                # Wait and retry if we haven't exceeded max retries
                if retry_count < self.max_retries:
                    time.sleep(retry_after)
                    return self._make_request(method, endpoint, data, params, retry_count + 1)
                else:
                    raise QuotaExceededError(i18n.tr("rate_limit_max_retries_exceeded"))
            
            # Parse response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"text": response.text, "raw_response": True}
            
            # Handle API errors
            if not response.ok:
                error_info = self._extract_detailed_error_info(response_data, response.status_code)
                request_log["error"] = error_info
                
                logger.error(f"API request failed: {error_info['message']}")
                
                # Update health metrics
                with self._health_lock:
                    self.health_metrics.failed_requests += 1
                    self.health_metrics.consecutive_failures += 1
                    self.health_metrics.last_error = error_info['message']
                
                # Determine if we should retry based on error type
                if self._should_retry_error(error_info['code'], retry_count):
                    wait_time = min(2 ** retry_count, 30)  # Exponential backoff, max 30s
                    logger.info(f"Retrying request in {wait_time} seconds...")
                    time.sleep(wait_time)
                    return self._make_request(method, endpoint, data, params, retry_count + 1)
                
                # Raise appropriate exception based on error code
                if error_info['code'] in [131014, 131016]:
                    raise QuotaExceededError(error_info['message'])
                else:
                    raise WhatsAppAPIError(error_info['message'])
            
            # Success - update metrics and rate limiting
            using_burst = details.get('using_burst', False)
            self.rate_limiter.record_request(QuotaType.MESSAGES_PER_MINUTE, use_burst=using_burst)
            
            # Also record for hourly and daily quotas
            self.rate_limiter.record_request(QuotaType.MESSAGES_PER_HOUR, use_burst=False)
            self.rate_limiter.record_request(QuotaType.MESSAGES_PER_DAY, use_burst=False)
            
            with self._health_lock:
                self.health_metrics.successful_requests += 1
                self.health_metrics.consecutive_failures = 0
                self.health_metrics.last_request_time = datetime.now()
                
                # Update average response time
                total_requests = self.health_metrics.total_requests
                current_avg = self.health_metrics.average_response_time
                self.health_metrics.average_response_time = (
                    (current_avg * total_requests + response_time) / (total_requests + 1)
                )
            
            logger.debug(f"API request successful in {response_time:.2f}s")
            return response_data
            
        except requests.exceptions.Timeout as e:
            request_log["error"] = {"type": "timeout", "message": str(e)}
            logger.error(f"Request timeout: {e}")
            
            with self._health_lock:
                self.health_metrics.failed_requests += 1
                self.health_metrics.consecutive_failures += 1
            
            if retry_count < self.max_retries:
                wait_time = min(2 ** retry_count, 30)
                logger.info(f"Retrying after timeout in {wait_time} seconds...")
                time.sleep(wait_time)
                return self._make_request(method, endpoint, data, params, retry_count + 1)
            
            raise WhatsAppAPIError(i18n.tr("request_timeout_exceeded"))
            
        except requests.exceptions.ConnectionError as e:
            request_log["error"] = {"type": "connection", "message": str(e)}
            logger.error(f"Connection error: {e}")
            
            with self._health_lock:
                self.health_metrics.failed_requests += 1
                self.health_metrics.consecutive_failures += 1
            
            if retry_count < self.max_retries:
                wait_time = min(2 ** retry_count, 30)
                logger.info(f"Retrying after connection error in {wait_time} seconds...")
                time.sleep(wait_time)
                return self._make_request(method, endpoint, data, params, retry_count + 1)
            
            raise ServiceUnavailableError(i18n.tr("whatsapp_service_unavailable"))
            
        except requests.exceptions.RequestException as e:
            request_log["error"] = {"type": "request", "message": str(e)}
            logger.error(f"Request failed: {e}")
            
            with self._health_lock:
                self.health_metrics.failed_requests += 1
                self.health_metrics.consecutive_failures += 1
            
            raise WhatsAppAPIError(f"Request failed: {e}")
            
        finally:
            # Update total request count and log the request
            with self._health_lock:
                self.health_metrics.total_requests += 1
            
            with self._log_lock:
                self.request_logs.append(request_log)
                # Keep only last 1000 requests to prevent memory issues
                if len(self.request_logs) > 1000:
                    self.request_logs = self.request_logs[-1000:]
            
            # Trigger health check callback if configured
            if self.enable_health_monitoring and self.health_check_callback:
                try:
                    self.health_check_callback(self.health_metrics)
                except Exception as e:
                    logger.warning(f"Health check callback failed: {e}")
    
    def _extract_detailed_error_info(self, response_data: Dict, status_code: int) -> Dict[str, Any]:
        """
        Extract detailed error information from API response.
        
        Args:
            response_data: API response data
            status_code: HTTP status code
            
        Returns:
            Dictionary with error details
        """
        error_info = {
            "code": status_code,
            "message": "Unknown error",
            "type": "unknown",
            "retryable": False
        }
        
        if 'error' in response_data:
            error = response_data['error']
            if isinstance(error, dict):
                # Extract WhatsApp-specific error code
                error_code = error.get('code', status_code)
                error_subcode = error.get('error_subcode')
                error_message = error.get('message', 'Unknown error')
                
                # Get human-readable error description
                if error_code in self.ERROR_CODES:
                    error_description = self.ERROR_CODES[error_code]
                    error_message = f"{error_description}: {error_message}"
                
                error_info.update({
                    "code": error_code,
                    "subcode": error_subcode,
                    "message": error_message,
                    "type": error.get('type', 'api_error'),
                    "retryable": self._is_retryable_error(error_code)
                })
            else:
                error_info["message"] = str(error)
        else:
            error_info["message"] = response_data.get('message', f'HTTP {status_code} error')
        
        return error_info
    
    def _is_retryable_error(self, error_code: int) -> bool:
        """
        Determine if an error is retryable.
        
        Args:
            error_code: WhatsApp API error code
            
        Returns:
            True if error is retryable
        """
        # Retryable errors (temporary issues)
        retryable_codes = {
            131016,  # Service temporarily unavailable
            133000,  # Generic system error
            133004,  # Request timeout
            133005,  # Service unavailable
            133006,  # Service overloaded
        }
        
        return error_code in retryable_codes
    
    def _should_retry_error(self, error_code: int, retry_count: int) -> bool:
        """
        Determine if we should retry a request based on error code and retry count.
        
        Args:
            error_code: WhatsApp API error code
            retry_count: Current retry count
            
        Returns:
            True if should retry
        """
        return (
            retry_count < self.max_retries and
            self._is_retryable_error(error_code)
        )
    
    def send_text_message(self, to: str, message: str) -> Dict[str, Any]:
        """
        Send a text message via WhatsApp.
        
        Args:
            to: Recipient phone number (with country code)
            message: Message text
            
        Returns:
            API response with message ID and status
            
        Raises:
            WhatsAppAPIError: If message sending fails
        """
        # Validate phone number format
        if not self.validate_phone_number(to):
            raise WhatsAppAPIError(f"Invalid phone number format: {to}")
        
        # Prepare message payload
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        endpoint = f"{self.phone_number_id}/messages"
        
        try:
            response = self._make_request("POST", endpoint, payload)
            
            # Extract message ID from response
            message_id = None
            if 'messages' in response and response['messages']:
                message_id = response['messages'][0].get('id')
            
            # Start delivery tracking if enabled
            if self.delivery_system and message_id:
                self.delivery_system.track_message(
                    message_id=message_id,
                    phone_number=to,
                    message_content=message
                )
                
                # Update status to sent
                self.delivery_system.delivery_tracker.update_message_status(
                    message_id=message_id,
                    status=MessageStatus.SENT
                )
            
            logger.info(f"Text message sent successfully. Message ID: {message_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to send text message to {to}: {e}")
            raise WhatsAppAPIError(f"Failed to send text message: {e}")
    
    def send_template_message(
        self, 
        to: str, 
        template_name: str, 
        language_code: str = "en",
        parameters: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send a template message via WhatsApp.
        
        Args:
            to: Recipient phone number
            template_name: Name of the approved template
            language_code: Template language code (default: en)
            parameters: Template parameter values
            
        Returns:
            API response with message ID and status
        """
        # Validate phone number
        if not self.validate_phone_number(to):
            raise WhatsAppAPIError(f"Invalid phone number format: {to}")
        
        # Prepare template payload
        template_payload = {
            "name": template_name,
            "language": {
                "code": language_code
            }
        }
        
        # Add parameters if provided
        if parameters:
            template_payload["components"] = [{
                "type": "body",
                "parameters": [{"type": "text", "text": param} for param in parameters]
            }]
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": template_payload
        }
        
        endpoint = f"{self.phone_number_id}/messages"
        
        try:
            response = self._make_request("POST", endpoint, payload)
            
            message_id = None
            if 'messages' in response and response['messages']:
                message_id = response['messages'][0].get('id')
            
            # Start delivery tracking if enabled
            if self.delivery_system and message_id:
                self.delivery_system.track_message(
                    message_id=message_id,
                    phone_number=to,
                    template_name=template_name
                )
                
                # Update status to sent
                self.delivery_system.delivery_tracker.update_message_status(
                    message_id=message_id,
                    status=MessageStatus.SENT
                )
            
            logger.info(f"Template message sent successfully. Message ID: {message_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to send template message to {to}: {e}")
            raise WhatsAppAPIError(f"Failed to send template message: {e}")
    
    def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """
        Get the delivery status of a message.
        
        Args:
            message_id: WhatsApp message ID
            
        Returns:
            Message status information
        """
        endpoint = f"{message_id}"
        
        try:
            response = self._make_request("GET", endpoint)
            logger.debug(f"Retrieved status for message {message_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to get message status for {message_id}: {e}")
            raise WhatsAppAPIError(f"Failed to get message status: {e}")
    
    def validate_phone_number(self, phone: str) -> bool:
        """
        Validate phone number format for WhatsApp.
        
        Args:
            phone: Phone number to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not phone:
            return False
        
        # Remove common formatting characters
        cleaned = phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
        
        # Check if it's all digits and has reasonable length
        if not cleaned.isdigit():
            return False
        
        # WhatsApp phone numbers should be 7-15 digits
        if len(cleaned) < 7 or len(cleaned) > 15:
            return False
        
        return True
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get WhatsApp Business Account information.
        
        Returns:
            Account information including phone number details
        """
        endpoint = f"{self.phone_number_id}"
        
        try:
            response = self._make_request("GET", endpoint)
            logger.info("Retrieved WhatsApp account information")
            return response
            
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise WhatsAppAPIError(f"Failed to get account info: {e}")
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test connection to WhatsApp Business API.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            account_info = self.get_account_info()
            
            # Check if we got valid account information
            if 'id' in account_info:
                phone_number = account_info.get('display_phone_number', 'Unknown')
                return True, f"Connected successfully. Phone: {phone_number}"
            else:
                return False, "Invalid response from WhatsApp API"
                
        except WhatsAppAPIError as e:
            return False, f"Connection failed: {e}"
        except Exception as e:
            return False, f"Unexpected error: {e}"
    
    def get_business_profile(self) -> Dict[str, Any]:
        """
        Get WhatsApp Business Profile information.
        
        Returns:
            Business profile data
        """
        endpoint = f"{self.phone_number_id}/whatsapp_business_profile"
        
        try:
            response = self._make_request("GET", endpoint)
            logger.info("Retrieved WhatsApp business profile")
            return response
            
        except Exception as e:
            logger.error(f"Failed to get business profile: {e}")
            raise WhatsAppAPIError(f"Failed to get business profile: {e}")
    
    def get_health_metrics(self) -> APIHealthMetrics:
        """
        Get current API health metrics.
        
        Returns:
            Current health metrics
        """
        with self._health_lock:
            return APIHealthMetrics(
                total_requests=self.health_metrics.total_requests,
                successful_requests=self.health_metrics.successful_requests,
                failed_requests=self.health_metrics.failed_requests,
                rate_limited_requests=self.health_metrics.rate_limited_requests,
                average_response_time=self.health_metrics.average_response_time,
                last_request_time=self.health_metrics.last_request_time,
                last_error=self.health_metrics.last_error,
                consecutive_failures=self.health_metrics.consecutive_failures
            )
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status from intelligent rate limiter.
        
        Returns:
            Comprehensive rate limit information
        """
        return self.rate_limiter.get_quota_status()
    
    def _handle_quota_alert(self, alert):
        """
        Handle quota alerts from the rate limiter.
        
        Args:
            alert: QuotaAlert object with alert information
        """
        logger.warning(f"Quota alert: {alert.message}")
        
        # Update health metrics based on alert level
        with self._health_lock:
            if alert.level.value in ['critical', 'emergency']:
                self.health_metrics.last_error = alert.message
            
        # You could also trigger additional actions here like:
        # - Sending notifications
        # - Adjusting request priorities
        # - Implementing circuit breaker patterns
    
    def get_request_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent request logs for debugging and analytics.
        
        Args:
            limit: Maximum number of logs to return
            
        Returns:
            List of request logs
        """
        with self._log_lock:
            return self.request_logs[-limit:] if self.request_logs else []
    
    def reset_health_metrics(self):
        """Reset health metrics (useful for testing or periodic resets)."""
        with self._health_lock:
            self.health_metrics = APIHealthMetrics()
        logger.info("Health metrics reset")
    
    def update_rate_limits(
        self, 
        requests_per_minute: Optional[int] = None,
        requests_per_hour: Optional[int] = None,
        requests_per_day: Optional[int] = None,
        burst_capacity_minute: Optional[int] = None,
        burst_capacity_hour: Optional[int] = None,
        burst_capacity_day: Optional[int] = None
    ):
        """
        Update rate limit configuration with advanced options.
        
        Args:
            requests_per_minute: New per-minute limit
            requests_per_hour: New per-hour limit
            requests_per_day: New per-day limit
            burst_capacity_minute: Burst capacity for per-minute quota
            burst_capacity_hour: Burst capacity for per-hour quota
            burst_capacity_day: Burst capacity for per-day quota
        """
        # Update minute quota
        if requests_per_minute is not None or burst_capacity_minute is not None:
            current_config = None
            for config in WHATSAPP_BUSINESS_QUOTAS:
                if config.quota_type == QuotaType.MESSAGES_PER_MINUTE:
                    current_config = config
                    break
            
            if current_config:
                new_config = QuotaConfig(
                    quota_type=QuotaType.MESSAGES_PER_MINUTE,
                    limit=requests_per_minute or current_config.limit,
                    window_seconds=current_config.window_seconds,
                    burst_capacity=burst_capacity_minute or current_config.burst_capacity,
                    warning_threshold=current_config.warning_threshold,
                    critical_threshold=current_config.critical_threshold
                )
                self.rate_limiter.update_quota_config(QuotaType.MESSAGES_PER_MINUTE, new_config)
        
        # Update hour quota
        if requests_per_hour is not None or burst_capacity_hour is not None:
            current_config = None
            for config in WHATSAPP_BUSINESS_QUOTAS:
                if config.quota_type == QuotaType.MESSAGES_PER_HOUR:
                    current_config = config
                    break
            
            if current_config:
                new_config = QuotaConfig(
                    quota_type=QuotaType.MESSAGES_PER_HOUR,
                    limit=requests_per_hour or current_config.limit,
                    window_seconds=current_config.window_seconds,
                    burst_capacity=burst_capacity_hour or current_config.burst_capacity,
                    warning_threshold=current_config.warning_threshold,
                    critical_threshold=current_config.critical_threshold
                )
                self.rate_limiter.update_quota_config(QuotaType.MESSAGES_PER_HOUR, new_config)
        
        # Update day quota
        if requests_per_day is not None or burst_capacity_day is not None:
            current_config = None
            for config in WHATSAPP_BUSINESS_QUOTAS:
                if config.quota_type == QuotaType.MESSAGES_PER_DAY:
                    current_config = config
                    break
            
            if current_config:
                new_config = QuotaConfig(
                    quota_type=QuotaType.MESSAGES_PER_DAY,
                    limit=requests_per_day or current_config.limit,
                    window_seconds=current_config.window_seconds,
                    burst_capacity=burst_capacity_day or current_config.burst_capacity,
                    warning_threshold=current_config.warning_threshold,
                    critical_threshold=current_config.critical_threshold,
                    reset_time=current_config.reset_time
                )
                self.rate_limiter.update_quota_config(QuotaType.MESSAGES_PER_DAY, new_config)
        
        logger.info(f"Rate limits updated: {self.get_rate_limit_status()}")
    
    def get_quota_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent quota alerts.
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of recent quota alerts
        """
        alerts = self.rate_limiter.get_recent_alerts(limit)
        return [alert.to_dict() for alert in alerts]
    
    def reset_quota(self, quota_type: str) -> bool:
        """
        Reset a specific quota (useful for testing).
        
        Args:
            quota_type: Type of quota to reset ('minute', 'hour', 'day')
            
        Returns:
            True if reset successfully
        """
        quota_type_map = {
            'minute': QuotaType.MESSAGES_PER_MINUTE,
            'hour': QuotaType.MESSAGES_PER_HOUR,
            'day': QuotaType.MESSAGES_PER_DAY
        }
        
        if quota_type not in quota_type_map:
            logger.warning(f"Unknown quota type: {quota_type}")
            return False
        
        return self.rate_limiter.reset_quota(quota_type_map[quota_type])
    
    def queue_message_request(
        self,
        to: str,
        message: str,
        priority: int = 5,
        callback: Optional[Callable] = None
    ) -> str:
        """
        Queue a message request to be sent when quota allows.
        
        Args:
            to: Recipient phone number
            message: Message text
            priority: Request priority (lower = higher priority)
            callback: Optional callback when message is sent
            
        Returns:
            Request ID for tracking
        """
        def send_message_callback():
            try:
                result = self.send_text_message(to, message)
                if callback:
                    callback(True, result)
                return result
            except Exception as e:
                if callback:
                    callback(False, str(e))
                raise
        
        return self.rate_limiter.queue_request(
            quota_type=QuotaType.MESSAGES_PER_MINUTE,
            callback=send_message_callback,
            priority=priority
        )
    
    def process_webhook(self, payload: str, signature: Optional[str] = None) -> bool:
        """
        Process incoming webhook payload for delivery status updates.
        
        Args:
            payload: JSON webhook payload
            signature: Webhook signature for verification
            
        Returns:
            True if processed successfully
        """
        if not self.delivery_system:
            logger.warning("Delivery system not initialized - cannot process webhook")
            return False
        
        return self.delivery_system.process_webhook(payload, signature)
    
    def get_delivery_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get delivery analytics for the specified time period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Delivery analytics data
        """
        if not self.delivery_system:
            return {"error": "Delivery system not initialized"}
        
        analytics = self.delivery_system.get_analytics(days)
        return analytics.to_dict()
    
    def get_message_delivery_status(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Get delivery status for a specific message.
        
        Args:
            message_id: Message identifier
            
        Returns:
            Message delivery record or None
        """
        if not self.delivery_system:
            return None
        
        record = self.delivery_system.delivery_tracker.get_message_status(message_id)
        return record.to_dict() if record else None
    
    def get_failed_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get failed messages that can be retried.
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of failed message records
        """
        if not self.delivery_system:
            return []
        
        failed_messages = self.delivery_system.get_failed_messages(limit)
        return [msg.to_dict() for msg in failed_messages]
    
    def retry_failed_message(self, message_id: str) -> bool:
        """
        Retry a failed message.
        
        Args:
            message_id: Message identifier
            
        Returns:
            True if retry was initiated successfully
        """
        if not self.delivery_system:
            return False
        
        return self.delivery_system.retry_failed_message(message_id)
    
    def _handle_webhook_event(self, event):
        """
        Handle webhook events from the delivery system.
        
        Args:
            event: WebhookEvent object
        """
        logger.debug(f"Received webhook event: {event.event_type.value}")
        
        # Update health metrics based on delivery events
        if event.event_type.value == "message_status":
            status = event.data.get('status')
            if status == 'failed':
                with self._health_lock:
                    self.health_metrics.consecutive_failures += 1
            elif status in ['delivered', 'read']:
                with self._health_lock:
                    self.health_metrics.consecutive_failures = 0
        
        # You could add additional webhook event handling here
        # For example: sending notifications, updating UI, etc.
    
    def is_healthy(self) -> bool:
        """
        Check if the API client is in a healthy state.
        
        Returns:
            True if healthy, False otherwise
        """
        return self.health_metrics.is_healthy
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive analytics summary.
        
        Returns:
            Analytics data including health, rate limits, and performance
        """
        health_metrics = self.get_health_metrics()
        rate_limit_status = self.get_rate_limit_status()
        
        return {
            "health": {
                "is_healthy": health_metrics.is_healthy,
                "success_rate": health_metrics.success_rate,
                "total_requests": health_metrics.total_requests,
                "successful_requests": health_metrics.successful_requests,
                "failed_requests": health_metrics.failed_requests,
                "rate_limited_requests": health_metrics.rate_limited_requests,
                "average_response_time": health_metrics.average_response_time,
                "consecutive_failures": health_metrics.consecutive_failures,
                "last_error": health_metrics.last_error
            },
            "rate_limits": rate_limit_status,
            "performance": {
                "average_response_time": health_metrics.average_response_time,
                "last_request_time": health_metrics.last_request_time.isoformat() if health_metrics.last_request_time else None
            }
        }
    
    def shutdown(self):
        """Shutdown the API client and clean up resources."""
        logger.info("Shutting down WhatsApp API client...")
        
        # Shutdown rate limiter
        if hasattr(self, 'rate_limiter'):
            self.rate_limiter.shutdown()
        
        # Shutdown delivery system
        if hasattr(self, 'delivery_system') and self.delivery_system:
            # Clean up old records before shutdown
            try:
                self.delivery_system.cleanup_old_records(days=90)
            except Exception as e:
                logger.warning(f"Failed to cleanup old delivery records: {e}")
        
        # Close session
        if hasattr(self, 'session'):
            self.session.close()
        
        logger.info("WhatsApp API client shutdown complete")
    
    def __del__(self):
        """Clean up session on destruction."""
        try:
            self.shutdown()
        except:
            pass
