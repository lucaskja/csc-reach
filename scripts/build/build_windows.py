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

# Import safe console utilities
try:
    from safe_console import safe_print, safe_format_size, safe_status
except ImportError:
    # Fallback if safe_console is not available
    def safe_print(*args, **kwargs):
        try:
            print(*args, **kwargs)
        except UnicodeEncodeError:
            # Replace problematic characters and try again
            safe_args = []
            for arg in args:
                text = str(arg).encode('ascii', 'replace').decode('ascii')
                safe_args.append(text)
            print(*safe_args, **kwargs)
    
    def safe_format_size(size_bytes):
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def safe_status(success, message=""):
        prefix = "[OK]" if success else "[ERROR]"
        safe_print(f"{prefix} {message}")


def main():
    """Main build function."""
    safe_print("Building CSC-Reach for Windows...")
    
    # Check if we're actually on Windows
    if platform.system() != 'Windows':
        safe_print("WARNING: Building Windows executable on non-Windows platform")
        safe_print("   This will create a native executable for the current platform")
        safe_print("   For true Windows builds, use:")
        safe_print("   1. Windows machine/VM")
        safe_print("   2. Docker with Windows base image")
        safe_print("   3. GitHub Actions CI/CD")
        safe_print("   4. See docs/dev/windows_build_guide.md for details")
        safe_print()
    
    # Get project root (scripts/build -> scripts -> root)
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    # Clean previous builds
    safe_print("Cleaning previous builds...")
    build_dir = project_root / 'build'
    if build_dir.exists():
        shutil.rmtree(build_dir)
        safe_print(f"   Removed {build_dir}/")
    
    # Also clean default dist directory
    dist_dir = project_root / 'dist'
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        safe_print(f"   Removed {dist_dir}/")
    
    # Create organized build directories
    build_dirs = ['build/dist', 'build/temp', 'build/logs']
    for build_path in build_dirs:
        Path(build_path).mkdir(parents=True, exist_ok=True)
    
    # Run PyInstaller
    safe_print("Running PyInstaller...")
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
        
        safe_status(True, "PyInstaller completed successfully")
        
        # Save build logs
        log_file = project_root / 'build' / 'logs' / 'build_windows.log'
        with open(log_file, 'w') as f:
            f.write("=== PyInstaller STDOUT ===\n")
            f.write(result.stdout)
            f.write("\n=== PyInstaller STDERR ===\n")
            f.write(result.stderr)
        
    except subprocess.CalledProcessError as e:
        safe_status(False, f"PyInstaller failed: {e}")
        safe_print("STDOUT:", e.stdout)
        safe_print("STDERR:", e.stderr)
        
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
        safe_status(True, f"Executable created: {exe_path}")
        safe_print(f"   Size: {safe_format_size(exe_path.stat().st_size)}")
        
        # Show platform information
        if platform.system() != 'Windows':
            safe_print(f"   Platform: {platform.system()} {platform.machine()}")
            safe_print("   Note: This is NOT a Windows executable")
            safe_print("   Use GitHub Actions or Windows machine for true Windows builds")
        
        # Create distribution package if on Windows
        if platform.system() == 'Windows':
            create_windows_distribution(project_root, exe_path)
        
        return True
    else:
        safe_status(False, "Executable was not created")
        safe_print("   Checked locations:")
        for location in possible_locations:
            safe_print(f"   - {location}")
        return False


def create_windows_distribution(project_root: Path, exe_path: Path):
    """Create Windows distribution package."""
    safe_print("Creating Windows distribution package...")
    
    try:
        # Import the Windows ZIP creation script
        sys.path.insert(0, str(project_root / 'scripts' / 'build'))
        from create_windows_zip import create_zip_distribution
        
        zip_path = create_zip_distribution(project_root, exe_path)
        if zip_path and zip_path.exists():
            safe_status(True, f"Windows ZIP created: {zip_path}")
            safe_print(f"   Size: {safe_format_size(zip_path.stat().st_size)}")
        else:
            safe_print("WARNING: Windows ZIP creation failed")
            
    except Exception as e:
        safe_print(f"WARNING: Could not create Windows ZIP: {e}")


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
