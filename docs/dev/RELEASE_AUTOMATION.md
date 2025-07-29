# Release Automation System

This document describes the comprehensive release automation system implemented for CSC-Reach.

## Overview

The release automation system provides:

- **Automated version management** with semantic versioning
- **Comprehensive release notes generation** from git history and GitHub data
- **Multi-channel distribution** (development, staging, production)
- **Cross-platform build automation** with GitHub Actions
- **Quality gates and testing** before releases
- **Asset management and validation**

## Quick Start

### Creating a Release

The simplest way to create a release is using the release script:

```bash
# Development release with patch version bump
python scripts/release.py --dev --patch

# Staging release with minor version bump  
python scripts/release.py --staging --minor

# Production release (current version)
python scripts/release.py --production

# Dry run to see what would happen
python scripts/release.py --production --major --dry-run
```

### Manual GitHub Actions Trigger

You can also trigger releases through GitHub Actions:

1. Go to the **Actions** tab in your repository
2. Select **Cross-Platform Build and Release** workflow
3. Click **Run workflow**
4. Choose your options:
   - **Release type**: development, staging, or production
   - **Version increment**: patch, minor, or major
   - **Version**: leave empty for auto-increment
   - **Skip tests**: only for development (not recommended)

## Components

### 1. Version Manager (`scripts/build/version_manager.py`)

Handles version operations:

```bash
# Show current version
python scripts/build/version_manager.py --current

# Show version information
python scripts/build/version_manager.py --info

# Bump version
python scripts/build/version_manager.py --bump patch

# Full release with git tag
python scripts/build/version_manager.py --bump minor --release --push
```

### 2. Release Notes Generator (`scripts/build/release_notes_generator.py`)

Generates comprehensive release notes:

```bash
# Generate release notes
python scripts/build/release_notes_generator.py \
  --version "1.2.0" \
  --release-type production \
  --output release-notes.md
```

Features:
- Categorizes commits by type (features, fixes, improvements)
- Includes GitHub issues and pull requests
- Adds download instructions and system requirements
- Shows contributor information

### 3. Distribution Manager (`scripts/build/distribution_manager.py`)

Manages distribution channels:

```bash
# Deploy to staging channel
python scripts/build/distribution_manager.py \
  --channel staging \
  --version "1.2.0" \
  --assets-dir ./release-assets

# Check channel status
python scripts/build/distribution_manager.py \
  --channel production \
  --action status

# List all channels
python scripts/build/distribution_manager.py --action list
```

### 4. Release Manager (`scripts/build/release_manager.py`)

Coordinates release creation:

```bash
# Create staged release
python scripts/build/release_manager.py \
  --version "1.2.0" \
  --release-type production \
  --assets-dir ./release-assets
```

### 5. Build Orchestrator (`scripts/build/build_orchestrator.py`)

Runs the complete pipeline:

```bash
# Full pipeline
python scripts/build/build_orchestrator.py \
  --release-type production \
  --increment minor

# Specific stages only
python scripts/build/build_orchestrator.py \
  --stages version_check build package \
  --dry-run
```

## Distribution Channels

### Development
- **Purpose**: Internal testing and feature validation
- **Auto-deploy**: Yes
- **Retention**: 7 days
- **GitHub Release**: Draft, prerelease

### Staging  
- **Purpose**: Pre-production testing and QA
- **Auto-deploy**: Yes
- **Retention**: 30 days
- **GitHub Release**: Public prerelease

### Production
- **Purpose**: End-user releases
- **Auto-deploy**: No (manual approval)
- **Retention**: 365 days
- **GitHub Release**: Public release

## Quality Gates

Different release types have different quality requirements:

| Check | Development | Staging | Production |
|-------|-------------|---------|------------|
| Tests | Optional | Required | Required |
| Quality Checks | Optional | Required | Required |
| Min Coverage | 0% | 70% | 80% |
| Security Scan | No | Yes | Yes |

## GitHub Actions Workflow

The workflow includes these jobs:

1. **test-and-quality**: Runs tests and quality checks
2. **build-windows**: Creates Windows executable and ZIP
3. **build-macos**: Creates macOS app bundle and DMG
4. **create-release**: Generates release with automation
5. **test-builds**: Verifies built applications work

### Triggers

- **Push to tags** (`v*`): Automatic production release
- **Push to main/develop**: Build and test only
- **Manual dispatch**: Full control over release type and version
- **Pull requests**: Build and test only

## Configuration

### Distribution Config (`scripts/build/distribution_config.yaml`)

Controls how releases are distributed:

```yaml
channels:
  production:
    description: "Production releases for end users"
    auto_deploy: false
    retention_days: 365
    destinations:
      - type: github_releases
        prerelease: false
        draft: false
```

### Build Config (`scripts/build/build_config.yaml`)

Controls the build pipeline (auto-generated):

```yaml
pipeline:
  stages: [version_check, quality_checks, tests, build, package, release]
  parallel_builds: true
  fail_fast: true
```

## Best Practices

### Version Management
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Increment PATCH for bug fixes
- Increment MINOR for new features
- Increment MAJOR for breaking changes

### Release Process
1. **Development**: Frequent releases for testing
2. **Staging**: Weekly releases for QA
3. **Production**: Monthly releases for users

### Quality Assurance
- Always run tests before production releases
- Use staging releases to validate changes
- Monitor build artifacts and logs

## Troubleshooting

### Common Issues

**Release script fails with import errors:**
```bash
# Install dependencies
pip install pyyaml requests

# Or install development dependencies
pip install -e ".[dev]"
```

**GitHub API rate limiting:**
- Set `GITHUB_TOKEN` environment variable
- Use `--no-github` flag to skip API calls

**Build artifacts missing:**
- Check that build scripts completed successfully
- Verify assets directory contains required files
- Run build verification script

### Debug Mode

Most scripts support dry-run mode:

```bash
# See what would happen without making changes
python scripts/release.py --production --major --dry-run
```

### Logs and Artifacts

- Build logs are stored in `build/logs/`
- Release artifacts are stored in `release-assets/`
- GitHub Actions artifacts are retained based on release type

## Integration with External Systems

### GitHub
- Automatic release creation
- Issue and PR integration in release notes
- Artifact storage and distribution

### AWS (Future)
- S3 distribution buckets
- CloudWatch monitoring
- Cost tracking and optimization

### Notifications (Future)
- Slack/Discord webhooks
- Email notifications
- Build status badges

## Security Considerations

- Code signing certificates (when available)
- Secure credential storage
- Access control for production releases
- Audit trails for all release activities

## Monitoring and Analytics

- Build success/failure rates
- Release frequency and size
- Download statistics
- Performance metrics

This automation system ensures consistent, reliable releases while maintaining quality and security standards.