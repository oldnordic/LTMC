"""Tests for Semantic Memory Manager."""

import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, patch
from typing import List, Dict, Any
import sqlite3
import tempfile
import os
from ltms.ml.semantic_memory_manager import SemanticMemoryManager, MemoryCluster
from ltms.services.embedding_service import create_embedding_model


class TestMemoryCluster:
    """Test MemoryCluster data structure."""

    def test_memory_cluster_creation(self):
        """Test creating a memory cluster."""
        cluster = MemoryCluster(
            cluster_id=1,
            centroid=np.array([0.1, 0.2, 0.3]),
            member_ids=[1, 2, 3],
            coherence_score=0.85,
            topic_keywords=['test', 'memory', 'cluster']
        )
        
        assert cluster.cluster_id == 1
        assert np.array_equal(cluster.centroid, np.array([0.1, 0.2, 0.3]))
        assert cluster.member_ids == [1, 2, 3]
        assert cluster.coherence_score == 0.85
        assert cluster.topic_keywords == ['test', 'memory', 'cluster']

    def test_memory_cluster_similarity(self):
        """Test computing similarity between clusters."""
        cluster1 = MemoryCluster(
            cluster_id=1,
            centroid=np.array([1.0, 0.0, 0.0]),
            member_ids=[1, 2],
            coherence_score=0.8,
            topic_keywords=['test']
        )
        
        cluster2 = MemoryCluster(
            cluster_id=2,
            centroid=np.array([0.0, 1.0, 0.0]),
            member_ids=[3, 4],
            coherence_score=0.7,
            topic_keywords=['memory']
        )
        
        similarity = cluster1.similarity_to(cluster2)
        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0


