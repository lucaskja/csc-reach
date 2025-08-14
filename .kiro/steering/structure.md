# Project Structure & Organization

## Root Directory Layout
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

## Source Code Organization (`src/multichannel_messaging/`)
- **`main.py`** - Application entry point
- **`core/`** - Business logic and core functionality
  - `application_manager.py` - Application lifecycle management
  - `config_manager.py` - Configuration handling
  - `csv_processor.py` - CSV file processing
  - `template_manager.py` - Template management system
  - `i18n_manager.py` - Internationalization
  - `models.py` - Data models and structures
- **`gui/`** - User interface components
  - `main_window.py` - Primary application window
  - `*_dialog.py` - Modal dialogs for specific features
- **`services/`** - External integrations
  - `email_service.py` - Email functionality
  - `outlook_*.py` - Platform-specific Outlook integration
  - `whatsapp_*.py` - WhatsApp service implementations
  - `api_clients/` - External API clients
- **`utils/`** - Utility modules
  - `logger.py` - Logging configuration
  - `exceptions.py` - Custom exception classes
  - `platform_utils.py` - Platform-specific utilities
- **`localization/`** - Translation files (JSON format)

## Test Organization (`tests/`)
- **`unit/`** - Fast, isolated unit tests
- **`integration/`** - End-to-end workflow tests
- **`performance/`** - Performance and load tests
- **`gui/`** - GUI-specific tests
- **`fixtures/`** - Test data and sample files
- **`conftest.py`** - Shared test configuration

## Documentation Structure (`docs/`)
- **`user/`** - End-user documentation and guides
- **`dev/`** - Developer documentation
- **`api/`** - API documentation
- **`summaries/`** - Implementation summaries and changelogs

## Build Scripts (`scripts/`)
- **`build/`** - Build system scripts
- **`dev/`** - Development utilities
- **`deploy/`** - Deployment scripts

## File Placement Rules
- **Tests**: ALWAYS place in `tests/unit/`, `tests/integration/`, or `tests/fixtures/`
- **Documentation**: ALWAYS place in appropriate `docs/` subdirectory
- **Source Code**: ALWAYS place in `src/multichannel_messaging/` structure
- **Scripts**: ALWAYS place in `scripts/` with appropriate subdirectory
- **Never place test files in project root**

## Architecture Patterns
- **MVC Pattern**: Clear separation of concerns
- **Service Layer**: External integrations abstracted
- **Configuration Management**: Centralized config system
- **Internationalization**: Comprehensive i18n support
- **Error Handling**: Graceful error recovery
- **Logging**: Comprehensive logging system

## Naming Conventions
- **Files**: snake_case for Python files
- **Classes**: PascalCase
- **Functions/Variables**: snake_case
- **Constants**: UPPER_SNAKE_CASE
- **Modules**: Short, descriptive names in snake_case

## Import Organization
- Standard library imports first
- Third-party imports second
- Local application imports last
- Relative imports for same-package modules

## Import Patterns
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

## Test File Naming
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

## Documentation Structure
```
docs/
├── user/                    # End-user documentation
├── dev/                     # Developer documentation
├── api/                     # API reference
└── summaries/               # Implementation summaries
```