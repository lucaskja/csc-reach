"""
AWS-compliant WhatsApp Business API service for CSC-Reach internal tool.
Designed for Cloud Sales Center team use with proper security and compliance.
"""

import json
import time
import boto3
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..core.models import Customer, MessageTemplate, MessageRecord, MessageStatus
from ..utils.exceptions import WhatsAppAPIError, WhatsAppConfigurationError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AWSWhatsAppBusinessService:
    """
    AWS-compliant WhatsApp Business API service for internal CSC-Reach tool.
    
    Features:
    - Official WhatsApp Business API integration
    - AWS Secrets Manager for credential storage
    - CloudWatch logging integration
    - Rate limiting and quota management
    - Compliance with AWS internal tool standards
    """
    
    def __init__(
        self,
        secret_name: str = "csc-reach/whatsapp-credentials",
        region_name: str = "us-east-1",
        rate_limit_per_minute: int = 20,
        daily_message_limit: int = 1000
    ):
        """
        Initialize AWS WhatsApp Business service.
        
        Args:
            secret_name: AWS Secrets Manager secret name for WhatsApp credentials
            region_name: AWS region for Secrets Manager
            rate_limit_per_minute: Messages per minute limit
            daily_message_limit: Daily message limit for compliance
        """
        self.secret_name = secret_name
        self.region_name = region_name
        self.rate_limit_per_minute = rate_limit_per_minute
        self.daily_message_limit = daily_message_limit
        
        # Initialize AWS clients
        self.secrets_client = boto3.client('secretsmanager', region_name=region_name)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
        
        # Rate limiting tracking
        self.message_timestamps = []
        self.daily_message_count = 0
        self.last_reset_date = datetime.now().date()
        
        # Load credentials and initialize API client
        self.credentials = self._load_credentials()
        self.api_client = self._initialize_api_client()
        
        logger.info("AWS WhatsApp Business service initialized for CSC-Reach")
    
    def _load_credentials(self) -> Dict[str, str]:
        """
        Load WhatsApp Business API credentials from AWS Secrets Manager.
        
        Returns:
            Dictionary containing API credentials
            
        Raises:
            WhatsAppConfigurationError: If credentials cannot be loaded
        """
        try:
            response = self.secrets_client.get_secret_value(SecretId=self.secret_name)
            credentials = json.loads(response['SecretString'])
            
            required_keys = ['access_token', 'phone_number_id', 'business_account_id']
            missing_keys = [key for key in required_keys if key not in credentials]
            
            if missing_keys:
                raise WhatsAppConfigurationError(f"Missing credentials: {missing_keys}")
            
            logger.info("WhatsApp credentials loaded from AWS Secrets Manager")
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to load WhatsApp credentials: {e}")
            raise WhatsAppConfigurationError(f"Credential loading failed: {e}")
    
    def _initialize_api_client(self) -> requests.Session:
        """Initialize HTTP client for WhatsApp Business API."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers
        session.headers.update({
            'Authorization': f'Bearer {self.credentials["access_token"]}',
            'Content-Type': 'application/json',
            'User-Agent': 'CSC-Reach-AWS-Internal/1.0'
        })
        
        return session
    
    def _check_rate_limits(self) -> bool:
        """
        Check if message can be sent within rate limits.
        
        Returns:
            True if within limits, False otherwise
        """
        now = datetime.now()
        
        # Reset daily counter if new day
        if now.date() > self.last_reset_date:
            self.daily_message_count = 0
            self.last_reset_date = now.date()
        
        # Check daily limit
        if self.daily_message_count >= self.daily_message_limit:
            logger.warning(f"Daily message limit reached: {self.daily_message_limit}")
            return False
        
        # Check per-minute rate limit
        one_minute_ago = now - timedelta(minutes=1)
        self.message_timestamps = [ts for ts in self.message_timestamps if ts > one_minute_ago]
        
        if len(self.message_timestamps) >= self.rate_limit_per_minute:
            logger.warning(f"Rate limit reached: {self.rate_limit_per_minute}/minute")
            return False
        
        return True
    
    def _log_message_sent(self):
        """Log message sending for rate limiting and metrics."""
        now = datetime.now()
        self.message_timestamps.append(now)
        self.daily_message_count += 1
        
        # Send metrics to CloudWatch
        try:
            self.cloudwatch.put_metric_data(
                Namespace='CSC-Reach/WhatsApp',
                MetricData=[
                    {
                        'MetricName': 'MessagesSent',
                        'Value': 1,
                        'Unit': 'Count',
                        'Timestamp': now
                    },
                    {
                        'MetricName': 'DailyMessageCount',
                        'Value': self.daily_message_count,
                        'Unit': 'Count',
                        'Timestamp': now
                    }
                ]
            )
        except Exception as e:
            logger.warning(f"Failed to send CloudWatch metrics: {e}")
    
    def send_message(self, customer: Customer, template: MessageTemplate) -> bool:
        """
        Send WhatsApp message to a customer.
        
        Args:
            customer: Customer to send message to
            template: Message template to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check rate limits
            if not self._check_rate_limits():
                logger.warning(f"Rate limit exceeded, skipping message to {customer.phone}")
                return False
            
            # Validate phone number
            if not self._validate_phone_number(customer.phone):
                logger.warning(f"Invalid phone number: {customer.phone}")
                return False
            
            # Render template
            rendered = template.render(customer)
            whatsapp_content = rendered.get('whatsapp_content', rendered.get('content', ''))
            
            if not whatsapp_content:
                logger.warning("No WhatsApp content available")
                return False
            
            # Prepare API request
            url = f"https://graph.facebook.com/v18.0/{self.credentials['phone_number_id']}/messages"
            payload = {
                "messaging_product": "whatsapp",
                "to": customer.phone,
                "type": "text",
                "text": {
                    "body": whatsapp_content[:4096]  # WhatsApp character limit
                }
            }
            
            # Send message
            response = self.api_client.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                message_id = response_data.get('messages', [{}])[0].get('id')
                
                self._log_message_sent()
                logger.info(f"WhatsApp message sent to {customer.phone}, ID: {message_id}")
                return True
            else:
                logger.error(f"WhatsApp API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message to {customer.phone}: {e}")
            return False
    
    def send_bulk_messages(
        self,
        customers: List[Customer],
        template: MessageTemplate,
        delay_between_messages: float = 3.0
    ) -> List[MessageRecord]:
        """
        Send bulk WhatsApp messages with proper rate limiting.
        
        Args:
            customers: List of customers
            template: Message template
            delay_between_messages: Delay between messages in seconds
            
        Returns:
            List of message records
        """
        records = []
        
        logger.info(f"Starting bulk WhatsApp send to {len(customers)} recipients")
        
        for i, customer in enumerate(customers):
            try:
                # Create message record
                record = MessageRecord(customer=customer, template=template)
                record.channel = "whatsapp"
                record.status = MessageStatus.SENDING
                
                # Send message
                success = self.send_message(customer, template)
                
                if success:
                    record.mark_as_sent()
                    logger.info(f"Message {i+1}/{len(customers)} sent to {customer.phone}")
                else:
                    record.mark_as_failed("Failed to send WhatsApp message")
                    logger.warning(f"Message {i+1}/{len(customers)} failed to {customer.phone}")
                
                records.append(record)
                
                # Rate limiting delay
                if i < len(customers) - 1:
                    time.sleep(delay_between_messages)
                
            except Exception as e:
                record = MessageRecord(customer=customer, template=template)
                record.channel = "whatsapp"
                record.mark_as_failed(str(e))
                records.append(record)
                logger.error(f"Error processing message for {customer.phone}: {e}")
        
        successful = sum(1 for r in records if r.status == MessageStatus.SENT)
        failed = sum(1 for r in records if r.status == MessageStatus.FAILED)
        
        logger.info(f"Bulk WhatsApp send completed: {successful} successful, {failed} failed")
        
        # Send summary metrics to CloudWatch
        try:
            self.cloudwatch.put_metric_data(
                Namespace='CSC-Reach/WhatsApp',
                MetricData=[
                    {
                        'MetricName': 'BulkSendSuccess',
                        'Value': successful,
                        'Unit': 'Count'
                    },
                    {
                        'MetricName': 'BulkSendFailed',
                        'Value': failed,
                        'Unit': 'Count'
                    }
                ]
            )
        except Exception as e:
            logger.warning(f"Failed to send bulk metrics: {e}")
        
        return records
    
    def _validate_phone_number(self, phone: str) -> bool:
        """Validate phone number format for WhatsApp."""
        if not phone:
            return False
        
        # Remove formatting
        cleaned = phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
        
        # Check if digits only and reasonable length
        return cleaned.isdigit() and 7 <= len(cleaned) <= 15
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test WhatsApp Business API connection.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            url = f"https://graph.facebook.com/v18.0/{self.credentials['phone_number_id']}"
            response = self.api_client.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                phone_number = data.get('display_phone_number', 'Unknown')
                return True, f"Connected successfully. Phone: {phone_number}"
            else:
                return False, f"API error: {response.status_code}"
                
        except Exception as e:
            return False, f"Connection failed: {e}"
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get current usage statistics.
        
        Returns:
            Dictionary with usage information
        """
        return {
            "daily_messages_sent": self.daily_message_count,
            "daily_limit": self.daily_message_limit,
            "remaining_daily": self.daily_message_limit - self.daily_message_count,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "messages_last_minute": len([
                ts for ts in self.message_timestamps 
                if ts > datetime.now() - timedelta(minutes=1)
            ])
        }


class WhatsAppBusinessSetupGuide:
    """
    Guide for setting up WhatsApp Business API for AWS internal use.
    """
    
    @staticmethod
    def get_setup_instructions() -> str:
        """Get setup instructions for WhatsApp Business API."""
        return """
        WhatsApp Business API Setup for CSC-Reach (AWS Internal Tool)
        
        1. Create Meta Business Account:
           - Go to business.facebook.com
           - Create business account with AWS corporate email
           - Verify business information
        
        2. Set up WhatsApp Business API:
           - Apply for WhatsApp Business API access
           - Get phone number verified and approved
           - Obtain access token and phone number ID
        
        3. Store Credentials in AWS Secrets Manager:
           - Create secret: csc-reach/whatsapp-credentials
           - Store JSON with: access_token, phone_number_id, business_account_id
           - Set appropriate IAM permissions for CSC-Reach application
        
        4. Configure CloudWatch Monitoring:
           - Metrics will be sent to CSC-Reach/WhatsApp namespace
           - Set up alarms for rate limiting and daily quotas
           - Monitor message success/failure rates
        
        5. Compliance Considerations:
           - Ensure customer consent for WhatsApp messaging
           - Follow AWS data handling policies
           - Implement proper logging and audit trails
           - Regular review of message content and usage
        """
    
    @staticmethod
    def get_aws_iam_policy() -> Dict[str, Any]:
        """Get required IAM policy for CSC-Reach WhatsApp functionality."""
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "secretsmanager:GetSecretValue"
                    ],
                    "Resource": "arn:aws:secretsmanager:*:*:secret:csc-reach/whatsapp-credentials*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "cloudwatch:PutMetricData"
                    ],
                    "Resource": "*",
                    "Condition": {
                        "StringEquals": {
                            "cloudwatch:namespace": "CSC-Reach/WhatsApp"
                        }
                    }
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "arn:aws:logs:*:*:log-group:/aws/csc-reach/*"
                }
            ]
        }
