"""FAISS configuration and path management for LTMC."""

import os
import tempfile
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class FAISSConfig:
    """Configuration manager for FAISS vector store paths and settings."""
    
    def __init__(self):
        self._index_path: Optional[str] = None
        self._data_dir: Optional[str] = None
        self._json_config = None
        
    def get_index_path(self, fallback_name: str = "faiss_index") -> str:
        """Get the absolute path for FAISS index storage.
        
        Priority order:
        1. FAISS_INDEX_PATH environment variable (if absolute)
        2. FAISS_INDEX_PATH relative to data directory
        3. Fallback name in data directory
        4. Fallback name in current working directory
        
        Args:
            fallback_name: Default index filename if not configured
            
        Returns:
            Absolute path for FAISS index storage
        """
        if self._index_path:
            return self._index_path
            
        # Check environment variable first
        env_path = os.getenv("FAISS_INDEX_PATH")
        if env_path:
            if os.path.isabs(env_path):
                self._index_path = env_path
            else:
                # Make relative to data directory
                data_dir = self.get_data_directory()
                self._index_path = os.path.join(data_dir, env_path)
        else:
            # Use fallback in data directory
            data_dir = self.get_data_directory()
            self._index_path = os.path.join(data_dir, fallback_name)
        
        # Ensure directory exists
        self._ensure_directory_exists(os.path.dirname(self._index_path))
        
        logger.info(f"FAISS index path resolved to: {self._index_path}")
        return self._index_path
    
    def _get_json_config(self):
        """Get JSON configuration instance (lazy loading)."""
        if self._json_config is None:
            try:
                from ltms.config.json_config_loader import get_config
                self._json_config = get_config()
            except ImportError as e:
                logger.warning(f"Could not load JSON config: {e}")
                self._json_config = None
        return self._json_config

    def get_data_directory(self) -> str:
        """Get the data directory for LTMC storage.
        
        UNIFIED CONFIGURATION APPROACH:
        1. Read from ltmc_config.json (primary source)
        2. Environment variable fallback (for backward compatibility)
        3. Default fallback only if config fails
        
        Returns:
            Absolute path to data directory
        """
        if self._data_dir:
            return self._data_dir
        
        # PRIMARY: Try to get from JSON configuration
        json_config = self._get_json_config()
        if json_config:
            try:
                # Use the database path directory from JSON config
                db_path = json_config.db_path
                if db_path:
                    # Extract directory from database path
                    self._data_dir = os.path.dirname(db_path)
                    logger.info(f"LTMC data directory from JSON config: {self._data_dir}")
                    self._ensure_directory_exists(self._data_dir)
                    return self._data_dir
            except Exception as e:
                logger.warning(f"Could not get data directory from JSON config: {e}")
        
        # FALLBACK: Check environment variable (backward compatibility)
        env_data_dir = os.getenv("LTMC_DATA_DIR")
        if env_data_dir and os.path.isabs(env_data_dir):
            self._data_dir = env_data_dir
            logger.info(f"LTMC data directory from environment: {self._data_dir}")
        else:
            # LAST RESORT: Use ./data relative to current working directory
            cwd_data_dir = os.path.join(os.getcwd(), "data")
            if os.access(os.getcwd(), os.W_OK):
                self._data_dir = cwd_data_dir
                logger.warning(f"LTMC data directory from fallback: {self._data_dir}")
            else:
                # Final fallback to temp directory if current directory not writable
                self._data_dir = os.path.join(tempfile.gettempdir(), "ltmc_data")
                logger.warning(f"Current directory not writable, using temp directory: {self._data_dir}")
        
        # Ensure data directory exists
        self._ensure_directory_exists(self._data_dir)
        
        return self._data_dir
    
    def _ensure_directory_exists(self, directory_path: str) -> None:
        """Ensure a directory exists with proper error handling.
        
        Args:
            directory_path: Path to directory to create
            
        Raises:
            OSError: If directory creation fails
        """
        if not directory_path:
            return
            
        try:
            os.makedirs(directory_path, exist_ok=True)
            
            # Verify directory is writable
            if not os.access(directory_path, os.W_OK):
                raise OSError(f"Directory {directory_path} is not writable")
                
        except OSError as e:
            logger.error(f"Failed to create/access directory {directory_path}: {e}")
            raise
    
    def validate_configuration(self) -> dict:
        """Validate current FAISS configuration.
        
        Returns:
            Dictionary with validation results
        """
        try:
            index_path = self.get_index_path()
            data_dir = self.get_data_directory()
            
            return {
                "valid": True,
                "index_path": index_path,
                "data_directory": data_dir,
                "index_exists": os.path.exists(index_path),
                "data_dir_writable": os.access(data_dir, os.W_OK),
                "index_dir_writable": os.access(os.path.dirname(index_path), os.W_OK)
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "index_path": None,
                "data_directory": None
            }
    
    def reset(self) -> None:
        """Reset cached paths for reconfiguration."""
        self._index_path = None
        self._data_dir = None


# Global configuration instance
faiss_config = FAISSConfig()


def get_configured_index_path(fallback_name: str = "faiss_index") -> str:
    """Get configured FAISS index path.
    
    Args:
        fallback_name: Fallback filename if not configured
        
    Returns:
        Absolute path for FAISS index
    """
    return faiss_config.get_index_path(fallback_name)


def validate_faiss_configuration() -> dict:
    """Validate current FAISS configuration.
    
    Returns:
        Dictionary with validation results
    """
    return faiss_config.validate_configuration()


def reset_faiss_configuration() -> None:
    """Reset FAISS configuration for testing."""
    faiss_config.reset()