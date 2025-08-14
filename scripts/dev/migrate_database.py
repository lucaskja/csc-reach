#!/usr/bin/env python3
"""
Database migration script to update existing message logging databases
with the new schema fields.
"""

import sqlite3
import sys
from pathlib import Path


def migrate_database(db_path: str):
    """Migrate database to new schema."""
    print(f"Migrating database: {db_path}")
    
    try:
        with sqlite3.connect(db_path) as conn:
            # Check if database exists and has tables
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='session_summaries'
            """)
            
            if not cursor.fetchone():
                print("  - No session_summaries table found, skipping migration")
                return True
            
            # Get current schema
            cursor = conn.execute("PRAGMA table_info(session_summaries)")
            columns = {row[1] for row in cursor.fetchall()}
            
            # Add missing columns
            new_columns = [
                ("channel", "TEXT"),
                ("template_used", "TEXT"),
                ("pending_messages", "INTEGER DEFAULT 0"),
                ("cancelled_messages", "INTEGER DEFAULT 0"),
                ("success_rate", "REAL DEFAULT 0.0")
            ]
            
            for column_name, column_type in new_columns:
                if column_name not in columns:
                    print(f"  - Adding column: {column_name}")
                    conn.execute(f"""
                        ALTER TABLE session_summaries 
                        ADD COLUMN {column_name} {column_type}
                    """)
            
            # Update existing records with default values
            conn.execute("""
                UPDATE session_summaries 
                SET channel = COALESCE(channel, 'email'),
                    template_used = COALESCE(template_used, 'Unknown'),
                    pending_messages = COALESCE(pending_messages, 0),
                    cancelled_messages = COALESCE(cancelled_messages, 0),
                    success_rate = CASE 
                        WHEN total_messages > 0 
                        THEN (CAST(successful_messages AS REAL) / total_messages) * 100 
                        ELSE 0.0 
                    END
                WHERE channel IS NULL OR template_used IS NULL 
                   OR pending_messages IS NULL OR cancelled_messages IS NULL 
                   OR success_rate IS NULL
            """)
            
            conn.commit()
            print("  - Migration completed successfully")
            return True
            
    except Exception as e:
        print(f"  - Migration failed: {e}")
        return False


def main():
    """Run database migration."""
    print("=" * 60)
    print("MESSAGE LOGGING DATABASE MIGRATION")
    print("=" * 60)
    
    # Common database locations
    db_paths = [
        "message_logs.db",
        "test_logs.db",
        "test_logs_2.db",
        Path.home() / ".csc-reach" / "logs" / "message_logs.db",
        Path("logs") / "message_logs.db"
    ]
    
    migrated_count = 0
    
    for db_path in db_paths:
        db_path = Path(db_path)
        if db_path.exists():
            if migrate_database(str(db_path)):
                migrated_count += 1
        else:
            print(f"Database not found: {db_path}")
    
    print("\n" + "=" * 60)
    if migrated_count > 0:
        print(f"MIGRATION COMPLETED: {migrated_count} database(s) migrated")
    else:
        print("NO DATABASES FOUND TO MIGRATE")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())