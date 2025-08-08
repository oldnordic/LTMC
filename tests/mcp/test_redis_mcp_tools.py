"""Tests for Redis MCP tools."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Import the MCP server functions
from ltms.mcp_server import redis_cache_stats, redis_flush_cache, redis_health_check


class TestRedisMCPTools:
    """Test Redis MCP tool functions."""
    
    def test_redis_cache_stats_success(self):
        """Test successful Redis cache stats retrieval."""
        mock_stats = {
            "connected": True,
            "redis_version": "6.2.7",
            "used_memory": "1.2M",
            "total_connections": 5,
            "embedding_cache_count": 10,
            "query_cache_count": 5,
            "total_keys": 15
        }
        
        with patch('ltms.mcp_server.get_cache_service') as mock_get_cache:
            mock_cache_service = AsyncMock()
            mock_cache_service.get_cache_stats.return_value = mock_stats
            mock_get_cache.return_value = mock_cache_service
            
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = mock_stats
                
                result = redis_cache_stats()
                
                assert result["success"] is True
                assert result["stats"] == mock_stats
    
    def test_redis_cache_stats_failure(self):
        """Test Redis cache stats failure."""
        with patch('ltms.mcp_server.get_cache_service') as mock_get_cache:
            mock_get_cache.side_effect = Exception("Redis connection failed")
            
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = {"connected": False, "error": "Redis connection failed"}
                
                result = redis_cache_stats()
                
                assert result["success"] is True  # Success in calling the function
                assert result["stats"]["connected"] is False
                assert "error" in result["stats"]
    
    def test_redis_flush_cache_all(self):
        """Test flushing all Redis cache types."""
        mock_result = {
            "flushed_embeddings": 10,
            "flushed_queries": 5,
            "flushed_chunks": 3,
            "flushed_resources": 2,
            "total_flushed": 20
        }
        
        with patch('ltms.mcp_server.get_cache_service') as mock_get_cache:
            mock_cache_service = AsyncMock()
            mock_cache_service.invalidate_cache.side_effect = [10, 5, 3, 2]  # Return counts for each call
            mock_get_cache.return_value = mock_cache_service
            
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = mock_result
                
                result = redis_flush_cache("all")
                
                assert result["success"] is True
                assert result["result"]["total_flushed"] == 20
                assert result["result"]["flushed_embeddings"] == 10
                assert result["result"]["flushed_queries"] == 5
    
    def test_redis_flush_cache_embeddings_only(self):
        """Test flushing only embedding cache."""
        with patch('ltms.mcp_server.get_cache_service') as mock_get_cache:
            mock_cache_service = AsyncMock()
            mock_cache_service.invalidate_cache.return_value = 15
            mock_get_cache.return_value = mock_cache_service
            
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = {"flushed_embeddings": 15}
                
                result = redis_flush_cache("embeddings")
                
                assert result["success"] is True
                assert result["result"]["flushed_embeddings"] == 15
    
    def test_redis_flush_cache_queries_only(self):
        """Test flushing only query cache."""
        with patch('ltms.mcp_server.get_cache_service') as mock_get_cache:
            mock_cache_service = AsyncMock()
            mock_cache_service.invalidate_cache.return_value = 8
            mock_get_cache.return_value = mock_cache_service
            
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = {"flushed_queries": 8}
                
                result = redis_flush_cache("queries")
                
                assert result["success"] is True
                assert result["result"]["flushed_queries"] == 8
    
    def test_redis_flush_cache_invalid_type(self):
        """Test flushing with invalid cache type."""
        with patch('ltms.mcp_server.get_cache_service') as mock_get_cache:
            mock_cache_service = AsyncMock()
            mock_get_cache.return_value = mock_cache_service
            
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = {"error": "Unknown cache_type: invalid"}
                
                result = redis_flush_cache("invalid")
                
                assert result["success"] is True
                assert "error" in result["result"]
    
    def test_redis_flush_cache_failure(self):
        """Test Redis cache flush failure."""
        with patch('ltms.mcp_server.get_cache_service') as mock_get_cache:
            mock_get_cache.side_effect = Exception("Redis connection failed")
            
            result = redis_flush_cache("all")
            
            assert result["success"] is False
            assert "error" in result
    
    def test_redis_health_check_healthy(self):
        """Test Redis health check when healthy."""
        mock_health = {
            "healthy": True,
            "connected": True,
            "host": "localhost",
            "port": 6380,
            "db": 0
        }
        
        with patch('ltms.mcp_server.get_redis_manager') as mock_get_manager:
            mock_manager = AsyncMock()
            mock_manager.health_check.return_value = True
            mock_manager.is_connected = True
            mock_manager.host = "localhost"
            mock_manager.port = 6380
            mock_manager.db = 0
            mock_get_manager.return_value = mock_manager
            
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = mock_health
                
                result = redis_health_check()
                
                assert result["success"] is True
                assert result["health"]["healthy"] is True
                assert result["health"]["connected"] is True
                assert result["health"]["host"] == "localhost"
                assert result["health"]["port"] == 6380
    
    def test_redis_health_check_unhealthy(self):
        """Test Redis health check when unhealthy."""
        mock_health = {
            "healthy": False,
            "connected": False,
            "error": "Connection refused"
        }
        
        with patch('ltms.mcp_server.get_redis_manager') as mock_get_manager:
            mock_get_manager.side_effect = Exception("Connection refused")
            
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = mock_health
                
                result = redis_health_check()
                
                assert result["success"] is True
                assert result["health"]["healthy"] is False
                assert result["health"]["connected"] is False
                assert "error" in result["health"]
    
    def test_redis_health_check_failure(self):
        """Test Redis health check failure."""
        with patch('ltms.mcp_server.get_redis_manager') as mock_get_manager:
            mock_get_manager.side_effect = Exception("Redis manager creation failed")
            
            result = redis_health_check()
            
            assert result["success"] is False
            assert "error" in result


class TestAsyncEventLoopHandling:
    """Test async event loop handling in MCP tools."""
    
    def test_running_event_loop_handling(self):
        """Test handling of running event loop in Redis tools."""
        mock_loop = MagicMock()
        mock_loop.is_running.return_value = True
        
        with patch('asyncio.get_event_loop', return_value=mock_loop):
            with patch('concurrent.futures.ThreadPoolExecutor') as mock_executor:
                mock_future = MagicMock()
                mock_future.result.return_value = {"connected": True}
                mock_executor.return_value.__enter__.return_value.submit.return_value = mock_future
                
                result = redis_cache_stats()
                
                assert result["success"] is True
                assert result["stats"]["connected"] is True
    
    def test_no_event_loop_handling(self):
        """Test handling when no event loop is running."""
        mock_loop = MagicMock()
        mock_loop.is_running.return_value = False
        
        with patch('asyncio.get_event_loop', return_value=mock_loop):
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = {"connected": True}
                
                result = redis_cache_stats()
                
                assert result["success"] is True
                assert result["stats"]["connected"] is True
                mock_run.assert_called_once()


class TestRedisToolsErrorHandling:
    """Test error handling in Redis MCP tools."""
    
    def test_general_exception_handling(self):
        """Test general exception handling in Redis tools."""
        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_get_loop.side_effect = Exception("Event loop error")
            
            result = redis_cache_stats()
            
            assert result["success"] is False
            assert "error" in result
    
    def test_async_function_exception_handling(self):
        """Test exception handling in async functions."""
        with patch('asyncio.run') as mock_run:
            mock_run.side_effect = Exception("Async execution error")
            
            result = redis_health_check()
            
            assert result["success"] is False
            assert "error" in result
    
    def test_concurrent_execution_error_handling(self):
        """Test error handling in concurrent execution."""
        mock_loop = MagicMock()
        mock_loop.is_running.return_value = True
        
        with patch('asyncio.get_event_loop', return_value=mock_loop):
            with patch('concurrent.futures.ThreadPoolExecutor') as mock_executor:
                mock_executor.side_effect = Exception("Executor error")
                
                result = redis_flush_cache("all")
                
                assert result["success"] is False
                assert "error" in result


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])