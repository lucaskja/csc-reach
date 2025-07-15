#!/usr/bin/env python3
"""
Create ZIP distribution for Windows executable.
"""

import os
import shutil
import zipfile
from pathlib import Path


def main():
    """Create Windows ZIP distribution."""
    print("📦 Creating Windows ZIP distribution for CSC-Reach...")
    
    # Get project root (scripts/build -> scripts -> root)
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    exe_folder = project_root / 'build' / 'dist' / 'CSC-Reach'
    zip_path = project_root / 'build' / 'dist' / 'CSC-Reach-Windows.zip'
    
    if not exe_folder.exists():
        print("❌ Windows executable folder not found. Please build the Windows version first.")
        return False
    
    # Remove existing ZIP
    if zip_path.exists():
        zip_path.unlink()
        print("🗑️  Removed existing ZIP")
    
    # Create ZIP
    print("🔨 Creating ZIP distribution...")
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all files from the CSC-Reach folder
            for file_path in exe_folder.rglob('*'):
                if file_path.is_file():
                    # Create relative path within the ZIP
                    arcname = file_path.relative_to(exe_folder.parent)
                    zipf.write(file_path, arcname)
        
        print(f"✅ ZIP created successfully: {zip_path}")
        
        # Get ZIP size
        try:
            size_bytes = zip_path.stat().st_size
            size_mb = size_bytes / (1024 * 1024)
            print(f"📏 ZIP size: {size_mb:.1f} MB")
        except:
            pass
        
        # Create installation instructions
        readme_path = project_root / 'build' / 'dist' / 'WINDOWS_INSTALLATION.txt'
        with open(readme_path, 'w') as f:
            f.write("""CSC-Reach for Windows - Installation Instructions
================================================

1. Extract the ZIP file to your desired location (e.g., C:\\Program Files\\CSC-Reach\\)

2. Navigate to the extracted CSC-Reach folder

3. Double-click on "CSC-Reach" (or "CSC-Reach.exe") to run the application

System Requirements:
- Windows 10 or later
- Microsoft Outlook installed and configured
- 4GB RAM minimum
- 500MB free disk space

Troubleshooting:
- If Windows shows a security warning, click "More info" then "Run anyway"
- Ensure Microsoft Outlook is installed and configured with your email account
- If the application doesn't start, try running as administrator

For support, please refer to the documentation or contact support.
""")
        
        print(f"📋 Installation instructions created: {readme_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create ZIP: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
