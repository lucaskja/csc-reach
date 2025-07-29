#!/usr/bin/env python3
"""
Release Strategy Pattern Implementation
Different strategies for different release types
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class ReleaseConfig:
    """Configuration for a release."""
    prerelease: bool
    draft: bool
    auto_publish: bool
    retention_days: int
    notification_channels: list[str]


class ReleaseStrategy(ABC):
    """Abstract base class for release strategies."""
    
    @abstractmethod
    def get_config(self) -> ReleaseConfig:
        """Get configuration for this release type."""
        pass
    
    @abstractmethod
    def should_run_full_tests(self) -> bool:
        """Determine if full test suite should run."""
        pass
    
    @abstractmethod
    def get_asset_retention_days(self) -> int:
        """Get how long to retain assets."""
        pass
    
    @abstractmethod
    def should_notify_stakeholders(self) -> bool:
        """Determine if stakeholders should be notified."""
        pass


class DevelopmentReleaseStrategy(ReleaseStrategy):
    """Strategy for development releases."""
    
    def get_config(self) -> ReleaseConfig:
        return ReleaseConfig(
            prerelease=True,
            draft=True,
            auto_publish=False,
            retention_days=7,
            notification_channels=['slack-dev']
        )
    
    def should_run_full_tests(self) -> bool:
        return False  # Skip some tests for faster feedback
    
    def get_asset_retention_days(self) -> int:
        return 7
    
    def should_notify_stakeholders(self) -> bool:
        return False


class StagingReleaseStrategy(ReleaseStrategy):
    """Strategy for staging releases."""
    
    def get_config(self) -> ReleaseConfig:
        return ReleaseConfig(
            prerelease=True,
            draft=False,
            auto_publish=True,
            retention_days=30,
            notification_channels=['slack-qa', 'email-qa']
        )
    
    def should_run_full_tests(self) -> bool:
        return True
    
    def get_asset_retention_days(self) -> int:
        return 30
    
    def should_notify_stakeholders(self) -> bool:
        return True


class ProductionReleaseStrategy(ReleaseStrategy):
    """Strategy for production releases."""
    
    def get_config(self) -> ReleaseConfig:
        return ReleaseConfig(
            prerelease=False,
            draft=False,
            auto_publish=True,
            retention_days=365,
            notification_channels=['slack-general', 'email-all', 'webhook-customers']
        )
    
    def should_run_full_tests(self) -> bool:
        return True
    
    def get_asset_retention_days(self) -> int:
        return 365
    
    def should_notify_stakeholders(self) -> bool:
        return True


class ReleaseStrategyFactory:
    """Factory for creating release strategies."""
    
    _strategies = {
        'development': DevelopmentReleaseStrategy,
        'staging': StagingReleaseStrategy,
        'production': ProductionReleaseStrategy
    }
    
    @classmethod
    def create_strategy(cls, release_type: str) -> ReleaseStrategy:
        """Create appropriate strategy for release type."""
        strategy_class = cls._strategies.get(release_type)
        if not strategy_class:
            raise ValueError(f"Unknown release type: {release_type}")
        return strategy_class()
    
    @classmethod
    def get_available_types(cls) -> list[str]:
        """Get list of available release types."""
        return list(cls._strategies.keys())