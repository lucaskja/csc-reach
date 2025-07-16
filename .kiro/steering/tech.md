# Technology Stack & Build System

## Core Technologies
- **Python 3.8+** - Main application language
- **PySide6** - Cross-platform GUI framework (Qt-based)
- **pandas** - CSV processing and data manipulation
- **PyYAML** - Configuration management
- **colorlog** - Enhanced logging with color support

## Platform-Specific Dependencies
### Windows
- **pywin32** - COM automation for Outlook integration
- **PyInstaller** - Executable creation

### macOS
- **pyobjc-framework-Cocoa** - macOS system integration
- **pyobjc-framework-ScriptingBridge** - AppleScript integration for Outlook
- **DMG creation tools** - macOS installer packaging

## Development Tools
- **pytest** - Testing framework with Qt support (`pytest-qt`)
- **black** - Code formatting (88 char line length)
- **flake8** - Linting with docstring and import order checks
- **mypy** - Type checking
- **isort** - Import sorting
- **coverage** - Test coverage reporting

## Build System
### Quick Build Commands
```bash
# Build everything
python build.py
make build

# Platform-specific builds
python build.py macos
python build.py windows
make build-macos
make build-windows

# Clean builds
python build.py clean
make build-clean
```

### Development Commands
```bash
# Setup development environment
pip install -e ".[dev]"
make install-dev

# Run tests
pytest
make test
make test-unit
make test-integration

# Code quality
make lint
make format
make type-check

# Run application
python src/multichannel_messaging/main.py
make run
```

## Configuration Management
- **YAML/JSON** configuration files
- Cross-platform config directory detection
- User-specific and application-wide settings
- Environment-specific configuration support

## Packaging & Distribution
- **PyInstaller** for executable creation
- **DMG** creation for macOS distribution
- **ZIP** packaging for Windows distribution
- Cross-platform build verification and testing