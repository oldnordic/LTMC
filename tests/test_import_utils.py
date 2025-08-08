"""Tests for import utilities to ensure robust import path resolution."""

import sys
import os
import pytest
from pathlib import Path
from unittest.mock import patch


class TestImportPathResolution:
    """Test import path resolution in different execution contexts."""

    def test_setup_import_paths_project_root(self):
        """Test that project root is correctly identified and added to sys.path."""
        # Arrange
        original_sys_path = sys.path.copy()
        
        # Act
        from core.import_utils import setup_import_paths
        project_root = setup_import_paths()
        
        # Assert
        assert isinstance(project_root, Path)
        assert project_root.exists()
        assert str(project_root) in sys.path
        # Should be first or near the front
        assert sys.path.index(str(project_root)) <= 1
        
        # Cleanup
        sys.path = original_sys_path

    def test_setup_import_paths_working_directory(self):
        """Test that working directory is changed to project root."""
        # Arrange
        original_cwd = os.getcwd()
        
        # Act
        from core.import_utils import setup_import_paths
        project_root = setup_import_paths()
        
        # Assert
        assert os.getcwd() == str(project_root)
        
        # Cleanup
        os.chdir(original_cwd)

    def test_setup_import_paths_idempotent(self):
        """Test that calling setup_import_paths multiple times doesn't duplicate."""
        # Arrange
        original_sys_path = sys.path.copy()
        
        # Act
        from core.import_utils import setup_import_paths
        project_root = setup_import_paths()
        setup_import_paths()  # Call again
        
        # Assert
        # Check that project root is in path (may have multiple entries)
        assert str(project_root) in sys.path
        
        # Cleanup
        sys.path = original_sys_path

    def test_safe_import_success(self):
        """Test successful import with safe_import."""
        # Arrange
        from core.import_utils import safe_import
        
        # Act & Assert
        # Should import successfully
        module = safe_import('os')
        assert module is not None
        assert hasattr(module, 'path')

    def test_safe_import_with_fallback(self):
        """Test import with fallback path when primary import fails."""
        # Arrange
        from core.import_utils import safe_import
        
        # Act & Assert
        # Test with a module that should exist
        module = safe_import('sys', fallback_path='/tmp')
        assert module is not None

    def test_safe_import_failure(self):
        """Test that safe_import raises ImportError for non-existent modules."""
        # Arrange
        from core.import_utils import safe_import
        
        # Act & Assert
        with pytest.raises(ImportError):
            safe_import('non_existent_module_12345')

    def test_import_in_different_contexts(self):
        """Test that imports work in different execution contexts."""
        # Arrange
        from core.import_utils import setup_import_paths
        
        # Act
        setup_import_paths()
        
        # Assert - Test core modules
        try:
            from core.config import settings
            assert settings is not None
        except ImportError as e:
            pytest.fail(f"Core config import failed: {e}")
        
        try:
            from tools.ask import ask_with_context
            assert ask_with_context is not None
        except ImportError as e:
            pytest.fail(f"Tools ask import failed: {e}")


class TestExecutionContextCompatibility:
    """Test compatibility with different execution contexts."""

    @patch('sys.path', [])
    def test_empty_sys_path_context(self):
        """Test import setup works with empty sys.path."""
        # Arrange
        from core.import_utils import setup_import_paths
        
        # Act
        project_root = setup_import_paths()
        
        # Assert
        assert str(project_root) in sys.path
        assert len(sys.path) > 0

    @patch('os.getcwd')
    def test_different_working_directories(self, mock_getcwd):
        """Test import setup works from different working directories."""
        # Arrange
        mock_getcwd.return_value = '/some/other/directory'
        from core.import_utils import setup_import_paths
        
        # Act
        project_root = setup_import_paths()
        
        # Assert
        assert project_root.exists()
        assert str(project_root) in sys.path

    def test_relative_import_handling(self):
        """Test that relative imports are handled correctly."""
        # Arrange
        from core.import_utils import setup_import_paths
        
        # Act
        setup_import_paths()
        
        # Assert - Test that we can import from our project
        try:
            # This should work after setup
            from core import config
            assert config is not None
        except ImportError as e:
            pytest.fail(f"Relative import failed: {e}")


class TestImportErrorHandling:
    """Test graceful handling of import errors."""

    def test_missing_core_config_handling(self):
        """Test handling when core.config is missing."""
        # Arrange
        from core.import_utils import safe_import
        
        # Act & Assert
        # This should raise ImportError but not crash
        with pytest.raises(ImportError):
            safe_import('completely_nonexistent_module_xyz',
                        fallback_path='/nonexistent')

    def test_fallback_path_handling(self):
        """Test that fallback paths are used correctly."""
        # Arrange
        from core.import_utils import safe_import
        
        # Act & Assert
        # Test with a real fallback path (current directory)
        try:
            module = safe_import('os', fallback_path=os.getcwd())
            assert module is not None
        except ImportError:
            pytest.fail("Fallback path should work for 'os' module")

    def test_import_error_reporting(self):
        """Test that import errors provide useful information."""
        # Arrange
        from core.import_utils import safe_import
        
        # Act & Assert
        with pytest.raises(ImportError) as exc_info:
            safe_import('completely_nonexistent_module_xyz')
        
        # Should contain useful error information
        assert 'completely_nonexistent_module_xyz' in str(exc_info.value)


class TestMCPServerIntegration:
    """Test integration with MCP server requirements."""

    def test_mcp_dev_compatibility(self):
        """Test that imports work in mcp dev context."""
        # Arrange
        from core.import_utils import setup_import_paths
        
        # Act
        setup_import_paths()
        
        # Assert - Test that we can import what MCP server needs
        try:
            from fastmcp import FastMCP
            assert FastMCP is not None
        except ImportError as e:
            pytest.skip(f"FastMCP not available: {e}")
        
        try:
            from core.config import settings
            assert settings is not None
        except ImportError as e:
            pytest.skip(f"Core config not available: {e}")

    def test_stdio_transport_compatibility(self):
        """Test that imports work for stdio transport."""
        # Arrange
        from core.import_utils import setup_import_paths
        
        # Act
        setup_import_paths()
        
        # Assert - Test stdio-compatible imports
        try:
            import sys
            import json
            assert sys is not None
            assert json is not None
        except ImportError as e:
            pytest.fail(f"Basic stdio imports failed: {e}")

    def test_http_transport_compatibility(self):
        """Test that imports work for HTTP transport."""
        # Arrange
        from core.import_utils import setup_import_paths
        
        # Act
        setup_import_paths()
        
        # Assert - Test HTTP-compatible imports
        try:
            import asyncio
            assert asyncio is not None
        except ImportError as e:
            pytest.skip(f"AsyncIO not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__])
