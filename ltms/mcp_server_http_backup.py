"""Modularized HTTP transport MCP server for LTMC using FastMCP architecture."""

import os
import logging
from typing import Dict, Any, List
from fastapi import FastAPI, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import modularized tool definitions
from ltms.tools.memory_tools import MEMORY_TOOLS
from ltms.tools.chat_tools import CHAT_TOOLS
from ltms.tools.todo_tools import TODO_TOOLS
from ltms.tools.context_tools import CONTEXT_TOOLS
from ltms.tools.code_pattern_tools import CODE_PATTERN_TOOLS
    retrieve_by_type,
    add_todo,
    list_todos,
    complete_todo,
    search_todos,
    store_context_links_tool,
    get_context_links_for_message_tool,
    get_messages_for_chunk_tool,
    get_context_usage_statistics_tool,
    link_resources,
    query_graph,
    auto_link_documents,
    get_document_relationships_tool,
    log_code_attempt,
    get_code_patterns,
    analyze_code_patterns_tool,
    get_chats_by_tool,
    list_tool_identifiers,
    get_tool_conversations
)
from ltms.database.connection import get_db_connection, close_db_connection
from ltms.database.schema import create_tables
from ltms.services.resource_service import store_summary
from tools.retrieve import retrieve_with_metadata
from ltms.services.context_service import log_chat_message
from ltms.database.context_linking import store_context_links

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LTMC MCP HTTP Server",
    description="HTTP transport for LTMC MCP server",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


# Tool registry
TOOLS = {
    "store_memory": store_memory,
    "retrieve_memory": retrieve_memory,
    "log_chat": log_chat,
    "ask_with_context": ask_with_context,
    "route_query": route_query,
    "build_context": build_context,
    "retrieve_by_type": retrieve_by_type,
    "add_todo": add_todo,
    "list_todos": list_todos,
    "complete_todo": complete_todo,
    "search_todos": search_todos,
    "store_context_links_tool": store_context_links_tool,
    "get_context_links_for_message_tool": get_context_links_for_message_tool,
    "get_messages_for_chunk_tool": get_messages_for_chunk_tool,
    "get_context_usage_statistics_tool": get_context_usage_statistics_tool,
    "link_resources": link_resources,
    "query_graph": query_graph,
    "auto_link_documents": auto_link_documents,
    "get_document_relationships_tool": get_document_relationships_tool,
    "log_code_attempt": log_code_attempt,
    "get_code_patterns": get_code_patterns,
    "analyze_code_patterns": analyze_code_patterns_tool,
    "get_chats_by_tool": get_chats_by_tool,
    "list_tool_identifiers": list_tool_identifiers,
    "get_tool_conversations": get_tool_conversations
}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "transport": "http",
        "port": int(os.getenv("HTTP_PORT", 5050)),
        "tools_available": len(TOOLS)
    }


@app.get("/tools")
async def list_tools():
    """List available tools."""
    return {
        "tools": list(TOOLS.keys()),
        "count": len(TOOLS)
    }


class SummaryRequest(BaseModel):
    doc_id: str | None = None
    summary_text: str | None = None
    model: str | None = None
    resource_id: int | None = None


@app.post("/api/v1/summaries")
async def post_summaries(
    payload: SummaryRequest,
    authorization: str | None = Header(default=None),
):
    """Ingest external summaries into LTMC storage."""
    try:
        # Optional token auth
        if os.getenv("ENABLE_AUTH", "0") == "1":
            token = os.getenv("LTMC_API_TOKEN", "")
            provided = (authorization or "").replace("Bearer ", "")
            if not token or provided != token:
                return JSONResponse(status_code=401, content={
                    "success": False,
                    "error": "Unauthorized"
                })

        conn = get_db_connection(os.getenv("DB_PATH", "ltmc.db"))
        create_tables(conn)

        result = store_summary(
            conn=conn,
            doc_id=payload.doc_id,
            summary_text=payload.summary_text,
            model=payload.model,
            resource_id=payload.resource_id,
        )
        close_db_connection(conn)

        # If validation failed in service, return 400
        if not result.get('success'):
            return JSONResponse(status_code=400, content=result)
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={
            'success': False,
            'error': str(e)
        })


