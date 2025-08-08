"""Context service for LTMC retrieval and chat history."""

from datetime import datetime
from typing import Dict, Any, List
from ltms.database.dal import get_chunks_by_vector_ids
from ltms.services.embedding_service import create_embedding_model, encode_text
from ltms.vector_store.faiss_store import load_index, search_vectors


def get_context_for_query(
    conn,
    index_path: str,
    conversation_id: str,
    query: str,
    top_k: int
) -> Dict[str, Any]:
    """Get relevant context for a query.
    
    This function implements the retrieval pipeline:
    1. Embed the query
    2. Search for similar chunks in the vector index
    3. Retrieve the full text of the chunks
    4. Log the query in chat history
    5. Create context links
    
    Args:
        conn: Database connection
        index_path: Path to the FAISS index file
        conversation_id: ID of the conversation
        query: User's query text
        top_k: Number of similar chunks to retrieve
        
    Returns:
        Dictionary with context and retrieved chunks information
    """
    try:
        # Step 1: Embed the query
        model = create_embedding_model("all-MiniLM-L6-v2")
        query_embedding = encode_text(model, query)
        
        # Step 2: Search for similar chunks
        index = load_index(index_path, dimension=384)
        distances, indices = search_vectors(index, query_embedding, top_k)
        
        if len(indices[0]) == 0:
            # No similar chunks found
            return {
                'success': True,
                'context': "",
                'retrieved_chunks': []
            }
        
        # Step 3: Retrieve chunk details from database
        vector_ids = indices[0].tolist()
        chunks = get_chunks_by_vector_ids(conn, vector_ids)
        
        # Step 4: Log the query in chat history
        message_id = log_chat_message(conn, conversation_id, "user", query)
        
        # Step 5: Create context links
        chunk_ids = [chunk['chunk_id'] for chunk in chunks]
        create_context_links(conn, message_id, chunk_ids)
        
        # Step 6: Assemble context
        context_parts = []
        retrieved_chunks = []
        
        for i, chunk in enumerate(chunks):
            context_parts.append(chunk['chunk_text'])
            
            # Get file name for the chunk
            cursor = conn.cursor()
            cursor.execute(
                "SELECT file_name FROM Resources WHERE id = ?",
                (chunk['resource_id'],)
            )
            file_name = cursor.fetchone()[0]
            
            # Calculate similarity score (inverse of distance)
            distance = float(distances[0][i])  # Convert numpy.float32 to Python float
            score = 1.0 / (1.0 + distance)  # Convert distance to similarity score
            
            retrieved_chunks.append({
                'chunk_id': chunk['chunk_id'],
                'resource_id': chunk['resource_id'],
                'file_name': file_name,
                'score': float(score)  # Ensure it's a Python float
            })
        
        context = "\n\n".join(context_parts)
        
        return {
            'success': True,
            'context': context,
            'retrieved_chunks': retrieved_chunks
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def log_chat_message(
    conn,
    conversation_id: str,
    role: str,
    content: str,
    agent_name: str | None = None,
    metadata: dict | None = None,
    source_tool: str | None = None,
) -> int:
    """Log a chat message in the database.
    
    Args:
        conn: Database connection
        conversation_id: ID of the conversation
        role: Role of the message sender ('user' or 'ai')
        content: Message content
        agent_name: Name of the agent if applicable
        metadata: Optional metadata dictionary
        source_tool: Tool that generated this message (claude-code, cursor, etc.)
        
    Returns:
        ID of the created message
    """
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    
    meta_json = None
    try:
        import json as _json
        if metadata is not None:
            meta_json = _json.dumps(metadata)
    except Exception:
        meta_json = None

    cursor.execute(
        (
            "INSERT INTO ChatHistory (conversation_id, role, content, timestamp, "
            "agent_name, metadata, source_tool) VALUES (?, ?, ?, ?, ?, ?, ?)"
        ),
        (conversation_id, role, content, timestamp, agent_name, meta_json, source_tool),
    )
    conn.commit()
    
    return cursor.lastrowid


def create_context_links(
    conn,
    message_id: int,
    chunk_ids: List[int]
) -> Dict[str, Any]:
    """Create context links between a message and chunks.
    
    Args:
        conn: Database connection
        message_id: ID of the chat message
        chunk_ids: List of chunk IDs used as context
        
    Returns:
        Dictionary with success status and number of links created
    """
    try:
        cursor = conn.cursor()
        links_created = 0
        
        for chunk_id in chunk_ids:
            cursor.execute(
                "INSERT INTO ContextLinks (message_id, chunk_id) VALUES (?, ?)",
                (message_id, chunk_id)
            )
            links_created += 1
        
        conn.commit()
        
        return {
            'success': True,
            'links_created': links_created
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
