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

# Import FastMCP SDK
from fastmcp import FastMCP

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

# Import Redis caching service
from ltms.services.redis_service import (
    get_redis_manager,
    get_cache_service,
    cleanup_redis,
    redis_context
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

# Import centralized configuration with proper .env loading
from ltms.config import config, DB_PATH, FAISS_INDEX_PATH, EMBEDDING_MODEL

# Import connection pooling for high performance
from ltms.core.connection_pool import get_connection_manager, PoolConfig

# Phase 3 Component 2: Documentation Synchronization Tools will be imported locally to avoid circular imports

# Import security integration components
from ltms.security.mcp_integration import (
    get_mcp_security_manager,
    initialize_mcp_security,
    secure_mcp_tool,
    MCPSecurityError
)

# Default environment variables (fallbacks). Actual paths are resolved at call time.
DEFAULT_DB_PATH = DB_PATH
DEFAULT_FAISS_INDEX_PATH = FAISS_INDEX_PATH

# Neo4j configuration
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "kwe_password",
    "database": "neo4j"
}

# Initialize security for MCP server
initialize_mcp_security(project_root, project_root)

# Initialize connection pooling for high concurrency
pool_config = PoolConfig(
    min_connections=5,
    max_connections=50,
    connection_timeout_ms=5000,
    idle_timeout_ms=300000,  # 5 minutes
    health_check_interval_ms=30000
)
connection_manager = get_connection_manager(
    db_path=config.get_db_path(),
    pool_config=pool_config
)

# Create the FastMCP server
mcp = FastMCP("LTMC Server")


@mcp.tool()
def store_memory(file_name: str, content: str, resource_type: str = "document", project_id: Optional[str] = None) -> Dict[str, Any]:
    """Store memory in LTMC with real database and vector storage.
    
    Args:
        file_name: Name of the file to store
        content: Content to store
        resource_type: Type of resource (document, code, note)
        project_id: Optional project ID for isolation (None = default project)
    """
    try:
        # Security validation
        security_manager = get_mcp_security_manager()
        try:
            validation_result = security_manager.validate_mcp_request(
                project_id=project_id,
                operation="write",
                file_path=file_name,
                user_input=content
            )
            # Use sanitized content
            if validation_result.get('sanitized_input'):
                content = validation_result['sanitized_input']
        except MCPSecurityError as e:
            return {"success": False, "error": f"Security validation failed: {e}"}
        
        # Validate input
        if not file_name or not content:
            return {"success": False, "error": "file_name and content are required"}
        
        # Get database connection (resolve path at call time)
        db_path = config.get_db_path()
        # Apply project scoping if available
        if validation_result.get('scoped_db_path'):
            db_path = validation_result['scoped_db_path']
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        # Add resource using real service
        result = add_resource(
            conn=conn,
            index_path=config.get_faiss_index_path(),
            file_name=file_name,
            resource_type=resource_type,
            content=content
        )
        
        # Close database connection
        close_db_connection(conn)
        
        if not result['success']:
            return {"success": False, "error": result.get('error', 'Unknown error')}
        
        response = {
            "success": True,
            "message": "Memory stored successfully",
            "resource_id": result['resource_id'],
            "chunk_count": result['chunk_count']
        }
        
        # Add security context
        response['_security_context'] = {
            "project_id": validation_result.get('project_id', 'default'),
            "validation_time_ms": validation_result.get('execution_time_ms', 0),
            "secure": True
        }
        
        return response
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def retrieve_memory(conversation_id: str, query: str, top_k: int = 3, project_id: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve memory from LTMC with real vector search.
    
    Args:
        conversation_id: ID of the conversation
        query: Search query
        top_k: Number of results to return
        project_id: Optional project ID for isolation (None = default project)
    """
    try:
        # Security validation
        security_manager = get_mcp_security_manager()
        try:
            validation_result = security_manager.validate_mcp_request(
                project_id=project_id,
                operation="read",
                user_input=query
            )
            # Use sanitized query
            if validation_result.get('sanitized_input'):
                query = validation_result['sanitized_input']
        except MCPSecurityError as e:
            return {"success": False, "error": f"Security validation failed: {e}"}
        
        # Validate input
        if not conversation_id or not query:
            return {"success": False, "error": "conversation_id and query are required"}
        
        # Get database connection
        db_path = config.get_db_path()
        # Apply project scoping if available
        if validation_result.get('scoped_db_path'):
            db_path = validation_result['scoped_db_path']
        
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        # Get context using real service
        result = get_context_for_query(
            conn=conn,
            index_path=config.get_faiss_index_path(),
            conversation_id=conversation_id,
            query=query,
            top_k=top_k
        )
        
        # Close database connection
        close_db_connection(conn)
        
        # Add security context to result
        if isinstance(result, dict):
            result['_security_context'] = {
                "project_id": validation_result.get('project_id', 'default'),
                "validation_time_ms": validation_result.get('execution_time_ms', 0),
                "secure": True
            }
        
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
    source_tool: str | None = None,
    project_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Log chat message in LTMC with source tool tracking.
    
    Args:
        conversation_id: ID of the conversation
        role: Role of the message sender ('user', 'ai', 'tool', 'system')
        content: Message content
        agent_name: Name of the agent if applicable
        metadata: Optional metadata dictionary
        source_tool: Tool that generated this message (claude-code, cursor, vscode, etc.)
        project_id: Optional project ID for isolation (None = default project)
        
    Returns:
        Dictionary with success status and message ID
    """
    try:
        # Security validation
        security_manager = get_mcp_security_manager()
        try:
            validation_result = security_manager.validate_mcp_request(
                project_id=project_id,
                operation="write",
                user_input=content
            )
            # Use sanitized content
            if validation_result.get('sanitized_input'):
                content = validation_result['sanitized_input']
        except MCPSecurityError as e:
            return {"success": False, "error": f"Security validation failed: {e}"}
        
        # Validate input
        if not conversation_id or not role or not content:
            return {"success": False, "error": "conversation_id, role, and content are required"}
        
        # Get database connection
        db_path = config.get_db_path()
        # Apply project scoping if available
        if validation_result.get('scoped_db_path'):
            db_path = validation_result['scoped_db_path']
        
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
            source_tool=source_tool,
        )
        
        # Close database connection
        close_db_connection(conn)
        
        response = {"success": True, "message_id": int(message_id)}
        
        # Add security context
        response['_security_context'] = {
            "project_id": validation_result.get('project_id', 'default'),
            "validation_time_ms": validation_result.get('execution_time_ms', 0),
            "secure": True
        }
        
        return response
        
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
        if not documents:
            return {
                "success": True,
                "context": "",
                "token_count": 0,
                "documents_processed": 0
            }
        
        context_text = build_context_window(documents, max_tokens)
        token_count = len(context_text.split())  # Approximate token count
        
        return {
            "success": True,
            "context": context_text,
            "token_count": token_count,
            "documents_processed": len(documents),
            "max_tokens": max_tokens
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "context": "",
            "token_count": 0
        }


