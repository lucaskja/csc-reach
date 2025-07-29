#!/usr/bin/env python3
"""
Distribution Manager for CSC-Reach
Manages distribution channels and deployment stages
"""

import argparse
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml


class DistributionManager:
    """Manages distribution channels and staged deployments."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the distribution manager."""
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.config_file = self.project_root / "scripts" / "build" / "distribution_config.yaml"
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load distribution configuration."""
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict:
        """Create default distribution configuration."""
        config = {
            'channels': {
                'development': {
                    'description': 'Development builds for testing',
                    'auto_deploy': True,
                    'retention_days': 7,
                    'destinations': [
                        {
                            'type': 'github_releases',
                            'prerelease': True,
                            'draft': True
                        },
                        {
                            'type': 'local_storage',
                            'path': 'build/dist/development'
                        }
                    ]
                },
                'staging': {
                    'description': 'Staging builds for pre-production testing',
                    'auto_deploy': True,
                    'retention_days': 30,
                    'destinations': [
                        {
                            'type': 'github_releases',
                            'prerelease': True,
                            'draft': False
                        },
                        {
                            'type': 'local_storage',
                            'path': 'build/dist/staging'
                        }
                    ]
                },
                'production': {
                    'description': 'Production releases',
                    'auto_deploy': False,
                    'retention_days': 365,
                    'destinations': [
                        {
                            'type': 'github_releases',
                            'prerelease': False,
                            'draft': False
                        },
                        {
                            'type': 'local_storage',
                            'path': 'build/dist/production'
                        }
                    ]
                }
            },
            'assets': {
                'required_patterns': [
                    '*Windows*.zip',
                    '*macOS*.dmg'
                ],
                'optional_patterns': [
                    '*Windows*.exe',
                    '*macOS*.app',
                    'release-manifest.json',
                    'release-notes.md'
                ]
            },
            'notifications': {
                'enabled': True,
                'channels': ['console', 'file'],
                'webhook_url': None
            }
        }
        
        # Save default config
        os.makedirs(self.config_file.parent, exist_ok=True)
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
            
        return config
    
    def validate_assets(self, assets_dir: Path) -> Dict[str, List[str]]:
        """Validate assets for distribution."""
        result = {
            'required': [],
            'optional': [],
            'missing_required': [],
            'missing_optional': []
        }
        
        # Check required assets
        required_patterns = self.config.get('assets', {}).get('required_patterns', [])
        for pattern in required_patterns:
            matching_files = list(assets_dir.glob(pattern))
            if matching_files:
                result['required'].extend([f.name for f in matching_files])
            else:
                result['missing_required'].append(pattern)
        
        # Check optional assets
        optional_patterns = self.config.get('assets', {}).get('optional_patterns', [])
        for pattern in optional_patterns:
            matching_files = list(assets_dir.glob(pattern))
            if matching_files:
                result['optional'].extend([f.name for f in matching_files])
            else:
                result['missing_optional'].append(pattern)
        
        return result
    
    def prepare_distribution(
        self, 
        channel: str, 
        version: str, 
        assets_dir: Path,
        dry_run: bool = False
    ) -> bool:
        """Prepare assets for distribution to a specific channel."""
        if channel not in self.config['channels']:
            print(f"❌ Unknown distribution channel: {channel}")
            return False
        
        channel_config = self.config['channels'][channel]
        print(f"📦 Preparing distribution for {channel} channel")
        print(f"   Description: {channel_config['description']}")
        
        # Validate assets
        validation_result = self.validate_assets(assets_dir)
        
        if validation_result['missing_required']:
            print("❌ Missing required assets:")
            for missing in validation_result['missing_required']:
                print(f"   - {missing}")
            return False
        
        print(f"✅ Found {len(validation_result['required'])} required assets")
        if validation_result['optional']:
            print(f"✅ Found {len(validation_result['optional'])} optional assets")
        
        if validation_result['missing_optional']:
            print(f"⚠️  Missing {len(validation_result['missing_optional'])} optional assets")
        
        # Process each destination
        success = True
        for destination in channel_config['destinations']:
            dest_success = self._process_destination(
                destination, channel, version, assets_dir, dry_run
            )
            success = success and dest_success
        
        return success
    
    def _process_destination(
        self, 
        destination: Dict, 
        channel: str, 
        version: str, 
        assets_dir: Path,
        dry_run: bool
    ) -> bool:
        """Process a single distribution destination."""
        dest_type = destination['type']
        
        if dest_type == 'local_storage':
            return self._deploy_to_local_storage(destination, channel, version, assets_dir, dry_run)
        elif dest_type == 'github_releases':
            return self._deploy_to_github_releases(destination, channel, version, assets_dir, dry_run)
        elif dest_type == 's3':
            return self._deploy_to_s3(destination, channel, version, assets_dir, dry_run)
        else:
            print(f"⚠️  Unknown destination type: {dest_type}")
            return True  # Don't fail for unknown types
    
    def _deploy_to_local_storage(
        self, 
        destination: Dict, 
        channel: str, 
        version: str, 
        assets_dir: Path,
        dry_run: bool
    ) -> bool:
        """Deploy to local storage."""
        storage_path = Path(destination['path'])
        version_dir = storage_path / version
        
        print(f"📁 Deploying to local storage: {version_dir}")
        
        if dry_run:
            print(f"   [DRY RUN] Would copy assets to {version_dir}")
            return True
        
        try:
            # Create version directory
            version_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy all assets
            for asset_file in assets_dir.iterdir():
                if asset_file.is_file():
                    dest_file = version_dir / asset_file.name
                    shutil.copy2(asset_file, dest_file)
                    print(f"   ✅ Copied {asset_file.name}")
            
            # Create deployment manifest
            manifest = {
                'channel': channel,
                'version': version,
                'deployed_at': datetime.now().isoformat(),
                'assets': [f.name for f in version_dir.iterdir() if f.is_file()]
            }
            
            manifest_file = version_dir / 'deployment-manifest.json'
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            print(f"   ✅ Created deployment manifest")
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to deploy to local storage: {e}")
            return False
    
    def _deploy_to_github_releases(
        self, 
        destination: Dict, 
        channel: str, 
        version: str, 
        assets_dir: Path,
        dry_run: bool
    ) -> bool:
        """Deploy to GitHub Releases."""
        print(f"🐙 Preparing for GitHub Releases deployment")
        
        # This is handled by the GitHub Actions workflow
        # We just prepare the metadata here
        
        release_config = {
            'tag_name': f"v{version}",
            'name': f"CSC-Reach {version}",
            'prerelease': destination.get('prerelease', False),
            'draft': destination.get('draft', False),
            'channel': channel
        }
        
        config_file = assets_dir / 'github-release-config.json'
        
        if dry_run:
            print(f"   [DRY RUN] Would create GitHub release config: {config_file}")
            print(f"   Config: {json.dumps(release_config, indent=2)}")
            return True
        
        try:
            with open(config_file, 'w') as f:
                json.dump(release_config, f, indent=2)
            
            print(f"   ✅ Created GitHub release configuration")
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to create GitHub release config: {e}")
            return False
    
    def _deploy_to_s3(
        self, 
        destination: Dict, 
        channel: str, 
        version: str, 
        assets_dir: Path,
        dry_run: bool
    ) -> bool:
        """Deploy to AWS S3."""
        bucket = destination.get('bucket')
        prefix = destination.get('prefix', f'releases/{channel}/{version}')
        
        print(f"☁️  Deploying to S3: s3://{bucket}/{prefix}")
        
        if not bucket:
            print("   ❌ S3 bucket not configured")
            return False
        
        if dry_run:
            print(f"   [DRY RUN] Would upload assets to s3://{bucket}/{prefix}")
            return True
        
        try:
            # Use AWS CLI if available
            for asset_file in assets_dir.iterdir():
                if asset_file.is_file():
                    s3_key = f"{prefix}/{asset_file.name}"
                    cmd = [
                        'aws', 's3', 'cp',
                        str(asset_file),
                        f"s3://{bucket}/{s3_key}"
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"   ✅ Uploaded {asset_file.name}")
                    else:
                        print(f"   ❌ Failed to upload {asset_file.name}: {result.stderr}")
                        return False
            
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to deploy to S3: {e}")
            return False
    
    def cleanup_old_releases(self, channel: str, dry_run: bool = False) -> bool:
        """Clean up old releases based on retention policy."""
        if channel not in self.config['channels']:
            print(f"❌ Unknown channel: {channel}")
            return False
        
        channel_config = self.config['channels'][channel]
        retention_days = channel_config.get('retention_days', 30)
        
        print(f"🧹 Cleaning up {channel} releases older than {retention_days} days")
        
        # Only handle local storage cleanup for now
        for destination in channel_config['destinations']:
            if destination['type'] == 'local_storage':
                storage_path = Path(destination['path'])
                if storage_path.exists():
                    self._cleanup_local_storage(storage_path, retention_days, dry_run)
        
        return True
    
    def _cleanup_local_storage(self, storage_path: Path, retention_days: int, dry_run: bool):
        """Clean up old releases from local storage."""
        cutoff_date = datetime.now().timestamp() - (retention_days * 24 * 60 * 60)
        
        for version_dir in storage_path.iterdir():
            if version_dir.is_dir():
                # Check if directory is older than retention period
                if version_dir.stat().st_mtime < cutoff_date:
                    if dry_run:
                        print(f"   [DRY RUN] Would remove {version_dir}")
                    else:
                        try:
                            shutil.rmtree(version_dir)
                            print(f"   🗑️  Removed {version_dir}")
                        except Exception as e:
                            print(f"   ❌ Failed to remove {version_dir}: {e}")
    
    def list_channels(self) -> Dict[str, Dict]:
        """List available distribution channels."""
        return self.config['channels']
    
    def get_channel_status(self, channel: str) -> Optional[Dict]:
        """Get status information for a channel."""
        if channel not in self.config['channels']:
            return None
        
        channel_config = self.config['channels'][channel]
        status = {
            'channel': channel,
            'description': channel_config['description'],
            'auto_deploy': channel_config['auto_deploy'],
            'retention_days': channel_config['retention_days'],
            'destinations': len(channel_config['destinations']),
            'releases': []
        }
        
        # Count releases in local storage destinations
        for destination in channel_config['destinations']:
            if destination['type'] == 'local_storage':
                storage_path = Path(destination['path'])
                if storage_path.exists():
                    releases = [d.name for d in storage_path.iterdir() if d.is_dir()]
                    status['releases'].extend(releases)
        
        return status


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="CSC-Reach Distribution Manager")
    parser.add_argument("--channel", choices=["development", "staging", "production"],
                       required=True, help="Distribution channel")
    parser.add_argument("--version", help="Version to distribute")
    parser.add_argument("--assets-dir", type=Path, help="Directory containing assets")
    parser.add_argument("--action", choices=["deploy", "cleanup", "status", "list"],
                       default="deploy", help="Action to perform")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    
    args = parser.parse_args()
    
    # Initialize distribution manager
    dist_manager = DistributionManager()
    
    if args.action == "list":
        print("📋 Available distribution channels:")
        channels = dist_manager.list_channels()
        for name, config in channels.items():
            print(f"   {name}: {config['description']}")
        return 0
    
    if args.action == "status":
        status = dist_manager.get_channel_status(args.channel)
        if status:
            print(f"📊 Channel Status: {args.channel}")
            print(f"   Description: {status['description']}")
            print(f"   Auto Deploy: {status['auto_deploy']}")
            print(f"   Retention: {status['retention_days']} days")
            print(f"   Destinations: {status['destinations']}")
            print(f"   Releases: {len(status['releases'])}")
            if status['releases']:
                for release in sorted(status['releases'])[-5:]:  # Show last 5
                    print(f"     - {release}")
        else:
            print(f"❌ Channel not found: {args.channel}")
            return 1
        return 0
    
    if args.action == "cleanup":
        success = dist_manager.cleanup_old_releases(args.channel, args.dry_run)
        return 0 if success else 1
    
    # Deploy action
    if not args.version:
        print("❌ Version is required for deployment")
        return 1
    
    if not args.assets_dir:
        args.assets_dir = Path("./release-assets")
    
    if not args.assets_dir.exists():
        print(f"❌ Assets directory not found: {args.assets_dir}")
        return 1
    
    success = dist_manager.prepare_distribution(
        args.channel, args.version, args.assets_dir, args.dry_run
    )
    
    if success:
        print(f"🎉 Successfully prepared {args.channel} distribution for version {args.version}")
        return 0
    else:
        print(f"❌ Failed to prepare {args.channel} distribution")
        return 1


if __name__ == "__main__":
    exit(main())