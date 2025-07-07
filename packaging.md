# Multi-Channel Bulk Messaging System - Build and Packaging Guide

## Overview

This document describes the build and packaging process for creating distributable versions of the Multi-Channel Bulk Messaging System for both macOS and Windows platforms.

## Prerequisites

### Development Environment
- Python 3.8+ (tested with Python 3.13)
- Virtual environment with all dependencies installed
- PyInstaller 5.13.0+

### Platform-Specific Requirements

#### macOS
- macOS 10.14+ (for development and building)
- Microsoft Outlook for Mac installed
- Xcode Command Line Tools (for DMG creation)
- Code signing certificate (optional, for distribution)

#### Windows
- Windows 10+ (for building and testing)
- Microsoft Outlook for Windows installed
- Visual Studio Build Tools (for pywin32 compilation)
- Code signing certificate (optional, for distribution)

## Icon Creation

The application uses a custom icon that needs to be converted to platform-specific formats:

### Source Icon
- **Location**: `assets/icons/csc-reach.png`
- **Format**: PNG with transparency
- **Recommended Size**: 1024x1024 pixels minimum

### Platform-Specific Formats
- **macOS**: `.icns` format (created automatically)
- **Windows**: `.ico` format (created automatically)

### Automatic Icon Generation
```bash
# Create all platform-specific icons from PNG source
python scripts/create_icons.py
```

This creates:
- `assets/icons/csc-reach.icns` - macOS icon bundle
- `assets/icons/csc-reach.ico` - Windows icon file

The build scripts automatically run this step, so manual icon creation is usually not necessary.

## Build Process

### Unified Build (Recommended)

For the simplest build process, use the unified build script:

```bash
# Build for current platform with icons
python scripts/build_all.py
```

This script automatically:
- Creates platform-specific icons from the source PNG
- Builds the application for the current platform
- Creates distribution packages (DMG for macOS)
- Provides clear output and error handling

### Platform-Specific Builds

#### macOS Build

#### 1. Prepare Environment
```bash
# Activate virtual environment
source venv/bin/activate

# Ensure all dependencies are installed
pip install -e ".[dev]"

# Create platform-specific icons (optional, done automatically)
python scripts/create_icons.py
```

#### 2. Build Application
```bash
# Build the macOS app bundle
python scripts/build_macos.py
```

This creates:
- `dist/MultiChannelMessaging.app` - The macOS application bundle
- Size: ~172MB

#### 3. Create DMG Installer
```bash
# Create DMG for distribution
python scripts/create_dmg.py
```

This creates:
- `dist/MultiChannelMessaging-macOS.dmg` - The installer DMG
- Size: ~82MB (compressed)

#### 4. Test the Build
```bash
# Test the app bundle
open dist/MultiChannelMessaging.app

# Test the DMG
open dist/MultiChannelMessaging-macOS.dmg
```

### Windows Build

#### 1. Prepare Environment (on Windows)
```cmd
# Activate virtual environment
venv\Scripts\activate

# Ensure all dependencies are installed
pip install -e ".[dev]"
```

#### 2. Build Application
```cmd
# Build the Windows executable
python scripts/build_windows.py
```

This creates:
- `dist/MultiChannelMessaging/MultiChannelMessaging.exe` - The Windows executable
- `dist/MultiChannelMessaging/` - Directory with all dependencies

#### 3. Create Installer (Optional)
For professional distribution, create an installer using:
- NSIS (Nullsoft Scriptable Install System)
- Inno Setup
- WiX Toolset

## Build Configuration

### PyInstaller Spec Files

#### macOS (`scripts/build_macos.spec`)
- Creates macOS app bundle (.app)
- Includes proper Info.plist with permissions
- Bundles all dependencies and assets
- Optimized for macOS distribution

#### Windows (`scripts/build_windows.spec`)
- Creates Windows executable (.exe)
- Includes all dependencies in distribution folder
- Excludes macOS-specific modules
- Optimized for Windows distribution

