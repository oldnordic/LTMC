import sqlite3
from ltms.database.schema import create_tables


def test_create_tables_creates_all_four_tables():
    """Test that create_tables function creates all four required tables."""
    # Create a temporary, in-memory SQLite database connection
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    # Call the create_tables function
    create_tables(conn)
    
    # Query the database's sqlite_master table to verify that the four tables exist
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name IN (
            'Resources', 'ResourceChunks', 'ChatHistory', 'ContextLinks'
        )
        ORDER BY name
    """)
    
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    # Assert that the count of existing tables is 4
    assert len(existing_tables) == 4, (
        f"Expected 4 tables, but found {len(existing_tables)}: "
        f"{existing_tables}"
    )
    
    # Also verify the specific table names
    expected_tables = [
        'ChatHistory', 'ContextLinks', 'ResourceChunks', 'Resources'
    ]
    assert set(existing_tables) == set(expected_tables), (
        f"Expected tables {expected_tables}, but found {existing_tables}"
    )
    
    conn.close()
