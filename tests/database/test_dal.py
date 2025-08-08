import sqlite3
import tempfile
import os
from datetime import datetime
from ltms.database.dal import (
    create_resource, create_resource_chunks, get_chunks_by_vector_ids
)
from ltms.database.schema import create_tables


def test_create_resource_creates_new_resource():
    """Test that create_resource creates a new resource in the database."""
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    try:
        conn = sqlite3.connect(db_path)
        create_tables(conn)
        
        # Create a resource
        file_name = "test_document.txt"
        resource_type = "document"
        created_at = datetime.now().isoformat()
        
        resource_id = create_resource(conn, file_name, resource_type, created_at)
        
        # Verify the resource was created
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, file_name, type, created_at FROM Resources WHERE id = ?",
            (resource_id,)
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == resource_id
        assert result[1] == file_name
        assert result[2] == resource_type
        assert result[3] == created_at
        
        conn.close()
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_create_resource_chunks_creates_chunks():
    """Test that create_resource_chunks creates chunks in the database."""
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    try:
        conn = sqlite3.connect(db_path)
        create_tables(conn)
        
        # Create a resource first
        file_name = "test_document.txt"
        resource_type = "document"
        created_at = datetime.now().isoformat()
        
        resource_id = create_resource(conn, file_name, resource_type, created_at)
        
        # Create chunks
        chunks_data = [
            ("This is chunk 1", 1),
            ("This is chunk 2", 2),
            ("This is chunk 3", 3)
        ]
        
        chunk_ids = create_resource_chunks(conn, resource_id, chunks_data)
        
        # Verify chunks were created
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, resource_id, chunk_text, vector_id FROM ResourceChunks WHERE resource_id = ?",
            (resource_id,)
        )
        results = cursor.fetchall()
        
        assert len(results) == 3
        assert len(chunk_ids) == 3
        
        # Verify each chunk
        for i, (chunk_id, res_id, chunk_text, vector_id) in enumerate(results):
            assert res_id == resource_id
            assert chunk_text == chunks_data[i][0]
            assert vector_id == chunks_data[i][1]
            assert chunk_id in chunk_ids
        
        conn.close()
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_get_chunks_by_vector_ids_retrieves_chunks():
    """Test that get_chunks_by_vector_ids retrieves chunks by vector IDs."""
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    try:
        conn = sqlite3.connect(db_path)
        create_tables(conn)
        
        # Create a resource and chunks
        file_name = "test_document.txt"
        resource_type = "document"
        created_at = datetime.now().isoformat()
        
        resource_id = create_resource(conn, file_name, resource_type, created_at)
        
        chunks_data = [
            ("This is chunk 1", 1),
            ("This is chunk 2", 2),
            ("This is chunk 3", 3)
        ]
        
        create_resource_chunks(conn, resource_id, chunks_data)
        
        # Retrieve chunks by vector IDs
        vector_ids = [1, 3]  # Get chunks 1 and 3
        chunks = get_chunks_by_vector_ids(conn, vector_ids)
        
        # Verify we got the right chunks
        assert len(chunks) == 2
        
        # Verify chunk content
        chunk_texts = [chunk['chunk_text'] for chunk in chunks]
        assert "This is chunk 1" in chunk_texts
        assert "This is chunk 3" in chunk_texts
        assert "This is chunk 2" not in chunk_texts
        
        # Verify chunk structure
        for chunk in chunks:
            assert 'chunk_id' in chunk
            assert 'resource_id' in chunk
            assert 'chunk_text' in chunk
            assert 'vector_id' in chunk
            assert chunk['resource_id'] == resource_id
        
        conn.close()
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
