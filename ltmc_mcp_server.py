#!/usr/bin/env python3
"""LTMC MCP Server - Entry point supporting both stdio and HTTP transport."""

import sys
import os
import logging
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_logging(transport_type: str):
    """Setup logging appropriate for transport type."""
    if transport_type == 'stdio':
        # For stdio transport, only use stderr to avoid interfering with MCP protocol
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            stream=sys.stderr,
            force=True
        )
    else:
        # For HTTP transport, normal logging is fine
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            force=True
        )

def main():
    parser = argparse.ArgumentParser(description='LTMC MCP Server')
    parser.add_argument(
        '--transport', 
        choices=['stdio', 'http'], 
        default='stdio',
        help='Transport protocol to use (default: stdio)'
    )
    parser.add_argument(
        '--host', 
        default='127.0.0.1',
        help='Host to bind to for HTTP transport (default: 127.0.0.1)'
    )
    parser.add_argument(
        '--port', 
        type=int, 
        default=5050,
        help='Port to bind to for HTTP transport (default: 5050)'
    )
    
    args = parser.parse_args()
    
    # Setup appropriate logging
    setup_logging(args.transport)
    logger = logging.getLogger(__name__)
    
    # Set environment variables for HTTP transport
    if args.transport == 'http':
        os.environ['FASTMCP_HOST'] = args.host
        os.environ['FASTMCP_PORT'] = str(args.port)
        
        print(f"Starting LTMC MCP Server with HTTP transport")
        print(f"Database: {os.getenv('DB_PATH', 'ltmc.db')}")
        print(f"FAISS Index: {os.getenv('FAISS_INDEX_PATH', 'faiss_index')}")
        print(f"Server will be available at http://{args.host}:{args.port}")
        print("Press Ctrl+C to stop the server")
    else:
        logger.info("Starting LTMC MCP Server with stdio transport")
    
    # Import and run the MCP server
    from ltms.mcp_server import mcp
    
    try:
        mcp.run(transport=args.transport)
    except KeyboardInterrupt:
        logger.info(f"LTMC MCP Server ({args.transport}) stopped by user")
    except Exception as e:
        logger.error(f"Error running LTMC MCP Server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()