"""
Basic Todo Tools - Consolidated Todo Management
==============================================

1 unified todo tool for all todo operations.

Consolidated Tool:
- todo_manage - Unified tool for all todo operations
  * add - Add new todo item to the task list
  * complete - Mark todo as completed
  * list - List todos with filtering and pagination
  * search - Search todos by content in title and description
  * update - Update existing todo item
  * delete - Delete todo item
"""

import logging
from typing import Dict, Any, List, Optional

# Official MCP SDK import
from mcp.server.fastmcp import FastMCP

# Local imports
from ...config.settings import LTMCSettings
from ...services.database_service import DatabaseService
from ...utils.validation_utils import sanitize_user_input, validate_content_length, validate_priority
from ...utils.logging_utils import get_tool_logger


def register_basic_todo_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """Register consolidated todo tools with FastMCP server."""
    logger = get_tool_logger('todo.basic')
    logger.info("Registering consolidated todo tools")
    
    # Initialize database service
    db_service = DatabaseService(settings)
    
    @mcp.tool()
    async def todo_manage(
        operation: str,
        title: str = None,
        description: str = None,
        priority: str = "medium",
        todo_id: int = None,
        status: str = None,
        limit: int = 10,
        offset: int = 0,
        query: str = None
    ) -> Dict[str, Any]:
        """
        Unified todo management tool.
        
        Args:
            operation: Operation to perform ("add", "complete", "list", "search", "update", "delete")
            title: Todo title (for add/update operations)
            description: Detailed todo description (for add/update operations)
            priority: Priority level (high, medium, low) (for add/update operations)
            todo_id: ID of the todo item (for complete/update/delete operations)
            status: Filter by status (pending, completed, all) (for list/search operations)
            limit: Maximum number of todos to return (for list/search operations)
            offset: Number of todos to skip for pagination (for list operations)
            query: Search query for todo content (for search operations)
            
        Returns:
            Dict with operation results and metadata
        """
        logger.debug(f"Todo operation: {operation}")
        
        try:
            if operation == "add":
                if not title or not description:
                    return {"success": False, "error": "title and description required for add operation"}
                
                # Validate inputs
                if not title or len(title.strip()) == 0:
                    return {
                        "success": False,
                        "error": "Title cannot be empty"
                    }
                
                title_validation = validate_content_length(title, max_length=200)
                if not title_validation.is_valid:
                    return {
                        "success": False,
                        "error": f"Invalid title: {', '.join(title_validation.errors)}"
                    }
                
                desc_validation = validate_content_length(description, max_length=2000)
                if not desc_validation.is_valid:
                    return {
                        "success": False,
                        "error": f"Invalid description: {', '.join(desc_validation.errors)}"
                    }
                
                priority_validation = validate_priority(priority)
                if not priority_validation.is_valid:
                    return {
                        "success": False,
                        "error": f"Invalid priority: {', '.join(priority_validation.errors)}"
                    }
                
                # Sanitize inputs for security
                title_clean = sanitize_user_input(title.strip())
                description_clean = sanitize_user_input(description.strip())
                priority_clean = priority.lower()
                
                # Actually call the database service
                todo_id = await db_service.add_todo(
                    title_clean,
                    description_clean,
                    priority_clean
                )
                
                logger.info(f"Added todo {todo_id}: {title_clean} ({priority_clean})")
                
                return {
                    "success": True,
                    "operation": "add",
                    "todo_id": todo_id,
                    "title": title_clean,
                    "priority": priority_clean,
                    "message": f"Todo '{title_clean}' added successfully"
                }
                
            elif operation == "complete":
                if not todo_id:
                    return {"success": False, "error": "todo_id required for complete operation"}
                
                # Validate todo_id
                if not isinstance(todo_id, int) or todo_id <= 0:
                    return {
                        "success": False,
                        "error": "Todo ID must be a positive integer"
                    }
                
                # Actually call the database service
                success = await db_service.complete_todo(todo_id)
                
                if success:
                    from datetime import datetime
                    completion_time = datetime.utcnow().isoformat()
                    
                    logger.info(f"Completed todo {todo_id}")
                    
                    return {
                        "success": True,
                        "operation": "complete",
                        "todo_id": todo_id,
                        "completed_at": completion_time,
                        "message": f"Todo {todo_id} marked as completed"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Todo {todo_id} not found or already completed"
                    }
                
            elif operation == "list":
                # Validate inputs
                if limit < 1 or limit > 100:
                    return {
                        "success": False,
                        "error": "Limit must be between 1 and 100"
                    }
                
                if offset < 0:
                    return {
                        "success": False,
                        "error": "Offset cannot be negative"
                    }
                
                # Validate status if provided
                if status and status != "all":
                    valid_statuses = ['pending', 'completed']
                    if status not in valid_statuses:
                        return {
                            "success": False,
                            "error": f"Status must be one of: {', '.join(valid_statuses + ['all'])}"
                        }
                
                # Validate priority if provided
                if priority:
                    priority_validation = validate_priority(priority)
                    if not priority_validation.is_valid:
                        return {
                            "success": False,
                            "error": f"Invalid priority: {', '.join(priority_validation.errors)}"
                        }
                
                # Convert "all" status to None for database query
                status_filter = None if status == "all" else status
                priority_filter = priority.lower() if priority else None
                
                # Actually call the database service
                todos, total_count = await db_service.list_todos(
                    status=status_filter,
                    priority=priority_filter,
                    limit=limit,
                    offset=offset
                )
                
                logger.info(f"Listed {len(todos)} todos out of {total_count} total")
                
                return {
                    "success": True,
                    "operation": "list",
                    "todos": todos,
                    "total_count": total_count,
                    "filtered_count": len(todos),
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + len(todos) < total_count,
                    "message": f"Listed {len(todos)} todos"
                }
                
            elif operation == "search":
                if not query:
                    return {"success": False, "error": "query required for search operation"}
                
                # Validate inputs
                if not query or len(query.strip()) == 0:
                    return {
                        "success": False,
                        "error": "Search query cannot be empty"
                    }
                
                query_validation = validate_content_length(query, max_length=200)
                if not query_validation.is_valid:
                    return {
                        "success": False,
                        "error": f"Invalid query: {', '.join(query_validation.errors)}"
                    }
                
                if limit < 1 or limit > 50:
                    return {
                        "success": False,
                        "error": "Limit must be between 1 and 50"
                    }
                
                # Validate status if provided
                if status and status != "all":
                    valid_statuses = ['pending', 'completed']
                    if status not in valid_statuses:
                        return {
                            "success": False,
                            "error": f"Status must be one of: {', '.join(valid_statuses + ['all'])}"
                        }
                
                # Sanitize query
                query_clean = sanitize_user_input(query.strip())
                status_filter = None if status == "all" else status
                
                # Get all todos first, then filter by search query
                # This is the actual implementation from advanced_todo_tools.py
                todos, _ = await db_service.list_todos(
                    status=status_filter,
                    limit=1000  # Get more for searching
                )
                
                # Simple text search in title and description
                matching_todos = []
                query_lower = query_clean.lower()
                
                for todo in todos:
                    title_lower = todo.get('title', '').lower()
                    desc_lower = todo.get('description', '').lower()
                    
                    if query_lower in title_lower or query_lower in desc_lower:
                        # Add search relevance score (simple)
                        relevance = 0.0
                        if query_lower in title_lower:
                            relevance += 1.0
                        if query_lower in desc_lower:
                            relevance += 0.5
                            
                        todo['relevance_score'] = relevance
                        matching_todos.append(todo)
                        
                        if len(matching_todos) >= limit:
                            break
                
                # Sort by relevance score (highest first)
                matching_todos.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
                
                logger.info(f"Found {len(matching_todos)} todos matching query")
                
                return {
                    "success": True,
                    "operation": "search",
                    "todos": matching_todos,
                    "query": query_clean,
                    "status_filter": status_filter,
                    "limit": limit,
                    "total_found": len(matching_todos),
                    "message": f"Found {len(matching_todos)} matching todos"
                }
                
            elif operation == "update":
                if not todo_id or not title or not description:
                    return {"success": False, "error": "todo_id, title, and description required for update operation"}
                
                # Validate inputs
                if not isinstance(todo_id, int) or todo_id <= 0:
                    return {
                        "success": False,
                        "error": "Todo ID must be a positive integer"
                    }
                
                title_validation = validate_content_length(title, max_length=200)
                if not title_validation.is_valid:
                    return {
                        "success": False,
                        "error": f"Invalid title: {', '.join(title_validation.errors)}"
                    }
                
                desc_validation = validate_content_length(description, max_length=2000)
                if not desc_validation.is_valid:
                    return {
                        "success": False,
                        "error": f"Invalid description: {', '.join(desc_validation.errors)}"
                    }
                
                if priority:
                    priority_validation = validate_priority(priority)
                    if not priority_validation.is_valid:
                        return {
                            "success": False,
                            "error": f"Invalid priority: {', '.join(priority_validation.errors)}"
                        }
                
                # Sanitize inputs
                title_clean = sanitize_user_input(title.strip())
                description_clean = sanitize_user_input(description.strip())
                priority_clean = priority.lower() if priority else None
                
                # Actually call the database service
                success = await db_service.update_todo(
                    todo_id, title_clean, description_clean, priority_clean
                )
                
                if success:
                    logger.info(f"Updated todo {todo_id}: {title_clean}")
                    
                    return {
                        "success": True,
                        "operation": "update",
                        "todo_id": todo_id,
                        "title": title_clean,
                        "description": description_clean,
                        "priority": priority_clean,
                        "message": f"Todo {todo_id} updated successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Todo {todo_id} not found or update failed"
                    }
                
            elif operation == "delete":
                if not todo_id:
                    return {"success": False, "error": "todo_id required for delete operation"}
                
                # Validate todo_id
                if not isinstance(todo_id, int) or todo_id <= 0:
                    return {
                        "success": False,
                        "error": "Todo ID must be a positive integer"
                    }
                
                # Actually call the database service
                success = await db_service.delete_todo(todo_id)
                
                if success:
                    logger.info(f"Deleted todo {todo_id}")
                    
                    return {
                        "success": True,
                        "operation": "delete",
                        "todo_id": todo_id,
                        "message": f"Todo {todo_id} deleted successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Todo {todo_id} not found or delete failed"
                    }
                
            else:
                return {
                    "success": False,
                    "error": f"Unknown operation: {operation}. Valid operations: add, complete, list, search, update, delete"
                }
                
        except Exception as e:
            logger.error(f"Error in todo operation '{operation}': {e}")
            return {
                "success": False,
                "error": f"Todo operation failed: {str(e)}"
            }
    
    logger.info("✅ Consolidated todo tools registered successfully")
    logger.info("📊 Tool consolidation: 6 individual tools → 1 unified tool")
    logger.info("🔧 All functionality preserved through operation parameter")