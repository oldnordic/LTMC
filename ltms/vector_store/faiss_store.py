"""FAISS vector store operations for LTMC - PRODUCTION IMPLEMENTATION."""

import os
import logging
import numpy as np
from typing import List, Tuple, Optional
from .faiss_config import get_configured_index_path

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    FAISS_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_faiss_index(dimension: int) -> faiss.IndexFlatL2:
    """Create a new FAISS index for vector similarity search.
    
    Args:
        dimension: Dimension of the vectors to be stored
        
    Returns:
        FAISS index instance
    """
    if not FAISS_AVAILABLE:
        raise ImportError("FAISS library is not available. Install with: pip install faiss-cpu")
    
    # Use IndexFlatL2 for exact L2 distance search
    index = faiss.IndexFlatL2(dimension)
    logger.info(f"Created FAISS IndexFlatL2 with dimension {dimension}")
    return index


def add_vectors(
    index: faiss.IndexFlatL2, 
    vectors: np.ndarray, 
    vector_ids: List[int]
) -> None:
    """Add vectors to the FAISS index.
    
    Args:
        index: FAISS index to add vectors to
        vectors: Numpy array of vectors to add (shape: n_vectors x dimension)
        vector_ids: List of vector IDs corresponding to the vectors
    """
    if not FAISS_AVAILABLE:
        raise ImportError("FAISS library is not available")
    
    # Ensure vectors are float32 and correct shape
    vectors = vectors.astype('float32')
    if vectors.ndim == 1:
        vectors = vectors.reshape(1, -1)
    
    # Validate dimensions
    if vectors.shape[1] != index.d:
        raise ValueError(f"Vector dimension {vectors.shape[1]} doesn't match index dimension {index.d}")
    
    # Add vectors to index
    index.add(vectors)
    logger.info(f"Added {len(vectors)} vectors to FAISS index. Total: {index.ntotal}")


