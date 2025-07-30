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
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import asdict, replace

from .models import MessageTemplate
from .config_manager import ConfigManager
from ..utils.exceptions import ValidationError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TemplateVersion:
    """Represents a single version of a template."""
    
    def __init__(self, version_id: str, template: MessageTemplate, author: str = "system", 
                 message: str = "", parent_version: str = None):
        self.version_id = version_id
        self.template = template
        self.author = author
        self.message = message
        self.parent_version = parent_version
        self.created_at = datetime.now()
        self.is_active = False  # Only one version can be active at a time
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_id": self.version_id,
            "template": {
                "id": self.template.id,
                "name": self.template.name,
                "channels": self.template.channels,
                "subject": self.template.subject,
                "content": self.template.content,
                "whatsapp_content": self.template.whatsapp_content,
                "language": self.template.language,
                "variables": self.template.variables,
                "created_at": self.template.created_at.isoformat(),
                "updated_at": self.template.updated_at.isoformat()
            },
            "author": self.author,
            "message": self.message,
            "parent_version": self.parent_version,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateVersion":
        template_data = data["template"]
        template = MessageTemplate(
            id=template_data["id"],
            name=template_data["name"],
            channels=template_data.get("channels", ["email"]),
            subject=template_data.get("subject", ""),
            content=template_data.get("content", ""),
            whatsapp_content=template_data.get("whatsapp_content", ""),
            language=template_data.get("language", "en"),
            variables=template_data.get("variables", [])
        )
        
        if "created_at" in template_data:
            template.created_at = datetime.fromisoformat(template_data["created_at"])
        if "updated_at" in template_data:
            template.updated_at = datetime.fromisoformat(template_data["updated_at"])
        
        version = cls(
            version_id=data["version_id"],
            template=template,
            author=data.get("author", "system"),
            message=data.get("message", ""),
            parent_version=data.get("parent_version")
        )
        
        if "created_at" in data:
            version.created_at = datetime.fromisoformat(data["created_at"])
        version.is_active = data.get("is_active", False)
        
        return version


class TemplateVersionManager:
    """Manages template versions with Git-like functionality."""
    
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        self.versions_dir = templates_dir / "versions"
        self.versions_dir.mkdir(exist_ok=True)
        
        # In-memory version storage
        self.versions: Dict[str, Dict[str, TemplateVersion]] = {}  # template_id -> {version_id -> version}
        self.active_versions: Dict[str, str] = {}  # template_id -> active_version_id
        
        self._load_versions()
    
    def _load_versions(self):
        """Load all versions from disk."""
        for version_file in self.versions_dir.glob("*.json"):
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                template_id = data["template_id"]
                versions_data = data.get("versions", {})
                active_version = data.get("active_version")
                
                self.versions[template_id] = {}
                for version_id, version_data in versions_data.items():
                    version = TemplateVersion.from_dict(version_data)
                    self.versions[template_id][version_id] = version
                
                if active_version:
                    self.active_versions[template_id] = active_version
                    if active_version in self.versions[template_id]:
                        self.versions[template_id][active_version].is_active = True
                
            except Exception as e:
                logger.error(f"Failed to load versions from {version_file}: {e}")
    
    def _save_versions(self, template_id: str):
        """Save versions for a specific template to disk."""
        if template_id not in self.versions:
            return
        
        version_file = self.versions_dir / f"{template_id}.json"
        
        try:
            versions_data = {}
            for version_id, version in self.versions[template_id].items():
                versions_data[version_id] = version.to_dict()
            
            data = {
                "template_id": template_id,
                "versions": versions_data,
                "active_version": self.active_versions.get(template_id),
                "updated_at": datetime.now().isoformat()
            }
            
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved versions for template {template_id}")
        except Exception as e:
            logger.error(f"Failed to save versions for template {template_id}: {e}")
    
    def create_version(self, template: MessageTemplate, author: str = "system", 
                      message: str = "", parent_version: str = None) -> str:
        """Create a new version of a template."""
        template_id = template.id
        
        # Generate version ID (timestamp-based for simplicity)
        version_id = f"v{int(datetime.now().timestamp())}"
        
        # Ensure template has versions dict
        if template_id not in self.versions:
            self.versions[template_id] = {}
        
        # If no parent specified, use current active version
        if parent_version is None:
            parent_version = self.active_versions.get(template_id)
        
        # Create version
        version = TemplateVersion(
            version_id=version_id,
            template=template,
            author=author,
            message=message,
            parent_version=parent_version
        )
        
        # Store version
        self.versions[template_id][version_id] = version
        
        # Set as active version
        self._set_active_version(template_id, version_id)
        
        # Save to disk
        self._save_versions(template_id)
        
        logger.info(f"Created version {version_id} for template {template_id}")
        return version_id
    
    def _set_active_version(self, template_id: str, version_id: str):
        """Set the active version for a template."""
        if template_id not in self.versions or version_id not in self.versions[template_id]:
            return False
        
        # Deactivate current active version
        current_active = self.active_versions.get(template_id)
        if current_active and current_active in self.versions[template_id]:
            self.versions[template_id][current_active].is_active = False
        
        # Set new active version
        self.active_versions[template_id] = version_id
        self.versions[template_id][version_id].is_active = True
        
        return True
    
    def get_active_version(self, template_id: str) -> Optional[TemplateVersion]:
        """Get the active version of a template."""
        active_version_id = self.active_versions.get(template_id)
        if not active_version_id or template_id not in self.versions:
            return None
        
        return self.versions[template_id].get(active_version_id)
    
    def get_version(self, template_id: str, version_id: str) -> Optional[TemplateVersion]:
        """Get a specific version of a template."""
        if template_id not in self.versions:
            return None
        
        return self.versions[template_id].get(version_id)
    
    def get_version_history(self, template_id: str) -> List[TemplateVersion]:
        """Get version history for a template, sorted by creation date."""
        if template_id not in self.versions:
            return []
        
        versions = list(self.versions[template_id].values())
        return sorted(versions, key=lambda v: v.created_at, reverse=True)
    
    def rollback_to_version(self, template_id: str, version_id: str) -> Optional[MessageTemplate]:
        """Rollback to a specific version (creates a new version)."""
        target_version = self.get_version(template_id, version_id)
        if not target_version:
            return None
        
        # Create a new version based on the target version
        rollback_template = target_version.template
        rollback_template.updated_at = datetime.now()
        
        new_version_id = self.create_version(
            template=rollback_template,
            author="system",
            message=f"Rollback to version {version_id}",
            parent_version=self.active_versions.get(template_id)
        )
        
        logger.info(f"Rolled back template {template_id} to version {version_id} (new version: {new_version_id})")
        return rollback_template
    
    def compare_versions(self, template_id: str, version1_id: str, version2_id: str) -> Dict[str, Any]:
        """Compare two versions of a template."""
        version1 = self.get_version(template_id, version1_id)
        version2 = self.get_version(template_id, version2_id)
        
        if not version1 or not version2:
            return {}
        
        t1, t2 = version1.template, version2.template
        
        differences = {
            "name": {"old": t1.name, "new": t2.name, "changed": t1.name != t2.name},
            "subject": {"old": t1.subject, "new": t2.subject, "changed": t1.subject != t2.subject},
            "content": {"old": t1.content, "new": t2.content, "changed": t1.content != t2.content},
            "whatsapp_content": {"old": t1.whatsapp_content, "new": t2.whatsapp_content, 
                               "changed": t1.whatsapp_content != t2.whatsapp_content},
            "channels": {"old": t1.channels, "new": t2.channels, "changed": t1.channels != t2.channels},
            "variables": {"old": t1.variables, "new": t2.variables, "changed": t1.variables != t2.variables},
            "language": {"old": t1.language, "new": t2.language, "changed": t1.language != t2.language}
        }
        
        # Calculate change summary
        changed_fields = [field for field, diff in differences.items() if diff["changed"]]
        
        return {
            "version1": {"id": version1_id, "created_at": version1.created_at, "author": version1.author},
            "version2": {"id": version2_id, "created_at": version2.created_at, "author": version2.author},
            "differences": differences,
            "changed_fields": changed_fields,
            "has_changes": len(changed_fields) > 0
        }
    
    def get_diff_text(self, template_id: str, version1_id: str, version2_id: str) -> str:
        """Get a text-based diff between two versions."""
        comparison = self.compare_versions(template_id, version1_id, version2_id)
        if not comparison.get("has_changes"):
            return "No changes between versions."
        
        diff_lines = [f"Diff between {version1_id} and {version2_id}:", ""]
        
        for field, diff in comparison["differences"].items():
            if diff["changed"]:
                diff_lines.append(f"=== {field.upper()} ===")
                diff_lines.append(f"- {diff['old']}")
                diff_lines.append(f"+ {diff['new']}")
                diff_lines.append("")
        
        return "\n".join(diff_lines)
    
    def branch_template(self, template_id: str, branch_name: str, base_version: str = None) -> str:
        """Create a branch from a template version."""
        if base_version is None:
            base_version = self.active_versions.get(template_id)
        
        base_version_obj = self.get_version(template_id, base_version)
        if not base_version_obj:
            return None
        
        # Create branch version ID
        branch_version_id = f"branch_{branch_name}_{int(datetime.now().timestamp())}"
        
        # Create branch version
        branch_template = base_version_obj.template
        branch_version = TemplateVersion(
            version_id=branch_version_id,
            template=branch_template,
            author="system",
            message=f"Created branch '{branch_name}' from {base_version}",
            parent_version=base_version
        )
        
        self.versions[template_id][branch_version_id] = branch_version
        self._save_versions(template_id)
        
        logger.info(f"Created branch '{branch_name}' for template {template_id}")
        return branch_version_id
    
    def merge_versions(self, template_id: str, source_version: str, target_version: str = None, 
                      author: str = "system") -> Optional[str]:
        """Merge one version into another (creates a new version)."""
        if target_version is None:
            target_version = self.active_versions.get(template_id)
        
        source_ver = self.get_version(template_id, source_version)
        target_ver = self.get_version(template_id, target_version)
        
        if not source_ver or not target_ver:
            return None
        
        # For simplicity, merge takes the source version's content
        # In a real implementation, this would handle conflicts
        merged_template = source_ver.template
        merged_template.updated_at = datetime.now()
        
        merge_version_id = self.create_version(
            template=merged_template,
            author=author,
            message=f"Merged {source_version} into {target_version}",
            parent_version=target_version
        )
        
        logger.info(f"Merged version {source_version} into {target_version} for template {template_id}")
        return merge_version_id
    
    def delete_version(self, template_id: str, version_id: str) -> bool:
        """Delete a specific version (cannot delete active version)."""
        if template_id not in self.versions or version_id not in self.versions[template_id]:
            return False
        
        # Cannot delete active version
        if self.active_versions.get(template_id) == version_id:
            logger.warning(f"Cannot delete active version {version_id}")
            return False
        
        del self.versions[template_id][version_id]
        self._save_versions(template_id)
        
        logger.info(f"Deleted version {version_id} for template {template_id}")
        return True
    
    def cleanup_old_versions(self, template_id: str, keep_count: int = 10):
        """Clean up old versions, keeping only the most recent ones."""
        if template_id not in self.versions:
            return
        
        versions = self.get_version_history(template_id)
        if len(versions) <= keep_count:
            return
        
        # Keep active version and most recent versions
        active_version_id = self.active_versions.get(template_id)
        versions_to_keep = set([active_version_id]) if active_version_id else set()
        
        # Add most recent versions
        for version in versions[:keep_count-1]:  # -1 for active version
            versions_to_keep.add(version.version_id)
        
        # Delete old versions
        versions_to_delete = []
        for version_id in self.versions[template_id].keys():
            if version_id not in versions_to_keep:
                versions_to_delete.append(version_id)
        
        for version_id in versions_to_delete:
            del self.versions[template_id][version_id]
        
        if versions_to_delete:
            self._save_versions(template_id)
            logger.info(f"Cleaned up {len(versions_to_delete)} old versions for template {template_id}")


