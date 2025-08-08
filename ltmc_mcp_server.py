#!/usr/bin/env python3
"""LTMC MCP Server entry point for MCP dev tool."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the MCP server (main server with all tools)
from ltms.mcp_server import mcp

if __name__ == "__main__":
    # Run the MCP server with stdio transport
    mcp.run(transport='stdio')
