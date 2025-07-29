#!/usr/bin/env python3
"""
Safe console output utility for Windows builds.
Handles Unicode characters gracefully on Windows console.
"""

import sys
import platform


def safe_print(*args, **kwargs):
    """
    Print function that safely handles Unicode characters on Windows.
    Falls back to ASCII-safe alternatives for emojis on Windows console.
    """
    # Convert args to strings and handle Unicode
    safe_args = []
    for arg in args:
        text = str(arg)
        
        # Replace common emojis with ASCII alternatives for Windows console
        if platform.system() == 'Windows' and sys.stdout.encoding == 'cp1252':
            emoji_replacements = {
                '🚀': '[BUILD]',
                '✅': '[OK]',
                '❌': '[ERROR]',
                '⚠️': '[WARNING]',
                '🧹': '[CLEAN]',
                '📦': '[PACKAGE]',
                '🔨': '[COMPILE]',
                '📏': '[SIZE]',
                '📋': '[INFO]',
                '🗑️': '[DELETE]',
                '🍎': '[MACOS]',
                '🪟': '[WINDOWS]',
                '🔧': '[TOOL]',
                '🏗️': '[BUILD]',
            }
            
            for emoji, replacement in emoji_replacements.items():
                text = text.replace(emoji, replacement)
        
        safe_args.append(text)
    
    # Use the original print function
    print(*safe_args, **kwargs)


def safe_format_size(size_bytes):
    """Format file size in a safe way."""
    size_mb = size_bytes / (1024 * 1024)
    return f"{size_mb:.1f} MB"


def safe_status(success, message=""):
    """Print a status message safely."""
    if success:
        safe_print(f"[OK] {message}")
    else:
        safe_print(f"[ERROR] {message}")