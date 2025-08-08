"""Tool Result Cache Service for LTMC Redis orchestration layer."""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from ltms.services.redis_service import get_redis_manager, RedisConnectionManager

logger = logging.getLogger(__name__)


class ToolCacheService:
    """Advanced caching with intelligent expiry for tool results."""
    
    def __init__(self, redis_manager: RedisConnectionManager):
        """Initialize Tool Cache Service.
        
        Args:
            redis_manager: Redis connection manager instance
        """
        self.redis_manager = redis_manager
        
        # Cache key prefixes
        self.TOOL_CACHE_PREFIX = "tool_cache"
        self.TOOL_DEPS_PREFIX = "tool_deps"
        self.TOOL_STATS_PREFIX = "tool_stats"
        self.TOOL_WARMUP_PREFIX = "tool_warmup"
        
        # Cache configuration
        self.DEFAULT_TTL = 1800  # 30 minutes
        self.WARMUP_TTL = 3600   # 1 hour for warmed caches
        self.STATS_TTL = 86400   # 24 hours for statistics
        self.MAX_CACHE_SIZE_MB = 100  # Max cache size per tool
        
        # Performance tracking
        self._hit_count = 0
        self._miss_count = 0
        self._warmup_tasks: Dict[str, asyncio.Task] = {}
    
    def _generate_cache_key(self, tool_name: str, params: Dict[str, Any]) -> str:
        """Generate cache key for tool result.
        
        Args:
            tool_name: Name of the MCP tool
            params: Tool parameters
            
        Returns:
            Redis cache key
        """
        # Sort params for consistent hashing
        sorted_params = json.dumps(params, sort_keys=True, default=str)
        param_hash = hashlib.sha256(sorted_params.encode()).hexdigest()[:16]
        return f"{self.TOOL_CACHE_PREFIX}:{tool_name}:{param_hash}"
    
    def _extract_dependencies(self, result: Any) -> List[str]:
        """Extract resource dependencies from tool result.
        
        Args:
            result: Tool execution result
            
        Returns:
            List of resource IDs that this result depends on
        """
        dependencies = []
        
        if isinstance(result, dict):
            # Look for common resource ID patterns
            if "resource_id" in result:
                dependencies.append(str(result["resource_id"]))
            if "chunk_id" in result:
                dependencies.append(f"chunk:{result['chunk_id']}")
            if "file_name" in result:
                dependencies.append(f"file:{result['file_name']}")
            if "results" in result and isinstance(result["results"], list):
                for item in result["results"]:
                    if isinstance(item, dict) and "id" in item:
                        dependencies.append(str(item["id"]))
        
        return dependencies
    
    async def cache_tool_result(
        self,
        tool_name: str,
        params: Dict[str, Any],
        result: Any,
        ttl: Optional[int] = None,
        dependencies: Optional[List[str]] = None
    ) -> bool:
        """Cache tool execution result.
        
        Args:
            tool_name: Name of the MCP tool
            params: Tool parameters used for execution
            result: Tool execution result
            ttl: Time to live in seconds (defaults to DEFAULT_TTL)
            dependencies: Explicit resource dependencies
            
        Returns:
            True if cached successfully
        """
        try:
            cache_key = self._generate_cache_key(tool_name, params)
            
            # Auto-detect dependencies if not provided
            if dependencies is None:
                dependencies = self._extract_dependencies(result)
            
            # Prepare cache entry
            cache_entry = {
                "result": result,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "tool_name": tool_name,
                "params": params,
                "dependencies": dependencies,
                "hit_count": 0
            }
            
            # Serialize cache entry
            cache_data = json.dumps(cache_entry, default=str)
            
            # Check cache size limit
            if len(cache_data.encode()) > self.MAX_CACHE_SIZE_MB * 1024 * 1024:
                logger.warning(f"Tool result too large to cache: {tool_name}")
                return False
            
            # Store cache entry
            ttl = ttl or self.DEFAULT_TTL
            redis_client = self.redis_manager.client
            
            # Use pipeline for atomic operations
            async with redis_client.pipeline(transaction=True) as pipe:
                # Store the cache entry
                pipe.setex(cache_key, ttl, cache_data)
                
                # Update dependency mappings
                for dep in dependencies:
                    dep_key = f"{self.TOOL_DEPS_PREFIX}:{dep}"
                    pipe.sadd(dep_key, cache_key)
                    pipe.expire(dep_key, ttl + 300)  # Slightly longer TTL
                
                # Update statistics
                stats_key = f"{self.TOOL_STATS_PREFIX}:{tool_name}"
                pipe.hincrby(stats_key, "cache_count", 1)
                pipe.hset(stats_key, "last_cached", datetime.now(timezone.utc).isoformat())
                pipe.expire(stats_key, self.STATS_TTL)
                
                await pipe.execute()
            
            logger.debug(f"Cached result for {tool_name} with {len(dependencies)} dependencies")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache tool result for {tool_name}: {e}")
            return False
    
    async def get_cached_result(
        self,
        tool_name: str,
        params: Dict[str, Any],
        max_age_seconds: Optional[int] = None
    ) -> Optional[Any]:
        """Get cached tool result.
        
        Args:
            tool_name: Name of the MCP tool
            params: Tool parameters
            max_age_seconds: Maximum age of cache entry to accept
            
        Returns:
            Cached result or None if not found/expired
        """
        try:
            cache_key = self._generate_cache_key(tool_name, params)
            redis_client = self.redis_manager.client
            
            # Get cache entry
            cache_data = await redis_client.get(cache_key)
            if not cache_data:
                self._miss_count += 1
                return None
            
            # Parse cache entry
            cache_entry = json.loads(cache_data)
            
            # Check age if specified
            if max_age_seconds:
                created_at = datetime.fromisoformat(cache_entry["created_at"])
                age = (datetime.now(timezone.utc) - created_at).total_seconds()
                if age > max_age_seconds:
                    self._miss_count += 1
                    return None
            
            # Update hit statistics atomically
            async with redis_client.pipeline(transaction=True) as pipe:
                # Increment hit count in cache entry
                cache_entry["hit_count"] += 1
                cache_entry["last_accessed"] = datetime.now(timezone.utc).isoformat()
                updated_data = json.dumps(cache_entry, default=str)
                
                # Get current TTL and maintain it
                ttl = await redis_client.ttl(cache_key)
                if ttl > 0:
                    pipe.setex(cache_key, ttl, updated_data)
                else:
                    pipe.set(cache_key, updated_data)
                
                # Update tool statistics
                stats_key = f"{self.TOOL_STATS_PREFIX}:{tool_name}"
                pipe.hincrby(stats_key, "hit_count", 1)
                pipe.hset(stats_key, "last_hit", datetime.now(timezone.utc).isoformat())
                
                await pipe.execute()
            
            self._hit_count += 1
            logger.debug(f"Cache hit for {tool_name}")
            return cache_entry["result"]
            
        except Exception as e:
            logger.error(f"Failed to get cached result for {tool_name}: {e}")
            self._miss_count += 1
            return None
    
    async def invalidate_by_dependency(self, resource_id: str) -> int:
        """Invalidate all cached results that depend on a resource.
        
        Args:
            resource_id: Resource ID that changed
            
        Returns:
            Number of cache entries invalidated
        """
        try:
            dep_key = f"{self.TOOL_DEPS_PREFIX}:{resource_id}"
            redis_client = self.redis_manager.client
            
            # Get all cache keys that depend on this resource
            dependent_keys = await redis_client.smembers(dep_key)
            
            if not dependent_keys:
                return 0
            
            # Delete cache entries and dependency mappings
            async with redis_client.pipeline(transaction=True) as pipe:
                # Delete cache entries
                for cache_key in dependent_keys:
                    pipe.delete(cache_key)
                
                # Delete dependency mapping
                pipe.delete(dep_key)
                
                results = await pipe.execute()
            
            invalidated_count = sum(1 for r in results[:-1] if r > 0)
            logger.info(f"Invalidated {invalidated_count} cache entries for resource {resource_id}")
            return invalidated_count
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache for resource {resource_id}: {e}")
            return 0
    
    async def warm_cache(
        self,
        tool_name: str,
        common_params: List[Dict[str, Any]],
        execute_func: callable
    ) -> int:
        """Warm cache with frequently used tool calls.
        
        Args:
            tool_name: Name of the MCP tool
            common_params: List of common parameter sets
            execute_func: Function to execute tool (async callable)
            
        Returns:
            Number of entries successfully cached
        """
        if tool_name in self._warmup_tasks and not self._warmup_tasks[tool_name].done():
            logger.debug(f"Cache warmup already in progress for {tool_name}")
            return 0
        
        async def _warmup_task():
            cached_count = 0
            
            for params in common_params:
                try:
                    # Check if already cached
                    existing = await self.get_cached_result(tool_name, params)
                    if existing is not None:
                        continue
                    
                    # Execute tool and cache result
                    result = await execute_func(**params)
                    success = await self.cache_tool_result(
                        tool_name, 
                        params, 
                        result, 
                        ttl=self.WARMUP_TTL
                    )
                    
                    if success:
                        cached_count += 1
                        logger.debug(f"Warmed cache for {tool_name} with params: {params}")
                    
                    # Small delay to avoid overwhelming the system
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Failed to warm cache for {tool_name}: {e}")
                    continue
            
            return cached_count
        
        task = asyncio.create_task(_warmup_task())
        self._warmup_tasks[tool_name] = task
        
        try:
            return await task
        finally:
            self._warmup_tasks.pop(tool_name, None)
    
    async def get_tool_statistics(self, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """Get cache statistics for tools.
        
        Args:
            tool_name: Specific tool name or None for all tools
            
        Returns:
            Dictionary with cache statistics
        """
        try:
            redis_client = self.redis_manager.client
            stats = {
                "overall": {
                    "hit_count": self._hit_count,
                    "miss_count": self._miss_count,
                    "hit_rate": (
                        self._hit_count / (self._hit_count + self._miss_count)
                        if (self._hit_count + self._miss_count) > 0 else 0
                    )
                }
            }
            
            if tool_name:
                # Get stats for specific tool
                stats_key = f"{self.TOOL_STATS_PREFIX}:{tool_name}"
                tool_stats = await redis_client.hgetall(stats_key)
                
                if tool_stats:
                    stats[tool_name] = {
                        k.decode() if isinstance(k, bytes) else k: 
                        v.decode() if isinstance(v, bytes) else v
                        for k, v in tool_stats.items()
                    }
            else:
                # Get stats for all tools
                pattern = f"{self.TOOL_STATS_PREFIX}:*"
                async for key in redis_client.scan_iter(match=pattern):
                    key_str = key.decode() if isinstance(key, bytes) else key
                    tool_name_from_key = key_str.split(":", 2)[-1]
                    
                    tool_stats = await redis_client.hgetall(key)
                    if tool_stats:
                        stats[tool_name_from_key] = {
                            k.decode() if isinstance(k, bytes) else k: 
                            v.decode() if isinstance(v, bytes) else v
                            for k, v in tool_stats.items()
                        }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get tool statistics: {e}")
            return {"error": str(e)}
    
    async def cleanup_expired_entries(self) -> Dict[str, int]:
        """Clean up expired cache entries and orphaned dependencies.
        
        Returns:
            Cleanup statistics
        """
        try:
            redis_client = self.redis_manager.client
            cleaned_cache = 0
            cleaned_deps = 0
            
            # Clean up orphaned dependency mappings
            dep_pattern = f"{self.TOOL_DEPS_PREFIX}:*"
            async for dep_key in redis_client.scan_iter(match=dep_pattern):
                # Get all cache keys for this dependency
                cache_keys = await redis_client.smembers(dep_key)
                valid_keys = []
                
                for cache_key in cache_keys:
                    exists = await redis_client.exists(cache_key)
                    if exists:
                        valid_keys.append(cache_key)
                
                # Update dependency mapping with only valid keys
                if len(valid_keys) != len(cache_keys):
                    if valid_keys:
                        await redis_client.delete(dep_key)
                        await redis_client.sadd(dep_key, *valid_keys)
                    else:
                        await redis_client.delete(dep_key)
                        cleaned_deps += 1
            
            return {
                "cleaned_cache_entries": cleaned_cache,
                "cleaned_dependency_mappings": cleaned_deps,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired entries: {e}")
            return {"error": str(e)}


# Global tool cache service instance
_tool_cache_service: Optional[ToolCacheService] = None


async def get_tool_cache_service() -> ToolCacheService:
    """Get or create tool cache service instance."""
    global _tool_cache_service
    if not _tool_cache_service:
        redis_manager = await get_redis_manager()
        _tool_cache_service = ToolCacheService(redis_manager)
    return _tool_cache_service


async def cleanup_tool_cache():
    """Cleanup tool cache service on shutdown."""
    global _tool_cache_service
    
    if _tool_cache_service:
        # Cancel any running warmup tasks
        for task in _tool_cache_service._warmup_tasks.values():
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if _tool_cache_service._warmup_tasks:
            await asyncio.gather(
                *_tool_cache_service._warmup_tasks.values(),
                return_exceptions=True
            )
        
        _tool_cache_service = None
        logger.info("Tool cache service cleanup completed")