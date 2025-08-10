#!/usr/bin/env python3
"""
LTMC FastMCP Server - Main Entry Point
====================================

Main server implementation following FastMCP 2.0 official patterns.
Modular architecture with tool modules ≤300 lines each.

Based on official MCP SDK documentation:
- Source: Official Python MCP SDK
- Pattern: from mcp.server.fastmcp import FastMCP + @mcp.tool decorators
- Transport: Automatic stdio/HTTP handling via mcp.run()
"""

import asyncio
import sys
from pathlib import Path

# Fix for "RuntimeError: Already running asyncio in this thread"
# Based on 2025 research: use nest-asyncio for event loop nesting
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    # Install nest-asyncio if not available
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "nest-asyncio"])
    import nest_asyncio
    nest_asyncio.apply()

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Official MCP SDK import pattern (from research findings)
from mcp.server.fastmcp import FastMCP

# Local imports
from config.settings import LTMCSettings
from config.database_config import DatabaseManager
from services.database_service import DatabaseService
from utils.logging_utils import setup_logging

# Tool registration imports - Using unified module approach
from tools import (
    register_memory_tools,
    register_chat_tools,
    register_todo_tools,
    register_context_tools,
    register_code_pattern_tools,
    register_redis_tools,
    register_advanced_tools,
    register_taskmaster_tools,
    register_blueprint_tools,
    register_documentation_tools,
    register_unified_tools
)


# Global server instance for MCP Inspector
mcp = None

async def create_server() -> FastMCP:
    """
    Create and configure LTMC MCP server.
    
    Following official FastMCP pattern:
    mcp = FastMCP("Demo 🚀")
    
    Returns:
        FastMCP: Configured server instance
    """
    global mcp
    
    # Load settings
    settings = LTMCSettings()
    
    # Setup logging
    setup_logging(settings.log_level)
    
    # Initialize FastMCP server using official MCP SDK pattern
    # Based on 2025 official examples: FastMCP only accepts name parameter
    mcp = FastMCP("ltmc")
    
    # Initialize database connections
    db_manager = DatabaseManager(settings)
    await db_manager.initialize_all_databases()
    
    # Initialize core services
    db_service = DatabaseService(settings)
    await db_service.initialize()
    
    # Register all tool modules following modular architecture
    print("🔧 Registering LTMC tool modules...")
    
    # Core LTMC tools
    register_memory_tools(mcp, settings)
    register_chat_tools(mcp, settings) 
    register_todo_tools(mcp, settings)
    
    # Context and pattern tools
    register_context_tools(mcp, settings)
    register_code_pattern_tools(mcp, settings)
    
    # Database and caching tools
    register_redis_tools(mcp, settings)
    register_advanced_tools(mcp, settings)
    
    # Task and blueprint tools
    register_taskmaster_tools(mcp, settings)
    register_blueprint_tools(mcp, settings)
    
    # Documentation and system tools
    register_documentation_tools(mcp, settings)
    register_unified_tools(mcp, settings)
    
    print("✅ All tool modules registered successfully")
    
    return mcp


async def main():
    """
    Main entry point following official FastMCP pattern.
    
    Official pattern from 2025 research:
    For async contexts, use run_async() instead of run():
        server = await create_server()
        await server.run_async()  # CORRECT for async contexts
    """
    try:
        # Create server with all tool registrations
        server = await create_server()
        
        # Use run_stdio_async() for async contexts (FIXED - actual FastMCP API)
        # This prevents "RuntimeError: Already running asyncio in this thread"
        await server.run_stdio_async()
        
    except KeyboardInterrupt:
        print("\n🛑 LTMC server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start LTMC server: {e}")
        raise


if __name__ == "__main__":
    # Official MCP SDK entry point pattern with nest-asyncio fix
    asyncio.run(main())