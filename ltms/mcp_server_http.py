"""Modularized HTTP transport MCP server for LTMC using FastMCP architecture."""

import os
import logging
import asyncio
from typing import Dict, Any, List, Optional
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

# Import Advanced ML Integration
from ltms.ml.learning_integration import AdvancedLearningIntegration

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

# Global Advanced ML Integration instance
ml_integration: Optional[AdvancedLearningIntegration] = None

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
    health_info = {
        "status": "healthy",
        "transport": "http",
        "port": int(os.environ.get("HTTP_PORT", 5050)),
        "tools_available": len(ALL_TOOLS),
        "architecture": "modularized_fastmcp_with_ml"
    }
    
    # Add ML integration health status
    global ml_integration
    if ml_integration:
        try:
            ml_status = await ml_integration.get_integration_status()
            health_info["advanced_ml_integration"] = {
                "enabled": True,
                "status": ml_status.get("overall_status", "unknown"),
                "completion": ml_status.get("integration_completion", "unknown"),
                "active_components": ml_status.get("active_components", 0),
                "total_components": ml_status.get("total_components", 0)
            }
        except Exception as e:
            health_info["advanced_ml_integration"] = {
                "enabled": True,
                "status": "error",
                "error": str(e)
            }
    else:
        health_info["advanced_ml_integration"] = {"enabled": False}
    
    # Add orchestration health status
    try:
        from ltms.mcp_orchestration_integration import get_orchestration_health
        orchestration_health = await get_orchestration_health()
        health_info["orchestration"] = orchestration_health
    except Exception as e:
        health_info["orchestration"] = {
            "enabled": False,
            "error": str(e),
            "message": "Orchestration health check failed"
        }
    
    return health_info

@app.get("/orchestration/health")
async def orchestration_health():
    """Orchestration-specific health check endpoint."""
    try:
        from ltms.mcp_orchestration_integration import (
            get_orchestration_health,
            is_orchestration_enabled,
            create_orchestration_config
        )
        
        orchestration_health = await get_orchestration_health()
        orchestration_config = create_orchestration_config()
        
        return {
            "orchestration_enabled": is_orchestration_enabled(),
            "health": orchestration_health,
            "config": orchestration_config
        }
    except Exception as e:
        return {
            "orchestration_enabled": False,
            "error": str(e),
            "message": "Failed to get orchestration health status"
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
        },
        "advanced_ml_integration": "enabled" if ml_integration else "disabled"
    }

@app.get("/ml/status")
async def ml_integration_status():
    """Get Advanced ML Integration status."""
    global ml_integration
    if not ml_integration:
        return {"error": "Advanced ML Integration not initialized"}
    
    try:
        return await ml_integration.get_integration_status()
    except Exception as e:
        return {"error": str(e)}

@app.get("/ml/insights")
async def ml_learning_insights():
    """Get comprehensive ML learning insights."""
    global ml_integration
    if not ml_integration:
        return {"error": "Advanced ML Integration not initialized"}
    
    try:
        return await ml_integration.get_learning_insights()
    except Exception as e:
        return {"error": str(e)}

@app.post("/ml/optimize")
async def trigger_ml_optimization():
    """Manually trigger comprehensive ML system optimization."""
    global ml_integration
    if not ml_integration:
        return {"error": "Advanced ML Integration not initialized"}
    
    try:
        return await ml_integration.trigger_system_optimization()
    except Exception as e:
        return {"error": str(e)}

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
            "/ml/status": "Advanced ML Integration status",
            "/ml/insights": "ML learning insights",
            "/ml/optimize": "Trigger ML optimization",
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
        db_path = os.environ.get("DB_PATH", "ltmc.db")
        conn = get_db_connection(db_path)
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
        
        # Initialize orchestration integration (optional)
        try:
            from ltms.mcp_orchestration_integration import (
                initialize_orchestration_integration,
                get_orchestration_mode_from_env,
                create_orchestration_config
            )
            
            orchestration_config = create_orchestration_config()
            orchestration_mode = orchestration_config['orchestration_mode']
            
            if orchestration_mode.value != 'disabled':
                await initialize_orchestration_integration(orchestration_mode)
                logger.info(f"Orchestration integration initialized: {orchestration_mode}")
            else:
                logger.info("Orchestration disabled via configuration")
                
        except Exception as orchestration_error:
            logger.warning(f"Orchestration integration failed (will use fallback mode): {orchestration_error}")
        
        # Initialize Advanced ML Integration
        global ml_integration
        try:
            logger.info("Initializing Advanced ML Integration...")
            ml_integration = AdvancedLearningIntegration(db_path)
            ml_success = await ml_integration.initialize()
            
            if ml_success:
                logger.info("🎉 Advanced ML Integration 100% COMPLETE and ACTIVE! 🎉")
                logger.info("✅ All 4 ML phases initialized and running")
                logger.info("✅ Cross-phase learning coordination active")
                logger.info("✅ ML endpoints available at /ml/status, /ml/insights, /ml/optimize")
            else:
                logger.error("❌ Advanced ML Integration initialization failed")
                ml_integration = None
                
        except Exception as ml_error:
            logger.error(f"Advanced ML Integration failed: {ml_error}")
            ml_integration = None
            
        logger.info(f"LTMC HTTP Server started with {len(ALL_TOOLS)} tools" + 
                   (" + Advanced ML Integration" if ml_integration else ""))
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

@app.on_event("shutdown") 
async def shutdown():
    """Clean up on shutdown."""
    try:
        # Shutdown Advanced ML Integration first
        global ml_integration
        if ml_integration:
            try:
                await ml_integration.cleanup()
                logger.info("Advanced ML Integration shutdown complete")
            except Exception as ml_error:
                logger.warning(f"ML integration shutdown error: {ml_error}")
        
        # Shutdown orchestration integration
        try:
            from ltms.mcp_orchestration_integration import shutdown_orchestration_integration
            await shutdown_orchestration_integration()
            logger.info("Orchestration integration shutdown complete")
        except Exception as orch_error:
            logger.warning(f"Orchestration shutdown error: {orch_error}")
        
        # Shutdown Redis
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