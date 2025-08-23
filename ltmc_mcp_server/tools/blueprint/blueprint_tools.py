"""
Blueprint Tools - FastMCP Implementation
========================================

Unified blueprint tools module combining core and query tools.
Maintains all 5 tools while respecting 300-line limit through modularization.

Tools implemented (from unified_mcp_server.py analysis):
1. create_blueprint_from_code - Create Neo4j blueprints from code analysis
2. update_blueprint_structure - Update blueprint structure from code changes
3. validate_blueprint_consistency - Validate blueprint-code consistency
4. query_blueprint_relationships - Query Neo4j blueprint relationships
5. generate_blueprint_documentation - Generate documentation from blueprints
"""

import logging

# Official MCP SDK import - from research findings
from mcp.server.fastmcp import FastMCP

# Local imports
from ...config.settings import LTMCSettings
from ...utils.logging_utils import get_tool_logger

# Import modular tool registration functions
from .core_blueprint_tools import register_core_blueprint_tools
from .query_blueprint_tools import register_query_blueprint_tools


def register_blueprint_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """
    Register all blueprint tools with FastMCP server.
    
    Combines core and query blueprint tools through modular components
    while maintaining unified interface and API compatibility.
    
    Following official FastMCP registration pattern:
    @mcp.tool()
    def tool_name(...) -> ...
    
    Args:
        mcp: FastMCP server instance
        settings: LTMC settings
    """
    logger = get_tool_logger('blueprint')
    logger.info("Registering unified blueprint tools")
    
    # Register core blueprint tools (create, update, validate)
    register_core_blueprint_tools(mcp, settings)
    
    # Register query blueprint tools (query relationships, generate docs)
    register_query_blueprint_tools(mcp, settings)
    
    logger.info("✅ All blueprint tools registered successfully")
    logger.info("  - Core tools: create_blueprint_from_code, update_blueprint_structure, validate_blueprint_consistency")
    logger.info("  - Query tools: query_blueprint_relationships, generate_blueprint_documentation")
    logger.info("  - Modular architecture: 2 components under 300 lines each")
    logger.info("  - Neo4j integration: Full blueprint enhancement capabilities")