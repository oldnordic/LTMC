"""Context and relationship management tools for LTMC MCP server."""

from typing import Dict, Any

# Import implementation functions
from ltms.mcp_server import (
    build_context as _build_context,
    retrieve_by_type as _retrieve_by_type,
    store_context_links_tool as _store_context_links,
    get_context_links_for_message_tool as _get_context_links_for_message,
    get_messages_for_chunk_tool as _get_messages_for_chunk,
    get_context_usage_statistics_tool as _get_context_usage_statistics,
    link_resources as _link_resources,
    query_graph as _query_graph,
    auto_link_documents as _auto_link_documents,
    get_document_relationships_tool as _get_document_relationships,
    list_tool_identifiers as _list_tool_identifiers,
    get_tool_conversations as _get_tool_conversations
)


def build_context_handler(documents: list, max_tokens: int = 4000) -> Dict[str, Any]:
    """Build a context window from documents."""
    return _build_context(documents, max_tokens)


def retrieve_by_type_handler(query: str, doc_type: str, top_k: int = 5) -> Dict[str, Any]:
    """Retrieve documents by type and query."""
    return _retrieve_by_type(query, doc_type, top_k)


def store_context_links_handler(message_id: str, chunk_ids: list) -> Dict[str, Any]:
    """Store context links between message and chunks."""
    return _store_context_links(message_id, chunk_ids)


def get_context_links_for_message_handler(message_id: str) -> Dict[str, Any]:
    """Get context links for a specific message."""
    return _get_context_links_for_message(message_id)


def get_messages_for_chunk_handler(chunk_id: int) -> Dict[str, Any]:
    """Get messages that reference a specific chunk."""
    return _get_messages_for_chunk(chunk_id)


def get_context_usage_statistics_handler() -> Dict[str, Any]:
    """Get statistics about context usage."""
    return _get_context_usage_statistics()


def link_resources_handler(source_id: str, target_id: str, relationship_type: str) -> Dict[str, Any]:
    """Link two resources with a relationship."""
    return _link_resources(source_id, target_id, relationship_type)


def query_graph_handler(query: str, relationship_types: list = None) -> Dict[str, Any]:
    """Query the knowledge graph."""
    return _query_graph(query, relationship_types)


def auto_link_documents_handler(document_id: str, similarity_threshold: float = 0.8) -> Dict[str, Any]:
    """Automatically link documents based on similarity."""
    return _auto_link_documents(document_id, similarity_threshold)


def get_document_relationships_handler(document_id: str, max_depth: int = 2) -> Dict[str, Any]:
    """Get document relationships up to specified depth."""
    return _get_document_relationships(document_id, max_depth)


def list_tool_identifiers_handler() -> Dict[str, Any]:
    """List all available tool identifiers."""
    return _list_tool_identifiers()


def get_tool_conversations_handler(tool_name: str, limit: int = 10) -> Dict[str, Any]:
    """Get conversations that used a specific tool."""
    return _get_tool_conversations(tool_name, limit)


# Tool definitions for MCP protocol
CONTEXT_TOOLS = {
    "build_context": {
        "handler": build_context_handler,
        "description": "Build a context window from a list of documents with token limiting",
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
                }
            },
            "required": ["documents"]
        }
    },
    
    "retrieve_by_type": {
        "handler": retrieve_by_type_handler,
        "description": "Retrieve documents filtered by type using semantic search",
        "schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "doc_type": {
                    "type": "string",
                    "description": "Type of documents to retrieve"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 50
                }
            },
            "required": ["query", "doc_type"]
        }
    },
    
    "store_context_links": {
        "handler": store_context_links_handler,
        "description": "Store links between a message and document chunks for context tracking",
        "schema": {
            "type": "object",
            "properties": {
                "message_id": {
                    "type": "string",
                    "description": "ID of the message"
                },
                "chunk_ids": {
                    "type": "array",
                    "description": "List of chunk IDs to link",
                    "items": {"type": "integer"}
                }
            },
            "required": ["message_id", "chunk_ids"]
        }
    },
    
    "get_context_links_for_message": {
        "handler": get_context_links_for_message_handler,
        "description": "Retrieve context links for a specific message",
        "schema": {
            "type": "object",
            "properties": {
                "message_id": {
                    "type": "string",
                    "description": "ID of the message to get links for"
                }
            },
            "required": ["message_id"]
        }
    },
    
    "get_messages_for_chunk": {
        "handler": get_messages_for_chunk_handler,
        "description": "Get messages that reference a specific document chunk",
        "schema": {
            "type": "object",
            "properties": {
                "chunk_id": {
                    "type": "integer",
                    "description": "ID of the chunk to find messages for"
                }
            },
            "required": ["chunk_id"]
        }
    },
    
    "get_context_usage_statistics": {
        "handler": get_context_usage_statistics_handler,
        "description": "Get statistics about context usage patterns",
        "schema": {
            "type": "object",
            "properties": {}
        }
    },
    
    "link_resources": {
        "handler": link_resources_handler,
        "description": "Create a relationship link between two resources",
        "schema": {
            "type": "object",
            "properties": {
                "source_id": {
                    "type": "string",
                    "description": "ID of the source resource"
                },
                "target_id": {
                    "type": "string", 
                    "description": "ID of the target resource"
                },
                "relationship_type": {
                    "type": "string",
                    "description": "Type of relationship (related_to, depends_on, etc.)"
                }
            },
            "required": ["source_id", "target_id", "relationship_type"]
        }
    },
    
    "query_graph": {
        "handler": query_graph_handler,
        "description": "Query the knowledge graph for related resources",
        "schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query to search the knowledge graph"
                },
                "relationship_types": {
                    "type": "array",
                    "description": "Filter by specific relationship types",
                    "items": {"type": "string"}
                }
            },
            "required": ["query"]
        }
    },
    
    "auto_link_documents": {
        "handler": auto_link_documents_handler,
        "description": "Automatically create links between similar documents",
        "schema": {
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "string",
                    "description": "ID of the document to find links for"
                },
                "similarity_threshold": {
                    "type": "number",
                    "description": "Minimum similarity score for linking",
                    "default": 0.8,
                    "minimum": 0.0,
                    "maximum": 1.0
                }
            },
            "required": ["document_id"]
        }
    },
    
    "get_document_relationships": {
        "handler": get_document_relationships_handler,
        "description": "Get all relationships for a document up to specified depth",
        "schema": {
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "string",
                    "description": "ID of the document"
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum depth to traverse relationships",
                    "default": 2,
                    "minimum": 1,
                    "maximum": 5
                }
            },
            "required": ["document_id"]
        }
    },
    
    "list_tool_identifiers": {
        "handler": list_tool_identifiers_handler,
        "description": "List all available tool identifiers in the system",
        "schema": {
            "type": "object",
            "properties": {}
        }
    },
    
    "get_tool_conversations": {
        "handler": get_tool_conversations_handler,
        "description": "Get conversations that involved a specific tool",
        "schema": {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": "Name of the tool"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of conversations to return",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100
                }
            },
            "required": ["tool_name"]
        }
    }
}