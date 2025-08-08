"""Modularized HTTP transport MCP server for LTMC using FastMCP architecture."""

import os
import logging
import asyncio
from typing import Dict, Any, List
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import modularized tool definitions
from ltms.tools.memory_tools import MEMORY_TOOLS
from ltms.tools.chat_tools import CHAT_TOOLS  
from ltms.tools.todo_tools import TODO_TOOLS
from ltms.tools.context_tools import CONTEXT_TOOLS
from ltms.tools.code_pattern_tools import CODE_PATTERN_TOOLS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LTMC MCP HTTP Server - Modularized",
    description="HTTP transport for LTMC MCP server with <300-line modular architecture",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Combine all tools from modules
ALL_TOOLS = {
    **MEMORY_TOOLS,
    **CHAT_TOOLS,
    **TODO_TOOLS, 
    **CONTEXT_TOOLS,
    **CODE_PATTERN_TOOLS
}

class JSONRPCRequest(BaseModel):
    """JSON-RPC request model."""
    jsonrpc: str = "2.0"
    id: Any
    method: str
    params: Dict[str, Any] = {}

class JSONRPCResponse(BaseModel):
    """JSON-RPC response model."""
    jsonrpc: str = "2.0"
    id: Any
    result: Dict[str, Any] = None
    error: Dict[str, Any] = None

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "transport": "http",
        "port": int(os.environ.get("HTTP_PORT", 5050)),
        "tools_available": len(ALL_TOOLS),
        "architecture": "modularized_fastmcp"
    }

@app.get("/tools")
async def list_tools():
    """List available MCP tools."""
    return {
        "tools": list(ALL_TOOLS.keys()),
        "count": len(ALL_TOOLS),
        "modules": {
            "memory": len(MEMORY_TOOLS),
            "chat": len(CHAT_TOOLS),
            "todo": len(TODO_TOOLS),
            "context": len(CONTEXT_TOOLS),
            "code_pattern": len(CODE_PATTERN_TOOLS)
        }
    }

@app.post("/jsonrpc")
async def jsonrpc_handler(request: JSONRPCRequest):
    """Handle JSON-RPC requests."""
    try:
        if request.method == "tools/call":
            tool_name = request.params.get("name")
            if tool_name not in ALL_TOOLS:
                return JSONRPCResponse(
                    id=request.id,
                    error={"code": -32601, "message": f"Tool '{tool_name}' not found"}
                )
            
            tool_config = ALL_TOOLS[tool_name]
            handler = tool_config["handler"]
            arguments = request.params.get("arguments", {})
            
            # Call the tool handler
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(**arguments)
                else:
                    result = handler(**arguments)
                
                return JSONRPCResponse(id=request.id, result=result)
                
            except Exception as e:
                logger.error(f"Tool {tool_name} execution error: {e}")
                return JSONRPCResponse(
                    id=request.id,
                    error={"code": -32603, "message": f"Tool execution error: {str(e)}"}
                )
        
        elif request.method == "tools/list":
            return JSONRPCResponse(
                id=request.id,
                result={
                    "tools": [
                        {
                            "name": name,
                            "description": config["description"], 
                            "inputSchema": config["schema"]
                        }
                        for name, config in ALL_TOOLS.items()
                    ]
                }
            )
        
        else:
            return JSONRPCResponse(
                id=request.id,
                error={"code": -32601, "message": f"Method '{request.method}' not found"}
            )
            
    except Exception as e:
        logger.error(f"JSON-RPC request error: {e}")
        return JSONRPCResponse(
            id=getattr(request, 'id', None),
            error={"code": -32603, "message": f"Internal error: {str(e)}"}
        )

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "LTMC MCP HTTP Server",
        "version": "2.0.0",
        "architecture": "modularized_fastmcp",
        "endpoints": {
            "/health": "Server health status",
            "/tools": "List available tools", 
            "/jsonrpc": "JSON-RPC 2.0 endpoint",
            "/": "This information"
        },
        "tools_count": len(ALL_TOOLS),
        "modular_design": "Each tool module <300 lines"
    }

# Initialize database on startup
@app.on_event("startup")
async def startup():
    """Initialize services on startup."""
    from ltms.database.schema import create_tables
    from ltms.database.connection import get_db_connection
    
    try:
        # Initialize database
        conn = get_db_connection()
        create_tables(conn)
        conn.close()
        logger.info("Database initialized successfully")
        
        # Initialize Redis if available
        try:
            from ltms.services.redis_service import get_redis_manager
            redis_manager = await get_redis_manager()
            if redis_manager.is_connected:
                logger.info(f"Redis connected: {redis_manager.host}:{redis_manager.port}")
        except Exception as redis_error:
            logger.warning(f"Redis initialization failed: {redis_error}")
            
        logger.info(f"LTMC HTTP Server started with {len(ALL_TOOLS)} tools")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

@app.on_event("shutdown") 
async def shutdown():
    """Clean up on shutdown."""
    try:
        from ltms.services.redis_service import cleanup_redis
        await cleanup_redis()
        logger.info("LTMC HTTP Server shutdown complete")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("HTTP_PORT", 5050))
    host = os.environ.get("HTTP_HOST", "localhost")
    uvicorn.run(app, host=host, port=port)