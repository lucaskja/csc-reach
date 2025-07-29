#!/usr/bin/env python3
"""
Custom exceptions for release management system.
"""


class ReleaseManagerError(Exception):
    """Base exception for release manager errors."""
    pass


class VersionError(ReleaseManagerError):
    """Raised when version operations fail."""
    pass


class AssetValidationError(ReleaseManagerError):
    """Raised when asset validation fails."""
    
    def __init__(self, message: str, missing_assets: list[str] = None):
        super().__init__(message)
        self.missing_assets = missing_assets or []


class GitOperationError(ReleaseManagerError):
    """Raised when git operations fail."""
    pass


class ConfigurationError(ReleaseManagerError):
    """Raised when configuration is invalid or missing."""
    pass


class ReleaseCreationError(ReleaseManagerError):
    """Raised when release creation fails."""
    pass


class ManifestError(ReleaseManagerError):
    """Raised when manifest operations fail."""
    pass