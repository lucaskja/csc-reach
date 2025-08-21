"""
Advanced email composition features with rich formatting, HTML support, and preview capabilities.
"""

import html
import re
import tempfile
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .models import Customer, MessageTemplate
from ..utils.logger import get_logger
from ..core.i18n_manager import get_i18n_manager

logger = get_logger(__name__)


class EmailFormat(Enum):
    """Email format types."""
    PLAIN_TEXT = "plain"
    HTML = "html"
    RTF = "rtf"


class DeviceType(Enum):
    """Device types for email preview."""
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"


@dataclass
class EmailAttachment:
    """Email attachment information."""
    file_path: str
    display_name: Optional[str] = None
    content_type: Optional[str] = None
    size_bytes: int = 0
    is_valid: bool = True
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Validate attachment after initialization."""
        self._validate_attachment()
    
    def _validate_attachment(self) -> None:
        """Validate the attachment file."""
        try:
            path = Path(self.file_path)
            
            if not path.exists():
                self.is_valid = False
                self.error_message = "File does not exist"
                return
            
            if not path.is_file():
                self.is_valid = False
                self.error_message = "Path is not a file"
                return
            
            # Get file size
            self.size_bytes = path.stat().st_size
            
            # Check size limits (25MB for most email systems)
            max_size = 25 * 1024 * 1024  # 25MB
            if self.size_bytes > max_size:
                self.is_valid = False
                self.error_message = f"File too large ({self.size_bytes} bytes, max {max_size})"
                return
            
            # Set display name if not provided
            if not self.display_name:
                self.display_name = path.name
            
            # Detect content type if not provided
            if not self.content_type:
                self.content_type = self._detect_content_type(path)
            
            self.is_valid = True
            
        except Exception as e:
            self.is_valid = False
            self.error_message = f"Validation error: {e}"
    
    def _detect_content_type(self, path: Path) -> str:
        """Detect content type based on file extension."""
        extension_map = {
            '.txt': 'text/plain',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.zip': 'application/zip',
            '.csv': 'text/csv'
        }
        
        suffix = path.suffix.lower()
        return extension_map.get(suffix, 'application/octet-stream')


@dataclass
class EmailComposition:
    """Complete email composition with all elements."""
    to_address: str
    subject: str
    content: str
    format_type: EmailFormat = EmailFormat.PLAIN_TEXT
    html_content: Optional[str] = None
    attachments: List[EmailAttachment] = field(default_factory=list)
    custom_headers: Dict[str, str] = field(default_factory=dict)
    
    # Preview and validation
    character_count: int = 0
    estimated_size_kb: float = 0.0
    validation_errors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Calculate metrics after initialization."""
        self._calculate_metrics()
        self._validate_composition()
    
    def _calculate_metrics(self) -> None:
        """Calculate email metrics."""
        # Character count
        self.character_count = len(self.content)
        
        # Estimated size
        content_size = len(self.content.encode('utf-8'))
        if self.html_content:
            content_size += len(self.html_content.encode('utf-8'))
        
        attachment_size = sum(att.size_bytes for att in self.attachments if att.is_valid)
        
        self.estimated_size_kb = (content_size + attachment_size) / 1024
    
    def _validate_composition(self) -> None:
        """Validate the email composition."""
        errors = []
        
        # Validate email address
        if not self._is_valid_email(self.to_address):
            errors.append("Invalid email address")
        
        # Validate subject
        if not self.subject.strip():
            errors.append("Subject is required")
        
        # Validate content
        if not self.content.strip():
            errors.append("Content is required")
        
        # Validate attachments
        invalid_attachments = [att for att in self.attachments if not att.is_valid]
        if invalid_attachments:
            for att in invalid_attachments:
                errors.append(f"Invalid attachment: {att.display_name} - {att.error_message}")
        
        # Check total size
        if self.estimated_size_kb > 25 * 1024:  # 25MB
            errors.append(f"Email too large ({self.estimated_size_kb:.1f}KB, max 25MB)")
        
        self.validation_errors = errors
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email address format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def is_valid(self) -> bool:
        """Check if the composition is valid."""
        return len(self.validation_errors) == 0


