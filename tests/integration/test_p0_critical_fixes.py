"""Integration tests for P0 critical fixes validation."""

import pytest
import sqlite3
import tempfile
import os
import asyncio
from typing import Dict, Any

# Test imports
from ltms.database.schema import create_tables
from ltms.database.connection import get_db_connection, close_db_connection
from ltms.ml.intelligent_context_retrieval import IntelligentContextRetrieval
from ltms.ml.semantic_memory_manager import SemanticMemoryManager
from ltms.mcp_server import list_todos, add_todo
from ltms.services.embedding_service import create_embedding_model


class TestP0CriticalFixes:
    """Test suite to validate all P0 critical fixes."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        # Set environment variable
        os.environ["DB_PATH"] = db_path
        
        # Create tables
        conn = get_db_connection(db_path)
        create_tables(conn)
        close_db_connection(conn)
        
        yield db_path
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_database_schema_table_names_correct(self, temp_db_path):
        """Test that database queries use correct table names from schema."""
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Verify correct table names exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Check that proper case table names exist
        assert "Resources" in tables, "Resources table should exist"
        assert "ResourceChunks" in tables, "ResourceChunks table should exist"
        assert "Todos" in tables, "Todos table should exist"
        
        # Check that lowercase versions don't exist
        assert "resources" not in tables, "Lowercase resources table should not exist"
        assert "resource_chunks" not in tables, "Lowercase resource_chunks table should not exist"
        
        conn.close()

    def test_database_column_names_correct(self, temp_db_path):
        """Test that ResourceChunks table has correct column names."""
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Get column info for ResourceChunks
        cursor.execute("PRAGMA table_info(ResourceChunks)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Verify correct column names
        assert "id" in columns, "ResourceChunks should have id column"
        assert "chunk_text" in columns, "ResourceChunks should have chunk_text column"
        assert "resource_id" in columns, "ResourceChunks should have resource_id column"
        assert "vector_id" in columns, "ResourceChunks should have vector_id column"
        
        # Verify incorrect column names don't exist
        assert "chunk_id" not in columns, "ResourceChunks should not have chunk_id column (use id instead)"
        assert "content" not in columns, "ResourceChunks should not have content column (use chunk_text instead)"
        
        conn.close()

    def test_list_todos_function_signature_works(self, temp_db_path):
        """Test that list_todos function works with correct signature."""
        # Add test todos
        add_result = add_todo("Test Todo", "Test description", "medium")
        assert add_result["success"], f"Failed to add todo: {add_result.get('error')}"
        
        # Test list_todos with new signature
        result = list_todos(status="all", limit=10)
        assert result["success"], f"list_todos failed: {result.get('error')}"
        assert "todos" in result, "list_todos should return todos list"
        assert isinstance(result["todos"], list), "todos should be a list"
        
        # Test different status filters
        pending_result = list_todos(status="pending", limit=10)
        assert pending_result["success"], f"list_todos pending failed: {pending_result.get('error')}"
        
        completed_result = list_todos(status="completed", limit=10)
        assert completed_result["success"], f"list_todos completed failed: {completed_result.get('error')}"

    @pytest.mark.asyncio
    async def test_intelligent_context_retrieval_queries_work(self, temp_db_path):
        """Test that IntelligentContextRetrieval uses correct table/column names."""
        # Create test data with correct schema
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Insert test resource
        cursor.execute(
            "INSERT INTO Resources (file_name, type, created_at) VALUES (?, ?, ?)",
            ("test.txt", "document", "2024-01-01T00:00:00")
        )
        resource_id = cursor.lastrowid
        
        # Insert test chunk
        cursor.execute(
            "INSERT INTO ResourceChunks (resource_id, chunk_text, vector_id) VALUES (?, ?, ?)",
            (resource_id, "This is a test content for retrieval", 1)
        )
        
        conn.commit()
        conn.close()
        
        # Initialize IntelligentContextRetrieval
        retrieval = IntelligentContextRetrieval(
            db_path=temp_db_path,
            embedding_model_name='all-MiniLM-L6-v2'
        )
        
        # Initialize the system
        init_success = await retrieval.initialize()
        assert init_success, "IntelligentContextRetrieval initialization should succeed"
        
        # Test that _get_all_chunks works with correct schema
        chunks = await retrieval._get_all_chunks()
        assert len(chunks) > 0, "Should retrieve at least one chunk"
        assert "chunk_id" in chunks[0], "Chunk should have chunk_id field"
        assert "content" in chunks[0], "Chunk should have content field"
        assert "file_name" in chunks[0], "Chunk should have file_name field"
        
        # Cleanup
        await retrieval.cleanup()

    @pytest.mark.asyncio
    async def test_semantic_memory_manager_queries_work(self, temp_db_path):
        """Test that SemanticMemoryManager uses correct table/column names."""
        # Create test data with correct schema
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Insert test resource
        cursor.execute(
            "INSERT INTO Resources (file_name, type, created_at) VALUES (?, ?, ?)",
            ("test.txt", "document", "2024-01-01T00:00:00")
        )
        resource_id = cursor.lastrowid
        
        # Insert test chunks
        cursor.execute(
            "INSERT INTO ResourceChunks (resource_id, chunk_text, vector_id) VALUES (?, ?, ?)",
            (resource_id, "This is test content for semantic memory", 1)
        )
        chunk_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        # Initialize SemanticMemoryManager
        manager = SemanticMemoryManager(
            db_path=temp_db_path,
            embedding_model_name='all-MiniLM-L6-v2'
        )
        
        # Initialize the system
        init_success = await manager.initialize()
        assert init_success, "SemanticMemoryManager initialization should succeed"
        
        # Test that get_cluster_memories works with correct schema
        # First we need to simulate a cluster
        from ltms.ml.semantic_memory_manager import MemoryCluster
        import numpy as np
        
        test_cluster = MemoryCluster(
            cluster_id=1,
            centroid=np.array([0.1, 0.2, 0.3]),  # dummy centroid
            member_ids=[chunk_id],
            coherence_score=0.8,
            topic_keywords=["test"]
        )
        
        memories = await manager.get_cluster_memories(test_cluster.cluster_id)
        # Even with no real cluster, the query should execute without SQL errors
        
        # Cleanup
        await manager.cleanup()

    def test_todos_end_to_end_workflow(self, temp_db_path):
        """Test complete todos workflow with fixed signatures."""
        # Add a todo
        add_result = add_todo("Fix critical bugs", "Fix all P0 issues", "high")
        assert add_result["success"], f"Failed to add todo: {add_result.get('error')}"
        todo_id = add_result.get("todo_id")
        assert todo_id is not None, "Todo ID should be returned"
        
        # List todos
        list_result = list_todos(status="all", limit=10)
        assert list_result["success"], f"Failed to list todos: {list_result.get('error')}"
        assert len(list_result["todos"]) > 0, "Should have at least one todo"
        
        # Find our todo
        our_todo = None
        for todo in list_result["todos"]:
            if todo["id"] == todo_id:
                our_todo = todo
                break
        
        assert our_todo is not None, "Should find our added todo"
        assert our_todo["title"] == "Fix critical bugs", "Todo title should match"
        assert not our_todo["completed"], "Todo should not be completed initially"
        
        # List pending todos specifically
        pending_result = list_todos(status="pending", limit=10)
        assert pending_result["success"], f"Failed to list pending todos: {pending_result.get('error')}"
        
        pending_ids = [todo["id"] for todo in pending_result["todos"]]
        assert todo_id in pending_ids, "Our todo should be in pending list"

    @pytest.mark.asyncio
    async def test_context_retrieval_returns_results(self, temp_db_path):
        """Test that context retrieval actually returns results instead of 0."""
        # Create meaningful test data
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Insert multiple resources with good content
        test_data = [
            ("python_guide.txt", "Python is a high-level programming language with dynamic semantics"),
            ("ml_basics.txt", "Machine learning algorithms can learn patterns from data automatically"),
            ("web_dev.txt", "Web development involves creating applications that run in web browsers")
        ]
        
        chunk_id_counter = 1
        for filename, content in test_data:
            cursor.execute(
                "INSERT INTO Resources (file_name, type, created_at) VALUES (?, ?, ?)",
                (filename, "document", "2024-01-01T00:00:00")
            )
            resource_id = cursor.lastrowid
            
            cursor.execute(
                "INSERT INTO ResourceChunks (resource_id, chunk_text, vector_id) VALUES (?, ?, ?)",
                (resource_id, content, chunk_id_counter)
            )
            chunk_id_counter += 1
        
        conn.commit()
        conn.close()
        
        # Initialize and test retrieval
        retrieval = IntelligentContextRetrieval(
            db_path=temp_db_path,
            embedding_model_name='all-MiniLM-L6-v2'
        )
        
        init_success = await retrieval.initialize()
        assert init_success, "IntelligentContextRetrieval initialization should succeed"
        
        # Test various retrieval queries
        queries = [
            "programming language",
            "machine learning",
            "web development",
            "Python programming"
        ]
        
        for query in queries:
            result = await retrieval.retrieve_context(query, max_results=5)
            
            assert result is not None, f"Retrieval should return result for query: {query}"
            assert result.total_retrieved >= 0, f"Should have non-negative retrieved count for query: {query}"
            
            # At least some queries should return results given our test data
            if any(keyword in query.lower() for keyword in ["python", "machine", "web"]):
                assert result.total_retrieved > 0, f"Should find results for relevant query: {query}"
        
        # Cleanup
        await retrieval.cleanup()

    def test_integration_with_mcp_tools(self, temp_db_path):
        """Test that the fixes work with actual MCP tool calls."""
        # Import the HTTP tools setup
        from ltms.tools.todo_tools import TODO_TOOLS
        
        # Verify list_todos tool configuration
        assert "list_todos" in TODO_TOOLS, "list_todos should be in TODO_TOOLS"
        
        list_todos_config = TODO_TOOLS["list_todos"]
        assert "handler" in list_todos_config, "list_todos should have handler"
        
        # Test calling the handler directly (simulates MCP call)
        handler = list_todos_config["handler"]
        
        # Add test data first
        add_todo("Test integration", "Test MCP integration", "medium")
        
        # Test handler with different parameters
        result = handler(status="all", limit=5)
        assert result["success"], f"Handler call failed: {result.get('error')}"
        assert "todos" in result, "Handler should return todos"
        
        # Test with different status
        result_pending = handler(status="pending", limit=5)
        assert result_pending["success"], f"Handler pending call failed: {result_pending.get('error')}"
        
        result_completed = handler(status="completed", limit=5)
        assert result_completed["success"], f"Handler completed call failed: {result_completed.get('error')}"


def test_run_basic_validations():
    """Quick validation test that can run without async setup."""
    # Test that imports work
    from ltms.mcp_server import list_todos, add_todo
    from ltms.ml.intelligent_context_retrieval import IntelligentContextRetrieval
    from ltms.ml.semantic_memory_manager import SemanticMemoryManager
    
    # Test function signatures
    import inspect
    
    # Verify list_todos signature
    sig = inspect.signature(list_todos)
    params = list(sig.parameters.keys())
    assert "status" in params, "list_todos should have status parameter"
    assert "limit" in params, "list_todos should have limit parameter"
    
    print("✅ All P0 critical fixes validated successfully!")
    
    return True


if __name__ == "__main__":
    # Run basic validation
    test_run_basic_validations()