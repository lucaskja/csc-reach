"""
WhatsApp Multi-Message Template Manager.

Manages WhatsApp multi-message templates with persistence and integration
with the existing template system.
"""

import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .whatsapp_multi_message import WhatsAppMultiMessageTemplate, MessageSplitStrategy
from .config_manager import ConfigManager
from ..utils.logger import get_logger
from ..utils.exceptions import ValidationError, TemplateError
from ..core.i18n_manager import get_i18n_manager

logger = get_logger(__name__)
i18n = get_i18n_manager()


class WhatsAppMultiMessageManager:
    """Manager for WhatsApp multi-message templates."""
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the WhatsApp multi-message template manager.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.templates: Dict[str, WhatsAppMultiMessageTemplate] = {}
        self._lock = threading.RLock()
        
        # Storage path
        self.storage_path = config_manager.get_app_data_path() / "whatsapp_multi_templates.json"
        
        # Load existing templates
        self._load_templates()
        
        logger.info("WhatsApp Multi-Message Template Manager initialized")
    
    def _load_templates(self):
        """Load templates from storage."""
        if not self.storage_path.exists():
            logger.debug("No existing WhatsApp multi-message templates found")
            return
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            templates_data = data.get('templates', {})
            
            for template_id, template_data in templates_data.items():
                try:
                    template = WhatsAppMultiMessageTemplate.from_dict(template_data)
                    self.templates[template_id] = template
                except Exception as e:
                    logger.error(f"Failed to load template {template_id}: {e}")
            
            logger.info(f"Loaded {len(self.templates)} WhatsApp multi-message templates")
            
        except Exception as e:
            logger.error(f"Failed to load WhatsApp multi-message templates: {e}")
    
    def _save_templates(self):
        """Save templates to storage."""
        try:
            # Ensure directory exists
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare data
            templates_data = {}
            for template_id, template in self.templates.items():
                templates_data[template_id] = template.to_dict()
            
            data = {
                'version': '1.0',
                'updated_at': datetime.now().isoformat(),
                'templates': templates_data
            }
            
            # Write to file
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved {len(self.templates)} WhatsApp multi-message templates")
            
        except Exception as e:
            logger.error(f"Failed to save WhatsApp multi-message templates: {e}")
            raise TemplateError(f"Failed to save templates: {e}")
    
    def create_template(
        self,
        name: str,
        content: str,
        language: str = "en",
        multi_message_mode: bool = False,
        split_strategy: MessageSplitStrategy = MessageSplitStrategy.PARAGRAPH,
        custom_delimiter: str = "\n\n",
        message_delay: float = 1.0,
        max_messages: int = 10
    ) -> WhatsAppMultiMessageTemplate:
        """
        Create a new WhatsApp multi-message template.
        
        Args:
            name: Template name
            content: Template content
            language: Language code
            multi_message_mode: Enable multi-message mode
            split_strategy: Message splitting strategy
            custom_delimiter: Custom delimiter for splitting
            message_delay: Delay between messages in seconds
            max_messages: Maximum messages per sequence
            
        Returns:
            Created template
            
        Raises:
            TemplateError: If template creation fails
        """
        with self._lock:
            # Validate name uniqueness
            if any(t.name.lower() == name.lower() for t in self.templates.values()):
                raise TemplateError(f"Template with name '{name}' already exists")
            
            # Generate unique ID
            template_id = f"whatsapp_multi_{int(datetime.now().timestamp())}"
            
            # Create template
            template = WhatsAppMultiMessageTemplate(
                id=template_id,
                name=name,
                content=content,
                language=language,
                multi_message_mode=multi_message_mode,
                split_strategy=split_strategy,
                custom_split_delimiter=custom_delimiter,
                message_delay_seconds=message_delay,
                max_messages_per_sequence=max_messages
            )
            
            # Validate template
            errors = template.validate_message_sequence()
            if errors:
                raise TemplateError(f"Template validation failed: {'; '.join(errors)}")
            
            # Store template
            self.templates[template_id] = template
            self._save_templates()
            
            logger.info(f"Created WhatsApp multi-message template: {name}")
            return template
    
    def update_template(
        self,
        template_id: str,
        name: Optional[str] = None,
        content: Optional[str] = None,
        language: Optional[str] = None,
        multi_message_mode: Optional[bool] = None,
        split_strategy: Optional[MessageSplitStrategy] = None,
        custom_delimiter: Optional[str] = None,
        message_delay: Optional[float] = None,
        max_messages: Optional[int] = None,
        message_sequence: Optional[List[str]] = None
    ) -> WhatsAppMultiMessageTemplate:
        """
        Update an existing template.
        
        Args:
            template_id: Template ID to update
            **kwargs: Fields to update
            
        Returns:
            Updated template
            
        Raises:
            TemplateError: If template not found or update fails
        """
        with self._lock:
            if template_id not in self.templates:
                raise TemplateError(f"Template {template_id} not found")
            
            template = self.templates[template_id]
            
            # Update fields
            if name is not None:
                # Check name uniqueness (excluding current template)
                if any(t.name.lower() == name.lower() and t.id != template_id 
                      for t in self.templates.values()):
                    raise TemplateError(f"Template with name '{name}' already exists")
                template.name = name
            
            if content is not None:
                template.content = content
            
            if language is not None:
                template.language = language
            
            if multi_message_mode is not None:
                template.multi_message_mode = multi_message_mode
            
            if split_strategy is not None:
                template.split_strategy = split_strategy
            
            if custom_delimiter is not None:
                template.custom_split_delimiter = custom_delimiter
            
            if message_delay is not None:
                template.message_delay_seconds = message_delay
            
            if max_messages is not None:
                template.max_messages_per_sequence = max_messages
            
            if message_sequence is not None:
                template.message_sequence = message_sequence
            
            # Update timestamp and re-extract variables
            template.updated_at = datetime.now()
            template.extract_variables()
            
            # Re-split messages if needed
            if template.multi_message_mode and not message_sequence:
                template.split_into_messages()
            
            # Validate updated template
            errors = template.validate_message_sequence()
            if errors:
                raise TemplateError(f"Template validation failed: {'; '.join(errors)}")
            
            # Save changes
            self._save_templates()
            
            logger.info(f"Updated WhatsApp multi-message template: {template.name}")
            return template
    
    def delete_template(self, template_id: str) -> bool:
        """
        Delete a template.
        
        Args:
            template_id: Template ID to delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            TemplateError: If template not found
        """
        with self._lock:
            if template_id not in self.templates:
                raise TemplateError(f"Template {template_id} not found")
            
            template_name = self.templates[template_id].name
            del self.templates[template_id]
            self._save_templates()
            
            logger.info(f"Deleted WhatsApp multi-message template: {template_name}")
            return True
    
    def get_template(self, template_id: str) -> Optional[WhatsAppMultiMessageTemplate]:
        """
        Get a template by ID.
        
        Args:
            template_id: Template ID
            
        Returns:
            Template or None if not found
        """
        with self._lock:
            return self.templates.get(template_id)
    
    def get_template_by_name(self, name: str) -> Optional[WhatsAppMultiMessageTemplate]:
        """
        Get a template by name.
        
        Args:
            name: Template name
            
        Returns:
            Template or None if not found
        """
        with self._lock:
            for template in self.templates.values():
                if template.name.lower() == name.lower():
                    return template
            return None
    
    def get_all_templates(self) -> List[WhatsAppMultiMessageTemplate]:
        """
        Get all templates.
        
        Returns:
            List of all templates
        """
        with self._lock:
            return list(self.templates.values())
    
    def get_templates_by_language(self, language: str) -> List[WhatsAppMultiMessageTemplate]:
        """
        Get templates by language.
        
        Args:
            language: Language code
            
        Returns:
            List of templates in the specified language
        """
        with self._lock:
            return [t for t in self.templates.values() if t.language == language]
    
    def search_templates(self, query: str) -> List[WhatsAppMultiMessageTemplate]:
        """
        Search templates by name or content.
        
        Args:
            query: Search query
            
        Returns:
            List of matching templates
        """
        with self._lock:
            query_lower = query.lower()
            results = []
            
            for template in self.templates.values():
                if (query_lower in template.name.lower() or 
                    query_lower in template.content.lower()):
                    results.append(template)
            
            return results
    
    def duplicate_template(self, template_id: str, new_name: str) -> WhatsAppMultiMessageTemplate:
        """
        Duplicate an existing template.
        
        Args:
            template_id: Template ID to duplicate
            new_name: Name for the new template
            
        Returns:
            Duplicated template
            
        Raises:
            TemplateError: If source template not found or name already exists
        """
        with self._lock:
            if template_id not in self.templates:
                raise TemplateError(f"Template {template_id} not found")
            
            source_template = self.templates[template_id]
            
            # Check name uniqueness
            if any(t.name.lower() == new_name.lower() for t in self.templates.values()):
                raise TemplateError(f"Template with name '{new_name}' already exists")
            
            # Create duplicate
            new_template_id = f"whatsapp_multi_{int(datetime.now().timestamp())}"
            
            duplicate = WhatsAppMultiMessageTemplate(
                id=new_template_id,
                name=new_name,
                content=source_template.content,
                language=source_template.language,
                multi_message_mode=source_template.multi_message_mode,
                split_strategy=source_template.split_strategy,
                custom_split_delimiter=source_template.custom_split_delimiter,
                message_delay_seconds=source_template.message_delay_seconds,
                max_messages_per_sequence=source_template.max_messages_per_sequence,
                message_sequence=source_template.message_sequence.copy()
            )
            
            # Store duplicate
            self.templates[new_template_id] = duplicate
            self._save_templates()
            
            logger.info(f"Duplicated WhatsApp multi-message template: {new_name}")
            return duplicate
    
    def export_templates(self, template_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Export templates to dictionary format.
        
        Args:
            template_ids: Optional list of template IDs to export (all if None)
            
        Returns:
            Dictionary with exported templates
        """
        with self._lock:
            if template_ids is None:
                templates_to_export = self.templates
            else:
                templates_to_export = {
                    tid: self.templates[tid] 
                    for tid in template_ids 
                    if tid in self.templates
                }
            
            export_data = {
                'version': '1.0',
                'export_date': datetime.now().isoformat(),
                'template_count': len(templates_to_export),
                'templates': {
                    tid: template.to_dict() 
                    for tid, template in templates_to_export.items()
                }
            }
            
            logger.info(f"Exported {len(templates_to_export)} WhatsApp multi-message templates")
            return export_data
    
    def import_templates(
        self, 
        import_data: Dict[str, Any], 
        overwrite_existing: bool = False
    ) -> List[WhatsAppMultiMessageTemplate]:
        """
        Import templates from dictionary format.
        
        Args:
            import_data: Dictionary with template data
            overwrite_existing: Whether to overwrite existing templates
            
        Returns:
            List of imported templates
            
        Raises:
            TemplateError: If import fails
        """
        with self._lock:
            if 'templates' not in import_data:
                raise TemplateError("Invalid import data: missing 'templates' key")
            
            imported_templates = []
            templates_data = import_data['templates']
            
            for template_id, template_data in templates_data.items():
                try:
                    template = WhatsAppMultiMessageTemplate.from_dict(template_data)
                    
                    # Check for name conflicts
                    existing_template = self.get_template_by_name(template.name)
                    if existing_template and not overwrite_existing:
                        # Generate unique name
                        base_name = template.name
                        counter = 1
                        while self.get_template_by_name(template.name):
                            template.name = f"{base_name} ({counter})"
                            counter += 1
                    
                    # Generate new ID to avoid conflicts
                    new_id = f"whatsapp_multi_{int(datetime.now().timestamp())}_{len(imported_templates)}"
                    template.id = new_id
                    
                    # Validate template
                    errors = template.validate_message_sequence()
                    if errors:
                        logger.warning(f"Skipping invalid template {template.name}: {'; '.join(errors)}")
                        continue
                    
                    # Store template
                    self.templates[new_id] = template
                    imported_templates.append(template)
                    
                except Exception as e:
                    logger.error(f"Failed to import template {template_id}: {e}")
            
            if imported_templates:
                self._save_templates()
                logger.info(f"Imported {len(imported_templates)} WhatsApp multi-message templates")
            
            return imported_templates
    
    def get_template_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about templates.
        
        Returns:
            Dictionary with template statistics
        """
        with self._lock:
            total_templates = len(self.templates)
            multi_message_templates = sum(1 for t in self.templates.values() if t.multi_message_mode)
            single_message_templates = total_templates - multi_message_templates
            
            languages = {}
            total_usage = 0
            total_success = 0
            
            for template in self.templates.values():
                # Language distribution
                lang = template.language
                languages[lang] = languages.get(lang, 0) + 1
                
                # Usage statistics
                total_usage += template.usage_count
                total_success += template.success_count
            
            success_rate = (total_success / total_usage * 100) if total_usage > 0 else 0
            
            return {
                'total_templates': total_templates,
                'multi_message_templates': multi_message_templates,
                'single_message_templates': single_message_templates,
                'languages': languages,
                'total_usage': total_usage,
                'total_success': total_success,
                'success_rate': success_rate
            }
    
    def cleanup_unused_templates(self, min_usage_threshold: int = 0) -> int:
        """
        Clean up templates with low usage.
        
        Args:
            min_usage_threshold: Minimum usage count to keep template
            
        Returns:
            Number of templates removed
        """
        with self._lock:
            templates_to_remove = []
            
            for template_id, template in self.templates.items():
                if template.usage_count <= min_usage_threshold:
                    templates_to_remove.append(template_id)
            
            for template_id in templates_to_remove:
                del self.templates[template_id]
            
            if templates_to_remove:
                self._save_templates()
                logger.info(f"Cleaned up {len(templates_to_remove)} unused WhatsApp multi-message templates")
            
            return len(templates_to_remove)