#!/usr/bin/env python3
"""
Development environment setup script for Multi-Channel Bulk Messaging System.
"""

import os
import sys
import subprocess
import venv
from pathlib import Path


def run_command(command, cwd=None):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True,
            cwd=cwd
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{command}': {e}")
        print(f"Error output: {e.stderr}")
        return None


def setup_virtual_environment():
    """Set up a virtual environment for development."""
    project_root = Path(__file__).parent.parent
    venv_path = project_root / "venv"
    
    if venv_path.exists():
        print("Virtual environment already exists.")
        return venv_path
    
    print("Creating virtual environment...")
    venv.create(venv_path, with_pip=True)
    
    return venv_path


def install_dependencies(venv_path):
    """Install project dependencies."""
    project_root = Path(__file__).parent.parent
    
    # Determine the correct pip path based on the platform
    if sys.platform == "win32":
        pip_path = venv_path / "Scripts" / "pip"
    else:
        pip_path = venv_path / "bin" / "pip"
    
    print("Installing dependencies...")
    
    # Install the project in development mode with dev dependencies
    run_command(f'"{pip_path}" install -e ".[dev]"', cwd=project_root)


def main():
    """Main setup function."""
    print("Setting up Multi-Channel Bulk Messaging System development environment...")
    
    # Set up virtual environment
    venv_path = setup_virtual_environment()
    
    # Install dependencies
    install_dependencies(venv_path)
    
    print("\nDevelopment environment setup complete!")
    print("\nTo activate the virtual environment:")
    
    if sys.platform == "win32":
        print(f"  {venv_path}\\Scripts\\activate")
    else:
        print(f"  source {venv_path}/bin/activate")
    
    print("\nTo run the application:")
    print("  python src/multichannel_messaging/main.py")
    
    print("\nTo run tests:")
    print("  pytest")


if __name__ == "__main__":
    main()
