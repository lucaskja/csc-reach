#!/usr/bin/env python3
"""
Global pytest configuration and fixtures for the test suite.
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Generator, Dict, Any

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import test utilities
from multichannel_messaging.core.config_manager import ConfigManager
from multichannel_messaging.core.template_manager import TemplateManager
from multichannel_messaging.core.models import Customer, MessageTemplate
from multichannel_messaging.core.i18n_manager import get_i18n_manager


# Test configuration
def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Set test environment variables
    os.environ["TESTING"] = "1"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    # Disable GUI components during testing
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    
    # Configure test markers
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for component interactions"
    )
    config.addinivalue_line(
        "markers", "gui: GUI tests requiring display"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests (> 5 seconds)"
    )
    config.addinivalue_line(
        "markers", "network: Tests requiring network access"
    )
    config.addinivalue_line(
        "markers", "external: Tests requiring external services"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "gui" in str(item.fspath):
            item.add_marker(pytest.mark.gui)
        
        # Add slow marker for tests that might be slow
        if any(keyword in item.name.lower() for keyword in ["slow", "performance", "load"]):
            item.add_marker(pytest.mark.slow)
        
        # Add network marker for tests that require network
        if any(keyword in item.name.lower() for keyword in ["api", "request", "http", "network"]):
            item.add_marker(pytest.mark.network)


# Global fixtures
@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Get the test data directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_config_manager(temp_dir: Path) -> ConfigManager:
    """Create a mock configuration manager for testing."""
    config_manager = ConfigManager()
    
    # Override paths to use temporary directory
    config_manager.get_config_dir = lambda: temp_dir / "config"
    config_manager.get_templates_path = lambda: temp_dir / "templates"
    config_manager.get_logs_path = lambda: temp_dir / "logs"
    config_manager.get_data_path = lambda: temp_dir / "data"
    
    # Create directories
    for path_func in [
        config_manager.get_config_dir,
        config_manager.get_templates_path,
        config_manager.get_logs_path,
        config_manager.get_data_path,
    ]:
        path_func().mkdir(parents=True, exist_ok=True)
    
    return config_manager


@pytest.fixture
def mock_template_manager(mock_config_manager: ConfigManager) -> TemplateManager:
    """Create a mock template manager for testing."""
    return TemplateManager(mock_config_manager)


@pytest.fixture
def sample_customer() -> Customer:
    """Create a sample customer for testing."""
    return Customer(
        name="John Doe",
        company="Test Corporation",
        phone="+1-555-0123",
        email="john.doe@testcorp.com",
        whatsapp="+1-555-0123"
    )


@pytest.fixture
def sample_customers() -> list[Customer]:
    """Create a list of sample customers for testing."""
    return [
        Customer(
            name="John Doe",
            company="Test Corporation",
            phone="+1-555-0123",
            email="john.doe@testcorp.com",
            whatsapp="+1-555-0123"
        ),
        Customer(
            name="Jane Smith",
            company="Tech Solutions Inc",
            phone="+1-555-0456",
            email="jane.smith@techsolutions.com",
            whatsapp="+1-555-0456"
        ),
        Customer(
            name="Bob Johnson",
            company="Global Enterprises",
            phone="+1-555-0789",
            email="bob.johnson@globalent.com",
            whatsapp="+1-555-0789"
        )
    ]


@pytest.fixture
def sample_email_template() -> MessageTemplate:
    """Create a sample email template for testing."""
    return MessageTemplate(
        id="test_email",
        name="Test Email Template",
        channels=["email"],
        subject="Welcome to {company}, {name}!",
        content="Dear {name},\n\nWelcome to our service at {company}!\n\nBest regards,\nThe Team",
        variables=["name", "company"]
    )


@pytest.fixture
def sample_whatsapp_template() -> MessageTemplate:
    """Create a sample WhatsApp template for testing."""
    return MessageTemplate(
        id="test_whatsapp",
        name="Test WhatsApp Template",
        channels=["whatsapp"],
        whatsapp_content="Hi {name}! Welcome to {company}! 👋",
        variables=["name", "company"]
    )


@pytest.fixture
def sample_multichannel_template() -> MessageTemplate:
    """Create a sample multi-channel template for testing."""
    return MessageTemplate(
        id="test_multichannel",
        name="Test Multi-Channel Template",
        channels=["email", "whatsapp"],
        subject="Welcome {name}!",
        content="Dear {name},\n\nWelcome to {company}!",
        whatsapp_content="Hi {name}! Welcome to {company}! 🎉",
        variables=["name", "company"]
    )


@pytest.fixture
def mock_i18n_manager():
    """Create a mock i18n manager for testing."""
    i18n_manager = get_i18n_manager()
    i18n_manager.set_language("en")  # Default to English for tests
    return i18n_manager


@pytest.fixture
def mock_email_service():
    """Create a mock email service for testing."""
    mock_service = Mock()
    mock_service.send_email.return_value = {"success": True, "message_id": "test_123"}
    mock_service.is_available.return_value = True
    mock_service.get_status.return_value = "connected"
    return mock_service


@pytest.fixture
def mock_whatsapp_service():
    """Create a mock WhatsApp service for testing."""
    mock_service = Mock()
    mock_service.send_message.return_value = {"success": True, "message_id": "wa_test_123"}
    mock_service.is_available.return_value = True
    mock_service.get_status.return_value = "connected"
    mock_service.get_rate_limit_status.return_value = {"remaining": 1000, "reset_time": 3600}
    return mock_service


@pytest.fixture
def mock_csv_data() -> str:
    """Create sample CSV data for testing."""
    return """name,company,email,phone,whatsapp
