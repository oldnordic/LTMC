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
from mcp.server.lowlevel import NotificationOptions
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent

# Local application imports - Migration to modular imports
from ltms.tools.common.tool_registry import get_consolidated_tools
from ltms.database.schema import create_tables
from ltms.database.neo4j_store import get_neo4j_graph_store, Neo4jGraphStore

# Configure logging to both stderr and file for debugging MCP connection issues
log_file = Path(os.environ.get('LTMC_DATA_DIR', '.')) / 'ltmc_server.log'
logging.basicConfig(
    level=logging.DEBUG,  # Increased to DEBUG level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),  # Required for stdio MCP transport
        logging.FileHandler(log_file, mode='a')  # Additional file logging for debugging
    ]
)
logger = logging.getLogger(__name__)

# Log startup attempt
logger.info("=" * 60)
logger.info("LTMC MCP SERVER STARTUP ATTEMPT")
logger.info(f"Python version: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"LTMC_DATA_DIR: {os.environ.get('LTMC_DATA_DIR', 'NOT SET')}")
logger.info(f"Log file: {log_file}")
logger.info("=" * 60)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Change to project root for consistent database paths
os.chdir(str(project_root))


def initialize_database():
    """Initialize database with proper schema."""
    try:
        logger.debug("Starting database initialization...")
        import sqlite3
        from ltms.config.json_config_loader import get_config
        
        # Get database path from config
        logger.debug("Loading LTMC configuration...")
        config = get_config()
        db_path = config.get_db_path()
        logger.debug(f"Database path resolved to: {db_path}")
        
        # Ensure parent directory exists
        db_parent = Path(db_path).parent
        if not db_parent.exists():
            logger.debug(f"Creating database directory: {db_parent}")
            db_parent.mkdir(parents=True, exist_ok=True)
        
        # Create connection and initialize tables
        logger.debug("Connecting to SQLite database...")
        with sqlite3.connect(db_path) as conn:
            logger.debug("Creating database tables...")
            create_tables(conn)
        
        logger.info(f"✅ Database initialized successfully at {db_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


async def initialize_graph_store():
    """Initialize Neo4j graph store for enhanced relationship management."""
    try:
        logger.debug("Starting Neo4j graph store initialization...")
        neo4j_store = await get_neo4j_graph_store()
        
        if neo4j_store and neo4j_store.driver:
            logger.debug("Neo4j graph store created, testing connection...")
            # Test the connection
            try:
                with neo4j_store.driver.session() as session:
                    session.run("RETURN 1")
                logger.info("✅ Neo4j graph store initialized and healthy - enhanced relationship features available")
                return True
            except Exception as e:
                logger.warning(f"⚠️  Neo4j store initialized but health check failed: {e}")
                logger.info("Will use SQLite fallback for relationship management")
                return False
        else:
            logger.info("ℹ️  Neo4j initialization skipped - using SQLite-only relationship management")
            return False
    except Exception as e:
        logger.error(f"❌ Graph store initialization failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.info("Will use SQLite fallback for relationship management")
        return False


async def create_mcp_server():
    """Create and configure the MCP server with consolidated tools."""
    logger.debug("Starting MCP server creation...")
    
    # Initialize database and exit if initialization fails
    logger.debug("Initializing database...")
    if not initialize_database():
        logger.error("Database initialization failed - cannot continue")
        sys.exit(1)
    
    # Initialize Neo4j graph store (non-blocking - failures allow SQLite fallback)
    logger.debug("Initializing Neo4j graph store...")
    graph_available = await initialize_graph_store()
    if graph_available:
        logger.info("🚀 LTMC Server starting with Neo4j + SQLite dual backend")
    else:
        logger.info("🚀 LTMC Server starting with SQLite-only backend")

    # Create MCP server instance with capabilities
    logger.debug("Creating MCP server instance...")
    server = MCPServer("LTMC Server")
    logger.debug(f"✅ MCP server instance created: {type(server)}")

    @server.list_tools()
    async def handle_list_tools():
        """List all available tools with proper MCP schemas."""
        logger.debug("🔧 handle_list_tools() called")
        tools = []
        
        try:
            logger.debug("Getting consolidated tools from registry...")
            consolidated_tools = get_consolidated_tools()
            logger.info(f"📋 Listing {len(consolidated_tools)} available tools")
            
            for tool_name, tool_def in consolidated_tools.items():
                try:
                    logger.debug(f"Processing tool: {tool_name}")
                    if isinstance(tool_def, dict):
                        # Structured tool definition with schema and handler
                        description = tool_def.get("description", f"{tool_name} tool")
                        schema = tool_def.get("schema", {"type": "object", "properties": {}})
                        tool_obj = Tool(
                            name=tool_name,
                            description=description,
                            inputSchema=schema
                        )
                        tools.append(tool_obj)
                        logger.debug(f"✅ Added structured tool: {tool_name}")
                    else:
                        # Legacy function reference - use docstring and basic schema
                        description = getattr(tool_def, "__doc__", f"{tool_name} tool")
                        tool_obj = Tool(
                            name=tool_name,
                            description=description,
                            inputSchema={"type": "object", "properties": {}}
                        )
                        tools.append(tool_obj)
                        logger.debug(f"✅ Added legacy tool: {tool_name}")
                        
                except Exception as e:
                    logger.error(f"❌ Failed to register tool {tool_name}: {e}")
                    logger.error(f"Tool definition: {tool_def}")
                    
            logger.info(f"🎯 Successfully registered {len(tools)} tools")
            logger.debug(f"Tool names: {[t.name for t in tools]}")
            return tools
            
        except Exception as e:
            logger.error(f"❌ handle_list_tools() failed completely: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

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
        logger.info("🚀 Starting LTMC MCP server main()...")
        
        logger.debug("Creating MCP server...")
        server = await create_mcp_server()
        logger.info("✅ MCP server created successfully")
        
        logger.info("🔌 Starting LTMC MCP server with stdio transport...")
        
        async with stdio_server() as (read_stream, write_stream):
            logger.info("📡 Server ready for MCP connections")
            logger.debug("Setting up server initialization options...")
            
            init_options = InitializationOptions(
                server_name="LTMC Server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
            logger.debug(f"Initialization options: {init_options}")
            
            logger.info("🎯 Starting server.run() - waiting for MCP client connections...")
            await server.run(read_stream, write_stream, init_options)
            
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user (KeyboardInterrupt)")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Server error in main(): {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        sys.exit(1)
    finally:
        logger.info("🏁 LTMC MCP server main() complete")


if __name__ == "__main__":
    anyio.run(main)