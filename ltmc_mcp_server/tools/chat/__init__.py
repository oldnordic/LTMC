"""Chat tools module."""

from .basic_chat_tools import register_basic_chat_tools
from .advanced_chat_tools import register_advanced_chat_tools
from .consolidated_advanced_chat_tools import register_consolidated_advanced_chat_tools

def register_chat_tools(mcp, settings):
    """Register all chat tools."""
    register_basic_chat_tools(mcp, settings)
    register_advanced_chat_tools(mcp, settings)

__all__ = ["register_chat_tools", "register_basic_chat_tools", "register_advanced_chat_tools", "register_consolidated_advanced_chat_tools"]