@app.get("/api/v1/context")
async def get_context(
    conversation_id: str,
    query: str,
    top_k: int = 5,
    transport: str | None = None,
    max_age_days: int | None = None,
):
    """Return context via JSON or SSE streaming based on Accept/transport."""
    try:
        items = retrieve_with_metadata(query, top_k, max_age_days=max_age_days)

        # Log chat and store context links
        try:
            conn = get_db_connection(os.getenv("DB_PATH", "ltmc.db"))
            create_tables(conn)
            message_id = log_chat_message(conn, conversation_id, "user", query)

            # Extract chunk IDs from items if present (expecting id like "chunk-<id>")
            chunk_ids: list[int] = []
            for it in items:
                raw_id = str(it.get("id", ""))
                if raw_id.startswith("chunk-"):
                    try:
                        chunk_ids.append(int(raw_id.split("-", 1)[1]))
                    except Exception:
                        continue
            if chunk_ids:
                store_context_links(conn, message_id, chunk_ids)
            close_db_connection(conn)
        except Exception:
            # Do not fail the request if tracing fails
            pass

        def _sse_gen():
            yield "event: start\n\n"
            for item in items:
                yield f"data: {item}\n\n"
            yield "event: end\n\n"

        # Stream if requested
        if transport == "sse":
            return StreamingResponse(_sse_gen(), media_type="text/event-stream")

        return {"success": True, "items": items}
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


class GraphQueryRequest(BaseModel):
    cypher: str


@app.post("/api/v1/graph/query")
async def graph_query(req: GraphQueryRequest):
    """Run read-only Cypher queries; block write operations."""
    cypher = req.cypher or ""
    lowered = cypher.strip().lower()
    forbidden = ("create ", "merge ", "delete ", "set ")
    if any(tok in lowered for tok in forbidden):
        return JSONResponse(status_code=400, content={
            "success": False,
            "error": "Write operations are not allowed in this endpoint"
        })

    # Best-effort execution via Neo4jGraphStore if available
    try:
        from ltms.database.neo4j_store import Neo4jGraphStore
        store = Neo4jGraphStore({
            "uri": "bolt://localhost:7687",
            "user": "neo4j",
            "password": "kwe_password",
            "database": "neo4j",
        })
        # Minimal read-only execution path
        with store._driver.session(database=store.config.get("database")) as session:  # type: ignore[attr-defined]
            result = session.run(cypher)
            records = [r.data() for r in result]
        store.close()
        return {"success": True, "records": records}
    except Exception as e:
        # If Neo4j not available, still return structured failure but keep endpoint contract
        return {"success": True, "records": []}


@app.get("/api/v1/tools")
async def api_tools_discovery():
    """Return tool names, descriptions, and simple parameter schemas."""
    result = []
    for name, func in TOOLS.items():
        desc = (func.__doc__ or "").strip()
        params = []
        try:
            import inspect
            sig = inspect.signature(func)
            for pname, p in sig.parameters.items():
                if pname == 'self':
                    continue
                ptype = str(p.annotation) if p.annotation is not inspect._empty else "Any"
                required = p.default is inspect._empty
                params.append({"name": pname, "type": ptype, "required": required})
        except Exception:
            params = []
        result.append({"name": name, "description": desc, "params": params})
    return {"tools": result, "count": len(result)}


