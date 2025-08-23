"""Todo group tools - canonical group:operation interface."""

from typing import Dict, Any

# Import existing implementations
from ltms.services.todo_service import (
    add_todo as _add_todo,
    list_todos as _list_todos,
    complete_todo as _complete_todo,
    search_todos as _search_todos
)


def todo_add(title: str, description: str = "", priority: str = "medium") -> Dict[str, Any]:
    """Add a new todo/task."""
    return _add_todo(title, description, priority)


def todo_list(status: str = "all", limit: int = 10) -> Dict[str, Any]:
    """List/search todos."""
    return _list_todos(status, limit)


def todo_complete(todo_id: int) -> Dict[str, Any]:
    """Mark todo as complete."""
    return _complete_todo(todo_id)


def todo_search(query: str, status: str = None, limit: int = 10) -> Dict[str, Any]:
    """Search todos by text."""
    return _search_todos(query, status, limit)


# Tool registry with group:operation names
TODO_GROUP_TOOLS = {
    "todo:add": {
        "handler": todo_add,
        "description": "Add a new todo/task",
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
            "required": ["title"]
        }
    },
    
    "todo:list": {
        "handler": todo_list,
        "description": "List/search todos",
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
    
    "todo:complete": {
        "handler": todo_complete,
        "description": "Mark todo as complete",
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
    
    "todo:search": {
        "handler": todo_search,
        "description": "Search todos by text",
        "schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to find matching todos"
                },
                "status": {
                    "type": "string",
                    "description": "Optional status filter (pending, in_progress, completed)",
                    "enum": ["pending", "in_progress", "completed"]
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of todos to return",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100
                }
            },
            "required": ["query"]
        }
    }
}