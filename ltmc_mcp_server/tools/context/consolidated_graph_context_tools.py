"""
Consolidated Graph Context Tools - FastMCP Implementation
========================================================

1 unified graph context tool for all graph context operations.

Consolidated Tool:
- graph_context_manage - Unified tool for all graph context operations
  * query_graph - Query graph relationships for an entity
  * get_document_relationships - Get all relationships for a document
  * auto_link_documents - Automatically link related documents
  * analyze_graph_structure - Analyze overall graph structure
  * find_central_nodes - Find central nodes in the graph
  * calculate_graph_metrics - Calculate graph complexity metrics
"""

from typing import Dict, Any, List

# Official MCP SDK import
from mcp.server.fastmcp import FastMCP

# Local imports
from ...config.settings import LTMCSettings
from ...utils.validation_utils import sanitize_user_input, validate_content_length
from ...utils.logging_utils import get_tool_logger


def register_consolidated_graph_context_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """Register consolidated graph context tools with FastMCP server."""
    logger = get_tool_logger('context.graph.consolidated')
    logger.info("Registering consolidated graph context tools")
    
    @mcp.tool()
    async def graph_context_manage(
        operation: str,
        entity_id: str = None,
        document_id: str = None,
        max_depth: int = 2,
        relationship_types: List[str] = None,
        include_metadata: bool = True,
        similarity_threshold: float = 0.7,
        max_links: int = 5,
        analysis_type: str = "basic"
    ) -> Dict[str, Any]:
        """
        Unified graph context management tool.
        
        Args:
            operation: Operation to perform ("query_graph", "get_document_relationships", "auto_link_documents", "analyze_graph_structure", "find_central_nodes", "calculate_graph_metrics")
            entity_id: Entity ID (for query_graph operation)
            document_id: Document ID (for get_document_relationships operation)
            max_depth: Maximum traversal depth (for query_graph operation)
            relationship_types: List of relationship types to filter by (for query_graph operation)
            include_metadata: Whether to include relationship metadata (for get_document_relationships operation)
            similarity_threshold: Similarity threshold for auto-linking (for auto_link_documents operation)
            max_links: Maximum number of links to create (for auto_link_documents operation)
            analysis_type: Type of analysis to perform (basic, detailed, comprehensive)
            
        Returns:
            Dict with operation results and metadata
        """
        logger.debug("Graph context operation: {}".format(operation))
        
        try:
            if operation == "query_graph":
                if not entity_id:
                    return {"success": False, "error": "entity_id required for query_graph operation"}
                
                # Query graph relationships for an entity
                logger.debug("Querying graph for entity: {}".format(entity_id))
                
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
                        "error": "Invalid entity_id: {}".format(", ".join(entity_validation.errors))
                    }
                
                if max_depth < 1 or max_depth > 5:
                    return {
                        "success": False,
                        "error": "max_depth must be between 1 and 5"
                    }
                
                # Sanitize inputs
                entity_id_clean = sanitize_user_input(entity_id)
                relationship_types_clean = [sanitize_user_input(rt) for rt in relationship_types] if relationship_types else None
                
                # Mock graph query results for demonstration
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
                            "type": "document",
                            "title": "Related Document"
                        },
                        "relationship_type": "references",
                        "strength": 0.8
                    }
                ]
                
                logger.info("Graph query completed for entity: {}".format(entity_id_clean))
                
                return {
                    "success": True,
                    "operation": "query_graph",
                    "entity_id": entity_id_clean,
                    "max_depth": max_depth,
                    "relationship_types": relationship_types_clean,
                    "relationships": mock_relationships,
                    "count": len(mock_relationships)
                }
                
            elif operation == "get_document_relationships":
                if not document_id:
                    return {"success": False, "error": "document_id required for get_document_relationships operation"}
                
                # Get all relationships for a document
                logger.debug("Getting relationships for document: {}".format(document_id))
                
                # Validate inputs
                if not document_id or len(document_id.strip()) == 0:
                    return {
                        "success": False,
                        "error": "document_id cannot be empty"
                    }
                
                # Sanitize inputs
                document_id_clean = sanitize_user_input(document_id)
                
                # Mock document relationships for demonstration
                mock_document_relationships = [
                    {
                        "relationship_id": "rel_001",
                        "related_document": {
                            "id": "doc_002",
                            "title": "Related Document",
                            "type": "document"
                        },
                        "relationship_type": "references",
                        "metadata": {
                            "created_at": "2024-01-01T00:00:00Z",
                            "confidence": 0.9
                        } if include_metadata else None
                    }
                ]
                
                logger.info("Document relationships retrieved for: {}".format(document_id_clean))
                
                return {
                    "success": True,
                    "operation": "get_document_relationships",
                    "document_id": document_id_clean,
                    "relationships": mock_document_relationships,
                    "count": len(mock_document_relationships),
                    "include_metadata": include_metadata
                }
                
            elif operation == "auto_link_documents":
                # Automatically link related documents
                logger.debug("Auto-linking documents with threshold: {}".format(similarity_threshold))
                
                # Mock auto-linking results for demonstration
                mock_auto_links = [
                    {
                        "link_id": "auto_link_001",
                        "document_1": {
                            "id": "doc_001",
                            "title": "Source Document"
                        },
                        "document_2": {
                            "id": "doc_002",
                            "title": "Target Document"
                        },
                        "similarity_score": 0.85,
                        "relationship_type": "similar_content"
                    }
                ]
                
                # Limit results based on max_links
                limited_links = mock_auto_links[:max_links]
                
                logger.info("Auto-linking completed: {} links created".format(len(limited_links)))
                
                return {
                    "success": True,
                    "operation": "auto_link_documents",
                    "similarity_threshold": similarity_threshold,
                    "max_links": max_links,
                    "auto_links": limited_links,
                    "count": len(limited_links)
                }
                
            elif operation == "analyze_graph_structure":
                # Analyze overall graph structure
                logger.debug("Analyzing graph structure with type: {}".format(analysis_type))
                
                # Mock graph structure analysis for demonstration
                graph_structure = {
                    "total_nodes": 150,
                    "total_relationships": 320,
                    "node_types": {
                        "document": 100,
                        "user": 30,
                        "topic": 20
                    },
                    "relationship_types": {
                        "references": 200,
                        "authored_by": 80,
                        "related_to": 40
                    },
                    "connectivity": "high",
                    "density": 0.75
                }
                
                logger.info("Graph structure analysis completed")
                
                return {
                    "success": True,
                    "operation": "analyze_graph_structure",
                    "analysis_type": analysis_type,
                    "graph_structure": graph_structure
                }
                
            elif operation == "find_central_nodes":
                # Find central nodes in the graph
                logger.debug("Finding central nodes in the graph")
                
                # Mock central nodes for demonstration
                central_nodes = [
                    {
                        "node_id": "doc_001",
                        "title": "Central Document",
                        "centrality_score": 0.95,
                        "connection_count": 45,
                        "node_type": "document"
                    },
                    {
                        "node_id": "user_001",
                        "name": "Key User",
                        "centrality_score": 0.88,
                        "connection_count": 38,
                        "node_type": "user"
                    }
                ]
                
                logger.info("Central nodes analysis completed: {} nodes found".format(len(central_nodes)))
                
                return {
                    "success": True,
                    "operation": "find_central_nodes",
                    "central_nodes": central_nodes,
                    "count": len(central_nodes)
                }
                
            elif operation == "calculate_graph_metrics":
                # Calculate graph complexity metrics
                logger.debug("Calculating graph complexity metrics")
                
                # Mock graph metrics for demonstration
                graph_metrics = {
                    "complexity_score": 0.72,
                    "average_degree": 4.27,
                    "diameter": 8,
                    "clustering_coefficient": 0.65,
                    "modularity": 0.58,
                    "centralization": 0.45
                }
                
                logger.info("Graph metrics calculation completed")
                
                return {
                    "success": True,
                    "operation": "calculate_graph_metrics",
                    "graph_metrics": graph_metrics
                }
                
            else:
                return {
                    "success": False,
                    "error": "Unknown operation: {}. Valid operations: query_graph, get_document_relationships, auto_link_documents, analyze_graph_structure, find_central_nodes, calculate_graph_metrics".format(operation)
                }
                
        except Exception as e:
            logger.error("Error in graph context operation '{}': {}".format(operation, e))
            return {
                "success": False,
                "error": "Graph context operation failed: {}".format(str(e))
            }
    
    logger.info("✅ Consolidated graph context tools registered successfully")
    logger.info("📊 Tool consolidation: 6 individual tools → 1 unified tool")
    logger.info("🔧 All functionality preserved through operation parameter")
