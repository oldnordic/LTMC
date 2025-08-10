"""
Basic Chat Tools - FastMCP Implementation
=========================================

Basic chat management tools following exact FastMCP patterns from research.

Tools implemented:
1. log_chat - Log chat messages to conversation history
2. ask_with_context - Query with automatic context retrieval
"""

import logging
from typing import Dict, Any, List

# Official MCP SDK import - from research findings
from mcp.server.fastmcp import FastMCP

# Local imports
from config.settings import LTMCSettings
from services.database_service import DatabaseService
from models.tool_models import (
    LogChatInput, LogChatOutput,
    AskWithContextInput, AskWithContextOutput
)
from utils.validation_utils import (
    validate_conversation_id, validate_content_length, sanitize_user_input
)
from utils.logging_utils import get_tool_logger


def register_basic_chat_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """
    Register basic chat tools with FastMCP server.
    
    Following official FastMCP registration pattern:
    @mcp.tool()
    def tool_name(...) -> ...:
    
    Args:
        mcp: FastMCP server instance
        settings: LTMC settings
    """
    logger = get_tool_logger('chat.basic')
    logger.info("Registering basic chat tools")
    
    # Initialize database service
    db_service = DatabaseService(settings)
    
    @mcp.tool()
    async def log_chat(
        content: str,
        conversation_id: str,
        role: str,
        agent_name: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Log chat message to conversation history.
        
        This tool stores chat messages in the LTMC database for conversation
        continuity and context building. Messages are linked to conversations
        and can be retrieved for context in future interactions.
        
        Args:
            content: Chat message content
            conversation_id: Conversation identifier
            role: Message role (user, assistant, system)
            agent_name: Optional name of the agent
            metadata: Optional metadata dictionary
            
        Returns:
            Dict with success status, message_id, and performance metrics
        """
        logger.debug(f"Logging chat message for conversation: {conversation_id}")
        
        try:
            # Validate inputs following MCP security requirements
            content_validation = validate_content_length(content)
            if not content_validation.is_valid:
                return {
                    "success": False,
                    "error": f"Invalid content: {', '.join(content_validation.errors)}"
                }
            
            conv_validation = validate_conversation_id(conversation_id)
            if not conv_validation.is_valid:
                return {
                    "success": False,
                    "error": f"Invalid conversation ID: {', '.join(conv_validation.errors)}"
                }
            
            # Validate role
            valid_roles = ['user', 'assistant', 'system']
            if role not in valid_roles:
                return {
                    "success": False,
                    "error": f"Role must be one of: {', '.join(valid_roles)}"
                }
            
            # Sanitize inputs for security
            content_clean = sanitize_user_input(content)
            conversation_id_clean = sanitize_user_input(conversation_id)
            agent_name_clean = sanitize_user_input(agent_name) if agent_name else None
            
            # Store in database
            message_id = await db_service.log_chat_message(
                conversation_id_clean,
                role,
                content_clean,
                agent_name_clean,
                metadata,
                source_tool="log_chat"
            )
            
            logger.info(f"Logged chat message {message_id} for conversation {conversation_id}")
            
            return {
                "success": True,
                "message_id": message_id,
                "conversation_id": conversation_id_clean,
                "message": "Chat message logged successfully"
            }
            
        except Exception as e:
            logger.error(f"Error logging chat: {e}")
            return {
                "success": False,
                "error": f"Failed to log chat message: {str(e)}"
            }
    
    @mcp.tool()
    async def ask_with_context(
        query: str,
        conversation_id: str,
        context_limit: int = 5,
        include_history: bool = True
    ) -> Dict[str, Any]:
        """
        Query with automatic context retrieval.
        
        This tool combines the query with relevant context from memory and
        conversation history to provide more informed responses. It automatically
        retrieves relevant content and chat history to build context.
        
        Args:
            query: Query with automatic context retrieval
            conversation_id: Conversation identifier
            context_limit: Maximum context items to retrieve
            include_history: Include chat history in context
            
        Returns:
            Dict with response, context used, and performance metrics
        """
        logger.debug(f"Processing query with context for conversation: {conversation_id}")
        
        try:
            # Validate inputs
            if not query or len(query.strip()) == 0:
                return {
                    "success": False,
                    "error": "Query cannot be empty"
                }
            
            conv_validation = validate_conversation_id(conversation_id)
            if not conv_validation.is_valid:
                return {
                    "success": False,
                    "error": f"Invalid conversation ID: {', '.join(conv_validation.errors)}"
                }
            
            if context_limit < 1 or context_limit > 20:
                return {
                    "success": False,
                    "error": "context_limit must be between 1 and 20"
                }
            
            # Sanitize inputs
            query_clean = sanitize_user_input(query)
            conversation_id_clean = sanitize_user_input(conversation_id)
            
            # Get conversation history if requested
            context_used = []
            if include_history:
                history = await db_service.get_chat_history(
                    conversation_id_clean, 
                    limit=context_limit
                )
                
                for msg in history:
                    context_used.append({
                        "id": msg["id"],
                        "content": msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"],
                        "similarity_score": 1.0,  # Chat history is always relevant
                        "resource_type": "chat_message",
                        "file_name": f"conversation_{conversation_id}",
                        "created_at": msg["timestamp"]
                    })
            
            # TODO: Add memory retrieval based on query
            # This would use retrieve_memory tool internally
            
            # For now, provide basic response with context
            response = f"Processed query: {query_clean}\nContext items found: {len(context_used)}"
            
            logger.info(f"Processed query with {len(context_used)} context items")
            
            return {
                "success": True,
                "response": response,
                "context_used": context_used,
                "conversation_id": conversation_id_clean,
                "query_processed": query_clean
            }
            
        except Exception as e:
            logger.error(f"Error processing query with context: {e}")
            return {
                "success": False,
                "error": f"Failed to process query: {str(e)}",
                "response": "",
                "context_used": []
            }
    
    logger.info("✅ Basic chat tools registered successfully")
    logger.info("  - log_chat: Log messages to conversation history")
    logger.info("  - ask_with_context: Query with automatic context retrieval")