"""
Advanced Tools - FastMCP Implementation
=======================================

Advanced analytics and context tools following exact FastMCP patterns from research.

Tools implemented (from unified_mcp_server.py analysis):
1. get_context_usage_statistics - Get comprehensive context usage statistics
2. advanced_context_search - Perform advanced context search with filters
"""

import logging
from typing import Dict, Any, Optional, List

# Official MCP SDK import - from research findings
from mcp.server.fastmcp import FastMCP

# Local imports
from config.settings import LTMCSettings
from services.database_service import DatabaseService
from services.faiss_service import FAISSService
from utils.validation_utils import sanitize_user_input, validate_content_length
from utils.logging_utils import get_tool_logger


def register_advanced_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """
    Register advanced analytics tools with FastMCP server.
    
    Following official FastMCP registration pattern:
    @mcp.tool()
    def tool_name(...) -> ...
    
    Args:
        mcp: FastMCP server instance
        settings: LTMC settings
    """
    logger = get_tool_logger('advanced')
    logger.info("Registering advanced analytics tools")
    
    # Initialize services
    db_service = DatabaseService(settings)
    faiss_service = FAISSService(settings)
    
    @mcp.tool()
    async def get_context_usage_statistics() -> Dict[str, Any]:
        """
        Get comprehensive context usage statistics.
        
        This tool provides detailed analytics about context usage patterns,
        query frequencies, and system performance metrics.
        
        Returns:
            Dict with comprehensive context usage statistics and analytics
        """
        logger.debug("Getting context usage statistics")
        
        try:
            # Get basic chat statistics
            chat_history = await db_service.get_chat_history("all_conversations", limit=1000)
            
            if not chat_history:
                return {
                    "success": True,
                    "statistics": {
                        "total_conversations": 0,
                        "total_messages": 0,
                        "message": "No conversation data available"
                    }
                }
            
            # Analyze conversation patterns
            total_messages = len(chat_history)
            user_messages = sum(1 for msg in chat_history if msg.get('role') == 'user')
            assistant_messages = sum(1 for msg in chat_history if msg.get('role') == 'assistant')
            
            # Get unique conversation IDs
            conversation_ids = set(msg.get('conversation_id', 'unknown') for msg in chat_history)
            total_conversations = len(conversation_ids)
            
            # Analyze message lengths
            message_lengths = [len(msg.get('content', '')) for msg in chat_history]
            avg_message_length = sum(message_lengths) / len(message_lengths) if message_lengths else 0
            
            # Count agent usage if available
            agent_usage = {}
            for msg in chat_history:
                agent = msg.get('agent_name', 'unknown')
                agent_usage[agent] = agent_usage.get(agent, 0) + 1
            
            # Top agents by usage
            top_agents = sorted(agent_usage.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Recent activity (last 50 messages)
            recent_messages = chat_history[:50] if len(chat_history) >= 50 else chat_history
            recent_user_messages = sum(1 for msg in recent_messages if msg.get('role') == 'user')
            recent_activity_rate = len(recent_messages) / min(len(chat_history), 50) if chat_history else 0
            
            logger.info(f"Generated context usage statistics: {total_messages} messages, {total_conversations} conversations")
            
            return {
                "success": True,
                "statistics": {
                    "conversations": {
                        "total_conversations": total_conversations,
                        "total_messages": total_messages,
                        "user_messages": user_messages,
                        "assistant_messages": assistant_messages,
                        "avg_messages_per_conversation": total_messages / total_conversations if total_conversations > 0 else 0
                    },
                    "content_analysis": {
                        "avg_message_length": round(avg_message_length, 2),
                        "total_content_characters": sum(message_lengths),
                        "content_density": "high" if avg_message_length > 500 else "medium" if avg_message_length > 100 else "low"
                    },
                    "agent_usage": {
                        "unique_agents": len(agent_usage),
                        "top_agents": top_agents,
                        "total_agent_interactions": sum(agent_usage.values())
                    },
                    "activity_patterns": {
                        "recent_messages_analyzed": len(recent_messages),
                        "recent_user_messages": recent_user_messages,
                        "recent_activity_score": round(recent_activity_rate, 3)
                    }
                },
                "insights": [
                    f"System has processed {total_messages} messages across {total_conversations} conversations",
                    f"Average message length indicates {('detailed' if avg_message_length > 500 else 'moderate' if avg_message_length > 100 else 'brief')} communication style",
                    f"Most active agent: {top_agents[0][0] if top_agents else 'none'}" + (f" ({top_agents[0][1]} interactions)" if top_agents else ""),
                    "Context system shows regular usage patterns" if recent_activity_rate > 0.8 else "Context usage could be improved"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting context usage statistics: {e}")
            return {
                "success": False,
                "error": f"Failed to get context statistics: {str(e)}",
                "statistics": {}
            }
    
    @mcp.tool()
    async def advanced_context_search(
        query: str,
        filters: Dict[str, Any] = None,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Perform advanced context search with filters.
        
        This tool provides sophisticated context search capabilities with
        advanced filtering, ranking, and result customization.
        
        Args:
            query: Search query string
            filters: Optional filters dict (conversation_id, date_range, agent_name, etc.)
            top_k: Maximum number of results to return (1-50)
            
        Returns:
            Dict with filtered search results and metadata
        """
        logger.debug(f"Performing advanced context search: {query[:100]}...")
        
        try:
            # Validate inputs
            if not query or len(query.strip()) == 0:
                return {
                    "success": False,
                    "error": "Query cannot be empty"
                }
            
            query_validation = validate_content_length(query, max_length=1000)
            if not query_validation.is_valid:
                return {
                    "success": False,
                    "error": f"Invalid query: {', '.join(query_validation.errors)}"
                }
            
            if top_k < 1 or top_k > 50:
                return {
                    "success": False,
                    "error": "top_k must be between 1 and 50"
                }
            
            # Sanitize inputs
            query_clean = sanitize_user_input(query)
            filters = filters or {}
            
            # Extract filter parameters
            conversation_filter = sanitize_user_input(filters.get('conversation_id', '')) if filters.get('conversation_id') else None
            agent_filter = sanitize_user_input(filters.get('agent_name', '')) if filters.get('agent_name') else None
            role_filter = sanitize_user_input(filters.get('role', '')) if filters.get('role') else None
            
            # For now, use basic database search with filtering
            # TODO: Implement advanced semantic search with FAISS
            
            # Get chat history with basic filtering
            if conversation_filter:
                chat_results = await db_service.get_chat_history(conversation_filter, limit=top_k * 2)
            else:
                chat_results = await db_service.get_chat_history("all_conversations", limit=top_k * 2)
            
            if not chat_results:
                return {
                    "success": True,
                    "results": [],
                    "query": query_clean,
                    "filters_applied": filters,
                    "total_found": 0,
                    "message": "No matching results found"
                }
            
            # Apply additional filters
            filtered_results = []
            for msg in chat_results:
                # Filter by agent name
                if agent_filter and msg.get('agent_name', '').lower() != agent_filter.lower():
                    continue
                    
                # Filter by role
                if role_filter and msg.get('role', '').lower() != role_filter.lower():
                    continue
                
                # Simple content matching (case-insensitive)
                content = msg.get('content', '').lower()
                if query_clean.lower() in content:
                    # Calculate relevance score (simple word matching)
                    query_words = query_clean.lower().split()
                    matches = sum(1 for word in query_words if word in content)
                    relevance_score = matches / len(query_words) if query_words else 0
                    
                    result = {
                        "id": msg.get('id', 'unknown'),
                        "content": msg.get('content', ''),
                        "conversation_id": msg.get('conversation_id', 'unknown'),
                        "role": msg.get('role', 'unknown'),
                        "agent_name": msg.get('agent_name', 'unknown'),
                        "created_at": msg.get('created_at', ''),
                        "relevance_score": round(relevance_score, 3),
                        "content_length": len(msg.get('content', ''))
                    }
                    filtered_results.append(result)
            
            # Sort by relevance score (highest first)
            filtered_results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Limit to top_k results
            final_results = filtered_results[:top_k]
            
            logger.info(f"Advanced context search returned {len(final_results)} results for query: {query_clean}")
            
            return {
                "success": True,
                "results": final_results,
                "query": query_clean,
                "filters_applied": {
                    "conversation_id": conversation_filter,
                    "agent_name": agent_filter,
                    "role": role_filter
                },
                "total_found": len(final_results),
                "search_metadata": {
                    "total_scanned": len(chat_results),
                    "post_filter_matches": len(filtered_results),
                    "returned_results": len(final_results),
                    "search_type": "content_matching",  # TODO: Upgrade to semantic search
                    "avg_relevance_score": sum(r['relevance_score'] for r in final_results) / len(final_results) if final_results else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error performing advanced context search: {e}")
            return {
                "success": False,
                "error": f"Failed to perform advanced search: {str(e)}",
                "results": []
            }
    
    logger.info("✅ Advanced analytics tools registered successfully")
    logger.info("  - get_context_usage_statistics: Comprehensive context analytics")
    logger.info("  - advanced_context_search: Advanced search with filtering")