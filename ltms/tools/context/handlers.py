"""
Context tool handlers for LTMC MCP server.
Handles delegation to LTMC consolidated tools with proper validation.
"""

from typing import Dict, Any, List
import logging

from .validation import (
    validate_message_id,
    validate_documents_list,
    validate_token_limit,
    validate_top_k,
    validate_string_parameter,
    validate_chunk_ids,
    create_error_response,
    create_success_response,
    ValidationError
)

logger = logging.getLogger(__name__)


def build_context_handler(documents: list, max_tokens: int = 4000) -> Dict[str, Any]:
    """
    Build a context window from documents with validation.
    
    Args:
        documents: List of documents to build context from
        max_tokens: Maximum tokens for context window
        
    Returns:
        Dict[str, Any]: Context build result
    """
    try:
        # Validate inputs
        validated_docs = validate_documents_list(documents)
        validated_tokens = validate_token_limit(max_tokens)
        
        # Import and call consolidated tools
        from ltms.tools.memory.memory_actions import memory_action
        
        result = memory_action(
            action="build_context",
            documents=validated_docs,
            max_tokens=validated_tokens
        )
        
        return create_success_response(result)
        
    except ValidationError as e:
        return create_error_response(str(e))
    except Exception as e:
        logger.error(f"Error in build_context_handler: {e}")
        return create_error_response(f"Internal error: {str(e)}", "internal_error")


