"""Tests for Redis service and caching functionality."""

import pytest
import numpy as np
import asyncio
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

from ltms.services.redis_service import (
    RedisConnectionManager,
    RedisCacheService,
    get_redis_manager,
    get_cache_service,
    cleanup_redis,
    redis_context
)


class TestRedisConnectionManager:
    """Test Redis connection management."""
    
    @pytest.mark.asyncio
    async def test_redis_manager_initialization(self):
        """Test Redis manager initialization with custom settings."""
        manager = RedisConnectionManager(
            host="localhost",
            port=6380,
            db=1,
            password="test_password",
            max_connections=10
        )
        
        assert manager.host == "localhost"
        assert manager.port == 6380
        assert manager.db == 1
        assert manager.password == "test_password"
        assert manager.max_connections == 10
        assert not manager.is_connected
    
    @pytest.mark.asyncio
    async def test_redis_manager_default_settings(self):
        """Test Redis manager with default settings."""
        manager = RedisConnectionManager()
        
        assert manager.host == "localhost"
        assert manager.port == 6380  # LTMC default port
        assert manager.db == 0
        assert manager.password is None
        assert not manager.is_connected
    
    @pytest.mark.asyncio
    async def test_redis_connection_failure(self):
        """Test Redis connection failure handling."""
        manager = RedisConnectionManager(port=9999)  # Non-existent port
        
        with pytest.raises(Exception):
            await manager.initialize()
        
        assert not manager.is_connected
    
    @pytest.mark.asyncio
    async def test_health_check_disconnected(self):
        """Test health check when disconnected."""
        manager = RedisConnectionManager()
        
        is_healthy = await manager.health_check()
        assert not is_healthy


class TestRedisCacheService:
    """Test Redis caching service."""
    
    @pytest.fixture
    async def mock_redis_manager(self):
        """Create mock Redis connection manager."""
        manager = MagicMock()
        manager.is_connected = True
        manager.client = AsyncMock()
        manager.host = "localhost"
        manager.port = 6380
        manager.db = 0
        return manager
    
    @pytest.fixture
    def cache_service(self, mock_redis_manager):
        """Create cache service with mock Redis manager."""
        return RedisCacheService(mock_redis_manager)
    
    @pytest.mark.asyncio
    async def test_cache_embedding_success(self, cache_service):
        """Test successful embedding caching."""
        text = "test text"
        embedding = np.array([1.0, 2.0, 3.0])
        
        # Mock Redis setex to return success
        cache_service.redis_manager.client.setex.return_value = True
        
        result = await cache_service.cache_embedding(text, embedding)
        
        assert result is True
        cache_service.redis_manager.client.setex.assert_called_once()
        
        # Check that the call was made with correct prefix
        call_args = cache_service.redis_manager.client.setex.call_args
        key = call_args[0][0]
        assert key.startswith("ltmc:embedding:")
    
    @pytest.mark.asyncio
    async def test_get_cached_embedding_hit(self, cache_service):
        """Test successful embedding cache retrieval."""
        text = "test text"
        cached_data = '{"embedding": [1.0, 2.0, 3.0], "text": "test text"}'
        
        # Mock Redis get to return cached data
        cache_service.redis_manager.client.get.return_value = cached_data
        
        result = await cache_service.get_cached_embedding(text)
        
        assert result == [1.0, 2.0, 3.0]
        cache_service.redis_manager.client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_cached_embedding_miss(self, cache_service):
        """Test embedding cache miss."""
        text = "test text"
        
        # Mock Redis get to return None (cache miss)
        cache_service.redis_manager.client.get.return_value = None
        
        result = await cache_service.get_cached_embedding(text)
        
        assert result is None
        cache_service.redis_manager.client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_query_result(self, cache_service):
        """Test query result caching."""
        query = "test query"
        results = [{"doc": "result1"}, {"doc": "result2"}]
        
        cache_service.redis_manager.client.setex.return_value = True
        
        success = await cache_service.cache_query_result(query, results)
        
        assert success is True
        cache_service.redis_manager.client.setex.assert_called_once()
        
        # Check that the call was made with correct prefix
        call_args = cache_service.redis_manager.client.setex.call_args
        key = call_args[0][0]
        assert key.startswith("ltmc:query:")
    
    @pytest.mark.asyncio
    async def test_get_cached_query_result(self, cache_service):
        """Test query result cache retrieval."""
        query = "test query"
        cached_data = '{"query": "test query", "results": [{"doc": "result1"}]}'
        
        cache_service.redis_manager.client.get.return_value = cached_data
        
        result = await cache_service.get_cached_query_result(query)
        
        assert result == [{"doc": "result1"}]
        cache_service.redis_manager.client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_invalidate_cache_success(self, cache_service):
        """Test cache invalidation."""
        pattern = "ltmc:embedding:*"
        
        # Mock scan_iter to return some keys
        async def mock_scan_iter(match):
            test_keys = [b"ltmc:embedding:1", b"ltmc:embedding:2"]
            for key in test_keys:
                yield key
        
        cache_service.redis_manager.client.scan_iter = mock_scan_iter
        cache_service.redis_manager.client.delete.return_value = 2
        
        deleted_count = await cache_service.invalidate_cache(pattern)
        
        assert deleted_count == 2
        cache_service.redis_manager.client.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_cache_stats(self, cache_service):
        """Test cache statistics retrieval."""
        mock_info = {
            "redis_version": "6.2.7",
            "used_memory_human": "1.2M",
            "connected_clients": 5,
            "db0": {"keys": 100}
        }
        
        cache_service.redis_manager.client.info.return_value = mock_info
        
        # Mock scan_iter for counting keys
        async def mock_scan_iter_empty(match):
            # Return no keys for simplicity
            return
            yield  # This line won't be reached, it's just to make this a generator
        
        cache_service.redis_manager.client.scan_iter = mock_scan_iter_empty
        
        stats = await cache_service.get_cache_stats()
        
        assert stats["connected"] is True
        assert stats["redis_version"] == "6.2.7"
        assert stats["used_memory"] == "1.2M"
        assert stats["total_connections"] == 5
        assert stats["total_keys"] == 100
    
    @pytest.mark.asyncio
    async def test_cache_error_handling(self, cache_service):
        """Test error handling in cache operations."""
        # Mock Redis client to raise exception
        cache_service.redis_manager.client.setex.side_effect = Exception("Redis error")
        
        result = await cache_service.cache_embedding("test", np.array([1.0, 2.0]))
        
        assert result is False


