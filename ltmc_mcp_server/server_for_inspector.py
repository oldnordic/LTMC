#!/usr/bin/env python3
"""
LTMC FastMCP Server - MCP Inspector Compatible
============================================

Simplified server for MCP Inspector testing.
Following exact FastMCP patterns from research.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Official MCP SDK import - from research findings
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server using exact research pattern
# From research: mcp = FastMCP("Demo")
mcp = FastMCP("ltmc")

# Simple test tools following exact research patterns
@mcp.tool()
def ping() -> dict:
    """Simple ping tool to test FastMCP functionality."""
    return {"status": "pong", "message": "LTMC server is responding"}

@mcp.tool()
def store_memory(content: str, file_name: str) -> dict:
    """Store content in memory (test version)."""
    return {
        "success": True,
        "message": f"Stored '{file_name}' with content length {len(content)}",
        "resource_id": 1
    }

@mcp.tool()
def list_todos(limit: int = 10) -> dict:
    """List todos (test version)."""
    return {
        "success": True,
        "todos": [
            {"id": 1, "title": "Test todo 1", "status": "pending"},
            {"id": 2, "title": "Test todo 2", "status": "completed"}
        ],
        "total_count": 2
    }

@mcp.tool()
def log_chat(content: str, conversation_id: str, role: str) -> dict:
    """Log chat message (test version)."""
    return {
        "success": True,
        "message_id": 1,
        "conversation_id": conversation_id,
        "message": "Chat logged successfully"
    }

# Entry point following official pattern
if __name__ == "__main__":
    # Official FastMCP entry point pattern from research
    mcp.run()