"""
LTMC Cache Action Module
Redis cache operations with proper async handling for MCP server context
"""

from typing import Dict, Any
from ltms.tools.common.async_utils import run_async_in_context


def cache_action(action: str, **params) -> Dict[str, Any]:
    """Cache operations with real internal Redis implementation.
    
    Actions: health_check, stats, flush, reset
    
    This implementation uses proper async handling to avoid event loop conflicts
    when called from within MCP server context.
    
    Args:
        action: The cache action to perform
        **params: Additional parameters for specific actions
        
    Returns:
        Dictionary with operation result and status
    """
    if not action:
        return {'success': False, 'error': 'Action parameter is required'}
    
    if action == 'health_check':
        return _handle_health_check()
    elif action == 'stats':
        return _handle_stats(params)
    elif action == 'flush': 
        return _handle_flush(params)
    elif action == 'reset':
        return _handle_reset()
    else:
        return {'success': False, 'error': f'Unknown cache action: {action}'}


def _handle_health_check() -> Dict[str, Any]:
    """Handle Redis health check with proper async handling."""
    try:
        async def check_redis():
            """Check Redis connection health and return status."""
            try:
                from ltms.services.redis_service import get_redis_manager
                manager = await get_redis_manager()
                is_healthy = await manager.health_check()
                
                if is_healthy:
                    return {
                        'success': True,
                        'connected': True,
                        'host': manager.host,
                        'port': manager.port,
                        'message': 'Redis connection healthy'
                    }
                else:
                    return {
                        'success': False,
                        'connected': False,
                        'error': 'Redis health check failed'
                    }
                    
            except Exception as e:
                return {
                    'success': False,
                    'connected': False,
                    'error': f'Redis connection failed: {str(e)}'
                }
        
        # Use async utils to handle event loop properly
        return run_async_in_context(check_redis())
        
    except Exception as e:
        return {'success': False, 'error': f'Cache health check failed: {str(e)}'}


def _handle_stats(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle cache statistics retrieval with proper async handling."""
    try:
        cache_type = params.get('cache_type', 'all')
        
        async def get_cache_stats():
            """Retrieve cache statistics from Redis server."""
            try:
                from ltms.services.redis_service import get_cache_service
                cache_service = await get_cache_service()
                stats = await cache_service.get_cache_stats()
                
                result = {
                    'success': True,
                    'cache_type': cache_type,
                    'stats': stats
                }
                
                if cache_type != 'all':
                    # Filter stats by type
                    filtered_stats = {}
                    if cache_type == 'embeddings':
                        filtered_stats['embedding_cache_count'] = stats.get('embedding_cache_count', 0)
                    elif cache_type == 'queries':
                        filtered_stats['query_cache_count'] = stats.get('query_cache_count', 0)
                    
                    result['stats'] = {**stats, 'filtered': filtered_stats}
                
                return result
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Failed to get cache stats: {str(e)}'
                }
        
        # Use async utils to handle event loop properly
        return run_async_in_context(get_cache_stats())
        
    except Exception as e:
        return {'success': False, 'error': f'Cache stats failed: {str(e)}'}


def _handle_flush(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle cache flushing with proper async handling."""
    try:
        cache_type = params.get('cache_type', 'all')
        pattern = params.get('pattern', '*')
        
        async def flush_cache():
            """Flush all cached data from Redis server."""
            try:
                from ltms.services.redis_service import get_cache_service
                cache_service = await get_cache_service()
                
                if cache_type == 'all':
                    # Flush all cache types
                    embedding_count = await cache_service.invalidate_cache(f"{cache_service.EMBEDDING_PREFIX}*")
                    query_count = await cache_service.invalidate_cache(f"{cache_service.QUERY_PREFIX}*")
                    chunk_count = await cache_service.invalidate_cache(f"{cache_service.CHUNK_PREFIX}*")
                    resource_count = await cache_service.invalidate_cache(f"{cache_service.RESOURCE_PREFIX}*")
                    
                    total_deleted = embedding_count + query_count + chunk_count + resource_count
                    
                    return {
                        'success': True,
                        'cache_type': cache_type,
                        'total_keys_deleted': total_deleted,
                        'breakdown': {
                            'embeddings': embedding_count,
                            'queries': query_count,
                            'chunks': chunk_count,
                            'resources': resource_count
                        }
                    }
                    
                elif cache_type == 'embeddings':
                    deleted = await cache_service.invalidate_cache(f"{cache_service.EMBEDDING_PREFIX}*")
                elif cache_type == 'queries':
                    deleted = await cache_service.invalidate_cache(f"{cache_service.QUERY_PREFIX}*")
                else:
                    # Custom pattern
                    deleted = await cache_service.invalidate_cache(pattern)
                
                return {
                    'success': True,
                    'cache_type': cache_type,
                    'pattern': pattern,
                    'keys_deleted': deleted
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Failed to flush cache: {str(e)}'
                }
        
        # Use async utils to handle event loop properly
        return run_async_in_context(flush_cache())
        
    except Exception as e:
        return {'success': False, 'error': f'Cache flush failed: {str(e)}'}


def _handle_reset() -> Dict[str, Any]:
    """Handle Redis reset with proper async handling."""
    try:
        async def reset_redis():
            """Reset Redis server and clear all data."""
            try:
                from ltms.services.redis_service import reset_redis_globals
                await reset_redis_globals()
                
                return {
                    'success': True,
                    'message': 'Redis global instances reset successfully'
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Failed to reset Redis: {str(e)}'
                }
        
        # Use async utils to handle event loop properly
        return run_async_in_context(reset_redis())
        
    except Exception as e:
        return {'success': False, 'error': f'Cache reset failed: {str(e)}'}