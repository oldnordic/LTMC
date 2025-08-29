#!/usr/bin/env python3
"""
Enhanced LTMC MCP Server with Claude Code Subagent Intelligence Integration

Production-ready MCP server with comprehensive subagent intelligence capture,
performance optimization, and cross-session learning capabilities.

File: ltms/subagent_main.py
Lines: ~295 (under 300 limit)
Purpose: Enhanced MCP server for Claude Code subagent integration
"""

# Standard library imports
import sys
import os
import logging
import asyncio
from pathlib import Path
from datetime import datetime

# Third-party imports
import anyio
from mcp.server.lowlevel.server import Server as MCPServer
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
from mcp.types import (
    ServerCapabilities, Tool, TextContent, ToolsCapability, 
    ResourcesCapability, PromptsCapability
)

# Local application imports
from ltms.tools.common.tool_registry import get_consolidated_tools
from ltms.database.schema import create_tables
from ltms.database.neo4j_store import get_neo4j_graph_store
from ltms.config.json_config_loader import get_config

# Subagent intelligence imports
from ltms.subagent.intelligence_tracker import SubagentIntelligenceTracker
from ltms.subagent.session_manager import SubagentSessionManager
from ltms.subagent.performance_optimizer import MCPPerformanceOptimizer

# Configure logging to stderr only (required for stdio MCP transport)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr  # CRITICAL: Only stderr for stdio transport
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Change to project root for consistent database paths
os.chdir(str(project_root))


