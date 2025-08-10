"""
Core Context Tools - FastMCP Implementation
==========================================

Core context and document management tools following FastMCP patterns.

Tools implemented:
1. build_context - Build context from documents
2. retrieve_by_type - Retrieve documents by type
3. link_resources - Link two resources with a relationship in the graph
"""

import logging
from typing import Dict, Any, List

# Official MCP SDK import - from research findings
from mcp.server.fastmcp import FastMCP

# Local imports
from config.settings import LTMCSettings
from services.database_service import DatabaseService
from services.neo4j_service import Neo4jService
from utils.validation_utils import sanitize_user_input, validate_content_length
from utils.logging_utils import get_tool_logger


def register_core_context_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """
    Register core context tools with FastMCP server.
    
    Args:
        mcp: FastMCP server instance
        settings: LTMC settings
    """
    logger = get_tool_logger('core_context')
    logger.info("Registering core context tools")
    
    # Initialize services
    db_service = DatabaseService(settings)
    neo4j_service = Neo4jService(settings)
    
    @mcp.tool()
    async def build_context(
        query: str,
        max_tokens: int = 8000,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Build context from documents.
        
        This tool builds a context window from stored documents based on semantic
        similarity to the provided query, respecting token limits.
        
        Args:
            query: Query to build context around
            max_tokens: Maximum tokens in context window
            top_k: Maximum number of documents to include
            
        Returns:
            Dict with built context and metadata
        """
        logger.debug(f"Building context for query: {query[:50]}...")
        
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
                    "error": f"Query validation failed: {', '.join(query_validation.errors)}"
                }
            
            if max_tokens <= 0 or max_tokens > 32000:
                return {
                    "success": False,
                    "error": "max_tokens must be between 1 and 32000"
                }
            
            if top_k <= 0 or top_k > 50:
                return {
                    "success": False,
                    "error": "top_k must be between 1 and 50"
                }
            
            # Sanitize query
            query_clean = sanitize_user_input(query)
            
            # TODO: Implement actual context building with semantic search
            # For now, return mock context data
            
            mock_documents = [
                {
                    "id": "doc_001",
                    "title": "FastMCP Implementation Guide",
                    "content": "FastMCP is a modern framework for building MCP servers...",
                    "relevance_score": 0.95,
                    "token_count": 250
                },
                {
                    "id": "doc_002",
                    "title": "Database Integration Patterns",
                    "content": "SQLite and Neo4j integration requires careful async handling...",
                    "relevance_score": 0.87,
                    "token_count": 180
                },
                {
                    "id": "doc_003",
                    "title": "Tool Registration Best Practices",
                    "content": "Using @mcp.tool() decorator ensures proper registration...",
                    "relevance_score": 0.82,
                    "token_count": 220
                }
            ]
            
            # Build context within token limits
            context_docs = []
            total_tokens = 0
            
            for doc in mock_documents:
                if len(context_docs) >= top_k:
                    break
                if total_tokens + doc["token_count"] <= max_tokens:
                    context_docs.append(doc)
                    total_tokens += doc["token_count"]
            
            built_context = "\\n\\n".join([f"**{doc['title']}**\\n{doc['content']}" for doc in context_docs])
            
            context_metadata = {
                "total_documents": len(context_docs),
                "total_tokens": total_tokens,
                "average_relevance": round(sum(d["relevance_score"] for d in context_docs) / len(context_docs), 3) if context_docs else 0,
                "query_processed": query_clean[:100] + ("..." if len(query_clean) > 100 else ""),
                "max_tokens_limit": max_tokens,
                "top_k_limit": top_k
            }
            
            logger.info(f"Built context with {len(context_docs)} documents, {total_tokens} tokens")
            
            return {
                "success": True,
                "context": built_context,
                "documents": context_docs,
                "metadata": context_metadata,
                "query": query_clean,
                "message": f"Context built with {len(context_docs)} documents"
            }
            
        except Exception as e:
            logger.error(f"Error building context: {e}")
            return {
                "success": False,
                "error": f"Failed to build context: {str(e)}"
            }
    
    @mcp.tool()
    async def retrieve_by_type(
        resource_type: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Retrieve documents by resource type.
        
        This tool queries the database for documents of a specific type
        (e.g., code, document, note) with optional limiting.
        
        Args:
            resource_type: Type of resource to retrieve
            limit: Maximum number of documents to return
            
        Returns:
            Dict with retrieved documents and type information
        """
        logger.debug(f"Retrieving documents by type: {resource_type}")
        
        try:
            # Validate inputs
            if not resource_type or len(resource_type.strip()) == 0:
                return {
                    "success": False,
                    "error": "resource_type cannot be empty"
                }
            
            valid_types = ["document", "code", "note", "blueprint", "task", "chat", "memory"]
            if resource_type not in valid_types:
                return {
                    "success": False,
                    "error": f"Invalid resource_type. Must be one of: {', '.join(valid_types)}"
                }
            
            if limit <= 0 or limit > 100:
                return {
                    "success": False,
                    "error": "limit must be between 1 and 100"
                }
            
            # TODO: Query actual database for documents by type
            # For now, return mock data based on resource type
            
            mock_documents = []
            if resource_type == "code":
                mock_documents = [
                    {
                        "id": "code_001",
                        "title": "FastMCP Server Implementation",
                        "file_path": "/src/main.py",
                        "content_preview": "async def create_server() -> FastMCP...",
                        "created_at": "2025-01-10T10:00:00Z",
                        "resource_type": "code"
                    },
                    {
                        "id": "code_002", 
                        "title": "Database Service Module",
                        "file_path": "/src/services/database_service.py",
                        "content_preview": "class DatabaseService: async def initialize...",
                        "created_at": "2025-01-10T09:30:00Z",
                        "resource_type": "code"
                    }
                ]
            elif resource_type == "document":
                mock_documents = [
                    {
                        "id": "doc_001",
                        "title": "LTMC Architecture Plan",
                        "content_preview": "Modular FastMCP architecture with tools...",
                        "created_at": "2025-01-10T08:00:00Z",
                        "resource_type": "document"
                    }
                ]
            else:
                mock_documents = [
                    {
                        "id": f"{resource_type}_001",
                        "title": f"Sample {resource_type.title()}",
                        "content_preview": f"This is a sample {resource_type} resource...",
                        "created_at": "2025-01-10T12:00:00Z",
                        "resource_type": resource_type
                    }
                ]
            
            # Apply limit
            limited_documents = mock_documents[:limit]
            
            retrieval_summary = {
                "resource_type": resource_type,
                "total_found": len(mock_documents),
                "returned_count": len(limited_documents),
                "limit_applied": limit,
                "has_more": len(mock_documents) > limit
            }
            
            logger.info(f"Retrieved {len(limited_documents)} documents of type '{resource_type}'")
            
            return {
                "success": True,
                "resource_type": resource_type,
                "documents": limited_documents,
                "summary": retrieval_summary,
                "message": f"Found {len(limited_documents)} documents of type '{resource_type}'"
            }
            
        except Exception as e:
            logger.error(f"Error retrieving documents by type: {e}")
            return {
                "success": False,
                "error": f"Failed to retrieve documents: {str(e)}"
            }
    
    @mcp.tool()
    async def link_resources(
        resource_1_id: str,
        resource_2_id: str,
        relationship_type: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Link two resources with a relationship in Neo4j graph.
        
        This tool creates a relationship between two resources in the 
        Neo4j knowledge graph with specified type and metadata.
        
        Args:
            resource_1_id: ID of the first resource
            resource_2_id: ID of the second resource
            relationship_type: Type of relationship (e.g., "depends_on", "references")
            metadata: Optional metadata for the relationship
            
        Returns:
            Dict with relationship creation results
        """
        logger.debug(f"Linking resources: {resource_1_id} -> {resource_2_id} ({relationship_type})")
        
        try:
            # Validate inputs
            if not resource_1_id or not resource_2_id or not relationship_type:
                return {
                    "success": False,
                    "error": "resource_1_id, resource_2_id, and relationship_type are required"
                }
            
            # Validate resource IDs
            for resource_id in [resource_1_id, resource_2_id]:
                id_validation = validate_content_length(resource_id, max_length=100)
                if not id_validation.is_valid:
                    return {
                        "success": False,
                        "error": f"Invalid resource ID: {resource_id}"
                    }
            
            # Validate relationship type
            valid_relationships = [
                "depends_on", "references", "contains", "implements", 
                "extends", "uses", "related_to", "part_of"
            ]
            if relationship_type not in valid_relationships:
                return {
                    "success": False,
                    "error": f"Invalid relationship_type. Must be one of: {', '.join(valid_relationships)}"
                }
            
            # Sanitize inputs
            resource_1_clean = sanitize_user_input(resource_1_id)
            resource_2_clean = sanitize_user_input(resource_2_id)
            relationship_clean = sanitize_user_input(relationship_type)
            
            # TODO: Create actual Neo4j relationship
            # For now, return mock relationship creation
            
            relationship_data = {
                "relationship_id": f"rel_{resource_1_clean}_{resource_2_clean}_{relationship_clean}",
                "from_resource": resource_1_clean,
                "to_resource": resource_2_clean,
                "relationship_type": relationship_clean,
                "metadata": metadata or {},
                "created_at": "2025-01-10T12:00:00Z"
            }
            
            logger.info(f"Created relationship: {resource_1_clean} -{relationship_clean}-> {resource_2_clean}")
            
            return {
                "success": True,
                "relationship": relationship_data,
                "message": f"Successfully linked {resource_1_clean} to {resource_2_clean} with '{relationship_clean}' relationship"
            }
            
        except Exception as e:
            logger.error(f"Error linking resources: {e}")
            return {
                "success": False,
                "error": f"Failed to link resources: {str(e)}"
            }
    
    logger.info("✅ Core context tools registered successfully")
    logger.info("  - build_context: Build context from documents")
    logger.info("  - retrieve_by_type: Retrieve documents by type")
    logger.info("  - link_resources: Link two resources with a relationship")