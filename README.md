# CSC-Reach - Email Communication Platform

## Overview

CSC-Reach is a cross-platform desktop application designed to facilitate bulk email communication through Microsoft Outlook integration. It processes customer data from CSV files and utilizes Outlook's native functionality for professional email campaigns. The application runs locally on users' machines, available for both Windows and macOS platforms.

This system caters to businesses needing to streamline their email communication processes with professional templates, automated personalization, and real-time sending progress tracking.

## 🎉 Current Status: Email Platform Completed

### ✅ **Fully Implemented Features:**
- **Multi-Format Data Import**: Support for CSV, Excel (XLSX/XLS), JSON, JSONL, TSV, and delimited files with automatic format detection, column mapping, and data validation
- **Email Template System**: Subject/content editing with variable substitution (`{name}`, `{company}`)
- **Cross-Platform Outlook Integration**: 
  - **macOS**: AppleScript integration with Microsoft Outlook
  - **Windows**: COM (Component Object Model) integration
- **Bulk Email Sending**: Background processing with real-time progress tracking
- **Professional GUI**: Menu bar, toolbar, recipient selection, email preview
- **Configuration Management**: Cross-platform settings with YAML/JSON support
- **Build System**: Complete packaging for both macOS (.app/.dmg) and Windows (.exe)
- **Professional Branding**: Custom application icon and professional UI design

### 🚀 **Ready for Production Use:**
CSC-Reach is fully functional and ready for production use on both platforms:
- **macOS**: Tested and packaged as `.app` bundle with `.dmg` installer
- **Windows**: Complete implementation ready for testing and packaging

## Key Features

- **Multi-format file processing** - CSV, Excel, JSON, JSONL, TSV, and delimited files (customer name, company name, telephone number, email)
- **Email composition and sending** via Outlook integration
- **Cross-platform Outlook integration** (macOS AppleScript + Windows COM)
- **Professional Template Management System** with library, categories, and import/export
- **Multi-language support** (Portuguese, Spanish, English) with complete internationalization
- **Cross-platform compatibility** (Windows and macOS)
- **Daily messaging quota management** (100 per day per user) - *Framework ready*
- **User-friendly interface** for multi-format file input and template customization
- **Real-time progress tracking** and comprehensive logging
- **Email preview functionality** before sending
- **Draft email creation** for testing and review

### Supported File Formats

CSC-Reach supports importing customer data from multiple file formats:

#### Text-Based Formats
- **CSV** (Comma-Separated Values) - `.csv`, `.txt`
- **TSV** (Tab-Separated Values) - `.tsv`
- **Pipe-delimited** - `.txt` with `|` delimiter
- **Semicolon-delimited** - `.txt` with `;` delimiter

#### Spreadsheet Formats
- **Excel XLSX** - `.xlsx` (modern Excel format)
- **Excel XLS** - `.xls` (legacy Excel format)

#### JSON Formats
- **JSON** - `.json` (array of objects)
- **JSONL/NDJSON** - `.jsonl`, `.ndjson` (JSON Lines format)

**Key Benefits:**
- **Automatic Format Detection** - No need to specify file type
- **Intelligent Column Mapping** - Automatically maps columns to required fields
- **Robust Encoding Detection** - Handles various text encodings
- **Memory-Efficient Streaming** - Processes large files without memory issues
- **Comprehensive Validation** - Detailed error reporting and suggestions

### Template Management Features
- **Template Library**: Organize templates by categories (Welcome, Follow-up, Promotional, Support, General)
- **Multi-Channel Templates**: Create templates for email, WhatsApp, or both channels
- **Import/Export**: Share templates between installations or create backups
- **Real-time Preview**: See how templates will look with actual customer data
- **Search & Filter**: Quickly find templates by name, content, or category
- **Usage Analytics**: Track template popularity and usage statistics
- **Automatic Backups**: Templates are automatically backed up before modifications
- **Variable Substitution**: Use {name}, {company}, etc. for personalized messages

## Technologies Used

- **Python 3.8+** - Core application language
- **PySide6** - Cross-platform GUI framework
- **Microsoft Outlook Integration**:
  - **macOS**: AppleScript via ScriptingBridge
  - **Windows**: COM automation via pywin32
- **Multi-Format Processing**: pandas with automatic format detection, encoding detection, and intelligent column mapping
- **Configuration**: YAML/JSON with cross-platform storage
- **Logging**: colorlog with file rotation
- **Build System**: PyInstaller for executable creation
- **Packaging**: DMG for macOS, executable distribution for Windows

## System Requirements

### Windows
- Windows 10 or later
- Microsoft Outlook installed and configured
- 4GB RAM minimum
- 2GHz processor or better
- 500MB free disk space

### macOS
- macOS 10.14 or later
- Microsoft Outlook for Mac installed and configured
- 4GB RAM minimum
- 2GHz processor or better
- 500MB free disk space

## Installation

### For End Users (Non-Technical)

**📖 Complete Installation Guides for Everyone:**

#### Windows Users (Most Common)
- **[Windows Installation Guide](docs/user/windows_installation_guide.md)** - Step-by-step installation for Windows 10/11
- **[Quick Start Guide](docs/user/quick_start_guide.md)** - Get started in 5 minutes
- **[User Manual](docs/user/user_manual.md)** - Complete guide to using CSC-Reach
- **[Troubleshooting Guide](docs/user/troubleshooting_guide.md)** - Fix common problems

#### Mac Users
- **[macOS Installation Guide](docs/user/macos_installation_guide.md)** - Step-by-step installation for macOS

> **💡 These guides are written for non-technical users** with simple language, screenshots descriptions, and step-by-step instructions.

### For Developers

#### macOS

