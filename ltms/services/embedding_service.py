"""Embedding service for LTMC text-to-vector conversion."""

import logging
import numpy as np
from typing import List, Optional
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Global model cache - singleton pattern following Redis service approach
_global_embedding_models: dict[str, SentenceTransformer] = {}
_is_initialized = False


def create_embedding_model(model_name: str) -> SentenceTransformer:
    """Create a sentence transformer model for text embedding.
    
    Args:
        model_name: Name of the model to load (e.g., 'all-MiniLM-L6-v2')
        
    Returns:
        SentenceTransformer model instance
    """
    # Use global singleton if available
    if model_name in _global_embedding_models:
        logger.debug(f"Reusing cached model: {model_name}")
        return _global_embedding_models[model_name]
    
    # Create new model (this is where the expensive loading happens)
    logger.info(f"Loading SentenceTransformer model: {model_name}")
    model = SentenceTransformer(model_name)
    
    # Cache it globally
    _global_embedding_models[model_name] = model
    logger.info(f"Model {model_name} loaded and cached globally")
    
    return model


def get_cached_model(model_name: str) -> Optional[SentenceTransformer]:
    """Get a cached model without loading if not available.
    
    Args:
        model_name: Name of the model
        
    Returns:
        Cached model instance or None if not loaded
    """
    return _global_embedding_models.get(model_name)


def initialize_embedding_models(model_names: List[str]) -> bool:
    """Pre-load embedding models during startup for performance.
    
    This should be called during server startup to avoid loading
    models on the first request.
    
    Args:
        model_names: List of model names to pre-load
        
    Returns:
        True if all models loaded successfully
    """
    global _is_initialized
    
    try:
        for model_name in model_names:
            if model_name not in _global_embedding_models:
                logger.info(f"Pre-loading embedding model: {model_name}")
                model = SentenceTransformer(model_name)
                _global_embedding_models[model_name] = model
                logger.info(f"✅ Model {model_name} pre-loaded successfully")
            else:
                logger.info(f"Model {model_name} already loaded")
        
        _is_initialized = True
        logger.info(f"🚀 Embedding models initialization complete: {list(_global_embedding_models.keys())}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to pre-load embedding models: {e}")
        return False


def cleanup_embedding_models() -> None:
    """Clean up cached embedding models."""
    global _global_embedding_models, _is_initialized
    
    model_count = len(_global_embedding_models)
    _global_embedding_models.clear()
    _is_initialized = False
    logger.info(f"Cleaned up {model_count} embedding models")


def get_model_stats() -> dict:
    """Get statistics about loaded models.
    
    Returns:
        Dictionary with model statistics
    """
    return {
        "initialized": _is_initialized,
        "loaded_models": list(_global_embedding_models.keys()),
        "model_count": len(_global_embedding_models)
    }


def encode_text(model: SentenceTransformer, text: str) -> np.ndarray:
    """Encode a single text into a vector embedding.
    
    Args:
        model: SentenceTransformer model
        text: Text to encode
        
    Returns:
        Numpy array containing the text embedding
    """
    embedding = model.encode(text)
    return embedding


def encode_texts(model: SentenceTransformer, texts: List[str]) -> np.ndarray:
    """Encode multiple texts into vector embeddings.
    
    Args:
        model: SentenceTransformer model
        texts: List of texts to encode
        
    Returns:
        Numpy array containing embeddings for all texts 
        (shape: n_texts x dimension)
    """
    if not texts:
        # Return empty array with correct dimension
        return np.empty((0, model.get_sentence_embedding_dimension()))
    
    embeddings = model.encode(texts)
    return embeddings
