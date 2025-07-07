"""
Custom exception classes for Multi-Channel Bulk Messaging System.
"""


class MultiChannelMessagingError(Exception):
    """Base exception class for the application."""
    pass


class ConfigurationError(MultiChannelMessagingError):
    """Raised when there's a configuration error."""
    pass


class ValidationError(MultiChannelMessagingError):
    """Raised when data validation fails."""
    pass


class CSVProcessingError(MultiChannelMessagingError):
    """Raised when CSV processing fails."""
    pass


class EmailServiceError(MultiChannelMessagingError):
    """Raised when email service operations fail."""
    pass


class OutlookIntegrationError(EmailServiceError):
    """Raised when Outlook integration fails."""
    pass


class QuotaExceededError(MultiChannelMessagingError):
    """Raised when daily quota is exceeded."""
    pass


class TemplateError(MultiChannelMessagingError):
    """Raised when template processing fails."""
    pass


class ServiceUnavailableError(MultiChannelMessagingError):
    """Raised when a required service is unavailable."""
    pass


class WhatsAppAPIError(ServiceUnavailableError):
    """Raised when WhatsApp Business API operations fail."""
    pass


class WhatsAppConfigurationError(ConfigurationError):
    """Raised when WhatsApp configuration is invalid or missing."""
    pass
