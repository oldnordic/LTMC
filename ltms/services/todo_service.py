"""Todo and task management service for LTMC."""

import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from ltms.config.json_config_loader import get_config
from ltms.database.connection import get_db_connection, close_db_connection
from ltms.database.schema import create_tables


def add_todo(title: str, description: str, priority: str = "medium") -> Dict[str, Any]:
    """Add a new todo item.
    
    Args:
        title: Brief title for the todo item
        description: Detailed description of the todo
        priority: Priority level ('low', 'medium', 'high', 'urgent')
        
    Returns:
        Dictionary with success status and todo_id
    """
    if not title or not description:
        return {
            'success': False,
            'error': 'title and description are required'
        }
    
    if priority not in ['low', 'medium', 'high', 'urgent']:
        return {
            'success': False,
            'error': 'priority must be one of: low, medium, high, urgent'
        }
    
    conn = None
    try:
        # Get database connection
        config = get_config()
        db_path = config.get_db_path()
        conn = get_db_connection(db_path)
        
        # Ensure tables exist
        create_tables(conn)
        
        cursor = conn.cursor()
        created_at = datetime.now(timezone.utc).isoformat()
        
        cursor.execute(
            """
            INSERT INTO todos (title, description, priority, status, completed, created_at)
            VALUES (?, ?, ?, 'pending', 0, ?)
            """,
            (title, description, priority, created_at)
        )
        
        conn.commit()
        todo_id = cursor.lastrowid
        
        return {
            'success': True,
            'todo_id': todo_id,
            'title': title,
            'priority': priority,
            'status': 'pending',
            'message': f'Todo "{title}" created successfully'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        if conn:
            close_db_connection(conn)


def list_todos(status: str = "all", limit: int = 10) -> Dict[str, Any]:
    """List todo items with optional status filtering.
    
    Args:
        status: Filter by status ('all', 'pending', 'in_progress', 'completed')
        limit: Maximum number of todos to return
        
    Returns:
        Dictionary with todo items list
    """
    conn = None
    try:
        # Get database connection
        config = get_config()
        db_path = config.get_db_path()
        conn = get_db_connection(db_path)
        
        cursor = conn.cursor()
        
        # Build query based on status filter
        if status == "all":
            query = """
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
            """
            params = (limit,)
        else:
            if status not in ['pending', 'in_progress', 'completed']:
                return {
                    'success': False,
                    'error': 'status must be one of: all, pending, in_progress, completed'
                }
            
            query = """
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
            """
            params = (status, limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        todos = []
        for row in rows:
            todo_id, title, description, priority, todo_status, completed, created_at, completed_at = row
            
            todos.append({
                'todo_id': todo_id,
                'title': title,
                'description': description,
                'priority': priority,
                'status': todo_status,
                'completed': bool(completed),
                'created_at': created_at,
                'completed_at': completed_at
            })
        
        return {
            'success': True,
            'todos': todos,
            'status_filter': status,
            'total_found': len(todos),
            'limit_applied': limit
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        if conn:
            close_db_connection(conn)


def complete_todo(todo_id: int) -> Dict[str, Any]:
    """Mark a todo item as completed.
    
    Args:
        todo_id: ID of the todo item to complete
        
    Returns:
        Dictionary with success status and updated todo info
    """
    if not todo_id:
        return {
            'success': False,
            'error': 'todo_id is required'
        }
    
    conn = None
    try:
        # Get database connection
        config = get_config()
        db_path = config.get_db_path()
        conn = get_db_connection(db_path)
        
        cursor = conn.cursor()
        
        # Check if todo exists
        cursor.execute("SELECT title, status FROM todos WHERE id = ?", (todo_id,))
        result = cursor.fetchone()
        
        if not result:
            return {
                'success': False,
                'error': f'Todo with ID {todo_id} not found'
            }
        
        title, current_status = result
        
        if current_status == 'completed':
            return {
                'success': True,
                'todo_id': todo_id,
                'title': title,
                'message': 'Todo is already completed'
            }
        
        # Mark as completed
        completed_at = datetime.now().isoformat()
        cursor.execute(
            """
            UPDATE todos 
            SET status = 'completed', completed = 1, completed_at = ?
            WHERE id = ?
            """,
            (completed_at, todo_id)
        )
        
        conn.commit()
        
        return {
            'success': True,
            'todo_id': todo_id,
            'title': title,
            'status': 'completed',
            'completed_at': completed_at,
            'message': f'Todo "{title}" marked as completed'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        if conn:
            close_db_connection(conn)


def search_todos(query: str, status: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    """Search todo items by text content.
    
    Args:
        query: Search text to match against title and description
        status: Optional status filter ('pending', 'in_progress', 'completed')
        limit: Maximum number of results to return
        
    Returns:
        Dictionary with matching todo items
    """
    if not query:
        return {
            'success': False,
            'error': 'query is required'
        }
    
    conn = None
    try:
        # Get database connection
        config = get_config()
        db_path = config.get_db_path()
        conn = get_db_connection(db_path)
        
        cursor = conn.cursor()
        
        # Build search query
        search_pattern = f"%{query}%"
        
        if status is not None:
            if status not in ['pending', 'in_progress', 'completed']:
                return {
                    'success': False,
                    'error': 'status must be one of: pending, in_progress, completed'
                }
            
            sql_query = """
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
            """
            params = (search_pattern, search_pattern, status, limit)
        else:
            sql_query = """
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
            """
            params = (search_pattern, search_pattern, limit)
        
        cursor.execute(sql_query, params)
        rows = cursor.fetchall()
        
        todos = []
        for row in rows:
            todo_id, title, description, priority, todo_status, completed, created_at, completed_at = row
            
            todos.append({
                'todo_id': todo_id,
                'title': title,
                'description': description,
                'priority': priority,
                'status': todo_status,
                'completed': bool(completed),
                'created_at': created_at,
                'completed_at': completed_at
            })
        
        return {
            'success': True,
            'todos': todos,
            'search_query': query,
            'status_filter': status,
            'total_found': len(todos),
            'limit_applied': limit
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        if conn:
            close_db_connection(conn)


def update_todo(todo_id: int, title: Optional[str] = None, description: Optional[str] = None, 
                priority: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
    """Update an existing todo item.
    
    Args:
        todo_id: ID of the todo to update
        title: New title (optional)
        description: New description (optional)
        priority: New priority (optional)
        status: New status (optional)
        
    Returns:
        Dictionary with success status and updated todo info
    """
    if not todo_id:
        return {
            'success': False,
            'error': 'todo_id is required'
        }
    
    # Validate priority if provided
    if priority and priority not in ['low', 'medium', 'high', 'urgent']:
        return {
            'success': False,
            'error': 'priority must be one of: low, medium, high, urgent'
        }
    
    # Validate status if provided
    if status and status not in ['pending', 'in_progress', 'completed']:
        return {
            'success': False,
            'error': 'status must be one of: pending, in_progress, completed'
        }
    
    conn = None
    try:
        # Get database connection
        config = get_config()
        db_path = config.get_db_path()
        conn = get_db_connection(db_path)
        
        cursor = conn.cursor()
        
        # Check if todo exists
        cursor.execute("SELECT title FROM todos WHERE id = ?", (todo_id,))
        result = cursor.fetchone()
        
        if not result:
            return {
                'success': False,
                'error': f'Todo with ID {todo_id} not found'
            }
        
        # Build update query dynamically
        update_fields = []
        params = []
        
        if title:
            update_fields.append("title = ?")
            params.append(title)
        
        if description:
            update_fields.append("description = ?")
            params.append(description)
        
        if priority:
            update_fields.append("priority = ?")
            params.append(priority)
        
        if status:
            update_fields.append("status = ?")
            params.append(status)
            
            # If marking as completed, set completed fields
            if status == 'completed':
                update_fields.append("completed = 1")
                update_fields.append("completed_at = ?")
                params.append(datetime.now().isoformat())
            elif status in ['pending', 'in_progress']:
                # If changing from completed to pending/in_progress, clear completion
                update_fields.append("completed = 0")
                update_fields.append("completed_at = NULL")
        
        if not update_fields:
            return {
                'success': False,
                'error': 'At least one field must be provided for update'
            }
        
        # Add todo_id to params for WHERE clause
        params.append(todo_id)
        
        # Execute update
        update_query = f"UPDATE todos SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(update_query, params)
        conn.commit()
        
        # Get updated todo
        cursor.execute(
            """
            SELECT id, title, description, priority, status, completed, created_at, completed_at
            FROM todos WHERE id = ?
            """,
            (todo_id,)
        )
        
        row = cursor.fetchone()
        if row:
            updated_todo = {
                'todo_id': row[0],
                'title': row[1],
                'description': row[2],
                'priority': row[3],
                'status': row[4],
                'completed': bool(row[5]),
                'created_at': row[6],
                'completed_at': row[7]
            }
        
        return {
            'success': True,
            'todo': updated_todo,
            'message': f'Todo "{updated_todo["title"]}" updated successfully'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        if conn:
            close_db_connection(conn)


def delete_todo(todo_id: int) -> Dict[str, Any]:
    """Delete a todo item.
    
    Args:
        todo_id: ID of the todo to delete
        
    Returns:
        Dictionary with success status
    """
    if not todo_id:
        return {
            'success': False,
            'error': 'todo_id is required'
        }
    
    conn = None
    try:
        # Get database connection
        config = get_config()
        db_path = config.get_db_path()
        conn = get_db_connection(db_path)
        
        cursor = conn.cursor()
        
        # Check if todo exists and get title
        cursor.execute("SELECT title FROM todos WHERE id = ?", (todo_id,))
        result = cursor.fetchone()
        
        if not result:
            return {
                'success': False,
                'error': f'Todo with ID {todo_id} not found'
            }
        
        title = result[0]
        
        # Delete the todo
        cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        conn.commit()
        
        return {
            'success': True,
            'todo_id': todo_id,
            'title': title,
            'message': f'Todo "{title}" deleted successfully'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        if conn:
            close_db_connection(conn)