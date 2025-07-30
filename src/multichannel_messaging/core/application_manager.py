"""
Application Manager for CSC-Reach - Enhanced core infrastructure management.

This module provides centralized application lifecycle management, health monitoring,
performance tracking, and resource management.
"""

import sys
import time
import threading
import psutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QApplication

from .config_manager import ConfigManager
from .message_logger import MessageLogger
from ..utils.logger import get_logger, setup_logging
from ..utils.platform_utils import get_logs_dir, get_platform, check_outlook_installed
from ..utils.exceptions import MultiChannelMessagingError

logger = get_logger(__name__)


@dataclass
class SystemInfo:
    """System information and diagnostics."""
    platform: str
    python_version: str
    app_version: str
    memory_total: int
    memory_available: int
    cpu_count: int
    outlook_installed: bool
    startup_time: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/reporting."""
        return {
            "platform": self.platform,
            "python_version": self.python_version,
            "app_version": self.app_version,
            "memory_total_mb": round(self.memory_total / (1024 * 1024)),
            "memory_available_mb": round(self.memory_available / (1024 * 1024)),
            "cpu_count": self.cpu_count,
            "outlook_installed": self.outlook_installed,
            "startup_time": self.startup_time.isoformat()
        }


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking."""
    startup_duration: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    active_threads: int = 0
    gui_response_time_ms: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/reporting."""
        return {
            "startup_duration_ms": round(self.startup_duration * 1000, 2),
            "memory_usage_mb": round(self.memory_usage_mb, 2),
            "cpu_usage_percent": round(self.cpu_usage_percent, 2),
            "active_threads": self.active_threads,
            "gui_response_time_ms": round(self.gui_response_time_ms, 2),
            "last_updated": self.last_updated.isoformat()
        }


class ApplicationHealthMonitor(QObject):
    """Application health monitoring with Qt integration."""
    
    health_updated = Signal(dict)  # Emits health status updates
    performance_updated = Signal(dict)  # Emits performance metrics
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.is_monitoring = False
        self.health_timer = QTimer()
        self.health_timer.timeout.connect(self._update_health_metrics)
        
        # Performance tracking
        self.performance_metrics = PerformanceMetrics()
        self.startup_time = time.time()
        
        # Health status
        self.health_status = {
            "overall": "healthy",
            "components": {},
            "last_check": datetime.now(),
            "uptime_seconds": 0
        }
    
    def start_monitoring(self, interval_ms: int = 30000) -> None:
        """Start health monitoring with specified interval."""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.health_timer.start(interval_ms)
            logger.info(f"Started health monitoring with {interval_ms}ms interval")
    
    def stop_monitoring(self) -> None:
        """Stop health monitoring."""
        if self.is_monitoring:
            self.is_monitoring = False
            self.health_timer.stop()
            logger.info("Stopped health monitoring")
    
    def _update_health_metrics(self) -> None:
        """Update health metrics and emit signals."""
        try:
            # Update performance metrics
            process = psutil.Process()
            self.performance_metrics.memory_usage_mb = process.memory_info().rss / (1024 * 1024)
            self.performance_metrics.cpu_usage_percent = process.cpu_percent()
            self.performance_metrics.active_threads = process.num_threads()
            self.performance_metrics.last_updated = datetime.now()
            
            # Update health status
            self.health_status["last_check"] = datetime.now()
            self.health_status["uptime_seconds"] = time.time() - self.startup_time
            
            # Check component health
            self._check_component_health()
            
            # Emit signals
            self.health_updated.emit(self.health_status.copy())
            self.performance_updated.emit(self.performance_metrics.to_dict())
            
        except Exception as e:
            logger.warning(f"Failed to update health metrics: {e}")
    
    def _check_component_health(self) -> None:
        """Check health of individual components."""
        components = {}
        
        # Check configuration
        try:
            self.config_manager.get("app.language")
            components["configuration"] = "healthy"
        except Exception:
            components["configuration"] = "unhealthy"
        
        # Check logging
        try:
            logger.debug("Health check log test")
            components["logging"] = "healthy"
        except Exception:
            components["logging"] = "unhealthy"
        
        # Check Outlook integration
        components["outlook"] = "healthy" if check_outlook_installed() else "unavailable"
        
        self.health_status["components"] = components
        
        # Determine overall health
        unhealthy_components = [k for k, v in components.items() if v == "unhealthy"]
        if unhealthy_components:
            self.health_status["overall"] = "degraded"
        else:
            self.health_status["overall"] = "healthy"
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return self.performance_metrics.to_dict()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return self.health_status.copy()


class ApplicationManager:
    """
    Enhanced application manager for CSC-Reach.
    
    Provides centralized management of application lifecycle, configuration,
    logging, health monitoring, and resource cleanup.
    """
    
    def __init__(self):
        self.startup_time = time.time()
        self.config_manager: Optional[ConfigManager] = None
        self.health_monitor: Optional[ApplicationHealthMonitor] = None
        self.message_logger: Optional[MessageLogger] = None
        self.qt_app: Optional[QApplication] = None
        self.main_window = None
        self.system_info: Optional[SystemInfo] = None
        self.cleanup_callbacks: List[Callable] = []
        self.is_initialized = False
        
        # Thread safety
        self._lock = threading.Lock()
    
    def initialize(self) -> bool:
        """
        Initialize the application with comprehensive setup.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            with self._lock:
                if self.is_initialized:
                    logger.warning("Application already initialized")
                    return True
                
                logger.info("Starting CSC-Reach application initialization...")
                
                # Step 1: Collect system information
                self._collect_system_info()
                
                # Step 2: Initialize Qt Application
                self._initialize_qt_application()
                
                # Step 3: Initialize configuration
                self._initialize_configuration()
                
                # Step 4: Setup logging
                self._setup_enhanced_logging()
                
                # Step 5: Initialize message logging
                self._initialize_message_logging()
                
                # Step 6: Initialize health monitoring
                self._initialize_health_monitoring()
                
                # Step 7: Perform health checks
                self._perform_startup_health_checks()
                
                # Calculate startup duration
                startup_duration = time.time() - self.startup_time
                logger.info(f"Application initialization completed in {startup_duration:.2f}s")
                
                # Log system information
                logger.info(f"System Info: {self.system_info.to_dict()}")
                
                self.is_initialized = True
                return True
                
        except Exception as e:
            logger.critical(f"Application initialization failed: {e}", exc_info=True)
            return False
    
    def _collect_system_info(self) -> None:
        """Collect comprehensive system information."""
        try:
            memory = psutil.virtual_memory()
            self.system_info = SystemInfo(
                platform=get_platform(),
                python_version=sys.version.split()[0],
                app_version="1.0.0",  # TODO: Get from package metadata
                memory_total=memory.total,
                memory_available=memory.available,
                cpu_count=psutil.cpu_count(),
                outlook_installed=check_outlook_installed()
            )
        except Exception as e:
            logger.error(f"Failed to collect system info: {e}")
            # Create minimal system info
            self.system_info = SystemInfo(
                platform=get_platform(),
                python_version=sys.version.split()[0],
                app_version="1.0.0",
                memory_total=0,
                memory_available=0,
                cpu_count=1,
                outlook_installed=False
            )
    
    def _initialize_qt_application(self) -> None:
        """Initialize Qt application with proper configuration."""
        if QApplication.instance() is None:
            self.qt_app = QApplication(sys.argv)
        else:
            self.qt_app = QApplication.instance()
        
        # Configure Qt application
        self.qt_app.setApplicationName("CSC-Reach")
        self.qt_app.setApplicationVersion("1.0.0")
        self.qt_app.setOrganizationName("CSC-Reach")
        self.qt_app.setOrganizationDomain("csc-reach.com")
        self.qt_app.setQuitOnLastWindowClosed(True)
        
        # Set application icon
        self._set_application_icon()
        
        logger.info("Qt application initialized")
    
    def _set_application_icon(self) -> None:
        """Set application icon with fallback handling."""
        try:
            from PySide6.QtGui import QIcon
            
            icon_paths = [
                # When running from source
                Path(__file__).parent.parent.parent.parent / "assets" / "icons" / "csc-reach.png",
                # When running from built app
                Path(sys.executable).parent / "assets" / "icons" / "csc-reach.png",
                # Alternative paths
                Path("assets/icons/csc-reach.png"),
            ]
            
            for icon_path in icon_paths:
                if icon_path.exists():
                    icon = QIcon(str(icon_path))
                    if not icon.isNull():
                        self.qt_app.setWindowIcon(icon)
                        logger.debug(f"Set application icon from: {icon_path}")
                        return
            
            logger.warning("Could not find application icon")
            
        except Exception as e:
            logger.warning(f"Failed to set application icon: {e}")
    
    def _initialize_configuration(self) -> None:
        """Initialize configuration manager."""
        try:
            self.config_manager = ConfigManager()
            logger.info("Configuration manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize configuration: {e}")
            raise
    
    def _setup_enhanced_logging(self) -> None:
        """Setup enhanced logging with configuration."""
        try:
            log_level = self.config_manager.get("logging.log_level", "INFO")
            log_file = get_logs_dir() / "app.log"
            console_enabled = self.config_manager.get("logging.console_enabled", True)
            file_enabled = self.config_manager.get("logging.file_enabled", True)
            
            setup_logging(
                log_level=log_level,
                log_file=str(log_file),
                console_enabled=console_enabled,
                file_enabled=file_enabled
            )
            
            logger.info("Enhanced logging configured")
            
        except Exception as e:
            # Fallback to basic logging
            import logging
            logging.basicConfig(level=logging.INFO)
            logger.error(f"Failed to setup enhanced logging: {e}")
    
    def _initialize_message_logging(self) -> None:
        """Initialize message logging system."""
        try:
            # Get user ID from config or generate one
            user_id = self.config_manager.get("user.id", "default_user")
            
            # Initialize message logger
            logs_dir = get_logs_dir()
            db_path = logs_dir / "message_logs.db"
            
            self.message_logger = MessageLogger(
                db_path=str(db_path),
                user_id=user_id
            )
            
            # Register cleanup callback
            self.register_cleanup_callback(self._cleanup_message_logger)
            
            logger.info("Message logging system initialized")
            
        except Exception as e:
            logger.warning(f"Failed to initialize message logging: {e}")
    
    def _initialize_health_monitoring(self) -> None:
        """Initialize health monitoring system."""
        try:
            self.health_monitor = ApplicationHealthMonitor(self.config_manager)
            
            # Connect health monitoring signals if needed
            # self.health_monitor.health_updated.connect(self._on_health_updated)
            # self.health_monitor.performance_updated.connect(self._on_performance_updated)
            
            # Start monitoring
            monitoring_interval = self.config_manager.get("monitoring.interval_ms", 30000)
            self.health_monitor.start_monitoring(monitoring_interval)
            
            logger.info("Health monitoring initialized")
            
        except Exception as e:
            logger.warning(f"Failed to initialize health monitoring: {e}")
    
    def _perform_startup_health_checks(self) -> None:
        """Perform comprehensive startup health checks."""
        health_issues = []
        
        # Check system requirements
        if self.system_info.memory_available < 512 * 1024 * 1024:  # 512MB
            health_issues.append("Low available memory (< 512MB)")
        
        # Check Outlook installation
        if not self.system_info.outlook_installed:
            health_issues.append("Microsoft Outlook not detected")
        
        # Check configuration
        try:
            self.config_manager.get("app.language")
        except Exception:
            health_issues.append("Configuration system not working")
        
        # Log health check results
        if health_issues:
            logger.warning(f"Startup health issues detected: {health_issues}")
        else:
            logger.info("All startup health checks passed")
    
    def create_main_window(self):
        """Create and configure the main application window."""
        try:
            from ..gui.main_window import MainWindow
            
            self.main_window = MainWindow(
                config_manager=self.config_manager,
                message_logger=self.message_logger
            )
            
            # Register cleanup callback
            self.register_cleanup_callback(self._cleanup_main_window)
            
            logger.info("Main window created")
            return self.main_window
            
        except Exception as e:
            logger.error(f"Failed to create main window: {e}")
            raise
    
    def run(self) -> int:
        """
        Run the application event loop.
        
        Returns:
            Application exit code
        """
        try:
            if not self.is_initialized:
                raise MultiChannelMessagingError("Application not initialized")
            
            if not self.main_window:
                self.create_main_window()
            
            # Show main window
            self.main_window.show()
            logger.info("Main window shown, starting event loop")
            
            # Run Qt event loop
            exit_code = self.qt_app.exec()
            
            logger.info(f"Application event loop finished with exit code: {exit_code}")
            return exit_code
            
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
            return 0
        except Exception as e:
            logger.critical(f"Critical error in application run: {e}", exc_info=True)
            return 1
        finally:
            self.cleanup()
    
    def register_cleanup_callback(self, callback: Callable) -> None:
        """Register a cleanup callback to be called on shutdown."""
        self.cleanup_callbacks.append(callback)
    
    def cleanup(self) -> None:
        """Perform comprehensive application cleanup."""
        logger.info("Starting application cleanup...")
        
        try:
            # Stop health monitoring
            if self.health_monitor:
                self.health_monitor.stop_monitoring()
            
            # Execute cleanup callbacks
            for callback in self.cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.warning(f"Cleanup callback failed: {e}")
            
            # Save configuration
            if self.config_manager:
                try:
                    self.config_manager.save_user_config()
                except Exception as e:
                    logger.warning(f"Failed to save configuration: {e}")
            
            logger.info("Application cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def _cleanup_main_window(self) -> None:
        """Cleanup main window resources."""
        if self.main_window:
            try:
                # Save window geometry
                if hasattr(self.main_window, 'save_geometry'):
                    self.main_window.save_geometry()
                
                self.main_window.close()
                logger.debug("Main window cleaned up")
            except Exception as e:
                logger.warning(f"Failed to cleanup main window: {e}")
    
    def _cleanup_message_logger(self) -> None:
        """Cleanup message logger resources."""
        if self.message_logger:
            try:
                # End any active session
                if self.message_logger.current_session_id:
                    self.message_logger.end_session()
                
                logger.debug("Message logger cleaned up")
            except Exception as e:
                logger.warning(f"Failed to cleanup message logger: {e}")
    
    def get_system_info(self) -> Optional[SystemInfo]:
        """Get system information."""
        return self.system_info
    
    def get_performance_metrics(self) -> Optional[Dict[str, Any]]:
        """Get current performance metrics."""
        if self.health_monitor:
            return self.health_monitor.get_current_metrics()
        return None
    
    def get_health_status(self) -> Optional[Dict[str, Any]]:
        """Get current health status."""
        if self.health_monitor:
            return self.health_monitor.get_health_status()
        return None
    
    def get_message_logger(self) -> Optional[MessageLogger]:
        """Get the message logger instance."""
        return self.message_logger


# Global application manager instance
_app_manager: Optional[ApplicationManager] = None


def get_application_manager() -> ApplicationManager:
    """Get the global application manager instance."""
    global _app_manager
    if _app_manager is None:
        _app_manager = ApplicationManager()
    return _app_manager


def initialize_application() -> bool:
    """Initialize the global application manager."""
    app_manager = get_application_manager()
    return app_manager.initialize()


def run_application() -> int:
    """Run the application using the global application manager."""
    app_manager = get_application_manager()
    return app_manager.run()