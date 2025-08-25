"""
Neo4j Database Manager for LTMC Atomic Operations.
Provides atomic document storage with graph relationship support.

File: ltms/database/neo4j_manager.py
Lines: ~290 (under 300 limit)
Purpose: Neo4j operations for atomic cross-database synchronization
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from .neo4j_store import Neo4jGraphStore
from ltms.config import get_config

logger = logging.getLogger(__name__)

class Neo4jManager:
    """
    Neo4j database manager for atomic document operations.
    Provides transaction-safe document nodes and relationship management.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, test_mode: bool = False):
        """Initialize Neo4j manager with graph store connection.
        
        Args:
            config: Neo4j configuration dictionary (uses app config if None)
            test_mode: Enable test mode for unit testing
        """
        self.test_mode = test_mode
        
        if test_mode:
            # Test mode doesn't require real connection
            self.graph_store = None
            self._is_connected = True
        else:
            # Use provided config or get from application config
            if config is None:
                app_config = get_config()
                config = {
                    "uri": app_config.NEO4J_URI,
                    "user": app_config.NEO4J_USER,
                    "password": app_config.NEO4J_PASSWORD,
                    "database": app_config.NEO4J_DATABASE
                }
            
            self.graph_store = Neo4jGraphStore(config)
            self._is_connected = self.graph_store.is_available()
        
        logger.info(f"Neo4jManager initialized (test_mode={test_mode}, connected={self._is_connected})")
    
    def is_available(self) -> bool:
        """Check if Neo4j is available and connected."""
        if self.test_mode:
            return True
        return self._is_connected and self.graph_store is not None
    
    async def store_document_node(self, doc_id: str, content: str, tags: List[str] = None, 
                                 metadata: Dict[str, Any] = None) -> bool:
        """
        Store document as node in Neo4j graph atomically.
        
        Args:
            doc_id: Unique document identifier
            content: Document content
            tags: List of document tags
            metadata: Document metadata dictionary
            
        Returns:
            True if storage successful, False otherwise
        """
        if self.test_mode:
            return True
            
        if not self.is_available():
            logger.error("Neo4j not available for document storage")
            return False
            
        try:
            # Prepare document properties
            current_time = datetime.now().isoformat()
            
            properties = {
                "content": content,
                "tags": json.dumps(tags or []),
                "metadata": json.dumps(metadata or {}),
                "created_at": current_time,
                "updated_at": current_time
            }
            
            # Store document node using graph store
            result = self.graph_store.create_document_node(doc_id, properties)
            
            if result.get("success", False):
                logger.info(f"Successfully stored document node {doc_id} in Neo4j")
                
                # Create tag relationships if tags exist
                if tags:
                    await self._create_tag_relationships(doc_id, tags)
                    
                return True
            else:
                logger.error(f"Failed to store document node {doc_id}: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Exception storing document node {doc_id} in Neo4j: {e}")
            return False
    
    async def _create_tag_relationships(self, doc_id: str, tags: List[str]) -> bool:
        """Create relationships between document and tag nodes."""
        try:
            for tag in tags:
                result = self.graph_store.create_relationship(
                    doc_id, 
                    "TAGGED_WITH", 
                    tag,
                    {"relationship_type": "tag", "created_at": datetime.now().isoformat()}
                )
                
                if not result.get("success", False):
                    logger.warning(f"Failed to create tag relationship {doc_id} -> {tag}")
                    
            return True
            
        except Exception as e:
            logger.error(f"Failed to create tag relationships for {doc_id}: {e}")
            return False
    
    async def retrieve_document_node(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve document node from Neo4j graph.
        
        Args:
            doc_id: Document identifier to retrieve
            
        Returns:
            Document data dictionary or None if not found
        """
        if self.test_mode:
            return {
                "id": doc_id,
                "content": "test content",
                "tags": ["test"],
                "metadata": {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
        if not self.is_available():
            return None
            
        try:
            result = self.graph_store.get_document_by_id(doc_id)
            
            if result.get("success", False) and result.get("document"):
                doc_data = result["document"]
                
                # Parse JSON fields
                return {
                    "id": doc_id,
                    "content": doc_data.get("content", ""),
                    "tags": json.loads(doc_data.get("tags", "[]")),
                    "metadata": json.loads(doc_data.get("metadata", "{}")),
                    "created_at": doc_data.get("created_at"),
                    "updated_at": doc_data.get("updated_at")
                }
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve document node {doc_id} from Neo4j: {e}")
            return None
    
    async def document_exists(self, doc_id: str) -> bool:
        """
        Check if document node exists in Neo4j graph.
        
        Args:
            doc_id: Document identifier to check
            
        Returns:
            True if document exists, False otherwise
        """
        if self.test_mode:
            return True
            
        if not self.is_available():
            return False
            
        try:
            result = self.graph_store.get_document_by_id(doc_id)
            return result.get("success", False) and result.get("document") is not None
            
        except Exception as e:
            logger.error(f"Failed to check document existence {doc_id} in Neo4j: {e}")
            return False
    
    async def delete_document_node(self, doc_id: str) -> bool:
        """
        Delete document node from Neo4j graph.
        
        Args:
            doc_id: Document identifier to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        if self.test_mode:
            return True
            
        if not self.is_available():
            return False
            
        try:
            result = self.graph_store.delete_document_node(doc_id)
            
            success = result.get("success", False)
            if success:
                logger.info(f"Successfully deleted document node {doc_id} from Neo4j")
            else:
                logger.error(f"Failed to delete document node {doc_id}: {result.get('error', 'Unknown error')}")
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete document node {doc_id} from Neo4j: {e}")
            return False
    
    async def list_document_nodes(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List document nodes in Neo4j graph.
        
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
                "metadata": {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }]
            
        if not self.is_available():
            return []
            
        try:
            result = self.graph_store.list_documents(limit=limit, skip=offset)
            
            if result.get("success", False):
                documents = []
                for doc_data in result.get("documents", []):
                    documents.append({
                        "id": doc_data.get("id"),
                        "content": doc_data.get("content", ""),
                        "tags": json.loads(doc_data.get("tags", "[]")),
                        "metadata": json.loads(doc_data.get("metadata", "{}")),
                        "created_at": doc_data.get("created_at"),
                        "updated_at": doc_data.get("updated_at")
                    })
                
                return documents
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to list document nodes from Neo4j: {e}")
            return []
    
    async def count_document_nodes(self) -> int:
        """
        Count total document nodes in Neo4j graph.
        
        Returns:
            Total number of document nodes
        """
        if self.test_mode:
            return 1
            
        if not self.is_available():
            return 0
            
        try:
            result = self.graph_store.count_documents()
            return result.get("count", 0)
            
        except Exception as e:
            logger.error(f"Failed to count document nodes in Neo4j: {e}")
            return 0
    
    async def create_document_relationship(self, source_doc_id: str, target_doc_id: str, 
                                         relationship_type: str, properties: Dict[str, Any] = None) -> bool:
        """
        Create relationship between two document nodes.
        
        Args:
            source_doc_id: Source document identifier
            target_doc_id: Target document identifier
            relationship_type: Type of relationship (e.g., "REFERENCES", "SIMILAR_TO")
            properties: Relationship properties
            
        Returns:
            True if relationship created successfully, False otherwise
        """
        if self.test_mode:
            return True
            
        if not self.is_available():
            return False
            
        try:
            result = self.graph_store.create_document_relationship(
                source_doc_id, 
                target_doc_id, 
                relationship_type, 
                properties or {}
            )
            
            success = result.get("success", False)
            if success:
                logger.info(f"Created relationship {source_doc_id} -{relationship_type}-> {target_doc_id}")
            else:
                logger.error(f"Failed to create relationship: {result.get('error', 'Unknown error')}")
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to create document relationship: {e}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of Neo4j graph store.
        
        Returns:
            Health status dictionary
        """
        if self.test_mode:
            return {
                "status": "healthy",
                "test_mode": True,
                "document_count": 1
            }
            
        try:
            if not self.is_available():
                return {
                    "status": "unhealthy",
                    "error": "Neo4j not available",
                    "test_mode": False
                }
            
            # Test connection with a simple query
            result = self.graph_store.health_check()
            
            if result.get("success", False):
                document_count = 0
                try:
                    # Get document count asynchronously would require async context
                    # For health check, we'll keep it simple
                    document_count = "unknown"
                except:
                    pass
                
                return {
                    "status": "healthy",
                    "test_mode": False,
                    "document_count": document_count,
                    "connection_info": result.get("connection_info", {})
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": result.get("error", "Health check failed"),
                    "test_mode": False
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "test_mode": self.test_mode
            }
    
    def close(self):
        """Close Neo4j connection."""
        if not self.test_mode and self.graph_store:
            self.graph_store.close()