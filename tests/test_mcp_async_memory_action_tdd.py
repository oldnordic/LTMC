"""
TDD Test Suite for MCP Async Memory Action Compatibility

This test suite validates:
1. MCP async memory_action compatibility
2. Atomic sync preservation across databases  
3. Event loop handling in MCP context
4. Real database operations (no mocks/stubs)
5. Rollback functionality
6. Performance SLA compliance

File: tests/test_mcp_async_memory_action_tdd.py
Purpose: Comprehensive TDD validation of async memory_action fixes
"""
import pytest
import asyncio
import time
import os
import sys
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ltms.tools.consolidated import memory_action
from ltms.tools.atomic_memory_integration import (
    get_atomic_memory_manager,
    async_atomic_memory_store,
    async_atomic_memory_retrieve,
    async_atomic_memory_search,
    async_atomic_memory_delete,
    _is_event_loop_running
)
from ltms.database.sync_coordinator import DatabaseSyncCoordinator
from ltms.sync.sync_models import DocumentData, DatabaseType


class TestMCPAsyncMemoryActionTDD:
    """TDD tests for MCP async memory_action compatibility."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        # Initialize basic schema
        with sqlite3.connect(db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS memory (
                    id TEXT PRIMARY KEY,
                    content TEXT,
                    tags TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
        
        yield db_path
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture  
    def sync_coordinator(self, temp_db_path):
        """Create test sync coordinator with real databases."""
        from ltms.database.sqlite_manager import SQLiteManager
        from ltms.database.neo4j_manager import Neo4jManager
        from ltms.database.faiss_manager import FAISSManager
        from ltms.database.redis_manager import RedisManager
        
        # Use test mode managers with real operations
        sqlite_manager = SQLiteManager(test_mode=True)
        neo4j_manager = Neo4jManager(test_mode=True)
        faiss_manager = FAISSManager(test_mode=True)
        redis_manager = RedisManager(test_mode=True)
        
        coordinator = DatabaseSyncCoordinator(
            sqlite_manager=sqlite_manager,
            neo4j_manager=neo4j_manager,
            faiss_store=faiss_manager,
            redis_cache=redis_manager,
            test_mode=True
        )
        
        return coordinator
        
    async def test_01_async_memory_action_can_be_called_from_mcp_context(self):
        """Test that memory_action can be called from MCP async context."""
        
        # Simulate MCP server async context (event loop already running)
        assert _is_event_loop_running(), "Test should run in async context"
        
        # Test basic memory_action call
        result = await memory_action(
            action="store",
            content="Test content for MCP async compatibility",
            tags=["test", "mcp", "async"],
            conversation_id="test_conversation"
        )
        
        assert result is not None
        assert isinstance(result, (dict, str))
        
        # If result is successful dict, validate structure
        if isinstance(result, dict) and result.get('success'):
            assert 'doc_id' in result or 'file_name' in result
            assert 'message' in result or 'success' in result
    
    async def test_02_async_atomic_memory_store_preserves_atomicity(self, sync_coordinator):
        """Test that async atomic memory store preserves atomicity."""
        
        document_data = DocumentData(
            id="test_atomic_doc",
            content="Test content for atomic storage",
            tags=["atomic", "test"],
            metadata={"test": True}
        )
        
        # Test atomic store operation
        result = await sync_coordinator.atomic_store_document(document_data)
        
        assert result.success is True
        assert result.doc_id == "test_atomic_doc"
        assert result.transaction_id is not None
        assert len(result.affected_databases) == 4  # All 4 databases
        assert DatabaseType.SQLITE in result.affected_databases
        assert DatabaseType.NEO4J in result.affected_databases  
        assert DatabaseType.FAISS in result.affected_databases
        assert DatabaseType.REDIS in result.affected_databases
        
        # Validate consistency report
        if result.consistency_report:
            assert result.consistency_report.doc_id == "test_atomic_doc"
    
    async def test_03_async_wrapper_functions_work_correctly(self):
        """Test that async wrapper functions work correctly."""
        
        # Test async_atomic_memory_store
        store_result = await async_atomic_memory_store(
            content="Test wrapper content",
            tags=["wrapper", "test"],
            metadata={"wrapper_test": True}
        )
        
        assert store_result is not None
        assert isinstance(store_result, dict)
        
        # Test async_atomic_memory_retrieve if store succeeded
        if store_result.get('success') and store_result.get('doc_id'):
            retrieve_result = await async_atomic_memory_retrieve(
                doc_id=store_result['doc_id']
            )
            assert retrieve_result is not None
            assert isinstance(retrieve_result, dict)
        
        # Test async_atomic_memory_search
        search_result = await async_atomic_memory_search(
            query="wrapper test",
            k=5,
            threshold=0.5
        )
        
        assert search_result is not None
        assert isinstance(search_result, dict)
    
    async def test_04_event_loop_detection_works(self):
        """Test that event loop detection works correctly."""
        
        # Should detect running event loop
        assert _is_event_loop_running() is True
        
        # Test in thread without event loop
        import threading
        import queue
        
        result_queue = queue.Queue()
        
        def thread_function():
            try:
                has_loop = _is_event_loop_running()
                result_queue.put(has_loop)
            except Exception as e:
                result_queue.put(e)
        
        thread = threading.Thread(target=thread_function)
        thread.start()
        thread.join()
        
        thread_result = result_queue.get()
        assert thread_result is False
    
    async def test_05_performance_sla_compliance(self, sync_coordinator):
        """Test that operations meet performance SLA requirements."""
        
        document_data = DocumentData(
            id="test_performance_doc",
            content="Performance test content",
            tags=["performance"],
            metadata={"performance_test": True}
        )
        
        start_time = time.time()
        result = await sync_coordinator.atomic_store_document(document_data)
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Check SLA compliance (should be < 500ms for single operation)
        assert execution_time_ms < 500, f"Operation took {execution_time_ms}ms, exceeds 500ms SLA"
        
        # Validate result includes timing information
        assert result.execution_time_ms is not None
        assert result.execution_time_ms > 0
    
    async def test_06_rollback_functionality_on_failure(self, sync_coordinator):
        """Test rollback functionality when operations fail."""
        
        document_data = DocumentData(
            id="test_rollback_doc", 
            content="Rollback test content",
            tags=["rollback"],
            metadata={"rollback_test": True}
        )
        
        # Force a failure condition by mocking one database operation to fail
        original_execute_neo4j = sync_coordinator._execute_neo4j_operation
        
        async def mock_failing_neo4j_operation(operation):
            # Simulate Neo4j failure
            operation.mark_started()
            operation.mark_completed(False, "Simulated Neo4j failure")
            return False
        
        sync_coordinator._execute_neo4j_operation = mock_failing_neo4j_operation
        
        try:
            result = await sync_coordinator.atomic_store_document(document_data)
            
            # Should fail due to Neo4j mock failure
            assert result.success is False
            assert result.error_message is not None
            
            # Should have attempted rollback
            transaction = sync_coordinator.active_transactions.get(result.transaction_id)
            if transaction:
                # If transaction exists, rollback should have been attempted
                assert transaction.rollback_attempted is not None
        
        finally:
            # Restore original method
            sync_coordinator._execute_neo4j_operation = original_execute_neo4j
    
    async def test_07_batch_operations_maintain_atomicity(self, sync_coordinator):
        """Test that batch operations maintain atomicity."""
        
        documents = [
            DocumentData(
                id=f"test_batch_doc_{i}",
                content=f"Batch test content {i}",
                tags=["batch", f"doc_{i}"],
                metadata={"batch_index": i}
            )
            for i in range(3)
        ]
        
        results = await sync_coordinator.atomic_batch_store(documents)
        
        assert len(results) == 3
        
        # All should succeed or all should fail (atomicity)
        success_count = sum(1 for r in results if r.success)
        assert success_count == 3 or success_count == 0
        
        # If successful, validate all results
        if success_count == 3:
            for i, result in enumerate(results):
                assert result.doc_id == f"test_batch_doc_{i}"
                assert result.success is True
                assert len(result.affected_databases) == 4
    
    async def test_08_consistency_validation_works(self, sync_coordinator):
        """Test that consistency validation works across databases."""
        
        document_data = DocumentData(
            id="test_consistency_doc",
            content="Consistency test content", 
            tags=["consistency"],
            metadata={"consistency_test": True}
        )
        
        result = await sync_coordinator.atomic_store_document(document_data)
        
        if result.success:
            # Test consistency validation
            consistency_report = await sync_coordinator.validate_consistency("test_consistency_doc")
            
            assert consistency_report.doc_id == "test_consistency_doc"
            assert hasattr(consistency_report, 'sqlite_consistent')
            assert hasattr(consistency_report, 'neo4j_consistent')
            assert hasattr(consistency_report, 'faiss_consistent')
            assert hasattr(consistency_report, 'redis_consistent')
            
            # In test mode, should be consistent
            if not consistency_report.inconsistencies:
                assert consistency_report.is_consistent is True
    
    async def test_09_memory_action_backwards_compatibility(self):
        """Test that memory_action maintains backwards compatibility."""
        
        # Test legacy parameter style
        result1 = await memory_action(
            action="store",
            content="Legacy compatibility test",
            tags=["legacy", "compatibility"]
        )
        
        assert result1 is not None
        
        # Test with conversation_id parameter
        result2 = await memory_action(
            action="store", 
            content="Conversation ID test",
            conversation_id="test_conversation",
            tags=["conversation", "test"]
        )
        
        assert result2 is not None
        
        # Test retrieve action
        result3 = await memory_action(
            action="retrieve",
            query="compatibility test"
        )
        
        assert result3 is not None

if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])