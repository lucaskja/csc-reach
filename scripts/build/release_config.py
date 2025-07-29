#!/usr/bin/env python3
"""
Configuration management for release system with validation.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import yaml
from cerberus import Validator


@dataclass
class AssetConfig:
    """Configuration for release assets."""
    patterns: List[str]
    required: bool = True


@dataclass
class ChannelConfig:
    """Configuration for release channels."""
    prerelease: bool
    draft: bool
    auto_publish: bool


@dataclass
class ReleaseConfig:
    """Main release configuration."""
    types: List[str] = field(default_factory=lambda: ['development', 'staging', 'production'])
    channels: Dict[str, ChannelConfig] = field(default_factory=dict)
    assets: Dict[str, AssetConfig] = field(default_factory=dict)


@dataclass
class VersioningConfig:
    """Versioning configuration."""
    scheme: str = 'semantic'
    auto_increment: bool = True
    tag_prefix: str = 'v'


@dataclass
class BuildConfig:
    """Complete build configuration."""
    release: ReleaseConfig = field(default_factory=ReleaseConfig)
    versioning: VersioningConfig = field(default_factory=VersioningConfig)


class ConfigManager:
    """Manages configuration with validation."""
    
    SCHEMA = {
        'release': {
            'type': 'dict',
            'schema': {
                'types': {'type': 'list', 'schema': {'type': 'string'}},
                'channels': {
                    'type': 'dict',
                    'valueschema': {
                        'type': 'dict',
                        'schema': {
                            'prerelease': {'type': 'boolean'},
                            'draft': {'type': 'boolean'},
                            'auto_publish': {'type': 'boolean'}
                        }
                    }
                },
                'assets': {
                    'type': 'dict',
                    'valueschema': {
                        'type': 'dict',
                        'schema': {
                            'patterns': {'type': 'list', 'schema': {'type': 'string'}},
                            'required': {'type': 'boolean'}
                        }
                    }
                }
            }
        },
        'versioning': {
            'type': 'dict',
            'schema': {
                'scheme': {'type': 'string', 'allowed': ['semantic', 'date', 'build']},
                'auto_increment': {'type': 'boolean'},
                'tag_prefix': {'type': 'string'}
            }
        }
    }
    
    def __init__(self, config_file: Path):
        self.config_file = config_file
        self.validator = Validator(self.SCHEMA)
    
    def load_config(self) -> BuildConfig:
        """Load and validate configuration."""
        try:
            with open(self.config_file, 'r') as f:
                raw_config = yaml.safe_load(f)
            
            if not self.validator.validate(raw_config):
                raise ValueError(f"Invalid configuration: {self.validator.errors}")
            
            return self._parse_config(raw_config)
            
        except FileNotFoundError:
            return self._create_default_config()
    
    def _parse_config(self, raw_config: Dict) -> BuildConfig:
        """Parse raw configuration into typed objects."""
        # Parse release config
        release_data = raw_config.get('release', {})
        
        channels = {}
        for name, channel_data in release_data.get('channels', {}).items():
            channels[name] = ChannelConfig(**channel_data)
        
        assets = {}
        for name, asset_data in release_data.get('assets', {}).items():
            assets[name] = AssetConfig(**asset_data)
        
        release_config = ReleaseConfig(
            types=release_data.get('types', ['development', 'staging', 'production']),
            channels=channels,
            assets=assets
        )
        
        # Parse versioning config
        versioning_data = raw_config.get('versioning', {})
        versioning_config = VersioningConfig(**versioning_data)
        
        return BuildConfig(release=release_config, versioning=versioning_config)
    
    def _create_default_config(self) -> BuildConfig:
        """Create default configuration."""
        default_config = BuildConfig(
            release=ReleaseConfig(
                channels={
                    'development': ChannelConfig(prerelease=True, draft=True, auto_publish=False),
                    'staging': ChannelConfig(prerelease=True, draft=False, auto_publish=True),
                    'production': ChannelConfig(prerelease=False, draft=False, auto_publish=True)
                },
                assets={
                    'windows': AssetConfig(patterns=['*Windows*.zip', '*Windows*.exe'], required=True),
                    'macos': AssetConfig(patterns=['*macOS*.dmg', '*macOS*.app'], required=True)
                }
            )
        )
        
        # Save default config
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config: BuildConfig) -> None:
        """Save configuration to file."""
        # Convert to dict for YAML serialization
        config_dict = {
            'release': {
                'types': config.release.types,
                'channels': {
                    name: {
                        'prerelease': channel.prerelease,
                        'draft': channel.draft,
                        'auto_publish': channel.auto_publish
                    }
                    for name, channel in config.release.channels.items()
                },
                'assets': {
                    name: {
                        'patterns': asset.patterns,
                        'required': asset.required
                    }
                    for name, asset in config.release.assets.items()
                }
            },
            'versioning': {
                'scheme': config.versioning.scheme,
                'auto_increment': config.versioning.auto_increment,
                'tag_prefix': config.versioning.tag_prefix
            }
        }
        
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False)