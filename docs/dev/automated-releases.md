# Automated Release Workflow

This document explains the automated release system for CSC-Reach.

## Overview

The automated build workflows now support both platforms and automatically:
1. **Detects version changes** in `pyproject.toml`
2. **Builds applications** for Windows and macOS when versions change
3. **Creates distribution files** (ZIP for both platforms, DMG for macOS)
4. **Creates Git tags** automatically
5. **Publishes GitHub releases** with all distribution files

## How It Works

### Automatic Triggers
The workflow triggers automatically when:
- You push changes to `main` branch that include `pyproject.toml` modifications
- The version in `pyproject.toml` is different from the latest Git tag
- You manually trigger it via GitHub Actions

### Version Detection
The system compares:
- Current version in `pyproject.toml`
- Latest Git tag (e.g., `v1.0.1`)

If they differ, it triggers a build and release.

## Making a Release

### Method 1: Using Make Commands (Recommended)
```bash
# For bug fixes
make release-patch    # 1.0.1 → 1.0.2

# For new features
make release-minor    # 1.0.1 → 1.1.0

# For breaking changes
make release-major    # 1.0.1 → 2.0.0
```

### Method 2: Manual Version Bump
```bash
# Bump version
python scripts/bump_version.py patch  # or minor/major

# Commit and push
git add pyproject.toml
git commit -m "Bump version to 1.0.2"
git push origin main
```

### Method 3: Direct Edit
1. Edit `pyproject.toml`
2. Change the `version = "1.0.1"` line
3. Commit and push to `main`

## What Gets Created

### Windows Artifacts
- **ZIP file**: `CSC-Reach-Windows-v1.0.2.zip`
  - Contains the complete Windows application
  - Ready to distribute to users

### macOS Artifacts
- **ZIP file**: `CSC-Reach-macOS-v1.0.2.zip`
  - Contains the complete macOS application bundle
- **DMG installer**: `CSC-Reach-macOS.dmg`
  - Professional macOS installer with drag-and-drop interface

### GitHub Release
- **Automatic tag**: `v1.0.2`
- **Release notes**: Auto-generated from commits
- **Multiple attachments**: Windows ZIP, macOS ZIP, and macOS DMG
- **Professional descriptions**: Platform-specific installation instructions

## Workflow Benefits

### ✅ Improvements Made
- **Single ZIP file**: No more duplicate artifacts
- **Automatic triggering**: No manual workflow runs needed
- **Version-based releases**: Only builds when version changes
- **Auto-tagging**: Creates Git tags automatically
- **Better naming**: Clear, version-specific file names

### 🔄 Process Flow
1. Developer updates version in `pyproject.toml`
2. Commits and pushes to `main`
3. GitHub Actions detects version change
4. **Parallel builds**: Windows and macOS workflows run simultaneously
5. **Windows**: Creates `CSC-Reach-Windows-v1.0.2.zip`
6. **macOS**: Creates `CSC-Reach-macOS-v1.0.2.zip` and `CSC-Reach-macOS.dmg`
7. Creates Git tag (e.g., `v1.0.2`)
8. Publishes GitHub release with all distribution files attached

## Monitoring Releases

### Check Build Status
- Visit **Actions** tab in GitHub repository
- Look for "Build Windows Executable" workflow
- Green checkmark = successful build and release

### Verify Release
- Visit **Releases** section in GitHub repository
- Latest release should show your new version
- ZIP file should be attached and downloadable

## Troubleshooting

### Build Doesn't Trigger
- Ensure `pyproject.toml` version is different from latest tag
- Check that you pushed to `main` branch
- Verify the commit includes `pyproject.toml` changes

### Build Fails
- Check GitHub Actions logs for detailed error messages
- Ensure all dependencies are properly specified
- Verify build scripts are present and executable

### Version Conflicts
- Use `make version-check` to see current version
- Use `git tag --sort=-version:refname | head -5` to see recent tags
- Ensure new version is higher than the latest tag

## Best Practices

### Version Numbering
- **Patch** (1.0.1 → 1.0.2): Bug fixes, small improvements
- **Minor** (1.0.1 → 1.1.0): New features, backwards compatible
- **Major** (1.0.1 → 2.0.0): Breaking changes, major updates

### Release Timing
- Test thoroughly before version bumps
- Use descriptive commit messages
- Consider batching small changes into single releases
- Avoid frequent releases (aim for meaningful updates)

### Testing
- The workflow includes automatic testing of the built executable
- Failed tests will prevent release creation
- Monitor test results in GitHub Actions logs

## Manual Override

If you need to manually trigger a build:
1. Go to **Actions** tab in GitHub
2. Select "Build Windows Executable" workflow
3. Click "Run workflow"
4. Specify version or leave as "latest"

This bypasses version detection and forces a build.