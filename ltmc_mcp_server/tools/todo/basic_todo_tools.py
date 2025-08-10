"""
Basic Todo Tools - FastMCP Implementation
==========================================

Basic todo management tools following exact FastMCP patterns from research.

Tools implemented:
1. add_todo - Add new todo item
2. complete_todo - Mark todo as completed
"""

import logging
from typing import Dict, Any

# Official MCP SDK import - from research findings
from mcp.server.fastmcp import FastMCP

# Local imports
from config.settings import LTMCSettings
from services.database_service import DatabaseService
from models.tool_models import (
    AddTodoInput, AddTodoOutput,
    CompleteTodoInput, CompleteTodoOutput
)
from utils.validation_utils import (
    validate_content_length, validate_priority, sanitize_user_input
)
from utils.logging_utils import get_tool_logger


def register_basic_todo_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """
    Register basic todo tools with FastMCP server.
    
    Following official FastMCP registration pattern:
    @mcp.tool()
    def tool_name(...) -> ...:
    
    Args:
        mcp: FastMCP server instance
        settings: LTMC settings
    """
    logger = get_tool_logger('todo.basic')
    logger.info("Registering basic todo tools")
    
    # Initialize database service
    db_service = DatabaseService(settings)
    
    @mcp.tool()
    async def add_todo(
        title: str,
        description: str,
        priority: str = "medium"
    ) -> Dict[str, Any]:
        """
        Add new todo item to the task list.
        
        This tool creates a new todo item with title, description, and priority.
        Todos are stored in the database and can be retrieved, filtered, and
        marked as completed using other todo tools.
        
        Args:
            title: Todo title (brief description)
            description: Detailed todo description
            priority: Priority level (high, medium, low)
            
        Returns:
            Dict with success status, todo_id, and performance metrics
        """
        logger.debug(f"Adding todo: {title} ({priority})")
        
        try:
            # Validate inputs following MCP security requirements
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
            
            # Store in database
            todo_id = await db_service.add_todo(
                title_clean,
                description_clean,
                priority_clean
            )
            
            logger.info(f"Added todo {todo_id}: {title_clean} ({priority_clean})")
            
            return {
                "success": True,
                "todo_id": todo_id,
                "title": title_clean,
                "priority": priority_clean,
                "message": f"Todo '{title_clean}' added successfully"
            }
            
        except Exception as e:
            logger.error(f"Error adding todo: {e}")
            return {
                "success": False,
                "error": f"Failed to add todo: {str(e)}"
            }
    
    @mcp.tool()
    async def complete_todo(todo_id: int) -> Dict[str, Any]:
        """
        Mark todo as completed.
        
        This tool marks a todo item as completed by updating its status
        in the database. Once completed, the todo will have a completion
        timestamp and won't appear in pending todo lists.
        
        Args:
            todo_id: ID of the todo item to complete
            
        Returns:
            Dict with success status, completion timestamp, and performance metrics
        """
        logger.debug(f"Completing todo: {todo_id}")
        
        try:
            # Validate todo_id
            if not isinstance(todo_id, int) or todo_id <= 0:
                return {
                    "success": False,
                    "error": "Todo ID must be a positive integer"
                }
            
            # Complete todo in database
            success = await db_service.complete_todo(todo_id)
            
            if success:
                from datetime import datetime
                completion_time = datetime.utcnow().isoformat()
                
                logger.info(f"Completed todo {todo_id}")
                
                return {
                    "success": True,
                    "todo_id": todo_id,
                    "completed_at": completion_time,
                    "message": f"Todo {todo_id} marked as completed"
                }
            else:
                return {
                    "success": False,
                    "error": f"Todo {todo_id} not found or already completed"
                }
            
        except Exception as e:
            logger.error(f"Error completing todo: {e}")
            return {
                "success": False,
                "error": f"Failed to complete todo: {str(e)}"
            }
    
    logger.info("✅ Basic todo tools registered successfully")
    logger.info("  - add_todo: Create new todo items")
    logger.info("  - complete_todo: Mark todos as completed")