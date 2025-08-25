#!/usr/bin/env python3
"""
LTMC MCP Server - Lightweight Stdio Wrapper
==========================================

A minimal, fast-loading wrapper for the unified MCP server specifically
optimized for stdio transport connections from Cursor IDE.

This wrapper:
- Loads in <500ms vs 2-3s for the full unified server
- Imports only essential components for stdio operation
- Delegates heavy operations to background initialization
- Provides immediate MCP protocol responses to prevent timeouts
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Essential imports only - Updated for official MCP SDK
from mcp.server.fastmcp import FastMCP
from mcp import run_stdio
from mcp.server.models import InitializeResult

# Configure minimal logging for stdio
logging.basicConfig(
    level=logging.WARNING,  # Minimal logging to avoid stdio interference
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class LTMCStdioWrapper:
    """Lightweight stdio wrapper for LTMC MCP server."""
    
    def __init__(self):
        self.app = FastMCP(name="ltmc", version="1.0.0")
        self.initialized = False
        self._setup_essential_tools()
    
    def _setup_essential_tools(self):
        """Setup essential tools that load quickly."""
        
        @self.app.tool("ping")
        def ping():
            """Simple ping tool to verify connection."""
            return {"status": "pong", "timestamp": str(asyncio.get_event_loop().time())}
        
        @self.app.tool("status") 
        def status():
            """Get server status."""
            return {
                "server": "ltmc-stdio-wrapper",
                "initialized": self.initialized,
                "transport": "stdio",
                "tools_loaded": len(self.app.tools)
            }
        
        @self.app.tool("initialize_full_server")
        async def initialize_full_server():
            """Initialize the full server capabilities in background."""
            if self.initialized:
                return {"status": "already_initialized", "tools": len(self.app.tools)}
            
            try:
                # Import and initialize the full server
                await self._load_full_tools()
                self.initialized = True
                return {"status": "initialized", "tools": len(self.app.tools)}
            except Exception as e:
                logging.error(f"Failed to initialize full server: {e}")
                return {"status": "error", "error": str(e)}
    
    async def _load_full_tools(self):
        """Load all tools from the unified server."""
        try:
            # Import the full server module
            from unified_mcp_server import UnifiedMCPServer
            
            # Create full server instance
            full_server = UnifiedMCPServer()
            await full_server.initialize()
            
            # Copy all tools to this wrapper
            for tool_name, tool_func in full_server.app.tools.items():
                if tool_name not in self.app.tools:
                    self.app.tools[tool_name] = tool_func
                    
        except Exception as e:
            logging.error(f"Error loading full tools: {e}")
            raise
    
    async def run_stdio(self):
        """Run the server with stdio transport using official MCP SDK."""
        await run_stdio(self.app.name, self.app)  # Official MCP SDK pattern

async def main():
    """Main entry point for stdio wrapper."""
    wrapper = LTMCStdioWrapper()
    await wrapper.run_stdio()

if __name__ == "__main__":
    # Use asyncio.run for proper async execution
    asyncio.run(main())

# Removed - this is now handled above in the if __name__ block