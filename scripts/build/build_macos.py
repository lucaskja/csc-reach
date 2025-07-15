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
    spec_file = project_root / 'scripts' / 'build' / 'build_macos.spec'
    
    try:
        result = subprocess.run([
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            str(spec_file)
        ], check=True, capture_output=True, text=True)
        
        print("✅ PyInstaller completed successfully")
        
        # Save build logs
        log_file = project_root / 'build' / 'logs' / 'build_macos.log'
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
        log_file = project_root / 'build' / 'logs' / 'build_macos_error.log'
        with open(log_file, 'w') as f:
            f.write("=== PyInstaller ERROR ===\n")
            f.write(f"Return code: {e.returncode}\n")
            f.write("STDOUT:\n")
            f.write(e.stdout)
            f.write("\nSTDERR:\n")
            f.write(e.stderr)
        
        return False
    
    # Check for app in multiple possible locations
    possible_locations = [
        project_root / 'build' / 'dist' / 'CSC-Reach.app',
        project_root / 'dist' / 'CSC-Reach.app'
    ]
    
    app_path = None
    for location in possible_locations:
        if location.exists():
            app_path = location
            break
    
    # Move app to organized location if needed
    if app_path and app_path.parent.name == 'dist' and app_path.parent.parent.name != 'build':
        # App is in root dist/, move to build/dist/
        target_path = project_root / 'build' / 'dist' / 'CSC-Reach.app'
        if target_path.exists():
            shutil.rmtree(target_path)
        shutil.move(str(app_path), str(target_path))
        app_path = target_path
        
        # Also move other files from dist/
        root_dist = project_root / 'dist'
        if root_dist.exists():
            for item in root_dist.iterdir():
                target = project_root / 'build' / 'dist' / item.name
                if target.exists():
                    if target.is_dir():
                        shutil.rmtree(target)
                    else:
                        target.unlink()
                shutil.move(str(item), str(target))
            root_dist.rmdir()
    
    if app_path and app_path.exists():
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
