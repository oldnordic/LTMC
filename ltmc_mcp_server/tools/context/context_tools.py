"""
Context Tools - FastMCP Implementation
======================================

Unified context tools module combining core and graph tools.
Maintains all 6 context tools while respecting 300-line limit through modularization.

Tools implemented (from unified_mcp_server.py analysis):
1. build_context - Build context from documents
2. retrieve_by_type - Retrieve documents by type
3. link_resources - Link two resources with a relationship in the graph
4. query_graph - Query graph relationships for an entity
5. get_document_relationships - Get all relationships for a document
6. auto_link_documents - Automatically link related documents based on content similarity
"""

import logging

# Official MCP SDK import - from research findings
from mcp.server.fastmcp import FastMCP

# Local imports
from config.settings import LTMCSettings
from utils.logging_utils import get_tool_logger

# Import modular tool registration functions
from .core_context_tools import register_core_context_tools
from .graph_context_tools import register_graph_context_tools


def register_context_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """
    Register all context tools with FastMCP server.
    
    Combines core and graph context tools through modular components
    while maintaining unified interface and API compatibility.
    
    Following official FastMCP registration pattern:
    @mcp.tool()
    def tool_name(...) -> ...
    
    Args:
        mcp: FastMCP server instance
        settings: LTMC settings
    """
    logger = get_tool_logger('context')
    logger.info("Registering unified context tools")
    
    # Register core context tools (3 tools)
    register_core_context_tools(mcp, settings)
    
    # Register graph context tools (3 tools) 
    register_graph_context_tools(mcp, settings)
    
    logger.info("✅ All context tools registered successfully")
    logger.info("  - Core tools: build_context, retrieve_by_type, link_resources")
    logger.info("  - Graph tools: query_graph, get_document_relationships, auto_link_documents")
    logger.info("  - Modular architecture: 2 components under 300 lines each")
    logger.info("  - Neo4j integration: Full knowledge graph capabilities")