"""
WhatsApp template management system with creation, submission, approval tracking, and analytics.

This module provides comprehensive WhatsApp Business API template management including:
- Template creation and submission workflow
- Template approval status tracking and notifications
- Template testing and preview functionality
- Template performance analytics and optimization suggestions
"""

import json
import time
import threading
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import re

from ..utils.logger import get_logger
from ..utils.exceptions import TemplateError, WhatsAppAPIError, ValidationError
from ..core.i18n_manager import get_i18n_manager

logger = get_logger(__name__)
i18n = get_i18n_manager()


class TemplateStatus(Enum):
    """WhatsApp template approval status."""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISABLED = "disabled"
    PAUSED = "paused"


class TemplateCategory(Enum):
    """WhatsApp template categories."""
    MARKETING = "marketing"
    UTILITY = "utility"
    AUTHENTICATION = "authentication"


class ComponentType(Enum):
    """WhatsApp template component types."""
    HEADER = "header"
    BODY = "body"
    FOOTER = "footer"
    BUTTONS = "buttons"


class ParameterType(Enum):
    """WhatsApp template parameter types."""
    TEXT = "text"
    CURRENCY = "currency"
    DATE_TIME = "date_time"
    IMAGE = "image"
    DOCUMENT = "document"
    VIDEO = "video"


@dataclass
class TemplateParameter:
    """WhatsApp template parameter definition."""
    type: ParameterType
    text: Optional[str] = None
    currency: Optional[Dict[str, Any]] = None
    date_time: Optional[Dict[str, Any]] = None
    image: Optional[Dict[str, str]] = None
    document: Optional[Dict[str, str]] = None
    video: Optional[Dict[str, str]] = None
    
    def validate(self) -> List[str]:
        """Validate parameter configuration."""
        errors = []
        
        if self.type == ParameterType.TEXT and not self.text:
            errors.append("Text parameter requires text value")
        elif self.type == ParameterType.CURRENCY and not self.currency:
            errors.append("Currency parameter requires currency configuration")
        elif self.type == ParameterType.DATE_TIME and not self.date_time:
            errors.append("DateTime parameter requires date_time configuration")
        elif self.type == ParameterType.IMAGE and not self.image:
            errors.append("Image parameter requires image configuration")
        elif self.type == ParameterType.DOCUMENT and not self.document:
            errors.append("Document parameter requires document configuration")
        elif self.type == ParameterType.VIDEO and not self.video:
            errors.append("Video parameter requires video configuration")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert parameter to WhatsApp API format."""
        result = {"type": self.type.value}
        
        if self.type == ParameterType.TEXT:
            result["text"] = self.text
        elif self.type == ParameterType.CURRENCY:
            result["currency"] = self.currency
        elif self.type == ParameterType.DATE_TIME:
            result["date_time"] = self.date_time
        elif self.type == ParameterType.IMAGE:
            result["image"] = self.image
        elif self.type == ParameterType.DOCUMENT:
            result["document"] = self.document
        elif self.type == ParameterType.VIDEO:
            result["video"] = self.video
        
        return result


@dataclass
class TemplateComponent:
    """WhatsApp template component (header, body, footer, buttons)."""
    type: ComponentType
    text: Optional[str] = None
    parameters: List[TemplateParameter] = field(default_factory=list)
    format: Optional[str] = None  # For header: TEXT, IMAGE, DOCUMENT, VIDEO
    example: Optional[Dict[str, Any]] = None
    buttons: Optional[List[Dict[str, Any]]] = None  # For button components
    
    def validate(self) -> List[str]:
        """Validate component configuration."""
        errors = []
        
        if self.type == ComponentType.BODY and not self.text:
            errors.append("Body component requires text")
        
        if self.type == ComponentType.HEADER and self.format:
            if self.format not in ["TEXT", "IMAGE", "DOCUMENT", "VIDEO"]:
                errors.append(f"Invalid header format: {self.format}")
        
        # Validate parameters
        for i, param in enumerate(self.parameters):
            param_errors = param.validate()
            for error in param_errors:
                errors.append(f"Parameter {i + 1}: {error}")
        
        # Validate parameter placeholders in text
        if self.text:
            placeholder_count = len(re.findall(r'\{\{\d+\}\}', self.text))
            if placeholder_count != len(self.parameters):
                errors.append(f"Parameter count mismatch: {placeholder_count} placeholders, {len(self.parameters)} parameters")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert component to WhatsApp API format."""
        result = {"type": self.type.value}
        
        if self.text:
            result["text"] = self.text
        
        if self.format:
            result["format"] = self.format
        
        if self.parameters:
            result["parameters"] = [param.to_dict() for param in self.parameters]
        
        if self.example:
            result["example"] = self.example
        
        if self.buttons:
            result["buttons"] = self.buttons
        
        return result


