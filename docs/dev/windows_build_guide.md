# Windows Build Guide

## Overview

Building Windows executables for CSC-Reach requires special consideration since PyInstaller creates native executables for the platform it runs on. This guide covers multiple approaches for creating Windows builds.

## ⚠️ Important Note

**PyInstaller cannot cross-compile** - it creates executables for the platform it runs on:
- Running on macOS → creates macOS executable
- Running on Linux → creates Linux executable  
- Running on Windows → creates Windows executable

## Build Options

### 1. 🖥️ Native Windows Build (Recommended)

**Requirements:**
- Windows 10/11 machine or VM
- Python 3.8+ installed
- Git for Windows

**Steps:**
```cmd
# Clone repository
git clone <repository-url>
cd sbai-dg-wpp

# Set up virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Build Windows executable
python scripts\build\build_windows.py
```

**Output:**
- `build/dist/CSC-Reach/CSC-Reach.exe` - Windows executable
- `build/dist/CSC-Reach-Windows.zip` - Distribution package

### 2. 🤖 GitHub Actions (Automated)

**Advantages:**
- ✅ True Windows environment
- ✅ Automated builds on code changes
- ✅ No local Windows machine needed
- ✅ Artifact storage and releases

**Setup:**
1. Push code to GitHub repository
2. GitHub Actions workflow automatically triggers
3. Download built executable from Actions artifacts

**Manual Trigger:**
```bash
# Go to GitHub repository → Actions → "Build Windows Executable" → Run workflow
```

**Workflow Features:**
- Builds on `windows-latest` runner
- Tests executable functionality
- Creates ZIP distribution
- Uploads artifacts with 30-day retention
- Creates GitHub releases for tagged versions

### 3. 🐳 Docker with Wine (Experimental)

**Advantages:**
- ✅ Can run on macOS/Linux
- ✅ Reproducible builds
- ✅ Isolated environment

**Limitations:**
- ⚠️ Complex setup with Wine
- ⚠️ May have compatibility issues
- ⚠️ Slower than native builds

**Usage:**
```bash
# Build using Docker
python scripts/build/build_windows_docker.py
```

**Requirements:**
- Docker installed and running
- Sufficient disk space (~2GB for image)
- Time for initial image build

### 4. ☁️ Cloud Build Services

**Options:**
- **Azure DevOps**: Windows build agents
- **AppVeyor**: Free for open source
- **CircleCI**: Windows executors available

## Current Build Status

### ✅ What Works
- **macOS builds**: Fully functional with `.app` and `.dmg` creation
- **Build scripts**: All infrastructure in place
- **GitHub Actions**: Workflow configured and ready
- **Cross-platform code**: Application runs on both Windows and macOS

### ⚠️ Current Limitation
- **Local Windows builds**: Require Windows environment
- **Cross-compilation**: Not supported by PyInstaller

## Recommended Approach

### For Development
1. **Use GitHub Actions** for automated Windows builds
2. **Test locally** on macOS for development
3. **Use Windows VM** if frequent Windows testing needed

### For Production Releases
1. **GitHub Actions** for consistent, automated builds
2. **Tag releases** to trigger automatic distribution
3. **Download artifacts** from successful builds

## Build Configuration

### Windows Spec File
Location: `scripts/build/build_windows.spec`

Key configurations:
```python
# Windows-specific hidden imports
hiddenimports=[
    'win32com.client',
    'pythoncom', 
    'pywintypes',
    # ... other imports
],

# Exclude macOS-specific modules
excludes=[
    'ScriptingBridge',
    'Foundation',
    'objc',
],
```

### Build Script Features
- ✅ Automatic output directory management
- ✅ Build logging and error reporting
- ✅ Size reporting and validation
- ✅ ZIP distribution creation
- ✅ Platform detection and warnings

## Troubleshooting

### Common Issues

**"Building Windows executable on non-Windows platform"**
- **Solution**: Use GitHub Actions or Windows machine
- **Workaround**: Docker with Wine (experimental)

**"PyInstaller failed"**
- **Check**: Dependencies are installed (`pip install -e ".[dev]"`)
- **Check**: PyInstaller is available (`pip install pyinstaller`)
- **Review**: Build logs in `build/logs/`

**"Executable not found"**
- **Check**: Build completed without errors
- **Look in**: `build/dist/CSC-Reach/` directory
- **Verify**: Correct file extension (`.exe` on Windows)

**"Import errors in built executable"**
- **Add**: Missing modules to `hiddenimports` in spec file
- **Test**: Application imports before building
- **Check**: All dependencies are included

### Debug Information

**Enable verbose logging:**
```bash
python scripts/build/build_windows.py --verbose
```

**Check build logs:**
```bash
# View build logs
cat build/logs/build_windows.log

# View error logs (if build failed)
cat build/logs/build_windows_error.log
```

**Test executable:**
```cmd
# On Windows, test the built executable
build\dist\CSC-Reach\CSC-Reach.exe --version
```

## GitHub Actions Usage

### Automatic Builds
- **Push to main**: Triggers build for testing
- **Create tag**: Triggers build and release
- **Pull request**: Triggers build for validation

### Manual Builds
1. Go to repository on GitHub
2. Click "Actions" tab
3. Select "Build Windows Executable"
4. Click "Run workflow"
5. Optionally specify version tag
6. Download artifacts when complete

### Artifacts
- **CSC-Reach-Windows-{version}**: Executable and dependencies
- **CSC-Reach-Windows-ZIP-{version}**: Distribution ZIP file
- **Retention**: 30 days for artifacts
- **Releases**: Permanent for tagged versions

## File Structure

```
build/
├── dist/
│   ├── CSC-Reach/
│   │   ├── CSC-Reach.exe          # Main executable
│   │   ├── _internal/             # Dependencies
│   │   └── ...
│   └── CSC-Reach-Windows.zip      # Distribution package
├── temp/                          # Build temporary files
└── logs/
    ├── build_windows.log          # Build output
    └── build_windows_error.log    # Error logs (if any)
```

## Performance Characteristics

### Build Times
- **Native Windows**: ~2-5 minutes
- **GitHub Actions**: ~5-10 minutes (including setup)
- **Docker with Wine**: ~10-20 minutes (first build)

### Output Sizes
- **Executable**: ~13-15 MB
- **Full distribution**: ~150-200 MB (with dependencies)
- **ZIP package**: ~50-80 MB (compressed)

## Best Practices

### For Developers
1. **Test locally** on macOS during development
2. **Use GitHub Actions** for Windows builds
3. **Tag releases** for distribution builds
4. **Test executables** on actual Windows machines

### For CI/CD
1. **Automate builds** on code changes
2. **Store artifacts** for testing
3. **Create releases** for stable versions
4. **Test executables** as part of pipeline

### For Distribution
1. **Use GitHub Releases** for official distributions
2. **Include checksums** for security
3. **Provide installation instructions**
4. **Test on multiple Windows versions**

## Future Improvements

### Planned Enhancements
- **Code signing**: Digital signatures for Windows executables
- **Installer creation**: MSI or NSIS installer packages
- **Auto-updates**: Built-in update mechanism
- **Multiple architectures**: x64 and ARM64 support

### Monitoring
- **Build success rates** across different methods
- **Performance metrics** for build times
- **Distribution statistics** for downloads
- **Error patterns** and common issues

This guide provides comprehensive coverage of Windows build options, with GitHub Actions being the recommended approach for most use cases.
