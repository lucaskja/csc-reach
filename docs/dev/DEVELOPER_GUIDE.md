# CSC-Reach Developer Guide

## Project Structure

```
sbai-dg-wpp/                           # Clean root with only essentials
├── README.md                          # Main project documentation
├── LICENSE                            # License file
├── pyproject.toml                     # Modern Python packaging
├── .gitignore                         # Git ignore rules
├── Makefile                           # Build automation
├── 
├── src/                               # Source code
│   └── multichannel_messaging/        # Main package
│       ├── __init__.py
│       ├── main.py
│       ├── core/                      # Business logic
│       ├── gui/                       # User interface
│       ├── services/                  # External integrations
│       ├── utils/                     # Utilities
│       └── localization/              # Translations
│
├── tests/                             # All tests
│   ├── unit/                          # Unit tests
│   ├── integration/                   # Integration tests
│   └── fixtures/                      # Test data
│
├── docs/                              # All documentation
│   ├── user/                          # User guides
│   ├── dev/                           # Developer docs
│   ├── api/                           # API documentation
│   └── summaries/                     # Implementation summaries
│
├── scripts/                           # Build and utility scripts
│   ├── build/                         # Build scripts
│   ├── dev/                           # Development utilities
│   └── deploy/                        # Deployment scripts
│
├── assets/                            # Static resources
│   ├── icons/
│   └── templates/
│
├── config/                            # Configuration files
│   └── default_config.yaml
│
└── build/                             # Build outputs (gitignored)
    ├── dist/                          # Distribution files
    ├── temp/                          # Temporary build files
    └── logs/                          # Build logs
```

## Development Setup

### Prerequisites
- Python 3.8+
- Git
- Microsoft Outlook (for testing)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sbai-dg-wpp
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**
   ```bash
   make install-dev
   # or
   pip install -e ".[dev]"
   ```

4. **Run the application**
   ```bash
   make run
   # or
   python src/multichannel_messaging/main.py
   ```

## Development Workflow

### Code Quality
```bash
# Format code
make format

# Run linting
make lint

# Type checking
make type-check

# Run all quality checks
make format lint type-check
```

### Testing
```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run integration tests only
make test-integration

# Run with coverage
make test-coverage
```

### Building

#### macOS
```bash
# Build app
make build-macos

# Create DMG installer
make dmg
```

#### Windows
```bash
# Build executable
make build-windows
```

## Architecture

### Core Components

1. **GUI Layer** (`src/multichannel_messaging/gui/`)
   - Main window and dialogs
   - PySide6-based interface
   - Cross-platform UI components

2. **Business Logic** (`src/multichannel_messaging/core/`)
   - CSV processing
   - Configuration management
   - Data models
   - Internationalization

3. **Services** (`src/multichannel_messaging/services/`)
   - Outlook integration (macOS/Windows)
   - WhatsApp Web automation
   - External API integrations

4. **Utilities** (`src/multichannel_messaging/utils/`)
   - Logging
   - Exception handling
   - Platform utilities

### Key Design Patterns

- **MVC Architecture**: Clear separation of concerns
- **Service Layer**: External integrations abstracted
- **Factory Pattern**: Platform-specific service creation
- **Observer Pattern**: Progress tracking and notifications

## Build System

### PyInstaller Configuration

The build system uses PyInstaller with custom spec files:
- `scripts/build/build_macos.spec` - macOS configuration
- `scripts/build/build_windows.spec` - Windows configuration

### Build Outputs

All build outputs are organized in the `build/` directory:
- `build/dist/` - Final distribution files
- `build/temp/` - Temporary build files
- `build/logs/` - Build logs and error reports

## Testing Strategy

### Unit Tests
- Test individual components in isolation
- Mock external dependencies
- Focus on business logic

### Integration Tests
- Test component interactions
- Test with real external services (when safe)
- End-to-end workflow testing

### Test Data
- Sample CSV files in `tests/fixtures/`
- Mock configurations for testing
- Isolated test environments

## Contributing

### Code Style
- Follow PEP 8
- Use Black for formatting
- Type hints required
- Comprehensive docstrings

### Commit Messages
- Use conventional commit format
- Include scope when relevant
- Reference issues when applicable

### Pull Request Process
1. Create feature branch
2. Implement changes with tests
3. Ensure all quality checks pass
4. Update documentation
5. Submit pull request

## Deployment

### Release Process
1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release builds
4. Test on target platforms
5. Create GitHub release
6. Upload distribution files

### Distribution
- macOS: `.dmg` installer
- Windows: `.exe` executable or installer
- Cross-platform: Python package

## Troubleshooting

### Common Development Issues

1. **Import errors**
   - Ensure virtual environment is activated
   - Check PYTHONPATH includes src/

2. **Build failures**
   - Check build logs in `build/logs/`
   - Verify all dependencies are installed
   - Ensure PyInstaller spec files are updated

3. **Test failures**
   - Check test data in `tests/fixtures/`
   - Verify mock configurations
   - Ensure external services are available

### Debug Mode
```bash
# Run with debug logging
PYTHONPATH=src python -m multichannel_messaging.main --debug

# Run tests with verbose output
pytest -v --tb=long
```

## Resources

- [PySide6 Documentation](https://doc.qt.io/qtforpython/)
- [PyInstaller Manual](https://pyinstaller.readthedocs.io/)
- [Python Packaging Guide](https://packaging.python.org/)
- [Project Documentation](../README.md)
