"""
Universal Search Integration for LTMC Memory Tools.
Extends memory retrieval with cross-storage-type universal semantic search.

File: ltms/tools/memory/universal_search_integration.py
Lines: ~290 (under 300 limit)
Purpose: Integrate universal search into existing memory tools
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class UniversalSearchIntegration:
    """
    Integration layer between LTMC memory tools and universal semantic search.
    Provides backward-compatible enhancements to existing memory retrieval.
    """
    
    def __init__(self, test_mode: bool = False):
        """Initialize universal search integration."""
        self.test_mode = test_mode
        self._universal_search = None
        self._enhanced_storage = None
        
        # Cache for performance optimization
        self._search_cache = {}
        self._cache_ttl = 300  # 5 minutes
        
        logger.info(f"UniversalSearchIntegration initialized (test_mode={test_mode})")
    
    @property
    def universal_search(self):
        """Lazy-loaded universal search interface."""
        if self._universal_search is None:
            try:
                from ltms.search.universal_semantic_search import get_universal_search
                self._universal_search = get_universal_search(test_mode=self.test_mode)
            except ImportError as e:
                logger.error(f"Failed to import universal search: {e}")
                self._universal_search = None
        return self._universal_search
    
    @property
    def enhanced_storage(self):
        """Lazy-loaded enhanced storage interface."""
        if self._enhanced_storage is None:
            try:
                from ltms.storage.enhanced_unified_storage import get_enhanced_unified_storage
                self._enhanced_storage = get_enhanced_unified_storage(test_mode=self.test_mode)
            except ImportError as e:
                logger.error(f"Failed to import enhanced storage: {e}")
                self._enhanced_storage = None
        return self._enhanced_storage
    
    def is_available(self) -> bool:
        """Check if universal search integration is available."""
        return (self.universal_search is not None and 
                self.enhanced_storage is not None)
    
    async def enhanced_retrieve(self, query: str, conversation_id: str = None,
                              top_k: int = 10, storage_types: List[str] = None,
                              include_cross_storage: bool = False) -> Dict[str, Any]:
        """
        Enhanced retrieve with optional cross-storage universal search.
        
        Args:
            query: Search query text
            conversation_id: Optional conversation filtering
            top_k: Number of results to return
            storage_types: Optional list of storage types to search
            include_cross_storage: Enable universal search across all storage types
            
        Returns:
            Enhanced search results with universal context
        """
        try:
            if include_cross_storage and self.is_available():
                # Use universal search for cross-storage results
                return await self._universal_cross_storage_search(
                    query, top_k, storage_types, conversation_id
                )
            else:
                # Fallback to atomic memory integration (existing behavior)
                return await self._fallback_atomic_search(query, conversation_id, top_k)
                
        except Exception as e:
            logger.error(f"Enhanced retrieve failed: {e}")
            return {
                'success': False,
                'error': f'Enhanced retrieve error: {str(e)}',
                'fallback_available': True
            }
    
    async def _universal_cross_storage_search(self, query: str, top_k: int,
                                            storage_types: List[str] = None,
                                            conversation_id: str = None) -> Dict[str, Any]:
        """Execute universal search across multiple storage types."""
        try:
            # Filter storage types or search all
            if storage_types:
                search_result = await self.universal_search.semantic_search_filtered(
                    query=query,
                    storage_types=storage_types,
                    top_k=top_k
                )
            else:
                search_result = await self.universal_search.semantic_search_all(
                    query=query,
                    top_k=top_k,
                    include_relationships=True
                )
            
            if search_result.get('success'):
                results = search_result.get('results', [])
                
                # Apply conversation filtering if specified
                if conversation_id:
                    filtered_results = []
                    for result in results:
                        result_metadata = result.get('metadata', {})
                        result_conv_id = result_metadata.get('conversation_id')
                        if result_conv_id == conversation_id or result_conv_id is None:
                            filtered_results.append(result)
                    results = filtered_results[:top_k]
                
                # Transform to memory tool format for backward compatibility
                transformed_results = []
                for result in results:
                    transformed_result = {
                        'doc_id': result.get('doc_id', result.get('universal_id', 'unknown')),
                        'content_preview': result.get('content_preview', ''),
                        'similarity_score': result.get('similarity_score', 0.0),
                        'metadata': result.get('metadata', {}),
                        'storage_type': result.get('storage_type', 'unknown'),
                        'source_database': result.get('source_database', 'unknown'),
                        'universal_search_enabled': True,
                        'cross_storage_result': True
                    }
                    transformed_results.append(transformed_result)
                
                return {
                    'success': True,
                    'results': transformed_results,
                    'total_found': len(transformed_results),
                    'universal_search_used': True,
                    'storage_types_searched': storage_types or ['all'],
                    'conversation_filtered': conversation_id is not None,
                    'facets': search_result.get('facets', {}),
                    'search_metadata': {
                        'query': query,
                        'top_k_requested': top_k,
                        'total_before_filtering': len(search_result.get('results', [])),
                        'search_time': search_result.get('search_time_ms', 0)
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f'Universal search failed: {search_result.get("error")}',
                    'fallback_recommended': True
                }
                
        except Exception as e:
            logger.error(f"Universal cross-storage search failed: {e}")
            return {
                'success': False,
                'error': f'Cross-storage search error: {str(e)}',
                'fallback_recommended': True
            }
    
    async def _fallback_atomic_search(self, query: str, conversation_id: str,
                                    top_k: int) -> Dict[str, Any]:
        """Fallback to existing atomic memory search."""
        try:
            from ltms.tools.atomic_memory_integration import get_atomic_memory_manager
            
            manager = get_atomic_memory_manager()
            result = await manager.atomic_search(
                query=query,
                k=top_k,
                conversation_id=conversation_id
            )
            
            if result.get('success'):
                return {
                    **result,
                    'universal_search_used': False,
                    'fallback_search_used': True,
                    'storage_types_searched': ['memory'],  # Atomic search is primarily memory
                    'cross_storage_result': False
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Fallback atomic search failed: {e}")
            return {
                'success': False,
                'error': f'Fallback search error: {str(e)}'
            }
    
    async def enhanced_store_with_universal_indexing(self, file_name: str, content: str,
                                                   resource_type: str = 'document',
                                                   conversation_id: str = 'default',
                                                   **metadata) -> Dict[str, Any]:
        """
        Enhanced store operation using enhanced unified storage.
        
        Automatically indexes content to universal FAISS for cross-storage search.
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'Enhanced storage not available',
                'fallback_recommended': True
            }
        
        try:
            # Map resource_type to storage_type
            storage_type_mapping = {
                'document': 'memory',
                'memory': 'memory',
                'task': 'tasks',
                'todo': 'tasks',
                'blueprint': 'blueprint',
                'architecture': 'blueprint',
                'cache': 'cache_data',
                'chat': 'log_chat'
            }
            
            storage_type = storage_type_mapping.get(resource_type.lower(), 'memory')
            
            # Prepare enhanced metadata
            enhanced_metadata = {
                'conversation_id': conversation_id,
                'resource_type': resource_type,
                **metadata
            }
            
            # Use enhanced unified storage
            result = await self.enhanced_storage.enhanced_store(
                storage_type=storage_type,
                content=content,
                file_name=file_name,
                metadata=enhanced_metadata
            )
            
            if result.get('success'):
                return {
                    **result,
                    'universal_indexing_enabled': result.get('universal_indexed', False),
                    'enhanced_storage_used': True,
                    'cross_storage_search_ready': result.get('universal_indexed', False)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Enhanced store with universal indexing failed: {e}")
            return {
                'success': False,
                'error': f'Enhanced store error: {str(e)}',
                'fallback_recommended': True
            }
    
    def get_search_capabilities(self) -> Dict[str, Any]:
        """Get current search capabilities and configuration."""
        capabilities = {
            'universal_search_available': self.is_available(),
            'enhanced_storage_available': self.enhanced_storage is not None,
            'test_mode': self.test_mode
        }
        
        if self.is_available():
            try:
                # Get universal search capabilities
                search_caps = self.universal_search.get_search_capabilities()
                storage_caps = self.enhanced_storage.get_enhanced_storage_routing()
                
                capabilities.update({
                    'supported_storage_types': list(storage_caps.keys()),
                    'cross_storage_search': True,
                    'universal_faceting': True,
                    'relationship_context': True,
                    'search_features': [
                        'semantic_similarity',
                        'cross_storage_type_search', 
                        'storage_type_filtering',
                        'conversation_filtering',
                        'relationship_context',
                        'faceted_results'
                    ]
                })
                
                # Add search interface details
                if isinstance(search_caps, dict):
                    capabilities['search_interface_details'] = search_caps
                    
            except Exception as e:
                logger.error(f"Failed to get detailed capabilities: {e}")
                capabilities['capability_error'] = str(e)
        else:
            capabilities.update({
                'fallback_search_available': True,
                'atomic_memory_search': True,
                'search_features': [
                    'semantic_similarity',
                    'memory_search_only',
                    'conversation_filtering'
                ]
            })
        
        return capabilities
    
    async def get_storage_statistics(self) -> Dict[str, Any]:
        """Get statistics across all storage types for monitoring."""
        if not self.is_available():
            return {'error': 'Universal search not available'}
        
        try:
            # Get enhanced storage metrics
            enhanced_metrics = self.enhanced_storage.get_enhanced_metrics()
            
            # Get universal search statistics
            search_stats = {}
            if hasattr(self.universal_search, 'get_search_statistics'):
                search_stats = await self.universal_search.get_search_statistics()
            
            return {
                'enhanced_storage_metrics': enhanced_metrics,
                'universal_search_statistics': search_stats,
                'integration_status': 'operational',
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage statistics: {e}")
            return {
                'error': str(e),
                'integration_status': 'degraded',
                'last_updated': datetime.now().isoformat()
            }


# Global instance for singleton pattern
_universal_search_integration = None


def get_universal_search_integration(test_mode: bool = False) -> UniversalSearchIntegration:
    """Get global universal search integration instance."""
    global _universal_search_integration
    if _universal_search_integration is None or test_mode:
        _universal_search_integration = UniversalSearchIntegration(test_mode=test_mode)
    return _universal_search_integration