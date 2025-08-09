#!/usr/bin/env python3
"""Unified HTTP transport using the same FastMCP server as stdio."""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup stderr logging for consistency
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr,
    force=True
)
logger = logging.getLogger(__name__)

# Import the SAME FastMCP server used by stdio transport
from ltms.mcp_server import mcp

if __name__ == "__main__":
    try:
        logger.info("Starting LTMC MCP Server with HTTP transport (unified)")
        # Use HTTP transport instead of stdio, but SAME tools
        mcp.run(transport='http')
    except KeyboardInterrupt:
        logger.info("LTMC MCP Server HTTP transport stopped by user")
    except Exception as e:
        logger.error(f"Error running LTMC MCP Server HTTP: {e}")
        sys.exit(1)