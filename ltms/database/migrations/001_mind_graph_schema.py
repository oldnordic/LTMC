"""
Mind Graph Schema Migration Script
File: ltms/database/migrations/001_mind_graph_schema.py
Purpose: Add Mind Graph tables to existing LTMC database
Status: Phase 1 - Real Database Implementation
"""

import sqlite3
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

class MindGraphMigration:
    """Real database migration for Mind Graph schema."""
    
    def __init__(self, db_path: str):
        """Initialize migration with database path.
        
        Args:
            db_path: Path to LTMC SQLite database
        """
        self.db_path = db_path
        self.migration_version = "001_mind_graph_schema"
        
    def apply_migration(self) -> bool:
        """Apply Mind Graph schema migration with real database operations.
        
        Returns:
            bool: True if migration successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            logger.info(f"Applying migration {self.migration_version}")
            
            # Check if migration already applied
            if self._is_migration_applied(cursor):
                logger.info(f"Migration {self.migration_version} already applied")
                conn.close()
                return True
            
            # Begin transaction
            cursor.execute("BEGIN TRANSACTION")
            
            try:
                # Create Mind Graph tables
                self._create_mind_graph_agents_table(cursor)
                self._create_mind_graph_changes_table(cursor)
                self._create_mind_graph_reasons_table(cursor)
                self._create_mind_graph_codefiles_table(cursor)
                self._create_mind_graph_relationships_table(cursor)
                
                # Create indexes for performance
                self._create_indexes(cursor)
                
                # Record migration
                self._record_migration(cursor)
                
                # Commit transaction
                cursor.execute("COMMIT")
                conn.close()
                
                logger.info(f"Migration {self.migration_version} applied successfully")
                return True
                
            except Exception as e:
                cursor.execute("ROLLBACK")
                conn.close()
                logger.error(f"Migration {self.migration_version} failed: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Migration connection failed: {e}")
            return False
    
    def _is_migration_applied(self, cursor: sqlite3.Cursor) -> bool:
        """Check if migration is already applied."""
        # Create migrations table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT UNIQUE NOT NULL,
                applied_at TEXT NOT NULL
            )
        """)
        
        # Check if this migration exists
        cursor.execute(
            "SELECT COUNT(*) FROM schema_migrations WHERE version = ?",
            (self.migration_version,)
        )
        
        return cursor.fetchone()[0] > 0
    
    def _record_migration(self, cursor: sqlite3.Cursor):
        """Record migration in schema_migrations table."""
        cursor.execute(
            "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
            (self.migration_version, datetime.now(timezone.utc).isoformat())
        )
    
    def _create_mind_graph_agents_table(self, cursor: sqlite3.Cursor):
        """Create MindGraph_Agents table with real schema."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MindGraph_Agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT UNIQUE NOT NULL,
                agent_name TEXT NOT NULL,
                agent_type TEXT NOT NULL,  -- 'human', 'claude-sonnet-4', 'subagent', etc.
                created_at TEXT NOT NULL,
                last_active_at TEXT,
                session_count INTEGER DEFAULT 0,
                total_changes INTEGER DEFAULT 0,
                metadata TEXT,  -- JSON
                UNIQUE(agent_id)
            )
        """)
        
        logger.info("Created MindGraph_Agents table")
    
    def _create_mind_graph_changes_table(self, cursor: sqlite3.Cursor):
        """Create MindGraph_Changes table with foreign key to existing tables."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MindGraph_Changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                change_id TEXT UNIQUE NOT NULL,
                agent_id TEXT NOT NULL,
                change_type TEXT NOT NULL,  -- 'code_edit', 'file_create', 'blueprint_update', etc.
                file_path TEXT,
                lines_changed INTEGER,
                change_summary TEXT NOT NULL,
                change_details TEXT,  -- JSON with detailed change info
                timestamp TEXT NOT NULL,
                session_id TEXT,
                conversation_id TEXT,
                blueprint_id TEXT,  -- Links to existing blueprints
                task_id TEXT,  -- Links to existing tasks
                tool_invocation_id INTEGER,  -- Links to subagent_tool_invocations
                before_hash TEXT,  -- File hash before change
                after_hash TEXT,   -- File hash after change
                impact_score REAL DEFAULT 0.0,  -- Estimated impact
                FOREIGN KEY (agent_id) REFERENCES MindGraph_Agents (agent_id),
                FOREIGN KEY (tool_invocation_id) REFERENCES subagent_tool_invocations (id),
                FOREIGN KEY (blueprint_id) REFERENCES blueprints (id),
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        """)
        
        logger.info("Created MindGraph_Changes table")
    
    def _create_mind_graph_reasons_table(self, cursor: sqlite3.Cursor):
        """Create MindGraph_Reasons table linking to existing systems."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MindGraph_Reasons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reason_id TEXT UNIQUE NOT NULL,
                reason_type TEXT NOT NULL,  -- 'bug_fix', 'feature_request', 'blueprint_task', 'user_request'
                description TEXT NOT NULL,
                context TEXT,  -- Additional context
                reasoning_chain_id TEXT,  -- Groups related reasons
                blueprint_id TEXT,  -- Links to existing blueprints  
                task_id TEXT,  -- Links to existing tasks/stories
                chat_message_id INTEGER,  -- Links to triggering chat message
                parent_reason_id TEXT,  -- For reason hierarchies
                priority_level INTEGER DEFAULT 1,
                confidence_score REAL DEFAULT 1.0,
                created_at TEXT NOT NULL,
                resolved_at TEXT,
                metadata TEXT,  -- JSON
                FOREIGN KEY (blueprint_id) REFERENCES blueprints (id),
                FOREIGN KEY (task_id) REFERENCES tasks (id),
                FOREIGN KEY (chat_message_id) REFERENCES chat_messages (id),
                FOREIGN KEY (parent_reason_id) REFERENCES MindGraph_Reasons (reason_id)
            )
        """)
        
        logger.info("Created MindGraph_Reasons table")
    
    def _create_mind_graph_codefiles_table(self, cursor: sqlite3.Cursor):
        """Create MindGraph_CodeFiles table for file tracking."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MindGraph_CodeFiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT UNIQUE NOT NULL,
                file_path TEXT UNIQUE NOT NULL,
                file_type TEXT,  -- 'python', 'javascript', 'markdown', etc.
                project_id TEXT,
                current_version INTEGER DEFAULT 1,
                lines_of_code INTEGER DEFAULT 0,
                complexity_score REAL DEFAULT 0.0,
                last_change_id TEXT,  -- References MindGraph_Changes
                created_at TEXT NOT NULL,
                last_modified TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                metadata TEXT,  -- JSON with file stats, LOC, etc.
                FOREIGN KEY (project_id) REFERENCES projects (id),
                FOREIGN KEY (last_change_id) REFERENCES MindGraph_Changes (change_id)
            )
        """)
        
        logger.info("Created MindGraph_CodeFiles table")
    
    def _create_mind_graph_relationships_table(self, cursor: sqlite3.Cursor):
        """Create MindGraph_Relationships table for SQLite backup of Neo4j relationships."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MindGraph_Relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                relationship_id TEXT UNIQUE NOT NULL,
                source_type TEXT NOT NULL,  -- 'change', 'agent', 'reason', 'codefile'
                source_id TEXT NOT NULL,
                target_type TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relationship_type TEXT NOT NULL,  -- 'MODIFIES', 'MOTIVATED_BY', 'MADE_CHANGE', etc.
                strength REAL DEFAULT 1.0,  -- Relationship strength
                confidence REAL DEFAULT 1.0,  -- Confidence in relationship
                properties TEXT,  -- JSON
                created_at TEXT NOT NULL,
                last_verified_at TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        logger.info("Created MindGraph_Relationships table")
    
    def _create_indexes(self, cursor: sqlite3.Cursor):
        """Create performance indexes for Mind Graph tables."""
        indexes = [
            # Agent indexes
            "CREATE INDEX IF NOT EXISTS idx_mindgraph_agents_type ON MindGraph_Agents (agent_type)",
            "CREATE INDEX IF NOT EXISTS idx_mindgraph_agents_active ON MindGraph_Agents (last_active_at)",
            
            # Changes indexes
            "CREATE INDEX IF NOT EXISTS idx_mindgraph_changes_agent ON MindGraph_Changes (agent_id)",
            "CREATE INDEX IF NOT EXISTS idx_mindgraph_changes_timestamp ON MindGraph_Changes (timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_mindgraph_changes_file ON MindGraph_Changes (file_path)",
            "CREATE INDEX IF NOT EXISTS idx_mindgraph_changes_type ON MindGraph_Changes (change_type)",
            "CREATE INDEX IF NOT EXISTS idx_mindgraph_changes_session ON MindGraph_Changes (session_id)",
            "CREATE INDEX IF NOT EXISTS idx_mindgraph_changes_blueprint ON MindGraph_Changes (blueprint_id)",
            
            # Reasons indexes
            "CREATE INDEX IF NOT EXISTS idx_mindgraph_reasons_type ON MindGraph_Reasons (reason_type)",
            "CREATE INDEX IF NOT EXISTS idx_mindgraph_reasons_chain ON MindGraph_Reasons (reasoning_chain_id)",
            "CREATE INDEX IF NOT EXISTS idx_mindgraph_reasons_blueprint ON MindGraph_Reasons (blueprint_id)",
            "CREATE INDEX IF NOT EXISTS idx_mindgraph_reasons_chat ON MindGraph_Reasons (chat_message_id)",
            "CREATE INDEX IF NOT EXISTS idx_mindgraph_reasons_parent ON MindGraph_Reasons (parent_reason_id)",
            
            # CodeFiles indexes
            "CREATE INDEX IF NOT EXISTS idx_mindgraph_codefiles_path ON MindGraph_CodeFiles (file_path)",
            "CREATE INDEX IF NOT EXISTS idx_mindgraph_codefiles_project ON MindGraph_CodeFiles (project_id)",
            "CREATE INDEX IF NOT EXISTS idx_mindgraph_codefiles_type ON MindGraph_CodeFiles (file_type)",
            "CREATE INDEX IF NOT EXISTS idx_mindgraph_codefiles_modified ON MindGraph_CodeFiles (last_modified)",
            
            # Relationships indexes  
            "CREATE INDEX IF NOT EXISTS idx_mindgraph_rels_source ON MindGraph_Relationships (source_type, source_id)",
            "CREATE INDEX IF NOT EXISTS idx_mindgraph_rels_target ON MindGraph_Relationships (target_type, target_id)",
            "CREATE INDEX IF NOT EXISTS idx_mindgraph_rels_type ON MindGraph_Relationships (relationship_type)",
            "CREATE INDEX IF NOT EXISTS idx_mindgraph_rels_active ON MindGraph_Relationships (is_active)",
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
            
        logger.info("Created Mind Graph performance indexes")


def apply_mind_graph_migration(db_path: str) -> bool:
    """Apply Mind Graph migration to LTMC database.
    
    Args:
        db_path: Path to LTMC SQLite database
        
    Returns:
        bool: True if successful, False otherwise
    """
    migration = MindGraphMigration(db_path)
    return migration.apply_migration()


def rollback_mind_graph_migration(db_path: str) -> bool:
    """Rollback Mind Graph migration (for testing/development).
    
    Args:
        db_path: Path to LTMC SQLite database
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Drop Mind Graph tables in reverse order
        tables_to_drop = [
            'MindGraph_Relationships',
            'MindGraph_CodeFiles', 
            'MindGraph_Reasons',
            'MindGraph_Changes',
            'MindGraph_Agents'
        ]
        
        cursor.execute("BEGIN TRANSACTION")
        
        try:
            for table in tables_to_drop:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                logger.info(f"Dropped table {table}")
            
            # Remove migration record
            cursor.execute(
                "DELETE FROM schema_migrations WHERE version = ?",
                ("001_mind_graph_schema",)
            )
            
            cursor.execute("COMMIT")
            conn.close()
            
            logger.info("Mind Graph migration rolled back successfully")
            return True
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            conn.close()
            logger.error(f"Migration rollback failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Rollback connection failed: {e}")
        return False


if __name__ == "__main__":
    # Test migration locally
    import os
    
    db_path = os.environ.get('LTMC_DATA_DIR', '/home/feanor/Projects/Data') + '/ltmc.db'
    
    print(f"Testing Mind Graph migration on {db_path}")
    
    if apply_mind_graph_migration(db_path):
        print("✅ Migration applied successfully")
    else:
        print("❌ Migration failed")