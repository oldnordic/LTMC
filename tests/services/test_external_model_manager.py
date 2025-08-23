#!/usr/bin/env python3
"""
LTMC External Model Manager Tests - TDD Implementation

MANDATORY: REAL TESTING ONLY
- Tests actual model downloads (no mocks)
- Tests real sentence-transformers initialization
- Tests real FAISS index creation
- Tests real file system operations
- Tests real network operations with external dependencies

NO MOCKS - REAL IMPLEMENTATION TESTING ONLY!
Following LTMC quality standards for external ML dependency management.
"""

import os
import sys
import tempfile
import shutil
import pytest
from pathlib import Path
from unittest import TestCase
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class TestExternalModelManagerTDD(TestCase):
    """
    TDD Tests for ExternalModelManager
    
    Tests the complete external model management system with REAL dependencies:
    - Actual model downloads and caching
    - Real sentence-transformers model initialization
    - Real FAISS index creation and storage
    - Real dependency checking and installation validation
    - Real directory structure creation and management
    """
    
    def setUp(self):
        """Set up test environment with temporary directories."""
        # Create temporary directory for each test
        self.temp_dir = tempfile.mkdtemp(prefix="ltmc_test_models_")
        self.models_dir = Path(self.temp_dir) / "models"
        self.cache_dir = Path(self.temp_dir) / "cache"
        
        logger.info(f"Test setup: temp_dir={self.temp_dir}")
    
    def tearDown(self):
        """Clean up temporary test directories."""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"Test cleanup: removed {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")
    
    def test_external_model_manager_initialization_creates_directories(self):
        """Test that ExternalModelManager creates necessary directories on initialization."""
        # This test will fail until we implement ExternalModelManager
        from ltms.services.external_model_manager import ExternalModelManager
        
        # Initialize manager with custom directories
        manager = ExternalModelManager(
            models_dir=self.models_dir,
            cache_dir=self.cache_dir
        )
        
        # Verify directories were created
        assert self.models_dir.exists(), f"Models directory not created: {self.models_dir}"
        assert self.cache_dir.exists(), f"Cache directory not created: {self.cache_dir}"
        
        # Verify directories have correct permissions
        assert self.models_dir.is_dir(), "Models path is not a directory"
        assert self.cache_dir.is_dir(), "Cache path is not a directory"
        
        # Verify manager properties
        assert manager.models_dir == self.models_dir
        assert manager.cache_dir == self.cache_dir
    
    def test_external_model_manager_detects_ml_dependencies_availability(self):
        """Test that ExternalModelManager correctly detects ML dependency availability."""
        from ltms.services.external_model_manager import ExternalModelManager
        
        manager = ExternalModelManager(
            models_dir=self.models_dir,
            cache_dir=self.cache_dir
        )
        
        # Test ML dependency detection
        has_torch = manager.check_ml_dependency_availability('torch')
        has_transformers = manager.check_ml_dependency_availability('transformers')
        has_sentence_transformers = manager.check_ml_dependency_availability('sentence_transformers')
        has_faiss = manager.check_ml_dependency_availability('faiss')
        
        # Verify return types
        assert isinstance(has_torch, bool), "torch availability check must return bool"
        assert isinstance(has_transformers, bool), "transformers availability check must return bool"
        assert isinstance(has_sentence_transformers, bool), "sentence_transformers availability check must return bool"
        assert isinstance(has_faiss, bool), "faiss availability check must return bool"
        
        # Test comprehensive dependency check
        all_available = manager.check_all_ml_dependencies_available()
        assert isinstance(all_available, bool), "comprehensive dependency check must return bool"
    
    def test_external_model_manager_detects_first_run_correctly(self):
        """Test that ExternalModelManager correctly detects first-run scenarios."""
        from ltms.services.external_model_manager import ExternalModelManager
        
        manager = ExternalModelManager(
            models_dir=self.models_dir,
            cache_dir=self.cache_dir
        )
        
        # Test first run detection on empty directories
        is_first_run = manager.is_first_run()
        assert is_first_run is True, "Should detect first run with empty model directory"
        
        # Create a model file and test again
        model_file = self.models_dir / "all-MiniLM-L6-v2" / "config.json"
        model_file.parent.mkdir(parents=True)
        model_file.write_text('{"model_type": "sentence-transformers"}')
        
        is_first_run_after = manager.is_first_run()
        assert is_first_run_after is False, "Should not detect first run when models exist"
    
    def test_external_model_manager_downloads_sentence_transformers_model(self):
        """Test that ExternalModelManager downloads and caches sentence-transformers models."""
        from ltms.services.external_model_manager import ExternalModelManager
        
        manager = ExternalModelManager(
            models_dir=self.models_dir,
            cache_dir=self.cache_dir
        )
        
        # Test model download (this is a real network operation)
        model_name = "all-MiniLM-L6-v2"
        model_path = manager.download_sentence_transformers_model(model_name)
        
        # Verify model was downloaded
        assert isinstance(model_path, (str, Path)), "Model path must be string or Path"
        model_path = Path(model_path)
        assert model_path.exists(), f"Model path does not exist: {model_path}"
        assert model_path.is_dir(), f"Model path is not a directory: {model_path}"
        
        # Verify model files exist
        config_file = model_path / "config.json"
        assert config_file.exists(), f"Model config file missing: {config_file}"
        
        # Verify model can be loaded
        loaded_model = manager.load_sentence_transformers_model(model_path)
        assert loaded_model is not None, "Failed to load downloaded model"
        assert hasattr(loaded_model, 'encode'), "Loaded model missing encode method"
        
        # Test model functionality
        test_text = "This is a test sentence for embedding validation."
        embedding = loaded_model.encode(test_text)
        
        # Verify embedding properties
        import numpy as np
        assert isinstance(embedding, np.ndarray), "Embedding must be numpy array"
        assert embedding.ndim == 1, "Embedding must be 1-dimensional"
        assert embedding.shape[0] == 384, "all-MiniLM-L6-v2 should produce 384-dimensional embeddings"
        assert not np.isnan(embedding).any(), "Embedding contains NaN values"
        assert not np.isinf(embedding).any(), "Embedding contains infinite values"
    
    def test_external_model_manager_initializes_faiss_index(self):
        """Test that ExternalModelManager initializes and manages FAISS indices."""
        from ltms.services.external_model_manager import ExternalModelManager
        
        manager = ExternalModelManager(
            models_dir=self.models_dir,
            cache_dir=self.cache_dir
        )
        
        # Test FAISS index initialization
        dimension = 384  # all-MiniLM-L6-v2 dimension
        index_name = "test_index"
        
        faiss_index = manager.initialize_faiss_index(dimension, index_name)
        
        # Verify FAISS index properties
        assert faiss_index is not None, "FAISS index should be created"
        assert hasattr(faiss_index, 'add'), "FAISS index missing add method"
        assert hasattr(faiss_index, 'search'), "FAISS index missing search method"
        assert faiss_index.d == dimension, f"FAISS index dimension mismatch: expected {dimension}"
        
        # Test index saving and loading
        index_path = manager.save_faiss_index(faiss_index, index_name)
        assert isinstance(index_path, (str, Path)), "Index path must be string or Path"
        assert Path(index_path).exists(), f"Saved index file does not exist: {index_path}"
        
        # Test loading saved index
        loaded_index = manager.load_faiss_index(index_path)
        assert loaded_index is not None, "Failed to load saved FAISS index"
        assert loaded_index.d == dimension, "Loaded index dimension mismatch"
    
    def test_external_model_manager_performs_complete_first_run_setup(self):
        """Test that ExternalModelManager performs complete first-run setup with all components."""
        from ltms.services.external_model_manager import ExternalModelManager
        
        manager = ExternalModelManager(
            models_dir=self.models_dir,
            cache_dir=self.cache_dir
        )
        
        # Test complete first-run setup
        setup_result = manager.perform_first_run_setup()
        
        # Verify setup result
        assert isinstance(setup_result, dict), "Setup result must be a dictionary"
        assert 'success' in setup_result, "Setup result missing success field"
        assert 'models_downloaded' in setup_result, "Setup result missing models_downloaded field"
        assert 'faiss_initialized' in setup_result, "Setup result missing faiss_initialized field"
        assert 'setup_time_seconds' in setup_result, "Setup result missing setup_time_seconds field"
        
        # Verify setup was successful
        assert setup_result['success'] is True, f"Setup failed: {setup_result}"
        
        # Verify models were downloaded
        models_downloaded = setup_result['models_downloaded']
        assert isinstance(models_downloaded, list), "models_downloaded must be a list"
        assert len(models_downloaded) > 0, "No models were downloaded"
        assert "all-MiniLM-L6-v2" in models_downloaded, "Core sentence transformer not downloaded"
        
        # Verify FAISS was initialized
        assert setup_result['faiss_initialized'] is True, "FAISS initialization failed"
        
        # Verify setup completed in reasonable time (< 5 minutes)
        setup_time = setup_result['setup_time_seconds']
        assert isinstance(setup_time, (int, float)), "Setup time must be numeric"
        assert setup_time > 0, "Setup time must be positive"
        assert setup_time < 300, f"Setup took too long: {setup_time} seconds"
        
        # Verify first-run flag is now false
        is_first_run_after = manager.is_first_run()
        assert is_first_run_after is False, "First-run flag should be false after setup"
    
    def test_external_model_manager_graceful_fallback_on_setup_failure(self):
        """Test that ExternalModelManager handles setup failures gracefully."""
        from ltms.services.external_model_manager import ExternalModelManager
        
        # Create manager with invalid/restricted directory to trigger failure
        invalid_dir = Path("/root/restricted_ltmc_models")  # Likely to cause permission error
        
        manager = ExternalModelManager(
            models_dir=invalid_dir,
            cache_dir=invalid_dir
        )
        
        # Test setup with expected failure
        setup_result = manager.perform_first_run_setup()
        
        # Verify graceful failure handling
        assert isinstance(setup_result, dict), "Failed setup result must still be a dictionary"
        assert 'success' in setup_result, "Failed setup result missing success field"
        assert 'error' in setup_result, "Failed setup result missing error field"
        
        # Verify failure is properly reported
        assert setup_result['success'] is False, "Setup should report failure"
        assert isinstance(setup_result['error'], str), "Error message must be a string"
        assert len(setup_result['error']) > 0, "Error message must not be empty"
        
        # Verify manager can still check dependencies even after setup failure
        dependency_check = manager.check_all_ml_dependencies_available()
        assert isinstance(dependency_check, bool), "Dependency check must work after setup failure"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    pytest.main([__file__, "-v"])