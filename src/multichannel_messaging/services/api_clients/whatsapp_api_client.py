"""
WhatsApp Business API client for sending messages and managing WhatsApp communication.
"""

import json
import time
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ...utils.exceptions import WhatsAppAPIError, ServiceUnavailableError
from ...utils.logger import get_logger

logger = get_logger(__name__)


class WhatsAppAPIClient:
    """
    Client for WhatsApp Business API integration.
    
    Supports both Cloud API and On-Premises API configurations.
    """
    
    # WhatsApp Business API endpoints
    CLOUD_API_BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(
        self, 
        access_token: str, 
        phone_number_id: str,
        api_version: str = "v18.0",
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize WhatsApp API client.
        
        Args:
            access_token: WhatsApp Business API access token
            phone_number_id: Phone number ID for sending messages
            api_version: API version to use (default: v18.0)
            base_url: Custom base URL for on-premises API (optional)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.api_version = api_version
        self.base_url = base_url or self.CLOUD_API_BASE_URL
        self.timeout = timeout
        
        # Configure session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'CSC-Reach/1.0'
        })
        
        logger.info("WhatsApp API client initialized")
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to WhatsApp API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request payload
            params: Query parameters
            
        Returns:
            API response as dictionary
            
        Raises:
            WhatsAppAPIError: If API request fails
        """
        url = urljoin(self.base_url, endpoint)
        
        try:
            logger.debug(f"Making {method} request to {url}")
            
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )
            
            # Log request details (without sensitive data)
            logger.debug(f"Request URL: {url}")
            logger.debug(f"Response status: {response.status_code}")
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                # Retry the request
                return self._make_request(method, endpoint, data, params)
            
            # Parse response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"text": response.text}
            
            # Handle API errors
            if not response.ok:
                error_message = self._extract_error_message(response_data)
                logger.error(f"API request failed: {error_message}")
                raise WhatsAppAPIError(f"API request failed: {error_message}")
            
            logger.debug("API request successful")
            return response_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise WhatsAppAPIError(f"Request failed: {e}")
    
    def _extract_error_message(self, response_data: Dict) -> str:
        """Extract error message from API response."""
        if 'error' in response_data:
            error = response_data['error']
            if isinstance(error, dict):
                return error.get('message', str(error))
            return str(error)
        return response_data.get('message', 'Unknown error')
    
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
    
    def __del__(self):
        """Clean up session on destruction."""
        if hasattr(self, 'session'):
            self.session.close()
