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
from multichannel_messaging.utils.platform_utils import get_logs_dir

try:
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon
except ImportError:
    print("PySide6 is required. Please install it with: pip install PySide6")
    sys.exit(1)


def main():
    """Main application entry point."""
    try:
        # Create QApplication first
        app = QApplication(sys.argv)
        app.setApplicationName("CSC-Reach")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("CSC-Reach")
        app.setOrganizationDomain("csc-reach.com")
        
        # Set application properties
        app.setQuitOnLastWindowClosed(True)
        
        # Set application icon
        try:
            icon_paths = [
                # When running from source
                Path(__file__).parent.parent.parent / "assets" / "icons" / "messager.png",
                # When running from built app
                Path(sys.executable).parent / "assets" / "icons" / "messager.png",
                # Alternative paths
                Path("assets/icons/messager.png"),
            ]
            
            for icon_path in icon_paths:
                if icon_path.exists():
                    from PySide6.QtGui import QIcon
                    icon = QIcon(str(icon_path))
                    if not icon.isNull():
                        app.setWindowIcon(icon)
                        break
        except Exception as e:
            print(f"Warning: Could not set application icon: {e}")
        
        # Initialize configuration
        try:
            config_manager = ConfigManager()
        except Exception as e:
            QMessageBox.critical(
                None,
                "Configuration Error",
                f"Failed to initialize configuration:\n{e}\n\nThe application will exit."
            )
            sys.exit(1)
        
        # Setup logging
        try:
            log_level = config_manager.get("logging.log_level", "INFO")
            log_file = get_logs_dir() / "app.log"
            console_enabled = config_manager.get("logging.console_enabled", True)
            file_enabled = config_manager.get("logging.file_enabled", True)
            
            setup_logging(
                log_level=log_level,
                log_file=str(log_file),
                console_enabled=console_enabled,
                file_enabled=file_enabled
            )
            
            logger = logging.getLogger(__name__)
            logger.info("Application starting...")
            logger.info(f"Configuration loaded from: {config_manager.config_file}")
            
        except Exception as e:
            # Fallback to basic logging if setup fails
            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to setup logging: {e}")
        
        # Create and show main window
        try:
            main_window = MainWindow(config_manager)
            main_window.show()
            
            logger.info("Main window created and shown")
            
        except Exception as e:
            logger.error(f"Failed to create main window: {e}")
            QMessageBox.critical(
                None,
                "Application Error",
                f"Failed to create main window:\n{e}\n\nThe application will exit."
            )
            sys.exit(1)
        
        # Show startup message
        logger.info("CSC-Reach started successfully")
        
        # Run the application
        exit_code = app.exec()
        logger.info(f"Application exiting with code: {exit_code}")
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        # Last resort error handling
        try:
            logger = logging.getLogger(__name__)
            logger.critical(f"Unhandled exception in main: {e}", exc_info=True)
        except:
            print(f"Critical error: {e}")
        
        # Try to show error dialog if possible
        try:
            if 'app' in locals():
                QMessageBox.critical(
                    None,
                    "Critical Error",
                    f"A critical error occurred:\n{e}\n\nThe application will exit."
                )
        except:
            print(f"Failed to show error dialog: {e}")
        
        sys.exit(1)


if __name__ == "__main__":
    main()