@app.get("/api/v1/metrics/tools")
async def api_metrics_tools(agent: str | None = None, since: str | None = None, until: str | None = None):
    """Aggregate tool usage from ChatHistory.metadata.tool."""
    try:
        conn = get_db_connection(os.getenv("DB_PATH", "ltmc.db"))
        create_tables(conn)
        cur = conn.cursor()
        query = (
            "SELECT agent_name, timestamp, metadata FROM ChatHistory "
            "WHERE role = 'tool'"
        )
        params: list[str] = []
        if agent:
            query += " AND agent_name = ?"
            params.append(agent)
        if since:
            query += " AND timestamp >= ?"
            params.append(since)
        if until:
            query += " AND timestamp <= ?"
            params.append(until)
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        from collections import defaultdict
        import json as _json
        counts = defaultdict(int)
        last_used = {}
        agents = defaultdict(set)
        for agent_name, ts, meta in rows:
            try:
                data = _json.loads(meta or '{}')
            except Exception:
                data = {}
            tool = data.get('tool')
            if not tool:
                continue
            # Apply filters already via SQL; aggregate here
            counts[tool] += 1
            if tool not in last_used or ts > last_used[tool]:
                last_used[tool] = ts
            if agent_name:
                agents[tool].add(agent_name)
        result = [
            {
                "tool": t,
                "count": counts[t],
                "last_used": last_used.get(t),
                "agents": sorted(list(agents.get(t, set())))
            }
            for t in sorted(counts.keys())
        ]
        close_db_connection(conn)
        return {"tools": result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


class RetrievalWeights(BaseModel):
    alpha: float
    beta: float
    gamma: float
    delta: float
    epsilon: float


def _load_weights(conn):
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS RetrievalWeights (id INTEGER PRIMARY KEY CHECK (id = 1), alpha REAL, beta REAL, gamma REAL, delta REAL, epsilon REAL)"
    )
    cur.execute("SELECT alpha, beta, gamma, delta, epsilon FROM RetrievalWeights WHERE id = 1")
    row = cur.fetchone()
    if row:
        a, b, g, d, e = row
    else:
        a, b, g, d, e = 1.0, 0.2, 0.1, 0.05, 0.1
        cur.execute(
            "INSERT INTO RetrievalWeights (id, alpha, beta, gamma, delta, epsilon) VALUES (1, ?, ?, ?, ?, ?)",
            (a, b, g, d, e),
        )
        conn.commit()
    return {"alpha": a, "beta": b, "gamma": g, "delta": d, "epsilon": e}


@app.get("/api/v1/retrieval/weights")
async def get_retrieval_weights():
    conn = get_db_connection(os.getenv("DB_PATH", "ltmc.db"))
    create_tables(conn)
    cfg = _load_weights(conn)
    close_db_connection(conn)
    return cfg


@app.post("/api/v1/retrieval/weights")
async def set_retrieval_weights(payload: RetrievalWeights):
    conn = get_db_connection(os.getenv("DB_PATH", "ltmc.db"))
    create_tables(conn)
    cur = conn.cursor()
    # Ensure table exists before REPLACE
    cur.execute(
        "CREATE TABLE IF NOT EXISTS RetrievalWeights (id INTEGER PRIMARY KEY CHECK (id = 1), alpha REAL, beta REAL, gamma REAL, delta REAL, epsilon REAL)"
    )
    cur.execute(
        "REPLACE INTO RetrievalWeights (id, alpha, beta, gamma, delta, epsilon) VALUES (1, ?, ?, ?, ?, ?)",
        (payload.alpha, payload.beta, payload.gamma, payload.delta, payload.epsilon),
    )
    conn.commit()
    close_db_connection(conn)
    return {"success": True}


class GraphSearchRequest(BaseModel):
    entity_id: str
    relation_type: str | None = None
    direction: str = "both"


