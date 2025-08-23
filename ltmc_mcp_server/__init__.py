"""
LTMC FastMCP Server Package
==========================

Long-Term Memory Context (LTMC) MCP server with FastMCP 2.10 lazy loading.
Provides 126 tools for advanced memory, context, and agent operations.
"""

__version__ = "2.10.0"
__author__ = "LTMC Development Team"
__description__ = "Long-Term Memory Context MCP Server with FastMCP Lazy Loading"

# Package metadata
__all__ = [
    "main",
    "config", 
    "services",
    "tools",
    "components",
    "utils"
]

# Lazy loading support - only import when needed
def get_version():
    """Get package version."""
    return __version__

def get_description():
    """Get package description."""
    return __description__