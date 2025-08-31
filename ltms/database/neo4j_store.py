"""Neo4j integration for graph memory functionality."""

from typing import List, Dict, Any, Optional
import logging

# Try to import Neo4j driver, but handle gracefully if not available
try:
    import sys
    import os
    # Add virtual environment site-packages to path if not already there
    venv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'venv', 'lib', 'python3.13', 'site-packages')
    if venv_path not in sys.path:
        sys.path.insert(0, venv_path)
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logging.warning("Neo4j driver not available. Graph functionality will be limited.")


class Neo4jGraphStore:
    """Neo4j graph store for document relationships."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Neo4j graph store.
        
        Args:
            config: Neo4j configuration dictionary with uri, user, password, database
        """
        self.config = config
        self.driver = None
        
        if NEO4J_AVAILABLE:
            try:
                self.driver = GraphDatabase.driver(
                    config["uri"],
                    auth=(config["user"], config["password"])
                )
                # Test connection
                with self.driver.session(database=config.get("database", "neo4j")) as session:
                    session.run("RETURN 1")
                logging.info("Neo4j connection established successfully")
            except Exception as e:
                logging.warning(f"Neo4j driver available but connection failed: {e}")
                self.driver = None
        else:
            logging.warning("Neo4j driver not available")
    
    def close(self):
        """Close the Neo4j driver connection."""
        if self.driver:
            self.driver.close()
    
    def is_available(self) -> bool:
        """Check if Neo4j is available and connected."""
        if not (self.driver and NEO4J_AVAILABLE):
            return False
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            return True
        except Exception:
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of Neo4j connection.
        
        Returns:
            Dictionary with health status, connection info, and basic stats
        """
        if not NEO4J_AVAILABLE:
            return {
                "success": False,
                "error": "Neo4j driver not available",
                "status": "unavailable"
            }
        
        if not self.driver:
            return {
                "success": False,
                "error": "Neo4j driver not initialized",
                "status": "disconnected"
            }
        
        try:
            with self.driver.session() as session:
                # Test basic connectivity
                result = session.run("RETURN 'Neo4j health check' AS message")
                message = result.single()["message"]
                
                # Get basic database statistics
                stats_result = session.run("""
                    MATCH (n)
                    RETURN count(n) AS total_nodes
                """)
                total_nodes = stats_result.single()["total_nodes"]
                
                # Get relationship count
                rel_result = session.run("""
                    MATCH ()-[r]->()
                    RETURN count(r) AS total_relationships
                """)
                total_relationships = rel_result.single()["total_relationships"]
                
                return {
                    "success": True,
                    "status": "healthy",
                    "message": message,
                    "database_stats": {
                        "total_nodes": total_nodes,
                        "total_relationships": total_relationships
                    },
                    "connection_info": {
                        "uri": self.config["uri"],
                        "database": self.config.get("database", "neo4j")
                    }
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status": "unhealthy"
            }
    
    def create_document_node(self, doc_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Create a document node in the graph.
        
        Args:
            doc_id: Unique document identifier
            properties: Document properties
            
        Returns:
            Dictionary with success status
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "Neo4j not available"
            }
        
        try:
            with self.driver.session() as session:
                # Create document node with properties
                query = """
                MERGE (d:Document {id: $doc_id})
                SET d += $properties
                RETURN d
                """
                result = session.run(query, doc_id=doc_id, properties=properties)
                record = result.single()
                
                if record:
                    return {
                        "success": True,
                        "node_created": True,
                        "doc_id": doc_id
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to create document node"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_relationship(
        self, 
        source_id: str, 
        target_id: str, 
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a relationship between two documents.
        
        Args:
            source_id: Source document ID
            target_id: Target document ID
            relationship_type: Type of relationship
            properties: Optional relationship properties
            
        Returns:
            Dictionary with success status
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "Neo4j not available"
            }
        
        if not source_id or not target_id or not relationship_type:
            return {
                "success": False,
                "error": "source_id, target_id, and relationship_type are required"
            }
        
        try:
            with self.driver.session() as session:
                # Create relationship between documents (create nodes if they don't exist)
                query = """
                MERGE (source:Document {id: $source_id})
                MERGE (target:Document {id: $target_id})
                MERGE (source)-[r:RELATES_TO {type: $relationship_type}]->(target)
                SET r += $properties
                RETURN r
                """
                
                result = session.run(
                    query,
                    source_id=source_id,
                    target_id=target_id,
                    relationship_type=relationship_type,
                    properties=properties or {}
                )
                
                record = result.single()
                if record:
                    return {
                        "success": True,
                        "relationship_created": True,
                        "source_id": source_id,
                        "target_id": target_id,
                        "relationship_type": relationship_type
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to create relationship"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_document_relationship(
        self, 
        source_doc_id: str, 
        target_doc_id: str, 
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a relationship between two documents (alias for create_relationship).
        
        Args:
            source_doc_id: Source document ID
            target_doc_id: Target document ID
            relationship_type: Type of relationship
            properties: Optional relationship properties
            
        Returns:
            Dictionary with success status
        """
        # This is an alias to create_relationship with the same signature
        return self.create_relationship(source_doc_id, target_doc_id, relationship_type, properties)
    
    def query_relationships(
        self, 
        entity_id: str, 
        relationship_type: Optional[str] = None,
        direction: str = "both"
    ) -> Dict[str, Any]:
        """Query relationships for a specific entity.
        
        Args:
            entity_id: Entity document ID
            relationship_type: Optional relationship type filter
            direction: Direction of relationships ("incoming", "outgoing", "both")
            
        Returns:
            Dictionary with relationships found
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "Neo4j not available"
            }
        
        try:
            with self.driver.session() as session:
                if relationship_type:
                    if direction == "incoming":
                        query = """
                        MATCH (target:Document {id: $entity_id})<-[r:RELATES_TO {type: $relationship_type}]-(source:Document)
                        RETURN source.id as source_id, target.id as target_id, r.type as relationship_type, r as properties
                        """
                    elif direction == "outgoing":
                        query = """
                        MATCH (source:Document {id: $entity_id})-[r:RELATES_TO {type: $relationship_type}]->(target:Document)
                        RETURN source.id as source_id, target.id as target_id, r.type as relationship_type, r as properties
                        """
                    else:  # both
                        query = """
                        MATCH (source:Document {id: $entity_id})-[r:RELATES_TO {type: $relationship_type}]-(target:Document)
                        RETURN source.id as source_id, target.id as target_id, r.type as relationship_type, r as properties
                        """
                else:
                    if direction == "incoming":
                        query = """
                        MATCH (target:Document {id: $entity_id})<-[r:RELATES_TO]-(source:Document)
                        RETURN source.id as source_id, target.id as target_id, r.type as relationship_type, r as properties
                        """
                    elif direction == "outgoing":
                        query = """
                        MATCH (source:Document {id: $entity_id})-[r:RELATES_TO]->(target:Document)
                        RETURN source.id as source_id, target.id as target_id, r.type as relationship_type, r as properties
                        """
                    else:  # both
                        query = """
                        MATCH (source:Document {id: $entity_id})-[r:RELATES_TO]-(target:Document)
                        RETURN source.id as source_id, target.id as target_id, r.type as relationship_type, r as properties
                        """
                
                result = session.run(query, entity_id=entity_id, relationship_type=relationship_type)
                relationships = []
                
                for record in result:
                    relationships.append({
                        "source_id": record["source_id"],
                        "target_id": record["target_id"],
                        "relationship_type": record["relationship_type"],
                        "properties": dict(record["properties"])
                    })
                
                return {
                    "success": True,
                    "relationships": relationships,
                    "count": len(relationships)
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def search_relations(self, entity_id: str, relation_type: Optional[str] = None, direction: str = "both") -> Dict[str, Any]:
        """Wrapper to perform a read-only search for relationships.

        Parameters mirror query_relationships and do not allow writes.
        """
        return self.query_relationships(entity_id, relation_type, direction)
    
    def auto_link_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Automatically link related documents based on content similarity.
        
        Args:
            documents: List of documents with id and content
            
        Returns:
            Dictionary with linking results
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "Neo4j not available"
            }
        
        try:
            links_created = 0
            
            # First, create document nodes
            for doc in documents:
                self.create_document_node(doc["id"], {
                    "content": doc.get("content", ""),
                    "type": doc.get("type", "document"),
                    "created_at": doc.get("created_at", "")
                })
            
            # Simple similarity-based linking (can be enhanced with embeddings)
            for i, doc_a in enumerate(documents):
                for j, doc_b in enumerate(documents[i+1:], i+1):
                    # Simple keyword-based similarity
                    content_a = doc_a.get("content", "").lower()
                    content_b = doc_b.get("content", "").lower()
                    
                    # Check for common keywords
                    words_a = set(content_a.split())
                    words_b = set(content_b.split())
                    common_words = words_a.intersection(words_b)
                    
                    if len(common_words) >= 2:  # At least 2 common words
                        result = self.create_relationship(
                            doc_a["id"], 
                            doc_b["id"], 
                            "SIMILAR_TO",
                            {"similarity_score": len(common_words) / max(len(words_a), len(words_b))}
                        )
                        if result["success"]:
                            links_created += 1
            
            return {
                "success": True,
                "links_created": links_created,
                "documents_processed": len(documents)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Convenience functions for external use
def create_graph_relationships(
    store: Neo4jGraphStore,
    source_id: str,
    target_id: str,
    relationship_type: str
) -> Dict[str, Any]:
    """Create a graph relationship between documents.
    
    Args:
        store: Neo4jGraphStore instance
        source_id: Source document ID
        target_id: Target document ID
        relationship_type: Type of relationship
        
    Returns:
        Dictionary with success status
    """
    return store.create_relationship(source_id, target_id, relationship_type)


def query_graph_relationships(
    store: Neo4jGraphStore,
    entity_id: str,
    relationship_type: Optional[str] = None
) -> Dict[str, Any]:
    """Query graph relationships for an entity.
    
    Args:
        store: Neo4jGraphStore instance
        entity_id: Entity document ID
        relationship_type: Optional relationship type filter
        
    Returns:
        Dictionary with relationships found
    """
    return store.query_relationships(entity_id, relationship_type)


def auto_link_related_documents(
    store: Neo4jGraphStore,
    documents: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Automatically link related documents.
    
    Args:
        store: Neo4jGraphStore instance
        documents: List of documents to link
        
    Returns:
        Dictionary with linking results
    """
    return store.auto_link_documents(documents)


def get_document_relationships(
    store: Neo4jGraphStore,
    doc_id: str
) -> Dict[str, Any]:
    """Get all relationships for a document.
    
    Args:
        store: Neo4jGraphStore instance
        doc_id: Document ID
        
    Returns:
        Dictionary with all relationships
    """
    return store.query_relationships(doc_id)


# Global instance management
_neo4j_store: Optional[Neo4jGraphStore] = None


async def get_neo4j_graph_store() -> Neo4jGraphStore:
    """Get or create Neo4j graph store instance."""
    global _neo4j_store
    if not _neo4j_store:
        # Load configuration from ltmc_config.json
        from ltms.config.json_config_loader import get_config
        ltmc_config = get_config()
        
        config = {
            "uri": ltmc_config.neo4j_uri,
            "user": ltmc_config.neo4j_user,
            "password": ltmc_config.neo4j_password,
            "database": "neo4j"  # Using default database name from ltmc_config.json
        }
        _neo4j_store = Neo4jGraphStore(config)
    return _neo4j_store
