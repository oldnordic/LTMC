"""
Todo management tools for LTMC MCP server.
Provides task and todo management with real SQLite implementation.

File: ltms/tools/todos/todo_actions.py
Lines: ~280 (under 300 limit)
Purpose: Todo and task management operations
"""

import sqlite3
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone

from ..core.mcp_base import MCPToolBase
from ..core.config import get_tool_config

logger = logging.getLogger(__name__)


class TodoTools(MCPToolBase):
    """Todo management tools with SQLite implementation.
    
    Provides task management operations including add, list, complete,
    and search functionality with real database operations.
    """
    
    def __init__(self):
        super().__init__("TodoTools")
        self.config = get_tool_config()
    
    def get_valid_actions(self) -> List[str]:
        """Get list of valid todo actions."""
        return ['add', 'list', 'complete', 'search']
    
    async def execute_action(self, action: str, **params) -> Dict[str, Any]:
        """Execute todo management action."""
        # Check required database systems
        db_check = self._check_database_availability(['sqlite'])
        if not db_check.get('success', False):
            return db_check
        
        if action == 'add':
            return await self._action_add(**params)
        elif action == 'list':
            return await self._action_list(**params)
        elif action == 'complete':
            return await self._action_complete(**params)
        elif action == 'search':
            return await self._action_search(**params)
        else:
            return self._create_error_response(f"Unknown todo action: {action}")
    
    async def _action_add(self, **params) -> Dict[str, Any]:
        """Add new todo to database."""
        if 'title' not in params:
            return self._create_error_response('Missing required parameter: title')
        
        try:
            # Create todos table if not exists
            self.db.execute_sqlite('''
                CREATE TABLE IF NOT EXISTS todos (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    priority TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'pending',
                    completed INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                )
            ''')
            
            # Validate priority
            priority = params.get('priority', 'medium')
            if priority not in ['low', 'medium', 'high', 'urgent']:
                priority = 'medium'
            
            created_at = datetime.now(timezone.utc).isoformat()
            
            # Insert new todo
            result = self.db.execute_sqlite('''
                INSERT INTO todos (title, description, priority, created_at)
                VALUES (?, ?, ?, ?)
            ''', (
                params['title'],
                params.get('description', ''),
                priority,
                created_at
            ), fetch='lastrowid')
            
            todo_id = result
            
            return self._create_success_response({
                'todo_id': todo_id,
                'title': params['title'],
                'priority': priority,
                'status': 'pending',
                'message': f'Todo "{params["title"]}" created successfully'
            })
            
        except Exception as e:
            return self._create_error_response(f'Todo add failed: {str(e)}')
    
    async def _action_list(self, **params) -> Dict[str, Any]:
        """List todos with optional status filtering."""
        try:
            status = params.get('status', 'all')
            limit = params.get('limit', 10)
            
            if status == 'all':
                rows = self.db.execute_sqlite('''
                    SELECT id, title, description, priority, status, completed, created_at, completed_at
                    FROM todos
                    ORDER BY 
                        CASE priority 
                            WHEN 'urgent' THEN 1 
                            WHEN 'high' THEN 2 
                            WHEN 'medium' THEN 3 
                            WHEN 'low' THEN 4 
                        END,
                        created_at DESC
                    LIMIT ?
                ''', (limit,), fetch='all')
            else:
                if status not in ['pending', 'in_progress', 'completed']:
                    return self._create_error_response('status must be one of: all, pending, in_progress, completed')
                
                rows = self.db.execute_sqlite('''
                    SELECT id, title, description, priority, status, completed, created_at, completed_at
                    FROM todos
                    WHERE status = ?
                    ORDER BY 
                        CASE priority 
                            WHEN 'urgent' THEN 1 
                            WHEN 'high' THEN 2 
                            WHEN 'medium' THEN 3 
                            WHEN 'low' THEN 4 
                        END,
                        created_at DESC
                    LIMIT ?
                ''', (status, limit), fetch='all')
            
            todos = []
            for row in rows:
                todos.append({
                    'todo_id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'priority': row[3],
                    'status': row[4],
                    'completed': bool(row[5]),
                    'created_at': row[6],
                    'completed_at': row[7]
                })
            
            return self._create_success_response({
                'todos': todos,
                'status_filter': status,
                'total_found': len(todos),
                'limit_applied': limit
            })
            
        except Exception as e:
            return self._create_error_response(f'Todo list failed: {str(e)}')
    
    async def _action_complete(self, **params) -> Dict[str, Any]:
        """Mark todo as completed."""
        if 'todo_id' not in params:
            return self._create_error_response('Missing required parameter: todo_id')
        
        try:
            # Check if todo exists
            result = self.db.execute_sqlite(
                'SELECT title, status FROM todos WHERE id = ?', 
                (params['todo_id'],), 
                fetch='one'
            )
            
            if not result:
                return self._create_error_response(f'Todo with ID {params["todo_id"]} not found')
            
            title, current_status = result
            
            if current_status == 'completed':
                return self._create_success_response({
                    'todo_id': params['todo_id'],
                    'title': title,
                    'message': 'Todo is already completed'
                })
            
            # Mark as completed
            completed_at = datetime.now().isoformat()
            self.db.execute_sqlite('''
                UPDATE todos 
                SET status = 'completed', completed = 1, completed_at = ?
                WHERE id = ?
            ''', (completed_at, params['todo_id']))
            
            return self._create_success_response({
                'todo_id': params['todo_id'],
                'title': title,
                'status': 'completed',
                'completed_at': completed_at,
                'message': f'Todo "{title}" marked as completed'
            })
            
        except Exception as e:
            return self._create_error_response(f'Todo complete failed: {str(e)}')
    
    async def _action_search(self, **params) -> Dict[str, Any]:
        """Search todos by query string."""
        if 'query' not in params:
            return self._create_error_response('Missing required parameter: query')
        
        try:
            search_pattern = f"%{params['query']}%"
            limit = params.get('limit', 10)
            status = params.get('status')
            
            if status and status not in ['pending', 'in_progress', 'completed']:
                return self._create_error_response('status must be one of: pending, in_progress, completed')
            
            if status:
                rows = self.db.execute_sqlite('''
                    SELECT id, title, description, priority, status, completed, created_at, completed_at
                    FROM todos
                    WHERE (title LIKE ? OR description LIKE ?) AND status = ?
                    ORDER BY 
                        CASE priority 
                            WHEN 'urgent' THEN 1 
                            WHEN 'high' THEN 2 
                            WHEN 'medium' THEN 3 
                            WHEN 'low' THEN 4 
                        END,
                        created_at DESC
                    LIMIT ?
                ''', (search_pattern, search_pattern, status, limit), fetch='all')
            else:
                rows = self.db.execute_sqlite('''
                    SELECT id, title, description, priority, status, completed, created_at, completed_at
                    FROM todos
                    WHERE title LIKE ? OR description LIKE ?
                    ORDER BY 
                        CASE priority 
                            WHEN 'urgent' THEN 1 
                            WHEN 'high' THEN 2 
                            WHEN 'medium' THEN 3 
                            WHEN 'low' THEN 4 
                        END,
                        created_at DESC
                    LIMIT ?
                ''', (search_pattern, search_pattern, limit), fetch='all')
            
            todos = []
            for row in rows:
                todos.append({
                    'todo_id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'priority': row[3],
                    'status': row[4],
                    'completed': bool(row[5]),
                    'created_at': row[6],
                    'completed_at': row[7]
                })
            
            return self._create_success_response({
                'todos': todos,
                'search_query': params['query'],
                'status_filter': status,
                'total_found': len(todos),
                'limit_applied': limit
            })
            
        except Exception as e:
            return self._create_error_response(f'Todo search failed: {str(e)}')


# Create global instance for backward compatibility
async def todo_action(action: str, **params) -> Dict[str, Any]:
    """Todo management operations (backward compatibility).
    
    Actions: add, list, complete, search
    """
    todo_tools = TodoTools()
    return await todo_tools(action, **params)