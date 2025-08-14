# Technology Stack & Build System

## Core Technologies
- **Python 3.8+**: Core application language
- **PySide6**: Cross-platform GUI framework
- **Microsoft Outlook Integration**:
  - **macOS**: AppleScript via ScriptingBridge
  - **Windows**: COM automation via pywin32

## Key Components
- **ConfigManager**: Application configuration management
- **I18nManager**: Internationalization and localization
- **TemplateManager**: Template management system
- **EmailService**: Outlook integration service
- **CSVProcessor**: CSV file processing

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

## Code Quality Standards
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Include comprehensive docstrings
- Implement proper error handling
- Add logging using the project's logger: `from ..utils.logger import get_logger`

## Testing Requirements
- Unit tests for all new functionality
- Integration tests for complex workflows
- Place test files in correct `tests/` subdirectories
- Use descriptive test names and comprehensive assertions
- Include test fixtures in `tests/fixtures/` when needed

## Common Mistakes to Avoid

### ❌ Don't Do
- Place test files in project root
- Hard-code user-facing strings
- Skip internationalization
- Ignore project structure
- Create files without proper documentation
- Skip error handling
- Forget to update README.md

### ✅ Do
- Follow established project structure
- Internationalize all user-facing text
- Place tests in correct directories
- Update documentation
- Add comprehensive error handling
- Use existing logging system
- Follow code quality standards