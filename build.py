#!/usr/bin/env python3
"""
Simple Build Wrapper for CSC-Reach
Quick and easy building with sensible defaults.
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Main wrapper function."""
    # Get the enhanced build script
    project_root = Path(__file__).parent
    build_script = project_root / 'scripts' / 'build' / 'build_unified.py'
    
    if not build_script.exists():
        print("❌ Enhanced build script not found!")
        print(f"Expected: {build_script}")
        return 1
    
    # Print quick help if no arguments or help requested
    if len(sys.argv) == 1 or '--help' in sys.argv or '-h' in sys.argv:
        print("🏗️  CSC-REACH QUICK BUILD")
        print("=" * 50)
        print()
        print("Quick Commands:")
        print("  python build.py                    # Build everything")
        print("  python build.py macos              # Build only macOS")
        print("  python build.py windows            # Build only Windows")
        print("  python build.py clean              # Clean build and rebuild all")
        print("  python build.py clean macos        # Clean build and rebuild macOS")
        print("  python build.py clean windows      # Clean build and rebuild Windows")
        print()
        print("Advanced Usage:")
        print("  python scripts/build/build_unified.py --help")
        print()
        return 0
    
    # Parse simple arguments
    args = sys.argv[1:]
    build_args = []
    
    # Handle clean command
    if 'clean' in args:
        build_args.append('--clean')
        args.remove('clean')
    
    # Handle platform selection
    if 'macos' in args:
        build_args.extend(['--platform', 'macos'])
        args.remove('macos')
    elif 'windows' in args:
        build_args.extend(['--platform', 'windows'])
        args.remove('windows')
    
    # Pass through any remaining arguments
    build_args.extend(args)
    
    # Run the enhanced build script
    try:
        result = subprocess.run([
            sys.executable, str(build_script)
        ] + build_args)
        return result.returncode
    except KeyboardInterrupt:
        print("\n❌ Build interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Error running build script: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
