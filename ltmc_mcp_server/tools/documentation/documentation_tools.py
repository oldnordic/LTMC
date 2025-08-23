"""
Documentation Tools - FastMCP Implementation
===========================================

Unified documentation tools module combining sync and analysis tools.
Maintains all 8 documentation tools while respecting 300-line limit through modularization.

Tools implemented (from unified_mcp_server.py analysis):
1. sync_documentation_with_code - Sync documentation with code changes
2. validate_documentation_consistency - Validate doc-code consistency
3. detect_documentation_drift - Detect documentation drift
4. update_documentation_from_blueprint - Update docs from blueprints
5. get_documentation_consistency_score - Get consistency score between docs and code
6. start_real_time_sync - Start real-time synchronization monitoring
7. get_sync_status - Get synchronization status for project
8. detect_code_changes - Detect changes in code files for synchronization
"""

# Official MCP SDK import - from research findings
from mcp.server.fastmcp import FastMCP

# Local imports
from ltmc_mcp_server.config.settings import LTMCSettings
from ltmc_mcp_server.utils.logging_utils import get_tool_logger

# Import modular tool registration functions
from .core_sync_tools import register_core_sync_documentation_tools
from .validation_sync_tools import register_validation_sync_documentation_tools
from .monitoring_analysis_tools import register_monitoring_analysis_documentation_tools
from .status_analysis_tools import register_status_analysis_documentation_tools


def register_documentation_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """
    Register all documentation tools with FastMCP server.
    
    Combines sync and analysis documentation tools through modular components
    while maintaining unified interface and API compatibility.
    
    Following official FastMCP registration pattern:
    @mcp.tool()
    def tool_name(...) -> ...
    
    Args:
        mcp: FastMCP server instance
        settings: LTMC settings
    """
    logger = get_tool_logger('documentation')
    logger.info("Registering unified documentation tools")
    
    # Register core sync documentation tools (2 tools)
    register_core_sync_documentation_tools(mcp, settings)
    
    # Register validation sync documentation tools (2 tools)
    register_validation_sync_documentation_tools(mcp, settings)
    
    # Register monitoring analysis documentation tools (2 tools)
    register_monitoring_analysis_documentation_tools(mcp, settings)
    
    # Register status analysis documentation tools (2 tools)
    register_status_analysis_documentation_tools(mcp, settings)
    
    logger.info("✅ All documentation tools registered successfully")
    logger.info("  - Core sync tools: sync_documentation_with_code, update_documentation_from_blueprint")
    logger.info("  - Validation sync tools: validate_documentation_consistency, detect_documentation_drift")
    logger.info("  - Monitoring analysis tools: get_documentation_consistency_score, start_real_time_sync")
    logger.info("  - Status analysis tools: get_sync_status, detect_code_changes")
    logger.info("  - Modular architecture: 4 components under 300 lines each")
    logger.info("  - Documentation synchronization: Full code-documentation consistency capabilities")