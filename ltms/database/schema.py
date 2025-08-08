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
            metadata TEXT
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
    
    conn.commit()