class TemplateAnalytics:
    """Template analytics and performance tracking system."""
    
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        self.analytics_dir = templates_dir / "analytics"
        self.analytics_dir.mkdir(exist_ok=True)
        
        # Analytics data storage
        self.usage_stats: Dict[str, Dict[str, Any]] = {}  # template_id -> stats
        self.performance_metrics: Dict[str, Dict[str, Any]] = {}  # template_id -> metrics
        self.ab_tests: Dict[str, Dict[str, Any]] = {}  # test_id -> test_data
        self.campaign_results: Dict[str, Dict[str, Any]] = {}  # campaign_id -> results
        
        self._load_analytics_data()
    
    def _load_analytics_data(self):
        """Load analytics data from disk."""
        analytics_files = {
            "usage_stats.json": self.usage_stats,
            "performance_metrics.json": self.performance_metrics,
            "ab_tests.json": self.ab_tests,
            "campaign_results.json": self.campaign_results
        }
        
        for filename, data_dict in analytics_files.items():
            file_path = self.analytics_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        loaded_data = json.load(f)
                        data_dict.update(loaded_data)
                except Exception as e:
                    logger.error(f"Failed to load {filename}: {e}")
    
    def _save_analytics_data(self):
        """Save analytics data to disk."""
        analytics_files = {
            "usage_stats.json": self.usage_stats,
            "performance_metrics.json": self.performance_metrics,
            "ab_tests.json": self.ab_tests,
            "campaign_results.json": self.campaign_results
        }
        
        for filename, data_dict in analytics_files.items():
            file_path = self.analytics_dir / filename
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data_dict, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Failed to save {filename}: {e}")
    
    def record_template_usage(self, template_id: str, channel: str, success: bool = True, 
                             response_time: float = None, context: Dict[str, Any] = None):
        """Record template usage for analytics."""
        if template_id not in self.usage_stats:
            self.usage_stats[template_id] = {
                "total_uses": 0,
                "successful_uses": 0,
                "failed_uses": 0,
                "channels": {},
                "response_times": [],
                "contexts": [],
                "first_used": datetime.now().isoformat(),
                "last_used": None
            }
        
        stats = self.usage_stats[template_id]
        stats["total_uses"] += 1
        stats["last_used"] = datetime.now().isoformat()
        
        if success:
            stats["successful_uses"] += 1
        else:
            stats["failed_uses"] += 1
        
        # Track channel usage
        if channel not in stats["channels"]:
            stats["channels"][channel] = {"uses": 0, "successes": 0, "failures": 0}
        
        stats["channels"][channel]["uses"] += 1
        if success:
            stats["channels"][channel]["successes"] += 1
        else:
            stats["channels"][channel]["failures"] += 1
        
        # Track response times
        if response_time is not None:
            stats["response_times"].append(response_time)
            # Keep only last 100 response times
            stats["response_times"] = stats["response_times"][-100:]
        
        # Track contexts
        if context:
            stats["contexts"].append({
                "timestamp": datetime.now().isoformat(),
                "context": context
            })
            # Keep only last 50 contexts
            stats["contexts"] = stats["contexts"][-50:]
        
        self._save_analytics_data()
    
    def get_template_analytics(self, template_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics for a template."""
        usage_stats = self.usage_stats.get(template_id, {})
        performance_metrics = self.performance_metrics.get(template_id, {})
        
        # Calculate success rate
        total_uses = usage_stats.get("total_uses", 0)
        successful_uses = usage_stats.get("successful_uses", 0)
        success_rate = (successful_uses / total_uses * 100) if total_uses > 0 else 0
        
        # Calculate average response time
        response_times = usage_stats.get("response_times", [])
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "template_id": template_id,
            "usage_statistics": {
                "total_uses": total_uses,
                "successful_uses": successful_uses,
                "failed_uses": usage_stats.get("failed_uses", 0),
                "success_rate": success_rate,
                "first_used": usage_stats.get("first_used"),
                "last_used": usage_stats.get("last_used"),
                "channels": usage_stats.get("channels", {}),
                "average_response_time": avg_response_time
            },
            "performance_metrics": performance_metrics,
            "effectiveness_score": self._calculate_effectiveness_score(template_id),
            "recommendations": self._generate_performance_recommendations(template_id)
        }
    
    def _calculate_effectiveness_score(self, template_id: str) -> float:
        """Calculate an overall effectiveness score for a template (0-100)."""
        usage_stats = self.usage_stats.get(template_id, {})
        
        # Simple effectiveness calculation based on usage and success rate
        total_uses = usage_stats.get("total_uses", 0)
        successful_uses = usage_stats.get("successful_uses", 0)
        
        if total_uses == 0:
            return 0.0
        
        success_rate = (successful_uses / total_uses) * 100
        
        # Factor in usage frequency (log scale)
        import math
        usage_factor = min(math.log10(total_uses + 1) * 20, 30)
        
        return min(success_rate * 0.7 + usage_factor * 0.3, 100)
    
    def _generate_performance_recommendations(self, template_id: str) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []
        usage_stats = self.usage_stats.get(template_id, {})
        
        total_uses = usage_stats.get("total_uses", 0)
        if total_uses > 0:
            success_rate = (usage_stats.get("successful_uses", 0) / total_uses) * 100
            if success_rate < 70:
                recommendations.append("Consider revising template content to improve success rate")
        
        if total_uses < 5:
            recommendations.append("Template has low usage - consider promoting or improving visibility")
        
        return recommendations
    
    def create_ab_test(self, test_name: str, template_a_id: str, template_b_id: str) -> str:
        """Create an A/B test between two templates."""
        test_id = f"ab_test_{int(datetime.now().timestamp())}"
        
        self.ab_tests[test_id] = {
            "test_name": test_name,
            "template_a_id": template_a_id,
            "template_b_id": template_b_id,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "results": {
                "template_a": {"uses": 0, "successes": 0},
                "template_b": {"uses": 0, "successes": 0}
            }
        }
        
        self._save_analytics_data()
        return test_id
    
    def get_top_performing_templates(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performing templates by effectiveness score."""
        template_scores = []
        
        for template_id in self.usage_stats.keys():
            score = self._calculate_effectiveness_score(template_id)
            template_scores.append({
                "template_id": template_id,
                "effectiveness_score": score
            })
        
        template_scores.sort(key=lambda x: x["effectiveness_score"], reverse=True)
        return template_scores[:limit]


class TemplateSearchIndex:
    """Full-text search index for templates with advanced search capabilities."""
    
    def __init__(self):
        self.index = {}  # template_id -> searchable_content
        self.tag_index = {}  # tag -> set of template_ids
        self.category_index = {}  # category_id -> set of template_ids
        self.usage_index = {}  # template_id -> usage_score
        
    def add_template(self, template: MessageTemplate, metadata: Dict[str, Any]):
        """Add or update a template in the search index."""
        template_id = template.id
        
        # Build searchable content
        searchable_parts = [
            template.name.lower(),
            template.subject.lower(),
            template.content.lower(),
            template.whatsapp_content.lower(),
            metadata.get("description", "").lower(),
            " ".join(template.variables).lower(),
            " ".join(template.channels).lower()
        ]
        
        # Add tags to searchable content
        tags = metadata.get("tags", [])
        searchable_parts.extend([tag.lower() for tag in tags])
        
        # Store in main index
        self.index[template_id] = " ".join(filter(None, searchable_parts))
        
        # Update tag index
        for tag in tags:
            tag_lower = tag.lower()
            if tag_lower not in self.tag_index:
                self.tag_index[tag_lower] = set()
            self.tag_index[tag_lower].add(template_id)
        
        # Update category index
        category_id = metadata.get("category_id", "general")
        if category_id not in self.category_index:
            self.category_index[category_id] = set()
        self.category_index[category_id].add(template_id)
        
        # Update usage index
        self.usage_index[template_id] = metadata.get("usage_count", 0)
    
    def remove_template(self, template_id: str):
        """Remove a template from the search index."""
        # Remove from main index
        if template_id in self.index:
            del self.index[template_id]
        
        # Remove from tag index
        for tag_set in self.tag_index.values():
            tag_set.discard(template_id)
        
        # Remove from category index
        for category_set in self.category_index.values():
            category_set.discard(template_id)
        
        # Remove from usage index
        if template_id in self.usage_index:
            del self.usage_index[template_id]
    
    def search(self, query: str, category_id: str = None, tags: List[str] = None, 
               channels: List[str] = None, limit: int = 50) -> List[Tuple[str, float]]:
        """
        Search templates with scoring and filtering.
        
        Returns:
            List of (template_id, relevance_score) tuples, sorted by relevance
        """
        if not query.strip() and not tags and not category_id and not channels:
            return []
        
        query_lower = query.lower().strip()
        results = []
        
        # Get candidate templates based on filters
        candidates = set(self.index.keys())
        
        if category_id:
            candidates &= self.category_index.get(category_id, set())
        
        if tags:
            tag_candidates = set()
            for tag in tags:
                tag_candidates |= self.tag_index.get(tag.lower(), set())
            candidates &= tag_candidates
        
        # Score each candidate template
        for template_id in candidates:
            if template_id not in self.index:
                continue
                
            content = self.index[template_id]
            score = self._calculate_relevance_score(query_lower, content, template_id)
            
            if score > 0:
                results.append((template_id, score))
        
        # Sort by relevance score (descending) and limit results
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def _calculate_relevance_score(self, query: str, content: str, template_id: str) -> float:
        """Calculate relevance score for a template."""
        if not query:
            return 1.0
        
        score = 0.0
        query_terms = query.split()
        
        for term in query_terms:
            if term in content:
                # Exact match gets higher score
                score += content.count(term) * 2.0
                
                # Bonus for matches in template name (assumed to be at start of content)
                if content.startswith(term) or f" {term}" in content[:100]:
                    score += 1.0
        
        # Boost score based on usage frequency
        usage_count = self.usage_index.get(template_id, 0)
        usage_boost = min(usage_count * 0.1, 2.0)  # Cap at 2.0 boost
        score += usage_boost
        
        return score
    
    def get_popular_tags(self, limit: int = 20) -> List[Tuple[str, int]]:
        """Get most popular tags by usage."""
        tag_counts = [(tag, len(template_ids)) for tag, template_ids in self.tag_index.items()]
        tag_counts.sort(key=lambda x: x[1], reverse=True)
        return tag_counts[:limit]
    
    def suggest_tags(self, template_content: str, existing_tags: List[str] = None) -> List[str]:
        """Suggest tags based on template content and existing tag patterns."""
        existing_tags = existing_tags or []
        suggestions = []
        
        # Simple keyword-based suggestions
        content_lower = template_content.lower()
        
        # Common tag patterns
        tag_patterns = {
            "welcome": ["welcome", "greeting", "hello", "introduction"],
            "follow_up": ["follow", "reminder", "check", "update"],
            "promotional": ["sale", "discount", "offer", "promotion", "deal"],
            "support": ["help", "support", "assistance", "problem", "issue"],
            "urgent": ["urgent", "important", "asap", "immediate"],
            "seasonal": ["holiday", "christmas", "new year", "summer", "winter"],
            "newsletter": ["newsletter", "news", "update", "announcement"]
        }
        
        for tag, keywords in tag_patterns.items():
            if tag not in existing_tags and any(keyword in content_lower for keyword in keywords):
                suggestions.append(tag)
        
        return suggestions[:5]  # Limit to 5 suggestions


class TemplateRecommendationEngine:
    """Recommendation engine for templates based on usage patterns."""
    
    def __init__(self):
        self.usage_patterns = {}  # template_id -> usage_metadata
        self.similarity_cache = {}  # (template_id1, template_id2) -> similarity_score
        
    def record_usage(self, template_id: str, context: Dict[str, Any] = None):
        """Record template usage for recommendation learning."""
        if template_id not in self.usage_patterns:
            self.usage_patterns[template_id] = {
                "usage_count": 0,
                "last_used": None,
                "contexts": [],
                "success_rate": 0.0
            }
        
        pattern = self.usage_patterns[template_id]
        pattern["usage_count"] += 1
        pattern["last_used"] = datetime.now()
        
        if context:
            pattern["contexts"].append(context)
            # Keep only recent contexts (last 50)
            pattern["contexts"] = pattern["contexts"][-50:]
    
    def get_recommendations(self, template_id: str = None, category_id: str = None, 
                          limit: int = 5) -> List[Tuple[str, float, str]]:
        """
        Get template recommendations.
        
        Returns:
            List of (template_id, confidence_score, reason) tuples
        """
        recommendations = []
        
        if template_id and template_id in self.usage_patterns:
            # Find similar templates based on usage patterns
            similar_templates = self._find_similar_templates(template_id)
            for similar_id, similarity in similar_templates[:limit]:
                recommendations.append((similar_id, similarity, "Similar usage pattern"))
        
        # Add popular templates in category
        if category_id:
            popular_in_category = self._get_popular_in_category(category_id, limit)
            for pop_id, popularity in popular_in_category:
                if not any(rec[0] == pop_id for rec in recommendations):
                    recommendations.append((pop_id, popularity, "Popular in category"))
        
        # Add recently used templates
        recent_templates = self._get_recently_used(limit)
        for recent_id, recency in recent_templates:
            if not any(rec[0] == recent_id for rec in recommendations):
                recommendations.append((recent_id, recency, "Recently used"))
        
        # Sort by confidence score and limit
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:limit]
    
    def _find_similar_templates(self, template_id: str) -> List[Tuple[str, float]]:
        """Find templates with similar usage patterns."""
        if template_id not in self.usage_patterns:
            return []
        
        target_pattern = self.usage_patterns[template_id]
        similarities = []
        
        for other_id, other_pattern in self.usage_patterns.items():
            if other_id == template_id:
                continue
            
            # Calculate similarity based on usage frequency and recency
            similarity = self._calculate_pattern_similarity(target_pattern, other_pattern)
            if similarity > 0.1:  # Minimum threshold
                similarities.append((other_id, similarity))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities
    
    def _calculate_pattern_similarity(self, pattern1: Dict, pattern2: Dict) -> float:
        """Calculate similarity between two usage patterns."""
        # Simple similarity based on usage frequency and recency
        usage_similarity = min(pattern1["usage_count"], pattern2["usage_count"]) / \
                          max(pattern1["usage_count"], pattern2["usage_count"], 1)
        
        # Recency similarity (both used recently = higher similarity)
        recency_similarity = 0.5
        if pattern1["last_used"] and pattern2["last_used"]:
            time_diff = abs((pattern1["last_used"] - pattern2["last_used"]).days)
            recency_similarity = max(0, 1.0 - (time_diff / 30.0))  # 30-day window
        
        return (usage_similarity * 0.7) + (recency_similarity * 0.3)
    
    def _get_popular_in_category(self, category_id: str, limit: int) -> List[Tuple[str, float]]:
        """Get popular templates in a specific category."""
        # This would need access to template metadata - simplified for now
        popular = []
        for template_id, pattern in self.usage_patterns.items():
            popularity = min(pattern["usage_count"] / 10.0, 1.0)  # Normalize to 0-1
            popular.append((template_id, popularity))
        
        popular.sort(key=lambda x: x[1], reverse=True)
        return popular[:limit]
    
    def _get_recently_used(self, limit: int) -> List[Tuple[str, float]]:
        """Get recently used templates."""
        recent = []
        now = datetime.now()
        
        for template_id, pattern in self.usage_patterns.items():
            if pattern["last_used"]:
                days_ago = (now - pattern["last_used"]).days
                recency_score = max(0, 1.0 - (days_ago / 7.0))  # 7-day window
                if recency_score > 0:
                    recent.append((template_id, recency_score))
        
        recent.sort(key=lambda x: x[1], reverse=True)
        return recent[:limit]


