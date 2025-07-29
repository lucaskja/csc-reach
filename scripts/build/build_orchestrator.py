#!/usr/bin/env python3
"""
Build Orchestrator for CSC-Reach
Coordinates the entire build, test, and release process
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml

# Import our custom modules
from release_manager import ReleaseManager
from release_notes_generator import ReleaseNotesGenerator
from distribution_manager import DistributionManager
from version_manager import VersionManager


class BuildOrchestrator:
    """Orchestrates the complete build, test, and release pipeline."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the build orchestrator."""
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.config_file = self.project_root / "scripts" / "build" / "build_config.yaml"
        
        # Initialize managers
        self.release_manager = ReleaseManager(self.project_root)
        self.notes_generator = ReleaseNotesGenerator(self.project_root)
        self.dist_manager = DistributionManager(self.project_root)
        self.version_manager = VersionManager(self.project_root)
        
        # Load configuration
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load build configuration."""
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict:
        """Create default build configuration."""
        config = {
            'pipeline': {
                'stages': [
                    'version_check',
                    'quality_checks',
                    'tests',
                    'build',
                    'package',
                    'release'
                ],
                'parallel_builds': True,
                'fail_fast': True
            },
            'quality': {
                'required_coverage': 80,
                'max_complexity': 10,
                'enable_security_scan': True
            },
            'build': {
                'platforms': ['windows', 'macos'],
                'create_installers': True,
                'sign_binaries': False  # Requires certificates
            },
            'release': {
                'auto_increment_version': True,
                'create_github_release': True,
                'notify_on_completion': True
            }
        }
        
        # Save default config
        os.makedirs(self.config_file.parent, exist_ok=True)
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
            
        return config
    
    def run_stage(self, stage: str, context: Dict) -> bool:
        """Run a specific pipeline stage."""
        print(f"🚀 Running stage: {stage}")
        
        try:
            if stage == "version_check":
                return self._stage_version_check(context)
            elif stage == "quality_checks":
                return self._stage_quality_checks(context)
            elif stage == "tests":
                return self._stage_tests(context)
            elif stage == "build":
                return self._stage_build(context)
            elif stage == "package":
                return self._stage_package(context)
            elif stage == "release":
                return self._stage_release(context)
            else:
                print(f"❌ Unknown stage: {stage}")
                return False
                
        except Exception as e:
            print(f"❌ Stage {stage} failed: {e}")
            return False
    
    def _stage_version_check(self, context: Dict) -> bool:
        """Version check and management stage."""
        print("📋 Version Check Stage")
        
        current_version = self.version_manager.get_current_version()
        print(f"   Current version: {current_version}")
        
        # Auto-increment version if requested
        if context.get('auto_increment') and context.get('increment_type'):
            new_version = self.version_manager.increment_version(
                current_version, context['increment_type']
            )
            
            if context.get('dry_run'):
                print(f"   [DRY RUN] Would increment version to: {new_version}")
                context['version'] = new_version
            else:
                if self.version_manager.update_version(new_version):
                    print(f"   ✅ Version incremented to: {new_version}")
                    context['version'] = new_version
                else:
                    print(f"   ❌ Failed to increment version")
                    return False
        else:
            context['version'] = current_version
        
        return True
    
    def _stage_quality_checks(self, context: Dict) -> bool:
        """Code quality checks stage."""
        print("🔍 Quality Checks Stage")
        
        checks = [
            ('black --check src/ tests/ scripts/', 'Code formatting'),
            ('flake8 src/ tests/ scripts/ --max-line-length=88', 'Linting'),
            ('mypy src/ --ignore-missing-imports', 'Type checking'),
            ('bandit -r src/ -f json', 'Security scan')
        ]
        
        failed_checks = []
        
        for command, description in checks:
            print(f"   Running {description}...")
            
            if context.get('dry_run'):
                print(f"   [DRY RUN] Would run: {command}")
                continue
            
            try:
                result = subprocess.run(
                    command.split(),
                    cwd=self.project_root,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print(f"   ✅ {description} passed")
                else:
                    print(f"   ❌ {description} failed")
                    failed_checks.append(description)
                    
            except Exception as e:
                print(f"   ❌ {description} error: {e}")
                failed_checks.append(description)
        
        if failed_checks and self.config.get('pipeline', {}).get('fail_fast', True):
            print(f"❌ Quality checks failed: {', '.join(failed_checks)}")
            return False
        
        return True
    
    def _stage_tests(self, context: Dict) -> bool:
        """Testing stage."""
        print("🧪 Testing Stage")
        
        if context.get('dry_run'):
            print("   [DRY RUN] Would run comprehensive test suite")
            return True
        
        try:
            # Run comprehensive test suite
            result = subprocess.run([
                'python', 'scripts/test_runner.py',
                '--test-type', 'all',
                '--verbose'
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("   ✅ All tests passed")
                return True
            else:
                print("   ❌ Tests failed")
                print(result.stdout)
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"   ❌ Test execution error: {e}")
            return False
    
    def _stage_build(self, context: Dict) -> bool:
        """Build stage."""
        print("🏗️ Build Stage")
        
        platforms = self.config.get('build', {}).get('platforms', ['windows', 'macos'])
        
        if context.get('dry_run'):
            print(f"   [DRY RUN] Would build for platforms: {', '.join(platforms)}")
            return True
        
        build_success = True
        
        for platform in platforms:
            print(f"   Building for {platform}...")
            
            try:
                if platform == 'windows':
                    result = subprocess.run([
                        'python', 'scripts/build/build_windows.py'
                    ], cwd=self.project_root)
                elif platform == 'macos':
                    result = subprocess.run([
                        'python', 'scripts/build/build_macos.py'
                    ], cwd=self.project_root)
                else:
                    print(f"   ⚠️ Unknown platform: {platform}")
                    continue
                
                if result.returncode == 0:
                    print(f"   ✅ {platform} build completed")
                else:
                    print(f"   ❌ {platform} build failed")
                    build_success = False
                    
            except Exception as e:
                print(f"   ❌ {platform} build error: {e}")
                build_success = False
        
        return build_success
    
    def _stage_package(self, context: Dict) -> bool:
        """Packaging stage."""
        print("📦 Packaging Stage")
        
        version = context.get('version', 'unknown')
        release_type = context.get('release_type', 'development')
        
        # Create release assets directory
        assets_dir = self.project_root / "release-assets"
        assets_dir.mkdir(exist_ok=True)
        
        if context.get('dry_run'):
            print(f"   [DRY RUN] Would package version {version} for {release_type}")
            return True
        
        try:
            # Copy build artifacts to release assets
            build_dir = self.project_root / "build" / "dist"
            
            if build_dir.exists():
                for item in build_dir.iterdir():
                    if item.is_file() and (item.suffix in ['.zip', '.dmg', '.exe']):
                        dest = assets_dir / item.name
                        dest.write_bytes(item.read_bytes())
                        print(f"   ✅ Packaged {item.name}")
            
            # Generate release notes
            notes = self.notes_generator.generate_release_notes(version, release_type)
            notes_file = assets_dir / "release-notes.md"
            with open(notes_file, 'w') as f:
                f.write(notes)
            print(f"   ✅ Generated release notes")
            
            # Create release manifest
            success = self.release_manager.create_staged_release(
                version, release_type, assets_dir
            )
            
            if success:
                print(f"   ✅ Created release manifest")
                return True
            else:
                print(f"   ❌ Failed to create release manifest")
                return False
                
        except Exception as e:
            print(f"   ❌ Packaging error: {e}")
            return False
    
    def _stage_release(self, context: Dict) -> bool:
        """Release stage."""
        print("🚀 Release Stage")
        
        version = context.get('version', 'unknown')
        release_type = context.get('release_type', 'development')
        assets_dir = self.project_root / "release-assets"
        
        if context.get('dry_run'):
            print(f"   [DRY RUN] Would create {release_type} release for version {version}")
            return True
        
        try:
            # Prepare distribution
            success = self.dist_manager.prepare_distribution(
                release_type, version, assets_dir
            )
            
            if success:
                print(f"   ✅ Distribution prepared for {release_type}")
                
                # Create git tag if this is a production release
                if release_type == 'production':
                    if self.version_manager.create_git_tag(version):
                        print(f"   ✅ Created git tag v{version}")
                    else:
                        print(f"   ⚠️ Failed to create git tag")
                
                return True
            else:
                print(f"   ❌ Failed to prepare distribution")
                return False
                
        except Exception as e:
            print(f"   ❌ Release error: {e}")
            return False
    
    def run_pipeline(
        self, 
        release_type: str = "development",
        increment_type: Optional[str] = None,
        stages: Optional[List[str]] = None,
        dry_run: bool = False
    ) -> bool:
        """Run the complete build pipeline."""
        print(f"🎯 Starting CSC-Reach Build Pipeline")
        print(f"   Release Type: {release_type}")
        print(f"   Dry Run: {dry_run}")
        
        # Prepare context
        context = {
            'release_type': release_type,
            'increment_type': increment_type,
            'auto_increment': increment_type is not None,
            'dry_run': dry_run,
            'start_time': datetime.now()
        }
        
        # Get stages to run
        if stages is None:
            stages = self.config.get('pipeline', {}).get('stages', [])
        
        print(f"   Stages: {' -> '.join(stages)}")
        print()
        
        # Run each stage
        failed_stages = []
        
        for stage in stages:
            stage_start = datetime.now()
            success = self.run_stage(stage, context)
            stage_duration = datetime.now() - stage_start
            
            if success:
                print(f"   ✅ Stage {stage} completed in {stage_duration.total_seconds():.1f}s")
            else:
                print(f"   ❌ Stage {stage} failed after {stage_duration.total_seconds():.1f}s")
                failed_stages.append(stage)
                
                if self.config.get('pipeline', {}).get('fail_fast', True):
                    break
            
            print()
        
        # Pipeline summary
        total_duration = datetime.now() - context['start_time']
        
        if failed_stages:
            print(f"❌ Pipeline failed after {total_duration.total_seconds():.1f}s")
            print(f"   Failed stages: {', '.join(failed_stages)}")
            return False
        else:
            print(f"✅ Pipeline completed successfully in {total_duration.total_seconds():.1f}s")
            if context.get('version'):
                print(f"   Version: {context['version']}")
            return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="CSC-Reach Build Orchestrator")
    parser.add_argument("--release-type", choices=["development", "staging", "production"],
                       default="development", help="Release type")
    parser.add_argument("--increment", choices=["major", "minor", "patch"],
                       help="Auto-increment version")
    parser.add_argument("--stages", nargs="+", 
                       choices=["version_check", "quality_checks", "tests", "build", "package", "release"],
                       help="Specific stages to run")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--config", type=Path, help="Custom configuration file")
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = BuildOrchestrator()
    
    # Run pipeline
    success = orchestrator.run_pipeline(
        release_type=args.release_type,
        increment_type=args.increment,
        stages=args.stages,
        dry_run=args.dry_run
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()