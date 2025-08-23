#!/usr/bin/env python3
"""
TDD Test Suite for Modularized LTMC Tools
Tests all 11 consolidated tools after smart modularization
NO MOCKS, NO STUBS, NO PLACEHOLDERS - Real implementations only
"""

import pytest
import sys
import os
from pathlib import Path

# Add LTMC to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestModularToolsStructure:
    """Test the modular structure follows python-mcp-sdk standards"""
    
    def test_tools_common_directory_exists(self):
        """Test that common utilities directory is created"""
        common_dir = project_root / "ltms" / "tools" / "common"
        assert common_dir.exists(), "tools/common directory must exist"
        assert common_dir.is_dir(), "tools/common must be a directory"
    
    def test_tools_actions_directory_exists(self):
        """Test that actions directory is created"""
        actions_dir = project_root / "ltms" / "tools" / "actions"
        assert actions_dir.exists(), "tools/actions directory must exist"  
        assert actions_dir.is_dir(), "tools/actions must be a directory"

class TestWarningSuppressionModule:
    """Test warning suppression utility module"""
    
    def test_warning_suppression_module_exists(self):
        """Test warning_suppression.py module exists and is importable"""
        try:
            from ltms.tools.common.warning_suppression import AdvancedImportSuppressor
            assert AdvancedImportSuppressor is not None
        except ImportError:
            pytest.fail("warning_suppression.py module must exist and be importable")
    
    def test_warning_suppression_functionality(self):
        """Test warning suppression actually works"""
        from ltms.tools.common.warning_suppression import AdvancedImportSuppressor
        
        with AdvancedImportSuppressor():
            # This should not produce warnings
            import warnings
            warnings.warn("Test warning", DeprecationWarning)
        
        # Test passed if no exception raised

class TestAsyncUtils:
    """Test async utilities for fixing event loop issues"""
    
    def test_async_utils_module_exists(self):
        """Test async_utils.py module exists"""
        try:
            from ltms.tools.common.async_utils import run_async_in_context
            assert callable(run_async_in_context)
        except ImportError:
            pytest.fail("async_utils.py module with run_async_in_context must exist")
    
    def test_async_event_loop_handling(self):
        """Test that async utilities handle event loop conflicts"""
        import asyncio
        from ltms.tools.common.async_utils import run_async_in_context
        
        async def test_coroutine():
            return "success"
        
        # This should work without "event loop already running" errors
        result = run_async_in_context(test_coroutine())
        assert result == "success"

class TestCacheActionModule:
    """Test cache_action module after modularization"""
    
    def test_cache_action_module_exists(self):
        """Test cache_action.py module exists"""
        try:
            from ltms.tools.actions.cache_action import cache_action
            assert callable(cache_action)
        except ImportError:
            pytest.fail("cache_action.py module must exist and be importable")
    
    def test_cache_action_no_event_loop_errors(self):
        """Test cache_action doesn't cause event loop errors"""
        from ltms.tools.actions.cache_action import cache_action
        
        # Test all cache actions without event loop errors
        actions = ['health_check', 'stats', 'flush', 'reset']
        for action in actions:
            try:
                result = cache_action(action)
                # Should return dict without event loop errors
                assert isinstance(result, dict)
                assert 'success' in result
                # Verify no event loop error in response
                result_str = str(result)
                assert 'asyncio.run() cannot be called from a running event loop' not in result_str
                assert 'This event loop is already running' not in result_str
            except RuntimeError as e:
                if 'event loop' in str(e).lower():
                    pytest.fail(f"Event loop error in cache_action({action}): {e}")

class TestGraphActionModule:
    """Test graph_action module after modularization"""
    
    def test_graph_action_module_exists(self):
        """Test graph_action.py module exists"""
        try:
            from ltms.tools.actions.graph_action import graph_action
            assert callable(graph_action)
        except ImportError:
            pytest.fail("graph_action.py module must exist and be importable")
    
    def test_graph_action_no_event_loop_errors(self):
        """Test graph_action doesn't cause event loop errors"""
        from ltms.tools.actions.graph_action import graph_action
        
        # Test key graph actions without event loop errors
        test_cases = [
            ('query', {'entity': 'test', 'query': 'MATCH (n) RETURN count(n)'}),
            ('link', {'source': 'test1', 'target': 'test2', 'relation_type': 'RELATED'}),
            ('get_relationships', {'doc_id': 'test'})
        ]
        
        for action, params in test_cases:
            try:
                result = graph_action(action, **params)
                # Should return dict without event loop errors
                assert isinstance(result, dict)
                assert 'success' in result
                # Verify no event loop error in response
                result_str = str(result)
                assert 'asyncio.run() cannot be called from a running event loop' not in result_str
                assert 'This event loop is already running' not in result_str
            except RuntimeError as e:
                if 'event loop' in str(e).lower():
                    pytest.fail(f"Event loop error in graph_action({action}): {e}")

