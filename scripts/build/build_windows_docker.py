#!/usr/bin/env python3
"""
Build Windows executable using Docker with Wine.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def main():
    """Main Docker build function."""
    print("🐳 Building CSC-Reach for Windows using Docker...")
    
    # Get project root
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    # Check if Docker is available
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Docker found: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker not found. Please install Docker to use this build method.")
        print("   Alternative: Use GitHub Actions or a Windows machine/VM")
        return False
    
    # Build Docker image
    print("🔨 Building Docker image...")
    dockerfile_path = project_root / 'docker' / 'Dockerfile.windows'
    
    try:
        subprocess.run([
            'docker', 'build',
            '-f', str(dockerfile_path),
            '-t', 'csc-reach-windows-builder',
            '.'
        ], check=True)
        print("✅ Docker image built successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker image build failed: {e}")
        return False
    
    # Clean previous builds
    print("🧹 Cleaning previous builds...")
    build_dir = project_root / 'build'
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)
    
    # Run build in Docker container
    print("📦 Running Windows build in Docker container...")
    try:
        subprocess.run([
            'docker', 'run',
            '--rm',
            '-v', f'{project_root}:/app',
            '-v', f'{build_dir}:/app/build',
            'csc-reach-windows-builder'
        ], check=True)
        print("✅ Docker build completed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker build failed: {e}")
        return False
    
    # Check for executable
    exe_path = build_dir / 'dist' / 'CSC-Reach' / 'CSC-Reach.exe'
    if exe_path.exists():
        print(f"✅ Windows executable created: {exe_path}")
        print(f"   Size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
        return True
    else:
        print("❌ Windows executable not found")
        print("   Check Docker build logs for errors")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
