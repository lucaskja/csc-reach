#!/usr/bin/env python3
"""
Unified build script for Multi-Channel Messaging System.
Builds for the current platform and creates distribution packages.
"""

import sys
import subprocess
from pathlib import Path

from multichannel_messaging.utils.platform_utils import is_windows, is_macos


def main():
    """Main build function."""
    print("🚀 CSC-Reach - Unified Build Script")
    print("=" * 40)
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Create icons first
    print("🎨 Creating platform-specific icons...")
    try:
        result = subprocess.run([
            sys.executable, str(project_root / "scripts" / "create_icons.py")
        ], check=True)
        print("✅ Icons created successfully")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Icon creation failed: {e}")
        print("Continuing with build...")
    
    print()
    
    # Build for current platform
    if is_macos():
        print("🍎 Building for macOS...")
        
        # Build app
        try:
            result = subprocess.run([
                sys.executable, str(project_root / "scripts" / "build_macos.py")
            ], check=True)
            print("✅ macOS app built successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ macOS build failed: {e}")
            return False
        
        # Create DMG
        try:
            result = subprocess.run([
                sys.executable, str(project_root / "scripts" / "create_dmg.py")
            ], check=True)
            print("✅ DMG created successfully")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  DMG creation failed: {e}")
        
        print("\n🎉 macOS build completed!")
        print(f"📱 App: {project_root}/dist/CSC-Reach.app")
        print(f"💿 DMG: {project_root}/dist/CSC-Reach-macOS.dmg")
        
    elif is_windows():
        print("🪟 Building for Windows...")
        
        # Build executable
        try:
            result = subprocess.run([
                sys.executable, str(project_root / "scripts" / "build_windows.py")
            ], check=True)
            print("✅ Windows executable built successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Windows build failed: {e}")
            return False
        
        print("\n🎉 Windows build completed!")
        print(f"💻 Executable: {project_root}/dist/CSC-Reach/CSC-Reach.exe")
        
    else:
        print("❌ Unsupported platform for building")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
