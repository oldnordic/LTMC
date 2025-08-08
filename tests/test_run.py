import tempfile
import os
from fastapi.testclient import TestClient
from ltms.api.main import app


def test_create_app_returns_fastapi_app():
    """Test that create_app returns a valid FastAPI application."""
    from ltms.run import create_app
    app_instance = create_app()
    
    # Verify it's a FastAPI app
    assert hasattr(app_instance, 'routes')
    assert hasattr(app_instance, 'title')
    assert app_instance.title == "LTMC API"


def test_server_starts_and_responds_to_health_check():
    """Test that the server starts and responds to health check."""
    # Create temporary database and index files
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = os.path.join(temp_dir, "test_index")
        
        # Set environment variables for test
        os.environ["DB_PATH"] = db_path
        os.environ["FAISS_INDEX_PATH"] = index_path
        
        try:
            # Use TestClient instead of subprocess
            client = TestClient(app)
            
            # Test health check
            response = client.get("/health")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == "healthy"
            assert 'timestamp' in data
            
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)
            # Clear environment variables
            os.environ.pop("DB_PATH", None)
            os.environ.pop("FAISS_INDEX_PATH", None)


def test_server_handles_resource_endpoint():
    """Test that the server handles resource endpoint correctly."""
    # Create temporary database and index files
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = os.path.join(temp_dir, "test_index")
        
        # Set environment variables for test
        os.environ["DB_PATH"] = db_path
        os.environ["FAISS_INDEX_PATH"] = index_path
        
        try:
            # Use TestClient instead of subprocess
            client = TestClient(app)
            
            # Test resource endpoint
            resource_data = {
                "file_name": "test_doc.txt",
                "resource_type": "document",
                "content": "This is a test document."
            }
            
            response = client.post(
                "/api/v1/resources",
                json=resource_data
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert 'resource_id' in data
            assert 'chunk_count' in data
            
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)
            # Clear environment variables
            os.environ.pop("DB_PATH", None)
            os.environ.pop("FAISS_INDEX_PATH", None)


def test_server_handles_context_endpoint():
    """Test that the server handles context endpoint correctly."""
    # Create temporary database and index files
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = os.path.join(temp_dir, "test_index")
        
        # Set environment variables for test
        os.environ["DB_PATH"] = db_path
        os.environ["FAISS_INDEX_PATH"] = index_path
        
        try:
            # Use TestClient instead of subprocess
            client = TestClient(app)
            
            # First add a resource
            resource_data = {
                "file_name": "ml_doc.txt",
                "resource_type": "document",
                "content": "Machine learning is a subset of AI."
            }
            
            add_response = client.post(
                "/api/v1/resources",
                json=resource_data
            )
            assert add_response.status_code == 200
            
            # Then test context endpoint
            context_data = {
                "conversation_id": "test_conv_123",
                "query": "What is machine learning?",
                "top_k": 2
            }
            
            response = client.post(
                "/api/v1/context",
                json=context_data
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert 'context' in data
            assert 'retrieved_chunks' in data
            
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)
            # Clear environment variables
            os.environ.pop("DB_PATH", None)
            os.environ.pop("FAISS_INDEX_PATH", None)