class TemplateCategory:
    """Enhanced template category with hierarchical support."""
    
    def __init__(self, id: str, name: str, description: str = "", color: str = "#007ACC", 
                 parent_id: str = None, icon: str = None, sort_order: int = 0):
        self.id = id
        self.name = name
        self.description = description
        self.color = color
        self.parent_id = parent_id  # For hierarchical categories
        self.icon = icon  # Icon identifier for UI
        self.sort_order = sort_order  # For custom ordering
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.template_count = 0  # Cached count of templates in this category
        self.usage_count = 0  # How often templates in this category are used
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "parent_id": self.parent_id,
            "icon": self.icon,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "template_count": self.template_count,
            "usage_count": self.usage_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateCategory":
        category = cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            color=data.get("color", "#007ACC"),
            parent_id=data.get("parent_id"),
            icon=data.get("icon"),
            sort_order=data.get("sort_order", 0)
        )
        if "created_at" in data:
            category.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            category.updated_at = datetime.fromisoformat(data["updated_at"])
        category.template_count = data.get("template_count", 0)
        category.usage_count = data.get("usage_count", 0)
        return category
    
    def get_full_path(self, categories_dict: Dict[str, "TemplateCategory"]) -> str:
        """Get the full hierarchical path of this category."""
        path_parts = [self.name]
        current_parent_id = self.parent_id
        
        while current_parent_id and current_parent_id in categories_dict:
            parent = categories_dict[current_parent_id]
            path_parts.insert(0, parent.name)
            current_parent_id = parent.parent_id
        
        return " > ".join(path_parts)
    
    def get_children(self, categories_dict: Dict[str, "TemplateCategory"]) -> List["TemplateCategory"]:
        """Get direct children of this category."""
        return [cat for cat in categories_dict.values() if cat.parent_id == self.id]
    
    def get_all_descendants(self, categories_dict: Dict[str, "TemplateCategory"]) -> List["TemplateCategory"]:
        """Get all descendants (children, grandchildren, etc.) of this category."""
        descendants = []
        children = self.get_children(categories_dict)
        
        for child in children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants(categories_dict))
        
        return descendants


