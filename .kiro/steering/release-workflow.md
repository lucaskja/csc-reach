# Release Workflow & Automated Build System

## Overview

CSC-Reach uses a fully automated cross-platform build and release system that triggers on version changes in `pyproject.toml`. The system builds for both Windows and macOS simultaneously and creates professional GitHub releases.

## Core Principles

### Version-Driven Releases
- **Single source of truth**: Version in `pyproject.toml` controls everything
- **Automatic detection**: Workflows trigger when version differs from latest Git tag
- **Semantic versioning**: Follow MAJOR.MINOR.PATCH format (e.g., 1.0.1)
- **Tag creation**: GitHub releases automatically create Git tags (e.g., v1.0.1)

### Cross-Platform Automation
- **Parallel builds**: Windows and macOS build simultaneously
- **Multiple formats**: ZIP files for both platforms, DMG for macOS
- **Consistent naming**: Version-specific filenames (CSC-Reach-Windows-v1.0.1.zip)
- **Professional releases**: Auto-generated release notes with installation instructions

## Release Commands

### Quick Release Commands
```bash
# For bug fixes (1.0.0 → 1.0.1)
make release-patch

# For new features (1.0.0 → 1.1.0)
make release-minor

# For breaking changes (1.0.0 → 2.0.0)
make release-major
```

### Version Management Commands
```bash
# Check current version
make version-check

# Preview version changes (dry run)
make version-dry-run-patch
make version-dry-run-minor
make version-dry-run-major

# Manual version bumps (without release)
make version-patch
make version-minor
make version-major
```

### Manual Version Bump
```bash
# Using the bump script directly
python scripts/bump_version.py patch    # or minor/major
python scripts/bump_version.py patch --dry-run  # preview only

# Manual edit of pyproject.toml
# Edit version = "1.0.0" to version = "1.0.1"
# Then commit and push to main branch
```

## Workflow Triggers

### Automatic Triggers
1. **Version change detection**: Push to `main` branch with `pyproject.toml` changes
2. **Version comparison**: Current version ≠ latest Git tag
3. **Parallel execution**: Both Windows and macOS workflows start simultaneously

### Manual Triggers
1. **GitHub Actions UI**: Actions tab → Select workflow → "Run workflow"
2. **Tag pushes**: Pushing tags like `git push origin v1.0.1` (legacy support)
3. **Pull requests**: Builds for testing (no release created)

## Workflow Files

### Windows Workflow: `.github/workflows/build-windows.yml`
- **Runner**: `windows-latest`
- **Python**: 3.11
- **Dependencies**: PyInstaller, PySide6, pywin32
- **Output**: `CSC-Reach-Windows-v1.0.1.zip`
- **Testing**: ZIP extraction and executable validation

### macOS Workflow: `.github/workflows/build-macos.yml`
- **Runner**: `macos-latest`
- **Python**: 3.11
- **Dependencies**: PyInstaller, PySide6, ScriptingBridge
- **Outputs**: `CSC-Reach-macOS-v1.0.1.zip` and `CSC-Reach-macOS.dmg`
- **Testing**: Both ZIP and DMG validation

## Build Process Flow

### 1. Version Detection Job
```yaml
check-version:
  - Compares pyproject.toml version with latest Git tag
  - Sets outputs: version-changed, new-version, should-release
  - Runs on ubuntu-latest for speed
```

### 2. Platform Build Jobs
```yaml
build-windows / build-macos:
  - Conditional: only if version changed or PR
  - Parallel execution for speed
  - Complete build, test, and artifact creation
```

### 3. Release Creation
```yaml
create-release:
  - Automatic tag creation (e.g., v1.0.1)
  - Professional release notes
  - Multiple file attachments
  - Platform-specific installation instructions
```

## Distribution Files Created

### Windows
- **CSC-Reach-Windows-v1.0.1.zip**: Complete Windows application
  - Contains CSC-Reach.exe and all dependencies
  - Ready to extract and run

### macOS
- **CSC-Reach-macOS-v1.0.1.zip**: macOS application bundle
  - Contains CSC-Reach.app bundle
  - Extract and move to Applications folder
- **CSC-Reach-macOS.dmg**: Professional macOS installer
  - Drag-and-drop installation interface
  - Native macOS installation experience

## Correct Tag Creation Process

