"""
MCP tool schema definitions for LTMC context tools.
Provides JSON schema definitions for all context management tools.
"""

from typing import Dict, Any

# Schema definitions for context tools
CONTEXT_TOOL_SCHEMAS = {
    "build_context": {
        "type": "object",
        "properties": {
            "documents": {
                "type": "array",
                "description": "List of documents to build context from",
                "items": {"type": "object"},
                "minItems": 1,
                "maxItems": 100
            },
            "max_tokens": {
                "type": "integer",
                "description": "Maximum tokens for the context window",
                "default": 4000,
                "minimum": 100,
                "maximum": 32000
            }
        },
        "required": ["documents"],
        "additionalProperties": False
    },
    
    "retrieve_by_type": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query for semantic retrieval",
                "minLength": 1,
                "maxLength": 500
            },
            "doc_type": {
                "type": "string",
                "description": "Type of documents to retrieve",
                "minLength": 1,
                "maxLength": 100
            },
            "top_k": {
                "type": "integer",
                "description": "Number of results to return",
                "default": 5,
                "minimum": 1,
                "maximum": 50
            }
        },
        "required": ["query", "doc_type"],
        "additionalProperties": False
    },
    
    "store_context_links": {
        "type": "object",
        "properties": {
            "message_id": {
                "type": "string",
                "description": "ID of the message to link chunks to",
                "pattern": "^[0-9]+$"
            },
            "chunk_ids": {
                "type": "array",
                "description": "List of chunk IDs to link to the message",
                "items": {
                    "type": "integer",
                    "minimum": 1
                },
                "minItems": 1,
                "maxItems": 50
            }
        },
        "required": ["message_id", "chunk_ids"],
        "additionalProperties": False
    },
    
    "get_context_links_for_message": {
        "type": "object",
        "properties": {
            "message_id": {
                "type": "string",
                "description": "ID of the message to get context links for",
                "pattern": "^[0-9]+$"
            }
        },
        "required": ["message_id"],
        "additionalProperties": False
    },
    
    "get_messages_for_chunk": {
        "type": "object",
        "properties": {
            "chunk_id": {
                "type": "integer",
                "description": "ID of the chunk to find messages for",
                "minimum": 1
            }
        },
        "required": ["chunk_id"],
        "additionalProperties": False
    },
    
    "get_context_usage_statistics": {
        "type": "object",
        "properties": {},
        "additionalProperties": False
    },
    
    "link_resources": {
        "type": "object",
        "properties": {
            "source_id": {
                "type": "string",
                "description": "ID of the source resource",
                "minLength": 1,
                "maxLength": 255
            },
            "target_id": {
                "type": "string",
                "description": "ID of the target resource",
                "minLength": 1,
                "maxLength": 255
            },
            "relation": {
                "type": "string",
                "description": "Type of relationship between resources",
                "enum": [
                    "related_to",
                    "depends_on",
                    "implements",
                    "extends",
                    "uses",
                    "references",
                    "contains",
                    "part_of",
                    "similar_to",
                    "conflicts_with"
                ]
            }
        },
        "required": ["source_id", "target_id", "relation"],
        "additionalProperties": False
    },
    
    "query_graph": {
        "type": "object",
        "properties": {
            "entity": {
                "type": "string",
                "description": "Entity to search the knowledge graph for",
                "minLength": 1,
                "maxLength": 255
            },
            "relation_type": {
                "type": "string",
                "description": "Optional filter by specific relationship type",
                "enum": [
                    "related_to",
                    "depends_on",
                    "implements", 
                    "extends",
                    "uses",
                    "references",
                    "contains",
                    "part_of",
                    "similar_to",
                    "conflicts_with"
                ]
            },
            "max_depth": {
                "type": "integer",
                "description": "Maximum depth to traverse in the graph",
                "default": 2,
                "minimum": 1,
                "maximum": 5
            }
        },
        "required": ["entity"],
        "additionalProperties": False
    },
    
    "auto_link_documents": {
        "type": "object",
        "properties": {
            "documents": {
                "type": "array",
                "description": "List of documents to auto-link based on similarity",
                "items": {"type": "object"},
                "minItems": 2,
                "maxItems": 50
            },
            "similarity_threshold": {
                "type": "number",
                "description": "Minimum similarity score for auto-linking",
                "default": 0.7,
                "minimum": 0.1,
                "maximum": 1.0
            }
        },
        "required": ["documents"],
        "additionalProperties": False
    },
    
    "get_document_relationships": {
        "type": "object",
        "properties": {
            "doc_id": {
                "type": "string",
                "description": "ID of the document to get relationships for",
                "minLength": 1,
                "maxLength": 255
            },
            "max_depth": {
                "type": "integer",
                "description": "Maximum relationship depth to retrieve",
                "default": 1,
                "minimum": 1,
                "maximum": 3
            }
        },
        "required": ["doc_id"],
        "additionalProperties": False
    },
    
    "list_tool_identifiers": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "Optional filter by tool category",
                "enum": ["memory", "chat", "graph", "pattern", "sync"]
            }
        },
        "additionalProperties": False
    },
    
    "get_tool_conversations": {
        "type": "object",
        "properties": {
            "source_tool": {
                "type": "string",
                "description": "Name of the tool to find conversations for",
                "minLength": 1,
                "maxLength": 100
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of conversations to return",
                "default": 10,
                "minimum": 1,
                "maximum": 100
            },
            "include_metadata": {
                "type": "boolean",
                "description": "Whether to include conversation metadata",
                "default": True
            }
        },
        "required": ["source_tool"],
        "additionalProperties": False
    }
}

