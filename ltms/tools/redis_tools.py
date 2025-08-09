"""Redis cache management tools for LTMC MCP server."""

from typing import Dict, Any

# Import async implementation functions directly from redis_service
from ltms.services.redis_service import get_redis_manager, get_cache_service


async def redis_cache_stats_handler() -> Dict[str, Any]:
    """Get Redis cache statistics and health status."""
    try:
        cache_service = await get_cache_service()
        stats = await cache_service.get_cache_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        return {"success": False, "error": str(e), "stats": {"connected": False, "error": str(e)}}


async def redis_flush_cache_handler(cache_type: str = "all") -> Dict[str, Any]:
    """Flush Redis cache entries."""
    try:
        cache_service = await get_cache_service()
        
        if cache_type == "all":
            # Flush all LTMC cache entries
            embedding_count = await cache_service.invalidate_cache("ltmc:embedding:*")
            query_count = await cache_service.invalidate_cache("ltmc:query:*")
            chunk_count = await cache_service.invalidate_cache("ltmc:chunk:*")
            resource_count = await cache_service.invalidate_cache("ltmc:resource:*")
            
            return {
                "success": True,
                "result": {
                    "flushed_embeddings": embedding_count,
                    "flushed_queries": query_count,
                    "flushed_chunks": chunk_count,
                    "flushed_resources": resource_count,
                    "total_flushed": embedding_count + query_count + chunk_count + resource_count
                }
            }
        elif cache_type == "embeddings":
            count = await cache_service.invalidate_cache("ltmc:embedding:*")
            return {"success": True, "result": {"flushed_embeddings": count}}
        elif cache_type == "queries":
            count = await cache_service.invalidate_cache("ltmc:query:*")
            return {"success": True, "result": {"flushed_queries": count}}
        else:
            return {"success": False, "error": f"Unknown cache_type: {cache_type}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


async def redis_health_check_handler() -> Dict[str, Any]:
    """Check Redis connection health and connectivity."""
    try:
        redis_manager = await get_redis_manager()
        is_healthy = await redis_manager.health_check()
        
        return {
            "success": True,
            "health": {
                "healthy": is_healthy,
                "connected": redis_manager.is_connected,
                "host": redis_manager.host,
                "port": redis_manager.port,
                "db": redis_manager.db
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "health": {
                "healthy": False,
                "connected": False,
                "error": str(e)
            }
        }


# Tool definitions for MCP protocol
REDIS_TOOLS = {
    "redis_cache_stats": {
        "handler": redis_cache_stats_handler,
        "description": "Get Redis cache statistics and performance metrics",
        "schema": {
            "type": "object",
            "properties": {}
        }
    },
    
    "redis_flush_cache": {
        "handler": redis_flush_cache_handler,
        "description": "Flush Redis cache entries by type",
        "schema": {
            "type": "object",
            "properties": {
                "cache_type": {
                    "type": "string",
                    "description": "Type of cache to flush",
                    "enum": ["all", "embeddings", "queries"],
                    "default": "all"
                }
            }
        }
    },
    
    "redis_health_check": {
        "handler": redis_health_check_handler,
        "description": "Check Redis connection health and connectivity status",
        "schema": {
            "type": "object",
            "properties": {}
        }
    }
}