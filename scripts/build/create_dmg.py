#!/usr/bin/env python3
"""
Create DMG installer for macOS app.
"""

import os
import subprocess
import shutil
from pathlib import Path


def main():
    """Create DMG installer."""
    print("📦 Creating DMG installer for CSC-Reach...")
    
    # Get project root (scripts/build -> scripts -> root)
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    app_path = project_root / 'build' / 'dist' / 'CSC-Reach.app'
    dmg_path = project_root / 'build' / 'dist' / 'CSC-Reach-macOS.dmg'
    
    if not app_path.exists():
        print("❌ App not found. Please build the app first.")
        return False
    
    # Remove existing DMG
    if dmg_path.exists():
        dmg_path.unlink()
        print("🗑️  Removed existing DMG")
    
    # Create DMG
    print("🔨 Creating DMG...")
    try:
        # Use hdiutil to create DMG
        subprocess.run([
            'hdiutil', 'create',
            '-volname', 'CSC-Reach',
            '-srcfolder', str(app_path),
            '-ov',
            '-format', 'UDZO',
            str(dmg_path)
        ], check=True)
        
        print(f"✅ DMG created successfully: {dmg_path}")
        
        # Get DMG size
        try:
            result = subprocess.run(['du', '-sh', str(dmg_path)], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                size = result.stdout.split()[0]
                print(f"📏 DMG size: {size}")
        except:
            pass
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create DMG: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