John Doe,Test Corp,john@testcorp.com,+1-555-0123,+1-555-0123
Jane Smith,Tech Solutions,jane@techsolutions.com,+1-555-0456,+1-555-0456
Bob Johnson,Global Enterprises,bob@globalent.com,+1-555-0789,+1-555-0789"""


@pytest.fixture
def mock_csv_file(temp_dir: Path, mock_csv_data: str) -> Path:
    """Create a temporary CSV file for testing."""
    csv_file = temp_dir / "test_customers.csv"
    csv_file.write_text(mock_csv_data, encoding="utf-8")
    return csv_file


# Platform-specific fixtures
@pytest.fixture
def is_windows() -> bool:
    """Check if running on Windows."""
    return sys.platform.startswith("win")


@pytest.fixture
def is_macos() -> bool:
    """Check if running on macOS."""
    return sys.platform == "darwin"


@pytest.fixture
def is_linux() -> bool:
    """Check if running on Linux."""
    return sys.platform.startswith("linux")


# GUI testing fixtures
@pytest.fixture
def qapp():
    """Create QApplication instance for GUI testing."""
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    yield app
    
    # Cleanup
    app.processEvents()


# Mock external services
@pytest.fixture
def mock_outlook_com():
    """Mock Outlook COM interface for Windows testing."""
    with patch("win32com.client.Dispatch") as mock_dispatch:
        mock_outlook = Mock()
        mock_dispatch.return_value = mock_outlook
        
        # Mock Outlook application
        mock_outlook.CreateItem.return_value = Mock()
        mock_outlook.GetNamespace.return_value = Mock()
        
        yield mock_outlook


@pytest.fixture
def mock_applescript():
    """Mock AppleScript execution for macOS testing."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        yield mock_run


# Performance testing fixtures
@pytest.fixture
def performance_timer():
    """Timer fixture for performance testing."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.perf_counter()
        
        def stop(self):
            self.end_time = time.perf_counter()
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# Test data validation fixtures
@pytest.fixture
def validate_test_data():
    """Fixture to validate test data integrity."""
    def _validate(data: Dict[str, Any], required_fields: list[str]) -> bool:
        """Validate that test data contains required fields."""
        for field in required_fields:
            if field not in data:
                return False
            if data[field] is None or data[field] == "":
                return False
        return True
    
    return _validate


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_test_environment():
    """Automatically cleanup test environment after each test."""
    yield
    
    # Clean up any temporary files or resources
    import gc
    gc.collect()
    
    # Reset environment variables
    test_env_vars = ["TESTING", "LOG_LEVEL", "QT_QPA_PLATFORM"]
    for var in test_env_vars:
        if var in os.environ and var != "TESTING":
            del os.environ[var]


# Skip markers for platform-specific tests
def pytest_runtest_setup(item):
    """Setup function to handle platform-specific test skipping."""
    # Skip Windows-specific tests on non-Windows platforms
    if item.get_closest_marker("platform_windows") and not sys.platform.startswith("win"):
        pytest.skip("Windows-specific test")
    
    # Skip macOS-specific tests on non-macOS platforms
    if item.get_closest_marker("platform_macos") and sys.platform != "darwin":
        pytest.skip("macOS-specific test")
    
    # Skip Linux-specific tests on non-Linux platforms
    if item.get_closest_marker("platform_linux") and not sys.platform.startswith("linux"):
        pytest.skip("Linux-specific test")
    
    # Skip network tests if no network access
    if item.get_closest_marker("network") and os.environ.get("SKIP_NETWORK_TESTS"):
        pytest.skip("Network tests disabled")
    
    # Skip external service tests if not configured
    if item.get_closest_marker("external") and os.environ.get("SKIP_EXTERNAL_TESTS"):
        pytest.skip("External service tests disabled")