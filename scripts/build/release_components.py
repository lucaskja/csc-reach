#!/usr/bin/env python3
"""
Release Management Components
Separated concerns for better maintainability
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import re
from datetime import datetime


class VersionManager:
    """Handles version operations and semantic versioning."""
    
    def __init__(self, version_file: Path):
        self.version_file = version_file
    
    def get_current_version(self) -> str:
        """Get current version from pyproject.toml."""
        try:
            with open(self.version_file, 'r') as f:
                content = f.read()
                
            version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            return version_match.group(1) if version_match else "1.0.0"
        except FileNotFoundError:
            return "1.0.0"
    
    def increment_version(self, version: str, increment_type: str = "patch") -> str:
        """Increment version number using semantic versioning."""
        try:
            parts = version.split('.')
            major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
            
            if increment_type == "major":
                return f"{major + 1}.0.0"
            elif increment_type == "minor":
                return f"{major}.{minor + 1}.0"
            elif increment_type == "patch":
                return f"{major}.{minor}.{patch + 1}"
            
            return version
        except (ValueError, IndexError):
            return datetime.now().strftime("%Y.%m.%d")
    
    def update_version(self, new_version: str) -> bool:
        """Update version in pyproject.toml."""
        try:
            with open(self.version_file, 'r') as f:
                content = f.read()
            
            updated_content = re.sub(
                r'version\s*=\s*["\'][^"\']+["\']',
                f'version = "{new_version}"',
                content
            )
            
            with open(self.version_file, 'w') as f:
                f.write(updated_content)
            
            return True
        except Exception:
            return False


class GitInfoProvider:
    """Provides git-related information for releases."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
    
    def get_recent_changes(self, since: str = "1 week ago") -> List[str]:
        """Get recent git changes for release notes."""
        try:
            result = subprocess.run(
                ['git', 'log', '--oneline', f'--since="{since}"'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                return [line.split(' ', 1)[1] for line in lines if line.strip()]
            
        except Exception:
            pass
        
        return []
    
    def get_build_info(self) -> Dict[str, str]:
        """Get comprehensive build information."""
        info = {
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            'commit': self._get_commit_hash(),
            'branch': self._get_branch_name(),
            'workflow': self._get_workflow_id()
        }
        return info
    
    def _get_commit_hash(self) -> str:
        """Get current commit hash."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            return result.stdout.strip()[:8] if result.returncode == 0 else 'unknown'
        except Exception:
            return 'unknown'
    
    def _get_branch_name(self) -> str:
        """Get current branch name."""
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            return result.stdout.strip() if result.returncode == 0 else 'unknown'
        except Exception:
            return 'unknown'
    
    def _get_workflow_id(self) -> str:
        """Get GitHub workflow ID from environment."""
        import os
        return os.environ.get('GITHUB_RUN_ID', 'N/A')


class ReleaseNotesGenerator:
    """Generates release notes from templates and data."""
    
    def __init__(self, git_provider: GitInfoProvider):
        self.git_provider = git_provider
    
    def generate(self, version: str, release_type: str = "production") -> str:
        """Generate comprehensive release notes."""
        template_data = {
            'version': version,
            'release_type': release_type,
            'changes': self.git_provider.get_recent_changes(),
            'build_info': self.git_provider.get_build_info()
        }
        
        return self._render_template(template_data)
    
    def _render_template(self, data: Dict) -> str:
        """Render release notes template."""
        notes = f"""# CSC-Reach {data['version']}

## 🚀 What's New

This {data['release_type']} release includes the latest improvements and bug fixes for CSC-Reach.

"""
        
        # Add changes section
        if data['changes']:
            notes += "## 📝 Changes\n\n"
            for change in data['changes']:
                notes += f"- {change}\n"
            notes += "\n"
        
        # Add standard sections
        notes += self._get_download_section()
        notes += self._get_system_requirements_section()
        notes += self._get_installation_section()
        notes += self._get_support_section()
        notes += self._get_build_info_section(data['build_info'], data['release_type'])
        
        return notes
    
    def _get_download_section(self) -> str:
        """Get download instructions section."""
        return """## 📦 Downloads

- **Windows**: Download `CSC-Reach-Windows.zip` and extract to your desired location
- **macOS**: Download `CSC-Reach-macOS.dmg` and drag the app to your Applications folder

"""
    
    def _get_system_requirements_section(self) -> str:
        """Get system requirements section."""
        return """## 🔧 System Requirements

### Windows
- Windows 10 or later (64-bit)
- Microsoft Outlook installed and configured
- 4GB RAM minimum, 8GB recommended

### macOS
- macOS 10.14 (Mojave) or later
- Microsoft Outlook for Mac installed and configured
- 4GB RAM minimum, 8GB recommended

"""
    
    def _get_installation_section(self) -> str:
        """Get installation instructions section."""
        return """## 📋 Installation Instructions

Detailed installation guides are available in the repository documentation.

"""
    
    def _get_support_section(self) -> str:
        """Get support section."""
        return """## 🐛 Bug Reports

If you encounter any issues, please report them in the GitHub Issues section.

---

"""
    
    def _get_build_info_section(self, build_info: Dict, release_type: str) -> str:
        """Get build information section."""
        return f"""**Build Information:**
- Build Date: {build_info['date']}
- Commit: {build_info['commit']}
- Branch: {build_info['branch']}
- Release Type: {release_type}
- Workflow: {build_info['workflow']}
"""


class AssetValidator:
    """Validates release assets against configuration."""
    
    def __init__(self, config: Dict):
        self.config = config
    
    def validate_assets(self, assets_dir: Path) -> tuple[bool, List[str]]:
        """Validate that required assets are present."""
        errors = []
        asset_config = self.config.get('release', {}).get('assets', {})
        
        for platform, config in asset_config.items():
            if not config.get('required', False):
                continue
                
            patterns = config.get('patterns', [])
            if not self._check_patterns_exist(assets_dir, patterns):
                errors.append(f"Missing required {platform} assets (patterns: {patterns})")
        
        return len(errors) == 0, errors
    
    def _check_patterns_exist(self, assets_dir: Path, patterns: List[str]) -> bool:
        """Check if any of the patterns match existing files."""
        for pattern in patterns:
            if list(assets_dir.glob(pattern)):
                return True
        return False


class ReleaseManifestBuilder:
    """Builder for creating release manifests."""
    
    def __init__(self):
        self._manifest = {}
        self._assets = []
    
    def with_version(self, version: str) -> 'ReleaseManifestBuilder':
        """Set release version."""
        self._manifest['version'] = version
        return self
    
    def with_release_type(self, release_type: str) -> 'ReleaseManifestBuilder':
        """Set release type."""
        self._manifest['release_type'] = release_type
        return self
    
    def with_build_info(self, build_info: Dict) -> 'ReleaseManifestBuilder':
        """Set build information."""
        self._manifest['build_info'] = build_info
        return self
    
    def with_timestamp(self, timestamp: Optional[str] = None) -> 'ReleaseManifestBuilder':
        """Set creation timestamp."""
        self._manifest['created_at'] = timestamp or datetime.now().isoformat()
        return self
    
    def add_asset(self, asset_path: Path) -> 'ReleaseManifestBuilder':
        """Add an asset to the manifest."""
        if asset_path.exists():
            asset_info = {
                'name': asset_path.name,
                'path': str(asset_path),
                'size': asset_path.stat().st_size,
                'platform': self._detect_platform(asset_path.name),
                'type': self._detect_asset_type(asset_path.name),
                'checksum': self._calculate_checksum(asset_path)
            }
            self._assets.append(asset_info)
        return self
    
    def add_assets_from_directory(self, assets_dir: Path) -> 'ReleaseManifestBuilder':
        """Add all assets from a directory."""
        for asset_path in assets_dir.glob("*"):
            if asset_path.is_file():
                self.add_asset(asset_path)
        return self
    
    def build(self) -> Dict:
        """Build the final manifest."""
        self._manifest['assets'] = self._assets
        self._manifest['asset_count'] = len(self._assets)
        self._manifest['total_size'] = sum(asset['size'] for asset in self._assets)
        return self._manifest.copy()
    
    def _detect_platform(self, filename: str) -> str:
        """Detect platform from filename."""
        filename_lower = filename.lower()
        if 'windows' in filename_lower or '.exe' in filename_lower:
            return 'windows'
        elif 'macos' in filename_lower or '.dmg' in filename_lower or '.app' in filename_lower:
            return 'macos'
        elif 'linux' in filename_lower:
            return 'linux'
        else:
            return 'unknown'
    
    def _detect_asset_type(self, filename: str) -> str:
        """Detect asset type from filename."""
        filename_lower = filename.lower()
        if '.zip' in filename_lower:
            return 'archive'
        elif '.dmg' in filename_lower:
            return 'installer'
        elif '.exe' in filename_lower:
            return 'executable'
        elif '.app' in filename_lower:
            return 'application'
        else:
            return 'unknown'
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file."""
        import hashlib
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()