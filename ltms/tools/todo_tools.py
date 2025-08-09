"""Todo and task management tools for LTMC MCP server."""

from typing import Dict, Any

# Import implementation functions
from ltms.mcp_server import (
    add_todo as _add_todo,
    list_todos as _list_todos,
    complete_todo as _complete_todo,
    search_todos as _search_todos
)


def add_todo_handler(title: str, description: str, priority: str = "medium") -> Dict[str, Any]:
    """Add a new todo item."""
    return _add_todo(title, description, priority)


def list_todos_handler(status: str = "all", limit: int = 10) -> Dict[str, Any]:
    """List todo items with optional status filtering."""
    return _list_todos(status, limit)


def complete_todo_handler(todo_id: int) -> Dict[str, Any]:
    """Mark a todo item as completed.""" 
    return _complete_todo(todo_id)


def search_todos_handler(query: str) -> Dict[str, Any]:
    """Search todo items by title or description."""
    return _search_todos(query)


# Tool definitions for MCP protocol
TODO_TOOLS = {
    "add_todo": {
        "handler": add_todo_handler,
        "description": "Add a new todo item to the task management system",
        "schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title of the todo item"
                },
                "description": {
                    "type": "string", 
                    "description": "Detailed description of the task",
                    "default": ""
                },
                "priority": {
                    "type": "string",
                    "description": "Priority level (low, medium, high)",
                    "enum": ["low", "medium", "high"],
                    "default": "medium"
                }
            },
            "required": ["title", "description"]
        }
    },
    
    "list_todos": {
        "handler": list_todos_handler,
        "description": "List todo items with optional status filtering",
        "schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter by status (all, pending, completed)",
                    "enum": ["all", "pending", "completed"],
                    "default": "all"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of todos to return",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100
                }
            }
        }
    },
    
    "complete_todo": {
        "handler": complete_todo_handler,
        "description": "Mark a specific todo item as completed",
        "schema": {
            "type": "object",
            "properties": {
                "todo_id": {
                    "type": "integer",
                    "description": "ID of the todo item to complete"
                }
            },
            "required": ["todo_id"]
        }
    },
    
    "search_todos": {
        "handler": search_todos_handler,
        "description": "Search todo items by title or description using text search",
        "schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to find matching todos"
                }
            },
            "required": ["query"]
        }
    }
}