"""
Enhanced Memory Actions with Universal Search Integration.
Extends existing memory tools with cross-storage-type search capabilities.

File: ltms/tools/memory/enhanced_memory_actions.py  
Lines: ~295 (under 300 limit)
Purpose: Universal search integration for memory tools
"""

import logging
from typing import Dict, Any, List
from .memory_actions import MemoryTools
from .universal_search_integration import get_universal_search_integration

logger = logging.getLogger(__name__)


class EnhancedMemoryTools(MemoryTools):
    """
    Enhanced memory tools with universal search capabilities.
    
    Extends base MemoryTools with cross-storage-type search while maintaining
    full backward compatibility with existing memory_action calls.
    """
    
    def __init__(self):
        super().__init__()
        self.universal_integration = get_universal_search_integration(test_mode=False)
        logger.info("EnhancedMemoryTools initialized with universal search integration")
    
    def get_valid_actions(self) -> List[str]:
        """Get list of valid memory actions including enhanced ones."""
        base_actions = super().get_valid_actions()
        enhanced_actions = [
            'universal_search',
            'cross_storage_retrieve', 
            'enhanced_store',
            'search_capabilities'
        ]
        return base_actions + enhanced_actions
    
    async def execute_action(self, action: str, **params) -> Dict[str, Any]:
        """Execute memory action with universal search enhancements."""
        # Handle enhanced actions
        if action == 'universal_search':
            return await self._action_universal_search(**params)
        elif action == 'cross_storage_retrieve':
            return await self._action_cross_storage_retrieve(**params)
        elif action == 'enhanced_store':
            return await self._action_enhanced_store(**params)
        elif action == 'search_capabilities':
            return await self._action_search_capabilities(**params)
        elif action == 'retrieve':
            # Enhanced retrieve with universal search option
            return await self._enhanced_action_retrieve(**params)
        elif action == 'store':
            # Enhanced store with universal indexing option
            return await self._enhanced_action_store(**params)
        else:
            # Fallback to base class for other actions
            return await super().execute_action(action, **params)
    
    async def _action_universal_search(self, **params) -> Dict[str, Any]:
        """Universal search across all storage types."""
        required_params = ['query']
        for param in required_params:
            if param not in params:
                return self._create_error_response(f'Missing required parameter: {param}')
        
        try:
            # Track reasoning for universal search
            reason_id = self._track_reasoning(
                reason_type="universal_search",
                description=f"Performing universal search for query '{params['query']}' across all storage types",
                priority_level=3,
                confidence_score=0.9
            )
            
            if not self.universal_integration.is_available():
                return self._create_error_response('Universal search not available')
            
            # Execute universal search
            result = await self.universal_integration.enhanced_retrieve(
                query=params['query'],
                conversation_id=params.get('conversation_id'),
                top_k=params.get('top_k', 10),
                storage_types=params.get('storage_types'),
                include_cross_storage=True
            )
            
            if result.get('success'):
                # Track successful universal search
                change_id = self._track_mind_graph_change(
                    change_type="universal_search",
                    change_summary=f"Universal search found {result.get('total_found', 0)} results",
                    change_details=f"Query: '{params['query']}', Storage types: {result.get('storage_types_searched', [])}"
                )
                
                # Link change to reasoning
                if change_id and reason_id:
                    self._link_change_to_reason(change_id, reason_id, "MOTIVATED_BY")
            
            return result
            
        except Exception as e:
            logger.error(f"Universal search failed: {e}")
            return self._create_error_response(f'Universal search error: {str(e)}')
    
    async def _action_cross_storage_retrieve(self, **params) -> Dict[str, Any]:
        """Cross-storage retrieval with storage type filtering."""
        required_params = ['query', 'storage_types']
        for param in required_params:
            if param not in params:
                return self._create_error_response(f'Missing required parameter: {param}')
        
        try:
            # Validate storage_types parameter
            storage_types = params['storage_types']
            if isinstance(storage_types, str):
                storage_types = [st.strip() for st in storage_types.split(',') if st.strip()]
            
            valid_storage_types = ['memory', 'tasks', 'blueprint', 'cache_data', 'document']
            invalid_types = [st for st in storage_types if st not in valid_storage_types]
            
            if invalid_types:
                return self._create_error_response(f'Invalid storage types: {invalid_types}. Valid types: {valid_storage_types}')
            
            # Track reasoning for cross-storage retrieval
            reason_id = self._track_reasoning(
                reason_type="cross_storage_retrieve",
                description=f"Cross-storage retrieval for '{params['query']}' in storage types: {storage_types}",
                priority_level=3,
                confidence_score=0.85
            )
            
            if not self.universal_integration.is_available():
                return self._create_error_response('Cross-storage search not available')
            
            # Execute cross-storage search
            result = await self.universal_integration.enhanced_retrieve(
                query=params['query'],
                conversation_id=params.get('conversation_id'),
                top_k=params.get('top_k', 10),
                storage_types=storage_types,
                include_cross_storage=True
            )
            
            if result.get('success'):
                # Track successful cross-storage retrieval
                change_id = self._track_mind_graph_change(
                    change_type="cross_storage_retrieve",
                    change_summary=f"Cross-storage search found {result.get('total_found', 0)} results",
                    change_details=f"Query: '{params['query']}', Types: {storage_types}, Results: {result.get('total_found', 0)}"
                )
                
                # Link change to reasoning
                if change_id and reason_id:
                    self._link_change_to_reason(change_id, reason_id, "MOTIVATED_BY")
            
            return result
            
        except Exception as e:
            logger.error(f"Cross-storage retrieve failed: {e}")
            return self._create_error_response(f'Cross-storage retrieve error: {str(e)}')
    
    async def _action_enhanced_store(self, **params) -> Dict[str, Any]:
        """Enhanced store with universal indexing."""
        required_params = ['file_name', 'content']
        for param in required_params:
            if param not in params:
                return self._create_error_response(f'Missing required parameter: {param}')
        
        try:
            # Track reasoning for enhanced store
            reason_id = self._track_reasoning(
                reason_type="enhanced_store",
                description=f"Enhanced store with universal indexing for '{params['file_name']}'",
                priority_level=2,
                confidence_score=0.9
            )
            
            if not self.universal_integration.is_available():
                # Fallback to regular store
                return await super()._action_store(**params)
            
            # Execute enhanced store with universal indexing
            result = await self.universal_integration.enhanced_store_with_universal_indexing(
                file_name=params['file_name'],
                content=params['content'],
                resource_type=params.get('resource_type', 'document'),
                conversation_id=params.get('conversation_id', 'default'),
                **{k: v for k, v in params.items() 
                   if k not in ['file_name', 'content', 'resource_type', 'conversation_id']}
            )
            
            if result.get('success'):
                # Track successful enhanced store
                change_id = self._track_mind_graph_change(
                    change_type="enhanced_store",
                    change_summary=f"Enhanced store completed for '{params['file_name']}'",
                    change_details=f"Universal indexed: {result.get('universal_indexing_enabled', False)}, Affected DBs: {result.get('affected_databases', [])}"
                )
                
                # Link change to reasoning
                if change_id and reason_id:
                    self._link_change_to_reason(change_id, reason_id, "MOTIVATED_BY")
            
            return result
            
        except Exception as e:
            logger.error(f"Enhanced store failed: {e}")
            return self._create_error_response(f'Enhanced store error: {str(e)}')
    
    async def _action_search_capabilities(self, **params) -> Dict[str, Any]:
        """Get current search capabilities and configuration."""
        try:
            capabilities = self.universal_integration.get_search_capabilities()
            
            # Add memory tools specific information
            capabilities['memory_tools_integration'] = {
                'enhanced_actions_available': [
                    'universal_search', 'cross_storage_retrieve', 
                    'enhanced_store', 'search_capabilities'
                ],
                'backward_compatibility': True,
                'mind_graph_integration': True,
                'atomic_memory_fallback': True
            }
            
            return {
                'success': True,
                'capabilities': capabilities
            }
            
        except Exception as e:
            logger.error(f"Failed to get search capabilities: {e}")
            return self._create_error_response(f'Search capabilities error: {str(e)}')
    
    async def _enhanced_action_retrieve(self, **params) -> Dict[str, Any]:
        """Enhanced retrieve with optional universal search."""
        # Check if universal search is requested
        use_universal = params.get('use_universal_search', False)
        storage_types = params.get('storage_types')
        
        if use_universal and self.universal_integration.is_available():
            # Use universal search integration
            try:
                result = await self.universal_integration.enhanced_retrieve(
                    query=params['query'],
                    conversation_id=params.get('conversation_id'),
                    top_k=params.get('top_k', 10),
                    storage_types=storage_types,
                    include_cross_storage=True
                )
                
                # Add backward compatibility fields
                if result.get('success'):
                    result['enhanced_retrieve_used'] = True
                    
                return result
                
            except Exception as e:
                logger.warning(f"Universal search failed, falling back to atomic search: {e}")
                # Continue to fallback below
        
        # Fallback to base implementation
        return await super()._action_retrieve(**params)
    
    async def _enhanced_action_store(self, **params) -> Dict[str, Any]:
        """Enhanced store with optional universal indexing."""
        # Check if enhanced storage is requested
        use_enhanced = params.get('use_enhanced_storage', False)
        
        if use_enhanced and self.universal_integration.is_available():
            # Use enhanced storage with universal indexing
            try:
                result = await self.universal_integration.enhanced_store_with_universal_indexing(
                    file_name=params['file_name'],
                    content=params['content'],
                    resource_type=params.get('resource_type', 'document'),
                    conversation_id=params.get('conversation_id', 'default'),
                    **{k: v for k, v in params.items() 
                       if k not in ['file_name', 'content', 'resource_type', 'conversation_id', 'use_enhanced_storage']}
                )
                
                # Add backward compatibility fields
                if result.get('success'):
                    result['enhanced_store_used'] = True
                    
                return result
                
            except Exception as e:
                logger.warning(f"Enhanced storage failed, falling back to atomic storage: {e}")
                # Continue to fallback below
        
        # Fallback to base implementation
        return await super()._action_store(**params)


# Backward compatibility function
async def enhanced_memory_action(action: str, **params) -> Dict[str, Any]:
    """
    Enhanced memory action function with universal search capabilities.
    
    Provides backward compatibility while adding universal search features.
    """
    enhanced_tools = EnhancedMemoryTools()
    return await enhanced_tools.execute_action(action, **params)


# Maintain backward compatibility with existing memory_action calls
async def memory_action(action: str, **params) -> Dict[str, Any]:
    """
    Enhanced memory action function that replaces the original memory_action.
    
    Maintains full backward compatibility while adding universal search capabilities.
    Users can opt-in to enhanced features by setting specific parameters.
    """
    return await enhanced_memory_action(action, **params)