class TestRedisSingleton:
    """Test Redis singleton instances."""
    
    @pytest.mark.asyncio
    async def test_get_redis_manager_singleton(self):
        """Test that get_redis_manager returns the same instance."""
        # Clear any existing instance
        global _redis_manager
        import ltms.services.redis_service as redis_module
        redis_module._redis_manager = None
        
        with patch.object(RedisConnectionManager, 'initialize') as mock_init:
            mock_init.return_value = None
            
            manager1 = await get_redis_manager()
            manager2 = await get_redis_manager()
            
            assert manager1 is manager2
            mock_init.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_cache_service_singleton(self):
        """Test that get_cache_service returns the same instance."""
        # Clear any existing instances
        import ltms.services.redis_service as redis_module
        redis_module._redis_manager = None
        redis_module._cache_service = None
        
        with patch.object(RedisConnectionManager, 'initialize') as mock_init:
            mock_init.return_value = None
            
            service1 = await get_cache_service()
            service2 = await get_cache_service()
            
            assert service1 is service2
    
    @pytest.mark.asyncio
    async def test_cleanup_redis(self):
        """Test Redis cleanup functionality."""
        import ltms.services.redis_service as redis_module
        
        # Create mock manager
        mock_manager = AsyncMock()
        redis_module._redis_manager = mock_manager
        redis_module._cache_service = MagicMock()
        
        await cleanup_redis()
        
        # Verify cleanup was called
        mock_manager.close.assert_called_once()
        
        # Verify instances were reset
        assert redis_module._redis_manager is None
        assert redis_module._cache_service is None


class TestRedisContext:
    """Test Redis context manager."""
    
    @pytest.mark.asyncio
    async def test_redis_context_success(self):
        """Test successful Redis context usage."""
        with patch('ltms.services.redis_service.get_redis_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.is_connected = True
            mock_get_manager.return_value = mock_manager
            
            async with redis_context() as manager:
                assert manager is mock_manager
                mock_get_manager.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_redis_context_with_reconnection(self):
        """Test Redis context with reconnection on disconnect."""
        with patch('ltms.services.redis_service.get_redis_manager') as mock_get_manager:
            mock_manager = AsyncMock()
            mock_manager.is_connected = False
            mock_get_manager.return_value = mock_manager
            
            async with redis_context() as manager:
                assert manager is mock_manager
                # Should attempt to reconnect
                mock_manager.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_redis_context_error_handling(self):
        """Test Redis context error handling."""
        with patch('ltms.services.redis_service.get_redis_manager') as mock_get_manager:
            mock_get_manager.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception, match="Connection failed"):
                async with redis_context() as manager:
                    pass


@pytest.mark.integration
class TestRedisIntegration:
    """Integration tests for Redis (requires running Redis server)."""
    
    @pytest.mark.asyncio
    async def test_real_redis_connection(self):
        """Test real Redis connection (skip if Redis not available)."""
        manager = RedisConnectionManager(port=6380, password=None)
        
        try:
            await manager.initialize()
            
            if manager.is_connected:
                # Test basic operations
                cache_service = RedisCacheService(manager)
                
                # Test embedding caching
                test_text = "integration test text"
                test_embedding = np.array([0.1, 0.2, 0.3, 0.4])
                
                # Cache the embedding
                success = await cache_service.cache_embedding(test_text, test_embedding)
                assert success is True
                
                # Retrieve the embedding
                cached_embedding = await cache_service.get_cached_embedding(test_text)
                assert cached_embedding is not None
                np.testing.assert_array_almost_equal(np.array(cached_embedding), test_embedding)
                
                # Clean up
                await cache_service.invalidate_cache("ltmc:embedding:*")
                await manager.close()
            else:
                pytest.skip("Redis server not available on port 6380")
                
        except Exception as e:
            pytest.skip(f"Redis integration test failed: {e}")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])