"""Statistics and performance tracking for chunk buffer service."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ltms.services.redis_service import RedisConnectionManager

logger = logging.getLogger(__name__)


class ChunkBufferStats:
    """Performance and usage statistics for chunk buffer."""
    
    def __init__(self, redis_manager: RedisConnectionManager):
        """Initialize chunk buffer statistics tracking.
        
        Args:
            redis_manager: Redis connection manager instance
        """
        self.redis_manager = redis_manager
        
        # Redis key prefixes for statistics
        self.STATS_PREFIX = "chunks:stats"
        self.PERFORMANCE_KEY = f"{self.STATS_PREFIX}:performance"
        self.USAGE_KEY = f"{self.STATS_PREFIX}:usage"
        
        # TTL for statistics (24 hours)
        self.STATS_TTL = 86400

    async def record_hit(self) -> None:
        """Record a cache hit."""
        try:
            redis_client = self.redis_manager.client
            async with redis_client.pipeline(transaction=True) as pipe:
                pipe.hincrby(self.PERFORMANCE_KEY, "hit_count", 1)
                pipe.hset(self.PERFORMANCE_KEY, "last_hit", datetime.now(timezone.utc).isoformat())
                pipe.expire(self.PERFORMANCE_KEY, self.STATS_TTL)
                await pipe.execute()
        except Exception as e:
            logger.error(f"Failed to record hit: {e}")

    async def record_miss(self) -> None:
        """Record a cache miss."""
        try:
            redis_client = self.redis_manager.client
            async with redis_client.pipeline(transaction=True) as pipe:
                pipe.hincrby(self.PERFORMANCE_KEY, "miss_count", 1)
                pipe.hset(self.PERFORMANCE_KEY, "last_miss", datetime.now(timezone.utc).isoformat())
                pipe.expire(self.PERFORMANCE_KEY, self.STATS_TTL)
                await pipe.execute()
        except Exception as e:
            logger.error(f"Failed to record miss: {e}")

    async def record_eviction(self) -> None:
        """Record a single chunk eviction."""
        try:
            redis_client = self.redis_manager.client
            async with redis_client.pipeline(transaction=True) as pipe:
                pipe.hincrby(self.PERFORMANCE_KEY, "eviction_count", 1)
                pipe.hset(self.PERFORMANCE_KEY, "last_eviction", datetime.now(timezone.utc).isoformat())
                pipe.expire(self.PERFORMANCE_KEY, self.STATS_TTL)
                await pipe.execute()
        except Exception as e:
            logger.error(f"Failed to record eviction: {e}")

    async def record_evictions(self, count: int) -> None:
        """Record multiple chunk evictions.
        
        Args:
            count: Number of chunks evicted
        """
        try:
            redis_client = self.redis_manager.client
            async with redis_client.pipeline(transaction=True) as pipe:
                pipe.hincrby(self.PERFORMANCE_KEY, "eviction_count", count)
                pipe.hset(self.PERFORMANCE_KEY, "last_eviction", datetime.now(timezone.utc).isoformat())
                pipe.expire(self.PERFORMANCE_KEY, self.STATS_TTL)
                await pipe.execute()
        except Exception as e:
            logger.error(f"Failed to record evictions: {e}")

    async def record_deduplication(self) -> None:
        """Record a deduplication save."""
        try:
            redis_client = self.redis_manager.client
            async with redis_client.pipeline(transaction=True) as pipe:
                pipe.hincrby(self.PERFORMANCE_KEY, "deduplication_saves", 1)
                pipe.hset(self.PERFORMANCE_KEY, "last_dedup", datetime.now(timezone.utc).isoformat())
                pipe.expire(self.PERFORMANCE_KEY, self.STATS_TTL)
                await pipe.execute()
        except Exception as e:
            logger.error(f"Failed to record deduplication: {e}")

    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        try:
            redis_client = self.redis_manager.client
            
            # Get performance metrics
            perf_data = await redis_client.hgetall(self.PERFORMANCE_KEY)
            
            if not perf_data:
                return {
                    "hit_count": 0,
                    "miss_count": 0,
                    "hit_rate": 0.0,
                    "eviction_count": 0,
                    "deduplication_saves": 0
                }
            
            # Convert bytes to strings and integers
            stats = {}
            for key, value in perf_data.items():
                key_str = key.decode() if isinstance(key, bytes) else key
                value_str = value.decode() if isinstance(value, bytes) else value
                
                if key_str.endswith("_count") or key_str.endswith("_saves"):
                    stats[key_str] = int(value_str)
                else:
                    stats[key_str] = value_str
            
            # Calculate hit rate
            hit_count = stats.get("hit_count", 0)
            miss_count = stats.get("miss_count", 0)
            total_requests = hit_count + miss_count
            
            if total_requests > 0:
                stats["hit_rate"] = hit_count / total_requests
            else:
                stats["hit_rate"] = 0.0
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {"error": str(e)}

    async def record_usage_metric(self, metric_name: str, value: Any) -> None:
        """Record a usage metric.
        
        Args:
            metric_name: Name of the metric
            value: Value to record
        """
        try:
            redis_client = self.redis_manager.client
            async with redis_client.pipeline(transaction=True) as pipe:
                pipe.hset(self.USAGE_KEY, metric_name, str(value))
                pipe.hset(self.USAGE_KEY, f"{metric_name}_timestamp", datetime.now(timezone.utc).isoformat())
                pipe.expire(self.USAGE_KEY, self.STATS_TTL)
                await pipe.execute()
        except Exception as e:
            logger.error(f"Failed to record usage metric {metric_name}: {e}")

    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics.
        
        Returns:
            Dictionary with usage metrics
        """
        try:
            redis_client = self.redis_manager.client
            usage_data = await redis_client.hgetall(self.USAGE_KEY)
            
            if not usage_data:
                return {}
            
            # Convert bytes to strings
            return {
                key.decode() if isinstance(key, bytes) else key:
                value.decode() if isinstance(value, bytes) else value
                for key, value in usage_data.items()
            }
            
        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            return {"error": str(e)}

    async def reset_stats(self) -> bool:
        """Reset all statistics.
        
        Returns:
            True if reset successfully
        """
        try:
            redis_client = self.redis_manager.client
            
            async with redis_client.pipeline(transaction=True) as pipe:
                pipe.delete(self.PERFORMANCE_KEY)
                pipe.delete(self.USAGE_KEY)
                await pipe.execute()
            
            logger.info("Chunk buffer statistics reset")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset stats: {e}")
            return False

    async def get_all_stats(self) -> Dict[str, Any]:
        """Get all statistics (performance + usage).
        
        Returns:
            Combined statistics dictionary
        """
        try:
            performance_stats = await self.get_performance_stats()
            usage_stats = await self.get_usage_stats()
            
            return {
                "performance": performance_stats,
                "usage": usage_stats,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get all stats: {e}")
            return {"error": str(e)}