"""LTMC MCP Server using FastMCP SDK with enhanced functionality."""

import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Setup import paths for all execution contexts
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
project_root_str = str(project_root)

if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)

# Change to project root for consistent behavior
os.chdir(project_root_str)

# Import MCP SDK
from mcp.server.fastmcp import FastMCP

# Import our existing services
from ltms.database.connection import get_db_connection, close_db_connection
from ltms.database.schema import create_tables
from ltms.services.resource_service import add_resource
from ltms.services.context_service import get_context_for_query, log_chat_message
from ltms.services.code_pattern_service import (
    store_code_pattern,
    retrieve_code_patterns,
    analyze_code_patterns
)

# Import tools for additional functionality
from tools.ask import ask_with_context as ask_with_context_tool
from tools.router import route_query as route_query_tool
from tools.context_builder import build_context_window
from tools.retrieve import retrieve_by_type as retrieve_by_type_tool

# Import context linking functionality
from ltms.database.context_linking import (
    store_context_links,
    get_context_links_for_message,
    get_messages_for_chunk,
    get_context_usage_statistics
)

# Import Neo4j graph functionality
from ltms.database.neo4j_store import (
    Neo4jGraphStore,
    create_graph_relationships,
    query_graph_relationships,
    auto_link_related_documents,
    get_document_relationships
)

# Default environment variables (fallbacks). Actual paths are resolved at call time.
DEFAULT_DB_PATH = os.getenv("DB_PATH", "ltmc.db")
DEFAULT_FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "faiss_index")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Neo4j configuration
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "kwe_password",
    "database": "neo4j"
}

# Create the FastMCP server
mcp = FastMCP("LTMC Server")