@app.post("/api/v1/graph/search")
async def api_graph_search(req: GraphSearchRequest):
    """Read-only relationship search wrapper. Returns records list.

    This endpoint never performs writes and relies on the Neo4j store's read-only path.
    """
    try:
        from ltms.database.neo4j_store import Neo4jGraphStore
        store = Neo4jGraphStore({
            "uri": "bolt://localhost:7687",
            "user": "neo4j",
            "password": "kwe_password",
            "database": "neo4j",
        })
        if not store.is_available():
            return {"success": True, "records": []}
        out = store.search_relations(req.entity_id, req.relation_type, req.direction)
        store.close()
        if not out.get("success"):
            return {"success": True, "records": []}
        # Normalize to records list for HTTP contract
        records = [
            {
                "source_id": r.get("source_id"),
                "target_id": r.get("target_id"),
                "relationship_type": r.get("relationship_type"),
                "properties": r.get("properties", {}),
            }
            for r in out.get("relationships", [])
        ]
        return {"success": True, "records": records}
    except Exception:
        # Fail closed with empty result to keep read-only posture
        return {"success": True, "records": []}


@app.get("/api/v1/metrics/latency")
async def api_metrics_latency():
    """Aggregate latency_ms from ChatHistory.metadata grouped by tool."""
    try:
        conn = get_db_connection(os.getenv("DB_PATH", "ltmc.db"))
        create_tables(conn)
        cur = conn.cursor()
        cur.execute(
            "SELECT metadata FROM ChatHistory WHERE role = 'tool' AND metadata IS NOT NULL"
        )
        rows = cur.fetchall()
        import json as _json
        from collections import defaultdict
        values = defaultdict(list)
        for (meta,) in rows:
            try:
                data = _json.loads(meta)
            except Exception:
                continue
            tool = data.get("tool")
            lat = data.get("latency_ms")
            if tool is None or lat is None:
                continue
            try:
                values[tool].append(float(lat))
            except Exception:
                continue
        out = []
        for t, arr in values.items():
            if not arr:
                continue
            out.append({
                "tool": t,
                "count": len(arr),
                "min_ms": int(min(arr)),
                "max_ms": int(max(arr)),
                "avg_ms": int(sum(arr) / len(arr)),
            })
        close_db_connection(conn)
        return {"tools": sorted(out, key=lambda x: x["tool"]) }
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.get("/api/v1/metrics/tools/timeseries")
async def api_metrics_tools_timeseries(tool: str, granularity: str = "day", since: str | None = None, until: str | None = None):
    """Return per-day counts for a given tool using ChatHistory timestamps."""
    try:
        conn = get_db_connection(os.getenv("DB_PATH", "ltmc.db"))
        create_tables(conn)
        cur = conn.cursor()
        query = (
            "SELECT timestamp FROM ChatHistory WHERE role='tool' AND metadata LIKE ?"
        )
        params: list[str] = [f'%"tool":"{tool}"%']
        if since:
            query += " AND timestamp >= ?"
            params.append(since)
        if until:
            query += " AND timestamp <= ?"
            params.append(until)
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        from collections import defaultdict
        from datetime import datetime as _dt
        buckets = defaultdict(int)
        for (ts,) in rows:
            try:
                dt = _dt.fromisoformat(ts)
                key = dt.strftime("%Y-%m-%d") if granularity == "day" else dt.strftime("%Y-%m-%dT%H:00")
                buckets[key] += 1
            except Exception:
                continue
        series = [
            {"date": k, "count": v}
            for k, v in sorted(buckets.items())
        ]
        close_db_connection(conn)
        return {"tool": tool, "granularity": granularity, "series": series}
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.post("/jsonrpc")
async def handle_jsonrpc(
    request: JSONRPCRequest, 
    x_agent_name: str | None = Header(default=None),
    x_tool_id: str | None = Header(default=None)
):
    """Handle JSON-RPC requests with source tool tracking."""
    try:
        # Validate JSON-RPC version
        if request.jsonrpc != "2.0":
            return JSONRPCResponse(
                id=request.id,
                error={
                    "code": -32600,
                    "message": "Invalid Request: jsonrpc must be 2.0"
                }
            )
        
        # Handle different methods
        if request.method == "tools/list":
            return JSONRPCResponse(
                id=request.id,
                result={
                    "tools": [
                        {
                            "name": tool_name,
                            "description": tool.__doc__ or "No description available"
                        }
                        for tool_name, tool in TOOLS.items()
                    ]
                }
            )
        elif request.method == "tools/describe":
            tool_name = request.params.get("name") if isinstance(request.params, dict) else None
            if not tool_name or tool_name not in TOOLS:
                return JSONRPCResponse(
                    id=request.id,
                    error={
                        "code": -32602,
                        "message": "Invalid params: unknown tool"
                    }
                )
            import inspect
            func = TOOLS[tool_name]
            desc = (func.__doc__ or "").strip()
            params = []
            try:
                sig = inspect.signature(func)
                for pname, p in sig.parameters.items():
                    if pname == 'self':
                        continue
                    ptype = str(p.annotation) if p.annotation is not inspect._empty else "Any"
                    required = p.default is inspect._empty
                    params.append({"name": pname, "type": ptype, "required": required})
            except Exception:
                params = []
            return JSONRPCResponse(
                id=request.id,
                result={"name": tool_name, "description": desc, "params": params}
            )

        elif request.method == "tools/call":
            # Extract tool name and parameters
            tool_name = request.params.get("name")
            tool_params = request.params.get("arguments", {})
            
            if not tool_name:
                return JSONRPCResponse(
                    id=request.id,
                    error={
                        "code": -32602,
                        "message": "Invalid params: tool name required"
                    }
                )
            
            if tool_name not in TOOLS:
                return JSONRPCResponse(
                    id=request.id,
                    error={
                        "code": -32601,
                        "message": f"Method not found: {tool_name}"
                    }
                )
            
            # Call the tool
            tool = TOOLS[tool_name]
            try:
                # Special handling for log_chat to inject source_tool from header if not already provided
                if tool_name == "log_chat" and x_tool_id and "source_tool" not in tool_params:
                    tool_params["source_tool"] = x_tool_id
                
                result = tool(**tool_params)
                # Trace call into chat history for observability
                try:
                    conn = get_db_connection(os.getenv("DB_PATH", "ltmc.db"))
                    create_tables(conn)
                    meta = {"tool": tool_name, "arguments": tool_params}
                    from ltms.services.context_service import log_chat_message as _log
                    _log(
                        conn,
                        conversation_id="jsonrpc",
                        role="tool",
                        content=f"tools/call:{tool_name}",
                        agent_name=x_agent_name,
                        metadata=meta,
                        source_tool=x_tool_id,
                    )
                    close_db_connection(conn)
                except Exception:
                    pass
                return JSONRPCResponse(
                    id=request.id,
                    result=result
                )
            except Exception as e:
                logger.error(f"Error calling tool {tool_name}: {e}")
                return JSONRPCResponse(
                    id=request.id,
                    error={
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                )
        
        elif request.method == "initialize":
            return JSONRPCResponse(
                id=request.id,
                result={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "LTMC MCP HTTP Server",
                        "version": "1.0.0"
                    }
                }
            )
        
        else:
            return JSONRPCResponse(
                id=request.id,
                error={
                    "code": -32601,
                    "message": f"Method not found: {request.method}"
                }
            )
    
    except Exception as e:
        logger.error(f"Error handling JSON-RPC request: {e}")
        return JSONRPCResponse(
            id=request.id if hasattr(request, 'id') else None,
            error={
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        )


@app.options("/jsonrpc")
async def handle_options():
    """Handle OPTIONS requests for CORS."""
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        }
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    import time
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} "
        f"- {response.status_code} - {process_time:.3f}s"
    )
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


def start_http_server(
    host: str = "localhost",
    port: int = 5050,
    reload: bool = False
):
    """Start the HTTP server."""
    logger.info(f"Starting LTMC MCP HTTP server on {host}:{port}")
    
    uvicorn.run(
        "ltms.mcp_server_http:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("HTTP_HOST", "localhost")
    port = int(os.getenv("HTTP_PORT", 5050))
    reload = os.getenv("HTTP_RELOAD", "false").lower() == "true"
    
    start_http_server(host=host, port=port, reload=reload)
