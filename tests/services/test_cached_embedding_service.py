"""Tests for cached embedding service."""

import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch

from ltms.services.cached_embedding_service import (
    CachedEmbeddingService,
    get_cached_embedding_service,
    encode_text_with_cache,
    encode_texts_with_cache
)


class TestCachedEmbeddingService:
    """Test cached embedding service functionality."""
    
    @pytest.fixture
    def mock_cache_service(self):
        """Create mock cache service."""
        cache_service = AsyncMock()
        cache_service.get_cached_embedding.return_value = None  # Default to cache miss
        cache_service.cache_embedding.return_value = True
        cache_service.get_cache_stats.return_value = {
            "cache_available": True,
            "embedding_cache_count": 10,
            "redis_connected": True
        }
        return cache_service
    
    @pytest.fixture
    def mock_model(self):
        """Create mock SentenceTransformer model."""
        model = MagicMock()
        model.encode.return_value = np.array([1.0, 2.0, 3.0])
        model.get_sentence_embedding_dimension.return_value = 3
        return model
    
    @pytest.fixture
    def embedding_service(self):
        """Create cached embedding service instance."""
        return CachedEmbeddingService("test-model")
    
    @pytest.mark.asyncio
    async def test_initialization(self, embedding_service):
        """Test service initialization."""
        assert embedding_service.model_name == "test-model"
        assert embedding_service._model is None
        assert embedding_service._cache_service is None
    
    @pytest.mark.asyncio
    async def test_encode_text_cache_miss(self, embedding_service, mock_cache_service, mock_model):
        """Test text encoding with cache miss."""
        text = "test text"
        expected_embedding = np.array([1.0, 2.0, 3.0])
        
        # Mock dependencies
        with patch('ltms.services.cached_embedding_service.get_cache_service', 
                  return_value=mock_cache_service):
            with patch('ltms.services.cached_embedding_service.create_embedding_model', 
                      return_value=mock_model):
                with patch('ltms.services.cached_embedding_service.encode_text',
                          return_value=expected_embedding):
                    
                    result = await embedding_service.encode_text_cached(text)
                    
                    # Verify cache was checked
                    mock_cache_service.get_cached_embedding.assert_called_once_with(text)
                    
                    # Verify embedding was computed and cached
                    mock_cache_service.cache_embedding.assert_called_once_with(text, expected_embedding)
                    
                    # Verify result
                    np.testing.assert_array_equal(result, expected_embedding)
    
    @pytest.mark.asyncio
    async def test_encode_text_cache_hit(self, embedding_service, mock_cache_service):
        """Test text encoding with cache hit."""
        text = "test text"
        cached_embedding = [1.0, 2.0, 3.0]
        expected_embedding = np.array(cached_embedding)
        
        # Configure cache to return cached embedding
        mock_cache_service.get_cached_embedding.return_value = cached_embedding
        
        with patch('ltms.services.cached_embedding_service.get_cache_service', 
                  return_value=mock_cache_service):
            
            result = await embedding_service.encode_text_cached(text)
            
            # Verify cache was checked
            mock_cache_service.get_cached_embedding.assert_called_once_with(text)
            
            # Verify no caching was attempted (since it was a hit)
            mock_cache_service.cache_embedding.assert_not_called()
            
            # Verify result
            np.testing.assert_array_equal(result, expected_embedding)
    
    @pytest.mark.asyncio
    async def test_encode_text_no_cache(self, embedding_service, mock_model):
        """Test text encoding when cache is unavailable."""
        text = "test text"
        expected_embedding = np.array([1.0, 2.0, 3.0])
        
        # Mock cache service to raise exception (cache unavailable)
        with patch('ltms.services.cached_embedding_service.get_cache_service', 
                  side_effect=Exception("Redis unavailable")):
            with patch('ltms.services.cached_embedding_service.create_embedding_model', 
                      return_value=mock_model):
                with patch('ltms.services.cached_embedding_service.encode_text',
                          return_value=expected_embedding):
                    
                    result = await embedding_service.encode_text_cached(text)
                    
                    # Verify result (should still work without cache)
                    np.testing.assert_array_equal(result, expected_embedding)
    
    @pytest.mark.asyncio
    async def test_encode_texts_mixed_cache(self, embedding_service, mock_cache_service, mock_model):
        """Test batch text encoding with mixed cache hits/misses."""
        texts = ["text1", "text2", "text3"]
        
        # Configure partial cache hits
        def mock_get_cached_embedding(text):
            if text == "text1":
                return [1.0, 0.0, 0.0]  # Cache hit
            elif text == "text3":
                return [0.0, 0.0, 1.0]  # Cache hit
            else:
                return None  # Cache miss for text2
        
        mock_cache_service.get_cached_embedding.side_effect = mock_get_cached_embedding
        
        # Mock model to return embeddings for uncached texts
        mock_model.encode.return_value = np.array([[0.0, 1.0, 0.0]])  # For text2
        mock_model.get_sentence_embedding_dimension.return_value = 3
        
        with patch('ltms.services.cached_embedding_service.get_cache_service', 
                  return_value=mock_cache_service):
            with patch('ltms.services.cached_embedding_service.create_embedding_model', 
                      return_value=mock_model):
                with patch('ltms.services.cached_embedding_service.encode_texts',
                          return_value=np.array([[0.0, 1.0, 0.0]])):
                    
                    result = await embedding_service.encode_texts_cached(texts)
                    
                    # Verify result shape and order
                    assert result.shape == (3, 3)
                    
                    # Check that embeddings are in correct order
                    expected = np.array([
                        [1.0, 0.0, 0.0],  # text1 (cached)
                        [0.0, 1.0, 0.0],  # text2 (computed)
                        [0.0, 0.0, 1.0]   # text3 (cached)
                    ])
                    np.testing.assert_array_equal(result, expected)
                    
                    # Verify cache operations
                    assert mock_cache_service.get_cached_embedding.call_count == 3
                    mock_cache_service.cache_embedding.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_encode_texts_empty_list(self, embedding_service, mock_model):
        """Test batch encoding with empty text list."""
        texts = []
        
        with patch('ltms.services.cached_embedding_service.create_embedding_model', 
                  return_value=mock_model):
            
            result = await embedding_service.encode_texts_cached(texts)
            
            # Should return empty array with correct dimensions
            assert result.shape == (0, 3)
    
    @pytest.mark.asyncio
    async def test_clear_embedding_cache(self, embedding_service, mock_cache_service):
        """Test clearing embedding cache."""
        mock_cache_service.invalidate_cache.return_value = 5
        
        with patch('ltms.services.cached_embedding_service.get_cache_service', 
                  return_value=mock_cache_service):
            
            cleared_count = await embedding_service.clear_embedding_cache()
            
            assert cleared_count == 5
            mock_cache_service.invalidate_cache.assert_called_once_with("ltmc:embedding:*")
    
    @pytest.mark.asyncio
    async def test_get_cache_stats(self, embedding_service, mock_cache_service):
        """Test getting cache statistics."""
        with patch('ltms.services.cached_embedding_service.get_cache_service', 
                  return_value=mock_cache_service):
            
            stats = await embedding_service.get_cache_stats()
            
            assert stats["cache_available"] is True
            assert stats["embedding_cache_count"] == 10
            assert stats["redis_connected"] is True


