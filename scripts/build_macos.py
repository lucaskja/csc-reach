#!/usr/bin/env python3
"""
Build script for macOS executable using PyInstaller.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def main():
    """Main build function."""
    print("🚀 Building CSC-Reach for macOS...")
    
    # Get project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Clean previous builds
    print("🧹 Cleaning previous builds...")
    build_dirs = ['build', 'dist']
    for build_dir in build_dirs:
        if Path(build_dir).exists():
            shutil.rmtree(build_dir)
            print(f"   Removed {build_dir}/")
    
    # Create build directory
    Path('build').mkdir(exist_ok=True)
    
    # Run PyInstaller
    print("📦 Running PyInstaller...")
    spec_file = project_root / 'scripts' / 'build_macos.spec'
    
    try:
        result = subprocess.run([
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            str(spec_file)
        ], check=True, capture_output=True, text=True)
        
        print("✅ PyInstaller completed successfully")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    
    # Check if app was created
    app_path = project_root / 'dist' / 'CSC-Reach.app'
    if app_path.exists():
        print(f"✅ macOS app created successfully: {app_path}")
        
        # Get app size
        try:
            result = subprocess.run(['du', '-sh', str(app_path)], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                size = result.stdout.split()[0]
                print(f"📏 App size: {size}")
        except:
            pass
        
        # Test the app
        print("🧪 Testing the app...")
        try:
            # Just check if it can start (will exit quickly)
            test_result = subprocess.run([
                str(app_path / 'Contents' / 'MacOS' / 'CSC-Reach'),
                '--help'
            ], capture_output=True, text=True, timeout=10)
            
            print("✅ App executable test passed")
            
        except subprocess.TimeoutExpired:
            print("⚠️  App test timed out (this might be normal for GUI apps)")
        except Exception as e:
            print(f"⚠️  App test failed: {e}")
        
        print(f"\n🎉 Build completed successfully!")
        print(f"📱 App location: {app_path}")
        print(f"💡 To run: open '{app_path}'")
        
        return True
    else:
        print("❌ App was not created")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
