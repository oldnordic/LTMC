#!/usr/bin/env python3
"""
Minimal LTMC Test Server for Claude Code Connection Testing
==========================================================

Bypasses lazy loading to test core MCP connectivity.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Official MCP SDK import
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)

logger = logging.getLogger(__name__)

# Create server
mcp = FastMCP("ltmc-test")

@mcp.tool()
async def ping() -> str:
    """Test connectivity with Claude Code."""
    logger.info("✅ Ping tool called - connection working!")
    return "🎯 LTMC Test Server - Connection successful!"

@mcp.tool() 
async def test_connection() -> dict:
    """Test basic MCP protocol functionality."""
    logger.info("✅ Test connection tool called")
    return {
        "status": "connected",
        "server": "ltmc-test",
        "protocol": "MCP JSON-RPC 2.0",
        "transport": "stdio",
        "message": "✅ LTMC binary successfully connected to Claude Code!"
    }

async def main():
    """Main entry point."""
    try:
        logger.info("🚀 Starting LTMC Test Server")
        logger.info("📡 Testing connection to Claude Code via stdio transport")
        
        # Check for existing event loop
        try:
            loop = asyncio.get_running_loop()
            logger.info("✅ Using existing asyncio event loop")
        except RuntimeError:
            logger.info("✅ Creating new asyncio event loop")
        
        # Run with asyncio compatibility
        await mcp.run_stdio_async()
        
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        raise

def sync_main():
    """Synchronous entry point."""
    try:
        # Check if there's already an event loop running
        loop = asyncio.get_running_loop()
        logger.warning("⚠️  Running inside existing event loop")
        task = loop.create_task(main())
        return task
    except RuntimeError:
        # No event loop running, create one
        logger.info("✅ No existing event loop, creating new one")
        return asyncio.run(main())

if __name__ == "__main__":
    sync_main()