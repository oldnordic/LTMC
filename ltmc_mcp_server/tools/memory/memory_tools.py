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

from typing import Dict, Any

# Local imports  
from ...config.settings import LTMCSettings
from ...services.database_service import DatabaseService
from ...utils.validation_utils import (
    validate_file_name, validate_content_length, 
    validate_resource_type, sanitize_user_input
)
from ...utils.logging_utils import get_tool_logger

# Global logger for memory tools
logger = get_tool_logger('memory')

# Global database service instance (will be initialized when tools are called)
_db_service = None


def _get_db_service(settings: LTMCSettings) -> DatabaseService:
    """Get or create database service instance."""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService(settings)
    return _db_service


def register_memory_tools(mcp, settings: LTMCSettings) -> None:
    """
    Register memory tools with FastMCP server.
    
    Args:
        mcp: FastMCP server instance
        settings: LTMC settings
    """
    logger.info("Registering memory tools")
    
    @mcp.tool()
    async def memory_store(
        content: str,
        file_name: str,
        resource_type: str = "document"
    ) -> Dict[str, Any]:
        """
        Store content in long-term memory with semantic indexing.
        
        This tool stores text content in the LTMC database with automatic
        semantic indexing for future retrieval. Content is stored with
        metadata and becomes searchable via memory_retrieve.
        
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
                    "error": f"Invalid file name: "
                             f"{', '.join(file_validation.errors)}"
                }
            
            content_validation = validate_content_length(content)
            if not content_validation.is_valid:
                return {
                    "success": False,
                    "error": f"Invalid content: "
                             f"{', '.join(content_validation.errors)}"
                }
            
            type_validation = validate_resource_type(resource_type)
            if not type_validation.is_valid:
                return {
                    "success": False,
                    "error": f"Invalid resource type: {', '.join(type_validation.errors)}"
                }
            
            # Sanitize user input
            content_clean = sanitize_user_input(content)
            file_name_clean = sanitize_user_input(file_name)
            
            # Initialize database service
            db_service = _get_db_service(settings)
            
            # Store content in database
            resource_id = await db_service.store_memory(
                content=content_clean,
                file_name=file_name_clean,
                resource_type=resource_type
            )
            
            if resource_id:
                logger.info(f"✅ Memory stored successfully: {file_name_clean} (ID: {resource_id})")
                return {
                    "success": True,
                    "resource_id": resource_id,
                    "vector_id": resource_id,  # Assuming vector ID matches resource ID
                    "chunks_created": 1,
                    "message": f"Successfully stored {file_name_clean} in memory"
                }
            else:
                logger.error(f"❌ Failed to store memory: {file_name_clean}")
                return {
                    "success": False,
                    "error": "Failed to store memory in database"
                }
                
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            return {
                "success": False,
                "error": f"Failed to store memory: {str(e)}"
            }
    
    @mcp.tool()
    async def memory_retrieve(
        query: str,
        top_k: int = 5,
        conversation_id: str = None
    ) -> Dict[str, Any]:
        """
        Retrieve content using semantic search.
        
        This tool searches the LTMC database for content relevant to the query
        using semantic similarity and text-based matching.
        
        Args:
            query: Search query string
            top_k: Maximum number of results to return
            conversation_id: Optional conversation context
            
        Returns:
            Dict with search results and metadata
        """
        logger.debug(f"Retrieving memory for query: {query} (top_k: {top_k})")
        
        try:
            # Sanitize user input
            query_clean = sanitize_user_input(query)
            
            # Initialize database service
            db_service = _get_db_service(settings)
            
            # Get all resources for search
            all_resources = await db_service.list_all_resources()
            results = []
            
            if not all_resources:
                logger.info("No resources found in database")
                return {
                    "success": True,
                    "results": [],
                    "query_processed": query_clean,
                    "total_matches": 0,
                    "conversation_id": conversation_id
                }
            
            # Try FAISS semantic search first
            try:
                faiss_results = await db_service.search_memory_semantic(
                    query_clean, top_k
                )
                
                if faiss_results:
                    for result in faiss_results:
                        # Get full resource details
                        resource = await db_service.get_resource_by_id(result['id'])
                        if resource:
                            vector_id = result.get('vector_id', resource.get('id'))
                            
                            result_data = {
                                "id": resource["id"],
                                "content": resource.get("content", 
                                    f"Content from {resource['file_name']}"),
                                "similarity_score": round(
                                    result.get('similarity_score', 1.0), 3
                                ),
                                "resource_type": resource["type"],
                                "file_name": resource["file_name"],
                                "created_at": resource["created_at"],
                                "vector_id": vector_id,
                                "search_type": "semantic"
                            }
                            results.append(result_data)
                            
                            if len(results) >= top_k:
                                break
                    
                    logger.info(f"FAISS semantic search returned {len(results)} results")
                
                # Fallback to text-based search if no semantic results
                if not results and all_resources:
                    logger.info("No FAISS results found, using text-based fallback search")
                    
                    query_lower = query_clean.lower()
                    text_matches = []
                    
                    for resource in all_resources:
                        # Check if query matches file name or content
                        file_name_lower = resource.get('file_name', '').lower()
                        
                        # Try to get content for text matching
                        try:
                            full_resource = await db_service.get_resource_by_id(
                                resource['id']
                            )
                            content = full_resource.get('content', '') if full_resource else ''
                            content_lower = content.lower()
                        except Exception:
                            content = ''
                            content_lower = ''
                        
                        # Calculate text relevance score
                        relevance = 0.0
                        if query_lower in file_name_lower:
                            relevance += 1.0
                        if query_lower in content_lower:
                            relevance += 0.8
                            # Boost for multiple word matches
                            query_words = query_lower.split()
                            word_matches = sum(1 for word in query_words 
                                             if word in content_lower)
                            relevance += (word_matches / len(query_words)) * 0.5 if query_words else 0
                        
                        if relevance > 0:
                            result = {
                                "id": resource["id"],
                                "content": content or f"Content from {resource['file_name']}",
                                "similarity_score": round(relevance, 3),
                                "resource_type": resource["type"],
                                "file_name": resource["file_name"],
                                "created_at": resource["created_at"],
                                "vector_id": resource.get('vector_id'),
                                "search_type": "text"
                            }
                            text_matches.append(result)
                    
                    # Sort by relevance and limit results
                    text_matches.sort(key=lambda x: x['similarity_score'], reverse=True)
                    results = text_matches[:top_k]
                    
                    logger.info(f"Text-based fallback search returned {len(results)} results")
                
            except Exception as faiss_error:
                logger.error(f"FAISS semantic search failed: {faiss_error}")
                
                # Final fallback - simple resource listing
                for resource in all_resources[:top_k]:
                    results.append({
                        "id": resource["id"],
                        "content": f"Content from {resource['file_name']}",
                        "similarity_score": 0.5,  # Default score
                        "resource_type": resource["type"],
                        "file_name": resource["file_name"],
                        "created_at": resource["created_at"],
                        "vector_id": resource.get('vector_id'),
                        "search_type": "fallback"
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
    logger.info("  - memory_store: Store content with semantic indexing")
    logger.info("  - memory_retrieve: Semantic search for relevant content")