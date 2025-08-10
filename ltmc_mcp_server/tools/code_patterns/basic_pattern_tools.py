"""
Basic Code Pattern Tools - FastMCP Implementation
=================================================

Basic code pattern logging and retrieval tools following FastMCP patterns.

Tools implemented:
1. log_code_attempt - Log a code attempt for pattern analysis
2. get_code_patterns - Get code patterns matching a query
"""

import logging
from typing import Dict, Any, List

# Official MCP SDK import - from research findings
from mcp.server.fastmcp import FastMCP

# Local imports
from config.settings import LTMCSettings
from services.database_service import DatabaseService
from utils.validation_utils import sanitize_user_input, validate_content_length
from utils.logging_utils import get_tool_logger


def register_basic_pattern_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """
    Register basic code pattern tools with FastMCP server.
    
    Args:
        mcp: FastMCP server instance
        settings: LTMC settings
    """
    logger = get_tool_logger('basic_patterns')
    logger.info("Registering basic code pattern tools")
    
    # Initialize services
    db_service = DatabaseService(settings)
    
    @mcp.tool()
    async def log_code_attempt(
        input_prompt: str,
        generated_code: str,
        result: str,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """
        Log a code attempt for pattern analysis.
        
        This tool logs code generation attempts with their outcomes for
        learning and pattern analysis. Essential for experience replay.
        
        Args:
            input_prompt: Original prompt or task description
            generated_code: The code that was generated
            result: Result status (pass, fail, partial, error)
            tags: Optional list of tags for categorization
            
        Returns:
            Dict with success status, pattern ID, and metadata
        """
        logger.debug(f"Logging code attempt: {result} for prompt: {input_prompt[:100]}...")
        
        try:
            # Validate inputs
            if not all([input_prompt, generated_code, result]):
                return {
                    "success": False,
                    "error": "input_prompt, generated_code, and result are required"
                }
            
            # Validate content lengths
            prompt_validation = validate_content_length(input_prompt, max_length=2000)
            if not prompt_validation.is_valid:
                return {
                    "success": False,
                    "error": f"Invalid prompt: {', '.join(prompt_validation.errors)}"
                }
            
            code_validation = validate_content_length(generated_code, max_length=10000)
            if not code_validation.is_valid:
                return {
                    "success": False,
                    "error": f"Invalid code: {', '.join(code_validation.errors)}"
                }
            
            # Validate result status
            valid_results = ['pass', 'fail', 'partial', 'error']
            result_clean = sanitize_user_input(result.lower())
            if result_clean not in valid_results:
                return {
                    "success": False,
                    "error": f"Invalid result. Must be one of: {', '.join(valid_results)}"
                }
            
            # Sanitize inputs
            prompt_clean = sanitize_user_input(input_prompt)
            code_clean = sanitize_user_input(generated_code)
            tags_clean = [sanitize_user_input(tag) for tag in tags] if tags else []
            
            # Log the code pattern
            pattern_id, vector_id = await db_service.log_code_pattern(
                input_prompt=prompt_clean,
                generated_code=code_clean,
                result=result_clean,
                execution_time_ms=None,
                error_message=None,
                tags=tags_clean
            )
            
            logger.info(f"Logged code pattern {pattern_id} with result: {result_clean}")
            
            return {
                "success": True,
                "pattern_id": pattern_id,
                "vector_id": vector_id,
                "result": result_clean,
                "tags_applied": tags_clean,
                "message": f"Code attempt logged successfully with ID {pattern_id}"
            }
            
        except Exception as e:
            logger.error(f"Error logging code attempt: {e}")
            return {
                "success": False,
                "error": f"Failed to log code attempt: {str(e)}"
            }
    
    @mcp.tool()
    async def get_code_patterns(
        query: str,
        result_filter: str = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Get code patterns matching a query.
        
        This tool retrieves previously logged code patterns that match
        a search query, optionally filtered by result status.
        
        Args:
            query: Search query to match against prompts and code
            result_filter: Optional filter by result (pass, fail, partial, error)
            top_k: Maximum number of patterns to return (1-50)
            
        Returns:
            Dict with matching patterns, total found, and search metadata
        """
        logger.debug(f"Getting code patterns for query: {query[:100]}...")
        
        try:
            # Validate inputs
            if not query or len(query.strip()) == 0:
                return {
                    "success": False,
                    "error": "Query cannot be empty"
                }
            
            query_validation = validate_content_length(query, max_length=500)
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
            
            # Validate result filter if provided
            if result_filter:
                valid_results = ['pass', 'fail', 'partial', 'error']
                result_filter_clean = sanitize_user_input(result_filter.lower())
                if result_filter_clean not in valid_results:
                    return {
                        "success": False,
                        "error": f"Invalid result_filter. Must be one of: {', '.join(valid_results)}"
                    }
            else:
                result_filter_clean = None
            
            # Sanitize query
            query_clean = sanitize_user_input(query)
            
            # For now, use simple database query by result filter and tags
            # TODO: Implement proper semantic search with query matching
            query_tags = query_clean.split()[:5]  # Simple tag extraction
            
            patterns = await db_service.get_code_patterns(
                query_tags=query_tags,
                result_filter=result_filter_clean,
                limit=top_k
            )
            
            logger.info(f"Found {len(patterns)} code patterns for query: {query_clean}")
            
            return {
                "success": True,
                "patterns": patterns,
                "query": query_clean,
                "result_filter": result_filter_clean,
                "total_found": len(patterns),
                "top_k": top_k,
                "search_metadata": {
                    "query_tags": query_tags,
                    "semantic_search": False  # TODO: Implement semantic search
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting code patterns: {e}")
            return {
                "success": False,
                "error": f"Failed to get code patterns: {str(e)}",
                "patterns": []
            }
    
    logger.info("✅ Basic code pattern tools registered successfully")
    logger.info("  - log_code_attempt: Log code attempts for pattern analysis")
    logger.info("  - get_code_patterns: Retrieve matching code patterns")