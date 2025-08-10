"""Todo tools module."""

from .basic_todo_tools import register_basic_todo_tools
from .advanced_todo_tools import register_advanced_todo_tools

def register_todo_tools(mcp, settings):
    """Register all todo tools."""
    register_basic_todo_tools(mcp, settings)
    register_advanced_todo_tools(mcp, settings)

__all__ = ["register_todo_tools", "register_basic_todo_tools", "register_advanced_todo_tools"]