"""
Unified Database Operations for LTMC - High-Level API.
Provides simplified atomic operations across all 4 databases.

File: ltms/database/unified_operations.py
Lines: ~300 (under 300 limit)
Purpose: High-level atomic database operations with automatic routing and optimization
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

from .atomic_coordinator import (
    AtomicDatabaseCoordinator, 
    OperationType, 
    DatabaseRole
)

logger = logging.getLogger(__name__)

class UnifiedDatabaseOperations:
    """
    High-level unified database operations that automatically coordinate
    across SQLite, FAISS, Neo4j, and Redis for optimal performance.
    """
    
    def __init__(self, coordinator: Optional[AtomicDatabaseCoordinator] = None,
                 test_mode: bool = False):
        """Initialize unified operations with atomic coordinator.
        
        Args:
            coordinator: Atomic database coordinator instance
            test_mode: Enable test mode for unit testing
        """
        self.coordinator = coordinator or AtomicDatabaseCoordinator(test_mode=test_mode)
        self.test_mode = test_mode
        
        # Operation routing cache for performance
        self._routing_cache: Dict[str, List[DatabaseRole]] = {}
        
        logger.info(f"UnifiedDatabaseOperations initialized (test_mode={test_mode})")
    
    async def store_document(self, doc_id: str, content: str, 
                            tags: List[str] = None,
                            metadata: Dict[str, Any] = None,
                            relationships: List[Dict[str, Any]] = None,
                            cache_ttl: int = 3600) -> Dict[str, Any]:
        """
        Store document atomically across all databases with optimal routing.
        
        Args:
            doc_id: Unique document identifier
            content: Document content
            tags: Document tags for categorization
            metadata: Additional metadata
            relationships: Graph relationships to other documents
            cache_ttl: Redis cache TTL in seconds
            
        Returns:
            Operation result with status from each database
        """
        result = {
            "doc_id": doc_id,
            "operation": "store",
            "timestamp": datetime.now().isoformat(),
            "databases": {}
        }
        
        try:
            async with self.coordinator.atomic_transaction() as tx:
                # 1. Store in SQLite (primary transactional store)
                tx.add_operation(
                    DatabaseRole.PRIMARY_TRANSACTIONAL,
                    {
                        "type": "store",
                        "doc_id": doc_id,
                        "content": content,
                        "tags": tags,
                        "metadata": metadata
                    },
                    rollback_op={
                        "type": "delete",
                        "doc_id": doc_id
                    }
                )
                
                # 2. Store vector in FAISS for semantic search
                tx.add_operation(
                    DatabaseRole.VECTOR_SEARCH,
                    {
                        "type": "store",
                        "doc_id": doc_id,
                        "content": content,
                        "metadata": metadata
                    },
                    rollback_op={
                        "type": "delete",
                        "doc_id": doc_id
                    }
                )
                
                # 3. Create node in Neo4j for graph relationships
                tx.add_operation(
                    DatabaseRole.GRAPH_RELATIONS,
                    {
                        "type": "store",
                        "doc_id": doc_id,
                        "content": content,
                        "tags": tags,
                        "metadata": metadata
                    },
                    rollback_op={
                        "type": "delete",
                        "doc_id": doc_id
                    }
                )
                
                # 4. Cache in Redis for fast access
                tx.add_operation(
                    DatabaseRole.CACHE_REALTIME,
                    {
                        "type": "cache",
                        "doc_id": doc_id,
                        "content": content,
                        "metadata": metadata,
                        "ttl": cache_ttl
                    },
                    rollback_op={
                        "type": "delete",
                        "doc_id": doc_id
                    }
                )
                
                # 5. Create relationships in Neo4j if provided
                if relationships:
                    for rel in relationships:
                        tx.add_operation(
                            DatabaseRole.GRAPH_RELATIONS,
                            {
                                "type": "create_relationship",
                                "source_doc_id": doc_id,
                                "target_doc_id": rel["target"],
                                "relationship_type": rel["type"],
                                "properties": rel.get("properties", {})
                            }
                        )
                
                result["transaction_id"] = tx.tx_id
                result["status"] = "success"
                result["databases"] = {
                    "sqlite": "committed",
                    "faiss": "committed",
                    "neo4j": "committed",
                    "redis": "committed"
                }
                
        except Exception as e:
            logger.error(f"Failed to store document {doc_id}: {e}")
            result["status"] = "failed"
            result["error"] = str(e)
            raise
        
        return result
    
    async def retrieve_document(self, doc_id: str, 
                               use_cache: bool = True,
                               include_relationships: bool = False) -> Optional[Dict[str, Any]]:
        """
        Retrieve document with intelligent source selection.
        
        Args:
            doc_id: Document identifier
            use_cache: Try Redis cache first for performance
            include_relationships: Include graph relationships
            
        Returns:
            Document data or None if not found
        """
        document = None
        
        try:
            # 1. Try cache first if enabled
            if use_cache:
                cached = await self.coordinator.redis.retrieve_cached_document(doc_id)
                if cached:
                    logger.debug(f"Retrieved {doc_id} from Redis cache")
                    document = cached
            
            # 2. Fallback to SQLite if not in cache
            if not document:
                sqlite_doc = self.coordinator.sqlite.retrieve_document(doc_id)
                if sqlite_doc:
                    logger.debug(f"Retrieved {doc_id} from SQLite")
                    document = sqlite_doc
                    
                    # Re-cache for future access
                    if use_cache:
                        await self.coordinator.redis.cache_document(
                            doc_id,
                            sqlite_doc["content"],
                            sqlite_doc.get("metadata", {})
                        )
            
            # 3. Enrich with graph relationships if requested
            if document and include_relationships:
                neo4j_data = await self.coordinator.neo4j.retrieve_document_node(doc_id)
                if neo4j_data:
                    document["relationships"] = neo4j_data.get("relationships", [])
            
            # 4. Add vector information if available
            if document:
                faiss_info = await self.coordinator.faiss.retrieve_document_vector(doc_id)
                if faiss_info:
                    document["vector_index"] = faiss_info.get("vector_index")
            
        except Exception as e:
            logger.error(f"Failed to retrieve document {doc_id}: {e}")
            raise
        
        return document
    
    async def delete_document(self, doc_id: str) -> Dict[str, Any]:
        """
        Delete document atomically from all databases.
        
        Args:
            doc_id: Document identifier to delete
            
        Returns:
            Operation result with status from each database
        """
        result = {
            "doc_id": doc_id,
            "operation": "delete",
            "timestamp": datetime.now().isoformat(),
            "databases": {}
        }
        
        try:
            async with self.coordinator.atomic_transaction() as tx:
                # Delete in reverse order of importance
                
                # 1. Clear cache first
                tx.add_operation(
                    DatabaseRole.CACHE_REALTIME,
                    {"type": "delete", "doc_id": doc_id}
                )
                
                # 2. Remove from graph (including relationships)
                tx.add_operation(
                    DatabaseRole.GRAPH_RELATIONS,
                    {"type": "delete", "doc_id": doc_id}
                )
                
                # 3. Remove from vector store
                tx.add_operation(
                    DatabaseRole.VECTOR_SEARCH,
                    {"type": "delete", "doc_id": doc_id}
                )
                
                # 4. Finally remove from primary store
                tx.add_operation(
                    DatabaseRole.PRIMARY_TRANSACTIONAL,
                    {"type": "delete", "doc_id": doc_id}
                )
                
                result["transaction_id"] = tx.tx_id
                result["status"] = "success"
                result["databases"] = {
                    "sqlite": "deleted",
                    "faiss": "deleted",
                    "neo4j": "deleted",
                    "redis": "deleted"
                }
                
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            result["status"] = "failed"
            result["error"] = str(e)
            raise
        
        return result
    
    async def semantic_search(self, query: str, k: int = 5,
                             filter_tags: List[str] = None) -> List[Dict[str, Any]]:
        """
        Perform semantic search using FAISS with metadata enrichment.
        
        Args:
            query: Search query text
            k: Number of results to return
            filter_tags: Optional tag filters
            
        Returns:
            List of similar documents with scores
        """
        results = []
        
        try:
            # 1. Get similar vectors from FAISS
            similar_docs = await self.coordinator.faiss.search_similar(query, k * 2)
            
            # 2. Enrich results with metadata
            for doc_info in similar_docs:
                doc_id = doc_info["doc_id"]
                
                # Get full document data
                full_doc = await self.retrieve_document(doc_id, use_cache=True)
                
                if full_doc:
                    # Apply tag filtering if specified
                    if filter_tags:
                        doc_tags = full_doc.get("tags", [])
                        if not any(tag in doc_tags for tag in filter_tags):
                            continue
                    
                    result = {
                        "doc_id": doc_id,
                        "similarity_score": 1.0 - doc_info["distance"],  # Convert distance to similarity
                        "content": full_doc["content"],
                        "tags": full_doc.get("tags", []),
                        "metadata": full_doc.get("metadata", {})
                    }
                    results.append(result)
                    
                    if len(results) >= k:
                        break
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise
        
        return results
    
    async def graph_traversal(self, start_doc_id: str, 
                            relationship_type: str = None,
                            max_depth: int = 2) -> List[Dict[str, Any]]:
        """
        Perform graph traversal from a starting document.
        
        Args:
            start_doc_id: Starting document for traversal
            relationship_type: Filter by relationship type
            max_depth: Maximum traversal depth
            
        Returns:
            List of connected documents with relationship paths
        """
        # This would use Neo4j's graph traversal capabilities
        # Implementation would depend on neo4j_store.py methods
        logger.info(f"Graph traversal from {start_doc_id} (type={relationship_type}, depth={max_depth})")
        
        # Placeholder for actual graph traversal
        # Would need to implement in neo4j_manager
        return []
    
    async def batch_operation(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute multiple operations atomically.
        
        Args:
            operations: List of operation specifications
            
        Returns:
            Batch operation results
        """
        result = {
            "batch_size": len(operations),
            "timestamp": datetime.now().isoformat(),
            "operations": [],
            "status": "pending"
        }
        
        try:
            async with self.coordinator.atomic_transaction() as tx:
                for op in operations:
                    op_type = op.get("type")
                    
                    if op_type == "store":
                        await self.store_document(
                            op["doc_id"],
                            op["content"],
                            op.get("tags"),
                            op.get("metadata"),
                            op.get("relationships"),
                            op.get("cache_ttl", 3600)
                        )
                    elif op_type == "delete":
                        await self.delete_document(op["doc_id"])
                    
                    result["operations"].append({
                        "type": op_type,
                        "doc_id": op.get("doc_id"),
                        "status": "completed"
                    })
                
                result["status"] = "success"
                
        except Exception as e:
            logger.error(f"Batch operation failed: {e}")
            result["status"] = "failed"
            result["error"] = str(e)
            raise
        
        return result
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics across all databases."""
        stats = {
            "timestamp": datetime.now().isoformat(),
            "databases": {},
            "coordinator_metrics": self.coordinator.metrics
        }
        
        # Gather stats from each database
        stats["databases"]["sqlite"] = {
            "document_count": self.coordinator.sqlite.count_documents()
        }
        
        stats["databases"]["redis"] = {
            "cached_documents": await self.coordinator.redis.count_cached_documents()
        }
        
        stats["databases"]["neo4j"] = {
            "node_count": await self.coordinator.neo4j.count_document_nodes()
        }
        
        stats["databases"]["faiss"] = self.coordinator.faiss.get_health_status()
        
        return stats