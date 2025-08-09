"""Database schema module for LTMC."""

import sqlite3


def create_tables(conn: sqlite3.Connection) -> None:
    """Create all database tables if they don't exist.
    
    Args:
        conn: SQLite database connection
    """
    cursor = conn.cursor()
    
    # Create Resources table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT,
            type TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    # Create ResourceChunks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ResourceChunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_id INTEGER,
            chunk_text TEXT NOT NULL,
            vector_id INTEGER UNIQUE NOT NULL,
            FOREIGN KEY (resource_id) REFERENCES Resources (id)
        )
    """)
    
    # Create ChatHistory table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ChatHistory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            agent_name TEXT,
            metadata TEXT,
            source_tool TEXT
        )
    """)
    
    # Create ContextLinks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ContextLinks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER,
            chunk_id INTEGER,
            FOREIGN KEY (message_id) REFERENCES ChatHistory (id),
            FOREIGN KEY (chunk_id) REFERENCES ResourceChunks (id)
        )
    """)

    # Create Summaries table (for auto-summary ingestion)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_id INTEGER,
            doc_id TEXT,
            summary_text TEXT NOT NULL,
            model TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (resource_id) REFERENCES Resources (id)
        )
    """)
    
    # Create Todos table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT DEFAULT 'medium',
            completed BOOLEAN DEFAULT 0,
            created_at TEXT NOT NULL,
            completed_at TEXT
        )
    """)
    
    # Create CodePatterns table for code pattern learning
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS CodePatterns (
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
    
    # Create CodePatternContext table for additional context
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS CodePatternContext (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_id INTEGER,
            context_type TEXT NOT NULL,
            context_data TEXT NOT NULL,
            FOREIGN KEY (pattern_id) REFERENCES CodePatterns (id)
        )
    """)
    
    # Create VectorIdSequence table for managing vector IDs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS VectorIdSequence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_vector_id INTEGER DEFAULT 0
        )
    """)
    
    # Initialize vector ID sequence if empty
    cursor.execute("INSERT OR IGNORE INTO VectorIdSequence (id, last_vector_id) VALUES (1, 0)")

    # Add source_tool column to existing ChatHistory tables (migration)
    try:
        cursor.execute("ALTER TABLE ChatHistory ADD COLUMN source_tool TEXT")
        conn.commit()
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e).lower():
            # Re-raise if it's not a duplicate column error
            raise
        # Column already exists, continue
    
    conn.commit()
