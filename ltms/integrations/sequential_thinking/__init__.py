"""
LTMC Sequential MCP Integration Package

Production-ready integration of Sequential Thinking MCP capabilities with 
LTMC's 4-database coordination infrastructure.

This package provides:
- ULID-based thought identification with content hashing
- Atomic storage across SQLite, FAISS, Neo4j, Redis using proven coordination
- Graph-based chain analysis and traversal
- Semantic similarity search for reasoning patterns
- Comprehensive observability and SLA monitoring
- Full integration with LTMC's existing tool registry
"""

from .ltmc_integration import (
    ThoughtData,
    SequentialThinkingCoordinator
)

from .mcp_tools import (
    SequentialMCPTools,
    SEQUENTIAL_MCP_TOOLS
)

__version__ = "1.0.0"

# Integration metadata for LTMC system discovery
INTEGRATION_INFO = {
    "name": "sequential_thinking",
    "version": __version__,
    "description": "Sequential Thinking MCP integration with LTMC coordination",
    "database_dependencies": ["sqlite", "faiss", "neo4j", "redis"],
    "mcp_tools": list(SEQUENTIAL_MCP_TOOLS.keys()),
    "sla_requirements": {
        "thought_creation_ms": 100,
        "thought_retrieval_ms": 50,
        "chain_analysis_ms": 2000
    },
    "coordination_pattern": "ordered_fanout",  # SQLite → FAISS → Neo4j → Redis
    "content_hashing": "sha256",
    "identification": "ulid"
}

def get_sequential_mcp_tools():
    """Get Sequential MCP tools for LTMC tool registry integration."""
    return SEQUENTIAL_MCP_TOOLS

def create_sequential_coordinator(sync_coordinator, test_mode=False):
    """Factory function for creating SequentialThinkingCoordinator."""
    return SequentialThinkingCoordinator(sync_coordinator, test_mode)

def get_integration_info():
    """Get integration metadata for LTMC system."""
    return INTEGRATION_INFO

__all__ = [
    'ThoughtData',
    'SequentialThinkingCoordinator', 
    'SequentialMCPTools',
    'SEQUENTIAL_MCP_TOOLS',
    'get_sequential_mcp_tools',
    'create_sequential_coordinator',
    'get_integration_info',
    'INTEGRATION_INFO'
]