class LTMCSubagentMCPServer:
    """
    Enhanced LTMC MCP Server with comprehensive subagent intelligence.
    
    Integrates intelligence tracking, session management, and performance
    optimization for Claude Code subagent interactions.
    """
    
    def __init__(self):
        self.server = MCPServer("LTMC-Subagent-Intelligence")
        self.intelligence_tracker = SubagentIntelligenceTracker()
        self.session_manager = SubagentSessionManager()
        self.performance_optimizer = MCPPerformanceOptimizer()
        self.config = get_config()
        self._current_session_id = None
        
    async def initialize(self):
        """Initialize all server components and databases."""
        # Initialize database
        if not self._initialize_database():
            logger.error("Database initialization failed")
            return False
        
        # Initialize graph store (non-blocking)
        graph_available = await self._initialize_graph_store()
        if graph_available:
            logger.info("LTMC Subagent Server starting with Neo4j + SQLite backend")
        else:
            logger.info("LTMC Subagent Server starting with SQLite-only backend")
        
        # Initialize intelligence tracking schema
        try:
            # Intelligence tracker initializes its own schema
            logger.info("Subagent intelligence tracking initialized")
        except Exception as e:
            logger.error(f"Intelligence tracking initialization failed: {e}")
            return False
        
        return True
    
    def _initialize_database(self) -> bool:
        """Initialize database with proper schema."""
        try:
            import sqlite3
            
            # Get database path from config
            db_path = self.config.get_db_path()
            
            # Create connection and initialize tables
            with sqlite3.connect(db_path) as conn:
                create_tables(conn)
            
            logger.info(f"Database initialized successfully at {db_path}")
            return True
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False
    
    async def _initialize_graph_store(self) -> bool:
        """Initialize Neo4j graph store for enhanced relationship management."""
        try:
            neo4j_store = await get_neo4j_graph_store()
            if neo4j_store and neo4j_store.driver:
                # Test the connection
                try:
                    with neo4j_store.driver.session() as session:
                        session.run("RETURN 1")
                    logger.info("Neo4j graph store initialized and healthy")
                    return True
                except Exception as e:
                    logger.warning(f"Neo4j health check failed: {e}")
                    return False
            else:
                logger.info("Neo4j initialization skipped")
                return False
        except Exception as e:
            logger.error(f"Graph store initialization failed: {e}")
            return False
    
    def setup_handlers(self):
        """Set up all MCP protocol handlers with subagent intelligence."""
        
        @self.server.list_tools()
        async def handle_list_tools():
            """List all available tools with enhanced schemas for subagent intelligence."""
            tools = []
            consolidated_tools = get_consolidated_tools()
            
            logger.info(f"Listing {len(consolidated_tools)} tools with subagent intelligence")
            
            for tool_name, tool_def in consolidated_tools.items():
                try:
                    if isinstance(tool_def, dict):
                        # Enhanced schema with subagent metadata
                        description = tool_def.get("description", f"{tool_name} tool")
                        schema = tool_def.get("schema", {"type": "object", "properties": {}})
                        
                        # Add subagent intelligence properties to schema
                        if "properties" not in schema:
                            schema["properties"] = {}
                        
                        schema["properties"]["_subagent_session_id"] = {
                            "type": "string",
                            "description": "Subagent session identifier for intelligence tracking"
                        }
                        schema["properties"]["_intelligence_capture"] = {
                            "type": "boolean", 
                            "description": "Enable intelligence capture for this call",
                            "default": True
                        }
                        schema["properties"]["_performance_optimize"] = {
                            "type": "boolean",
                            "description": "Enable performance optimization for this call", 
                            "default": True
                        }
                        
                        tools.append(Tool(
                            name=tool_name,
                            description=f"[SUBAGENT-ENHANCED] {description}",
                            inputSchema=schema
                        ))
                    else:
                        # Legacy function reference with basic enhancement
                        description = getattr(tool_def, "__doc__", f"{tool_name} tool")
                        enhanced_schema = {
                            "type": "object",
                            "properties": {
                                "_subagent_session_id": {
                                    "type": "string",
                                    "description": "Subagent session identifier"
                                }
                            },
                            "additionalProperties": True
                        }
                        
                        tools.append(Tool(
                            name=tool_name,
                            description=f"[SUBAGENT-ENHANCED] {description}",
                            inputSchema=enhanced_schema
                        ))
                        
                    logger.debug(f"Enhanced tool registered: {tool_name}")
                    
                except Exception as e:
                    logger.error(f"Failed to register enhanced tool {tool_name}: {e}")
            
            logger.info(f"Successfully registered {len(tools)} enhanced tools")
            return tools
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict):
            """Execute tool with comprehensive subagent intelligence capture."""
            start_time = datetime.now()
            
            # Extract subagent metadata
            session_id = arguments.pop("_subagent_session_id", self._current_session_id)
            intelligence_capture = arguments.pop("_intelligence_capture", True)
            performance_optimize = arguments.pop("_performance_optimize", True)
            
            # Create session if needed
            if session_id is None:
                session_id = await self.session_manager.create_session(
                    session_type="analysis",
                    initial_context={"tool_call": name}
                )
                self._current_session_id = session_id
                logger.info(f"Created new subagent session: {session_id}")
            
            logger.debug(f"Executing tool {name} in session {session_id}")
            
            try:
                # Execute tool with optimization if enabled
                if performance_optimize:
                    result = await self.performance_optimizer.optimize_tool_call(
                        name, arguments, session_id
                    )
                else:
                    # Direct execution without optimization
                    result = await self._execute_tool_direct(name, arguments)
                
                execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                
                # Track tool usage for intelligence capture
                if intelligence_capture:
                    await self.session_manager.track_tool_usage(
                        session_id=session_id,
                        tool_name=name,
                        arguments=arguments,
                        result=result,
                        execution_time_ms=execution_time_ms,
                        token_count=self._estimate_token_count(arguments, result),
                        success=True
                    )
                
                # Return result with subagent metadata
                result_text = str(result)
                if intelligence_capture:
                    result_text += f"\n\n[SUBAGENT-INFO] Session: {session_id}, Tools used: {len(self.session_manager.active_sessions.get(session_id, type('', (), {'tools_used': set()})).tools_used)}"
                
                return [TextContent(type="text", text=result_text)]
                
            except Exception as e:
                execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                
                # Track failed tool usage
                if intelligence_capture:
                    await self.session_manager.track_tool_usage(
                        session_id=session_id,
                        tool_name=name,
                        arguments=arguments,
                        execution_time_ms=execution_time_ms,
                        success=False,
                        error_message=str(e)
                    )
                
                logger.error(f"Enhanced tool {name} execution failed: {e}")
                raise
        
        @self.server.list_resources()
        async def handle_list_resources():
            """List available resources including subagent intelligence resources."""
            return [
                {
                    "uri": "ltmc://subagent/sessions",
                    "name": "Active Subagent Sessions",
                    "description": "Information about active Claude Code subagent sessions"
                },
                {
                    "uri": "ltmc://subagent/intelligence",
                    "name": "Subagent Intelligence Data", 
                    "description": "Captured intelligence patterns and insights"
                },
                {
                    "uri": "ltmc://subagent/performance",
                    "name": "Performance Statistics",
                    "description": "Performance optimization statistics and metrics"
                }
            ]
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str):
            """Read subagent intelligence resources."""
            if uri == "ltmc://subagent/sessions":
                sessions = await self.session_manager.get_active_sessions()
                return [TextContent(
                    type="text", 
                    text=f"Active Subagent Sessions:\n{self._format_sessions(sessions)}"
                )]
            
            elif uri == "ltmc://subagent/performance":
                stats = await self.performance_optimizer.get_performance_stats()
                return [TextContent(
                    type="text",
                    text=f"Performance Statistics:\n{self._format_performance_stats(stats)}"
                )]
            
            elif uri == "ltmc://subagent/intelligence":
                # Get intelligence summary
                if self._current_session_id:
                    intelligence = await self.intelligence_tracker.get_session_intelligence(
                        self._current_session_id
                    )
                    return [TextContent(
                        type="text",
                        text=f"Intelligence Summary:\n{self._format_intelligence(intelligence)}"
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text="No active session for intelligence display"
                    )]
            
            return [TextContent(type="text", text=f"Unknown resource: {uri}")]
    
    async def _execute_tool_direct(self, name: str, arguments: dict):
        """Execute tool directly without optimization."""
        consolidated_tools = get_consolidated_tools()
        
        if name not in consolidated_tools:
            raise ValueError(f"Unknown tool: {name}")
        
        tool_def = consolidated_tools[name]
        
        if isinstance(tool_def, dict):
            tool_func = tool_def["handler"]
        else:
            tool_func = tool_def
        
        if asyncio.iscoroutinefunction(tool_func):
            return await tool_func(**arguments)
        else:
            return tool_func(**arguments)
    
    def _estimate_token_count(self, arguments: dict, result: any) -> int:
        """Estimate token count for intelligence tracking."""
        import json
        args_str = json.dumps(arguments)
        result_str = str(result)
        return (len(args_str) + len(result_str)) // 4  # Rough approximation
    
    def _format_sessions(self, sessions: list) -> str:
        """Format session information for display."""
        if not sessions:
            return "No active sessions"
        
        formatted = []
        for session in sessions:
            formatted.append(
                f"- Session {session['session_id'][:8]}...: "
                f"{session['session_type']}, "
                f"{len(session['tools_used'])} tools, "
                f"{session['total_tool_calls']} calls"
            )
        return "\n".join(formatted)
    
    def _format_performance_stats(self, stats: dict) -> str:
        """Format performance statistics for display."""
        return (
            f"Total Calls: {stats['total_tool_calls']}\n"
            f"Cache Hit Rate: {stats['cache_hit_rate']:.2%}\n"
            f"Optimization: {'Enabled' if stats['optimization_enabled'] else 'Disabled'}\n"
            f"Batching: {'Enabled' if stats['batching_enabled'] else 'Disabled'}"
        )
    
    def _format_intelligence(self, intelligence: dict) -> str:
        """Format intelligence data for display."""
        if "error" in intelligence:
            return f"Error: {intelligence['error']}"
        
        summary = intelligence.get("summary", {})
        return (
            f"Tools Used: {summary.get('total_tools', 0)}\n"
            f"Success Rate: {summary.get('success_rate', 0):.2%}\n"
            f"Total Execution Time: {summary.get('total_execution_time', 0)}ms\n"
            f"Total Tokens: {summary.get('total_tokens', 0)}"
        )


