#!/usr/bin/env python3
"""HTTP wrapper for FastMCP server to maintain tool compatibility."""

import sys
import logging
import json
import asyncio
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup stderr logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr,
    force=True
)
logger = logging.getLogger(__name__)

# Import the FastMCP server
from ltms.mcp_server import mcp

# Create FastAPI app
app = FastAPI(
    title="LTMC MCP HTTP Wrapper", 
    description="HTTP wrapper for unified FastMCP server",
    version="3.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    tool_count = len(mcp._tools) if hasattr(mcp, '_tools') else 0
    return {
        "status": "healthy",
        "transport": "http_wrapper",
        "port": 5050,
        "tools_available": tool_count,
        "architecture": "unified_fastmcp_wrapper",
        "message": "HTTP wrapper for unified FastMCP server"
    }

@app.get("/tools")
async def list_tools():
    """List all available tools."""
    if not hasattr(mcp, '_tools'):
        return {"tools": [], "count": 0}
    
    tools = list(mcp._tools.keys())
    return {
        "tools": sorted(tools),
        "count": len(tools)
    }

@app.post("/jsonrpc")
async def handle_jsonrpc(request: Dict[str, Any]):
    """Handle JSON-RPC requests."""
    try:
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        if method == "tools/list":
            # Return tools list in MCP format
            tools = []
            if hasattr(mcp, '_tools'):
                for tool_name, tool_func in mcp._tools.items():
                    # Get tool schema from FastMCP
                    tool_info = {
                        "name": tool_name,
                        "description": tool_func.__doc__ or f"Tool: {tool_name}",
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                    tools.append(tool_info)
            
            return {
                "jsonrpc": "2.0", 
                "id": request_id,
                "result": {"tools": tools}
            }
        
        elif method == "tools/call":
            # Execute tool call
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if not tool_name or not hasattr(mcp, '_tools'):
                raise HTTPException(status_code=400, detail="Invalid tool call")
            
            if tool_name not in mcp._tools:
                raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
            
            # Execute the tool
            try:
                tool_func = mcp._tools[tool_name]
                result = tool_func(**arguments)
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id, 
                    "result": result
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": f"Tool execution error: {str(e)}"
                    }
                }
        
        else:
            return {
                "jsonrpc": "2.0", 
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
            
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }

if __name__ == "__main__":
    try:
        logger.info("Starting LTMC HTTP wrapper for unified FastMCP server")
        uvicorn.run(app, host="localhost", port=5050, log_level="info")
    except KeyboardInterrupt:
        logger.info("LTMC HTTP wrapper stopped by user")
    except Exception as e:
        logger.error(f"Error running LTMC HTTP wrapper: {e}")
        sys.exit(1)