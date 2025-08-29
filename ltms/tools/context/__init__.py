"""
LTMC Context Tools - Modularized Implementation.

This module provides a modular, high-performance context management system for LTMC
with comprehensive validation, relationship management, and MCP protocol compliance.

Public API maintains full compatibility with the original monolithic implementation.
"""

# Core handler functions
from .handlers import (
    build_context_handler,
    retrieve_by_type_handler,
    store_context_links_handler,
    get_context_links_for_message_handler,
    get_messages_for_chunk_handler,
    get_context_usage_statistics_handler,
    link_resources_handler,
    query_graph_handler,
    auto_link_documents_handler,
    get_document_relationships_handler,
    list_tool_identifiers_handler,
    get_tool_conversations_handler
)

# Schema definitions
from .schemas import (
    CONTEXT_TOOL_SCHEMAS,
    CONTEXT_TOOL_DESCRIPTIONS,
    CONTEXT_TOOL_RESPONSE_SCHEMAS,
    get_tool_schema,
    get_tool_description,
    validate_tool_exists,
    list_available_tools,
    get_tools_by_category
)

# Validation utilities
from .validation import (
    ValidationError,
    validate_message_id,
    validate_documents_list,
    validate_token_limit,
    validate_top_k,
    validate_string_parameter,
    validate_chunk_ids,
    create_error_response,
    create_success_response
)

# Relationship management
from .relationships import (
    RelationshipManager,
    relationship_manager
)

# Build the complete CONTEXT_TOOLS dictionary for MCP compatibility
CONTEXT_TOOLS = {}

# Tool definitions mapping handlers to schemas
_TOOL_MAPPINGS = [
    ("build_context", build_context_handler),
    ("retrieve_by_type", retrieve_by_type_handler),
    ("store_context_links", store_context_links_handler),
    ("get_context_links_for_message", get_context_links_for_message_handler),
    ("get_messages_for_chunk", get_messages_for_chunk_handler),
    ("get_context_usage_statistics", get_context_usage_statistics_handler),
    ("link_resources", link_resources_handler),
    ("query_graph", query_graph_handler),
    ("auto_link_documents", auto_link_documents_handler),
    ("get_document_relationships", get_document_relationships_handler),
    ("list_tool_identifiers", list_tool_identifiers_handler),
    ("get_tool_conversations", get_tool_conversations_handler)
]

# Build CONTEXT_TOOLS dictionary
for tool_name, handler_func in _TOOL_MAPPINGS:
    CONTEXT_TOOLS[tool_name] = {
        "handler": handler_func,
        "description": get_tool_description(tool_name),
        "schema": get_tool_schema(tool_name)
    }

# Utility functions for backward compatibility
def get_context_tool_handler(tool_name: str):
    """
    Get handler function for a specific context tool.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        Callable: Handler function
        
    Raises:
        KeyError: If tool not found
    """
    if tool_name not in CONTEXT_TOOLS:
        raise KeyError(f"Tool not found: {tool_name}")
    
    return CONTEXT_TOOLS[tool_name]["handler"]


def get_context_tool_info(tool_name: str) -> dict:
    """
    Get complete information about a context tool.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        dict: Tool information including handler, description, and schema
        
    Raises:
        KeyError: If tool not found
    """
    if tool_name not in CONTEXT_TOOLS:
        raise KeyError(f"Tool not found: {tool_name}")
    
    return CONTEXT_TOOLS[tool_name].copy()


def validate_context_tool_request(tool_name: str, parameters: dict) -> dict:
    """
    Validate a tool request against its schema.
    
    Args:
        tool_name: Name of the tool
        parameters: Request parameters
        
    Returns:
        dict: Validation result with success status
    """
    try:
        if not validate_tool_exists(tool_name):
            return create_error_response(f"Unknown tool: {tool_name}")
        
        schema = get_tool_schema(tool_name)
        
        # Basic validation - in production, use jsonschema library
        required_params = schema.get("required", [])
        properties = schema.get("properties", {})
        
        # Check required parameters
        for param in required_params:
            if param not in parameters:
                return create_error_response(f"Missing required parameter: {param}")
        
        # Check parameter types (basic validation)
        for param, value in parameters.items():
            if param in properties:
                expected_type = properties[param].get("type")
                if expected_type == "string" and not isinstance(value, str):
                    return create_error_response(f"Parameter {param} must be a string")
                elif expected_type == "integer" and not isinstance(value, int):
                    return create_error_response(f"Parameter {param} must be an integer")
                elif expected_type == "array" and not isinstance(value, list):
                    return create_error_response(f"Parameter {param} must be an array")
                elif expected_type == "object" and not isinstance(value, dict):
                    return create_error_response(f"Parameter {param} must be an object")
        
        return create_success_response({"validated": True})
        
    except Exception as e:
        return create_error_response(f"Validation error: {str(e)}")


def get_context_tools_summary() -> dict:
    """
    Get a summary of all available context tools.
    
    Returns:
        dict: Summary of context tools organized by category
    """
    tools_by_category = get_tools_by_category()
    
    summary = {
        "total_tools": len(CONTEXT_TOOLS),
        "categories": {},
        "all_tools": list(CONTEXT_TOOLS.keys())
    }
    
    for category, tools in tools_by_category.items():
        summary["categories"][category] = {
            "count": len(tools),
            "tools": tools,
            "descriptions": {tool: get_tool_description(tool) for tool in tools}
        }
    
    return summary


# Public API exports - maintains full backward compatibility
__all__ = [
    # Handler functions (backward compatibility)
    "build_context_handler",
    "retrieve_by_type_handler",
    "store_context_links_handler",
    "get_context_links_for_message_handler", 
    "get_messages_for_chunk_handler",
    "get_context_usage_statistics_handler",
    "link_resources_handler",
    "query_graph_handler",
    "auto_link_documents_handler",
    "get_document_relationships_handler",
    "list_tool_identifiers_handler",
    "get_tool_conversations_handler",
    
    # MCP tools dictionary (backward compatibility)
    "CONTEXT_TOOLS",
    
    # Schema utilities
    "CONTEXT_TOOL_SCHEMAS",
    "CONTEXT_TOOL_DESCRIPTIONS",
    "CONTEXT_TOOL_RESPONSE_SCHEMAS",
    "get_tool_schema",
    "get_tool_description",
    "validate_tool_exists",
    "list_available_tools",
    "get_tools_by_category",
    
    # Validation utilities
    "ValidationError",
    "validate_message_id",
    "validate_documents_list", 
    "validate_token_limit",
    "validate_top_k",
    "validate_string_parameter",
    "validate_chunk_ids",
    "create_error_response",
    "create_success_response",
    
    # Relationship management
    "RelationshipManager",
    "relationship_manager",
    
    # Utility functions
    "get_context_tool_handler",
    "get_context_tool_info",
    "validate_context_tool_request",
    "get_context_tools_summary"
]

# Version information
__version__ = "2.0.0"
__description__ = "LTMC Context Tools - Modularized Implementation"