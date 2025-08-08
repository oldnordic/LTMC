"""Embedding service for LTMC text-to-vector conversion."""

import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer


def create_embedding_model(model_name: str) -> SentenceTransformer:
    """Create a sentence transformer model for text embedding.
    
    Args:
        model_name: Name of the model to load (e.g., 'all-MiniLM-L6-v2')
        
    Returns:
        SentenceTransformer model instance
    """
    return SentenceTransformer(model_name)


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
