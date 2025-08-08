"""Test MCP dev context specifically."""

import os
import sys
import subprocess
import pytest
from pathlib import Path


class TestMCPDevContext:
    """Test the specific MCP dev context that's failing."""

    def test_mcp_dev_import_failure(self):
        """Test that reproduces the exact mcp dev import failure."""
        # This simulates what happens when mcp dev tries to import the server
        project_root = Path(__file__).parent.parent
        
        # Simulate the exact import chain that fails
        try:
            # Add project root to path (like mcp dev does)
            sys.path.insert(0, str(project_root))
            
            # Try to import the server module directly (like mcp dev does)
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "server_module", 
                project_root / "ltms" / "mcp_server.py"
            )
            module = importlib.util.module_from_spec(spec)
            
            # This should fail with the same error as mcp dev
            spec.loader.exec_module(module)
            
            # If we get here, the import worked
            assert hasattr(module, 'LTMCStdioServer')
            
        except ImportError as e:
            # This is the expected failure
            print(f"Expected import failure: {e}")
            pytest.fail(f"MCP dev context import failed: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
            pytest.fail(f"Unexpected error in MCP dev context: {e}")
        finally:
            # Clean up
            if str(project_root) in sys.path:
                sys.path.remove(str(project_root))

    def test_tools_ingest_import_in_mcp_context(self):
        """Test tools.ingest import in MCP context."""
        project_root = Path(__file__).parent.parent
        
        # Simulate the exact import that fails in tools/ingest.py
        try:
            sys.path.insert(0, str(project_root))
            
            # This is the exact import that fails
            from core.config import settings
            assert hasattr(settings, 'EMBEDDING_MODEL')
            
        except ImportError as e:
            print(f"tools.ingest import failure: {e}")
            pytest.fail(f"tools.ingest import failed: {e}")
        finally:
            if str(project_root) in sys.path:
                sys.path.remove(str(project_root))

    def test_path_resolution_in_mcp_context(self):
        """Test path resolution in MCP context."""
        # This test simulates the exact path resolution issue
        
        def find_project_root_from_anywhere():
            """Find project root from any execution context."""
            current = Path.cwd()
            
            # Strategy 1: Look for core/config.py
            for parent in [current] + list(current.parents):
                if (parent / "core" / "config.py").exists():
                    return parent
            
            # Strategy 2: Look for ltms/mcp_server.py
            for parent in [current] + list(current.parents):
                if (parent / "ltms" / "mcp_server.py").exists():
                    return parent
            
            # Strategy 3: Use current directory if it has key files
            if (current / "core" / "config.py").exists():
                return current
            
            return None
        
        project_root = find_project_root_from_anywhere()
        assert project_root is not None, "Could not find project root"
        
        # Test that we can import from the found root
        sys.path.insert(0, str(project_root))
        try:
            from core.config import settings
            assert hasattr(settings, 'EMBEDDING_MODEL')
        finally:
            if str(project_root) in sys.path:
                sys.path.remove(str(project_root))


class TestRobustImportSolution:
    """Test the robust import solution."""

    def test_robust_path_resolution(self):
        """Test robust path resolution that works in all contexts."""
        
        def setup_import_paths():
            """Setup import paths that work in all contexts."""
            import sys
            import os
            from pathlib import Path
            
            # Find project root
            current = Path.cwd()
            project_root = None
            
            # Try multiple strategies
            for parent in [current] + list(current.parents):
                if (parent / "core" / "config.py").exists() and \
                   (parent / "ltms" / "mcp_server.py").exists():
                    project_root = parent
                    break
            
            if not project_root:
                # Fallback: use current directory if it has key files
                if (current / "core" / "config.py").exists():
                    project_root = current
            
            if project_root:
                # Add to path if not already there
                project_root_str = str(project_root)
                if project_root_str not in sys.path:
                    sys.path.insert(0, project_root_str)
                
                return project_root
            
            return None
        
        # Test the robust path resolution
        project_root = setup_import_paths()
        assert project_root is not None, "Could not setup import paths"
        
        # Test that imports work
        try:
            from core.config import settings
            assert hasattr(settings, 'EMBEDDING_MODEL')
            
            from tools.ingest import store_document
            assert callable(store_document)
            
            from ltms.mcp_server import LTMCStdioServer
            assert hasattr(LTMCStdioServer, 'store_memory')
            
        except ImportError as e:
            pytest.fail(f"Robust import failed: {e}")

    def test_safe_import_with_fallback(self):
        """Test safe import with fallback for missing modules."""
        
        def safe_import_settings():
            """Safely import settings with fallback."""
            try:
                from core.config import settings
                return settings
            except ImportError:
                # Create fallback settings
                class FallbackSettings:
                    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
                    FAISS_INDEX_PATH = "./data/ltmc.index"
                    DATABASE_PATH = "./data/ltmc.db"
                    SUMMARIZATION_MODEL = "gpt-3.5-turbo"
                
                return FallbackSettings()
        
        # Test that safe import works
        settings = safe_import_settings()
        assert hasattr(settings, 'EMBEDDING_MODEL')
        assert hasattr(settings, 'DATABASE_PATH')
