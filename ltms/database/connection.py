"""Database connection management for LTMC."""

import sqlite3


def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Get a SQLite database connection.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        SQLite database connection
    """
    return sqlite3.connect(db_path)


def close_db_connection(conn: sqlite3.Connection) -> None:
    """Close a database connection.
    
    Args:
        conn: SQLite database connection to close
    """
    if conn:
        conn.close()
