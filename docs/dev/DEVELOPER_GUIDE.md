# Developer Guide

## Project Overview

CSC-Reach is a cross-platform desktop application built with Python and PySide6, designed for multi-channel bulk messaging through Microsoft Outlook and WhatsApp Web integration.

## Architecture

### Design Patterns
- **MVC Architecture**: Clear separation of concerns
- **Strategy Pattern**: Platform-specific implementations
- **Observer Pattern**: Event-driven communication
- **Factory Pattern**: Dynamic component creation
- **Singleton Pattern**: Global resource management

### Core Components
- **Application Manager**: Lifecycle and coordination
- **Configuration Manager**: Settings and persistence
- **Template Manager**: Message template CRUD
- **Data Processor**: Multi-format file processing
- **Service Layer**: External integrations
- **GUI Layer**: User interface components

## Development Setup

### Prerequisites
- Python 3.8+
- Git
- Virtual environment tool
- Platform-specific dependencies:
  - **Windows**: Visual Studio Build Tools
  - **macOS**: Xcode Command Line Tools

### Environment Setup
```bash
# Clone repository
git clone <repository-url>
cd sbai-dg-wpp

# Create virtual environment
python -m venv venv

# Activate environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Verify installation
python -m pytest tests/unit/
```

### IDE Configuration
Recommended settings for VS Code:
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true
}
```

## Project Structure

```
src/multichannel_messaging/
├── core/                    # Business Logic
│   ├── application_manager.py
│   ├── config_manager.py
│   ├── template_manager.py
│   ├── csv_processor.py
│   └── message_logger.py
├── gui/                     # User Interface
│   ├── main_window.py
│   ├── template_library_dialog.py
│   └── progress_dialog.py
├── services/                # External Integrations
│   ├── email_service.py
│   ├── outlook_windows.py
│   ├── outlook_macos.py
│   └── whatsapp_web_service.py
├── utils/                   # Utilities
│   ├── logger.py
│   ├── exceptions.py
│   └── platform_utils.py
└── localization/           # Translations
    ├── en.json
    ├── pt.json
    └── es.json
```

## Development Workflow

### Code Standards
- **PEP 8** compliance via Black formatter
- **Type hints** for all public APIs
- **Docstrings** for classes and methods
- **Error handling** with custom exceptions
- **Logging** for debugging and monitoring

### Testing Strategy
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/multichannel_messaging

# Run specific test categories
pytest tests/unit/           # Unit tests
pytest tests/integration/    # Integration tests
pytest tests/gui/           # GUI tests

# Run performance tests
pytest tests/performance/
```

### Code Quality Tools
```bash
# Format code
black src/ tests/

# Check style
flake8 src/ tests/

# Type checking
mypy src/

# Security analysis
bandit -r src/

# Import sorting
isort src/ tests/
```

## Key Development Areas

### Adding New File Formats
1. Extend `CSVProcessor` class
2. Add format detection logic
3. Implement parser method
4. Add validation rules
5. Update tests

Example:
```python
class CSVProcessor:
    def _parse_xml(self, file_path: str) -> List[Dict]:
        """Parse XML file format"""
        # Implementation here
        pass
```

### Creating New Templates
1. Define template schema
2. Add to template categories
3. Implement validation
4. Create preview functionality
5. Add to template library

### Platform Integration
For new service integrations:
1. Create abstract base class
2. Implement platform-specific classes
3. Add service factory
4. Update configuration
5. Add comprehensive tests

### GUI Components
When adding new dialogs:
1. Inherit from base dialog class
2. Implement proper signal/slot connections
3. Add internationalization support
4. Include accessibility features
5. Test on both platforms

## Build System

### Development Build
```bash
# Run in development mode
python src/multichannel_messaging/main.py

# With debug logging
CSC_REACH_DEBUG=1 python src/multichannel_messaging/main.py
```

### Production Build
```bash
# Build for current platform
python scripts/build.py

# Platform-specific builds
python scripts/build_windows.py  # Windows
python scripts/build_macos.py    # macOS

# Create installers
python scripts/create_installers.py
```

### Build Configuration
Key files:
- `pyproject.toml` - Project metadata and dependencies
- `scripts/build.py` - Build automation
- `.github/workflows/` - CI/CD pipelines

## Testing Guidelines

### Unit Tests
- Test individual components in isolation
- Mock external dependencies
- Cover edge cases and error conditions
- Maintain >80% code coverage

### Integration Tests
- Test component interactions
- Use real data files for testing
- Test cross-platform functionality
- Validate end-to-end workflows

### GUI Tests
- Use pytest-qt for Qt testing
- Test user interactions
- Validate dialog behavior
- Check accessibility features

## Debugging

### Debug Mode
Enable comprehensive logging:
```bash
export CSC_REACH_DEBUG=1  # macOS/Linux
set CSC_REACH_DEBUG=1     # Windows
```

### Common Debug Scenarios
- **Outlook Integration**: Check COM/AppleScript permissions
- **File Processing**: Validate encoding and format
- **Template Rendering**: Verify variable substitution
- **GUI Issues**: Check Qt event handling

### Logging
Structured logging with different levels:
```python
from multichannel_messaging.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("Operation completed")
logger.error("Failed to process file", exc_info=True)
```

## Performance Optimization

### Memory Management
- Use generators for large datasets
- Implement proper cleanup in destructors
- Monitor memory usage during development
- Profile memory-intensive operations

### I/O Optimization
- Implement async file operations
- Use streaming for large files
- Cache frequently accessed data
- Optimize database queries

### GUI Performance
- Use lazy loading for heavy components
- Implement virtual lists for large datasets
- Debounce rapid UI updates
- Move heavy operations to background threads

## Security Considerations

### Data Protection
- Validate all user inputs
- Sanitize file paths
- Encrypt sensitive configurations
- Implement secure logging

### Integration Security
- Use official APIs only
- Validate external responses
- Implement timeout mechanisms
- Handle authentication securely

## Deployment

### Release Process
1. Update version numbers
2. Run full test suite
3. Build for all platforms
4. Create release packages
5. Update documentation
6. Tag release in Git

### Distribution
- **Windows**: MSI installer or ZIP archive
- **macOS**: DMG with app bundle
- **Code Signing**: Required for distribution

## Contributing

### Pull Request Process
1. Fork repository
2. Create feature branch
3. Implement changes with tests
4. Update documentation
5. Submit pull request

### Code Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass and coverage maintained
- [ ] Documentation updated
- [ ] No security vulnerabilities
- [ ] Cross-platform compatibility verified

### Issue Reporting
Include:
- Clear problem description
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Log files if applicable

## Resources

### Documentation
- [User Manual](../user/user_manual.md)
- [API Reference](../generated-docs/API.md)
- [Architecture Guide](../generated-docs/BACKEND.md)

### External Resources
- [PySide6 Documentation](https://doc.qt.io/qtforpython/)
- [Python Packaging Guide](https://packaging.python.org/)
- [Qt Best Practices](https://doc.qt.io/qt-6/qtquick-bestpractices.html)

### Community
- GitHub Issues for bug reports
- Discussions for feature requests
- Wiki for additional documentation
