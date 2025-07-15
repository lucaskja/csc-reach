#!/usr/bin/env python3
"""
Script to help trigger Windows builds via GitHub Actions.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Guide user through Windows build process."""
    print("🚀 CSC-Reach Windows Build Helper")
    print("=" * 50)
    
    project_root = Path(__file__).parent.parent.parent
    
    print("Since PyInstaller cannot cross-compile, we need to use GitHub Actions")
    print("to build a true Windows executable on actual Windows runners.")
    print()
    
    # Check if we're in a git repository with remote
    try:
        result = subprocess.run(['git', 'remote', '-v'], 
                              capture_output=True, text=True, check=True, cwd=project_root)
        if 'github.com' in result.stdout:
            print("✅ GitHub repository detected")
            print()
            print("🎯 TO BUILD WINDOWS EXECUTABLE:")
            print("1. Push your code to GitHub (if not already done)")
            print("2. Go to your GitHub repository")
            print("3. Click on 'Actions' tab")
            print("4. Find 'Build Windows Executable' workflow")
            print("5. Click 'Run workflow' button")
            print("6. Optionally specify version (e.g., 'v1.0.0')")
            print("7. Click 'Run workflow' to start the build")
            print()
            print("📥 AFTER BUILD COMPLETES:")
            print("1. Go to the completed workflow run")
            print("2. Scroll down to 'Artifacts' section")
            print("3. Download 'CSC-Reach-Windows-latest.zip'")
            print("4. Extract to get your Windows executable")
            print()
            
            # Try to get the repository URL
            try:
                url_result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                          capture_output=True, text=True, check=True, cwd=project_root)
                repo_url = url_result.stdout.strip()
                if repo_url.endswith('.git'):
                    repo_url = repo_url[:-4]
                
                actions_url = f"{repo_url}/actions"
                print(f"🔗 Direct link to Actions: {actions_url}")
                print()
                
            except subprocess.CalledProcessError:
                pass
                
        else:
            print("⚠️  No GitHub remote found")
            print("   You need to push this repository to GitHub first")
            print()
            
    except subprocess.CalledProcessError:
        print("⚠️  Not in a git repository or git not available")
        print()
    
    print("🔄 ALTERNATIVE OPTIONS:")
    print()
    print("1. 🖥️  Use a Windows machine/VM:")
    print("   - Clone repository on Windows")
    print("   - Run: python scripts/build/build_windows.py")
    print()
    print("2. 🐳 Try Docker (experimental):")
    print("   - Run: python scripts/build/build_windows_docker.py")
    print("   - Note: Uses Wine, may have compatibility issues")
    print()
    print("3. ☁️  Use cloud build services:")
    print("   - Azure DevOps, AppVeyor, CircleCI")
    print("   - All support Windows build agents")
    print()
    
    # Show current platform build as demonstration
    print("🔧 DEMONSTRATION BUILD (Current Platform):")
    print("To show the build system works, I can create a native executable")
    print("for the current platform (macOS). This demonstrates that the")
    print("application and build system are working correctly.")
    print()
    
    response = input("Would you like to create a demonstration build? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        print()
        print("🚀 Creating demonstration build...")
        try:
            result = subprocess.run([
                sys.executable, 'scripts/build/build_windows.py'
            ], cwd=project_root, check=True)
            
            print()
            print("✅ Demonstration build completed!")
            print("   This shows the build system works correctly.")
            print("   For Windows executable, use GitHub Actions as described above.")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Build failed: {e}")
            return False
    
    print()
    print("📚 For detailed instructions, see:")
    print("   docs/dev/windows_build_guide.md")
    
    return True


if __name__ == '__main__':
    main()
