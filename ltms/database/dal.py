"""Data Access Layer for LTMC database operations."""

import sqlite3
from typing import List, Dict, Any, Tuple


def create_resource(
    conn: sqlite3.Connection, 
    file_name: str, 
    resource_type: str, 
    created_at: str
) -> int:
    """Create a new resource in the database.
    
    Args:
        conn: Database connection
        file_name: Name of the file
        resource_type: Type of resource (e.g., 'document', 'code')
        created_at: ISO 8601 timestamp
        
    Returns:
        The ID of the created resource
    """
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Resources (file_name, type, created_at) VALUES (?, ?, ?)",
        (file_name, resource_type, created_at)
    )
    conn.commit()
    resource_id = cursor.lastrowid
    assert resource_id is not None
    return resource_id


def get_next_vector_id(conn: sqlite3.Connection) -> int:
    """Get the next sequential vector ID.
    
    This function ensures unique, sequential vector IDs by using a dedicated
    sequence table. This prevents the UNIQUE constraint failed error.
    
    Args:
        conn: Database connection
        
    Returns:
        The next sequential vector ID
    """
    cursor = conn.cursor()
    
    # Create sequence table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS VectorIdSequence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_vector_id INTEGER DEFAULT 0
        )
    """)
    
    # Insert next sequence value and get the ID
    cursor.execute("""
        INSERT INTO VectorIdSequence (last_vector_id) 
        VALUES (COALESCE((SELECT MAX(last_vector_id) FROM VectorIdSequence), 0) + 1)
    """)
    conn.commit()
    
    vector_id = cursor.lastrowid
    assert vector_id is not None
    return vector_id


def create_resource_chunks(
    conn: sqlite3.Connection, 
    resource_id: int, 
    chunks_data: List[Tuple[str, int]]
) -> List[int]:
    """Create resource chunks in the database.
    
    Args:
        conn: Database connection
        resource_id: ID of the parent resource
        chunks_data: List of (chunk_text, vector_id) tuples
        
    Returns:
        List of chunk IDs that were created
    """
    cursor = conn.cursor()
    chunk_ids = []
    
    for chunk_text, vector_id in chunks_data:
        cursor.execute(
            "INSERT INTO ResourceChunks (resource_id, chunk_text, vector_id) "
            "VALUES (?, ?, ?)",
            (resource_id, chunk_text, vector_id)
        )
        chunk_id = cursor.lastrowid
        assert chunk_id is not None
        chunk_ids.append(chunk_id)
    
    conn.commit()
    return chunk_ids


def get_chunks_by_vector_ids(
    conn: sqlite3.Connection, 
    vector_ids: List[int]
) -> List[Dict[str, Any]]:
    """Retrieve chunks by their vector IDs.
    
    Args:
        conn: Database connection
        vector_ids: List of vector IDs to retrieve
        
    Returns:
        List of chunk dictionaries with keys: chunk_id, resource_id, chunk_text, vector_id
    """
    cursor = conn.cursor()
    
    # Create placeholders for the IN clause
    placeholders = ','.join(['?' for _ in vector_ids])
    
    cursor.execute(
        f"SELECT id, resource_id, chunk_text, vector_id FROM ResourceChunks "
        f"WHERE vector_id IN ({placeholders})",
        vector_ids
    )
    
    results = cursor.fetchall()
    
    chunks = []
    for chunk_id, resource_id, chunk_text, vector_id in results:
        chunks.append({
            'chunk_id': chunk_id,
            'resource_id': resource_id,
            'chunk_text': chunk_text,
            'vector_id': vector_id
        })
    
    return chunks
