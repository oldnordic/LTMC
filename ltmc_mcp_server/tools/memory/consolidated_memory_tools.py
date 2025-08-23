"""
Consolidated Memory Tools - FastMCP Implementation
==================================================

1 unified memory tool for all memory operations.

Consolidated Tool:
- memory_manage - Unified tool for all memory operations
  * store - Store content in long-term memory with semantic indexing
  * retrieve - Retrieve content using semantic search
  * search - Search memory by content and metadata
  * list - List all stored resources
  * delete - Delete stored memory content
  * analyze - Analyze memory usage patterns
"""

from typing import Dict, Any

# Official MCP SDK import
from mcp.server.fastmcp import FastMCP

# Local imports
from ...config.settings import LTMCSettings
from ...services.database_service import DatabaseService
from ...utils.validation_utils import (
    validate_file_name, validate_content_length, 
    validate_resource_type, sanitize_user_input
)
from ...utils.logging_utils import get_tool_logger


def register_consolidated_memory_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """Register consolidated memory tools with FastMCP server."""
    logger = get_tool_logger('memory.consolidated')
    logger.info("Registering consolidated memory tools")
    
    # Initialize database service
    db_service = DatabaseService(settings)
    
    @mcp.tool()
    async def memory_manage(
        operation: str,
        content: str = None,
        file_name: str = None,
        resource_type: str = "document",
        query: str = None,
        resource_id: str = None,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Unified memory management tool.
        
        Args:
            operation: Operation to perform ("store", "retrieve", "search", "list", "delete", "analyze")
            content: Content to store in memory (for store operation)
            file_name: Name for the stored content (for store operation)
            resource_type: Type of resource (document, code, note) (for store operation)
            query: Search query for retrieve/search operations
            resource_id: Resource ID for delete operation
            limit: Maximum number of results to return (for list/search operations)
            offset: Number of results to skip for pagination (for list/search operations)
            
        Returns:
            Dict with operation results and metadata
        """
        logger.debug("Memory operation: {}".format(operation))
        
        try:
            if operation == "store":
                if not content or not file_name:
                    return {"success": False, "error": "content and file_name required for store operation"}
                
                # Validate inputs
                file_validation = validate_file_name(file_name)
                if not file_validation.is_valid:
                    return {
                        "success": False,
                        "error": "Invalid file name: {}".format(", ".join(file_validation.errors))
                    }
                
                content_validation = validate_content_length(content)
                if not content_validation.is_valid:
                    return {
                        "success": False,
                        "error": "Invalid content: {}".format(", ".join(content_validation.errors))
                    }
                
                type_validation = validate_resource_type(resource_type)
                if not type_validation.is_valid:
                    return {
                        "success": False,
                        "error": "Invalid resource type: {}".format(", ".join(type_validation.errors))
                    }
                
                # Sanitize user input
                content_clean = sanitize_user_input(content)
                file_name_clean = sanitize_user_input(file_name)
                
                # Store content in database
                resource_id = await db_service.store_memory(
                    content=content_clean,
                    file_name=file_name_clean,
                    resource_type=resource_type
                )
                
                if resource_id:
                    logger.info("Stored memory: {} ({})".format(file_name_clean, resource_type))
                    return {
                        "success": True,
                        "operation": "store",
                        "resource_id": resource_id,
                        "file_name": file_name_clean,
                        "resource_type": resource_type,
                        "message": "Content stored successfully in memory"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to store content in memory"
                    }
                
            elif operation == "retrieve":
                if not query:
                    return {"success": False, "error": "query required for retrieve operation"}
                
                # Retrieve content using semantic search
                logger.debug("Retrieving memory with query: {}".format(query))
                results = await db_service.search_memory_semantic(query, limit=limit)
                
                if results:
                    logger.info("Retrieved {} memory items".format(len(results)))
                    return {
                        "success": True,
                        "operation": "retrieve",
                        "query": query,
                        "results": results,
                        "count": len(results),
                        "message": "Memory retrieval completed successfully"
                    }
                else:
                    return {
                        "success": True,
                        "operation": "retrieve",
                        "query": query,
                        "results": [],
                        "count": 0,
                        "message": "No memory items found for query"
                    }
                
            elif operation == "search":
                if not query:
                    return {"success": False, "error": "query required for search operation"}
                
                # Search memory by content and metadata
                logger.debug("Searching memory with query: {}".format(query))
                results = await db_service.search_memory_semantic(query, limit=limit)
                
                if results:
                    logger.info("Found {} memory items".format(len(results)))
                    return {
                        "success": True,
                        "operation": "search",
                        "query": query,
                        "results": results,
                        "count": len(results),
                        "message": "Memory search completed successfully"
                    }
                else:
                    return {
                        "success": True,
                        "operation": "search",
                        "query": query,
                        "results": [],
                        "count": 0,
                        "message": "No memory items found for query"
                    }
                
            elif operation == "list":
                # List all stored resources
                logger.debug("Listing memory resources")
                resources = await db_service.list_all_resources(limit=limit, offset=offset)
                
                if resources:
                    logger.info("Listed {} memory resources".format(len(resources)))
                    return {
                        "success": True,
                        "operation": "list",
                        "resources": resources,
                        "count": len(resources),
                        "limit": limit,
                        "offset": offset,
                        "message": "Memory resources listed successfully"
                    }
                else:
                    return {
                        "success": True,
                        "operation": "list",
                        "resources": [],
                        "count": 0,
                        "limit": limit,
                        "offset": offset,
                        "message": "No memory resources found"
                    }
                
            elif operation == "delete":
                if not resource_id:
                    return {"success": False, "error": "resource_id required for delete operation"}
                
                # Delete stored memory content
                logger.debug("Deleting memory resource: {}".format(resource_id))
                success = await db_service.delete_memory(resource_id)
                
                if success:
                    logger.info("Deleted memory resource: {}".format(resource_id))
                    return {
                        "success": True,
                        "operation": "delete",
                        "resource_id": resource_id,
                        "message": "Memory resource deleted successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to delete memory resource"
                    }
                
            elif operation == "analyze":
                # Analyze memory usage patterns
                logger.debug("Analyzing memory usage patterns")
                
                # Get basic statistics
                total_resources = await db_service.count_resources()
                resource_types = await db_service.get_resource_type_distribution()
                
                logger.info("Analyzed memory usage patterns")
                return {
                    "success": True,
                    "operation": "analyze",
                    "total_resources": total_resources,
                    "resource_types": resource_types,
                    "message": "Memory analysis completed successfully"
                }
                
            else:
                return {
                    "success": False,
                    "error": "Unknown operation: {}. Valid operations: store, retrieve, search, list, delete, analyze".format(operation)
                }
                
        except Exception as e:
            logger.error("Error in memory operation '{}': {}".format(operation, e))
            return {
                "success": False,
                "error": "Memory operation failed: {}".format(str(e))
            }
    
    logger.info("✅ Consolidated memory tools registered successfully")
    logger.info("📊 Tool consolidation: 6 individual tools → 1 unified tool")
    logger.info("🔧 All functionality preserved through operation parameter")
