"""
Chat management tools for LTMC MCP server.
Provides chat logging and conversation management.

File: ltms/tools/memory/chat_actions.py
Lines: ~240 (under 300 limit)
Purpose: Chat operations with real SQLite implementation
"""

import json
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone

from ..core.mcp_base import MCPToolBase
from ..core.config import get_tool_config

logger = logging.getLogger(__name__)


class ChatTools(MCPToolBase):
    """Chat management tools with SQLite storage.
    
    Provides chat logging, conversation retrieval, and query routing
    functionality.
    """
    
    def __init__(self):
        super().__init__("ChatTools")
        self.config = get_tool_config()
    
    def get_valid_actions(self) -> List[str]:
        """Get list of valid chat actions."""
        return ['log', 'get_by_tool', 'get_tool_conversations', 'route_query']
    
    async def execute_action(self, action: str, **params) -> Dict[str, Any]:
        """Execute chat action with SQLite operations."""
        # Check required database systems
        db_check = self._check_database_availability(['sqlite'])
        if not db_check.get('success', False):
            return db_check
        
        if action == 'log':
            return await self._action_log(**params)
        elif action == 'get_by_tool':
            return await self._action_get_by_tool(**params)
        elif action == 'get_tool_conversations':
            return await self._action_get_tool_conversations(**params)
        elif action == 'route_query':
            return await self._action_route_query(**params)
        else:
            return self._create_error_response(f"Unknown chat action: {action}")
    
    async def _action_log(self, **params) -> Dict[str, Any]:
        """Log chat message to SQLite database."""
        required_params = ['conversation_id', 'role', 'content']
        for param in required_params:
            if param not in params:
                return self._create_error_response(f'Missing required parameter: {param}')
        
        try:
            # Validate role
            if params['role'] not in ['user', 'assistant', 'system']:
                return self._create_error_response('role must be one of: user, assistant, system')
            
            # Create chats table
            self.db.execute_sqlite('''
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    agent_name TEXT,
                    metadata TEXT,
                    source_tool TEXT,
                    created_at TEXT NOT NULL
                )
            ''')
            
            created_at = datetime.now(timezone.utc).isoformat()
            metadata_json = json.dumps(params.get('metadata')) if params.get('metadata') else None
            
            # Insert chat message
            rowcount = self.db.execute_sqlite('''
                INSERT INTO chats (conversation_id, role, content, agent_name, metadata, source_tool, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                params['conversation_id'],
                params['role'],
                params['content'],
                params.get('agent_name'),
                metadata_json,
                params.get('source_tool'),
                created_at
            ))
            
            # Get the inserted row ID
            chat_id = self.db.execute_sqlite('SELECT last_insert_rowid()', fetch='one')[0]
            
            return self._create_success_response({
                'chat_id': chat_id,
                'conversation_id': params['conversation_id'],
                'role': params['role'],
                'created_at': created_at,
                'message': 'Chat message logged successfully'
            })
            
        except Exception as e:
            return self._create_error_response(f'Chat log failed: {str(e)}')
    
    async def _action_get_by_tool(self, **params) -> Dict[str, Any]:
        """Get chat messages filtered by source tool."""
        if 'source_tool' not in params:
            return self._create_error_response('Missing required parameter: source_tool')
        
        try:
            limit = params.get('limit', 10)
            
            rows = self.db.execute_sqlite('''
                SELECT id, conversation_id, role, content, agent_name, metadata, created_at
                FROM chats
                WHERE source_tool = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (params['source_tool'], limit), fetch='all')
            
            chats = []
            for row in rows:
                metadata = json.loads(row[5]) if row[5] else None
                chats.append({
                    'chat_id': row[0],
                    'conversation_id': row[1],
                    'role': row[2],
                    'content': row[3],
                    'agent_name': row[4],
                    'metadata': metadata,
                    'created_at': row[6]
                })
            
            return self._create_success_response({
                'chats': chats,
                'source_tool': params['source_tool'],
                'total_found': len(chats),
                'limit_applied': limit
            })
            
        except Exception as e:
            return self._create_error_response(f'Chat get_by_tool failed: {str(e)}')
    
    async def _action_get_tool_conversations(self, **params) -> Dict[str, Any]:
        """Get tool conversations using context service."""
        if 'tool_name' not in params:
            return self._create_error_response('Missing required parameter: tool_name')
        
        try:
            from ltms.services.context_service import get_tool_conversations
            
            result = get_tool_conversations(
                tool_name=params['tool_name'],
                limit=params.get('limit', 10)
            )
            
            # Wrap in success response if not already wrapped
            if isinstance(result, dict) and 'success' in result:
                return result
            else:
                return self._create_success_response(result)
            
        except Exception as e:
            return self._create_error_response(f'Get tool conversations failed: {str(e)}')
    
    async def _action_route_query(self, **params) -> Dict[str, Any]:
        """Route query to different sources using chat service."""
        required_params = ['query']
        for param in required_params:
            if param not in params:
                return self._create_error_response(f'Missing required parameter: {param}')
        
        try:
            from ltms.services.chat_service import route_query
            
            result = route_query(
                query=params['query'],
                source_types=params.get('source_types'),
                top_k=params.get('top_k', 5)
            )
            
            # Wrap in success response if not already wrapped
            if isinstance(result, dict) and 'success' in result:
                return result
            else:
                return self._create_success_response(result)
            
        except Exception as e:
            return self._create_error_response(f'Route query failed: {str(e)}')


# Create global instance for backward compatibility
async def chat_action(action: str, **params) -> Dict[str, Any]:
    """Chat operations with real SQLite implementation (backward compatibility).
    
    Actions: log, get_by_tool, get_tool_conversations, route_query
    """
    chat_tools = ChatTools()
    return await chat_tools(action, **params)