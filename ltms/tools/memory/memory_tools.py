"""
LTMC Memory Tools - Smart Modularized Memory Operations
Extracted from consolidated.py for single responsibility and maintainability

Real ATOMIC SYNCHRONIZATION across SQLite+FAISS+Neo4j+Redis
NO SHORTCUTS - Production-ready memory operations with error handling
"""

import os
import sys
import warnings
from typing import Dict, Any

# Environment setup for suppression
os.environ["PYTHONWARNINGS"] = "ignore::DeprecationWarning"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)

async def memory_action(action: str, **params) -> Dict[str, Any]:
    """Memory operations with ATOMIC SYNCHRONIZATION across SQLite+FAISS+Neo4j+Redis.
    
    Actions: store, retrieve, build_context, retrieve_by_type, ask_with_context
    """
    if not action:
        return {'success': False, 'error': 'Action parameter is required'}
    
    if action == 'store':
        required_params = ['file_name', 'content']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            # Use atomic memory integration for synchronized storage
            from ltms.tools.atomic_memory_integration import get_atomic_memory_manager
            
            # Extract tags from params if provided
            tags = params.get('tags', [])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
            
            # Get atomic memory manager and call async store operation
            manager = get_atomic_memory_manager()
            result = await manager.atomic_store(
                file_name=params['file_name'],
                content=params['content'],
                resource_type=params.get('resource_type', 'document'),
                tags=tags,
                conversation_id=params.get('conversation_id', 'default'),
                **{k: v for k, v in params.items() if k not in ['file_name', 'content', 'resource_type', 'tags', 'conversation_id']}
            )
            
            return result
                
        except Exception as e:
            return {'success': False, 'error': f'Atomic memory store failed: {str(e)}'}
    
    elif action == 'retrieve':
        required_params = ['conversation_id', 'query']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            # Use atomic memory integration for vector search
            from ltms.tools.atomic_memory_integration import get_atomic_memory_manager
            import asyncio
            
            # Get atomic memory manager
            manager = get_atomic_memory_manager()
            
            # Perform vector search using atomic FAISS manager
            search_result = await manager.atomic_search(
                query=params['query'], 
                k=params.get('top_k', 10)
            )
            
            if search_result['success']:
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
                
                return {
                    'success': True,
                    'documents': documents,
                    'query': params['query'],
                    'conversation_id': params['conversation_id'],
                    'total_found': len(documents),
                    'atomic_search': True
                }
            else:
                return search_result
            
        except Exception as e:
            return {'success': False, 'error': f'Atomic memory retrieve failed: {str(e)}'}
    
    elif action == 'build_context':
        if 'documents' not in params:
            return {'success': False, 'error': 'Missing required parameter: documents'}
        
        try:
            documents = params['documents']
            max_tokens = params.get('max_tokens', 4000)
            
            if not isinstance(documents, list):
                return {'success': False, 'error': 'Documents must be a list'}
            
            context_parts = []
            current_tokens = 0
            
            for i, doc in enumerate(documents):
                if not isinstance(doc, dict) or 'content' not in doc:
                    continue
                
                content = str(doc['content'])
                estimated_tokens = len(content) // 4
                
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
                    if remaining_tokens > 50:
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
            
            return {
                'success': True,
                'context': context_text,
                'parts': context_parts,
                'total_tokens': current_tokens,
                'max_tokens': max_tokens,
                'documents_included': len(context_parts)
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Build context failed: {str(e)}'}
    
    elif action == 'retrieve_by_type':
        required_params = ['query', 'doc_type']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            from ltms.services.context_service import retrieve_by_type
            
            return retrieve_by_type(
                query=params['query'],
                doc_type=params['doc_type'],
                top_k=params.get('top_k', 5)
            )
            
        except Exception as e:
            return {'success': False, 'error': f'Retrieve by type failed: {str(e)}'}
    
    elif action == 'ask_with_context':
        required_params = ['query', 'conversation_id']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            from ltms.services.chat_service import ask_with_context
            
            return ask_with_context(
                query=params['query'],
                conversation_id=params['conversation_id'],
                top_k=params.get('top_k', 5)
            )
            
        except Exception as e:
            return {'success': False, 'error': f'Ask with context failed: {str(e)}'}
    
    else:
        return {'success': False, 'error': f'Unknown memory action: {action}'}


# Export for import compatibility
__all__ = ['memory_action']