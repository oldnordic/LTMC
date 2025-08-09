"""Memory management tools for LTMC MCP server."""

from typing import Dict, Any, Callable

# Import the actual implementation functions from the main server
# This maintains compatibility with existing code
from ltms.mcp_server import (
    store_memory as _store_memory,
    retrieve_memory as _retrieve_memory
)


def store_memory_handler(file_name: str, content: str, resource_type: str = "document") -> Dict[str, Any]:
    """Store memory/document in LTMC with chunking and vector indexing."""
    return _store_memory(file_name, content, resource_type)


def retrieve_memory_handler(conversation_id: str, query: str, top_k: int = 10) -> Dict[str, Any]:
    """Retrieve relevant memory/documents from LTMC using semantic search."""
    return _retrieve_memory(conversation_id, query, top_k)


# Tool definitions for MCP protocol
MEMORY_TOOLS = {
    "store_memory": {
        "handler": store_memory_handler,
        "description": "Store a document or memory in LTMC with automatic chunking and vector indexing",
        "schema": {
            "type": "object",
            "properties": {
                "file_name": {
                    "type": "string",
                    "description": "Name of the file/document to store"
                },
                "content": {
                    "type": "string", 
                    "description": "Content to store"
                },
                "resource_type": {
                    "type": "string",
                    "description": "Type of resource (document, code, note, etc.)",
                    "default": "document"
                }
            },
            "required": ["file_name", "content"]
        }
    },
    
    "retrieve_memory": {
        "handler": retrieve_memory_handler,
        "description": "Retrieve relevant documents/memories using semantic search",
        "schema": {
            "type": "object",
            "properties": {
                "conversation_id": {
                    "type": "string",
                    "description": "Conversation ID to scope the search"
                },
                "query": {
                    "type": "string",
                    "description": "Search query to find relevant memories"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (default: 10)",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100
                }
            },
            "required": ["conversation_id", "query"]
        }
    }
}