#### Option 1: Download Pre-built App (Recommended)
1. Download `CSC-Reach-macOS.dmg` from the releases page
2. Open the DMG file and drag the application to your Applications folder
3. Right-click on the application and select "Open" to bypass macOS security restrictions on the first run

#### Option 2: Build from Source
```bash
# Clone the repository
git clone <repository-url>
cd sbai-dg-wpp

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Build the app
python scripts/build_macos.py

# Create DMG (optional)
python scripts/create_dmg.py
```

### Windows

#### Option 1: Download Pre-built Executable (Coming Soon)
1. Download `CSC-Reach-Windows.zip` from the releases page
2. Extract the ZIP file to your desired location
3. Run `CSC-Reach.exe`

#### Option 2: Build from Source
```cmd
# Clone the repository
git clone <repository-url>
cd sbai-dg-wpp

# Set up virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Build the executable
python scripts/build_windows.py
```

## Configuration

### Microsoft Outlook Setup
The application automatically detects and integrates with your installed Microsoft Outlook:

- **macOS**: Uses AppleScript to control Outlook for Mac
- **Windows**: Uses COM automation to control Outlook for Windows

Ensure Outlook is installed and configured with your email account before using the application.

### WhatsApp Business API Setup (Future Enhancement)
1. Obtain WhatsApp Business API credentials from the WhatsApp Business Platform
2. In the application settings, navigate to "WhatsApp Configuration"
3. Enter your API key, phone number ID, and other required credentials

## Usage

### Basic Workflow
1. **Launch** the CSC-Reach application
2. **Import CSV**: Click "Import CSV" and select your customer data file
   - Required columns: name, company, phone, email
   - Automatic column detection and mapping
3. **Customize Template**: Edit the email subject and content
   - Use variables like `{name}` and `{company}` for personalization
4. **Preview**: Click "Preview Email" to see how emails will look
5. **Test**: Use "Create Draft" to create a test email in Outlook
6. **Select Recipients**: Choose which customers to send emails to
7. **Send**: Click "Send Emails" to start the bulk sending process
8. **Monitor**: Watch real-time progress and status updates

### Advanced Features
- **Email Preview**: See exactly how your personalized emails will appear
- **Draft Creation**: Create test emails in Outlook for review before bulk sending
- **Progress Tracking**: Real-time status updates with success/failure counts
- **Error Handling**: Comprehensive error reporting and recovery
- **Logging**: Detailed logs for troubleshooting and audit trails

## Development

### Project Structure

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

### Development Setup
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

# Run specific test categories
pytest tests/unit/                    # Unit tests only
pytest tests/integration/             # Integration tests only
pytest tests/unit/test_template_*     # Template management tests

# Format code
black src/ tests/

# Build for distribution
python scripts/build_macos.py    # macOS
python scripts/build_windows.py  # Windows
```

### Testing

The project includes comprehensive test coverage with proper organization:

#### Test Structure
```
tests/
├── unit/                           # Fast, isolated unit tests
│   ├── test_template_management.py # Template manager core functionality
│   ├── test_template_i18n.py      # Internationalization tests
│   └── test_*.py                   # Other unit tests
├── integration/                    # End-to-end integration tests
│   ├── test_template_workflow.py  # Complete template workflows
│   └── test_*.py                   # Other integration tests
└── fixtures/                       # Test data and fixtures
    ├── sample_templates.json       # Sample template data
    ├── test_customers.csv          # Test customer data
    └── *.json                      # Other test fixtures
```

#### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/multichannel_messaging

# Run specific test files
pytest tests/unit/test_template_management.py
pytest tests/integration/test_template_workflow.py

# Run tests with verbose output
pytest -v

# Run tests matching a pattern
pytest -k "template"
```

#### Test Categories
- **Unit Tests**: Fast, isolated tests for individual components
- **Integration Tests**: End-to-end workflow testing
- **Internationalization Tests**: Multi-language support validation
- **Template Management Tests**: Comprehensive template system testing

## Future Enhancements

### Planned Features
- **WhatsApp Business API Integration**: Complete the multi-channel functionality
- **Advanced Template Management**: Template library with import/export
- **Quota Management System**: Daily limits with reset scheduling
- **Multi-language UI**: Complete Portuguese and Spanish translations
- **Reporting Dashboard**: Advanced analytics and sending reports
- **Scheduled Sending**: Queue messages for future delivery
- **Contact Management**: Built-in customer database

### Technical Roadmap
- **Windows Testing**: Complete testing on Windows platform
- **Code Signing**: Implement proper code signing for both platforms
- **Auto-Updates**: Implement automatic update mechanism
- **Performance Optimization**: Optimize for larger datasets
- **Cloud Integration**: Optional cloud backup and sync

## Support and Documentation

- **User Manual**: Comprehensive guide with screenshots
- **API Documentation**: Technical documentation for developers
- **Troubleshooting Guide**: Common issues and solutions
- **Build Guide**: Complete packaging and distribution instructions

## Limitations

- Daily limit of 100 messages per user (configurable)
- Requires local installation of Microsoft Outlook
- WhatsApp functionality pending Business API integration
- Adheres to email anti-spam regulations and best practices

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Changelog

### Version 1.0.0 (Current)
- ✅ Complete Email MVP implementation
- ✅ Cross-platform Outlook integration (macOS + Windows)
- ✅ Professional GUI with real-time progress tracking
- ✅ CSV import with automatic column detection
- ✅ Email template system with variable substitution
- ✅ Build system for both macOS and Windows
- ✅ Comprehensive error handling and logging

### Upcoming Version 1.1.0
- 🔄 WhatsApp Business API integration
- 🔄 Advanced template management
- 🔄 Multi-language UI support
- 🔄 Quota management system