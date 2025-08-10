"""
Code Pattern Tools - FastMCP Implementation
==========================================

Unified code pattern tools module combining basic and analysis tools.
Maintains all 4 tools while respecting 300-line limit through modularization.

Tools implemented (from unified_mcp_server.py analysis):
1. log_code_attempt - Log a code attempt for pattern analysis
2. get_code_patterns - Get code patterns matching a query
3. analyze_code_patterns - Analyze code patterns for insights
4. get_code_statistics - Get comprehensive code pattern statistics
"""

import logging

# Official MCP SDK import - from research findings
from mcp.server.fastmcp import FastMCP

# Local imports
from config.settings import LTMCSettings
from utils.logging_utils import get_tool_logger

# Import modular tool registration functions
from .basic_pattern_tools import register_basic_pattern_tools
from .analysis_pattern_tools import register_analysis_pattern_tools


def register_code_pattern_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """
    Register all code pattern tools with FastMCP server.
    
    Combines basic and analysis pattern tools through modular components
    while maintaining unified interface and API compatibility.
    
    Following official FastMCP registration pattern:
    @mcp.tool()
    def tool_name(...) -> ...
    
    Args:
        mcp: FastMCP server instance
        settings: LTMC settings
    """
    logger = get_tool_logger('code_patterns')
    logger.info("Registering unified code pattern tools")
    
    # Register basic pattern tools (log_code_attempt, get_code_patterns)
    register_basic_pattern_tools(mcp, settings)
    
    # Register analysis pattern tools (analyze_code_patterns, get_code_statistics)  
    register_analysis_pattern_tools(mcp, settings)
    
    logger.info("✅ All code pattern tools registered successfully")
    logger.info("  - Basic tools: log_code_attempt, get_code_patterns")
    logger.info("  - Analysis tools: analyze_code_patterns, get_code_statistics")
    logger.info("  - Modular architecture: 2 components under 300 lines each")