class TemplateManager:
    """Comprehensive template management system with advanced categorization."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.templates_dir = config_manager.get_templates_path()
        self.categories_file = self.templates_dir / "categories.json"
        self.templates_index_file = self.templates_dir / "index.json"
        self.search_index_file = self.templates_dir / "search_index.json"
        self.recommendations_file = self.templates_dir / "recommendations.json"
        
        # Initialize directories
        self._ensure_directories()
        
        # Load data
        self._categories: Dict[str, TemplateCategory] = {}
        self._templates: Dict[str, MessageTemplate] = {}
        self._template_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Initialize advanced features
        self.search_index = TemplateSearchIndex()
        self.recommendation_engine = TemplateRecommendationEngine()
        self.version_manager = TemplateVersionManager(self.templates_dir)
        self.analytics = TemplateAnalytics(self.templates_dir)
        
        self._load_categories()
        self._load_templates()
        self._load_search_index()
        self._load_recommendations()
        
        # Create default category if none exist
        if not self._categories:
            self._create_default_categories()
        
        # Rebuild search index if needed
        self._rebuild_search_index_if_needed()
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        (self.templates_dir / "backups").mkdir(exist_ok=True)
        (self.templates_dir / "exports").mkdir(exist_ok=True)
        (self.templates_dir / "imports").mkdir(exist_ok=True)
        (self.templates_dir / "analytics").mkdir(exist_ok=True)
    
    def _create_default_categories(self):
        """Create default template categories with hierarchical structure."""
        default_categories = [
            # Root categories
            TemplateCategory("welcome", "Welcome Messages", "Initial contact and welcome messages", 
                           "#4CAF50", icon="welcome", sort_order=1),
            TemplateCategory("follow_up", "Follow-up", "Follow-up and reminder messages", 
                           "#FF9800", icon="follow_up", sort_order=2),
            TemplateCategory("promotional", "Promotional", "Marketing and promotional content", 
                           "#E91E63", icon="promotional", sort_order=3),
            TemplateCategory("support", "Support", "Customer support templates", 
                           "#2196F3", icon="support", sort_order=4),
            TemplateCategory("general", "General", "General purpose templates", 
                           "#607D8B", icon="general", sort_order=5),
            
            # Sub-categories for promotional
            TemplateCategory("promo_sales", "Sales & Discounts", "Sales promotions and discount offers", 
                           "#E91E63", parent_id="promotional", icon="sale", sort_order=1),
            TemplateCategory("promo_events", "Events & Announcements", "Event invitations and announcements", 
                           "#E91E63", parent_id="promotional", icon="event", sort_order=2),
            TemplateCategory("promo_newsletter", "Newsletters", "Regular newsletter content", 
                           "#E91E63", parent_id="promotional", icon="newsletter", sort_order=3),
            
            # Sub-categories for support
            TemplateCategory("support_help", "Help & Assistance", "General help and assistance templates", 
                           "#2196F3", parent_id="support", icon="help", sort_order=1),
            TemplateCategory("support_technical", "Technical Support", "Technical issue resolution", 
                           "#2196F3", parent_id="support", icon="technical", sort_order=2),
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
    
    def _load_search_index(self):
        """Load search index from file."""
        if not self.search_index_file.exists():
            return
        
        try:
            with open(self.search_index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Restore search index state
            self.search_index.index = data.get("index", {})
            self.search_index.tag_index = {k: set(v) for k, v in data.get("tag_index", {}).items()}
            self.search_index.category_index = {k: set(v) for k, v in data.get("category_index", {}).items()}
            self.search_index.usage_index = data.get("usage_index", {})
            
            logger.debug("Loaded search index")
        except Exception as e:
            logger.error(f"Failed to load search index: {e}")
    
    def _save_search_index(self):
        """Save search index to file."""
        try:
            data = {
                "index": self.search_index.index,
                "tag_index": {k: list(v) for k, v in self.search_index.tag_index.items()},
                "category_index": {k: list(v) for k, v in self.search_index.category_index.items()},
                "usage_index": self.search_index.usage_index,
                "updated_at": datetime.now().isoformat()
            }
            
            with open(self.search_index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("Saved search index")
        except Exception as e:
            logger.error(f"Failed to save search index: {e}")
    
    def _load_recommendations(self):
        """Load recommendation engine data from file."""
        if not self.recommendations_file.exists():
            return
        
        try:
            with open(self.recommendations_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Restore recommendation engine state
            usage_patterns = data.get("usage_patterns", {})
            for template_id, pattern in usage_patterns.items():
                if "last_used" in pattern and pattern["last_used"]:
                    pattern["last_used"] = datetime.fromisoformat(pattern["last_used"])
                self.recommendation_engine.usage_patterns[template_id] = pattern
            
            logger.debug("Loaded recommendation engine data")
        except Exception as e:
            logger.error(f"Failed to load recommendation engine data: {e}")
    
    def _save_recommendations(self):
        """Save recommendation engine data to file."""
        try:
            usage_patterns = {}
            for template_id, pattern in self.recommendation_engine.usage_patterns.items():
                pattern_copy = pattern.copy()
                if "last_used" in pattern_copy and pattern_copy["last_used"]:
                    pattern_copy["last_used"] = pattern_copy["last_used"].isoformat()
                usage_patterns[template_id] = pattern_copy
            
            data = {
                "usage_patterns": usage_patterns,
                "updated_at": datetime.now().isoformat()
            }
            
            with open(self.recommendations_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("Saved recommendation engine data")
        except Exception as e:
            logger.error(f"Failed to save recommendation engine data: {e}")
    
    def _rebuild_search_index_if_needed(self):
        """Rebuild search index if it's empty or outdated."""
        if not self.search_index.index and self._templates:
            logger.info("Rebuilding search index...")
            for template_id, template in self._templates.items():
                metadata = self._template_metadata.get(template_id, {})
                self.search_index.add_template(template, metadata)
            self._save_search_index()
            logger.info(f"Rebuilt search index for {len(self._templates)} templates")
    
    # Public API methods
    
    def get_categories(self) -> List[TemplateCategory]:
        """Get all template categories."""
        return list(self._categories.values())
    
    def get_category(self, category_id: str) -> Optional[TemplateCategory]:
        """Get a specific category by ID."""
        return self._categories.get(category_id)
    
    def create_category(self, id: str, name: str, description: str = "", color: str = "#007ACC", 
                       parent_id: str = None, icon: str = None, sort_order: int = 0) -> TemplateCategory:
        """Create a new template category with hierarchical support."""
        if id in self._categories:
            raise ValidationError(f"Category with ID '{id}' already exists")
        
        # Validate parent category exists if specified
        if parent_id and parent_id not in self._categories:
            raise ValidationError(f"Parent category '{parent_id}' does not exist")
        
        category = TemplateCategory(id, name, description, color, parent_id, icon, sort_order)
        self._categories[id] = category
        self._save_categories()
        
        logger.info(f"Created category: {name} (parent: {parent_id})")
        return category
    
    def update_category(self, category_id: str, name: str = None, description: str = None, 
                       color: str = None, parent_id: str = None, icon: str = None, 
                       sort_order: int = None) -> bool:
        """Update an existing category."""
        if category_id not in self._categories:
            return False
        
        # Validate parent category exists if specified
        if parent_id is not None and parent_id != "" and parent_id not in self._categories:
            raise ValidationError(f"Parent category '{parent_id}' does not exist")
        
        # Prevent circular references
        if parent_id and self._would_create_circular_reference(category_id, parent_id):
            raise ValidationError("Cannot set parent category: would create circular reference")
        
        category = self._categories[category_id]
        if name is not None:
            category.name = name
        if description is not None:
            category.description = description
        if color is not None:
            category.color = color
        if parent_id is not None:
            category.parent_id = parent_id if parent_id != "" else None
        if icon is not None:
            category.icon = icon
        if sort_order is not None:
            category.sort_order = sort_order
        
        category.updated_at = datetime.now()
        self._save_categories()
        logger.info(f"Updated category: {category_id}")
        return True
    
    def delete_category(self, category_id: str, move_to_category: str = "general") -> bool:
        """Delete a category (moves templates and child categories)."""
        if category_id not in self._categories:
            return False
        
        # Move child categories to parent or root level
        category = self._categories[category_id]
        for child_category in category.get_children(self._categories):
            child_category.parent_id = category.parent_id
        
        # Move templates to specified category
        for template_id, metadata in self._template_metadata.items():
            if metadata.get("category_id") == category_id:
                metadata["category_id"] = move_to_category
        
        del self._categories[category_id]
        self._save_categories()
        self._update_templates_index()
        
        logger.info(f"Deleted category: {category_id}")
        return True
    
    def _would_create_circular_reference(self, category_id: str, new_parent_id: str) -> bool:
        """Check if setting a new parent would create a circular reference."""
        current_id = new_parent_id
        visited = set()
        
        while current_id and current_id not in visited:
            if current_id == category_id:
                return True
            visited.add(current_id)
            current_id = self._categories.get(current_id, {}).parent_id
        
        return False
    
    def get_category_hierarchy(self) -> Dict[str, Any]:
        """Get the complete category hierarchy as a nested structure."""
        def build_hierarchy(parent_id: str = None) -> List[Dict[str, Any]]:
            children = []
            for category in sorted(self._categories.values(), key=lambda c: c.sort_order):
                if category.parent_id == parent_id:
                    category_dict = category.to_dict()
                    category_dict["children"] = build_hierarchy(category.id)
                    children.append(category_dict)
            return children
        
        return {
            "categories": build_hierarchy(),
            "total_categories": len(self._categories),
            "max_depth": self._calculate_max_depth()
        }
    
    def _calculate_max_depth(self) -> int:
        """Calculate the maximum depth of the category hierarchy."""
        max_depth = 0
        
        for category in self._categories.values():
            depth = self._get_category_depth(category.id)
            max_depth = max(max_depth, depth)
        
        return max_depth
    
    def _get_category_depth(self, category_id: str) -> int:
        """Get the depth of a category in the hierarchy."""
        depth = 0
        current_id = category_id
        visited = set()
        
        while current_id and current_id not in visited:
            visited.add(current_id)
            category = self._categories.get(current_id)
            if not category or not category.parent_id:
                break
            current_id = category.parent_id
            depth += 1
        
        return depth
    
    def get_root_categories(self) -> List[TemplateCategory]:
        """Get all root-level categories (no parent)."""
        return [cat for cat in self._categories.values() if not cat.parent_id]
    
    def get_category_path(self, category_id: str) -> List[TemplateCategory]:
        """Get the full path from root to the specified category."""
        if category_id not in self._categories:
            return []
        
        path = []
        current_id = category_id
        visited = set()
        
        while current_id and current_id not in visited:
            visited.add(current_id)
            category = self._categories[current_id]
            path.insert(0, category)
            current_id = category.parent_id
        
        return path
    
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
                     description: str = "", tags: List[str] = None, author: str = "system",
                     commit_message: str = "") -> bool:
        """Save a new or updated template with versioning and advanced indexing."""
        try:
            # Validate template
            template.validate()
            
            # Validate category exists
            if category_id not in self._categories:
                logger.warning(f"Category {category_id} does not exist, using 'general'")
                category_id = "general"
            
            # Auto-suggest tags if none provided
            if not tags:
                tags = self.suggest_tags_for_template(template)
            
            # Determine if this is a new template or update
            is_new_template = template.id not in self._templates
            
            # Update timestamp
            if is_new_template:
                template.created_at = datetime.now()
                template.updated_at = datetime.now()
                if not commit_message:
                    commit_message = f"Initial version of template '{template.name}'"
            else:
                template.updated_at = datetime.now()
                if not commit_message:
                    commit_message = f"Updated template '{template.name}'"
                
                # Create backup if template exists
                self._create_template_backup(template.id)
            
            # Create version in version control system
            version_id = self.version_manager.create_version(
                template=template,
                author=author,
                message=commit_message
            )
            
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
                "usage_count": self._template_metadata.get(template.id, {}).get("usage_count", 0),
                "current_version": version_id
            }
            
            # Update search index
            self.search_index.add_template(template, self._template_metadata[template.id])
            
            # Update category template count
            if category_id in self._categories:
                self._update_category_counts()
            
            self._update_templates_index()
            self._save_search_index()
            
            logger.info(f"Saved template: {template.name} (version: {version_id}) with tags: {tags}")
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
        """Delete a template with full cleanup."""
        if template_id not in self._templates:
            return False
        
        try:
            # Create backup before deletion
            self._create_template_backup(template_id)
            
            # Remove from search index
            self.search_index.remove_template(template_id)
            
            # Remove from recommendation engine
            if template_id in self.recommendation_engine.usage_patterns:
                del self.recommendation_engine.usage_patterns[template_id]
            
            # Remove from memory
            del self._templates[template_id]
            if template_id in self._template_metadata:
                del self._template_metadata[template_id]
            
            # Remove file
            template_file = self.templates_dir / f"{template_id}.json"
            if template_file.exists():
                template_file.unlink()
            
            # Update category counts
            self._update_category_counts()
            
            self._update_templates_index()
            self._save_search_index()
            self._save_recommendations()
            
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
    
    def search_templates(self, query: str = "", category_id: str = None, tags: List[str] = None, 
                        channels: List[str] = None, limit: int = 50, 
                        include_subcategories: bool = True) -> List[Tuple[MessageTemplate, float]]:
        """Advanced template search with scoring and filtering."""
        # Handle subcategory inclusion
        search_categories = []
        if category_id:
            search_categories.append(category_id)
            if include_subcategories and category_id in self._categories:
                category = self._categories[category_id]
                descendants = category.get_all_descendants(self._categories)
                search_categories.extend([desc.id for desc in descendants])
        
        # Use search index for efficient searching
        results = []
        if query or tags or category_id or channels:
            # Search using the index
            for search_cat in search_categories or [category_id]:
                search_results = self.search_index.search(
                    query=query, 
                    category_id=search_cat, 
                    tags=tags, 
                    channels=channels, 
                    limit=limit
                )
                results.extend(search_results)
        else:
            # Return all templates with default scoring
            for template_id in self._templates.keys():
                results.append((template_id, 1.0))
        
        # Convert to template objects and sort by relevance
        template_results = []
        seen_templates = set()
        
        for template_id, score in sorted(results, key=lambda x: x[1], reverse=True):
            if template_id in seen_templates or template_id not in self._templates:
                continue
            
            template = self._templates[template_id]
            template_results.append((template, score))
            seen_templates.add(template_id)
            
            if len(template_results) >= limit:
                break
        
        return template_results
    
    def get_template_suggestions(self, partial_query: str, limit: int = 10) -> List[str]:
        """Get template name suggestions based on partial query."""
        partial_lower = partial_query.lower()
        suggestions = []
        
        for template in self._templates.values():
            if partial_lower in template.name.lower():
                suggestions.append(template.name)
        
        return sorted(suggestions)[:limit]
    
    def get_popular_tags(self, limit: int = 20) -> List[Tuple[str, int]]:
        """Get most popular tags across all templates."""
        return self.search_index.get_popular_tags(limit)
    
    def suggest_tags_for_template(self, template: MessageTemplate, existing_tags: List[str] = None) -> List[str]:
        """Suggest tags for a template based on its content."""
        content = f"{template.name} {template.subject} {template.content} {template.whatsapp_content}"
        return self.search_index.suggest_tags(content, existing_tags)
    
    def get_templates_by_tags(self, tags: List[str], match_all: bool = False) -> List[MessageTemplate]:
        """Get templates that have specific tags."""
        if not tags:
            return []
        
        matching_templates = []
        
        for template_id, metadata in self._template_metadata.items():
            template_tags = set(tag.lower() for tag in metadata.get("tags", []))
            search_tags = set(tag.lower() for tag in tags)
            
            if match_all:
                # All tags must be present
                if search_tags.issubset(template_tags):
                    matching_templates.append(self._templates[template_id])
            else:
                # Any tag can be present
                if search_tags.intersection(template_tags):
                    matching_templates.append(self._templates[template_id])
        
        return matching_templates
    
    def add_template_tags(self, template_id: str, tags: List[str]) -> bool:
        """Add tags to a template."""
        if template_id not in self._template_metadata:
            return False
        
        metadata = self._template_metadata[template_id]
        existing_tags = set(metadata.get("tags", []))
        new_tags = set(tags)
        
        # Add new tags
        all_tags = list(existing_tags.union(new_tags))
        metadata["tags"] = all_tags
        metadata["updated_at"] = datetime.now().isoformat()
        
        # Update search index
        if template_id in self._templates:
            self.search_index.add_template(self._templates[template_id], metadata)
        
        self._update_templates_index()
        self._save_search_index()
        
        logger.info(f"Added tags {tags} to template {template_id}")
        return True
    
    def remove_template_tags(self, template_id: str, tags: List[str]) -> bool:
        """Remove tags from a template."""
        if template_id not in self._template_metadata:
            return False
        
        metadata = self._template_metadata[template_id]
        existing_tags = set(metadata.get("tags", []))
        remove_tags = set(tags)
        
        # Remove tags
        remaining_tags = list(existing_tags - remove_tags)
        metadata["tags"] = remaining_tags
        metadata["updated_at"] = datetime.now().isoformat()
        
        # Update search index
        if template_id in self._templates:
            self.search_index.add_template(self._templates[template_id], metadata)
        
        self._update_templates_index()
        self._save_search_index()
        
        logger.info(f"Removed tags {tags} from template {template_id}")
        return True
    
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
    
    def increment_template_usage(self, template_id: str, channel: str = "email", 
                                success: bool = True, response_time: float = None,
                                context: Dict[str, Any] = None):
        """Increment usage count for a template and record usage pattern with analytics."""
        if template_id in self._template_metadata:
            # Update metadata
            self._template_metadata[template_id]["usage_count"] = \
                self._template_metadata[template_id].get("usage_count", 0) + 1
            self._template_metadata[template_id]["updated_at"] = datetime.now().isoformat()
            
            # Update search index usage
            self.search_index.usage_index[template_id] = \
                self._template_metadata[template_id]["usage_count"]
            
            # Record usage in recommendation engine
            self.recommendation_engine.record_usage(template_id, context)
            
            # Record usage in analytics system
            self.analytics.record_template_usage(
                template_id=template_id,
                channel=channel,
                success=success,
                response_time=response_time,
                context=context
            )
            
            # Update category usage count
            category_id = self._template_metadata[template_id].get("category_id")
            if category_id and category_id in self._categories:
                self._categories[category_id].usage_count += 1
            
            self._update_templates_index()
            self._save_search_index()
            self._save_recommendations()
            
            logger.debug(f"Incremented usage for template {template_id} on {channel} channel")
    
    def get_template_recommendations(self, template_id: str = None, category_id: str = None, 
                                   limit: int = 5) -> List[Tuple[MessageTemplate, float, str]]:
        """Get template recommendations based on usage patterns."""
        recommendations = self.recommendation_engine.get_recommendations(
            template_id=template_id, 
            category_id=category_id, 
            limit=limit
        )
        
        # Convert to template objects
        template_recommendations = []
        for rec_id, confidence, reason in recommendations:
            if rec_id in self._templates:
                template_recommendations.append((self._templates[rec_id], confidence, reason))
        
        return template_recommendations
    
    def get_similar_templates(self, template_id: str, limit: int = 5) -> List[Tuple[MessageTemplate, float]]:
        """Get templates similar to the specified template."""
        if template_id not in self._templates:
            return []
        
        template = self._templates[template_id]
        metadata = self._template_metadata.get(template_id, {})
        
        # Search for similar content
        search_query = f"{template.name} {template.subject}"
        similar_results = self.search_index.search(
            query=search_query,
            category_id=metadata.get("category_id"),
            limit=limit + 1  # +1 to exclude the original template
        )
        
        # Filter out the original template and convert to template objects
        similar_templates = []
        for sim_id, score in similar_results:
            if sim_id != template_id and sim_id in self._templates:
                similar_templates.append((self._templates[sim_id], score))
        
        return similar_templates[:limit]
    
    def _update_category_counts(self):
        """Update template counts for all categories."""
        # Reset counts
        for category in self._categories.values():
            category.template_count = 0
        
        # Count templates in each category
        for metadata in self._template_metadata.values():
            category_id = metadata.get("category_id", "general")
            if category_id in self._categories:
                self._categories[category_id].template_count += 1
        
        self._save_categories()
    
    def get_category_analytics(self, category_id: str) -> Dict[str, Any]:
        """Get analytics for a specific category."""
        if category_id not in self._categories:
            return {}
        
        category = self._categories[category_id]
        templates_in_category = self.get_templates(category_id)
        
        # Calculate statistics
        total_usage = sum(
            self._template_metadata.get(t.id, {}).get("usage_count", 0) 
            for t in templates_in_category
        )
        
        avg_usage = total_usage / len(templates_in_category) if templates_in_category else 0
        
        # Most used template in category
        most_used = None
        max_usage = 0
        for template in templates_in_category:
            usage = self._template_metadata.get(template.id, {}).get("usage_count", 0)
            if usage > max_usage:
                max_usage = usage
                most_used = template
        
        # Tag distribution
        tag_counts = {}
        for template in templates_in_category:
            tags = self._template_metadata.get(template.id, {}).get("tags", [])
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        return {
            "category": category.to_dict(),
            "template_count": len(templates_in_category),
            "total_usage": total_usage,
            "average_usage": avg_usage,
            "most_used_template": most_used.to_dict() if most_used else None,
            "popular_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "subcategories": [child.to_dict() for child in category.get_children(self._categories)]
        }
    
    # Version Management Methods
    
    def get_template_versions(self, template_id: str) -> List[Dict[str, Any]]:
        """Get version history for a template."""
        versions = self.version_manager.get_version_history(template_id)
        return [
            {
                "version_id": v.version_id,
                "author": v.author,
                "message": v.message,
                "created_at": v.created_at.isoformat(),
                "is_active": v.is_active,
                "parent_version": v.parent_version
            }
            for v in versions
        ]
    
    def get_template_version(self, template_id: str, version_id: str) -> Optional[MessageTemplate]:
        """Get a specific version of a template."""
        version = self.version_manager.get_version(template_id, version_id)
        return version.template if version else None
    
    def rollback_template(self, template_id: str, version_id: str, author: str = "system") -> bool:
        """Rollback a template to a specific version."""
        try:
            rolled_back_template = self.version_manager.rollback_to_version(template_id, version_id)
            if not rolled_back_template:
                return False
            
            # Update the current template
            self._templates[template_id] = rolled_back_template
            self._save_template_file(rolled_back_template)
            
            # Update metadata
            if template_id in self._template_metadata:
                self._template_metadata[template_id]["updated_at"] = rolled_back_template.updated_at.isoformat()
                self._template_metadata[template_id]["current_version"] = self.version_manager.active_versions.get(template_id)
            
            # Update search index
            self.search_index.add_template(rolled_back_template, self._template_metadata.get(template_id, {}))
            
            self._update_templates_index()
            self._save_search_index()
            
            logger.info(f"Rolled back template {template_id} to version {version_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback template {template_id} to version {version_id}: {e}")
            return False
    
    def compare_template_versions(self, template_id: str, version1_id: str, version2_id: str) -> Dict[str, Any]:
        """Compare two versions of a template."""
        return self.version_manager.compare_versions(template_id, version1_id, version2_id)
    
    def get_template_diff(self, template_id: str, version1_id: str, version2_id: str) -> str:
        """Get a text-based diff between two template versions."""
        return self.version_manager.get_diff_text(template_id, version1_id, version2_id)
    
    def create_template_branch(self, template_id: str, branch_name: str, base_version: str = None) -> Optional[str]:
        """Create a branch from a template version."""
        try:
            branch_version_id = self.version_manager.branch_template(template_id, branch_name, base_version)
            if branch_version_id:
                logger.info(f"Created branch '{branch_name}' for template {template_id}")
            return branch_version_id
        except Exception as e:
            logger.error(f"Failed to create branch for template {template_id}: {e}")
            return None
    
    def merge_template_versions(self, template_id: str, source_version: str, 
                               target_version: str = None, author: str = "system") -> Optional[str]:
        """Merge one template version into another."""
        try:
            merge_version_id = self.version_manager.merge_versions(
                template_id, source_version, target_version, author
            )
            
            if merge_version_id:
                # Update current template with merged version
                merged_version = self.version_manager.get_active_version(template_id)
                if merged_version:
                    self._templates[template_id] = merged_version.template
                    self._save_template_file(merged_version.template)
                    
                    # Update metadata
                    if template_id in self._template_metadata:
                        self._template_metadata[template_id]["updated_at"] = merged_version.template.updated_at.isoformat()
                        self._template_metadata[template_id]["current_version"] = merge_version_id
                    
                    # Update search index
                    self.search_index.add_template(merged_version.template, self._template_metadata.get(template_id, {}))
                    
                    self._update_templates_index()
                    self._save_search_index()
                
                logger.info(f"Merged versions for template {template_id}")
            
            return merge_version_id
            
        except Exception as e:
            logger.error(f"Failed to merge versions for template {template_id}: {e}")
            return None
    
    def delete_template_version(self, template_id: str, version_id: str) -> bool:
        """Delete a specific version of a template."""
        try:
            success = self.version_manager.delete_version(template_id, version_id)
            if success:
                logger.info(f"Deleted version {version_id} for template {template_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to delete version {version_id} for template {template_id}: {e}")
            return False
    
    def cleanup_template_versions(self, template_id: str, keep_count: int = 10):
        """Clean up old versions of a template."""
        try:
            self.version_manager.cleanup_old_versions(template_id, keep_count)
            logger.info(f"Cleaned up old versions for template {template_id}")
        except Exception as e:
            logger.error(f"Failed to cleanup versions for template {template_id}: {e}")
    
    def get_template_change_log(self, template_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get a change log for a template showing version history."""
        versions = self.version_manager.get_version_history(template_id)
        
        change_log = []
        for i, version in enumerate(versions[:limit]):
            entry = {
                "version_id": version.version_id,
                "author": version.author,
                "message": version.message,
                "created_at": version.created_at.isoformat(),
                "is_active": version.is_active,
                "changes": []
            }
            
            # Compare with previous version to show changes
            if i < len(versions) - 1:
                prev_version = versions[i + 1]
                comparison = self.version_manager.compare_versions(
                    template_id, prev_version.version_id, version.version_id
                )
                if comparison.get("has_changes"):
                    entry["changes"] = comparison["changed_fields"]
            
            change_log.append(entry)
        
        return change_log
    
    # Analytics and Performance Tracking Methods
    
    def get_template_analytics(self, template_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics for a template."""
        return self.analytics.get_template_analytics(template_id)
    
    def get_top_performing_templates(self, limit: int = 10, criteria: str = "effectiveness_score") -> List[Dict[str, Any]]:
        """Get top performing templates."""
        top_templates = self.analytics.get_top_performing_templates(limit)
        
        # Enrich with template information
        enriched_results = []
        for result in top_templates:
            template_id = result["template_id"]
            if template_id in self._templates:
                template = self._templates[template_id]
                metadata = self._template_metadata.get(template_id, {})
                
                enriched_results.append({
                    "template": {
                        "id": template.id,
                        "name": template.name,
                        "channels": template.channels,
                        "category_id": metadata.get("category_id", "general")
                    },
                    "effectiveness_score": result["effectiveness_score"],
                    "analytics": self.analytics.get_template_analytics(template_id)
                })
        
        return enriched_results
    
    def create_ab_test(self, test_name: str, template_a_id: str, template_b_id: str) -> Optional[str]:
        """Create an A/B test between two templates."""
        # Validate templates exist
        if template_a_id not in self._templates or template_b_id not in self._templates:
            logger.error("Both templates must exist to create A/B test")
            return None
        
        try:
            test_id = self.analytics.create_ab_test(test_name, template_a_id, template_b_id)
            logger.info(f"Created A/B test '{test_name}' between {template_a_id} and {template_b_id}")
            return test_id
        except Exception as e:
            logger.error(f"Failed to create A/B test: {e}")
            return None
    
    def record_campaign_result(self, campaign_id: str, template_id: str, channel: str,
                              total_sent: int, successful: int, failed: int,
                              open_rate: float = None, click_rate: float = None,
                              conversion_rate: float = None, metadata: Dict[str, Any] = None):
        """Record campaign results for performance tracking."""
        try:
            self.analytics.record_campaign_result(
                campaign_id=campaign_id,
                template_id=template_id,
                channel=channel,
                total_sent=total_sent,
                successful=successful,
                failed=failed,
                open_rate=open_rate,
                click_rate=click_rate,
                conversion_rate=conversion_rate,
                metadata=metadata
            )
            logger.info(f"Recorded campaign results for {campaign_id}")
        except Exception as e:
            logger.error(f"Failed to record campaign results: {e}")
    
    def get_analytics_dashboard_data(self) -> Dict[str, Any]:
        """Get data for analytics dashboard."""
        try:
            # Get overall statistics
            total_templates = len(self._templates)
            total_categories = len(self._categories)
            
            # Get top performers
            top_performers = self.get_top_performing_templates(5)
            
            # Get category performance
            category_performance = {}
            for category_id, category in self._categories.items():
                templates_in_category = self.get_templates(category_id)
                if templates_in_category:
                    total_usage = sum(
                        self._template_metadata.get(t.id, {}).get("usage_count", 0)
                        for t in templates_in_category
                    )
                    avg_effectiveness = sum(
                        self.analytics._calculate_effectiveness_score(t.id)
                        for t in templates_in_category
                    ) / len(templates_in_category)
                    
                    category_performance[category_id] = {
                        "name": category.name,
                        "template_count": len(templates_in_category),
                        "total_usage": total_usage,
                        "average_effectiveness": avg_effectiveness
                    }
            
            # Get recent activity (templates used in last 7 days)
            recent_activity = []
            cutoff_date = datetime.now() - timedelta(days=7)
            
            for template_id, stats in self.analytics.usage_stats.items():
                last_used_str = stats.get("last_used")
                if last_used_str:
                    try:
                        last_used = datetime.fromisoformat(last_used_str)
                        if last_used >= cutoff_date and template_id in self._templates:
                            template = self._templates[template_id]
                            recent_activity.append({
                                "template_id": template_id,
                                "template_name": template.name,
                                "last_used": last_used_str,
                                "usage_count": stats.get("total_uses", 0)
                            })
                    except ValueError:
                        continue
            
            # Sort by last used
            recent_activity.sort(key=lambda x: x["last_used"], reverse=True)
            
            return {
                "overview": {
                    "total_templates": total_templates,
                    "total_categories": total_categories,
                    "active_templates": len([t for t in self.analytics.usage_stats.values() 
                                           if t.get("total_uses", 0) > 0]),
                    "total_usage": sum(t.get("total_uses", 0) for t in self.analytics.usage_stats.values())
                },
                "top_performers": top_performers,
                "category_performance": category_performance,
                "recent_activity": recent_activity[:10],  # Last 10 activities
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate dashboard data: {e}")
            return {}
    
    def export_analytics_report(self, template_ids: List[str] = None, 
                               export_path: Path = None) -> Optional[Path]:
        """Export analytics report to file."""
        try:
            if export_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_path = self.templates_dir / "analytics" / f"analytics_report_{timestamp}.json"
            
            # Generate comprehensive report
            report_data = {
                "report_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "template_count": len(template_ids) if template_ids else len(self._templates),
                    "report_type": "comprehensive_analytics"
                },
                "dashboard_data": self.get_analytics_dashboard_data(),
                "detailed_analytics": {}
            }
            
            # Add detailed analytics for each template
            templates_to_analyze = template_ids if template_ids else list(self._templates.keys())
            for template_id in templates_to_analyze:
                if template_id in self._templates:
                    template = self._templates[template_id]
                    report_data["detailed_analytics"][template_id] = {
                        "template_info": {
                            "id": template.id,
                            "name": template.name,
                            "channels": template.channels,
                            "category": self._template_metadata.get(template_id, {}).get("category_id", "general")
                        },
                        "analytics": self.get_template_analytics(template_id),
                        "versions": self.get_template_versions(template_id)
                    }
            
            # Save report
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported analytics report to {export_path}")
            return export_path
            
        except Exception as e:
            logger.error(f"Failed to export analytics report: {e}")
            return None
    
    # Enhanced Import/Export System
    
    def bulk_import_templates(self, import_path: Path, category_id: str = None,
                             progress_callback: Optional[callable] = None,
                             validation_mode: str = "strict") -> Dict[str, Any]:
        """
        Bulk import templates with progress tracking and validation.
        
        Args:
            import_path: Path to import file or directory
            category_id: Default category for imported templates
            progress_callback: Callback function for progress updates
            validation_mode: "strict", "lenient", or "skip" validation
            
        Returns:
            Dictionary with import results and statistics
        """
        import_results = {
            "total_processed": 0,
            "successful_imports": 0,
            "failed_imports": 0,
            "skipped_imports": 0,
            "imported_templates": [],
            "errors": [],
            "warnings": []
        }
        
        try:
            # Determine import type (single file or directory)
            if import_path.is_file():
                files_to_process = [import_path]
            elif import_path.is_dir():
                # Find all JSON files in directory
                files_to_process = list(import_path.glob("*.json"))
            else:
                import_results["errors"].append(f"Import path does not exist: {import_path}")
                return import_results
            
            total_files = len(files_to_process)
            import_results["total_processed"] = total_files
            
            for i, file_path in enumerate(files_to_process):
                if progress_callback:
                    progress_callback(i, total_files, f"Processing {file_path.name}")
                
                try:
                    # Load and validate file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Handle different import formats
                    if "templates" in data:
                        # Bulk export format
                        templates_data = data["templates"]
                        categories_data = data.get("categories", {})
                        metadata = data.get("metadata", {})
                        
                        # Import categories first
                        for cat_id, cat_data in categories_data.items():
                            if cat_id not in self._categories:
                                try:
                                    category = TemplateCategory.from_dict(cat_data)
                                    self._categories[cat_id] = category
                                    import_results["warnings"].append(f"Imported category: {category.name}")
                                except Exception as e:
                                    import_results["warnings"].append(f"Failed to import category {cat_id}: {e}")
                        
                        # Import templates
                        for template_id, template_data in templates_data.items():
                            result = self._import_single_template(
                                template_data, 
                                metadata.get(template_id, {}),
                                category_id,
                                validation_mode
                            )
                            
                            if result["success"]:
                                import_results["successful_imports"] += 1
                                import_results["imported_templates"].append(result["template_id"])
                            else:
                                import_results["failed_imports"] += 1
                                import_results["errors"].extend(result["errors"])
                    
                    elif "template" in data:
                        # Single template export format
                        template_data = data["template"]
                        template_metadata = data.get("metadata", {})
                        
                        result = self._import_single_template(
                            template_data,
                            template_metadata,
                            category_id,
                            validation_mode
                        )
                        
                        if result["success"]:
                            import_results["successful_imports"] += 1
                            import_results["imported_templates"].append(result["template_id"])
                        else:
                            import_results["failed_imports"] += 1
                            import_results["errors"].extend(result["errors"])
                    
                    else:
                        # Try to import as direct template data
                        result = self._import_single_template(
                            data,
                            {},
                            category_id,
                            validation_mode
                        )
                        
                        if result["success"]:
                            import_results["successful_imports"] += 1
                            import_results["imported_templates"].append(result["template_id"])
                        else:
                            import_results["failed_imports"] += 1
                            import_results["errors"].extend(result["errors"])
                
                except Exception as e:
                    import_results["failed_imports"] += 1
                    import_results["errors"].append(f"Failed to process {file_path.name}: {e}")
            
            # Save updated categories and update search index
            if import_results["successful_imports"] > 0:
                self._save_categories()
                self._update_templates_index()
                self._save_search_index()
                
                # Update category counts
                self._update_category_counts()
            
            if progress_callback:
                progress_callback(total_files, total_files, "Import completed")
            
            logger.info(f"Bulk import completed: {import_results['successful_imports']} successful, "
                       f"{import_results['failed_imports']} failed")
            
        except Exception as e:
            import_results["errors"].append(f"Bulk import failed: {e}")
            logger.error(f"Bulk import failed: {e}")
        
        return import_results
    
    def _import_single_template(self, template_data: Dict[str, Any], metadata: Dict[str, Any],
                               default_category: str = None, validation_mode: str = "strict") -> Dict[str, Any]:
        """Import a single template with validation."""
        result = {
            "success": False,
            "template_id": None,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Create template object
            template = MessageTemplate(
                id=template_data.get("id", f"imported_{int(datetime.now().timestamp())}"),
                name=template_data.get("name", "Imported Template"),
                channels=template_data.get("channels", ["email"]),
                subject=template_data.get("subject", ""),
                content=template_data.get("content", ""),
                whatsapp_content=template_data.get("whatsapp_content", ""),
                language=template_data.get("language", "en"),
                variables=template_data.get("variables", [])
            )
            
            # Handle ID conflicts
            original_id = template.id
            if template.id in self._templates:
                if validation_mode == "strict":
                    result["errors"].append(f"Template ID '{template.id}' already exists")
                    return result
                elif validation_mode == "lenient":
                    # Generate new ID
                    timestamp = int(datetime.now().timestamp())
                    template.id = f"{original_id}_imported_{timestamp}"
                    result["warnings"].append(f"Template ID changed from '{original_id}' to '{template.id}'")
            
            # Validate template
            if validation_mode != "skip":
                try:
                    template.validate()
                except ValidationError as e:
                    if validation_mode == "strict":
                        result["errors"].append(f"Template validation failed: {e}")
                        return result
                    else:
                        result["warnings"].append(f"Template validation warning: {e}")
            
            # Determine category
            category_id = metadata.get("category_id") or default_category or "general"
            if category_id not in self._categories:
                if validation_mode == "strict":
                    result["errors"].append(f"Category '{category_id}' does not exist")
                    return result
                else:
                    category_id = "general"
                    result["warnings"].append(f"Category not found, using 'general'")
            
            # Save template
            success = self.save_template(
                template=template,
                category_id=category_id,
                description=metadata.get("description", f"Imported template"),
                tags=metadata.get("tags", []),
                author="import_system",
                commit_message=f"Imported template from external source"
            )
            
            if success:
                result["success"] = True
                result["template_id"] = template.id
            else:
                result["errors"].append("Failed to save imported template")
        
        except Exception as e:
            result["errors"].append(f"Import error: {e}")
        
        return result
    
    def validate_import_file(self, import_path: Path) -> Dict[str, Any]:
        """
        Validate an import file before importing.
        
        Returns:
            Validation results with details about the file
        """
        validation_result = {
            "valid": False,
            "format": "unknown",
            "template_count": 0,
            "category_count": 0,
            "errors": [],
            "warnings": [],
            "preview": {}
        }
        
        try:
            if not import_path.exists():
                validation_result["errors"].append("Import file does not exist")
                return validation_result
            
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Detect format
            if "templates" in data and "export_info" in data:
                validation_result["format"] = "bulk_export_v2"
                templates_data = data["templates"]
                categories_data = data.get("categories", {})
            elif "templates" in data:
                validation_result["format"] = "bulk_export_v1"
                templates_data = data["templates"]
                categories_data = data.get("categories", {})
            elif "template" in data:
                validation_result["format"] = "single_template"
                templates_data = {data["template"]["id"]: data["template"]}
                categories_data = {}
            else:
                # Try to parse as direct template
                if "id" in data and "name" in data:
                    validation_result["format"] = "direct_template"
                    templates_data = {data["id"]: data}
                    categories_data = {}
                else:
                    validation_result["errors"].append("Unrecognized file format")
                    return validation_result
            
            validation_result["template_count"] = len(templates_data)
            validation_result["category_count"] = len(categories_data)
            
            # Validate templates
            template_errors = []
            template_warnings = []
            
            for template_id, template_data in templates_data.items():
                try:
                    # Basic validation
                    if not template_data.get("name"):
                        template_errors.append(f"Template {template_id}: Missing name")
                    
                    channels = template_data.get("channels", ["email"])
                    if "email" in channels and not template_data.get("subject"):
                        template_warnings.append(f"Template {template_id}: Email template missing subject")
                    
                    if "whatsapp" in channels and not template_data.get("whatsapp_content"):
                        template_warnings.append(f"Template {template_id}: WhatsApp template missing content")
                    
                    # Check for ID conflicts
                    if template_id in self._templates:
                        template_warnings.append(f"Template {template_id}: ID already exists")
                
                except Exception as e:
                    template_errors.append(f"Template {template_id}: Validation error - {e}")
            
            validation_result["errors"].extend(template_errors)
            validation_result["warnings"].extend(template_warnings)
            
            # Create preview
            preview_templates = list(templates_data.items())[:3]  # First 3 templates
            validation_result["preview"] = {
                "templates": [
                    {
                        "id": tid,
                        "name": tdata.get("name", "Unknown"),
                        "channels": tdata.get("channels", ["email"])
                    }
                    for tid, tdata in preview_templates
                ],
                "categories": [
                    {
                        "id": cid,
                        "name": cdata.get("name", "Unknown")
                    }
                    for cid, cdata in list(categories_data.items())[:3]
                ]
            }
            
            # Mark as valid if no critical errors
            validation_result["valid"] = len(validation_result["errors"]) == 0
            
        except json.JSONDecodeError as e:
            validation_result["errors"].append(f"Invalid JSON format: {e}")
        except Exception as e:
            validation_result["errors"].append(f"Validation failed: {e}")
        
        return validation_result
    
    def bulk_export_templates(self, template_ids: List[str] = None, export_path: Path = None,
                             include_categories: bool = True, include_metadata: bool = True,
                             include_analytics: bool = False, include_versions: bool = False,
                             progress_callback: Optional[callable] = None) -> Optional[Path]:
        """
        Enhanced bulk export with comprehensive options.
        
        Args:
            template_ids: List of template IDs to export (None for all)
            export_path: Export file path
            include_categories: Include category definitions
            include_metadata: Include template metadata
            include_analytics: Include analytics data
            include_versions: Include version history
            progress_callback: Progress callback function
            
        Returns:
            Path to exported file or None if failed
        """
        try:
            if export_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_path = self.templates_dir / "exports" / f"bulk_export_{timestamp}.json"
            
            # Determine templates to export
            templates_to_export = template_ids if template_ids else list(self._templates.keys())
            total_templates = len(templates_to_export)
            
            export_data = {
                "export_info": {
                    "exported_at": datetime.now().isoformat(),
                    "version": "2.0",
                    "total_templates": total_templates,
                    "export_options": {
                        "include_categories": include_categories,
                        "include_metadata": include_metadata,
                        "include_analytics": include_analytics,
                        "include_versions": include_versions
                    }
                },
                "templates": {},
                "metadata": {},
                "categories": {},
                "analytics": {},
                "versions": {}
            }
            
            # Export categories
            if include_categories:
                for cat_id, category in self._categories.items():
                    export_data["categories"][cat_id] = category.to_dict()
            
            # Export templates and related data
            for i, template_id in enumerate(templates_to_export):
                if progress_callback:
                    progress_callback(i, total_templates, f"Exporting {template_id}")
                
                if template_id not in self._templates:
                    continue
                
                template = self._templates[template_id]
                
                # Export template data
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
                
                # Export metadata
                if include_metadata and template_id in self._template_metadata:
                    export_data["metadata"][template_id] = self._template_metadata[template_id].copy()
                
                # Export analytics
                if include_analytics:
                    analytics_data = self.get_template_analytics(template_id)
                    export_data["analytics"][template_id] = analytics_data
                
                # Export versions
                if include_versions:
                    versions_data = self.get_template_versions(template_id)
                    export_data["versions"][template_id] = versions_data
            
            # Save export file
            export_path.parent.mkdir(parents=True, exist_ok=True)
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            if progress_callback:
                progress_callback(total_templates, total_templates, "Export completed")
            
            logger.info(f"Bulk exported {total_templates} templates to {export_path}")
            return export_path
            
        except Exception as e:
            logger.error(f"Bulk export failed: {e}")
            return None
    
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
