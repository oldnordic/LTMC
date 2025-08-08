"""Enhanced embedding service with Redis caching for LTMC."""

import numpy as np
import logging
from typing import List, Optional, Any
from sentence_transformers import SentenceTransformer

from .embedding_service import create_embedding_model, encode_text, encode_texts
from .redis_service import get_cache_service, redis_context

logger = logging.getLogger(__name__)


class CachedEmbeddingService:
    """Embedding service with Redis caching layer."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize cached embedding service.
        
        Args:
            model_name: Name of the SentenceTransformer model
        """
        self.model_name = model_name
        self._model: Optional[SentenceTransformer] = None
        self._cache_service: Optional[Any] = None
        
    async def _get_model(self) -> SentenceTransformer:
        """Get or create the embedding model."""
        if self._model is None:
            self._model = create_embedding_model(self.model_name)
        return self._model
    
    async def _get_cache_service(self) -> Any:
        """Get or create the Redis cache service."""
        if self._cache_service is None:
            try:
                self._cache_service = await get_cache_service()
            except Exception as e:
                logger.warning(f"Redis cache not available: {e}")
                self._cache_service = None
        return self._cache_service
    
    async def encode_text_cached(self, text: str) -> np.ndarray:
        """Encode text with caching support.
        
        Args:
            text: Text to encode
            
        Returns:
            Numpy array containing the text embedding
        """
        # Try to get from cache first
        cache_service = await self._get_cache_service()
        
        if cache_service:
            try:
                cached_embedding = await cache_service.get_cached_embedding(text)
                if cached_embedding is not None:
                    logger.debug(f"Cache hit for text embedding (length: {len(text)})")
                    return np.array(cached_embedding)
            except Exception as e:
                logger.warning(f"Cache retrieval failed: {e}")
        
        # Cache miss or cache unavailable - compute embedding
        model = await self._get_model()
        embedding = encode_text(model, text)
        
        # Store in cache if available
        if cache_service:
            try:
                await cache_service.cache_embedding(text, embedding)
                logger.debug(f"Cached text embedding (length: {len(text)})")
            except Exception as e:
                logger.warning(f"Cache storage failed: {e}")
        
        return embedding
    
    async def encode_texts_cached(self, texts: List[str]) -> np.ndarray:
        """Encode multiple texts with caching support.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            Numpy array containing embeddings for all texts
        """
        if not texts:
            model = await self._get_model()
            return np.empty((0, model.get_sentence_embedding_dimension()))
        
        cache_service = await self._get_cache_service()
        cached_embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        # Check cache for each text
        if cache_service:
            for i, text in enumerate(texts):
                try:
                    cached_embedding = await cache_service.get_cached_embedding(text)
                    if cached_embedding is not None:
                        cached_embeddings.append((i, np.array(cached_embedding)))
                    else:
                        uncached_texts.append(text)
                        uncached_indices.append(i)
                except Exception as e:
                    logger.warning(f"Cache retrieval failed for text {i}: {e}")
                    uncached_texts.append(text)
                    uncached_indices.append(i)
        else:
            # No cache available, process all texts
            uncached_texts = texts
            uncached_indices = list(range(len(texts)))
        
        # Compute embeddings for uncached texts
        new_embeddings = []
        if uncached_texts:
            model = await self._get_model()
            computed_embeddings = encode_texts(model, uncached_texts)
            
            # Store new embeddings in cache
            if cache_service:
                for text, embedding in zip(uncached_texts, computed_embeddings):
                    try:
                        await cache_service.cache_embedding(text, embedding)
                    except Exception as e:
                        logger.warning(f"Cache storage failed: {e}")
            
            new_embeddings = [(idx, emb) for idx, emb in zip(uncached_indices, computed_embeddings)]
        
        # Combine cached and new embeddings in correct order
        all_embeddings = cached_embeddings + new_embeddings
        all_embeddings.sort(key=lambda x: x[0])  # Sort by original index
        
        result = np.array([emb for _, emb in all_embeddings])
        
        cache_hits = len(cached_embeddings)
        cache_misses = len(new_embeddings)
        logger.debug(f"Embedding batch: {cache_hits} cache hits, {cache_misses} cache misses")
        
        return result
    
    async def clear_embedding_cache(self) -> int:
        """Clear embedding cache.
        
        Returns:
            Number of cache entries cleared
        """
        cache_service = await self._get_cache_service()
        if cache_service:
            try:
                return await cache_service.invalidate_cache("ltmc:embedding:*")
            except Exception as e:
                logger.error(f"Failed to clear embedding cache: {e}")
                return 0
        return 0
    
    async def get_cache_stats(self) -> dict:
        """Get embedding cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        cache_service = await self._get_cache_service()
        if cache_service:
            try:
                stats = await cache_service.get_cache_stats()
                return {
                    "cache_available": True,
                    "embedding_cache_count": stats.get("embedding_cache_count", 0),
                    "redis_connected": stats.get("connected", False)
                }
            except Exception as e:
                logger.error(f"Failed to get cache stats: {e}")
                return {"cache_available": False, "error": str(e)}
        return {"cache_available": False}


# Global cached embedding service instance
_cached_embedding_service: Optional[CachedEmbeddingService] = None


async def get_cached_embedding_service(model_name: str = "all-MiniLM-L6-v2") -> CachedEmbeddingService:
    """Get or create cached embedding service instance.
    
    Args:
        model_name: Name of the SentenceTransformer model
        
    Returns:
        CachedEmbeddingService instance
    """
    global _cached_embedding_service
    if _cached_embedding_service is None:
        _cached_embedding_service = CachedEmbeddingService(model_name)
    return _cached_embedding_service


# Convenience functions for backward compatibility and easy integration
async def encode_text_with_cache(text: str, model_name: str = "all-MiniLM-L6-v2") -> np.ndarray:
    """Encode text with caching support.
    
    Args:
        text: Text to encode
        model_name: Name of the SentenceTransformer model
        
    Returns:
        Numpy array containing the text embedding
    """
    service = await get_cached_embedding_service(model_name)
    return await service.encode_text_cached(text)


async def encode_texts_with_cache(texts: List[str], model_name: str = "all-MiniLM-L6-v2") -> np.ndarray:
    """Encode multiple texts with caching support.
    
    Args:
        texts: List of texts to encode
        model_name: Name of the SentenceTransformer model
        
    Returns:
        Numpy array containing embeddings for all texts
    """
    service = await get_cached_embedding_service(model_name)
    return await service.encode_texts_cached(texts)