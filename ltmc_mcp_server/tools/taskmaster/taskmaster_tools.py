"""
Taskmaster Tools - FastMCP Implementation
=========================================

Unified taskmaster tools module combining basic and analysis tools.
Note: Full taskmaster implementation has 13 tools - this implements 4 core tools.

Tools implemented (from unified_mcp_server.py analysis):
1. create_task_blueprint - Create new task blueprints with ML complexity analysis
2. get_task_dependencies - Get dependencies for a task blueprint
3. analyze_task_complexity - Analyze task complexity using ML-based scoring
4. get_taskmaster_performance_metrics - Get performance metrics for the task manager

Remaining 9 tools: update_blueprint_metadata, list_project_blueprints, 
resolve_blueprint_execution_order, add_blueprint_dependency, delete_task_blueprint,
decompose_task_blueprint, assign_task_to_team, update_task_progress, get_team_workload_overview
"""

# Official MCP SDK import - from research findings
from mcp.server.fastmcp import FastMCP

# Local imports
from ltmc_mcp_server.config.settings import LTMCSettings
from ltmc_mcp_server.utils.logging_utils import get_tool_logger

# Import modular tool registration functions
from .basic_taskmaster_tools import register_basic_taskmaster_tools
from .analysis_taskmaster_tools import register_analysis_taskmaster_tools


def register_taskmaster_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """
    Register core taskmaster tools with FastMCP server.
    
    Combines basic and analysis taskmaster tools through modular components
    while maintaining unified interface and API compatibility.
    
    Following official FastMCP registration pattern:
    @mcp.tool()
    def tool_name(...) -> ...
    
    Args:
        mcp: FastMCP server instance
        settings: LTMC settings
    """
    logger = get_tool_logger('taskmaster')
    logger.info("Registering unified taskmaster tools")
    
    # Register basic taskmaster tools (create_task_blueprint, get_task_dependencies)
    register_basic_taskmaster_tools(mcp, settings)
    
    # Register analysis taskmaster tools (analyze_task_complexity, get_taskmaster_performance_metrics)
    register_analysis_taskmaster_tools(mcp, settings)
    
    logger.info("✅ Core taskmaster tools registered successfully")
    logger.info("  - Basic tools: create_task_blueprint, get_task_dependencies")
    logger.info("  - Analysis tools: analyze_task_complexity, get_taskmaster_performance_metrics")
    logger.info("  - Modular architecture: 2 components under 300 lines each")
    logger.info("  - Note: 4 of 13 total taskmaster tools implemented (core subset)")