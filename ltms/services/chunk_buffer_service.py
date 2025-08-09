"""Shared Chunk Buffer Service for LTMC Redis orchestration layer."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from ltms.services.redis_service import get_redis_manager, RedisConnectionManager
import faiss
from ltms.vector_store.faiss_store import create_faiss_index
from ltms.services.chunk_buffer_core import ChunkBufferCore
from ltms.services.chunk_buffer_stats import ChunkBufferStats

logger = logging.getLogger(__name__)


class ChunkBufferService:
    """Store and coordinate recent chunk access across agents."""
    
    def __init__(self, redis_manager: RedisConnectionManager, faiss_store: Optional[faiss.IndexFlatL2] = None):
        """Initialize Shared Chunk Buffer Service.
        
        Args:
            redis_manager: Redis connection manager instance
            faiss_store: FAISS index for fallback operations
        """
        self.redis_manager = redis_manager
        self.faiss_store = faiss_store
        
        # Initialize core components
        self.core = ChunkBufferCore(redis_manager)
        self.stats = ChunkBufferStats(redis_manager)
        
        # Configuration constants
        self.CHUNK_BUFFER_SIZE = 1000  # Maximum chunks in buffer
        self.MAX_MEMORY_MB = 50  # Maximum memory usage for chunk buffer

    async def get_chunk(
        self,
        chunk_id: str,
        agent_id: Optional[str] = None,
        fallback_to_faiss: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get chunk from buffer with popularity tracking.
        
        Args:
            chunk_id: Unique chunk identifier
            agent_id: Agent requesting the chunk
            fallback_to_faiss: Whether to fallback to FAISS if not in buffer
            
        Returns:
            Chunk data with metadata or None if not found
        """
        try:
            # Try buffer first
            chunk = await self.core.get_chunk_from_buffer(chunk_id)
            
            if chunk:
                # Update access tracking
                await self.core.update_access_tracking(chunk_id, agent_id)
                await self.stats.record_hit()
                logger.debug(f"Chunk buffer hit for chunk_id: {chunk_id}")
                return chunk
            
            # Buffer miss - try FAISS fallback if enabled
            if fallback_to_faiss and self.faiss_store:
                chunk = await self._load_from_faiss(chunk_id)
                if chunk:
                    # Cache in buffer for future access
                    await self.cache_chunk(chunk_id, chunk, agent_id)
                    await self.stats.record_miss()
                    logger.debug(f"Chunk loaded from FAISS fallback: {chunk_id}")
                    return chunk
            
            await self.stats.record_miss()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get chunk {chunk_id}: {e}")
            return None

    async def cache_chunk(
        self,
        chunk_id: str,
        chunk_data: Dict[str, Any],
        agent_id: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache chunk in buffer with deduplication and popularity tracking.
        
        Args:
            chunk_id: Unique chunk identifier
            chunk_data: Chunk content and metadata
            agent_id: Agent caching the chunk
            ttl: Time to live in seconds (default: 3600)
            
        Returns:
            True if cached successfully
        """
        try:
            # Check for deduplication
            if await self.core.chunk_exists(chunk_id):
                await self.core.update_access_tracking(chunk_id, agent_id)
                await self.stats.record_deduplication()
                return True
            
            # Check memory limits before caching
            chunk_entry = self.core.prepare_chunk_entry(chunk_data, chunk_id, agent_id)
            entry_size = len(json.dumps(chunk_entry).encode())
            
            if not await self._check_memory_limits(entry_size):
                await self._evict_chunks()
            
            # Cache the chunk
            success = await self.core.cache_chunk_entry(chunk_id, chunk_entry, agent_id, ttl)
            
            if success:
                await self.core.update_access_tracking(chunk_id, agent_id)
                logger.debug(f"Cached chunk {chunk_id} for agent {agent_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to cache chunk {chunk_id}: {e}")
            return False

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
        return await self.core.get_popular_chunks(time_window, limit)

    async def get_agent_chunks(self, agent_id: str) -> List[str]:
        """Get chunks accessed by a specific agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of chunk IDs accessed by the agent
        """
        return await self.core.get_agent_chunks(agent_id)

    async def evict_chunk(self, chunk_id: str) -> bool:
        """Manually evict a specific chunk from buffer.
        
        Args:
            chunk_id: Chunk identifier to evict
            
        Returns:
            True if evicted successfully
        """
        success = await self.core.evict_chunk(chunk_id)
        if success:
            await self.stats.record_eviction()
        return success

    async def get_buffer_stats(self) -> Dict[str, Any]:
        """Get comprehensive buffer statistics.
        
        Returns:
            Dictionary with buffer performance and usage statistics
        """
        core_stats = await self.core.get_basic_stats()
        performance_stats = await self.stats.get_performance_stats()
        memory_usage = await self.core.estimate_memory_usage()
        
        return {
            **core_stats,
            **performance_stats,
            "memory_usage_mb": memory_usage,
            "memory_limit_mb": self.MAX_MEMORY_MB,
            "buffer_limit": self.CHUNK_BUFFER_SIZE,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def _check_memory_limits(self, new_entry_size: int) -> bool:
        """Check if adding new entry would exceed memory limits."""
        try:
            current_memory = await self.core.estimate_memory_usage()
            new_memory = current_memory + (new_entry_size / (1024 * 1024))  # Convert to MB
            return new_memory <= self.MAX_MEMORY_MB
        except Exception as e:
            logger.error(f"Failed to check memory limits: {e}")
            return True  # Allow caching if check fails

    async def _evict_chunks(self) -> int:
        """Evict least popular chunks using LRU with popularity weighting."""
        evicted_count = await self.core.evict_lru_chunks()
        await self.stats.record_evictions(evicted_count)
        logger.info(f"Evicted {evicted_count} chunks to free memory")
        return evicted_count

    async def _load_from_faiss(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Load chunk from FAISS store as fallback."""
        try:
            if not self.faiss_store:
                return None
            
            # Mock implementation - in reality would query FAISS
            # and retrieve associated chunk data from database
            return {
                "content": f"Fallback content for chunk {chunk_id}",
                "metadata": {"source": "faiss_fallback", "chunk_id": chunk_id}
            }
            
        except Exception as e:
            logger.error(f"Failed to load chunk from FAISS: {e}")
            return None


# Global chunk buffer service instance
_chunk_buffer_service: Optional[ChunkBufferService] = None


async def get_chunk_buffer_service(faiss_store: Optional[faiss.IndexFlatL2] = None) -> ChunkBufferService:
    """Get or create chunk buffer service instance."""
    global _chunk_buffer_service
    if not _chunk_buffer_service:
        redis_manager = await get_redis_manager()
        _chunk_buffer_service = ChunkBufferService(redis_manager, faiss_store)
    return _chunk_buffer_service


async def cleanup_chunk_buffer():
    """Cleanup chunk buffer service on shutdown."""
    global _chunk_buffer_service
    
    if _chunk_buffer_service:
        try:
            logger.info("Chunk buffer service cleanup completed")
        except Exception as e:
            logger.error(f"Error during chunk buffer cleanup: {e}")
        finally:
            _chunk_buffer_service = None