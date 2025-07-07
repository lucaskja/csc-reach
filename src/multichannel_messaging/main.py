#!/usr/bin/env python3
"""
Main entry point for the Multi-Channel Bulk Messaging System.
"""

import sys
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from multichannel_messaging.gui.main_window import MainWindow
from multichannel_messaging.core.config_manager import ConfigManager
from multichannel_messaging.utils.logger import setup_logging

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
except ImportError:
    print("PySide6 is required. Please install it with: pip install PySide6")
    sys.exit(1)


def main():
    """Main application entry point."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Create QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("Multi-Channel Bulk Messaging System")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("Multi-Channel Messaging")
        
        # Initialize configuration
        config_manager = ConfigManager()
        
        # Create and show main window
        main_window = MainWindow(config_manager)
        main_window.show()
        
        logger.info("Application started successfully")
        
        # Run the application
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
