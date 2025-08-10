"""
Basic Redis Tools - FastMCP Implementation
==========================================

Basic Redis operations tools following FastMCP patterns.

Tools implemented:
1. redis_health_check - Check Redis connection health
2. redis_cache_stats - Get Redis cache statistics
3. redis_set_cache - Set a value in Redis cache
4. redis_get_cache - Get a value from Redis cache
"""

import json
import logging
from typing import Dict, Any, Optional

# Official MCP SDK import - from research findings
from mcp.server.fastmcp import FastMCP

# Local imports
from config.settings import LTMCSettings
from services.redis_service import RedisService
from utils.validation_utils import sanitize_user_input, validate_content_length
from utils.logging_utils import get_tool_logger


def register_basic_redis_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """
    Register basic Redis tools with FastMCP server.
    
    Args:
        mcp: FastMCP server instance
        settings: LTMC settings
    """
    logger = get_tool_logger('basic_redis')
    logger.info("Registering basic Redis tools")
    
    # Initialize Redis service
    redis_service = RedisService(settings)
    
    @mcp.tool()
    async def redis_health_check() -> Dict[str, Any]:
        """
        Check Redis connection health.
        
        This tool checks the connectivity and health status of the Redis
        cache server, including latency and basic operations.
        
        Returns:
            Dict with connection status, latency, and health metrics
        """
        logger.debug("Performing Redis health check")
        
        try:
            # Initialize Redis connection if needed
            await redis_service.initialize()
            
            # Perform health check
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
            
        except Exception as e:
            logger.error(f"Error during Redis health check: {e}")
            return {
                "success": False,
                "connected": False,
                "error": f"Redis health check failed: {str(e)}",
                "status": "error"
            }
    
    @mcp.tool()
    async def redis_cache_stats() -> Dict[str, Any]:
        """
        Get Redis cache statistics.
        
        This tool retrieves comprehensive statistics about Redis cache
        usage, performance, and storage metrics.
        
        Returns:
            Dict with cache statistics, hit rates, and performance metrics
        """
        logger.debug("Getting Redis cache statistics")
        
        try:
            # Get comprehensive cache statistics
            stats = await redis_service.get_cache_stats()
            
            logger.info(f"Retrieved Redis cache stats: {stats.get('total_keys', 0)} keys")
            
            return {
                "success": True,
                "statistics": stats,
                "cache_health": "good" if stats.get("hit_rate", 0) > 0.8 else "needs_attention",
                "recommendations": [
                    "Monitor hit rate for cache efficiency",
                    "Consider increasing TTL for frequently accessed data",
                    "Review memory usage patterns"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting Redis cache stats: {e}")
            return {
                "success": False,
                "error": f"Failed to get cache statistics: {str(e)}",
                "statistics": {}
            }
    
    @mcp.tool()
    async def redis_set_cache(
        key: str,
        value: Any,
        ttl: int = None
    ) -> Dict[str, Any]:
        """
        Set a value in Redis cache.
        
        This tool stores a value in the Redis cache with an optional
        time-to-live (TTL) expiration.
        
        Args:
            key: Cache key to store the value under
            value: Value to store (will be JSON serialized)
            ttl: Optional time-to-live in seconds
            
        Returns:
            Dict with success status and cache operation details
        """
        logger.debug(f"Setting Redis cache key: {key}, TTL: {ttl}")
        
        try:
            # Validate inputs
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
            
            # Validate TTL if provided
            if ttl is not None:
                if not isinstance(ttl, int) or ttl < 1 or ttl > 86400 * 30:  # Max 30 days
                    return {
                        "success": False,
                        "error": "TTL must be an integer between 1 and 2592000 (30 days)"
                    }
            
            # Sanitize key
            key_clean = sanitize_user_input(key)
            
            # Serialize value to JSON
            try:
                value_json = json.dumps(value)
            except (TypeError, ValueError) as e:
                return {
                    "success": False,
                    "error": f"Value cannot be JSON serialized: {str(e)}"
                }
            
            # Set cache value
            success = await redis_service.set_cache(key_clean, value_json, ttl)
            
            if success:
                logger.info(f"Set cache key '{key_clean}' with TTL: {ttl}")
                return {
                    "success": True,
                    "key": key_clean,
                    "ttl": ttl,
                    "value_size": len(value_json),
                    "message": f"Successfully cached value for key '{key_clean}'"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to set cache value",
                    "key": key_clean
                }
                
        except Exception as e:
            logger.error(f"Error setting Redis cache: {e}")
            return {
                "success": False,
                "error": f"Failed to set cache: {str(e)}"
            }
    
    @mcp.tool()
    async def redis_get_cache(key: str) -> Dict[str, Any]:
        """
        Get a value from Redis cache.
        
        This tool retrieves a cached value by its key, automatically
        deserializing JSON data.
        
        Args:
            key: Cache key to retrieve
            
        Returns:
            Dict with success status, value (if found), and metadata
        """
        logger.debug(f"Getting Redis cache key: {key}")
        
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
            
            # Get cache value
            value_json = await redis_service.get_cache(key_clean)
            
            if value_json is not None:
                # Try to deserialize JSON
                try:
                    value = json.loads(value_json)
                    logger.info(f"Retrieved cache key '{key_clean}' (JSON)")
                    return {
                        "success": True,
                        "key": key_clean,
                        "value": value,
                        "found": True,
                        "value_type": "json",
                        "value_size": len(value_json)
                    }
                except json.JSONDecodeError:
                    # Return raw string if not valid JSON
                    logger.info(f"Retrieved cache key '{key_clean}' (string)")
                    return {
                        "success": True,
                        "key": key_clean,
                        "value": value_json,
                        "found": True,
                        "value_type": "string",
                        "value_size": len(value_json)
                    }
            else:
                logger.debug(f"Cache key '{key_clean}' not found")
                return {
                    "success": True,
                    "key": key_clean,
                    "value": None,
                    "found": False,
                    "message": f"Key '{key_clean}' not found in cache"
                }
                
        except Exception as e:
            logger.error(f"Error getting Redis cache: {e}")
            return {
                "success": False,
                "error": f"Failed to get cache: {str(e)}",
                "found": False
            }
    
    logger.info("✅ Basic Redis tools registered successfully")
    logger.info("  - redis_health_check: Check connection health")
    logger.info("  - redis_cache_stats: Get cache statistics")
    logger.info("  - redis_set_cache: Store cached values")
    logger.info("  - redis_get_cache: Retrieve cached values")