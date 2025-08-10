"""
Redis Cache Tools - FastMCP Implementation
==========================================

Unified Redis cache tools module combining basic and management tools.
Maintains all 6 tools while respecting 300-line limit through modularization.

Tools implemented (from unified_mcp_server.py analysis):
1. redis_health_check - Check Redis connection health
2. redis_cache_stats - Get Redis cache statistics  
3. redis_set_cache - Set a value in Redis cache
4. redis_get_cache - Get a value from Redis cache
5. redis_delete_cache - Delete a key from Redis cache
6. redis_clear_cache - Clear Redis cache with optional pattern
"""

import logging

# Official MCP SDK import - from research findings
from mcp.server.fastmcp import FastMCP

# Local imports
from config.settings import LTMCSettings
from utils.logging_utils import get_tool_logger

# Import modular tool registration functions
from .basic_redis_tools import register_basic_redis_tools
from .management_redis_tools import register_management_redis_tools


def register_redis_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """
    Register all Redis cache tools with FastMCP server.
    
    Combines basic and management Redis tools through modular components
    while maintaining unified interface and API compatibility.
    
    Following official FastMCP registration pattern:
    @mcp.tool()
    def tool_name(...) -> ...
    
    Args:
        mcp: FastMCP server instance
        settings: LTMC settings
    """
    logger = get_tool_logger('redis')
    logger.info("Registering unified Redis cache tools")
    
    # Register basic Redis tools (health_check, cache_stats, set_cache, get_cache)
    register_basic_redis_tools(mcp, settings)
    
    # Register management Redis tools (delete_cache, clear_cache)
    register_management_redis_tools(mcp, settings)
    
    logger.info("✅ All Redis cache tools registered successfully")
    logger.info("  - Basic tools: redis_health_check, redis_cache_stats, redis_set_cache, redis_get_cache")
    logger.info("  - Management tools: redis_delete_cache, redis_clear_cache")
    logger.info("  - Modular architecture: 2 components under 300 lines each")