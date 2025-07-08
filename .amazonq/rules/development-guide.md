# CSC-Reach Development Guide

## Quick Start for Developers

### Environment Setup
```bash
# Clone and setup
git clone <repository-url>
cd sbai-dg-wpp
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install in development mode
pip install -e ".[dev]"

# Run the application
python src/multichannel_messaging/main.py

# Run tests
pytest tests/

# Format code
black src/ tests/

# Build for distribution
python scripts/build/build_macos.py    # macOS
python scripts/build/build_windows.py  # Windows
```

## Development Rules

### 1. File Organization
- **Source Code**: `src/multichannel_messaging/`
- **Tests**: `tests/unit/`, `tests/integration/`, `tests/fixtures/`
- **Documentation**: `docs/user/`, `docs/dev/`, `docs/api/`, `docs/summaries/`
- **Scripts**: `scripts/build/`, `scripts/dev/`, `scripts/deploy/`
- **Assets**: `assets/icons/`, `assets/templates/`
- **Config**: `config/default_config.yaml`

### 2. Internationalization (i18n)
**MANDATORY**: All user-facing text must be internationalized

```python
# Import i18n manager
from ..core.i18n_manager import get_i18n_manager

# In class constructor
self.i18n = get_i18n_manager()

# Use translations
button_text = self.i18n.tr("save_template")
message = self.i18n.tr("template_saved_success", name=template.name)

# Add to translation files
# src/multichannel_messaging/localization/en.json
# src/multichannel_messaging/localization/pt.json  
# src/multichannel_messaging/localization/es.json
```

### 3. Testing Standards
```python
# Unit test example - tests/unit/test_template_manager.py
import pytest
from src.multichannel_messaging.core.template_manager import TemplateManager

class TestTemplateManager:
    def test_save_template_success(self):
        # Test implementation
        pass

# Integration test example - tests/integration/test_template_workflow.py
class TestTemplateWorkflow:
    def test_complete_template_creation_workflow(self):
        # Test implementation
        pass

# Test fixtures - tests/fixtures/sample_templates.json
{
    "templates": [
        {
            "id": "test_template",
            "name": "Test Template",
            "content": "Hello {name}"
        }
    ]
}
```

### 4. Logging Standards
```python
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Usage
logger.info("Template saved successfully")
logger.error(f"Failed to save template: {error}")
logger.debug("Debug information for troubleshooting")
```

### 5. Error Handling
```python
try:
    # Operation that might fail
    result = risky_operation()
    logger.info("Operation completed successfully")
    return result
except SpecificException as e:
    logger.error(f"Specific error occurred: {e}")
    # Handle specific error
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Handle general error
    raise
```

## Code Quality Checklist

### Before Committing
- [ ] Code follows project structure
- [ ] All user-facing text is internationalized (en/pt/es)
- [ ] Tests are in correct `tests/` directories
- [ ] Documentation is updated
- [ ] Error handling is implemented
- [ ] Logging is added where appropriate
- [ ] Type hints are used
- [ ] Docstrings are comprehensive
- [ ] Code is formatted with black
- [ ] Tests pass

### Component Development
```python
# Example component structure
class NewComponent:
    """Component description with proper docstring."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize component with dependencies."""
        self.config_manager = config_manager
        self.i18n = get_i18n_manager()
        self.logger = get_logger(__name__)
        
    def public_method(self, param: str) -> bool:
        """
        Public method with type hints and docstring.
        
        Args:
            param: Description of parameter
            
        Returns:
            Description of return value
            
        Raises:
            ValidationError: When validation fails
        """
        try:
            # Implementation
            self.logger.info("Operation completed")
            return True
        except Exception as e:
            self.logger.error(f"Operation failed: {e}")
            raise
```

## Architecture Guidelines

### 1. Separation of Concerns
- **Core**: Business logic and data models
- **GUI**: User interface components
- **Services**: External integrations (Outlook, WhatsApp)
- **Utils**: Utility functions and helpers

### 2. Dependency Injection
```python
# Good: Inject dependencies
class EmailService:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager

# Bad: Create dependencies internally
class EmailService:
    def __init__(self):
        self.config_manager = ConfigManager()  # Hard to test
```

### 3. Configuration Management
```python
# Use centralized configuration
from ..core.config_manager import ConfigManager

config = ConfigManager()
setting = config.get_setting("email.timeout", default=30)
```

## Testing Guidelines

