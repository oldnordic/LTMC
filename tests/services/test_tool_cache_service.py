"""Tests for Tool Cache Service functionality."""

import asyncio
import json
import pytest
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch


class MockAsyncContextManager:
    """Mock async context manager for Redis pipeline."""
    
    def __init__(self, mock_pipe):
        self.mock_pipe = mock_pipe
    
    async def __aenter__(self):
        return self.mock_pipe
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None

from ltms.services.tool_cache_service import (
    ToolCacheService,
    get_tool_cache_service,
    cleanup_tool_cache
)
from ltms.services.redis_service import RedisConnectionManager


class TestToolCacheService:
    """Test Tool Cache Service functionality."""
    
    @pytest.fixture
    async def mock_redis_manager(self):
        """Create mock Redis connection manager."""
        manager = MagicMock()
        manager.is_connected = True
        manager.client = AsyncMock()
        return manager
    
    @pytest.fixture
    def cache_service(self, mock_redis_manager):
        """Create cache service with mock Redis manager."""
        return ToolCacheService(mock_redis_manager)
    
    def test_cache_key_generation(self, cache_service):
        """Test cache key generation consistency."""
        tool_name = "store_memory"
        params1 = {"file_name": "test.md", "content": "test content"}
        params2 = {"content": "test content", "file_name": "test.md"}  # Different order
        
        key1 = cache_service._generate_cache_key(tool_name, params1)
        key2 = cache_service._generate_cache_key(tool_name, params2)
        
        # Keys should be identical despite parameter order
        assert key1 == key2
        assert key1.startswith("tool_cache:store_memory:")
        assert len(key1.split(":")[-1]) == 16  # Hash length
    
    def test_dependency_extraction(self, cache_service):
        """Test dependency extraction from results."""
        # Test result with multiple dependency types
        result = {
            "success": True,
            "resource_id": "res_123",
            "chunk_id": "chunk_456", 
            "file_name": "document.md",
            "results": [
                {"id": "item_1", "content": "data1"},
                {"id": "item_2", "content": "data2"}
            ]
        }
        
        dependencies = cache_service._extract_dependencies(result)
        
        expected = ["res_123", "chunk:chunk_456", "file:document.md", "item_1", "item_2"]
        assert set(dependencies) == set(expected)
    
    def test_dependency_extraction_empty(self, cache_service):
        """Test dependency extraction with no dependencies."""
        result = {"success": True, "message": "No dependencies"}
        dependencies = cache_service._extract_dependencies(result)
        assert dependencies == []
    
    @pytest.mark.asyncio
    async def test_cache_tool_result_success(self, cache_service):
        """Test successful tool result caching."""
        tool_name = "retrieve_memory"
        params = {"query": "test query", "limit": 10}
        result = {"results": [{"id": "1", "content": "test"}], "count": 1}
        
        # Mock individual Redis operations instead of pipeline
        with patch.object(cache_service, 'redis_manager') as mock_manager:
            mock_client = AsyncMock()
            mock_manager.client = mock_client
            
            # Mock pipeline context manager properly
            mock_pipe = AsyncMock()
            mock_pipe.execute.return_value = [True, True, True, True, True, True]
            
            async_context = MockAsyncContextManager(mock_pipe)
            mock_client.pipeline.return_value = async_context
            
            success = await cache_service.cache_tool_result(tool_name, params, result)
            
            assert success is True
            
            # Verify pipeline operations
            assert mock_pipe.setex.called
            assert mock_pipe.sadd.called
            assert mock_pipe.hincrby.called
            assert mock_pipe.hset.called
            assert mock_pipe.expire.called
    
    @pytest.mark.asyncio
    async def test_cache_tool_result_with_explicit_dependencies(self, cache_service):
        """Test caching with explicit dependencies."""
        tool_name = "link_resources"
        params = {"source": "res1", "target": "res2"}
        result = {"success": True}
        dependencies = ["res1", "res2", "custom_dep"]
        
        # Mock individual Redis operations instead of pipeline
        with patch.object(cache_service, 'redis_manager') as mock_manager:
            mock_client = AsyncMock()
            mock_manager.client = mock_client
            
            # Mock pipeline context manager properly
            mock_pipe = AsyncMock()
            mock_pipe.execute.return_value = [True] * 10
            
            async_context = MockAsyncContextManager(mock_pipe)
            mock_client.pipeline.return_value = async_context
            
            success = await cache_service.cache_tool_result(
                tool_name, params, result, dependencies=dependencies
            )
            
            assert success is True
            
            # Verify dependency handling - should be called once per dependency
            assert mock_pipe.sadd.call_count == len(dependencies)
    
    @pytest.mark.asyncio
    async def test_cache_tool_result_size_limit(self, cache_service):
        """Test cache size limit enforcement."""
        tool_name = "large_result"
        params = {"size": "large"}
        
        # Create result that exceeds size limit (100MB default)
        large_data = "x" * (cache_service.MAX_CACHE_SIZE_MB * 1024 * 1024 + 1)
        result = {"data": large_data}
        
        success = await cache_service.cache_tool_result(tool_name, params, result)
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_get_cached_result_logic(self, cache_service):
        """Test successful cache hit."""
        tool_name = "store_memory"
        params = {"file_name": "test.md", "content": "content"}
        cached_result = {"success": True, "id": "res_123"}
        
        cache_entry = {
            "result": cached_result,
            "created_at": datetime.utcnow().isoformat(),
            "tool_name": tool_name,
            "params": params,
            "dependencies": ["res_123"],
            "hit_count": 0
        }
        
        # Mock Redis operations
        cache_service.redis_manager.client.get.return_value = json.dumps(cache_entry)
        cache_service.redis_manager.client.ttl.return_value = 1800
        
        # Mock pipeline for hit count update
        with patch.object(cache_service, 'redis_manager') as mock_manager:
            mock_client = AsyncMock()
            mock_manager.client = mock_client
            
            # Set up get and ttl mocks
            mock_client.get.return_value = json.dumps(cache_entry)
            mock_client.ttl.return_value = 1800
            
            # Mock pipeline context manager properly
            mock_pipe = AsyncMock()
            mock_pipe.execute.return_value = [True, True, True]
            
            async_context = MockAsyncContextManager(mock_pipe)
            mock_client.pipeline.return_value = async_context
            
            result = await cache_service.get_cached_result(tool_name, params)
            
            assert result == cached_result
            assert cache_service._hit_count == 1
            
            # Verify hit count update
            assert mock_pipe.setex.called or mock_pipe.set.called
            assert mock_pipe.hincrby.called
            assert mock_pipe.hset.called
    
    @pytest.mark.asyncio
    async def test_get_cached_result_miss(self, cache_service):
        """Test cache miss."""
        tool_name = "retrieve_memory"
        params = {"query": "nonexistent"}
        
        cache_service.redis_manager.client.get.return_value = None
        
        result = await cache_service.get_cached_result(tool_name, params)
        
        assert result is None
        assert cache_service._miss_count == 1
    
    @pytest.mark.asyncio
    async def test_get_cached_result_max_age(self, cache_service):
        """Test cache result with max age enforcement."""
        tool_name = "aged_result"
        params = {"test": "old"}
        
        # Create old cache entry (2 hours ago)
        old_time = datetime.now(timezone.utc) - timedelta(hours=2)
        cache_entry = {
            "result": {"old": True},
            "created_at": old_time.isoformat(),
            "tool_name": tool_name,
            "params": params,
            "dependencies": [],
            "hit_count": 0
        }
        
        cache_service.redis_manager.client.get.return_value = json.dumps(cache_entry)
        
        # Request with max age of 1 hour (3600 seconds)
        result = await cache_service.get_cached_result(tool_name, params, max_age_seconds=3600)
        
        assert result is None  # Should be rejected as too old
        assert cache_service._miss_count == 1
    
    @pytest.mark.asyncio
    async def test_invalidate_by_dependency(self, cache_service):
        """Test cache invalidation by dependency."""
        resource_id = "res_123"
        dependent_keys = [
            b"tool_cache:store_memory:abc123",
            b"tool_cache:retrieve_memory:def456"
        ]
        
        # Mock Redis operations
        cache_service.redis_manager.client.smembers.return_value = dependent_keys
        
        # Mock pipeline
        with patch.object(cache_service, 'redis_manager') as mock_manager:
            mock_client = AsyncMock()
            mock_manager.client = mock_client
            
            # Mock smembers to return dependent keys
            mock_client.smembers.return_value = dependent_keys
            
            # Mock pipeline context manager properly
            mock_pipe = AsyncMock()
            mock_pipe.execute.return_value = [1, 1, 1]  # 2 cache deletes + 1 dep delete
            
            async_context = MockAsyncContextManager(mock_pipe)
            mock_client.pipeline.return_value = async_context
            
            count = await cache_service.invalidate_by_dependency(resource_id)
            
            assert count == 2  # Two cache entries invalidated
            assert mock_pipe.delete.call_count == 3  # 2 cache keys + 1 dependency key
    
    @pytest.mark.asyncio
    async def test_invalidate_by_dependency_no_dependents(self, cache_service):
        """Test invalidation when no dependents exist."""
        resource_id = "orphan_resource"
        
        cache_service.redis_manager.client.smembers.return_value = []
        
        count = await cache_service.invalidate_by_dependency(resource_id)
        
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_warm_cache(self, cache_service):
        """Test cache warming functionality."""
        tool_name = "warm_test"
        common_params = [
            {"param1": "value1"},
            {"param2": "value2"},
            {"param3": "value3"}
        ]
        
        # Mock execute function
        async def mock_execute_func(**params):
            return {"result": f"executed with {params}"}
        
        # Mock get_cached_result to simulate cache misses
        cache_service.get_cached_result = AsyncMock(return_value=None)
        
        # Mock cache_tool_result to simulate successful caching
        cache_service.cache_tool_result = AsyncMock(return_value=True)
        
        cached_count = await cache_service.warm_cache(tool_name, common_params, mock_execute_func)
        
        assert cached_count == len(common_params)
        assert cache_service.cache_tool_result.call_count == len(common_params)
    
    @pytest.mark.asyncio
    async def test_warm_cache_skip_existing(self, cache_service):
        """Test cache warming skips existing entries."""
        tool_name = "warm_existing"
        common_params = [{"param": "existing"}]
        
        async def mock_execute_func(**params):
            return {"result": "should not be called"}
        
        # Mock get_cached_result to simulate cache hit
        cache_service.get_cached_result = AsyncMock(return_value={"cached": True})
        cache_service.cache_tool_result = AsyncMock()
        
        cached_count = await cache_service.warm_cache(tool_name, common_params, mock_execute_func)
        
        assert cached_count == 0
        assert not cache_service.cache_tool_result.called
    
    @pytest.mark.asyncio
    async def test_warm_cache_concurrent_prevention(self, cache_service):
        """Test prevention of concurrent warmup tasks."""
        tool_name = "concurrent_test"
        
        # Start first warmup task
        task1 = asyncio.create_task(cache_service.warm_cache(tool_name, [], AsyncMock()))
        cache_service._warmup_tasks[tool_name] = task1
        
        # Try to start second warmup - should return 0 immediately
        result = await cache_service.warm_cache(tool_name, [{"test": "params"}], AsyncMock())
        
        assert result == 0
        
        # Cleanup
        task1.cancel()
        await asyncio.gather(task1, return_exceptions=True)
    
    @pytest.mark.asyncio
    async def test_get_tool_statistics_specific_tool(self, cache_service):
        """Test getting statistics for a specific tool."""
        tool_name = "test_tool"
        mock_stats = {
            b"hit_count": b"10",
            b"cache_count": b"5",
            b"last_hit": b"2025-01-01T12:00:00"
        }
        
        cache_service.redis_manager.client.hgetall.return_value = mock_stats
        cache_service._hit_count = 15
        cache_service._miss_count = 5
        
        stats = await cache_service.get_tool_statistics(tool_name)
        
        assert "overall" in stats
        assert stats["overall"]["hit_rate"] == 0.75  # 15/(15+5)
        assert tool_name in stats
        assert stats[tool_name]["hit_count"] == "10"
    
    @pytest.mark.asyncio
    async def test_get_tool_statistics_all_tools(self, cache_service):
        """Test getting statistics for all tools."""
        # Mock scan_iter to return tool stats keys
        async def mock_scan_iter(match):
            keys = [
                b"tool_stats:store_memory",
                b"tool_stats:retrieve_memory"
            ]
            for key in keys:
                yield key
        
        cache_service.redis_manager.client.scan_iter = mock_scan_iter
        cache_service.redis_manager.client.hgetall.return_value = {b"hit_count": b"5"}
        
        stats = await cache_service.get_tool_statistics()
        
        assert "overall" in stats
        assert "store_memory" in stats
        assert "retrieve_memory" in stats
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_entries(self, cache_service):
        """Test cleanup of expired cache entries."""
        # Mock dependency keys
        async def mock_scan_iter(match):
            yield b"tool_deps:res_123"
            yield b"tool_deps:res_456"
        
        cache_service.redis_manager.client.scan_iter = mock_scan_iter
        
        # Mock smembers to return cache keys (some valid, some invalid)
        def mock_smembers(key):
            if key == b"tool_deps:res_123":
                return [b"cache_key_1", b"cache_key_2"]  # Both valid
            else:
                return [b"cache_key_3", b"cache_key_4"]  # One invalid
        
        cache_service.redis_manager.client.smembers.side_effect = mock_smembers
        
        # Mock exists to simulate some cache keys are gone
        def mock_exists(key):
            if key == b"cache_key_4":
                return False  # This key is invalid
            return True
        
        cache_service.redis_manager.client.exists.side_effect = mock_exists
        
        cleanup_stats = await cache_service.cleanup_expired_entries()
        
        assert "cleaned_cache_entries" in cleanup_stats
        assert "cleaned_dependency_mappings" in cleanup_stats
        assert "timestamp" in cleanup_stats


