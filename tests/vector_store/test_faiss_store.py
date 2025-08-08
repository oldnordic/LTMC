import tempfile
import os
import numpy as np
from ltms.vector_store.faiss_store import (
    create_faiss_index, add_vectors, search_vectors, save_index, load_index
)


def test_create_faiss_index_creates_valid_index():
    """Test that create_faiss_index creates a valid FAISS index."""
    # Create a temporary directory for the index
    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = os.path.join(temp_dir, "test_index")
        
        # Create index
        index = create_faiss_index(dimension=384)
        
        # Verify it's a valid FAISS index
        assert index is not None
        assert hasattr(index, 'add')
        assert hasattr(index, 'search')
        
        # Test that we can add vectors
        vectors = np.random.rand(5, 384).astype('float32')
        index.add(vectors)
        
        # Test that we can search
        query_vector = np.random.rand(1, 384).astype('float32')
        distances, indices = index.search(query_vector, k=3)
        
        assert len(distances) == 1
        assert len(indices) == 1
        assert len(distances[0]) == 3
        assert len(indices[0]) == 3


def test_add_vectors_adds_vectors_to_index():
    """Test that add_vectors adds vectors to the FAISS index."""
    # Create a temporary directory for the index
    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = os.path.join(temp_dir, "test_index")
        
        # Create index
        index = create_faiss_index(dimension=384)
        
        # Create test vectors
        vectors = np.random.rand(3, 384).astype('float32')
        vector_ids = [1, 2, 3]
        
        # Add vectors
        add_vectors(index, vectors, vector_ids)
        
        # Verify vectors were added by searching
        query_vector = np.random.rand(1, 384).astype('float32')
        distances, indices = search_vectors(index, query_vector, k=3)
        
        assert len(indices[0]) == 3
        # Should find our vectors (indices should be 0, 1, 2)
        assert set(indices[0]) == {0, 1, 2}


def test_search_vectors_finds_similar_vectors():
    """Test that search_vectors finds the most similar vectors."""
    # Create a temporary directory for the index
    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = os.path.join(temp_dir, "test_index")
        
        # Create index
        index = create_faiss_index(dimension=384)
        
        # Create test vectors
        base_vector = np.random.rand(1, 384).astype('float32')
        similar_vector = base_vector + 0.1 * np.random.rand(1, 384).astype('float32')
        different_vector = np.random.rand(1, 384).astype('float32')
        
        vectors = np.vstack([base_vector, similar_vector, different_vector])
        vector_ids = [1, 2, 3]
        
        # Add vectors
        add_vectors(index, vectors, vector_ids)
        
        # Search with the base vector
        distances, indices = search_vectors(index, base_vector, k=2)
        
        # The most similar should be the base vector itself (index 0)
        # and the similar vector (index 1)
        assert indices[0][0] == 0  # Most similar is itself
        assert distances[0][0] < distances[0][1]  # Distance to self should be smallest


def test_save_and_load_index_persists_data():
    """Test that save_index and load_index properly persist and restore data."""
    # Create a temporary directory for the index
    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = os.path.join(temp_dir, "test_index")
        
        # Create index and add vectors
        index = create_faiss_index(dimension=384)
        vectors = np.random.rand(3, 384).astype('float32')
        vector_ids = [1, 2, 3]
        add_vectors(index, vectors, vector_ids)
        
        # Save index
        save_index(index, index_path)
        
        # Verify file was created
        assert os.path.exists(index_path)
        
        # Load index
        loaded_index = load_index(index_path, dimension=384)
        
        # Verify loaded index works
        query_vector = np.random.rand(1, 384).astype('float32')
        distances, indices = search_vectors(loaded_index, query_vector, k=3)
        
        assert len(indices[0]) == 3
        assert set(indices[0]) == {0, 1, 2}
