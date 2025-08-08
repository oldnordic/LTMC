import tempfile
import os
import json
from fastapi.testclient import TestClient
from ltms.api.main import app


def test_add_resource_endpoint_creates_resource():
    """Test that POST /api/v1/resources creates a new resource."""
    # Create temporary database and index files
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = os.path.join(temp_dir, "test_index")
        
        # Set environment variables for test
        os.environ["DB_PATH"] = db_path
        os.environ["FAISS_INDEX_PATH"] = index_path
        
        try:
            client = TestClient(app)
            
            # Test data
            resource_data = {
                "file_name": "test_document.txt",
                "resource_type": "document",
                "content": "This is a test document about testing."
            }
            
            # Make request
            response = client.post(
                "/api/v1/resources",
                json=resource_data
            )
            
            # Log error details if failed
            if response.status_code != 200:
                print(f"Response status: {response.status_code}")
                print(f"Response body: {response.text}")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert 'resource_id' in data
            assert 'chunk_count' in data
            assert data['chunk_count'] > 0
            
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)
            # Clear environment variables
            os.environ.pop("DB_PATH", None)
            os.environ.pop("FAISS_INDEX_PATH", None)


def test_get_context_endpoint_retrieves_context():
    """Test that POST /api/v1/context retrieves relevant context."""
    # Create temporary database and index files
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = os.path.join(temp_dir, "test_index")
        
        # Set environment variables for test
        os.environ["DB_PATH"] = db_path
        os.environ["FAISS_INDEX_PATH"] = index_path
        
        try:
            client = TestClient(app)
            
            # First add a resource
            resource_data = {
                "file_name": "ml_doc.txt",
                "resource_type": "document",
                "content": (
                    "Machine learning is a subset of artificial intelligence. "
                    "It involves training models on data to make predictions."
                )
            }
            
            add_response = client.post("/api/v1/resources", json=resource_data)
            
            # Log error details if failed
            if add_response.status_code != 200:
                print(f"Add resource response status: {add_response.status_code}")
                print(f"Add resource response body: {add_response.text}")
            
            assert add_response.status_code == 200
            
            # Then test context retrieval
            context_data = {
                "conversation_id": "test_conversation_123",
                "query": "What is machine learning?",
                "top_k": 2
            }
            
            response = client.post("/api/v1/context", json=context_data)
            
            # Log error details if failed
            if response.status_code != 200:
                print(f"Context response status: {response.status_code}")
                print(f"Context response body: {response.text}")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert 'context' in data
            assert 'retrieved_chunks' in data
            assert len(data['retrieved_chunks']) > 0
            
            # Verify context contains relevant information
            context = data['context'].lower()
            assert 'machine learning' in context
            
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)
            # Clear environment variables
            os.environ.pop("DB_PATH", None)
            os.environ.pop("FAISS_INDEX_PATH", None)


def test_add_resource_endpoint_handles_invalid_data():
    """Test that POST /api/v1/resources handles invalid data gracefully."""
    client = TestClient(app)
    
    # Test with missing required fields
    invalid_data = {
        "file_name": "test.txt"
        # Missing resource_type and content
    }
    
    response = client.post("/api/v1/resources", json=invalid_data)
    
    # Should return 422 (validation error)
    assert response.status_code == 422


def test_get_context_endpoint_handles_empty_query():
    """Test that POST /api/v1/context handles empty query gracefully."""
    # Create temporary database and index files
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = os.path.join(temp_dir, "test_index")
        
        # Set environment variables for test
        os.environ["DB_PATH"] = db_path
        os.environ["FAISS_INDEX_PATH"] = index_path
        
        try:
            client = TestClient(app)
            
            # Test with empty query
            context_data = {
                "conversation_id": "test_conversation_456",
                "query": "",
                "top_k": 3
            }
            
            response = client.post("/api/v1/context", json=context_data)
            
            # Log error details if failed
            if response.status_code != 200:
                print(f"Empty query response status: {response.status_code}")
                print(f"Empty query response body: {response.text}")
            
            # Should still return success but with empty context
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['context'] == ""
            assert len(data['retrieved_chunks']) == 0
            
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)
            # Clear environment variables
            os.environ.pop("DB_PATH", None)
            os.environ.pop("FAISS_INDEX_PATH", None)


def test_api_health_check():
    """Test that the API health check endpoint works."""
    client = TestClient(app)
    
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == "healthy"
    assert 'timestamp' in data
