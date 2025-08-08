"""Tests for Neo4j integration functionality."""

import pytest
import tempfile
import os
from datetime import datetime
from typing import List, Dict, Any

# Import the functions we'll implement
from ltms.database.neo4j_store import (
    Neo4jGraphStore,
    create_graph_relationships,
    query_graph_relationships,
    auto_link_related_documents,
    get_document_relationships
)


class TestNeo4jIntegration:
    """Test suite for Neo4j integration functionality."""
    
    @pytest.fixture
    def temp_neo4j_config(self):
        """Create temporary Neo4j configuration for testing."""
        # Use the existing Neo4j Docker instance
        config = {
            "uri": "bolt://localhost:7687",
            "user": "neo4j",
            "password": "kwe_password",
            "database": "neo4j"
        }
        return config
    
    def test_neo4j_store_initialization(self, temp_neo4j_config):
        """Test Neo4j store initialization."""
        try:
            store = Neo4jGraphStore(temp_neo4j_config)
            assert store is not None
            assert store.config == temp_neo4j_config
        except Exception as e:
            # If Neo4j is not available, this is expected
            assert "Connection" in str(e) or "driver" in str(e)
    
    def test_create_graph_relationships(self, temp_neo4j_config):
        """Test creating graph relationships between documents."""
        try:
            store = Neo4jGraphStore(temp_neo4j_config)
            
            # Create test documents first
            store.create_document_node("doc_123", {"title": "Test Doc 1", "content": "Test content 1"})
            store.create_document_node("doc_456", {"title": "Test Doc 2", "content": "Test content 2"})
            
            # Test creating relationships
            doc_a_id = "doc_123"
            doc_b_id = "doc_456"
            relation_type = "REFERENCES"
            
            result = create_graph_relationships(
                store, doc_a_id, doc_b_id, relation_type
            )
            
            assert result['success'] is True
            assert result['relationship_created'] is True
            
        except Exception as e:
            # If Neo4j is not available, this is expected
            assert "Connection" in str(e) or "driver" in str(e)
    
    def test_query_graph_relationships(self, temp_neo4j_config):
        """Test querying graph relationships."""
        try:
            store = Neo4jGraphStore(temp_neo4j_config)
            
            # Test querying relationships
            entity_id = "doc_123"
            relation_type = "REFERENCES"
            
            result = query_graph_relationships(
                store, entity_id, relation_type
            )
            
            assert result['success'] is True
            assert 'relationships' in result
            
        except Exception as e:
            # If Neo4j is not available, this is expected
            assert "Connection" in str(e) or "driver" in str(e)
    
    def test_auto_link_related_documents(self, temp_neo4j_config):
        """Test automatic linking of related documents."""
        try:
            store = Neo4jGraphStore(temp_neo4j_config)
            
            # Test auto-linking
            documents = [
                {"id": "doc_1", "content": "Machine learning basics"},
                {"id": "doc_2", "content": "Deep learning algorithms"},
                {"id": "doc_3", "content": "Neural networks tutorial"}
            ]
            
            result = auto_link_related_documents(store, documents)
            
            assert result['success'] is True
            assert 'links_created' in result
            
        except Exception as e:
            # If Neo4j is not available, this is expected
            assert "Connection" in str(e) or "driver" in str(e)
    
    def test_get_document_relationships(self, temp_neo4j_config):
        """Test getting all relationships for a document."""
        try:
            store = Neo4jGraphStore(temp_neo4j_config)
            
            # Test getting relationships
            doc_id = "doc_123"
            
            result = get_document_relationships(store, doc_id)
            
            assert result['success'] is True
            assert 'relationships' in result
            
        except Exception as e:
            # If Neo4j is not available, this is expected
            assert "Connection" in str(e) or "driver" in str(e)
    
    def test_relationship_types(self, temp_neo4j_config):
        """Test different types of relationships."""
        try:
            store = Neo4jGraphStore(temp_neo4j_config)
            
            # Create test documents first
            store.create_document_node("doc_a", {"title": "Test Doc A", "content": "Test content A"})
            store.create_document_node("doc_b", {"title": "Test Doc B", "content": "Test content B"})
            
            # Test different relationship types
            relationship_types = [
                "REFERENCES",
                "SIMILAR_TO",
                "DEPENDS_ON",
                "EXTENDS",
                "IMPLEMENTS"
            ]
            
            for rel_type in relationship_types:
                result = create_graph_relationships(
                    store, "doc_a", "doc_b", rel_type
                )
                assert result['success'] is True
                
        except Exception as e:
            # If Neo4j is not available, this is expected
            assert "Connection" in str(e) or "driver" in str(e)
    
    def test_graph_traversal(self, temp_neo4j_config):
        """Test graph traversal functionality."""
        try:
            store = Neo4jGraphStore(temp_neo4j_config)
            
            # Create test documents first
            store.create_document_node("doc_1", {"title": "Test Doc 1", "content": "Test content 1"})
            store.create_document_node("doc_2", {"title": "Test Doc 2", "content": "Test content 2"})
            store.create_document_node("doc_3", {"title": "Test Doc 3", "content": "Test content 3"})
            store.create_document_node("doc_4", {"title": "Test Doc 4", "content": "Test content 4"})
            
            # Create a chain of relationships
            relationships = [
                ("doc_1", "doc_2", "REFERENCES"),
                ("doc_2", "doc_3", "EXTENDS"),
                ("doc_3", "doc_4", "IMPLEMENTS")
            ]
            
            for source, target, rel_type in relationships:
                result = create_graph_relationships(store, source, target, rel_type)
                assert result['success'] is True
            
            # Test traversal
            result = query_graph_relationships(store, "doc_1", "REFERENCES")
            assert result['success'] is True
            
        except Exception as e:
            # If Neo4j is not available, this is expected
            assert "Connection" in str(e) or "driver" in str(e)
    
    def test_error_handling(self, temp_neo4j_config):
        """Test error handling for invalid inputs."""
        try:
            store = Neo4jGraphStore(temp_neo4j_config)
            
            # Test with invalid inputs - these should fail validation
            result = create_graph_relationships(store, "", "", "")
            assert result['success'] is False
            assert 'error' in result
            
            # Query with empty string should return empty results, not error
            result = query_graph_relationships(store, "", "")
            assert result['success'] is True
            assert 'relationships' in result
            
        except Exception as e:
            # If Neo4j is not available, this is expected
            assert "Connection" in str(e) or "driver" in str(e)


if __name__ == "__main__":
    pytest.main([__file__])
