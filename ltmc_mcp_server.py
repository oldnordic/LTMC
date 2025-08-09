#!/usr/bin/env python3
"""LTMC MCP Server entry point for MCP dev tool."""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup stderr-only logging for stdio transport compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr,  # CRITICAL: Only stderr for stdio transport
    force=True
)
logger = logging.getLogger(__name__)

# Import and run the MCP server (main server with all tools)
from ltms.mcp_server import mcp

if __name__ == "__main__":
    # Run the MCP server with stdio transport
    try:
        logger.info("Starting LTMC MCP Server with stdio transport")
        mcp.run(transport='stdio')
    except KeyboardInterrupt:
        logger.info("LTMC MCP Server stdio transport stopped by user")
    except Exception as e:
        logger.error(f"Error running LTMC MCP Server: {e}")
        sys.exit(1)
