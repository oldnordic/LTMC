"""Tests for ML-enhanced MCP tools."""

import pytest
import pytest_asyncio
import asyncio
import sqlite3
import tempfile
import os
from ltms.ml.enhanced_tools import MLEnhancedTools, get_ml_tools_instance


class TestMLEnhancedTools:
    """Test ML-enhanced tools functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        # Set up test database with comprehensive sample data
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
        
        # Insert comprehensive test data
        test_resources = [
            (1, 'ml_fundamentals.md', 'Machine learning fundamentals and core algorithms'),
            (2, 'python_advanced.md', 'Advanced Python programming techniques and patterns'),
            (3, 'data_analysis.md', 'Data analysis methodologies and statistical approaches'),
            (4, 'web_development.md', 'Modern web development with JavaScript frameworks'),
            (5, 'database_systems.md', 'Database design principles and optimization techniques'),
            (6, 'ai_research.md', 'Artificial intelligence research and recent developments'),
            (7, 'software_engineering.md', 'Software engineering best practices and methodologies')
        ]
        
        test_chunks = [
            (1, 1, 'Machine learning algorithms include supervised learning techniques', 1),
            (2, 1, 'Deep learning neural networks process complex data patterns', 2),
            (3, 1, 'Unsupervised learning discovers hidden patterns in data', 3),
            (4, 2, 'Python decorators provide elegant solutions for cross-cutting concerns', 4),
            (5, 2, 'Context managers enable resource management with clean syntax', 5),
            (6, 2, 'Metaclasses allow customization of class creation process', 6),
            (7, 3, 'Statistical hypothesis testing validates data analysis conclusions', 7),
            (8, 3, 'Data visualization reveals insights through graphical representations', 8),
            (9, 3, 'Regression analysis models relationships between variables', 9),
            (10, 4, 'React hooks revolutionized state management in functional components', 10),
            (11, 4, 'Modern JavaScript features enable cleaner and more efficient code', 11),
            (12, 4, 'WebAssembly brings near-native performance to web applications', 12),
            (13, 5, 'Database normalization reduces redundancy and improves consistency', 13),
            (14, 5, 'Query optimization techniques enhance database performance significantly', 14),
            (15, 5, 'NoSQL databases offer flexible schemas for diverse data types', 15),
            (16, 6, 'Large language models demonstrate emergent reasoning capabilities', 16),
            (17, 6, 'Computer vision advances enable real-time object detection', 17),
            (18, 6, 'Reinforcement learning solves complex sequential decision problems', 18),
            (19, 7, 'Agile methodologies emphasize iterative development and collaboration', 19),
            (20, 7, 'Clean code principles improve maintainability and readability', 20)
        ]
        
        for res in test_resources:
            conn.execute("INSERT INTO resources (id, file_name, content) VALUES (?, ?, ?)", res)
        
        for chunk in test_chunks:
            conn.execute("INSERT INTO resource_chunks (id, resource_id, content, vector_id) VALUES (?, ?, ?, ?)", chunk)
        
        conn.commit()
        conn.close()
        
        yield db_path
        os.unlink(db_path)

    @pytest_asyncio.fixture
    async def ml_tools(self, temp_db):
        """Create ML-enhanced tools instance."""
        tools = MLEnhancedTools(temp_db)
        await tools.initialize()
        yield tools
        await tools.cleanup()

    @pytest.mark.asyncio
    async def test_initialization(self, temp_db):
        """Test ML tools initialization."""
        tools = MLEnhancedTools(temp_db)
        await tools.initialize()
        
        assert tools._initialized
        assert tools.semantic_manager is not None
        assert tools.context_retrieval is not None
        
        await tools.cleanup()

    @pytest.mark.asyncio
    async def test_enhanced_retrieve_memory_semantic(self, ml_tools):
        """Test enhanced memory retrieval with semantic strategy."""
        result = await ml_tools.enhanced_retrieve_memory(
            query="machine learning algorithms",
            strategy="semantic",
            max_results=5,
            include_explanations=True,
            cluster_insights=True
        )
        
        assert result['success'] is True
        assert result['strategy_used'] == "semantic"
        assert result['results_count'] <= 5
        assert len(result['results']) == result['results_count']
        
        # Check result structure
        if result['results']:
            first_result = result['results'][0]
            assert 'chunk_id' in first_result
            assert 'content' in first_result
            assert 'relevance_score' in first_result
            assert 'context_type' in first_result
            assert 'reasoning' in first_result
            
            # Check relevance scores are valid
            assert 0.0 <= first_result['relevance_score'] <= 1.0

    @pytest.mark.asyncio
    async def test_enhanced_retrieve_memory_hybrid(self, ml_tools):
        """Test enhanced memory retrieval with hybrid strategy."""
        result = await ml_tools.enhanced_retrieve_memory(
            query="python programming techniques",
            strategy="hybrid",
            max_results=3,
            include_explanations=False,
            cluster_insights=False
        )
        
        assert result['success'] is True
        assert result['strategy_used'] == "hybrid"
        assert result['results_count'] <= 3
        assert result['explanations'] == []
        assert result['insights'] == {}

    @pytest.mark.asyncio
    async def test_enhanced_retrieve_memory_clustering(self, ml_tools):
        """Test enhanced memory retrieval with clustering strategy."""
        result = await ml_tools.enhanced_retrieve_memory(
            query="data analysis methods",
            strategy="clustering",
            max_results=4,
            include_explanations=True
        )
        
        assert result['success'] is True
        assert result['strategy_used'] == "clustering"
        assert result['results_count'] <= 4

    @pytest.mark.asyncio
    async def test_enhanced_suggest_related(self, ml_tools):
        """Test enhanced related memory suggestions."""
        result = await ml_tools.enhanced_suggest_related(
            memory_id=1,
            max_suggestions=3,
            include_cluster_context=True,
            diversity_threshold=0.3
        )
        
        assert result['success'] is True
        assert result['memory_id'] == 1
        assert result['suggestions_count'] <= 3
        assert len(result['suggestions']) == result['suggestions_count']
        assert 'cluster_context' in result

    @pytest.mark.asyncio
    async def test_enhanced_memory_analysis_full(self, ml_tools):
        """Test comprehensive memory analysis."""
        result = await ml_tools.enhanced_memory_analysis(
            analysis_type="full",
            rebuild_clusters=True,
            min_cluster_size=2
        )
        
        assert result['success'] is True
        assert result['analysis_type'] == "full"
        assert 'clusters_built' in result
        assert 'clustering_stats' in result
        assert 'cluster_summaries' in result
        assert 'memory_statistics' in result
        
        # Check memory statistics structure
        memory_stats = result['memory_statistics']
        assert 'total_resources' in memory_stats
        assert 'total_chunks' in memory_stats
        assert 'average_content_length' in memory_stats

    @pytest.mark.asyncio
    async def test_enhanced_memory_analysis_clusters_only(self, ml_tools):
        """Test cluster-only memory analysis."""
        result = await ml_tools.enhanced_memory_analysis(
            analysis_type="clusters",
            rebuild_clusters=True,
            min_cluster_size=3
        )
        
        assert result['success'] is True
        assert result['analysis_type'] == "clusters"
        assert 'cluster_summaries' in result
        assert 'coherence_analysis' not in result

    @pytest.mark.asyncio
    async def test_enhanced_memory_analysis_coherence_only(self, ml_tools):
        """Test coherence-only memory analysis."""
        result = await ml_tools.enhanced_memory_analysis(
            analysis_type="coherence",
            rebuild_clusters=False
        )
        
        assert result['success'] is True
        assert result['analysis_type'] == "coherence"
        assert 'coherence_analysis' in result

    @pytest.mark.asyncio
    async def test_diversity_filtering(self, ml_tools):
        """Test diversity filtering in suggestions."""
        # Create mock suggestions with similar content
        mock_suggestions = [
            {'content': 'Machine learning algorithms and techniques', 'chunk_id': 1},
            {'content': 'Machine learning methods and approaches', 'chunk_id': 2},
            {'content': 'Database design principles and patterns', 'chunk_id': 3},
            {'content': 'Web development frameworks and tools', 'chunk_id': 4}
        ]
        
        # Test diversity filtering
        diverse_suggestions = ml_tools._apply_diversity_filtering(
            mock_suggestions, diversity_threshold=0.5
        )
        
        # Should filter out very similar content
        assert len(diverse_suggestions) <= len(mock_suggestions)
        assert diverse_suggestions[0] == mock_suggestions[0]  # Top suggestion always included

    @pytest.mark.asyncio
    async def test_cluster_distribution_analysis(self, ml_tools):
        """Test cluster distribution analysis."""
        mock_results = [
            {'metadata': {'cluster_id': 1}},
            {'metadata': {'cluster_id': 1}},
            {'metadata': {'cluster_id': 2}},
            {'metadata': {}}  # No cluster_id
        ]
        
        distribution = ml_tools._analyze_cluster_distribution(mock_results)
        
        assert 'cluster_distribution' in distribution
        assert 'total_clusters_represented' in distribution
        assert 'unassigned_results' in distribution
        assert 'diversity_score' in distribution
        
        assert distribution['cluster_distribution']['1'] == 2
        assert distribution['cluster_distribution']['2'] == 1
        assert distribution['unassigned_results'] == 1

    @pytest.mark.asyncio
    async def test_simple_similarity_calculation(self, ml_tools):
        """Test simple similarity calculation."""
        text1 = "machine learning algorithms"
        text2 = "machine learning techniques"
        text3 = "database design patterns"
        
        # High similarity (shared words)
        sim1 = ml_tools._calculate_simple_similarity(text1, text2)
        assert sim1 >= 0.5
        
        # Low similarity (different topics)
        sim2 = ml_tools._calculate_simple_similarity(text1, text3)
        assert sim2 < 0.3

    @pytest.mark.asyncio
    async def test_memory_stats_calculation(self, ml_tools):
        """Test memory statistics calculation."""
        stats = await ml_tools._calculate_memory_stats()
        
        assert 'total_resources' in stats
        assert 'total_chunks' in stats
        assert 'average_content_length' in stats
        assert 'total_clusters' in stats
        assert 'clustered_memories' in stats
        
        assert stats['total_resources'] > 0
        assert stats['total_chunks'] > 0
        assert stats['average_content_length'] > 0

    @pytest.mark.asyncio
    async def test_error_handling(self, temp_db):
        """Test error handling in ML tools."""
        tools = MLEnhancedTools(temp_db)
        
        # Test using tools before initialization
        result = await tools.enhanced_retrieve_memory("test query")
        
        # Should auto-initialize and work
        assert result['success'] is True
        
        await tools.cleanup()

    @pytest.mark.asyncio
    async def test_global_instance_management(self, temp_db):
        """Test global ML tools instance management."""
        # Get instance
        instance1 = await get_ml_tools_instance(temp_db)
        assert instance1 is not None
        assert instance1._initialized
        
        # Get same instance
        instance2 = await get_ml_tools_instance(temp_db)
        assert instance1 is instance2
        
        # Cleanup
        from ltms.ml.enhanced_tools import cleanup_ml_tools
        await cleanup_ml_tools()
        
        # Should create new instance after cleanup
        instance3 = await get_ml_tools_instance(temp_db)
        assert instance3 is not instance1
        
        await cleanup_ml_tools()

    @pytest.mark.asyncio
    async def test_conversation_context_handling(self, ml_tools):
        """Test conversation context handling."""
        conversation_id = "test_conversation_123"
        
        result = await ml_tools.enhanced_retrieve_memory(
            query="python programming",
            conversation_id=conversation_id,
            strategy="semantic"
        )
        
        assert result['success'] is True
        assert result['conversation_id'] == conversation_id
        assert 'timestamp' in result

    @pytest.mark.asyncio
    async def test_retrieval_with_different_thresholds(self, ml_tools):
        """Test retrieval with different relevance thresholds."""
        # Test with high threshold
        result_high = await ml_tools.enhanced_retrieve_memory(
            query="machine learning",
            strategy="semantic",
            max_results=10
        )
        
        # Simulate different threshold by checking relevance scores
        high_relevance_results = [
            r for r in result_high['results'] 
            if r['relevance_score'] > 0.7
        ]
        
        low_relevance_results = [
            r for r in result_high['results'] 
            if r['relevance_score'] > 0.1
        ]
        
        # Should have fewer high-relevance results
        assert len(high_relevance_results) <= len(low_relevance_results)