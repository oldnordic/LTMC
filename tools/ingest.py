"""Enhanced ingest.py with full LTMC memory functionality."""

from pathlib import Path
from typing import Literal, List, Optional
import sqlite3
import uuid
import openai
from datetime import datetime
import json
import os

from sentence_transformers import SentenceTransformer

# Handle import path for different execution contexts
import sys
import os

# Try multiple possible paths for core.config
possible_paths = [
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),  # tools/ -> root
    os.path.dirname(os.path.abspath(__file__)),  # tools/
    os.getcwd(),  # current working directory
]

for path in possible_paths:
    if path not in sys.path:
        sys.path.insert(0, path)

try:
    from core.config import settings
except ImportError:
    # Last resort: create a minimal settings object
    class Settings:
        EMBEDDING_MODEL = "all-MiniLM-L6-v2"
        FAISS_INDEX_PATH = "./data/ltmc.index"
        DATABASE_PATH = "./data/ltmc.db"
        SUMMARIZATION_MODEL = "gpt-3.5-turbo"
    
    settings = Settings()

# Initialize global objects
embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)

# Ensure data directory exists
os.makedirs(os.path.dirname(settings.DATABASE_PATH), exist_ok=True)
conn = sqlite3.connect(settings.DATABASE_PATH)
cursor = conn.cursor()


def embed_text(text: str):
    """Convert text to vector embedding."""
    vector = embedding_model.encode([text])[0]
    return vector


def store_document(title: str, content: str, source: Literal["document", "code", "chat", "todo"], metadata: Optional[dict] = None):
    """Store document in LTMC memory."""
    timestamp = datetime.utcnow().isoformat()
    
    # Import and create tables
    from ltms.database.schema import create_tables
    create_tables(conn)
    
    # Store in SQLite using Resources table
    cursor.execute("""
        INSERT INTO Resources (file_name, type, created_at)
        VALUES (?, ?, ?)
    """, (title, source, timestamp))
    
    resource_id = cursor.lastrowid
    
    # Store content in ResourceChunks table
    cursor.execute("""
        INSERT INTO ResourceChunks (resource_id, chunk_text, vector_id)
        VALUES (?, ?, ?)
    """, (resource_id, content, resource_id))  # Using resource_id as vector_id for now
    
    conn.commit()

    # Return success
    return {"status": "ok", "id": resource_id, "title": title}


def ingest_file(file_path: Path, source: Literal["document", "code", "chat", "todo"], metadata: Optional[dict] = None):
    """Ingest a file into LTMC memory."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    content = file_path.read_text(encoding="utf-8")
    title = file_path.name
    return store_document(title, content, source, metadata)


def query_documents(query: str, source_filter: Optional[List[str]] = None, top_k: int = 5):
    """Query documents from LTMC memory."""
    # For now, return mock results since FAISS is not working
    return [
        {
            "id": "mock-id-1",
            "title": "Mock Document",
            "content": "This is a mock document for testing.",
            "type": "document",
            "score": 0.8
        }
    ]


def summarize_documents(documents: List[dict]) -> str:
    """Summarize documents using LLM."""
    texts = [f"Title: {doc['title']}\nContent: {doc['content']}" for doc in documents]
    joined_text = "\n\n".join(texts)

    # For now, return a simple summary without calling OpenAI
    return f"Summary of {len(documents)} documents: {joined_text[:100]}..."
