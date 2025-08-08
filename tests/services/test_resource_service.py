import tempfile
import os
import sqlite3
from datetime import datetime
from ltms.services.resource_service import add_resource
from ltms.database.schema import create_tables
from ltms.database.connection import get_db_connection, close_db_connection


def test_add_resource_creates_resource_and_chunks():
    """Test that add_resource creates a resource and its chunks."""
    # Create temporary database and index files
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = os.path.join(temp_dir, "test_index")
        
        try:
            # Create database and tables
            conn = get_db_connection(db_path)
            create_tables(conn)
            
            # Test resource addition
            file_name = "test_document.txt"
            resource_type = "document"
            content = (
                "This is the first sentence. "
                "This is the second sentence. "
                "This is the third sentence. "
                "This is the fourth sentence."
            )
            
            result = add_resource(
                conn=conn,
                index_path=index_path,
                file_name=file_name,
                resource_type=resource_type,
                content=content
            )
            
            # Verify result
            assert result['success'] is True
            assert 'resource_id' in result
            assert 'chunk_count' in result
            assert result['chunk_count'] > 0
            
            # Verify resource was created in database
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, file_name, type FROM Resources WHERE id = ?",
                (result['resource_id'],)
            )
            resource = cursor.fetchone()
            
            assert resource is not None
            assert resource[1] == file_name
            assert resource[2] == resource_type
            
            # Verify chunks were created
            cursor.execute(
                "SELECT COUNT(*) FROM ResourceChunks WHERE resource_id = ?",
                (result['resource_id'],)
            )
            chunk_count = cursor.fetchone()[0]
            assert chunk_count == result['chunk_count']
            
            # Verify vector index was created
            assert os.path.exists(index_path)
            
            conn.close()
            
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)


def test_add_resource_handles_empty_content():
    """Test that add_resource handles empty content gracefully."""
    # Create temporary database and index files
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = os.path.join(temp_dir, "test_index")
        
        try:
            # Create database and tables
            conn = get_db_connection(db_path)
            create_tables(conn)
            
            # Test with empty content
            result = add_resource(
                conn=conn,
                index_path=index_path,
                file_name="empty.txt",
                resource_type="document",
                content=""
            )
            
            # Verify result
            assert result['success'] is True
            assert result['chunk_count'] == 0
            
            conn.close()
            
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)


def test_add_resource_handles_single_sentence():
    """Test that add_resource handles single sentence content."""
    # Create temporary database and index files
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = os.path.join(temp_dir, "test_index")
        
        try:
            # Create database and tables
            conn = get_db_connection(db_path)
            create_tables(conn)
            
            # Test with single sentence
            content = "This is a single sentence."
            
            result = add_resource(
                conn=conn,
                index_path=index_path,
                file_name="single.txt",
                resource_type="document",
                content=content
            )
            
            # Verify result
            assert result['success'] is True
            assert result['chunk_count'] == 1
            
            conn.close()
            
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)


def test_add_resource_creates_vector_ids():
    """Test that add_resource creates proper vector IDs for chunks."""
    # Create temporary database and index files
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = os.path.join(temp_dir, "test_index")
        
        try:
            # Create database and tables
            conn = get_db_connection(db_path)
            create_tables(conn)
            
            # Test resource addition
            content = (
                "This is the first sentence. "
                "This is the second sentence. "
                "This is the third sentence."
            )
            
            result = add_resource(
                conn=conn,
                index_path=index_path,
                file_name="test.txt",
                resource_type="document",
                content=content
            )
            
            # Verify vector IDs were created
            cursor = conn.cursor()
            cursor.execute(
                "SELECT vector_id FROM ResourceChunks WHERE resource_id = ? ORDER BY vector_id",
                (result['resource_id'],)
            )
            vector_ids = [row[0] for row in cursor.fetchall()]
            
            # Should have sequential vector IDs starting from 0
            assert len(vector_ids) == result['chunk_count']
            assert vector_ids == list(range(len(vector_ids)))
            
            conn.close()
            
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)