@dataclass
class WhatsAppTemplate:
    """WhatsApp Business API template."""
    name: str
    language: str
    category: TemplateCategory
    components: List[TemplateComponent] = field(default_factory=list)
    
    # Metadata
    id: Optional[str] = None
    status: TemplateStatus = TemplateStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    # Analytics
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    last_used: Optional[datetime] = None
    
    # Quality metrics
    quality_score: Optional[float] = None
    delivery_rate: Optional[float] = None
    read_rate: Optional[float] = None
    response_rate: Optional[float] = None
    
    def validate(self) -> List[str]:
        """Validate template configuration."""
        errors = []
        
        # Validate name
        if not self.name:
            errors.append("Template name is required")
        elif not re.match(r'^[a-z0-9_]+$', self.name):
            errors.append("Template name must contain only lowercase letters, numbers, and underscores")
        elif len(self.name) > 512:
            errors.append("Template name must be 512 characters or less")
        
        # Validate language
        if not self.language:
            errors.append("Template language is required")
        elif not re.match(r'^[a-z]{2}(_[A-Z]{2})?$', self.language):
            errors.append("Invalid language code format (use ISO 639-1 format like 'en' or 'en_US')")
        
        # Validate components
        if not self.components:
            errors.append("Template must have at least one component")
        
        body_count = sum(1 for c in self.components if c.type == ComponentType.BODY)
        if body_count != 1:
            errors.append("Template must have exactly one body component")
        
        header_count = sum(1 for c in self.components if c.type == ComponentType.HEADER)
        if header_count > 1:
            errors.append("Template can have at most one header component")
        
        footer_count = sum(1 for c in self.components if c.type == ComponentType.FOOTER)
        if footer_count > 1:
            errors.append("Template can have at most one footer component")
        
        # Validate each component
        for i, component in enumerate(self.components):
            component_errors = component.validate()
            for error in component_errors:
                errors.append(f"Component {i + 1} ({component.type.value}): {error}")
        
        return errors
    
    def get_body_text(self) -> Optional[str]:
        """Get the body text of the template."""
        for component in self.components:
            if component.type == ComponentType.BODY:
                return component.text
        return None
    
    def get_parameter_count(self) -> int:
        """Get total number of parameters in the template."""
        return sum(len(component.parameters) for component in self.components)
    
    def get_success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.usage_count == 0:
            return 0.0
        return (self.success_count / self.usage_count) * 100.0
    
    def update_analytics(self, success: bool):
        """Update template analytics."""
        self.usage_count += 1
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        self.last_used = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary format."""
        return {
            "name": self.name,
            "language": self.language,
            "category": self.category.value,
            "components": [comp.to_dict() for comp in self.components],
            "id": self.id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "rejection_reason": self.rejection_reason,
            "usage_count": self.usage_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "quality_score": self.quality_score,
            "delivery_rate": self.delivery_rate,
            "read_rate": self.read_rate,
            "response_rate": self.response_rate
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WhatsAppTemplate":
        """Create template from dictionary."""
        components = []
        for comp_data in data.get("components", []):
            parameters = []
            for param_data in comp_data.get("parameters", []):
                param = TemplateParameter(
                    type=ParameterType(param_data["type"]),
                    text=param_data.get("text"),
                    currency=param_data.get("currency"),
                    date_time=param_data.get("date_time"),
                    image=param_data.get("image"),
                    document=param_data.get("document"),
                    video=param_data.get("video")
                )
                parameters.append(param)
            
            component = TemplateComponent(
                type=ComponentType(comp_data["type"]),
                text=comp_data.get("text"),
                parameters=parameters,
                format=comp_data.get("format"),
                example=comp_data.get("example"),
                buttons=comp_data.get("buttons")
            )
            components.append(component)
        
        return cls(
            name=data["name"],
            language=data["language"],
            category=TemplateCategory(data["category"]),
            components=components,
            id=data.get("id"),
            status=TemplateStatus(data.get("status", "draft")),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
            submitted_at=datetime.fromisoformat(data["submitted_at"]) if data.get("submitted_at") else None,
            approved_at=datetime.fromisoformat(data["approved_at"]) if data.get("approved_at") else None,
            rejected_at=datetime.fromisoformat(data["rejected_at"]) if data.get("rejected_at") else None,
            rejection_reason=data.get("rejection_reason"),
            usage_count=data.get("usage_count", 0),
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0),
            last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None,
            quality_score=data.get("quality_score"),
            delivery_rate=data.get("delivery_rate"),
            read_rate=data.get("read_rate"),
            response_rate=data.get("response_rate")
        )


@dataclass
class TemplateAnalytics:
    """Template performance analytics."""
    template_name: str
    time_period: str
    total_sent: int = 0
    delivered: int = 0
    read: int = 0
    replied: int = 0
    failed: int = 0
    
    delivery_rate: float = 0.0
    read_rate: float = 0.0
    response_rate: float = 0.0
    
    cost_per_message: float = 0.0
    total_cost: float = 0.0
    
    recommendations: List[str] = field(default_factory=list)
    
    def calculate_rates(self):
        """Calculate performance rates."""
        if self.total_sent > 0:
            self.delivery_rate = (self.delivered / self.total_sent) * 100.0
            self.read_rate = (self.read / self.total_sent) * 100.0
            self.response_rate = (self.replied / self.total_sent) * 100.0
        
        self.total_cost = self.total_sent * self.cost_per_message
    
    def generate_recommendations(self):
        """Generate optimization recommendations."""
        self.recommendations.clear()
        
        if self.delivery_rate < 95.0:
            self.recommendations.append(i18n.tr("template_recommendation_improve_delivery"))
        
        if self.read_rate < 70.0:
            self.recommendations.append(i18n.tr("template_recommendation_improve_content"))
        
        if self.response_rate < 10.0:
            self.recommendations.append(i18n.tr("template_recommendation_add_cta"))
        
        if self.total_sent < 100:
            self.recommendations.append(i18n.tr("template_recommendation_increase_usage"))


class WhatsAppTemplateManager:
    """
    Comprehensive WhatsApp template management system.
    
    Features:
    - Template creation and validation
    - Submission workflow with approval tracking
    - Template testing and preview
    - Performance analytics and optimization
    - Automatic status monitoring
    """
    
    def __init__(
        self,
        api_client,
        storage_path: Optional[Path] = None,
        status_callback: Optional[Callable[[str, TemplateStatus], None]] = None
    ):
        """
        Initialize WhatsApp template manager.
        
        Args:
            api_client: WhatsApp API client instance
            storage_path: Path to store template data
            status_callback: Callback for template status changes
        """
        self.api_client = api_client
        self.storage_path = storage_path or Path("whatsapp_templates.json")
        self.status_callback = status_callback
        
        # Template storage
        self.templates: Dict[str, WhatsAppTemplate] = {}
        self._lock = threading.RLock()
        
        # Status monitoring
        self.monitoring_enabled = True
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_interval = 300  # 5 minutes
        
        # Load existing templates
        self._load_templates()
        
        # Start status monitoring
        self._start_status_monitoring()
        
        logger.info(i18n.tr("whatsapp_template_manager_initialized"))
    
    def create_template(
        self,
        name: str,
        language: str,
        category: TemplateCategory,
        body_text: str,
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
        buttons: Optional[List[Dict[str, Any]]] = None
    ) -> WhatsAppTemplate:
        """
        Create a new WhatsApp template.
        
        Args:
            name: Template name (lowercase, alphanumeric, underscores only)
            language: Language code (e.g., 'en', 'es', 'pt')
            category: Template category
            body_text: Main message text
            header_text: Optional header text
            footer_text: Optional footer text
            buttons: Optional button configuration
            
        Returns:
            Created WhatsApp template
            
        Raises:
            TemplateError: If template creation fails
        """
        with self._lock:
            # Check if template already exists
            if name in self.templates:
                raise TemplateError(f"Template '{name}' already exists")
            
            # Create components
            components = []
            
            # Add header if provided
            if header_text:
                header_component = TemplateComponent(
                    type=ComponentType.HEADER,
                    format="TEXT",
                    text=header_text
                )
                components.append(header_component)
            
            # Add body (required)
            # Extract parameters from body text
            import re
            placeholder_count = len(re.findall(r'\{\{\d+\}\}', body_text))
            parameters = []
            for i in range(placeholder_count):
                parameters.append(TemplateParameter(type=ParameterType.TEXT, text=f"param_{i+1}"))
            
            body_component = TemplateComponent(
                type=ComponentType.BODY,
                text=body_text,
                parameters=parameters
            )
            components.append(body_component)
            
            # Add footer if provided
            if footer_text:
                footer_component = TemplateComponent(
                    type=ComponentType.FOOTER,
                    text=footer_text
                )
                components.append(footer_component)
            
            # Add buttons if provided
            if buttons:
                button_component = TemplateComponent(
                    type=ComponentType.BUTTONS,
                    buttons=buttons
                )
                components.append(button_component)
            
            # Create template
            template = WhatsAppTemplate(
                name=name,
                language=language,
                category=category,
                components=components
            )
            
            # Validate template
            errors = template.validate()
            if errors:
                raise TemplateError(f"Template validation failed: {'; '.join(errors)}")
            
            # Store template
            self.templates[name] = template
            self._save_templates()
            
            logger.info(f"Created WhatsApp template: {name}")
            return template
    
    def submit_template(self, template_name: str) -> bool:
        """
        Submit template for approval to WhatsApp.
        
        Args:
            template_name: Name of template to submit
            
        Returns:
            True if submission successful
            
        Raises:
            TemplateError: If submission fails
        """
        with self._lock:
            if template_name not in self.templates:
                raise TemplateError(f"Template '{template_name}' not found")
            
            template = self.templates[template_name]
            
            if template.status != TemplateStatus.DRAFT:
                raise TemplateError(f"Template '{template_name}' is not in draft status")
            
            # Validate before submission
            errors = template.validate()
            if errors:
                raise TemplateError(f"Template validation failed: {'; '.join(errors)}")
            
            try:
                # Submit to WhatsApp API
                response = self._submit_to_whatsapp_api(template)
                
                # Update template status
                template.status = TemplateStatus.PENDING
                template.submitted_at = datetime.now()
                template.updated_at = datetime.now()
                
                if 'id' in response:
                    template.id = response['id']
                
                self._save_templates()
                
                # Trigger status callback
                if self.status_callback:
                    self.status_callback(template_name, TemplateStatus.PENDING)
                
                logger.info(f"Submitted template '{template_name}' for approval")
                return True
                
            except Exception as e:
                logger.error(f"Failed to submit template '{template_name}': {e}")
                raise TemplateError(f"Template submission failed: {e}")
    
    def get_template_status(self, template_name: str) -> Optional[TemplateStatus]:
        """
        Get current status of a template.
        
        Args:
            template_name: Name of template
            
        Returns:
            Current template status or None if not found
        """
        with self._lock:
            if template_name in self.templates:
                return self.templates[template_name].status
            return None
    
    def update_template_status(self, template_name: str, new_status: TemplateStatus, reason: Optional[str] = None):
        """
        Update template status (typically called by status monitoring).
        
        Args:
            template_name: Name of template
            new_status: New status
            reason: Optional reason for status change (e.g., rejection reason)
        """
        with self._lock:
            if template_name not in self.templates:
                return
            
            template = self.templates[template_name]
            old_status = template.status
            
            template.status = new_status
            template.updated_at = datetime.now()
            
            if new_status == TemplateStatus.APPROVED:
                template.approved_at = datetime.now()
            elif new_status == TemplateStatus.REJECTED:
                template.rejected_at = datetime.now()
                template.rejection_reason = reason
            
            self._save_templates()
            
            # Trigger status callback
            if self.status_callback and old_status != new_status:
                self.status_callback(template_name, new_status)
            
            logger.info(f"Template '{template_name}' status changed: {old_status.value} -> {new_status.value}")
    
    def get_template_analytics(self, template_name: str, days: int = 30) -> Optional[TemplateAnalytics]:
        """
        Get analytics for a specific template.
        
        Args:
            template_name: Name of template
            days: Number of days to analyze
            
        Returns:
            Template analytics or None if not found
        """
        with self._lock:
            if template_name not in self.templates:
                return None
            
            template = self.templates[template_name]
            
            # Create analytics object
            analytics = TemplateAnalytics(
                template_name=template_name,
                time_period=f"Last {days} days",
                total_sent=template.usage_count,
                delivered=template.success_count,
                failed=template.failure_count
            )
            
            # Calculate rates
            analytics.calculate_rates()
            
            # Generate recommendations
            analytics.generate_recommendations()
            
            return analytics
    
    def get_all_templates(self) -> List[WhatsAppTemplate]:
        """Get all templates."""
        with self._lock:
            return list(self.templates.values())
    
    def get_approved_templates(self) -> List[WhatsAppTemplate]:
        """Get only approved templates."""
        with self._lock:
            return [t for t in self.templates.values() if t.status == TemplateStatus.APPROVED]
    
    def delete_template(self, template_name: str) -> bool:
        """
        Delete a template.
        
        Args:
            template_name: Name of template to delete
            
        Returns:
            True if deleted successfully
        """
        with self._lock:
            if template_name not in self.templates:
                return False
            
            template = self.templates[template_name]
            
            # Can only delete draft or rejected templates
            if template.status not in [TemplateStatus.DRAFT, TemplateStatus.REJECTED]:
                raise TemplateError(f"Cannot delete template in {template.status.value} status")
            
            del self.templates[template_name]
            self._save_templates()
            
            logger.info(f"Deleted template: {template_name}")
            return True
    
    def preview_template(self, template_name: str, parameters: Dict[str, str]) -> Dict[str, str]:
        """
        Preview template with sample parameters.
        
        Args:
            template_name: Name of template
            parameters: Parameter values for preview
            
        Returns:
            Dictionary with rendered template content
            
        Raises:
            TemplateError: If preview fails
        """
        with self._lock:
            if template_name not in self.templates:
                raise TemplateError(f"Template '{template_name}' not found")
            
            template = self.templates[template_name]
            
            try:
                preview = {}
                
                for component in template.components:
                    if component.text:
                        rendered_text = component.text
                        
                        # Replace parameter placeholders
                        for i, param in enumerate(component.parameters):
                            placeholder = f"{{{{{i + 1}}}}}"
                            param_key = f"param_{i + 1}"
                            
                            if param_key in parameters:
                                rendered_text = rendered_text.replace(placeholder, parameters[param_key])
                            else:
                                rendered_text = rendered_text.replace(placeholder, f"[{param.type.value}]")
                        
                        preview[component.type.value] = rendered_text
                
                return preview
                
            except Exception as e:
                raise TemplateError(f"Template preview failed: {e}")
    
    def _submit_to_whatsapp_api(self, template: WhatsAppTemplate) -> Dict[str, Any]:
        """Submit template to WhatsApp Business API."""
        # This would make the actual API call to submit the template
        # For now, we'll simulate the response
        
        payload = {
            "name": template.name,
            "language": template.language,
            "category": template.category.value,
            "components": [comp.to_dict() for comp in template.components]
        }
        
        # Simulate API call
        logger.debug(f"Submitting template to WhatsApp API: {json.dumps(payload, indent=2)}")
        
        # Return simulated response
        return {
            "id": f"template_{template.name}_{int(time.time())}",
            "status": "PENDING",
            "category": template.category.value
        }
    
    def _start_status_monitoring(self):
        """Start background status monitoring."""
        if not self.monitoring_enabled:
            return
        
        def monitor_status():
            while self.monitoring_enabled:
                try:
                    self._check_template_statuses()
                    time.sleep(self.monitoring_interval)
                except Exception as e:
                    logger.error(f"Error in template status monitoring: {e}")
                    time.sleep(60)  # Wait a minute before retrying
        
        self.monitoring_thread = threading.Thread(target=monitor_status, daemon=True)
        self.monitoring_thread.start()
        logger.debug("Template status monitoring started")
    
    def _check_template_statuses(self):
        """Check status of pending templates."""
        with self._lock:
            pending_templates = [
                t for t in self.templates.values() 
                if t.status == TemplateStatus.PENDING and t.id
            ]
            
            for template in pending_templates:
                try:
                    # Check status via API
                    # This would make actual API calls to check template status
                    # For now, we'll simulate status changes
                    
                    # Simulate approval after 5 minutes for demo purposes
                    if template.submitted_at and datetime.now() - template.submitted_at > timedelta(minutes=5):
                        self.update_template_status(template.name, TemplateStatus.APPROVED)
                    
                except Exception as e:
                    logger.warning(f"Failed to check status for template '{template.name}': {e}")
    
    def _save_templates(self):
        """Save templates to persistent storage."""
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "templates": {name: template.to_dict() for name, template in self.templates.items()}
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to save templates: {e}")
    
    def _load_templates(self):
        """Load templates from persistent storage."""
        if not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            for name, template_data in data.get("templates", {}).items():
                try:
                    template = WhatsAppTemplate.from_dict(template_data)
                    self.templates[name] = template
                except Exception as e:
                    logger.warning(f"Failed to load template '{name}': {e}")
            
            logger.info(f"Loaded {len(self.templates)} WhatsApp templates")
            
        except Exception as e:
            logger.warning(f"Failed to load templates: {e}")
    
    def shutdown(self):
        """Shutdown template manager."""
        logger.info("Shutting down WhatsApp template manager...")
        
        # Stop monitoring
        self.monitoring_enabled = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        
        # Save final state
        self._save_templates()
        
        logger.info("WhatsApp template manager shutdown complete")
    
    def __del__(self):
        """Cleanup on destruction."""
        try:
            self.shutdown()
        except:
            pass