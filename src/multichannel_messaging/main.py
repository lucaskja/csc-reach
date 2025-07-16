#!/usr/bin/env python3
"""
Main entry point for the Multi-Channel Bulk Messaging System.
Enhanced with comprehensive application management and health monitoring.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Check for required dependencies early
try:
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon
except ImportError:
    print("PySide6 is required. Please install it with: pip install PySide6")
    sys.exit(1)

try:
    import psutil
except ImportError:
    print("psutil is required for system monitoring. Please install it with: pip install psutil")
    sys.exit(1)

from multichannel_messaging.core.application_manager import (
    get_application_manager, 
    initialize_application, 
    run_application
)
from multichannel_messaging.utils.logger import get_logger


def main():
    """Enhanced main application entry point with comprehensive error handling."""
    try:
        # Initialize the application with enhanced infrastructure
        if not initialize_application():
            print("Failed to initialize application. Check logs for details.")
            sys.exit(1)
        
        # Get logger after initialization
        logger = get_logger(__name__)
        logger.info("CSC-Reach application starting with enhanced infrastructure...")
        
        # Run the application
        exit_code = run_application()
        
        logger.info(f"CSC-Reach application finished with exit code: {exit_code}")
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        # Last resort error handling
        print(f"Critical application error: {e}")
        
        # Try to get logger for detailed error logging
        try:
            logger = get_logger(__name__)
            logger.critical(f"Unhandled exception in main: {e}", exc_info=True)
        except:
            pass
        
        # Try to show error dialog if Qt is available
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            QMessageBox.critical(
                None,
                "Critical Error",
                f"A critical error occurred:\n{e}\n\nThe application will exit.\n\nCheck logs for detailed information."
            )
        except:
            print(f"Failed to show error dialog. Original error: {e}")
        
        sys.exit(1)


if __name__ == "__main__":
    main()
