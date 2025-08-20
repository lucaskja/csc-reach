#!/usr/bin/env python3
"""
Version bumping utility for CSC-Reach.

This script helps increment version numbers in pyproject.toml following semantic versioning.
"""

import argparse
import re
import sys
from pathlib import Path


def get_current_version(pyproject_path: Path) -> str:
    """Get the current version from pyproject.toml."""
    content = pyproject_path.read_text()
    match = re.search(r'^version = "([^"]+)"', content, re.MULTILINE)
    if not match:
        raise ValueError("Could not find version in pyproject.toml")
    return match.group(1)


def bump_version(version: str, bump_type: str) -> str:
    """Bump version according to semantic versioning."""
    parts = version.split('.')
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {version}")
    
    major, minor, patch = map(int, parts)
    
    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    elif bump_type == 'patch':
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")
    
    return f"{major}.{minor}.{patch}"


def update_version_in_file(pyproject_path: Path, new_version: str) -> None:
    """Update the version in pyproject.toml."""
    content = pyproject_path.read_text()
    new_content = re.sub(
        r'^version = "[^"]+"',
        f'version = "{new_version}"',
        content,
        flags=re.MULTILINE
    )
    pyproject_path.write_text(new_content)


def main():
    parser = argparse.ArgumentParser(description="Bump version in pyproject.toml")
    parser.add_argument(
        'bump_type',
        choices=['major', 'minor', 'patch'],
        help='Type of version bump'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without making changes'
    )
    
    args = parser.parse_args()
    
    # Find pyproject.toml
    pyproject_path = Path('pyproject.toml')
    if not pyproject_path.exists():
        print("Error: pyproject.toml not found in current directory")
        sys.exit(1)
    
    try:
        current_version = get_current_version(pyproject_path)
        new_version = bump_version(current_version, args.bump_type)
        
        print(f"Current version: {current_version}")
        print(f"New version: {new_version}")
        
        if args.dry_run:
            print("Dry run - no changes made")
        else:
            update_version_in_file(pyproject_path, new_version)
            print(f"✅ Version updated to {new_version}")
            print("\nNext steps:")
            print("1. Commit the version change:")
            print(f"   git add pyproject.toml")
            print(f"   git commit -m 'Bump version to {new_version}'")
            print("2. Push to trigger automatic build and release:")
            print("   git push origin main")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()