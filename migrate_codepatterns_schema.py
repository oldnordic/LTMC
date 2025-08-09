#!/usr/bin/env python3
"""
CodePatterns table schema migration script.
CRITICAL: Fixes missing columns that break 3 MCP tools.
"""

import sqlite3
import os
import shutil
from datetime import datetime

DB_PATH = '/home/feanor/Projects/lmtc/ltmc.db'
BACKUP_PATH = f'/home/feanor/Projects/lmtc/ltmc_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'

def backup_database():
    """Create backup before migration."""
    print(f"Creating backup: {BACKUP_PATH}")
    shutil.copy2(DB_PATH, BACKUP_PATH)
    return BACKUP_PATH

def migrate_codepatterns_table():
    """Migrate CodePatterns table to expected schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("Starting CodePatterns schema migration...")
        
        # Check if table exists and get current schema
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='CodePatterns'")
        current_schema = cursor.fetchone()
        print(f"Current schema: {current_schema[0] if current_schema else 'Table not found'}")
        
        # Check if table has data
        cursor.execute("SELECT COUNT(*) FROM CodePatterns")
        row_count = cursor.fetchone()[0]
        print(f"Existing rows: {row_count}")
        
        if row_count == 0:
            # No data - safe to DROP and recreate
            print("No data found - dropping and recreating table...")
            cursor.execute("DROP TABLE IF EXISTS CodePatterns")
            
            # Create new table with correct schema
            cursor.execute("""
                CREATE TABLE CodePatterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    function_name TEXT,
                    file_name TEXT,
                    module_name TEXT,
                    input_prompt TEXT NOT NULL,
                    generated_code TEXT NOT NULL,
                    result TEXT CHECK(result IN ('pass', 'fail', 'partial')) NOT NULL,
                    execution_time_ms INTEGER,
                    error_message TEXT,
                    tags TEXT,
                    created_at TEXT NOT NULL,
                    vector_id INTEGER UNIQUE,
                    FOREIGN KEY (vector_id) REFERENCES ResourceChunks (id)
                )
            """)
            
        else:
            # Data exists - use ALTER TABLE approach
            print("Data exists - using ALTER TABLE migration...")
            
            # Add missing columns one by one
            missing_columns = [
                ("function_name", "TEXT"),
                ("file_name", "TEXT"),
                ("module_name", "TEXT"),
                ("tags", "TEXT"),
                ("vector_id", "INTEGER")
            ]
            
            for col_name, col_type in missing_columns:
                try:
                    cursor.execute(f"ALTER TABLE CodePatterns ADD COLUMN {col_name} {col_type}")
                    print(f"Added column: {col_name} {col_type}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"Column {col_name} already exists - skipping")
                    else:
                        raise
            
            # Rename execution_time to execution_time_ms if needed
            try:
                cursor.execute("ALTER TABLE CodePatterns ADD COLUMN execution_time_ms INTEGER")
                cursor.execute("UPDATE CodePatterns SET execution_time_ms = CAST(execution_time * 1000 AS INTEGER) WHERE execution_time IS NOT NULL")
                print("Converted execution_time to execution_time_ms")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e):
                    raise
        
        conn.commit()
        
        # Verify new schema
        cursor.execute("PRAGMA table_info(CodePatterns)")
        columns = cursor.fetchall()
        print("New schema columns:")
        for col in columns:
            print(f"  {col[1]} {col[2]} {'NOT NULL' if col[3] else ''}")
        
        print("Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def validate_migration():
    """Validate that migration was successful."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check all expected columns exist
        cursor.execute("PRAGMA table_info(CodePatterns)")
        columns = [col[1] for col in cursor.fetchall()]
        
        expected_columns = [
            'id', 'function_name', 'file_name', 'module_name', 
            'input_prompt', 'generated_code', 'result',
            'execution_time_ms', 'error_message', 'tags', 
            'created_at', 'vector_id'
        ]
        
        missing = [col for col in expected_columns if col not in columns]
        if missing:
            print(f"VALIDATION FAILED - Missing columns: {missing}")
            return False
            
        print("VALIDATION PASSED - All expected columns present")
        return True
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("LTMC CodePatterns Schema Migration")
    print("=" * 50)
    
    # Create backup
    backup_path = backup_database()
    
    # Run migration
    success = migrate_codepatterns_table()
    
    if success:
        # Validate migration
        if validate_migration():
            print(f"\n✅ MIGRATION SUCCESSFUL")
            print(f"Backup saved to: {backup_path}")
        else:
            print(f"\n❌ MIGRATION VALIDATION FAILED")
            print(f"Restore from backup: {backup_path}")
    else:
        print(f"\n❌ MIGRATION FAILED")
        print(f"Restore from backup: {backup_path}")