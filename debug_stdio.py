#!/usr/bin/env python3
"""Debug version of stdio transport to understand the issue."""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Change to project root for consistent behavior
os.chdir(str(project_root))

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),  # Log to stderr so stdout is clean for MCP
        logging.FileHandler('/tmp/ltmc_stdio_debug.log')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Debug main function."""
    try:
        logger.info("Starting LTMC MCP Server stdio transport debug...")
        
        # Import and run the MCP server
        from ltms.mcp_server import mcp
        
        logger.info("MCP server instance created successfully")
        logger.info(f"Available tools: {len(mcp._tools)}")
        
        # List the tools for debugging
        for tool_name in mcp._tools.keys():
            logger.info(f"Tool available: {tool_name}")
        
        logger.info("Attempting to run stdio transport...")
        
        # Run the MCP server with stdio transport
        mcp.run(transport='stdio')
        
        logger.info("MCP server stdio transport completed")
        
    except KeyboardInterrupt:
        logger.info("LTMC MCP Server stdio transport stopped by user")
    except Exception as e:
        logger.error(f"Error running LTMC MCP Server: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()