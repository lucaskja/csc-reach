#!/usr/bin/env python3
"""
Simple Release Script for CSC-Reach
Provides an easy interface for creating releases
"""

import argparse
import sys
from pathlib import Path

# Add build scripts to path
sys.path.insert(0, str(Path(__file__).parent / "build"))

from build_orchestrator import BuildOrchestrator
from version_manager import VersionManager
from release_manager import ReleaseManager


def main():
    """Main entry point for release script."""
    parser = argparse.ArgumentParser(
        description="Create a release for CSC-Reach",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a development release with patch version bump
  python scripts/release.py --dev --patch
  
  # Create a staging release with minor version bump
  python scripts/release.py --staging --minor
  
  # Create a production release with current version
  python scripts/release.py --production
  
  # Dry run for production release with major version bump
  python scripts/release.py --production --major --dry-run
  
  # Just show current version
  python scripts/release.py --version
        """
    )
    
    # Release type (mutually exclusive)
    release_group = parser.add_mutually_exclusive_group()
    release_group.add_argument("--dev", "--development", action="store_const", 
                              const="development", dest="release_type",
                              help="Create development release")
    release_group.add_argument("--staging", action="store_const", 
                              const="staging", dest="release_type",
                              help="Create staging release")
    release_group.add_argument("--production", "--prod", action="store_const", 
                              const="production", dest="release_type",
                              help="Create production release")
    
    # Version increment (mutually exclusive)
    version_group = parser.add_mutually_exclusive_group()
    version_group.add_argument("--major", action="store_const", 
                              const="major", dest="increment",
                              help="Increment major version")
    version_group.add_argument("--minor", action="store_const", 
                              const="minor", dest="increment",
                              help="Increment minor version")
    version_group.add_argument("--patch", action="store_const", 
                              const="patch", dest="increment",
                              help="Increment patch version")
    
    # Other options
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be done without actually doing it")
    parser.add_argument("--version", action="store_true", 
                       help="Show current version and exit")
    parser.add_argument("--info", action="store_true", 
                       help="Show version information and exit")
    parser.add_argument("--quick", action="store_true", 
                       help="Skip quality checks and tests (not recommended)")
    
    args = parser.parse_args()
    
    # Initialize managers
    version_manager = VersionManager()
    
    # Show version information
    if args.version:
        print(version_manager.get_current_version())
        return 0
    
    if args.info:
        info = version_manager.get_version_info()
        print("📊 CSC-Reach Version Information")
        print(f"   Current Version: {info['current_version']}")
        print(f"   Latest Git Tag: {info['latest_tag'] or 'None'}")
        print(f"   Is Prerelease: {info['is_prerelease']}")
        print()
        print("   Next Versions:")
        for bump_type, next_version in info['next_versions'].items():
            print(f"     {bump_type.capitalize()}: {next_version}")
        return 0
    
    # Default to development release
    release_type = args.release_type or "development"
    
    # Validate production releases
    if release_type == "production":
        if args.increment:
            print("⚠️  Production release with version increment.")
            print("   This will create a new version and tag.")
            
            response = input("   Continue? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("   Cancelled.")
                return 0
    
    # Determine stages to run
    stages = None
    if args.quick:
        stages = ["version_check", "build", "package", "release"]
        print("⚠️  Quick mode: Skipping quality checks and tests")
    
    # Initialize orchestrator and run pipeline
    orchestrator = BuildOrchestrator()
    
    print(f"🚀 Creating {release_type} release for CSC-Reach")
    if args.increment:
        print(f"   Version increment: {args.increment}")
    if args.dry_run:
        print("   Mode: Dry run (no changes will be made)")
    print()
    
    success = orchestrator.run_pipeline(
        release_type=release_type,
        increment_type=args.increment,
        stages=stages,
        dry_run=args.dry_run
    )
    
    if success:
        print()
        print("🎉 Release completed successfully!")
        
        if not args.dry_run:
            current_version = version_manager.get_current_version()
            print(f"   Version: {current_version}")
            
            if release_type == "production":
                print("   🏷️  Git tag created")
                print("   📦 GitHub release will be created by CI/CD")
            else:
                print(f"   📦 {release_type.title()} build artifacts created")
        
        return 0
    else:
        print()
        print("❌ Release failed!")
        print("   Check the logs above for details.")
        return 1


if __name__ == "__main__":
    exit(main())