class EmailComposer:
    """Advanced email composer with rich formatting and preview capabilities."""
    
    def __init__(self):
        """Initialize the email composer."""
        self.i18n_manager = get_i18n_manager()
        
        # HTML templates for different layouts
        self.html_templates = {
            'simple': self._get_simple_html_template(),
            'professional': self._get_professional_html_template(),
            'newsletter': self._get_newsletter_html_template()
        }
        
        # CSS styles for different device types
        self.device_styles = {
            DeviceType.DESKTOP: self._get_desktop_styles(),
            DeviceType.MOBILE: self._get_mobile_styles(),
            DeviceType.TABLET: self._get_tablet_styles()
        }
    
    def compose_email(
        self,
        customer: Customer,
        template: MessageTemplate,
        format_type: EmailFormat = EmailFormat.PLAIN_TEXT,
        attachments: Optional[List[str]] = None,
        custom_variables: Optional[Dict[str, str]] = None
    ) -> EmailComposition:
        """
        Compose an email with advanced formatting.
        
        Args:
            customer: Customer information
            template: Email template
            format_type: Desired email format
            attachments: List of attachment file paths
            custom_variables: Additional variables for template rendering
            
        Returns:
            EmailComposition object
        """
        try:
            # Render template with variables
            rendered = self._render_template_enhanced(template, customer, custom_variables)
            
            # Create base composition
            composition = EmailComposition(
                to_address=customer.email,
                subject=rendered.get('subject', ''),
                content=rendered.get('content', ''),
                format_type=format_type
            )
            
            # Generate HTML content if requested
            if format_type == EmailFormat.HTML:
                composition.html_content = self._convert_to_html(
                    composition.content,
                    template_style='professional'
                )
            
            # Process attachments
            if attachments:
                composition.attachments = self._process_attachments(attachments)
            
            logger.info(f"Email composed for {customer.email} ({format_type.value} format)")
            return composition
            
        except Exception as e:
            logger.error(f"Failed to compose email for {customer.email}: {e}")
            # Return a basic composition with error
            return EmailComposition(
                to_address=customer.email,
                subject="Composition Error",
                content=f"Error composing email: {e}",
                validation_errors=[str(e)]
            )
    
    def _render_template_enhanced(
        self,
        template: MessageTemplate,
        customer: Customer,
        custom_variables: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Enhanced template rendering with additional variables and formatting.
        
        Args:
            template: Message template
            customer: Customer data
            custom_variables: Additional variables
            
        Returns:
            Dictionary with rendered content
        """
        # Start with standard template rendering
        rendered = template.render(customer)
        
        # Add custom variables if provided
        if custom_variables:
            subject = rendered.get('subject', '')
            content = rendered.get('content', '')
            
            for key, value in custom_variables.items():
                placeholder = f"{{{key}}}"
                subject = subject.replace(placeholder, value)
                content = content.replace(placeholder, value)
            
            rendered['subject'] = subject
            rendered['content'] = content
        
        # Add system variables
        import datetime
        system_vars = {
            'current_date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'current_time': datetime.datetime.now().strftime('%H:%M'),
            'current_year': str(datetime.datetime.now().year)
        }
        
        for key, value in system_vars.items():
            placeholder = f"{{{key}}}"
            rendered['subject'] = rendered.get('subject', '').replace(placeholder, value)
            rendered['content'] = rendered.get('content', '').replace(placeholder, value)
        
        return rendered
    
    def _convert_to_html(self, plain_text: str, template_style: str = 'simple') -> str:
        """
        Convert plain text to HTML with professional formatting.
        
        Args:
            plain_text: Plain text content
            template_style: HTML template style to use
            
        Returns:
            HTML formatted content
        """
        if not plain_text:
            return ""
        
        # Escape HTML special characters
        html_content = html.escape(plain_text)
        
        # Convert line breaks to HTML
        html_content = html_content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Process paragraphs and line breaks
        paragraphs = html_content.split('\n\n')
        formatted_paragraphs = []
        
        for paragraph in paragraphs:
            if paragraph.strip():
                # Convert single line breaks within paragraphs to <br>
                formatted_paragraph = paragraph.replace('\n', '<br>')
                formatted_paragraphs.append(f'<p>{formatted_paragraph}</p>')
        
        body_content = '\n'.join(formatted_paragraphs)
        
        # Apply HTML template
        template = self.html_templates.get(template_style, self.html_templates['simple'])
        return template.format(content=body_content)
    
    def _process_attachments(self, attachment_paths: List[str]) -> List[EmailAttachment]:
        """
        Process and validate attachments.
        
        Args:
            attachment_paths: List of file paths
            
        Returns:
            List of EmailAttachment objects
        """
        attachments = []
        
        for path in attachment_paths:
            try:
                attachment = EmailAttachment(file_path=path)
                attachments.append(attachment)
                
                if attachment.is_valid:
                    logger.debug(f"Processed attachment: {attachment.display_name}")
                else:
                    logger.warning(f"Invalid attachment: {path} - {attachment.error_message}")
                    
            except Exception as e:
                logger.error(f"Failed to process attachment {path}: {e}")
                # Add invalid attachment for error reporting
                attachments.append(EmailAttachment(
                    file_path=path,
                    is_valid=False,
                    error_message=str(e)
                ))
        
        return attachments
    
    def create_preview(
        self,
        composition: EmailComposition,
        device_type: DeviceType = DeviceType.DESKTOP
    ) -> Dict[str, Any]:
        """
        Create email preview for different device types.
        
        Args:
            composition: Email composition
            device_type: Target device type
            
        Returns:
            Dictionary with preview information
        """
        preview = {
            'device_type': device_type.value,
            'to_address': composition.to_address,
            'subject': composition.subject,
            'content': composition.content,
            'format': composition.format_type.value,
            'character_count': composition.character_count,
            'estimated_size_kb': composition.estimated_size_kb,
            'attachment_count': len(composition.attachments),
            'valid_attachments': len([att for att in composition.attachments if att.is_valid]),
            'validation_errors': composition.validation_errors,
            'is_valid': composition.is_valid()
        }
        
        # Add HTML preview if available
        if composition.html_content:
            preview['html_content'] = self._apply_device_styles(
                composition.html_content,
                device_type
            )
        
        # Add attachment details
        if composition.attachments:
            preview['attachments'] = [
                {
                    'name': att.display_name,
                    'size_kb': att.size_bytes / 1024,
                    'type': att.content_type,
                    'valid': att.is_valid,
                    'error': att.error_message
                }
                for att in composition.attachments
            ]
        
        return preview
    
    def _apply_device_styles(self, html_content: str, device_type: DeviceType) -> str:
        """
        Apply device-specific CSS styles to HTML content.
        
        Args:
            html_content: HTML content
            device_type: Target device type
            
        Returns:
            HTML content with device-specific styles
        """
        styles = self.device_styles.get(device_type, self.device_styles[DeviceType.DESKTOP])
        
        # Insert styles into HTML
        if '<head>' in html_content:
            return html_content.replace('<head>', f'<head>\n<style>\n{styles}\n</style>')
        else:
            return f'<style>\n{styles}\n</style>\n{html_content}'
    
    def _get_simple_html_template(self) -> str:
        """Get simple HTML template."""
        return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email</title>
</head>
<body>
    <div class="email-container">
        {content}
    </div>
</body>
</html>'''
    
    def _get_professional_html_template(self) -> str:
        """Get professional HTML template."""
        return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .email-container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        p {{ margin-bottom: 16px; }}
        .signature {{ margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px; }}
    </style>
</head>
<body>
    <div class="email-container">
        {content}
    </div>
</body>
</html>'''
    
    def _get_newsletter_html_template(self) -> str:
        """Get newsletter HTML template."""
        return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Newsletter</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background-color: #f4f4f4; }}
        .email-container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        p {{ margin-bottom: 18px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .footer {{ margin-top: 40px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>Newsletter</h1>
        </div>
        {content}
        <div class="footer">
            <p>Thank you for reading!</p>
        </div>
    </div>
</body>
</html>'''
    
    def _get_desktop_styles(self) -> str:
        """Get desktop-specific CSS styles."""
        return '''
        .email-container { max-width: 800px; font-size: 14px; }
        p { margin-bottom: 16px; }
        h1 { font-size: 24px; }
        h2 { font-size: 20px; }
        '''
    
    def _get_mobile_styles(self) -> str:
        """Get mobile-specific CSS styles."""
        return '''
        .email-container { max-width: 100%; padding: 10px; font-size: 16px; }
        p { margin-bottom: 14px; }
        h1 { font-size: 22px; }
        h2 { font-size: 18px; }
        '''
    
    def _get_tablet_styles(self) -> str:
        """Get tablet-specific CSS styles."""
        return '''
        .email-container { max-width: 600px; font-size: 15px; }
        p { margin-bottom: 15px; }
        h1 { font-size: 23px; }
        h2 { font-size: 19px; }
        '''
    
    def validate_composition(self, composition: EmailComposition) -> Tuple[bool, List[str]]:
        """
        Validate email composition.
        
        Args:
            composition: Email composition to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        return composition.is_valid(), composition.validation_errors
    
    def get_composition_stats(self, composition: EmailComposition) -> Dict[str, Any]:
        """
        Get detailed statistics about the email composition.
        
        Args:
            composition: Email composition
            
        Returns:
            Dictionary with composition statistics
        """
        stats = {
            'character_count': composition.character_count,
            'word_count': len(composition.content.split()),
            'line_count': composition.content.count('\n') + 1,
            'paragraph_count': len([p for p in composition.content.split('\n\n') if p.strip()]),
            'estimated_size_kb': composition.estimated_size_kb,
            'attachment_count': len(composition.attachments),
            'valid_attachments': len([att for att in composition.attachments if att.is_valid]),
            'total_attachment_size_kb': sum(att.size_bytes for att in composition.attachments if att.is_valid) / 1024,
            'format_type': composition.format_type.value,
            'has_html': composition.html_content is not None,
            'validation_errors': len(composition.validation_errors),
            'is_valid': composition.is_valid()
        }
        
        return stats