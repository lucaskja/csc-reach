"""
Configuration management for Multi-Channel Bulk Messaging System.
"""

import json
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

from ..utils.exceptions import ConfigurationError
from ..utils.platform_utils import get_config_dir, get_app_data_dir
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """Configuration manager for the application."""
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file (optional)
        """
        self.config_dir = get_config_dir()
        self.config_file = config_file or (self.config_dir / "config.yaml")
        self.user_config_file = self.config_dir / "user_config.json"
        
        # Default configuration
        self._default_config = {
            "app": {
                "language": "en",
                "theme": "system",
                "auto_save": True,
                "log_level": "INFO"
            },
            "email": {
                "outlook_profile": "default",
                "signature_include": True,
                "batch_size": 50
            },
            "whatsapp": {
                "enabled": False,
                "rate_limit_per_minute": 20,
                "daily_message_limit": 1000,
                "api_version": "v18.0",
                "timeout_seconds": 30,
                "delay_between_messages": 3.0,
                "auto_save_credentials": True
            },
            "quotas": {
                "daily_limit": 100,
                "reset_time": "00:00",
                "warning_threshold": 90
            },
            "templates": {
                "default_email": "welcome_email"
            },
            "ui": {
                "window_width": 1200,
                "window_height": 800,
                "remember_geometry": True
            },
            "logging": {
                "file_enabled": True,
                "console_enabled": True,
                "max_file_size": "10MB",
                "backup_count": 5
            }
        }
        
        self._config = self._default_config.copy()
        self._user_config = {}
        
        # Load configurations
        self._load_config()
        self._load_user_config()
    
    def _load_config(self) -> None:
        """Load main configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    if self.config_file.suffix.lower() in ['.yaml', '.yml']:
                        file_config = yaml.safe_load(f) or {}
                    else:
                        file_config = json.load(f)
                
                # Merge with default config
                self._config = self._deep_merge(self._default_config, file_config)
                logger.info(f"Loaded configuration from {self.config_file}")
            else:
                # Create default config file
                self.save_config()
                logger.info("Created default configuration file")
                
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise ConfigurationError(f"Failed to load configuration: {e}")
    
    def _load_user_config(self) -> None:
        """Load user-specific configuration."""
        try:
            if self.user_config_file.exists():
                with open(self.user_config_file, 'r', encoding='utf-8') as f:
                    self._user_config = json.load(f)
                logger.debug("Loaded user configuration")
        except Exception as e:
            logger.warning(f"Failed to load user configuration: {e}")
            self._user_config = {}
    
    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries.
        
        Args:
            base: Base dictionary
            update: Dictionary to merge into base
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key (dot-separated for nested values)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        # Check user config first
        value = self._get_nested_value(self._user_config, key)
        if value is not None:
            return value
        
        # Check main config
        value = self._get_nested_value(self._config, key)
        if value is not None:
            return value
        
        return default
    
    def set(self, key: str, value: Any, user_config: bool = True) -> None:
        """
        Set configuration value.
        
        Args:
            key: Configuration key (dot-separated for nested values)
            value: Value to set
            user_config: Whether to save in user config (True) or main config (False)
        """
        target_config = self._user_config if user_config else self._config
        self._set_nested_value(target_config, key, value)
        
        if user_config:
            self.save_user_config()
        else:
            self.save_config()
    
    def _get_nested_value(self, config: Dict[str, Any], key: str) -> Any:
        """Get nested value from configuration dictionary."""
        keys = key.split('.')
        current = config
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        
        return current
    
    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any) -> None:
        """Set nested value in configuration dictionary."""
        keys = key.split('.')
        current = config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def save_config(self) -> None:
        """Save main configuration to file."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                if self.config_file.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(self._config, f, default_flow_style=False, indent=2)
                else:
                    json.dump(self._config, f, indent=2)
            
            logger.debug(f"Saved configuration to {self.config_file}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise ConfigurationError(f"Failed to save configuration: {e}")
    
    def save_user_config(self) -> None:
        """Save user configuration to file."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            with open(self.user_config_file, 'w', encoding='utf-8') as f:
                json.dump(self._user_config, f, indent=2)
            
            logger.debug("Saved user configuration")
            
        except Exception as e:
            logger.warning(f"Failed to save user configuration: {e}")
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults."""
        self._config = self._default_config.copy()
        self._user_config = {}
        self.save_config()
        self.save_user_config()
        logger.info("Reset configuration to defaults")
    
    def get_app_data_path(self) -> Path:
        """Get application data directory path."""
        return get_app_data_dir()
    
    def get_templates_path(self) -> Path:
        """Get templates directory path."""
        templates_dir = self.get_app_data_path() / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)
        return templates_dir
    
    def get_logs_path(self) -> Path:
        """Get logs directory path."""
        from ..utils.platform_utils import get_logs_dir
        return get_logs_dir()
    
    # Convenience methods for common configuration values
    
    def get_language(self) -> str:
        """Get current language setting."""
        return self.get("app.language", "en")
    
    def set_language(self, language: str) -> None:
        """Set language setting."""
        self.set("app.language", language)
    
    def get_daily_quota(self) -> int:
        """Get daily message quota."""
        return self.get("quotas.daily_limit", 100)
    
    def get_window_geometry(self) -> Dict[str, int]:
        """Get window geometry settings."""
        return {
            "width": self.get("ui.window_width", 1200),
            "height": self.get("ui.window_height", 800)
        }
    
    def set_window_geometry(self, width: int, height: int) -> None:
        """Set window geometry settings."""
        self.set("ui.window_width", width)
        self.set("ui.window_height", height)
    
    def get_email_batch_size(self) -> int:
        """Get email batch size."""
        return self.get("email.batch_size", 50)
    
    def should_include_signature(self) -> bool:
        """Check if email signature should be included."""
        return self.get("email.signature_include", True)
