#!/usr/bin/env python3
"""
Create ZIP distribution for Windows executable.
"""

import os
import shutil
import zipfile
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
    """Create Windows ZIP distribution."""
    safe_print("Creating Windows ZIP distribution for CSC-Reach...")
    
    # Get project root (scripts/build -> scripts -> root)
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    exe_folder = project_root / 'build' / 'dist' / 'CSC-Reach'
    zip_path = project_root / 'build' / 'dist' / 'CSC-Reach-Windows.zip'
    
    if not exe_folder.exists():
        safe_status(False, "Windows executable folder not found. Please build the Windows version first.")
        return False
    
    # Remove existing ZIP
    if zip_path.exists():
        zip_path.unlink()
        safe_print("Removed existing ZIP")
    
    # Create ZIP
    safe_print("Creating ZIP distribution...")
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all files from the CSC-Reach folder
            for file_path in exe_folder.rglob('*'):
                if file_path.is_file():
                    # Create relative path within the ZIP
                    arcname = file_path.relative_to(exe_folder.parent)
                    zipf.write(file_path, arcname)
        
        safe_status(True, f"ZIP created successfully: {zip_path}")
        
        # Get ZIP size
        try:
            size_bytes = zip_path.stat().st_size
            safe_print(f"ZIP size: {safe_format_size(size_bytes)}")
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
        
        safe_print(f"Installation instructions created: {readme_path}")
        
        return True
        
    except Exception as e:
        safe_status(False, f"Failed to create ZIP: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
