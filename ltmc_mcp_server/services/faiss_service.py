"""
FAISS Service - Vector Operations
================================

FAISS vector operations for semantic search.
Existing FAISS index in data/faiss_index directory.
"""

import faiss
import numpy as np
import logging
from typing import List, Tuple, Optional, Dict, Any, TYPE_CHECKING
from pathlib import Path

from config.settings import LTMCSettings
from utils.performance_utils import measure_performance

if TYPE_CHECKING:
    from services.database_service import DatabaseService


class FAISSService:
    """
    FAISS service for vector operations and semantic search.
    
    Manages existing FAISS index for semantic search operations.
    """
    
    def __init__(self, settings: LTMCSettings, database_service: Optional['DatabaseService'] = None):
        self.settings = settings
        self.database_service = database_service
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
        
        vector_id = await self._get_next_vector_id()
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
    
    async def _get_next_vector_id(self) -> int:
        """
        Get next available vector ID using atomic database sequence.
        
        RACE CONDITION FIX: Uses atomic UPDATE with row locking to prevent 
        concurrent operations from generating the same vector_id.
        
        Returns:
            int: Next sequential vector ID from database
            
        Raises:
            RuntimeError: If database service is not available
        """
        if not self.database_service:
            raise RuntimeError("Database service not available for vector ID generation")
        
        try:
            import aiosqlite
            async with aiosqlite.connect(self.database_service.basic_service.db_path) as db:
                # ATOMIC FIX: Use UPDATE with immediate commit to prevent race conditions
                # This ensures only one operation can increment the sequence at a time
                
                # First, ensure the sequence record exists
                await db.execute("""
                    INSERT OR IGNORE INTO VectorIdSequence (id, last_vector_id) 
                    VALUES (1, 0)
                """)
                
                # ATOMIC OPERATION: Increment and get new value in one statement
                # Use RETURNING clause for atomic read-after-write (SQLite 3.35+)
                try:
                    cursor = await db.execute("""
                        UPDATE VectorIdSequence 
                        SET last_vector_id = last_vector_id + 1 
                        WHERE id = 1 
                        RETURNING last_vector_id
                    """)
                    row = await cursor.fetchone()
                    await db.commit()
                    
                    if row:
                        next_id = row[0]
                        self.logger.debug(f"Generated vector ID (atomic): {next_id}")
                        return next_id
                    else:
                        raise RuntimeError("Failed to update VectorIdSequence atomically")
                        
                except aiosqlite.OperationalError:
                    # Fallback for older SQLite versions without RETURNING support
                    # Use transaction with immediate locking
                    await db.execute("BEGIN IMMEDIATE")
                    try:
                        cursor = await db.execute("SELECT last_vector_id FROM VectorIdSequence WHERE id = 1")
                        row = await cursor.fetchone()
                        
                        next_id = (row[0] + 1) if row else 1
                        
                        await db.execute(
                            "UPDATE VectorIdSequence SET last_vector_id = ? WHERE id = 1",
                            (next_id,)
                        )
                        await db.commit()
                        
                        self.logger.debug(f"Generated vector ID (fallback): {next_id}")
                        return next_id
                        
                    except Exception as e:
                        await db.rollback()
                        raise RuntimeError(f"Atomic vector ID generation failed: {e}")
                
        except Exception as e:
            self.logger.error(f"Failed to get next vector ID: {e}")
            raise RuntimeError(f"Vector ID generation failed: {e}")
    
    @measure_performance
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform FAISS vector database health check.
        
        Returns:
            Dict with health status, index info, and vector metrics
        """
        import time
        import os
        
        try:
            # Test index availability and basic operations
            start_time = time.time()
            
            if not self.index:
                return {
                    "status": "error",
                    "connected": False,
                    "service": "FAISS",
                    "latency_ms": None,
                    "metrics": {"error_details": "Index not initialized"},
                    "error": "FAISS index not initialized"
                }
            
            # Test index basic properties
            vector_count = self.index.ntotal
            index_dimension = self.index.d
            
            # Test index file accessibility
            index_path = self.settings.faiss_index_path
            index_exists = index_path.exists()
            index_size = os.path.getsize(index_path) if index_exists else 0
            
            # Test search capability (if we have vectors)
            search_capable = False
            if vector_count > 0:
                try:
                    # Create a test query vector
                    test_vector = np.random.random((1, index_dimension)).astype('float32')
                    distances, indices = self.index.search(test_vector, min(1, vector_count))
                    search_capable = True
                except Exception as search_error:
                    self.logger.warning(f"FAISS search test failed: {search_error}")
                    search_capable = False
            else:
                search_capable = True  # Search is capable, just no data to search
            
            # Test add capability (with rollback)
            add_capable = False
            original_count = vector_count
            try:
                # Add a test vector
                test_vector = np.random.random((1, index_dimension)).astype('float32')
                self.index.add(test_vector)
                
                # Verify it was added
                if self.index.ntotal == original_count + 1:
                    add_capable = True
                    
                    # Remove the test vector by reconstructing original index
                    if original_count > 0:
                        # Reconstruct original vectors (this is expensive, but thorough)
                        original_vectors = np.zeros((original_count, index_dimension), dtype='float32')
                        for i in range(original_count):
                            original_vectors[i] = self.index.reconstruct(i)
                        
                        # Recreate index with original vectors only
                        self.index = faiss.IndexFlatL2(index_dimension)
                        self.index.add(original_vectors)
                    else:
                        # Just reset to empty index
                        self.index = faiss.IndexFlatL2(index_dimension)
                        
            except Exception as add_error:
                self.logger.warning(f"FAISS add test failed: {add_error}")
                add_capable = False
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "connected": True,
                "service": "FAISS",
                "latency_ms": round(latency_ms, 2),
                "metrics": {
                    "vector_count": vector_count,
                    "index_dimension": index_dimension,
                    "index_file_exists": index_exists,
                    "index_file_size_bytes": index_size,
                    "index_file_path": str(index_path),
                    "search_capable": search_capable,
                    "add_capable": add_capable
                },
                "error": None
            }
            
        except Exception as e:
            self.logger.error(f"FAISS health check failed: {e}")
            return {
                "status": "error",
                "connected": False,
                "service": "FAISS",
                "latency_ms": None,
                "metrics": {
                    "error_details": str(e),
                    "index_initialized": self.index is not None,
                    "index_file_path": str(self.settings.faiss_index_path) if hasattr(self.settings, 'faiss_index_path') else None
                },
                "error": str(e)
            }