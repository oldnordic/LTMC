"""FastAPI application for LTMC API endpoints."""

from datetime import datetime
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from ltms.database.connection import get_db_connection, close_db_connection
from ltms.database.schema import create_tables
from ltms.services.resource_service import add_resource
from ltms.services.context_service import get_context_for_query
import os


# Pydantic models for request/response validation
class ResourceRequest(BaseModel):
    file_name: str = Field(..., description="Name of the file")
    resource_type: str = Field(..., description="Type of resource (e.g., 'document', 'code')")
    content: str = Field(..., description="Text content of the resource")


class ContextRequest(BaseModel):
    conversation_id: str = Field(..., description="ID of the conversation")
    query: str = Field(..., description="User's query text")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of similar chunks to retrieve")


class HealthResponse(BaseModel):
    status: str
    timestamp: str


# Create FastAPI app
app = FastAPI(
    title="LTMC API",
    description="Long-Term Memory Core API for resource management and context retrieval",
    version="1.0.0"
)


def get_db_path() -> str:
    """Get database path from environment variable."""
    return os.getenv("DB_PATH", "ltmc.db")


def get_index_path() -> str:
    """Get FAISS index path from environment variable."""
    return os.getenv("FAISS_INDEX_PATH", "faiss_index")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat()
    )


@app.post("/api/v1/resources")
async def add_resource_endpoint(request: ResourceRequest) -> Dict[str, Any]:
    """Add a new resource to the system.
    
    This endpoint implements the complete ingestion pipeline:
    1. Chunks the text into semantically coherent pieces
    2. Generates embeddings for each chunk
    3. Stores the resource and chunks in the database
    4. Adds the embeddings to the vector index
    """
    try:
        # Get database connection
        db_path = get_db_path()
        index_path = get_index_path()
        
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        # Add resource using the service layer
        result = add_resource(
            conn=conn,
            index_path=index_path,
            file_name=request.file_name,
            resource_type=request.resource_type,
            content=request.content
        )
        
        # Close database connection
        close_db_connection(conn)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Unknown error'))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/context")
async def get_context_endpoint(request: ContextRequest) -> Dict[str, Any]:
    """Get relevant context for a query.
    
    This endpoint implements the complete retrieval pipeline:
    1. Embeds the query
    2. Searches for similar chunks in the vector index
    3. Retrieves the full text of the chunks
    4. Logs the query in chat history
    5. Creates context links
    """
    try:
        # Get database connection
        db_path = get_db_path()
        index_path = get_index_path()
        
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        # Get context using the service layer
        result = get_context_for_query(
            conn=conn,
            index_path=index_path,
            conversation_id=request.conversation_id,
            query=request.query,
            top_k=request.top_k
        )
        
        # Close database connection
        close_db_connection(conn)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Unknown error'))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
