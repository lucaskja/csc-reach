# CSC-Reach Build Guide

## Overview

Comprehensive guide for building and packaging CSC-Reach for distribution on Windows and macOS platforms.

## Prerequisites

### Development Environment
- **Python 3.8+** (tested up to Python 3.12)
- **Virtual environment** with all dependencies
- **PyInstaller 5.13.0+** for executable creation
- **Git** for version control

### Platform-Specific Requirements

#### Windows
- **Windows 10+** for building and testing
- **Microsoft Outlook** for Windows installed
- **Visual Studio Build Tools** for pywin32 compilation
- **Code signing certificate** (optional, for distribution)

#### macOS
- **macOS 10.14+** for development and building
- **Microsoft Outlook for Mac** installed
- **Xcode Command Line Tools** for DMG creation
- **Code signing certificate** (optional, for distribution)

## Quick Start

### Simple Building
```bash
# Build for current platform
python build.py

# Build specific platform
python build.py macos
python build.py windows

# Clean build (removes previous builds)
python build.py clean
```

### Using Make
```bash
# Build everything
make build

# Platform-specific
make build-macos
make build-windows

# Clean
make clean
```

## Build Process

### 1. Environment Setup
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
pip install -e ".[dev,build]"
```

### 2. Build Configuration

#### Icon Creation
The application uses custom icons converted to platform-specific formats:

**Source Icon**: `assets/icons/app_icon.png` (1024x1024 PNG)

**Platform Conversions**:
- **Windows**: Convert to `.ico` format
- **macOS**: Convert to `.icns` format

```bash
# Convert icons (requires pillow and additional tools)
python scripts/convert_icons.py
```

#### PyInstaller Configuration
Build specifications are defined in:
- `build_specs/macos.spec` - macOS build configuration
- `build_specs/windows.spec` - Windows build configuration

### 3. Building Executables

#### macOS Build
```bash
# Build .app bundle
python scripts/build_macos.py

# Create DMG installer
python scripts/create_dmg.py

# Output locations:
# - build/dist/CSC-Reach.app
# - build/dist/CSC-Reach-macOS.dmg
```

#### Windows Build
```bash
# Build .exe executable
python scripts/build_windows.py

# Create installer (optional)
python scripts/create_installer.py

# Output locations:
# - build/dist/CSC-Reach.exe
# - build/dist/CSC-Reach-Windows-Setup.exe
```

### 4. Build Verification

#### Automated Testing
```bash
# Run build verification tests
python scripts/verify_build.py

# Test specific platform
python scripts/verify_build.py --platform macos
python scripts/verify_build.py --platform windows
```

#### Manual Testing Checklist
- [ ] Application launches without errors
- [ ] All GUI components render correctly
- [ ] File import functionality works
- [ ] Email integration connects to Outlook
- [ ] WhatsApp Web automation functions
- [ ] All translations display properly
- [ ] Themes switch correctly

## Advanced Build Options

### Code Signing

#### macOS Code Signing
```bash
# Sign the application
codesign --force --verify --verbose --sign "Developer ID Application: Your Name" build/dist/CSC-Reach.app

# Verify signature
codesign --verify --verbose build/dist/CSC-Reach.app
spctl --assess --verbose build/dist/CSC-Reach.app
```

#### Windows Code Signing
```bash
# Sign the executable (requires signtool.exe)
signtool sign /f certificate.p12 /p password /t http://timestamp.digicert.com build/dist/CSC-Reach.exe

# Verify signature
signtool verify /pa build/dist/CSC-Reach.exe
```

### Build Optimization

#### Size Optimization
```python
# In PyInstaller spec file
excludes = [
    'tkinter',
    'matplotlib',
    'scipy',
    'numpy.distutils',
    'distutils',
    'setuptools'
]

# Hidden imports (if needed)
hiddenimports = [
    'multichannel_messaging.localization',
    'multichannel_messaging.services'
]
```

#### Performance Optimization
- **UPX Compression**: Reduce executable size (optional)
- **One-file vs One-dir**: Choose based on startup time vs size requirements
- **Exclude unused modules**: Remove unnecessary dependencies

### Cross-Platform Considerations

#### File Paths
```python
# Use pathlib for cross-platform paths
from pathlib import Path

config_dir = Path.home() / ".csc-reach"
```

#### Platform Detection
```python
import platform

if platform.system() == "Windows":
    # Windows-specific code
elif platform.system() == "Darwin":
    # macOS-specific code
```

## Release Automation

### Automated Release Pipeline

#### GitHub Actions Workflow
```yaml
name: Build and Release
on:
  push:
    tags: ['v*']

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Build Windows
        run: python scripts/build_windows.py
      - name: Upload artifacts
        uses: actions/upload-artifact@v3

  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Build macOS
        run: python scripts/build_macos.py
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
```

#### Release Script
```bash
# Automated release process
python scripts/release.py --version 1.0.5

# Steps performed:
# 1. Update version numbers
# 2. Run tests
# 3. Build for all platforms
# 4. Create release packages
# 5. Generate checksums
# 6. Create GitHub release
```

### Version Management

#### Semantic Versioning
- **Major.Minor.Patch** (e.g., 1.0.5)
- **Major**: Breaking changes
- **Minor**: New features, backward compatible
- **Patch**: Bug fixes, backward compatible

#### Version Update Process
```python
# Update version in multiple files
python scripts/bump_version.py 1.0.5

# Files updated:
# - pyproject.toml
# - src/multichannel_messaging/__init__.py
# - build_specs/*.spec
```

## Troubleshooting

### Common Build Issues

#### Missing Dependencies
```bash
# Error: Module not found during build
# Solution: Add to hiddenimports in spec file
hiddenimports = ['missing_module']
```

#### Icon Issues
```bash
# Error: Icon not found or invalid format
# Solution: Verify icon paths and formats
python scripts/verify_icons.py
```

#### Platform-Specific Errors
```bash
# Windows: pywin32 compilation errors
# Solution: Install Visual Studio Build Tools

# macOS: Code signing issues
# Solution: Check certificate and keychain access
```

### Build Debugging

#### Verbose Output
```bash
# Enable detailed build logging
python build.py --verbose

# PyInstaller debug mode
pyinstaller --debug=all build_specs/macos.spec
```

#### Build Analysis
```bash
# Analyze build dependencies
python scripts/analyze_build.py

# Check for missing files
python scripts/verify_build_completeness.py
```

## Distribution

### Package Formats

#### macOS Distribution
- **DMG**: Disk image with drag-to-install
- **PKG**: Installer package (advanced)
- **App Store**: Mac App Store distribution (requires additional setup)

#### Windows Distribution
- **Portable EXE**: Single executable file
- **MSI Installer**: Windows Installer package
- **Microsoft Store**: Windows Store distribution (requires additional setup)

### Distribution Checklist
- [ ] Code signed for security
- [ ] Tested on clean systems
- [ ] Documentation updated
- [ ] Release notes prepared
- [ ] Checksums generated
- [ ] Backup of release artifacts

## Maintenance

### Regular Tasks
- **Update dependencies**: Monthly security updates
- **Test builds**: Verify on latest OS versions
- **Performance monitoring**: Track build times and sizes
- **Documentation updates**: Keep build instructions current

### Monitoring
- **Build success rates**: Track CI/CD pipeline health
- **Distribution metrics**: Monitor download and usage statistics
- **Error reporting**: Collect and analyze build failures

This comprehensive build guide ensures consistent, reliable builds across all supported platforms while maintaining security and quality standards.