### Key Features
- **Hidden Imports**: Ensures all required modules are included
- **Data Files**: Bundles configuration files and templates
- **Exclusions**: Removes unnecessary modules to reduce size
- **Platform Detection**: Automatically handles platform-specific dependencies

## Distribution

### macOS Distribution

#### App Store Distribution
1. Code sign the app bundle
2. Create app-specific password
3. Notarize with Apple
4. Submit to App Store

#### Direct Distribution
1. Code sign the app bundle (recommended)
2. Notarize with Apple (required for macOS 10.15+)
3. Distribute DMG file
4. Provide installation instructions

### Windows Distribution

#### Microsoft Store Distribution
1. Package as MSIX
2. Code sign the package
3. Submit to Microsoft Store

#### Direct Distribution
1. Code sign the executable (recommended)
2. Create installer package
3. Distribute installer or ZIP file
4. Provide installation instructions

## Testing

### Automated Testing
```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run all tests with coverage
pytest --cov=src/multichannel_messaging
```

### Manual Testing

#### macOS Testing
1. Test app bundle launch
2. Verify Outlook integration
3. Test CSV import functionality
4. Verify email sending
5. Test all GUI components

#### Windows Testing
1. Test executable launch
2. Verify Outlook COM integration
3. Test CSV import functionality
4. Verify email sending
5. Test all GUI components

### Cross-Platform Testing
- CSV file compatibility
- Configuration file portability
- Template file compatibility
- Email formatting consistency

## Troubleshooting

### Common Build Issues

#### macOS
- **Missing ScriptingBridge**: Install pyobjc packages
- **Permission Errors**: Check file permissions and code signing
- **App Won't Launch**: Verify all dependencies are bundled

#### Windows
- **Missing win32com**: Install pywin32 package
- **COM Errors**: Ensure Outlook is properly installed
- **Executable Won't Run**: Check for missing Visual C++ redistributables

### Performance Optimization
- Use UPX compression (enabled by default)
- Exclude unnecessary modules
- Optimize asset bundling
- Consider lazy loading for large dependencies

## Security Considerations

### Code Signing
- **macOS**: Use Apple Developer certificate
- **Windows**: Use Authenticode certificate
- **Benefits**: User trust, security warnings prevention

### Notarization (macOS)
- Required for macOS 10.15+
- Automated malware scanning
- Improves user experience

### Best Practices
- Sign all executables and installers
- Use secure build environments
- Verify build integrity
- Implement update mechanisms

## Continuous Integration

### GitHub Actions Example
```yaml
name: Build and Package

on: [push, pull_request]

jobs:
  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Build macOS app
        run: python scripts/build_macos.py
      - name: Create DMG
        run: python scripts/create_dmg.py

  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Build Windows exe
        run: python scripts/build_windows.py
```

## Release Process

1. **Version Bump**: Update version in `__init__.py` and spec files
2. **Testing**: Run full test suite on both platforms
3. **Build**: Create platform-specific builds
4. **Sign**: Code sign all executables
5. **Package**: Create distribution packages
6. **Upload**: Upload to distribution channels
7. **Document**: Update release notes and documentation

## File Sizes and Performance

### macOS
- **App Bundle**: ~172MB
- **DMG**: ~82MB (compressed)
- **Startup Time**: ~3-5 seconds
- **Memory Usage**: ~150-200MB

### Windows
- **Executable + Dependencies**: ~150-180MB
- **Installer**: ~80-100MB (compressed)
- **Startup Time**: ~3-5 seconds
- **Memory Usage**: ~150-200MB

## Support and Maintenance

### Update Strategy
- Implement automatic update checking
- Provide manual update instructions
- Maintain backward compatibility
- Document breaking changes

### User Support
- Provide installation guides
- Create troubleshooting documentation
- Maintain FAQ and known issues list
- Offer multiple support channels