# Tool descriptions for MCP protocol
CONTEXT_TOOL_DESCRIPTIONS = {
    "build_context": "Build a context window from a list of documents with token limiting and optimization",
    "retrieve_by_type": "Retrieve documents filtered by type using semantic search with FAISS indexing",
    "store_context_links": "Store bidirectional links between messages and document chunks for context tracking",
    "get_context_links_for_message": "Retrieve all context links associated with a specific message",
    "get_messages_for_chunk": "Find all messages that reference a specific document chunk",
    "get_context_usage_statistics": "Get comprehensive statistics about context usage patterns and performance",
    "link_resources": "Create typed relationship links between resources in the knowledge graph",
    "query_graph": "Query the Neo4j knowledge graph for related resources with depth control",
    "auto_link_documents": "Automatically create similarity-based links between documents using ML",
    "get_document_relationships": "Get all relationships for a document up to specified traversal depth",
    "list_tool_identifiers": "List all available tool identifiers in the LTMC system with optional filtering",
    "get_tool_conversations": "Get detailed conversation history that involved a specific tool"
}

# Response schemas for validation
CONTEXT_TOOL_RESPONSE_SCHEMAS = {
    "success_response": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "const": True},
            "error": {"type": "null"},
            "data": {"type": "object"},
            "message": {"type": "string"}
        },
        "required": ["success", "error", "data"],
        "additionalProperties": False
    },
    
    "error_response": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "const": False},
            "error": {"type": "string"},
            "error_code": {"type": "string"},
            "data": {"type": "null"}
        },
        "required": ["success", "error", "error_code", "data"],
        "additionalProperties": False
    }
}


def get_tool_schema(tool_name: str) -> Dict[str, Any]:
    """
    Get the JSON schema for a specific tool.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        Dict[str, Any]: JSON schema for the tool
        
    Raises:
        KeyError: If tool not found
    """
    if tool_name not in CONTEXT_TOOL_SCHEMAS:
        raise KeyError(f"Schema not found for tool: {tool_name}")
    
    return CONTEXT_TOOL_SCHEMAS[tool_name]


def get_tool_description(tool_name: str) -> str:
    """
    Get the description for a specific tool.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        str: Tool description
        
    Raises:
        KeyError: If tool not found
    """
    if tool_name not in CONTEXT_TOOL_DESCRIPTIONS:
        raise KeyError(f"Description not found for tool: {tool_name}")
    
    return CONTEXT_TOOL_DESCRIPTIONS[tool_name]


def validate_tool_exists(tool_name: str) -> bool:
    """
    Check if a tool schema exists.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        bool: True if tool exists
    """
    return tool_name in CONTEXT_TOOL_SCHEMAS


def list_available_tools() -> list:
    """
    List all available context tools.
    
    Returns:
        list: List of available tool names
    """
    return list(CONTEXT_TOOL_SCHEMAS.keys())


def get_tools_by_category() -> Dict[str, list]:
    """
    Group tools by functional category.
    
    Returns:
        Dict[str, list]: Tools grouped by category
    """
    return {
        "context_building": [
            "build_context",
            "retrieve_by_type",
            "get_context_usage_statistics"
        ],
        "message_linking": [
            "store_context_links",
            "get_context_links_for_message",
            "get_messages_for_chunk"
        ],
        "knowledge_graph": [
            "link_resources",
            "query_graph",
            "auto_link_documents",
            "get_document_relationships"
        ],
        "tool_management": [
            "list_tool_identifiers",
            "get_tool_conversations"
        ]
    }