### ❌ NEVER Do This Manually
```bash
# DON'T create tags manually - this bypasses the build system
git tag v1.0.1
git push origin v1.0.1
```

### ✅ ALWAYS Use Version-Driven Process
```bash
# Method 1: One-command release (RECOMMENDED)
make release-patch  # Automatically: bump → commit → push → build → tag → release

# Method 2: Manual version bump
python scripts/bump_version.py patch
git add pyproject.toml
git commit -m "Bump version to 1.0.1"
git push origin main
# Workflows automatically: build → tag → release

# Method 3: Direct edit
# Edit pyproject.toml: version = "1.0.1"
git add pyproject.toml
git commit -m "Bump version to 1.0.1"
git push origin main
```

## Version Management Rules

### Semantic Versioning
- **PATCH (1.0.0 → 1.0.1)**: Bug fixes, small improvements
- **MINOR (1.0.0 → 1.1.0)**: New features, backwards compatible
- **MAJOR (1.0.0 → 2.0.0)**: Breaking changes, major updates

### Version Consistency
- **Single source**: Only edit version in `pyproject.toml`
- **No manual tags**: Let the release system create tags
- **Sequential versions**: Don't skip versions (1.0.0 → 1.0.2 ❌)

## Monitoring Releases

### GitHub Actions
1. **Actions tab**: Monitor workflow progress
2. **Green checkmarks**: Successful builds
3. **Red X marks**: Failed builds (check logs)
4. **Yellow circles**: Currently running

### Release Verification
1. **Releases section**: New release should appear
2. **Download test**: Verify all files are attached
3. **Installation test**: Test on target platforms
4. **Tag verification**: Check that Git tag was created

## Troubleshooting

### Common Issues

#### Version Not Triggering Build
- **Check**: Version in `pyproject.toml` vs latest Git tag
- **Fix**: Ensure version is different from latest tag
- **Verify**: `make version-check` and `git tag --sort=-version:refname | head -1`

#### Build Failures
- **Windows**: Check PyInstaller logs, dependency issues
- **macOS**: Check app bundle creation, permission issues
- **Both**: Verify build scripts exist and are executable

#### Permission Errors
- **Workflows have**: `contents: write` permission
- **No manual tagging**: Let release action handle tags
- **Token issues**: GITHUB_TOKEN should work automatically

#### Release Not Created
- **Check conditions**: `should-release == 'true'` and not PR
- **Verify files**: Build artifacts must exist
- **Tag conflicts**: Ensure tag doesn't already exist

### Debug Commands
```bash
# Check current state
make version-check
git tag --sort=-version:refname | head -5
git log --oneline -3

# Test version bump (dry run)
make version-dry-run-patch

# Manual workflow trigger
# Go to GitHub Actions → Select workflow → "Run workflow"
```

## Best Practices

### Release Timing
- **Test thoroughly** before version bumps
- **Batch small changes** into meaningful releases
- **Use descriptive commit messages** for release notes
- **Avoid frequent releases** (aim for quality over quantity)

### Version Strategy
- **Start clean**: Use semantic versioning from v1.0.0
- **Document changes**: Clear commit messages become release notes
- **Test releases**: Verify downloads and installations work
- **Monitor feedback**: Track which distribution formats users prefer

### Team Workflow
- **One person releases**: Avoid conflicts from multiple release attempts
- **Communicate releases**: Let team know when releases are happening
- **Test before release**: Use PR builds to test changes
- **Document issues**: Keep track of build problems and solutions

## Emergency Procedures

### Failed Release Recovery
1. **Cancel running workflows** if needed
2. **Fix the issue** in code
3. **Don't increment version** for fixes
4. **Push fix** and re-run workflows
5. **If tag exists**: May need to delete and recreate release

### Rollback Process
1. **Don't delete releases** (users may have downloaded)
2. **Create new patch version** with fixes
3. **Mark problematic release** as pre-release if needed
4. **Communicate issues** to users via release notes

## Integration with Development

### Pull Request Testing
- **Workflows run on PRs** for validation
- **No releases created** from PR builds
- **Test artifacts available** for 30 days
- **Use for pre-release testing**

### Branch Strategy
- **Main branch**: Only stable, release-ready code
- **Feature branches**: Develop and test before merging
- **Release from main**: All releases come from main branch
- **No release branches**: Version-driven releases eliminate need

This automated release system ensures consistent, professional releases across all platforms while minimizing manual intervention and potential errors.