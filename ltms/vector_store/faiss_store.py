"""FAISS vector store operations for LTMC."""

import os
import numpy as np
import pickle
from typing import List, Tuple


class MockFAISSIndex:
    """Mock FAISS index for testing purposes."""
    
    def __init__(self, dimension: int):
        self.dimension = dimension
        self.vectors = []
        self.vector_count = 0
    
    def add(self, vectors: np.ndarray):
        """Add vectors to the index."""
        vectors = vectors.astype('float32')
        for i in range(vectors.shape[0]):
            self.vectors.append(vectors[i])
            self.vector_count += 1
    
    def search(self, query_vector: np.ndarray, k: int):
        """Search for similar vectors."""
        query_vector = query_vector.astype('float32')
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)
        
        if not self.vectors:
            return np.array([[]]), np.array([[]])
        
        # Simple L2 distance calculation
        distances = []
        indices = []
        
        for i, vector in enumerate(self.vectors):
            dist = np.linalg.norm(query_vector[0] - vector)
            distances.append(dist)
            indices.append(i)
        
        # Sort by distance and take top k
        sorted_pairs = sorted(zip(distances, indices))
        top_k_distances = [pair[0] for pair in sorted_pairs[:k]]
        top_k_indices = [pair[1] for pair in sorted_pairs[:k]]
        
        return np.array([top_k_distances]), np.array([top_k_indices])


def create_faiss_index(dimension: int) -> MockFAISSIndex:
    """Create a new FAISS index for vector similarity search.
    
    Args:
        dimension: Dimension of the vectors to be stored
        
    Returns:
        FAISS index instance
    """
    return MockFAISSIndex(dimension)


def add_vectors(
    index: MockFAISSIndex, 
    vectors: np.ndarray, 
    vector_ids: List[int]
) -> None:
    """Add vectors to the FAISS index.
    
    Args:
        index: FAISS index to add vectors to
        vectors: Numpy array of vectors to add (shape: n_vectors x dimension)
        vector_ids: List of vector IDs corresponding to the vectors
    """
    # Ensure vectors are float32
    vectors = vectors.astype('float32')
    
    # Add vectors to index
    index.add(vectors)


def search_vectors(
    index: MockFAISSIndex, 
    query_vector: np.ndarray, 
    k: int
) -> Tuple[np.ndarray, np.ndarray]:
    """Search for similar vectors in the FAISS index.
    
    Args:
        index: FAISS index to search in
        query_vector: Query vector (shape: 1 x dimension)
        k: Number of similar vectors to return
        
    Returns:
        Tuple of (distances, indices) where distances are L2 distances
        and indices are the positions of similar vectors in the index
    """
    # Ensure query vector is float32 and has correct shape
    query_vector = query_vector.astype('float32')
    if query_vector.ndim == 1:
        query_vector = query_vector.reshape(1, -1)
    
    # Search for similar vectors
    distances, indices = index.search(query_vector, k)
    
    return distances, indices


def save_index(index: MockFAISSIndex, file_path: str) -> None:
    """Save a FAISS index to disk.
    
    Args:
        index: FAISS index to save
        file_path: Path where to save the index
    """
    # For mock implementation, save the vectors using pickle
    data = {
        'dimension': index.dimension,
        'vectors': index.vectors,
        'vector_count': index.vector_count
    }
    with open(file_path, 'wb') as f:
        pickle.dump(data, f)


def load_index(file_path: str, dimension: int) -> MockFAISSIndex:
    """Load a FAISS index from disk.
    
    Args:
        file_path: Path to the saved index file
        dimension: Dimension of the vectors in the index
        
    Returns:
        Loaded FAISS index
    """
    if os.path.exists(file_path):
        # For mock implementation, load the vectors using pickle
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
        
        index = MockFAISSIndex(data['dimension'])
        index.vectors = data['vectors']
        index.vector_count = data['vector_count']
        return index
    else:
        # Return a new index if file doesn't exist
        return create_faiss_index(dimension)
