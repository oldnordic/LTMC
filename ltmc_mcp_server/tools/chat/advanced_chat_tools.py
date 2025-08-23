"""
Advanced Chat Tools - FastMCP Implementation
============================================

Advanced chat management tools following exact FastMCP patterns from research.

Tools implemented:
1. build_context - Build context windows with token limits
2. route_query - Smart query routing to best processing method
"""

from typing import Dict, Any, List

# Official MCP SDK import - from research findings
from mcp.server.fastmcp import FastMCP

# Local imports
from ltmc_mcp_server.config.settings import LTMCSettings
from ltmc_mcp_server.utils.validation_utils import sanitize_user_input
from ltmc_mcp_server.utils.logging_utils import get_tool_logger


def register_advanced_chat_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """
    Register advanced chat tools with FastMCP server.
    
    Following official FastMCP registration pattern:
    @mcp.tool()
    def tool_name(...) -> ...:
    
    Args:
        mcp: FastMCP server instance
        settings: LTMC settings
    """
    logger = get_tool_logger('chat.advanced')
    logger.info("Registering advanced chat tools")
    
    @mcp.tool()
    async def build_context(
        items: List[str],
        token_limit: int = 4000,
        prioritize_recent: bool = True
    ) -> Dict[str, Any]:
        """
        Build context windows with token limits.
        
        This tool takes a list of content items and builds an optimized context
        window that fits within token limits. It can prioritize recent content
        and truncate items to maximize relevant information.
        
        Args:
            items: List of content items to include in context
            token_limit: Maximum tokens for the context window
            prioritize_recent: Whether to prioritize recent items
            
        Returns:
            Dict with built context, token count, and items included
        """
        logger.debug(f"Building context window with {len(items)} items, limit: {token_limit}")
        
        try:
            if token_limit < 100 or token_limit > 100000:
                return {
                    "success": False,
                    "error": "token_limit must be between 100 and 100000"
                }
            
            if not items:
                return {
                    "success": True,
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
                "context": context,
                "token_count": total_tokens,
                "items_included": items_included,
                "items_truncated": items_truncated,
                "total_items": len(items)
            }
            
        except Exception as e:
            logger.error(f"Error building context: {e}")
            return {
                "success": False,
                "error": f"Failed to build context: {str(e)}",
                "context": "",
                "token_count": 0
            }
    
    @mcp.tool()
    async def route_query(
        query: str,
        available_methods: List[str] = None
    ) -> Dict[str, Any]:
        """
        Smart query routing to best processing method.
        
        This tool analyzes the query and determines the best method for processing
        based on content type, complexity, and available processing methods.
        It provides routing recommendations and confidence scores.
        
        Args:
            query: Query to analyze for routing
            available_methods: List of available processing methods
            
        Returns:
            Dict with recommended method, confidence, and reasoning
        """
        logger.debug(f"Routing query: {query[:100]}...")
        
        try:
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
                "recommended_method": recommended_method,
                "confidence": confidence,
                "reasoning": reasoning,
                "available_methods": available_methods,
                "query_processed": query_clean
            }
            
        except Exception as e:
            logger.error(f"Error routing query: {e}")
            return {
                "success": False,
                "error": f"Failed to route query: {str(e)}",
                "recommended_method": "general_query",
                "confidence": 0.0
            }
    
    logger.info("✅ Advanced chat tools registered successfully") 
    logger.info("  - build_context: Build optimized context windows")
    logger.info("  - route_query: Smart query routing")