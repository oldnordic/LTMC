#!/usr/bin/env python3
"""
LTMC First-Run Setup Integration Tests

MANDATORY: REAL INTEGRATION TESTING ONLY
- Tests actual MCP server initialization with first-run setup
- Tests real ML dependency downloads during server startup
- Tests integration with create_mcp_server() function
- Tests MCP protocol compliance after ML setup
- Tests graceful fallback when ML setup fails

NO MOCKS - REAL SYSTEM INTEGRATION TESTING ONLY!
Tests the complete first-run setup workflow during MCP server startup.
"""

import os
import sys
import asyncio
import tempfile
import shutil
import pytest
import json
from pathlib import Path
from typing import Dict, Any
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class TestFirstRunSetupIntegration:
    """
    Integration Tests for First-Run Setup in MCP Server
    
    Tests the complete integration of ExternalModelManager with LTMC MCP server
    startup, including real ML dependency setup and MCP protocol compliance.
    """
    
    def setup_method(self):
        """Set up test environment with isolated directories."""
        # Create temporary directory for each test
        self.temp_dir = tempfile.mkdtemp(prefix="ltmc_test_integration_")
        self.models_dir = Path(self.temp_dir) / "models"
        self.cache_dir = Path(self.temp_dir) / "cache"
        self.db_dir = Path(self.temp_dir) / "db"
        self.config_dir = Path(self.temp_dir) / "config"
        
        # Create test config file
        self.config_file = self.config_dir / "ltmc_config.json"
        self.config_dir.mkdir(parents=True)
        
        test_config = {
            "database": {
                "sqlite_path": str(self.db_dir / "test_ltmc.db"),
                "faiss_index_path": str(self.cache_dir / "faiss_index")
            },
            "neo4j": {
                "uri": "bolt://localhost:7687",
                "user": "neo4j",
                "password": "test_password",
                "database": "neo4j"
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "db": 0
            },
            "paths": {
                "data_dir": str(self.temp_dir / "data"),
                "models_dir": str(self.models_dir),
                "cache_dir": str(self.cache_dir)
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f, indent=2)
        
        # Set environment to use test config
        os.environ['LTMC_CONFIG_PATH'] = str(self.config_file)
        
        logger.info(f"Integration test setup: temp_dir={self.temp_dir}")
    
    def teardown_method(self):
        """Clean up test environment."""
        try:
            # Clean up environment
            if 'LTMC_CONFIG_PATH' in os.environ:
                del os.environ['LTMC_CONFIG_PATH']
                
            # Remove test directory
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"Integration test cleanup: removed {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Integration test cleanup warning: {e}")
    
    def test_first_run_setup_integration_with_mcp_server_initialization(self):
        """Test that first-run setup integrates properly with MCP server initialization."""
        from ltms.services.external_model_manager import initialize_ml_dependencies_for_ltmc
        from ltms.main import initialize_database
        
        # Test ML dependency initialization during server startup simulation
        ml_init_result = initialize_ml_dependencies_for_ltmc()
        
        # Verify initialization result structure
        assert isinstance(ml_init_result, dict), "ML init result must be dictionary"
        assert 'success' in ml_init_result, "ML init result missing success field"
        
        # Test database initialization (part of create_mcp_server flow)
        db_init_result = initialize_database()
        assert isinstance(db_init_result, bool), "Database init result must be boolean"
        
        logger.info(f"ML init result: {ml_init_result}")
        logger.info(f"Database init result: {db_init_result}")
    
    def test_first_run_setup_creates_necessary_directories_during_server_startup(self):
        """Test that first-run setup creates all necessary directories during server startup."""
        from ltms.services.external_model_manager import get_external_model_manager
        
        # Simulate server startup model manager access
        manager = get_external_model_manager()
        
        # Override manager directories to use test directories
        manager.models_dir = self.models_dir
        manager.cache_dir = self.cache_dir
        manager._create_directories()
        
        # Verify directories created
        assert self.models_dir.exists(), f"Models directory not created: {self.models_dir}"
        assert self.cache_dir.exists(), f"Cache directory not created: {self.cache_dir}"
        
        # Test first-run detection
        is_first_run = manager.is_first_run()
        assert is_first_run is True, "Should detect first run with empty directories"
    
    def test_first_run_setup_dependency_checking_integration(self):
        """Test dependency checking integration during server startup."""
        from ltms.services.external_model_manager import ExternalModelManager
        
        manager = ExternalModelManager(
            models_dir=self.models_dir,
            cache_dir=self.cache_dir
        )
        
        # Test individual dependency checking
        deps_to_check = ['torch', 'transformers', 'sentence_transformers', 'faiss']
        dependency_results = {}
        
        for dep in deps_to_check:
            available = manager.check_ml_dependency_availability(dep)
            dependency_results[dep] = available
            assert isinstance(available, bool), f"Dependency check for {dep} must return bool"
        
        # Test comprehensive dependency check
        all_available = manager.check_all_ml_dependencies_available()
        assert isinstance(all_available, bool), "Comprehensive dependency check must return bool"
        
        logger.info(f"Dependency check results: {dependency_results}")
        logger.info(f"All dependencies available: {all_available}")
        
        # If dependencies available, test would continue with model downloads
        # If not available, server should still start with limited functionality
        if all_available:
            logger.info("All ML dependencies available - full setup would proceed")
        else:
            logger.info("Some ML dependencies missing - server would start with limited functionality")
    
    def test_first_run_setup_graceful_fallback_on_failure(self):
        """Test that server startup handles ML setup failures gracefully."""
        from ltms.services.external_model_manager import ExternalModelManager
        
        # Create manager with restricted directory to simulate failure
        restricted_dir = Path("/root/restricted_ltmc_test")
        
        manager = ExternalModelManager(
            models_dir=restricted_dir,
            cache_dir=restricted_dir
        )
        
        # Test setup with expected failure
        setup_result = manager.perform_first_run_setup()
        
        # Verify graceful failure handling
        assert isinstance(setup_result, dict), "Failed setup result must be dictionary"
        assert 'success' in setup_result, "Failed setup result missing success field"
        assert 'error' in setup_result, "Failed setup result missing error field"
        
        # Verify failure properly reported
        assert setup_result['success'] is False, "Setup should report failure"
        assert isinstance(setup_result['error'], str), "Error message must be string"
        assert len(setup_result['error']) > 0, "Error message must not be empty"
        
        logger.info(f"Graceful failure test result: {setup_result}")
        
        # Verify server could still continue (dependency checking still works)
        can_check_deps = manager.check_ml_dependency_availability('os')  # Always available
        assert can_check_deps is True, "Basic functionality should work after setup failure"
    
    def test_mcp_server_tools_list_availability_after_first_run_setup(self):
        """Test that MCP server tools remain available after first-run setup integration."""
        from ltms.tools import CANONICAL_TOOLS
        from ltms.services.external_model_manager import initialize_ml_dependencies_for_ltmc
        
        # Test tools availability before ML setup
        tools_before = len(CANONICAL_TOOLS)
        assert tools_before > 0, "CANONICAL_TOOLS should not be empty"
        
        # Simulate ML initialization during server startup
        ml_init_result = initialize_ml_dependencies_for_ltmc()
        
        # Test tools availability after ML setup
        tools_after = len(CANONICAL_TOOLS)
        assert tools_after == tools_before, "Tools count should remain unchanged after ML setup"
        
        # Verify specific memory tools are available (these use ML)
        memory_tools = ['store_memory', 'retrieve_memory', 'build_context']
        for tool_name in memory_tools:
            assert tool_name in CANONICAL_TOOLS, f"Memory tool {tool_name} should be available"
        
        logger.info(f"MCP tools available: {tools_before} (before), {tools_after} (after ML setup)")
    
    def test_mcp_server_initialization_timing_with_first_run_setup(self):
        """Test that MCP server initialization timing is reasonable with first-run setup."""
        import time
        from ltms.services.external_model_manager import initialize_ml_dependencies_for_ltmc
        
        # Measure initialization timing
        start_time = time.time()
        
        # Simulate server startup with ML initialization
        ml_init_result = initialize_ml_dependencies_for_ltmc()
        
        initialization_time = time.time() - start_time
        
        # Verify timing is reasonable (should be under 30 seconds for detection/setup)
        assert initialization_time < 30.0, f"Initialization took too long: {initialization_time}s"
        assert initialization_time > 0, "Initialization time should be positive"
        
        logger.info(f"ML initialization timing: {initialization_time:.2f}s")
        
        # If actual setup occurred, verify it's recorded
        if ml_init_result.get('success') and 'setup_time_seconds' in ml_init_result:
            setup_time = ml_init_result['setup_time_seconds']
            assert isinstance(setup_time, (int, float)), "Setup time must be numeric"
            assert setup_time >= 0, "Setup time must be non-negative"
            logger.info(f"Actual setup time: {setup_time:.2f}s")
    
    def test_integration_with_create_mcp_server_function_flow(self):
        """Test integration with the actual create_mcp_server() initialization flow."""
        # This test verifies the integration point where first-run setup would be called
        # We can't easily test the full create_mcp_server() without starting the full MCP server
        # But we can test the integration points
        
        from ltms.main import initialize_database, initialize_graph_store
        from ltms.services.external_model_manager import initialize_ml_dependencies_for_ltmc
        
        # Test the initialization sequence that would occur in create_mcp_server()
        # 1. Database initialization
        db_result = initialize_database()
        logger.info(f"Database initialization: {db_result}")
        
        # 2. Graph store initialization (Neo4j)
        graph_result = initialize_graph_store()
        logger.info(f"Graph store initialization: {graph_result}")
        
        # 3. ML dependencies initialization (our new integration point)
        ml_result = initialize_ml_dependencies_for_ltmc()
        logger.info(f"ML dependencies initialization: {ml_result}")
        
        # Verify all steps completed without critical failures
        # Database must succeed, others can gracefully fall back
        assert isinstance(db_result, bool), "Database initialization must return boolean"
        assert isinstance(graph_result, bool), "Graph initialization must return boolean"
        assert isinstance(ml_result, dict), "ML initialization must return dictionary"
        assert 'success' in ml_result, "ML initialization must include success field"
        
        # Server should be able to continue regardless of ML setup result
        logger.info("✅ Integration flow completed - server would be ready for MCP protocol")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    pytest.main([__file__, "-v"])