class TestCachedEmbeddingSingleton:
    """Test cached embedding service singleton functionality."""
    
    @pytest.mark.asyncio
    async def test_get_cached_embedding_service_singleton(self):
        """Test that get_cached_embedding_service returns same instance."""
        # Clear any existing instance
        import ltms.services.cached_embedding_service as ces_module
        ces_module._cached_embedding_service = None
        
        service1 = await get_cached_embedding_service("model1")
        service2 = await get_cached_embedding_service("model2")  # Different model name
        
        # Should return the same instance regardless of model name
        assert service1 is service2
        assert service1.model_name == "model1"  # Uses first model name
    
    @pytest.mark.asyncio
    async def test_encode_text_with_cache_convenience_function(self):
        """Test convenience function for text encoding."""
        text = "test text"
        expected_embedding = np.array([1.0, 2.0, 3.0])
        
        with patch('ltms.services.cached_embedding_service.get_cached_embedding_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.encode_text_cached.return_value = expected_embedding
            mock_get_service.return_value = mock_service
            
            result = await encode_text_with_cache(text, "test-model")
            
            # Verify service was obtained with correct model
            mock_get_service.assert_called_once_with("test-model")
            
            # Verify encoding was called
            mock_service.encode_text_cached.assert_called_once_with(text)
            
            # Verify result
            np.testing.assert_array_equal(result, expected_embedding)
    
    @pytest.mark.asyncio
    async def test_encode_texts_with_cache_convenience_function(self):
        """Test convenience function for batch text encoding."""
        texts = ["text1", "text2"]
        expected_embeddings = np.array([[1.0, 2.0], [3.0, 4.0]])
        
        with patch('ltms.services.cached_embedding_service.get_cached_embedding_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.encode_texts_cached.return_value = expected_embeddings
            mock_get_service.return_value = mock_service
            
            result = await encode_texts_with_cache(texts, "test-model")
            
            # Verify service was obtained with correct model
            mock_get_service.assert_called_once_with("test-model")
            
            # Verify encoding was called
            mock_service.encode_texts_cached.assert_called_once_with(texts)
            
            # Verify result
            np.testing.assert_array_equal(result, expected_embeddings)


class TestErrorHandling:
    """Test error handling in cached embedding service."""
    
    @pytest.mark.asyncio
    async def test_cache_service_creation_failure(self):
        """Test handling of cache service creation failure."""
        embedding_service = CachedEmbeddingService("test-model")
        
        with patch('ltms.services.cached_embedding_service.get_cache_service', 
                  side_effect=Exception("Cache creation failed")):
            
            # Should not raise exception, just log warning and proceed without cache
            cache_service = await embedding_service._get_cache_service()
            assert cache_service is None
    
    @pytest.mark.asyncio
    async def test_cache_retrieval_failure(self, mock_cache_service, mock_model):
        """Test handling of cache retrieval failure."""
        embedding_service = CachedEmbeddingService("test-model")
        text = "test text"
        expected_embedding = np.array([1.0, 2.0, 3.0])
        
        # Configure cache to raise exception on retrieval
        mock_cache_service.get_cached_embedding.side_effect = Exception("Cache retrieval failed")
        
        with patch('ltms.services.cached_embedding_service.get_cache_service', 
                  return_value=mock_cache_service):
            with patch('ltms.services.cached_embedding_service.create_embedding_model', 
                      return_value=mock_model):
                with patch('ltms.services.cached_embedding_service.encode_text',
                          return_value=expected_embedding):
                    
                    result = await embedding_service.encode_text_cached(text)
                    
                    # Should still return result despite cache failure
                    np.testing.assert_array_equal(result, expected_embedding)
    
    @pytest.mark.asyncio
    async def test_cache_storage_failure(self, mock_cache_service, mock_model):
        """Test handling of cache storage failure."""
        embedding_service = CachedEmbeddingService("test-model")
        text = "test text"
        expected_embedding = np.array([1.0, 2.0, 3.0])
        
        # Configure cache to fail on storage
        mock_cache_service.cache_embedding.side_effect = Exception("Cache storage failed")
        
        with patch('ltms.services.cached_embedding_service.get_cache_service', 
                  return_value=mock_cache_service):
            with patch('ltms.services.cached_embedding_service.create_embedding_model', 
                      return_value=mock_model):
                with patch('ltms.services.cached_embedding_service.encode_text',
                          return_value=expected_embedding):
                    
                    result = await embedding_service.encode_text_cached(text)
                    
                    # Should still return result despite cache storage failure
                    np.testing.assert_array_equal(result, expected_embedding)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])