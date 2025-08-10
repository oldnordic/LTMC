"""LTMC Tools Package

Shared tool definitions for both FastMCP STDIO and FastAPI HTTP transports.
Eliminates code duplication by providing a single source of truth for all MCP tools.
"""

from .memory_tools import MEMORY_TOOLS
from .chat_tools import CHAT_TOOLS  
from .todo_tools import TODO_TOOLS
from .code_pattern_tools import CODE_PATTERN_TOOLS
from .context_tools import CONTEXT_TOOLS
from .blueprint_tool_registry import BLUEPRINT_TOOLS

__all__ = [
    'MEMORY_TOOLS',
    'CHAT_TOOLS',
    'TODO_TOOLS', 
    'CODE_PATTERN_TOOLS',
    'CONTEXT_TOOLS',
    'BLUEPRINT_TOOLS',
    'ALL_TOOLS'
]

# Combined registry of all tools
ALL_TOOLS = {
    **MEMORY_TOOLS,
    **CHAT_TOOLS,
    **TODO_TOOLS,
    **CODE_PATTERN_TOOLS,
    **CONTEXT_TOOLS,
    **BLUEPRINT_TOOLS
}