#!/usr/bin/env python3
"""LTMC MCP Server HTTP entry point using native FastMCP HTTP transport."""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Change to project root for consistent behavior
os.chdir(str(project_root))

# Import and run the MCP server (main server with all tools)
from ltms.mcp_server import mcp

if __name__ == "__main__":
    # Set FastMCP HTTP transport configuration
    os.environ['FASTMCP_HOST'] = os.getenv('FASTMCP_HOST', '127.0.0.1')
    os.environ['FASTMCP_PORT'] = os.getenv('FASTMCP_PORT', '5050')
    
    host = os.environ['FASTMCP_HOST']
    port = os.environ['FASTMCP_PORT']
    
    # Run the MCP server with native FastMCP HTTP transport
    print("Starting LTMC MCP Server with native FastMCP HTTP transport")
    print(f"Database: {os.getenv('DB_PATH', 'ltmc.db')}")
    print(f"FAISS Index: {os.getenv('FAISS_INDEX_PATH', 'faiss_index')}")
    print(f"HTTP Server will be available on http://{host}:{port}")
    print("Press Ctrl+C to stop the server")
    
    mcp.run(transport='streamable-http')