# CSC-Reach - Multi-Channel Bulk Messaging System

## Overview

CSC-Reach is a professional cross-platform desktop application designed to revolutionize business communication through intelligent multi-channel messaging. Built with Python and PySide6, it seamlessly integrates with Microsoft Outlook and WhatsApp Web to deliver personalized bulk messaging campaigns with enterprise-grade reliability and performance.

**What problem does it solve?**
- Eliminates manual, time-consuming email and messaging campaigns
- Provides unified multi-channel communication (Email + WhatsApp)
- Offers intelligent data processing with automatic column mapping
- Delivers professional template management with dynamic personalization
- Ensures cross-platform compatibility (Windows/macOS) with native integrations

**Technology Stack:**
- **Frontend**: PySide6 (Qt) with professional UI, themes, and accessibility
- **Backend**: Python 3.8+ with MVC architecture and robust error handling
- **Integrations**: Microsoft Outlook (COM/AppleScript), WhatsApp Web automation
- **Data Processing**: pandas, openpyxl, chardet for multi-format support
- **Configuration**: YAML/JSON with cross-platform persistence

## Features

- **Multi-Channel Communication** - Unified platform for Email (Outlook) and WhatsApp messaging
- **Multi-Format Data Processing** - CSV, Excel, JSON, JSONL, TSV with intelligent column mapping
- **Cross-Platform Outlook Integration** - Native integration for both macOS (AppleScript) and Windows (COM)
- **WhatsApp Web Automation** - Complete browser automation with multi-message support
- **Professional Template Management** - Library with categories, import/export, and dynamic variable substitution
- **Multi-Language Support** - Complete internationalization (Portuguese, Spanish, English)
- **Real-Time Progress Tracking** - Live monitoring with comprehensive logging and analytics
- **Enterprise-Grade Configuration** - YAML/JSON configuration with user preferences
- **Accessibility & Navigation** - Full accessibility support with keyboard navigation
- **Theme Management** - Professional dark/light themes with customization options

## Prerequisites

### Required AWS Setup
This application does not require AWS resources as it operates entirely on local systems with native integrations.

### Development Environment

#### System Requirements
- **Windows**: Windows 10 or later
- **macOS**: macOS 10.14 (Mojave) or later
- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 500MB for installation
- **Processor**: 2GHz or better

#### Required Software
- **Microsoft Outlook**: Must be installed and configured with email account
  - Windows: Outlook for Windows (Office 365 or standalone)
  - macOS: Microsoft Outlook for Mac
- **Python 3.8+**: For development (not required for end users)
- **Web Browser**: Chrome, Firefox, or Safari for WhatsApp Web automation

## Architecture Diagram

The architecture follows a layered approach with clear separation of concerns:

- **User Interface Layer**: PySide6-based GUI with main window, template management, and progress tracking
- **Core Logic Layer**: Data processing, template engine, variable management, and configuration
- **Services Layer**: Email and WhatsApp service abstractions for platform-specific implementations
- **External Systems**: Integration with Microsoft Outlook and WhatsApp Web

## Project Components

### Core Components

#### Data Processing Engine (`src/multichannel_messaging/core/`)
- **CSVProcessor**: Multi-format file processing with automatic detection
- **ColumnMapper**: Intelligent column mapping and data validation
- **DataValidator**: Comprehensive data validation with error reporting

#### Template Management System (`src/multichannel_messaging/core/`)
- **TemplateManager**: CRUD operations for message templates
- **DynamicVariableManager**: Variable substitution and management
- **WhatsAppTemplateManager**: WhatsApp-specific template handling

#### User Interface (`src/multichannel_messaging/gui/`)
- **MainWindow**: Primary application interface with menu and toolbar
- **TemplateLibraryDialog**: Professional template management interface
- **ProgressDialog**: Real-time progress tracking with analytics
- **PreferencesDialog**: User settings and configuration management

#### Platform Services (`src/multichannel_messaging/services/`)
- **EmailService**: Abstract email service interface
- **OutlookWindows**: Windows COM integration for Outlook
- **OutlookMacOS**: macOS AppleScript integration for Outlook
- **WhatsAppWebService**: Browser automation for WhatsApp Web

## Next Steps

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

## Clean Up

Since this application runs entirely locally and doesn't deploy any cloud resources, cleanup involves:

1. **Uninstall Application**:
   - **Windows**: Use "Add or Remove Programs" or delete the application folder
   - **macOS**: Drag the application from Applications folder to Trash

2. **Remove User Data** (optional):
   - **Windows**: `%APPDATA%/CSC-Reach/`
   - **macOS**: `~/Library/Application Support/CSC-Reach/`

3. **Clear Logs** (optional):
   - Application logs are stored in the user data directory
   - SQLite database with message history can be deleted if desired

## Troubleshooting

### Common Issues

#### Microsoft Outlook Integration
- **Issue**: "Outlook not found" error
- **Solution**: Ensure Microsoft Outlook is installed and configured with an email account
- **Windows**: Verify COM registration with `regsvr32 outlook.exe`
- **macOS**: Check automation permissions in System Preferences

#### macOS Permissions
- **Issue**: "Not authorized to send Apple events"
- **Solution**: Grant automation permissions:
  1. System Preferences → Security & Privacy → Privacy → Automation
  2. Find CSC-Reach and enable Microsoft Outlook

#### File Import Issues
- **Issue**: "Cannot read file" or encoding errors
- **Solution**: 
  - Ensure file is not open in another application
  - Try saving as UTF-8 encoded CSV
  - Use the built-in column mapping dialog for complex files

#### Performance Issues
- **Issue**: Slow processing of large files
- **Solution**:
  - Process files in smaller batches (< 1000 records)
  - Close other applications to free memory
  - Use SSD storage for better I/O performance

### Debug Mode
Enable debug logging by setting environment variable:
```bash
export CSC_REACH_DEBUG=1  # macOS/Linux
set CSC_REACH_DEBUG=1     # Windows
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
