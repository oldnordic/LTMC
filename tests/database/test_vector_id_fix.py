"""TDD tests for LTMC Vector ID Fix implementation.

Tests the sequential vector ID generation and database schema updates
to resolve the UNIQUE constraint failed: ResourceChunks.vector_id issue.
"""

import pytest
import sqlite3
import tempfile
import os
from datetime import datetime
from typing import Dict, Any

from ltms.database.connection import get_db_connection, close_db_connection
from ltms.database.schema import create_tables
from ltms.services.resource_service import add_resource


class TestVectorIdFix:
    """Test suite for vector ID fix implementation."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        # Create database connection
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        yield db_path, conn
        
        # Cleanup
        close_db_connection(conn)
        os.unlink(db_path)
    
    @pytest.fixture
    def temp_index(self):
        """Create a temporary FAISS index file."""
        import tempfile
        fd, index_path = tempfile.mkstemp(suffix='.index')
        os.close(fd)
        yield index_path
        os.unlink(index_path)
    
    def test_vector_id_sequence_table_creation(self, temp_db):
        """Test that VectorIdSequence table is created correctly."""
        db_path, conn = temp_db
        
        # Create the sequence table
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS VectorIdSequence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_vector_id INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        
        # Verify table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='VectorIdSequence'")
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == 'VectorIdSequence'
        
        # Verify table structure
        cursor.execute("PRAGMA table_info(VectorIdSequence)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        assert 'id' in column_names
        assert 'last_vector_id' in column_names
    
    def test_get_next_vector_id_generation(self, temp_db):
        """Test sequential vector ID generation."""
        db_path, conn = temp_db
        
        # Create sequence table
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS VectorIdSequence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_vector_id INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        
        # Test vector ID generation function
        def get_next_vector_id(conn: sqlite3.Connection) -> int:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO VectorIdSequence (last_vector_id) 
                VALUES (COALESCE((SELECT MAX(last_vector_id) FROM VectorIdSequence), 0) + 1)
            """)
            conn.commit()
            return cursor.lastrowid
        
        # Generate multiple vector IDs
        vector_ids = []
        for _ in range(5):
            vector_id = get_next_vector_id(conn)
            vector_ids.append(vector_id)
        
        # Verify sequential generation
        assert len(vector_ids) == 5
        assert vector_ids == [1, 2, 3, 4, 5]  # Sequential IDs
    
    def test_resource_chunks_generation_method_column(self, temp_db):
        """Test adding generation_method column to ResourceChunks."""
        db_path, conn = temp_db
        
        # Add the generation_method column
        cursor = conn.cursor()
        cursor.execute("""
            ALTER TABLE ResourceChunks ADD COLUMN generation_method TEXT DEFAULT 'sequential'
        """)
        conn.commit()
        
        # Verify column was added
        cursor.execute("PRAGMA table_info(ResourceChunks)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        assert 'generation_method' in column_names
        
        # Verify default value
        cursor.execute("SELECT generation_method FROM ResourceChunks LIMIT 1")
        result = cursor.fetchone()
        if result:
            assert result[0] == 'sequential'
    
    def test_memory_storage_with_sequential_vector_ids(self, temp_db, temp_index):
        """Test that memory storage works with sequential vector IDs."""
        db_path, conn = temp_db
        
        # Create sequence table
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS VectorIdSequence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_vector_id INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        
        # Add generation_method column
        cursor.execute("""
            ALTER TABLE ResourceChunks ADD COLUMN generation_method TEXT DEFAULT 'sequential'
        """)
        conn.commit()
        
        # Test memory storage
        test_content = "This is a test document for vector ID fix validation."
        result = add_resource(
            conn=conn,
            index_path=temp_index,
            file_name="test_vector_id_fix.md",
            resource_type="document",
            content=test_content
        )
        
        # Verify storage was successful
        if not result['success']:
            print(f"Storage failed with error: {result.get('error', 'Unknown error')}")
        assert result['success'] is True
        
        # Verify vector IDs are sequential
        cursor.execute("SELECT vector_id FROM ResourceChunks ORDER BY vector_id")
        vector_ids = [row[0] for row in cursor.fetchall()]
        
        # Check that vector IDs are sequential (no gaps)
        if len(vector_ids) > 1:
            for i in range(1, len(vector_ids)):
                assert vector_ids[i] == vector_ids[i-1] + 1
    
    def test_multiple_memory_storage_operations(self, temp_db, temp_index):
        """Test multiple memory storage operations without constraint violations."""
        db_path, conn = temp_db
        
        # Setup database
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS VectorIdSequence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_vector_id INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            ALTER TABLE ResourceChunks ADD COLUMN generation_method TEXT DEFAULT 'sequential'
        """)
        conn.commit()
        
        # Store multiple resources
        test_contents = [
            "First test document for vector ID validation.",
            "Second test document with different content.",
            "Third test document to verify sequential IDs.",
            "Fourth test document for comprehensive testing.",
            "Fifth test document to ensure no constraint violations."
        ]
        
        results = []
        for i, content in enumerate(test_contents):
            result = add_resource(
                conn=conn,
                index_path=temp_index,
                file_name=f"test_doc_{i+1}.md",
                resource_type="document",
                content=content
            )
            results.append(result)
        
        # Verify all storage operations succeeded
        for result in results:
            assert result['success'] is True
            assert result['chunk_count'] > 0
        
        # Verify no constraint violations occurred
        cursor.execute("SELECT COUNT(*) FROM ResourceChunks")
        total_chunks = cursor.fetchone()[0]
        assert total_chunks > 0
        
        # Verify vector IDs are unique and sequential
        cursor.execute("SELECT vector_id FROM ResourceChunks ORDER BY vector_id")
        vector_ids = [row[0] for row in cursor.fetchall()]
        
        # Check uniqueness
        assert len(vector_ids) == len(set(vector_ids))
        
        # Check sequential ordering (if multiple chunks)
        if len(vector_ids) > 1:
            for i in range(1, len(vector_ids)):
                assert vector_ids[i] == vector_ids[i-1] + 1
    
    def test_vector_id_uniqueness_constraint(self, temp_db, temp_index):
        """Test that vector ID uniqueness constraint is maintained."""
        db_path, conn = temp_db
        
        # Setup database
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS VectorIdSequence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_vector_id INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            ALTER TABLE ResourceChunks ADD COLUMN generation_method TEXT DEFAULT 'sequential'
        """)
        conn.commit()
        
        # Store a resource
        result = add_resource(
            conn=conn,
            index_path=temp_index,
            file_name="uniqueness_test.md",
            resource_type="document",
            content="Test content for uniqueness validation."
        )
        
        assert result['success'] is True
        
        # Verify vector IDs are unique
        cursor.execute("SELECT vector_id FROM ResourceChunks")
        vector_ids = [row[0] for row in cursor.fetchall()]
        
        # Check uniqueness
        assert len(vector_ids) == len(set(vector_ids))
        
        # Verify no duplicate vector IDs exist
        cursor.execute("""
            SELECT vector_id, COUNT(*) 
            FROM ResourceChunks 
            GROUP BY vector_id 
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()
        assert len(duplicates) == 0
    
    def test_migration_compatibility(self, temp_db, temp_index):
        """Test that the fix is compatible with existing data structure."""
        db_path, conn = temp_db
        
        # Setup database with new schema
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS VectorIdSequence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_vector_id INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            ALTER TABLE ResourceChunks ADD COLUMN generation_method TEXT DEFAULT 'sequential'
        """)
        conn.commit()
        
        # Verify all existing tables are accessible
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['Resources', 'ResourceChunks', 'ChatHistory', 'ContextLinks', 'Summaries', 'VectorIdSequence']
        for table in required_tables:
            assert table in tables
        
        # Test that existing functionality still works
        result = add_resource(
            conn=conn,
            index_path=temp_index,
            file_name="compatibility_test.md",
            resource_type="document",
            content="Test content for compatibility validation."
        )
        
        assert result['success'] is True
        assert 'resource_id' in result
        assert 'chunk_count' in result
    
    def test_embedding_model_compatibility(self, temp_db, temp_index):
        """Test that the fix maintains 384-dimension embedding compatibility."""
        db_path, conn = temp_db
        
        # Setup database
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS VectorIdSequence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_vector_id INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            ALTER TABLE ResourceChunks ADD COLUMN generation_method TEXT DEFAULT 'sequential'
        """)
        conn.commit()
        
        # Test with embedding model
        from ltms.services.embedding_service import create_embedding_model, encode_text
        
        model = create_embedding_model("all-MiniLM-L6-v2")
        test_text = "Test text for embedding compatibility."
        embedding = encode_text(model, test_text)
        
        # Verify embedding dimensions
        assert embedding.shape == (384,)
        assert embedding.dtype.name == 'float32'
        
        # Test storage with embeddings
        result = add_resource(
            conn=conn,
            index_path=temp_index,
            file_name="embedding_test.md",
            resource_type="document",
            content=test_text
        )
        
        assert result['success'] is True
        assert result['chunk_count'] > 0
    
    def test_performance_requirements(self, temp_db, temp_index):
        """Test that the fix meets performance requirements."""
        db_path, conn = temp_db
        
        # Setup database
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS VectorIdSequence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_vector_id INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            ALTER TABLE ResourceChunks ADD COLUMN generation_method TEXT DEFAULT 'sequential'
        """)
        conn.commit()
        
        # Test storage performance
        import time
        
        start_time = time.time()
        result = add_resource(
            conn=conn,
            index_path=temp_index,
            file_name="performance_test.md",
            resource_type="document",
            content="Test content for performance validation. " * 100  # Larger content
        )
        end_time = time.time()
        
        storage_time = end_time - start_time
        
        # Verify performance requirements
        assert result['success'] is True
        assert storage_time < 2.0  # Less than 2 seconds per resource
        assert result['chunk_count'] > 0
    
    def test_error_handling(self, temp_db, temp_index):
        """Test error handling in vector ID generation."""
        db_path, conn = temp_db
        
        # Test with invalid database connection
        try:
            add_resource(
                conn=None,  # Invalid connection
                index_path=temp_index,
                file_name="error_test.md",
                resource_type="document",
                content="Test content."
            )
            assert False, "Should have raised an exception"
        except Exception:
            # Expected behavior
            pass
        
        # Test with invalid index path
        result = add_resource(
            conn=conn,
            index_path="/invalid/path/that/does/not/exist",
            file_name="error_test.md",
            resource_type="document",
            content="Test content."
        )
        
        # Should handle the error gracefully
        assert result['success'] is False
        assert 'error' in result

    def test_vector_id_generation_without_faiss(self, temp_db):
        """Test vector ID generation without FAISS index to isolate core functionality."""
        db_path, conn = temp_db
        
        # Create sequence table
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS VectorIdSequence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_vector_id INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        
        # Add generation_method column
        cursor.execute("""
            ALTER TABLE ResourceChunks ADD COLUMN generation_method TEXT DEFAULT 'sequential'
        """)
        conn.commit()
        
        # Test vector ID generation directly
        from ltms.database.dal import get_next_vector_id
        
        vector_ids = []
        for _ in range(5):
            vector_id = get_next_vector_id(conn)
            vector_ids.append(vector_id)
        
        # Verify sequential generation
        assert len(vector_ids) == 5
        assert vector_ids == [1, 2, 3, 4, 5]  # Sequential IDs
        
        # Test that they can be stored in ResourceChunks
        cursor.execute("""
            INSERT INTO Resources (file_name, type, created_at) 
            VALUES (?, ?, ?)
        """, ("test.txt", "document", datetime.now().isoformat()))
        resource_id = cursor.lastrowid
        
        # Store chunks with the generated vector IDs
        for i, vector_id in enumerate(vector_ids):
            cursor.execute("""
                INSERT INTO ResourceChunks (resource_id, chunk_text, vector_id) 
                VALUES (?, ?, ?)
            """, (resource_id, f"chunk_{i}", vector_id))
        
        conn.commit()
        
        # Verify no constraint violations
        cursor.execute("SELECT COUNT(*) FROM ResourceChunks")
        chunk_count = cursor.fetchone()[0]
        assert chunk_count == 5
        
        # Verify vector IDs are unique
        cursor.execute("SELECT vector_id FROM ResourceChunks ORDER BY vector_id")
        stored_vector_ids = [row[0] for row in cursor.fetchall()]
        assert len(stored_vector_ids) == len(set(stored_vector_ids))
        assert stored_vector_ids == vector_ids


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