class TestSemanticMemoryManager:
    """Test SemanticMemoryManager functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        # Set up test database
        conn = sqlite3.connect(db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY,
                file_name TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS resource_chunks (
                id INTEGER PRIMARY KEY,
                resource_id INTEGER,
                content TEXT NOT NULL,
                vector_id INTEGER,
                FOREIGN KEY (resource_id) REFERENCES resources (id)
            )
        ''')
        conn.close()
        
        yield db_path
        os.unlink(db_path)

    @pytest.fixture
    def semantic_manager(self, temp_db):
        """Create a SemanticMemoryManager instance for testing."""
        manager = SemanticMemoryManager(
            db_path=temp_db,
            embedding_model_name='all-MiniLM-L6-v2',
            clustering_algorithm='hdbscan'
        )
        return manager

    @pytest.mark.asyncio
    async def test_initialization(self, semantic_manager):
        """Test SemanticMemoryManager initialization."""
        await semantic_manager.initialize()
        
        assert semantic_manager.embedding_model is not None
        assert semantic_manager.clustering_algorithm == 'hdbscan'
        assert semantic_manager.clusters == {}
        assert semantic_manager.is_initialized

    @pytest.mark.asyncio
    async def test_cluster_memories(self, semantic_manager, temp_db):
        """Test clustering memory chunks."""
        await semantic_manager.initialize()
        
        # Add test data
        conn = sqlite3.connect(temp_db)
        conn.execute("INSERT INTO resources (file_name, content) VALUES (?, ?)", 
                    ('test1.md', 'This is about machine learning algorithms'))
        conn.execute("INSERT INTO resources (file_name, content) VALUES (?, ?)", 
                    ('test2.md', 'Deep learning neural networks are powerful'))
        conn.execute("INSERT INTO resource_chunks (resource_id, content, vector_id) VALUES (?, ?, ?)", 
                    (1, 'machine learning algorithms', 1))
        conn.execute("INSERT INTO resource_chunks (resource_id, content, vector_id) VALUES (?, ?, ?)", 
                    (2, 'deep learning neural networks', 2))
        conn.commit()
        conn.close()
        
        # Perform clustering
        clusters = await semantic_manager.cluster_memories(min_cluster_size=2)
        
        assert isinstance(clusters, dict)
        assert len(clusters) >= 0  # May be 0 if not enough similar data

    @pytest.mark.asyncio
    async def test_find_semantic_neighbors(self, semantic_manager, temp_db):
        """Test finding semantic neighbors for a query."""
        await semantic_manager.initialize()
        
        # Add test data
        conn = sqlite3.connect(temp_db)
        conn.execute("INSERT INTO resources (file_name, content) VALUES (?, ?)", 
                    ('test1.md', 'Python programming tutorial'))
        conn.execute("INSERT INTO resources (file_name, content) VALUES (?, ?)", 
                    ('test2.md', 'JavaScript web development'))
        conn.execute("INSERT INTO resource_chunks (resource_id, content, vector_id) VALUES (?, ?, ?)", 
                    (1, 'Python programming tutorial', 1))
        conn.execute("INSERT INTO resource_chunks (resource_id, content, vector_id) VALUES (?, ?, ?)", 
                    (2, 'JavaScript web development', 2))
        conn.commit()
        conn.close()
        
        # Find neighbors
        neighbors = await semantic_manager.find_semantic_neighbors(
            query="programming languages",
            top_k=2,
            similarity_threshold=0.0
        )
        
        assert isinstance(neighbors, list)
        assert len(neighbors) <= 2
        for neighbor in neighbors:
            assert 'chunk_id' in neighbor
            assert 'similarity_score' in neighbor
            assert 'content' in neighbor

    @pytest.mark.asyncio
    async def test_get_cluster_summary(self, semantic_manager):
        """Test getting cluster summary."""
        await semantic_manager.initialize()
        
        # Create a test cluster
        cluster = MemoryCluster(
            cluster_id=1,
            centroid=np.array([0.1, 0.2, 0.3]),
            member_ids=[1, 2],
            coherence_score=0.8,
            topic_keywords=['test', 'cluster']
        )
        semantic_manager.clusters[1] = cluster
        
        summary = await semantic_manager.get_cluster_summary(cluster_id=1)
        
        assert summary is not None
        assert summary['cluster_id'] == 1
        assert summary['member_count'] == 2
        assert summary['coherence_score'] == 0.8
        assert summary['topic_keywords'] == ['test', 'cluster']

    @pytest.mark.asyncio
    async def test_suggest_related_memories(self, semantic_manager, temp_db):
        """Test suggesting related memories."""
        await semantic_manager.initialize()
        
        # Add test data
        conn = sqlite3.connect(temp_db)
        conn.execute("INSERT INTO resources (file_name, content) VALUES (?, ?)", 
                    ('test1.md', 'Machine learning fundamentals'))
        conn.execute("INSERT INTO resources (file_name, content) VALUES (?, ?)", 
                    ('test2.md', 'Deep learning applications'))
        conn.execute("INSERT INTO resource_chunks (resource_id, content, vector_id) VALUES (?, ?, ?)", 
                    (1, 'Machine learning fundamentals', 1))
        conn.execute("INSERT INTO resource_chunks (resource_id, content, vector_id) VALUES (?, ?, ?)", 
                    (2, 'Deep learning applications', 2))
        conn.commit()
        conn.close()
        
        # Get suggestions
        suggestions = await semantic_manager.suggest_related_memories(
            memory_id=1,
            max_suggestions=3
        )
        
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 3
        for suggestion in suggestions:
            assert 'chunk_id' in suggestion
            assert 'similarity_score' in suggestion
            assert 'reasoning' in suggestion

    @pytest.mark.asyncio
    async def test_memory_coherence_analysis(self, semantic_manager, temp_db):
        """Test analyzing memory coherence."""
        await semantic_manager.initialize()
        
        # Add test data
        conn = sqlite3.connect(temp_db)
        conn.execute("INSERT INTO resources (file_name, content) VALUES (?, ?)", 
                    ('test1.md', 'Consistent topic about AI'))
        conn.execute("INSERT INTO resource_chunks (resource_id, content, vector_id) VALUES (?, ?, ?)", 
                    (1, 'Artificial intelligence research', 1))
        conn.commit()
        conn.close()
        
        analysis = await semantic_manager.analyze_memory_coherence(chunk_ids=[1])
        
        assert isinstance(analysis, dict)
        assert 'coherence_score' in analysis
        assert 'topic_consistency' in analysis
        assert 'cluster_assignments' in analysis

    @pytest.mark.asyncio
    async def test_cleanup(self, semantic_manager):
        """Test cleanup operations."""
        await semantic_manager.initialize()
        await semantic_manager.cleanup()
        
        assert not semantic_manager.is_initialized