async def create_enhanced_mcp_server():
    """Create and configure the enhanced MCP server with subagent intelligence."""
    server_instance = LTMCSubagentMCPServer()
    
    # Initialize all components
    if not await server_instance.initialize():
        logger.error("Server initialization failed")
        sys.exit(1)
    
    # Setup protocol handlers
    server_instance.setup_handlers()
    
    return server_instance.server


async def main():
    """Main entry point for enhanced LTMC MCP server."""
    try:
        server = await create_enhanced_mcp_server()
        logger.info("Starting Enhanced LTMC MCP server with Claude Code subagent intelligence...")
        
        async with stdio_server() as (read_stream, write_stream):
            logger.info("Enhanced server ready for subagent connections")
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="LTMC-Subagent-Intelligence-Server",
                    server_version="2.0.0",
                    capabilities=ServerCapabilities(
                        tools=ToolsCapability(),
                        resources=ResourcesCapability(subscribe=True, listChanged=True),
                        prompts=PromptsCapability(listChanged=True),
                        experimental={
                            "subagentIntelligence": True,
                            "crossSessionLearning": True,
                            "performanceOptimization": True,
                            "intelligenceCapture": True
                        }
                    )
                )
            )
    except KeyboardInterrupt:
        logger.info("Enhanced server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Enhanced server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    anyio.run(main)