def retrieve_by_type_handler(query: str, doc_type: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Retrieve documents by type using semantic search.
    
    Args:
        query: Search query
        doc_type: Type of documents to retrieve
        top_k: Number of results to return
        
    Returns:
        Dict[str, Any]: Retrieval result
    """
    try:
        # Validate inputs
        validated_query = validate_string_parameter(query, "query")
        validated_type = validate_string_parameter(doc_type, "doc_type")
        validated_k = validate_top_k(top_k, max_val=50)
        
        # Import and call consolidated tools
        from ltms.tools.memory.memory_actions import memory_action
        
        result = memory_action(
            action="retrieve_by_type",
            query=validated_query,
            doc_type=validated_type,
            top_k=validated_k
        )
        
        return create_success_response(result)
        
    except ValidationError as e:
        return create_error_response(str(e))
    except Exception as e:
        logger.error(f"Error in retrieve_by_type_handler: {e}")
        return create_error_response(f"Internal error: {str(e)}", "internal_error")


def store_context_links_handler(message_id: str, chunk_ids: list) -> Dict[str, Any]:
    """
    Store links between a message and document chunks.
    
    Args:
        message_id: ID of the message
        chunk_ids: List of chunk IDs to link
        
    Returns:
        Dict[str, Any]: Storage result
    """
    try:
        # Validate inputs
        validated_msg_id = validate_message_id(message_id)
        validated_chunk_ids = validate_chunk_ids(chunk_ids)
        
        # Import and call consolidated tools
        from ltms.tools.memory.chat_actions import chat_action
        
        result = chat_action(
            action="store_context_links",
            message_id=validated_msg_id,
            chunk_ids=validated_chunk_ids
        )
        
        return create_success_response(result)
        
    except ValidationError as e:
        return create_error_response(str(e))
    except Exception as e:
        logger.error(f"Error in store_context_links_handler: {e}")
        return create_error_response(f"Internal error: {str(e)}", "internal_error")


def get_context_links_for_message_handler(message_id: str) -> Dict[str, Any]:
    """
    Retrieve context links for a specific message.
    
    Args:
        message_id: ID of the message to get links for
        
    Returns:
        Dict[str, Any]: Context links result
    """
    try:
        # Validate inputs
        validated_msg_id = validate_message_id(message_id)
        
        # Import and call consolidated tools
        from ltms.tools.memory.chat_actions import chat_action
        
        result = chat_action(
            action="get_context_links",
            message_id=validated_msg_id
        )
        
        return create_success_response(result)
        
    except ValidationError as e:
        return create_error_response(str(e))
    except Exception as e:
        logger.error(f"Error in get_context_links_for_message_handler: {e}")
        return create_error_response(f"Internal error: {str(e)}", "internal_error")


def get_messages_for_chunk_handler(chunk_id: int) -> Dict[str, Any]:
    """
    Get messages that reference a specific document chunk.
    
    Args:
        chunk_id: ID of the chunk to find messages for
        
    Returns:
        Dict[str, Any]: Messages result
    """
    try:
        # Validate inputs
        if not isinstance(chunk_id, int) or chunk_id < 1:
            raise ValidationError("chunk_id must be a positive integer")
        
        # Import and call consolidated tools
        from ltms.tools.memory.chat_actions import chat_action
        
        result = chat_action(
            action="get_messages_for_chunk",
            chunk_id=chunk_id
        )
        
        return create_success_response(result)
        
    except ValidationError as e:
        return create_error_response(str(e))
    except Exception as e:
        logger.error(f"Error in get_messages_for_chunk_handler: {e}")
        return create_error_response(f"Internal error: {str(e)}", "internal_error")


def get_context_usage_statistics_handler() -> Dict[str, Any]:
    """
    Get statistics about context usage patterns.
    
    Returns:
        Dict[str, Any]: Usage statistics result
    """
    try:
        # Import and call consolidated tools
        from ltms.tools.memory.memory_actions import memory_action
        
        result = memory_action(action="get_context_statistics")
        
        return create_success_response(result)
        
    except Exception as e:
        logger.error(f"Error in get_context_usage_statistics_handler: {e}")
        return create_error_response(f"Internal error: {str(e)}", "internal_error")


def link_resources_handler(source_id: str, target_id: str, relation: str) -> Dict[str, Any]:
    """
    Create a relationship link between two resources.
    
    Args:
        source_id: ID of the source resource
        target_id: ID of the target resource
        relation: Type of relationship
        
    Returns:
        Dict[str, Any]: Link creation result
    """
    try:
        # Validate inputs
        validated_source = validate_string_parameter(source_id, "source_id")
        validated_target = validate_string_parameter(target_id, "target_id")
        validated_relation = validate_string_parameter(relation, "relation")
        
        # Import and call consolidated tools
        from ltms.tools.graph.graph_actions import graph_action
        
        result = graph_action(
            action="link",
            source_id=validated_source,
            target_id=validated_target,
            relation_type=validated_relation
        )
        
        return create_success_response(result)
        
    except ValidationError as e:
        return create_error_response(str(e))
    except Exception as e:
        logger.error(f"Error in link_resources_handler: {e}")
        return create_error_response(f"Internal error: {str(e)}", "internal_error")


def query_graph_handler(entity: str, relation_type: str = None) -> Dict[str, Any]:
    """
    Query the knowledge graph for related resources.
    
    Args:
        entity: Entity to search for
        relation_type: Optional filter by relationship type
        
    Returns:
        Dict[str, Any]: Graph query result
    """
    try:
        # Validate inputs
        validated_entity = validate_string_parameter(entity, "entity")
        validated_relation = validate_string_parameter(relation_type, "relation_type", required=False)
        
        # Import and call consolidated tools
        from ltms.tools.graph.graph_actions import graph_action
        
        result = graph_action(
            action="query",
            entity=validated_entity,
            relation_type=validated_relation
        )
        
        return create_success_response(result)
        
    except ValidationError as e:
        return create_error_response(str(e))
    except Exception as e:
        logger.error(f"Error in query_graph_handler: {e}")
        return create_error_response(f"Internal error: {str(e)}", "internal_error")


def auto_link_documents_handler(documents: list) -> Dict[str, Any]:
    """
    Automatically create links between similar documents.
    
    Args:
        documents: List of documents to auto-link
        
    Returns:
        Dict[str, Any]: Auto-linking result
    """
    try:
        # Validate inputs
        validated_docs = validate_documents_list(documents)
        
        # Import and call consolidated tools
        from ltms.tools.graph.graph_actions import graph_action
        
        result = graph_action(
            action="auto_link",
            documents=validated_docs
        )
        
        return create_success_response(result)
        
    except ValidationError as e:
        return create_error_response(str(e))
    except Exception as e:
        logger.error(f"Error in auto_link_documents_handler: {e}")
        return create_error_response(f"Internal error: {str(e)}", "internal_error")


def get_document_relationships_handler(doc_id: str) -> Dict[str, Any]:
    """
    Get all relationships for a document.
    
    Args:
        doc_id: ID of the document
        
    Returns:
        Dict[str, Any]: Document relationships result
    """
    try:
        # Validate inputs
        validated_doc_id = validate_string_parameter(doc_id, "doc_id")
        
        # Import and call consolidated tools
        from ltms.tools.graph.graph_actions import graph_action
        
        result = graph_action(
            action="get_relationships",
            doc_id=validated_doc_id
        )
        
        return create_success_response(result)
        
    except ValidationError as e:
        return create_error_response(str(e))
    except Exception as e:
        logger.error(f"Error in get_document_relationships_handler: {e}")
        return create_error_response(f"Internal error: {str(e)}", "internal_error")


def list_tool_identifiers_handler() -> Dict[str, Any]:
    """
    List all available tool identifiers in the system.
    
    Returns:
        Dict[str, Any]: Tool identifiers result
    """
    try:
        # Import and call consolidated tools
        from ltms.tools.memory.chat_actions import chat_action
        
        result = chat_action(action="get_tool_identifiers")
        
        return create_success_response(result)
        
    except Exception as e:
        logger.error(f"Error in list_tool_identifiers_handler: {e}")
        return create_error_response(f"Internal error: {str(e)}", "internal_error")


def get_tool_conversations_handler(source_tool: str, limit: int = 50) -> Dict[str, Any]:
    """
    Get conversations that involved a specific tool.
    
    Args:
        source_tool: Name of the source tool
        limit: Maximum number of conversations to return
        
    Returns:
        Dict[str, Any]: Tool conversations result
    """
    try:
        # Validate inputs
        validated_tool = validate_string_parameter(source_tool, "source_tool")
        validated_limit = validate_top_k(limit, default=50, max_val=100)
        
        # Import and call consolidated tools
        from ltms.tools.memory.chat_actions import chat_action
        
        result = chat_action(
            action="get_tool_conversations",
            source_tool=validated_tool,
            limit=validated_limit
        )
        
        return create_success_response(result)
        
    except ValidationError as e:
        return create_error_response(str(e))
    except Exception as e:
        logger.error(f"Error in get_tool_conversations_handler: {e}")
        return create_error_response(f"Internal error: {str(e)}", "internal_error")