@mcp.tool()
def retrieve_by_type(query: str, doc_type: str, top_k: int = 5) -> Dict[str, Any]:
    """Retrieve documents by type."""
    try:
        results = retrieve_by_type_tool(query, doc_type, top_k)
        return {
            "success": True,
            "documents": results,
            "count": len(results)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def add_todo(title: str, description: str, priority: str = "medium", project_id: Optional[str] = None) -> Dict[str, Any]:
    """Add a new todo item with real database storage.
    
    Args:
        title: Todo title
        description: Todo description
        priority: Priority level (low, medium, high)
        project_id: Optional project ID for isolation (None = default project)
    """
    try:
        # Security validation
        security_manager = get_mcp_security_manager()
        try:
            validation_result = security_manager.validate_mcp_request(
                project_id=project_id,
                operation="write",
                user_input=f"{title} {description}"
            )
            # Use sanitized input
            if validation_result.get('sanitized_input'):
                sanitized_input = validation_result['sanitized_input']
                # Simple splitting approach - in production might need more sophisticated parsing
                words = sanitized_input.split()
                if len(words) >= 2:
                    title = words[0]
                    description = ' '.join(words[1:])
        except MCPSecurityError as e:
            return {"success": False, "error": f"Security validation failed: {e}"}
        
        # Validate input
        if not title or not description:
            return {"success": False, "error": "title and description are required"}
        
        # Get database connection
        db_path = config.get_db_path()
        # Apply project scoping if available
        if validation_result.get('scoped_db_path'):
            db_path = validation_result['scoped_db_path']
        
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
        
        response = {
            "success": True,
            "todo_id": todo_id,
            "message": "Todo added successfully"
        }
        
        # Add security context
        response['_security_context'] = {
            "project_id": validation_result.get('project_id', 'default'),
            "validation_time_ms": validation_result.get('execution_time_ms', 0),
            "secure": True
        }
        
        return response
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_todos(status: str = "all", limit: int = 10) -> Dict[str, Any]:
    """List todo items with real database query."""
    try:
        # Get database connection
        db_path = config.get_db_path()
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        # Query todos based on status
        cursor = conn.cursor()
        if status == "all":
            cursor.execute("SELECT * FROM Todos ORDER BY created_at DESC LIMIT ?", (limit,))
        elif status == "pending":
            cursor.execute(
                "SELECT * FROM Todos WHERE completed = 0 ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
        elif status == "completed":
            cursor.execute(
                "SELECT * FROM Todos WHERE completed = 1 ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
        else:
            cursor.execute("SELECT * FROM Todos ORDER BY created_at DESC LIMIT ?", (limit,))
        
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
        db_path = config.get_db_path()
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
def search_todos(query: str, limit: int = 10) -> Dict[str, Any]:
    """Search todos by title or description with real database search."""
    try:
        # Validate input
        if not query:
            return {"success": False, "error": "query is required"}
        
        # Get database connection
        db_path = config.get_db_path()
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        # Search todos
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM Todos WHERE title LIKE ? OR description LIKE ? ORDER BY created_at DESC LIMIT ?",
            (f"%{query}%", f"%{query}%", limit)
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
        db_path = config.get_db_path()
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        # Ensure ContextLinks table exists
        from ltms.database.context_linking import create_context_links_table
        create_context_links_table(conn)
        
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
        db_path = config.get_db_path()
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
        db_path = config.get_db_path()
        conn = get_db_connection(db_path)
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
        db_path = config.get_db_path()
        conn = get_db_connection(db_path)
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
        db_path = config.get_db_path()
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
        db_path = config.get_db_path()
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
    time_range_days: int = 30,
    patterns: List[str] = None
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
        db_path = config.get_db_path()
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


@mcp.tool()
def get_chats_by_tool(source_tool: str, limit: int = 100, conversation_id: str | None = None) -> Dict[str, Any]:
    """Get chat messages by source tool with optional conversation filtering.
    
    Args:
        source_tool: Tool identifier (claude-code, cursor, vscode, etc.)
        limit: Maximum number of messages to retrieve
        conversation_id: Optional conversation ID filter
        
    Returns:
        Dictionary with chat messages from specified source tool
    """
    try:
        # Validate input
        if not source_tool:
            return {"success": False, "error": "source_tool is required"}
        
        if limit <= 0 or limit > 1000:
            return {"success": False, "error": "limit must be between 1 and 1000"}
        
        # Get database connection
        db_path = config.get_db_path()
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        # Build query
        cursor = conn.cursor()
        query = "SELECT id, conversation_id, role, content, timestamp, agent_name, metadata, source_tool FROM ChatHistory WHERE source_tool = ?"
        params = [source_tool]
        
        if conversation_id:
            query += " AND conversation_id = ?"
            params.append(conversation_id)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        messages = []
        for row in rows:
            messages.append({
                "id": row[0],
                "conversation_id": row[1],
                "role": row[2],
                "content": row[3],
                "timestamp": row[4],
                "agent_name": row[5],
                "metadata": row[6],
                "source_tool": row[7]
            })
        
        # Close database connection
        close_db_connection(conn)
        
        return {
            "success": True,
            "messages": messages,
            "count": len(messages),
            "source_tool": source_tool
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_tool_identifiers() -> Dict[str, Any]:
    """List all known tool identifiers and their usage statistics.
    
    Returns:
        Dictionary with tool identifiers and usage counts
    """
    try:
        # Get database connection
        db_path = config.get_db_path()
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        # Query tool usage statistics
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                source_tool, 
                COUNT(*) as message_count,
                COUNT(DISTINCT conversation_id) as conversation_count,
                MIN(timestamp) as first_used,
                MAX(timestamp) as last_used
            FROM ChatHistory 
            WHERE source_tool IS NOT NULL 
            GROUP BY source_tool 
            ORDER BY message_count DESC
        """)
        rows = cursor.fetchall()
        
        tools = []
        total_messages = 0
        for row in rows:
            tool_info = {
                "identifier": row[0],
                "message_count": row[1],
                "conversation_count": row[2], 
                "first_used": row[3],
                "last_used": row[4],
                "status": "active" if row[1] > 0 else "inactive"
            }
            tools.append(tool_info)
            total_messages += row[1]
        
        # Standard tool identifiers (for validation)
        standard_tools = [
            "claude-code", "cursor", "vscode", "pycharm", "jupyter", 
            "vim", "emacs", "sublime", "atom", "nova", "zed", "copilot"
        ]
        
        # Close database connection
        close_db_connection(conn)
        
        return {
            "success": True,
            "tools": tools,
            "total_tools": len(tools),
            "total_messages": total_messages,
            "standard_identifiers": standard_tools
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_tool_conversations(source_tool: str, limit: int = 50) -> Dict[str, Any]:
    """Get unique conversations for a specific tool.
    
    Args:
        source_tool: Tool identifier
        limit: Maximum number of conversations to retrieve
        
    Returns:
        Dictionary with conversation summaries for the tool
    """
    try:
        # Validate input
        if not source_tool:
            return {"success": False, "error": "source_tool is required"}
        
        if limit <= 0 or limit > 200:
            return {"success": False, "error": "limit must be between 1 and 200"}
        
        # Get database connection
        db_path = config.get_db_path()
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        # Query conversations for the tool
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                conversation_id,
                COUNT(*) as message_count,
                MIN(timestamp) as started_at,
                MAX(timestamp) as last_activity,
                GROUP_CONCAT(DISTINCT role) as roles
            FROM ChatHistory 
            WHERE source_tool = ?
            GROUP BY conversation_id
            ORDER BY last_activity DESC
            LIMIT ?
        """, (source_tool, limit))
        rows = cursor.fetchall()
        
        conversations = []
        for row in rows:
            conversations.append({
                "conversation_id": row[0],
                "message_count": row[1],
                "started_at": row[2],
                "last_activity": row[3],
                "roles": row[4].split(",") if row[4] else []
            })
        
        # Close database connection  
        close_db_connection(conn)
        
        return {
            "success": True,
            "conversations": conversations,
            "count": len(conversations),
            "source_tool": source_tool
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def redis_cache_stats() -> Dict[str, Any]:
    """Get Redis cache statistics and health status.
    
    Returns:
        Dictionary with Redis cache statistics and connection health
    """
    try:
        cache_service = await get_cache_service()
        stats = await cache_service.get_cache_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        return {"success": False, "error": str(e), "stats": {"connected": False, "error": str(e)}}


@mcp.tool()
async def redis_flush_cache(cache_type: str = "all") -> Dict[str, Any]:
    """Flush Redis cache entries.
    
    Args:
        cache_type: Type of cache to flush ("all", "embeddings", "queries")
        
    Returns:
        Dictionary with flush results
    """
    try:
        cache_service = await get_cache_service()
        
        if cache_type == "all":
            # Flush all LTMC cache entries
            embedding_count = await cache_service.invalidate_cache("ltmc:embedding:*")
            query_count = await cache_service.invalidate_cache("ltmc:query:*")
            chunk_count = await cache_service.invalidate_cache("ltmc:chunk:*")
            resource_count = await cache_service.invalidate_cache("ltmc:resource:*")
            
            return {
                "success": True,
                "result": {
                    "flushed_embeddings": embedding_count,
                    "flushed_queries": query_count,
                    "flushed_chunks": chunk_count,
                    "flushed_resources": resource_count,
                    "total_flushed": embedding_count + query_count + chunk_count + resource_count
                }
            }
        elif cache_type == "embeddings":
            count = await cache_service.invalidate_cache("ltmc:embedding:*")
            return {"success": True, "result": {"flushed_embeddings": count}}
        elif cache_type == "queries":
            count = await cache_service.invalidate_cache("ltmc:query:*")
            return {"success": True, "result": {"flushed_queries": count}}
        else:
            return {"success": False, "error": f"Unknown cache_type: {cache_type}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def redis_health_check() -> Dict[str, Any]:
    """Check Redis connection health and connectivity.
    
    Returns:
        Dictionary with health check results
    """
    import asyncio
    
    async def check_health():
        try:
            redis_manager = await get_redis_manager()
            is_healthy = await redis_manager.health_check()
            
            return {
                "healthy": is_healthy,
                "connected": redis_manager.is_connected,
                "host": redis_manager.host,
                "port": redis_manager.port,
                "db": redis_manager.db
            }
        except Exception as e:
            return {
                "healthy": False,
                "connected": False,
                "error": str(e)
            }
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, check_health())
                return {"success": True, "health": future.result()}
        else:
            return {"success": True, "health": asyncio.run(check_health())}
    except Exception as e:
        return {"success": False, "error": str(e)}


# The FastMCP server is now ready to use. Expose convenience async wrappers and stdio stub

import asyncio


def run_stdio():
    """Run the LTMC MCP server with stdio transport."""
    mcp.run(transport="stdio")


async def _store_memory_proxy(file_name: str, content: str, resource_type: str = "document") -> Dict[str, Any]:
    return store_memory(file_name, content, resource_type)


async def _retrieve_memory_proxy(conversation_id: str, query: str, top_k: int = 3) -> Dict[str, Any]:
    return retrieve_memory(conversation_id, query, top_k)


# MCP Security Management Tools
@mcp.tool()
def register_project(project_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Register a new project for multi-tenant isolation.
    
    Args:
        project_id: Unique project identifier
        config: Project configuration with allowed_paths, database_prefix, redis_namespace, neo4j_label
        
    Returns:
        Registration result with success status
    """
    try:
        security_manager = get_mcp_security_manager()
        return security_manager.register_project(project_id, config)
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_security_context(project_id: Optional[str] = None) -> Dict[str, Any]:
    """Get security context for a project.
    
    Args:
        project_id: Project identifier (None for default)
        
    Returns:
        Security context with project info and performance stats
    """
    try:
        security_manager = get_mcp_security_manager()
        return {
            "success": True,
            "context": security_manager.get_security_context(project_id)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_projects() -> Dict[str, Any]:
    """List all registered projects.
    
    Returns:
        List of project IDs and their basic information
    """
    try:
        security_manager = get_mcp_security_manager()
        project_ids = security_manager.project_isolation.list_projects()
        
        projects_info = []
        for pid in project_ids:
            config = security_manager.project_isolation.get_project_config(pid)
            if config:
                projects_info.append({
                    "project_id": pid,
                    "name": config.name,
                    "database_prefix": config.database_prefix,
                    "redis_namespace": config.redis_namespace,
                    "neo4j_label": config.neo4j_label
                })
        
        return {
            "success": True,
            "projects": projects_info,
            "count": len(projects_info)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_connection_pool_metrics() -> Dict[str, Any]:
    """Get connection pool performance metrics and health status.
    
    Returns:
        Dictionary with metrics for all connection pools (database, Redis, Neo4j)
    """
    try:
        all_metrics = connection_manager.get_all_metrics()
        return {
            "success": True,
            "metrics": all_metrics,
            "pool_health": {
                "database_healthy": all_metrics["database"]["creation_errors"] == 0,
                "redis_healthy": "redis" in all_metrics and all_metrics["redis"].get("creation_errors", 0) == 0,
                "neo4j_healthy": all_metrics["neo4j"]["creation_errors"] == 0,
                "overall_healthy": all([
                    all_metrics["database"]["creation_errors"] == 0,
                    all_metrics["neo4j"]["creation_errors"] == 0
                ])
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_security_statistics() -> Dict[str, Any]:
    """Get comprehensive security and performance statistics.
    
    Returns:
        Security statistics including validation metrics and performance data
    """
    try:
        security_manager = get_mcp_security_manager()
        
        # Get performance metrics from both components
        isolation_metrics = security_manager.project_isolation.get_performance_metrics()
        path_security_stats = security_manager.path_validator.get_security_statistics()
        validation_stats = security_manager.validation_stats.copy()
        
        return {
            "success": True,
            "statistics": {
                "project_isolation": isolation_metrics,
                "path_security": path_security_stats,
                "validation_performance": validation_stats,
                "security_features": {
                    "project_isolation_enabled": True,
                    "path_validation_enabled": True,
                    "input_sanitization_enabled": True,
                    "performance_monitoring_enabled": True
                }
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==============================================================================
# Phase 3 Component 2: Documentation Synchronization MCP Tools
# ==============================================================================


@mcp.tool()
def sync_documentation_with_code_tool(
    file_path: str,
    project_id: str,
    force_update: bool = False
) -> Dict[str, Any]:
    """
    Synchronize documentation with code changes using dual-source validation.
    
    This tool performs real-time synchronization between Neo4j blueprints and actual code,
    updating documentation automatically when changes are detected.
    
    Args:
        file_path: Path to Python file to sync
        project_id: Project identifier for isolation
        force_update: Force update even if no changes detected
        
    Returns:
        Dict with synchronization results including performance metrics
    """
    try:
        from ltms.tools.documentation_sync_tools import sync_documentation_with_code
        return sync_documentation_with_code(file_path, project_id, force_update)
    except Exception as e:
        return {"success": False, "error": f"Documentation sync failed: {e}"}


@mcp.tool()
def validate_documentation_consistency_tool(
    file_path: str,
    project_id: str
) -> Dict[str, Any]:
    """
    Validate consistency between documentation and code with >90% accuracy target.
    
    This tool performs dual-source validation between Neo4j blueprints and actual code
    to calculate detailed consistency scores and identify discrepancies.
    
    Args:
        file_path: Path to Python file to validate
        project_id: Project identifier for isolation
        
    Returns:
        Dict with consistency validation results and scoring details
    """
    try:
        from ltms.tools.documentation_sync_tools import validate_documentation_consistency
        return validate_documentation_consistency(file_path, project_id)
    except Exception as e:
        return {"success": False, "error": f"Consistency validation failed: {e}"}


@mcp.tool()
def detect_documentation_drift_tool(
    file_path: str,
    project_id: str,
    time_threshold_hours: Optional[int] = 24
) -> Dict[str, Any]:
    """
    Detect documentation drift from recent code changes.
    
    This tool analyzes recent changes to detect when documentation may be out of sync
    with code modifications, helping maintain documentation currency.
    
    Args:
        file_path: Path to Python file to analyze
        project_id: Project identifier for isolation
        time_threshold_hours: Hours to look back for changes
        
    Returns:
        Dict with drift detection results and affected sections
    """
    try:
        from ltms.tools.documentation_sync_tools import detect_documentation_drift
        return detect_documentation_drift(file_path, project_id, time_threshold_hours)
    except Exception as e:
        return {"success": False, "error": f"Drift detection failed: {e}"}


@mcp.tool()
def update_documentation_from_blueprint_tool(
    blueprint_id: str,
    project_id: str,
    sections: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Update documentation from Neo4j blueprint changes.
    
    This tool updates documentation based on changes in Neo4j blueprints,
    ensuring documentation stays synchronized with architectural changes.
    
    Args:
        blueprint_id: Blueprint identifier in Neo4j
        project_id: Project identifier for isolation
        sections: Specific sections to update (optional)
        
    Returns:
        Dict with documentation update results and performance metrics
    """
    try:
        from ltms.tools.documentation_sync_tools import update_documentation_from_blueprint
        return update_documentation_from_blueprint(blueprint_id, project_id, sections)
    except Exception as e:
        return {"success": False, "error": f"Blueprint documentation update failed: {e}"}


@mcp.tool()
def get_documentation_consistency_score_tool(
    file_path: str,
    project_id: str,
    detailed_analysis: bool = False
) -> Dict[str, Any]:
    """
    Get detailed consistency score between documentation and code with <5ms performance.
    
    This tool provides comprehensive consistency analysis including node-level and
    relationship-level scoring with detailed metrics and recommendations.
    
    Args:
        file_path: Path to Python file to analyze
        project_id: Project identifier for isolation
        detailed_analysis: Include detailed node-by-node analysis
        
    Returns:
        Dict with detailed consistency score and quality indicators
    """
    try:
        from ltms.tools.documentation_sync_tools import get_documentation_consistency_score
        return get_documentation_consistency_score(file_path, project_id, detailed_analysis)
    except Exception as e:
        return {"success": False, "error": f"Consistency scoring failed: {e}"}


@mcp.tool()
def start_real_time_documentation_sync_tool(
    file_paths: List[str],
    project_id: str,
    sync_interval_ms: int = 100
) -> Dict[str, Any]:
    """
    Start real-time documentation synchronization monitoring with <100ms latency.
    
    This tool enables continuous monitoring and synchronization of documentation
    with code changes, providing real-time updates when files are modified.
    
    Args:
        file_paths: List of file paths to monitor
        project_id: Project identifier for isolation
        sync_interval_ms: Monitoring interval in milliseconds
        
    Returns:
        Dict with real-time sync startup results and monitoring configuration
    """
    try:
        from ltms.tools.documentation_sync_tools import start_real_time_documentation_sync
        return start_real_time_documentation_sync(file_paths, project_id, sync_interval_ms)
    except Exception as e:
        return {"success": False, "error": f"Real-time sync startup failed: {e}"}


@mcp.tool()
def get_documentation_sync_status_tool(
    project_id: str,
    include_pending_changes: bool = True
) -> Dict[str, Any]:
    """
    Get comprehensive documentation synchronization status for a project.
    
    This tool provides detailed status information about documentation synchronization
    activities, including monitoring status and pending changes.
    
    Args:
        project_id: Project identifier for isolation
        include_pending_changes: Include information about pending changes
        
    Returns:
        Dict with comprehensive sync status and monitoring information
    """
    try:
        from ltms.tools.documentation_sync_tools import get_documentation_sync_status
        return get_documentation_sync_status(project_id, include_pending_changes)
    except Exception as e:
        return {"success": False, "error": f"Sync status retrieval failed: {e}"}


# Redis tool proxy functions for async handling
async def _redis_health_check_proxy() -> Dict[str, Any]:
    return await redis_health_check()


async def _redis_cache_stats_proxy() -> Dict[str, Any]:
    return await redis_cache_stats()


async def _redis_flush_cache_proxy(cache_type: str = "all") -> Dict[str, Any]:
    return await redis_flush_cache(cache_type)


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


# Phase 3 Component 3: Advanced Markdown Generation Tools

@mcp.tool()
async def generate_advanced_documentation(
    file_path: str,
    project_id: str,
    template_type: str = "api_docs",
    output_path: str = None,
    variables: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Generate advanced documentation using intelligent templates."""
    try:
        from ltms.tools.advanced_markdown_tools import generate_advanced_documentation
        return await generate_advanced_documentation(file_path, project_id, template_type, output_path, variables)
    except Exception as e:
        return {"success": False, "error": f"Advanced documentation generation failed: {e}"}


@mcp.tool()
async def create_documentation_template(
    template_name: str,
    template_content: str,
    template_type: str,
    project_id: str,
    author: str = "LTMC System",
    description: str = None,
    version: str = "1.0.0",
    tags: List[str] = None
) -> Dict[str, Any]:
    """Create custom documentation template."""
    try:
        from ltms.tools.advanced_markdown_tools import create_documentation_template
        return await create_documentation_template(
            template_name, template_content, template_type, project_id, 
            author, description, version, tags
        )
    except Exception as e:
        return {"success": False, "error": f"Template creation failed: {e}"}


@mcp.tool()
async def maintain_documentation_integrity(
    project_id: str,
    fix_broken_links: bool = False,
    update_index: bool = True,
    validate_cross_references: bool = True
) -> Dict[str, Any]:
    """Perform comprehensive documentation maintenance."""
    try:
        from ltms.tools.advanced_markdown_tools import maintain_documentation_integrity
        return await maintain_documentation_integrity(
            project_id, fix_broken_links, update_index, validate_cross_references
        )
    except Exception as e:
        return {"success": False, "error": f"Documentation maintenance failed: {e}"}


@mcp.tool()
async def commit_documentation_changes(
    file_paths: List[str],
    project_id: str,
    commit_message: str = None,
    create_tag: bool = False,
    tag_name: str = None
) -> Dict[str, Any]:
    """Commit documentation changes to version control."""
    try:
        from ltms.tools.advanced_markdown_tools import commit_documentation_changes
        return await commit_documentation_changes(
            file_paths, project_id, commit_message, create_tag, tag_name
        )
    except Exception as e:
        return {"success": False, "error": f"Documentation commit failed: {e}"}


@mcp.tool()
async def generate_documentation_changelog(
    project_id: str,
    since_date: str = None,
    output_format: str = "markdown",
    include_stats: bool = True
) -> Dict[str, Any]:
    """Generate changelog for documentation changes."""
    try:
        from ltms.tools.advanced_markdown_tools import generate_documentation_changelog
        return await generate_documentation_changelog(
            project_id, since_date, output_format, include_stats
        )
    except Exception as e:
        return {"success": False, "error": f"Changelog generation failed: {e}"}


@mcp.tool()
async def validate_template_syntax(
    template_content: str,
    template_variables: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Validate Jinja2 template syntax and test rendering."""
    try:
        from ltms.tools.advanced_markdown_tools import validate_template_syntax
        return await validate_template_syntax(template_content, template_variables)
    except Exception as e:
        return {"success": False, "error": f"Template validation failed: {e}"}


# Phase 3 Component 4: Consistency Validation & Enforcement Tools

@mcp.tool()
async def validate_blueprint_consistency(
    file_path: str,
    project_id: str,
    validation_level: str = "comprehensive",
    include_recommendations: bool = True,
    cache_results: bool = True
) -> Dict[str, Any]:
    """Validate consistency between blueprint and code structure."""
    try:
        from ltms.tools.consistency_validation_tools import validate_blueprint_consistency
        return await validate_blueprint_consistency(
            file_path, project_id, validation_level, include_recommendations, cache_results
        )
    except Exception as e:
        return {"success": False, "error": f"Blueprint consistency validation failed: {e}"}


@mcp.tool()
async def analyze_change_impact(
    file_path: str,
    project_id: str,
    change_type: str,
    changed_content: str = None,
    block_on_critical: bool = True
) -> Dict[str, Any]:
    """Analyze impact of code changes on blueprint consistency."""
    try:
        from ltms.tools.consistency_validation_tools import analyze_change_impact
        return await analyze_change_impact(
            file_path, project_id, change_type, changed_content, block_on_critical
        )
    except Exception as e:
        return {"success": False, "error": f"Change impact analysis failed: {e}"}


@mcp.tool()
async def enforce_consistency_rules(
    file_path: str,
    project_id: str,
    enforcement_mode: str = "auto",
    dry_run: bool = False,
    severity_threshold: str = "medium"
) -> Dict[str, Any]:
    """Enforce consistency rules and apply automated fixes."""
    try:
        from ltms.tools.consistency_validation_tools import enforce_consistency_rules
        return await enforce_consistency_rules(
            file_path, project_id, enforcement_mode, dry_run, severity_threshold
        )
    except Exception as e:
        return {"success": False, "error": f"Consistency enforcement failed: {e}"}


@mcp.tool()
async def detect_consistency_violations(
    file_path: str,
    project_id: str,
    violation_types: List[str] = None,
    include_auto_fixable: bool = True,
    group_by_severity: bool = True
) -> Dict[str, Any]:
    """Detect specific types of consistency violations."""
    try:
        from ltms.tools.consistency_validation_tools import detect_consistency_violations
        return await detect_consistency_violations(
            file_path, project_id, violation_types, include_auto_fixable, group_by_severity
        )
    except Exception as e:
        return {"success": False, "error": f"Violation detection failed: {e}"}


@mcp.tool()
async def generate_consistency_report(
    project_id: str,
    file_paths: List[str] = None,
    include_statistics: bool = True,
    include_recommendations: bool = True,
    output_format: str = "json"
) -> Dict[str, Any]:
    """Generate comprehensive consistency report for project or files."""
    try:
        from ltms.tools.consistency_validation_tools import generate_consistency_report
        return await generate_consistency_report(
            project_id, file_paths, include_statistics, include_recommendations, output_format
        )
    except Exception as e:
        return {"success": False, "error": f"Consistency report generation failed: {e}"}


@mcp.tool()
async def configure_enforcement_rules(
    project_id: str,
    rule_configuration: Dict[str, Any],
    apply_immediately: bool = False
) -> Dict[str, Any]:
    """Configure consistency enforcement rules for a project."""
    try:
        from ltms.tools.consistency_validation_tools import configure_enforcement_rules
        return await configure_enforcement_rules(
            project_id, rule_configuration, apply_immediately
        )
    except Exception as e:
        return {"success": False, "error": f"Rule configuration failed: {e}"}


# Attach proxies to mcp instance for tests that access them as attributes
mcp.run_stdio = run_stdio  # type: ignore[attr-defined]
mcp.store_memory = _store_memory_proxy  # type: ignore[attr-defined]
mcp.retrieve_memory = _retrieve_memory_proxy  # type: ignore[attr-defined]
mcp.log_chat = _log_chat_proxy  # type: ignore[attr-defined]
mcp.ask_with_context = _ask_with_context_proxy  # type: ignore[attr-defined]
mcp.route_query = _route_query_proxy  # type: ignore[attr-defined]
mcp.build_context = _build_context_proxy  # type: ignore[attr-defined]
mcp.retrieve_by_type = _retrieve_by_type_proxy  # type: ignore[attr-defined]