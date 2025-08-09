#!/usr/bin/env python3
"""LTMC MCP Server with STDIO response unwrapping for P1 standardization.

P1 Implementation: STDIO Response Format Standardization
- Converts MCP JSON-RPC wrapped responses to direct JSON tool results
- Maintains MCP protocol compliance while providing consistent client experience
- Enables transport parity between HTTP and STDIO formats
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Add project root to path  
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup stderr-only logging for stdio transport compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr,
    force=True
)
logger = logging.getLogger(__name__)

def unwrap_mcp_response(mcp_response_str: str) -> str:
    """Unwrap MCP JSON-RPC response to direct tool result.
    
    P1 Core Function: Converts MCP format to direct JSON for transport parity
    
    Handles FastMCP response structure:
    - MCP JSON-RPC wrapper: {"jsonrpc": "2.0", "id": X, "result": {...}}
    - FastMCP tool result: {"structuredContent": {"result": {...}}, ...}
    - Target output: Direct tool result JSON
    
    Args:
        mcp_response_str: MCP JSON-RPC formatted response string
        
    Returns:
        Direct JSON tool result string for consistent client consumption
    """
    try:
        mcp_data = json.loads(mcp_response_str)
        
        # Handle MCP JSON-RPC format
        if isinstance(mcp_data, dict) and "jsonrpc" in mcp_data:
            if "result" in mcp_data and mcp_data["result"] is not None:
                result = mcp_data["result"]
                
                # Handle FastMCP structured response format
                if isinstance(result, dict):
                    # Extract structured content if present (tool responses)
                    if "structuredContent" in result and "result" in result["structuredContent"]:
                        return json.dumps(result["structuredContent"]["result"])
                    
                    # Handle initialization responses (keep as-is)
                    elif "protocolVersion" in result or "capabilities" in result:
                        return json.dumps(result)
                    
                    # Handle other structured responses
                    else:
                        return json.dumps(result)
                        
                return json.dumps(result)
                
            elif "error" in mcp_data and mcp_data["error"] is not None:
                error_result = {
                    "success": False,
                    "error": mcp_data["error"].get("message", "Unknown error"),
                    "error_code": mcp_data["error"].get("code", -1)
                }
                return json.dumps(error_result)
        
        # Return as-is if not MCP format
        return mcp_response_str
        
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Response unwrapping failed: {e}")
        return mcp_response_str

def main():
    """P1 STDIO Transport with Response Unwrapping."""
    try:
        logger.info("P1: Starting LTMC STDIO with response unwrapping")
        
        # Import and setup MCP server
        from ltms.mcp_server import mcp
        
        # Custom stdio handler that unwraps responses
        original_stdout_write = sys.stdout.write
        response_buffer = []
        
        def unwrapping_write(data):
            if data.strip():
                response_buffer.append(data.strip())
                # Check for complete JSON response
                full_response = ''.join(response_buffer)
                try:
                    json.loads(full_response)  # Validate complete JSON
                    # Unwrap and output
                    unwrapped = unwrap_mcp_response(full_response)
                    original_stdout_write(unwrapped + '\n')
                    sys.stdout.flush()
                    response_buffer.clear()
                except json.JSONDecodeError:
                    # Continue buffering
                    pass
            else:
                original_stdout_write(data)
        
        # Replace stdout write method
        sys.stdout.write = unwrapping_write
        
        # Run MCP server with stdio transport
        mcp.run(transport='stdio')
        
    except KeyboardInterrupt:
        logger.info("P1 STDIO transport stopped by user")
    except Exception as e:
        logger.error(f"P1 STDIO transport error: {e}")
        sys.exit(1)
    finally:
        # Restore original stdout
        sys.stdout.write = original_stdout_write

if __name__ == "__main__":
    main()