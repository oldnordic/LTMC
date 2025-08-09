"""Chat and conversation management tools for LTMC MCP server."""

from typing import Dict, Any, List

# Import implementation functions
from ltms.mcp_server import (
    log_chat as _log_chat,
    ask_with_context as _ask_with_context,
    route_query as _route_query,
    get_chats_by_tool as _get_chats_by_tool
)


def log_chat_handler(conversation_id: str, role: str, content: str, agent_name: str = None, metadata: Dict[str, Any] = None, source_tool: str = None) -> Dict[str, Any]:
    """Log a chat message with automatic context linking."""
    return _log_chat(conversation_id, role, content, agent_name, metadata, source_tool)


def ask_with_context_handler(query: str, conversation_id: str, top_k: int = 5) -> Dict[str, Any]:
    """Ask a question with relevant context from memory."""
    return _ask_with_context(query, conversation_id, top_k)


def route_query_handler(query: str, source_types: List[str] = None, top_k: int = 5) -> Dict[str, Any]:
    """Route a query to the most appropriate context or tool."""
    if source_types is None:
        source_types = ["document", "code", "chat", "todo"]
    return _route_query(query, source_types, top_k)


def get_chats_by_tool_handler(source_tool: str, limit: int = 10) -> Dict[str, Any]:
    """Get chat messages that used a specific tool."""
    return _get_chats_by_tool(source_tool, limit)


# Tool definitions for MCP protocol
CHAT_TOOLS = {
    "log_chat": {
        "handler": log_chat_handler,
        "description": "Log a chat message with automatic context linking and relationship building",
        "schema": {
            "type": "object",
            "properties": {
                "conversation_id": {
                    "type": "string",
                    "description": "Unique identifier for the conversation"
                },
                "role": {
                    "type": "string",
                    "description": "Role of the message sender (user, assistant, system)",
                    "enum": ["user", "assistant", "system"]
                },
                "content": {
                    "type": "string",
                    "description": "The chat message content to log"
                },
                "agent_name": {
                    "type": "string",
                    "description": "Name of the agent if applicable"
                },
                "metadata": {
                    "type": "object",
                    "description": "Optional metadata dictionary"
                },
                "source_tool": {
                    "type": "string",
                    "description": "Tool that generated this message (claude-code, cursor, vscode, etc.)"
                }
            },
            "required": ["conversation_id", "role", "content"]
        }
    },
    
    "ask_with_context": {
        "handler": ask_with_context_handler,
        "description": "Ask a question with relevant context retrieved from memory",
        "schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query/question to ask"
                },
                "conversation_id": {
                    "type": "string",
                    "description": "Conversation ID for context scoping"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Maximum number of context items to retrieve",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 50
                }
            },
            "required": ["query", "conversation_id"]
        }
    },
    
    "route_query": {
        "handler": route_query_handler,
        "description": "Route a query to the most appropriate context or processing method",
        "schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query to route and process"
                },
                "source_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Types of sources to search (document, code, chat, todo)",
                    "default": ["document", "code", "chat", "todo"]
                },
                "top_k": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 50
                }
            },
            "required": ["query"]
        }
    },
    
    "get_chats_by_tool": {
        "handler": get_chats_by_tool_handler,
        "description": "Retrieve chat messages that involved a specific tool usage",
        "schema": {
            "type": "object",
            "properties": {
                "source_tool": {
                    "type": "string",
                    "description": "Name of the source tool to search for in chat history"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of chat messages to return",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100
                }
            },
            "required": ["source_tool"]
        }
    }
}