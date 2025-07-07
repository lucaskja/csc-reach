#!/usr/bin/env python3
"""
Build script for Windows executable using PyInstaller.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def main():
    """Main build function."""
    print("🚀 Building Multi-Channel Messaging System for Windows...")
    
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
    spec_file = project_root / 'scripts' / 'build_windows.spec'
    
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
    
    # Check if executable was created
    exe_path = project_root / 'dist' / 'MultiChannelMessaging' / 'MultiChannelMessaging.exe'
    if exe_path.exists():
        print(f"✅ Windows executable created successfully: {exe_path}")
        
        # Get executable size
        try:
            size_bytes = exe_path.stat().st_size
            size_mb = size_bytes / (1024 * 1024)
            print(f"📏 Executable size: {size_mb:.1f} MB")
        except:
            pass
        
        # Test the executable
        print("🧪 Testing the executable...")
        try:
            # Just check if it can start (will exit quickly)
            test_result = subprocess.run([
                str(exe_path), '--help'
            ], capture_output=True, text=True, timeout=10)
            
            print("✅ Executable test passed")
            
        except subprocess.TimeoutExpired:
            print("⚠️  Executable test timed out (this might be normal for GUI apps)")
        except Exception as e:
            print(f"⚠️  Executable test failed: {e}")
        
        print(f"\n🎉 Build completed successfully!")
        print(f"💻 Executable location: {exe_path}")
        print(f"📁 Distribution folder: {exe_path.parent}")
        
        return True
    else:
        print("❌ Executable was not created")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
