"""Resource service for LTMC resource ingestion pipeline."""

from datetime import datetime
from typing import Dict, Any, Optional
from ltms.database.dal import create_resource, create_resource_chunks, get_next_vector_id
from ltms.services.chunking_service import create_chunker, split_text_into_chunks
from ltms.services.embedding_service import create_embedding_model, encode_texts
from ltms.vector_store.faiss_store import add_vectors, save_index, load_index


def add_resource(
    conn,
    index_path: str,
    file_name: str,
    resource_type: str,
    content: str
) -> Dict[str, Any]:
    """Add a new resource to the system.
    
    This function orchestrates the complete ingestion pipeline:
    1. Chunks the text into semantically coherent pieces
    2. Generates embeddings for each chunk
    3. Stores the resource and chunks in the database
    4. Adds the embeddings to the vector index
    
    Args:
        conn: Database connection
        index_path: Path to the FAISS index file
        file_name: Name of the file
        resource_type: Type of resource (e.g., 'document', 'code')
        content: Text content of the resource
        
    Returns:
        Dictionary with success status, resource_id, and chunk_count
    """
    try:
        # Step 1: Create resource in database
        created_at = datetime.now().isoformat()
        resource_id = create_resource(conn, file_name, resource_type, created_at)
        
        # Step 2: Chunk the text
        chunker = create_chunker(chunk_size=512, chunk_overlap=50)
        chunks = split_text_into_chunks(chunker, content)
        
        if not chunks:
            # No chunks created (empty content)
            return {
                'success': True,
                'resource_id': resource_id,
                'chunk_count': 0
            }
        
        # Step 3: Generate embeddings
        model = create_embedding_model("all-MiniLM-L6-v2")
        embeddings = encode_texts(model, chunks)
        
        # Step 4: Generate sequential vector IDs using database sequence
        # This prevents UNIQUE constraint violations
        vector_ids = [get_next_vector_id(conn) for _ in range(len(chunks))]
        
        # Step 5: Store chunks in database
        chunks_data = list(zip(chunks, vector_ids))
        create_resource_chunks(conn, resource_id, chunks_data)
        
        # Step 6: Add embeddings to vector index
        index = load_index(index_path, dimension=384)
        add_vectors(index, embeddings, vector_ids)
        save_index(index, index_path)
        
        return {
            'success': True,
            'resource_id': resource_id,
            'chunk_count': len(chunks)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def store_summary(
    conn,
    doc_id: Optional[str],
    summary_text: str,
    model: Optional[str] = None,
    resource_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Store an external summary for a document or resource.

    Either doc_id or resource_id must be provided.
    """
    if not summary_text:
        return {'success': False, 'error': 'summary_text is required'}
    if not doc_id and not resource_id:
        return {'success': False, 'error': 'doc_id or resource_id is required'}

    cursor = conn.cursor()
    created_at = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT INTO Summaries (resource_id, doc_id, summary_text, model, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (resource_id, doc_id, summary_text, model, created_at),
    )
    conn.commit()
    return {'success': True, 'summary_id': cursor.lastrowid}
