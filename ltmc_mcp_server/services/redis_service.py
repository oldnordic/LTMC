"""
Redis Service - Caching Operations
=================================

Extended Redis operations service for LTMC caching.
Existing Redis config: port 6382, password 'ltmc_cache_2025'
"""

import redis.asyncio as redis
import json
import time
import logging
from typing import Any, Optional, Dict, List

from config.settings import LTMCSettings
from utils.performance_utils import measure_performance


class RedisService:
    """
    Extended Redis service for caching operations.
    
    Uses existing Redis instance on port 6382 with password.
    Supports all operations needed by redis tools.
    """
    
    def __init__(self, settings: LTMCSettings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.redis_client: Optional[redis.Redis] = None
        self._initialized = False
        
    async def initialize(self) -> bool:
        """Initialize Redis connection."""
        if self._initialized:
            return True
            
        if not self.settings.redis_enabled:
            self.logger.info("Redis disabled in settings")
            return False
            
        try:
            self.redis_client = redis.Redis(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                password=self.settings.redis_password,
                db=self.settings.redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            await self.redis_client.ping()
            self._initialized = True
            self.logger.info("✅ Redis connection initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Redis initialization failed: {e}")
            return False
    
    @measure_performance
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform Redis health check.
        
        Returns:
            Dict with health status, latency, and metrics
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            if not self.redis_client:
                return {
                    "status": "error",
                    "connected": False,
                    "error": "Redis client not initialized"
                }
            
            # Measure ping latency
            start_time = time.time()
            pong = await self.redis_client.ping()
            latency_ms = (time.time() - start_time) * 1000
            
            if pong:
                # Get basic Redis info
                info = await self.redis_client.info()
                
                return {
                    "status": "healthy",
                    "connected": True,
                    "latency_ms": round(latency_ms, 2),
                    "version": info.get("redis_version", "unknown"),
                    "memory_usage": {
                        "used_memory": info.get("used_memory", 0),
                        "used_memory_human": info.get("used_memory_human", "0B"),
                        "max_memory": info.get("maxmemory", 0)
                    }
                }
            else:
                return {
                    "status": "unhealthy",
                    "connected": False,
                    "error": "Ping failed"
                }
                
        except Exception as e:
            self.logger.error(f"Redis health check failed: {e}")
            return {
                "status": "error",
                "connected": False,
                "error": str(e)
            }
    
    @measure_performance
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics.
        
        Returns:
            Dict with cache statistics and metrics
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            if not self.redis_client:
                return {"error": "Redis client not initialized", "total_keys": 0, "hit_rate": 0}
            
            # Get Redis info
            info = await self.redis_client.info()
            
            # Count total keys
            total_keys = await self.redis_client.dbsize()
            
            # Calculate hit rate from Redis stats
            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 0)
            total_requests = hits + misses
            hit_rate = (hits / total_requests) if total_requests > 0 else 0
            
            return {
                "total_keys": total_keys,
                "keyspace_hits": hits,
                "keyspace_misses": misses,
                "hit_rate": round(hit_rate, 3),
                "memory_usage": {
                    "used_memory": info.get("used_memory", 0),
                    "used_memory_human": info.get("used_memory_human", "0B"),
                    "peak_memory": info.get("used_memory_peak", 0),
                    "peak_memory_human": info.get("used_memory_peak_human", "0B")
                },
                "connections": {
                    "connected_clients": info.get("connected_clients", 0),
                    "total_connections": info.get("total_connections_received", 0)
                },
                "uptime_seconds": info.get("uptime_in_seconds", 0)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get cache stats: {e}")
            return {
                "error": str(e),
                "total_keys": 0,
                "hit_rate": 0
            }
    
    # Legacy methods (maintain compatibility)
    @measure_performance
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache (legacy method)."""
        if not self.redis_client:
            return None
            
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            self.logger.error(f"Redis get error: {e}")
            return None
    
    @measure_performance  
    async def set(self, key: str, value: Any, expiry: int = 3600) -> bool:
        """Set value in Redis cache with expiry (legacy method)."""
        if not self.redis_client:
            return False
            
        try:
            await self.redis_client.set(
                key, 
                json.dumps(value), 
                ex=expiry
            )
            return True
        except Exception as e:
            self.logger.error(f"Redis set error: {e}")
            return False
    
    # New methods for redis tools
    @measure_performance
    async def set_cache(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set a cache value with optional TTL."""
        if not self.redis_client:
            return False
            
        try:
            if ttl:
                result = await self.redis_client.setex(key, ttl, value)
            else:
                result = await self.redis_client.set(key, value)
            
            return result is True
            
        except Exception as e:
            self.logger.error(f"Failed to set cache key '{key}': {e}")
            return False
    
    @measure_performance
    async def get_cache(self, key: str) -> Optional[str]:
        """Get a cache value by key (returns raw string)."""
        if not self.redis_client:
            return None
            
        try:
            value = await self.redis_client.get(key)
            return value
            
        except Exception as e:
            self.logger.error(f"Failed to get cache key '{key}': {e}")
            return None
    
    @measure_performance
    async def delete_cache(self, key: str) -> bool:
        """Delete a cache key."""
        if not self.redis_client:
            return False
            
        try:
            deleted_count = await self.redis_client.delete(key)
            return deleted_count > 0
            
        except Exception as e:
            self.logger.error(f"Failed to delete cache key '{key}': {e}")
            return False
    
    @measure_performance
    async def clear_cache(self, pattern: Optional[str] = None) -> int:
        """Clear cache keys matching pattern or all keys."""
        if not self.redis_client:
            return 0
            
        try:
            if pattern:
                # Get keys matching pattern
                keys = await self.redis_client.keys(pattern)
                if keys:
                    deleted_count = await self.redis_client.delete(*keys)
                    return deleted_count
                else:
                    return 0
            else:
                # Get current key count, then clear all
                current_keys = await self.redis_client.dbsize()
                await self.redis_client.flushdb()
                return current_keys
                
        except Exception as e:
            self.logger.error(f"Failed to clear cache with pattern '{pattern}': {e}")
            return 0
    
    async def get_keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching a pattern."""
        if not self.redis_client:
            return []
            
        try:
            keys = await self.redis_client.keys(pattern)
            return keys or []
            
        except Exception as e:
            self.logger.error(f"Failed to get keys with pattern '{pattern}': {e}")
            return []
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()