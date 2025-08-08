"""Chunk buffer operations and utility functions."""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from ltms.services.redis_service import RedisConnectionManager

logger = logging.getLogger(__name__)


class ChunkBufferOperations:
    """Utility operations for chunk buffer management."""
    
    def __init__(self, redis_manager: RedisConnectionManager):
        """Initialize chunk buffer operations.
        
        Args:
            redis_manager: Redis connection manager instance
        """
        self.redis_manager = redis_manager
        
        # Redis key prefixes
        self.CHUNK_BUFFER_PREFIX = "chunks:buffer"
        self.CHUNK_RECENT_KEY = "chunks:recent"
        self.CHUNK_POPULARITY_PREFIX = "chunks:popularity"
        self.CHUNK_ACCESS_PREFIX = "chunks:access"
        self.CHUNK_AGENT_PREFIX = "chunks:agent"
        
        # Configuration
        self.EVICTION_BATCH_SIZE = 100
        self.TIME_WINDOWS = {
            "1h": 3600,
            "4h": 14400,
            "24h": 86400
        }

    async def sample_buffer_sizes(self) -> Tuple[int, int]:
        """Sample buffer entry sizes for memory estimation.
        
        Returns:
            Tuple of (total_sample_size, sample_count)
        """
        try:
            redis_client = self.redis_manager.client
            buffer_pattern = f"{self.CHUNK_BUFFER_PREFIX}:*"
            sample_count = 0
            sample_size = 0
            
            async for key in redis_client.scan_iter(match=buffer_pattern):
                data = await redis_client.get(key)
                if data:
                    sample_size += len(data.encode() if isinstance(data, str) else data)
                    sample_count += 1
                
                if sample_count >= 50:  # Sample only first 50 keys
                    break
            
            return sample_size, sample_count
            
        except Exception as e:
            logger.error(f"Failed to sample buffer sizes: {e}")
            return 0, 0

    async def get_buffer_count(self) -> int:
        """Get current number of chunks in buffer.
        
        Returns:
            Number of chunks currently in buffer
        """
        try:
            redis_client = self.redis_manager.client
            buffer_pattern = f"{self.CHUNK_BUFFER_PREFIX}:*"
            count = 0
            async for _ in redis_client.scan_iter(match=buffer_pattern):
                count += 1
            return count
        except Exception as e:
            logger.error(f"Failed to get buffer count: {e}")
            return 0

    async def get_eviction_candidates(self) -> List[str]:
        """Get candidates for eviction from recent list.
        
        Returns:
            List of chunk IDs that are candidates for eviction
        """
        try:
            redis_client = self.redis_manager.client
            candidates = await redis_client.lrange(
                self.CHUNK_RECENT_KEY, 
                -self.EVICTION_BATCH_SIZE, 
                -1
            )
            return [c.decode() if isinstance(c, bytes) else c for c in candidates]
        except Exception as e:
            logger.error(f"Failed to get eviction candidates: {e}")
            return []

    async def score_candidates(self, candidates: List[str]) -> List[Tuple[str, float]]:
        """Score eviction candidates by popularity.
        
        Args:
            candidates: List of chunk IDs to score
            
        Returns:
            List of (chunk_id, score) tuples sorted by popularity (lowest first)
        """
        try:
            redis_client = self.redis_manager.client
            popularity_key = f"{self.CHUNK_POPULARITY_PREFIX}:1h"
            chunk_scores = []
            
            for chunk_id in candidates:
                score = await redis_client.zscore(popularity_key, chunk_id) or 0
                chunk_scores.append((chunk_id, score))
            
            # Sort by popularity (ascending - least popular first)
            chunk_scores.sort(key=lambda x: x[1])
            return chunk_scores
        except Exception as e:
            logger.error(f"Failed to score candidates: {e}")
            return []

    async def bulk_evict_chunks(self, chunk_ids: List[str]) -> int:
        """Bulk evict multiple chunks efficiently.
        
        Args:
            chunk_ids: List of chunk IDs to evict
            
        Returns:
            Number of chunks successfully evicted
        """
        try:
            redis_client = self.redis_manager.client
            evicted_count = 0
            
            # Process in batches for efficiency
            batch_size = 20
            for i in range(0, len(chunk_ids), batch_size):
                batch = chunk_ids[i:i + batch_size]
                
                async with redis_client.pipeline(transaction=True) as pipe:
                    for chunk_id in batch:
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
                    
                    # Count successful deletions (every 4th result is a chunk deletion)
                    for j in range(0, len(results), 4):
                        if j < len(results) and results[j] > 0:
                            evicted_count += 1
            
            return evicted_count
            
        except Exception as e:
            logger.error(f"Failed to bulk evict chunks: {e}")
            return 0

    async def update_chunk_metadata(
        self,
        chunk_id: str,
        metadata_updates: Dict[str, Any]
    ) -> bool:
        """Update metadata for an existing chunk.
        
        Args:
            chunk_id: Chunk identifier
            metadata_updates: Dictionary of metadata fields to update
            
        Returns:
            True if updated successfully
        """
        try:
            redis_client = self.redis_manager.client
            chunk_key = f"{self.CHUNK_BUFFER_PREFIX}:{chunk_id}"
            
            # Get current chunk data
            chunk_data = await redis_client.get(chunk_key)
            if not chunk_data:
                return False
            
            chunk = json.loads(chunk_data)
            
            # Update metadata
            for key, value in metadata_updates.items():
                if key == "metadata":
                    chunk["metadata"].update(value if isinstance(value, dict) else {})
                else:
                    chunk[key] = value
            
            # Update last modified timestamp
            chunk["last_modified"] = datetime.now(timezone.utc).isoformat()
            
            # Get current TTL and maintain it
            ttl = await redis_client.ttl(chunk_key)
            if ttl > 0:
                await redis_client.setex(chunk_key, ttl, json.dumps(chunk))
            else:
                await redis_client.set(chunk_key, json.dumps(chunk))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update chunk metadata for {chunk_id}: {e}")
            return False

    async def get_chunk_access_history(self, chunk_id: str) -> List[float]:
        """Get access history timestamps for a chunk.
        
        Args:
            chunk_id: Chunk identifier
            
        Returns:
            List of access timestamps
        """
        try:
            redis_client = self.redis_manager.client
            access_key = f"{self.CHUNK_ACCESS_PREFIX}:{chunk_id}"
            
            timestamps = await redis_client.lrange(access_key, 0, -1)
            return [
                float(ts.decode() if isinstance(ts, bytes) else ts)
                for ts in timestamps
            ]
            
        except Exception as e:
            logger.error(f"Failed to get access history for {chunk_id}: {e}")
            return []

    async def cleanup_expired_popularity_scores(self) -> int:
        """Clean up expired popularity tracking entries.
        
        Returns:
            Number of entries cleaned up
        """
        try:
            redis_client = self.redis_manager.client
            cleaned_count = 0
            
            # Clean up each time window
            for window_name, window_seconds in self.TIME_WINDOWS.items():
                popularity_key = f"{self.CHUNK_POPULARITY_PREFIX}:{window_name}"
                
                # Remove entries with score 0 (expired)
                removed = await redis_client.zremrangebyscore(popularity_key, 0, 0)
                cleaned_count += removed
                
                # Refresh TTL for the key
                await redis_client.expire(popularity_key, window_seconds)
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired popularity scores: {e}")
            return 0

    async def get_agent_activity_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of agent activity across all agents.
        
        Returns:
            Dictionary with agent activity summaries
        """
        try:
            redis_client = self.redis_manager.client
            agent_pattern = f"{self.CHUNK_AGENT_PREFIX}:*"
            agent_summary = {}
            
            async for key in redis_client.scan_iter(match=agent_pattern):
                key_str = key.decode() if isinstance(key, bytes) else key
                agent_id = key_str.split(":", 2)[-1]
                
                chunk_count = await redis_client.scard(key)
                ttl = await redis_client.ttl(key)
                
                agent_summary[agent_id] = {
                    "chunk_count": chunk_count,
                    "session_ttl": ttl,
                    "active": ttl > 0
                }
            
            return agent_summary
            
        except Exception as e:
            logger.error(f"Failed to get agent activity summary: {e}")
            return {}

    def prepare_chunk_entry(
        self,
        chunk_data: Dict[str, Any],
        chunk_id: str,
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Prepare chunk entry with standardized metadata.
        
        Args:
            chunk_data: Raw chunk data
            chunk_id: Unique chunk identifier
            agent_id: Agent caching the chunk
            
        Returns:
            Formatted chunk entry with metadata
        """
        now = datetime.now(timezone.utc).isoformat()
        
        return {
            "content": chunk_data.get("content", ""),
            "metadata": chunk_data.get("metadata", {}),
            "chunk_id": chunk_id,
            "cached_at": now,
            "last_modified": now,
            "access_count": 1,
            "last_accessed": now,
            "cached_by": agent_id or "unknown",
            "size_bytes": len(str(chunk_data.get("content", "")).encode())
        }