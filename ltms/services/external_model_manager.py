#!/usr/bin/env python3
"""
LTMC External Model Manager - Production Implementation

Real implementation for managing external ML dependencies and models.
Handles first-run setup, model downloads, caching, and dependency management
for PyInstaller binary optimization.

MANDATORY: REAL IMPLEMENTATION ONLY
- Real sentence-transformers model downloads
- Real FAISS index creation and management
- Real dependency checking and validation
- Real file system operations with proper error handling
- Real network operations for model acquisition

NO MOCKS, STUBS, OR PLACEHOLDERS - PRODUCTION-READY ONLY!
"""

import os
import sys
import time
import logging
import importlib
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import json
import shutil

logger = logging.getLogger(__name__)


class ExternalModelManager:
    """
    External Model Manager for LTMC ML Dependencies
    
    Manages ML models and dependencies external to the PyInstaller binary
    to keep binary size minimal while providing full ML functionality.
    
    Key responsibilities:
    - Detect first-run scenarios and perform automated setup
    - Download and cache sentence-transformers models
    - Initialize and manage FAISS indices  
    - Check ML dependency availability
    - Provide graceful fallback when dependencies unavailable
    """
    
    def __init__(self, models_dir: Optional[Union[str, Path]] = None, 
                 cache_dir: Optional[Union[str, Path]] = None):
        """
        Initialize External Model Manager with directory configuration.
        
        Args:
            models_dir: Directory for storing downloaded models (default: ~/.ltmc/models)
            cache_dir: Directory for caching temporary files (default: ~/.ltmc/cache)
        """
        # Set up directory paths
        if models_dir is None:
            self.models_dir = Path.home() / ".ltmc" / "models"
        else:
            self.models_dir = Path(models_dir)
            
        if cache_dir is None:
            self.cache_dir = Path.home() / ".ltmc" / "cache"
        else:
            self.cache_dir = Path(cache_dir)
        
        # Create directories
        self._create_directories()
        
        logger.info(f"ExternalModelManager initialized - models: {self.models_dir}, cache: {self.cache_dir}")
    
    def _create_directories(self):
        """Create necessary directories with proper permissions."""
        try:
            self.models_dir.mkdir(parents=True, exist_ok=True)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directories: {self.models_dir}, {self.cache_dir}")
        except Exception as e:
            logger.error(f"Failed to create directories: {e}")
            raise
    
    def check_ml_dependency_availability(self, dependency_name: str) -> bool:
        """
        Check if a specific ML dependency is available for import.
        
        Args:
            dependency_name: Name of the dependency to check
            
        Returns:
            bool: True if dependency is available, False otherwise
        """
        try:
            importlib.import_module(dependency_name)
            logger.debug(f"Dependency available: {dependency_name}")
            return True
        except ImportError:
            logger.debug(f"Dependency not available: {dependency_name}")
            return False
    
    def check_all_ml_dependencies_available(self) -> bool:
        """
        Check if all required ML dependencies are available.
        
        Returns:
            bool: True if all dependencies available, False otherwise
        """
        required_deps = ['torch', 'transformers', 'sentence_transformers', 'faiss']
        
        for dep in required_deps:
            if not self.check_ml_dependency_availability(dep):
                logger.warning(f"Missing ML dependency: {dep}")
                return False
        
        logger.info("All ML dependencies are available")
        return True
    
    def is_first_run(self) -> bool:
        """
        Detect if this is a first-run scenario (no models downloaded).
        
        Returns:
            bool: True if first run, False if models exist
        """
        # Check for existing models
        if not self.models_dir.exists():
            return True
            
        # Check if any model directories exist
        model_dirs = [d for d in self.models_dir.iterdir() if d.is_dir()]
        if len(model_dirs) == 0:
            return True
        
        # Check for core model
        core_model_dir = self.models_dir / "all-MiniLM-L6-v2"
        if not core_model_dir.exists():
            return True
            
        # Check if model has config file
        config_file = core_model_dir / "config.json"
        if not config_file.exists():
            return True
            
        logger.debug("First-run check: models exist, not first run")
        return False
    
    def download_sentence_transformers_model(self, model_name: str) -> Path:
        """
        Download and cache a sentence-transformers model.
        
        Args:
            model_name: Name of the sentence-transformers model
            
        Returns:
            Path: Local path to the downloaded model
            
        Raises:
            ImportError: If sentence-transformers not available
            Exception: If download fails
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            logger.error("sentence-transformers not available for model download")
            raise ImportError("sentence-transformers dependency required for model download") from e
        
        model_path = self.models_dir / model_name
        
        try:
            logger.info(f"Downloading sentence-transformers model: {model_name}")
            start_time = time.time()
            
            # Download model (this will cache it locally)
            model = SentenceTransformer(model_name)
            
            # Save model to our managed directory
            model.save(str(model_path))
            
            download_time = time.time() - start_time
            logger.info(f"Model {model_name} downloaded in {download_time:.2f}s to {model_path}")
            
            return model_path
            
        except Exception as e:
            logger.error(f"Failed to download model {model_name}: {e}")
            # Clean up partial download
            if model_path.exists():
                shutil.rmtree(model_path, ignore_errors=True)
            raise
    
    def load_sentence_transformers_model(self, model_path: Union[str, Path]):
        """
        Load a sentence-transformers model from local path.
        
        Args:
            model_path: Path to the model directory
            
        Returns:
            SentenceTransformer: Loaded model instance
            
        Raises:
            ImportError: If sentence-transformers not available
            Exception: If model loading fails
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            logger.error("sentence-transformers not available for model loading")
            raise ImportError("sentence-transformers dependency required for model loading") from e
        
        try:
            model_path = Path(model_path)
            logger.info(f"Loading sentence-transformers model from {model_path}")
            
            model = SentenceTransformer(str(model_path))
            logger.info(f"Model loaded successfully from {model_path}")
            
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model from {model_path}: {e}")
            raise
    
    def initialize_faiss_index(self, dimension: int, index_name: str):
        """
        Initialize a FAISS index for vector similarity search.
        
        Args:
            dimension: Dimension of vectors to be indexed
            index_name: Name for the index (used for caching)
            
        Returns:
            faiss.Index: Initialized FAISS index
            
        Raises:
            ImportError: If faiss not available
            Exception: If index creation fails
        """
        try:
            import faiss
        except ImportError as e:
            logger.error("faiss not available for index creation")
            raise ImportError("faiss dependency required for index creation") from e
        
        try:
            logger.info(f"Initializing FAISS index: {index_name} (dimension: {dimension})")
            
            # Create flat L2 index for exact search
            index = faiss.IndexFlatL2(dimension)
            
            logger.info(f"FAISS index {index_name} initialized successfully")
            return index
            
        except Exception as e:
            logger.error(f"Failed to create FAISS index {index_name}: {e}")
            raise
    
    def save_faiss_index(self, index, index_name: str) -> Path:
        """
        Save a FAISS index to disk.
        
        Args:
            index: FAISS index to save
            index_name: Name for the saved index file
            
        Returns:
            Path: Path to the saved index file
            
        Raises:
            ImportError: If faiss not available
            Exception: If saving fails
        """
        try:
            import faiss
        except ImportError as e:
            logger.error("faiss not available for index saving")
            raise ImportError("faiss dependency required for index saving") from e
        
        try:
            index_path = self.cache_dir / f"{index_name}.faiss"
            
            logger.info(f"Saving FAISS index to {index_path}")
            faiss.write_index(index, str(index_path))
            
            logger.info(f"FAISS index saved successfully to {index_path}")
            return index_path
            
        except Exception as e:
            logger.error(f"Failed to save FAISS index {index_name}: {e}")
            raise
    
    def load_faiss_index(self, index_path: Union[str, Path]):
        """
        Load a FAISS index from disk.
        
        Args:
            index_path: Path to the saved index file
            
        Returns:
            faiss.Index: Loaded FAISS index
            
        Raises:
            ImportError: If faiss not available
            Exception: If loading fails
        """
        try:
            import faiss
        except ImportError as e:
            logger.error("faiss not available for index loading")
            raise ImportError("faiss dependency required for index loading") from e
        
        try:
            index_path = Path(index_path)
            logger.info(f"Loading FAISS index from {index_path}")
            
            index = faiss.read_index(str(index_path))
            
            logger.info(f"FAISS index loaded successfully from {index_path}")
            return index
            
        except Exception as e:
            logger.error(f"Failed to load FAISS index from {index_path}: {e}")
            raise
    
    def perform_first_run_setup(self) -> Dict[str, Any]:
        """
        Perform complete first-run setup with all ML components.
        
        Downloads core models, initializes indices, and prepares the system
        for full ML functionality. Designed to run during MCP server startup.
        
        Returns:
            Dict[str, Any]: Setup results with success status and details
        """
        setup_start_time = time.time()
        
        try:
            logger.info("Starting first-run setup for LTMC ML dependencies")
            
            # Check if ML dependencies are available
            if not self.check_all_ml_dependencies_available():
                return {
                    'success': False,
                    'error': 'ML dependencies not available - install torch, transformers, sentence-transformers, faiss',
                    'setup_time_seconds': time.time() - setup_start_time
                }
            
            models_downloaded = []
            
            # Download core sentence-transformers model
            try:
                core_model_name = "all-MiniLM-L6-v2"
                model_path = self.download_sentence_transformers_model(core_model_name)
                models_downloaded.append(core_model_name)
                logger.info(f"Core model downloaded: {core_model_name}")
            except Exception as e:
                logger.error(f"Failed to download core model: {e}")
                return {
                    'success': False,
                    'error': f'Failed to download core model: {e}',
                    'setup_time_seconds': time.time() - setup_start_time
                }
            
            # Initialize FAISS index
            faiss_initialized = False
            try:
                dimension = 384  # all-MiniLM-L6-v2 dimension
                test_index = self.initialize_faiss_index(dimension, "ltmc_main")
                index_path = self.save_faiss_index(test_index, "ltmc_main")
                faiss_initialized = True
                logger.info(f"FAISS index initialized and saved to {index_path}")
            except Exception as e:
                logger.warning(f"FAISS initialization failed (non-critical): {e}")
                # FAISS failure is non-critical for basic functionality
            
            # Create setup completion marker
            setup_marker = self.models_dir / ".ltmc_setup_complete"
            setup_info = {
                'setup_completed_at': time.time(),
                'models_downloaded': models_downloaded,
                'faiss_initialized': faiss_initialized,
                'setup_version': '1.0.0'
            }
            
            with open(setup_marker, 'w') as f:
                json.dump(setup_info, f, indent=2)
            
            setup_time = time.time() - setup_start_time
            
            logger.info(f"First-run setup completed successfully in {setup_time:.2f}s")
            
            return {
                'success': True,
                'models_downloaded': models_downloaded,
                'faiss_initialized': faiss_initialized,
                'setup_time_seconds': setup_time,
                'setup_info': setup_info
            }
            
        except Exception as e:
            setup_time = time.time() - setup_start_time
            logger.error(f"First-run setup failed after {setup_time:.2f}s: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'setup_time_seconds': setup_time
            }


# Convenience functions for integration with existing LTMC services
def get_external_model_manager() -> ExternalModelManager:
    """Get singleton instance of ExternalModelManager."""
    global _model_manager_instance
    if '_model_manager_instance' not in globals():
        _model_manager_instance = ExternalModelManager()
    return _model_manager_instance


def initialize_ml_dependencies_for_ltmc() -> Dict[str, Any]:
    """
    Initialize ML dependencies for LTMC server startup.
    
    Designed to be called during create_mcp_server() for first-run setup.
    
    Returns:
        Dict[str, Any]: Initialization results
    """
    try:
        logger.info("Initializing ML dependencies for LTMC")
        
        manager = get_external_model_manager()
        
        # Check if this is first run
        if manager.is_first_run():
            logger.info("First run detected - performing ML setup")
            result = manager.perform_first_run_setup()
            
            if result['success']:
                logger.info(f"ML setup completed - downloaded {len(result['models_downloaded'])} models")
            else:
                logger.warning(f"ML setup failed: {result['error']}")
            
            return result
        else:
            logger.info("ML models already initialized - skipping setup")
            return {
                'success': True,
                'first_run': False,
                'models_available': True
            }
            
    except Exception as e:
        logger.error(f"ML dependency initialization failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'first_run': None
        }