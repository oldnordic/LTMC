"""
LTMC Graph Action Module
Knowledge graph operations with real Neo4j implementation and proper async handling
"""

import json
from typing import Dict, Any
from ltms.tools.common.async_utils import run_async_in_context


def graph_action(action: str, **params) -> Dict[str, Any]:
    """Knowledge graph operations with real internal Neo4j implementation.
    
    Actions: link, query, auto_link, get_relationships
    
    This implementation uses proper async handling to avoid event loop conflicts
    when called from within MCP server context.
    
    Args:
        action: The graph action to perform
        **params: Additional parameters for specific actions
        
    Returns:
        Dictionary with operation result and status
    """
    if not action:
        return {'success': False, 'error': 'Action parameter is required'}
    
    if action == 'link':
        return _handle_link_creation(params)
    elif action == 'query':
        return _handle_query_relationships(params)
    elif action == 'auto_link':
        return _handle_auto_link(params)
    elif action == 'get_relationships':
        return _handle_get_relationships(params)
    else:
        return {'success': False, 'error': f'Unknown graph action: {action}'}


def _handle_link_creation(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle creation of new graph relationship link."""
    required_params = ['source_id', 'target_id', 'relation']
    for param in required_params:
        if param not in params:
            return {'success': False, 'error': f'Missing required parameter: {param}'}
    
    try:
        async def create_link():
            """Create new relationship link in Neo4j graph database."""
            from ltms.database.neo4j_store import get_neo4j_graph_store
            
            store = await get_neo4j_graph_store()
            
            if not store.is_available():
                return {
                    'success': False,
                    'error': 'Neo4j graph store not available'
                }
            
            properties = params.get('properties', {})
            weight = params.get('weight', 1.0)
            metadata = params.get('metadata', {})
            
            # Add weight and metadata to properties
            properties.update({
                'weight': weight,
                'metadata': json.dumps(metadata) if metadata else None
            })
            
            result = store.create_relationship(
                source_id=params['source_id'],
                target_id=params['target_id'],
                relationship_type=params['relation'],
                properties=properties
            )
            
            return result
        
        # Use async utils to handle event loop properly
        return run_async_in_context(create_link())
        
    except Exception as e:
        return {'success': False, 'error': f'Graph link failed: {str(e)}'}


def _handle_query_relationships(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle querying of existing graph relationships."""
    required_params = ['entity']
    for param in required_params:
        if param not in params:
            return {'success': False, 'error': f'Missing required parameter: {param}'}
    
    try:
        async def query_relationships():
            """Query existing relationships in Neo4j graph database."""
            from ltms.database.neo4j_store import get_neo4j_graph_store
            
            store = await get_neo4j_graph_store()
            
            if not store.is_available():
                return {
                    'success': False,
                    'error': 'Neo4j graph store not available'
                }
            
            relation_type = params.get('relation_type')
            direction = params.get('direction', 'both')
            
            result = store.query_relationships(
                entity_id=params['entity'],
                relationship_type=relation_type,
                direction=direction
            )
            
            return result
        
        # Use async utils to handle event loop properly
        return run_async_in_context(query_relationships())
        
    except Exception as e:
        return {'success': False, 'error': f'Graph query failed: {str(e)}'}


def _handle_auto_link(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle automatic linking of related documents."""
    if 'documents' not in params:
        return {'success': False, 'error': 'Missing required parameter: documents'}
    
    try:
        async def auto_link_docs():
            """Automatically create links between related documents."""
            from ltms.database.neo4j_store import get_neo4j_graph_store
            
            store = await get_neo4j_graph_store()
            
            if not store.is_available():
                return {
                    'success': False,
                    'error': 'Neo4j graph store not available'
                }
            
            documents = params['documents']
            max_links = params.get('max_links_per_document', 5)
            similarity_threshold = params.get('similarity_threshold', 0.7)
            
            result = store.auto_link_documents(documents)
            
            return result
        
        # Use async utils to handle event loop properly
        return run_async_in_context(auto_link_docs())
        
    except Exception as e:
        return {'success': False, 'error': f'Graph auto link failed: {str(e)}'}


def _handle_get_relationships(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle retrieval of relationships for a specific document."""
    if 'doc_id' not in params:
        return {'success': False, 'error': 'Missing required parameter: doc_id'}
    
    try:
        async def get_doc_relationships():
            """Get relationships for specific document from Neo4j."""
            from ltms.database.neo4j_store import get_neo4j_graph_store
            
            store = await get_neo4j_graph_store()
            
            if not store.is_available():
                return {
                    'success': False,
                    'error': 'Neo4j graph store not available'
                }
            
            result = store.query_relationships(params['doc_id'])
            
            return result
        
        # Use async utils to handle event loop properly
        return run_async_in_context(get_doc_relationships())
        
    except Exception as e:
        return {'success': False, 'error': f'Get relationships failed: {str(e)}'}