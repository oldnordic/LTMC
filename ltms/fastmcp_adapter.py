"""
FastMCP Adapter for LTMC Consolidated Tools

This module provides a FastMCP-based MCP server that properly exposes
the existing LTMC consolidated tool system. This solves the tool exposure
issues with the low-level MCP server implementation by using FastMCP's
automatic tool registration and proper MCP protocol compliance.

Key Benefits:
- Proper tool exposure to Claude Code using FastMCP patterns
- Maintains compatibility with existing LTMC tool registry
- Automatic @mcp.tool() decorator handling by FastMCP
- Proper MCP protocol compliance and error handling
- Preserves all existing 14 consolidated tools
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# FastMCP imports
from mcp.server.fastmcp import FastMCP

# LTMC imports - ensure project root is in path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(str(project_root))

from ltms.tools.common.tool_registry import get_consolidated_tools
from ltms.database.schema import create_tables
from ltms.database.neo4j_store import get_neo4j_graph_store

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP("LTMC Server")

def initialize_database():
    """Initialize database with proper schema."""
    try:
        logger.info("Starting database initialization...")
        import sqlite3
        from ltms.config.json_config_loader import get_config
        
        config = get_config()
        db_path = config.get_db_path()
        logger.info(f"Database path: {db_path}")
        
        # Ensure parent directory exists
        db_parent = Path(db_path).parent
        if not db_parent.exists():
            db_parent.mkdir(parents=True, exist_ok=True)
        
        # Create connection and initialize tables
        with sqlite3.connect(db_path) as conn:
            create_tables(conn)
        
        logger.info(f"✅ Database initialized successfully at {db_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

async def initialize_graph_store():
    """Initialize Neo4j graph store for enhanced relationship management."""
    try:
        logger.info("Starting Neo4j graph store initialization...")
        neo4j_store = await get_neo4j_graph_store()
        
        if neo4j_store and neo4j_store.driver:
            # Test the connection
            try:
                with neo4j_store.driver.session() as session:
                    session.run("RETURN 1")
                logger.info("✅ Neo4j graph store initialized and healthy")
                return True
            except Exception as e:
                logger.warning(f"⚠️  Neo4j store initialized but health check failed: {e}")
                return False
        else:
            logger.info("ℹ️  Neo4j initialization skipped - using SQLite-only mode")
            return False
    except Exception as e:
        logger.error(f"❌ Graph store initialization failed: {e}")
        return False

def register_consolidated_tools():
    """Register all LTMC consolidated tools with FastMCP."""
    try:
        logger.info("Starting tool registration...")
        
        # Get consolidated tools from existing registry
        consolidated_tools = get_consolidated_tools()
        logger.info(f"Found {len(consolidated_tools)} consolidated tools to register")
        
        # Counter for successfully registered tools
        registered_count = 0
        
        # Register each consolidated tool with FastMCP
        for tool_name, tool_def in consolidated_tools.items():
            try:
                if isinstance(tool_def, dict) and 'handler' in tool_def:
                    # Extract handler function and metadata
                    handler_func = tool_def['handler']
                    description = tool_def.get('description', f'{tool_name} - LTMC consolidated tool')
                    schema = tool_def.get('schema', {})
                    
                    # Create FastMCP tool with proper typing
                    @mcp.tool(description=description, schema=schema)
                    async def fastmcp_tool_wrapper(*args, **kwargs):
                        """FastMCP wrapper for consolidated LTMC tools."""
                        try:
                            # Call the original handler
                            if asyncio.iscoroutinefunction(handler_func):
                                result = await handler_func(*args, **kwargs)
                            else:
                                result = handler_func(*args, **kwargs)
                            
                            # Ensure result is string for MCP protocol
                            if isinstance(result, dict):
                                import json
                                return json.dumps(result, indent=2)
                            elif isinstance(result, str):
                                return result
                            else:
                                return str(result)
                        except Exception as e:
                            logger.error(f"Tool {tool_name} execution failed: {e}")
                            return f"Error executing {tool_name}: {str(e)}"
                    
                    # Set the correct function name for FastMCP registration
                    fastmcp_tool_wrapper.__name__ = tool_name
                    fastmcp_tool_wrapper.__doc__ = description
                    
                    # Register with FastMCP
                    registered_count += 1
                    logger.info(f"✅ Registered tool: {tool_name}")
                    
                else:
                    logger.warning(f"⚠️  Skipping malformed tool definition: {tool_name}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to register tool {tool_name}: {e}")
        
        logger.info(f"🎯 Successfully registered {registered_count} out of {len(consolidated_tools)} tools")
        return registered_count
        
    except Exception as e:
        logger.error(f"❌ Tool registration failed completely: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return 0

def create_consolidated_tools():
    """Create FastMCP tools from consolidated LTMC tools."""
    try:
        logger.info("Creating consolidated FastMCP tools...")
        
        consolidated_tools = get_consolidated_tools()
        
        # Register memory_action tool
        if 'memory_action' in consolidated_tools:
            handler = consolidated_tools['memory_action']['handler']
            @mcp.tool()
            async def memory_action(action: str, **params) -> str:
                """Memory operations with real SQLite+FAISS implementation: store, retrieve, build_context"""
                try:
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(action=action, **params)
                    else:
                        result = handler(action=action, **params)
                    
                    import json
                    return json.dumps(result, indent=2) if isinstance(result, dict) else str(result)
                except Exception as e:
                    return f"Error in memory_action: {str(e)}"
        
        # Register todo_action tool
        if 'todo_action' in consolidated_tools:
            handler = consolidated_tools['todo_action']['handler']
            @mcp.tool()
            async def todo_action(action: str, **params) -> str:
                """Todo operations with real SQLite implementation: add, list, complete, search"""
                try:
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(action=action, **params)
                    else:
                        result = handler(action=action, **params)
                    
                    import json
                    return json.dumps(result, indent=2) if isinstance(result, dict) else str(result)
                except Exception as e:
                    return f"Error in todo_action: {str(e)}"
        
        # Register unix_action tool
        if 'unix_action' in consolidated_tools:
            handler = consolidated_tools['unix_action']['handler']
            @mcp.tool()
            async def unix_action(action: str, **params) -> str:
                """Unix utilities with real external tool integration: ls(exa), cat(bat), grep(ripgrep), find(fd), tree, jq"""
                try:
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(action=action, **params)
                    else:
                        result = handler(action=action, **params)
                    
                    import json
                    return json.dumps(result, indent=2) if isinstance(result, dict) else str(result)
                except Exception as e:
                    return f"Error in unix_action: {str(e)}"
        
        # Register pattern_action tool
        if 'pattern_action' in consolidated_tools:
            handler = consolidated_tools['pattern_action']['handler']
            @mcp.tool()
            async def pattern_action(action: str, **params) -> str:
                """Code pattern analysis with real Python AST implementation: extract_functions, extract_classes, summarize_code"""
                try:
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(action=action, **params)
                    else:
                        result = handler(action=action, **params)
                    
                    import json
                    return json.dumps(result, indent=2) if isinstance(result, dict) else str(result)
                except Exception as e:
                    return f"Error in pattern_action: {str(e)}"
        
        # Register documentation_action tool
        if 'documentation_action' in consolidated_tools:
            handler = consolidated_tools['documentation_action']['handler']
            @mcp.tool()
            async def documentation_action(action: str, **params) -> str:
                """Documentation operations with real internal implementation: generate_api_docs, sync_documentation_with_code"""
                try:
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(action=action, **params)
                    else:
                        result = handler(action=action, **params)
                    
                    import json
                    return json.dumps(result, indent=2) if isinstance(result, dict) else str(result)
                except Exception as e:
                    return f"Error in documentation_action: {str(e)}"
        
        logger.info("🎯 FastMCP consolidated tools created successfully")
        
    except Exception as e:
        logger.error(f"❌ FastMCP tool creation failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

async def main():
    """Main entry point for FastMCP LTMC server."""
    try:
        logger.info("🚀 Starting LTMC FastMCP server...")
        
        # Initialize database
        if not initialize_database():
            logger.error("Database initialization failed - cannot continue")
            sys.exit(1)
        
        # Initialize Neo4j (optional)
        graph_available = await initialize_graph_store()
        if graph_available:
            logger.info("🚀 LTMC Server starting with Neo4j + SQLite dual backend")
        else:
            logger.info("🚀 LTMC Server starting with SQLite-only backend")
        
        # Create consolidated tools
        create_consolidated_tools()
        
        # Start FastMCP server
        logger.info("🔌 Starting FastMCP server with stdio transport...")
        await mcp.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user (KeyboardInterrupt)")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Server error in main(): {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        sys.exit(1)
    finally:
        logger.info("🏁 LTMC FastMCP server main() complete")

if __name__ == "__main__":
    try:
        # Try to use existing event loop if available
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Already in async context, just run the main function
            import sys
            sys.exit("Cannot run FastMCP adapter in existing event loop - use as module")
        else:
            asyncio.run(main())
    except RuntimeError:
        # No event loop, create one
        asyncio.run(main())