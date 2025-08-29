"""Memory service for LTMC document storage and retrieval."""

import sqlite3
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
from pathlib import Path

from ltms.config.json_config_loader import get_config
from ltms.database.connection import get_db_connection, close_db_connection
from ltms.database.dal import create_resource, get_next_vector_id, create_resource_chunks
from ltms.database.schema import create_tables
from ltms.services.embedding_service import create_embedding_model, encode_text
from ltms.services.chunking_service import create_chunker, split_text_into_chunks
from ltms.vector_store.faiss_store import create_faiss_index, save_index, load_index, search_vectors, add_vectors

logger = logging.getLogger(__name__)


def store_memory(file_name: str, content: str, resource_type: str = "document") -> Dict[str, Any]:
    """Store memory/document in LTMC with chunking and vector indexing.
    
    This function implements the complete document ingestion pipeline:
    1. Store document metadata in Resources table
    2. Chunk the document content
    3. Generate embeddings for chunks
    4. Store chunks in ResourceChunks table
    5. Update FAISS index with new embeddings
    
    Args:
        file_name: Name of the file being stored
        content: Full text content of the document
        resource_type: Type of resource (default: "document")
        
    Returns:
        Dictionary with success status, resource_id, and chunk count
    """
    if not file_name or not content:
        return {
            'success': False,
            'error': 'file_name and content are required'
        }
    
    conn = None
    try:
        # Get database connection
        config = get_config()
        db_path = config.get_db_path()
        conn = get_db_connection(db_path)
        
        # Ensure tables exist
        create_tables(conn)
        
        # Step 1: Create resource record
        created_at = datetime.now(timezone.utc).isoformat()
        resource_id = create_resource(conn, file_name, resource_type, created_at)
        
        # Step 2: Chunk the content
        chunker = create_chunker(chunk_size=500, chunk_overlap=50)
        chunks = split_text_into_chunks(chunker, content)
        
        if not chunks:
            return {
                'success': False,
                'error': 'No chunks generated from content'
            }
        
        # Step 3: Generate embeddings and prepare chunk data
        model = create_embedding_model("all-MiniLM-L6-v2")
        chunks_data = []
        embeddings = []
        
        for chunk in chunks:
            # Generate embedding
            embedding = encode_text(model, chunk)
            embeddings.append(embedding)
            
            # Get sequential vector ID
            vector_id = get_next_vector_id(conn)
            chunks_data.append((chunk, vector_id))
        
        # Step 4: Store chunks in database
        chunk_ids = create_resource_chunks(conn, resource_id, chunks_data)
        
        # Step 5: Update FAISS index using optimized service
        from ltms.services.optimized_faiss_service import get_optimized_faiss_service
        
        import numpy as np
        embeddings_array = np.array(embeddings)
        vector_ids = [chunk_data[1] for chunk_data in chunks_data]
        
        # Use optimized FAISS service for immediate indexing
        faiss_service = get_optimized_faiss_service()
        faiss_result = faiss_service.add_vectors_optimized(embeddings_array, vector_ids)
        
        # Log performance metrics
        if faiss_result.get('success'):
            logger.info(f"FAISS indexing: {faiss_result['vectors_added']} vectors added in {faiss_result['add_time_ms']:.1f}ms")
            if faiss_result.get('immediate_search_validation', {}).get('validation_passed'):
                logger.info("✅ Immediate search validation passed - newly stored data is searchable")
            else:
                logger.warning("⚠️ Immediate search validation failed - potential indexing delay")
        
        return {
            'success': True,
            'resource_id': resource_id,
            'chunks_created': len(chunk_ids),
            'file_name': file_name,
            'message': f'Stored {len(chunk_ids)} chunks for {file_name}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        if conn:
            close_db_connection(conn)


def retrieve_memory(conversation_id: str, query: str, top_k: int = 10) -> Dict[str, Any]:
    """Retrieve relevant memory/documents from LTMC using semantic search.
    
    This function implements the retrieval pipeline:
    1. Generate query embedding
    2. Search FAISS index for similar chunks
    3. Retrieve chunk details from database
    4. Log the query in chat history
    5. Return ranked results with metadata
    
    Args:
        conversation_id: ID of the conversation (used for chat logging)
        query: Search query text
        top_k: Maximum number of chunks to retrieve
        
    Returns:
        Dictionary with success status, retrieved chunks, and context
    """
    if not query:
        return {
            'success': False,
            'error': 'query is required'
        }
    
    conn = None
    try:
        # Get database connection
        config = get_config()
        db_path = config.get_db_path()
        conn = get_db_connection(db_path)
        
        # Step 1: Generate query embedding
        model = create_embedding_model("all-MiniLM-L6-v2")
        query_embedding = encode_text(model, query)
        
        # Step 2: Search FAISS index using optimized service
        from ltms.services.optimized_faiss_service import get_optimized_faiss_service
        
        faiss_service = get_optimized_faiss_service()
        search_result = faiss_service.search_vectors_optimized(query_embedding, top_k)
        
        if not search_result.get('success'):
            return {
                'success': False,
                'error': f"FAISS search failed: {search_result.get('error', 'Unknown error')}"
            }
        
        distances = search_result['distances']
        indices = search_result['indices']
        
        if search_result['found_count'] == 0:
            return {
                'success': True,
                'retrieved_chunks': [],
                'context': "",
                'message': 'No similar chunks found',
                'search_time_ms': search_result.get('search_time_ms', 0)
            }
        
        # Step 3: Retrieve chunk details from database
        vector_ids = indices[0].tolist()
        
        # Get chunks by vector IDs
        cursor = conn.cursor()
        placeholders = ','.join(['?' for _ in vector_ids])
        cursor.execute(
            f"""
            SELECT rc.id, rc.resource_id, rc.chunk_text, rc.vector_id, r.file_name, r.type
            FROM resource_chunks rc
            JOIN resources r ON rc.resource_id = r.id
            WHERE rc.vector_id IN ({placeholders})
            """,
            vector_ids
        )
        
        results = cursor.fetchall()
        
        # Step 4: Build response with similarity scores
        retrieved_chunks = []
        context_parts = []
        
        for i, (chunk_id, resource_id, chunk_text, vector_id, file_name, resource_type) in enumerate(results):
            # Calculate similarity score (inverse of distance)
            distance = float(distances[0][i])
            score = 1.0 / (1.0 + distance)
            
            chunk_info = {
                'chunk_id': chunk_id,
                'resource_id': resource_id,
                'file_name': file_name,
                'resource_type': resource_type,
                'chunk_text': chunk_text,
                'score': score,
                'vector_id': vector_id
            }
            retrieved_chunks.append(chunk_info)
            context_parts.append(f"[{file_name}] {chunk_text}")
        
        # Step 5: Log the query if conversation_id provided
        if conversation_id:
            # Import here to avoid circular imports
            from ltms.services.context_service import log_chat_message
            log_chat_message(
                conn, 
                conversation_id, 
                "user", 
                query, 
                source_tool="memory_retrieval"
            )
        
        context = "\n\n".join(context_parts)
        
        return {
            'success': True,
            'retrieved_chunks': retrieved_chunks,
            'context': context,
            'query': query,
            'total_found': len(retrieved_chunks)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        if conn:
            close_db_connection(conn)


def search_memory_by_type(query: str, resource_type: str, top_k: int = 5) -> Dict[str, Any]:
    """Search memory by resource type.
    
    Args:
        query: Search query text
        resource_type: Type of resource to search for
        top_k: Maximum number of results to return
        
    Returns:
        Dictionary with search results filtered by type
    """
    if not query or not resource_type:
        return {
            'success': False,
            'error': 'query and resource_type are required'
        }
    
    conn = None
    try:
        # Get database connection
        config = get_config()
        db_path = config.get_db_path()
        conn = get_db_connection(db_path)
        
        # Step 1: Generate query embedding
        model = create_embedding_model("all-MiniLM-L6-v2")
        query_embedding = encode_text(model, query)
        
        # Step 2: Search FAISS index using optimized service
        from ltms.services.optimized_faiss_service import get_optimized_faiss_service
        
        faiss_service = get_optimized_faiss_service()
        search_result = faiss_service.search_vectors_optimized(query_embedding, top_k * 2)  # Get more to filter by type
        
        if not search_result.get('success'):
            return {
                'success': False,
                'error': f"FAISS search failed: {search_result.get('error', 'Unknown error')}"
            }
        
        distances = search_result['distances']
        indices = search_result['indices']
        
        if search_result['found_count'] == 0:
            return {
                'success': True,
                'retrieved_chunks': [],
                'message': 'No similar chunks found',
                'search_time_ms': search_result.get('search_time_ms', 0)
            }
        
        # Step 3: Filter by resource type
        vector_ids = indices[0].tolist()
        
        cursor = conn.cursor()
        placeholders = ','.join(['?' for _ in vector_ids])
        cursor.execute(
            f"""
            SELECT rc.id, rc.resource_id, rc.chunk_text, rc.vector_id, r.file_name, r.type
            FROM resource_chunks rc
            JOIN resources r ON rc.resource_id = r.id
            WHERE rc.vector_id IN ({placeholders}) AND r.type = ?
            LIMIT ?
            """,
            vector_ids + [resource_type, top_k]
        )
        
        results = cursor.fetchall()
        
        # Step 4: Build filtered response
        retrieved_chunks = []
        
        for i, (chunk_id, resource_id, chunk_text, vector_id, file_name, r_type) in enumerate(results):
            # Find corresponding distance
            vector_index = vector_ids.index(vector_id) if vector_id in vector_ids else 0
            distance = float(distances[0][vector_index])
            score = 1.0 / (1.0 + distance)
            
            chunk_info = {
                'chunk_id': chunk_id,
                'resource_id': resource_id,
                'file_name': file_name,
                'resource_type': r_type,
                'chunk_text': chunk_text,
                'score': score,
                'vector_id': vector_id
            }
            retrieved_chunks.append(chunk_info)
        
        return {
            'success': True,
            'retrieved_chunks': retrieved_chunks,
            'query': query,
            'resource_type': resource_type,
            'total_found': len(retrieved_chunks)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        if conn:
            close_db_connection(conn)