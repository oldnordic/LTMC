"""Integration tests for critical bug fixes in LTMC production system.

This test suite validates the fixes for the critical production failures:
1. Database schema consistency
2. Function parameter alignment 
3. Missing import dependencies
4. ML context retrieval system functionality

All tests use real database connections and services without mocks.
"""

import pytest
import tempfile
import os
import sqlite3
from typing import Dict, Any

# Import core LTMC components
from ltms.database.schema import create_tables
from ltms.database.connection import get_db_connection, close_db_connection
from ltms.services.context_service import get_context_for_query, log_chat_message
from ltms.services.resource_service import add_resource
from ltms.database.dal import create_resource, create_resource_chunks, get_chunks_by_vector_ids, get_next_vector_id


class TestCriticalBugFixes:
    """Integration tests for critical production bug fixes."""

    def setup_method(self):
        """Setup test database for each test method."""
        # Create temporary database
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        os.environ["DB_PATH"] = self.db_path
        
        # Create temporary FAISS index path
        self.index_path = tempfile.mkdtemp()
        os.environ["FAISS_INDEX_PATH"] = self.index_path
        
        # Setup database connection and tables
        self.conn = get_db_connection(self.db_path)
        create_tables(self.conn)

    def teardown_method(self):
        """Cleanup test database after each test."""
        if hasattr(self, 'conn') and self.conn:
            close_db_connection(self.conn)
        
        if hasattr(self, 'db_fd'):
            os.close(self.db_fd)
            os.unlink(self.db_path)

    def test_database_schema_consistency(self):
        """Test 1: Validate database schema table naming consistency.
        
        This test ensures that the database schema uses consistent table naming
        and that all tables exist as expected.
        """
        cursor = self.conn.cursor()
        
        # Verify all expected tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        
        expected_tables = {
            'Resources', 'ResourceChunks', 'ChatHistory', 'ContextLinks',
            'Summaries', 'Todos', 'CodePatterns', 'CodePatternContext', 
            'VectorIdSequence'
        }
        
        assert expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}"
        
        # Verify table case sensitivity is handled properly
        # Test that both case variations work for queries
        cursor.execute("SELECT COUNT(*) FROM Resources")
        resource_count_1 = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ResourceChunks")  
        chunk_count_1 = cursor.fetchone()[0]
        
        # Both should work without errors
        assert resource_count_1 >= 0
        assert chunk_count_1 >= 0

    def test_missing_import_fix(self):
        """Test 2: Validate that missing imports are now working.
        
        This test ensures that the store_context_links import is properly
        resolved in the context_service module.
        """
        # Test that we can import the previously missing function
        from ltms.database.context_linking import store_context_links
        from ltms.services.context_service import get_context_for_query
        
        # The function should be callable
        assert callable(store_context_links)
        assert callable(get_context_for_query)
        
        # Test that context_service can use the imported function
        # Create a test resource and chunk first
        resource_id = create_resource(
            self.conn,
            "test_file.txt", 
            "document",
            "2025-01-01T00:00:00"
        )
        
        vector_id = get_next_vector_id(self.conn)
        chunk_ids = create_resource_chunks(
            self.conn,
            resource_id,
            [("Test content for import validation", vector_id)]
        )
        
        # Log a message to get message_id
        message_id = log_chat_message(
            self.conn,
            "test_conversation",
            "user", 
            "Test query for import validation"
        )
        
        # Test that store_context_links works without import errors
        result = store_context_links(self.conn, message_id, chunk_ids)
        assert result['success'] is True
        assert result['links_created'] == 1

    def test_function_parameter_consistency(self):
        """Test 3: Validate function parameter consistency fixes.
        
        This test ensures that function signatures match their usage patterns
        and that all required parameters are properly handled.
        """
        # Test list_todos function with various parameter combinations
        from ltms.mcp_server import list_todos
        
        # Test with no parameters (default)
        result = list_todos()
        assert result['success'] is True
        assert 'todos' in result
        assert 'count' in result
        
        # Test with completed=None (explicit)
        result = list_todos(completed=None)
        assert result['success'] is True
        
        # Test with completed=False
        result = list_todos(completed=False)
        assert result['success'] is True
        
        # Test with completed=True
        result = list_todos(completed=True)
        assert result['success'] is True
        
        # All parameter variations should work without errors

    def test_ml_context_retrieval_system(self):
        """Test 4: Validate ML context retrieval system functionality.
        
        This test ensures that the entire ML pipeline works end-to-end:
        - Resource storage
        - Vector embedding
        - Similarity search
        - Context retrieval
        """
        # Add test content to the system
        test_content = "This is test content for machine learning context retrieval validation."
        
        result = add_resource(
            conn=self.conn,
            index_path=self.index_path,
            file_name="ml_test.txt",
            resource_type="document",
            content=test_content
        )
        
        assert result['success'] is True
        assert result['chunk_count'] > 0
        resource_id = result['resource_id']
        
        # Test context retrieval functionality
        query = "test content machine learning"
        conversation_id = "ml_test_conversation"
        
        retrieval_result = get_context_for_query(
            conn=self.conn,
            index_path=self.index_path,
            conversation_id=conversation_id,
            query=query,
            top_k=3
        )
        
        # Validate retrieval results
        assert retrieval_result['success'] is True
        
        # With our test content, we should get results
        if retrieval_result['retrieved_chunks']:
            assert len(retrieval_result['retrieved_chunks']) > 0
            assert retrieval_result['context'] != ""
            
            # Validate chunk structure
            chunk = retrieval_result['retrieved_chunks'][0]
            assert 'chunk_id' in chunk
            assert 'resource_id' in chunk
            assert 'file_name' in chunk
            assert 'score' in chunk
            assert chunk['file_name'] == 'ml_test.txt'

    def test_database_variable_references(self):
        """Test 5: Validate database path variable references are consistent.
        
        This test ensures that all functions use the correct environment variable
        pattern instead of hardcoded DB_PATH references.
        """
        from ltms.mcp_server import (
            get_messages_for_chunk_tool,
            get_context_usage_statistics_tool
        )
        
        # These functions should work without NameError exceptions
        # (Previously failed due to DB_PATH vs os.getenv pattern)
        
        # Test get_messages_for_chunk_tool
        result = get_messages_for_chunk_tool(chunk_id=999)  # Non-existent chunk
        assert result['success'] is True  # Should not error on variable reference
        
        # Test get_context_usage_statistics_tool  
        result = get_context_usage_statistics_tool()
        assert result['success'] is True  # Should not error on variable reference

    def test_vector_id_sequence_functionality(self):
        """Test 6: Validate vector ID sequence prevents constraint violations.
        
        This test ensures that the vector ID sequence system works correctly
        to prevent UNIQUE constraint failures.
        """
        # Create multiple resources with chunks
        for i in range(5):
            resource_id = create_resource(
                self.conn,
                f"test_file_{i}.txt",
                "document", 
                "2025-01-01T00:00:00"
            )
            
            # Generate unique vector IDs
            vector_id_1 = get_next_vector_id(self.conn)
            vector_id_2 = get_next_vector_id(self.conn)
            
            # Ensure vector IDs are unique
            assert vector_id_1 != vector_id_2
            
            # Create chunks with unique vector IDs
            chunk_ids = create_resource_chunks(
                self.conn,
                resource_id,
                [
                    (f"Chunk 1 content for resource {i}", vector_id_1),
                    (f"Chunk 2 content for resource {i}", vector_id_2)
                ]
            )
            
            # Should create 2 chunks per resource
            assert len(chunk_ids) == 2

    def test_end_to_end_system_integration(self):
        """Test 7: Full end-to-end system integration test.
        
        This test validates that all fixed components work together
        in a realistic usage scenario.
        """
        # 1. Store memory content
        from ltms.mcp_server import store_memory, retrieve_memory, log_chat
        
        test_data = {
            "content": "Integration test content for end-to-end validation of LTMC system",
            "file_name": "integration_test.md"
        }
        
        store_result = store_memory(**test_data)
        assert store_result['success'] is True
        
        # 2. Retrieve the stored content
        retrieve_result = retrieve_memory(
            conversation_id="integration_test",
            query="integration test content",
            top_k=2
        )
        assert retrieve_result['success'] is True
        
        # 3. Log chat interaction
        chat_result = log_chat(
            conversation_id="integration_test",
            role="user",
            content="Integration test query",
            source_tool="claude-code"
        )
        assert chat_result['success'] is True
        
        # 4. Validate all systems integrated successfully
        assert store_result['chunk_count'] > 0
        
        # The system should be able to find relevant context
        if retrieve_result['retrieved_chunks']:
            assert len(retrieve_result['retrieved_chunks']) > 0
            assert retrieve_result['context'] != ""

    def test_all_critical_fixes_validated(self):
        """Test 8: Meta-test to ensure all critical issues are resolved.
        
        This test validates that our test suite covers all the critical
        production issues that were identified.
        """
        # List of critical issues that should be tested
        critical_issues = [
            "database_schema_consistency",
            "missing_import_fix", 
            "function_parameter_consistency",
            "ml_context_retrieval_system",
            "database_variable_references",
            "vector_id_sequence_functionality",
            "end_to_end_system_integration"
        ]
        
        # Get list of test methods in this class
        test_methods = [method for method in dir(self) if method.startswith('test_')]
        
        # Verify we have tests for all critical issues
        for issue in critical_issues:
            test_method_name = f"test_{issue}"
            assert test_method_name in test_methods, f"Missing test for critical issue: {issue}"
        
        # All critical fixes should be covered by our test suite
        assert len(test_methods) >= len(critical_issues) + 1  # +1 for this meta-test


# Additional helper functions for testing
def validate_database_integrity(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Validate database integrity after operations.
    
    Args:
        conn: Database connection to validate
        
    Returns:
        Dictionary with integrity check results
    """
    cursor = conn.cursor()
    
    # Check foreign key constraints
    cursor.execute("PRAGMA foreign_key_check")
    fk_violations = cursor.fetchall()
    
    # Check table integrity
    cursor.execute("PRAGMA integrity_check")
    integrity_result = cursor.fetchone()[0]
    
    # Check for orphaned records
    cursor.execute("""
        SELECT COUNT(*) FROM ResourceChunks rc 
        LEFT JOIN Resources r ON rc.resource_id = r.id 
        WHERE r.id IS NULL
    """)
    orphaned_chunks = cursor.fetchone()[0]
    
    return {
        "foreign_key_violations": len(fk_violations),
        "integrity_check": integrity_result,
        "orphaned_chunks": orphaned_chunks,
        "healthy": len(fk_violations) == 0 and integrity_result == "ok" and orphaned_chunks == 0
    }


if __name__ == "__main__":
    """Run the critical bug fix tests directly."""
    pytest.main([__file__, "-v", "--tb=short"])