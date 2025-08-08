"""Test import issues and path resolution for LTMC MCP Server."""

import os
import sys
import pytest
from pathlib import Path


class TestImportIssues:
    """Test import path resolution issues."""

    def test_project_root_detection(self):
        """Test that we can detect the project root from different contexts."""
        # Test from project root
        project_root = Path(__file__).parent.parent
        assert project_root.exists()
        assert (project_root / "core" / "config.py").exists()
        assert (project_root / "ltms" / "mcp_server.py").exists()

    def test_core_config_import_from_root(self):
        """Test importing core.config from project root."""
        # Add project root to path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        try:
            from core.config import settings
            assert hasattr(settings, 'EMBEDDING_MODEL')
            assert hasattr(settings, 'DATABASE_PATH')
        except ImportError as e:
            pytest.fail(f"Failed to import core.config from root: {e}")
        finally:
            # Clean up
            if str(project_root) in sys.path:
                sys.path.remove(str(project_root))

    def test_core_config_import_from_ltms(self):
        """Test importing core.config from ltms directory."""
        # Simulate running from ltms directory
        project_root = Path(__file__).parent.parent
        ltms_dir = project_root / "ltms"
        
        # Change to ltms directory
        original_cwd = os.getcwd()
        os.chdir(ltms_dir)
        
        try:
            # Add project root to path
            sys.path.insert(0, str(project_root))
            
            from core.config import settings
            assert hasattr(settings, 'EMBEDDING_MODEL')
            assert hasattr(settings, 'DATABASE_PATH')
        except ImportError as e:
            pytest.fail(f"Failed to import core.config from ltms: {e}")
        finally:
            # Clean up
            os.chdir(original_cwd)
            if str(project_root) in sys.path:
                sys.path.remove(str(project_root))

    def test_tools_ingest_import(self):
        """Test that tools.ingest can import its dependencies."""
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        try:
            # This should work without import errors
            from tools.ingest import store_document, query_documents
            assert callable(store_document)
            assert callable(query_documents)
        except ImportError as e:
            pytest.fail(f"Failed to import tools.ingest: {e}")
        finally:
            if str(project_root) in sys.path:
                sys.path.remove(str(project_root))

    def test_mcp_server_import(self):
        """Test that mcp_server can import its dependencies."""
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        try:
            # This should work without import errors
            from ltms.mcp_server import LTMCStdioServer
            assert hasattr(LTMCStdioServer, 'store_memory')
            assert hasattr(LTMCStdioServer, 'retrieve_memory')
        except ImportError as e:
            pytest.fail(f"Failed to import mcp_server: {e}")
        finally:
            if str(project_root) in sys.path:
                sys.path.remove(str(project_root))


class TestPathResolution:
    """Test path resolution utilities."""

    def test_find_project_root(self):
        """Test finding project root from different locations."""
        from pathlib import Path
        
        def find_project_root():
            """Find project root by looking for key files."""
            current = Path.cwd()
            
            # Walk up the directory tree
            for parent in [current] + list(current.parents):
                if (parent / "core" / "config.py").exists() and \
                   (parent / "ltms" / "mcp_server.py").exists():
                    return parent
            
            return None
        
        project_root = find_project_root()
        assert project_root is not None
        assert (project_root / "core" / "config.py").exists()
        assert (project_root / "ltms" / "mcp_server.py").exists()

    def test_safe_import(self):
        """Test safe import with fallback."""
        def safe_import(module_name, fallback=None):
            """Safely import module with fallback."""
            try:
                return __import__(module_name)
            except ImportError:
                if fallback:
                    return fallback()
                raise
        
        # Test successful import
        os_module = safe_import('os')
        assert os_module is not None
        
        # Test fallback import
        def fallback_func():
            return "fallback_value"
        
        result = safe_import('nonexistent_module', fallback_func)
        assert result == "fallback_value"


class TestExecutionContexts:
    """Test different execution contexts."""

    def test_start_script_context(self):
        """Test imports work in start script context."""
        # Simulate start script: cd to project root, then run
        project_root = Path(__file__).parent.parent
        original_cwd = os.getcwd()
        
        try:
            os.chdir(project_root)
            sys.path.insert(0, str(project_root))
            
            # Test that we can import everything
            from core.config import settings
            from tools.ingest import store_document
            from ltms.mcp_server import LTMCStdioServer
            
            assert hasattr(settings, 'EMBEDDING_MODEL')
            assert callable(store_document)
            assert hasattr(LTMCStdioServer, 'store_memory')
            
        except ImportError as e:
            pytest.fail(f"Start script context failed: {e}")
        finally:
            os.chdir(original_cwd)
            if str(project_root) in sys.path:
                sys.path.remove(str(project_root))

    def test_mcp_dev_context(self):
        """Test imports work in mcp dev context."""
        # Simulate mcp dev: run from current directory
        project_root = Path(__file__).parent.parent
        original_cwd = os.getcwd()
        
        try:
            # Don't change directory, just add to path
            sys.path.insert(0, str(project_root))
            
            # Test that we can import everything
            from core.config import settings
            from tools.ingest import store_document
            from ltms.mcp_server import LTMCStdioServer
            
            assert hasattr(settings, 'EMBEDDING_MODEL')
            assert callable(store_document)
            assert hasattr(LTMCStdioServer, 'store_memory')
            
        except ImportError as e:
            pytest.fail(f"MCP dev context failed: {e}")
        finally:
            if str(project_root) in sys.path:
                sys.path.remove(str(project_root))
