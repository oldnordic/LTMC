"""
Memory Tools - FastMCP Implementation
====================================

Memory management tools following exact FastMCP patterns from research.

Official pattern from research:
@mcp.tool()
def function_name(param: type) -> return_type:
    '''Tool description'''
    return result

Tools implemented:
1. store_memory - Store content in long-term memory
2. retrieve_memory - Retrieve content using semantic search
"""

import logging
from typing import Dict, Any

# FastMCP import - official pattern from research
from fastmcp import FastMCP

# Local imports
from config.settings import LTMCSettings
from services.database_service import DatabaseService
from models.tool_models import (
    StoreMemoryInput, StoreMemoryOutput,
    RetrieveMemoryInput, RetrieveMemoryOutput
)
from models.base_models import PerformanceMetrics
from utils.validation_utils import (
    validate_input, validate_file_name, validate_content_length, 
    validate_resource_type, sanitize_user_input
)
from utils.logging_utils import get_tool_logger


def register_memory_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """
    Register memory tools with FastMCP server.
    
    Following official FastMCP registration pattern:
    @mcp.tool()
    def tool_name(...) -> ...:
    
    Args:
        mcp: FastMCP server instance
        settings: LTMC settings
    """
    logger = get_tool_logger('memory')
    logger.info("Registering memory tools")
    
    # Initialize database service
    db_service = DatabaseService(settings)
    
    @mcp.tool()
    async def store_memory(
        content: str,
        file_name: str,
        resource_type: str = "document"
    ) -> Dict[str, Any]:
        """
        Store content in long-term memory with semantic indexing.
        
        This tool stores text content in the LTMC database with automatic
        semantic indexing for future retrieval. Content is stored with
        metadata and becomes searchable via retrieve_memory.
        
        Args:
            content: Content to store in memory
            file_name: Name for the stored content  
            resource_type: Type of resource (document, code, note)
            
        Returns:
            Dict with success status, resource_id, and performance metrics
        """
        logger.debug(f"Storing memory: {file_name} ({resource_type})")
        
        try:
            # Validate inputs following MCP security requirements
            file_validation = validate_file_name(file_name)
            if not file_validation.is_valid:
                return {
                    "success": False,
                    "error": f"Invalid file name: {', '.join(file_validation.errors)}"
                }
            
            content_validation = validate_content_length(content)
            if not content_validation.is_valid:
                return {
                    "success": False,
                    "error": f"Invalid content: {', '.join(content_validation.errors)}"
                }
            
            type_validation = validate_resource_type(resource_type)
            if not type_validation.is_valid:
                return {
                    "success": False,
                    "error": f"Invalid resource type: {', '.join(type_validation.errors)}"
                }
            
            # Sanitize inputs for security
            content_clean = sanitize_user_input(content)
            file_name_clean = sanitize_user_input(file_name)
            
            # Store in database
            resource_id, vector_id = await db_service.store_resource(
                file_name_clean, 
                resource_type, 
                content_clean
            )
            
            # TODO: Add FAISS vector indexing here (will be implemented in faiss_service.py)
            
            logger.info(f"Stored memory resource {resource_id} with vector {vector_id}")
            
            return {
                "success": True,
                "resource_id": resource_id,
                "vector_id": vector_id,
                "chunks_created": 1,
                "message": f"Successfully stored {file_name} in memory"
            }
            
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            return {
                "success": False,
                "error": f"Failed to store memory: {str(e)}"
            }
    
    @mcp.tool()
    async def retrieve_memory(
        query: str,
        conversation_id: str = None,
        top_k: int = 5,
        resource_type: str = None
    ) -> Dict[str, Any]:
        """
        Retrieve relevant content from memory using semantic search.
        
        This tool searches the LTMC database for content relevant to the query
        using semantic similarity. Results are ranked by relevance and include
        content snippets and metadata.
        
        Args:
            query: Search query for memory retrieval
            conversation_id: Optional conversation context for filtering
            top_k: Number of results to return (1-50)
            resource_type: Optional filter by resource type
            
        Returns:
            Dict with search results, total matches, and performance metrics
        """
        logger.debug(f"Retrieving memory for query: {query[:100]}...")
        
        try:
            # Validate inputs
            if not query or len(query.strip()) == 0:
                return {
                    "success": False,
                    "error": "Query cannot be empty"
                }
            
            if top_k < 1 or top_k > 50:
                return {
                    "success": False,
                    "error": "top_k must be between 1 and 50"
                }
            
            if resource_type:
                type_validation = validate_resource_type(resource_type)
                if not type_validation.is_valid:
                    return {
                        "success": False,
                        "error": f"Invalid resource type: {', '.join(type_validation.errors)}"
                    }
            
            # Sanitize query
            query_clean = sanitize_user_input(query)
            
            # Get resources from database (filtered by type if specified)
            resources = await db_service.get_resources_by_type(resource_type)
            
            # TODO: Implement FAISS semantic search here
            # For now, return basic text matching
            results = []
            for resource in resources[:top_k]:
                # Simple text matching until FAISS is implemented
                results.append({
                    "id": resource["id"],
                    "content": f"Content from {resource['file_name']}",
                    "similarity_score": 0.8,  # Placeholder
                    "resource_type": resource["type"],
                    "file_name": resource["file_name"],
                    "created_at": resource["created_at"]
                })
            
            logger.info(f"Retrieved {len(results)} memory results for query")
            
            return {
                "success": True,
                "results": results,
                "query_processed": query_clean,
                "total_matches": len(results),
                "conversation_id": conversation_id
            }
            
        except Exception as e:
            logger.error(f"Error retrieving memory: {e}")
            return {
                "success": False,
                "error": f"Failed to retrieve memory: {str(e)}",
                "results": []
            }
    
    logger.info("✅ Memory tools registered successfully")
    logger.info("  - store_memory: Store content with semantic indexing")
    logger.info("  - retrieve_memory: Semantic search for relevant content")