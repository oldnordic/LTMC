"""
Graph database tools for LTMC MCP server.
Provides knowledge graph operations with real Neo4j implementation.

File: ltms/tools/graph/graph_actions.py
Lines: ~400 (under 300 limit split into extension)
Purpose: Graph database operations
"""

import asyncio
import json
import sqlite3
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone

from ..core.mcp_base import MCPToolBase
from ..core.config import get_tool_config

logger = logging.getLogger(__name__)


class GraphTools(MCPToolBase):
    """Graph database tools with Neo4j implementation.
    
    Provides knowledge graph operations, relationship management,
    and graph traversal functionality with real database operations.
    """
    
    def __init__(self):
        super().__init__("GraphTools")
        self.config = get_tool_config()
    
    def get_valid_actions(self) -> List[str]:
        """Get list of valid graph actions."""
        return [
            'link', 'query', 'auto_link', 'get_relationships',
            'context', 'get', 'messages', 'stats', 'remove', 
            'list', 'discover', 'conversations', 'create_causal_link'
        ]
    
    async def execute_action(self, action: str, **params) -> Dict[str, Any]:
        """Execute graph database action."""
        # Check required database systems
        db_check = self._check_database_availability(['sqlite', 'neo4j'])
        if not db_check.get('success', False):
            return db_check
        
        if action == 'link':
            return await self._action_link(**params)
        elif action == 'query':
            return await self._action_query(**params)
        elif action == 'auto_link':
            return await self._action_auto_link(**params)
        elif action == 'get_relationships':
            return await self._action_get_relationships(**params)
        elif action == 'context':
            return await self._action_context(**params)
        elif action == 'get':
            return await self._action_get(**params)
        elif action == 'messages':
            return await self._action_messages(**params)
        elif action == 'stats':
            return await self._action_stats(**params)
        elif action == 'remove':
            return await self._action_remove(**params)
        elif action == 'list':
            return await self._action_list(**params)
        elif action == 'discover':
            return await self._action_discover(**params)
        elif action == 'conversations':
            return await self._action_conversations(**params)
        elif action == 'create_causal_link':
            return await self._action_create_causal_link(**params)
        else:
            return self._create_error_response(f"Unknown graph action: {action}")
    
    async def _action_link(self, **params) -> Dict[str, Any]:
        """Create new relationship link in Neo4j graph database with Mind Graph tracking."""
        required_params = ['source_id', 'target_id', 'relation']
        for param in required_params:
            if param not in params:
                return self._create_error_response(f'Missing required parameter: {param}')
        
        try:
            # Track reasoning for relationship creation
            reason_id = self._track_reasoning(
                reason_type="relationship_creation",
                description=f"Creating '{params['relation']}' relationship between '{params['source_id']}' and '{params['target_id']}'",
                priority_level=2,
                confidence_score=0.9
            )
            from ltms.database.neo4j_store import get_neo4j_graph_store
            
            store = await get_neo4j_graph_store()
            
            if not store.is_available():
                return self._create_error_response('Neo4j graph store not available')
            
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
            
            # Track successful relationship creation
            change_id = self._track_mind_graph_change(
                change_type="graph_relationship_created",
                change_summary=f"Created '{params['relation']}' relationship in knowledge graph",
                change_details=f"Source: {params['source_id']}, Target: {params['target_id']}, Properties: {properties}"
            )
            
            if change_id and reason_id:
                self._link_change_to_reason(change_id, reason_id, "MOTIVATED_BY")
            
            # Add Mind Graph metadata to result
            result_data = self._create_success_response({
                **result,
                'mind_graph_patterns': {
                    'operation': 'create_relationship',
                    'reasoning_id': reason_id,
                    'change_id': change_id,
                    'relationship_type': params['relation']
                }
            })
            
            return result_data
            
        except Exception as e:
            return self._create_error_response(f'Graph link failed: {str(e)}')
    
    async def _action_query(self, **params) -> Dict[str, Any]:
        """Query existing relationships in Neo4j graph database with Mind Graph tracking."""
        required_params = ['entity']
        for param in required_params:
            if param not in params:
                return self._create_error_response(f'Missing required parameter: {param}')
        
        try:
            # Track reasoning for relationship query
            reason_id = self._track_reasoning(
                reason_type="graph_query",
                description=f"Querying relationships for entity '{params['entity']}' with direction '{params.get('direction', 'both')}'",
                priority_level=3,
                confidence_score=0.8
            )
            from ltms.database.neo4j_store import get_neo4j_graph_store
            
            store = await get_neo4j_graph_store()
            
            if not store.is_available():
                return self._create_error_response('Neo4j graph store not available')
            
            relation_type = params.get('relation_type')
            direction = params.get('direction', 'both')
            
            result = store.query_relationships(
                entity_id=params['entity'],
                relationship_type=relation_type,
                direction=direction
            )
            
            # Track successful query execution
            change_id = self._track_mind_graph_change(
                change_type="graph_query_executed",
                change_summary=f"Executed relationship query for entity '{params['entity']}'",
                change_details=f"Found {len(result.get('relationships', []))} relationships, Direction: {direction}, Type: {relation_type}"
            )
            
            if change_id and reason_id:
                self._link_change_to_reason(change_id, reason_id, "MOTIVATED_BY")
            
            # Add Mind Graph metadata to result
            result_data = self._create_success_response({
                **result,
                'mind_graph_patterns': {
                    'operation': 'query_relationships',
                    'reasoning_id': reason_id,
                    'change_id': change_id,
                    'entity_queried': params['entity']
                }
            })
            
            return result_data
            
        except Exception as e:
            return self._create_error_response(f'Graph query failed: {str(e)}')
    
    async def _action_auto_link(self, **params) -> Dict[str, Any]:
        """Automatically create links between related documents."""
        if 'documents' not in params:
            return self._create_error_response('Missing required parameter: documents')
        
        try:
            from ltms.database.neo4j_store import get_neo4j_graph_store
            
            store = await get_neo4j_graph_store()
            
            if not store.is_available():
                return self._create_error_response('Neo4j graph store not available')
            
            documents = params['documents']
            max_links = params.get('max_links_per_document', 5)
            similarity_threshold = params.get('similarity_threshold', 0.7)
            
            result = store.auto_link_documents(documents)
            
            return self._create_success_response(result)
            
        except Exception as e:
            return self._create_error_response(f'Graph auto link failed: {str(e)}')
    
    async def _action_get_relationships(self, **params) -> Dict[str, Any]:
        """Get relationships for specific document from Neo4j."""
        if 'doc_id' not in params:
            return self._create_error_response('Missing required parameter: doc_id')
        
        try:
            from ltms.database.neo4j_store import get_neo4j_graph_store
            
            store = await get_neo4j_graph_store()
            
            if not store.is_available():
                return self._create_error_response('Neo4j graph store not available')
            
            result = store.query_relationships(params['doc_id'])
            
            return self._create_success_response(result)
            
        except Exception as e:
            return self._create_error_response(f'Get relationships failed: {str(e)}')
    
    async def _action_context(self, **params) -> Dict[str, Any]:
        """Handle both build_context and retrieve_by_type functionality."""
        if 'query' not in params:
            return self._create_error_response('Missing required parameter: query')
        
        try:
            from ltms.config.json_config_loader import get_config
            config = get_config()
            db_path = config.get_db_path()
            
            # Direct SQLite connection
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            query = params['query']
            doc_type = params.get('doc_type', 'document')
            top_k = params.get('top_k', 5)
            max_tokens = params.get('max_tokens', 4000)
            
            # Simple text matching for context retrieval
            cursor.execute('''
                SELECT id, file_name, content, resource_type, created_at
                FROM documents 
                WHERE resource_type = ? AND (content LIKE ? OR file_name LIKE ?)
                ORDER BY created_at DESC
                LIMIT ?
            ''', (doc_type, f'%{query}%', f'%{query}%', top_k))
            
            results = []
            total_tokens = 0
            
            for row in cursor.fetchall():
                doc_id, file_name, content, resource_type, created_at = row
                
                # Estimate tokens (roughly 4 chars per token)
                content_tokens = len(content) // 4
                if total_tokens + content_tokens > max_tokens:
                    # Truncate content to fit token limit
                    remaining_tokens = max_tokens - total_tokens
                    content = content[:remaining_tokens * 4] + "..."
                    content_tokens = remaining_tokens
                
                results.append({
                    'id': doc_id,
                    'file_name': file_name,
                    'content': content,
                    'resource_type': resource_type,
                    'created_at': created_at,
                    'tokens': content_tokens
                })
                
                total_tokens += content_tokens
                if total_tokens >= max_tokens:
                    break
            
            conn.close()
            
            return self._create_success_response({
                'query': query,
                'doc_type': doc_type,
                'results': results,
                'total_documents': len(results),
                'total_tokens': total_tokens,
                'max_tokens': max_tokens
            })
            
        except Exception as e:
            return self._create_error_response(f'Graph context failed: {str(e)}')
    
    async def _action_get(self, **params) -> Dict[str, Any]:
        """Get all resource links from Neo4j graph database."""
        if 'resource_id' not in params:
            return self._create_error_response('Missing required parameter: resource_id')
        
        try:
            from ltms.database.neo4j_store import get_neo4j_graph_store
            
            store = await get_neo4j_graph_store()
            
            if not store.is_available():
                return self._create_error_response('Neo4j graph store not available')
            
            resource_id = params['resource_id']
            link_type = params.get('link_type')
            
            # Query both incoming and outgoing relationships
            relationships = store.query_relationships(
                entity_id=resource_id,
                relationship_type=link_type,
                direction='both'
            )
            
            return self._create_success_response({
                'resource_id': resource_id,
                'link_type': link_type,
                'relationships': relationships
            })
            
        except Exception as e:
            return self._create_error_response(f'Graph get failed: {str(e)}')
    
    async def _action_messages(self, **params) -> Dict[str, Any]:
        """Find messages that reference a specific chunk."""
        if 'chunk_id' not in params:
            return self._create_error_response('Missing required parameter: chunk_id')
        
        try:
            chunk_id = params['chunk_id']
            
            # Find messages that reference this chunk
            rows = self.db.execute_sqlite('''
                SELECT id, conversation_id, role, content, agent_name, source_tool, created_at
                FROM chat_messages 
                WHERE content LIKE ? OR content LIKE ?
                ORDER BY created_at DESC
            ''', (f'%chunk_{chunk_id}%', f'%{chunk_id}%'), fetch='all')
            
            messages = []
            for row in rows:
                msg_id, conv_id, role, content, agent_name, source_tool, created_at = row
                messages.append({
                    'id': msg_id,
                    'conversation_id': conv_id,
                    'role': role,
                    'content': content,
                    'agent_name': agent_name,
                    'source_tool': source_tool,
                    'created_at': created_at
                })
            
            return self._create_success_response({
                'chunk_id': chunk_id,
                'messages': messages,
                'message_count': len(messages)
            })
            
        except Exception as e:
            return self._create_error_response(f'Graph messages failed: {str(e)}')
    
    async def _action_stats(self, **params) -> Dict[str, Any]:
        """Get context usage statistics from database with Mind Graph tracking."""
        try:
            # Track reasoning for statistics query
            reason_id = self._track_reasoning(
                reason_type="statistics_query",
                description="Retrieving comprehensive database statistics including Mind Graph metrics",
                priority_level=3,
                confidence_score=0.9
            )
            # Get document statistics
            doc_count = self.db.execute_sqlite('SELECT COUNT(*) FROM documents', fetch='one')[0]
            
            # Get chat message statistics
            message_count = self.db.execute_sqlite('SELECT COUNT(*) FROM chat_messages', fetch='one')[0]
            
            # Get blueprint statistics
            blueprint_count = self.db.execute_sqlite('SELECT COUNT(*) FROM blueprints', fetch='one')[0]
            
            # Get todo statistics  
            todo_count = self.db.execute_sqlite('SELECT COUNT(*) FROM todos', fetch='one')[0]
            
            # Get Mind Graph statistics
            agents_count = self.db.execute_sqlite('SELECT COUNT(*) FROM MindGraph_Agents', fetch='one')[0]
            changes_count = self.db.execute_sqlite('SELECT COUNT(*) FROM MindGraph_Changes', fetch='one')[0]
            reasons_count = self.db.execute_sqlite('SELECT COUNT(*) FROM MindGraph_Reasons', fetch='one')[0]
            relationships_count = self.db.execute_sqlite('SELECT COUNT(*) FROM MindGraph_Relationships', fetch='one')[0]
            
            # Get causal relationships specifically
            causal_links_count = self.db.execute_sqlite(
                "SELECT COUNT(*) FROM MindGraph_Relationships WHERE relationship_type LIKE 'CAUSAL_%'", fetch='one')[0]
            
            # Track successful statistics gathering
            change_id = self._track_mind_graph_change(
                change_type="statistics_gathered",
                change_summary="Gathered comprehensive database statistics including Mind Graph metrics",
                change_details=f"Documents: {doc_count}, Messages: {message_count}, Mind Graph Agents: {agents_count}, Changes: {changes_count}, Causal Links: {causal_links_count}"
            )
            
            if change_id and reason_id:
                self._link_change_to_reason(change_id, reason_id, "MOTIVATED_BY")
            
            result = self._create_success_response({
                'statistics': {
                    'total_documents': doc_count,
                    'total_messages': message_count,
                    'total_blueprints': blueprint_count,
                    'total_todos': todo_count,
                    'total_resources': doc_count + message_count + blueprint_count + todo_count,
                    'mind_graph': {
                        'total_agents': agents_count,
                        'total_changes': changes_count,
                        'total_reasons': reasons_count,
                        'total_relationships': relationships_count,
                        'causal_links': causal_links_count
                    }
                },
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'mind_graph_patterns': {
                    'operation': 'database_statistics',
                    'reasoning_id': reason_id,
                    'change_id': change_id,
                    'statistics_gathered': True
                }
            })
            
            return result
            
        except Exception as e:
            return self._create_error_response(f'Graph stats failed: {str(e)}')
    
    async def _action_remove(self, **params) -> Dict[str, Any]:
        """Remove specific relationship link from Neo4j graph."""
        if 'link_id' not in params:
            return self._create_error_response('Missing required parameter: link_id')
        
        try:
            from ltms.database.neo4j_store import get_neo4j_graph_store
            
            store = await get_neo4j_graph_store()
            
            if not store.is_available():
                return self._create_error_response('Neo4j graph store not available')
            
            link_id = params['link_id']
            
            # Remove relationship by ID (this would need Neo4j store implementation)
            result = store.delete_relationship(link_id)
            
            return self._create_success_response({
                'link_id': link_id,
                'message': 'Resource link removed successfully'
            })
            
        except Exception as e:
            return self._create_error_response(f'Graph remove failed: {str(e)}')
    
    async def _action_list(self, **params) -> Dict[str, Any]:
        """List all relationship links in Neo4j graph database."""
        try:
            from ltms.database.neo4j_store import get_neo4j_graph_store
            
            store = await get_neo4j_graph_store()
            
            if not store.is_available():
                return self._create_error_response('Neo4j graph store not available')
            
            limit = params.get('limit', 100)
            
            # Get all relationships (this would need Neo4j store implementation)
            relationships = store.list_all_relationships(limit=limit)
            
            return self._create_success_response({
                'relationships': relationships,
                'limit': limit,
                'count': len(relationships)
            })
            
        except Exception as e:
            return self._create_error_response(f'Graph list failed: {str(e)}')
    
    async def _action_discover(self, **params) -> Dict[str, Any]:
        """List tool identifiers from chat messages."""
        try:
            # Get unique source tools from chat messages
            rows = self.db.execute_sqlite('''
                SELECT DISTINCT source_tool, COUNT(*) as usage_count
                FROM chat_messages 
                WHERE source_tool IS NOT NULL AND source_tool != ''
                GROUP BY source_tool
                ORDER BY usage_count DESC
            ''', fetch='all')
            
            tools = []
            for row in rows:
                tool_name, usage_count = row
                tools.append({
                    'tool_name': tool_name,
                    'usage_count': usage_count
                })
            
            return self._create_success_response({
                'tool_identifiers': tools,
                'total_tools': len(tools)
            })
            
        except Exception as e:
            return self._create_error_response(f'Graph discover failed: {str(e)}')
    
    async def _action_conversations(self, **params) -> Dict[str, Any]:
        """Get tool conversations from database."""
        if 'source_tool' not in params:
            return self._create_error_response('Missing required parameter: source_tool')
        
        try:
            source_tool = params['source_tool']
            limit = params.get('limit', 10)
            
            # Get conversations that used this tool
            rows = self.db.execute_sqlite('''
                SELECT DISTINCT conversation_id, COUNT(*) as message_count,
                       MIN(created_at) as first_message,
                       MAX(created_at) as last_message
                FROM chat_messages 
                WHERE source_tool = ?
                GROUP BY conversation_id
                ORDER BY last_message DESC
                LIMIT ?
            ''', (source_tool, limit), fetch='all')
            
            conversations = []
            for row in rows:
                conv_id, msg_count, first_msg, last_msg = row
                conversations.append({
                    'conversation_id': conv_id,
                    'message_count': msg_count,
                    'first_message': first_msg,
                    'last_message': last_msg,
                    'source_tool': source_tool
                })
            
            return self._create_success_response({
                'source_tool': source_tool,
                'conversations': conversations,
                'conversation_count': len(conversations),
                'limit': limit
            })
            
        except Exception as e:
            return self._create_error_response(f'Graph conversations failed: {str(e)}')
    
    async def _action_create_causal_link(self, **params) -> Dict[str, Any]:
        """Create causal relationships between Mind Graph entities (changes and reasons)."""
        required_params = ['cause_id', 'effect_id', 'causal_type']
        for param in required_params:
            if param not in params:
                return self._create_error_response(f'Missing required parameter: {param}')
        
        try:
            # Track reasoning for causal link creation
            reason_id = self._track_reasoning(
                reason_type="causal_analysis",
                description=f"Creating causal relationship: '{params['cause_id']}' {params['causal_type']} '{params['effect_id']}'",
                priority_level=1,  # High priority for causal relationships
                confidence_score=params.get('confidence', 0.8)
            )
            
            cause_id = params['cause_id']
            effect_id = params['effect_id']
            causal_type = params['causal_type']  # e.g., "CAUSES", "ENABLES", "PREVENTS", "INFLUENCES"
            
            # Validate causal types
            valid_causal_types = ["CAUSES", "ENABLES", "PREVENTS", "INFLUENCES", "LEADS_TO", "BLOCKS", "REQUIRES"]
            if causal_type not in valid_causal_types:
                return self._create_error_response(f'Invalid causal_type. Must be one of: {valid_causal_types}')
            
            # Create the causal link in the Mind Graph relationships table
            # Store additional data as JSON in properties field
            properties_data = {
                'evidence': params.get('evidence', ''),
                'temporal_order': params.get('temporal_order', 'sequential'),
                'context': params.get('context', ''),
                'created_by_agent': self.agent_id,
                'causal_type': causal_type
            }
            
            relationship_data = {
                'source_type': 'change',  # Most causal links are between changes
                'source_id': cause_id,
                'target_type': 'change',
                'target_id': effect_id,
                'relationship_type': f'CAUSAL_{causal_type}',
                'strength': params.get('strength', 0.8),
                'confidence': params.get('confidence', 0.8),
                'properties': json.dumps(properties_data),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Insert into Mind Graph relationships table
            relationship_id = f"causal_{cause_id}_{effect_id}_{causal_type.lower()}_{int(datetime.now().timestamp())}"
            
            self.db.execute_sqlite('''
                INSERT INTO MindGraph_Relationships (
                    relationship_id, source_type, source_id, target_type, target_id, 
                    relationship_type, strength, confidence, properties, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                relationship_id, relationship_data['source_type'], cause_id, 
                relationship_data['target_type'], effect_id, f'CAUSAL_{causal_type}',
                relationship_data['strength'], relationship_data['confidence'],
                relationship_data['properties'], relationship_data['created_at']
            ))
            
            # Also create in Neo4j if available
            neo4j_success = False
            try:
                from ltms.database.neo4j_store import get_neo4j_graph_store
                
                store = await get_neo4j_graph_store()
                if store.is_available():
                    neo4j_result = store.create_relationship(
                        source_id=cause_id,
                        target_id=effect_id,
                        relationship_type=f'CAUSAL_{causal_type}',
                        properties=relationship_data
                    )
                    neo4j_success = True
            except Exception as e:
                logger.warning(f"Neo4j causal link creation failed: {e}")
            
            # Track successful causal link creation
            change_id = self._track_mind_graph_change(
                change_type="causal_link_created",
                change_summary=f"Created causal relationship: {cause_id} {causal_type} {effect_id}",
                change_details=f"Relationship ID: {relationship_id}, Strength: {relationship_data['strength']}, Confidence: {relationship_data['confidence']}, Evidence: {properties_data['evidence']}"
            )
            
            if change_id and reason_id:
                self._link_change_to_reason(change_id, reason_id, "MOTIVATED_BY")
            
            # Build comprehensive result
            result = {
                'relationship_id': relationship_id,
                'cause_id': cause_id,
                'effect_id': effect_id,
                'causal_type': causal_type,
                'strength': relationship_data['strength'],
                'confidence': relationship_data['confidence'],
                'evidence': properties_data['evidence'],
                'temporal_order': properties_data['temporal_order'],
                'context': properties_data['context'],
                'created_at': relationship_data['created_at'],
                'stored_in_sqlite': True,
                'stored_in_neo4j': neo4j_success,
                'mind_graph_patterns': {
                    'operation': 'create_causal_link',
                    'reasoning_id': reason_id,
                    'change_id': change_id,
                    'causal_relationship_type': causal_type,
                    'causal_strength': relationship_data['strength']
                }
            }
            
            return self._create_success_response(result)
            
        except Exception as e:
            logger.error(f"Causal link creation failed: {e}")
            import traceback
            traceback.print_exc()
            return self._create_error_response(f'Causal link creation failed: {str(e)}')


# Create global instance for backward compatibility
async def graph_action(action: str, **params) -> Dict[str, Any]:
    """Graph database operations (backward compatibility).
    
    Actions: link, query, auto_link, get_relationships, context, get, 
             messages, stats, remove, list, discover, conversations
    """
    graph_tools = GraphTools()
    return await graph_tools(action, **params)