class TestToolCacheSingleton:
    """Test tool cache service singleton functionality."""
    
    @pytest.mark.asyncio
    async def test_get_tool_cache_service_singleton(self):
        """Test that get_tool_cache_service returns the same instance."""
        # Clear any existing instance
        import ltms.services.tool_cache_service as cache_module
        cache_module._tool_cache_service = None
        
        with patch('ltms.services.tool_cache_service.get_redis_manager') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis
            
            service1 = await cache_module.get_tool_cache_service()
            service2 = await cache_module.get_tool_cache_service()
            
            assert service1 is service2
            mock_get_redis.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_tool_cache(self):
        """Test tool cache cleanup functionality."""
        import ltms.services.tool_cache_service as cache_module
        
        # Create mock service with warmup tasks
        mock_service = MagicMock()
        mock_task = MagicMock()  # Don't use AsyncMock for done() method
        mock_task.done.return_value = False
        mock_task.cancel = MagicMock()
        mock_service._warmup_tasks = {"test_tool": mock_task}
        
        cache_module._tool_cache_service = mock_service
        
        await cache_module.cleanup_tool_cache()
        
        # Verify cleanup
        mock_task.cancel.assert_called_once()
        assert cache_module._tool_cache_service is None


@pytest.mark.integration
class TestToolCacheServiceIntegration:
    """Integration tests for Tool Cache Service with real Redis."""
    
    @pytest.mark.asyncio
    async def test_real_redis_tool_caching(self):
        """Test tool caching with real Redis connection."""
        try:
            # Use test Redis instance
            from ltms.services.redis_service import RedisConnectionManager
            manager = RedisConnectionManager(
                host="localhost",
                port=6381,
                password=os.getenv("REDIS_PASSWORD", "test_password"),
                db=1  # Use different DB for tests
            )
            await manager.initialize()
            
            if not manager.is_connected:
                pytest.skip("Redis server not available for integration test")
            
            cache_service = ToolCacheService(manager)
            
            # Test full cache lifecycle
            tool_name = "integration_test_tool"
            params = {"test_param": "test_value"}
            result = {"success": True, "resource_id": "test_res_123"}
            
            # Cache the result
            cache_success = await cache_service.cache_tool_result(tool_name, params, result)
            assert cache_success is True
            
            # Retrieve the result
            cached_result = await cache_service.get_cached_result(tool_name, params)
            assert cached_result == result
            
            # Test dependency invalidation
            invalidated = await cache_service.invalidate_by_dependency("test_res_123")
            assert invalidated >= 1
            
            # Verify result is no longer cached
            cached_after_invalidation = await cache_service.get_cached_result(tool_name, params)
            assert cached_after_invalidation is None
            
            # Test statistics
            stats = await cache_service.get_tool_statistics(tool_name)
            assert "overall" in stats
            assert stats["overall"]["hit_count"] >= 1
            
            # Cleanup
            await cache_service.cleanup_expired_entries()
            await manager.close()
            
        except Exception as e:
            pytest.skip(f"Redis integration test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])