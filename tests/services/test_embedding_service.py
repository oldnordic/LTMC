import numpy as np
from ltms.services.embedding_service import (
    create_embedding_model, encode_text, encode_texts
)


def test_create_embedding_model_creates_valid_model():
    """Test that create_embedding_model creates a valid embedding model."""
    # Create embedding model
    model = create_embedding_model("all-MiniLM-L6-v2")
    
    # Verify it's a valid model
    assert model is not None
    assert hasattr(model, 'encode')
    
    # Test that we can encode text
    test_text = "This is a test sentence."
    embedding = encode_text(model, test_text)
    
    # Verify embedding is a numpy array with correct shape
    assert isinstance(embedding, np.ndarray)
    assert embedding.ndim == 1
    assert embedding.shape[0] == 384  # all-MiniLM-L6-v2 dimension


def test_encode_text_creates_valid_embedding():
    """Test that encode_text creates valid embeddings for single text."""
    # Create embedding model
    model = create_embedding_model("all-MiniLM-L6-v2")
    
    # Test single text encoding
    test_text = "This is a test sentence for embedding."
    embedding = encode_text(model, test_text)
    
    # Verify embedding properties
    assert isinstance(embedding, np.ndarray)
    assert embedding.ndim == 1
    assert embedding.shape[0] == 384
    assert not np.isnan(embedding).any()  # No NaN values
    assert not np.isinf(embedding).any()  # No infinite values


def test_encode_texts_creates_valid_embeddings():
    """Test that encode_texts creates valid embeddings for multiple texts."""
    # Create embedding model
    model = create_embedding_model("all-MiniLM-L6-v2")
    
    # Test multiple text encoding
    test_texts = [
        "This is the first sentence.",
        "This is the second sentence.",
        "This is the third sentence."
    ]
    
    embeddings = encode_texts(model, test_texts)
    
    # Verify embeddings properties
    assert isinstance(embeddings, np.ndarray)
    assert embeddings.ndim == 2
    assert embeddings.shape[0] == 3  # Number of texts
    assert embeddings.shape[1] == 384  # Embedding dimension
    assert not np.isnan(embeddings).any()  # No NaN values
    assert not np.isinf(embeddings).any()  # No infinite values


def test_encode_texts_handles_empty_list():
    """Test that encode_texts handles empty list gracefully."""
    # Create embedding model
    model = create_embedding_model("all-MiniLM-L6-v2")
    
    # Test empty list
    embeddings = encode_texts(model, [])
    
    # Verify result
    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape[0] == 0
    assert embeddings.shape[1] == 384


def test_encode_texts_handles_single_text():
    """Test that encode_texts handles single text correctly."""
    # Create embedding model
    model = create_embedding_model("all-MiniLM-L6-v2")
    
    # Test single text
    test_texts = ["This is a single sentence."]
    embeddings = encode_texts(model, test_texts)
    
    # Verify result
    assert isinstance(embeddings, np.ndarray)
    assert embeddings.ndim == 2
    assert embeddings.shape[0] == 1
    assert embeddings.shape[1] == 384