### 1. Test Organization
```
tests/
├── unit/                           # Fast, isolated tests
│   ├── core/
│   │   ├── test_template_manager.py
│   │   ├── test_i18n_manager.py
│   │   └── test_config_manager.py
│   ├── gui/
│   │   └── test_template_dialog.py
│   └── services/
│       └── test_email_service.py
├── integration/                    # Slower, end-to-end tests
│   ├── test_template_workflow.py
│   └── test_email_integration.py
└── fixtures/                       # Test data
    ├── sample_templates.json
    ├── test_customers.csv
    └── config_test.yaml
```

### 2. Test Naming Convention
```python
def test_should_save_template_when_valid_data_provided():
    """Test names should describe the expected behavior."""
    pass

def test_should_raise_validation_error_when_name_is_empty():
    """Test error conditions clearly."""
    pass
```

### 3. Test Data Management
```python
# Use fixtures for test data
@pytest.fixture
def sample_template():
    return MessageTemplate(
        id="test_template",
        name="Test Template",
        content="Hello {name}"
    )

def test_template_rendering(sample_template):
    # Use fixture in test
    pass
```

## Documentation Standards

### 1. Code Documentation
```python
class TemplateManager:
    """
    Manages message templates with CRUD operations.
    
    Provides functionality for creating, reading, updating, and deleting
    message templates with support for categories and internationalization.
    
    Attributes:
        config_manager: Configuration management instance
        templates_dir: Directory for template storage
        
    Example:
        >>> manager = TemplateManager(config_manager)
        >>> template = manager.get_template("welcome_email")
        >>> manager.save_template(template, category_id="welcome")
    """
```

### 2. API Documentation
- Document all public methods
- Include parameter types and descriptions
- Provide usage examples
- Document exceptions that can be raised

### 3. User Documentation
- Update README.md for user-facing changes
- Create step-by-step guides in `docs/user/`
- Include screenshots for GUI features
- Provide troubleshooting information

## Build and Deployment

### 1. Build Scripts
```bash
# Development build
python scripts/dev/dev_build.py

# Production build
python scripts/build/build_macos.py
python scripts/build/build_windows.py

# Create distribution packages
python scripts/deploy/create_dmg.py      # macOS
python scripts/deploy/create_installer.py  # Windows
```

### 2. Version Management
- Update version in `pyproject.toml`
- Tag releases with semantic versioning
- Update changelog for each release
- Test builds on both platforms

## Performance Guidelines

### 1. Lazy Loading
```python
# Load resources only when needed
@property
def templates(self):
    if not hasattr(self, '_templates'):
        self._templates = self._load_templates()
    return self._templates
```

### 2. Caching
```python
# Cache expensive operations
from functools import lru_cache

@lru_cache(maxsize=128)
def get_translated_text(self, key: str, language: str) -> str:
    return self._load_translation(key, language)
```

### 3. Resource Management
```python
# Proper resource cleanup
class ResourceManager:
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
```

## Security Guidelines

### 1. Input Validation
```python
def validate_template_name(name: str) -> str:
    """Validate and sanitize template name."""
    if not name or not name.strip():
        raise ValidationError("Template name is required")
    
    # Sanitize input
    clean_name = name.strip()[:100]  # Limit length
    
    # Validate characters
    if not re.match(r'^[a-zA-Z0-9\s\-_]+$', clean_name):
        raise ValidationError("Invalid characters in template name")
    
    return clean_name
```

### 2. File Operations
```python
def safe_file_write(file_path: Path, content: str):
    """Safely write content to file."""
    # Validate path is within allowed directory
    if not file_path.is_relative_to(self.templates_dir):
        raise SecurityError("Invalid file path")
    
    # Create backup before writing
    if file_path.exists():
        backup_path = file_path.with_suffix('.bak')
        shutil.copy2(file_path, backup_path)
    
    # Write with proper permissions
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
```

## Troubleshooting

### Common Issues
1. **Import Errors**: Check PYTHONPATH and virtual environment
2. **Translation Missing**: Add to all three language files
3. **Test Failures**: Ensure tests are in correct directories
4. **Build Errors**: Check dependencies and platform requirements

### Debug Mode
```python
# Enable debug logging
import logging
logging.getLogger('multichannel_messaging').setLevel(logging.DEBUG)

# Use debugger
import pdb; pdb.set_trace()
```

Remember: **Quality over speed. Follow the established patterns and maintain high standards.**
