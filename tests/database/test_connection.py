import sqlite3
import tempfile
import os
from ltms.database.connection import get_db_connection, close_db_connection


def test_get_db_connection_creates_valid_connection():
    """Test that get_db_connection creates a valid SQLite connection."""
    # Create a temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    try:
        # Get database connection
        conn = get_db_connection(db_path)
        
        # Verify it's a valid SQLite connection
        assert isinstance(conn, sqlite3.Connection)
        
        # Test that we can execute a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1
        
        # Close the connection
        close_db_connection(conn)
        
    finally:
        # Clean up the temporary file
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_close_db_connection_properly_closes():
    """Test that close_db_connection properly closes the database connection."""
    # Create a temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    try:
        # Get database connection
        conn = get_db_connection(db_path)
        
        # Verify connection is working (not closed)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1
        
        # Close the connection
        close_db_connection(conn)
        
        # Verify connection is closed by trying to execute a query
        # This should raise a ProgrammingError if the connection is closed
        try:
            cursor.execute("SELECT 1")
            assert False, "Connection should be closed"
        except sqlite3.ProgrammingError:
            # Expected behavior - connection is closed
            pass
        
    finally:
        # Clean up the temporary file
        if os.path.exists(db_path):
            os.unlink(db_path)
