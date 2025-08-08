import tempfile
import os
import sqlite3
from datetime import datetime
from ltms.services.context_service import (
    get_context_for_query, log_chat_message, create_context_links
)
from ltms.database.schema import create_tables
from ltms.database.connection import get_db_connection
from ltms.services.resource_service import add_resource


def test_get_context_for_query_retrieves_relevant_context():
    """Test that get_context_for_query retrieves relevant context for a query."""
    # Create temporary database and index files
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = os.path.join(temp_dir, "test_index")
        
        try:
            # Create database and tables
            conn = get_db_connection(db_path)
            create_tables(conn)
            
            # Add a test resource
            content = (
                "This is a document about machine learning. "
                "Machine learning is a subset of artificial intelligence. "
                "It involves training models on data to make predictions."
            )
            
            add_resource(
                conn=conn,
                index_path=index_path,
                file_name="ml_doc.txt",
                resource_type="document",
                content=content
            )
            
            # Test context retrieval
            conversation_id = "test_conversation_123"
            query = "What is machine learning?"
            top_k = 2
            
            result = get_context_for_query(
                conn=conn,
                index_path=index_path,
                conversation_id=conversation_id,
                query=query,
                top_k=top_k
            )
            
            # Verify result structure
            assert result['success'] is True
            assert 'context' in result
            assert 'retrieved_chunks' in result
            assert len(result['retrieved_chunks']) > 0
            
            # Verify context contains relevant information
            context = result['context'].lower()
            assert 'machine learning' in context
            
            # Verify retrieved chunks structure
            for chunk in result['retrieved_chunks']:
                assert 'chunk_id' in chunk
                assert 'resource_id' in chunk
                assert 'file_name' in chunk
                assert 'score' in chunk
                assert chunk['score'] >= 0  # Score should be non-negative
            
            conn.close()
            
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)


def test_log_chat_message_creates_chat_history_entry():
    """Test that log_chat_message creates a chat history entry."""
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        # Create database and tables
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        # Test logging a chat message
        conversation_id = "test_conversation_456"
        role = "user"
        content = "What is artificial intelligence?"
        
        message_id = log_chat_message(
            conn=conn,
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        
        # Verify message was created
        assert message_id is not None
        
        # Verify in database
        cursor = conn.cursor()
        cursor.execute(
            "SELECT conversation_id, role, content FROM ChatHistory WHERE id = ?",
            (message_id,)
        )
        message = cursor.fetchone()
        
        assert message is not None
        assert message[0] == conversation_id
        assert message[1] == role
        assert message[2] == content
        
        conn.close()
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_create_context_links_creates_links():
    """Test that create_context_links creates context links."""
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        # Create database and tables
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        # Create a test resource and chunks
        content = "This is a test document about testing."
        add_resource(
            conn=conn,
            index_path="dummy_index",  # Not used for this test
            file_name="test.txt",
            resource_type="document",
            content=content
        )
        
        # Get the chunk IDs
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM ResourceChunks")
        chunk_ids = [row[0] for row in cursor.fetchall()]
        
        # Test creating context links
        message_id = 1  # Dummy message ID
        result = create_context_links(conn, message_id, chunk_ids)
        
        # Verify links were created
        assert result['success'] is True
        assert result['links_created'] == len(chunk_ids)
        
        # Verify in database
        cursor.execute(
            "SELECT COUNT(*) FROM ContextLinks WHERE message_id = ?",
            (message_id,)
        )
        link_count = cursor.fetchone()[0]
        assert link_count == len(chunk_ids)
        
        conn.close()
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_get_context_for_query_handles_empty_results():
    """Test that get_context_for_query handles empty results gracefully."""
    # Create temporary database and index files
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = os.path.join(temp_dir, "test_index")
        
        try:
            # Create database and tables
            conn = get_db_connection(db_path)
            create_tables(conn)
            
            # Test context retrieval with no resources
            conversation_id = "empty_conversation"
            query = "This query has no relevant content."
            top_k = 3
            
            result = get_context_for_query(
                conn=conn,
                index_path=index_path,
                conversation_id=conversation_id,
                query=query,
                top_k=top_k
            )
            
            # Verify result structure
            assert result['success'] is True
            assert 'context' in result
            assert 'retrieved_chunks' in result
            assert len(result['retrieved_chunks']) == 0
            assert result['context'] == ""  # Empty context
            
            conn.close()
            
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)
