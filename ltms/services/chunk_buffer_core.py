"""Core chunk buffer operations for LTMC Redis orchestration layer."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from ltms.services.redis_service import RedisConnectionManager
from ltms.services.chunk_buffer_operations import ChunkBufferOperations

logger = logging.getLogger(__name__)


class ChunkBufferCore:
    """Core chunk buffer operations and data management."""
    
    def __init__(self, redis_manager: RedisConnectionManager):
        """Initialize chunk buffer core operations.
        
        Args:
            redis_manager: Redis connection manager instance
        """
        self.redis_manager = redis_manager
        self.operations = ChunkBufferOperations(redis_manager)
        
        # Redis key prefixes for data structures
        self.CHUNK_BUFFER_PREFIX = "chunks:buffer"
        self.CHUNK_RECENT_KEY = "chunks:recent"
        self.CHUNK_POPULARITY_PREFIX = "chunks:popularity"
        self.CHUNK_ACCESS_PREFIX = "chunks:access"
        self.CHUNK_AGENT_PREFIX = "chunks:agent"
        
        # Configuration
        self.EVICTION_BATCH_SIZE = 100
        
        # Popularity time windows for tracking
        self.TIME_WINDOWS = {
            "1h": 3600,
            "4h": 14400,
            "24h": 86400
        }

    async def get_chunk_from_buffer(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Get chunk data from Redis buffer.
        
        Args:
            chunk_id: Unique chunk identifier
            
        Returns:
            Chunk data or None if not found
        """
        try:
            redis_client = self.redis_manager.client
            chunk_key = f"{self.CHUNK_BUFFER_PREFIX}:{chunk_id}"
            
            chunk_data = await redis_client.get(chunk_key)
            if chunk_data:
                return json.loads(chunk_data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get chunk from buffer {chunk_id}: {e}")
            return None

    async def chunk_exists(self, chunk_id: str) -> bool:
        """Check if chunk exists in buffer.
        
        Args:
            chunk_id: Unique chunk identifier
            
        Returns:
            True if chunk exists in buffer
        """
        try:
            redis_client = self.redis_manager.client
            chunk_key = f"{self.CHUNK_BUFFER_PREFIX}:{chunk_id}"
            return await redis_client.exists(chunk_key) > 0
        except Exception as e:
            logger.error(f"Failed to check chunk existence {chunk_id}: {e}")
            return False

    def prepare_chunk_entry(
        self,
        chunk_data: Dict[str, Any],
        chunk_id: str,
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Prepare chunk entry with metadata."""
        return self.operations.prepare_chunk_entry(chunk_data, chunk_id, agent_id)

    async def cache_chunk_entry(
        self,
        chunk_id: str,
        chunk_entry: Dict[str, Any],
        agent_id: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """Store chunk entry in Redis buffer.
        
        Args:
            chunk_id: Unique chunk identifier
            chunk_entry: Prepared chunk entry
            agent_id: Agent caching the chunk
            ttl: Time to live in seconds (default: 3600)
            
        Returns:
            True if cached successfully
        """
        try:
            redis_client = self.redis_manager.client
            chunk_key = f"{self.CHUNK_BUFFER_PREFIX}:{chunk_id}"
            
            # Use pipeline for atomic operations
            ttl = ttl or 3600  # Default 1 hour TTL
            async with redis_client.pipeline(transaction=True) as pipe:
                # Store chunk in buffer
                pipe.setex(chunk_key, ttl, json.dumps(chunk_entry))
                
                # Add to recent chunks list (FIFO)
                pipe.lpush(self.CHUNK_RECENT_KEY, chunk_id)
                pipe.ltrim(self.CHUNK_RECENT_KEY, 0, 999)  # Keep last 1000
                
                # Track agent access
                if agent_id:
                    agent_key = f"{self.CHUNK_AGENT_PREFIX}:{agent_id}"
                    pipe.sadd(agent_key, chunk_id)
                    pipe.expire(agent_key, ttl)
                
                await pipe.execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache chunk entry {chunk_id}: {e}")
            return False

    async def update_access_tracking(self, chunk_id: str, agent_id: Optional[str]) -> None:
        """Update chunk access tracking and popularity scores."""
        try:
            await self._update_chunk_access_count(chunk_id)
            await self._update_popularity_scores(chunk_id)
            await self._record_access_timestamp(chunk_id)
        except Exception as e:
            logger.error(f"Failed to update access tracking for {chunk_id}: {e}")

    async def _update_chunk_access_count(self, chunk_id: str) -> None:
        """Update access count in chunk entry."""
        redis_client = self.redis_manager.client
        chunk_key = f"{self.CHUNK_BUFFER_PREFIX}:{chunk_id}"
        
        chunk_data = await redis_client.get(chunk_key)
        if chunk_data:
            chunk = json.loads(chunk_data)
            chunk["access_count"] = chunk.get("access_count", 0) + 1
            chunk["last_accessed"] = datetime.now(timezone.utc).isoformat()
            
            # Maintain current TTL
            ttl = await redis_client.ttl(chunk_key)
            if ttl > 0:
                await redis_client.setex(chunk_key, ttl, json.dumps(chunk))
            else:
                await redis_client.set(chunk_key, json.dumps(chunk))

    async def _update_popularity_scores(self, chunk_id: str) -> None:
        """Update popularity scores for all time windows."""
        redis_client = self.redis_manager.client
        
        async with redis_client.pipeline(transaction=True) as pipe:
            for window_name, window_seconds in self.TIME_WINDOWS.items():
                popularity_key = f"{self.CHUNK_POPULARITY_PREFIX}:{window_name}"
                pipe.zincrby(popularity_key, 1, chunk_id)
                pipe.expire(popularity_key, window_seconds)
            await pipe.execute()

    async def _record_access_timestamp(self, chunk_id: str) -> None:
        """Record access timestamp for chunk."""
        redis_client = self.redis_manager.client
        now = datetime.now(timezone.utc)
        
        async with redis_client.pipeline(transaction=True) as pipe:
            access_key = f"{self.CHUNK_ACCESS_PREFIX}:{chunk_id}"
            pipe.lpush(access_key, now.timestamp())
            pipe.ltrim(access_key, 0, 99)  # Keep last 100 access times
            pipe.expire(access_key, 86400)  # 24 hours
            await pipe.execute()

    async def get_popular_chunks(
        self,
        time_window: str = "1h",
        limit: int = 20
    ) -> List[Tuple[str, int]]:
        """Get most popular chunks in time window.
        
        Args:
            time_window: Time window ("1h", "4h", "24h")
            limit: Maximum number of chunks to return
            
        Returns:
            List of (chunk_id, access_count) tuples
        """
        try:
            if time_window not in self.TIME_WINDOWS:
                raise ValueError(f"Invalid time window: {time_window}")
            
            redis_client = self.redis_manager.client
            popularity_key = f"{self.CHUNK_POPULARITY_PREFIX}:{time_window}"
            
            # Get top chunks by score (access count)
            popular_chunks = await redis_client.zrevrange(
                popularity_key, 0, limit - 1, withscores=True
            )
            
            return [
                (chunk_id.decode() if isinstance(chunk_id, bytes) else chunk_id, int(score))
                for chunk_id, score in popular_chunks
            ]
            
        except Exception as e:
            logger.error(f"Failed to get popular chunks: {e}")
            return []

    async def get_agent_chunks(self, agent_id: str) -> List[str]:
        """Get chunks accessed by a specific agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of chunk IDs accessed by the agent
        """
        try:
            redis_client = self.redis_manager.client
            agent_key = f"{self.CHUNK_AGENT_PREFIX}:{agent_id}"
            
            chunk_ids = await redis_client.smembers(agent_key)
            return [
                chunk_id.decode() if isinstance(chunk_id, bytes) else chunk_id
                for chunk_id in chunk_ids
            ]
            
        except Exception as e:
            logger.error(f"Failed to get chunks for agent {agent_id}: {e}")
            return []

    async def evict_chunk(self, chunk_id: str) -> bool:
        """Evict a specific chunk from buffer.
        
        Args:
            chunk_id: Chunk identifier to evict
            
        Returns:
            True if evicted successfully
        """
        try:
            redis_client = self.redis_manager.client
            
            async with redis_client.pipeline(transaction=True) as pipe:
                # Remove chunk from buffer
                chunk_key = f"{self.CHUNK_BUFFER_PREFIX}:{chunk_id}"
                pipe.delete(chunk_key)
                
                # Remove from recent list
                pipe.lrem(self.CHUNK_RECENT_KEY, 1, chunk_id)
                
                # Remove from popularity tracking
                for window in self.TIME_WINDOWS:
                    popularity_key = f"{self.CHUNK_POPULARITY_PREFIX}:{window}"
                    pipe.zrem(popularity_key, chunk_id)
                
                results = await pipe.execute()
            
            return results[0] > 0  # First operation (delete) returns count
            
        except Exception as e:
            logger.error(f"Failed to evict chunk {chunk_id}: {e}")
            return False

    async def evict_lru_chunks(self) -> int:
        """Evict least popular chunks using LRU with popularity weighting.
        
        Returns:
            Number of chunks evicted
        """
        try:
            candidates = await self.operations.get_eviction_candidates()
            if not candidates:
                return 0
            
            chunk_scores = await self.operations.score_candidates(candidates)
            evict_limit = min(self.EVICTION_BATCH_SIZE, len(chunk_scores) // 2)
            
            if evict_limit > 0:
                to_evict = [chunk_id for chunk_id, _ in chunk_scores[:evict_limit]]
                return await self.operations.bulk_evict_chunks(to_evict)
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to evict LRU chunks: {e}")
            return 0

    async def get_basic_stats(self) -> Dict[str, Any]:
        """Get basic buffer statistics.
        
        Returns:
            Dictionary with basic buffer statistics
        """
        try:
            redis_client = self.redis_manager.client
            
            # Count buffer entries
            buffer_pattern = f"{self.CHUNK_BUFFER_PREFIX}:*"
            buffer_keys = [key async for key in redis_client.scan_iter(match=buffer_pattern)]
            buffer_count = len(buffer_keys)
            
            # Get recent chunks count
            recent_count = await redis_client.llen(self.CHUNK_RECENT_KEY)
            
            # Get popularity stats for different windows
            popularity_stats = {}
            for window in self.TIME_WINDOWS:
                popularity_key = f"{self.CHUNK_POPULARITY_PREFIX}:{window}"
                count = await redis_client.zcard(popularity_key)
                popularity_stats[window] = count
            
            return {
                "buffer_size": buffer_count,
                "recent_chunks": recent_count,
                "popularity_tracking": popularity_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get basic stats: {e}")
            return {"error": str(e)}

    async def estimate_memory_usage(self) -> float:
        """Estimate current memory usage of chunk buffer in MB.
        
        Returns:
            Estimated memory usage in MB
        """
        try:
            sample_size, sample_count = await self.operations.sample_buffer_sizes()
            
            if sample_count > 0:
                buffer_count = await self.operations.get_buffer_count()
                avg_size = sample_size / sample_count
                total_size = avg_size * buffer_count
                return total_size / (1024 * 1024)  # Convert to MB
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Failed to estimate memory usage: {e}")
            return 0.0

