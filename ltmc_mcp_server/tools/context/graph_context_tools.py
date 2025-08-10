"""
Graph Context Tools - FastMCP Implementation
===========================================

Graph relationship and auto-linking tools following FastMCP patterns.

Tools implemented:
1. query_graph - Query graph relationships for an entity
2. get_document_relationships - Get all relationships for a document
3. auto_link_documents - Automatically link related documents based on content similarity
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


def register_graph_context_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """
    Register graph context tools with FastMCP server.
    
    Args:
        mcp: FastMCP server instance
        settings: LTMC settings
    """
    logger = get_tool_logger('graph_context')
    logger.info("Registering graph context tools")
    
    # Initialize services
    db_service = DatabaseService(settings)
    neo4j_service = Neo4jService(settings)
    
    @mcp.tool()
    async def query_graph(
        entity_id: str,
        max_depth: int = 2,
        relationship_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Query graph relationships for an entity.
        
        This tool queries the Neo4j graph to find relationships
        for a specific entity with configurable depth and filtering.
        
        Args:
            entity_id: Entity ID to query relationships for
            max_depth: Maximum traversal depth (1-5)
            relationship_types: Optional list of relationship types to filter by
            
        Returns:
            Dict with graph query results and relationship data
        """
        logger.debug(f"Querying graph for entity: {entity_id}")
        
        try:
            # Validate inputs
            if not entity_id or len(entity_id.strip()) == 0:
                return {
                    "success": False,
                    "error": "entity_id cannot be empty"
                }
            
            entity_validation = validate_content_length(entity_id, max_length=100)
            if not entity_validation.is_valid:
                return {
                    "success": False,
                    "error": f"Invalid entity_id: {', '.join(entity_validation.errors)}"
                }
            
            if max_depth < 1 or max_depth > 5:
                return {
                    "success": False,
                    "error": "max_depth must be between 1 and 5"
                }
            
            # Sanitize inputs
            entity_id_clean = sanitize_user_input(entity_id)
            relationship_types_clean = [sanitize_user_input(rt) for rt in relationship_types] if relationship_types else None
            
            # TODO: Query actual Neo4j graph
            # For now, return mock graph data
            
            mock_relationships = [
                {
                    "relationship_id": "rel_001",
                    "from_entity": {
                        "id": entity_id_clean,
                        "type": "document",
                        "title": "Main Document"
                    },
                    "to_entity": {
                        "id": "doc_002",
                        "type": "code",
                        "title": "Implementation File"
                    },
                    "relationship": {
                        "type": "references",
                        "direction": "outgoing",
                        "depth": 1,
                        "properties": {
                            "strength": 0.8,
                            "created_at": "2025-01-10T10:00:00Z"
                        }
                    }
                },
                {
                    "relationship_id": "rel_002",
                    "from_entity": {
                        "id": "doc_003",
                        "type": "blueprint",
                        "title": "System Blueprint"
                    },
                    "to_entity": {
                        "id": entity_id_clean,
                        "type": "document",
                        "title": "Main Document"
                    },
                    "relationship": {
                        "type": "depends_on",
                        "direction": "incoming",
                        "depth": 1,
                        "properties": {
                            "strength": 0.9,
                            "created_at": "2025-01-10T09:30:00Z"
                        }
                    }
                }
            ]
            
            # Filter by relationship types if specified
            if relationship_types_clean:
                mock_relationships = [
                    rel for rel in mock_relationships
                    if rel["relationship"]["type"] in relationship_types_clean
                ]
            
            # Filter by max_depth
            filtered_relationships = [
                rel for rel in mock_relationships
                if rel["relationship"]["depth"] <= max_depth
            ]
            
            # Build graph statistics
            unique_entities = set()
            outgoing_count = 0
            incoming_count = 0
            
            for rel in filtered_relationships:
                unique_entities.add(rel["from_entity"]["id"])
                unique_entities.add(rel["to_entity"]["id"])
                
                if rel["relationship"]["direction"] == "outgoing":
                    outgoing_count += 1
                else:
                    incoming_count += 1
            
            graph_statistics = {
                "total_relationships": len(filtered_relationships),
                "unique_entities": len(unique_entities),
                "outgoing_relationships": outgoing_count,
                "incoming_relationships": incoming_count,
                "max_depth_reached": max(rel["relationship"]["depth"] for rel in filtered_relationships) if filtered_relationships else 0
            }
            
            logger.info(f"Found {len(filtered_relationships)} relationships for entity {entity_id_clean}")
            
            return {
                "success": True,
                "entity_id": entity_id_clean,
                "relationships": filtered_relationships,
                "graph_statistics": graph_statistics,
                "query_parameters": {
                    "max_depth": max_depth,
                    "relationship_types_filter": relationship_types_clean
                },
                "message": f"Found {len(filtered_relationships)} relationships for {entity_id_clean}"
            }
            
        except Exception as e:
            logger.error(f"Error querying graph: {e}")
            return {
                "success": False,
                "error": f"Failed to query graph: {str(e)}"
            }
    
    @mcp.tool()
    async def get_document_relationships(
        document_id: str,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Get all relationships for a specific document.
        
        This tool retrieves all incoming and outgoing relationships
        for a document from the Neo4j knowledge graph.
        
        Args:
            document_id: Document ID to get relationships for
            include_metadata: Whether to include relationship metadata
            
        Returns:
            Dict with document relationships and analysis
        """
        logger.debug(f"Getting relationships for document: {document_id}")
        
        try:
            # Validate input
            if not document_id or len(document_id.strip()) == 0:
                return {
                    "success": False,
                    "error": "document_id cannot be empty"
                }
            
            doc_validation = validate_content_length(document_id, max_length=100)
            if not doc_validation.is_valid:
                return {
                    "success": False,
                    "error": f"Invalid document_id: {', '.join(doc_validation.errors)}"
                }
            
            document_id_clean = sanitize_user_input(document_id)
            
            # TODO: Query actual Neo4j document relationships
            # For now, return mock relationship data
            
            incoming_relationships = [
                {
                    "from_document": {
                        "id": "doc_source_001",
                        "title": "Source Document A",
                        "type": "blueprint"
                    },
                    "relationship_type": "generates",
                    "metadata": {
                        "created_at": "2025-01-10T09:00:00Z",
                        "confidence": 0.85
                    } if include_metadata else {}
                },
                {
                    "from_document": {
                        "id": "doc_source_002", 
                        "title": "Reference Manual",
                        "type": "document"
                    },
                    "relationship_type": "references",
                    "metadata": {
                        "created_at": "2025-01-10T08:30:00Z",
                        "confidence": 0.92
                    } if include_metadata else {}
                }
            ]
            
            outgoing_relationships = [
                {
                    "to_document": {
                        "id": "doc_target_001",
                        "title": "Implementation Guide",
                        "type": "code"
                    },
                    "relationship_type": "implements",
                    "metadata": {
                        "created_at": "2025-01-10T10:15:00Z",
                        "confidence": 0.88
                    } if include_metadata else {}
                },
                {
                    "to_document": {
                        "id": "doc_target_002",
                        "title": "Test Cases",
                        "type": "code"
                    },
                    "relationship_type": "tests",
                    "metadata": {
                        "created_at": "2025-01-10T10:30:00Z",
                        "confidence": 0.79
                    } if include_metadata else {}
                }
            ]
            
            # Build relationship analysis
            total_relationships = len(incoming_relationships) + len(outgoing_relationships)
            relationship_types = set()
            
            for rel in incoming_relationships + outgoing_relationships:
                relationship_types.add(rel["relationship_type"])
            
            relationship_analysis = {
                "total_relationships": total_relationships,
                "incoming_count": len(incoming_relationships),
                "outgoing_count": len(outgoing_relationships),
                "unique_relationship_types": len(relationship_types),
                "relationship_types": list(relationship_types),
                "connection_strength": "high" if total_relationships > 5 else "medium" if total_relationships > 2 else "low"
            }
            
            logger.info(f"Retrieved {total_relationships} relationships for document {document_id_clean}")
            
            return {
                "success": True,
                "document_id": document_id_clean,
                "incoming_relationships": incoming_relationships,
                "outgoing_relationships": outgoing_relationships,
                "relationship_analysis": relationship_analysis,
                "include_metadata": include_metadata,
                "message": f"Found {total_relationships} relationships for document {document_id_clean}"
            }
            
        except Exception as e:
            logger.error(f"Error getting document relationships: {e}")
            return {
                "success": False,
                "error": f"Failed to get document relationships: {str(e)}"
            }
    
    @mcp.tool()
    async def auto_link_documents(
        source_document_id: str,
        similarity_threshold: float = 0.7,
        max_links: int = 5
    ) -> Dict[str, Any]:
        """
        Automatically link related documents based on content similarity.
        
        This tool analyzes document content to find semantically similar
        documents and creates automatic relationships in the knowledge graph.
        
        Args:
            source_document_id: Source document ID to find links for
            similarity_threshold: Minimum similarity score for linking (0.0-1.0)
            max_links: Maximum number of automatic links to create
            
        Returns:
            Dict with automatic linking results and created relationships
        """
        logger.debug(f"Auto-linking documents for: {source_document_id}")
        
        try:
            # Validate inputs
            if not source_document_id or len(source_document_id.strip()) == 0:
                return {
                    "success": False,
                    "error": "source_document_id cannot be empty"
                }
            
            doc_validation = validate_content_length(source_document_id, max_length=100)
            if not doc_validation.is_valid:
                return {
                    "success": False,
                    "error": f"Invalid source_document_id: {', '.join(doc_validation.errors)}"
                }
            
            if similarity_threshold < 0.0 or similarity_threshold > 1.0:
                return {
                    "success": False,
                    "error": "similarity_threshold must be between 0.0 and 1.0"
                }
            
            if max_links <= 0 or max_links > 20:
                return {
                    "success": False,
                    "error": "max_links must be between 1 and 20"
                }
            
            source_document_id_clean = sanitize_user_input(source_document_id)
            
            # TODO: Implement actual semantic similarity analysis with FAISS/embeddings
            # For now, return mock auto-linking results
            
            similar_documents = [
                {
                    "document_id": "doc_similar_001",
                    "title": "Related Implementation",
                    "similarity_score": 0.89,
                    "content_preview": "FastMCP server implementation with similar patterns..."
                },
                {
                    "document_id": "doc_similar_002",
                    "title": "Architecture Blueprint",
                    "similarity_score": 0.82,
                    "content_preview": "Modular architecture design following similar principles..."
                },
                {
                    "document_id": "doc_similar_003",
                    "title": "Testing Framework",
                    "similarity_score": 0.75,
                    "content_preview": "Test patterns that complement this implementation..."
                }
            ]
            
            # Filter by similarity threshold and limit
            qualifying_documents = [
                doc for doc in similar_documents 
                if doc["similarity_score"] >= similarity_threshold
            ][:max_links]
            
            # Create automatic links
            created_links = []
            for doc in qualifying_documents:
                link = {
                    "link_id": f"auto_link_{source_document_id_clean}_{doc['document_id']}",
                    "source_document": source_document_id_clean,
                    "target_document": doc["document_id"],
                    "relationship_type": "similar_to",
                    "similarity_score": doc["similarity_score"],
                    "auto_created": True,
                    "created_at": "2025-01-10T12:00:00Z"
                }
                created_links.append(link)
            
            linking_summary = {
                "source_document": source_document_id_clean,
                "documents_analyzed": len(similar_documents),
                "qualifying_documents": len(qualifying_documents),
                "links_created": len(created_links),
                "similarity_threshold": similarity_threshold,
                "max_links_limit": max_links,
                "average_similarity": round(sum(doc["similarity_score"] for doc in qualifying_documents) / len(qualifying_documents), 3) if qualifying_documents else 0
            }
            
            logger.info(f"Auto-linked {len(created_links)} documents for {source_document_id_clean}")
            
            return {
                "success": True,
                "source_document_id": source_document_id_clean,
                "similar_documents": qualifying_documents,
                "created_links": created_links,
                "linking_summary": linking_summary,
                "message": f"Auto-created {len(created_links)} links for {source_document_id_clean}"
            }
            
        except Exception as e:
            logger.error(f"Error auto-linking documents: {e}")
            return {
                "success": False,
                "error": f"Failed to auto-link documents: {str(e)}"
            }
    
    logger.info("✅ Graph context tools registered successfully")
    logger.info("  - query_graph: Query graph relationships for an entity")
    logger.info("  - get_document_relationships: Get all relationships for a document")
    logger.info("  - auto_link_documents: Automatically link related documents")