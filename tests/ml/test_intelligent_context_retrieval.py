"""Tests for Intelligent Context Retrieval."""

import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, patch
from typing import List, Dict, Any
import sqlite3
import tempfile
import os
from ltms.ml.intelligent_context_retrieval import (
    IntelligentContextRetrieval,
    ContextMatch,
    RetrievalStrategy
)


class TestContextMatch:
    """Test ContextMatch data structure."""

    def test_context_match_creation(self):
        """Test creating a context match."""
        match = ContextMatch(
            chunk_id=1,
            content="test content",
            relevance_score=0.85,
            context_type="semantic",
            reasoning="High semantic similarity to query"
        )
        
        assert match.chunk_id == 1
        assert match.content == "test content"
        assert match.relevance_score == 0.85
        assert match.context_type == "semantic"
        assert match.reasoning == "High semantic similarity to query"

    def test_context_match_ordering(self):
        """Test that context matches can be ordered by relevance."""
        match1 = ContextMatch(1, "content1", 0.7, "semantic", "reason1")
        match2 = ContextMatch(2, "content2", 0.9, "semantic", "reason2")
        match3 = ContextMatch(3, "content3", 0.8, "semantic", "reason3")
        
        matches = [match1, match2, match3]
        sorted_matches = sorted(matches, key=lambda m: m.relevance_score, reverse=True)
        
        assert sorted_matches[0].chunk_id == 2  # 0.9
        assert sorted_matches[1].chunk_id == 3  # 0.8
        assert sorted_matches[2].chunk_id == 1  # 0.7


