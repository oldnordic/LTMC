"""
Basic Redis Tools - Consolidated Redis Management
================================================

1 unified Redis tool for all cache operations.

Consolidated Tool:
- redis_manage - Unified tool for all Redis operations
  * health - Check Redis connection health
  * stats - Get cache statistics
  * set - Set cache value
  * get - Get cache value
  * delete - Delete cache entry
  * clear - Clear cache pattern
"""

import json
import logging
from typing import Dict, Any

# Official MCP SDK import - from research findings
from mcp.server.fastmcp import FastMCP

# Local imports
from ...config.settings import LTMCSettings
from ...services.redis_service import RedisService
from ...utils.validation_utils import sanitize_user_input, validate_content_length
from ...utils.logging_utils import get_tool_logger


def register_basic_redis_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """
    Register consolidated Redis tools with FastMCP server.
    
    Args:
        mcp: FastMCP server instance
        settings: LTMC settings
    """
    logger = get_tool_logger('basic_redis')
    logger.info("Registering consolidated Redis tools")
    
    # Initialize Redis service
    redis_service = RedisService(settings)
    
    @mcp.tool()
    async def redis_manage(
        operation: str,
        key: str = None,
        value: str = None,
        pattern: str = None
    ) -> Dict[str, Any]:
        """
        Unified Redis management tool.
        
        Args:
            operation: Operation to perform ("health", "stats", "set", "get", "delete", "clear")
            key: Cache key (for set/get/delete operations)
            value: Cache value (for set operation)
            pattern: Pattern for clear operation
            
        Returns:
            Dict with operation results and metadata
        """
        try:
            if operation == "health":
                # Check Redis connection health
                logger.debug("Performing Redis health check")
                await redis_service.initialize()
                health_result = await redis_service.health_check()
                
                logger.info(f"Redis health check completed: {health_result.get('status', 'unknown')}")
                
                return {
                    "success": True,
                    "connected": health_result.get("connected", False),
                    "status": health_result.get("status", "unknown"),
                    "latency_ms": health_result.get("latency_ms", 0),
                    "redis_version": health_result.get("version", "unknown"),
                    "memory_usage": health_result.get("memory_usage", {}),
                    "message": f"Redis health: {health_result.get('status', 'unknown')}"
                }
                
            elif operation == "stats":
                # Get Redis cache statistics
                logger.debug("Getting Redis cache statistics")
                stats = await redis_service.get_cache_stats()
                
                logger.info(f"Retrieved Redis cache stats: {stats.get('total_keys', 0)} keys")
                
                return {
                    "success": True,
                    "total_keys": stats.get("total_keys", 0),
                    "memory_usage": stats.get("memory_usage", {}),
                    "hit_rate": stats.get("hit_rate", 0),
                    "miss_rate": stats.get("miss_rate", 0),
                    "evictions": stats.get("evictions", 0),
                    "message": f"Cache stats: {stats.get('total_keys', 0)} keys"
                }
                
            elif operation == "set":
                if not key or not value:
                    return {"success": False, "error": "key and value required for set operation"}
                
                # Set cache value
                logger.debug(f"Setting Redis cache: {key}")
                result = await redis_service.set_cache(key, value)
                
                logger.info(f"Set Redis cache key: {key}")
                return {
                    "success": True,
                    "key": key,
                    "value": value,
                    "message": f"Cache key '{key}' set successfully"
                }
                
            elif operation == "get":
                if not key:
                    return {"success": False, "error": "key required for get operation"}
                
                # Get cache value
                logger.debug(f"Getting Redis cache: {key}")
                value = await redis_service.get_cache(key)
                
                if value is not None:
                    logger.info(f"Retrieved Redis cache key: {key}")
                    return {
                        "success": True,
                        "key": key,
                        "value": value,
                        "message": f"Cache key '{key}' retrieved successfully"
                    }
                else:
                    return {
                        "success": False,
                        "key": key,
                        "message": f"Cache key '{key}' not found"
                    }
                
            elif operation == "delete":
                if not key:
                    return {"success": False, "error": "key required for delete operation"}
                
                # Delete cache key
                logger.debug(f"Deleting Redis cache: {key}")
                result = await redis_service.delete_cache(key)
                
                logger.info(f"Deleted Redis cache key: {key}")
                return {
                    "success": True,
                    "key": key,
                    "message": f"Cache key '{key}' deleted successfully"
                }
                
            elif operation == "clear":
                # Clear cache pattern
                logger.debug(f"Clearing Redis cache pattern: {pattern or 'all'}")
                result = await redis_service.clear_cache(pattern)
                
                logger.info(f"Cleared Redis cache pattern: {pattern or 'all'}")
                return {
                    "success": True,
                    "pattern": pattern or "all",
                    "keys_cleared": result.get("keys_cleared", 0),
                    "message": f"Cache cleared: {result.get('keys_cleared', 0)} keys removed"
                }
                
            else:
                return {
                    "success": False,
                    "error": f"Unknown operation: {operation}. Valid operations: health, stats, set, get, delete, clear"
                }
            
        except Exception as e:
            logger.error(f"Error during Redis operation '{operation}': {e}")
            return {
                "success": False,
                "error": f"Redis operation failed: {str(e)}"
            }
    
    logger.info("✅ Consolidated Redis tools registered successfully")
    logger.info("📊 Tool consolidation: 6 individual tools → 1 unified tool")
    logger.info("🔧 All functionality preserved through operation parameter")