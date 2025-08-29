"""
Memory management tools for LTMC MCP server.
Provides atomic memory operations across SQLite+FAISS+Neo4j+Redis.

File: ltms/tools/memory/memory_actions.py
Lines: ~280 (under 300 limit)
Purpose: Memory operations with atomic synchronization
"""

import logging
from typing import Dict, Any, List

from ..core.mcp_base import MCPToolBase
from ..core.config import get_tool_config

logger = logging.getLogger(__name__)


class MemoryTools(MCPToolBase):
    """Memory management tools with atomic synchronization.
    
    Provides memory operations across SQLite, FAISS, Neo4j, and Redis
    with atomic transaction support.
    """
    
    def __init__(self):
        super().__init__("MemoryTools")
        self.config = get_tool_config()
    
    def get_valid_actions(self) -> List[str]:
        """Get list of valid memory actions."""
        return ['store', 'retrieve', 'build_context', 'retrieve_by_type', 'ask_with_context']
    
    async def execute_action(self, action: str, **params) -> Dict[str, Any]:
        """Execute memory action with atomic synchronization."""
        # Check required database systems
        db_check = self._check_database_availability(['sqlite', 'faiss'])
        if not db_check.get('success', False):
            return db_check
        
        if action == 'store':
            return await self._action_store(**params)
        elif action == 'retrieve':
            return await self._action_retrieve(**params)
        elif action == 'build_context':
            return await self._action_build_context(**params)
        elif action == 'retrieve_by_type':
            return await self._action_retrieve_by_type(**params)
        elif action == 'ask_with_context':
            return await self._action_ask_with_context(**params)
        else:
            return self._create_error_response(f"Unknown memory action: {action}")
    
    async def _action_store(self, **params) -> Dict[str, Any]:
        """Store content in LTMC memory with atomic synchronization and Mind Graph tracking."""
        required_params = ['file_name', 'content']
        for param in required_params:
            if param not in params:
                return self._create_error_response(f'Missing required parameter: {param}')
        
        try:
            # Track reasoning for memory store operation
            reason_id = self._track_reasoning(
                reason_type="memory_storage",
                description=f"Storing document '{params['file_name']}' in LTMC memory with {len(params['content'])} characters",
                priority_level=2,
                confidence_score=0.9
            )
            
            # Use atomic memory integration for synchronized storage
            from ltms.tools.atomic_memory_integration import get_atomic_memory_manager
            
            # Extract tags from params if provided
            tags = params.get('tags', [])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
            
            # Get atomic memory manager and call tiered priority store operation
            manager = get_atomic_memory_manager()
            result = await manager.atomic_store_with_tiered_priority(
                file_name=params['file_name'],
                content=params['content'],
                resource_type=params.get('resource_type', 'document'),
                tags=tags,
                conversation_id=params.get('conversation_id', 'default'),
                **{k: v for k, v in params.items() 
                   if k not in ['file_name', 'content', 'resource_type', 'tags', 'conversation_id']}
            )
            
            # Track the memory storage change
            if result.get('success'):
                change_id = self._track_mind_graph_change(
                    change_type="memory_store",
                    change_summary=f"Successfully stored '{params['file_name']}' in memory",
                    change_details=f"Stored across databases: {result.get('affected_databases', [])}",
                    file_path=params['file_name'],
                    lines_changed=len(params['content'].split('\n'))
                )
                
                # Link change to reasoning
                if change_id and reason_id:
                    self._link_change_to_reason(change_id, reason_id, "MOTIVATED_BY")
                
                # Add Mind Graph metadata to result
                result['mind_graph_memory'] = {
                    'operation': 'store',
                    'reasoning_id': reason_id,
                    'change_id': change_id,
                    'document_tracked': params['file_name']
                }
            
            return result
                
        except Exception as e:
            return self._create_error_response(f'Atomic memory store failed: {str(e)}')
    
    async def _action_retrieve(self, **params) -> Dict[str, Any]:
        """Retrieve content from LTMC memory with vector search and Mind Graph tracking."""
        required_params = ['conversation_id', 'query']
        for param in required_params:
            if param not in params:
                return self._create_error_response(f'Missing required parameter: {param}')
        
        try:
            # Track reasoning for memory retrieval operation
            reason_id = self._track_reasoning(
                reason_type="memory_retrieval",
                description=f"Searching memory for query '{params['query']}' in conversation '{params['conversation_id']}'",
                priority_level=2,
                confidence_score=0.8
            )
            
            # Use atomic memory integration for vector search
            from ltms.tools.atomic_memory_integration import get_atomic_memory_manager
            
            # Get atomic memory manager
            manager = get_atomic_memory_manager()
            
            # Perform vector search using atomic FAISS manager with conversation filtering
            search_result = await manager.atomic_search(
                query=params['query'], 
                k=params.get('top_k', 10),
                conversation_id=params['conversation_id']
            )
            
            if search_result['success']:
                # Track the memory retrieval change
                change_id = self._track_mind_graph_change(
                    change_type="memory_retrieve",
                    change_summary=f"Retrieved {len(search_result.get('results', []))} documents for query",
                    change_details=f"Query: '{params['query']}', Results: {len(search_result.get('results', []))}"
                )
                
                # Link change to reasoning
                if change_id and reason_id:
                    self._link_change_to_reason(change_id, reason_id, "MOTIVATED_BY")
                
                # Format results for compatibility
                documents = []
                for i, result in enumerate(search_result.get('results', [])):
                    documents.append({
                        'file_name': result.get('doc_id'),
                        'content': result.get('content_preview', ''),
                        'resource_type': result.get('metadata', {}).get('resource_type', 'document'),
                        'created_at': result.get('metadata', {}).get('stored_at', ''),
                        'similarity_score': 1.0 - result.get('distance', 1.0),  # Convert distance to similarity
                        'rank': i + 1
                    })
                
                result = self._create_success_response({
                    'documents': documents,
                    'query': params['query'],
                    'conversation_id': params['conversation_id'],
                    'total_found': len(documents),
                    'atomic_search': True,
                    'mind_graph_memory': {
                        'operation': 'retrieve',
                        'reasoning_id': reason_id,
                        'change_id': change_id,
                        'query_tracked': params['query']
                    }
                })
                
                return result
            else:
                return search_result
            
        except Exception as e:
            return self._create_error_response(f'Atomic memory retrieve failed: {str(e)}')
    
    async def _action_build_context(self, **params) -> Dict[str, Any]:
        """Build context from documents with token management and Mind Graph tracking."""
        if 'documents' not in params:
            return self._create_error_response('Missing required parameter: documents')
        
        try:
            documents = params['documents']
            max_tokens = params.get('max_tokens', 4000)
            
            # Track reasoning for context building operation
            reason_id = self._track_reasoning(
                reason_type="context_building",
                description=f"Building context from {len(documents) if isinstance(documents, list) else 'unknown'} documents with max {max_tokens} tokens",
                priority_level=3,
                confidence_score=0.7
            )
            
            # Handle string max_tokens parameter from MCP (Fix #1: Critical Type Error)
            if isinstance(max_tokens, str):
                try:
                    max_tokens = int(max_tokens)
                except (ValueError, TypeError):
                    return self._create_error_response('max_tokens must be a valid integer')
            elif not isinstance(max_tokens, int):
                max_tokens = 4000
            
            # Handle JSON string format from MCP parameter parsing (Fix #3)
            if isinstance(documents, str):
                import json
                try:
                    documents = json.loads(documents)
                except (json.JSONDecodeError, TypeError):
                    return self._create_error_response('Documents must be a valid list or JSON array')
            
            if not isinstance(documents, list):
                return self._create_error_response('Documents must be a list')
            
            context_parts = []
            current_tokens = 0
            
            for i, doc in enumerate(documents):
                if not isinstance(doc, dict) or 'content' not in doc:
                    continue
                
                content = str(doc['content'])
                estimated_tokens = len(content) // 4  # Rough estimation: 4 chars per token
                
                if current_tokens + estimated_tokens <= max_tokens:
                    context_parts.append({
                        'index': i,
                        'content': content,
                        'tokens': estimated_tokens,
                        'source': doc.get('file_name', f'document_{i}')
                    })
                    current_tokens += estimated_tokens
                else:
                    remaining_tokens = max_tokens - current_tokens
                    if remaining_tokens > 50:  # Only add if significant space remains
                        truncated_content = content[:remaining_tokens * 4]
                        context_parts.append({
                            'index': i,
                            'content': truncated_content + '...[truncated]',
                            'tokens': remaining_tokens,
                            'source': doc.get('file_name', f'document_{i}'),
                            'truncated': True
                        })
                    break
            
            context_text = '\n\n---\n\n'.join([part['content'] for part in context_parts])
            
            # Track the context building change
            change_id = self._track_mind_graph_change(
                change_type="context_build",
                change_summary=f"Built context from {len(context_parts)} documents ({current_tokens} tokens)",
                change_details=f"Sources: {[part['source'] for part in context_parts]}"
            )
            
            # Link change to reasoning
            if change_id and reason_id:
                self._link_change_to_reason(change_id, reason_id, "MOTIVATED_BY")
            
            result = self._create_success_response({
                'context': context_text,
                'parts': context_parts,
                'total_tokens': current_tokens,
                'max_tokens': max_tokens,
                'documents_included': len(context_parts),
                'mind_graph_memory': {
                    'operation': 'build_context',
                    'reasoning_id': reason_id,
                    'change_id': change_id,
                    'documents_processed': len(documents),
                    'context_created': len(context_parts)
                }
            })
            
            return result
            
        except Exception as e:
            return self._create_error_response(f'Build context failed: {str(e)}')
    
    async def _action_retrieve_by_type(self, **params) -> Dict[str, Any]:
        """Retrieve documents filtered by resource type with Mind Graph tracking."""
        required_params = ['resource_type']
        for param in required_params:
            if param not in params:
                return self._create_error_response(f'Missing required parameter: {param}')
        
        try:
            # Track reasoning for retrieve by type operation
            reason_id = self._track_reasoning(
                reason_type="memory_retrieve_by_type",
                description=f"Retrieving documents of type '{params['resource_type']}' in project '{params.get('project_id', 'all')}'",
                priority_level=2,
                confidence_score=0.8
            )
            
            from ltms.services.context_service import retrieve_by_type
            
            result = retrieve_by_type(
                resource_type=params['resource_type'],
                project_id=params.get('project_id'),
                limit=params.get('limit', 10),
                offset=params.get('offset', 0),
                date_range=params.get('date_range')
            )
            
            # Track the successful retrieval as a Mind Graph change
            if isinstance(result, dict) and result.get('success', True):
                change_id = self._track_mind_graph_change(
                    change_type="memory_retrieve_by_type",
                    change_summary=f"Retrieved {result.get('filtered_count', 0)} documents of type '{params['resource_type']}'",
                    change_details=f"Total found: {result.get('total_count', 0)}, Project: {params.get('project_id', 'all')}"
                )
                
                # Link change to reasoning
                if change_id and reason_id:
                    self._link_change_to_reason(change_id, reason_id, "MOTIVATED_BY")
                
                # Create standardized success response with proper data structure
                return self._create_success_response({
                    'documents': result.get('documents', []),
                    'total_count': result.get('total_count', 0),
                    'filtered_count': result.get('filtered_count', 0),
                    'limit': result.get('limit', 10),
                    'offset': result.get('offset', 0),
                    'mind_graph_memory': {
                        'operation': 'retrieve_by_type',
                        'reasoning_id': reason_id,
                        'change_id': change_id,
                        'resource_type': params['resource_type']
                    }
                })
            else:
                return self._create_error_response(result.get('error', 'Unknown error in retrieve_by_type'))
            
        except Exception as e:
            return self._create_error_response(f'Retrieve by type failed: {str(e)}')
    
    async def _action_ask_with_context(self, **params) -> Dict[str, Any]:
        """Ask question with contextual information."""
        required_params = ['query', 'conversation_id']
        for param in required_params:
            if param not in params:
                return self._create_error_response(f'Missing required parameter: {param}')
        
        try:
            from ltms.services.chat_service import ask_with_context
            
            result = ask_with_context(
                query=params['query'],
                conversation_id=params['conversation_id'],
                top_k=params.get('top_k', 5)
            )
            
            # Wrap in success response if not already wrapped
            if isinstance(result, dict) and 'success' in result:
                return result
            else:
                return self._create_success_response(result)
            
        except Exception as e:
            return self._create_error_response(f'Ask with context failed: {str(e)}')


# Create global instance for backward compatibility
async def memory_action(action: str, **params) -> Dict[str, Any]:
    """Memory operations with atomic synchronization (backward compatibility).
    
    Actions: store, retrieve, build_context, retrieve_by_type, ask_with_context
    """
    memory_tools = MemoryTools()
    return await memory_tools(action, **params)