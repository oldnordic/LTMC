"""Redis service for LTMC caching layer."""

import json
import logging
import pickle
from typing import Any, Dict, List, Optional, Union
import redis
import redis.asyncio as aioredis
from contextlib import asynccontextmanager
import asyncio

logger = logging.getLogger(__name__)

class RedisConnectionManager:
    """Manages Redis connections for LTMC with standalone server configuration."""
    
    def __init__(
        self,
        host: str = "localhost", 
        port: int = 6381,  # Different port to avoid KWE conflicts (6379=KWE native, 6380=KWE docker)
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 20,
        socket_keepalive: bool = True,
        socket_keepalive_options: Optional[Dict[str, int]] = None
    ):
        """Initialize Redis connection manager.
        
        Args:
            host: Redis server host
            port: Redis server port (6381 to avoid KWE conflicts)
            db: Redis database number
            password: Optional password for authentication
            max_connections: Maximum connection pool size
            socket_keepalive: Enable socket keepalive
            socket_keepalive_options: Socket keepalive options
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.max_connections = max_connections
        
        # Configure socket keepalive - import socket module constants
        import socket as sock
        self.socket_keepalive_options = socket_keepalive_options or {
            sock.TCP_KEEPINTVL: 1,
            sock.TCP_KEEPCNT: 3,
            sock.TCP_KEEPIDLE: 1
        }
        
        self._pool: Optional[aioredis.ConnectionPool] = None
        self._client: Optional[aioredis.Redis] = None
        self._is_connected = False
        
    async def initialize(self) -> None:
        """Initialize Redis connection pool."""
        try:
            self._pool = aioredis.ConnectionPool(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                max_connections=self.max_connections,
                socket_keepalive=True,
                socket_keepalive_options=self.socket_keepalive_options,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            self._client = aioredis.Redis(connection_pool=self._pool)
            
            # Test connection
            await self._client.ping()
            self._is_connected = True
            logger.info(f"Redis connection established on {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._is_connected = False
            raise
    
    async def close(self) -> None:
        """Close Redis connections."""
        if self._client:
            await self._client.aclose()
            self._client = None
        
        if self._pool:
            await self._pool.aclose()
            self._pool = None
        
        self._is_connected = False
        logger.info("Redis connection closed")
    
    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        return self._is_connected
    
    @property
    def client(self) -> aioredis.Redis:
        """Get Redis client instance."""
        if not self._client or not self._is_connected:
            raise RuntimeError("Redis client not initialized or disconnected")
        return self._client
    
    async def health_check(self) -> bool:
        """Check Redis connection health."""
        try:
            if not self._client:
                return False
            await self._client.ping()
            return True
        except Exception:
            self._is_connected = False
            return False


class RedisCacheService:
    """Redis caching service for LTMC with embedding and query caching."""
    
    def __init__(self, connection_manager: RedisConnectionManager):
        """Initialize Redis cache service.
        
        Args:
            connection_manager: Redis connection manager instance
        """
        self.redis_manager = connection_manager
        
        # Cache prefixes for different data types
        self.EMBEDDING_PREFIX = "ltmc:embedding:"
        self.QUERY_PREFIX = "ltmc:query:"
        self.CHUNK_PREFIX = "ltmc:chunk:"
        self.RESOURCE_PREFIX = "ltmc:resource:"
        
        # Default TTL values (in seconds)
        self.DEFAULT_TTL = 3600  # 1 hour
        self.EMBEDDING_TTL = 7200  # 2 hours
        self.QUERY_TTL = 1800  # 30 minutes
    
    async def cache_embedding(
        self, 
        text: str, 
        embedding: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Cache text embedding.
        
        Args:
            text: Original text
            embedding: Embedding vector (numpy array or list)
            ttl: Time to live in seconds
            
        Returns:
            True if cached successfully
        """
        try:
            key = f"{self.EMBEDDING_PREFIX}{hash(text)}"
            
            # Serialize embedding using pickle for numpy compatibility
            if hasattr(embedding, 'tolist'):
                # Convert numpy array to list for JSON serialization
                data = {"embedding": embedding.tolist(), "text": text}
                value = json.dumps(data)
            else:
                # Use pickle for complex objects
                value = pickle.dumps({"embedding": embedding, "text": text})
            
            ttl = ttl or self.EMBEDDING_TTL
            await self.redis_manager.client.setex(key, ttl, value)
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache embedding: {e}")
            return False
    
    async def get_cached_embedding(self, text: str) -> Optional[Any]:
        """Get cached embedding for text.
        
        Args:
            text: Original text
            
        Returns:
            Cached embedding or None if not found
        """
        try:
            key = f"{self.EMBEDDING_PREFIX}{hash(text)}"
            value = await self.redis_manager.client.get(key)
            
            if not value:
                return None
            
            try:
                # Try JSON first
                data = json.loads(value)
                return data.get("embedding")
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Fall back to pickle
                data = pickle.loads(value)
                return data.get("embedding")
                
        except Exception as e:
            logger.error(f"Failed to get cached embedding: {e}")
            return None
    
    async def cache_query_result(
        self, 
        query: str, 
        results: List[Dict[str, Any]], 
        ttl: Optional[int] = None
    ) -> bool:
        """Cache query results.
        
        Args:
            query: Search query
            results: Query results
            ttl: Time to live in seconds
            
        Returns:
            True if cached successfully
        """
        try:
            key = f"{self.QUERY_PREFIX}{hash(query)}"
            value = json.dumps({"query": query, "results": results})
            ttl = ttl or self.QUERY_TTL
            await self.redis_manager.client.setex(key, ttl, value)
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache query result: {e}")
            return False
    
    async def get_cached_query_result(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached query results.
        
        Args:
            query: Search query
            
        Returns:
            Cached results or None if not found
        """
        try:
            key = f"{self.QUERY_PREFIX}{hash(query)}"
            value = await self.redis_manager.client.get(key)
            
            if not value:
                return None
            
            data = json.loads(value)
            return data.get("results")
            
        except Exception as e:
            logger.error(f"Failed to get cached query result: {e}")
            return None
    
    async def invalidate_cache(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "ltmc:embedding:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            keys = []
            async for key in self.redis_manager.client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self.redis_manager.client.delete(*keys)
            return 0
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            info = await self.redis_manager.client.info()
            
            # Count keys by prefix
            embedding_count = len([
                key async for key in self.redis_manager.client.scan_iter(
                    match=f"{self.EMBEDDING_PREFIX}*"
                )
            ])
            
            query_count = len([
                key async for key in self.redis_manager.client.scan_iter(
                    match=f"{self.QUERY_PREFIX}*"
                )
            ])
            
            return {
                "connected": self.redis_manager.is_connected,
                "redis_version": info.get("redis_version", "unknown"),
                "used_memory": info.get("used_memory_human", "unknown"),
                "total_connections": info.get("connected_clients", 0),
                "embedding_cache_count": embedding_count,
                "query_cache_count": query_count,
                "total_keys": info.get("db0", {}).get("keys", 0) if "db0" in info else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"connected": False, "error": str(e)}


# Global Redis instances (initialized lazily)
_redis_manager: Optional[RedisConnectionManager] = None
_cache_service: Optional[RedisCacheService] = None


async def get_redis_manager() -> RedisConnectionManager:
    """Get or create Redis connection manager."""
    global _redis_manager
    if not _redis_manager:
        _redis_manager = RedisConnectionManager(
            host="localhost",
            port=6381,
            password="ltmc_cache_2025"
        )
        await _redis_manager.initialize()
    return _redis_manager


async def get_cache_service() -> RedisCacheService:
    """Get or create Redis cache service."""
    global _cache_service
    if not _cache_service:
        manager = await get_redis_manager()
        _cache_service = RedisCacheService(manager)
    return _cache_service


@asynccontextmanager
async def redis_context():
    """Context manager for Redis operations."""
    manager = None
    try:
        manager = await get_redis_manager()
        yield manager
    except Exception as e:
        logger.error(f"Redis context error: {e}")
        raise
    finally:
        if manager and not manager.is_connected:
            # Try to reconnect if disconnected
            try:
                await manager.initialize()
            except Exception as e:
                logger.error(f"Failed to reconnect to Redis: {e}")


async def cleanup_redis():
    """Cleanup Redis connections on shutdown."""
    global _redis_manager, _cache_service
    
    if _redis_manager:
        await _redis_manager.close()
        _redis_manager = None
    
    _cache_service = None
    logger.info("Redis cleanup completed")