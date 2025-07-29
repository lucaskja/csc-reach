#!/usr/bin/env python3
"""
Version Manager for CSC-Reach
Handles version bumping, tagging, and version-related operations
"""

import argparse
import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml


class VersionManager:
    """Manages version information and operations for CSC-Reach."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the version manager."""
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.pyproject_file = self.project_root / "pyproject.toml"
        self.setup_file = self.project_root / "setup.py"
        self.version_file = self.project_root / "VERSION"
        
    def get_current_version(self) -> str:
        """Get current version from pyproject.toml."""
        try:
            with open(self.pyproject_file, 'r') as f:
                content = f.read()
                
            # Extract version using regex
            version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if version_match:
                return version_match.group(1)
            else:
                return "1.0.0"
        except FileNotFoundError:
            return "1.0.0"
    
    def parse_version(self, version: str) -> Tuple[int, int, int, Optional[str]]:
        """Parse semantic version into components."""
        # Handle pre-release versions (e.g., 1.0.0-alpha.1)
        if '-' in version:
            base_version, prerelease = version.split('-', 1)
        else:
            base_version, prerelease = version, None
        
        try:
            parts = base_version.split('.')
            major = int(parts[0]) if len(parts) > 0 else 0
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            return major, minor, patch, prerelease
        except (ValueError, IndexError):
            return 1, 0, 0, None
    
    def increment_version(
        self, 
        version: str, 
        increment_type: str = "patch",
        prerelease: Optional[str] = None
    ) -> str:
        """Increment version number."""
        major, minor, patch, current_prerelease = self.parse_version(version)
        
        if increment_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif increment_type == "minor":
            minor += 1
            patch = 0
        elif increment_type == "patch":
            patch += 1
        elif increment_type == "prerelease":
            # Handle prerelease increment
            if current_prerelease:
                # Extract number from prerelease (e.g., alpha.1 -> alpha.2)
                match = re.search(r'(.+)\.(\d+)$', current_prerelease)
                if match:
                    pre_name, pre_num = match.groups()
                    prerelease = f"{pre_name}.{int(pre_num) + 1}"
                else:
                    prerelease = f"{current_prerelease}.1"
            else:
                prerelease = prerelease or "alpha.1"
        
        new_version = f"{major}.{minor}.{patch}"
        if prerelease:
            new_version += f"-{prerelease}"
        
        return new_version
    
    def update_version_in_file(self, file_path: Path, new_version: str) -> bool:
        """Update version in a specific file."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            if file_path.name == "pyproject.toml":
                # Update version in pyproject.toml
                updated_content = re.sub(
                    r'version\s*=\s*["\'][^"\']+["\']',
                    f'version = "{new_version}"',
                    content
                )
            elif file_path.name == "setup.py":
                # Update version in setup.py
                updated_content = re.sub(
                    r'version\s*=\s*["\'][^"\']+["\']',
                    f'version="{new_version}"',
                    content
                )
            else:
                # For other files, just replace the content
                updated_content = new_version
            
            with open(file_path, 'w') as f:
                f.write(updated_content)
            
            return True
        except Exception as e:
            print(f"❌ Failed to update {file_path}: {e}")
            return False
    
    def update_version(self, new_version: str) -> bool:
        """Update version in all relevant files."""
        success = True
        
        # Update pyproject.toml
        if self.pyproject_file.exists():
            if self.update_version_in_file(self.pyproject_file, new_version):
                print(f"✅ Updated version in {self.pyproject_file}")
            else:
                success = False
        
        # Update setup.py if it exists
        if self.setup_file.exists():
            if self.update_version_in_file(self.setup_file, new_version):
                print(f"✅ Updated version in {self.setup_file}")
            else:
                success = False
        
        # Create/update VERSION file
        if self.update_version_in_file(self.version_file, new_version):
            print(f"✅ Updated version in {self.version_file}")
        else:
            success = False
        
        return success
    
    def create_git_tag(self, version: str, message: Optional[str] = None) -> bool:
        """Create a git tag for the version."""
        try:
            tag_name = f"v{version}"
            tag_message = message or f"Release version {version}"
            
            # Create annotated tag
            result = subprocess.run([
                'git', 'tag', '-a', tag_name, '-m', tag_message
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Created git tag: {tag_name}")
                return True
            else:
                print(f"❌ Failed to create git tag: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to create git tag: {e}")
            return False
    
    def push_git_tag(self, version: str) -> bool:
        """Push git tag to remote repository."""
        try:
            tag_name = f"v{version}"
            
            result = subprocess.run([
                'git', 'push', 'origin', tag_name
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Pushed git tag: {tag_name}")
                return True
            else:
                print(f"❌ Failed to push git tag: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to push git tag: {e}")
            return False
    
    def get_git_tags(self) -> List[str]:
        """Get list of existing git tags."""
        try:
            result = subprocess.run([
                'git', 'tag', '-l'
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                tags = [tag.strip() for tag in result.stdout.split('\n') if tag.strip()]
                return tags
            else:
                return []
                
        except Exception:
            return []
    
    def get_latest_tag(self) -> Optional[str]:
        """Get the latest git tag."""
        try:
            result = subprocess.run([
                'git', 'describe', '--tags', '--abbrev=0'
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return None
                
        except Exception:
            return None
    
    def commit_version_changes(self, version: str) -> bool:
        """Commit version changes to git."""
        try:
            # Add changed files
            files_to_add = []
            if self.pyproject_file.exists():
                files_to_add.append(str(self.pyproject_file))
            if self.setup_file.exists():
                files_to_add.append(str(self.setup_file))
            if self.version_file.exists():
                files_to_add.append(str(self.version_file))
            
            if files_to_add:
                subprocess.run([
                    'git', 'add'
                ] + files_to_add, cwd=self.project_root, check=True)
                
                # Commit changes
                commit_message = f"Bump version to {version}"
                subprocess.run([
                    'git', 'commit', '-m', commit_message
                ], cwd=self.project_root, check=True)
                
                print(f"✅ Committed version changes: {commit_message}")
                return True
            else:
                print("⚠️ No version files to commit")
                return True
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to commit version changes: {e}")
            return False
        except Exception as e:
            print(f"❌ Failed to commit version changes: {e}")
            return False
    
    def get_version_info(self) -> Dict:
        """Get comprehensive version information."""
        current_version = self.get_current_version()
        major, minor, patch, prerelease = self.parse_version(current_version)
        latest_tag = self.get_latest_tag()
        
        info = {
            'current_version': current_version,
            'major': major,
            'minor': minor,
            'patch': patch,
            'prerelease': prerelease,
            'latest_tag': latest_tag,
            'is_prerelease': prerelease is not None,
            'next_versions': {
                'patch': self.increment_version(current_version, 'patch'),
                'minor': self.increment_version(current_version, 'minor'),
                'major': self.increment_version(current_version, 'major'),
                'prerelease': self.increment_version(current_version, 'prerelease', 'alpha')
            }
        }
        
        return info
    
    def release_version(
        self, 
        increment_type: str = "patch",
        prerelease: Optional[str] = None,
        commit: bool = True,
        tag: bool = True,
        push: bool = False,
        dry_run: bool = False
    ) -> Optional[str]:
        """Perform a complete version release."""
        current_version = self.get_current_version()
        new_version = self.increment_version(current_version, increment_type, prerelease)
        
        print(f"🚀 Releasing version {current_version} -> {new_version}")
        
        if dry_run:
            print(f"[DRY RUN] Would perform the following actions:")
            print(f"  - Update version files to {new_version}")
            if commit:
                print(f"  - Commit version changes")
            if tag:
                print(f"  - Create git tag v{new_version}")
            if push:
                print(f"  - Push git tag to remote")
            return new_version
        
        # Update version files
        if not self.update_version(new_version):
            print("❌ Failed to update version files")
            return None
        
        # Commit changes
        if commit:
            if not self.commit_version_changes(new_version):
                print("❌ Failed to commit version changes")
                return None
        
        # Create git tag
        if tag:
            if not self.create_git_tag(new_version):
                print("❌ Failed to create git tag")
                return None
        
        # Push tag
        if push:
            if not self.push_git_tag(new_version):
                print("❌ Failed to push git tag")
                return None
        
        print(f"✅ Successfully released version {new_version}")
        return new_version


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="CSC-Reach Version Manager")
    parser.add_argument("--current", action="store_true", help="Show current version")
    parser.add_argument("--info", action="store_true", help="Show version information")
    parser.add_argument("--bump", choices=["major", "minor", "patch", "prerelease"],
                       help="Bump version")
    parser.add_argument("--prerelease", help="Prerelease identifier (e.g., alpha, beta)")
    parser.add_argument("--set", help="Set specific version")
    parser.add_argument("--release", action="store_true", help="Perform full release")
    parser.add_argument("--no-commit", action="store_true", help="Don't commit changes")
    parser.add_argument("--no-tag", action="store_true", help="Don't create git tag")
    parser.add_argument("--push", action="store_true", help="Push git tag to remote")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    
    args = parser.parse_args()
    
    # Initialize version manager
    version_manager = VersionManager()
    
    # Show current version
    if args.current:
        print(version_manager.get_current_version())
        return 0
    
    # Show version information
    if args.info:
        info = version_manager.get_version_info()
        print("📊 Version Information:")
        print(f"   Current: {info['current_version']}")
        print(f"   Latest Tag: {info['latest_tag'] or 'None'}")
        print(f"   Is Prerelease: {info['is_prerelease']}")
        print("   Next Versions:")
        for bump_type, next_version in info['next_versions'].items():
            print(f"     {bump_type}: {next_version}")
        return 0
    
    # Set specific version
    if args.set:
        if version_manager.update_version(args.set):
            print(f"✅ Version set to {args.set}")
            return 0
        else:
            print(f"❌ Failed to set version to {args.set}")
            return 1
    
    # Bump version
    if args.bump:
        if args.release:
            # Perform full release
            new_version = version_manager.release_version(
                increment_type=args.bump,
                prerelease=args.prerelease,
                commit=not args.no_commit,
                tag=not args.no_tag,
                push=args.push,
                dry_run=args.dry_run
            )
            if new_version:
                return 0
            else:
                return 1
        else:
            # Just bump version
            current_version = version_manager.get_current_version()
            new_version = version_manager.increment_version(
                current_version, args.bump, args.prerelease
            )
            
            if args.dry_run:
                print(f"[DRY RUN] Would bump version: {current_version} -> {new_version}")
                return 0
            
            if version_manager.update_version(new_version):
                print(f"✅ Version bumped: {current_version} -> {new_version}")
                return 0
            else:
                print(f"❌ Failed to bump version")
                return 1
    
    # Default: show help
    parser.print_help()
    return 0


if __name__ == "__main__":
    exit(main())