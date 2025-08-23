"""
Advanced Todo Tools - FastMCP Implementation
============================================

Advanced todo management tools following exact FastMCP patterns from research.

Tools implemented:
1. list_todos - List todos with filtering and pagination
2. search_todos - Search todos by content
"""

from typing import Dict, Any, Tuple, List

# Official MCP SDK import - from research findings
from mcp.server.fastmcp import FastMCP

# Local imports
from ltmc_mcp_server.config.settings import LTMCSettings
from ltmc_mcp_server.services.database_service import DatabaseService
from ltmc_mcp_server.models.tool_models import ListTodosInput, ListTodosOutput
from ltmc_mcp_server.utils.validation_utils import (
    validate_content_length, validate_priority, sanitize_user_input
)
from ltmc_mcp_server.utils.logging_utils import get_tool_logger


def register_advanced_todo_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """
    Register advanced todo tools with FastMCP server.
    
    Following official FastMCP registration pattern:
    @mcp.tool()
    def tool_name(...) -> ...:
    
    Args:
        mcp: FastMCP server instance
        settings: LTMC settings
    """
    logger = get_tool_logger('todo.advanced')
    logger.info("Registering advanced todo tools")
    
    # Initialize database service
    db_service = DatabaseService(settings)
    
    @mcp.tool()
    async def list_todos(
        status: str = None,
        priority: str = None,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List todos with filtering and pagination.
        
        This tool retrieves todos from the database with optional filtering
        by status and priority. Results are paginated to handle large todo lists
        efficiently.
        
        Args:
            status: Filter by status (pending, completed, all)
            priority: Filter by priority (high, medium, low)  
            limit: Maximum number of todos to return (1-100)
            offset: Number of todos to skip for pagination
            
        Returns:
            Dict with todos list, total count, and performance metrics
        """
        logger.debug(f"Listing todos: status={status}, priority={priority}, limit={limit}")
        
        try:
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
            
            # Get todos from database
            todos, total_count = await db_service.list_todos(
                status=status_filter,
                priority=priority_filter,
                limit=limit,
                offset=offset
            )
            
            logger.info(f"Listed {len(todos)} todos out of {total_count} total")
            
            return {
                "success": True,
                "todos": todos,
                "total_count": total_count,
                "filtered_count": len(todos),
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(todos) < total_count
            }
            
        except Exception as e:
            logger.error(f"Error listing todos: {e}")
            return {
                "success": False,
                "error": f"Failed to list todos: {str(e)}",
                "todos": [],
                "total_count": 0
            }
    
    @mcp.tool()
    async def search_todos(
        query: str,
        status: str = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search todos by content in title and description.
        
        This tool searches through todo titles and descriptions to find
        matching items. Search is case-insensitive and supports partial
        matching for flexible todo retrieval.
        
        Args:
            query: Search query for todo content
            status: Optional status filter (pending, completed, all)
            limit: Maximum number of results to return
            
        Returns:
            Dict with matching todos, search query, and performance metrics
        """
        logger.debug(f"Searching todos for: {query[:100]}...")
        
        try:
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
            # TODO: Implement proper full-text search in database
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
                "todos": matching_todos,
                "query_processed": query_clean,
                "total_matches": len(matching_todos),
                "status_filter": status,
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"Error searching todos: {e}")
            return {
                "success": False,
                "error": f"Failed to search todos: {str(e)}",
                "todos": [],
                "total_matches": 0
            }
    
    logger.info("✅ Advanced todo tools registered successfully")
    logger.info("  - list_todos: List todos with filtering")
    logger.info("  - search_todos: Search todos by content")