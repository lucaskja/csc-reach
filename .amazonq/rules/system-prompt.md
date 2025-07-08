# CSC-Reach System Prompt for Amazon Q

## Project Overview
CSC-Reach is a cross-platform desktop application for bulk email communication through Microsoft Outlook integration. It processes customer data from CSV files and utilizes Outlook's native functionality for professional email campaigns.

## Core Principles

### 1. Project Structure Adherence
**ALWAYS** follow the established project structure:

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

### 2. File Placement Rules
- **Tests**: ALWAYS place in `tests/unit/`, `tests/integration/`, or `tests/fixtures/`
- **Documentation**: ALWAYS place in appropriate `docs/` subdirectory
- **Source Code**: ALWAYS place in `src/multichannel_messaging/` structure
- **Scripts**: ALWAYS place in `scripts/` with appropriate subdirectory
- **Never place test files in project root**

### 3. Internationalization Requirements
- **Everything must be internationalized**
- Support English (en), Portuguese (pt), and Spanish (es)
- Use the existing i18n system: `from ..core.i18n_manager import get_i18n_manager`
- All user-facing text must use `i18n.tr("key")` or `self.i18n_manager.tr("key")`
- Add translations to all three language files in `src/multichannel_messaging/localization/`

### 4. Code Quality Standards
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Include comprehensive docstrings
- Implement proper error handling
- Add logging using the project's logger: `from ..utils.logger import get_logger`

### 5. Testing Requirements
- Unit tests for all new functionality
- Integration tests for complex workflows
- Place test files in correct `tests/` subdirectories
- Use descriptive test names and comprehensive assertions
- Include test fixtures in `tests/fixtures/` when needed

### 6. Documentation Standards
- Update README.md for user-facing changes
- Create technical documentation in `docs/dev/`
- Add API documentation in `docs/api/`
- Create implementation summaries in `docs/summaries/`
- Keep documentation current with code changes

## Technology Stack

### Core Technologies
- **Python 3.8+**: Core application language
- **PySide6**: Cross-platform GUI framework
- **Microsoft Outlook Integration**:
  - **macOS**: AppleScript via ScriptingBridge
  - **Windows**: COM automation via pywin32

### Key Components
- **ConfigManager**: Application configuration management
- **I18nManager**: Internationalization and localization
- **TemplateManager**: Template management system
- **EmailService**: Outlook integration service
- **CSVProcessor**: CSV file processing

### Build System
- **PyInstaller**: Executable creation
- **Cross-platform**: macOS (.app/.dmg) and Windows (.exe)
- **Automated builds**: Via scripts in `scripts/build/`

## Development Workflow

### 1. Feature Development
1. Create feature branch from main
2. Implement functionality in appropriate `src/` directory
3. Add comprehensive tests in `tests/` directory
4. Add internationalization for all user-facing text
5. Update documentation in `docs/`
6. Test on both macOS and Windows if applicable

### 2. Code Review Checklist
- [ ] Code follows project structure
- [ ] All user-facing text is internationalized
- [ ] Tests are in correct `tests/` directories
- [ ] Documentation is updated
- [ ] Error handling is implemented
- [ ] Logging is added where appropriate
- [ ] Type hints are used
- [ ] Docstrings are comprehensive

### 3. Commit Standards
- Use conventional commit messages
- Include scope when applicable: `feat(templates): add template library`
- Reference issues when applicable
- Keep commits atomic and focused

## Current Status

### Completed Features
- ✅ Email MVP with Outlook integration
- ✅ Cross-platform support (macOS + Windows)
- ✅ CSV import with automatic column detection
- ✅ Template Management System with library
- ✅ Complete internationalization (en/pt/es)
- ✅ Professional build system

### Architecture Patterns
- **MVC Pattern**: Clear separation of concerns
- **Service Layer**: External integrations abstracted
- **Configuration Management**: Centralized config system
- **Internationalization**: Comprehensive i18n support
- **Error Handling**: Graceful error recovery
- **Logging**: Comprehensive logging system

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

## Quick Reference

### Import Patterns
```python
# i18n
from ..core.i18n_manager import get_i18n_manager

# Logging
from ..utils.logger import get_logger

# Configuration
from ..core.config_manager import ConfigManager

# Models
from ..core.models import MessageTemplate, Customer
```

### Test File Naming
```
tests/
├── unit/
│   ├── test_template_manager.py
│   ├── test_i18n_manager.py
│   └── test_csv_processor.py
├── integration/
│   ├── test_template_workflow.py
│   └── test_email_integration.py
└── fixtures/
    ├── sample_templates.json
    └── test_customers.csv
```

### Documentation Structure
```
docs/
├── user/                    # End-user documentation
├── dev/                     # Developer documentation
├── api/                     # API reference
└── summaries/               # Implementation summaries
```

Remember: **Always follow the established project structure and internationalize everything!**