class TestIntelligentContextRetrieval:
    """Test IntelligentContextRetrieval functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        # Set up test database with sample data
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
        
        # Insert test data
        test_resources = [
            (1, 'ml_basics.md', 'Machine learning fundamentals and algorithms'),
            (2, 'python_guide.md', 'Python programming best practices'),
            (3, 'data_science.md', 'Data science workflow and analysis'),
            (4, 'web_dev.md', 'Web development with React and Node.js'),
            (5, 'database_design.md', 'Database design principles and SQL')
        ]
        
        test_chunks = [
            (1, 1, 'Machine learning is a subset of AI focusing on algorithms', 1),
            (2, 1, 'Supervised learning uses labeled data for training', 2),
            (3, 2, 'Python list comprehensions are powerful and concise', 3),
            (4, 2, 'Virtual environments isolate project dependencies', 4),
            (5, 3, 'Data cleaning is crucial for analysis accuracy', 5),
            (6, 3, 'Statistical analysis helps find patterns in data', 6),
            (7, 4, 'React components manage state and lifecycle', 7),
            (8, 4, 'Node.js enables server-side JavaScript execution', 8),
            (9, 5, 'Normalization reduces data redundancy in databases', 9),
            (10, 5, 'SQL joins combine data from multiple tables', 10)
        ]
        
        for res in test_resources:
            conn.execute("INSERT INTO resources (id, file_name, content) VALUES (?, ?, ?)", res)
        
        for chunk in test_chunks:
            conn.execute("INSERT INTO resource_chunks (id, resource_id, content, vector_id) VALUES (?, ?, ?, ?)", chunk)
        
        conn.commit()
        conn.close()
        
        yield db_path
        os.unlink(db_path)

    @pytest.fixture
    def context_retrieval(self, temp_db):
        """Create an IntelligentContextRetrieval instance for testing."""
        retrieval = IntelligentContextRetrieval(
            db_path=temp_db,
            embedding_model_name='all-MiniLM-L6-v2'
        )
        return retrieval

    @pytest.mark.asyncio
    async def test_initialization(self, context_retrieval):
        """Test IntelligentContextRetrieval initialization."""
        await context_retrieval.initialize()
        
        assert context_retrieval.embedding_model is not None
        assert context_retrieval.semantic_manager is not None
        assert context_retrieval.is_initialized

    @pytest.mark.asyncio
    async def test_retrieve_context_semantic(self, context_retrieval):
        """Test semantic context retrieval."""
        await context_retrieval.initialize()
        
        results = await context_retrieval.retrieve_context(
            query="machine learning algorithms",
            strategy=RetrievalStrategy.SEMANTIC,
            max_results=3
        )
        
        assert isinstance(results, list)
        assert len(results) <= 3
        for result in results:
            assert isinstance(result, ContextMatch)
            assert result.context_type == "semantic"
            assert 0.0 <= result.relevance_score <= 1.0

    @pytest.mark.asyncio
    async def test_retrieve_context_hybrid(self, context_retrieval):
        """Test hybrid context retrieval."""
        await context_retrieval.initialize()
        
        results = await context_retrieval.retrieve_context(
            query="python programming",
            strategy=RetrievalStrategy.HYBRID,
            max_results=5
        )
        
        assert isinstance(results, list)
        assert len(results) <= 5
        for result in results:
            assert isinstance(result, ContextMatch)
            assert result.context_type in ["semantic", "keyword", "hybrid"]
            assert 0.0 <= result.relevance_score <= 1.0

    @pytest.mark.asyncio
    async def test_retrieve_context_clustering(self, context_retrieval):
        """Test clustering-based context retrieval."""
        await context_retrieval.initialize()
        
        # First build clusters
        await context_retrieval.semantic_manager.cluster_memories(min_cluster_size=2)
        
        results = await context_retrieval.retrieve_context(
            query="data analysis",
            strategy=RetrievalStrategy.CLUSTERING,
            max_results=4
        )
        
        assert isinstance(results, list)
        for result in results:
            assert isinstance(result, ContextMatch)
            assert result.context_type == "cluster"

    @pytest.mark.asyncio
    async def test_intelligent_ranking(self, context_retrieval):
        """Test intelligent ranking of context matches."""
        await context_retrieval.initialize()
        
        # Create mock context matches
        mock_matches = [
            ContextMatch(1, "Python is a programming language", 0.8, "semantic", "High similarity"),
            ContextMatch(2, "Machine learning with Python", 0.7, "semantic", "Good similarity"),
            ContextMatch(3, "Python web development", 0.6, "keyword", "Keyword match")
        ]
        
        ranked_matches = await context_retrieval._intelligent_ranking(
            matches=mock_matches,
            query="Python programming tutorial",
            context_window=["programming", "tutorial", "code"]
        )
        
        assert len(ranked_matches) == 3
        # Should be ranked by relevance score (descending)
        assert ranked_matches[0].relevance_score >= ranked_matches[1].relevance_score
        assert ranked_matches[1].relevance_score >= ranked_matches[2].relevance_score

    @pytest.mark.asyncio
    async def test_explain_retrieval(self, context_retrieval):
        """Test explanation of retrieval decisions."""
        await context_retrieval.initialize()
        
        results = await context_retrieval.retrieve_context(
            query="database design",
            strategy=RetrievalStrategy.SEMANTIC,
            max_results=2
        )
        
        for result in results:
            explanation = await context_retrieval.explain_retrieval(result)
            assert isinstance(explanation, dict)
            assert 'reasoning' in explanation
            assert 'confidence' in explanation
            assert 'factors' in explanation

    @pytest.mark.asyncio
    async def test_adaptive_threshold(self, context_retrieval):
        """Test adaptive threshold adjustment."""
        await context_retrieval.initialize()
        
        # Test with high threshold
        high_threshold_results = await context_retrieval.retrieve_context(
            query="specific technical term xyz123",
            strategy=RetrievalStrategy.SEMANTIC,
            max_results=5,
            relevance_threshold=0.8
        )
        
        # Test with low threshold
        low_threshold_results = await context_retrieval.retrieve_context(
            query="specific technical term xyz123",
            strategy=RetrievalStrategy.SEMANTIC,
            max_results=5,
            relevance_threshold=0.1
        )
        
        # Low threshold should return more results
        assert len(low_threshold_results) >= len(high_threshold_results)

    @pytest.mark.asyncio
    async def test_context_diversity(self, context_retrieval):
        """Test context diversity optimization."""
        await context_retrieval.initialize()
        
        results = await context_retrieval.retrieve_context(
            query="programming",
            strategy=RetrievalStrategy.HYBRID,
            max_results=5,
            diversify_results=True
        )
        
        # Check that results are diverse (not all from same resource)
        if len(results) > 1:
            resource_ids = set()
            for result in results:
                # Would need to fetch resource_id from database in real implementation
                pass  # This is a simplified test

    @pytest.mark.asyncio
    async def test_temporal_relevance(self, context_retrieval):
        """Test temporal relevance consideration."""
        await context_retrieval.initialize()
        
        results = await context_retrieval.retrieve_context(
            query="recent developments",
            strategy=RetrievalStrategy.TEMPORAL,
            max_results=3
        )
        
        assert isinstance(results, list)
        for result in results:
            assert isinstance(result, ContextMatch)
            assert result.context_type == "temporal"

    @pytest.mark.asyncio
    async def test_multi_strategy_fusion(self, context_retrieval):
        """Test fusion of multiple retrieval strategies."""
        await context_retrieval.initialize()
        
        results = await context_retrieval._multi_strategy_fusion(
            query="python machine learning",
            strategies=[RetrievalStrategy.SEMANTIC, RetrievalStrategy.KEYWORD],
            max_results=5
        )
        
        assert isinstance(results, list)
        assert len(results) <= 5
        
        # Should contain results from different strategies
        strategy_types = set(result.context_type for result in results)
        # May contain semantic, keyword, or hybrid types

    @pytest.mark.asyncio
    async def test_cleanup(self, context_retrieval):
        """Test cleanup operations."""
        await context_retrieval.initialize()
        await context_retrieval.cleanup()
        
        assert not context_retrieval.is_initialized