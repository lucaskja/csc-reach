#!/usr/bin/env python3
"""
Release Manager for CSC-Reach
Handles automated release creation, versioning, and distribution
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import yaml

from .release_components import (
    VersionManager, 
    GitInfoProvider, 
    ReleaseNotesGenerator, 
    AssetValidator,
    ReleaseManifestBuilder
)
from .release_strategies import ReleaseStrategyFactory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CachedReleaseManager:
    """Release manager with caching for expensive operations."""
    
    def __init__(self, release_manager: 'ReleaseManager'):
        self._release_manager = release_manager
        self._cache = {}
    
    def get_current_version(self) -> str:
        """Get current version with caching."""
        if 'current_version' not in self._cache:
            self._cache['current_version'] = self._release_manager.get_current_version()
        return self._cache['current_version']
    
    def invalidate_cache(self):
        """Invalidate all cached values."""
        self._cache.clear()
    
    def __getattr__(self, name):
        """Delegate all other attributes to the wrapped release manager."""
        return getattr(self._release_manager, name)


class ReleaseManager:
    """Manages automated releases and distribution for CSC-Reach."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the release manager with dependency injection."""
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.config_file = self.project_root / "scripts" / "build" / "build_config.yaml"
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize components with dependency injection
        self.version_manager = VersionManager(self.project_root / "pyproject.toml")
        self.git_provider = GitInfoProvider(self.project_root)
        self.notes_generator = ReleaseNotesGenerator(self.git_provider)
        self.asset_validator = AssetValidator(self.config)
        self.manifest_builder = ReleaseManifestBuilder()
        
    def _load_config(self) -> Dict:
        """Load build configuration."""
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict:
        """Create default configuration."""
        config = {
            'release': {
                'types': ['development', 'staging', 'production'],
                'channels': {
                    'development': {
                        'prerelease': True,
                        'draft': True,
                        'auto_publish': False
                    },
                    'staging': {
                        'prerelease': True,
                        'draft': False,
                        'auto_publish': True
                    },
                    'production': {
                        'prerelease': False,
                        'draft': False,
                        'auto_publish': True
                    }
                },
                'assets': {
                    'windows': {
                        'patterns': ['*Windows*.zip', '*Windows*.exe'],
                        'required': True
                    },
                    'macos': {
                        'patterns': ['*macOS*.dmg', '*macOS*.app'],
                        'required': True
                    }
                }
            },
            'versioning': {
                'scheme': 'semantic',  # semantic, date, build
                'auto_increment': True,
                'tag_prefix': 'v'
            }
        }
        
        # Save default config
        os.makedirs(self.config_file.parent, exist_ok=True)
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
            
        return config
    
    def get_current_version(self) -> str:
        """Get current version from pyproject.toml."""
        return self.version_manager.get_current_version()
    
    def increment_version(self, version: str, increment_type: str = "patch") -> str:
        """Increment version number."""
        return self.version_manager.increment_version(version, increment_type)
    
    def update_version(self, new_version: str) -> bool:
        """Update version in pyproject.toml."""
        success = self.version_manager.update_version(new_version)
        if success:
            logger.info(f"Updated version to {new_version}")
        else:
            logger.error(f"Failed to update version to {new_version}")
        return success
    
    def generate_release_notes(self, version: str, release_type: str = "production") -> str:
        """Generate release notes for the version."""
        return self.notes_generator.generate(version, release_type)
    
    def create_release_manifest(self, version: str, release_type: str, assets: List[Path]) -> Dict:
        """Create release manifest with metadata."""
        build_info = self.git_provider.get_build_info()
        
        manifest = (self.manifest_builder
                   .with_version(version)
                   .with_release_type(release_type)
                   .with_build_info(build_info)
                   .with_timestamp())
        
        # Add all assets
        for asset in assets:
            manifest.add_asset(asset)
        
        return manifest.build()
    
    def validate_assets(self, assets_dir: Path) -> Tuple[bool, List[str]]:
        """Validate that required assets are present."""
        return self.asset_validator.validate_assets(assets_dir)
    
    def create_staged_release(
        self, 
        version: str, 
        release_type: str, 
        assets_dir: Path,
        dry_run: bool = False
    ) -> bool:
        """Create a staged release."""
        try:
            logger.info(f"Creating {release_type} release for version {version}")
            
            # Get release strategy
            strategy = ReleaseStrategyFactory.create_strategy(release_type)
            config = strategy.get_config()
            
            # Validate assets
            valid, errors = self.validate_assets(assets_dir)
            if not valid:
                logger.error("Asset validation failed:")
                for error in errors:
                    logger.error(f"   - {error}")
                return False
            
            # Generate release notes
            release_notes = self.generate_release_notes(version, release_type)
            
            # Create release manifest
            assets = list(assets_dir.glob("*"))
            manifest = self.create_release_manifest(version, release_type, assets)
            
            # Save manifest
            manifest_file = assets_dir / "release-manifest.json"
            self._save_json_file(manifest_file, manifest)
            
            # Save release notes
            notes_file = assets_dir / "release-notes.md"
            self._save_text_file(notes_file, release_notes)
            
            if dry_run:
                logger.info("Dry run - would create release with:")
                logger.info(f"   Version: {version}")
                logger.info(f"   Type: {release_type}")
                logger.info(f"   Assets: {len(assets)} files")
                logger.info(f"   Manifest: {manifest_file}")
                logger.info(f"   Notes: {notes_file}")
                return True
            
            logger.info("Release preparation completed")
            logger.info(f"   Manifest: {manifest_file}")
            logger.info(f"   Notes: {notes_file}")
            logger.info(f"   Assets: {len(assets)} files")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create staged release: {e}")
            return False
    
    def _save_json_file(self, file_path: Path, data: Dict) -> None:
        """Safely save JSON data to file."""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save JSON file {file_path}: {e}")
            raise
    
    def _save_text_file(self, file_path: Path, content: str) -> None:
        """Safely save text content to file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Failed to save text file {file_path}: {e}")
            raise
    
    def bump_version(self, increment_type: str = "patch") -> str:
        """Bump version and return new version."""
        current_version = self.get_current_version()
        new_version = self.increment_version(current_version, increment_type)
        
        if self.update_version(new_version):
            return new_version
        else:
            return current_version


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="CSC-Reach Release Manager")
    parser.add_argument("--version", help="Version to release")
    parser.add_argument("--release-type", choices=["development", "staging", "production"], 
                       default="development", help="Release type")
    parser.add_argument("--assets-dir", type=Path, help="Directory containing release assets")
    parser.add_argument("--bump", choices=["major", "minor", "patch"], 
                       help="Bump version before release")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--current-version", action="store_true", 
                       help="Show current version and exit")
    
    args = parser.parse_args()
    
    # Initialize release manager
    release_manager = ReleaseManager()
    
    # Show current version if requested
    if args.current_version:
        print(release_manager.get_current_version())
        return
    
    # Bump version if requested
    if args.bump:
        new_version = release_manager.bump_version(args.bump)
        print(f"Version bumped to: {new_version}")
        if not args.version:
            args.version = new_version
    
    # Use current version if not specified
    if not args.version:
        args.version = release_manager.get_current_version()
    
    # Default assets directory
    if not args.assets_dir:
        args.assets_dir = Path("./release-assets")
    
    # Create staged release
    success = release_manager.create_staged_release(
        args.version,
        args.release_type,
        args.assets_dir,
        args.dry_run
    )
    
    if success:
        print(f"🎉 Release {args.version} prepared successfully!")
        sys.exit(0)
    else:
        print(f"❌ Failed to prepare release {args.version}")
        sys.exit(1)


if __name__ == "__main__":
    main()