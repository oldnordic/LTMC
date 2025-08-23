"""Memory group tools - canonical group:operation interface."""

from typing import Dict, Any, Callable

# Import existing implementations
from ltms.services.memory_service import (
    store_memory as _store_memory,
    retrieve_memory as _retrieve_memory
)
from ltms.services.context_service import (
    build_context as _build_context,
    retrieve_by_type as _retrieve_by_type
)
from ltms.services.chat_service import (
    ask_with_context as _ask_with_context
)


def memory_store(file_name: str, content: str, resource_type: str = "document") -> Dict[str, Any]:
    """Store memory/doc/code/blueprint."""
    return _store_memory(file_name, content, resource_type)


def memory_retrieve(query: str, conversation_id: str = "default", top_k: int = 10) -> Dict[str, Any]:
    """Semantic search for memory."""
    return _retrieve_memory(conversation_id, query, top_k)


def memory_build_context(documents: list, max_tokens: int = 4000, topic: str = None) -> Dict[str, Any]:
    """Build context window."""
    # Topic parameter is mentioned in canonical table but not in current implementation
    # Using existing build_context function
    return _build_context(documents, max_tokens)


def memory_list(query: str = "*", resource_type: str = "document", top_k: int = 10) -> Dict[str, Any]:
    """List all resources by type."""
    # This uses retrieve_by_type with query as empty string by default
    return _retrieve_by_type(query, resource_type, top_k)


def memory_ask_with_context(query: str, conversation_id: str = "default", top_k: int = 5) -> Dict[str, Any]:
    """Query with context expansion."""
    return _ask_with_context(query, conversation_id, top_k)


# Tool registry with group:operation names
MEMORY_GROUP_TOOLS = {
    "memory:store": {
        "handler": memory_store,
        "description": "Store memory/doc/code/blueprint",
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
                    "description": "Type of resource (document, code, note, blueprint, etc.)",
                    "default": "document"
                }
            },
            "required": ["file_name", "content"]
        }
    },
    
    "memory:retrieve": {
        "handler": memory_retrieve,
        "description": "Semantic search for memory",
        "schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to find relevant memories"
                },
                "conversation_id": {
                    "type": "string",
                    "description": "Conversation ID to scope the search",
                    "default": "default"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (default: 10)",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100
                }
            },
            "required": ["query"]
        }
    },
    
    "memory:build_context": {
        "handler": memory_build_context,
        "description": "Build context window",
        "schema": {
            "type": "object",
            "properties": {
                "documents": {
                    "type": "array",
                    "description": "List of documents to build context from",
                    "items": {"type": "object"}
                },
                "max_tokens": {
                    "type": "integer",
                    "description": "Maximum tokens for the context window",
                    "default": 4000,
                    "minimum": 100,
                    "maximum": 32000
                },
                "topic": {
                    "type": "string",
                    "description": "Optional topic focus for context building"
                }
            },
            "required": ["documents"]
        }
    },
    
    "memory:list": {
        "handler": memory_list,
        "description": "List all resources by type",
        "schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query filter (* for all)",
                    "default": "*"
                },
                "resource_type": {
                    "type": "string",
                    "description": "Type of resources to list (document, code, blueprint, etc.)",
                    "default": "document"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50
                }
            },
            "required": []
        }
    },
    
    "memory:ask_with_context": {
        "handler": memory_ask_with_context,
        "description": "Query with context expansion",
        "schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Question to ask with context"
                },
                "conversation_id": {
                    "type": "string",
                    "description": "Conversation ID for context scoping",
                    "default": "default"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Maximum number of context items to retrieve",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 50
                }
            },
            "required": ["query"]
        }
    }
}