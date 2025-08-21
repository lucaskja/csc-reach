"""
Database migration utilities for message logger.
Handles schema updates and data migrations safely.
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any
from contextlib import contextmanager


class DatabaseMigrator:
    """Handles database schema migrations for the message logger."""
    
    def __init__(self, db_path: Path):
        """
        Initialize the database migrator.
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
    
    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper configuration."""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=30)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.row_factory = sqlite3.Row
            yield conn
        finally:
            if conn:
                conn.close()
    
    def get_current_schema_version(self) -> int:
        """Get the current schema version from the database."""
        try:
            with self._get_connection() as conn:
                # Check if schema_version table exists
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='schema_version'
                """)
                
                if not cursor.fetchone():
                    # No schema version table, this is version 0
                    return 0
                
                # Get current version
                cursor = conn.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
                row = cursor.fetchone()
                return row[0] if row else 0
                
        except Exception as e:
            self.logger.warning(f"Failed to get schema version: {e}")
            return 0
    
    def set_schema_version(self, version: int) -> None:
        """Set the current schema version."""
        try:
            with self._get_connection() as conn:
                # Create schema_version table if it doesn't exist
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        version INTEGER PRIMARY KEY,
                        applied_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert new version
                conn.execute("""
                    INSERT OR REPLACE INTO schema_version (version) VALUES (?)
                """, (version,))
                
                conn.commit()
                self.logger.info(f"Schema version updated to {version}")
                
        except Exception as e:
            self.logger.error(f"Failed to set schema version: {e}")
            raise
    
    def check_column_exists(self, table: str, column: str) -> bool:
        """Check if a column exists in a table."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]
                return column in columns
        except Exception as e:
            self.logger.warning(f"Failed to check column {table}.{column}: {e}")
            return False
    
    def add_column_if_missing(self, table: str, column: str, column_type: str, default_value: str = None) -> bool:
        """Add a column to a table if it doesn't exist."""
        if self.check_column_exists(table, column):
            self.logger.debug(f"Column {table}.{column} already exists")
            return False
        
        try:
            with self._get_connection() as conn:
                sql = f"ALTER TABLE {table} ADD COLUMN {column} {column_type}"
                if default_value and default_value != "CURRENT_TIMESTAMP":
                    sql += f" DEFAULT {default_value}"
                
                conn.execute(sql)
                
                # If we added a timestamp column, update existing rows
                if default_value == "CURRENT_TIMESTAMP":
                    conn.execute(f"UPDATE {table} SET {column} = CURRENT_TIMESTAMP WHERE {column} IS NULL")
                
                conn.commit()
                self.logger.info(f"Added column {table}.{column}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to add column {table}.{column}: {e}")
            raise
    
    def migrate_to_version_1(self) -> None:
        """Migrate to version 1: Add missing columns to existing tables."""
        self.logger.info("Migrating to schema version 1...")
        
        # Add missing columns to message_logs table
        self.add_column_if_missing("message_logs", "updated_at", "TEXT", "CURRENT_TIMESTAMP")
        
        # Add missing columns to session_summaries table  
        self.add_column_if_missing("session_summaries", "channels_used", "TEXT", "''")
        self.add_column_if_missing("session_summaries", "templates_used", "TEXT", "''")
        self.add_column_if_missing("session_summaries", "session_metadata", "TEXT", "'{}'")
        self.add_column_if_missing("session_summaries", "updated_at", "TEXT", "CURRENT_TIMESTAMP")
        
        # Create update triggers if they don't exist
        try:
            with self._get_connection() as conn:
                # Check if triggers exist
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='trigger' AND name='update_message_logs_timestamp'
                """)
                
                if not cursor.fetchone():
                    conn.execute("""
                        CREATE TRIGGER update_message_logs_timestamp 
                        AFTER UPDATE ON message_logs
                        BEGIN
                            UPDATE message_logs SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                        END
                    """)
                    self.logger.info("Created update_message_logs_timestamp trigger")
                
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='trigger' AND name='update_session_summaries_timestamp'
                """)
                
                if not cursor.fetchone():
                    conn.execute("""
                        CREATE TRIGGER update_session_summaries_timestamp 
                        AFTER UPDATE ON session_summaries
                        BEGIN
                            UPDATE session_summaries SET updated_at = CURRENT_TIMESTAMP WHERE session_id = NEW.session_id;
                        END
                    """)
                    self.logger.info("Created update_session_summaries_timestamp trigger")
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to create triggers: {e}")
            raise
        
        self.logger.info("Schema version 1 migration completed")
    
    def run_migrations(self) -> None:
        """Run all necessary migrations to bring database to current version."""
        current_version = self.get_current_schema_version()
        target_version = 1  # Current target version
        
        self.logger.info(f"Current schema version: {current_version}, target: {target_version}")
        
        if current_version >= target_version:
            self.logger.info("Database schema is up to date")
            return
        
        # Run migrations in order
        if current_version < 1:
            self.migrate_to_version_1()
            self.set_schema_version(1)
        
        self.logger.info("All database migrations completed successfully")
    
    def verify_schema(self) -> Dict[str, Any]:
        """Verify the database schema is correct."""
        verification_results = {
            "schema_version": self.get_current_schema_version(),
            "tables_exist": {},
            "columns_exist": {},
            "triggers_exist": {},
            "issues": []
        }
        
        # Check required tables
        required_tables = ["message_logs", "session_summaries", "analytics_cache", "system_logs"]
        
        try:
            with self._get_connection() as conn:
                for table in required_tables:
                    cursor = conn.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name=?
                    """, (table,))
                    verification_results["tables_exist"][table] = bool(cursor.fetchone())
                    
                    if not verification_results["tables_exist"][table]:
                        verification_results["issues"].append(f"Missing table: {table}")
                
                # Check required columns
                required_columns = {
                    "message_logs": ["id", "timestamp", "user_id", "session_id", "channel", 
                                   "template_id", "template_name", "recipient_email", 
                                   "message_status", "updated_at"],
                    "session_summaries": ["session_id", "user_id", "start_time", "end_time",
                                        "channel", "total_messages", "successful_messages",
                                        "channels_used", "templates_used", "updated_at"]
                }
                
                for table, columns in required_columns.items():
                    if verification_results["tables_exist"][table]:
                        verification_results["columns_exist"][table] = {}
                        for column in columns:
                            exists = self.check_column_exists(table, column)
                            verification_results["columns_exist"][table][column] = exists
                            
                            if not exists:
                                verification_results["issues"].append(f"Missing column: {table}.{column}")
                
                # Check required triggers
                required_triggers = ["update_message_logs_timestamp", "update_session_summaries_timestamp"]
                
                for trigger in required_triggers:
                    cursor = conn.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='trigger' AND name=?
                    """, (trigger,))
                    verification_results["triggers_exist"][trigger] = bool(cursor.fetchone())
                    
                    if not verification_results["triggers_exist"][trigger]:
                        verification_results["issues"].append(f"Missing trigger: {trigger}")
        
        except Exception as e:
            verification_results["issues"].append(f"Schema verification failed: {e}")
        
        return verification_results


def migrate_message_logger_database(db_path: Path) -> bool:
    """
    Migrate the message logger database to the latest schema.
    
    Args:
        db_path: Path to the database file
        
    Returns:
        True if migration was successful
    """
    logger = logging.getLogger(__name__)
    
    try:
        migrator = DatabaseMigrator(db_path)
        
        # Run migrations
        migrator.run_migrations()
        
        # Verify schema
        verification = migrator.verify_schema()
        
        if verification["issues"]:
            logger.warning(f"Schema verification found issues: {verification['issues']}")
            return False
        
        logger.info("Database migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        return False