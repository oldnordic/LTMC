"""Blueprint management tools for LTMC MCP server Phase 2."""

from typing import Dict, Any, Callable

# Import the actual implementation functions
from .blueprint_tools import (
    create_task_blueprint as _create_task_blueprint,
    analyze_task_complexity as _analyze_task_complexity,
    get_task_dependencies as _get_task_dependencies,
    update_blueprint_metadata as _update_blueprint_metadata,
    list_project_blueprints as _list_project_blueprints,
    resolve_blueprint_execution_order as _resolve_blueprint_execution_order,
    add_blueprint_dependency as _add_blueprint_dependency,
    delete_task_blueprint as _delete_task_blueprint
)


def create_task_blueprint_handler(**kwargs) -> Dict[str, Any]:
    """Create a new task blueprint with automatic complexity scoring."""
    return _create_task_blueprint(**kwargs)


def analyze_task_complexity_handler(**kwargs) -> Dict[str, Any]:
    """Analyze task complexity using ML-based scoring."""
    return _analyze_task_complexity(**kwargs)


def get_task_dependencies_handler(**kwargs) -> Dict[str, Any]:
    """Get dependencies for a task blueprint."""
    return _get_task_dependencies(**kwargs)


def update_blueprint_metadata_handler(**kwargs) -> Dict[str, Any]:
    """Update metadata for an existing blueprint."""
    return _update_blueprint_metadata(**kwargs)


def list_project_blueprints_handler(**kwargs) -> Dict[str, Any]:
    """List blueprints for a specific project with filtering."""
    return _list_project_blueprints(**kwargs)


def resolve_blueprint_execution_order_handler(**kwargs) -> Dict[str, Any]:
    """Resolve execution order for a set of blueprints based on dependencies."""
    return _resolve_blueprint_execution_order(**kwargs)


def add_blueprint_dependency_handler(**kwargs) -> Dict[str, Any]:
    """Add a dependency between two blueprints."""
    return _add_blueprint_dependency(**kwargs)


def delete_task_blueprint_handler(**kwargs) -> Dict[str, Any]:
    """Delete a task blueprint and its dependencies."""
    return _delete_task_blueprint(**kwargs)


# Tool definitions for MCP protocol
BLUEPRINT_TOOLS = {
    "create_task_blueprint": {
        "handler": create_task_blueprint_handler,
        "description": "Create a new task blueprint with automatic complexity scoring",
        "schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Blueprint title (required)"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description (required)"
                },
                "estimated_duration_minutes": {
                    "type": "integer",
                    "description": "Estimated duration in minutes",
                    "default": 60
                },
                "required_skills": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of required skills"
                },
                "priority_score": {
                    "type": "number",
                    "description": "Priority score (0.0 to 1.0)",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.5
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of tags for categorization"
                },
                "resource_requirements": {
                    "type": "object",
                    "description": "Resource requirements dictionary"
                },
                "project_id": {
                    "type": "string",
                    "description": "Project identifier for isolation"
                },
                "complexity": {
                    "type": "string",
                    "enum": ["TRIVIAL", "SIMPLE", "MODERATE", "COMPLEX", "CRITICAL"],
                    "description": "Optional explicit complexity level"
                }
            },
            "required": ["title", "description"]
        }
    },
    
    "analyze_task_complexity": {
        "handler": analyze_task_complexity_handler,
        "description": "Analyze task complexity using ML-based scoring",
        "schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Task title"
                },
                "description": {
                    "type": "string",
                    "description": "Task description"
                },
                "required_skills": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of required skills"
                }
            },
            "required": ["title", "description"]
        }
    },
    
    "get_task_dependencies": {
        "handler": get_task_dependencies_handler,
        "description": "Get dependencies for a task blueprint",
        "schema": {
            "type": "object",
            "properties": {
                "blueprint_id": {
                    "type": "string",
                    "description": "Blueprint identifier"
                }
            },
            "required": ["blueprint_id"]
        }
    },
    
    "update_blueprint_metadata": {
        "handler": update_blueprint_metadata_handler,
        "description": "Update metadata for an existing blueprint",
        "schema": {
            "type": "object",
            "properties": {
                "blueprint_id": {
                    "type": "string",
                    "description": "Blueprint to update"
                },
                "estimated_duration_minutes": {
                    "type": "integer",
                    "description": "New duration estimate"
                },
                "required_skills": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "New required skills list"
                },
                "priority_score": {
                    "type": "number",
                    "description": "New priority score",
                    "minimum": 0.0,
                    "maximum": 1.0
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "New tags list"
                },
                "resource_requirements": {
                    "type": "object",
                    "description": "New resource requirements"
                }
            },
            "required": ["blueprint_id"]
        }
    },
    
    "list_project_blueprints": {
        "handler": list_project_blueprints_handler,
        "description": "List blueprints for a specific project with filtering",
        "schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results"
                },
                "offset": {
                    "type": "integer",
                    "description": "Number of results to skip",
                    "default": 0
                },
                "min_complexity": {
                    "type": "string",
                    "enum": ["TRIVIAL", "SIMPLE", "MODERATE", "COMPLEX", "CRITICAL"],
                    "description": "Minimum complexity level"
                },
                "max_complexity": {
                    "type": "string",
                    "enum": ["TRIVIAL", "SIMPLE", "MODERATE", "COMPLEX", "CRITICAL"],
                    "description": "Maximum complexity level"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by tags"
                }
            },
            "required": ["project_id"]
        }
    },
    
    "resolve_blueprint_execution_order": {
        "handler": resolve_blueprint_execution_order_handler,
        "description": "Resolve execution order for a set of blueprints based on dependencies",
        "schema": {
            "type": "object",
            "properties": {
                "blueprint_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of blueprint IDs to order"
                }
            },
            "required": ["blueprint_ids"]
        }
    },
    
    "add_blueprint_dependency": {
        "handler": add_blueprint_dependency_handler,
        "description": "Add a dependency between two blueprints",
        "schema": {
            "type": "object",
            "properties": {
                "dependent_blueprint_id": {
                    "type": "string",
                    "description": "Blueprint that depends on prerequisite"
                },
                "prerequisite_blueprint_id": {
                    "type": "string",
                    "description": "Blueprint that must be completed first"
                },
                "dependency_type": {
                    "type": "string",
                    "enum": ["blocking", "soft", "resource"],
                    "description": "Type of dependency",
                    "default": "blocking"
                },
                "is_critical": {
                    "type": "boolean",
                    "description": "Whether this is a critical dependency",
                    "default": False
                }
            },
            "required": ["dependent_blueprint_id", "prerequisite_blueprint_id"]
        }
    },
    
    "delete_task_blueprint": {
        "handler": delete_task_blueprint_handler,
        "description": "Delete a task blueprint and its dependencies",
        "schema": {
            "type": "object",
            "properties": {
                "blueprint_id": {
                    "type": "string",
                    "description": "Blueprint to delete"
                }
            },
            "required": ["blueprint_id"]
        }
    }
}