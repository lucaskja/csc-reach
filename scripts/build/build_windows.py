#!/usr/bin/env python3
"""
Build script for Windows executable using PyInstaller.
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path


def main():
    """Main build function."""
    print("🚀 Building CSC-Reach for Windows...")
    
    # Check if we're actually on Windows
    if platform.system() != 'Windows':
        print("⚠️  WARNING: Building Windows executable on non-Windows platform")
        print("   This will create a native executable for the current platform")
        print("   For true Windows builds, use:")
        print("   1. Windows machine/VM")
        print("   2. Docker with Windows base image")
        print("   3. GitHub Actions CI/CD")
        print("   4. See docs/dev/windows_build_guide.md for details")
        print()
    
    # Get project root (scripts/build -> scripts -> root)
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    # Clean previous builds
    print("🧹 Cleaning previous builds...")
    build_dir = project_root / 'build'
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print(f"   Removed {build_dir}/")
    
    # Also clean default dist directory
    dist_dir = project_root / 'dist'
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print(f"   Removed {dist_dir}/")
    
    # Create organized build directories
    build_dirs = ['build/dist', 'build/temp', 'build/logs']
    for build_path in build_dirs:
        Path(build_path).mkdir(parents=True, exist_ok=True)
    
    # Run PyInstaller
    print("📦 Running PyInstaller...")
    spec_file = project_root / 'scripts' / 'build' / 'build_windows.spec'
    
    try:
        result = subprocess.run([
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            '--distpath', str(project_root / 'build' / 'dist'),
            '--workpath', str(project_root / 'build' / 'temp'),
            str(spec_file)
        ], check=True, capture_output=True, text=True)
        
        print("✅ PyInstaller completed successfully")
        
        # Save build logs
        log_file = project_root / 'build' / 'logs' / 'build_windows.log'
        with open(log_file, 'w') as f:
            f.write("=== PyInstaller STDOUT ===\n")
            f.write(result.stdout)
            f.write("\n=== PyInstaller STDERR ===\n")
            f.write(result.stderr)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        
        # Save error logs
        log_file = project_root / 'build' / 'logs' / 'build_windows_error.log'
        with open(log_file, 'w') as f:
            f.write("=== PyInstaller ERROR ===\n")
            f.write(f"Return code: {e.returncode}\n")
            f.write("STDOUT:\n")
            f.write(e.stdout)
            f.write("\nSTDERR:\n")
            f.write(e.stderr)
        
        return False
    
    # Check for executable in build/dist directory
    exe_name = 'CSC-Reach.exe' if platform.system() == 'Windows' else 'CSC-Reach'
    possible_locations = [
        project_root / 'build' / 'dist' / 'CSC-Reach' / exe_name,
        project_root / 'build' / 'dist' / exe_name,
    ]
    
    exe_path = None
    for location in possible_locations:
        if location.exists():
            exe_path = location
            break
    
    if exe_path:
        print(f"✅ Executable created: {exe_path}")
        print(f"   Size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
        
        # Show platform information
        if platform.system() != 'Windows':
            print(f"   Platform: {platform.system()} {platform.machine()}")
            print("   Note: This is NOT a Windows executable")
            print("   Use GitHub Actions or Windows machine for true Windows builds")
        
        # Create distribution package if on Windows
        if platform.system() == 'Windows':
            create_windows_distribution(project_root, exe_path)
        
        return True
    else:
        print("❌ Executable was not created")
        print("   Checked locations:")
        for location in possible_locations:
            print(f"   - {location}")
        return False


def create_windows_distribution(project_root: Path, exe_path: Path):
    """Create Windows distribution package."""
    print("📦 Creating Windows distribution package...")
    
    try:
        # Import the Windows ZIP creation script
        sys.path.insert(0, str(project_root / 'scripts' / 'build'))
        from create_windows_zip import create_zip_distribution
        
        zip_path = create_zip_distribution(project_root, exe_path)
        if zip_path and zip_path.exists():
            print(f"✅ Windows ZIP created: {zip_path}")
            print(f"   Size: {zip_path.stat().st_size / (1024*1024):.1f} MB")
        else:
            print("⚠️  Windows ZIP creation failed")
            
    except Exception as e:
        print(f"⚠️  Could not create Windows ZIP: {e}")


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
