"""
FAISS Service - Vector Operations
================================

FAISS vector operations for semantic search.
Existing FAISS index in data/faiss_index directory.
"""

import faiss
import numpy as np
import logging
from typing import List, Tuple, Optional
from pathlib import Path

from config.settings import LTMCSettings
from utils.performance_utils import measure_performance


class FAISSService:
    """
    FAISS service for vector operations and semantic search.
    
    Manages existing FAISS index for semantic search operations.
    """
    
    def __init__(self, settings: LTMCSettings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.index: Optional[faiss.IndexFlatL2] = None
        self.dimension = 384  # Standard sentence transformer dimension
        
    async def initialize(self) -> bool:
        """Initialize FAISS index."""
        try:
            index_path = self.settings.faiss_index_path
            
            if index_path.exists():
                # Load existing index
                self.index = faiss.read_index(str(index_path))
                self.logger.info(f"✅ Loaded FAISS index with {self.index.ntotal} vectors")
            else:
                # Create new index
                self.index = faiss.IndexFlatL2(self.dimension)
                # Ensure directory exists
                index_path.parent.mkdir(parents=True, exist_ok=True)
                faiss.write_index(self.index, str(index_path))
                self.logger.info("✅ Created new FAISS index")
                
            return True
            
        except Exception as e:
            self.logger.error(f"❌ FAISS initialization failed: {e}")
            return False
    
    @measure_performance
    async def add_vector(self, content: str) -> int:
        """
        Add vector to FAISS index.
        
        Args:
            content: Text content to vectorize and add
            
        Returns:
            int: Vector ID
        """
        if not self.index:
            raise RuntimeError("FAISS index not initialized")
            
        # TODO: Implement actual text embedding
        # For now, create a dummy vector
        vector = np.random.random((1, self.dimension)).astype('float32')
        
        vector_id = self.index.ntotal
        self.index.add(vector)
        
        # Save index
        faiss.write_index(self.index, str(self.settings.faiss_index_path))
        
        return vector_id
    
    @measure_performance
    async def search_vectors(self, query: str, top_k: int = 5) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query: Query text to search for
            top_k: Number of results to return
            
        Returns:
            List of (vector_id, similarity_score) tuples
        """
        if not self.index or self.index.ntotal == 0:
            return []
            
        # TODO: Implement actual text embedding for query
        # For now, create a dummy query vector
        query_vector = np.random.random((1, self.dimension)).astype('float32')
        
        distances, indices = self.index.search(query_vector, min(top_k, self.index.ntotal))
        
        # Convert to list of tuples (vector_id, similarity_score)
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx != -1:  # Valid result
                # Convert L2 distance to similarity score (0-1, higher is better)
                similarity = max(0.0, 1.0 / (1.0 + dist))
                results.append((int(idx), float(similarity)))
        
        return results