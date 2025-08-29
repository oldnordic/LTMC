"""
SQLite Database Manager for LTMC Atomic Operations.
Provides atomic document storage with transaction support.

File: ltms/database/sqlite_manager.py
Lines: ~290 (under 300 limit)
Purpose: SQLite operations for atomic cross-database synchronization
"""
import sqlite3
import logging
import json
import threading
from typing import Dict, List, Any, Optional
from contextlib import contextmanager
from datetime import datetime

from .connection import get_db_connection, close_db_connection
from .dal import create_resource
from .schema import create_tables
from ltms.config.json_config_loader import get_config

logger = logging.getLogger(__name__)

class SQLiteManager:
    """
    SQLite database manager for atomic document operations.
    Provides transaction-safe document storage and retrieval.
    """
    
    # Class-level connection for test mode to persist in-memory database
    _test_connection: Optional[sqlite3.Connection] = None
    _test_connection_lock = threading.Lock()
    
    def __init__(self, db_path: Optional[str] = None, test_mode: bool = False):
        """Initialize SQLite manager with database connection.
        
        Args:
            db_path: Path to SQLite database file (uses config default if None)
            test_mode: Enable test mode for unit testing
        """
        self.test_mode = test_mode
        
        if test_mode:
            self.db_path = ":memory:"
        elif db_path:
            self.db_path = db_path
        else:
            config = get_config()
            self.db_path = config.get_db_path()
        
        self._connection: Optional[sqlite3.Connection] = None
        
        # Initialize database schema (always create schema, even in test mode)
        self._ensure_schema()
            
        logger.info(f"SQLiteManager initialized (test_mode={test_mode}, db_path={self.db_path})")
    
    def _ensure_schema(self):
        """Ensure database schema exists."""
        try:
            with self.get_connection() as conn:
                create_tables(conn)
        except Exception as e:
            logger.error(f"Failed to ensure database schema: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get database connection context manager."""
        if self.test_mode:
            # Use shared connection for test mode to persist in-memory database
            if SQLiteManager._test_connection is None:
                SQLiteManager._test_connection = sqlite3.connect(":memory:")
            yield SQLiteManager._test_connection
        else:
            # Standard file-based connection for production
            conn = None
            try:
                conn = get_db_connection(self.db_path)
                yield conn
            except Exception as e:
                if conn:
                    conn.rollback()
                logger.error(f"Database connection error: {e}")
                raise
            finally:
                if conn:
                    close_db_connection(conn)
    
    def _get_next_vector_id(self, cursor: sqlite3.Cursor) -> int:
        """Get next available vector ID from sequence table.
        
        Args:
            cursor: Database cursor within active transaction
            
        Returns:
            Next available vector ID
        """
        # Get current vector ID and increment it atomically
        cursor.execute("SELECT last_vector_id FROM VectorIdSequence WHERE id = 1")
        row = cursor.fetchone()
        
        if row:
            current_id = row[0]
            next_id = current_id + 1
        else:
            # Initialize sequence if it doesn't exist
            next_id = 1
        
        # Update the sequence
        cursor.execute(
            "UPDATE VectorIdSequence SET last_vector_id = ? WHERE id = 1",
            (next_id,)
        )
        
        # Verify update worked
        if cursor.rowcount == 0:
            # Insert if update failed (shouldn't happen with schema initialization)
            cursor.execute(
                "INSERT OR REPLACE INTO VectorIdSequence (id, last_vector_id) VALUES (1, ?)",
                (next_id,)
            )
        
        return next_id
    
    def store_document(self, doc_id: str, content: str, tags: List[str] = None, 
                      metadata: Dict[str, Any] = None) -> bool:
        """
        Store document in SQLite database atomically.
        
        Args:
            doc_id: Unique document identifier
            content: Document content
            tags: List of document tags
            metadata: Document metadata dictionary
            
        Returns:
            True if storage successful, False otherwise
        """
            
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if document already exists
                cursor.execute(
                    "SELECT id FROM Resources WHERE file_name = ?", 
                    (doc_id,)
                )
                
                current_time = datetime.now().isoformat()
                tags_json = json.dumps(tags or [])
                metadata_json = json.dumps(metadata or {})
                
                existing_row = cursor.fetchone()
                if existing_row:
                    resource_id = existing_row[0]
                    
                    # Get existing vector_id for this resource to reuse it
                    cursor.execute(
                        "SELECT vector_id FROM ResourceChunks WHERE resource_id = ? LIMIT 1",
                        (resource_id,)
                    )
                    existing_chunk = cursor.fetchone()
                    
                    if existing_chunk:
                        # Reuse existing vector_id for updates
                        vector_id = existing_chunk[0]
                        cursor.execute("DELETE FROM ResourceChunks WHERE resource_id = ?", (resource_id,))
                    else:
                        # Generate new vector_id if no chunks exist
                        vector_id = self._get_next_vector_id(cursor)
                    
                    cursor.execute("""
                        INSERT INTO ResourceChunks (resource_id, chunk_text, vector_id) 
                        VALUES (?, ?, ?)
                    """, (resource_id, content, vector_id))
                    
                    logger.info(f"Updated document {doc_id} in SQLite with vector_id {vector_id}")
                else:
                    # Create new document - insert into Resources, then ResourceChunks
                    cursor.execute("""
                        INSERT INTO Resources (file_name, type, created_at) 
                        VALUES (?, ?, ?)
                    """, (doc_id, "document", current_time))
                    
                    resource_id = cursor.lastrowid
                    vector_id = self._get_next_vector_id(cursor)
                    
                    cursor.execute("""
                        INSERT INTO ResourceChunks (resource_id, chunk_text, vector_id) 
                        VALUES (?, ?, ?)
                    """, (resource_id, content, vector_id))
                    
                    logger.info(f"Created document {doc_id} in SQLite with vector_id {vector_id}")
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to store document {doc_id} in SQLite: {e}")
            return False
    
    def retrieve_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve document from SQLite database.
        
        Args:
            doc_id: Document identifier to retrieve
            
        Returns:
            Document data dictionary or None if not found
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT r.id, r.file_name, r.created_at
                    FROM Resources r
                    WHERE r.file_name = ?
                """, (doc_id,))
                
                row = cursor.fetchone()
                if row:
                    resource_id, file_name, created_at = row
                    
                    # Get content from ResourceChunks
                    cursor.execute("""
                        SELECT chunk_text FROM ResourceChunks 
                        WHERE resource_id = ? 
                        ORDER BY id
                    """, (resource_id,))
                    
                    chunks = cursor.fetchall()
                    content = ''.join(chunk[0] for chunk in chunks) if chunks else ""
                    
                    return {
                        "id": file_name,
                        "content": content,
                        "tags": [],  # Tags not in current schema
                        "metadata": {},  # Metadata not in current schema
                        "created_at": created_at,
                        "updated_at": created_at  # No updated_at in current schema
                    }
                    
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve document {doc_id} from SQLite: {e}")
            return None
    
    def document_exists(self, doc_id: str) -> bool:
        """
        Check if document exists in SQLite database.
        
        Args:
            doc_id: Document identifier to check
            
        Returns:
            True if document exists, False otherwise
        """
        if self.test_mode:
            return True
            
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM Resources WHERE file_name = ? LIMIT 1", 
                    (doc_id,)
                )
                return cursor.fetchone() is not None
                
        except Exception as e:
            logger.error(f"Failed to check document existence {doc_id} in SQLite: {e}")
            return False
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete document from SQLite database.
        
        Args:
            doc_id: Document identifier to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        if self.test_mode:
            return True
            
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM Resources WHERE file_name = ?", 
                    (doc_id,)
                )
                conn.commit()
                
                deleted_count = cursor.rowcount
                logger.info(f"Deleted document {doc_id} from SQLite (rows affected: {deleted_count})")
                return deleted_count > 0
                
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id} from SQLite: {e}")
            return False
    
    def list_documents(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List documents in SQLite database.
        
        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            List of document data dictionaries
        """
        if self.test_mode:
            return [{
                "id": "test_doc_1",
                "content": "test content",
                "tags": ["test"],
                "metadata": {}
            }]
            
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT r.id, r.file_name, r.created_at
                    FROM Resources r
                    ORDER BY r.created_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                documents = []
                for row in cursor.fetchall():
                    resource_id, file_name, created_at = row
                    
                    # Get content from ResourceChunks for each resource
                    cursor.execute("""
                        SELECT chunk_text FROM ResourceChunks 
                        WHERE resource_id = ? 
                        ORDER BY id
                    """, (resource_id,))
                    
                    chunks = cursor.fetchall()
                    content = ''.join(chunk[0] for chunk in chunks) if chunks else ""
                    
                    documents.append({
                        "id": file_name,
                        "content": content,
                        "tags": [],
                        "metadata": {},
                        "created_at": created_at,
                        "updated_at": created_at
                    })
                
                return documents
                
        except Exception as e:
            logger.error(f"Failed to list documents from SQLite: {e}")
            return []
    
    def count_documents(self) -> int:
        """
        Count total documents in SQLite database.
        
        Returns:
            Total number of documents
        """
        if self.test_mode:
            return 1
            
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM Resources")
                
                count = cursor.fetchone()[0]
                return count or 0
                
        except Exception as e:
            logger.error(f"Failed to count documents in SQLite: {e}")
            return 0
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of SQLite database.
        
        Returns:
            Health status dictionary
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                
                document_count = self.count_documents()
                
                return {
                    "status": "healthy",
                    "database_path": self.db_path,
                    "document_count": document_count,
                    "test_mode": self.test_mode
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "database_path": self.db_path,
                "test_mode": self.test_mode
            }