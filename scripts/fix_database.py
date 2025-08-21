#!/usr/bin/env python3
"""
Script to fix database schema issues in the message logger.
Run this to migrate the database to the latest schema.
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from multichannel_messaging.core.database_migration import migrate_message_logger_database
from multichannel_messaging.utils.platform_utils import get_logs_dir


def main():
    """Fix database schema issues."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get database path
        logs_dir = get_logs_dir()
        db_path = logs_dir / "message_logs.db"
        
        logger.info(f"Fixing database at: {db_path}")
        
        if not db_path.exists():
            logger.info("Database doesn't exist yet - will be created with correct schema")
            return
        
        # Run migration
        success = migrate_message_logger_database(db_path)
        
        if success:
            logger.info("Database migration completed successfully!")
        else:
            logger.error("Database migration failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Failed to fix database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()