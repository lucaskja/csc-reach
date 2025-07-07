"""
Platform-specific utilities for Multi-Channel Bulk Messaging System.
"""

import platform
import sys
from pathlib import Path
from typing import Optional


def get_platform() -> str:
    """
    Get the current platform name.
    
    Returns:
        Platform name: 'windows', 'macos', or 'linux'
    """
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    else:
        return "linux"


def is_windows() -> bool:
    """Check if running on Windows."""
    return get_platform() == "windows"


def is_macos() -> bool:
    """Check if running on macOS."""
    return get_platform() == "macos"


def is_linux() -> bool:
    """Check if running on Linux."""
    return get_platform() == "linux"


def get_app_data_dir() -> Path:
    """
    Get the application data directory for the current platform.
    
    Returns:
        Path to application data directory
    """
    if is_windows():
        # Windows: %APPDATA%/CSC-Reach
        app_data = Path.home() / "AppData" / "Roaming" / "CSC-Reach"
    elif is_macos():
        # macOS: ~/Library/Application Support/CSC-Reach
        app_data = Path.home() / "Library" / "Application Support" / "CSC-Reach"
    else:
        # Linux: ~/.local/share/CSC-Reach
        app_data = Path.home() / ".local" / "share" / "CSC-Reach"
    
    app_data.mkdir(parents=True, exist_ok=True)
    return app_data


def get_config_dir() -> Path:
    """
    Get the configuration directory for the current platform.
    
    Returns:
        Path to configuration directory
    """
    if is_windows():
        # Windows: %APPDATA%/CSC-Reach
        config_dir = get_app_data_dir()
    elif is_macos():
        # macOS: ~/Library/Preferences/CSC-Reach
        config_dir = Path.home() / "Library" / "Preferences" / "CSC-Reach"
    else:
        # Linux: ~/.config/CSC-Reach
        config_dir = Path.home() / ".config" / "CSC-Reach"
    
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_logs_dir() -> Path:
    """
    Get the logs directory for the current platform.
    
    Returns:
        Path to logs directory
    """
    if is_windows():
        # Windows: %APPDATA%/CSC-Reach/logs
        logs_dir = get_app_data_dir() / "logs"
    elif is_macos():
        # macOS: ~/Library/Logs/CSC-Reach
        logs_dir = Path.home() / "Library" / "Logs" / "CSC-Reach"
    else:
        # Linux: ~/.local/share/CSC-Reach/logs
        logs_dir = get_app_data_dir() / "logs"
    
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_outlook_executable_path() -> Optional[Path]:
    """
    Get the path to the Outlook executable for the current platform.
    
    Returns:
        Path to Outlook executable or None if not found
    """
    if is_windows():
        # Common Outlook paths on Windows
        possible_paths = [
            Path("C:/Program Files/Microsoft Office/root/Office16/OUTLOOK.EXE"),
            Path("C:/Program Files (x86)/Microsoft Office/root/Office16/OUTLOOK.EXE"),
            Path("C:/Program Files/Microsoft Office/Office16/OUTLOOK.EXE"),
            Path("C:/Program Files (x86)/Microsoft Office/Office16/OUTLOOK.EXE"),
        ]
        for path in possible_paths:
            if path.exists():
                return path
    elif is_macos():
        # Outlook on macOS
        outlook_path = Path("/Applications/Microsoft Outlook.app")
        if outlook_path.exists():
            return outlook_path
    
    return None


def check_outlook_installed() -> bool:
    """
    Check if Microsoft Outlook is installed on the system.
    
    Returns:
        True if Outlook is installed, False otherwise
    """
    return get_outlook_executable_path() is not None


def get_python_executable() -> Path:
    """
    Get the path to the current Python executable.
    
    Returns:
        Path to Python executable
    """
    return Path(sys.executable)
