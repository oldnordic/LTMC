#!/usr/bin/env python3
"""
TDD Tests for main.py Compatibility with Consolidated System

Tests that main.py can import and work with the current consolidated 
11-powertool system instead of the old 68-tool structure.
"""

import pytest
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class TestMainPyCompatibility:
    """Test main.py compatibility with consolidated system."""
    
    def test_consolidated_powertools_available(self):
        """Test that consolidated powertools can be imported."""
        from ltms.tools.consolidated import (
            memory_action, todo_action, chat_action, unix_action, 
            pattern_action, blueprint_action, cache_action, 
            graph_action, documentation_action, sync_action, config_action
        )
        
        # Verify all 11 powertools exist
        powertools = [
            memory_action, todo_action, chat_action, unix_action,
            pattern_action, blueprint_action, cache_action,
            graph_action, documentation_action, sync_action, config_action
        ]
        
        assert len(powertools) == 11
        for tool in powertools:
            assert callable(tool)
    
    def test_main_py_imports_successfully(self):
        """Test that main.py can import without errors after modification."""
        # This will fail initially - main.py needs to be modified
        try:
            # Import the module without running main()
            import ltms.main
            assert hasattr(ltms.main, 'main')
            assert callable(ltms.main.main)
        except ImportError as e:
            pytest.fail(f"main.py import failed: {e}")
    
    def test_database_schema_import(self):
        """Test that database schema can be imported."""
        from ltms.database.schema import create_tables
        assert callable(create_tables)
    
    def test_config_system_import(self):
        """Test that config system can be imported."""
        from ltms.config import get_config
        config = get_config()
        assert hasattr(config, 'get_db_path')
        assert callable(config.get_db_path)
    
    def test_mcp_sdk_imports(self):
        """Test that python-mcp-sdk imports work."""
        from mcp.server.lowlevel.server import Server as MCPServer
        from mcp.server.stdio import stdio_server
        from mcp.server.models import InitializationOptions
        from mcp.types import ServerCapabilities, Tool, TextContent, ToolsCapability
        
        # Verify classes exist
        assert MCPServer
        assert stdio_server
        assert InitializationOptions
        assert ServerCapabilities
        assert Tool
        assert TextContent
        assert ToolsCapability
    
    def test_consolidated_tools_structure(self):
        """Test that consolidated tools have proper structure for MCP."""
        from ltms.tools.consolidated import CONSOLIDATED_TOOLS
        
        assert isinstance(CONSOLIDATED_TOOLS, dict)
        assert len(CONSOLIDATED_TOOLS) == 11
        
        # Each tool should have handler and schema
        for tool_name, tool_def in CONSOLIDATED_TOOLS.items():
            assert isinstance(tool_def, dict)
            assert 'handler' in tool_def
            assert 'description' in tool_def
            assert 'schema' in tool_def
            assert callable(tool_def['handler'])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])