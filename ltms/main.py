#!/usr/bin/env python3
"""
LTMC MCP Server - Main Entry Point

Production-ready MCP server using consolidated tools with real
database operations. Follows standard Model Context Protocol with
stdio transport. No stubs, no mocks, no placeholders - all tools perform
real functionality.
"""

# Standard library imports
import sys
import os
import logging
import asyncio
from pathlib import Path

# Third-party imports
import anyio
from mcp.server.lowlevel.server import Server as MCPServer
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
from mcp.types import ServerCapabilities, Tool, TextContent, ToolsCapability

# Local application imports
from ltms.tools.common.tool_registry import get_consolidated_tools
from ltms.database.schema import create_tables
from ltms.database.neo4j_store import get_neo4j_graph_store, Neo4jGraphStore

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


def initialize_database():
    """Initialize database with proper schema."""
    try:
        import sqlite3
        from ltms.config import get_config
        
        # Get database path from config
        config = get_config()
        db_path = config.get_db_path()
        
        # Create connection and initialize tables
        with sqlite3.connect(db_path) as conn:
            create_tables(conn)
        
        logger.info(f"Database initialized successfully at {db_path}")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


async def initialize_graph_store():
    """Initialize Neo4j graph store for enhanced relationship management."""
    try:
        neo4j_store = await get_neo4j_graph_store()
        if neo4j_store and neo4j_store.driver:
            # Test the connection
            try:
                with neo4j_store.driver.session() as session:
                    session.run("RETURN 1")
                logger.info("Neo4j graph store initialized and healthy - enhanced relationship features available")
                return True
            except Exception as e:
                logger.warning(f"Neo4j store initialized but health check failed: {e}")
                logger.info("Will use SQLite fallback for relationship management")
                return False
        else:
            logger.info("Neo4j initialization skipped - using SQLite-only relationship management")
            return False
    except Exception as e:
        logger.error(f"Graph store initialization failed: {e}")
        logger.info("Will use SQLite fallback for relationship management")
        return False


async def create_mcp_server():
    """Create and configure the MCP server with consolidated tools."""
    # Initialize database and exit if initialization fails
    if not initialize_database():
        sys.exit(1)
    
    # Initialize Neo4j graph store (non-blocking - failures allow SQLite fallback)
    graph_available = await initialize_graph_store()
    if graph_available:
        logger.info("LTMC Server starting with Neo4j + SQLite dual backend")
    else:
        logger.info("LTMC Server starting with SQLite-only backend")

    # Create MCP server instance with capabilities
    server = MCPServer("LTMC Server")

    @server.list_tools()
    async def handle_list_tools():
        """List all available tools with proper MCP schemas."""
        tools = []
        consolidated_tools = get_consolidated_tools()
        logger.info(f"Listing {len(consolidated_tools)} available tools")
        for tool_name, tool_def in consolidated_tools.items():
            try:
                if isinstance(tool_def, dict):
                    # Structured tool definition with schema and handler
                    description = tool_def.get("description", f"{tool_name} tool")
                    schema = tool_def.get("schema", {"type": "object", "properties": {}})
                    tools.append(Tool(
                        name=tool_name,
                        description=description,
                        inputSchema=schema
                    ))
                else:
                    # Legacy function reference - use docstring and basic schema
                    description = getattr(tool_def, "__doc__", f"{tool_name} tool")
                    tools.append(Tool(
                        name=tool_name,
                        description=description,
                        inputSchema={"type": "object", "properties": {}}
                    ))
                logger.debug(f"Added tool: {tool_name}")
            except Exception as e:
                logger.error(f"Failed to register tool {tool_name}: {e}")
        logger.info(f"Successfully registered {len(tools)} tools")
        return tools

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict):
        """Execute a tool by name with proper error handling."""
        # DEBUG: Log tool calls for sync_documentation_with_code
        if name == "sync_documentation_with_code":
            print(f"DEBUG handle_call_tool: name={name}, arguments={arguments}")
            for key, value in arguments.items():
                print(f"DEBUG   {key}={value} (type={type(value)})")
        
        consolidated_tools = get_consolidated_tools()
        if name not in consolidated_tools:
            raise ValueError(f"Unknown tool: {name}")

        try:
            tool_def = consolidated_tools[name]
            
            if isinstance(tool_def, dict):
                # Structured tool definition - call handler
                tool_func = tool_def["handler"]
            else:
                # Legacy function reference
                tool_func = tool_def
            
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**arguments)
            else:
                result = tool_func(**arguments)
                
            return [TextContent(
                type="text",
                text=str(result)
            )]
        except Exception as e:
            logger.error(f"Tool {name} execution failed: {e}")
            raise

    @server.list_resources()
    async def handle_list_resources():
        """List available resources (required for MCP protocol)."""
        return []

    return server


async def main():
    """Main entry point for LTMC MCP server."""
    try:
        server = await create_mcp_server()
        logger.info("Starting LTMC MCP server with stdio transport...")
        
        async with stdio_server() as (read_stream, write_stream):
            logger.info("Server ready for MCP connections")
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="LTMC Server",
                    server_version="1.0.0",
                    capabilities=ServerCapabilities(
                        tools=ToolsCapability()
                    )
                )
            )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    anyio.run(main)