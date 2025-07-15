#!/usr/bin/env python3
"""
Unified build script for all platforms.
"""

import sys
import subprocess
from pathlib import Path


def run_script(script_path, description):
    """Run a build script and return success status."""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([
            sys.executable, str(script_path)
        ], check=True)
        
        print(f"✅ {description} completed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        return False


def main():
    """Main build function."""
    print("🏗️  CSC-REACH UNIFIED BUILD SYSTEM")
    print("Building for all supported platforms...")
    
    # Get project root (scripts/build -> scripts -> root)
    project_root = Path(__file__).parent.parent.parent
    scripts_dir = project_root / 'scripts' / 'build'
    
    build_results = {}
    
    # Build macOS version
    macos_script = scripts_dir / 'build_macos.py'
    if macos_script.exists():
        build_results['macOS App'] = run_script(macos_script, "Building macOS Application")
        
        # Create DMG if macOS build succeeded
        if build_results['macOS App']:
            dmg_script = scripts_dir / 'create_dmg.py'
            if dmg_script.exists():
                build_results['macOS DMG'] = run_script(dmg_script, "Creating macOS DMG Installer")
    
    # Build Windows version
    windows_script = scripts_dir / 'build_windows.py'
    if windows_script.exists():
        build_results['Windows EXE'] = run_script(windows_script, "Building Windows Executable")
        
        # Create ZIP if Windows build succeeded
        if build_results.get('Windows EXE', False):
            zip_script = scripts_dir / 'create_windows_zip.py'
            if zip_script.exists():
                build_results['Windows ZIP'] = run_script(zip_script, "Creating Windows ZIP Distribution")
    
    # Print summary
    print(f"\n{'='*60}")
    print("🎯 BUILD SUMMARY")
    print(f"{'='*60}")
    
    success_count = 0
    total_count = 0
    
    for build_type, success in build_results.items():
        total_count += 1
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{build_type:20} {status}")
        if success:
            success_count += 1
    
    print(f"\n📊 Results: {success_count}/{total_count} builds successful")
    
    if success_count == total_count:
        print("\n🎉 ALL BUILDS COMPLETED SUCCESSFULLY!")
        print("\n📦 Distribution files:")
        
        # List distribution files
        dist_dir = project_root / 'build' / 'dist'
        if dist_dir.exists():
            for item in dist_dir.iterdir():
                if item.is_file() and item.suffix in ['.dmg', '.zip', '.exe']:
                    try:
                        size_mb = item.stat().st_size / (1024 * 1024)
                        print(f"   📁 {item.name} ({size_mb:.1f} MB)")
                    except:
                        print(f"   📁 {item.name}")
        
        print(f"\n💡 Distribution location: {dist_dir}")
        return True
    else:
        print(f"\n⚠️  Some builds failed. Check the logs above for details.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