def search_vectors(
    index: faiss.IndexFlatL2, 
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
    if not FAISS_AVAILABLE:
        raise ImportError("FAISS library is not available")
    
    # Ensure query vector is float32 and has correct shape
    query_vector = query_vector.astype('float32')
    if query_vector.ndim == 1:
        query_vector = query_vector.reshape(1, -1)
    
    # Validate dimensions
    if query_vector.shape[1] != index.d:
        raise ValueError(f"Query vector dimension {query_vector.shape[1]} doesn't match index dimension {index.d}")
    
    # Limit k to available vectors
    k = min(k, index.ntotal) if index.ntotal > 0 else 0
    
    if k == 0:
        # Return empty results if no vectors in index
        return np.array([[]], dtype=np.float32), np.array([[]], dtype=np.int64)
    
    # Search for similar vectors
    distances, indices = index.search(query_vector, k)
    
    logger.debug(f"FAISS search returned {len(indices[0])} results for k={k}")
    return distances, indices


def save_index(index: faiss.IndexFlatL2, file_path: str) -> None:
    """Save a FAISS index to disk with robust error handling and atomic operations.
    
    Args:
        index: FAISS index to save
        file_path: Path where to save the index
        
    Raises:
        ImportError: If FAISS is not available
        OSError: If file operations fail
    """
    if not FAISS_AVAILABLE:
        raise ImportError("FAISS library is not available")
    
    try:
        # Use configured path if file_path is just a filename
        if not os.path.dirname(file_path):
            # file_path is just a filename, use configuration system
            abs_file_path = get_configured_index_path(file_path)
        else:
            # file_path has directory, use as provided but make absolute
            abs_file_path = os.path.abspath(file_path)
        
        # Create directory structure if needed
        parent_dir = os.path.dirname(abs_file_path)
        if parent_dir:  # Only create if parent_dir is not empty
            os.makedirs(parent_dir, exist_ok=True)
        
        # Use atomic write pattern with temporary file
        temp_path = abs_file_path + ".tmp"
        
        try:
            # Write to temporary file first
            faiss.write_index(index, temp_path)
            
            # Atomic move - only succeeds if write was successful
            os.rename(temp_path, abs_file_path)
            
            logger.info(f"Saved FAISS index with {index.ntotal} vectors to {abs_file_path}")
            
        except Exception as e:
            # Clean up temporary file if write failed
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass  # Ignore cleanup errors
            raise OSError(f"Failed to save FAISS index to {abs_file_path}: {e}")
            
    except Exception as e:
        logger.error(f"FAISS index save failed: {e}")
        raise


def load_index(file_path: str, dimension: int) -> faiss.IndexFlatL2:
    """Load a FAISS index from disk with robust path handling.
    
    Args:
        file_path: Path to the saved index file
        dimension: Dimension of the vectors in the index
        
    Returns:
        Loaded FAISS index or new index if loading fails
    """
    if not FAISS_AVAILABLE:
        raise ImportError("FAISS library is not available")
    
    # Use configured path if file_path is just a filename
    if not os.path.dirname(file_path):
        # file_path is just a filename, use configuration system
        abs_file_path = get_configured_index_path(file_path)
    else:
        # file_path has directory, use as provided but make absolute
        abs_file_path = os.path.abspath(file_path)
    
    # Check for temporary files from failed saves and clean them up
    temp_path = abs_file_path + ".tmp"
    if os.path.exists(temp_path):
        logger.warning(f"Found orphaned temporary file {temp_path}, removing")
        try:
            os.remove(temp_path)
        except OSError as e:
            logger.error(f"Failed to remove temporary file {temp_path}: {e}")
    
    if os.path.exists(abs_file_path):
        try:
            # Verify file is not empty or corrupted
            file_size = os.path.getsize(abs_file_path)
            if file_size == 0:
                logger.warning(f"Index file {abs_file_path} is empty, creating new index")
                return create_faiss_index(dimension)
            
            # Load FAISS index from disk using FAISS native format
            index = faiss.read_index(abs_file_path)
            
            # Verify this is IndexFlat compatible (IndexFlatL2 serializes as IndexFlat in FAISS 1.7.4)
            if not isinstance(index, faiss.IndexFlat):
                logger.warning(f"Loaded index is not IndexFlat compatible, creating new index")
                return create_faiss_index(dimension)
            
            if index.d != dimension:
                logger.warning(f"Index dimension {index.d} != expected {dimension}, creating new index")
                return create_faiss_index(dimension)
            
            logger.info(f"Loaded FAISS index with {index.ntotal} vectors from {abs_file_path}")
            return index
            
        except Exception as e:
            logger.error(f"Failed to load FAISS index from {abs_file_path}: {e}")
            logger.info("Creating new FAISS index due to load failure")
            return create_faiss_index(dimension)
    else:
        logger.info(f"Index file {abs_file_path} doesn't exist, creating new index")
        return create_faiss_index(dimension)


def get_index_stats(index: faiss.IndexFlatL2) -> dict:
    """Get statistics about the FAISS index.
    
    Args:
        index: FAISS index to get stats for
        
    Returns:
        Dictionary with index statistics
    """
    if not FAISS_AVAILABLE:
        raise ImportError("FAISS library is not available")
    
    return {
        "total_vectors": index.ntotal,
        "dimension": index.d,
        "index_type": "IndexFlatL2",
        "is_trained": index.is_trained
    }


def diagnose_faiss_persistence(file_path: str = "faiss_index") -> dict:
    """Diagnose FAISS persistence issues and provide troubleshooting information.
    
    Args:
        file_path: Path to check for FAISS index
        
    Returns:
        Dictionary with diagnostic information
    """
    from .faiss_config import validate_faiss_configuration
    
    # Get configuration validation
    config_info = validate_faiss_configuration()
    
    # Use configured path if file_path is just a filename
    if not os.path.dirname(file_path):
        abs_file_path = get_configured_index_path(file_path)
    else:
        abs_file_path = os.path.abspath(file_path)
    
    diagnostic_info = {
        "faiss_available": FAISS_AVAILABLE,
        "configuration": config_info,
        "file_diagnostics": {
            "requested_path": file_path,
            "resolved_path": abs_file_path,
            "file_exists": os.path.exists(abs_file_path),
            "file_size": os.path.getsize(abs_file_path) if os.path.exists(abs_file_path) else 0,
            "parent_directory_exists": os.path.exists(os.path.dirname(abs_file_path)),
            "parent_directory_writable": os.access(os.path.dirname(abs_file_path), os.W_OK) if os.path.exists(os.path.dirname(abs_file_path)) else False
        },
        "environment": {
            "FAISS_INDEX_PATH": os.getenv("FAISS_INDEX_PATH"),
            "LTMC_DATA_DIR": os.getenv("LTMC_DATA_DIR"),
            "working_directory": os.getcwd()
        }
    }
    
    # Check for temporary files
    temp_file = abs_file_path + ".tmp"
    diagnostic_info["file_diagnostics"]["temp_file_exists"] = os.path.exists(temp_file)
    
    # Try to load index if it exists
    if os.path.exists(abs_file_path) and os.path.getsize(abs_file_path) > 0:
        try:
            if FAISS_AVAILABLE:
                test_index = faiss.read_index(abs_file_path)
                diagnostic_info["index_validation"] = {
                    "readable": True,
                    "type": type(test_index).__name__,
                    "dimension": test_index.d,
                    "total_vectors": test_index.ntotal,
                    "is_trained": test_index.is_trained
                }
            else:
                diagnostic_info["index_validation"] = {
                    "readable": False,
                    "error": "FAISS not available"
                }
        except Exception as e:
            diagnostic_info["index_validation"] = {
                "readable": False,
                "error": str(e)
            }
    else:
        diagnostic_info["index_validation"] = {
            "readable": False,
            "reason": "File does not exist or is empty"
        }
    
    return diagnostic_info


def fix_faiss_persistence_issues(file_path: str = "faiss_index", dimension: int = 384) -> dict:
    """Attempt to fix common FAISS persistence issues.
    
    Args:
        file_path: Path for FAISS index
        dimension: Vector dimension for new index creation
        
    Returns:
        Dictionary with fix results
    """
    results = {
        "fixes_applied": [],
        "errors": [],
        "final_status": "unknown"
    }
    
    try:
        # Use configured path if file_path is just a filename
        if not os.path.dirname(file_path):
            abs_file_path = get_configured_index_path(file_path)
        else:
            abs_file_path = os.path.abspath(file_path)
        
        # Fix 1: Ensure parent directory exists
        parent_dir = os.path.dirname(abs_file_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
            results["fixes_applied"].append(f"Created parent directory: {parent_dir}")
        
        # Fix 2: Remove temporary files from failed saves
        temp_file = abs_file_path + ".tmp"
        if os.path.exists(temp_file):
            os.remove(temp_file)
            results["fixes_applied"].append(f"Removed orphaned temporary file: {temp_file}")
        
        # Fix 3: Check if existing file is corrupted and remove if so
        if os.path.exists(abs_file_path):
            try:
                if os.path.getsize(abs_file_path) == 0:
                    os.remove(abs_file_path)
                    results["fixes_applied"].append("Removed empty index file")
                elif FAISS_AVAILABLE:
                    # Try to load the index to validate it
                    test_index = faiss.read_index(abs_file_path)
                    if test_index.d != dimension:
                        os.remove(abs_file_path)
                        results["fixes_applied"].append(f"Removed index with wrong dimension ({test_index.d} != {dimension})")
            except Exception as e:
                # File exists but is corrupted
                os.remove(abs_file_path)
                results["fixes_applied"].append(f"Removed corrupted index file: {e}")
        
        # Fix 4: Create a new valid index if none exists
        if not os.path.exists(abs_file_path) and FAISS_AVAILABLE:
            new_index = create_faiss_index(dimension)
            save_index(new_index, abs_file_path)
            results["fixes_applied"].append(f"Created new FAISS index at {abs_file_path}")
        
        results["final_status"] = "success"
        
    except Exception as e:
        results["errors"].append(str(e))
        results["final_status"] = "failed"
    
    return results