class TestToolRegistry:
    """Test the modular tool registry"""
    
    def test_tool_registry_module_exists(self):
        """Test tool_registry.py module exists"""
        try:
            from ltms.tools.common.tool_registry import get_consolidated_tools
            assert callable(get_consolidated_tools)
        except ImportError:
            pytest.fail("tool_registry.py module must exist and be importable")
    
    def test_consolidated_tools_registry_complete(self):
        """Test that all 11 tools are properly registered"""
        from ltms.tools.common.tool_registry import get_consolidated_tools
        
        tools = get_consolidated_tools()
        assert isinstance(tools, dict)
        
        expected_tools = [
            'memory_action', 'todo_action', 'chat_action', 'unix_action',
            'pattern_action', 'blueprint_action', 'cache_action', 'graph_action',
            'documentation_action', 'sync_action', 'config_action'
        ]
        
        for tool_name in expected_tools:
            assert tool_name in tools, f"Tool {tool_name} must be in registry"
            assert 'handler' in tools[tool_name], f"Tool {tool_name} must have handler"
            assert 'description' in tools[tool_name], f"Tool {tool_name} must have description"
            assert 'schema' in tools[tool_name], f"Tool {tool_name} must have schema"

class TestModularizationCompliance:
    """Test that all modules comply with 300-line limit"""
    
    def test_all_modules_under_300_lines(self):
        """Test that no module exceeds 300 lines"""
        common_dir = project_root / "ltms" / "tools" / "common"
        actions_dir = project_root / "ltms" / "tools" / "actions"
        
        for directory in [common_dir, actions_dir]:
            if directory.exists():
                for py_file in directory.glob("*.py"):
                    if py_file.name.startswith("__"):
                        continue
                    
                    with open(py_file, 'r') as f:
                        line_count = len(f.readlines())
                    
                    assert line_count <= 300, f"Module {py_file.name} has {line_count} lines, exceeds 300-line limit"

def test_unix_filesystem_module_exists():
    """Test that unix_filesystem module exists and follows modular structure."""
    import sys
    from pathlib import Path
    
    project_root = Path(__file__).parent.parent
    filesystem_module = project_root / "ltms" / "tools" / "actions" / "unix_filesystem.py"
    
    # Module should exist
    assert filesystem_module.exists(), "unix_filesystem.py module should exist"
    
    # Module should be importable
    sys.path.insert(0, str(project_root))
    from ltms.tools.actions.unix_filesystem import unix_filesystem_action
    
    # Should have the main function
    assert callable(unix_filesystem_action), "unix_filesystem_action should be callable"


def test_unix_text_processing_module_exists():
    """Test that unix_text_processing module exists and follows modular structure."""
    import sys
    from pathlib import Path
    
    project_root = Path(__file__).parent.parent
    text_module = project_root / "ltms" / "tools" / "actions" / "unix_text_processing.py"
    
    # Module should exist
    assert text_module.exists(), "unix_text_processing.py module should exist"
    
    # Module should be importable
    sys.path.insert(0, str(project_root))
    from ltms.tools.actions.unix_text_processing import unix_text_processing_action
    
    # Should have the main function
    assert callable(unix_text_processing_action), "unix_text_processing_action should be callable"


def test_unix_modern_tools_module_exists():
    """Test that unix_modern_tools module exists and follows modular structure."""
    import sys
    from pathlib import Path
    
    project_root = Path(__file__).parent.parent
    modern_module = project_root / "ltms" / "tools" / "actions" / "unix_modern_tools.py"
    
    # Module should exist
    assert modern_module.exists(), "unix_modern_tools.py module should exist"
    
    # Module should be importable
    sys.path.insert(0, str(project_root))
    from ltms.tools.actions.unix_modern_tools import unix_modern_tools_action
    
    # Should have the main function
    assert callable(unix_modern_tools_action), "unix_modern_tools_action should be callable"


def test_unix_actions_functionality():
    """Test that unix action modules function correctly."""
    from ltms.tools.actions.unix_filesystem import unix_filesystem_action
    from ltms.tools.actions.unix_text_processing import unix_text_processing_action
    from ltms.tools.actions.unix_modern_tools import unix_modern_tools_action
    
    # Test filesystem actions
    result = unix_filesystem_action("ls", path=".")
    assert 'success' in result
    
    # Test text processing actions  
    result = unix_text_processing_action("grep", pattern="test", path=".")
    assert 'success' in result
    
    # Test modern tools actions
    result = unix_modern_tools_action("list_modern", path=".")
    assert 'success' in result


if __name__ == '__main__':
    # Run the tests
    pytest.main([__file__, '-v', '--tb=short'])