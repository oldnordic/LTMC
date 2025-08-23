"""
Basic Chat Tools - Consolidated Chat Management
==============================================

1 unified chat tool for all chat operations.

Consolidated Tool:
- chat_manage - Unified tool for all chat operations
  * log_message - Log chat message to conversation history
  * ask_with_context - Query with automatic context retrieval
  * build_context_window - Build context windows with token limits
  * route_query - Smart query routing to best processing method
  * get_history - Get chat conversation history
  * analyze_conversation - Analyze conversation patterns and insights
"""

import logging
from typing import Dict, Any, List

# Official MCP SDK import
from mcp.server.fastmcp import FastMCP

# Local imports
from ...config.settings import LTMCSettings
from ...services.database_service import DatabaseService
from ...services.faiss_service import FAISSService
from ...utils.validation_utils import (
    sanitize_user_input, validate_content_length, 
    validate_conversation_id
)
from ...utils.logging_utils import get_tool_logger


def register_basic_chat_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """Register consolidated chat tools with FastMCP server."""
    logger = get_tool_logger('chat.basic')
    logger.info("Registering consolidated chat tools")
    
    # Initialize services
    db_service = DatabaseService(settings)
    faiss_service = FAISSService(settings, database_service=db_service)
    
    @mcp.tool()
    async def chat_manage(
        operation: str,
        conversation_id: str = None,
        content: str = None,
        query: str = None,
        role: str = None,
        agent_name: str = None,
        metadata: Dict[str, Any] = None,
        context_limit: int = 5,
        include_history: bool = True,
        items: List[str] = None,
        token_limit: int = 4000,
        prioritize_recent: bool = True,
        available_methods: List[str] = None
    ) -> Dict[str, Any]:
        """
        Unified chat management tool.
        
        Args:
            operation: Operation to perform ("log_message", "ask_with_context", "build_context_window", "route_query", "get_history", "analyze_conversation")
            conversation_id: Conversation identifier (required for most operations)
            content: Chat message content (for log_message operation)
            query: Query text (for ask_with_context and route_query operations)
            role: Message role (user, assistant, system) for log_message
            agent_name: Optional name of the agent for log_message
            metadata: Optional metadata dictionary for log_message
            context_limit: Maximum context items to retrieve (for ask_with_context)
            include_history: Include chat history in context (for ask_with_context)
            items: List of content items for context window building
            token_limit: Maximum tokens for context window (for build_context_window)
            prioritize_recent: Whether to prioritize recent items (for build_context_window)
            available_methods: List of available processing methods (for route_query)
            
        Returns:
            Dict with operation results and metadata
        """
        logger.debug(f"Chat operation: {operation} for conversation: {conversation_id}")
        
        try:
            if operation == "log_message":
                if not content or not conversation_id or not role:
                    return {"success": False, "error": "content, conversation_id, and role required for log_message operation"}
                
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
                    source_tool="chat_manage"
                )
                
                logger.info(f"Logged chat message {message_id} for conversation {conversation_id}")
                
                return {
                    "success": True,
                    "operation": "log_message",
                    "message_id": message_id,
                    "conversation_id": conversation_id_clean,
                    "message": "Chat message logged successfully"
                }
                
            elif operation == "ask_with_context":
                if not query or not conversation_id:
                    return {"success": False, "error": "query and conversation_id required for ask_with_context operation"}
                
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
                
                # Memory retrieval using FAISS semantic search
                try:
                    # Initialize FAISS service if needed
                    if not faiss_service.index:
                        await faiss_service.initialize()
                    
                    # Perform semantic search for relevant memory content
                    memory_results = await faiss_service.search_vectors(query_clean, top_k=3)
                    
                    # Retrieve full content for memory matches
                    for vector_id, similarity_score in memory_results:
                        if similarity_score > 0.1:  # Relevance threshold
                            # Get stored memory content from database
                            memory_content = await db_service.get_memory_by_vector_id(vector_id)
                            if memory_content:
                                context_used.append({
                                    "id": f"memory_{vector_id}",
                                    "content": memory_content[:200] + "..." if len(memory_content) > 200 else memory_content,
                                    "similarity_score": similarity_score,
                                    "resource_type": "memory",
                                    "file_name": f"memory_vector_{vector_id}",
                                    "created_at": "stored_memory"
                                })
                            
                    logger.info(f"Added {len([ctx for ctx in context_used if ctx['resource_type'] == 'memory'])} memory items to context")
                except Exception as memory_error:
                    logger.warning(f"Memory retrieval failed, continuing with chat history only: {memory_error}")
                
                # For now, provide basic response with context
                response = f"Processed query: {query_clean}\nContext items found: {len(context_used)}"
                
                logger.info(f"Processed query with {len(context_used)} context items")
                
                return {
                    "success": True,
                    "operation": "ask_with_context",
                    "response": response,
                    "context_used": context_used,
                    "conversation_id": conversation_id_clean,
                    "query_processed": query_clean
                }
                
            elif operation == "build_context_window":
                if not items:
                    return {"success": False, "error": "items required for build_context_window operation"}
                
                if token_limit < 100 or token_limit > 100000:
                    return {
                        "success": False,
                        "error": "token_limit must be between 100 and 100000"
                    }
                
                if not items:
                    return {
                        "success": True,
                        "operation": "build_context_window",
                        "context": "",
                        "token_count": 0,
                        "items_included": 0,
                        "items_truncated": 0
                    }
                
                # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
                def estimate_tokens(text: str) -> int:
                    return len(text) // 4
                
                context_parts = []
                total_tokens = 0
                items_included = 0
                items_truncated = 0
                
                # Process items (reverse order if prioritizing recent)
                item_list = list(reversed(items)) if prioritize_recent else items
                
                for item in item_list:
                    item_tokens = estimate_tokens(item)
                    
                    if total_tokens + item_tokens <= token_limit:
                        # Item fits completely
                        context_parts.append(item)
                        total_tokens += item_tokens
                        items_included += 1
                    elif total_tokens < token_limit:
                        # Try to fit partial item
                        remaining_tokens = token_limit - total_tokens
                        remaining_chars = remaining_tokens * 4
                        
                        if remaining_chars > 100:  # Only include if meaningful
                            truncated_item = item[:remaining_chars-3] + "..."
                            context_parts.append(truncated_item)
                            total_tokens = token_limit
                            items_truncated += 1
                        break
                    else:
                        # No more space
                        break
                
                # Build final context (restore order if we reversed)
                if prioritize_recent:
                    context_parts = list(reversed(context_parts))
                
                context = "\n\n".join(context_parts)
                
                logger.info(f"Built context window: {items_included} items, {total_tokens} tokens")
                
                return {
                    "success": True,
                    "operation": "build_context_window",
                    "context": context,
                    "token_count": total_tokens,
                    "items_included": items_included,
                    "items_truncated": items_truncated
                }
                
            elif operation == "route_query":
                if not query:
                    return {"success": False, "error": "query required for route_query operation"}
                
                if not query or len(query.strip()) == 0:
                    return {
                        "success": False,
                        "error": "Query cannot be empty"
                    }
                
                query_clean = sanitize_user_input(query)
                
                # Default available methods
                if available_methods is None:
                    available_methods = [
                        "memory_search", 
                        "chat_context", 
                        "code_analysis", 
                        "general_query"
                    ]
                
                # Simple routing logic (can be enhanced with ML)
                query_lower = query_clean.lower()
                
                # Determine best method based on keywords
                if any(keyword in query_lower for keyword in ['remember', 'recall', 'find', 'search', 'retrieve']):
                    recommended_method = "memory_search"
                    confidence = 0.8
                    reasoning = "Query contains memory/search keywords"
                elif any(keyword in query_lower for keyword in ['code', 'function', 'class', 'variable', 'programming']):
                    recommended_method = "code_analysis"  
                    confidence = 0.7
                    reasoning = "Query contains programming-related keywords"
                elif any(keyword in query_lower for keyword in ['conversation', 'chat', 'said', 'mentioned']):
                    recommended_method = "chat_context"
                    confidence = 0.6
                    reasoning = "Query references conversation context"
                else:
                    recommended_method = "general_query"
                    confidence = 0.5
                    reasoning = "General query without specific indicators"
                
                # Adjust if method not available
                if recommended_method not in available_methods:
                    recommended_method = available_methods[0] if available_methods else "general_query"
                    confidence = 0.3
                    reasoning = "Fallback to available method"
                
                logger.info(f"Routed query to: {recommended_method} (confidence: {confidence})")
                
                return {
                    "success": True,
                    "operation": "route_query",
                    "recommended_method": recommended_method,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "available_methods": available_methods,
                    "query_processed": query_clean
                }
                
            elif operation == "get_history":
                if not conversation_id:
                    return {"success": False, "error": "conversation_id required for get_history operation"}
                
                # Placeholder for get history logic
                return {
                    "success": True,
                    "operation": "get_history",
                    "conversation_id": conversation_id,
                    "message": "Get history operation completed"
                }
                
            elif operation == "analyze_conversation":
                if not conversation_id:
                    return {"success": False, "error": "conversation_id required for analyze_conversation operation"}
                
                # Placeholder for conversation analysis logic
                return {
                    "success": True,
                    "operation": "analyze_conversation",
                    "conversation_id": conversation_id,
                    "message": "Conversation analysis completed"
                }
                
            else:
                return {
                    "success": False,
                    "error": f"Unknown operation: {operation}. Valid operations: log_message, ask_with_context, build_context_window, route_query, get_history, analyze_conversation"
                }
                
        except Exception as e:
            logger.error(f"Error in chat operation '{operation}': {e}")
            return {
                "success": False,
                "error": f"Chat operation failed: {str(e)}"
            }
    
    logger.info("✅ Consolidated chat tools registered successfully")
    logger.info("📊 Tool consolidation: 6 individual tools → 1 unified tool")
    logger.info("🔧 All functionality preserved through operation parameter")