# Development Rules & Standards

## Core Principles

### 1. Project Structure Adherence
**ALWAYS** follow the established project structure. Never place files in incorrect locations.

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

Remember: **Always follow the established project structure and internationalize everything!**