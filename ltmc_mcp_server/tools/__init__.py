"""
LTMC Tools Module - Official MCP SDK Implementation
==================================================

Simple, clean tool registration following official Python MCP SDK patterns.
One function to register all tools - simple and correct.
"""

# Import all tool registration functions
from .memory import register_memory_tools, register_consolidated_memory_tools
from .advanced import register_advanced_tools, register_consolidated_advanced_tools
from .unified import register_unified_tools, register_consolidated_unified_tools
from .chat import register_basic_chat_tools, register_advanced_chat_tools, register_consolidated_advanced_chat_tools
from .todo import register_basic_todo_tools, register_advanced_todo_tools, register_consolidated_advanced_todo_tools
from .context import (
    register_core_context_tools, register_context_tools, 
    register_graph_context_tools, register_consolidated_graph_context_tools
)
from .blueprint import (
    register_core_blueprint_tools, register_query_blueprint_tools,
    register_consolidated_blueprint_tools
)
from .redis import register_basic_redis_tools, register_management_redis_tools, register_consolidated_redis_tools
from .taskmaster import (
    register_basic_taskmaster_tools, register_analysis_taskmaster_tools,
    register_consolidated_analysis_taskmaster_tools
)
from .documentation import (
    register_core_sync_documentation_tools, register_documentation_tools,
    register_validation_sync_documentation_tools, 
    register_monitoring_analysis_documentation_tools,
    register_status_analysis_documentation_tools,
    register_consolidated_specialized_documentation_tools
)
from .code_patterns import (
    register_basic_pattern_tools, register_code_pattern_tools, 
    register_analysis_pattern_tools, register_consolidated_analysis_pattern_tools
)
from .mermaid import (
    register_basic_mermaid_tools, register_advanced_mermaid_tools,
    register_analysis_core_mermaid_tools, register_analysis_intelligence_mermaid_tools,
    register_consolidated_analysis_mermaid_tools,
    register_consolidated_analysis_core_mermaid_tools,
    register_consolidated_advanced_mermaid_tools,
    register_consolidated_analysis_intelligence_mermaid_tools
)


def get_all_tools(settings):
    """
    Get all LTMC tools as a dictionary suitable for low-level MCP server.
    
    Returns:
        dict: Dictionary of tool_name -> tool_definition
    """
    # This would need to be implemented to collect all tools
    # For now, return a simple test tool to get the server working
    return {
        "ping": {
            "description": "Test connectivity with LTMC server",
            "schema": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Optional message to echo back"
                    }
                }
            },
            "handler": lambda message="pong": f"LTMC Server Response: {message}"
        }
    }


def register_all_tools(server, settings):
    """
    Register all LTMC tools with the MCP server.
    
    This is the ONE function that registers everything.
    Simple, clean, and follows official MCP SDK patterns.
    
    Args:
        server: FastMCP server instance
        settings: LTMC settings
    """
    # Register all tools in one clean function
    # This is the proper, simple way
    
    # Memory tools
    register_memory_tools(server, settings)
    register_consolidated_memory_tools(server, settings)
    
    # Advanced tools
    register_advanced_tools(server, settings)
    register_consolidated_advanced_tools(server, settings)
    
    # Unified tools
    register_unified_tools(server, settings)
    register_consolidated_unified_tools(server, settings)
    
    # Chat tools
    register_basic_chat_tools(server, settings)
    register_advanced_chat_tools(server, settings)
    register_consolidated_advanced_chat_tools(server, settings)
    
    # Todo tools
    register_basic_todo_tools(server, settings)
    register_advanced_todo_tools(server, settings)
    register_consolidated_advanced_todo_tools(server, settings)
    
    # Context tools
    register_core_context_tools(server, settings)
    register_context_tools(server, settings)
    register_graph_context_tools(server, settings)
    register_consolidated_graph_context_tools(server, settings)
    
    # Blueprint tools
    register_core_blueprint_tools(server, settings)
    register_query_blueprint_tools(server, settings)
    register_consolidated_blueprint_tools(server, settings)
    
    # Redis tools
    register_basic_redis_tools(server, settings)
    register_management_redis_tools(server, settings)
    register_consolidated_redis_tools(server, settings)
    
    # Taskmaster tools
    register_basic_taskmaster_tools(server, settings)
    register_analysis_taskmaster_tools(server, settings)
    register_consolidated_analysis_taskmaster_tools(server, settings)
    
    # Documentation tools
    register_core_sync_documentation_tools(server, settings)
    register_documentation_tools(server, settings)
    register_validation_sync_documentation_tools(server, settings)
    register_monitoring_analysis_documentation_tools(server, settings)
    register_status_analysis_documentation_tools(server, settings)
    register_consolidated_specialized_documentation_tools(server, settings)
    
    # Code pattern tools
    register_basic_pattern_tools(server, settings)
    register_code_pattern_tools(server, settings)
    register_analysis_pattern_tools(server, settings)
    register_consolidated_analysis_pattern_tools(server, settings)
    
    # Mermaid tools
    register_basic_mermaid_tools(server, settings)
    register_advanced_mermaid_tools(server, settings)
    register_analysis_core_mermaid_tools(server, settings)
    register_analysis_intelligence_mermaid_tools(server, settings)
    register_consolidated_analysis_mermaid_tools(server, settings)
    register_consolidated_analysis_core_mermaid_tools(server, settings)
    register_consolidated_advanced_mermaid_tools(server, settings)
    register_consolidated_analysis_intelligence_mermaid_tools(server, settings)


# Export the main functions
__all__ = ["register_all_tools", "get_all_tools"]