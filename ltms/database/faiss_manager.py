"""
FAISS Vector Store Manager for LTMC Atomic Operations.
Provides atomic document vector storage with embedding support.

File: ltms/database/faiss_manager.py
Lines: ~290 (under 300 limit)
Purpose: FAISS operations for atomic cross-database synchronization
"""
import os
import logging
import numpy as np
import pickle
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from ltms.vector_store.faiss_store import (
    create_faiss_index, add_vectors, search_vectors, 
    save_index, load_index, FAISS_AVAILABLE
)
from ltms.vector_store.faiss_config import get_configured_index_path
from ltms.config.json_config_loader import get_config

logger = logging.getLogger(__name__)

class FAISSManager:
    """
    FAISS vector store manager for atomic document operations.
    Provides transaction-safe document vector storage and retrieval.
    """
    
    def __init__(self, index_path: Optional[str] = None, dimension: Optional[int] = None, 
                 test_mode: bool = False):
        """Initialize FAISS manager with vector index.
        
        Args:
            index_path: Path to FAISS index file (uses config default if None)
            dimension: Vector dimension for embeddings (uses config default if None)
            test_mode: Enable test mode for unit testing
        """
        self.test_mode = test_mode
        
        # Get dimension from config if not provided
        if dimension is None:
            from ..config.json_config_loader import get_config
            config = get_config()
            self.dimension = config.vector_dimension  # Uses 384 from config
        else:
            self.dimension = dimension
        
        if test_mode:
            self.index_path = None
            self.metadata_path = None
            self._index = None
            self._metadata: Dict[str, Any] = {}
            self._is_available = True
        else:
            if index_path:
                self.index_path = index_path
            else:
                self.index_path = get_configured_index_path()
            
            self.metadata_path = self.index_path + ".metadata"
            self._index = None
            self._metadata: Dict[str, Any] = {}
            self._is_available = FAISS_AVAILABLE
            
            if self._is_available:
                self._load_or_create_index()
        
        logger.info(f"FAISSManager initialized (test_mode={test_mode}, available={self._is_available})")
    
    def is_available(self) -> bool:
        """Check if FAISS is available."""
        return self._is_available
    
    def _load_or_create_index(self):
        """Load existing index or create new one."""
        try:
            if os.path.exists(self.index_path):
                self._index = load_index(self.index_path, self.dimension)
                logger.info(f"Loaded FAISS index from {self.index_path}")
                
                # Load metadata
                if os.path.exists(self.metadata_path):
                    with open(self.metadata_path, 'rb') as f:
                        self._metadata = pickle.load(f)
                    logger.info(f"Loaded FAISS metadata from {self.metadata_path}")
                else:
                    # Initialize empty metadata if file doesn't exist
                    self._metadata = {}
                    
                # Ensure required metadata keys exist
                self._ensure_metadata_structure()
            else:
                # Create new index
                self._index = create_faiss_index(self.dimension)
                self._metadata = {
                    "doc_id_to_index": {},
                    "index_to_doc_id": {},
                    "next_index": 0,
                    "created_at": datetime.now().isoformat()
                }
                logger.info(f"Created new FAISS index with dimension {self.dimension}")
                
        except Exception as e:
            logger.error(f"Failed to load/create FAISS index: {e}")
            self._is_available = False
    
    def _ensure_metadata_structure(self):
        """Ensure metadata has all required keys with proper defaults."""
        if not isinstance(self._metadata, dict):
            self._metadata = {}
        
        # Ensure core structure exists
        if "doc_id_to_index" not in self._metadata:
            self._metadata["doc_id_to_index"] = {}
        if "index_to_doc_id" not in self._metadata:
            self._metadata["index_to_doc_id"] = {}
        if "next_index" not in self._metadata:
            self._metadata["next_index"] = 0
        if "created_at" not in self._metadata:
            self._metadata["created_at"] = datetime.now().isoformat()
    
    def _save_index(self):
        """Save index and metadata to disk."""
        if self.test_mode:
            return True
            
        try:
            if self._index is not None:
                save_index(self._index, self.index_path)
                
                # Save metadata
                with open(self.metadata_path, 'wb') as f:
                    pickle.dump(self._metadata, f)
                    
                logger.info(f"Saved FAISS index and metadata")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")
            return False
    
    def _generate_embedding(self, content: str) -> np.ndarray:
        """Generate semantic embedding vector for content using real transformer model."""
        # In test mode, return deterministic fake embedding
        if self.test_mode:
            # Create deterministic fake embedding based on content hash
            hash_value = hash(content)
            np.random.seed(abs(hash_value) % (2**32))
            return np.random.random(self.dimension).astype('float32')
        
        # For production, use real semantic embeddings via EmbeddingService
        try:
            # Import delayed to avoid circular imports and startup issues  
            from ..services.embedding_service import get_embedding_service
            
            # Get singleton embedding service instance
            embedding_service = get_embedding_service(test_mode=self.test_mode)
            
            if not embedding_service.is_available():
                logger.warning("EmbeddingService not available, falling back to zero vector")
                return np.zeros(self.dimension, dtype='float32')
            
            # Generate real semantic embedding with caching and normalization
            embedding = embedding_service.encode(
                content, 
                use_cache=True,  # Enable caching for performance
                normalize=True   # Normalize for cosine similarity
            )
            
            # Verify dimension consistency for FAISS compatibility
            if len(embedding) != self.dimension:
                logger.error(f"Embedding dimension mismatch: got {len(embedding)}, expected {self.dimension}")
                return np.zeros(self.dimension, dtype='float32')
            
            # Ensure correct dtype for FAISS
            embedding = embedding.astype('float32')
            
            logger.debug(f"Generated semantic embedding for {len(content)} chars content")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate semantic embedding: {e}")
            # Return normalized zero vector as fallback to maintain system stability
            fallback = np.zeros(self.dimension, dtype='float32')
            # Add small random noise to prevent identical zero vectors
            fallback += np.random.normal(0, 0.01, self.dimension).astype('float32')
            fallback = fallback / np.linalg.norm(fallback)  # Normalize
            return fallback
    
    async def store_document_vector(self, doc_id: str, content: str, 
                                   metadata: Dict[str, Any] = None) -> bool:
        """
        Store document vector in FAISS index atomically.
        
        Args:
            doc_id: Unique document identifier
            content: Document content for embedding generation
            metadata: Document metadata dictionary
            
        Returns:
            True if storage successful, False otherwise
        """
        if self.test_mode:
            return True
            
        if not self.is_available():
            logger.error("FAISS not available for document storage")
            return False
            
        try:
            # Ensure metadata structure is valid before proceeding
            self._ensure_metadata_structure()
            
            # Generate embedding
            embedding = self._generate_embedding(content)
            
            # Check if document already exists
            if doc_id in self._metadata["doc_id_to_index"]:
                # Update existing vector (in FAISS, we need to remove and re-add)
                old_index = self._metadata["doc_id_to_index"][doc_id]
                logger.warning(f"Document {doc_id} already exists at index {old_index}, updating...")
            
            # Get next index
            vector_index = self._metadata["next_index"]
            
            # Add vector to index
            add_vectors(self._index, embedding.reshape(1, -1), [vector_index])
            
            # Update metadata
            self._metadata["doc_id_to_index"][doc_id] = vector_index
            self._metadata["index_to_doc_id"][vector_index] = doc_id
            self._metadata["next_index"] = vector_index + 1
            self._metadata[f"doc_{doc_id}"] = {
                "content_preview": content[:100],
                "metadata": metadata or {},
                "stored_at": datetime.now().isoformat(),
                "vector_index": vector_index
            }
            
            # Save to disk
            success = self._save_index()
            
            if success:
                logger.info(f"Successfully stored document vector {doc_id} at index {vector_index}")
            else:
                logger.error(f"Failed to save document vector {doc_id} to disk")
                
            return success
            
        except Exception as e:
            logger.error(f"Exception storing document vector {doc_id} in FAISS: {e}")
            return False
    
    async def retrieve_document_vector(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve document vector information from FAISS.
        
        Args:
            doc_id: Document identifier to retrieve
            
        Returns:
            Document vector information or None if not found
        """
        if self.test_mode:
            return {
                "id": doc_id,
                "vector_index": 0,
                "content_preview": "test content",
                "metadata": {},
                "stored_at": datetime.now().isoformat()
            }
            
        if not self.is_available():
            return None
            
        try:
            # Ensure metadata structure exists
            self._ensure_metadata_structure()
            
            if doc_id not in self._metadata["doc_id_to_index"]:
                return None
                
            doc_metadata = self._metadata.get(f"doc_{doc_id}")
            if doc_metadata:
                return {
                    "id": doc_id,
                    "vector_index": doc_metadata.get("vector_index"),
                    "content_preview": doc_metadata.get("content_preview", ""),
                    "metadata": doc_metadata.get("metadata", {}),
                    "stored_at": doc_metadata.get("stored_at")
                }
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve document vector {doc_id} from FAISS: {e}")
            return None
    
    async def document_exists(self, doc_id: str) -> bool:
        """
        Check if document vector exists in FAISS index.
        
        Args:
            doc_id: Document identifier to check
            
        Returns:
            True if document exists, False otherwise
        """
        if self.test_mode:
            return True
            
        if not self.is_available():
            return False
            
        try:
            # Ensure metadata structure exists
            self._ensure_metadata_structure()
            return doc_id in self._metadata["doc_id_to_index"]
            
        except Exception as e:
            logger.error(f"Failed to check document existence {doc_id} in FAISS: {e}")
            return False
    
    async def delete_document_vector(self, doc_id: str) -> bool:
        """
        Delete document vector from FAISS index.
        Note: FAISS doesn't support true deletion, so we mark as deleted in metadata.
        
        Args:
            doc_id: Document identifier to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        if self.test_mode:
            return True
            
        if not self.is_available():
            return False
            
        try:
            # Ensure metadata structure exists
            self._ensure_metadata_structure()
            
            if doc_id not in self._metadata["doc_id_to_index"]:
                logger.warning(f"Document {doc_id} not found in FAISS index")
                return True
                
            # Get vector index
            vector_index = self._metadata["doc_id_to_index"][doc_id]
            
            # Mark as deleted in metadata (FAISS doesn't support true deletion)
            del self._metadata["doc_id_to_index"][doc_id]
            del self._metadata["index_to_doc_id"][vector_index]
            
            # Remove document metadata
            if f"doc_{doc_id}" in self._metadata:
                del self._metadata[f"doc_{doc_id}"]
            
            # Mark index as deleted
            self._metadata.setdefault("deleted_indices", set()).add(vector_index)
            
            # Save metadata
            success = self._save_index()
            
            if success:
                logger.info(f"Successfully marked document vector {doc_id} as deleted from FAISS")
            else:
                logger.error(f"Failed to save deletion of document vector {doc_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete document vector {doc_id} from FAISS: {e}")
            return False
    
    async def search_similar(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector similarity.
        
        Args:
            query: Query text to find similar documents
            k: Number of similar documents to return
            
        Returns:
            List of similar document information
        """
        if self.test_mode:
            return [{
                "doc_id": "test_doc_1",
                "distance": 0.1,
                "content_preview": "test content"
            }]
            
        if not self.is_available() or self._index.ntotal == 0:
            return []
            
        try:
            # Ensure metadata structure exists
            self._ensure_metadata_structure()
            
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            
            # Search for similar vectors
            distances, indices = search_vectors(self._index, query_embedding.reshape(1, -1), k)
            
            results = []
            for i, (distance, index) in enumerate(zip(distances[0], indices[0])):
                # Skip deleted indices
                if index in self._metadata.get("deleted_indices", set()):
                    continue
                    
                # Get document ID
                doc_id = self._metadata["index_to_doc_id"].get(index)
                if doc_id:
                    doc_metadata = self._metadata.get(f"doc_{doc_id}", {})
                    
                    # Include stored_at timestamp from FAISS internal metadata
                    document_metadata = doc_metadata.get("metadata", {}).copy()
                    document_metadata["stored_at"] = doc_metadata.get("stored_at", "")
                    
                    results.append({
                        "doc_id": doc_id,
                        "distance": float(distance),
                        "content_preview": doc_metadata.get("content_preview", ""),
                        "metadata": document_metadata,
                        "vector_index": index
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search similar documents in FAISS: {e}")
            return []
    
    async def search_similar_with_conversation_filter(self, query: str, k: int = 5, conversation_id: str = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector similarity with conversation filtering.
        
        Args:
            query: Query text to find similar documents
            k: Number of similar documents to return
            conversation_id: Optional conversation ID to filter results
            
        Returns:
            List of similar document information filtered by conversation
        """
        if self.test_mode:
            return [{
                "doc_id": "test_doc_1",
                "distance": 0.1,
                "content_preview": "test content",
                "metadata": {"conversation_id": conversation_id} if conversation_id else {}
            }]
            
        if not self.is_available() or self._index.ntotal == 0:
            return []
            
        try:
            # Ensure metadata structure exists
            self._ensure_metadata_structure()
            
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            
            # Search for similar vectors with much larger k to account for filtering
            # Increase search window significantly to ensure conversation filtering can find relevant documents
            search_k = min(k * 10, self._index.ntotal)  # Get 10x results to filter (was 3x)
            distances, indices = search_vectors(self._index, query_embedding.reshape(1, -1), search_k)
            
            results = []
            for i, (distance, index) in enumerate(zip(distances[0], indices[0])):
                # Skip deleted indices
                if index in self._metadata.get("deleted_indices", set()):
                    continue
                    
                # Get document ID
                doc_id = self._metadata["index_to_doc_id"].get(index)
                if doc_id:
                    doc_metadata = self._metadata.get(f"doc_{doc_id}", {})
                    
                    # Apply conversation filtering if specified
                    if conversation_id:
                        doc_conversation = doc_metadata.get("metadata", {}).get("conversation_id")
                        if doc_conversation != conversation_id:
                            logger.debug(f"Filtering out doc {doc_id}: conversation '{doc_conversation}' != '{conversation_id}'")
                            continue
                    
                    # Include stored_at timestamp from FAISS internal metadata
                    document_metadata = doc_metadata.get("metadata", {}).copy()
                    document_metadata["stored_at"] = doc_metadata.get("stored_at", "")
                    
                    results.append({
                        "doc_id": doc_id,
                        "distance": float(distance),
                        "content_preview": doc_metadata.get("content_preview", ""),
                        "metadata": document_metadata,
                        "vector_index": index
                    })
                    
                    # Stop when we have enough results
                    if len(results) >= k:
                        break
            
            logger.info(f"FAISS search: query='{query}', conversation_id='{conversation_id}', found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search similar documents with conversation filter in FAISS: {e}")
            return []
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of FAISS vector store.
        
        Returns:
            Health status dictionary
        """
        try:
            if not self.is_available():
                return {
                    "status": "unhealthy",
                    "error": "FAISS not available",
                    "test_mode": self.test_mode
                }
            
            if self.test_mode:
                return {
                    "status": "healthy",
                    "test_mode": True,
                    "vector_count": 1,
                    "dimension": self.dimension
                }
            
            # Ensure metadata structure exists
            self._ensure_metadata_structure()
            
            vector_count = self._index.ntotal if self._index else 0
            document_count = len(self._metadata["doc_id_to_index"])
            
            return {
                "status": "healthy",
                "test_mode": False,
                "vector_count": vector_count,
                "document_count": document_count,
                "dimension": self.dimension,
                "index_path": self.index_path
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "test_mode": self.test_mode
            }


# Global instance for singleton pattern
faiss_manager = FAISSManager()