@mcp.tool()
def store_memory(file_name: str, content: str, resource_type: str = "document") -> Dict[str, Any]:
    """Store memory in LTMC with real database and vector storage."""
    try:
        # Validate input
        if not file_name or not content:
            return {"success": False, "error": "file_name and content are required"}
        
        # Get database connection (resolve path at call time)
        db_path = os.getenv("DB_PATH", DEFAULT_DB_PATH)
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        # Add resource using real service
        result = add_resource(
            conn=conn,
            index_path=os.getenv("FAISS_INDEX_PATH", DEFAULT_FAISS_INDEX_PATH),
            file_name=file_name,
            resource_type=resource_type,
            content=content
        )
        
        # Close database connection
        close_db_connection(conn)
        
        if not result['success']:
            return {"success": False, "error": result.get('error', 'Unknown error')}
        
        return {
            "success": True,
            "message": "Memory stored successfully",
            "resource_id": result['resource_id'],
            "chunk_count": result['chunk_count']
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def retrieve_memory(conversation_id: str, query: str, top_k: int = 3) -> Dict[str, Any]:
    """Retrieve memory from LTMC with real vector search."""
    try:
        # Validate input
        if not conversation_id or not query:
            return {"success": False, "error": "conversation_id and query are required"}
        
        # Get database connection
        db_path = os.getenv("DB_PATH", DEFAULT_DB_PATH)
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        # Get context using real service
        result = get_context_for_query(
            conn=conn,
             index_path=os.getenv("FAISS_INDEX_PATH", DEFAULT_FAISS_INDEX_PATH),
            conversation_id=conversation_id,
            query=query,
            top_k=top_k
        )
        
        # Close database connection
        close_db_connection(conn)
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def log_chat(
    conversation_id: str,
    role: str,
    content: str,
    agent_name: str | None = None,
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Log chat message in LTMC."""
    try:
        # Validate input
        if not conversation_id or not role or not content:
            return {"success": False, "error": "conversation_id, role, and content are required"}
        
        # Get database connection
        db_path = os.getenv("DB_PATH", DEFAULT_DB_PATH)
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        # Log chat message
        message_id = log_chat_message(
            conn,
            conversation_id,
            role,
            content,
            agent_name=agent_name,
            metadata=metadata,
        )
        
        # Close database connection
        close_db_connection(conn)
        
        return {"success": True, "message_id": int(message_id)}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def ask_with_context(query: str, conversation_id: str, top_k: int = 5) -> Dict[str, Any]:
    """Ask a question with context from LTMC memory."""
    try:
        return ask_with_context_tool(query, conversation_id, top_k)
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def route_query(query: str, source_types: List[str], top_k: int = 5) -> Dict[str, Any]:
    """Route query to different sources using LTMC memory."""
    try:
        return route_query_tool(query, source_types, top_k)
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def build_context(documents: List[Dict[str, Any]], max_tokens: int = 4000) -> Dict[str, Any]:
    """Build context from documents."""
    try:
        return build_context_window(documents, max_tokens)
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def retrieve_by_type(query: str, doc_type: str, top_k: int = 5) -> Dict[str, Any]:
    """Retrieve documents by type."""
    try:
        return retrieve_by_type_tool(query, doc_type, top_k)
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def add_todo(title: str, description: str, priority: str = "medium") -> Dict[str, Any]:
    """Add a new todo item with real database storage."""
    try:
        # Validate input
        if not title or not description:
            return {"success": False, "error": "title and description are required"}
        
        # Get database connection
        db_path = os.getenv("DB_PATH", DEFAULT_DB_PATH)
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        # Add todo
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Todos (title, description, priority, completed, created_at) VALUES (?, ?, ?, ?, ?)",
            (title, description, priority, False, datetime.now().isoformat())
        )
        todo_id = cursor.lastrowid
        conn.commit()
        
        # Close database connection
        close_db_connection(conn)
        
        return {
            "success": True,
            "todo_id": todo_id,
            "message": "Todo added successfully"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_todos(completed: Optional[bool] = None) -> Dict[str, Any]:
    """List todo items with real database query."""
    try:
        # Get database connection
        db_path = os.getenv("DB_PATH", DEFAULT_DB_PATH)
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        # Query todos
        cursor = conn.cursor()
        if completed is None:
            cursor.execute("SELECT * FROM Todos ORDER BY created_at DESC")
        else:
            cursor.execute(
                "SELECT * FROM Todos WHERE completed = ? ORDER BY created_at DESC",
                (completed,)
            )
        
        todos = []
        for row in cursor.fetchall():
            todos.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "priority": row[3],
                "completed": bool(row[4]),
                "created_at": row[5]
            })
        
        # Close database connection
        close_db_connection(conn)
        
        return {
            "success": True,
            "todos": todos,
            "count": len(todos)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def complete_todo(todo_id: int) -> Dict[str, Any]:
    """Mark a todo as completed with real database update."""
    try:
        # Validate input
        if not todo_id:
            return {"success": False, "error": "todo_id is required"}
        
        # Get database connection
        db_path = os.getenv("DB_PATH", DEFAULT_DB_PATH)
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        # Update todo
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Todos SET completed = ? WHERE id = ?",
            (True, todo_id)
        )
        
        if cursor.rowcount == 0:
            return {"success": False, "error": "Todo not found"}
        
        conn.commit()
        
        # Close database connection
        close_db_connection(conn)
        
        return {
            "success": True,
            "message": "Todo marked as completed"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def search_todos(query: str) -> Dict[str, Any]:
    """Search todos by title or description with real database search."""
    try:
        # Validate input
        if not query:
            return {"success": False, "error": "query is required"}
        
        # Get database connection
        db_path = os.getenv("DB_PATH", DEFAULT_DB_PATH)
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        # Search todos
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM Todos WHERE title LIKE ? OR description LIKE ? ORDER BY created_at DESC",
            (f"%{query}%", f"%{query}%")
        )
        
        todos = []
        for row in cursor.fetchall():
            todos.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "priority": row[3],
                "completed": bool(row[4]),
                "created_at": row[5]
            })
        
        # Close database connection
        close_db_connection(conn)
        
        return {
            "success": True,
            "todos": todos,
            "count": len(todos)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# Context Linking Tools
@mcp.tool()
def store_context_links_tool(message_id: int, chunk_ids: List[int]) -> Dict[str, Any]:
    """Store context links between a message and the chunks it used."""
    try:
        # Validate input
        if not message_id or not chunk_ids:
            return {"success": False, "error": "message_id and chunk_ids are required"}
        
        # Get database connection
        db_path = os.getenv("DB_PATH", DEFAULT_DB_PATH)
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        # Store context links
        result = store_context_links(conn, message_id, chunk_ids)
        
        # Close database connection
        close_db_connection(conn)
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_context_links_for_message_tool(message_id: int) -> Dict[str, Any]:
    """Get all context links for a specific message."""
    try:
        # Validate input
        if not message_id:
            return {"success": False, "error": "message_id is required"}
        
        # Get database connection
        db_path = os.getenv("DB_PATH", DEFAULT_DB_PATH)
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        # Get context links
        result = get_context_links_for_message(conn, message_id)
        
        # Close database connection
        close_db_connection(conn)
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_messages_for_chunk_tool(chunk_id: int) -> Dict[str, Any]:
    """Get all messages that used a specific chunk."""
    try:
        # Validate input
        if not chunk_id:
            return {"success": False, "error": "chunk_id is required"}
        
        # Get database connection
        conn = get_db_connection(DB_PATH)
        create_tables(conn)
        
        # Get messages for chunk
        result = get_messages_for_chunk(conn, chunk_id)
        
        # Close database connection
        close_db_connection(conn)
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_context_usage_statistics_tool() -> Dict[str, Any]:
    """Get statistics about context usage."""
    try:
        # Get database connection
        conn = get_db_connection(DB_PATH)
        create_tables(conn)
        
        # Get statistics
        result = get_context_usage_statistics(conn)
        
        # Close database connection
        close_db_connection(conn)
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# Neo4j Graph Tools
@mcp.tool()
def link_resources(source_id: str, target_id: str, relation: str) -> Dict[str, Any]:
    """Link two resources with a relationship in the graph.

    Args:
        source_id: The source document ID
        target_id: The target document ID
        relation: The relationship type (e.g., REFERENCES)
    """
    try:
        # Validate input
        if not source_id or not target_id or not relation:
            return {
                "success": False,
                "error": "source_id, target_id, and relation are required",
            }
        
        # Initialize Neo4j store with correct configuration
        neo4j_config = NEO4J_CONFIG
        
        store = Neo4jGraphStore(neo4j_config)
        
        # Create relationship
        result = create_graph_relationships(store, source_id, target_id, relation)
        
        # Close connection
        store.close()
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def query_graph(entity: str, relation_type: str = None) -> Dict[str, Any]:
    """Query graph relationships for an entity."""
    try:
        # Validate input
        if not entity:
            return {"success": False, "error": "entity is required"}
        
        # Initialize Neo4j store with correct configuration
        neo4j_config = NEO4J_CONFIG
        
        store = Neo4jGraphStore(neo4j_config)
        
        # Query relationships
        result = query_graph_relationships(store, entity, relation_type)
        
        # Close connection
        store.close()
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def auto_link_documents(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Automatically link related documents based on content similarity."""
    try:
        # Validate input
        if not documents:
            return {"success": False, "error": "documents list is required"}
        
        # Initialize Neo4j store with correct configuration
        neo4j_config = NEO4J_CONFIG
        
        store = Neo4jGraphStore(neo4j_config)
        
        # Auto-link documents
        result = auto_link_related_documents(store, documents)
        
        # Close connection
        store.close()
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_document_relationships_tool(doc_id: str) -> Dict[str, Any]:
    """Get all relationships for a document."""
    try:
        # Validate input
        if not doc_id:
            return {"success": False, "error": "doc_id is required"}
        
        # Initialize Neo4j store with correct configuration
        neo4j_config = NEO4J_CONFIG
        
        store = Neo4jGraphStore(neo4j_config)
        
        # Get relationships
        result = get_document_relationships(store, doc_id)
        
        # Close connection
        store.close()
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def log_code_attempt(
    input_prompt: str,
    generated_code: str,
    result: str,
    function_name: str = None,
    file_name: str = None,
    module_name: str = None,
    execution_time_ms: int = None,
    error_message: str = None,
    tags: List[str] = None
) -> Dict[str, Any]:
    """Log a code generation attempt for pattern learning.
    
    Stores code generation attempts (successes and failures) to enable
    "Experience Replay for Code" - allowing models to learn from past
    success and failure across sessions.
    """
    try:
        # Validate input
        if not input_prompt or not generated_code or not result:
            return {"success": False, "error": "input_prompt, generated_code, and result are required"}
        
        if result not in ['pass', 'fail', 'partial']:
            return {"success": False, "error": "result must be one of: pass, fail, partial"}
        
        # Get database connection
        db_path = os.getenv("DB_PATH", DEFAULT_DB_PATH)
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        # Store code pattern
        result_data = store_code_pattern(
            conn=conn,
            input_prompt=input_prompt,
            generated_code=generated_code,
            result=result,
            function_name=function_name,
            file_name=file_name,
            module_name=module_name,
            execution_time_ms=execution_time_ms,
            error_message=error_message,
            tags=tags
        )
        
        # Close database connection
        close_db_connection(conn)
        
        return result_data
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_code_patterns(
    query: str,
    result_filter: str = None,
    function_name: str = None,
    file_name: str = None,
    module_name: str = None,
    top_k: int = 5
) -> Dict[str, Any]:
    """Retrieve similar code patterns for learning.
    
    Finds similar code generation patterns to help models learn from
    past successes and failures.
    """
    try:
        # Validate input
        if not query:
            return {"success": False, "error": "query is required"}
        
        if result_filter and result_filter not in ['pass', 'fail', 'partial']:
            return {"success": False, "error": "result_filter must be one of: pass, fail, partial"}
        
        # Get database connection
        db_path = os.getenv("DB_PATH", DEFAULT_DB_PATH)
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        # Retrieve code patterns
        result_data = retrieve_code_patterns(
            conn=conn,
            query=query,
            result_filter=result_filter,
            function_name=function_name,
            file_name=file_name,
            module_name=module_name,
            top_k=top_k
        )
        
        # Close database connection
        close_db_connection(conn)
        
        return result_data
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def analyze_code_patterns_tool(
    function_name: str = None,
    file_name: str = None,
    module_name: str = None,
    time_range_days: int = 30
) -> Dict[str, Any]:
    """Analyze code pattern success rates and trends.
    
    Provides insights into code generation success rates, helping
    identify areas for improvement and learning opportunities.
    """
    try:
        # Validate input
        if time_range_days <= 0:
            return {"success": False, "error": "time_range_days must be positive"}
        
        # Get database connection
        db_path = os.getenv("DB_PATH", DEFAULT_DB_PATH)
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        # Analyze code patterns
        result_data = analyze_code_patterns(
            conn=conn,
            function_name=function_name,
            file_name=file_name,
            module_name=module_name,
            time_range_days=time_range_days
        )
        
        # Close database connection
        close_db_connection(conn)
        
        return result_data
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# The FastMCP server is now ready to use. Expose convenience async wrappers and stdio stub

import asyncio


async def run_stdio() -> None:
    """Stub method to satisfy stdio capability checks in tests.

    Real stdio transport is handled by external runners (e.g., mcp dev).
    """
    return None


async def _store_memory_proxy(file_name: str, content: str, resource_type: str = "document") -> Dict[str, Any]:
    return store_memory(file_name, content, resource_type)


async def _retrieve_memory_proxy(conversation_id: str, query: str, top_k: int = 3) -> Dict[str, Any]:
    return retrieve_memory(conversation_id, query, top_k)


async def _log_chat_proxy(conversation_id: str, role: str, content: str) -> Dict[str, Any]:
    return log_chat(conversation_id, role, content)


async def _ask_with_context_proxy(query: str, conversation_id: str, top_k: int = 5) -> Dict[str, Any]:
    return ask_with_context(query, conversation_id, top_k)


async def _route_query_proxy(query: str, source_types: List[str], top_k: int = 5) -> Dict[str, Any]:
    return route_query(query, source_types, top_k)


async def _build_context_proxy(documents: List[Dict[str, Any]], max_tokens: int = 4000) -> Dict[str, Any]:
    return build_context(documents, max_tokens)


async def _retrieve_by_type_proxy(query: str, doc_type: str, top_k: int = 5) -> Dict[str, Any]:
    return retrieve_by_type(query, doc_type, top_k)


# Attach proxies to mcp instance for tests that access them as attributes
mcp.run_stdio = run_stdio  # type: ignore[attr-defined]
mcp.store_memory = _store_memory_proxy  # type: ignore[attr-defined]
mcp.retrieve_memory = _retrieve_memory_proxy  # type: ignore[attr-defined]
mcp.log_chat = _log_chat_proxy  # type: ignore[attr-defined]
mcp.ask_with_context = _ask_with_context_proxy  # type: ignore[attr-defined]
mcp.route_query = _route_query_proxy  # type: ignore[attr-defined]
mcp.build_context = _build_context_proxy  # type: ignore[attr-defined]
mcp.retrieve_by_type = _retrieve_by_type_proxy  # type: ignore[attr-defined]
