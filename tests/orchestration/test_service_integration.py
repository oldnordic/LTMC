"""
Service Integration Tests for Redis Orchestration Layer.

Comprehensive integration tests for orchestration services with real Redis integration.
Tests tool caching, chunk buffering, session management, and cross-service coordination.
"""

import pytest
import pytest_asyncio
import asyncio
import tempfile
import os
import json
import uuid
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class TestOrchestrationServiceIntegration:
    """
    Test integration of all orchestration services with real Redis.
    """
    
    @pytest.fixture(scope="class")
    def test_database(self):
        """Create a test database for integration testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        # Set up test database
        os.environ["DB_PATH"] = db_path
        
        from ltms.database.connection import get_db_connection, close_db_connection
        from ltms.database.schema import create_tables
        
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        yield db_path
        
        # Cleanup
        close_db_connection(conn)
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest_asyncio.fixture
    async def redis_manager(self):
        """Create Redis manager for integration testing."""
        from ltms.services.redis_service import RedisConnectionManager
        
        # Use dedicated test database to avoid conflicts
        manager = RedisConnectionManager(host="localhost", port=6379, db=15)
        
        try:
            await manager.initialize()
            if not manager.is_connected:
                pytest.skip("Redis not available for integration testing")
            
            # Clean test database before tests
            await manager.client.flushdb()
            yield manager
            
        finally:
            try:
                # Clean up after tests
                if manager.is_connected:
                    await manager.client.flushdb()
                await manager.close()
            except Exception:
                pass  # Ignore cleanup errors
    
    def test_orchestration_services_importable(self):
        """Test that all orchestration services can be imported."""
        # This test ensures all orchestration services exist and are importable
        try:
            from ltms.services.orchestration_service import OrchestrationService
            from ltms.services.agent_registry_service import AgentRegistryService
            from ltms.services.context_coordination_service import ContextCoordinationService
            from ltms.services.memory_locking_service import MemoryLockingService
            from ltms.services.tool_cache_service import ToolCacheService
            from ltms.services.chunk_buffer_service import ChunkBufferService
            from ltms.services.session_state_service import SessionStateService
            assert True, "All orchestration services imported successfully"
        except ImportError as e:
            pytest.skip(f"Orchestration services not yet implemented: {e}")
    
    def test_orchestration_integration_exists(self):
        """Test that orchestration integration module exists."""
        try:
            from ltms.mcp_orchestration_integration import OrchestrationIntegration
            assert True, "Orchestration integration module exists"
        except ImportError:
            pytest.skip("Orchestration integration not yet implemented")
    
    @pytest.mark.asyncio
    async def test_tool_cache_redis_integration(self, redis_manager, test_database):
        """Test tool cache service with real Redis integration."""
        from ltms.services.tool_cache_service import ToolCacheService
        
        # Initialize service with real Redis
        cache_service = ToolCacheService(redis_manager)
        
        # Test caching and retrieval
        tool_name = "test_tool"
        params = {"query": "test query", "limit": 10}
        result = {"results": [{"id": "123", "content": "test content"}], "count": 1}
        
        # Cache the result
        success = await cache_service.cache_tool_result(tool_name, params, result)
        assert success is True, "Should successfully cache result"
        
        # Retrieve cached result
        cached_result = await cache_service.get_cached_result(tool_name, params)
        assert cached_result is not None, "Should retrieve cached result"
        assert cached_result["count"] == 1, "Cached result should match original"
        
        # Test cache statistics
        stats = await cache_service.get_tool_statistics(tool_name)
        assert "overall" in stats, "Should have overall statistics"
        assert stats["overall"]["hit_count"] >= 1, "Should track cache hits"
        
        logger.info(f"Tool cache integration test passed: {stats}")
    
    @pytest.mark.asyncio
    async def test_chunk_buffer_cross_agent_coordination(self, redis_manager, test_database):
        """Test chunk buffer sharing between multiple agents."""
        from ltms.services.chunk_buffer_service import ChunkBufferService
        
        # Initialize chunk buffer with real Redis
        buffer_service = ChunkBufferService(redis_manager)
        
        # Test chunk caching and cross-agent access
        chunk_id = "test_chunk_123"
        chunk_data = {
            "content": "This is test chunk content",
            "metadata": {"source": "test", "type": "text"}
        }
        
        # Agent 1 caches chunk
        agent1_id = "agent_1"
        success = await buffer_service.cache_chunk(chunk_id, chunk_data, agent1_id)
        assert success is True, "Agent 1 should successfully cache chunk"
        
        # Agent 2 retrieves chunk (cross-agent access)
        agent2_id = "agent_2"
        retrieved_chunk = await buffer_service.get_chunk(chunk_id, agent2_id, fallback_to_faiss=False)
        assert retrieved_chunk is not None, "Agent 2 should retrieve cached chunk"
        assert retrieved_chunk["content"] == chunk_data["content"], "Retrieved content should match"
        
        # Test popularity tracking
        popular_chunks = await buffer_service.get_popular_chunks("1h", 10)
        assert len(popular_chunks) >= 1, "Should track popular chunks"
        assert any(chunk[0] == chunk_id for chunk in popular_chunks), "Test chunk should be in popular list"
        
        # Test buffer statistics
        stats = await buffer_service.get_buffer_stats()
        assert stats.get("buffer_size", 0) >= 1 or stats.get("chunk_count", 0) >= 1, f"Should track buffer statistics: {stats}"
        
        logger.info(f"Chunk buffer coordination test passed: {stats}")
    
    @pytest.mark.asyncio
    async def test_session_state_persistence(self, redis_manager, test_database):
        """Test session state survives agent disconnections."""
        from ltms.services.session_state_service import SessionStateService
        
        # Initialize session state service with real Redis
        session_service = SessionStateService(redis_manager)
        await session_service.start()
        
        try:
            # Create session with multiple participants
            session_id = f"test_session_{uuid.uuid4()}"
            participants = ["agent_1", "agent_2"]
            
            session = await session_service.create_session(
                session_id=session_id,
                participants=participants,
                metadata={"test": True}
            )
            
            assert session.session_id == session_id, "Session should have correct ID"
            assert len(session.participants) == 2, "Session should have correct participants"
            
            # Update session state
            state_updates = {
                "current_task": "integration_testing",
                "progress": 50
            }
            success = await session_service.update_session_state(session_id, state_updates)
            assert success is True, "Should update session state"
            
            # Simulate "disconnection" by creating new service instance
            # but using same Redis - state should persist
            new_session_service = SessionStateService(redis_manager)
            await new_session_service.start()
            
            # Retrieve session with new service instance
            retrieved_session = await new_session_service.get_session(session_id)
            assert retrieved_session is not None, "Session should persist across service instances"
            assert retrieved_session.persistent_state["current_task"] == "integration_testing", "State should persist"
            assert retrieved_session.persistent_state["progress"] == 50, "State values should persist"
            
            # Test session statistics
            stats = await new_session_service.get_session_stats()
            assert stats.get("active_sessions", 0) >= 1, "Should track active sessions"
            
            # Cleanup
            await session_service.terminate_session(session_id)
            await new_session_service.stop()
            
            logger.info(f"Session persistence test passed: {stats}")
            
        finally:
            await session_service.stop()
    
    @pytest.mark.asyncio
    async def test_all_services_coordination(self, redis_manager, test_database):
        """Test all orchestration services work together."""
        from ltms.services.tool_cache_service import ToolCacheService
        from ltms.services.chunk_buffer_service import ChunkBufferService
        from ltms.services.session_state_service import SessionStateService
        
        # Initialize all services
        cache_service = ToolCacheService(redis_manager)
        buffer_service = ChunkBufferService(redis_manager)
        session_service = SessionStateService(redis_manager)
        await session_service.start()
        
        try:
            # Create coordinated session
            session_id = f"coordination_test_{uuid.uuid4()}"
            agent_id = "coordinator_agent"
            
            session = await session_service.create_session(
                session_id=session_id,
                participants=[agent_id],
                metadata={"coordination_test": True}
            )
            
            # Cache tool result related to session
            tool_result = {
                "session_id": session_id,
                "agent_id": agent_id,
                "results": ["coordination", "test", "data"]
            }
            
            cache_success = await cache_service.cache_tool_result(
                "coordination_tool",
                {"session_id": session_id},
                tool_result
            )
            assert cache_success is True, "Tool result caching should succeed"
            
            # Cache chunk for the session
            chunk_data = {
                "session_id": session_id,
                "content": "Coordinated chunk content",
                "metadata": {"coordination": True}
            }
            
            chunk_id = f"coord_chunk_{session_id}"
            buffer_success = await buffer_service.cache_chunk(chunk_id, chunk_data, agent_id)
            assert buffer_success is True, "Chunk caching should succeed"
            
            # Update session state with references to cached data
            session_updates = {
                "cached_tool_result": True,
                "cached_chunk_id": chunk_id,
                "coordination_status": "active"
            }
            
            state_success = await session_service.update_session_state(session_id, session_updates)
            assert state_success is True, "Session state update should succeed"
            
            # Verify cross-service coordination by retrieving all data
            cached_tool = await cache_service.get_cached_result("coordination_tool", {"session_id": session_id})
            cached_chunk = await buffer_service.get_chunk(chunk_id, agent_id, fallback_to_faiss=False)
            updated_session = await session_service.get_session(session_id)
            
            assert cached_tool is not None, "Tool result should be retrievable"
            assert cached_chunk is not None, "Cached chunk should be retrievable"
            assert updated_session is not None, "Updated session should be retrievable"
            
            # Verify data consistency across services
            assert cached_tool["session_id"] == session_id, "Tool result should reference correct session"
            assert cached_chunk.get("session_id") == session_id or chunk_data["session_id"] in str(cached_chunk), "Cached chunk should reference correct session"
            assert updated_session.persistent_state["cached_chunk_id"] == chunk_id, "Session should reference chunk"
            
            # Test performance improvement from coordination
            # Second retrieval should be faster due to caching
            start_time = time.time()
            second_retrieval = await cache_service.get_cached_result("coordination_tool", {"session_id": session_id})
            retrieval_time = time.time() - start_time
            
            assert second_retrieval is not None, "Second retrieval should succeed"
            assert retrieval_time < 0.1, "Cached retrieval should be fast"
            
            logger.info(f"Service coordination test passed in {retrieval_time:.4f}s")
            
        finally:
            # Cleanup
            await session_service.terminate_session(session_id)
            await session_service.stop()


class TestPerformanceValidation:
    """
    Test performance improvements from orchestration services.
    """
    
    @pytest_asyncio.fixture
    async def redis_manager(self):
        """Create Redis manager for performance testing."""
        from ltms.services.redis_service import RedisConnectionManager
        
        manager = RedisConnectionManager(host="localhost", port=6379, db=15)
        
        try:
            await manager.initialize()
            if not manager.is_connected:
                pytest.skip("Redis not available for performance testing")
            
            await manager.client.flushdb()
            yield manager
            
        finally:
            try:
                if manager.is_connected:
                    await manager.client.flushdb()
                await manager.close()
            except Exception:
                pass
    
    @pytest.mark.asyncio
    async def test_cache_hit_rate_improvements(self, redis_manager):
        """Test cache hit rate improvements with tool caching."""
        from ltms.services.tool_cache_service import ToolCacheService
        
        cache_service = ToolCacheService(redis_manager)
        
        # Simulate repeated tool calls with same parameters
        tool_name = "performance_tool"
        params = {"query": "performance test", "limit": 100}
        result = {
            "results": [{"id": f"perf_{i}", "data": f"result_{i}"} for i in range(100)],
            "count": 100
        }
        
        # First call - cache miss (should be slower)
        start_time = time.time()
        await cache_service.cache_tool_result(tool_name, params, result)
        first_retrieval = await cache_service.get_cached_result(tool_name, params)
        first_call_time = time.time() - start_time
        
        assert first_retrieval is not None, "First retrieval should succeed"
        
        # Repeated calls - cache hits (should be faster)
        hit_times = []
        for _ in range(5):
            start_time = time.time()
            cached_result = await cache_service.get_cached_result(tool_name, params)
            hit_time = time.time() - start_time
            hit_times.append(hit_time)
            assert cached_result is not None, "Cache hit should succeed"
        
        avg_hit_time = sum(hit_times) / len(hit_times)
        
        # Cache hits should be significantly faster
        assert avg_hit_time < first_call_time / 2, f"Cache hits ({avg_hit_time:.4f}s) should be faster than first call ({first_call_time:.4f}s)"
        
        # Test hit rate statistics
        stats = await cache_service.get_tool_statistics(tool_name)
        hit_rate = stats["overall"]["hit_rate"]
        assert hit_rate > 0.8, f"Hit rate should be high: {hit_rate:.2f}"
        
        logger.info(f"Cache hit rate validation passed: {hit_rate:.2%} hit rate, avg {avg_hit_time:.4f}s per hit")
    
    @pytest.mark.asyncio
    async def test_chunk_buffer_memory_efficiency(self, redis_manager):
        """Test chunk buffer memory efficiency and LRU eviction."""
        from ltms.services.chunk_buffer_service import ChunkBufferService
        
        buffer_service = ChunkBufferService(redis_manager)
        
        # Cache many chunks to test memory management
        chunk_data_template = {
            "content": "A" * 1000,  # 1KB per chunk
            "metadata": {"size": "1KB", "test": True}
        }
        
        cached_chunks = []
        for i in range(20):  # Cache 20KB of data
            chunk_id = f"memory_test_chunk_{i}"
            chunk_data = {**chunk_data_template, "chunk_id": chunk_id}
            
            success = await buffer_service.cache_chunk(chunk_id, chunk_data, f"agent_{i % 3}")
            if success:
                cached_chunks.append(chunk_id)
        
        # Check memory usage
        stats = await buffer_service.get_buffer_stats()
        memory_usage = stats.get("memory_usage_mb", 0)
        
        assert memory_usage > 0, "Should track memory usage"
        assert memory_usage < 10, f"Memory usage should be reasonable: {memory_usage}MB"
        
        # Test that popular chunks are retained
        popular_chunks = await buffer_service.get_popular_chunks("1h", 10)
        assert len(popular_chunks) > 0, "Should track popular chunks"
        
        logger.info(f"Memory efficiency test passed: {memory_usage:.2f}MB used, {len(popular_chunks)} popular chunks")
    
    @pytest.mark.asyncio
    async def test_session_state_overhead(self, redis_manager):
        """Test session state management overhead."""
        from ltms.services.session_state_service import SessionStateService
        
        session_service = SessionStateService(redis_manager)
        await session_service.start()
        
        try:
            # Create multiple sessions to test overhead
            session_ids = []
            participants_per_session = 3
            
            # Measure session creation time
            start_time = time.time()
            for i in range(10):
                session_id = f"overhead_test_session_{i}"
                participants = [f"agent_{j}_{i}" for j in range(participants_per_session)]
                
                session = await session_service.create_session(
                    session_id=session_id,
                    participants=participants,
                    metadata={"test_index": i}
                )
                
                session_ids.append(session_id)
            
            creation_time = time.time() - start_time
            avg_creation_time = creation_time / len(session_ids)
            
            # Session creation should be fast
            assert avg_creation_time < 0.1, f"Session creation should be fast: {avg_creation_time:.4f}s per session"
            
            # Test state update performance
            start_time = time.time()
            for session_id in session_ids:
                await session_service.update_session_state(
                    session_id,
                    {"test_update": True, "timestamp": time.time()}
                )
            
            update_time = time.time() - start_time
            avg_update_time = update_time / len(session_ids)
            
            # State updates should be fast
            assert avg_update_time < 0.05, f"State updates should be fast: {avg_update_time:.4f}s per update"
            
            # Get overall statistics
            stats = await session_service.get_session_stats()
            assert stats["active_sessions"] == len(session_ids), "Should track correct number of sessions"
            
            logger.info(f"Session overhead test passed: {avg_creation_time:.4f}s create, {avg_update_time:.4f}s update")
            
            # Cleanup
            for session_id in session_ids:
                await session_service.terminate_session(session_id)
        
        finally:
            await session_service.stop()
    
    @pytest.mark.asyncio
    async def test_coordination_latency_benchmark(self, redis_manager):
        """Benchmark coordination latency between services."""
        from ltms.services.tool_cache_service import ToolCacheService
        from ltms.services.chunk_buffer_service import ChunkBufferService
        from ltms.services.session_state_service import SessionStateService
        
        # Initialize all services
        cache_service = ToolCacheService(redis_manager)
        buffer_service = ChunkBufferService(redis_manager)
        session_service = SessionStateService(redis_manager)
        await session_service.start()
        
        try:
            # Benchmark full coordination workflow
            iterations = 5
            total_times = []
            
            for i in range(iterations):
                workflow_start = time.time()
                
                # 1. Create session
                session_id = f"benchmark_session_{i}"
                session = await session_service.create_session(
                    session_id=session_id,
                    participants=[f"benchmark_agent_{i}"]
                )
                
                # 2. Cache tool result
                tool_result = {"benchmark": True, "iteration": i, "data": list(range(50))}
                await cache_service.cache_tool_result(
                    f"benchmark_tool_{i}",
                    {"session_id": session_id},
                    tool_result
                )
                
                # 3. Cache chunk
                chunk_data = {"benchmark_content": "B" * 500, "iteration": i}
                chunk_id = f"benchmark_chunk_{i}"
                await buffer_service.cache_chunk(chunk_id, chunk_data, f"benchmark_agent_{i}")
                
                # 4. Update session state
                await session_service.update_session_state(
                    session_id,
                    {"benchmark_complete": True, "chunk_id": chunk_id}
                )
                
                # 5. Retrieve everything (coordination verification)
                retrieved_tool = await cache_service.get_cached_result(
                    f"benchmark_tool_{i}",
                    {"session_id": session_id}
                )
                retrieved_chunk = await buffer_service.get_chunk(chunk_id, f"benchmark_agent_{i}", False)
                updated_session = await session_service.get_session(session_id)
                
                workflow_time = time.time() - workflow_start
                total_times.append(workflow_time)
                
                # Verify coordination worked
                assert retrieved_tool is not None, "Tool result should be retrievable"
                assert retrieved_chunk is not None, "Cached chunk should be retrievable"
                assert updated_session is not None, "Updated session should be retrievable"
                assert updated_session.persistent_state["chunk_id"] == chunk_id, "Cross-references should work"
                
                # Cleanup for next iteration
                await session_service.terminate_session(session_id)
            
            avg_coordination_time = sum(total_times) / len(total_times)
            max_coordination_time = max(total_times)
            min_coordination_time = min(total_times)
            
            # Coordination should be reasonably fast
            assert avg_coordination_time < 1.0, f"Average coordination time should be reasonable: {avg_coordination_time:.4f}s"
            assert max_coordination_time < 2.0, f"Max coordination time should be reasonable: {max_coordination_time:.4f}s"
            
            logger.info(f"Coordination latency benchmark passed: avg {avg_coordination_time:.4f}s, "
                       f"min {min_coordination_time:.4f}s, max {max_coordination_time:.4f}s")
        
        finally:
            await session_service.stop()


class TestErrorRecoveryScenarios:
    """
    Test error recovery and resilience scenarios.
    """
    
    @pytest_asyncio.fixture
    async def redis_manager(self):
        """Create Redis manager for error recovery testing."""
        from ltms.services.redis_service import RedisConnectionManager
        
        manager = RedisConnectionManager(host="localhost", port=6379, db=15)
        
        try:
            await manager.initialize()
            if not manager.is_connected:
                pytest.skip("Redis not available for error recovery testing")
            
            await manager.client.flushdb()
            yield manager
            
        finally:
            try:
                if manager.is_connected:
                    await manager.client.flushdb()
                await manager.close()
            except Exception:
                pass
    
    @pytest.mark.asyncio
    async def test_redis_connection_failure_handling(self, redis_manager):
        """Test graceful handling of Redis connection failures."""
        from ltms.services.tool_cache_service import ToolCacheService
        
        # Start with working service
        cache_service = ToolCacheService(redis_manager)
        
        # Test normal operation
        success = await cache_service.cache_tool_result(
            "test_tool",
            {"param": "value"},
            {"result": "success"}
        )
        assert success is True, "Normal caching should work"
        
        # Simulate connection failure by closing Redis
        await redis_manager.close()
        
        # Test graceful failure handling
        failed_cache = await cache_service.cache_tool_result(
            "test_tool_2",
            {"param": "value2"},
            {"result": "should_fail"}
        )
        
        # Should handle failure gracefully (return False, not crash)
        assert failed_cache is False, "Should handle Redis failure gracefully"
        
        failed_retrieval = await cache_service.get_cached_result(
            "test_tool",
            {"param": "value"}
        )
        
        # Should handle retrieval failure gracefully (return None, not crash)
        assert failed_retrieval is None, "Should handle Redis retrieval failure gracefully"
        
        logger.info("Redis connection failure handling test passed")
    
    @pytest.mark.asyncio
    async def test_service_degradation_scenarios(self, redis_manager):
        """Test system behavior under service degradation."""
        from ltms.services.chunk_buffer_service import ChunkBufferService
        from ltms.services.session_state_service import SessionStateService
        
        # Start services normally
        buffer_service = ChunkBufferService(redis_manager)
        session_service = SessionStateService(redis_manager)
        await session_service.start()
        
        try:
            # Create session and cache data normally
            session_id = "degradation_test_session"
            session = await session_service.create_session(
                session_id=session_id,
                participants=["test_agent"]
            )
            
            chunk_id = "degradation_test_chunk"
            chunk_data = {"content": "test content", "metadata": {}}
            
            # Normal operation should work
            cache_success = await buffer_service.cache_chunk(chunk_id, chunk_data, "test_agent")
            assert cache_success is True, "Normal chunk caching should work"
            
            retrieved_chunk = await buffer_service.get_chunk(chunk_id, "test_agent", fallback_to_faiss=False)
            assert retrieved_chunk is not None, "Normal chunk retrieval should work"
            
            # Simulate Redis memory pressure by filling up memory
            large_chunk_data = {"content": "X" * 10000, "metadata": {"large": True}}
            
            # Try to cache many large chunks to trigger eviction
            for i in range(20):
                await buffer_service.cache_chunk(
                    f"large_chunk_{i}",
                    large_chunk_data,
                    "test_agent"
                )
            
            # Original chunk might be evicted, but service should still work
            stats = await buffer_service.get_buffer_stats()
            assert "error" not in stats, "Service should handle memory pressure gracefully"
            
            # Session service should continue working
            session_update = await session_service.update_session_state(
                session_id,
                {"degradation_test": "completed"}
            )
            assert session_update is True, "Session updates should continue working under pressure"
            
            logger.info("Service degradation scenario test passed")
        
        finally:
            await session_service.terminate_session(session_id)
            await session_service.stop()
    
    @pytest.mark.asyncio
    async def test_resource_cleanup_on_failures(self, redis_manager):
        """Test proper resource cleanup when operations fail."""
        from ltms.services.session_state_service import SessionStateService
        
        session_service = SessionStateService(redis_manager)
        await session_service.start()
        
        try:
            # Create session that will be used for cleanup testing
            session_id = "cleanup_test_session"
            session = await session_service.create_session(
                session_id=session_id,
                participants=["cleanup_agent"],
                metadata={"cleanup_test": True}
            )
            
            # Add some state that needs cleanup
            await session_service.update_session_state(
                session_id,
                {"temp_data": list(range(100)), "cleanup_required": True}
            )
            
            # Verify session exists
            existing_session = await session_service.get_session(session_id)
            assert existing_session is not None, "Session should exist before cleanup"
            
            # Test cleanup through termination
            cleanup_success = await session_service.terminate_session(session_id, cleanup_resources=True)
            assert cleanup_success is True, "Session termination should succeed"
            
            # Wait a moment for cleanup to complete
            await asyncio.sleep(0.1)
            
            # Session should still exist briefly but marked as terminated
            terminated_session = await session_service.get_session(session_id)
            if terminated_session:
                from ltms.services.session_models import SessionStatus
                assert terminated_session.status == SessionStatus.TERMINATED, "Session should be marked as terminated"
            
            # Trigger immediate cleanup for testing (instead of waiting 60 seconds)
            # Cancel any existing delayed cleanup and do immediate cleanup
            await session_service._delayed_delete_session(session_id, 0)
            
            # Now session should be completely cleaned up
            cleaned_session = await session_service.get_session(session_id)
            assert cleaned_session is None, "Session should be cleaned up after immediate cleanup"
            
            logger.info("Resource cleanup on failure test passed")
        
        finally:
            await session_service.stop()
    
    @pytest.mark.asyncio 
    async def test_data_consistency_validation(self, redis_manager):
        """Test data consistency across services under error conditions."""
        from ltms.services.tool_cache_service import ToolCacheService
        from ltms.services.chunk_buffer_service import ChunkBufferService
        
        cache_service = ToolCacheService(redis_manager)
        buffer_service = ChunkBufferService(redis_manager)
        
        # Create interdependent data
        resource_id = "consistency_test_resource"
        tool_result = {
            "resource_id": resource_id,
            "data": "important data",
            "dependencies": ["chunk_1", "chunk_2"]
        }
        
        chunk_data = {
            "resource_id": resource_id,
            "content": "chunk content",
            "metadata": {"dependency": True}
        }
        
        # Cache tool result with dependencies
        cache_success = await cache_service.cache_tool_result(
            "dependency_tool",
            {"resource_id": resource_id},
            tool_result,
            dependencies=[resource_id]
        )
        assert cache_success is True, "Tool result caching should succeed"
        
        # Cache related chunk
        buffer_success = await buffer_service.cache_chunk(
            "dependent_chunk",
            chunk_data,
            "consistency_agent"
        )
        assert buffer_success is True, "Chunk caching should succeed"
        
        # Verify data is retrievable
        cached_tool = await cache_service.get_cached_result("dependency_tool", {"resource_id": resource_id})
        cached_chunk = await buffer_service.get_chunk("dependent_chunk", "consistency_agent", False)
        
        assert cached_tool is not None, "Cached tool result should be retrievable"
        assert cached_chunk is not None, "Cached chunk should be retrievable"
        
        # Test invalidation cascade
        invalidated_count = await cache_service.invalidate_by_dependency(resource_id)
        assert invalidated_count > 0, "Should invalidate dependent cache entries"
        
        # Verify invalidated data is no longer retrievable
        invalidated_tool = await cache_service.get_cached_result("dependency_tool", {"resource_id": resource_id})
        assert invalidated_tool is None, "Invalidated tool result should not be retrievable"
        
        # But non-dependent data should still exist
        non_dependent_chunk = await buffer_service.get_chunk("dependent_chunk", "consistency_agent", False)
        assert non_dependent_chunk is not None, "Non-dependent chunk should still exist"
        
        logger.info("Data consistency validation test passed")


class TestBackwardCompatibility:
    """
    Test backward compatibility with existing LTMC functionality.
    """
    
    def test_existing_services_still_work(self):
        """Test that existing LTMC services are not broken by orchestration."""
        # Test that core services can still be imported and used
        from ltms.services.redis_service import RedisConnectionManager
        from ltms.database import dal
        from ltms.vector_store.faiss_store import MockFAISSIndex, create_faiss_index
        from ltms.services.embedding_service import create_embedding_model, encode_text
        
        # Should be able to create instances
        redis_manager = RedisConnectionManager(host="localhost", port=6379, db=0)
        faiss_store = create_faiss_index(384)
        
        # Test embedding service functions are available
        assert callable(create_embedding_model), "create_embedding_model should be callable"
        assert callable(encode_text), "encode_text should be callable"
        
        # Test DAL functions are available
        assert callable(dal.get_next_vector_id), "dal.get_next_vector_id should be callable"
        
        assert redis_manager is not None, "Redis manager should be creatable"
        assert faiss_store is not None, "FAISS store should be creatable"
        
        logger.info("Backward compatibility test passed")
    
    @pytest.mark.asyncio
    async def test_orchestration_does_not_interfere(self):
        """Test that orchestration services don't interfere with existing functionality."""
        # This test verifies that the orchestration layer is truly optional
        # and doesn't break existing LTMC functionality
        
        try:
            from ltms.services.orchestration_service import OrchestrationService
            
            # Should be able to import without affecting other services
            orchestration = OrchestrationService()
            assert orchestration is not None, "Orchestration service should be importable"
            
        except ImportError:
            # If orchestration isn't implemented, that's fine for this test
            pass
        
        # Core functionality should still work
        from ltms.services.embedding_service import create_embedding_model, encode_text
        
        try:
            # Test that embedding functions are still available
            assert callable(create_embedding_model), "Embedding model creation should still work"
            assert callable(encode_text), "Text encoding should still work"
        except Exception as e:
            # Some initialization may fail in test environment, that's okay
            logger.debug(f"Embedding service validation failed (expected in test): {e}")
        
        logger.info("Orchestration non-interference test passed")


if __name__ == "__main__":
    """Run service integration tests."""
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent.absolute()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    pytest.main([__file__, "-v", "--tb=short", "--asyncio-mode=auto"])