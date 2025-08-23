#!/usr/bin/env python3
"""
Minimal Official MCP SDK Test Server
====================================

Test server using official MCP Python SDK to validate Claude Code connectivity.
This will prove our hypothesis that the official SDK works while jlowin's FastMCP doesn't.
"""

import asyncio
import logging
from pathlib import Path

# Official MCP SDK import (CORRECT)
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create official MCP SDK server
mcp = FastMCP("ltmc-test")

@mcp.tool()
def ping() -> str:
    """Test connectivity with Claude Code MCP client."""
    return "pong - Official MCP SDK working!"

@mcp.tool()
def test_basic_functionality() -> str:
    """Test basic tool functionality."""
    return "Official MCP SDK test tool responding correctly"

@mcp.tool()
def get_server_info() -> dict:
    """Get server information to validate connection."""
    return {
        "server_name": "ltmc-test", 
        "implementation": "Official MCP Python SDK",
        "status": "connected",
        "message": "This confirms official SDK works with Claude Code"
    }

def main():
    """
    Main entry point using official MCP SDK pattern.
    """
    try:
        logger.info("🧪 Starting Official MCP SDK Test Server...")
        logger.info("📡 Server: ltmc-test")
        logger.info("🔧 Implementation: Official MCP Python SDK")
        logger.info("🎯 Purpose: Validate Claude Code connectivity")
        
        # Run with stdio transport (official pattern)
        mcp.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Test server stopped by user")
    except Exception as e:
        logger.error(f"❌ Test server failed: {e}")
        raise

if __name__ == "__main__":
    main()