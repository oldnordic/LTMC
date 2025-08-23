"""
Management Redis Tools - FastMCP Implementation
===============================================

Redis cache management tools following FastMCP patterns.

Tools implemented:
1. redis_delete_cache - Delete a key from Redis cache
2. redis_clear_cache - Clear Redis cache with optional pattern
"""

import logging
from typing import Dict, Any

# Official MCP SDK import - from research findings
from mcp.server.fastmcp import FastMCP

# Local imports
from ...config.settings import LTMCSettings
from ...services.redis_service import RedisService
from ...utils.validation_utils import sanitize_user_input, validate_content_length
from ...utils.logging_utils import get_tool_logger


def register_management_redis_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """
    Register Redis management tools with FastMCP server.
    
    Args:
        mcp: FastMCP server instance
        settings: LTMC settings
    """
    logger = get_tool_logger('management_redis')
    logger.info("Registering Redis management tools")
    
    # Initialize Redis service
    redis_service = RedisService(settings)
    
    @mcp.tool()
    async def redis_delete_cache(key: str) -> Dict[str, Any]:
        """
        Delete a key from Redis cache.
        
        This tool removes a cached value by its key.
        
        Args:
            key: Cache key to delete
            
        Returns:
            Dict with success status and deletion result
        """
        logger.debug(f"Deleting Redis cache key: {key}")
        
        try:
            # Validate input
            if not key or len(key.strip()) == 0:
                return {
                    "success": False,
                    "error": "Cache key cannot be empty"
                }
            
            key_validation = validate_content_length(key, max_length=250)
            if not key_validation.is_valid:
                return {
                    "success": False,
                    "error": f"Invalid key: {', '.join(key_validation.errors)}"
                }
            
            # Sanitize key
            key_clean = sanitize_user_input(key)
            
            # Delete cache key
            deleted = await redis_service.delete_cache(key_clean)
            
            if deleted:
                logger.info(f"Deleted cache key '{key_clean}'")
                return {
                    "success": True,
                    "key": key_clean,
                    "deleted": True,
                    "message": f"Successfully deleted key '{key_clean}'"
                }
            else:
                logger.debug(f"Cache key '{key_clean}' was not found for deletion")
                return {
                    "success": True,
                    "key": key_clean,
                    "deleted": False,
                    "message": f"Key '{key_clean}' was not found in cache"
                }
                
        except Exception as e:
            logger.error(f"Error deleting Redis cache: {e}")
            return {
                "success": False,
                "error": f"Failed to delete cache: {str(e)}"
            }
    
    @mcp.tool()
    async def redis_clear_cache(pattern: str = None) -> Dict[str, Any]:
        """
        Clear Redis cache with optional pattern.
        
        This tool clears cache keys, either all keys or those matching
        a specific pattern (using Redis glob-style patterns).
        
        Args:
            pattern: Optional pattern to match keys (e.g., "user:*", "session:*")
            
        Returns:
            Dict with success status and number of keys cleared
        """
        logger.debug(f"Clearing Redis cache with pattern: {pattern}")
        
        try:
            # Validate pattern if provided
            if pattern:
                pattern_validation = validate_content_length(pattern, max_length=100)
                if not pattern_validation.is_valid:
                    return {
                        "success": False,
                        "error": f"Invalid pattern: {', '.join(pattern_validation.errors)}"
                    }
                
                # Sanitize pattern
                pattern_clean = sanitize_user_input(pattern)
            else:
                pattern_clean = None
            
            # Clear cache keys
            cleared_count = await redis_service.clear_cache(pattern_clean)
            
            if pattern_clean:
                logger.info(f"Cleared {cleared_count} cache keys matching pattern '{pattern_clean}'")
                message = f"Cleared {cleared_count} keys matching pattern '{pattern_clean}'"
            else:
                logger.info(f"Cleared {cleared_count} cache keys (all keys)")
                message = f"Cleared {cleared_count} keys from cache"
            
            return {
                "success": True,
                "pattern": pattern_clean,
                "cleared_count": cleared_count,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"Error clearing Redis cache: {e}")
            return {
                "success": False,
                "error": f"Failed to clear cache: {str(e)}",
                "cleared_count": 0
            }
    
    logger.info("✅ Redis management tools registered successfully")
    logger.info("  - redis_delete_cache: Delete specific keys")
    logger.info("  - redis_clear_cache: Clear keys by pattern")