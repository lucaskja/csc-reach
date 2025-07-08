"""
Template Management System for Multi-Channel Messaging.

Provides comprehensive template management including:
- Template library with categories
- Import/export functionality
- Template validation and preview
- Version control and backup
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import asdict, replace

from .models import MessageTemplate
from .config_manager import ConfigManager
from ..utils.exceptions import ValidationError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TemplateCategory:
    """Template category for organization."""
    
    def __init__(self, id: str, name: str, description: str = "", color: str = "#007ACC"):
        self.id = id
        self.name = name
        self.description = description
        self.color = color
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateCategory":
        category = cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            color=data.get("color", "#007ACC")
        )
        if "created_at" in data:
            category.created_at = datetime.fromisoformat(data["created_at"])
        return category


class TemplateManager:
    """Comprehensive template management system."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.templates_dir = config_manager.get_templates_path()
        self.categories_file = self.templates_dir / "categories.json"
        self.templates_index_file = self.templates_dir / "index.json"
        
        # Initialize directories
        self._ensure_directories()
        
        # Load data
        self._categories: Dict[str, TemplateCategory] = {}
        self._templates: Dict[str, MessageTemplate] = {}
        self._template_metadata: Dict[str, Dict[str, Any]] = {}
        
        self._load_categories()
        self._load_templates()
        
        # Create default category if none exist
        if not self._categories:
            self._create_default_categories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        (self.templates_dir / "backups").mkdir(exist_ok=True)
        (self.templates_dir / "exports").mkdir(exist_ok=True)
        (self.templates_dir / "imports").mkdir(exist_ok=True)
    
    def _create_default_categories(self):
        """Create default template categories."""
        default_categories = [
            TemplateCategory("welcome", "Welcome Messages", "Initial contact and welcome messages", "#4CAF50"),
            TemplateCategory("follow_up", "Follow-up", "Follow-up and reminder messages", "#FF9800"),
            TemplateCategory("promotional", "Promotional", "Marketing and promotional content", "#E91E63"),
            TemplateCategory("support", "Support", "Customer support templates", "#2196F3"),
            TemplateCategory("general", "General", "General purpose templates", "#607D8B")
        ]
        
        for category in default_categories:
            self._categories[category.id] = category
        
        self._save_categories()
        logger.info(f"Created {len(default_categories)} default template categories")
    
    def _load_categories(self):
        """Load template categories from file."""
        if not self.categories_file.exists():
            return
        
        try:
            with open(self.categories_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for cat_data in data.get("categories", []):
                category = TemplateCategory.from_dict(cat_data)
                self._categories[category.id] = category
            
            logger.info(f"Loaded {len(self._categories)} template categories")
        except Exception as e:
            logger.error(f"Failed to load categories: {e}")
    
    def _save_categories(self):
        """Save template categories to file."""
        try:
            data = {
                "categories": [cat.to_dict() for cat in self._categories.values()],
                "updated_at": datetime.now().isoformat()
            }
            
            with open(self.categories_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("Saved template categories")
        except Exception as e:
            logger.error(f"Failed to save categories: {e}")
    
    def _load_templates(self):
        """Load all templates from the templates directory."""
        if not self.templates_index_file.exists():
            return
        
        try:
            with open(self.templates_index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            for template_id, metadata in index_data.get("templates", {}).items():
                template_file = self.templates_dir / f"{template_id}.json"
                if template_file.exists():
                    template = self._load_template_file(template_file)
                    if template:
                        self._templates[template_id] = template
                        self._template_metadata[template_id] = metadata
            
            logger.info(f"Loaded {len(self._templates)} templates")
        except Exception as e:
            logger.error(f"Failed to load templates index: {e}")
    
    def _load_template_file(self, template_file: Path) -> Optional[MessageTemplate]:
        """Load a single template file."""
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert old format if needed
            if "channel" in data and isinstance(data["channel"], str):
                # Old single-channel format
                data["channels"] = [data.pop("channel")]
            
            template = MessageTemplate(
                id=data["id"],
                name=data["name"],
                channels=data.get("channels", ["email"]),
                subject=data.get("subject", ""),
                content=data.get("content", ""),
                whatsapp_content=data.get("whatsapp_content", ""),
                language=data.get("language", "en"),
                variables=data.get("variables", [])
            )
            
            # Set timestamps if available
            if "created_at" in data:
                template.created_at = datetime.fromisoformat(data["created_at"])
            if "updated_at" in data:
                template.updated_at = datetime.fromisoformat(data["updated_at"])
            
            return template
        except Exception as e:
            logger.error(f"Failed to load template from {template_file}: {e}")
            return None
    
    def _save_template_file(self, template: MessageTemplate):
        """Save a template to its individual file."""
        template_file = self.templates_dir / f"{template.id}.json"
        
        try:
            data = {
                "id": template.id,
                "name": template.name,
                "channels": template.channels,
                "subject": template.subject,
                "content": template.content,
                "whatsapp_content": template.whatsapp_content,
                "language": template.language,
                "variables": template.variables,
                "created_at": template.created_at.isoformat(),
                "updated_at": template.updated_at.isoformat()
            }
            
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved template {template.id}")
        except Exception as e:
            logger.error(f"Failed to save template {template.id}: {e}")
            raise
    
    def _update_templates_index(self):
        """Update the templates index file."""
        try:
            index_data = {
                "templates": self._template_metadata,
                "updated_at": datetime.now().isoformat()
            }
            
            with open(self.templates_index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
            
            logger.debug("Updated templates index")
        except Exception as e:
            logger.error(f"Failed to update templates index: {e}")
    
    # Public API methods
    
    def get_categories(self) -> List[TemplateCategory]:
        """Get all template categories."""
        return list(self._categories.values())
    
    def get_category(self, category_id: str) -> Optional[TemplateCategory]:
        """Get a specific category by ID."""
        return self._categories.get(category_id)
    
    def create_category(self, id: str, name: str, description: str = "", color: str = "#007ACC") -> TemplateCategory:
        """Create a new template category."""
        if id in self._categories:
            raise ValidationError(f"Category with ID '{id}' already exists")
        
        category = TemplateCategory(id, name, description, color)
        self._categories[id] = category
        self._save_categories()
        
        logger.info(f"Created category: {name}")
        return category
    
    def update_category(self, category_id: str, name: str = None, description: str = None, color: str = None) -> bool:
        """Update an existing category."""
        if category_id not in self._categories:
            return False
        
        category = self._categories[category_id]
        if name is not None:
            category.name = name
        if description is not None:
            category.description = description
        if color is not None:
            category.color = color
        
        self._save_categories()
        logger.info(f"Updated category: {category_id}")
        return True
    
    def delete_category(self, category_id: str) -> bool:
        """Delete a category (moves templates to 'general' category)."""
        if category_id not in self._categories:
            return False
        
        # Move templates to general category
        for template_id, metadata in self._template_metadata.items():
            if metadata.get("category_id") == category_id:
                metadata["category_id"] = "general"
        
        del self._categories[category_id]
        self._save_categories()
        self._update_templates_index()
        
        logger.info(f"Deleted category: {category_id}")
        return True
    
    def get_templates(self, category_id: str = None) -> List[MessageTemplate]:
        """Get templates, optionally filtered by category."""
        if category_id is None:
            return list(self._templates.values())
        
        filtered_templates = []
        for template_id, template in self._templates.items():
            metadata = self._template_metadata.get(template_id, {})
            if metadata.get("category_id") == category_id:
                filtered_templates.append(template)
        
        return filtered_templates
    
    def get_template(self, template_id: str) -> Optional[MessageTemplate]:
        """Get a specific template by ID."""
        return self._templates.get(template_id)
    
    def get_template_metadata(self, template_id: str) -> Dict[str, Any]:
        """Get template metadata."""
        return self._template_metadata.get(template_id, {})
    
    def save_template(self, template: MessageTemplate, category_id: str = "general", 
                     description: str = "", tags: List[str] = None) -> bool:
        """Save a new or updated template."""
        try:
            # Validate template
            template.validate()
            
            # Update timestamp
            if template.id in self._templates:
                template.updated_at = datetime.now()
            else:
                template.created_at = datetime.now()
                template.updated_at = datetime.now()
            
            # Create backup if template exists
            if template.id in self._templates:
                self._create_template_backup(template.id)
            
            # Save template
            self._templates[template.id] = template
            self._save_template_file(template)
            
            # Update metadata
            self._template_metadata[template.id] = {
                "category_id": category_id,
                "description": description,
                "tags": tags or [],
                "created_at": template.created_at.isoformat(),
                "updated_at": template.updated_at.isoformat(),
                "usage_count": self._template_metadata.get(template.id, {}).get("usage_count", 0)
            }
            
            self._update_templates_index()
            logger.info(f"Saved template: {template.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save template {template.id}: {e}")
            return False
    
    def update_template(self, template_id: str, **updates) -> bool:
        """Update an existing template."""
        if template_id not in self._templates:
            return False
        
        try:
            template = self._templates[template_id]
            
            # Create backup before updating
            self._create_template_backup(template_id)
            
            # Apply updates
            for field, value in updates.items():
                if hasattr(template, field):
                    setattr(template, field, value)
            
            template.updated_at = datetime.now()
            
            # Validate and save
            template.validate()
            self._save_template_file(template)
            
            # Update metadata timestamp
            if template_id in self._template_metadata:
                self._template_metadata[template_id]["updated_at"] = template.updated_at.isoformat()
                self._update_templates_index()
            
            logger.info(f"Updated template: {template_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update template {template_id}: {e}")
            return False
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a template."""
        if template_id not in self._templates:
            return False
        
        try:
            # Create backup before deletion
            self._create_template_backup(template_id)
            
            # Remove from memory
            del self._templates[template_id]
            if template_id in self._template_metadata:
                del self._template_metadata[template_id]
            
            # Remove file
            template_file = self.templates_dir / f"{template_id}.json"
            if template_file.exists():
                template_file.unlink()
            
            self._update_templates_index()
            logger.info(f"Deleted template: {template_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete template {template_id}: {e}")
            return False
    
    def duplicate_template(self, template_id: str, new_name: str, new_id: str = None) -> Optional[MessageTemplate]:
        """Create a duplicate of an existing template."""
        if template_id not in self._templates:
            return None
        
        original = self._templates[template_id]
        original_metadata = self._template_metadata.get(template_id, {})
        
        # Generate new ID if not provided
        if new_id is None:
            new_id = f"{template_id}_copy_{int(datetime.now().timestamp())}"
        
        # Create duplicate
        duplicate = replace(original, id=new_id, name=new_name)
        duplicate.created_at = datetime.now()
        duplicate.updated_at = datetime.now()
        
        # Save duplicate
        if self.save_template(
            duplicate, 
            category_id=original_metadata.get("category_id", "general"),
            description=f"Copy of {original.name}",
            tags=original_metadata.get("tags", [])
        ):
            return duplicate
        
        return None
    
    def search_templates(self, query: str, category_id: str = None) -> List[MessageTemplate]:
        """Search templates by name, content, or tags."""
        query = query.lower().strip()
        if not query:
            return self.get_templates(category_id)
        
        results = []
        for template_id, template in self._templates.items():
            # Filter by category if specified
            if category_id:
                metadata = self._template_metadata.get(template_id, {})
                if metadata.get("category_id") != category_id:
                    continue
            
            # Search in various fields
            searchable_text = " ".join([
                template.name.lower(),
                template.subject.lower(),
                template.content.lower(),
                template.whatsapp_content.lower(),
                " ".join(self._template_metadata.get(template_id, {}).get("tags", []))
            ])
            
            if query in searchable_text:
                results.append(template)
        
        return results
    
    def get_template_usage_stats(self) -> Dict[str, Any]:
        """Get template usage statistics."""
        total_templates = len(self._templates)
        categories_count = len(self._categories)
        
        # Count templates by category
        category_counts = {}
        for metadata in self._template_metadata.values():
            cat_id = metadata.get("category_id", "general")
            category_counts[cat_id] = category_counts.get(cat_id, 0) + 1
        
        # Most used templates
        most_used = sorted(
            [(tid, meta.get("usage_count", 0)) for tid, meta in self._template_metadata.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "total_templates": total_templates,
            "total_categories": categories_count,
            "templates_by_category": category_counts,
            "most_used_templates": most_used
        }
    
    def increment_template_usage(self, template_id: str):
        """Increment usage count for a template."""
        if template_id in self._template_metadata:
            self._template_metadata[template_id]["usage_count"] = \
                self._template_metadata[template_id].get("usage_count", 0) + 1
            self._update_templates_index()
    
    def _create_template_backup(self, template_id: str):
        """Create a backup of a template before modification."""
        if template_id not in self._templates:
            return
        
        try:
            backup_dir = self.templates_dir / "backups"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"{template_id}_{timestamp}.json"
            
            template_file = self.templates_dir / f"{template_id}.json"
            if template_file.exists():
                shutil.copy2(template_file, backup_file)
                logger.debug(f"Created backup: {backup_file}")
        except Exception as e:
            logger.warning(f"Failed to create backup for {template_id}: {e}")
    
    def export_template(self, template_id: str, export_path: Path = None) -> Optional[Path]:
        """Export a template to a file."""
        if template_id not in self._templates:
            return None
        
        try:
            template = self._templates[template_id]
            metadata = self._template_metadata.get(template_id, {})
            
            export_data = {
                "template": {
                    "id": template.id,
                    "name": template.name,
                    "channels": template.channels,
                    "subject": template.subject,
                    "content": template.content,
                    "whatsapp_content": template.whatsapp_content,
                    "language": template.language,
                    "variables": template.variables,
                    "created_at": template.created_at.isoformat(),
                    "updated_at": template.updated_at.isoformat()
                },
                "metadata": metadata,
                "export_info": {
                    "exported_at": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }
            
            if export_path is None:
                export_path = self.templates_dir / "exports" / f"{template_id}_export.json"
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported template {template_id} to {export_path}")
            return export_path
            
        except Exception as e:
            logger.error(f"Failed to export template {template_id}: {e}")
            return None
    
    def import_template(self, import_path: Path, new_id: str = None, 
                       category_id: str = None) -> Optional[MessageTemplate]:
        """Import a template from a file."""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            template_data = data.get("template", data)  # Support both formats
            metadata = data.get("metadata", {})
            
            # Create template
            template = MessageTemplate(
                id=new_id or template_data["id"],
                name=template_data["name"],
                channels=template_data.get("channels", ["email"]),
                subject=template_data.get("subject", ""),
                content=template_data.get("content", ""),
                whatsapp_content=template_data.get("whatsapp_content", ""),
                language=template_data.get("language", "en"),
                variables=template_data.get("variables", [])
            )
            
            # Handle ID conflicts
            if template.id in self._templates:
                timestamp = int(datetime.now().timestamp())
                template.id = f"{template.id}_imported_{timestamp}"
            
            # Save template
            save_category = category_id or metadata.get("category_id", "general")
            if self.save_template(
                template,
                category_id=save_category,
                description=metadata.get("description", f"Imported from {import_path.name}"),
                tags=metadata.get("tags", [])
            ):
                logger.info(f"Imported template: {template.name}")
                return template
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to import template from {import_path}: {e}")
            return None
    
    def export_all_templates(self, export_path: Path = None) -> Optional[Path]:
        """Export all templates to a single file."""
        try:
            if export_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_path = self.templates_dir / "exports" / f"all_templates_{timestamp}.json"
            
            export_data = {
                "templates": {},
                "categories": {cat_id: cat.to_dict() for cat_id, cat in self._categories.items()},
                "metadata": self._template_metadata,
                "export_info": {
                    "exported_at": datetime.now().isoformat(),
                    "version": "1.0",
                    "total_templates": len(self._templates)
                }
            }
            
            # Add all templates
            for template_id, template in self._templates.items():
                export_data["templates"][template_id] = {
                    "id": template.id,
                    "name": template.name,
                    "channels": template.channels,
                    "subject": template.subject,
                    "content": template.content,
                    "whatsapp_content": template.whatsapp_content,
                    "language": template.language,
                    "variables": template.variables,
                    "created_at": template.created_at.isoformat(),
                    "updated_at": template.updated_at.isoformat()
                }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(self._templates)} templates to {export_path}")
            return export_path
            
        except Exception as e:
            logger.error(f"Failed to export all templates: {e}")
            return None
