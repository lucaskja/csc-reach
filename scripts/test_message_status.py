#!/usr/bin/env python3
"""
Test script to verify MessageStatus enum is working correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from multichannel_messaging.core.models import MessageStatus


def main():
    """Test MessageStatus enum."""
    print("Testing MessageStatus enum...")
    
    # Test all status values
    statuses = [
        MessageStatus.PENDING,
        MessageStatus.SENDING,
        MessageStatus.SENT,
        MessageStatus.DELIVERED,
        MessageStatus.READ,
        MessageStatus.FAILED,
        MessageStatus.CANCELLED
    ]
    
    for status in statuses:
        print(f"  {status.name}: {status.value}")
    
    # Test that DELIVERED exists (this was the main issue)
    try:
        delivered_status = MessageStatus.DELIVERED
        print(f"\n✓ MessageStatus.DELIVERED exists: {delivered_status.value}")
    except AttributeError as e:
        print(f"\n✗ MessageStatus.DELIVERED missing: {e}")
        return False
    
    # Test that READ exists
    try:
        read_status = MessageStatus.READ
        print(f"✓ MessageStatus.READ exists: {read_status.value}")
    except AttributeError as e:
        print(f"✗ MessageStatus.READ missing: {e}")
        return False
    
    print("\n✓ All MessageStatus values are working correctly!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)