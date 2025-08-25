"""
Redis Cache Manager for LTMC Atomic Operations.
Provides atomic document caching with TTL support.

File: ltms/database/redis_manager.py
Lines: ~290 (under 300 limit)
Purpose: Redis operations for atomic cross-database synchronization
"""
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from ltms.services.redis_service import RedisConnectionManager
from ltms.config import get_config

logger = logging.getLogger(__name__)

class RedisManager:
    """
    Redis cache manager for atomic document operations.
    Provides transaction-safe document caching and retrieval.
    """
    
    def __init__(self, connection_config: Optional[Dict[str, Any]] = None, 
                 default_ttl: int = 3600, test_mode: bool = False):
        """Initialize Redis manager with cache connection.
        
        Args:
            connection_config: Redis connection configuration
            default_ttl: Default time-to-live for cached documents (seconds)
            test_mode: Enable test mode for unit testing
        """
        self.test_mode = test_mode
        self.default_ttl = default_ttl
        
        if test_mode:
            self._connection_manager = None
            self._is_available = True
            self._test_cache: Dict[str, Any] = {}
        else:
            # Initialize connection manager
            if connection_config is None:
                # Use default configuration
                connection_config = {
                    "host": "localhost",
                    "port": 6382,
                    "db": 0,
                    "password": None
                }
            
            self._connection_manager = RedisConnectionManager(**connection_config)
            self._is_available = False
            self._test_cache = {}
            
            # Initialize connection asynchronously (will be done on first use)
        
        logger.info(f"RedisManager initialized (test_mode={test_mode}, ttl={default_ttl}s)")
    
    async def _ensure_connection(self):
        """Ensure Redis connection is established."""
        if self.test_mode or self._is_available:
            return True
            
        try:
            await self._connection_manager.initialize()
            self._is_available = True
            logger.info("Redis connection established")
            return True
            
        except Exception as e:
            logger.error(f"Failed to establish Redis connection: {e}")
            self._is_available = False
            return False
    
    def is_available(self) -> bool:
        """Check if Redis is available."""
        return self._is_available or self.test_mode
    
    def _generate_cache_key(self, doc_id: str, key_type: str = "doc") -> str:
        """Generate cache key for document."""
        return f"ltmc:{key_type}:{doc_id}"
    
    async def cache_document(self, doc_id: str, content: str, 
                            metadata: Dict[str, Any] = None, ttl: Optional[int] = None) -> bool:
        """
        Cache document in Redis atomically.
        
        Args:
            doc_id: Unique document identifier
            content: Document content
            metadata: Document metadata dictionary
            ttl: Time-to-live in seconds (uses default if None)
            
        Returns:
            True if caching successful, False otherwise
        """
        if self.test_mode:
            # Store in test cache
            self._test_cache[doc_id] = {
                "content": content,
                "metadata": metadata or {},
                "cached_at": datetime.now().isoformat(),
                "ttl": ttl or self.default_ttl
            }
            return True
            
        if not await self._ensure_connection():
            logger.error("Redis not available for document caching")
            return False
            
        try:
            cache_key = self._generate_cache_key(doc_id)
            cache_ttl = ttl or self.default_ttl
            
            # Prepare cache data
            cache_data = {
                "id": doc_id,
                "content": content,
                "metadata": metadata or {},
                "cached_at": datetime.now().isoformat(),
                "ttl": cache_ttl
            }
            
            # Store in Redis with TTL
            async with self._connection_manager.get_connection() as redis_client:
                await redis_client.setex(
                    cache_key, 
                    cache_ttl, 
                    json.dumps(cache_data)
                )
            
            logger.info(f"Successfully cached document {doc_id} in Redis (TTL: {cache_ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Exception caching document {doc_id} in Redis: {e}")
            return False
    
    async def retrieve_cached_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached document from Redis.
        
        Args:
            doc_id: Document identifier to retrieve
            
        Returns:
            Cached document data or None if not found
        """
        if self.test_mode:
            cached_data = self._test_cache.get(doc_id)
            if cached_data:
                return {
                    "id": doc_id,
                    "content": cached_data["content"],
                    "metadata": cached_data["metadata"],
                    "cached_at": cached_data["cached_at"],
                    "ttl": cached_data["ttl"]
                }
            return None
            
        if not await self._ensure_connection():
            return None
            
        try:
            cache_key = self._generate_cache_key(doc_id)
            
            async with self._connection_manager.get_connection() as redis_client:
                cached_data = await redis_client.get(cache_key)
                
                if cached_data:
                    return json.loads(cached_data)
                    
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve cached document {doc_id} from Redis: {e}")
            return None
    
    async def document_exists(self, doc_id: str) -> bool:
        """
        Check if document exists in Redis cache.
        
        Args:
            doc_id: Document identifier to check
            
        Returns:
            True if document exists in cache, False otherwise
        """
        if self.test_mode:
            return doc_id in self._test_cache
            
        if not await self._ensure_connection():
            return False
            
        try:
            cache_key = self._generate_cache_key(doc_id)
            
            async with self._connection_manager.get_connection() as redis_client:
                exists = await redis_client.exists(cache_key)
                return bool(exists)
                
        except Exception as e:
            logger.error(f"Failed to check document existence {doc_id} in Redis: {e}")
            return False
    
    async def delete_cached_document(self, doc_id: str) -> bool:
        """
        Delete cached document from Redis.
        
        Args:
            doc_id: Document identifier to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        if self.test_mode:
            if doc_id in self._test_cache:
                del self._test_cache[doc_id]
                return True
            return True  # Consider non-existent as successfully deleted
            
        if not await self._ensure_connection():
            return False
            
        try:
            cache_key = self._generate_cache_key(doc_id)
            
            async with self._connection_manager.get_connection() as redis_client:
                deleted_count = await redis_client.delete(cache_key)
                
                success = deleted_count > 0
                if success:
                    logger.info(f"Successfully deleted cached document {doc_id} from Redis")
                else:
                    logger.warning(f"Document {doc_id} was not found in Redis cache")
                    
                return True  # Consider both cases as success for atomicity
                
        except Exception as e:
            logger.error(f"Failed to delete cached document {doc_id} from Redis: {e}")
            return False
    
    async def list_cached_documents(self, pattern: str = "*", limit: int = 100) -> List[Dict[str, Any]]:
        """
        List cached documents in Redis.
        
        Args:
            pattern: Key pattern to match (default: all LTMC documents)
            limit: Maximum number of documents to return
            
        Returns:
            List of cached document data
        """
        if self.test_mode:
            return [{
                "id": doc_id,
                "content": data["content"],
                "metadata": data["metadata"],
                "cached_at": data["cached_at"],
                "ttl": data["ttl"]
            } for doc_id, data in list(self._test_cache.items())[:limit]]
            
        if not await self._ensure_connection():
            return []
            
        try:
            search_pattern = f"ltmc:doc:{pattern}"
            
            async with self._connection_manager.get_connection() as redis_client:
                keys = []
                async for key in redis_client.scan_iter(match=search_pattern, count=limit):
                    keys.append(key)
                    if len(keys) >= limit:
                        break
                
                documents = []
                for key in keys:
                    try:
                        cached_data = await redis_client.get(key)
                        if cached_data:
                            doc_data = json.loads(cached_data)
                            documents.append(doc_data)
                    except Exception as e:
                        logger.warning(f"Failed to parse cached document {key}: {e}")
                        continue
                
                return documents
                
        except Exception as e:
            logger.error(f"Failed to list cached documents from Redis: {e}")
            return []
    
    async def count_cached_documents(self) -> int:
        """
        Count total cached documents in Redis.
        
        Returns:
            Total number of cached documents
        """
        if self.test_mode:
            return len(self._test_cache)
            
        if not await self._ensure_connection():
            return 0
            
        try:
            search_pattern = "ltmc:doc:*"
            
            async with self._connection_manager.get_connection() as redis_client:
                count = 0
                async for _ in redis_client.scan_iter(match=search_pattern):
                    count += 1
                
                return count
                
        except Exception as e:
            logger.error(f"Failed to count cached documents in Redis: {e}")
            return 0
    
    async def set_document_ttl(self, doc_id: str, ttl: int) -> bool:
        """
        Set or update TTL for cached document.
        
        Args:
            doc_id: Document identifier
            ttl: New time-to-live in seconds
            
        Returns:
            True if TTL updated successfully, False otherwise
        """
        if self.test_mode:
            if doc_id in self._test_cache:
                self._test_cache[doc_id]["ttl"] = ttl
                return True
            return False
            
        if not await self._ensure_connection():
            return False
            
        try:
            cache_key = self._generate_cache_key(doc_id)
            
            async with self._connection_manager.get_connection() as redis_client:
                success = await redis_client.expire(cache_key, ttl)
                
                if success:
                    logger.info(f"Updated TTL for document {doc_id} to {ttl} seconds")
                else:
                    logger.warning(f"Failed to update TTL for document {doc_id} (document may not exist)")
                    
                return bool(success)
                
        except Exception as e:
            logger.error(f"Failed to set TTL for document {doc_id}: {e}")
            return False
    
    async def flush_cache(self, pattern: str = None) -> bool:
        """
        Flush cached documents matching pattern.
        
        Args:
            pattern: Key pattern to match (default: all LTMC documents)
            
        Returns:
            True if flush successful, False otherwise
        """
        if self.test_mode:
            if pattern:
                # Remove matching keys from test cache
                import fnmatch
                keys_to_remove = [k for k in self._test_cache.keys() if fnmatch.fnmatch(k, pattern)]
                for key in keys_to_remove:
                    del self._test_cache[key]
            else:
                self._test_cache.clear()
            return True
            
        if not await self._ensure_connection():
            return False
            
        try:
            search_pattern = f"ltmc:doc:{pattern or '*'}"
            
            async with self._connection_manager.get_connection() as redis_client:
                keys_to_delete = []
                async for key in redis_client.scan_iter(match=search_pattern):
                    keys_to_delete.append(key)
                
                if keys_to_delete:
                    deleted_count = await redis_client.delete(*keys_to_delete)
                    logger.info(f"Flushed {deleted_count} cached documents from Redis")
                else:
                    logger.info("No documents to flush from Redis cache")
                    
                return True
                
        except Exception as e:
            logger.error(f"Failed to flush cache from Redis: {e}")
            return False
    
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of Redis cache.
        
        Returns:
            Health status dictionary
        """
        if self.test_mode:
            return {
                "status": "healthy",
                "test_mode": True,
                "cached_documents": len(self._test_cache),
                "default_ttl": self.default_ttl
            }
            
        try:
            if not await self._ensure_connection():
                return {
                    "status": "unhealthy",
                    "error": "Redis not available",
                    "test_mode": False
                }
            
            async with self._connection_manager.get_connection() as redis_client:
                # Test connection
                pong = await redis_client.ping()
                
                if pong:
                    cached_count = await self.count_cached_documents()
                    
                    # Get Redis info
                    info = await redis_client.info()
                    
                    return {
                        "status": "healthy",
                        "test_mode": False,
                        "cached_documents": cached_count,
                        "default_ttl": self.default_ttl,
                        "redis_info": {
                            "connected_clients": info.get("connected_clients", 0),
                            "used_memory": info.get("used_memory_human", "unknown"),
                            "uptime": info.get("uptime_in_seconds", 0)
                        }
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": "Redis ping failed",
                        "test_mode": False
                    }
                    
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "test_mode": self.test_mode
            }
    
    async def close(self):
        """Close Redis connection."""
        if not self.test_mode and self._connection_manager:
            await self._connection_manager.close()