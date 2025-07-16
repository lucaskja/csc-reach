# Project Structure & Organization

## Root Directory Layout
```
├── src/multichannel_messaging/     # Main application package
├── tests/                          # All test files
├── docs/                           # Documentation
├── scripts/                        # Build and utility scripts
├── assets/                         # Static resources (icons, templates)
├── config/                         # Configuration files
├── build/                          # Build outputs (gitignored)
├── pyproject.toml                  # Modern Python packaging
├── Makefile                        # Build automation
└── build.py                        # Simple build wrapper
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

## Architecture Patterns
- **Separation of Concerns**: Clear separation between GUI, business logic, and services
- **Cross-Platform Abstraction**: Platform-specific code isolated in service layer
- **Configuration-Driven**: Extensive use of configuration files for customization
- **Modular Design**: Each component has a single responsibility
- **Error Handling**: Comprehensive exception handling with custom exception types
- **Logging**: Structured logging throughout the application
- **Testing**: Comprehensive test coverage with multiple test types

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