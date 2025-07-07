#!/usr/bin/env python3
"""
Create platform-specific icons from the source PNG file.
"""

import os
import sys
from pathlib import Path
from PIL import Image


def create_ico_file(png_path: Path, ico_path: Path):
    """Create Windows ICO file from PNG."""
    print(f"Creating Windows ICO: {ico_path}")
    
    # Open the PNG image
    img = Image.open(png_path)
    
    # Convert to RGBA if not already
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Create different sizes for ICO
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    
    # Resize and save as ICO
    img.save(ico_path, format='ICO', sizes=sizes)
    print(f"✅ Created ICO file: {ico_path}")


def create_icns_file(png_path: Path, icns_path: Path):
    """Create macOS ICNS file from PNG using system tools."""
    print(f"Creating macOS ICNS: {icns_path}")
    
    # Create temporary iconset directory
    iconset_dir = icns_path.parent / f"{icns_path.stem}.iconset"
    iconset_dir.mkdir(exist_ok=True)
    
    try:
        # Open the source image
        img = Image.open(png_path)
        
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Define the required sizes for macOS iconset
        icon_sizes = [
            (16, "icon_16x16.png"),
            (32, "icon_16x16@2x.png"),
            (32, "icon_32x32.png"),
            (64, "icon_32x32@2x.png"),
            (128, "icon_128x128.png"),
            (256, "icon_128x128@2x.png"),
            (256, "icon_256x256.png"),
            (512, "icon_256x256@2x.png"),
            (512, "icon_512x512.png"),
            (1024, "icon_512x512@2x.png"),
        ]
        
        # Create each required size
        for size, filename in icon_sizes:
            resized_img = img.resize((size, size), Image.Resampling.LANCZOS)
            resized_img.save(iconset_dir / filename, format='PNG')
        
        # Use iconutil to create ICNS file
        import subprocess
        result = subprocess.run([
            'iconutil', '-c', 'icns', str(iconset_dir), '-o', str(icns_path)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Created ICNS file: {icns_path}")
        else:
            print(f"❌ Failed to create ICNS: {result.stderr}")
            return False
            
    finally:
        # Clean up iconset directory
        import shutil
        if iconset_dir.exists():
            shutil.rmtree(iconset_dir)
    
    return True


def main():
    """Main function to create all icon formats."""
    print("🎨 Creating platform-specific icons...")
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Source PNG file
    png_path = project_root / "assets" / "icons" / "messager.png"
    
    if not png_path.exists():
        print(f"❌ Source PNG not found: {png_path}")
        return False
    
    print(f"📁 Source PNG: {png_path}")
    
    # Create output paths
    ico_path = project_root / "assets" / "icons" / "messager.ico"
    icns_path = project_root / "assets" / "icons" / "messager.icns"
    
    success = True
    
    # Create ICO for Windows
    try:
        create_ico_file(png_path, ico_path)
    except Exception as e:
        print(f"❌ Failed to create ICO: {e}")
        success = False
    
    # Create ICNS for macOS
    try:
        if not create_icns_file(png_path, icns_path):
            success = False
    except Exception as e:
        print(f"❌ Failed to create ICNS: {e}")
        success = False
    
    if success:
        print("🎉 All icons created successfully!")
    else:
        print("⚠️  Some icons failed to create")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
