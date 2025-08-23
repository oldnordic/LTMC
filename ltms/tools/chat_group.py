"""Chat group tools - canonical group:operation interface."""

from typing import Dict, Any

# Import existing implementations
from ltms.services.chat_service import (
    log_chat as _log_chat,
    get_chats_by_tool as _get_chats_by_tool
)
from ltms.services.context_service import (
    get_tool_conversations as _get_tool_conversations
)


def chat_log(content: str, conversation_id: str, role: str = "user", agent_name: str = None, metadata: Dict[str, Any] = None, source_tool: str = None) -> Dict[str, Any]:
    """Log a chat/conversation."""
    return _log_chat(conversation_id, role, content, agent_name, metadata, source_tool)


def chat_get_by_tool(tool: str, limit: int = 10) -> Dict[str, Any]:
    """Retrieve chats for a tool/topic."""
    return _get_chats_by_tool(tool, limit)


def chat_get_tool_conversations(tool: str, limit: int = 50) -> Dict[str, Any]:
    """Get all conversations for a tool."""
    return _get_tool_conversations(tool, limit)


# Tool registry with group:operation names
CHAT_GROUP_TOOLS = {
    "chat:log": {
        "handler": chat_log,
        "description": "Log a chat/conversation",
        "schema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The chat message content to log"
                },
                "conversation_id": {
                    "type": "string",
                    "description": "Unique identifier for the conversation"
                },
                "role": {
                    "type": "string",
                    "description": "Role of the message sender (user, assistant, system)",
                    "enum": ["user", "assistant", "system"],
                    "default": "user"
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
            "required": ["conversation_id", "content"]
        }
    },
    
    "chat:get_by_tool": {
        "handler": chat_get_by_tool,
        "description": "Retrieve chats for a tool/topic",
        "schema": {
            "type": "object",
            "properties": {
                "tool": {
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
            "required": ["tool"]
        }
    },
    
    "chat:get_tool_conversations": {
        "handler": chat_get_tool_conversations,
        "description": "Get all conversations for a tool",
        "schema": {
            "type": "object",
            "properties": {
                "tool": {
                    "type": "string",
                    "description": "Name of the source tool"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of conversations to return",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 100
                }
            },
            "required": ["tool"]
        }
    }
}